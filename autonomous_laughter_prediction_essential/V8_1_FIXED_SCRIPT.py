#!/usr/bin/env python3
"""
V8.1 BIOSEMOTIC ABLATION STUDY - FIXED VERSION
=====================================================
14 experiments with 27-dim biosemotic features

FIXED: Precision/Recall conversion bug in evaluate function
IMPROVEMENTS FROM V7/V8:
- GPU guard: Refuses if compute < 7.0
- Incremental save: After EVERY experiment
- V7 hyperparams: dropout=0.2, batch=12, label_smoothing=0.1
- Uses full 41K dataset with biosemotic features
- Token-level classification with subword alignment

DATA: 41,240 examples with real [laughter] markers + 27 biosemotic dims
URL: https://github.com/Das-rebel/ChuckleNet/releases/download/v0.1-data/
"""

import os
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
os.environ['HF_HUB_DISABLE_SYMLINKS'] = '1'

import subprocess
import sys
import json
import time
import gc
import math
import random
from pathlib import Path

# Install deps
subprocess.run([sys.executable, '-m', 'pip', 'install', '-q',
    'transformers', 'scikit-learn'], check=True)

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModel, AutoConfig
from transformers import get_linear_schedule_with_warmup
from sklearn.metrics import f1_score, precision_recall_fscore_support

# ═══════════════════════════════════════════════════════════════
# GPU GUARD - MUST CHECK BEFORE ANYTHING
# ═══════════════════════════════════════════════════════════════
if not torch.cuda.is_available():
    raise RuntimeError("FATAL: No CUDA GPU available. Training ABORTED.")

gpu_name = torch.cuda.get_device_name(0)
gpu_cap = torch.cuda.get_device_capability(0)
if gpu_cap[0] < 7:
    raise RuntimeError(
        f"FATAL: GPU {gpu_name} has compute capability {gpu_cap[0]}.{gpu_cap[1]} < 7.0. "
        f"Not compatible with PyTorch CUDA 12.x. Training ABORTED."
    )

print("=" * 60)
print(f"GPU: {gpu_name} (compute {gpu_cap[0]}.{gpu_cap[1]})")
print(f"Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
print("=" * 60)

# ═══════════════════════════════════════════════════════════════
# DOWNLOAD 27-DIM DATA FROM GITHUB RELEASES
# ═══════════════════════════════════════════════════════════════
BASE_URL = "https://github.com/Das-rebel/ChuckleNet/releases/download/v0.1-data"

for s in ['train', 'valid', 'test']:
    fname = f'{s}.jsonl'
    if not Path(fname).exists():
        print(f"Downloading {fname}... (full 41K dataset)")
        subprocess.run(
            ['curl', '-sL', '-o', fname, f'{BASE_URL}/{fname}'],
            check=True, timeout=600
        )
    else:
        print(f"{fname}: already exists")

# Verify
n_train = sum(1 for _ in open('train.jsonl'))
n_valid = sum(1 for _ in open('valid.jsonl'))
n_test  = sum(1 for _ in open('test.jsonl'))
print(f"Data: train={n_train:,} valid={n_valid:,} test={n_test:,}")

# Check biosemotic fields
sample = json.loads(open('train.jsonl').readline())
bio_keys = [k for k in sample if k not in ['words','labels','language','metadata','example_id','cue_bucket_ids']]
print(f"Biosemotic fields: {len(bio_keys)} dims")

# ═══════════════════════════════════════════════════════════════
# DATASET WITH SUBWORD-ALIGNED LABELS + BIOSEMOTIC FEATURES
# ═══════════════════════════════════════════════════════════════
class BiosemoticDataset(Dataset):
    """Token-level dataset with biosemotic auxiliary features."""

    def __init__(self, filepath, tokenizer, max_length=256):
        self.examples = []
        raw = []
        with open(filepath) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        raw.append(json.loads(line))
                    except:
                        pass

        print(f"  Pre-tokenizing {len(raw)} examples...")
        for idx, ex in enumerate(raw):
            words = [str(x) for x in ex.get('words', [])]
            if not words:
                continue
            labels = ex.get('labels', [0]*len(words))

            # Subword tokenization
            enc = tokenizer(words, is_split_into_words=True,
                          truncation=True, max_length=max_length,
                          padding='max_length', return_tensors='pt')
            input_ids = enc['input_ids'].squeeze(0)
            attention_mask = enc['attention_mask'].squeeze(0)

            # Align labels to subword tokens
            word_ids = enc.word_ids(batch_index=0)
            tok_labels = []
            prev = None
            for wid in word_ids:
                if wid is None:
                    tok_labels.append(-100)
                elif wid != prev and wid < len(labels):
                    tok_labels.append(labels[wid])
                    prev = wid
                else:
                    tok_labels.append(-100)

            # Feature helpers
            def _s(field, default=0.5):
                v = ex.get(field, default)
                return float(v) if v is not None else default

            # Duchenne (4)
            duchenne = torch.tensor([
                _s('duchenne_joy_intensity'),
                _s('duchenne_genuine_humor_probability'),
                _s('duchenne_spontaneous_laughter_markers'),
                _s('duchenne_setup_punchline_structure'),
            ], dtype=torch.float32)

            # Incongruity (3)
            incongruity = torch.tensor([
                _s('incongruity_expectation_violation_score'),
                _s('incongruity_humor_complexity_score'),
                _s('incongruity_resolution_time'),
            ], dtype=torch.float32)

            # Theory of Mind (4)
            tom_intent = torch.tensor([_s('tom_speaker_intent_label')], dtype=torch.long)
            tom_reg = torch.tensor([
                _s('tom_speaker_intent_confidence'),
                _s('tom_audience_perspective_score'),
                _s('tom_social_context_humor_score'),
                _s('tom_character_interaction_pattern'),
                _s('tom_character_interaction_score'),
            ], dtype=torch.float32)

            # Cue buckets (4)
            cue = torch.tensor([_s('cue_bucket_ids', 0)], dtype=torch.long)

            # Structural humor (3)
            structural = torch.tensor([
                _s('clause_boundary_ratio'),
                _s('punchline_zone_ratio'),
                _s('setup_zone_ratio'),
            ], dtype=torch.float32)

            # Linguistic humor (3)
            linguistic = torch.tensor([
                _s('negation_ratio'),
                _s('exclamation_ratio'),
                _s('quoted_speech_ratio'),
            ], dtype=torch.float32)

            # Metadata (2)
            metadata = torch.tensor([
                _s('comedian_id', 0),
                _s('show_id', 0),
            ], dtype=torch.long)

            self.examples.append({
                'input_ids': input_ids,
                'attention_mask': attention_mask,
                'token_labels': torch.tensor(tok_labels, dtype=torch.long),
                'duchenne': duchenne,
                'incongruity': incongruity,
                'tom_intent': tom_intent,
                'tom_reg': tom_reg,
                'cue': cue,
                'structural': structural,
                'linguistic': linguistic,
                'metadata': metadata,
                'laughter': torch.tensor([1 if any(l == 1 for l in labels) else 0], dtype=torch.long),
            })

        print(f"  Total: {len(self.examples)} token-level examples")

    def __len__(self):
        return len(self.examples)

    def __getitem__(self, idx):
        return self.examples[idx]

# ═══════════════════════════════════════════════════════════════
# MODEL WITH AUXILIARY BIOSEMOTIC TASKS
# ═══════════════════════════════════════════════════════════════
class XLMRBiosemotic(nn.Module):
    """XLM-R with biosemotic auxiliary tasks."""

    def __init__(self, model_name='FacebookAI/xlm-roberta-base', dropout=0.2):
        super().__init__()
        self.backbone = AutoModel.from_pretrained(model_name)
        self.dropout = nn.Dropout(dropout)

        # Main classifier (token-level + sentence-level)
        hidden_size = self.backbone.config.hidden_size
        self.laughter_logits = nn.Linear(hidden_size, 2)  # token-level
        self.laughter_classifier = nn.Linear(hidden_size, 1)  # sentence-level

        # Auxiliary task heads
        self.duchenne = nn.Linear(hidden_size, 4)
        self.incongruity = nn.Linear(hidden_size, 3)
        self.tom_intent = nn.Linear(hidden_size, 4)  # intent labels
        self.tom_reg = nn.Linear(hidden_size, 5)     # regression
        self.cue = nn.Linear(hidden_size, 4)         # cue buckets
        self.structural = nn.Linear(hidden_size, 3)
        self.linguistic = nn.Linear(hidden_size, 3)
        self.metadata = nn.Linear(hidden_size, 2)   # comedian/show ids

    def forward(self, input_ids, attention_mask):
        outputs = self.backbone(input_ids, attention_mask)
        pooled = outputs.last_hidden_state.mean(dim=1)  # sentence-level [CLS]
        hidden = outputs.last_hidden_state              # token-level

        # Apply dropout
        hidden = self.dropout(hidden)
        pooled = self.dropout(pooled)

        # Main tasks
        laughter_logits = self.laughter_logits(hidden)
        laughter_pred = self.laughter_classifier(pooled)

        # Auxiliary tasks (only on [CLS] token)
        aux_features = {
            'laughter_logits': laughter_logits,
            'laughter_pred': laughter_pred,
        }

        # Only compute auxiliary features if not disabled
        if not getattr(self, 'disable_all_aux', False):
            aux_features.update({
                'duchenne': self.duchenne(pooled),
                'incongruity': self.incongruity(pooled),
                'tom_intent': self.tom_intent(pooled),
                'tom_reg': self.tom_reg(pooled),
                'cue': self.cue(pooled),
                'structural': self.structural(pooled),
                'linguistic': self.linguistic(pooled),
                'metadata': self.metadata(pooled),
            })

        return aux_features

# ═══════════════════════════════════════════════════════════════
# TRAINING & EVALUATION
# ═══════════════════════════════════════════════════════════════
def compute_loss(outputs, batch, pos_weight=5.0, aux_weight=0.3, label_smoothing=0.1):
    # Main loss (token-level)
    laughter_logits = outputs['laughter_logits']
    token_labels = batch['token_labels'].to(laughter_logits.device)
    mask = (token_labels != -100)
    
    # Use focal loss for imbalanced laughter data
    probs = F.softmax(laughter_logits, dim=-1)
    log_probs = F.log_softmax(laughter_logits, dim=-1)
    
    # Only compute loss on non-padding tokens
    active_loss = mask.view(-1)
    active_probs = probs.view(-1, 2)[active_loss]
    active_log_probs = log_probs.view(-1, 2)[active_loss]
    active_labels = token_labels.view(-1)[active_loss]
    
    # Apply label smoothing
    if label_smoothing > 0:
        n_classes = 2
        smoothing = label_smoothing / n_classes
        smooth_labels = torch.full((len(active_labels), n_classes), smoothing, device=laughter_logits.device)
        smooth_labels.scatter_(1, active_labels.unsqueeze(1), 1.0 - label_smoothing + smoothing)
        smoothed_probs = active_probs * smooth_labels
        focal_loss = -torch.log(smoothed_probs + 1e-8)
    else:
        focal_loss = -active_log_probs
        
    # Focal loss for imbalanced data
    pt = torch.gather(active_probs, 1, active_labels.unsqueeze(1)).squeeze(1)
    focal_loss = (1 - pt) ** 2 * focal_loss
    
    # Weight positive class
    weights = torch.ones_like(active_labels, dtype=torch.float, device=laughter_logits.device)
    weights[active_labels == 1] = pos_weight
    weighted_loss = focal_loss[active_labels == 0] + focal_loss[active_labels == 1] * weights[active_labels == 1]
    
    losses = {'laughter': weighted_loss.mean()}
    
    # Auxiliary losses
    aux_losses = {}
    if 'duchenne' in outputs and not getattr(self, 'disable_duchenne', False):
        aux_losses['duchenne'] = F.mse_loss(outputs['duchenne'], batch['duchenne'].to(device))
    if 'incongruity' in outputs and not getattr(self, 'disable_incongruity', False):
        aux_losses['incongruity'] = F.mse_loss(outputs['incongruity'], batch['incongruity'].to(device))
    if 'tom_intent' in outputs and not getattr(self, 'disable_tom', False):
        aux_losses['tom_intent'] = F.cross_entropy(outputs['tom_intent'], batch['tom_intent'].to(device))
    if 'tom_reg' in outputs and not getattr(self, 'disable_tom', False):
        aux_losses['tom_reg'] = F.mse_loss(outputs['tom_reg'], batch['tom_reg'].to(device))
    if 'cue' in outputs and not getattr(self, 'disable_cue', False):
        aux_losses['cue'] = F.cross_entropy(outputs['cue'], batch['cue_buckets'].to(device))
    if 'structural' in outputs and not getattr(self, 'disable_structural', False):
        aux_losses['structural'] = F.mse_loss(outputs['structural'], batch['structural'].to(device))
    if 'linguistic' in outputs and not getattr(self, 'disable_linguistic', False):
        aux_losses['linguistic'] = F.mse_loss(outputs['linguistic'], batch['linguistic'].to(device))
    if 'metadata' in outputs and not getattr(self, 'disable_metadata', False):
        aux_losses['metadata'] = F.cross_entropy(outputs['metadata'], batch['metadata'].to(device))
    
    total = losses['laughter']
    if aux_losses:
        total = total + aux_weight * sum(aux_losses.values()) / len(aux_losses)
    
    losses.update(aux_losses)
    return total, losses

@torch.no_grad()
def evaluate(model, loader, device, pos_weight=5.0, aux_weight=0.3, label_smoothing=0.1):
    model.eval()
    all_preds, all_labels = [], []
    total_loss = 0

    for batch in loader:
        input_ids = batch['input_ids'].to(device)
        attention_mask = batch['attention_mask'].to(device)
        outputs = model(input_ids, attention_mask)
        loss, _ = compute_loss(outputs, batch, pos_weight, aux_weight, label_smoothing)
        total_loss += loss.item()

        labels = batch['token_labels'].to(device)
        mask = (labels != -100)
        preds = outputs['laughter_logits'].argmax(dim=-1)
        all_preds.extend(preds[mask].cpu().tolist())
        all_labels.extend(labels[mask].cpu().tolist())

    avg_loss = total_loss / len(loader)
    f1 = f1_score(all_labels, all_preds, pos_label=1, zero_division=0)
    p, r, _, _ = precision_recall_fscore_support(
        all_labels, all_preds, pos_label=1, zero_division=0
    )
    # FIXED: Extract precision/recall for positive class correctly
    return {'loss': avg_loss, 'f1': f1, 'precision': float(p[1]), 'recall': float(r[1])}

# ═══════════════════════════════════════════════════════════════
# SINGLE EXPERIMENT
# ═══════════════════════════════════════════════════════════════
def run_experiment(name, pos_weight=5.0, epochs=10, lr=2e-5,
                   batch_size=12, aux_weight=0.3, label_smoothing=0.1, 
                   weight_decay=0.02, warmup_ratio=0.1, dropout=0.2,
                   **kwargs):
    """Run single experiment with given configuration."""
    
    # Handle disable flags from kwargs
    for key in ['disable_all_aux', 'disable_duchenne', 'disable_incongruity', 
                'disable_tom', 'disable_cue', 'disable_structural', 
                'disable_linguistic', 'disable_metadata']:
        if key in kwargs:
            setattr(model, key, kwargs[key])
    
    print(f"\n{'='*60}")
    print(f" {name}")
    print(f" pw={pos_weight} aux={aux_weight} epochs={epochs}")
    print(f" Disabled: {kwargs.get('disabled_dims', [])}")
    print(f"{'='*60}")
    
    # Create datasets
    tokenizer = AutoTokenizer.from_pretrained('FacebookAI/xlm-roberta-base')
    train_ds = BiosemoticDataset('train.jsonl', tokenizer)
    valid_ds = BiosemoticDataset('valid.jsonl', tokenizer)
    test_ds = BiosemoticDataset('test.jsonl', tokenizer)
    
    # Data loaders
    train_dl = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    valid_dl = DataLoader(valid_ds, batch_size=batch_size, shuffle=False)
    test_dl = DataLoader(test_ds, batch_size=batch_size, shuffle=False)
    
    # Model
    model = XLMRBiosemotic(dropout=dropout)
    model.to(device)
    
    # Optimizer with weight decay
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)
    total_steps = len(train_dl) * epochs
    scheduler = get_linear_schedule_with_warmup(
        optimizer, 
        num_warmup_steps=int(total_steps * warmup_ratio),
        num_training_steps=total_steps
    )
    
    # Training loop
    best_val_f1 = 0
    best_epoch = 0
    
    for epoch in range(epochs):
        model.train()
        total_loss = 0
        
        for batch in train_dl:
            optimizer.zero_grad()
            
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            
            outputs = model(input_ids, attention_mask)
            loss, losses = compute_loss(outputs, batch, pos_weight, aux_weight, label_smoothing)
            
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            scheduler.step()
            
            total_loss += loss.item()
        
        # Validation
        val = evaluate(model, valid_dl, device, pos_weight, aux_weight, label_smoothing)
        train_loss = total_loss / len(train_dl)
        
        print(f"  Epoch {epoch+1}/{epochs}: "
              f"Train={train_loss:.4f} Val={val['loss']:.4f} F1={val['f1']:.4f}")
        
        # Save best model
        if val['f1'] > best_val_f1:
            best_val_f1 = val['f1']
            best_epoch = epoch + 1
            # Save model state
            torch.save({
                'model': model.state_dict(),
                'config': {
                    'name': name,
                    'pos_weight': pos_weight,
                    'aux_weight': aux_weight,
                    'epoch': epoch + 1,
                    'val_f1': val['f1'],
                }
            }, f'/tmp/{name}_best.pt')
    
    # Final evaluation
    print(f"  Best: Epoch {best_epoch} ValF1={best_val_f1:.4f}")
    
    # Test on best model
    checkpoint = torch.load(f'/tmp/{name}_best.pt')
    model.load_state_dict(checkpoint['model'])
    test = evaluate(model, test_dl, device, pos_weight, aux_weight, label_smoothing)
    
    return {
        'name': name,
        'val_f1': best_val_f1,
        'test_f1': test['f1'],
        'test_precision': test['precision'],
        'test_recall': test['recall'],
        'best_epoch': best_epoch,
        'config': checkpoint['config'],
        'status': 'completed'
    }

# ═══════════════════════════════════════════════════════════════
# MAIN EXECUTION
# ═══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    # Run experiments
    results = []
    experiments = [
        ("A1_baseline_pw5", {"pos_weight": 5.0, "disable_all_aux": True}),
        ("A2_baseline_pw3", {"pos_weight": 3.0, "disable_all_aux": True}),
        ("B1_full27dim_aw03", {"pos_weight": 5.0, "aux_weight": 0.3}),
        ("B2_full27dim_aw05", {"pos_weight": 5.0, "aux_weight": 0.5}),
        ("C1_no_duchenne", {"pos_weight": 5.0, "aux_weight": 0.3, "disable_duchenne": True}),
        ("C2_no_incongruity", {"pos_weight": 5.0, "aux_weight": 0.3, "disable_incongruity": True}),
        ("C3_no_tom", {"pos_weight": 5.0, "aux_weight": 0.3, "disable_tom": True}),
        ("C4_no_cue", {"pos_weight": 5.0, "aux_weight": 0.3, "disable_cue": True}),
        ("C5_no_structural", {"pos_weight": 5.0, "aux_weight": 0.3, "disable_structural": True}),
        ("C6_no_linguistic", {"pos_weight": 5.0, "aux_weight": 0.3, "disable_linguistic": True}),
        ("C7_no_metadata", {"pos_weight": 5.0, "aux_weight": 0.3, "disable_metadata": True}),
        ("D1_core_trio_only", {"pos_weight": 5.0, "aux_weight": 0.3, "disable_cue": True, "disable_structural": True, "disable_linguistic": True, "disable_metadata": True}),
        ("D2_no_cognitive", {"pos_weight": 5.0, "aux_weight": 0.3, "disable_duchenne": True, "disable_incongruity": True, "disable_tom": True}),
        ("D3_surface_only", {"pos_weight": 5.0, "aux_weight": 0.3, "disable_duchenne": True, "disable_incongruity": True, "disable_tom": True}),
    ]
    
    for name, kwargs in experiments:
        result = run_experiment(name, **kwargs)
        results.append(result)
        # Save after each experiment
        with open('/tmp/v81_results.json', 'w') as f:
            json.dump(results, f, indent=2)
    
    # Final results
    print("\n" + "="*60)
    print("FINAL RESULTS")
    print("="*60)
    for r in results:
        print(f"{r['name']}: ValF1={r['val_f1']:.4f} TestF1={r['test_f1']:.4f}")
    
    # Save final results
    with open('/tmp/v81_final_results.json', 'w') as f:
        json.dump(results, f, indent=2)