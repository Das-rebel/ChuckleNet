#!/usr/bin/env python3
"""
WavLM Utterance-Level Training with Proper Holdout
==================================================
Trains on 12,200 utterances, evaluates on 2,800 held-out comedian utterances.
"""
import json, os, numpy as np, torch, time
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import f1_score, precision_score, recall_score, classification_report

# Paths
WAVLM_DIR = '/Users/Subho/data/chuckle-net/wavlm_embeddings'
OUTPUT_DIR = '/Users/Subho/autonomous_laughter_prediction/experiments/wavlm_final'
os.makedirs(OUTPUT_DIR, exist_ok=True)

DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Device: {DEVICE}")

# Held-out comedians
HELD_OUT = {'BFIHCzw3itk', 'BAD4askmGgk', '1Nb3_os4RSA'}

# Load all utterances
print("Loading utterances...")
train_data = []
holdout_data = []

for f in Path(WAVLM_DIR).glob('*.json'):
    with open(f) as fp:
        data = json.load(fp)
    vid = f.stem
    
    for k, v in data.items():
        if isinstance(v, dict) and 'label' in v:
            item = {
                'uid': k,
                'video_id': vid,
                'embedding': v['embedding'],
                'label': v['label'],
                'text': v.get('text', ''),
            }
            if vid in HELD_OUT:
                holdout_data.append(item)
            else:
                train_data.append(item)

print(f"Train: {len(train_data)} utterances")
print(f"Holdout: {len(holdout_data)} utterances")

# Label distribution
train_pos = sum(1 for d in train_data if d['label'] == 1)
holdout_pos = sum(1 for d in holdout_data if d['label'] == 1)
print(f"Train positive: {train_pos} ({100*train_pos/len(train_data):.1f}%)")
print(f"Holdout positive: {holdout_pos} ({100*holdout_pos/len(holdout_data):.1f}%)")

# Split train into train/val
X_train = np.array([d['embedding'] for d in train_data], dtype=np.float32)
y_train = np.array([d['label'] for d in train_data])
video_ids_train = [d['video_id'] for d in train_data]

X_train_split, X_val, y_train_split, y_val = train_test_split(
    X_train, y_train, test_size=0.15, stratify=y_train, random_state=42
)

print(f"\nTrain split: {len(X_train_split)} ({sum(y_train_split)} pos)")
print(f"Val: {len(X_val)} ({sum(y_val)} pos)")

# Holdout
X_holdout = np.array([d['embedding'] for d in holdout_data], dtype=np.float32)
y_holdout = np.array([d['label'] for d in holdout_data])

# Normalize
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train_split)
X_val_scaled = scaler.transform(X_val)
X_holdout_scaled = scaler.transform(X_holdout)

# PyTorch Dataset
class AudioDataset(torch.utils.data.TensorDataset):
    def __init__(self, X, y):
        super().__init__(torch.tensor(X, dtype=torch.float32), torch.tensor(y, dtype=torch.long))
    def __getitem__(self, idx):
        x, y = super().__getitem__(idx)
        return x, y

train_ds = AudioDataset(X_train_scaled, y_train_split)
val_ds = AudioDataset(X_val_scaled, y_val)
holdout_ds = AudioDataset(X_holdout_scaled, y_holdout)

train_loader = torch.utils.data.DataLoader(train_ds, batch_size=64, shuffle=True)
val_loader = torch.utils.data.DataLoader(val_ds, batch_size=128)
holdout_loader = torch.utils.data.DataLoader(holdout_ds, batch_size=128)

# Model
class AudioClassifier(torch.nn.Module):
    def __init__(self, input_dim=768, hidden_dim=256, dropout=0.3):
        super().__init__()
        self.net = torch.nn.Sequential(
            torch.nn.Linear(input_dim, hidden_dim),
            torch.nn.ReLU(),
            torch.nn.Dropout(dropout),
            torch.nn.Linear(hidden_dim, hidden_dim // 2),
            torch.nn.ReLU(),
            torch.nn.Dropout(dropout),
            torch.nn.Linear(hidden_dim // 2, 2)
        )
    def forward(self, x):
        return self.net(x)

# Class weights for imbalanced data
n_neg = sum(y_train_split == 0)
n_pos = sum(y_train_split == 1)
pos_weight = torch.tensor([1.0, n_neg / max(n_pos, 1)], dtype=torch.float32).to(DEVICE)

model = AudioClassifier().to(DEVICE)
optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=0.01)
scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=30)
criterion = torch.nn.CrossEntropyLoss(weight=pos_weight)

print(f"Pos weight: {pos_weight[1]:.2f}")

# Training
print("\nTraining...")
best_val_f1 = 0
best_state = None
t0 = time.time()

for epoch in range(30):
    model.train()
    train_loss = 0
    for x, y_batch in train_loader:
        x, y_batch = x.to(DEVICE), y_batch.to(DEVICE)
        optimizer.zero_grad()
        out = model(x)
        loss = criterion(out, y_batch)
        loss.backward()
        optimizer.step()
        train_loss += loss.item()
    
    scheduler.step()
    
    # Evaluate
    model.eval()
    val_preds, val_true = [], []
    with torch.no_grad():
        for x, y_batch in val_loader:
            out = model(x.to(DEVICE))
            preds = out.argmax(dim=1).cpu().numpy()
            val_preds.extend(preds)
            val_true.extend(y_batch.numpy())
    
    val_f1 = f1_score(val_true, val_preds)
    val_p = precision_score(val_true, val_preds, zero_division=0)
    val_r = recall_score(val_true, val_preds, zero_division=0)
    
    if val_f1 > best_val_f1:
        best_val_f1 = val_f1
        best_state = model.state_dict().copy()
    
    if (epoch + 1) % 5 == 0 or epoch == 0:
        print(f"Epoch {epoch+1:2d}: loss={train_loss/len(train_loader):.4f}, val_f1={val_f1:.4f} (p={val_p:.3f}, r={val_r:.3f})")

# Load best and evaluate on holdout
model.load_state_dict(best_state)
model.eval()

holdout_preds, holdout_true = [], []
with torch.no_grad():
    for x, y_batch in holdout_loader:
        out = model(x.to(DEVICE))
        preds = out.argmax(dim=1).cpu().numpy()
        holdout_preds.extend(preds)
        holdout_true.extend(y_batch.numpy())

holdout_f1 = f1_score(holdout_true, holdout_preds)
holdout_p = precision_score(holdout_true, holdout_preds, zero_division=0)
holdout_r = recall_score(holdout_true, holdout_preds, zero_division=0)

print(f"\n=== FINAL RESULTS ===")
print(f"Best Val F1: {best_val_f1:.4f}")
print(f"Holdout F1: {holdout_f1:.4f} (p={holdout_p:.3f}, r={holdout_r:.3f})")
print(f"\nClassification Report (Holdout):")
print(classification_report(holdout_true, holdout_preds, target_names=['No Laughter', 'Laughter']))

print(f"Training time: {(time.time()-t0)/60:.1f} min")

# Save
torch.save(best_state, f'{OUTPUT_DIR}/best.pt')
torch.save(scaler, f'{OUTPUT_DIR}/scaler.pt')

results = {
    'val_f1': best_val_f1,
    'holdout_f1': holdout_f1,
    'holdout_precision': holdout_p,
    'holdout_recall': holdout_r,
    'held_out_comedians': list(HELD_OUT),
    'n_train': len(X_train_split),
    'n_val': len(X_val),
    'n_holdout': len(X_holdout),
}
with open(f'{OUTPUT_DIR}/results.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\nSaved to {OUTPUT_DIR}/")
