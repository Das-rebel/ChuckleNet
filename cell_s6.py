# S6: Dataset & Training Config (Accelerate + PEFT-ready)
# MOCK SETUP: all data/state that would come from prior cells S2-S5
import torch
import random
from collections import defaultdict

# Mock: 100 fake utterances matching the format from S2
utterances = []
for i in range(100):
    utterances.append({
        'utterance_id': f'utt_{i:04d}',
        'video_id': f'vid_{(i//10):04d}',
        'text': f'This is utterance number {i} with some text for testing.',
        'start': 0.0,
        'end': 2.0,
        'label_any': 1 if random.random() < 0.32 else 0,
    })

# Mock: fake embeddings (768-dim, one per utterance)
emb_dict = {}
for u in utterances:
    emb_dict[u['utterance_id']] = torch.randn(768)

# Mock: load from "file" (simulate S5 output)
emb_data = {'utterance_ids': [u['utterance_id'] for u in utterances], 'embeddings': torch.stack(list(emb_dict.values()))}

# ====== BEGIN ORIGINAL S6 CODE ======
import torch.nn as nn
from torch.optim import AdamW
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModel, get_cosine_schedule_with_warmup
from sklearn.metrics import f1_score, precision_score, recall_score
import random, gc, os

DEVICE = torch.device('cuda')

# Load embeddings from merged file
emb_data = torch.load('/content/gdrive/MyDrive/wavlm_embeddings_15k', map_location='cpu')
emb_dict = {uid: emb for uid, emb in zip(emb_data['utterance_ids'], emb_data['embeddings'])}
print(f'Embeddings: {len(emb_dict)}')

tokenizer = AutoTokenizer.from_pretrained('FacebookAI/xlm-roberta-base')

class AudioTextDataset(Dataset):
    def __init__(self, utts, emb_dict):
        self.utts = [u for u in utts if u['utterance_id'] in emb_dict]
        self.emb = emb_dict
    def __len__(self): return len(self.utts)
    def __getitem__(self, i):
        u = self.utts[i]
        enc = tokenizer(u['text'], max_length=128, padding='max_length', truncation=True, return_tensors='pt')
        return {
            'input_ids': enc['input_ids'].squeeze(0),
            'attention_mask': enc['attention_mask'].squeeze(0),
            'audio_emb': self.emb[u['utterance_id']].float(),
            'label': torch.tensor(u.get('label_any',0), dtype=torch.long)
        }

def collate(batch):
    return {
        'input_ids': torch.stack([b['input_ids'] for b in batch]),
        'attention_mask': torch.stack([b['attention_mask'] for b in batch]),
        'audio_emb': torch.stack([b['audio_emb'] for b in batch]),
        'labels': torch.stack([b['label'] for b in batch])
    }

# Video-level split (same as before)
from collections import defaultdict
vid_map = defaultdict(list)
for i, u in enumerate(utterances):
    if u['utterance_id'] in emb_dict:
        vid_map[u['video_id']].append(i)

random.seed(42)
vids = sorted(vid_map.keys())
random.shuffle(vids)
n_val = max(1, len(vids)//10)
val_vids = set(vids[:n_val])

train_utts = [u for u in utterances if u['utterance_id'] in emb_dict and u['video_id'] not in val_vids]
val_utts = [u for u in utterances if u['utterance_id'] in emb_dict and u['video_id'] in val_vids]

train_ds = AudioTextDataset(train_utts, emb_dict)
val_ds = AudioTextDataset(val_utts, emb_dict)
print(f'Train: {len(train_ds)}, Val: {len(val_ds)}')

# Compute class weights for imbalanced data (32% positive)
n_pos = sum(1 for u in train_utts if u.get('label_any',0)==1)
n_neg = len(train_utts) - n_pos
pos_weight = torch.tensor([1.0, n_neg/max(n_pos,1)]).to(DEVICE)
print(f'Class weight for positive: {pos_weight[1].item():.2f}')

BS = 16
train_loader = DataLoader(train_ds, batch_size=BS, shuffle=True, collate_fn=collate, num_workers=0)
val_loader = DataLoader(val_ds, batch_size=BS*2, shuffle=False, collate_fn=collate, num_workers=0)
print(f'Train batches: {len(train_loader)}, Val batches: {len(val_loader)}')
