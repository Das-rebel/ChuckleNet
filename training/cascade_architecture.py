#!/usr/bin/env python3
"""
Cascade Architecture for Laughter Detection

ARCHITECTURE:
Stage 1: XLM-R text → propose likely laugh REGIONS (coarse span prediction)
Stage 2: Prosody/audio → refine BOUNDARIES within regions (boundary offset regression)

RATIONALE:
- Single-stage classifier trying to do both region detection AND boundary refinement
  causes the IoU-F1 ceiling at 0.50
- Separating these tasks lets each module focus
- Text is good at predicting "is there a joke here?" (region)
- Prosody is good at predicting "where exactly does laughter start/end?" (boundary)

Usage:
    python3 training/cascade_architecture.py
"""

import os
import json
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from transformers import XLMRobertaTokenizer, XLMRobertaModel
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
    OUTPUT_DIR = '/Users/Subho/autonomous_laughter_prediction/experiments/cascade'
    
    # Model
    XLM_MODEL = 'xlm-roberta-base'
    MAX_LENGTH = 128
    
    # Training
    BATCH_SIZE = 16
    LEARNING_RATE = 5e-5
    WEIGHT_DECAY = 0.01
    MAX_EPOCHS = 15
    EARLY_STOPPING_PATIENCE = 5
    
    # Region threshold (Stage 1)
    REGION_THRESHOLD = 0.3  # Low threshold to catch most regions
    
    # Boundary offset range (Stage 2)
    MAX_OFFSET = 2.0  # seconds
    
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
# STAGE 1: REGION PROPOSAL (Text-based)
# ============================================================================

class RegionProposalDataset(Dataset):
    """
    Dataset for Stage 1: Text-based region proposal.
    
    Each sample is a word with its context, and the label is
    whether laughter follows within the next N seconds.
    """
    def __init__(self, utterances, tokenizer, max_length=128, window_size=5):
        self.utterances = utterances
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.window_size = window_size  # Words to include in context
        
        # Build samples
        self.samples = self._build_samples()
    
    def _build_samples(self):
        samples = []
        
        for utt in self.utterances:
            video_id = utt['video_id']
            words = utt.get('words', [])
            start_time = utt.get('start', 0)
            laughter = utt.get('laughter', 0)
            
            if not words:
                continue
            
            # For each word, create a sample
            for i, word_info in enumerate(words):
                word = word_info.get('word', '')
                word_start = word_info.get('start', start_time)
                word_end = word_info.get('end', word_start + 1)
                
                # Get context words
                context_start = max(0, i - self.window_size)
                context_end = min(len(words), i + self.window_size + 1)
                
                context_words = [w.get('word', '') for w in words[context_start:context_end]]
                text = ' '.join(context_words)
                
                # Label: is there laughter within the next 5 seconds after this word?
                # This is approximated by the utterance-level label for simplicity
                # In practice, you would need word-level alignment
                label = laughter  # Placeholder: use utterance label
                
                samples.append({
                    'text': text,
                    'word': word,
                    'word_start': word_start,
                    'word_end': word_end,
                    'uid': utt['uid'],
                    'video_id': video_id,
                    'label': label
                })
        
        return samples
    
    def __len__(self):
        return len(self.samples)
    
    def __getitem__(self, idx):
        sample = self.samples[idx]
        
        encoding = self.tokenizer(
            sample['text'],
            truncation=True,
            max_length=self.max_length,
            padding='max_length',
            return_tensors='pt'
        )
        
        return {
            'input_ids': encoding['input_ids'].squeeze(),
            'attention_mask': encoding['attention_mask'].squeeze(),
            'label': torch.tensor(sample['label'], dtype=torch.long),
            'word_start': torch.tensor(sample['word_start']),
            'word_end': torch.tensor(sample['word_end']),
            'uid': sample['uid'],
            'video_id': sample['video_id']
        }

class RegionProposalModel(nn.Module):
    """
    Stage 1: XLM-R based region proposal.
    
    Takes text context and predicts probability of laughter following.
    """
    def __init__(self, model_name='xlm-roberta-base', hidden_dim=256):
        super().__init__()
        
        self.encoder = XLMRobertaModel.from_pretrained(model_name)
        hidden_size = self.encoder.config.hidden_size  # 768 for XLM-R
        
        # Projection
        self.proj = nn.Sequential(
            nn.Linear(hidden_size, hidden_dim),
            nn.GELU(),
            nn.Dropout(0.1)
        )
        
        # Classifier
        self.classifier = nn.Linear(hidden_dim, 2)
    
    def forward(self, input_ids, attention_mask):
        outputs = self.encoder(
            input_ids=input_ids,
            attention_mask=attention_mask
        )
        
        # Use [CLS] token
        cls_output = outputs.last_hidden_state[:, 0, :]
        
        # Project and classify
        proj = self.proj(cls_output)
        logits = self.classifier(proj)
        
        return logits

# ============================================================================
# STAGE 2: BOUNDARY REFINEMENT (Prosody-based)
# ============================================================================

class BoundaryRefinementDataset(Dataset):
    """
    Dataset for Stage 2: Prosody-based boundary refinement.
    
    Takes regions proposed by Stage 1 and refines their boundaries
    using acoustic features.
    """
    def __init__(self, utterances, prosody_features, scaler=None, is_train=True):
        self.utterances = utterances
        self.prosody_features = prosody_features
        
        # Filter to utterances with prosody
        self.valid_indices = []
        for i, utt in enumerate(utterances):
            uid = utt['uid']
            if uid in prosody_features:
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
        
        # Get prosody features
        prosody = np.array(self.prosody_features[uid], dtype=np.float32)
        prosody = self.scaler.transform([prosody])[0]
        
        # Get word timing info
        words = utt.get('words', [])
        start_time = utt.get('start', 0)
        
        # Estimate boundary offset (difference between word start and laughter start)
        # This is a placeholder - real boundary offset requires word-level alignment
        boundary_offset = 0.0  # Placeholder
        
        return {
            'prosody': torch.tensor(prosody),
            'label': torch.tensor(label, dtype=torch.long),
            'uid': uid,
            'video_id': utt['video_id'],
            'boundary_offset': torch.tensor(boundary_offset, dtype=torch.float32)
        }

class BoundaryRefinementModel(nn.Module):
    """
    Stage 2: Prosody-based boundary refinement.
    
    Takes prosody features and predicts boundary offsets.
    """
    def __init__(self, prosody_dim=21, hidden_dim=128):
        super().__init__()
        
        # Prosody encoder
        self.prosody_encoder = nn.Sequential(
            nn.Linear(prosody_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2)
        )
        
        # Boundary offset predictor (regression)
        self.boundary_head = nn.Linear(hidden_dim, 1)
        
        # Laughter classifier
        self.laughter_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim // 2, 2)
        )
    
    def forward(self, prosody):
        encoded = self.prosody_encoder(prosody)
        
        boundary_offset = self.boundary_head(encoded)  # Regression
        laughter_logits = self.laughter_head(encoded)  # Classification
        
        return boundary_offset, laughter_logits

# ============================================================================
# CASCADE PIPELINE
# ============================================================================

class CascadeLaughterDetector(nn.Module):
    """
    Two-stage cascade for laughter detection.
    
    Stage 1: Text-based region proposal
    Stage 2: Prosody-based boundary refinement
    """
    def __init__(self, region_proposal_model, boundary_refinement_model):
        super().__init__()
        
        self.region_proposal = region_proposal_model
        self.boundary_refinement = boundary_refinement_model
    
    def forward(self, text_input_ids, text_attention_mask, prosody):
        # Stage 1: Region proposal
        region_logits = self.region_proposal(text_input_ids, text_attention_mask)
        
        # Stage 2: Boundary refinement
        boundary_offset, boundary_logits = self.boundary_refinement(prosody)
        
        return region_logits, boundary_logits, boundary_offset

# ============================================================================
# TRAINING
# ============================================================================

def train_stage1(model, dataloader, optimizer, criterion, device):
    """Train Stage 1 (Region Proposal)."""
    model.train()
    total_loss = 0
    all_preds = []
    all_labels = []
    
    for batch in dataloader:
        input_ids = batch['input_ids'].to(device)
        attention_mask = batch['attention_mask'].to(device)
        labels = batch['label'].to(device)
        
        optimizer.zero_grad()
        
        logits = model(input_ids, attention_mask)
        loss = criterion(logits, labels)
        
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        
        total_loss += loss.item()
        
        preds = torch.argmax(logits, dim=-1)
        all_preds.extend(preds.cpu().numpy())
        all_labels.extend(labels.cpu().numpy())
    
    f1 = f1_score(all_labels, all_preds, average='binary', zero_division=0)
    
    return total_loss / len(dataloader), f1

def train_stage2(model, dataloader, optimizer, criterion, device):
    """Train Stage 2 (Boundary Refinement)."""
    model.train()
    total_loss = 0
    all_preds = []
    all_labels = []
    
    for batch in dataloader:
        prosody = batch['prosody'].to(device)
        labels = batch['label'].to(device)
        
        optimizer.zero_grad()
        
        _, laughter_logits = model(prosody)
        loss = criterion(laughter_logits, labels)
        
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        
        total_loss += loss.item()
        
        preds = torch.argmax(laughter_logits, dim=-1)
        all_preds.extend(preds.cpu().numpy())
        all_labels.extend(labels.cpu().numpy())
    
    f1 = f1_score(all_labels, all_preds, average='binary', zero_division=0)
    
    return total_loss / len(dataloader), f1

@torch.no_grad()
def evaluate(model, dataloader, criterion, device, stage='both'):
    """Evaluate the model."""
    model.eval()
    total_loss = 0
    all_preds = []
    all_labels = []
    
    for batch in dataloader:
        if stage == 1:
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            labels = batch['label'].to(device)
            
            logits = model(input_ids, attention_mask)
            loss = criterion(logits, labels)
            
            preds = torch.argmax(logits, dim=-1)
            
        elif stage == 2:
            prosody = batch['prosody'].to(device)
            labels = batch['label'].to(device)
            
            _, laughter_logits = model(prosody)
            loss = criterion(laughter_logits, labels)
            
            preds = torch.argmax(laughter_logits, dim=-1)
        
        total_loss += loss.item()
        all_preds.extend(preds.cpu().numpy())
        all_labels.extend(labels.cpu().numpy())
    
    f1 = f1_score(all_labels, all_preds, average='binary', zero_division=0)
    precision = precision_score(all_labels, all_preds, average='binary', zero_division=0)
    recall = recall_score(all_labels, all_preds, average='binary', zero_division=0)
    
    return total_loss / len(dataloader), f1, precision, recall

# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 70)
    print("CASCADE ARCHITECTURE FOR LAUGHTER DETECTION")
    print("=" * 70)
    print(f"Device: {Config.DEVICE}")
    print()
    
    # Load data
    print("Loading data...")
    utterances = load_aligned_data()
    
    # Load prosody features
    prosody_path = os.path.join(Config.DATA_DIR, 'prosody_phaseD.json')
    with open(prosody_path, 'r') as f:
        prosody_data = json.load(f)
    
    prosody_features = {item['uid']: item['feats'] for item in prosody_data}
    print(f"Loaded {len(prosody_features)} prosody features")
    
    # Split data
    train_utts, held_out_utts = prepare_held_out_split(utterances)
    
    # Initialize tokenizer
    print("\nLoading XLM-R tokenizer...")
    tokenizer = XLMRobertaTokenizer.from_pretrained(Config.XLM_MODEL)
    
    # NOTE: This is a simplified version. Full implementation would need:
    # 1. Word-level timing alignment for proper boundary offset labels
    # 2. Cascaded evaluation (Stage 1 regions → Stage 2 refinement)
    # 3. IoU-F1 evaluation for boundary precision
    
    print("\n" + "=" * 70)
    print("NOTE: Full cascade implementation requires:")
    print("1. Word-level laughter timing alignment (current labels are utterance-level)")
    print("2. Proper cascade evaluation (Stage 1 → Stage 2)")
    print("3. IoU-F1 boundary metrics (current metrics are word-level F1)")
    print("=" * 70)
    
    # Placeholder for results
    results = {
        'status': 'requires_word_level_alignment',
        'note': 'Cascade architecture requires word-level laughter timing, not just utterance-level',
        'suggested_next_steps': [
            'Align word-level laughter markers from VTT [laughter] to word timestamps',
            'Compute boundary offset as (laughter_start - word_start) for each labeled word',
            'Retrain Stage 1 on word-level binary labels',
            'Retrain Stage 2 on boundary offset regression'
        ]
    }
    
    output_path = os.path.join(Config.OUTPUT_DIR, 'cascade_results.json')
    os.makedirs(Config.OUTPUT_DIR, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: {output_path}")

if __name__ == '__main__':
    main()
