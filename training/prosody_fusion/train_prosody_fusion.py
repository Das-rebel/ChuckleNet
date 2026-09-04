#!/usr/bin/env python3
"""
Track B: Late Fusion of Sentence Embeddings + Prosody (21-dim)
Architecture: SBERT frozen → embedding(768d) + prosody(21d) → MLP(789→256→64→2)

This script trains ONLY the MLP on pre-extracted embeddings.
Since embeddings are cached, training is fast (~seconds per epoch).
"""
import json, os, sys, time, torch, torch.nn as nn, numpy as np

# ============ CONFIG ============
DATA_DIR = '/Users/Subho/autonomous_laughter_prediction/training/prosody_fusion_data'
EMBED_DIR = '/Users/Subho/autonomous_laughter_prediction/training/prosody_fusion_embeddings'
OUT_DIR = '/Users/Subho/autonomous_laughter_prediction/training/prosody_fusion_results'
EPOCHS = 50
BATCH_SIZE = 128
LR = 5e-4
WEIGHT_DECAY = 0.01
HIDDEN = 256
DROPOUT = 0.3
SEED = 42
# Prosody: 21-dim, normalized [0,1]
PROSODY_DIM = 21
EMBED_DIM = 768  # SBERT embedding dim
# ================================

os.makedirs(OUT_DIR, exist_ok=True)
torch.manual_seed(SEED)
np.random.seed(SEED)

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Device: {device}")

# ============ LOAD CACHED EMBEDDINGS ============
print("\nLoading pre-extracted embeddings...")
data = {}
for split in ['train', 'valid', 'test']:
    npz = np.load(os.path.join(EMBED_DIR, f'{split}_embeddings.npz'))
    data[split] = {
        'embeddings': torch.tensor(npz['embeddings'], dtype=torch.float32),
        'prosody': torch.tensor(npz['prosody'], dtype=torch.float32),
        'labels': torch.tensor(npz['labels'], dtype=torch.long),
    }
    print(f"  {split}: embeddings={data[split]['embeddings'].shape}, "
          f"prosody={data[split]['prosody'].shape}, "
          f"labels={data[split]['labels'].shape}")

train_emb = data['train']['embeddings'].to(device)
train_pros = data['train']['prosody'].to(device)
train_lbl = data['train']['labels'].to(device)
val_emb = data['valid']['embeddings'].to(device)
val_pros = data['valid']['prosody'].to(device)
val_lbl = data['valid']['labels'].to(device)
test_emb = data['test']['embeddings'].to(device)
test_pros = data['test']['prosody'].to(device)
test_lbl = data['test']['labels'].to(device)

n_train = len(train_emb)
n_val = len(val_emb)
n_test = len(test_emb)

# Class weight
pos_count = (train_lbl == 1).sum().item()
neg_count = (train_lbl == 0).sum().item()
pos_weight = neg_count / pos_count
print(f"\nClass balance: {neg_count} neg / {pos_count} pos (ratio={pos_weight:.2f})")

# ============ MODEL ============
class LateFusionMLP(nn.Module):
    def __init__(self, embed_dim=768, prosody_dim=21, hidden=256, dropout=0.3):
        super().__init__()
        total_dim = embed_dim + prosody_dim  # 789
        
        self.prosody_norm = nn.LayerNorm(prosody_dim)  # normalize prosody
        self.classifier = nn.Sequential(
            nn.Dropout(dropout),
            nn.Linear(total_dim, hidden),
            nn.ReLU(),
            nn.Dropout(dropout * 0.7),
            nn.Linear(hidden, 64),
            nn.ReLU(),
            nn.Linear(64, 2)
        )
        
    def forward(self, embeddings, prosody):
        prosody_norm = self.prosody_norm(prosody)
        fused = torch.cat([embeddings, prosody_norm], dim=1)
        return self.classifier(fused)

model = LateFusionMLP(EMBED_DIM, PROSODY_DIM, HIDDEN, DROPOUT).to(device)
optimizer = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=WEIGHT_DECAY)
scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=EPOCHS, eta_min=LR * 0.1)

# Class-weighted BCE
pos_weight_tensor = torch.tensor([1.0, min(pos_weight, 5.0)]).to(device)  # cap at 5
criterion = nn.CrossEntropyLoss(weight=pos_weight_tensor)

print(f"\nModel: LateFusionMLP({EMBED_DIM}+{PROSODY_DIM} → {HIDDEN} → 64 → 2)")
print(f"  Prosody norm: LayerNorm({PROSODY_DIM})")
print(f"  Dropout: {DROPOUT}")
print(f"  LR: {LR}, WD: {WEIGHT_DECAY}, Pos weight cap: {min(pos_weight, 5.0):.1f}")
print(f"  Trainable params: {sum(p.numel() for p in model.parameters() if p.requires_grad):,}")

# ============ TRAINING ============
def compute_metrics(preds, labels):
    tp = ((preds == 1) & (labels == 1)).sum().item()
    fp = ((preds == 1) & (labels == 0)).sum().item()
    fn = ((preds == 0) & (labels == 1)).sum().item()
    tn = ((preds == 0) & (labels == 0)).sum().item()
    p = tp / (tp + fp + 1e-8)
    r = tp / (tp + fn + 1e-8)
    f1 = 2 * p * r / (p + r + 1e-8)
    acc = (tp + tn) / (tp + fp + fn + tn + 1e-8)
    return {'f1': f1, 'precision': p, 'recall': r, 'accuracy': acc, 
            'tp': tp, 'fp': fp, 'fn': fn, 'tn': tn}

best_val_f1 = 0
best_state = None
history = []

print(f"\nTraining: {EPOCHS} epochs, batch_size={BATCH_SIZE}")

for epoch in range(1, EPOCHS + 1):
    t0 = time.time()
    
    # Shuffle
    perm = torch.randperm(n_train)
    train_emb_shuf = train_emb[perm]
    train_pros_shuf = train_pros[perm]
    train_lbl_shuf = train_lbl[perm]
    
    # Train
    model.train()
    train_preds, train_labels = [], []
    n_batches = (n_train + BATCH_SIZE - 1) // BATCH_SIZE
    
    for i in range(n_batches):
        start = i * BATCH_SIZE
        end = min(start + BATCH_SIZE, n_train)
        emb_batch = train_emb_shuf[start:end]
        pros_batch = train_pros_shuf[start:end]
        lbl_batch = train_lbl_shuf[start:end]
        
        optimizer.zero_grad()
        logits = model(emb_batch, pros_batch)
        loss = criterion(logits, lbl_batch)
        loss.backward()
        optimizer.step()
        
        preds = logits.argmax(dim=1).cpu().numpy()
        train_preds.extend(preds)
        train_labels.extend(lbl_batch.cpu().numpy())
    
    scheduler.step()
    train_metrics = compute_metrics(np.array(train_preds), np.array(train_labels))
    
    # Validate
    model.eval()
    val_preds, val_labels = [], []
    with torch.no_grad():
        for i in range(0, n_val, BATCH_SIZE):
            emb_batch = val_emb[i:i+BATCH_SIZE]
            pros_batch = val_pros[i:i+BATCH_SIZE]
            lbl_batch = val_lbl[i:i+BATCH_SIZE]
            logits = model(emb_batch, pros_batch)
            preds = logits.argmax(dim=1).cpu().numpy()
            val_preds.extend(preds)
            val_labels.extend(lbl_batch.cpu().numpy())
    
    val_metrics = compute_metrics(np.array(val_preds), np.array(val_labels))
    elapsed = time.time() - t0
    gap = train_metrics['f1'] - val_metrics['f1']
    
    lr_now = optimizer.param_groups[0]['lr']
    marker = " ★" if val_metrics['f1'] > best_val_f1 else ""
    print(f"  Epoch {epoch:2d} | Train F1={train_metrics['f1']:.4f} P={train_metrics['precision']:.4f} R={train_metrics['recall']:.4f} | "
          f"Val F1={val_metrics['f1']:.4f} P={val_metrics['precision']:.4f} R={val_metrics['recall']:.4f} | "
          f"Gap={gap:.3f} | LR={lr_now:.2e} | {elapsed:.1f}s{marker}")
    
    history.append({'epoch': epoch, 'train': train_metrics, 'val': val_metrics, 'lr': lr_now})
    
    if val_metrics['f1'] > best_val_f1:
        best_val_f1 = val_metrics['f1']
        best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}

# ============ TEST EVALUATION ============
print(f"\nBest val F1: {best_val_f1:.4f}")
if best_state:
    model.load_state_dict(best_state)

model.eval()
test_preds, test_labels = [], []
with torch.no_grad():
    for i in range(0, n_test, BATCH_SIZE):
        emb_batch = test_emb[i:i+BATCH_SIZE]
        pros_batch = test_pros[i:i+BATCH_SIZE]
        lbl_batch = test_lbl[i:i+BATCH_SIZE]
        logits = model(emb_batch, pros_batch)
        preds = logits.argmax(dim=1).cpu().numpy()
        test_preds.extend(preds)
        test_labels.extend(lbl_batch.cpu().numpy())

test_metrics = compute_metrics(np.array(test_preds), np.array(test_labels))
print(f"\n{'='*60}")
print(f"TEST SET (held-out comedians: Bill Burr, Dave Chappelle, Russell Peters)")
print(f"  F1={test_metrics['f1']:.4f} P={test_metrics['precision']:.4f} R={test_metrics['recall']:.4f}")
print(f"  Accuracy={test_metrics['accuracy']:.4f}")
print(f"  TP={test_metrics['tp']} FP={test_metrics['fp']} FN={test_metrics['fn']} TN={test_metrics['tn']}")
print(f"{'='*60}")

# Save
torch.save(best_state, os.path.join(OUT_DIR, 'best_model.pt'))
results = {
    'best_val_f1': best_val_f1,
    'test_f1': test_metrics['f1'],
    'test_precision': test_metrics['precision'],
    'test_recall': test_metrics['recall'],
    'test_accuracy': test_metrics['accuracy'],
    'test_tp': test_metrics['tp'],
    'test_fp': test_metrics['fp'],
    'test_fn': test_metrics['fn'],
    'test_tn': test_metrics['tn'],
    'history': history,
    'config': {
        'embedding_model': 'paraphrase-multilingual-mpnet-base-v2',
        'prosody_dim': PROSODY_DIM,
        'hidden': HIDDEN,
        'dropout': DROPOUT,
        'batch_size': BATCH_SIZE,
        'epochs': EPOCHS,
        'lr': LR,
        'weight_decay': WEIGHT_DECAY,
        'pos_weight_capped': min(pos_weight, 5.0),
    }
}
with open(os.path.join(OUT_DIR, 'results.json'), 'w') as f:
    json.dump(results, f, indent=2)

print(f"\nSaved to: {OUT_DIR}/")
