#!/usr/bin/env python3
"""V8 Fixed Training - Handles words/labels → text/label conversion"""
import os, json, subprocess
from pathlib import Path
import torch, torch.nn as nn, torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModel
from sklearn.metrics import f1_score

print("=" * 50)
print("V8 FIXED TRAINING")
print("=" * 50)

MODEL = '/tmp/xlmr'
Path(MODEL).mkdir(exist_ok=True)

# Download model
for fname in ['config.json','model.safetensors','tokenizer_config.json','tokenizer.json','sentencepiece.bpe.model']:
    dst = f'{MODEL}/{fname}'
    if not Path(dst).exists() or Path(dst).stat().st_size < 100:
        print(f'Downloading {fname}...')
        subprocess.run(['curl','-sL','-o', dst,
                       f'https://huggingface.co/FacebookAI/xlm-roberta-base/resolve/main/{fname}'],timeout=300)

# Download data
print('Downloading data...')
for name, url in [
    ('train_raw.jsonl', 'https://raw.githubusercontent.com/Das-rebel/ChuckleNet/main/data/train_small.jsonl'),
    ('valid_raw.jsonl', 'https://raw.githubusercontent.com/Das-rebel/ChuckleNet/main/data/valid_small.jsonl'),
]:
    subprocess.run(['curl','-sL','-o', name, url], timeout=120)
    n = sum(1 for _ in open(name))
    print(f'  {name}: {n} samples')

# ═══════════════════════════════════════════════════════════════
# KEY FIX: Convert words/labels → text/label format
# ═══════════════════════════════════════════════════════════════
def convert_data(input_path, output_path):
    """Convert word-level data to sentence-level with binary label"""
    converted = 0
    with open(input_path) as fin, open(output_path, 'w') as fout:
        for line in fin:
            if not line.strip():
                continue
            try:
                d = json.loads(line)
            except:
                continue
            
            words = d.get('words', [])
            labels = d.get('labels', [])
            
            if not words or not labels:
                continue
            
            # Join words into single text string
            text = ' '.join(words)
            
            # Binary label: 1 if ANY word is labeled as 1 (laughter), else 0
            label = 1 if any(l == 1 for l in labels) else 0
            
            out = {'text': text, 'label': label}
            fout.write(json.dumps(out) + '\n')
            converted += 1
    
    return converted

print('\nConverting data format...')
n_train = convert_data('train_raw.jsonl', 'train.jsonl')
n_valid = convert_data('valid_raw.jsonl', 'valid.jsonl')
print(f'  train.jsonl: {n_train} samples')
print(f'  valid.jsonl: {n_valid} samples')

# Verify conversion
with open('train.jsonl') as f:
    sample = json.loads(f.readline())
print(f'\nVerification - sample keys: {list(sample.keys())}')
print(f'  text[:50]: {sample["text"][:50]}...')
print(f'  label: {sample["label"]}')

# Label distribution
pos_train = sum(1 for l in open('train.jsonl') if json.loads(l)['label'] == 1)
pos_valid = sum(1 for l in open('valid.jsonl') if json.loads(l)['label'] == 1)
print(f'  Train positive ratio: {pos_train}/{n_train} = {pos_train/n_train:.2%}')
print(f'  Valid positive ratio: {pos_valid}/{n_valid} = {pos_valid/n_valid:.2%}')

# Model
class Model(nn.Module):
    def __init__(self):
        super().__init__()
        self.enc = AutoModel.from_pretrained(MODEL)
        for p in self.enc.parameters():
            p.requires_grad = False
        for i in range(8, 12):
            for p in self.enc.encoder.layer[i].parameters():
                p.requires_grad = True
        self.clf = nn.Sequential(nn.Dropout(0.1), nn.Linear(768,256), nn.ReLU(), nn.Linear(256,2))
    def forward(self, ids, mask):
        return self.clf(self.enc(input_ids=ids, attention_mask=mask).last_hidden_state[:,0,:])

class DS(Dataset):
    def __init__(self, path, tok):
        self.tok = tok
        with open(path) as f:
            self.data = [json.loads(l) for l in f if l.strip()]
    def __len__(self):
        return len(self.data)
    def __getitem__(self, i):
        d = self.data[i]
        enc = self.tok(d['text'], max_length=128, padding='max_length', truncation=True, return_tensors='pt')
        return {k: v.squeeze() for k, v in enc.items()}, torch.tensor(d['label'])

tok = AutoTokenizer.from_pretrained(MODEL)
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f'\nDevice: {device}')
m = Model().to(device)
opt = torch.optim.AdamW(m.parameters(), lr=2e-5)
tr = DataLoader(DS('train.jsonl', tok), batch_size=32, shuffle=True)
va = DataLoader(DS('valid.jsonl', tok), batch_size=64)
print(f'Train: {len(tr)} batches, Valid: {len(va)} batches')

# GPU guard
if device.type == 'cuda':
    cap = torch.cuda.get_device_capability(0)
    if cap[0] < 7:
        raise RuntimeError(f'GPU compute {cap[0]}.{cap[1]} < 7.0 not supported!')
    print(f'GPU: {torch.cuda.get_device_name(0)} (compute {cap[0]}.{cap[1]})')

# Training
results = []
cw = torch.tensor([1., 5.]).to(device)
for ep in range(20):
    m.train()
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
    
    with open('v8_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    if f1 > 0.72:
        break

best = max(r['val_f1'] for r in results)
print(f'\nDONE! Best ValF1: {best:.4f}')
print(json.dumps(results, indent=2))
