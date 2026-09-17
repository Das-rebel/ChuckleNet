#!/usr/bin/env python3
"""P1 temporal-effect validation on ChuckleNet 118v human-label data.

Protocol upgrade over E02:
- 3 fixed seeds x 5 video-disjoint folds.
- Conditions: true order, full random order, local-block shuffle, reversed order.
- Same model initialization seed across conditions within a seed/fold.
- Predictions are mapped back to original window order for paired evaluation.
- Paired video-level bootstrap CIs, clustered by video ID.

Input contract:
- /tmp/p1_data/scale221/embeddings/{vid}.npy: [n_windows, 791]
- /tmp/p1_data/labels/labels/{vid}.csv: text,timestamp,label with B/I/L/O/U
"""

import ast
import glob
import hashlib
import json
import os
import random
import time
import zlib
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.metrics import f1_score
from sklearn.model_selection import GroupKFold

ROOT = Path('/Users/Subho/autonomous_laughter_prediction_essential')
EMB_DIR = Path('/tmp/p1_data/scale221/embeddings')
LAB_DIR = Path('/tmp/p1_data/labels/labels')
OUT_DIR = ROOT / 'results' / 'p1'
OUT_DIR.mkdir(parents=True, exist_ok=True)

SEEDS = [42, 43, 44]
N_FOLDS = 5
WIN_SECONDS = 5.0
EPOCHS = 40
PATIENCE = 8
POS_WEIGHT = 8.0
LR = 5e-4
GRAD_CLIP = 1.0
LOCAL_BLOCK = 5  # 5 x 5 s = 25 s broad-location block
BOOT_N = 10000
BOOT_SEED = 20260918

conditions = ['true', 'random', 'local_shuffle', 'reverse']


def sha256_file(path: Path, limit_bytes: int = 50_000_000) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while True:
            b = f.read(1024 * 1024)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def label_windows(csv_path: Path, n_windows: int, win: float = WIN_SECONDS):
    """Registry-compatible window label: positive if B/I/L midpoint lies in window."""
    df = pd.read_csv(csv_path)
    labels = np.zeros(n_windows, dtype=np.int64)
    for _, row in df.iterrows():
        if row['label'] not in ('B', 'I', 'L'):
            continue
        try:
            start, end = ast.literal_eval(str(row['timestamp']))
        except Exception:
            continue
        if end <= start:
            continue
        k = int(((start + end) / 2.0) // win)
        if 0 <= k < n_windows:
            labels[k] = 1
    return labels


def temporal_features(times: np.ndarray) -> np.ndarray:
    """E02 temporal-6 features, retained for protocol parity."""
    n = len(times)
    start, end = times[:, 0], times[:, 1]
    pause_before = np.zeros(n, dtype=np.float32)
    pause_before[1:] = np.maximum(0.0, start[1:] - end[:-1])
    pause_after = np.zeros(n, dtype=np.float32)
    pause_after[:-1] = pause_before[1:]
    duration = end - start
    is_gap = (pause_before > 0.3).astype(np.float32)
    since_gap = np.zeros(n, dtype=np.float32)
    run = 0
    for i in range(n):
        run = 0 if is_gap[i] else run + 1
        since_gap[i] = run
    next_gap = np.zeros(n, dtype=np.float32)
    next_gap[:-1] = pause_before[1:]
    return np.stack([
        np.log1p(pause_before),
        np.log1p(pause_after),
        np.log1p(np.clip(duration, 0, 30)),
        is_gap,
        np.log1p(np.clip(since_gap, 0, 100)),
        np.log1p(next_gap),
    ], axis=1).astype(np.float32)


class BiGRU(nn.Module):
    def __init__(self, input_dim: int, hidden: int = 128):
        super().__init__()
        self.gru = nn.GRU(input_dim, hidden, batch_first=True, bidirectional=True)
        self.head = nn.Sequential(nn.Linear(2 * hidden, 64), nn.ReLU(), nn.Linear(64, 1))

    def forward(self, x):
        z, _ = self.gru(x)
        return self.head(z).squeeze(-1)


def permutation_for(condition: str, video_id: str, n: int, seed: int, fold: int):
    """Return permutation p such that shuffled[p] gives original order after inverse map."""
    if condition == 'true':
        return None
    if condition == 'reverse':
        return np.arange(n)[::-1]
    rng = np.random.default_rng(seed * 1_000_003 + fold * 10_007 + zlib.crc32(video_id.encode()) % 999_983)
    perm = rng.permutation(n)
    if condition == 'random':
        return perm
    if condition == 'local_shuffle':
        # Permute within contiguous 25 s blocks, preserving broad temporal location.
        shuffled = np.arange(n)
        for block_start in range(0, n, LOCAL_BLOCK):
            block = np.arange(block_start, min(block_start + LOCAL_BLOCK, n))
            shuffled[block] = block[rng.permutation(len(block))]
        return shuffled
    raise ValueError(condition)


def train_eval_fold(train_ids, val_ids, seed: int, fold: int, condition: str):
    torch.manual_seed(seed)
    np.random.seed(seed)
    random.seed(seed)

    all_train = np.concatenate([
        np.concatenate([data[v]['features'], data[v]['temporal']], axis=1)
        for v in train_ids
    ], axis=0)
    mean = all_train.mean(axis=0)
    std = all_train.std(axis=0) + 1e-6

    model = BiGRU(data[train_ids[0]]['features'].shape[1] + 6)
    criterion = nn.BCEWithLogitsLoss(pos_weight=torch.tensor(float(POS_WEIGHT)))
    optimizer = torch.optim.AdamW(model.parameters(), lr=LR)
    model.head[-1].bias.data.fill_(-2.0)

    prepared_train = {}
    for v in train_ids:
        d = data[v]
        X = np.concatenate([d['features'], d['temporal']], axis=1)
        X = (X - mean) / std
        y = d['labels']
        perm = permutation_for(condition, v, len(X), seed, fold)
        if perm is not None:
            X = X[perm]
            y = y[perm]
        prepared_train[v] = (X, y)

    best_f1 = -1.0
    best_state = None
    best_epoch = -1
    for epoch in range(EPOCHS):
        model.train()
        for v in train_ids:
            X, y = prepared_train[v]
            xt = torch.from_numpy(X).float().unsqueeze(0)
            yt = torch.from_numpy(y).float()
            optimizer.zero_grad()
            loss = criterion(model(xt).squeeze(-1).squeeze(0), yt)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), GRAD_CLIP)
            optimizer.step()

        model.eval()
        val_preds = []
        val_truth = []
        with torch.no_grad():
            for v in val_ids:
                d = data[v]
                X = np.concatenate([d['features'], d['temporal']], axis=1)
                X = (X - mean) / std
                y = d['labels']
                perm = permutation_for(condition, v, len(X), seed, fold)
                X_eval = X[perm] if perm is not None else X
                pred_shuffled = torch.sigmoid(model(torch.from_numpy(X_eval).float().unsqueeze(0)).squeeze(-1).squeeze(0)).numpy()
                if perm is None:
                    pred_original = pred_shuffled
                else:
                    pred_original = np.empty_like(pred_shuffled)
                    pred_original[perm] = pred_shuffled
                val_preds.append(pred_original)
                val_truth.append(y)
        pv = np.concatenate(val_preds)
        yt = np.concatenate(val_truth)
        score = f1_score(yt, (pv > 0.5).astype(int), zero_division=0)
        if score > best_f1:
            best_f1 = score
            best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
            best_epoch = epoch
        elif epoch - best_epoch >= PATIENCE:
            break

    if best_state is None:
        best_state = model.state_dict()
        best_epoch = 0
    model.load_state_dict(best_state)
    model.eval()

    records = []
    with torch.no_grad():
        for v in val_ids:
            d = data[v]
            X = np.concatenate([d['features'], d['temporal']], axis=1)
            X = (X - mean) / std
            y = d['labels']
            perm = permutation_for(condition, v, len(X), seed, fold)
            X_eval = X[perm] if perm is not None else X
            pred_shuffled = torch.sigmoid(model(torch.from_numpy(X_eval).float().unsqueeze(0)).squeeze(-1).squeeze(0)).numpy()
            if perm is None:
                pred_original = pred_shuffled
            else:
                pred_original = np.empty_like(pred_shuffled)
                pred_original[perm] = pred_shuffled
            pred_labels = (pred_original > 0.5).astype(int)
            video_f1 = f1_score(y, pred_labels, zero_division=0)
            records.append({
                'seed': seed,
                'fold': fold,
                'video': v,
                'n_windows': int(len(y)),
                'n_positive': int(y.sum()),
                'f1': float(video_f1),
                'precision': float(__import__('sklearn.metrics', fromlist=['precision_score']).precision_score(y, pred_labels, zero_division=0)),
                'recall': float(__import__('sklearn.metrics', fromlist=['recall_score']).recall_score(y, pred_labels, zero_division=0)),
            })
    return records, best_epoch, best_f1


def clustered_bootstrap_paired(records_true, records_control, key_condition, n_boot=BOOT_N, rng_seed=BOOT_SEED):
    """Bootstrap mean paired F1 delta, resampling video IDs and including all seed/fold rows."""
    true_by_video = {}
    control_by_video = {}
    for r in records_true:
        true_by_video.setdefault(r['video'], []).append(r['f1'])
    for r in records_control:
        control_by_video.setdefault(r['video'], []).append(r['f1'])
    videos = sorted(set(true_by_video) & set(control_by_video))
    deltas = []
    improved = worsened = unchanged = 0
    for v in videos:
        vals = np.array(true_by_video[v]) - np.array(control_by_video[v])
        deltas.extend(vals.tolist())
    deltas = np.array(deltas, dtype=np.float64)
    improved = int((deltas > 1e-12).sum())
    worsened = int((deltas < -1e-12).sum())
    unchanged = int((np.abs(deltas) <= 1e-12).sum())

    video_list = np.array(videos)
    rng = np.random.default_rng(rng_seed)
    boot = np.empty(n_boot, dtype=np.float64)
    by_video_delta = {
        v: np.array(true_by_video[v]) - np.array(control_by_video[v])
        for v in videos
    }
    for b in range(n_boot):
        sample_videos = rng.choice(video_list, size=len(video_list), replace=True)
        vals = [by_video_delta[v] for v in sample_videos]
        boot[b] = np.concatenate(vals).mean()
    return {
        'comparison': f'true_minus_{key_condition}',
        'mean_delta_f1': float(deltas.mean()),
        'median_delta_f1': float(np.median(deltas)),
        'bootstrap_ci95': [float(np.quantile(boot, 0.025)), float(np.quantile(boot, 0.975))],
        'n_observations': int(len(deltas)),
        'n_clustered_videos': int(len(videos)),
        'improved': improved,
        'worsened': worsened,
        'unchanged': unchanged,
        'bootstrap_seed': int(rng_seed),
        'bootstrap_resamples': int(n_boot),
    }


t_start = time.time()
emb_ids = {os.path.basename(p)[:-4] for p in glob.glob(str(EMB_DIR / '*.npy'))}
lab_ids = {os.path.basename(p)[:-4] for p in glob.glob(str(LAB_DIR / '*.csv'))}
video_ids = sorted(emb_ids & lab_ids)

data = {}
for video_id in video_ids:
    features = np.nan_to_num(np.load(EMB_DIR / f'{video_id}.npy').astype(np.float32))
    if features.ndim != 2:
        continue
    labels = label_windows(LAB_DIR / f'{video_id}.csv', len(features))
    if len(labels) != len(features):
        continue
    times = np.stack([
        np.arange(len(features)) * WIN_SECONDS,
        np.arange(len(features)) * WIN_SECONDS + WIN_SECONDS,
    ], axis=1).astype(np.float32)
    data[video_id] = {
        'features': features,
        'labels': labels,
        'temporal': temporal_features(times),
    }
video_ids = sorted(data)
groups = np.array(video_ids)
folds = list(GroupKFold(n_splits=N_FOLDS).split(np.zeros(len(video_ids)), groups=groups))

print(f'videos={len(video_ids)} windows={sum(len(d["labels"]) for d in data.values())} '
      f'positives={sum(int(d["labels"].sum()) for d in data.values())}', flush=True)

all_records = {c: [] for c in conditions}
fold_summaries = {c: [] for c in conditions}
for seed in SEEDS:
    for fold, (train_idx, val_idx) in enumerate(folds):
        train_ids = [video_ids[i] for i in train_idx]
        val_ids = [video_ids[i] for i in val_idx]
        for condition in conditions:
            records, best_epoch, best_f1 = train_eval_fold(train_ids, val_ids, seed, fold, condition)
            all_records[condition].extend(records)
            fold_summaries[condition].append({
                'seed': seed, 'fold': fold, 'best_epoch': best_epoch, 'fold_f1': float(best_f1)
            })
            print(f'seed={seed} fold={fold} condition={condition} f1={best_f1:.4f} epoch={best_epoch}', flush=True)

summary = {
    'experiment_id': 'P1-TEMPORAL-PAIRED-118V-2026-09-18',
    'created_utc_epoch': int(time.time()),
    'canonical_goal': 'Mandate V4 P1: paired, seeded, permutation-controlled temporal validation',
    'dataset': {
        'embeddings': 'subhajitdas/chucklenet-scale221',
        'labels': 'subhajitdas/standup4ai-en-uk-labels',
        'label_tier': 'human-verified EMNLP B/I/L/O/U word labels',
        'intersection_videos': len(video_ids),
        'windows': int(sum(len(d['labels']) for d in data.values())),
        'positives': int(sum(int(d['labels'].sum()) for d in data.values())),
        'window_seconds': WIN_SECONDS,
        'window_label_rule': 'positive iff B/I/L word midpoint lies in the 5 s window',
    },
    'model': {
        'architecture': 'BiGRU(797,128,bidirectional)+64+1',
        'features': '791-d WavLM+prosody embeddings + E02 temporal-6',
        'standardization': 'train-fold only',
        'loss': 'BCEWithLogitsLoss pos_weight=8',
        'optimizer': 'AdamW lr=5e-4',
        'final_bias_init': -2.0,
        'grad_clip': GRAD_CLIP,
        'epochs': EPOCHS,
        'early_stopping_patience': PATIENCE,
        'model_selection': 'validation original-order F1@0.5',
    },
    'protocol': {
        'split': f'GroupKFold by video, {N_FOLDS} folds',
        'seeds': SEEDS,
        'conditions': conditions,
        'condition_definition': {
            'true': 'original temporal order',
            'random': 'within-video full random permutation, per seed/fold/video',
            'local_shuffle': 'within-video permutation inside contiguous 25 s blocks',
            'reverse': 'within-video reversal',
        },
        'paired_design': 'same seed/fold/video; model seed fixed across conditions; predictions mapped back to original order',
        'clustered_bootstrap': 'video-ID clusters; all seed/fold observations for each sampled video',
    },
    'overall': {},
    'fold_summaries': fold_summaries,
    'paired_tests': {},
}

for condition in conditions:
    scores = [r['f1'] for r in all_records[condition]]
    fold_scores = [x['fold_f1'] for x in fold_summaries[condition]]
    summary['overall'][condition] = {
        'video_observation_mean_f1': float(np.mean(scores)),
        'video_observation_std_f1': float(np.std(scores)),
        'fold_mean_f1': float(np.mean(fold_scores)),
        'fold_std_f1': float(np.std(fold_scores)),
        'n_observations': len(scores),
    }

# The primary comparison is true vs random.
for control in ['random', 'local_shuffle', 'reverse']:
    paired = clustered_bootstrap_paired(all_records['true'], all_records[control], control)
    summary['paired_tests'][f'true_vs_{control}'] = paired

# Pre-registered interpretation gate.
primary = summary['paired_tests']['true_vs_random']
ci_low, ci_high = primary['bootstrap_ci95']
gate_pass = bool(ci_low > 0 and primary['mean_delta_f1'] > 0.02)
secondary_pass = all(
    summary['paired_tests'][f'true_vs_{c}']['bootstrap_ci95'][0] > 0
    for c in ['local_shuffle', 'reverse']
)
summary['decision_gate'] = {
    'primary_comparison': 'true_vs_random',
    'gate': 'bootstrap CI95 lower bound > 0 AND mean paired delta F1 > 0.02',
    'gate_pass': gate_pass,
    'secondary_control_ci_lower_positive': secondary_pass,
    'verdict': (
        'STRONGER SUPPORTED' if gate_pass and secondary_pass else
        'PARTIAL' if gate_pass else
        'NOT SUPPORTED'
    ),
}
summary['runtime_seconds'] = float(time.time() - t_start)
summary['video_ids'] = video_ids
# Keep per-observation records for audit but not in the top-level summary.
records_path = OUT_DIR / 'p1_temporal_118v_observations.json.gz'
import gzip
with gzip.open(records_path, 'wt', encoding='utf-8') as f:
    json.dump(all_records, f, separators=(',', ':'))

result_path = OUT_DIR / 'p1_temporal_118v_results.json'
result_path.write_text(json.dumps(summary, indent=2))
print(json.dumps({
    'overall': summary['overall'],
    'paired_tests': summary['paired_tests'],
    'decision_gate': summary['decision_gate'],
    'runtime_seconds': summary['runtime_seconds'],
}, indent=2))
print('saved', result_path)
print('saved', records_path)
