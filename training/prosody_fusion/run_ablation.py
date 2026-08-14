#!/usr/bin/env python3
import json, os, time, torch, torch.nn as nn, numpy as np

EMBED_DIR = '/Users/Subho/autonomous_laughter_prediction/training/prosody_fusion_embeddings'
OUT_DIR = '/Users/Subho/autonomous_laughter_prediction/training/prosody_fusion_results'
os.makedirs(OUT_DIR, exist_ok=True)
torch.manual_seed(42)
np.random.seed(42)
device = torch.device('cpu')

# Load data
data = {}
for split in ['train', 'valid', 'test']:
    npz = np.load(os.path.join(EMBED_DIR, f'{split}_embeddings.npz'))
    data[split] = {
        'embeddings': torch.tensor(npz['embeddings'].astype(np.float32)),
        'prosody': torch.tensor(npz['prosody'].astype(np.float32)),
        'labels': torch.tensor(npz['labels']),
    }
    print(f"{split}: emb={data[split]['embeddings'].shape}, prosody={data[split]['prosody'].shape}")

train_emb = data['train']['embeddings'].to(device)
train_pros = data['train']['prosody'].to(device)
train_lbl = data['train']['labels'].to(device)
val_emb = data['valid']['embeddings'].to(device)
val_pros = data['valid']['prosody'].to(device)
val_lbl = data['valid']['labels'].to(device)
test_emb = data['test']['embeddings'].to(device)
test_pros = data['test']['prosody'].to(device)
test_lbl = data['test']['labels'].to(device)
n_train, n_val, n_test = len(train_emb), len(val_emb), len(test_emb)
pos_count = int((train_lbl == 1).sum())
neg_count = int((train_lbl == 0).sum())
print(f"Train={n_train}, Val={n_val}, Test={n_test}, Pos={pos_count}, Neg={neg_count}, Ratio={neg_count/pos_count:.2f}")

def compute_metrics(tp, fp, fn, tn):
    p = tp / (tp + fp + 1e-8)
    r = tp / (tp + fn + 1e-8)
    f1 = 2 * p * r / (p + r + 1e-8)
    return f1, p, r

class TextOnly(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Dropout(0.3),
            nn.Linear(384, 256),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, 64),
            nn.ReLU(),
            nn.Linear(64, 2)
        )
    def forward(self, x):
        return self.net(x)

class LateFusion(nn.Module):
    def __init__(self):
        super().__init__()
        self.pn = nn.LayerNorm(21)
        self.net = nn.Sequential(
            nn.Dropout(0.3),
            nn.Linear(384 + 21, 256),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, 64),
            nn.ReLU(),
            nn.Linear(64, 2)
        )
    def forward(self, emb, pros):
        return self.net(torch.cat([emb, self.pn(pros)], dim=1))

class ProsodyOnly(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Dropout(0.3),
            nn.Linear(21, 64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, 2)
        )
    def forward(self, x):
        return self.net(x)

def train_and_eval(model_fn, get_logits_fn, weight, epochs=50):
    model = model_fn().to(device)
    criterion = nn.CrossEntropyLoss(weight=torch.tensor(weight, dtype=torch.float32).to(device))
    optimizer = torch.optim.AdamW(model.parameters(), lr=5e-4, weight_decay=0.01)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs, eta_min=5e-5)
    BS = 128
    best_vf1 = 0.0
    best_state = None

    for epoch in range(1, epochs + 1):
        perm = torch.randperm(n_train)
        model.train()
        for i in range(0, n_train, BS):
            idx = perm[i:i+BS]
            optimizer.zero_grad()
            loss = criterion(get_logits_fn(model, train_emb[idx], train_pros[idx]), train_lbl[idx])
            loss.backward()
            optimizer.step()
        scheduler.step()

        model.eval()
        vp, vl = [], []
        with torch.no_grad():
            for i in range(0, n_val, BS):
                preds = get_logits_fn(model, val_emb[i:i+BS], val_pros[i:i+BS]).argmax(1).cpu().numpy()
                vp.extend(preds)
                vl.extend(val_lbl[i:i+BS].numpy())
        tp_v = int(((np.array(vp) == 1) & (np.array(vl) == 1)).sum())
        fp_v = int(((np.array(vp) == 1) & (np.array(vl) == 0)).sum())
        fn_v = int(((np.array(vp) == 0) & (np.array(vl) == 1)).sum())
        vf1, _, _ = compute_metrics(tp_v, fp_v, fn_v, 0)
        if vf1 > best_vf1:
            best_vf1 = vf1
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}

    model.load_state_dict(best_state)
    model.eval()
    tp = fp = fn = tn = 0
    with torch.no_grad():
        for i in range(0, n_test, BS):
            preds = get_logits_fn(model, test_emb[i:i+BS], test_pros[i:i+BS]).argmax(1).cpu().numpy()
            labs = test_lbl[i:i+BS].numpy()
            tp += int(((preds == 1) & (labs == 1)).sum())
            fp += int(((preds == 1) & (labs == 0)).sum())
            fn += int(((preds == 0) & (labs == 1)).sum())
            tn += int(((preds == 0) & (labs == 0)).sum())
    tf1, p, r = compute_metrics(tp, fp, fn, tn)
    return float(best_vf1), float(tf1), float(p), float(r), tp, fp, fn, tn

# Configurations
configs = [
    ('Text-Only_balanced', lambda: TextOnly(), lambda m, e, p: m(e), [1.0, 1.0]),
    ('Text-Only_weighted', lambda: TextOnly(), lambda m, e, p: m(e), [1.0, neg_count / pos_count]),
    ('LateFusion_balanced', lambda: LateFusion(), lambda m, e, p: m(e, p), [1.0, 1.0]),
    ('LateFusion_weighted', lambda: LateFusion(), lambda m, e, p: m(e, p), [1.0, neg_count / pos_count]),
    ('Prosody-Only_balanced', lambda: ProsodyOnly(), lambda m, e, p: m(p), [1.0, 1.0]),
    ('Prosody-Only_weighted', lambda: ProsodyOnly(), lambda m, e, p: m(p), [1.0, neg_count / pos_count]),
]

results = {}
for name, model_fn, get_logits, weight in configs:
    vf1, tf1, p, r, tp, fp, fn, tn = train_and_eval(model_fn, get_logits, weight)
    results[name] = {'val_f1': vf1, 'test_f1': tf1, 'p': p, 'r': r, 'tp': tp, 'fp': fp, 'fn': fn, 'tn': tn}
    print(f"  {name:22s}: Val={vf1:.4f} Test={tf1:.4f} P={p:.4f} R={r:.4f} | TP={tp:4d} FP={fp:4d} FN={fn:4d} TN={tn:4d}")

print(f"\n{'='*70}")
print("SUMMARY (held-out: Bill Burr, Chappelle, Russell Peters)")
print(f"{'='*70}")
print(f"{'Model':22s} {'Wt':>6} {'ValF1':>8} {'TestF1':>8} {'Prec':>6} {'Rec':>6} {'FP':>6}")
for k, v in sorted(results.items(), key=lambda x: -x[1]['test_f1']):
    wt = 'bal' if 'balanced' in k else 'wtd'
    n = k.replace('_balanced', '').replace('_weighted', '')
    print(f"{n:22s} {wt:>6} {v['val_f1']:8.4f} {v['test_f1']:8.4f} {v['p']:6.4f} {v['r']:6.4f} {v['fp']:6d}")

to_b = results.get('Text-Only_balanced', {})
lf_b = results.get('LateFusion_balanced', {})
po_b = results.get('Prosody-Only_balanced', {})

print(f"\nKey findings:")
if to_b and lf_b:
    d = lf_b['test_f1'] - to_b['test_f1']
    print(f"  LateFusion vs Text-Only (balanced): ΔF1={d:+.4f} ({'PROSODY HELPS' if d > 0.005 else 'no gain'})")
if to_b and po_b:
    ratio = to_b['test_f1'] / max(po_b['test_f1'], 0.001)
    print(f"  Text vs Prosody alone: {ratio:.1f}x text advantage")
print(f"  Best test F1: {max(v['test_f1'] for v in results.values()):.4f}")

with open(os.path.join(OUT_DIR, 'ablation_results.json'), 'w') as f:
    json.dump(results, f, indent=2)
print(f"\nSaved: {OUT_DIR}/ablation_results.json")
