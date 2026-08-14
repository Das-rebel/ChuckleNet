#!/usr/bin/env python3
"""
Train on 500+ videos with ALL features (energy + F0 + MFCC/spectral = 50 dims).
Labels: energy-based (rel_energy > 2.0 = audience laughter).
"""
import numpy as np
from sklearn.metrics import f1_score, precision_score, recall_score, classification_report
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
import torch, torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from collections import Counter
import json, os

def train_and_eval():
    print("=" * 70)
    print("FULL FEATURE TRAINING: 500+ videos, 50 features")
    print("=" * 70)
    
    # Load energy features (10 dims + rel_energy)
    edata = np.load('data/prosody_aligned/energy_labels_668.npz', allow_pickle=True)
    X_energy = edata['features']  # (N, 10)
    y_vtt = edata['labels']
    vids = edata['vids']
    rel_e = edata['features'][:, 8]  # rel_energy
    
    # Load F0 features (5 dims)
    fdata = np.load('data/prosody_aligned/f0_668_videos.npz', allow_pickle=True)
    X_f0 = fdata['features']
    
    # Load spectral features (35 dims)
    sdata = np.load('data/prosody_aligned/spectral_668.npz', allow_pickle=True)
    X_spec = sdata['features']
    spec_vids = sdata['vids']
    
    # Verify same order
    assert len(X_energy) == len(X_f0) == len(X_spec), f"Length mismatch: {len(X_energy)} vs {len(X_f0)} vs {len(X_spec)}"
    
    # Combine ALL features: 10 + 5 + 35 = 50
    X_all = np.hstack([X_energy, X_f0, X_spec])
    print(f"Features: {X_all.shape[1]} (10 energy + 5 F0 + 35 spectral)")
    
    # Labels: rel_energy > 2.0 = laughter
    y_all = (rel_e > 2.0).astype(int)
    
    # Filter to comedy videos (>=2% positive, >=20 utterances)
    vid_list = list(vids)
    vp, vt = Counter(), Counter()
    for i, v in enumerate(vid_list):
        vt[v] += 1
        if y_all[i] == 1: vp[v] += 1
    
    good_vids = set()
    for v in vt:
        if vt[v] >= 20 and vp[v]/vt[v] >= 0.02:
            good_vids.add(v)
    
    mask = np.array([v in good_vids for v in vid_list])
    X = X_all[mask]
    y = y_all[mask]
    vids_f = vids[mask]
    
    print(f"\nDataset: {len(set(vids_f))} videos, {len(y):,} utterances, {y.mean()*100:.1f}% positive")
    
    # Video-level split
    unique_f = sorted(set(vids_f))
    np.random.seed(42)
    np.random.shuffle(unique_f)
    n_tr = int(0.8 * len(unique_f))
    tr_v = set(unique_f[:n_tr])
    te_v = set(unique_f[n_tr:])
    
    tr_idx = [i for i, v in enumerate(vids_f) if v in tr_v]
    te_idx = [i for i, v in enumerate(vids_f) if v in te_v]
    
    X_tr, y_tr = X[tr_idx], y[tr_idx]
    X_te, y_te = X[te_idx], y[te_idx]
    
    print(f"Split: {len(tr_v)} train / {len(te_v)} test videos")
    print(f"  Train: {len(y_tr):,} ({y_tr.mean()*100:.1f}% pos)")
    print(f"  Test: {len(y_te):,} ({y_te.mean()*100:.1f}% pos)")
    
    # Standardize
    scaler = StandardScaler()
    X_tr_s = scaler.fit_transform(X_tr)
    X_te_s = scaler.transform(X_te)
    
    # Feature importance via LR
    lr = LogisticRegression(class_weight='balanced', max_iter=1000, C=1.0)
    lr.fit(X_tr_s, y_tr)
    lr_pred = lr.predict(X_te_s)
    lr_f1 = f1_score(y_te, lr_pred)
    
    feat_names = (['rms_mean','rms_max','rms_std','rms_p90','spec_cent','spec_flat','spec_roll','spike_rate','rel_energy','video_median'] +
                  ['f0_mean','f0_std','f0_max','f0_min','voiced_rate'] +
                  [f'mfcc_{i}' for i in range(26)] + ['contrast_mean','chroma_mean','chroma_std','zcr','spec_bw'] + 
                  [f'extra_{i}' for i in range(4)])
    
    print(f"\nLR F1: {lr_f1:.4f}")
    print(f"\nTop 10 features (|LR coef|):")
    coefs = [(feat_names[i] if i < len(feat_names) else f'feat_{i}', abs(lr.coef_[0][i])) 
             for i in range(min(len(feat_names), X_tr_s.shape[1]))]
    for name, coef in sorted(coefs, key=lambda x: -x[1])[:10]:
        print(f"  {name:15s}: {coef:.3f}")
    
    # Train Deep MLP
    class DS(Dataset):
        def __init__(self, X, y):
            self.X = torch.tensor(X, dtype=torch.float32)
            self.y = torch.tensor(y, dtype=torch.float32)
        def __len__(self): return len(self.X)
        def __getitem__(self, i): return self.X[i], self.y[i]
    
    class DeepMLP(nn.Module):
        def __init__(self, d=50):
            super().__init__()
            self.net = nn.Sequential(
                nn.Linear(d, 256), nn.ReLU(), nn.BatchNorm1d(256), nn.Dropout(0.3),
                nn.Linear(256, 128), nn.ReLU(), nn.BatchNorm1d(128), nn.Dropout(0.2),
                nn.Linear(128, 64), nn.ReLU(), nn.BatchNorm1d(64), nn.Dropout(0.1),
                nn.Linear(64, 1))
        def forward(self, x): return self.net(x).squeeze(-1)
    
    train_loader = DataLoader(DS(X_tr_s, y_tr), batch_size=512, shuffle=True)
    model = DeepMLP(X_tr_s.shape[1])
    pos_w = torch.tensor([(len(y_tr)-y_tr.sum())/max(y_tr.sum(),1)])
    criterion = nn.BCEWithLogitsLoss(pos_weight=pos_w)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=0.01)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=50)
    
    best_f1 = 0
    for epoch in range(50):
        model.train()
        for x, yb in train_loader:
            optimizer.zero_grad()
            criterion(model(x), yb).backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
        scheduler.step()
        model.eval()
        with torch.no_grad():
            vp = (torch.sigmoid(model(torch.tensor(X_te_s, dtype=torch.float32))) > 0.5).numpy()
        f1 = f1_score(y_te, vp)
        if f1 > best_f1:
            best_f1 = f1
            best_p = precision_score(y_te, vp)
            best_r = recall_score(y_te, vp)
    
    print(f"\n{'='*70}")
    print(f"FINAL RESULTS: {len(set(vids_f))} videos, {X_all.shape[1]} features")
    print(f"{'='*70}")
    print(f"  LR F1:        {lr_f1:.4f}")
    print(f"  MLP F1:       {best_f1:.4f}")
    print(f"  Precision:    {best_p:.4f}")
    print(f"  Recall:       {best_r:.4f}")
    
    # Ablation: without rel_energy
    no_rel = list(range(8)) + list(range(9, X_all.shape[1]))  # Skip feature 8
    X_no_rel = X_all[:, no_rel]
    X_tr_nr = scaler.fit_transform(X_no_rel[tr_idx])
    X_te_nr = scaler.transform(X_no_rel[te_idx])
    
    lr2 = LogisticRegression(class_weight='balanced', max_iter=1000, C=1.0)
    lr2.fit(X_tr_nr, y_tr)
    lr2_f1 = f1_score(y_te, lr2.predict(X_te_nr))
    print(f"\n  Without rel_energy LR F1: {lr2_f1:.4f}")
    
    # Save
    np.savez('data/prosody_aligned/FINAL_500plus_50feat.npz',
             features=X, labels=y, vids=vids_f, feature_names=feat_names[:X.shape[1]])
    
    torch.save({
        'model_state': model.state_dict(),
        'scaler_mean': scaler.mean_,
        'scaler_scale': scaler.scale_,
        'best_f1': best_f1,
        'n_videos': len(set(vids_f)),
        'n_features': X.shape[1],
    }, 'experiments/final_500plus_50feat.pt')
    
    print(f"\nSaved: experiments/final_500plus_50feat.pt")

if __name__ == '__main__':
    train_and_eval()
