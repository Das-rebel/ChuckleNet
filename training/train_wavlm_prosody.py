#!/usr/bin/env python3
"""Train laughter detection with WavLM + Prosody."""

import json
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score, precision_score, recall_score
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

# Config
DATA_FILE = "data/prosody_aligned/wavlm_training_data.npz"
EPOCHS = 20
BATCH_SIZE = 64
LR = 1e-3
HIDDEN = 256

print("Loading data...")
data = np.load(DATA_FILE)
X_emb = data['embeddings']  # (N, 768)
X_pros = data['prosody']    # (N, 23)
y = data['labels']           # (N,)
uids = data['uids']

print(f"Dataset: {len(y)} samples, {y.mean():.1%} positive")

# Split - use indices to keep alignment
indices = np.arange(len(y))
idx_train, idx_test = train_test_split(indices, test_size=0.2, random_state=42, stratify=y)
idx_train, idx_val = train_test_split(idx_train, test_size=0.1, random_state=42, stratify=y[idx_train])

X_emb_train, X_emb_val, X_emb_test = X_emb[idx_train], X_emb[idx_val], X_emb[idx_test]
X_pro_train, X_pro_val, X_pro_test = X_pros[idx_train], X_pros[idx_val], X_pros[idx_test]
y_train, y_val, y_test = y[idx_train], y[idx_val], y[idx_test]
uid_test = uids[idx_test]

print(f"Train: {len(y_train)}, Val: {len(y_val)}, Test: {len(y_test)}")

# Normalize prosody
scaler = StandardScaler()
X_pro_train = scaler.fit_transform(X_pro_train)
X_pro_val = scaler.transform(X_pro_val)
X_pro_test = scaler.transform(X_pro_test)

# Model
class LaughterModel(nn.Module):
    def __init__(self, emb_dim=768, pros_dim=23, hidden=256):
        super().__init__()
        self.proj = nn.Linear(pros_dim, emb_dim)
        self.net = nn.Sequential(
            nn.Linear(emb_dim * 2, hidden),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden, hidden),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden, 1)
        )
    
    def forward(self, emb, pros):
        pros = self.proj(pros)
        x = torch.cat([emb, pros], dim=1)
        return self.net(x)

model = LaughterModel()
optimizer = torch.optim.AdamW(model.parameters(), lr=LR)
criterion = nn.BCEWithLogitsLoss(pos_weight=torch.tensor([(1-y_train.mean())/y_train.mean()]))

# Training
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = model.to(device)
print(f"Device: {device}")

best_f1 = 0
for epoch in range(EPOCHS):
    model.train()
    total_loss = 0
    
    for i in range(0, len(y_train), BATCH_SIZE):
        emb = torch.tensor(X_emb_train[i:i+BATCH_SIZE]).float().to(device)
        pro = torch.tensor(X_pro_train[i:i+BATCH_SIZE]).float().to(device)
        label = torch.tensor(y_train[i:i+BATCH_SIZE]).float().to(device)
        
        optimizer.zero_grad()
        out = model(emb, pro).squeeze()
        loss = criterion(out, label)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
    
    # Validation
    model.eval()
    with torch.no_grad():
        val_emb = torch.tensor(X_emb_val).float().to(device)
        val_pro = torch.tensor(X_pro_val).float().to(device)
        val_pred = torch.sigmoid(model(val_emb, val_pro)).squeeze().cpu().numpy() > 0.5
        val_f1 = f1_score(y_val, val_pred)
    
    if val_f1 > best_f1:
        best_f1 = val_f1
        torch.save(model.state_dict(), "data/prosody_aligned/best_model.pt")
    
    if epoch % 5 == 0:
        print(f"Epoch {epoch}: loss={total_loss:.4f}, val_f1={val_f1:.4f}, best={best_f1:.4f}")

# Final test
model.load_state_dict(torch.load("data/prosody_aligned/best_model.pt"))
model.eval()
with torch.no_grad():
    test_emb = torch.tensor(X_emb_test).float().to(device)
    test_pro = torch.tensor(X_pro_test).float().to(device)
    test_pred = (torch.sigmoid(model(test_emb, test_pro)).squeeze().cpu().numpy() > 0.5).astype(int)

test_f1 = f1_score(y_test, test_pred)
test_prec = precision_score(y_test, test_pred)
test_rec = recall_score(y_test, test_pred)

print(f"\n=== TEST RESULTS ===")
print(f"F1: {test_f1:.4f}")
print(f"Precision: {test_prec:.4f}")
print(f"Recall: {test_rec:.4f}")

# Save results
results = {
    "test_f1": float(test_f1),
    "test_precision": float(test_prec),
    "test_recall": float(test_rec),
    "val_f1": float(best_f1),
    "n_train": len(y_train),
    "n_val": len(y_val),
    "n_test": len(y_test),
    "positive_rate": float(y.mean())
}
with open("data/prosody_aligned/training_results.json", "w") as f:
    json.dump(results, f, indent=2)
print(f"\nResults saved to data/prosody_aligned/training_results.json")
