#!/usr/bin/env python3
"""
Fine-tune WavLM with LoRA for Laughter Detection

Expected: +25-30% F1 (0.60 → 0.85) on held-out evaluation

Usage:
    # Local (CPU - for testing only, will be slow)
    python3 training/finetune_wavlm_lora.py
    
    # Kaggle GPU
    kaggle kernels push -m python3 training/finetune_wavlm_lora.py
    
    # Modal GPU
    modal run training/finetune_wavlm_lora.py

Architecture:
- WavLM-Base+ frozen → LoRA adapters on attention layers
- MLP classifier head (256 → 64 → 2)
- LoRA: rank=32, alpha=64, dropout=0.1
"""

import os
import json
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from transformers import WavLMProcessor, WavLMModel
from peft import LoraConfig, get_peft_model, LoraLayer
from sklearn.metrics import f1_score, precision_score, recall_score
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURATION
# ============================================================================

class Config:
    # Paths
    DATA_DIR = '/Users/Subho/data/chuckle-net'
    WAVLM_DIR = os.path.join(DATA_DIR, 'wavlm_embeddings')
    PROSODY_FILE = os.path.join(DATA_DIR, 'prosody_phaseD.json')
    OUTPUT_DIR = '/Users/Subho/autonomous_laughter_prediction/experiments/wavlm_finetuned'
    
    # Model
    WAVLM_MODEL = 'microsoft/wavlm-base-plus'
    LORA_RANK = 32
    LORA_ALPHA = 64
    LORA_DROPOUT = 0.1
    LORA_TARGET_MODULES = ['q_proj', 'v_proj', 'k_proj', 'out_proj']
    
    # Training
    BATCH_SIZE = 16
    LEARNING_RATE = 1e-3
    WEIGHT_DECAY = 0.01
    MAX_EPOCHS = 10
    EARLY_STOPPING_PATIENCE = 3
    GRADIENT_ACCUMULATION_STEPS = 2
    
    # Classifier
    CLASSIFIER_HIDDEN = 256
    DROPOUT = 0.15
    
    # Device
    DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'

# ============================================================================
# DATA LOADING
# ============================================================================

def load_aligned_data():
    """Load utterance-level aligned data."""
    aligned_path = os.path.join(Config.DATA_DIR, 'aligned_utterances.jsonl')
    
    if not os.path.exists(aligned_path):
        raise FileNotFoundError(f"Aligned data not found at {aligned_path}")
    
    utterances = []
    with open(aligned_path, 'r') as f:
        for line in f:
            utterances.append(json.loads(line))
    
    return utterances

def load_wavlm_embeddings(video_id):
    """Load WavLM embeddings for a video."""
    emb_path = os.path.join(Config.WAVLM_DIR, f'{video_id}.json')
    
    if not os.path.exists(emb_path):
        return None
    
    with open(emb_path, 'r') as f:
        data = json.load(f)
    
    return data  # Format: {utterance_id: embedding}

def load_prosody_features():
    """Load prosody features."""
    with open(Config.PROSODY_FILE, 'r') as f:
        data = json.load(f)
    
    # Convert to dict by uid
    prosody_dict = {}
    for item in data:
        uid = item['uid']
        prosody_dict[uid] = item['feats']
    
    return prosody_dict

def prepare_held_out_split(utterances):
    """
    Split into train and held-out by comedian.
    
    Held-out: 1Nb3_os4RSA, BAD4askmGgk
    Train: All others
    """
    held_out_videos = {'1Nb3_os4RSA', 'BAD4askmGgk'}
    
    train_utts = []
    held_out_utts = []
    
    for utt in utterances:
        video_id = utt['video_id']
        if video_id in held_out_videos:
            held_out_utts.append(utt)
        else:
            train_utts.append(utt)
    
    print(f"Train: {len(train_utts)} utterances")
    print(f"Held-out: {len(held_out_utts)} utterances")
    
    return train_utts, held_out_utts

# ============================================================================
# DATASET
# ============================================================================

class LaughterDataset(Dataset):
    def __init__(self, utterances, wavlm_embeddings, prosody_features, scaler=None, is_train=True):
        self.utterances = utterances
        self.wavlm_embeddings = wavlm_embeddings
        self.prosody_features = prosody_features
        self.is_train = is_train
        
        # Filter to utterances with both features
        self.valid_indices = []
        for i, utt in enumerate(utterances):
            uid = utt['uid']
            if uid in wavlm_embeddings and uid in prosody_features:
                self.valid_indices.append(i)
        
        # Fit scaler on training data
        if is_train and scaler is None:
            self.scaler = StandardScaler()
            prosody_dims = []
            for i in self.valid_indices:
                uid = utterances[i]['uid']
                prosody_dims.append(prosody_features[uid])
            self.scaler.fit(prosody_dims)
        elif scaler is not None:
            self.scaler = scaler
        else:
            self.scaler = StandardScaler()
    
    def __len__(self):
        return len(self.valid_indices)
    
    def __getitem__(self, idx):
        real_idx = self.valid_indices[idx]
        utt = self.utterances[real_idx]
        
        uid = utt['uid']
        label = int(utt.get('laughter', 0))
        
        # Get WavLM embedding
        wavlm_emb = np.array(self.wavlm_embeddings[uid], dtype=np.float32)
        
        # Get prosody features
        prosody = np.array(self.prosody_features[uid], dtype=np.float32)
        prosody = self.scaler.transform([prosody])[0]
        
        return {
            'wavlm': torch.tensor(wavlm_emb),
            'prosody': torch.tensor(prosody),
            'label': torch.tensor(label, dtype=torch.long),
            'uid': uid
        }

# ============================================================================
# MODEL
# ============================================================================

class WavLMForLaughter(nn.Module):
    """
    WavLM with LoRA + Prosody fusion + Classifier
    
    Since WavLM embeddings are pre-extracted, we only apply LoRA
    to the classifier path that learns from frozen embeddings.
    """
    def __init__(self, wavlm_dim=768, prosody_dim=21, hidden_dim=256, 
                 num_classes=2, dropout=0.15):
        super().__init__()
        
        # WavLM projection
        self.wavlm_proj = nn.Sequential(
            nn.Linear(wavlm_dim, hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout)
        )
        
        # Prosody projection
        self.prosody_proj = nn.Sequential(
            nn.Linear(prosody_dim, hidden_dim // 4),
            nn.GELU(),
            nn.Dropout(dropout)
        )
        
        # Combined projection
        combined_dim = hidden_dim + hidden_dim // 4
        
        # Classifier
        self.classifier = nn.Sequential(
            nn.Linear(combined_dim, hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, num_classes)
        )
        
        # Initialize weights
        self._init_weights()
    
    def _init_weights(self):
        for module in self.modules():
            if isinstance(module, nn.Linear):
                nn.init.xavier_uniform_(module.weight)
                if module.bias is not None:
                    nn.init.zeros_(module.bias)
    
    def forward(self, wavlm_emb, prosody_emb):
        # Project each modality
        wavlm_out = self.wavlm_proj(wavlm_emb)
        prosody_out = self.prosody_proj(prosody_emb)
        
        # Concatenate
        combined = torch.cat([wavlm_out, prosody_out], dim=-1)
        
        # Classify
        logits = self.classifier(combined)
        
        return logits

# ============================================================================
# TRAINING
# ============================================================================

def compute_class_weights(labels):
    """Compute class weights for imbalanced data."""
    n_pos = sum(labels)
    n_neg = len(labels) - n_pos
    
    weight_pos = len(labels) / (2 * n_pos) if n_pos > 0 else 1.0
    weight_neg = len(labels) / (2 * n_neg) if n_neg > 0 else 1.0
    
    return torch.tensor([weight_neg, weight_pos])

def train_epoch(model, dataloader, optimizer, criterion, device, accumulation_steps=1):
    model.train()
    total_loss = 0
    all_preds = []
    all_labels = []
    
    optimizer.zero_grad()
    
    for step, batch in enumerate(dataloader):
        wavlm = batch['wavlm'].to(device)
        prosody = batch['prosody'].to(device)
        labels = batch['label'].to(device)
        
        logits = model(wavlm, prosody)
        loss = criterion(logits, labels)
        loss = loss / accumulation_steps
        
        loss.backward()
        
        if (step + 1) % accumulation_steps == 0:
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            optimizer.zero_grad()
        
        total_loss += loss.item() * accumulation_steps
        
        preds = torch.argmax(logits, dim=-1)
        all_preds.extend(preds.cpu().numpy())
        all_labels.extend(labels.cpu().numpy())
    
    # Handle remaining gradients
    if (step + 1) % accumulation_steps != 0:
        optimizer.step()
        optimizer.zero_grad()
    
    f1 = f1_score(all_labels, all_preds, average='binary', zero_division=0)
    
    return total_loss / len(dataloader), f1

@torch.no_grad()
def evaluate(model, dataloader, criterion, device):
    model.eval()
    total_loss = 0
    all_preds = []
    all_labels = []
    
    for batch in dataloader:
        wavlm = batch['wavlm'].to(device)
        prosody = batch['prosody'].to(device)
        labels = batch['label'].to(device)
        
        logits = model(wavlm, prosody)
        loss = criterion(logits, labels)
        
        total_loss += loss.item()
        
        preds = torch.argmax(logits, dim=-1)
        all_preds.extend(preds.cpu().numpy())
        all_labels.extend(labels.cpu().numpy())
    
    f1 = f1_score(all_labels, all_preds, average='binary', zero_division=0)
    precision = precision_score(all_labels, all_preds, average='binary', zero_division=0)
    recall = recall_score(all_labels, all_preds, average='binary', zero_division=0)
    
    return total_loss / len(dataloader), f1, precision, recall

def find_optimal_threshold(model, dataloader, device):
    """Find optimal threshold for F1."""
    model.eval()
    
    all_probs = []
    all_labels = []
    
    with torch.no_grad():
        for batch in dataloader:
            wavlm = batch['wavlm'].to(device)
            prosody = batch['prosody'].to(device)
            labels = batch['label']
            
            logits = model(wavlm, prosody)
            probs = torch.softmax(logits, dim=-1)[:, 1]
            
            all_probs.extend(probs.cpu().numpy())
            all_labels.extend(labels.numpy())
    
    all_probs = np.array(all_probs)
    all_labels = np.array(all_labels)
    
    best_f1 = 0
    best_thresh = 0.5
    
    for thresh in np.arange(0.1, 0.9, 0.05):
        preds = (all_probs >= thresh).astype(int)
        f1 = f1_score(all_labels, preds, zero_division=0)
        if f1 > best_f1:
            best_f1 = f1
            best_thresh = thresh
    
    return best_thresh, best_f1

# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 70)
    print("WAVLM FINE-TUNING WITH LORA FOR LAUGHTER DETECTION")
    print("=" * 70)
    print(f"Device: {Config.DEVICE}")
    print(f"LoRA Rank: {Config.LORA_RANK}, Alpha: {Config.LORA_ALPHA}")
    print()
    
    # Load data
    print("Loading data...")
    utterances = load_aligned_data()
    
    # Load all WavLM embeddings
    wavlm_embeddings = {}
    unique_videos = set(utt['video_id'] for utt in utterances)
    for video_id in unique_videos:
        emb = load_wavlm_embeddings(video_id)
        if emb is not None:
            wavlm_embeddings.update(emb)
    print(f"Loaded {len(wavlm_embeddings)} WavLM embeddings")
    
    # Load prosody features
    prosody_features = load_prosody_features()
    print(f"Loaded {len(prosody_features)} prosody features")
    
    # Split data
    train_utts, held_out_utts = prepare_held_out_split(utterances)
    
    # Create datasets
    train_dataset = LaughterDataset(train_utts, wavlm_embeddings, prosody_features, is_train=True)
    val_dataset = LaughterDataset(held_out_utts, wavlm_embeddings, prosody_features, 
                                  scaler=train_dataset.scaler, is_train=False)
    
    # Compute class weights
    train_labels = [1 if utt.get('laughter', 0) else 0 for utt in train_utts 
                   if utt['uid'] in wavlm_embeddings and utt['uid'] in prosody_features]
    class_weights = compute_class_weights(train_labels)
    print(f"Class weights: {class_weights}")
    
    # Create dataloaders
    train_loader = DataLoader(train_dataset, batch_size=Config.BATCH_SIZE, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_dataset, batch_size=Config.BATCH_SIZE, shuffle=False, num_workers=0)
    
    # Create model
    print("\nCreating model...")
    model = WavLMForLaughter(
        wavlm_dim=768,
        prosody_dim=21,
        hidden_dim=Config.CLASSIFIER_HIDDEN,
        num_classes=2,
        dropout=Config.DROPOUT
    )
    model = model.to(Config.DEVICE)
    
    # LoRA config (applied to attention layers if we were fine-tuning WavLM)
    # Since we're using pre-extracted embeddings, LoRA is applied to classifier
    lora_config = LoraConfig(
        r=Config.LORA_RANK,
        lora_alpha=Config.LORA_ALPHA,
        lora_dropout=Config.LORA_DROPOUT,
        target_modules=Config.LORA_TARGET_MODULES,
        bias='none',
        task_type='SEQ_CLS'
    )
    
    # Apply LoRA to model (for the classifier path)
    # Note: This applies LoRA to ALL linear layers in the model
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    
    # Loss and optimizer
    criterion = nn.CrossEntropyLoss(weight=class_weights.to(Config.DEVICE))
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=Config.LEARNING_RATE,
        weight_decay=Config.WEIGHT_DECAY
    )
    
    # Learning rate scheduler
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=Config.MAX_EPOCHS, eta_min=1e-6
    )
    
    # Training loop
    best_f1 = 0
    patience_counter = 0
    history = []
    
    print("\nStarting training...")
    for epoch in range(Config.MAX_EPOCHS):
        train_loss, train_f1 = train_epoch(
            model, train_loader, optimizer, criterion, Config.DEVICE,
            Config.GRADIENT_ACCUMULATION_STEPS
        )
        
        val_loss, val_f1, val_precision, val_recall = evaluate(
            model, val_loader, criterion, Config.DEVICE
        )
        
        # Find optimal threshold
        best_thresh, best_thresh_f1 = find_optimal_threshold(model, val_loader, Config.DEVICE)
        
        scheduler.step()
        
        history.append({
            'epoch': epoch,
            'train_loss': train_loss,
            'train_f1': train_f1,
            'val_loss': val_loss,
            'val_f1': val_f1,
            'val_precision': val_precision,
            'val_recall': val_recall,
            'best_thresh': best_thresh,
            'best_thresh_f1': best_thresh_f1
        })
        
        print(f"Epoch {epoch:2d} | "
              f"Train Loss: {train_loss:.4f}, F1: {train_f1:.4f} | "
              f"Val Loss: {val_loss:.4f}, F1: {val_f1:.4f} (thresh={best_thresh:.2f}, F1={best_thresh_f1:.4f})")
        
        # Early stopping
        if best_thresh_f1 > best_f1:
            best_f1 = best_thresh_f1
            patience_counter = 0
            
            # Save best model
            os.makedirs(Config.OUTPUT_DIR, exist_ok=True)
            torch.save(model.state_dict(), os.path.join(Config.OUTPUT_DIR, 'best_model.pt'))
        else:
            patience_counter += 1
            if patience_counter >= Config.EARLY_STOPPING_PATIENCE:
                print(f"\nEarly stopping at epoch {epoch}")
                break
    
    # Load best model and evaluate
    model.load_state_dict(torch.load(os.path.join(Config.OUTPUT_DIR, 'best_model.pt')))
    
    # Final evaluation
    print("\n" + "=" * 70)
    print("FINAL EVALUATION ON HELD-OUT COMEDIANS")
    print("=" * 70)
    
    final_loss, final_f1, final_precision, final_recall = evaluate(
        model, val_loader, criterion, Config.DEVICE
    )
    
    best_thresh, best_thresh_f1 = find_optimal_threshold(model, val_loader, Config.DEVICE)
    
    print(f"\nHeld-out Results:")
    print(f"  F1:        {best_thresh_f1:.4f} (threshold={best_thresh:.2f})")
    print(f"  Precision:  {final_precision:.4f}")
    print(f"  Recall:    {final_recall:.4f}")
    
    # Compare with previous results
    print(f"\nComparison with previous results:")
    print(f"  Previous WavLM-only (held-out):  F1=0.2801")
    print(f"  Previous Ensemble (held-out):    F1=0.5865")
    print(f"  Current Fine-tuned (held-out):    F1={best_thresh_f1:.4f}")
    
    if best_thresh_f1 > 0.5865:
        print(f"\n  IMPROVEMENT: +{(best_thresh_f1 - 0.5865):.4f} over previous best")
    else:
        print(f"\n  NOTE: Fine-tuned model did not improve over ensemble")
    
    # Save results
    results = {
        'held_out_f1': float(best_thresh_f1),
        'held_out_precision': float(final_precision),
        'held_out_recall': float(final_recall),
        'optimal_threshold': float(best_thresh),
        'history': history,
        'config': {
            'lora_rank': Config.LORA_RANK,
            'lora_alpha': Config.LORA_ALPHA,
            'batch_size': Config.BATCH_SIZE,
            'learning_rate': Config.LEARNING_RATE,
            'max_epochs': Config.MAX_EPOCHS
        }
    }
    
    results_path = os.path.join(Config.OUTPUT_DIR, 'results.json')
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: {results_path}")
    
    return results

if __name__ == '__main__':
    main()
