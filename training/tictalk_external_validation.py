#!/usr/bin/env python3
"""TIC-TALK external validation — prospective laughter anticipation, second lab's data.

Data: public HF dataset ENC-PSL/TIC-TALK (CC-BY-NC-4.0): 90 stand-up specials,
5,416 x 60 s blocks; per-block 384-d sentence-BERT text embedding, Whisper-AT
laugh event spans, per-second pose detections. No raw audio distributed —
this is a PROTOCOL replication (anticipation in their feature space), not an
audio replication.

Task: predict whether the NEXT block contains >=1 laugh event, from the
CURRENT block only (strictly causal, same anticipation design as our Level A).

Arms:
  position_only   block position (shortcut control)
  text_only       384-d sentence-BERT (their semantic stream)
  kin_only        non-lexical kinematic proxies (detection rate, bbox area,
                  center motion, area variance, duration norm) + position
  text_plus_kin   both
Gates (paired, clustered by show, 10k bootstrap): CI95 lower > 0 AND dACC-F1 > 0.02
  E1: text_plus_kin - text_only   (non-lexical context adds beyond text)
  E2: kin_only - text_only        (non-lexical alone)
  E3: text_only - position_only   (text anticipates at all)
Model/protocol: identical MLP 256-64-1, 5-fold GroupKFold by show, seeds 42/43/44.
"""
import gzip, json, time
from pathlib import Path
import numpy as np, pandas as pd
import torch, torch.nn as nn
from sklearn.metrics import f1_score
from sklearn.model_selection import GroupKFold

ROOT = Path('/Users/Subho/autonomous_laughter_prediction_essential')
OUT_DIR = ROOT / 'results' / 'p2_tictalk'
OUT_DIR.mkdir(parents=True, exist_ok=True)
PARQUET = Path('/Users/Subho/.cache/huggingface/hub/datasets--ENC-PSL--TIC-TALK/snapshots/3a2552f89111dbd11a03d4dc7770b97f8b80a7d4/unified_humor_dataset.parquet')

SEEDS = [42, 43, 44]
N_FOLDS = 5
EPOCHS = 40
PATIENCE = 8
LR = 1e-3
GRAD_CLIP = 1.0
BOOT_N = 10000
BOOT_SEED = 20260922
ARMS = ['position_only', 'text_only', 'kin_only', 'text_plus_kin']

class MLP(nn.Module):
    def __init__(self, d):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(d, 256), nn.BatchNorm1d(256), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(256, 64), nn.ReLU(), nn.Dropout(0.2), nn.Linear(64, 1))
    def forward(self, x):
        return self.net(x).squeeze(-1)

def kin_features(row):
    """Non-lexical block summary from per-second pose detections."""
    kps = row['pose_keypoints']
    if kps is None:
        kps = []
    kps = list(kps)
    dets = [k for k in kps if k.get('has_detection')]
    n = max(len(kps), 1)
    if len(dets) < 2:
        return np.array([len(dets) / n, 0.0, 0.0, 0.0, row['end'] - row['start']], dtype=np.float32)
    areas, cx, cy, ts = [], [], [], []
    for k in dets:
        x0, x1 = k.get('bbox_xmin'), k.get('bbox_xmax')
        y0, y1 = k.get('bbox_ymin'), k.get('bbox_ymax')
        if x0 is None or x1 is None or y0 is None or y1 is None:
            continue
        areas.append(max(0.0, (x1 - x0) * (y1 - y0)))
        cx.append((x0 + x1) / 2.0); cy.append((y0 + y1) / 2.0); ts.append(k['time'])
    if len(areas) < 2:
        return np.array([len(dets) / n, 0.0, 0.0, 0.0, row['end'] - row['start']], dtype=np.float32)
    a = np.array(areas); c = np.array(cx); d = np.array(cy); t = np.array(ts)
    motion = float(np.mean(np.sqrt(np.diff(c) ** 2 + np.diff(d) ** 2)))
    return np.array([
        len(dets) / n,                    # performer visibility rate
        float(a.mean()),                  # mean apparent size (proximity)
        motion,                           # center motion (kinetic proxy)
        float(a.std()),                   # size variance (approach/retreat)
        float(t[-1] - t[0]),              # detection span within block
    ], dtype=np.float32)

def main():
    t0 = time.time()
    df = pd.read_parquet(PARQUET)
    df = df.sort_values(['show_id', 'block_id']).reset_index(drop=True)
    shows = sorted(df['show_id'].unique())
    print(f'rows={len(df)} shows={len(shows)}', flush=True)

    texts = np.stack([np.asarray(e, dtype=np.float32) for e in df['embedding']])
    kins = np.stack([kin_features(r) for _, r in df.iterrows()])
    # Sparse target: laughter ONSET in the next block, where an onset is a laugh
    # event starting after >=5 s of laughter-free time in the show timeline.
    # (Naive 'any laugh in next block' is degenerate: 94% positives.)
    onset_blocks = set()
    for sid, g in df.groupby('show_id', sort=False):
        prev_end = None
        for _, r in g.iterrows():
            onset_here = False
            les = r['laugh_events']
            for le in (les if les is not None else []):
                st = float(le['start'])
                if prev_end is None or st - prev_end >= 5.0:
                    onset_here = True
                prev_end = st if prev_end is None else max(prev_end, float(le['end']))
            if onset_here:
                onset_blocks.add((sid, int(r['block_id'])))
    has_onset_next = []
    show_ids = df['show_id'].to_numpy()
    block_ids = df['block_id'].to_numpy()
    for i in range(len(df)):
        has_onset_next.append((show_ids[i], int(block_ids[i]) + 1) in onset_blocks)
    has_onset_next = np.array(has_onset_next)
    tgt = np.zeros(len(df), dtype=np.int64)
    for i in range(len(df) - 1):
        if show_ids[i + 1] == show_ids[i] and block_ids[i + 1] == block_ids[i] + 1:
            tgt[i] = int(has_onset_next[i])
    keep = np.ones(len(df), dtype=bool)
    keep[-1] = False
    # also drop rows whose next row is a different show (no defined target)
    for i in range(len(df) - 1):
        if show_ids[i + 1] != show_ids[i] or block_ids[i + 1] != block_ids[i] + 1:
            keep[i] = False
    idx = np.flatnonzero(keep)
    groups = show_ids[idx]
    pos = np.array([b / max(int(df[df['show_id'] == s]['show_n_blocks'].iloc[0]) - 1, 1)
                    for s, b in zip(show_ids[idx], block_ids[idx])], dtype=np.float32)[:, None]

    F = {
        'position_only': pos.astype(np.float32),
        'text_only': texts[idx],
        'kin_only': np.concatenate([kins[idx], pos], axis=1),
    }
    F['text_plus_kin'] = np.concatenate([F['text_only'], F['kin_only']], axis=1)
    y = tgt[idx]
    print(f'valid={len(idx)} positive_rate={y.mean():.3f}', flush=True)

    folds = list(GroupKFold(n_splits=N_FOLDS).split(np.zeros(len(idx)), groups=groups))
    recs = {a: [] for a in ARMS}
    fsum = {a: [] for a in ARMS}
    for seed in SEEDS:
        for fold, (tri, vai) in enumerate(folds):
            Xtr_all = {a: F[a][tri] for a in ARMS}
            Xva_all = {a: F[a][vai] for a in ARMS}
            ytr, yva = y[tri], y[vai]
            for a in ARMS:
                mu, sd = Xtr_all[a].mean(0), Xtr_all[a].std(0) + 1e-6
                Xtr = (Xtr_all[a] - mu) / sd; Xva = (Xva_all[a] - mu) / sd
                torch.manual_seed(seed); np.random.seed(seed)
                model = MLP(Xtr.shape[1])
                p = max(int(ytr.sum()), 1); n_ = max(len(ytr) - p, 1)
                crit = nn.BCEWithLogitsLoss(pos_weight=torch.tensor(float(n_ / p)))
                opt = torch.optim.AdamW(model.parameters(), lr=LR)
                model.net[-1].bias.data.fill_(-2.0)
                xt = torch.from_numpy(Xtr).float(); yt = torch.from_numpy(ytr).float()
                xv = torch.from_numpy(Xva).float()
                best = (-1.0, None, 0)
                for ep in range(EPOCHS):
                    model.train(); perm = torch.randperm(len(xt))
                    for i2 in range(0, len(xt), 512):
                        j = perm[i2:i2 + 512]
                        opt.zero_grad(); crit(model(xt[j]), yt[j]).backward()
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
                for sh in sorted(set(groups[vai])):
                    m = groups[vai] == sh
                    yy = yva[m]; pp = pv[m]
                    if len(yy) == 0:
                        continue
                    recs[a].append(dict(show=sh, seed=seed, fold=fold,
                                        block_f1=float(f1_score(yy, (pp > 0.5).astype(int), zero_division=0)),
                                        n_blocks=int(len(yy))))
                    cur += m.sum()
                fsum[a].append(dict(seed=seed, fold=fold, fold_f1=float(best[0]), epoch=best[2]))
            print(f'seed={seed} fold={fold} done', flush=True)

    def paired(a, b):
        da = {}; db = {}
        for r in recs[a]: da.setdefault(r['show'], []).append(r['block_f1'])
        for r in recs[b]: db.setdefault(r['show'], []).append(r['block_f1'])
        vs = sorted(set(da) & set(db))
        deltas = np.array([np.mean(da[v]) - np.mean(db[v]) for v in vs])
        rng = np.random.default_rng(BOOT_SEED)
        boot = np.empty(BOOT_N)
        for i in range(BOOT_N):
            sel = rng.choice(vs, len(vs), replace=True)
            boot[i] = np.mean([np.mean(da[v]) - np.mean(db[v]) for v in sel])
        return dict(comparison=f'{a}_minus_{b}', mean_delta_f1=float(deltas.mean()),
                    bootstrap_ci95=[float(np.quantile(boot, .025)), float(np.quantile(boot, .975))],
                    n_shows=len(vs), improved=int((deltas > 0).sum()), worsened=int((deltas < 0).sum()))

    summary = dict(
        experiment_id='TICTALK-EXTERNAL-ANTICIPATION-ONSET-2026-09-18',
        created_utc_epoch=int(time.time()),
        source='ENC-PSL/TIC-TALK (HF, CC-BY-NC-4.0); 90 specials, 5,416 x 60s blocks; no raw audio',
        task='predict laughter ONSET (event starting after >=5s laugh-free gap) in NEXT 60s block from CURRENT block (causal)',
        note='first run used any-laugh target (94% positives, saturated, archived as tictalk_external_results_v1 AnyLaugh in git history)',
        protocol=dict(arms=ARMS, model='MLP 256-64-1', split='5-fold GroupKFold by show',
                      seeds=SEEDS, positive_rate=float(y.mean()),
                      caveat='protocol replication in their feature space (SBERT+pose), NOT audio; 60s blocks'),
        overall={}, paired_tests={}, gates={})
    for a in ARMS:
        fs = [x['fold_f1'] for x in fsum[a]]
        summary['overall'][a] = dict(fold_mean_f1=float(np.mean(fs)), fold_std_f1=float(np.std(fs)))
    t1 = paired('text_plus_kin', 'text_only')
    t2 = paired('kin_only', 'text_only')
    t3 = paired('text_only', 'position_only')
    summary['paired_tests'] = {'E1_text_kin_vs_text': t1, 'E2_kin_vs_text': t2, 'E3_text_vs_position': t3}
    for g, t in [('E1', t1), ('E2', t2), ('E3', t3)]:
        summary['gates'][g] = dict(**{k: t[k] for k in ['mean_delta_f1', 'bootstrap_ci95']},
                                   gate_pass=bool(t['bootstrap_ci95'][0] > 0 and t['mean_delta_f1'] > 0.02))
    passes = [g for g, v in summary['gates'].items() if v['gate_pass']]
    summary['decision_gate'] = dict(gates_passed=passes,
                                    verdict=('PROTOCOL REPLICATES ON TIC-TALK' if 'E1' in passes or 'E2' in passes
                                             else 'DOES NOT REPLICATE on their feature space'))
    summary['runtime_seconds'] = float(time.time() - t0)
    out = OUT_DIR / 'tictalk_external_onset_results.json'
    out.write_text(json.dumps(summary, indent=2))
    with gzip.open(OUT_DIR / 'tictalk_external_observations.json.gz', 'wt') as f:
        json.dump(recs, f, separators=(',', ':'))
    print(json.dumps({'overall': summary['overall'], 'paired_tests': summary['paired_tests'],
                      'decision_gate': summary['decision_gate']}, indent=2))
    print('saved', out)

if __name__ == '__main__':
    main()
