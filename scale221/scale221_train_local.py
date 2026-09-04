#!/usr/bin/env python3
"""
Scale221 Local Training Script
================================
Uses pre-extracted 791-dim embeddings (WavLM 768 + prosody 23).
Processes on local CPU/GPU with checkpointing.

Usage:
    python3 scale221_train_local.py

Requirements:
    pip install torch numpy scikit-learn tqdm
"""
import os, json, sys
import numpy as np
import torch
import torch.nn as nn
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GroupKFold
from sklearn.metrics import f1_score, precision_score, recall_score
from tqdm import tqdm

# ── Config ──────────────────────────────────────────────
SCALE_DIR = os.path.dirname(os.path.abspath(__file__))
EMB_DIR  = os.path.join(SCALE_DIR, "embeddings")
VIDEO_IDS = os.path.join(SCALE_DIR, "video_ids.json")
FUSION_MODEL = os.path.join(SCALE_DIR, "best_fusion_model.pt")
RESULTS_JSON = os.path.join(SCALE_DIR, "results.json")
MODEL_OUT   = os.path.join(SCALE_DIR, "scale221_fusion_model.pt")

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Device: {DEVICE}")

# ── Model ────────────────────────────────────────────────
class FusionMLP(nn.Module):
    def __init__(self, input_dim=791):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 512), nn.ReLU(), nn.BatchNorm1d(512), nn.Dropout(0.3),
            nn.Linear(512, 256), nn.ReLU(), nn.BatchNorm1d(256), nn.Dropout(0.3),
            nn.Linear(256, 64), nn.ReLU(), nn.BatchNorm1d(64), nn.Dropout(0.3),
            nn.Linear(64, 1), nn.Sigmoid()
        )
    def forward(self, x):
        return self.net(x)

# ── Load Teacher ────────────────────────────────────────
print("Loading teacher model...")
teacher = FusionMLP(input_dim=791)
teacher.load_state_dict(torch.load(FUSION_MODEL, map_location="cpu"), strict=False)
teacher.eval()
print(f"✓ Teacher loaded: {sum(p.numel() for p in teacher.parameters()):,} params")

# ── Load Embeddings ──────────────────────────────────────
with open(VIDEO_IDS) as f:
    video_ids = json.load(f)
print(f"Video IDs: {len(video_ids)}")

emb_files = sorted([f for f in os.listdir(EMB_DIR) if f.endswith(".npy")])
print(f"Embedding files: {len(emb_files)}")

X_list, y_list, vids_list = [], [], []
for f in tqdm(emb_files, desc="Loading embeddings"):
    vid = f.replace(".npy", "")
    emb = np.load(os.path.join(EMB_DIR, f))   # (n_segs, 791)
    X_list.append(emb)
    vids_list.extend([vid] * len(emb))

X_all = np.vstack(X_list)
vids_all = vids_list
print(f"Total segments: {len(vids_all)}")

# ── Pseudo-label ────────────────────────────────────────
print("Pseudo-labeling with teacher...")
with torch.no_grad():
    probs = teacher(torch.tensor(X_all, dtype=torch.float32)).numpy().squeeze()

y_new = (probs >= 0.5).astype(int)
pos_rate = y_new.mean()
print(f"Pseudo-labeled: {y_new.sum()} pos / {len(y_new)} ({100*pos_rate:.1f}%)")
print(f"Prob dist: min={probs.min():.4f}, max={probs.max():.4f}, mean={probs.mean():.4f}")

# Fallback: top 30% if positive rate < 15%
if pos_rate < 0.15:
    print(f"⚠️ Positive rate {100*pos_rate:.1f}% < 15%, using top 30%")
    threshold = np.percentile(probs, 70)
    y_new = (probs >= threshold).astype(int)
    print(f"New pos rate: {100*y_new.mean():.1f}%")

y_all = y_new
print(f"Final: {len(y_all)} segs, {y_all.sum()} pos ({100*y_all.mean():.1f}%)")

# ── GroupKFold Training ─────────────────────────────────
groups = np.array(vids_all)
unique_vids = list(set(vids_all))
n_vids = len(unique_vids)
print(f"\nTraining on {len(y_all)} segments from {n_vids} videos")

gkf = GroupKFold(n_splits=min(5, n_vids))
models, scalers, fold_f1s = [], [], []

for fold, (tr_idx, te_idx) in enumerate(gkf.split(X_all, y_all, groups)):
    print(f"\n=== Fold {fold+1} ===")
    Xtr, Xte = X_all[tr_idx], X_all[te_idx]
    ytr, yte = y_all[tr_idx], y_all[te_idx]

    scaler = StandardScaler()
    Xtr_s = scaler.fit_transform(Xtr)
    Xte_s = scaler.transform(Xte)

    model = FusionMLP(input_dim=791)
    
    # Historical rule: pos_weight <= 3.0
    pos_rate_tr = ytr.sum() / max(len(ytr), 1)
    pos_weight = min((1.0 - pos_rate_tr) / (pos_rate_tr + 1e-8), 3.0)
    print(f"pos_rate={pos_rate_tr:.3f}, pos_weight={pos_weight:.2f}")

    opt = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=0.01)
    criterion = nn.BCELoss(pos_weight=torch.tensor([pos_weight]))

    Xtr_t = torch.tensor(Xtr_s, dtype=torch.float32)
    ytr_t = torch.tensor(ytr, dtype=torch.float32).unsqueeze(1)

    best_f1, patience, no_imp = 0, 5, 0
    for epoch in range(50):
        model.train()
        for i in range(0, len(Xtr_t), 256):
            bx = Xtr_t[i:i+256]
            by = ytr_t[i:i+256]
            opt.zero_grad()
            loss = criterion(model(bx), by)
            loss.backward()
            opt.step()

        model.eval()
        with torch.no_grad():
            preds = model(torch.tensor(Xte_s, dtype=torch.float32)).numpy().squeeze()
            f = f1_score(yte, (preds >= 0.5).astype(int), zero_division=0)
            if f > best_f1:
                best_f1 = f
                no_imp = 0
            else:
                no_imp += 1
            if no_imp >= patience:
                break

    model.eval()
    with torch.no_grad():
        # Saturation check
        sample_probs = model(torch.tensor(Xte_s[:100], dtype=torch.float32)).numpy().squeeze()
        prob_std = sample_probs.std()
        if prob_std < 0.01:
            print(f"⚠️ SATURATION: prob_std={prob_std:.6f}")

        preds = model(torch.tensor(Xte_s, dtype=torch.float32)).numpy().squeeze()
        p = precision_score(yte, (preds >= 0.5).astype(int), zero_division=0)
        r = recall_score(yte, (preds >= 0.5).astype(int), zero_division=0)
        f = f1_score(yte, (preds >= 0.5).astype(int), zero_division=0)
        print(f"F1={f:.4f} P={p:.4f} R={r:.4f}")

    models.append(model)
    scalers.append(scaler)
    fold_f1s.append(f)

print(f"\n=== CV F1: {np.mean(fold_f1s):.4f} ± {np.std(fold_f1s):.4f} ===")

# ── Save ───────────────────────────────────────────────
best_idx = int(np.argmax(fold_f1s))
torch.save(models[best_idx].state_dict(), MODEL_OUT)
print(f"✓ Model saved: {MODEL_OUT}")

results = {
    "n_videos": n_vids,
    "n_segments": int(len(y_all)),
    "positive_rate": float(y_all.mean()),
    "cross_val_f1": float(np.mean(fold_f1s)),
    "cross_val_std": float(np.std(fold_f1s)),
    "fold_f1s": [float(f) for f in fold_f1s],
    "teacher_max_prob": float(probs.max()),
}
with open(RESULTS_JSON, "w") as f:
    json.dump(results, f, indent=2)
print(f"✓ Results saved: {RESULTS_JSON}")
print(json.dumps(results, indent=2))
