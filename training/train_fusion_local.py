#!/usr/bin/env python3
"""
ChuckleNet Fusion Training
WavLM (768-dim) + Prosody (23-dim) = 791-dim → Laughter detection
Uses existing July 16 dataset (21,468 samples, 22.7% positive)
"""

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.metrics import f1_score, classification_report
from collections import defaultdict
import time
import json

# Load data
print("Loading data...")
data = np.load(
    '/Users/Subho/autonomous_laughter_prediction_essential/data/prosody_aligned/wavlm_training_data_expanded.npz',
    allow_pickle=True
)

embeddings = data['embeddings']  # (21468, 768)
prosody = data['prosody']        # (21468, 23)
labels = data['labels']          # (21468,)
uids = data['uids']              # (21468,)

print(f"Samples: {len(labels):,}")
print(f"Positive: {labels.sum():,} ({labels.mean()*100:.1f}%)")

# Combine WavLM + prosody
X = np.concatenate([embeddings, prosody], axis=1)  # (21468, 791)
print(f"Feature dim: {X.shape[1]}")

# Split by video (no leakage)
video_ids = [uid.rsplit('_', 1)[0] for uid in uids]
unique_vids = list(set(video_ids))
np.random.seed(42)
np.random.shuffle(unique_vids)

n_train = int(0.8 * len(unique_vids))
n_val = int(0.1 * len(unique_vids))

train_vids = set(unique_vids[:n_train])
val_vids = set(unique_vids[n_train:n_train+n_val])
test_vids = set(unique_vids[n_train+n_val:])

X_train, y_train, X_val, y_val, X_test, y_test = [], [], [], [], [], []

for i, vid in enumerate(video_ids):
    if vid in train_vids:
        X_train.append(X[i])
        y_train.append(labels[i])
    elif vid in val_vids:
        X_val.append(X[i])
        y_val.append(labels[i])
    else:
        X_test.append(X[i])
        y_test.append(labels[i])

X_train = np.array(X_train, dtype=np.float32)
y_train = np.array(y_train, dtype=np.float32)
X_val = np.array(X_val, dtype=np.float32)
y_val = np.array(y_val, dtype=np.float32)
X_test = np.array(X_test, dtype=np.float32)
y_test = np.array(y_test, dtype=np.float32)

print(f"\nTrain: {len(X_train):,} ({y_train.sum():.0f} pos, {y_train.mean()*100:.1f}%)")
print(f"Val:   {len(X_val):,} ({y_val.sum():.0f} pos, {y_val.mean()*100:.1f}%)")
print(f"Test:  {len(X_test):,} ({y_test.sum():.0f} pos, {y_test.mean()*100:.1f}%)")

# Dataset
class FusionDataset(Dataset):
    def __init__(self, X, y):
        self.X = torch.tensor(X, dtype=torch.float32)
        self.y = torch.tensor(y, dtype=torch.float32)
    def __len__(self):
        return len(self.X)
    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]

train_ds = FusionDataset(X_train, y_train)
val_ds = FusionDataset(X_val, y_val)
test_ds = FusionDataset(X_test, y_test)

train_loader = DataLoader(train_ds, batch_size=256, shuffle=True)
val_loader = DataLoader(val_ds, batch_size=256)
test_loader = DataLoader(test_ds, batch_size=256)

# Model - fusion MLP
device = torch.device('mps' if torch.backends.mps.is_available() else 'cpu')
print(f"\nDevice: {device}")

model = nn.Sequential(
    nn.Linear(791, 512),
    nn.BatchNorm1d(512),
    nn.ReLU(),
    nn.Dropout(0.3),
    nn.Linear(512, 256),
    nn.BatchNorm1d(256),
    nn.ReLU(),
    nn.Dropout(0.2),
    nn.Linear(256, 64),
    nn.ReLU(),
    nn.Linear(64, 1),
).to(device)

# Class weights
pos_count = y_train.sum()
neg_count = len(y_train) - pos_count
pos_weight = neg_count / (pos_count + 1e-8)
print(f"Pos weight: {pos_weight:.2f}")

criterion = nn.BCEWithLogitsLoss(pos_weight=torch.tensor([pos_weight]).to(device))
optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=0.01)
scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=30)

EPOCHS = 30
best_f1 = 0
best_state = None

print(f"\nTraining for {EPOCHS} epochs...")
print("-" * 70)

for epoch in range(EPOCHS):
    t0 = time.time()
    
    # Train
    model.train()
    train_loss = 0
    for x, y in train_loader:
        x, y = x.to(device), y.to(device)
        optimizer.zero_grad()
        out = model(x).squeeze(-1)
        loss = criterion(out, y)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        train_loss += loss.item()
    scheduler.step()
    
    # Validate
    model.eval()
    val_preds, val_labels = [], []
    with torch.no_grad():
        for x, y in val_loader:
            x = x.to(device)
            out = model(x).squeeze(-1)
            val_preds.extend((torch.sigmoid(out) > 0.5).cpu().numpy())
            val_labels.extend(y.numpy())
    
    val_f1 = f1_score(val_labels, val_preds)
    epoch_time = time.time() - t0
    
    marker = ""
    if val_f1 > best_f1:
        best_f1 = val_f1
        best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
        marker = " ★"
    
    print(f"Epoch {epoch+1:2d}/{EPOCHS} | Loss: {train_loss/len(train_loader):.4f} | Val F1: {val_f1:.4f} | Time: {epoch_time:.1f}s{marker}")

# Test
print("\n" + "=" * 70)
model.load_state_dict(best_state)
model.eval()

test_preds, test_labels = [], []
with torch.no_grad():
    for x, y in test_loader:
        x = x.to(device)
        out = model(x).squeeze(-1)
        test_preds.extend((torch.sigmoid(out) > 0.5).cpu().numpy())
        test_labels.extend(y.numpy())

test_f1 = f1_score(test_labels, test_preds)
print(f"\n🏆 BEST VAL F1: {best_f1:.4f}")
print(f"🏆 TEST F1:     {test_f1:.4f}")
print(f"\n{classification_report(test_labels, test_preds, target_names=['No Laughter', 'Laughter'])}")

# Save results
results = {
    'val_f1': float(best_f1),
    'test_f1': float(test_f1),
    'n_train': len(X_train),
    'n_val': len(X_val),
    'n_test': len(X_test),
    'epochs': EPOCHS,
}
with open('/Users/Subho/autonomous_laughter_prediction_essential/experiments/fusion_results.json', 'w') as f:
    json.dump(results, f, indent=2)

# Save model
torch.save(best_state, '/Users/Subho/autonomous_laughter_prediction_essential/experiments/best_fusion_model.pt')
print(f"\nModel saved to experiments/best_fusion_model.pt")
print(f"Results saved to experiments/fusion_results.json")
