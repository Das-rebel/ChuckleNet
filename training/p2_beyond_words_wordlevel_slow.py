#!/usr/bin/env python3
"""
P2 — beyond-words validation on ChuckleNet 118v EMNLP word-level labels.

Protocol: word-level B/I/L classification; compare word-identity-only (TF-IDF)
vs word-identity + pause/temporal features.

Design:
- A: word TF-IDF features only (unigrams from EMNLP transcripts)
- B: A + temporal features (pause before/after, speaking rate, position, word duration)
- Same BiGRU(512) per word sequence; GroupKFold by video; 3 seeds × 5 folds
- Paired per-video aggregated F1 delta; bootstrap CI clustered by video ID

Data: 118-video EMNLP B/I/L/O/U labels + scale221 window embeddings (for timing).
Word sequences derived from EMNLP timestamps; TF-IDF from word text.
Temporal features computed from word-to-word timing.

Mandate V4 P2 gate: B > A with CI lower bound > 0 and Δ > 0.02 F1.
Null is a valid outcome and narrows the thesis.
"""

import ast, glob, hashlib, json, os, time, random, re
from pathlib import Path
import numpy as np, pandas as pd
import torch, torch.nn as nn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import GroupKFold
from sklearn.metrics import f1_score, precision_score, recall_score
from scipy.sparse import issparse

ROOT = Path('/Users/Subho/autonomous_laughter_prediction_essential')
LAB_DIR = Path('/tmp/p1_data/labels/labels')
EMB_DIR = Path('/tmp/p1_data/scale221/embeddings')
OUT_DIR = ROOT / 'results' / 'p2'
OUT_DIR.mkdir(parents=True, exist_ok=True)

WIN_SEC = 5.0
SEEDS = [42, 43, 44]
N_FOLDS = 5
EPOCHS = 50
PATIENCE = 10
POS_WEIGHT = 5.0
LR = 1e-3
GRAD_CLIP = 1.0
MAX_TFIDF_FEATURES = 5000
BOOT_N = 10000
BOOT_SEED = 20260918

TFIDF_CONDITION = 'tfidf_only'
FULL_CONDITION = 'tfidf_plus_temporal'
conditions = [TFIDF_CONDITION, FULL_CONDITION]

DEVICE = 'cpu'


def parse_timestamp(ts):
    try:
        return ast.literal_eval(str(ts))
    except Exception:
        return None


def build_dataset():
    """Load all 118 intersecting videos; returns dict keyed by video_id."""
    emb_files = {os.path.basename(f)[:-4] for f in glob.glob(str(EMB_DIR / '*.npy'))}
    lab_files = {os.path.basename(f)[:-4] for f in glob.glob(str(LAB_DIR / '*.csv'))}
    vids = sorted(emb_files & lab_files)

    word_data = {}  # vid -> DataFrame with text, t_start, t_end, label

    for vid in vids:
        df = pd.read_csv(LAB_DIR / f'{vid}.csv')
        df = df[['text', 'timestamp', 'label']].copy()
        rows = []
        for _, r in df.iterrows():
            ts = parse_timestamp(r['timestamp'])
            if ts is None:
                continue
            rows.append({'text': str(r['text']).strip(), 't_start': ts[0], 't_end': ts[1],
                         'label': r['label']})
        if not rows:
            continue
        wdf = pd.DataFrame(rows)
        wdf = wdf[wdf['label'].isin(('B', 'I', 'L', 'O', 'U'))].reset_index(drop=True)
        word_data[vid] = wdf

    # Load window embeddings to get per-window timing (for pause computation)
    # scale221: [n_windows, 791] where window k starts at k*5.0
    win_data = {}
    for vid in vids:
        emb = np.load(EMB_DIR / f'{vid}.npy')
        n_win = len(emb)
        win_starts = np.arange(n_win) * WIN_SEC
        win_ends = win_starts + WIN_SEC
        win_data[vid] = {'n_windows': n_win, 'win_starts': win_starts, 'win_ends': win_ends}

    # Assign each word to a window index
    for vid in word_data:
        wd = word_data[vid]
        wd['win_idx'] = np.clip(
            ((wd['t_start'] + wd['t_end']) / 2.0 / WIN_SEC).astype(int),
            0, win_data[vid]['n_windows'] - 1
        ).values

    return word_data, win_data


def compute_temporal_features_for_video(wd):
    """Compute per-word temporal features from word timestamps."""
    n = len(wd)
    t_start = wd['t_start'].values.astype(np.float32)
    t_end = wd['t_end'].values.astype(np.float32)

    # Pause before each word = gap between previous word end and this word start
    pause_before = np.zeros(n, dtype=np.float32)
    pause_before[1:] = np.maximum(0.0, t_start[1:] - t_end[:-1])

    # Pause after each word = gap between this word end and next word start
    pause_after = np.zeros(n, dtype=np.float32)
    pause_after[:-1] = np.maximum(0.0, t_start[1:] - t_end[:-1])

    # Word duration
    word_dur = t_end - t_start

    # Speaking rate: chars per second (proxy for articulation speed)
    word_len = wd['text'].str.len().values.astype(np.float32)
    speaking_rate = np.zeros(n, dtype=np.float32)
    nonzero = word_dur > 0
    speaking_rate[nonzero] = word_len[nonzero] / word_dur[nonzero]

    # Relative position in video
    total_dur = t_end[-1] - t_start[0] if n > 1 else 1.0
    rel_pos = (t_start - t_start[0]) / max(total_dur, 1.0)

    return np.stack([
        np.log1p(pause_before),
        np.log1p(pause_after),
        np.log1p(np.clip(word_dur, 0, 10)),
        np.log1p(np.clip(speaking_rate, 0, 100)),
        rel_pos,
        np.log1p(np.clip(pause_before * pause_after, 0, 100)),
    ], axis=1).astype(np.float32)  # [n_words, 6]


def build_word_sequences(word_data, vid_list, tfidf_vectorizer=None, fit_tfidf=False):
    """
    Build word-level sequences for a list of videos.
    Returns X (features), y (labels), temporal_feats, word_texts, and the TF-IDF vectorizer.
    If fit_tfidf=True, fit on the provided videos; else transform using existing vectorizer.
    """
    all_texts = []
    for vid in vid_list:
        wd = word_data[vid]
        all_texts.extend(wd['text'].tolist())

    if fit_tfidf:
        tfidf_vectorizer = TfidfVectorizer(
            max_features=MAX_TFIDF_FEATURES,
            analyzer='word',
            ngram_range=(1, 2),
            min_df=2,
            max_df=0.95,
            sublinear_tf=True,
        )
        tfidf_matrix = tfidf_vectorizer.fit_transform(all_texts)
    else:
        tfidf_matrix = tfidf_vectorizer.transform(all_texts)

    # Split back by video
    X_tfidf_list = []
    X_temporal_list = []
    y_list = []
    seq_lens = []
    for vid in vid_list:
        wd = word_data[vid]
        n = len(wd)
        start = len(X_tfidf_list) if not X_tfidf_list else sum(len(x) for x in X_tfidf_list)
        end = start + n

        X_tfidf_list.append(tfidf_matrix[start:end])
        X_temporal_list.append(compute_temporal_features_for_video(wd))
        y_list.append((wd['label'].isin(('B', 'I', 'L'))).astype(np.int64).values)
        seq_lens.append(n)

    return X_tfidf_list, X_temporal_list, y_list, seq_lens, tfidf_vectorizer


class WordBRNN(nn.Module):
    """Bidirectional RNN over word sequences; handles sparse + dense input."""
    def __init__(self, tfidf_dim, temporal_dim, hidden=128):
        super().__init__()
        self.tfidf_proj = nn.Linear(tfidf_dim, 256) if tfidf_dim > 256 else None
        self.temporal_proj = nn.Linear(temporal_dim, 64) if temporal_dim > 0 else None
        total_dim = (256 if tfidf_dim > 256 else tfidf_dim) + (64 if temporal_dim > 0 else 0)
        self.rnn = nn.GRU(total_dim, hidden, batch_first=True, bidirectional=True)
        self.head = nn.Sequential(
            nn.Linear(2 * hidden, 64),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(64, 1)
        )

    def forward(self, tfidf_x, temporal_x=None):
        h = tfidf_x
        if self.tfidf_proj is not None:
            h = self.tfidf_proj(h)
        if temporal_x is not None and self.temporal_proj is not None:
            h = torch.cat([h, self.temporal_proj(temporal_x)], dim=-1)
        elif temporal_x is not None:
            h = torch.cat([h, temporal_x], dim=-1)
        out, _ = self.rnn(h)
        return self.head(out).squeeze(-1)


def train_eval_fold(tfidf_tr_list, temporal_tr_list, y_tr_list,
                   tfidf_va_list, temporal_va_list, y_va_list,
                   val_vid_list,
                   seed, fold, use_temporal):
    torch.manual_seed(seed)
    np.random.seed(seed)
    random.seed(seed)

    # Determine input dimensions
    tfidf_dim = tfidf_tr_list[0].shape[1] if tfidf_tr_list else 0
    temporal_dim = temporal_tr_list[0].shape[1] if temporal_tr_list and temporal_tr_list[0] is not None else 0

    model = WordBRNN(tfidf_dim, temporal_dim if use_temporal else 0).to(DEVICE)
    crit = nn.BCEWithLogitsLoss(pos_weight=torch.tensor(float(POS_WEIGHT), device=DEVICE))
    opt = torch.optim.AdamW(model.parameters(), lr=LR)
    model.head[-1].bias.data.fill_(-2.0)

    best_f1 = -1.0
    best_state = None
    best_epoch = -1

    for ep in range(EPOCHS):
        model.train()
        for vi, (tfidf_v, temp_v, y_v) in enumerate(zip(tfidf_tr_list, temporal_tr_list, y_tr_list)):
            tfidf_t = torch.from_numpy(tfidf_v.toarray() if issparse(tfidf_v) else tfidf_v).float().to(DEVICE)
            y_t = torch.from_numpy(y_v).float().to(DEVICE)
            temp_t = (torch.from_numpy(temp_v).float().to(DEVICE) if use_temporal and temp_v is not None
                      else torch.zeros(tfidf_t.shape[0], 0).float().to(DEVICE))

            # Shuffle within video
            perm = torch.randperm(len(tfidf_t))
            tfidf_t = tfidf_t[perm]
            temp_t = temp_t[perm]
            y_t = y_t[perm]

            # Chunk into manageable batches
            for start in range(0, len(tfidf_t), 64):
                end = min(start + 64, len(tfidf_t))
                opt.zero_grad()
                out = model(tfidf_t[start:end], temp_t[start:end] if use_temporal else None)
                crit(out, y_t[start:end]).backward()
                nn.utils.clip_grad_norm_(model.parameters(), GRAD_CLIP)
                opt.step()

        model.eval()
        all_preds, all_labels, all_vids = [], [], []
        with torch.no_grad():
            for vi, (tfidf_v, temp_v, y_v) in enumerate(zip(tfidf_va_list, temporal_va_list, y_va_list)):
                tfidf_t = torch.from_numpy(tfidf_v.toarray() if issparse(tfidf_v) else tfidf_v).float().to(DEVICE)
                temp_t = (torch.from_numpy(temp_v).float().to(DEVICE) if use_temporal and temp_v is not None
                          else torch.zeros(tfidf_t.shape[0], 0).float().to(DEVICE))
                preds = torch.sigmoid(model(tfidf_t, temp_t if use_temporal else None)).cpu().numpy()
                all_preds.append(preds)
                all_labels.append(y_v)
                all_vids.extend([val_vid_list[vi]] * len(y_v))

        pv = np.concatenate(all_preds)
        yt = np.concatenate(all_labels)
        score = f1_score(yt, (pv > 0.5).astype(int), zero_division=0)
        if score > best_f1:
            best_f1 = score
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
            best_epoch = ep
        elif ep - best_epoch >= PATIENCE:
            break

    if best_state is None:
        best_state = model.state_dict()
        best_epoch = 0
    model.load_state_dict(best_state)
    model.eval()

    # Collect per-word predictions and labels
    records = []
    with torch.no_grad():
        for vi, (tfidf_v, temp_v, y_v) in enumerate(zip(tfidf_va_list, temporal_va_list, y_va_list)):
            tfidf_t = torch.from_numpy(tfidf_v.toarray() if issparse(tfidf_v) else tfidf_v).float().to(DEVICE)
            temp_t = (torch.from_numpy(temp_v).float().to(DEVICE) if use_temporal and temp_v is not None
                      else torch.zeros(tfidf_t.shape[0], 0).float().to(DEVICE))
            preds = torch.sigmoid(model(tfidf_t, temp_t if use_temporal else None)).cpu().numpy()
            vid = val_vid_list[vi]
            for j, (p, l) in enumerate(zip(preds, y_v)):
                records.append({
                    'seed': seed, 'fold': fold, 'video': vid,
                    'word_idx': j, 'pred': float(p), 'label': int(l),
                    'f1': float(f1_score([l], [int(p > 0.5)], zero_division=0))
                })
    return records, best_epoch, best_f1


def clustered_bootstrap_paired(records_a, records_b, name_a, name_b, n_boot=BOOT_N, rng_seed=BOOT_SEED):
    """Paired bootstrap on per-video mean F1 delta, clustered by video ID."""
    # Aggregate to video-level mean F1 per seed/fold/video
    def video_stats(records):
        import pandas as pd
        df = pd.DataFrame(records)
        return df.groupby('video')['f1'].mean().to_dict()

    stats_a = video_stats(records_a)
    stats_b = video_stats(records_b)
    videos = sorted(set(stats_a) & set(stats_b))
    deltas = [stats_a[v] - stats_b[v] for v in videos]

    improved = sum(1 for d in deltas if d > 1e-12)
    worsened = sum(1 for d in deltas if d < -1e-12)
    unchanged = sum(1 for d in deltas if abs(d) <= 1e-12)

    boot = np.zeros(n_boot)
    rng = np.random.default_rng(rng_seed)
    for b in range(n_boot):
        sample_vids = rng.choice(videos, size=len(videos), replace=True)
        boot[b] = np.mean([stats_a[v] - stats_b[v] for v in sample_vids])

    mean_delta = np.mean(deltas)
    return {
        f'{name_a}_minus_{name_b}': {
            'mean_delta_f1': float(mean_delta),
            'median_delta_f1': float(np.median(deltas)),
            'bootstrap_ci95': [float(np.quantile(boot, 0.025)), float(np.quantile(boot, 0.975))],
            'n_videos': len(videos),
            'improved': improved,
            'worsened': worsened,
            'unchanged': unchanged,
            'bootstrap_seed': int(rng_seed),
            'bootstrap_resamples': int(n_boot),
        }
    }


print("Building dataset…", flush=True)
t0 = time.time()
word_data, win_data = build_dataset()
vids = sorted(word_data.keys())
print(f"videos={len(vids)} | total_words={sum(len(word_data[v]) for v in vids)} "
      f"| total_pos={sum(int(word_data[v]["label"].isin(("B","I","L")).sum()) for v in vids)} "
      f"| time={time.time()-t0:.0f}s", flush=True)

# Compute temporal features for all videos once
print("Computing temporal features…", flush=True)
temporal_all = {vid: compute_temporal_features_for_video(word_data[vid]) for vid in vids}

# Fit TF-IDF on all words across all videos (using training fold only in actual experiment)
all_words_flat = [w for vid in vids for w in word_data[vid]['text'].tolist()]
_tfidf_global = TfidfVectorizer(
    max_features=MAX_TFIDF_FEATURES,
    analyzer='word', ngram_range=(1, 2), min_df=2, max_df=0.95, sublinear_tf=True,
)
_tfidf_global.fit(all_words_flat)
tfidf_dim = min(len(_tfidf_global.vocabulary_), MAX_TFIDF_FEATURES)
print(f"TF-IDF vocabulary: {tfidf_dim} features", flush=True)

# Build TF-IDF per video
print("Building TF-IDF vectors…", flush=True)
tfidf_all = {}
for vid in vids:
    tfidf_all[vid] = _tfidf_global.transform(word_data[vid]['text'].tolist())

# Labels per video
labels_all = {vid: (word_data[vid]['label'].isin(('B', 'I', 'L'))).astype(np.int64).values for vid in vids}

# Create folds
groups = np.array(vids)
folds = list(GroupKFold(n_splits=N_FOLDS).split(np.zeros(len(vids)), groups=groups))

all_records = {TFIDF_CONDITION: [], FULL_CONDITION: []}
fold_summaries = {TFIDF_CONDITION: [], FULL_CONDITION: []}

print(f"\nRunning P2 beyond-words: {N_FOLDS} folds × {len(SEEDS)} seeds × {len(conditions)} conditions\n",
      flush=True)

for seed in SEEDS:
    for fold_idx, (train_idx, val_idx) in enumerate(folds):
        tr_vids = [vids[i] for i in train_idx]
        va_vids = [vids[i] for i in val_idx]

        # Fit TF-IDF on training videos only (no leakage)
        tfidf_fit_words = [w for vid in tr_vids for w in word_data[vid]['text'].tolist()]
        tfidf_vectorizer = TfidfVectorizer(
            max_features=MAX_TFIDF_FEATURES,
            analyzer='word', ngram_range=(1, 2), min_df=2, max_df=0.95, sublinear_tf=True,
        )
        tfidf_vectorizer.fit(tfidf_fit_words)
        actual_dim = min(len(tfidf_vectorizer.vocabulary_), MAX_TFIDF_FEATURES)

        # Build training data
        tfidf_tr = [tfidf_vectorizer.transform(word_data[v]['text'].tolist()) for v in tr_vids]
        temporal_tr = [temporal_all[v] for v in tr_vids]
        y_tr = [labels_all[v] for v in tr_vids]

        # Build validation data
        tfidf_va = [tfidf_vectorizer.transform(word_data[v]['text'].tolist()) for v in va_vids]
        temporal_va = [temporal_all[v] for v in va_vids]
        y_va = [labels_all[v] for v in va_vids]

        # Condition A: TF-IDF only (temporal features set to zero)
        zero_temporal_tr = [np.zeros_like(t) for t in temporal_tr]
        zero_temporal_va = [np.zeros_like(t) for t in temporal_va]

        for cond, use_temporal in [(TFIDF_CONDITION, False), (FULL_CONDITION, True)]:
            tf_t = temporal_tr if use_temporal else zero_temporal_tr
            tf_v = temporal_va if use_temporal else zero_temporal_va

            records, best_epoch, best_f1 = train_eval_fold(
                tfidf_tr, tf_t, y_tr,
                tfidf_va, tf_v, y_va,
                va_vids,
                seed, fold_idx, use_temporal
            )
            all_records[cond].extend(records)
            fold_summaries[cond].append({
                'seed': seed, 'fold': fold_idx, 'best_epoch': best_epoch, 'fold_f1': float(best_f1)
            })
            print(f"  seed={seed} fold={fold_idx} cond={cond} f1={best_f1:.4f} ep={best_epoch}", flush=True)

# Aggregate results
summary = {
    'experiment_id': 'P2-BEYOND-WORDS-118V-2026-09-18',
    'created_utc_epoch': int(time.time()),
    'canonical_goal': 'Mandate V4 P2: beyond-words incremental information test',
    'protocol': {
        'task': 'word-level B/I/L classification from EMNLP word sequences',
        'baseline': 'TF-IDF word unigrams+bigrams (semantic baseline)',
        'full': 'TF-IDF + 6 pause/temporal features (pause before/after, word duration, speaking rate, rel position, pause product)',
        'model': 'BiGRU(256proj+64temp→128→64→1), BCE pos_weight=5, AdamW 1e-3, bias init -2',
        'split': f'GroupKFold by video, {N_FOLDS} folds',
        'seeds': SEEDS,
        'tfidf_vocabulary': actual_dim,
        'paired_design': 'same seed/fold/videos; TF-IDF fit on training fold only',
        'clustered_bootstrap': 'video-level mean F1 delta, resample video IDs',
    },
    'overall': {},
    'fold_summaries': fold_summaries,
    'paired_tests': {},
}

# Compute overall stats per condition
for cond in conditions:
    scores = [r['f1'] for r in all_records[cond]]
    fold_scores = [x['fold_f1'] for x in fold_summaries[cond]]
    summary['overall'][cond] = {
        'word_observation_mean_f1': float(np.mean(scores)),
        'word_observation_std_f1': float(np.std(scores)),
        'fold_mean_f1': float(np.mean(fold_scores)),
        'fold_std_f1': float(np.std(fold_scores)),
        'n_observations': len(scores),
    }

# Primary paired test: tfidf_plus_temporal vs tfidf_only
paired = clustered_bootstrap_paired(
    all_records[TFIDF_CONDITION], all_records[FULL_CONDITION],
    TFIDF_CONDITION, FULL_CONDITION
)
summary['paired_tests'] = paired

# Decision gate
delta = paired[f'{TFIDF_CONDITION}_minus_{FULL_CONDITION}']
ci_low, ci_high = delta['bootstrap_ci95']
mean_d = delta['mean_delta_f1']
gate_pass = bool(ci_low > 0 and mean_d > 0.02)
summary['decision_gate'] = {
    'comparison': f'{FULL_CONDITION} vs {TFIDF_CONDITION}',
    'gate': 'CI95 lower > 0 AND mean Δ > 0.02 F1',
    'gate_pass': gate_pass,
    'mean_delta_f1': float(mean_d),
    'ci95': [float(ci_low), float(ci_high)],
    'verdict': 'BEYOND-WORDS SUPPORTED' if gate_pass else ('PARTIAL' if ci_low > 0 else 'NOT SUPPORTED'),
}
summary['runtime_seconds'] = float(time.time() - t0)

# Save
result_path = OUT_DIR / 'p2_beyond_words_results.json'
result_path.write_text(json.dumps(summary, indent=2))
records_gz_path = OUT_DIR / 'p2_beyond_words_observations.json.gz'
import gzip
with gzip.open(records_gz_path, 'wt', encoding='utf-8') as f:
    json.dump(all_records, f, separators=(',', ':'))

print(json.dumps({
    'overall': summary['overall'],
    'paired_tests': summary['paired_tests'],
    'decision_gate': summary['decision_gate'],
    'runtime_seconds': summary['runtime_seconds'],
}, indent=2))
print(f"\nsaved {result_path}")
print(f"saved {records_gz_path}")
