#!/usr/bin/env python3
"""P2 Level A — prospective laughter-onset prediction (pre-registered 2026-09-18).

Task: for each window t, predict whether window t+1 contains a laughter word
(B/I/L midpoint). Features use ONLY information from windows <= t. The
concurrent-content confound is structurally removed.

Arms (identical MLP 256-64-1, 5-fold GroupKFold, seeds 42/43/44):
  position_only            rel. position of t (shortcut control)
  words_before             cumulative TF-IDF up to and incl. window t
  words_before_plus_timing B + 6 timing-of-context features
  acoustic_before          [mean WavLM emb t-2..t, emb t, position]
  acoustic_plus_words      acoustic_before + words_before + timing

Primary gates (video-clustered bootstrap, 10k): CI95 lower > 0 AND dF1 > 0.02
  G1: acoustic_plus_words - words_before   (H4-prospective)
  G2: words_before_plus_timing - words_before (timing)
  G3: acoustic_before - words_before       (acoustic alone)
Reported: words_before - position_only (shortcut quantification).
"""
import ast, glob, gzip, json, os, random, time
from pathlib import Path
import numpy as np, pandas as pd
import torch, torch.nn as nn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import f1_score
from sklearn.model_selection import GroupKFold

ROOT = Path('/Users/Subho/autonomous_laughter_prediction_essential')
LAB_DIR = Path('/tmp/p1_data/labels/labels')
EMB_DIR = Path('/tmp/p1_data/scale221/embeddings')
OUT_DIR = ROOT / 'results' / 'p2_level_a'
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

ARMS = ['position_only', 'words_before', 'words_before_plus_timing',
        'acoustic_before', 'acoustic_plus_words']
TIMING_DIM = 6
ACOUSTIC_DIM = 791 + 1  # mean(3) + last + position -> actually 791*? see below
# acoustic feature vector = [mean emb of trailing<=3 windows (791), emb of t (791), position (1)] = 1583

def parse_ts(x):
    try:
        return ast.literal_eval(str(x))
    except Exception:
        return None

def load():
    emb_ids = {os.path.basename(f)[:-4] for f in glob.glob(str(EMB_DIR / '*.npy'))}
    lab_ids = {os.path.basename(f)[:-4] for f in glob.glob(str(LAB_DIR / '*.csv'))}
    vids = sorted(emb_ids & lab_ids)
    words, embs = {}, {}
    for v in vids:
        df = pd.read_csv(LAB_DIR / f'{v}.csv')
        rows = []
        for _, r in df.iterrows():
            ts = parse_ts(r['timestamp'])
            if ts is None:
                continue
            rows.append((str(r['text']).strip(), float(ts[0]), float(ts[1]), str(r['label'])))
        wdf = pd.DataFrame(rows, columns=['text', 'start', 'end', 'label'])
        wdf = wdf[wdf['label'].isin(['B', 'I', 'L', 'O', 'U'])].reset_index(drop=True)
        if not len(wdf) or wdf['end'].max() <= 0:
            continue
        words[v] = wdf
        embs[v] = np.nan_to_num(np.load(EMB_DIR / f'{v}.npy').astype(np.float32))
    return sorted(words), words, embs

def n_windows_for(df):
    return max(1, int(np.ceil(df['end'].max() / WIN_SEC)))

def window_words_and_labels(df, n):
    texts = [''] * n
    labels = np.zeros(n, dtype=np.int64)
    for _, r in df.iterrows():
        k = int(((r['start'] + r['end']) / 2.0) // WIN_SEC)
        if 0 <= k < n:
            texts[k] = (texts[k] + ' ' + r['text']).strip() if texts[k] else r['text']
            if r['label'] in ('B', 'I', 'L'):
                labels[k] = 1
    return texts, labels

def context_timing(texts, df, n):
    """Timing features of context (windows <= t), trailing 3 windows + cumulative pause info."""
    out = np.zeros((n, TIMING_DIM), dtype=np.float32)
    starts = df['start'].to_numpy(float); ends = df['end'].to_numpy(float)
    # per-window aggregates
    pw_pause = np.zeros(n); pw_rate = np.zeros(n); pw_count = np.zeros(n)
    for k in range(n):
        lo, hi = k * WIN_SEC, (k + 1) * WIN_SEC
        m = (starts < hi) & (ends > lo)
        if not m.any():
            continue
        st, en = starts[m], ends[m]
        g = np.maximum(0.0, st[1:] - en[:-1]) if len(st) > 1 else np.zeros(0)
        d = np.maximum(0.0, en - st)
        ls = df['text'].str.len().to_numpy(float)[m]
        r = np.divide(ls, d, out=np.zeros_like(ls), where=d > 0)
        pw_pause[k] = g.sum(); pw_rate[k] = r.mean() if len(r) else 0.0
        pw_count[k] = len(st)
    for t in range(n):
        trail = slice(max(0, t - 2), t + 1)
        out[t] = [
            np.log1p(pw_pause[trail].sum() / 3.0),
            np.log1p(pw_pause[trail].max()),
            np.log1p(pw_count[trail].sum() / 3.0),
            np.log1p(pw_rate[t]),
            np.log1p(pw_pause[t]),
            float(t) / max(n - 1, 1),
        ]
    return out

def build_fold(vids, words, embs, tr_idx, va_idx):
    tr = [vids[i] for i in tr_idx]; va = [vids[i] for i in va_idx]
    # per-video: texts, labels, shifted target
    per = {}
    for v in vids:
        n = n_windows_for(words[v])
        texts, y = window_words_and_labels(words[v], n)
        # target: laugh in NEXT window (shift -1); last window has no target -> drop
        tgt = np.zeros(n, dtype=np.int64)
        tgt[:-1] = y[1:]
        per[v] = dict(n=n, texts=texts, y=y, tgt=tgt, timing=context_timing(texts, words[v], n))
    # cumulative text per window (context up to incl. t)
    for v in vids:
        texts = per[v]['texts']
        cum = []
        acc = ''
        for tx in texts:
            acc = (acc + ' ' + tx).strip()
            cum.append(acc)
        per[v]['cum'] = cum
    # TF-IDF on training cumulative texts only
    fit_texts = []
    for v in tr:
        fit_texts += per[v]['cum']
    vec = TfidfVectorizer(max_features=MAX_TFIDF, analyzer='word', ngram_range=(1, 2),
                          min_df=2, max_df=0.95, sublinear_tf=True)
    vec.fit(fit_texts)
    def acoustic(v):
        n = per[v]['n']; E = embs[v]
        d = min(n, E.shape[0])
        A = np.zeros((n, 791), dtype=np.float32)
        L = np.zeros((n, 791), dtype=np.float32)
        A[:d] = E[:d]; L[:d] = E[:d]
        for t in range(n):
            lo = max(0, t - 2)
            A[t] = E[lo:min(t + 1, E.shape[0])].mean(axis=0) if t < E.shape[0] else 0.0
        pos = (np.arange(n, dtype=np.float32) / max(n - 1, 1))[:, None]
        return np.concatenate([A, L, pos], axis=1)  # 1583
    def assemble(vid_list):
        X = {a: [] for a in ARMS}; Y = []
        bounds = []
        for v in vid_list:
            p = per[v]; n = p['n']
            W = vec.transform(p['cum']).toarray().astype(np.float32)
            T = p['timing']; A = acoustic(v)
            pos = np.zeros((n, 1), dtype=np.float32)
            pos[:, 0] = np.arange(n, dtype=np.float32) / max(n - 1, 1)
            X['position_only'].append(pos)
            X['words_before'].append(W)
            X['words_before_plus_timing'].append(np.concatenate([W, T], 1))
            X['acoustic_before'].append(A)
            X['acoustic_plus_words'].append(np.concatenate([A, W, T], 1))
            Y.append(p['tgt'])
            bounds.append((v, n))
        return {a: np.concatenate(X[a]) for a in ARMS}, np.concatenate(Y), bounds
    Xtr, ytr, _ = assemble(tr)
    Xva, yva, bounds_va = assemble(va)
    # standardize per arm (train stats)
    for a in ARMS:
        mu, sd = Xtr[a].mean(0), Xtr[a].std(0) + 1e-6
        Xtr[a] = (Xtr[a] - mu) / sd
        Xva[a] = (Xva[a] - mu) / sd
    return Xtr, ytr, Xva, yva, bounds_va

class MLP(nn.Module):
    def __init__(self, d):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(d, 256), nn.BatchNorm1d(256), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(256, 64), nn.ReLU(), nn.Dropout(0.2), nn.Linear(64, 1))
    def forward(self, x):
        return self.net(x).squeeze(-1)

def train_eval(Xtr, ytr, Xv, yv, bounds_va, seed, arm):
    torch.manual_seed(seed); np.random.seed(seed); random.seed(seed)
    model = MLP(Xtr.shape[1])
    pos = max(int(ytr.sum()), 1); neg = max(len(ytr) - pos, 1)
    crit = nn.BCEWithLogitsLoss(pos_weight=torch.tensor(float(neg / pos)))
    opt = torch.optim.AdamW(model.parameters(), lr=LR)
    model.net[-1].bias.data.fill_(-2.0)
    xt = torch.from_numpy(Xtr).float(); yt = torch.from_numpy(ytr).float()
    xv = torch.from_numpy(Xv).float()
    best = (-1.0, None, 0)
    for ep in range(EPOCHS):
        model.train(); perm = torch.randperm(len(xt))
        for i in range(0, len(xt), 512):
            idx = perm[i:i + 512]
            opt.zero_grad(); crit(model(xt[idx]), yt[idx]).backward()
            nn.utils.clip_grad_norm_(model.parameters(), GRAD_CLIP); opt.step()
        model.eval()
        with torch.no_grad():
            pv = torch.sigmoid(model(xv)).numpy()
        s = f1_score(yv, (pv > 0.5).astype(int), zero_division=0)
        if s > best[0]:
            best = (s, {k: v.clone() for k, v in model.state_dict().items()}, ep)
        elif ep - best[2] >= PATIENCE:
            break
    if best[1] is None:
        best = (0.0, {k: v.clone() for k, v in model.state_dict().items()}, 0)
    model.load_state_dict(best[1]); model.eval()
    with torch.no_grad():
        pv = torch.sigmoid(model(xv)).numpy()
    recs = []; cur = 0
    for v, n in bounds_va:
        yy = yv[cur:cur + n]; pp = pv[cur:cur + n]
        recs.append(dict(video=v, seed=seed, video_f1=float(f1_score(yy, (pp > 0.5).astype(int), zero_division=0)),
                         n_windows=int(n), pos_rate=float(yy.mean()) if n else 0.0))
        cur += n
    return recs, best[2], best[0]

def main():
    t0 = time.time()
    vids, words, embs = load()
    tot = sum(n_windows_for(words[v]) for v in vids)
    print(f'videos={len(vids)} windows={tot}', flush=True)
    folds = list(GroupKFold(n_splits=N_FOLDS).split(np.zeros(len(vids)), groups=np.array(vids)))
    recs = {a: [] for a in ARMS}; fsum = {a: [] for a in ARMS}
    base_pos = None
    for seed in SEEDS:
        for fold, (tri, vai) in enumerate(folds):
            Xtr, ytr, Xva, yva, bva = build_fold(vids, words, embs, tri, vai)
            base_pos = float(yva.mean())
            for arm in ARMS:
                r, ep, f1 = train_eval(Xtr[arm], ytr, Xva[arm], yva, bva, seed, arm)
                recs[arm].extend(r)
                fsum[arm].append(dict(seed=seed, fold=fold, fold_f1=float(f1), epoch=ep))
                print(f'seed={seed} fold={fold} arm={arm} foldF1={f1:.4f} ep={ep}', flush=True)
    summary = dict(
        experiment_id='P2-LEVELA-PROSPECTIVE-118V-2026-09-18',
        created_utc_epoch=int(time.time()),
        task='predict laughter word presence in window t+1 from context <= t (5s windows)',
        dataset=dict(videos=len(vids), windows=tot, val_positive_rate=base_pos,
                     label_rule='B/I/L word midpoint; target shifted by -1'),
        protocol=dict(arms=ARMS, model='MLP 256-64-1', split='5-fold GroupKFold by video',
                      seeds=SEEDS, tfidf='cumulative context text, train-fold fit',
                      acoustic='[mean emb t-2..t, emb t, position], scale221 frozen WavLM',
                      anti_leakage='features strictly <=t; punchline words of t+1 excluded by construction'),
        overall={}, fold_summaries=fsum, paired_tests={}, gates={})
    for a in ARMS:
        vals = [r['video_f1'] for r in recs[a]]
        fs = [x['fold_f1'] for x in fsum[a]]
        summary['overall'][a] = dict(video_mean_f1=float(np.mean(vals)), video_std_f1=float(np.std(vals)),
                                     fold_mean_f1=float(np.mean(fs)), fold_std_f1=float(np.std(fs)))
    def by_video(a):
        d = {}
        for r in recs[a]:
            d.setdefault(r['video'], []).append(r['video_f1'])
        return d
    def paired(a, b):
        da, db = by_video(a), by_video(b)
        vs = sorted(set(da) & set(db))
        deltas = np.array([np.mean(da[v]) - np.mean(db[v]) for v in vs])
        rng = np.random.default_rng(BOOT_SEED)
        boot = np.empty(BOOT_N)
        for i in range(BOOT_N):
            sel = rng.choice(vs, len(vs), replace=True)
            boot[i] = np.mean([np.mean(da[v]) - np.mean(db[v]) for v in sel])
        return dict(comparison=f'{a}_minus_{b}', mean_delta_f1=float(deltas.mean()),
                    median_delta_f1=float(np.median(deltas)),
                    bootstrap_ci95=[float(np.quantile(boot, .025)), float(np.quantile(boot, .975))],
                    n_videos=len(vs), improved=int((deltas > 0).sum()), worsened=int((deltas < 0).sum()))
    tests = {
        # NOTE: paired(a, b) returns mean(F1_a) - mean(F1_b): a is the TREATMENT,
        # b is the BASELINE. Gate wants treatment - baseline > 0. No negation.
        'G1_H4_prospective': paired('acoustic_plus_words', 'words_before'),
        'G2_timing': paired('words_before_plus_timing', 'words_before'),
        'G3_acoustic_alone': paired('acoustic_before', 'words_before'),
        'shortcut_position': paired('words_before', 'position_only'),
    }
    summary['paired_tests'] = tests
    for g in ['G1_H4_prospective', 'G2_timing', 'G3_acoustic_alone']:
        t = tests[g]
        mean_treatment_minus_baseline = t['mean_delta_f1']
        ci = list(t['bootstrap_ci95'])
        summary['gates'][g] = dict(treatment_minus_baseline_mean=mean_treatment_minus_baseline,
                                   treatment_minus_baseline_ci95=ci,
                                   gate_pass=bool(ci[0] > 0 and mean_treatment_minus_baseline > 0.02))
    passes = [g for g in ['G1_H4_prospective', 'G2_timing', 'G3_acoustic_alone'] if summary['gates'][g]['gate_pass']]
    summary['decision_gate'] = dict(
        rule='CI95 lower > 0 AND mean dF1 > 0.02 (second arm minus first arm)',
        gates_passed=passes,
        verdict=('BEYOND-WORDS PROSPECTIVE SUPPORTED' if passes else
                 'NOT SUPPORTED — pre-onset signal not extractable from these features at 5s resolution'))
    summary['runtime_seconds'] = float(time.time() - t0)
    out = OUT_DIR / 'p2_level_a_results.json'
    out.write_text(json.dumps(summary, indent=2))
    with gzip.open(OUT_DIR / 'p2_level_a_observations.json.gz', 'wt') as f:
        json.dump(recs, f, separators=(',', ':'))
    print(json.dumps({k: summary[k] for k in ['overall', 'paired_tests', 'gates', 'decision_gate']}, indent=2))
    print('saved', out)

if __name__ == '__main__':
    main()
