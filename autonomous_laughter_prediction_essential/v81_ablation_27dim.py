#!/usr/bin/env python3
"""
V8.1 BIOSEMOTIC ABLATION STUDY - UPDATED 2026-04-27
=====================================================
14 experiments with 27-dim biosemotic features

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

            # Theory of Mind (1 cls + 3 reg)
            intent_map = {'humor_expression': 0, 'playful_banter': 1, 'storytelling': 2}
            tom_intent = torch.tensor(
                intent_map.get(ex.get('tom_speaker_intent_label', ''), 0), dtype=torch.long)
            tom_reg = torch.tensor([
                _s('tom_speaker_intent_confidence'),
                _s('tom_audience_perspective_score'),
                _s('tom_social_context_humor_score'),
            ], dtype=torch.float32)

            # Cue buckets (7)
            cue_ids = ex.get('cue_bucket_ids', [0]*7)
            cue_buckets = torch.tensor((cue_ids + [0]*7)[:7], dtype=torch.long)

            # Structural (3)
            structural = torch.tensor([
                _s('clause_boundary_ratio', 0.33),
                _s('punchline_zone_ratio', 0.33),
                _s('setup_zone_ratio', 0.33),
            ], dtype=torch.float32)

            # Linguistic (4)
            linguistic = torch.tensor([
                _s('filler_token_ratio', 0.1),
                _s('negation_ratio', 0.1),
                _s('exclamation_ratio', 0.1),
                _s('quoted_speech_ratio', 0.1),
            ], dtype=torch.float32)

            # Metadata (6)
            def _hash_cat(field, n_bins=6):
                return hash(str(ex.get(field, 'unknown'))) % n_bins
            metadata = torch.tensor([
                _hash_cat('language'),
                _hash_cat('dialect_bucket'),
                _hash_cat('laughter_type'),
                _hash_cat('gender'),
                _hash_cat('age_group'),
                _hash_cat('comedian_id'),
            ], dtype=torch.long)

            self.examples.append({
                'input_ids': input_ids,
                'attention_mask': attention_mask,
                'token_labels': torch.tensor(tok_labels, dtype=torch.long),
                'duchenne': duchenne,
                'incongruity': incongruity,
                'tom_intent': tom_intent,
                'tom_reg': tom_reg,
                'cue_buckets': cue_buckets,
                'structural': structural,
                'linguistic': linguistic,
                'metadata': metadata,
            })

            if (idx+1) % 10000 == 0:
                print(f"    {idx+1}/{len(raw)}")

        print(f"  Done: {len(self.examples)} examples")

    def __len__(self):
        return len(self.examples)

    def __getitem__(self, idx):
        return {k: v.clone() for k, v in self.examples[idx].items()}


def collate_fn(batch):
    return {k: torch.stack([b[k] for b in batch]) for k in batch[0]}


# ═══════════════════════════════════════════════════════════════
# MODEL WITH 7 BIOSEMOTIC AUXILIARY HEADS
# ═══════════════════════════════════════════════════════════════
class BiosemoticModel(nn.Module):
    def __init__(self, model_name='FacebookAI/xlm-roberta-base',
                 disable_duchenne=False, disable_incongruity=False,
                 disable_tom=False, disable_cue=False,
                 disable_structural=False, disable_linguistic=False,
                 disable_metadata=False, disable_all_aux=False,
                 dropout=0.2):  # V7 hyperparam: dropout=0.2
        super().__init__()
        self.flags = {
            'duchenne': disable_duchenne or disable_all_aux,
            'incongruity': disable_incongruity or disable_all_aux,
            'tom': disable_tom or disable_all_aux,
            'cue': disable_cue or disable_all_aux,
            'structural': disable_structural or disable_all_aux,
            'linguistic': disable_linguistic or disable_all_aux,
            'metadata': disable_metadata or disable_all_aux,
        }

        config = AutoConfig.from_pretrained(model_name)
        self.backbone = AutoModel.from_pretrained(model_name, config=config)
        hidden = config.hidden_size

        # Primary: Token-level laughter (with V7 dropout)
        self.laughter_head = nn.Sequential(
            nn.Dropout(dropout),
            nn.Linear(hidden, 256),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(256, 2)
        )

        # Aux heads (only if enabled)
        self.duchenne_head = nn.Linear(hidden, 4) if not self.flags['duchenne'] else None
        self.incongruity_head = nn.Linear(hidden, 3) if not self.flags['incongruity'] else None
        self.tom_intent_head = nn.Linear(hidden, 3) if not self.flags['tom'] else None
        self.tom_reg_head = nn.Linear(hidden, 3) if not self.flags['tom'] else None
        self.cue_head = nn.Linear(hidden, 7) if not self.flags['cue'] else None
        self.structural_head = nn.Linear(hidden, 3) if not self.flags['structural'] else None
        self.linguistic_head = nn.Linear(hidden, 4) if not self.flags['linguistic'] else None
        self.metadata_head = nn.Linear(hidden, 6) if not self.flags['metadata'] else None

    def forward(self, input_ids, attention_mask):
        out = self.backbone(input_ids=input_ids, attention_mask=attention_mask)
        seq = out.last_hidden_state
        result = {'laughter_logits': self.laughter_head(seq)}
        if self.duchenne_head:    result['duchenne'] = self.duchenne_head(seq[:, 0])
        if self.incongruity_head: result['incongruity'] = self.incongruity_head(seq[:, 0])
        if self.tom_intent_head:  result['tom_intent'] = self.tom_intent_head(seq[:, 0])
        if self.tom_reg_head:     result['tom_reg'] = self.tom_reg_head(seq[:, 0])
        if self.cue_head:        result['cue'] = self.cue_head(seq[:, 0])
        if self.structural_head:  result['structural'] = self.structural_head(seq[:, 0])
        if self.linguistic_head:  result['linguistic'] = self.linguistic_head(seq[:, 0])
        if self.metadata_head:   result['metadata'] = self.metadata_head(seq[:, 0])
        return result


# ═══════════════════════════════════════════════════════════════
# LOSS WITH LABEL SMOOTHING (V7 hyperparam)
# ═══════════════════════════════════════════════════════════════
def compute_loss(outputs, batch, pos_weight=5.0, aux_weight=0.3,
                label_smoothing=0.1):  # V7: label_smoothing=0.1
    device = outputs['laughter_logits'].device
    losses = {}

    # PRIMARY: Token-level laughter with label smoothing
    logits = outputs['laughter_logits']
    labels = batch['token_labels'].to(device)
    mask = (labels != -100)
    if mask.sum() > 0:
        cw = torch.tensor([1.0, pos_weight], device=device)
        losses['laughter'] = F.cross_entropy(
            logits.view(-1, 2)[mask.view(-1)],
            labels.view(-1)[mask.view(-1)],
            weight=cw,
            label_smoothing=label_smoothing  # V7 hyperparam
        )

    # AUX losses (MSE for regression, CE for classification)
    if 'duchenne' in outputs:
        losses['duchenne'] = F.mse_loss(outputs['duchenne'], batch['duchenne'].to(device))
    if 'incongruity' in outputs:
        losses['incongruity'] = F.mse_loss(outputs['incongruity'], batch['incongruity'].to(device))
    if 'tom_intent' in outputs:
        losses['tom_intent'] = F.cross_entropy(outputs['tom_intent'], batch['tom_intent'].to(device))
    if 'tom_reg' in outputs:
        losses['tom_reg'] = F.mse_loss(outputs['tom_reg'], batch['tom_reg'].to(device))
    if 'cue' in outputs:
        losses['cue'] = F.cross_entropy(outputs['cue'], batch['cue_buckets'].to(device))
    if 'structural' in outputs:
        losses['structural'] = F.mse_loss(outputs['structural'], batch['structural'].to(device))
    if 'linguistic' in outputs:
        losses['linguistic'] = F.mse_loss(outputs['linguistic'], batch['linguistic'].to(device))
    if 'metadata' in outputs:
        losses['metadata'] = F.cross_entropy(outputs['metadata'], batch['metadata'].to(device))

    total = losses['laughter']
    aux_keys = [k for k in losses if k != 'laughter']
    if aux_keys:
        total = total + aux_weight * sum(losses[k] for k in aux_keys) / len(aux_keys)

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
    # Convert precision/recall scalars (they're arrays for binary classification)
    return {'loss': avg_loss, 'f1': f1, 'precision': float(p[1]), 'recall': float(r[1])}


# ═══════════════════════════════════════════════════════════════
# SINGLE EXPERIMENT
# ═══════════════════════════════════════════════════════════════
def run_experiment(name, pos_weight=5.0, epochs=10, lr=2e-5,
                   batch_size=12,  # V7: batch_size=12
                   aux_weight=0.3, patience=3, unfreeze_layers=4,
                   dropout=0.2,  # V7: dropout=0.2
                   label_smoothing=0.1,  # V7: label_smoothing=0.1
                   weight_decay=0.02,  # V7: weight_decay=0.02
                   **disable_flags):
    print(f"\n{'─'*60}")
    print(f" {name}")
    print(f" pw={pos_weight} bs={batch_size} lr={lr} drop={dropout}")
    print(f" aux={aux_weight} smooth={label_smoothing} wd={weight_decay}")
    disabled = [k for k,v in disable_flags.items() if v]
    if disabled:
        print(f" Disabled: {disabled}")
    print(f"{'─'*60}")

    device = torch.device('cuda')
    tokenizer = AutoTokenizer.from_pretrained('FacebookAI/xlm-roberta-base')
    start = time.time()

    # Datasets
    train_ds = BiosemoticDataset('train.jsonl', tokenizer)
    valid_ds = BiosemoticDataset('valid.jsonl', tokenizer)
    test_ds  = BiosemoticDataset('test.jsonl', tokenizer)

    # V7 batch_size
    train_dl = DataLoader(train_ds, batch_size=batch_size, shuffle=True,
                          collate_fn=collate_fn, num_workers=2, pin_memory=True)
    valid_dl = DataLoader(valid_ds, batch_size=batch_size*2, shuffle=False,
                          collate_fn=collate_fn, num_workers=2, pin_memory=True)
    test_dl  = DataLoader(test_ds, batch_size=batch_size*2, shuffle=False,
                          collate_fn=collate_fn, num_workers=2, pin_memory=True)

    # Model
    model = BiosemoticModel(dropout=dropout, **disable_flags).to(device)

    # V7 optimizer params
    optimizer = torch.optim.AdamW([
        {'params': model.backbone.parameters(), 'lr': lr, 'weight_decay': weight_decay},
        {'params': model.laughter_head.parameters(), 'lr': lr * 5, 'weight_decay': weight_decay},
    ])

    total_steps = len(train_dl) * epochs
    warmup_steps = int(0.1 * total_steps)
    scheduler = get_linear_schedule_with_warmup(optimizer, warmup_steps, total_steps)

    best_f1 = 0.0
    best_state = None
    wait = 0

    for epoch in range(epochs):
        # Layer unfreezing (gradual)
        if epoch == 0:
            for p in model.backbone.parameters():
                p.requires_grad = False
        else:
            for p in model.backbone.parameters():
                p.requires_grad = False
            if 0 < unfreeze_layers < 12:
                for layer in model.backbone.encoder.layer[-unfreeze_layers:]:
                    for p in layer.parameters():
                        p.requires_grad = True
            elif unfreeze_layers >= 12:
                for p in model.backbone.parameters():
                    p.requires_grad = True
        for p in model.laughter_head.parameters():
            p.requires_grad = True

        # Train
        model.train()
        epoch_loss = 0
        optimizer.zero_grad()
        for step, batch in enumerate(train_dl):
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            outputs = model(input_ids, attention_mask)
            loss, _ = compute_loss(outputs, batch, pos_weight, aux_weight, label_smoothing)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            scheduler.step()
            optimizer.zero_grad()
            epoch_loss += loss.item()

        # Validate
        val = evaluate(model, valid_dl, device, pos_weight, aux_weight, label_smoothing)
        improved = val['f1'] > best_f1
        if improved:
            best_f1 = val['f1']
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
            wait = 0
        else:
            wait += 1

        elapsed = (time.time() - start) / 60
        print(f"  E{epoch+1:2d}/{epochs} loss={epoch_loss/len(train_dl):.4f} "
              f"VaF1={val['f1']:.4f} best={best_f1:.4f} "
              f"{'★' if improved else ''} [{elapsed:.1f}m]", flush=True)

        if wait >= patience:
            print(f"  Early stop at epoch {epoch+1}")
            break

    # Test with best
    if best_state:
        model.load_state_dict(best_state)
    test = evaluate(model, test_dl, device, pos_weight, aux_weight, label_smoothing)

    print(f"  TEST: F1={test['f1']:.4f} P={test['precision']:.4f} R={test['recall']:.4f}")

    # Cleanup
    del model, best_state, train_ds, valid_ds, test_ds
    gc.collect()
    torch.cuda.empty_cache()

    return {
        'name': name,
        'val_f1': best_f1,
        'test_f1': test['f1'],
        'test_precision': test['precision'],
        'test_recall': test['recall'],
        'time_min': round((time.time() - start)/60),
        'disabled': disabled,
        'config': {
            'pos_weight': pos_weight,
            'batch_size': batch_size,
            'lr': lr,
            'dropout': dropout,
            'label_smoothing': label_smoothing,
            'weight_decay': weight_decay,
            'aux_weight': aux_weight
        }
    }


# ═══════════════════════════════════════════════════════════════
# INCREMENTAL SAVE - AFTER EVERY EXPERIMENT
# ═══════════════════════════════════════════════════════════════
ALL_RESULTS = []
RESULTS_FILE = 'v81_ablation_results.json'

def save_incremental(result, num):
    """Save after EVERY experiment - prevents data loss on disconnect"""
    ALL_RESULTS.append(result)
    with open(RESULTS_FILE, 'w') as f:
        json.dump({
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_experiments': 14,
            'completed': len(ALL_RESULTS),
            'results': ALL_RESULTS
        }, f, indent=2)
    try:
        from google.colab import drive
        drive.mount('/content/drive', force_remount=True)
        with open('/content/drive/MyDrive/' + RESULTS_FILE, 'w') as f:
            json.dump({
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'total_experiments': 14,
                'completed': len(ALL_RESULTS),
                'results': ALL_RESULTS
            }, f, indent=2)
        print(f"  ✓ Saved to Drive + local ({len(ALL_RESULTS)}/14)")
    except:
        print(f"  ✓ Saved locally ({len(ALL_RESULTS)}/14)")


# ═══════════════════════════════════════════════════════════════
# RUN ALL 14 EXPERIMENTS
# ═══════════════════════════════════════════════════════════════
print(f"\n{'='*70}")
print(f" V8.1 BIOSEMOTIC ABLATION")
print(f" {n_train:,} examples, 27 biosemotic dims")
print(f" V7 hyperparams: dropout=0.2, bs=12, label_smoothing=0.1, wd=0.02")
print(f"{'='*70}\n")

t0 = time.time()

experiments = [
    # PHASE A: Baselines (no aux tasks)
    ("A1_baseline_pw5", {"pos_weight": 5.0, "disable_all_aux": True}),
    ("A2_baseline_pw3", {"pos_weight": 3.0, "disable_all_aux": True}),
    # PHASE B: Full biosemotic model
    ("B1_full27dim_aw03", {"pos_weight": 5.0, "aux_weight": 0.3}),
    ("B2_full27dim_aw05", {"pos_weight": 5.0, "aux_weight": 0.5}),
    # PHASE C: Single-dimension ablation
    ("C1_no_duchenne", {"disable_duchenne": True}),
    ("C2_no_incongruity", {"disable_incongruity": True}),
    ("C3_no_tom", {"disable_tom": True}),
    ("C4_no_cue", {"disable_cue": True}),
    ("C5_no_structural", {"disable_structural": True}),
    ("C6_no_linguistic", {"disable_linguistic": True}),
    ("C7_no_metadata", {"disable_metadata": True}),
    # PHASE D: Group ablation
    ("D1_core_trio_only", {"disable_cue": True, "disable_structural": True, "disable_linguistic": True, "disable_metadata": True}),
    ("D2_no_cognitive", {"disable_duchenne": True, "disable_incongruity": True, "disable_tom": True}),
    ("D3_surface_only", {"disable_duchenne": True, "disable_incongruity": True, "disable_tom": True}),
]

total = len(experiments)
print(f"Running {total} experiments...\n")

for i, (name, kwargs) in enumerate(experiments, 1):
    result = run_experiment(name, **kwargs)
    save_incremental(result, i)
    
    elapsed = (time.time() - t0) / 60
    best_so_far = max(r['val_f1'] for r in ALL_RESULTS)
    print(f"  → {name}: ValF1={result['val_f1']:.4f} | Best: {best_so_far:.4f} | Time: {elapsed:.1f}m")

total_time = (time.time() - t0) / 60

# ═══════════════════════════════════════════════════════════════
# FINAL RESULTS
# ═══════════════════════════════════════════════════════════════
print(f"\n{'='*70}")
print(f" FINAL RESULTS — {len(ALL_RESULTS)} experiments in {total_time:.0f} min")
print(f"{'='*70}")

ranked = sorted(ALL_RESULTS, key=lambda r: r['val_f1'], reverse=True)
print(f"\n{'Rank':<5} {'Name':<22} {'ValF1':>7} {'TeF1':>7} {'Prec':>7} {'Rec':>7} {'Time':>6}")
print('─'*80)
for i, r in enumerate(ranked, 1):
    dis = ','.join(r.get('disabled',[])) or '—'
    print(f"{i:<5} {r['name']:<22} {r['val_f1']:>7.4f} {r['test_f1']:>7.4f} "
          f"{r['test_precision']:>7.4f} {r['test_recall']:>7.4f} {r['time_min']:>5}m")

# Key insights
baselines = [r for r in ALL_RESULTS if 'baseline' in r['name']]
full = [r for r in ALL_RESULTS if 'full27dim' in r['name']]
ablations = [r for r in ALL_RESULTS if r['name'].startswith('C')]

if baselines and full:
    b = max(baselines, key=lambda r: r['val_f1'])
    f = max(full, key=lambda r: r['val_f1'])
    delta = f['val_f1'] - b['val_f1']
    print(f"\n📊 BASELINE vs FULL BIOSEMOTIC:")
    print(f"   Baseline:   {b['name']} ValF1={b['val_f1']:.4f}")
    print(f"   Full 27dim: {f['name']} ValF1={f['val_f1']:.4f}")
    print(f"   Δ = {delta:+.4f} {'↑ BIOSEMOTIC HELPS!' if delta > 0 else '↓ No improvement'}")

if ablations:
    base_f1 = b['val_f1'] if baselines else 0
    print(f"\n🔬 DIMENSION IMPORTANCE:")
    for a in sorted(ablations, key=lambda r: r['val_f1']):
        impact = base_f1 - a['val_f1'] if base_f1 else 0
        dim = '_'.join(a['name'].split('_')[1:])
        print(f"   Remove {dim:<18}: F1={a['val_f1']:.4f} (Δ={impact:+.4f})")

best = ranked[0] if ranked else None
if best:
    print(f"\n★ BEST: {best['name']} ValF1={best['val_f1']:.4f}")

print(f"\n💾 All results saved to {RESULTS_FILE}")
