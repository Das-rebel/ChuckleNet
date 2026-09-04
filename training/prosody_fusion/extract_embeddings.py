#!/usr/bin/env python3
"""
Step 1: Pre-extract XLM-R [CLS] embeddings for all dataset samples.
This is a ONE-TIME operation. Saves embeddings to .npz files.
Then train_prosody_fusion.py trains only the MLP on cached embeddings.
"""
import json, os, time, torch, numpy as np
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModel

MODEL_NAME = 'FacebookAI/xlm-roberta-base'
DATA_DIR = '/Users/Subho/autonomous_laughter_prediction/training/prosody_fusion_data'
OUT_DIR = '/Users/Subho/autonomous_laughter_prediction/training/prosody_fusion_embeddings'
BATCH_SIZE = 16  # Smaller batch for CPU
MAX_LEN = 128
EMBED_DIM = 768  # XLM-R hidden size

os.makedirs(OUT_DIR, exist_ok=True)

device = torch.device('cpu')
print(f"Device: {device}")

# Load tokenizer and model
print("Loading XLM-R...")
tok = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModel.from_pretrained(MODEL_NAME).to(device)
model.eval()
print(f"  Model loaded: {MODEL_NAME}")

class TextDataset(Dataset):
    def __init__(self, path):
        self.samples = [json.loads(line) for line in open(path)]
    def __len__(self): return len(self.samples)
    def __getitem__(self, idx):
        return self.samples[idx]['text']

def extract_embeddings(split_name, dataset_path):
    out_file = os.path.join(OUT_DIR, f'{split_name}_embeddings.npz')
    if os.path.exists(out_file):
        print(f"  {split_name}: already extracted, skipping")
        return
    
    print(f"\nExtracting {split_name} embeddings from {dataset_path}...")
    ds = TextDataset(dataset_path)
    loader = DataLoader(ds, batch_size=BATCH_SIZE, shuffle=False)
    
    all_embeddings = []
    t0 = time.time()
    total_batches = len(loader)
    
    for batch_idx, texts in enumerate(loader):
        enc = tok(
            list(texts), 
            truncation=True, 
            max_length=MAX_LEN, 
            padding='max_length', 
            return_tensors='pt'
        )
        input_ids = enc['input_ids'].to(device)
        attention_mask = enc['attention_mask'].to(device)
        
        with torch.no_grad():
            outputs = model(input_ids=input_ids, attention_mask=attention_mask)
            cls_emb = outputs.last_hidden_state[:, 0, :].cpu().numpy()  # [CLS]
        
        all_embeddings.append(cls_emb)
        
        if (batch_idx + 1) % 50 == 0:
            elapsed = time.time() - t0
            pct = (batch_idx + 1) / total_batches * 100
            eta = elapsed / (batch_idx + 1) * (total_batches - batch_idx - 1)
            print(f"  {batch_idx+1}/{total_batches} batches ({pct:.0f}%) | ETA: {eta:.0f}s")
    
    embeddings = np.vstack(all_embeddings)  # [N, 768]
    np.savez_compressed(out_file, embeddings=embeddings)
    elapsed = time.time() - t0
    print(f"  {split_name}: extracted {len(embeddings)} embeddings, shape={embeddings.shape}, saved to {out_file}")
    print(f"  Time: {elapsed:.0f}s ({elapsed/len(embeddings)*1000:.1f}ms/sample)")
    
    return embeddings

# Extract all splits
for split in ['train', 'valid', 'test']:
    path = os.path.join(DATA_DIR, f'{split}.jsonl')
    extract_embeddings(split, path)

print("\n✅ Embedding extraction complete!")
print(f"Embeddings saved to: {OUT_DIR}/")
