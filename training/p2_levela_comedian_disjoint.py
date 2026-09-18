#!/usr/bin/env python3
"""Level A H=1 under COMEDIAN-DISJOINT folds (leakage-hardening check).

Prior Level A folds were video-disjoint but not comedian-disjoint; same-comedian
specials could appear in train and validation (map shows Stephen Bailey x4,
Michael McIntyre x3, ...). This rerun groups by comedian key (title-extracted
first-two-words + channel) and reruns the 3 main arms x 3 seeds x 5 folds.
Gate unchanged: treatment-minus-baseline CI95 lower > 0 AND delta > 0.02.
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
CMAP = Path('/tmp/p1_data/comedian_map.json')
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
BOOT_SEED = 20260921
ARMS = ['words_before', 'acoustic_before', 'acoustic_plus_words']

def parse_ts(x):
    try:
        return ast.literal_eval(str(x))
    except Exception:
        return None

def load():
    cmap = json.loads(CMAP.read_text())
    emb_ids = {os.path.basename(f)[:-4] for f in glob.glob(str(EMB_DIR / '*.npy'))}
    lab_ids = {os.path.basename(f)[:-4] for f in glob.glob(str(LAB_DIR / '*.csv'))}
    vids = sorted((emb_ids & lab_ids) & set(cmap))
    words, embs, groups = {}, {}, {}
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
        groups[v] = cmap[v]['comedian_key'] + '|' + cmap[v]['channel']
    return sorted(words), words, embs, groups

def n_windows_for(df):
    return max(1, int(np.ceil(df['end'].max() / WIN_SEC)))

def window_texts_labels(df, n):
    texts = [''] * n
    labels = np.zeros(n, dtype=np.int64)
    for _, r in df.iterrows():
        k = int(((r['start'] + r['end']) / 2.0) // WIN_SEC)
        if 0 <= k < n:
            texts[k] = (texts[k] + ' ' + r['text']).strip() if texts[k] else r['text']
            if r['label'] in ('B', 'I', 'L'):
                labels[k] = 1
    return texts, labels

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
    vids, words, embs, groups = load()
    print(f'videos={len(vids)} comedian_groups={len(set(groups.values()))}', flush=True)
    per = {}
    for v in vids:
        n = n_windows_for(words[v])
        texts, y = window_texts_labels(words[v], n)
        cum = []
        acc = ''
        for tx in texts:
            acc = (acc + ' ' + tx).strip()
            cum.append(acc)
        tgt = np.zeros(n, dtype=np.int64)
        tgt[:-1] = y[1:]
        per[v] = dict(n=n, cum=cum, tgt=tgt, timing=context_timing(words[v], n))

    garr = np.array([groups[v] for v in vids])
    folds = list(GroupKFold(n_splits=N_FOLDS).split(np.zeros(len(vids)), groups=garr))
    recs = {a: [] for a in ARMS}
    fsum = {a: [] for a in ARMS}
    for seed in SEEDS:
        for fold, (tri, vai) in enumerate(folds):
            tr = [vids[i] for i in tri]; va = [vids[i] for i in vai]
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
            Xtr = {a: [] for a in ARMS}; Xva = {a: [] for a in ARMS}
            ytr_l, yva_l, meta = [], [], []
            for v in tr:
                F_w = vec.transform(per[v]['cum']).toarray().astype(np.float32)
                F_a = acoustic(v)
                Xtr['words_before'].append(F_w); Xtr['acoustic_before'].append(F_a)
                Xtr['acoustic_plus_words'].append(np.concatenate([F_a, F_w, per[v]['timing']], 1))
                ytr_l.append(per[v]['tgt'])
            for v in va:
                F_w = vec.transform(per[v]['cum']).toarray().astype(np.float32)
                F_a = acoustic(v)
                Xva['words_before'].append(F_w); Xva['acoustic_before'].append(F_a)
                Xva['acoustic_plus_words'].append(np.concatenate([F_a, F_w, per[v]['timing']], 1))
                yva_l.append(per[v]['tgt']); meta.append((v, per[v]['n']))
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
                for v, n in meta:
                    yy = yva[cur:cur + n]; pp = pv[cur:cur + n]
                    recs[a].append(dict(video=v, seed=seed, fold=fold,
                                        video_f1=float(f1_score(yy, (pp > 0.5).astype(int), zero_division=0)),
                                        n_windows=int(n), pos_rate=float(yy.mean()) if n else 0.0))
                    cur += n
                fsum[a].append(dict(seed=seed, fold=fold, fold_f1=float(best[0]), epoch=best[2]))
                print(f'seed={seed} fold={fold} arm={a} foldF1={best[0]:.4f} ep={best[2]}', flush=True)

    def paired(a, b):
        da = {}; db = {}
        for r in recs[a]: da.setdefault(r['video'], []).append(r['video_f1'])
        for r in recs[b]: db.setdefault(r['video'], []).append(r['video_f1'])
        vs = sorted(set(da) & set(db))
        deltas = np.array([np.mean(da[v]) - np.mean(db[v]) for v in vs])
        rng = np.random.default_rng(BOOT_SEED)
        boot = np.empty(BOOT_N)
        for i in range(BOOT_N):
            sel = rng.choice(vs, len(vs), replace=True)
            boot[i] = np.mean([np.mean(da[v]) - np.mean(db[v]) for v in sel])
        return dict(comparison=f'{a}_minus_{b}', mean_delta_f1=float(deltas.mean()),
                    bootstrap_ci95=[float(np.quantile(boot, .025)), float(np.quantile(boot, .975))],
                    n_videos=len(vs), improved=int((deltas > 0).sum()), worsened=int((deltas < 0).sum()))
    summary = dict(
        experiment_id='P2-LEVELA-COMEDIAN-DISJOINT-2026-09-18',
        created_utc_epoch=int(time.time()),
        purpose='leakage hardening: same Level A H=1 protocol with comedian-disjoint folds',
        grouping='comedian key (first-2-words of oEmbed title) + channel; oEmbed map of 118 intersecting videos',
        overall={}, paired_tests={}, gates={})
    for a in ARMS:
        fs = [x['fold_f1'] for x in fsum[a]]
        vals = [r['video_f1'] for r in recs[a]]
        summary['overall'][a] = dict(fold_mean_f1=float(np.mean(fs)), fold_std_f1=float(np.std(fs)),
                                     video_mean_f1=float(np.mean(vals)))
    t1 = paired('acoustic_plus_words', 'words_before')
    t3 = paired('acoustic_before', 'words_before')
    summary['paired_tests'] = {'acoustic_plus_words_vs_words': t1, 'acoustic_vs_words': t3}
    summary['gates'] = {
        'acoustic_plus_words_minus_words': dict(**{k: t1[k] for k in ['mean_delta_f1', 'bootstrap_ci95']},
                                                gate_pass=bool(t1['bootstrap_ci95'][0] > 0 and t1['mean_delta_f1'] > 0.02)),
        'acoustic_minus_words': dict(**{k: t3[k] for k in ['mean_delta_f1', 'bootstrap_ci95']},
                                     gate_pass=bool(t3['bootstrap_ci95'][0] > 0 and t3['mean_delta_f1'] > 0.02))}
    passes = [g for g, v in summary['gates'].items() if v['gate_pass']]
    summary['decision_gate'] = dict(gates_passed=passes,
                                    verdict=('SURVIVES COMEDIAN-DISJOINT SPLIT' if passes else
                                             'DOES NOT SURVIVE COMEDIAN-DISJOINT SPLIT — comedian identity was contributing'))
    summary['runtime_seconds'] = float(time.time() - t0)
    out = OUT_DIR / 'p2_levela_comedian_disjoint_results.json'
    out.write_text(json.dumps(summary, indent=2))
    with gzip.open(OUT_DIR / 'p2_levela_comedian_disjoint_observations.json.gz', 'wt') as f:
        json.dump(recs, f, separators=(',', ':'))
    print(json.dumps({'overall': summary['overall'], 'gates': summary['gates'],
                      'decision_gate': summary['decision_gate']}, indent=2))
    print('saved', out)

if __name__ == '__main__':
    main()
