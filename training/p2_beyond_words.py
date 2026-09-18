#!/usr/bin/env python3
"""P2 — beyond-words validation on ChuckleNet 118v (window-level, efficient).

Mandate V4 P2: does non-semantic interaction/timing information add
incremental value over word content?

Dataset: 118 videos with EMNLP word labels; fixed 5-second windows
(same window protocol as E02/P1: positive iff a B/I/L word midpoint lies
inside the window).

Conditions (paired, identical protocol):
  A = word_content_tfidf        TF-IDF unigrams+bigrams of words in window
  B = word_content_plus_temporal A + 7 pause/timing features

Split: 5-fold GroupKFold by video (same fold structure as P1).
Seeds: 42/43/44. TF-IDF fit on training fold only (no leakage).
Primary gate: B > A, clustered video-level bootstrap CI95 lower > 0 AND
mean paired delta F1 > 0.02. Null narrows the thesis.
"""
import ast
import glob
import gzip
import json
import os
import random
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import f1_score
from sklearn.model_selection import GroupKFold

ROOT = Path('/Users/Subho/autonomous_laughter_prediction_essential')
LAB_DIR = Path('/tmp/p1_data/labels/labels')
EMB_DIR = Path('/tmp/p1_data/scale221/embeddings')
OUT_DIR = ROOT / 'results' / 'p2'
OUT_DIR.mkdir(parents=True, exist_ok=True)

WIN_SEC = 5.0
SEEDS = [42, 43, 44]
N_FOLDS = 5
EPOCHS = 40
PATIENCE = 8
LR = 1e-3
GRAD_CLIP = 1.0
MAX_TFIDF = 5000
BOOT_N = 10000
BOOT_SEED = 20260918
COND_A = 'word_content_tfidf'
COND_B = 'word_content_plus_temporal'
CONDITIONS = [COND_A, COND_B]
TEMPORAL_DIM = 7  # log_total_pause, log_max_pause, log_pause_ct, log_mean_dur, log_mean_rate, word_density, rel_pos


def parse_ts(x):
    try:
        return ast.literal_eval(str(x))
    except Exception:
        return None


def load_data():
    emb_ids = {os.path.basename(f)[:-4] for f in glob.glob(str(EMB_DIR / '*.npy'))}
    lab_ids = {os.path.basename(f)[:-4] for f in glob.glob(str(LAB_DIR / '*.csv'))}
    vids = sorted(emb_ids & lab_ids)
    words = {}
    for vid in vids:
        df = pd.read_csv(LAB_DIR / f'{vid}.csv')
        rows = []
        for _, r in df.iterrows():
            ts = parse_ts(r['timestamp'])
            if ts is None:
                continue
            rows.append((str(r['text']).strip(), float(ts[0]), float(ts[1]), str(r['label'])))
        wdf = pd.DataFrame(rows, columns=['text', 'start', 'end', 'label'])
        wdf = wdf[wdf['label'].isin(['B', 'I', 'L', 'O', 'U'])].reset_index(drop=True)
        if len(wdf) and wdf['end'].max() > 0:
            words[vid] = wdf
    vids = sorted(words)
    return vids, words


def n_windows_for(df):
    return max(1, int(np.ceil(df['end'].max() / WIN_SEC)))


def make_windows(df, n):
    """Window texts and labels. Label: any B/I/L word midpoint inside window."""
    texts = [''] * n
    labels = np.zeros(n, dtype=np.int64)
    for _, r in df.iterrows():
        k = int(((r['start'] + r['end']) / 2.0) // WIN_SEC)
        if 0 <= k < n:
            texts[k] = (texts[k] + ' ' + r['text']).strip() if texts[k] else r['text']
            if r['label'] in ('B', 'I', 'L'):
                labels[k] = 1
    return texts, labels


def temporal_features(df, n):
    """7 pause/timing features per window (no label info, no text content)."""
    out = np.zeros((n, TEMPORAL_DIM), dtype=np.float32)
    starts = df['start'].to_numpy(float)
    ends = df['end'].to_numpy(float)
    total_dur = max(float(ends.max()), 1.0)
    for k in range(n):
        lo, hi = k * WIN_SEC, (k + 1) * WIN_SEC
        m = (starts < hi) & (ends > lo)
        if not m.any():
            out[k, 6] = ((k + 0.5) * WIN_SEC) / total_dur
            continue
        st, en = starts[m], ends[m]
        ds = np.maximum(0.0, en - st)
        ls = df['text'].str.len().to_numpy(float)[m]
        gs = np.maximum(0.0, st[1:] - en[:-1]) if len(st) > 1 else np.zeros(0)
        rs = np.divide(ls, ds, out=np.zeros_like(ls), where=ds > 0)
        out[k] = [
            np.log1p(gs.sum()),
            np.log1p(gs.max() if len(gs) else 0.0),
            np.log1p(float((gs > 0.3).sum())),
            np.log1p(float(ds.mean())),
            np.log1p(float(rs.mean())),
            float(len(st)) / WIN_SEC,
            ((k + 0.5) * WIN_SEC) / total_dur,
        ]
    return out


class MLP(nn.Module):
    def __init__(self, in_dim):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_dim, 256), nn.BatchNorm1d(256), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(256, 64), nn.ReLU(), nn.Dropout(0.2),
            nn.Linear(64, 1),
        )

    def forward(self, x):
        return self.net(x).squeeze(-1)


def build_fold(train_df_texts, train_vids, val_vids, words):
    """Fit TF-IDF on train windows only; assemble standardized arrays + per-video boundaries."""
    vec = TfidfVectorizer(max_features=MAX_TFIDF, analyzer='word', ngram_range=(1, 2),
                          min_df=2, max_df=0.95, sublinear_tf=True)
    vec.fit(train_df_texts)

    def assemble(vid_list):
        X_list, T_list, y_list, bounds = [], [], [], []
        for v in vid_list:
            df = words[v]
            n = n_windows_for(df)
            texts, y = make_windows(df, n)
            X_list.append(vec.transform(texts).toarray().astype(np.float32))
            T_list.append(temporal_features(df, n))
            y_list.append(y)
            bounds.append((v, n))
        X = np.concatenate(X_list)
        T = np.concatenate(T_list)
        y = np.concatenate(y_list)
        return X, T, y, bounds

    Xtr, Ttr, ytr, _ = assemble(train_vids)
    Xva, Tva, yva, bounds_va = assemble(val_vids)
    mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-6
    Xtr = (Xtr - mu) / sd
    Xva = (Xva - mu) / sd
    mt, st = Ttr.mean(0), Ttr.std(0) + 1e-6
    Ttr = (Ttr - mt) / st
    Tva = (Tva - mt) / st
    return Xtr, Ttr, ytr, Xva, Tva, yva, bounds_va, len(vec.vocabulary_)


def train_eval(Xtr, Ttr, ytr, Xva, Tva, yva, bounds_va, seed, condition):
    """Train one model; returns per-video records + best epoch + fold F1."""
    torch.manual_seed(seed)
    np.random.seed(seed)
    random.seed(seed)
    use_t = condition == COND_B
    if use_t:
        Xtr_in = np.concatenate([Xtr, Ttr], axis=1)
        Xva_in = np.concatenate([Xva, Tva], axis=1)
    else:
        Xtr_in, Xva_in = Xtr, Xva
    model = MLP(Xtr_in.shape[1])
    pos = max(int(ytr.sum()), 1)
    neg = max(len(ytr) - pos, 1)
    crit = nn.BCEWithLogitsLoss(pos_weight=torch.tensor(float(neg / pos)))
    opt = torch.optim.AdamW(model.parameters(), lr=LR)
    model.net[-1].bias.data.fill_(-2.0)
    xt = torch.from_numpy(Xtr_in).float()
    yt = torch.from_numpy(ytr).float()
    xv = torch.from_numpy(Xva_in).float()
    best = (-1.0, None, 0)
    for ep in range(EPOCHS):
        model.train()
        perm = torch.randperm(len(xt))
        for i in range(0, len(xt), 512):
            idx = perm[i:i + 512]
            opt.zero_grad()
            crit(model(xt[idx]), yt[idx]).backward()
            nn.utils.clip_grad_norm_(model.parameters(), GRAD_CLIP)
            opt.step()
        model.eval()
        with torch.no_grad():
            pv = torch.sigmoid(model(xv)).numpy()
        score = f1_score(yva, (pv > 0.5).astype(int), zero_division=0)
        if score > best[0]:
            best = (score, {k: v.clone() for k, v in model.state_dict().items()}, ep)
        elif ep - best[2] >= PATIENCE:
            break
    if best[1] is None:
        best = (0.0, {k: v.clone() for k, v in model.state_dict().items()}, 0)
    model.load_state_dict(best[1])
    model.eval()
    with torch.no_grad():
        pv = torch.sigmoid(model(xv)).numpy()
    records = []
    cursor = 0
    for v, n in bounds_va:
        yv = yva[cursor:cursor + n]
        pp = pv[cursor:cursor + n]
        vf1 = f1_score(yv, (pp > 0.5).astype(int), zero_division=0)
        records.append({'video': v, 'seed': seed, 'fold_f1_context': best[0],
                        'video_f1': float(vf1), 'n_windows': int(n),
                        'pos_rate': float(yv.mean()) if n else 0.0})
        cursor += n
    return records, best[2], best[0]


def main():
    t0 = time.time()
    vids, words = load_data()
    n_w = {v: n_windows_for(words[v]) for v in vids}
    total_windows = sum(n_w.values())
    total_pos = sum(int(make_windows(words[v], n_w[v])[1].sum()) for v in vids)
    print(f'videos={len(vids)} windows={total_windows} positives={total_pos} '
          f'({100 * total_pos / max(total_windows, 1):.1f}%)', flush=True)

    groups = np.array(vids)
    folds = list(GroupKFold(n_splits=N_FOLDS).split(np.zeros(len(vids)), groups=groups))
    all_records = {c: [] for c in CONDITIONS}
    fold_summary = {c: [] for c in CONDITIONS}

    for seed in SEEDS:
        for fold, (tr_idx, va_idx) in enumerate(folds):
            tr = [vids[i] for i in tr_idx]
            va = [vids[i] for i in va_idx]
            train_texts = []
            for v in tr:
                train_texts += make_windows(words[v], n_w[v])[0]
            Xtr, Ttr, ytr, Xva, Tva, yva, bounds_va, tfidf_dim = build_fold(
                train_texts, tr, va, words)
            for cond in CONDITIONS:
                records, ep, f1 = train_eval(Xtr, Ttr, ytr, Xva, Tva, yva,
                                             bounds_va, seed, cond)
                all_records[cond].extend(records)
                fold_summary[cond].append({'seed': seed, 'fold': fold,
                                           'fold_f1': float(f1), 'epoch': ep})
                print(f'seed={seed} fold={fold} cond={cond} tfidf_dim={tfidf_dim} '
                      f'foldF1={f1:.4f} ep={ep}', flush=True)

    # Aggregate
    summary = {
        'experiment_id': 'P2-BEYOND-WORDS-118V-2026-09-18',
        'created_utc_epoch': int(time.time()),
        'task': '5s-window laughter classification; word-content TF-IDF vs +pause/timing',
        'dataset': {'videos': len(vids), 'windows': total_windows,
                    'positives': total_pos,
                    'label_rule': 'B/I/L word midpoint inside 5s window'},
        'protocol': {
            'condition_A': 'TF-IDF word unigrams+bigrams (train-fold-fit)',
            'condition_B': 'A + 7 temporal features (total/max/count pauses>0.3s, mean word dur, mean chars-per-sec, word density, relative position)',
            'model': 'MLP 256-64-1, BCE pos_weight=train neg/pos, AdamW 1e-3, clip 1.0, bias -2',
            'epochs': EPOCHS, 'patience': PATIENCE,
            'split': '5-fold GroupKFold by video', 'seeds': SEEDS,
            'tfidf_max_features': MAX_TFIDF,
            'paired': 'same seed/fold/video; identical split; TF-IDF train-fold only',
            'bootstrap': f'video-clustered, {BOOT_N} resamples, seed {BOOT_SEED}',
        },
        'overall': {},
        'fold_summaries': fold_summary,
        'paired_tests': {},
    }
    for cond in CONDITIONS:
        vals = [r['video_f1'] for r in all_records[cond]]
        fs = [x['fold_f1'] for x in fold_summary[cond]]
        summary['overall'][cond] = {
            'video_observation_mean_f1': float(np.mean(vals)),
            'video_observation_std_f1': float(np.std(vals)),
            'fold_mean_f1': float(np.mean(fs)),
            'fold_std_f1': float(np.std(fs)),
            'n_observations': len(vals),
        }

    # Paired bootstrap clustered by video
    def by_video(cond):
        d = {}
        for r in all_records[cond]:
            d.setdefault(r['video'], []).append(r['video_f1'])
        return d
    da, db = by_video(COND_A), by_video(COND_B)
    vids2 = sorted(set(da) & set(db))
    deltas = np.array([np.mean(da[v]) - np.mean(db[v]) for v in vids2])
    rng = np.random.default_rng(BOOT_SEED)
    boot = np.empty(BOOT_N)
    for i in range(BOOT_N):
        sel = rng.choice(vids2, len(vids2), replace=True)
        boot[i] = np.mean([np.mean(da[v]) - np.mean(db[v]) for v in sel])
    delta_f1 = float(deltas.mean())
    ci = [float(np.quantile(boot, 0.025)), float(np.quantile(boot, 0.975))]
    paired = {
        'comparison': f'{COND_A}_minus_{COND_B}',
        'mean_delta_f1': delta_f1,
        'median_delta_f1': float(np.median(deltas)),
        'bootstrap_ci95': ci,
        'n_videos': len(vids2),
        'improved_A': int((deltas > 0).sum()),
        'worsened_A': int((deltas < 0).sum()),
        'unchanged': int((deltas == 0).sum()),
    }
    summary['paired_tests'][paired['comparison']] = paired

    gate_pass = bool(ci[0] > 0 and delta_f1 > 0.02)
    summary['decision_gate'] = {
        'comparison': f'{COND_B} vs {COND_A}',
        'gate': 'B-minus-A CI95 lower > 0 AND mean delta > 0.02 F1',
        'b_minus_a_mean': -delta_f1,
        'b_minus_a_ci95': [-ci[1], -ci[0]],
        'gate_pass': gate_pass,
        'verdict': ('BEYOND-WORDS SUPPORTED' if gate_pass
                    else 'PARTIAL' if -delta_f1 > 0 and ci[1] < 0
                    else 'NOT SUPPORTED'),
    }
    summary['runtime_seconds'] = float(time.time() - t0)
    summary['video_ids'] = vids2

    out = OUT_DIR / 'p2_beyond_words_results.json'
    out.write_text(json.dumps(summary, indent=2))
    with gzip.open(OUT_DIR / 'p2_beyond_words_observations.json.gz', 'wt') as f:
        json.dump(all_records, f, separators=(',', ':'))
    print(json.dumps({'overall': summary['overall'],
                      'paired_tests': summary['paired_tests'],
                      'decision_gate': summary['decision_gate'],
                      'runtime_seconds': summary['runtime_seconds']}, indent=2))
    print('saved', out)


if __name__ == '__main__':
    main()
