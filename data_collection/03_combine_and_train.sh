#!/bin/bash
# PART 3: Combine All Data and Train Final Model
# Run after Parts 1 and 2 complete

echo "=== PART 3: COMBINE AND TRAIN ==="
echo ""

cd /Users/Subho/autonomous_laughter_prediction_essential

python3 << 'ENDPY'
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from sklearn.metrics import f1_score
from sklearn.model_selection import train_test_split
import os

print("Loading all datasets...")

# 1. Original 87 Gillick (gold standard)
d87 = np.load("data/prosody_aligned/wavlm_training_data_expanded.npz", allow_pickle=True)
X87 = d87['prosody']  # (21468, 23)
y87 = d87['labels']     # (21468,)
vids87 = [str(u).rsplit('_',1)[0] for u in d87['uids']]
print(f"Gillick 87: {len(y87)} utts, {y87.sum()} pos ({100*y87.mean():.1f}%)")

# 2. YouTube 481 with improved labels
d481 = np.load("data/prosody_aligned/FINAL_500plus_41feat.npz", allow_pickle=True)
# Use first 23 features to match
X481 = d481['features'][:, :23]  # (183087, 23)
y481_improved = d481['labels']  # Using original energy-based for now
print(f"YouTube 481: {len(y481_improved)} utts, {y481_improved.sum()} pos ({100*y481_improved.mean():.1f}%)")

# 3. Gillick downloaded (Part 1) - extract prosody when available
gillick_dir = "/Users/Subho/data/utterances/gillick_audio"
if os.path.exists(gillick_dir):
    gillick_files = [f for f in os.listdir(gillick_dir) if f.endswith('.mp3')]
    print(f"Gillick downloaded: {len(gillick_files)} audio files")
else:
    print("Gillick download: Not started yet")

# Combine datasets
print("\nCombining datasets...")
X_all = np.vstack([X87, X481])
y_all = np.concatenate([y87, y481_improved])
print(f"Combined: {len(y_all)} utts, {y_all.sum()} pos ({100*y_all.mean():.1f}%)")

# Video-level train/val/test split
print("\nCreating video-level splits...")
from collections import defaultdict
vid_to_idx = defaultdict(list)
for i, v in enumerate(vids87):
    vid_to_idx[v].append(i)
for i, v in enumerate([str(v) for v in d481['vids']], start=len(vids87)):
    vid_to_idx[v].append(i)

all_vids = list(vid_to_idx.keys())
np.random.seed(42)
np.random.shuffle(all_vids)
n_val = int(0.1 * len(all_vids))
n_test = int(0.1 * len(all_vids))

val_vids = set(all_vids[:n_val])
test_vids = set(all_vids[n_val:n_val+n_test])
train_vids = set(all_vids[n_val+n_test:])

train_idx = [i for v in train_vids for i in vid_to_idx[v]]
val_idx = [i for v in val_vids for i in vid_to_idx[v]]
test_idx = [i for v in test_vids for i in vid_to_idx[v]]

X_train, X_val, X_test = X_all[train_idx], X_all[val_idx], X_all[test_idx]
y_train, y_val, y_test = y_all[train_idx], y_all[val_idx], y_all[test_idx]

print(f"Train: {len(y_train)} ({y_train.sum()} pos, {100*y_train.mean():.1f}%)")
print(f"Val: {len(y_val)} ({y_val.sum()} pos, {100*y_val.mean():.1f}%)")
print(f"Test: {len(y_test)} ({y_test.sum()} pos, {100*y_test.mean():.1f}%)")

# Normalize
X_mean = X_train.mean(axis=0)
X_std = X_train.std(axis=0) + 1e-8
X_train = (X_train - X_mean) / X_std
X_val = (X_val - X_mean) / X_std
X_test = (X_test - X_mean) / X_std

# MLP Training
print("\nTraining MLP...")

class LaughterDataset(Dataset):
    def __init__(self, X, y):
        self.X = torch.tensor(X, dtype=torch.float32)
        self.y = torch.tensor(y, dtype=torch.float32)
    def __len__(self):
        return len(self.y)
    def __getitem__(self, i):
        return self.X[i], self.y[i]

class MLP(torch.nn.Module):
    def __init__(self, dim=23):
        super().__init__()
        self.net = torch.nn.Sequential(
            torch.nn.Linear(dim, 128),
            torch.nn.ReLU(),
            torch.nn.Dropout(0.3),
            torch.nn.Linear(128, 32),
            torch.nn.ReLU(),
            torch.nn.Linear(32, 1),
        )
    def forward(self, x):
        return self.net(x).squeeze(-1)

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Device: {device}")

train_ds = LaughterDataset(X_train, y_train)
val_ds = LaughterDataset(X_val, y_val)
test_ds = LaughterDataset(X_test, y_test)

train_loader = DataLoader(train_ds, batch_size=256, shuffle=True)
val_loader = DataLoader(val_ds, batch_size=256)
test_loader = DataLoader(test_ds, batch_size=256)

model = MLP().to(device)
pos_weight = torch.tensor([(len(y_train) - y_train.sum()) / max(1, y_train.sum())]).to(device)
criterion = torch.nn.BCEWithLogitsLoss(pos_weight=pos_weight)
optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=0.01)

best_f1 = 0
best_state = None

for epoch in range(30):
    model.train()
    for x, y in train_loader:
        x, y = x.to(device), y.to(device)
        optimizer.zero_grad()
        loss = criterion(model(x), y)
        loss.backward()
        optimizer.step()
    
    # Validate
    model.eval()
    preds, labels = [], []
    with torch.no_grad():
        for x, y in val_loader:
            x = x.to(device)
            p = (torch.sigmoid(model(x)) > 0.5).cpu().numpy()
            preds.extend(p)
            labels.extend(y.numpy())
    
    val_f1 = f1_score(labels, preds)
    
    if val_f1 > best_f1:
        best_f1 = val_f1
        best_state = model.state_dict().copy()
        torch.save(best_state, "models/best_prosody_mlp.pt")
    
    print(f"Epoch {epoch+1}: Val F1 = {val_f1:.4f}")

# Final test
model.load_state_dict(best_state)
model.eval()
preds, labels = [], []
with torch.no_grad():
    for x, y in test_loader:
        x = x.to(device)
        p = (torch.sigmoid(model(x)) > 0.5).cpu().numpy()
        preds.extend(p)
        labels.extend(y.numpy())

test_f1 = f1_score(labels, preds)
print(f"\n=== TEST F1: {test_f1:.4f} ===")

# Save results
import json
results = {
    "train_size": len(y_train),
    "val_size": len(y_val),
    "test_size": len(y_test),
    "val_f1": float(best_f1),
    "test_f1": float(test_f1),
}
with open("models/training_results_1168.json", 'w') as f:
    json.dump(results, f, indent=2)
print(f"Results saved to models/training_results_1168.json")
ENDPY

echo ""
echo "=== PART 3 COMPLETE ==="
