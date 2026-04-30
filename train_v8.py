#!/usr/bin/env python3
"""V8 Complete Training"""
import os, json, subprocess
from pathlib import Path
import torch, torch.nn as nn, torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModel
from sklearn.metrics import f1_score

MODEL = '/tmp/xlm-roberta-base-ms'
Path(MODEL).mkdir(exist_ok=True)
HF_FILES = ['config.json','model.safetensors','tokenizer_config.json','tokenizer.json','sentencepiece.bpe.model']
for fname in HF_FILES:
    subprocess.run(['curl','-sL','-o',f'{MODEL}/{fname}',
                  f'https://huggingface.co/FacebookAI/xlm-roberta-base/resolve/main/{fname}'], timeout=300)

for s in ['train','valid','test']:
    subprocess.run(['curl','-sL','-o',f'{s}.jsonl',
                   f'https://raw.githubusercontent.com/Subho-ML/autonomous-laughter/main/data/training/standup_word_level_FINAL_27dim/{s}.jsonl'], timeout=120)

class Model(nn.Module):
    def __init__(self):
        super().__init__()
        self.enc = AutoModel.from_pretrained(MODEL)
        for p in self.enc.parameters(): p.requires_grad = False
        for i in range(8,12): 
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
        return {k:v.squeeze() for k,v in enc.items()}, torch.tensor(d.get('label',0))

def save_results(results):
    with open('v8_results.json', 'w') as f:
        json.dump({'results': results}, f, indent=2)
    try:
        from google.colab import drive
        drive.mount('/content/drive', force_remount=True)
        with open('/content/drive/MyDrive/v8_results.json', 'w') as f:
            json.dump({'results': results}, f, indent=2)
    except: pass

tokenizer = AutoTokenizer.from_pretrained(MODEL)
model = Model().cuda()
opt = torch.optim.AdamW(model.parameters(), lr=2e-5)
tr = DataLoader(DS('train.jsonl', tokenizer), batch_size=32, shuffle=True)
va = DataLoader(DS('valid.jsonl', tokenizer), batch_size=64)

results = []
for ep in range(20):
    model.train()
    for b, l in tr:
        ids, mk = b['input_ids'].cuda(), b['attention_mask'].cuda()
        l = l.cuda()
        opt.zero_grad()
        F.cross_entropy(model(ids,mk), l, weight=torch.tensor([1.,5.]).cuda()).backward()
        opt.step()
    model.eval()
    p, y = [], []
    with torch.no_grad():
        for b, l in va:
            p.extend(model(b['input_ids'].cuda(), b['attention_mask'].cuda()).argmax(-1).cpu())
            y.extend(l.numpy())
    f1 = f1_score(y, p, average='binary')
    print(f"E{ep+1} ValF1={f1:.4f}")
    results.append({'epoch':ep+1, 'val_f1':f1})
    save_results(results)
    if f1 > 0.72: break

print(f"Done! Best: {max(r['val_f1'] for r in results):.4f}")
