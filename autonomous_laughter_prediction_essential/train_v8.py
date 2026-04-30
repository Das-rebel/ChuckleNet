#!/usr/bin/env python3
"""V8 Complete Training - Writes results to GitHub after each epoch"""
import os, json, subprocess
from pathlib import Path
import torch, torch.nn as nn, torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModel
from sklearn.metrics import f1_score

print("=" * 50)
print("V8 TRAINING STARTING")
print("=" * 50)

# Download model
MODEL = '/tmp/xlmr'
Path(MODEL).mkdir(exist_ok=True)
for fname in ['config.json','model.safetensors','tokenizer_config.json','tokenizer.json','sentencepiece.bpe.model']:
    dst = f'{MODEL}/{fname}'
    if not Path(dst).exists() or Path(dst).stat().st_size < 100:
        print(f'Downloading {fname}...')
        subprocess.run(['curl','-sL','-o', dst,
                       f'https://huggingface.co/FacebookAI/xlm-roberta-base/resolve/main/{fname}'],timeout=300)

# Download data
print('Downloading data...')
for name, url in [
    ('train.jsonl', 'https://raw.githubusercontent.com/Das-rebel/ChuckleNet/main/data/train_small.jsonl'),
    ('valid.jsonl', 'https://raw.githubusercontent.com/Das-rebel/ChuckleNet/main/data/valid_small.jsonl'),
]:
    subprocess.run(['curl','-sL','-o', name, url], timeout=120)
    n = sum(1 for _ in open(name))
    print(f'  {name}: {n} samples')

class Model(nn.Module):
    def __init__(self):
        super().__init__()
        self.enc = AutoModel.from_pretrained(MODEL)
        for p in self.enc.parameters(): p.requires_grad = False
        for i in range(8, 12):
            for p in self.enc.encoder.layer[i].parameters(): p.requires_grad = True
        self.clf = nn.Sequential(nn.Dropout(0.1), nn.Linear(768,256), nn.ReLU(), nn.Linear(256,2))
    def forward(self, ids, mask):
        return self.clf(self.enc(input_ids=ids, attention_mask=mask).last_hidden_state[:,0,:])

class DS(Dataset):
    def __init__(self, path, tok):
        self.tok = tok
        with open(path) as f: self.data = [json.loads(l) for l in f if l.strip()]
    def __len__(self): return len(self.data)
    def __getitem__(self, i):
        d = self.data[i]
        enc = self.tok(d.get('text',''), max_length=128, padding='max_length', truncation=True, return_tensors='pt')
        return {k: v.squeeze() for k, v in enc.items()}, torch.tensor(d.get('label', 0))

def save_results(results):
    with open('v8_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    try:
        from google.colab import drive
        drive.mount('/content/drive')
        with open('/content/drive/MyDrive/v8_results.json', 'w') as f:
            json.dump(results, f)
        print(f'Saved to Drive! {len(results)} epochs')
    except:
        print(f'Saved locally! {len(results)} epochs')

tok = AutoTokenizer.from_pretrained(MODEL)
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f'Using device: {device}')
m = Model().to(device)
opt = torch.optim.AdamW(m.parameters(), lr=2e-5)
tr = DataLoader(DS('train.jsonl', tok), batch_size=32, shuffle=True)
va = DataLoader(DS('valid.jsonl', tok), batch_size=64)
print(f'Train: {len(tr)} batches, Valid: {len(va)} batches')

results = []
for ep in range(20):
    m.train()
    cw = torch.tensor([1.,5.]).to(device)
    for b, l in tr:
        ids, mk = b['input_ids'].to(device), b['attention_mask'].to(device)
        l = l.to(device)
        opt.zero_grad()
        F.cross_entropy(m(ids,mk), l, weight=cw).backward()
        opt.step()
    m.eval()
    p, y = [], []
    with torch.no_grad():
        for b, l in va:
            p.extend(m(b['input_ids'].to(device), b['attention_mask'].to(device)).argmax(-1).cpu())
            y.extend(l.numpy())
    f1 = f1_score(y, p, average='binary')
    print(f'E{ep+1} ValF1={f1:.4f}')
    results.append({'epoch':ep+1, 'val_f1':float(f1)})
    save_results(results)
    if f1 > 0.72: break

best = max(r['val_f1'] for r in results)
print(f'DONE! Best ValF1: {best:.4f}')

# Write final output to a file we can read
with open('/tmp/v8_final.txt', 'w') as f:
    f.write(f'BEST_VAL_F1={best:.4f}\n')
    for r in results:
        f.write(f"E{r['epoch']} ValF1={r['val_f1']:.4f}\n")
