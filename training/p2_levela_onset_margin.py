#!/usr/bin/env python3
"""P2 Level A refinement — onset-margin stratification (registered 2026-09-18).

Question: is the Level A acoustic advantage genuine anticipation, or very-early
onset detection (laughter audibly beginning inside the context window)?

Method: retrain the same Level A arms (identical seeds/folds/protocol), but save
PER-WINDOW predictions. For each positive target (laugh word midpoint in t+1),
margin = earliest laugh-word start in t+1 minus the context boundary 5(t+1):
  margin < 0     straddle — a laugh word STARTS inside context window t
  0 <= m < 1s    early   — onset in first second of target window
  1 <= m < 2.5s  mid
  m >= 2.5s      late    — laugh begins well after context ends

Stratified metrics per arm: hit rate on positives (pred > 0.5), mean predicted
probability on positives and negatives. Paired clustered-bootstrap difference
(acoustic - words) per stratum.

Pre-registered read:
  acoustic advantage persisting on mid/late strata  -> genuine anticipation
  advantage concentrated in straddle/early          -> early-onset detection claim
"""
import ast, glob, gzip, json, os, random, time
from pathlib import Path
import numpy as np, pandas as pd
import torch, torch.nn as nn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import GroupKFold
from sklearn.metrics import f1_score

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
BOOT_SEED = 20260919
ARMS = ['words_before', 'acoustic_before', 'acoustic_plus_words']
STRATA = ['straddle', 'early', 'mid', 'late', 'nonegative_all']

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

def window_words_labels_margins(df, n):
    """Per window: text, current label, and for TARGET use, margin of earliest
    laugh-word start relative to this window's start (for windows that contain
    a laugh word with midpoint inside)."""
    texts = [''] * n
    labels = np.zeros(n, dtype=np.int64)
    margins = np.full(n, np.nan, dtype=np.float64)
    laugh = df[df['label'].isin(['B', 'I', 'L'])]
    for _, r in df.iterrows():
        k = int(((r['start'] + r['end']) / 2.0) // WIN_SEC)
        if 0 <= k < n:
            texts[k] = (texts[k] + ' ' + r['text']).strip() if texts[k] else r['text']
    for _, r in laugh.iterrows():
        k = int(((r['start'] + r['end']) / 2.0) // WIN_SEC)
        if 0 <= k < n:
            labels[k] = 1
            m = r['start'] - k * WIN_SEC
            margins[k] = m if (np.isnan(margins[k]) or m < margins[k]) else margins[k]
    return texts, labels, margins

def context_timing(df, n):
    out = np.zeros((n, 6), dtype=np.float32)
    starts = df['start'].to_numpy(float); ends = df['end'].to_numpy(float)
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
        out[t] = [np.log1p(pw_pause[trail].sum() / 3.0), np.log1p(pw_pause[trail].max()),
                  np.log1p(pw_count[trail].sum() / 3.0), np.log1p(pw_rate[t]),
                  np.log1p(pw_pause[t]), float(t) / max(n - 1, 1)]
    return out

class MLP(nn.Module):
    def __init__(self, d):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(d, 256), nn.BatchNorm1d(256), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(256, 64), nn.ReLU(), nn.Dropout(0.2), nn.Linear(64, 1))
    def forward(self, x):
        return self.net(x).squeeze(-1)

def main():
    t0 = time.time()
    vids, words, embs = load()
    print(f'videos={len(vids)}', flush=True)
    per = {}
    for v in vids:
        n = n_windows_for(words[v])
        texts, y, marg = window_words_labels_margins(words[v], n)
        tgt = np.zeros(n, dtype=np.int64)
        tgt[:-1] = y[1:]
        # margin of the TARGET window's earliest laugh onset relative to target start
        tgt_margin = np.full(n, np.nan)
        tgt_margin[:-1] = marg[1:]
        # context features identical to Level A
        cum = []
        acc = ''
        for tx in texts:
            acc = (acc + ' ' + tx).strip()
            cum.append(acc)
        per[v] = dict(n=n, cum=cum, tgt=tgt, tgt_margin=tgt_margin,
                      timing=context_timing(words[v], n))

    folds = list(GroupKFold(n_splits=N_FOLDS).split(np.zeros(len(vids)), groups=np.array(vids)))
    win_records = []
    for seed in SEEDS:
        for fold, (tri, vai) in enumerate(folds):
            tr = [vids[i] for i in tri]
            va = [vids[i] for i in vai]
            vec = TfidfVectorizer(max_features=MAX_TFIDF, analyzer='word', ngram_range=(1, 2),
                                  min_df=2, max_df=0.95, sublinear_tf=True)
            vec.fit([t for v in tr for t in per[v]['cum']])
            def acoustic(v):
                n = per[v]['n']; E = embs[v]
                A = np.zeros((n, 791), dtype=np.float32)
                L = np.zeros((n, 791), dtype=np.float32)
                d = min(n, E.shape[0]); A[:d] = E[:d]; L[:d] = E[:d]
                for t in range(n):
                    if t < E.shape[0]:
                        A[t] = E[max(0, t - 2):t + 1].mean(axis=0)
                pos = (np.arange(n, dtype=np.float32) / max(n - 1, 1))[:, None]
                return np.concatenate([A, L, pos], axis=1)
            def feats(v):
                W = vec.transform(per[v]['cum']).toarray().astype(np.float32)
                T = per[v]['timing']; A = acoustic(v)
                return {'words_before': W,
                        'acoustic_before': A,
                        'acoustic_plus_words': np.concatenate([A, W, T], 1)}
            Xtr = {a: [] for a in ARMS}; Xva = {a: [] for a in ARMS}
            ytr_l, yva_l, meta_va = [], [], []
            for v in tr:
                F = feats(v)
                for a in ARMS:
                    Xtr[a].append(F[a])
                ytr_l.append(per[v]['tgt'])
            for v in va:
                F = feats(v)
                for a in ARMS:
                    Xva[a].append(F[a])
                yva_l.append(per[v]['tgt'])
                meta_va.append(v)
            Xtr = {a: np.concatenate(Xtr[a]) for a in ARMS}
            Xva = {a: np.concatenate(Xva[a]) for a in ARMS}
            ytr = np.concatenate(ytr_l); yva = np.concatenate(yva_l)
            for a in ARMS:
                mu, sd = Xtr[a].mean(0), Xtr[a].std(0) + 1e-6
                Xtr[a] = (Xtr[a] - mu) / sd; Xva[a] = (Xva[a] - mu) / sd
            for a in ARMS:
                torch.manual_seed(seed); np.random.seed(seed); random.seed(seed)
                model = MLP(Xtr[a].shape[1])
                pos = max(int(ytr.sum()), 1); neg = max(len(ytr) - pos, 1)
                crit = nn.BCEWithLogitsLoss(pos_weight=torch.tensor(float(neg / pos)))
                opt = torch.optim.AdamW(model.parameters(), lr=LR)
                model.net[-1].bias.data.fill_(-2.0)
                xt = torch.from_numpy(Xtr[a]).float(); yt = torch.from_numpy(ytr).float()
                xv = torch.from_numpy(Xva[a]).float()
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
                    s = f1_score(yva, (pv > 0.5).astype(int), zero_division=0)
                    if s > best[0]:
                        best = (s, {k: v.clone() for k, v in model.state_dict().items()}, ep)
                    elif ep - best[2] >= PATIENCE:
                        break
                if best[1] is None:
                    best = (0.0, {k: v.clone() for k, v in model.state_dict().items()}, 0)
                model.load_state_dict(best[1]); model.eval()
                with torch.no_grad():
                    pv = torch.sigmoid(model(xv)).numpy()
                cur = 0
                for v in meta_va:
                    n = per[v]['n']
                    tm = per[v]['tgt_margin']; yy = yva[cur:cur + n]; pp = pv[cur:cur + n]
                    for t in range(n):
                        if np.isnan(tm[t]):
                            stratum = 'nonegative_all' if yy[t] == 0 else 'straddle_missing'
                            stratum = 'nonegative_all'  # negatives have no margin
                        else:
                            stratum = ('straddle' if tm[t] < 0 else 'early' if tm[t] < 1.0
                                       else 'mid' if tm[t] < 2.5 else 'late')
                        win_records.append(dict(video=v, seed=seed, fold=fold, arm=a, t=t,
                                                label=int(yy[t]), pred=float(pp[t]),
                                                stratum=stratum, margin=float(tm[t]) if not np.isnan(tm[t]) else None))
                    cur += n
                print(f'seed={seed} fold={fold} arm={a} foldF1={best[0]:.4f} ep={best[2]}', flush=True)

    # Stratified analysis
    import collections
    def strat_stats(arm, stratum):
        rows = [r for r in win_records if r['arm'] == arm and r['stratum'] == stratum and r['label'] == 1]
        negs = [r for r in win_records if r['arm'] == arm and r['stratum'] == stratum and r['label'] == 0]
        if not rows:
            return None
        return dict(n_pos=len(rows), hit_rate=float(np.mean([r['pred'] > 0.5 for r in rows])),
                    mean_pred_pos=float(np.mean([r['pred'] for r in rows])),
                    n_neg=len(negs), mean_pred_neg=float(np.mean([r['pred'] for r in negs])) if negs else None)
    stratified = {a: {s: strat_stats(a, s) for s in STRATA} for a in ARMS}

    # Paired bootstrap per stratum: acoustic_plus_words - words_before hit-rate difference
    def paired_hitrate(stratum, arm_a='acoustic_plus_words', arm_b='words_before'):
        def per_video(arm):
            d = collections.defaultdict(list)
            for r in win_records:
                if r['arm'] == arm and r['stratum'] == stratum and r['label'] == 1:
                    d[r['video']].append(1.0 if r['pred'] > 0.5 else 0.0)
            return {v: np.mean(x) for v, x in d.items()}
        da, db = per_video(arm_a), per_video(arm_b)
        vs = sorted(set(da) & set(db))
        if len(vs) < 5:
            return None
        deltas = np.array([da[v] - db[v] for v in vs])
        rng = np.random.default_rng(BOOT_SEED)
        boot = np.empty(BOOT_N)
        for i in range(BOOT_N):
            sel = rng.choice(vs, len(vs), replace=True)
            boot[i] = np.mean([da[v] - db[v] for v in sel])
        return dict(stratum=stratum, n_videos=len(vs), n_pos_obs=int(sum(len([1 for r in win_records if r['arm'] == 'acoustic_plus_words' and r['stratum'] == stratum and r['label'] == 1 and r['video'] == v]) for v in vs)),
                    mean_hitrate_delta=float(deltas.mean()),
                    ci95=[float(np.quantile(boot, .025)), float(np.quantile(boot, .975))])
    paired_strata = {s: paired_hitrate(s) for s in ['straddle', 'early', 'mid', 'late']}

    summary = dict(
        experiment_id='P2-LEVELA-ONSET-MARGIN-2026-09-18',
        created_utc_epoch=int(time.time()),
        question='genuine anticipation vs very-early onset detection',
        strata_definition='straddle: laugh word starts inside context window t; early: 0-1s into t+1; mid: 1-2.5s; late: >=2.5s; nonegative_all: negatives',
        arms=ARMS,
        stratified=stratified,
        paired_hitrate_acoustic_plus_words_minus_words=paired_strata,
        read_rule='advantage persisting on mid/late -> genuine anticipation; concentrated in straddle/early -> early-onset detection',
        runtime_seconds=float(time.time() - t0))
    out = OUT_DIR / 'p2_levela_onset_margin_results.json'
    out.write_text(json.dumps(summary, indent=2))
    with gzip.open(OUT_DIR / 'p2_levela_onset_margin_observations.json.gz', 'wt') as f:
        json.dump(win_records, f, separators=(',', ':'))
    print(json.dumps(summary, indent=2))
    print('saved', out)

if __name__ == '__main__':
    main()
