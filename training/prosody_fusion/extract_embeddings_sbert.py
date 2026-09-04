#!/usr/bin/env python3
"""
Step 1: Pre-extract sentence embeddings using sentence-transformers.
paraphrase-multilingual-mpnet-base-v2 is OPTIMIZED for embedding extraction
and is faster than XLM-R [CLS] on CPU.
"""
import json, os, time, numpy as np
from torch.utils.data import Dataset, DataLoader
from sentence_transformers import SentenceTransformer

MODEL_NAME = 'paraphrase-multilingual-mpnet-base-v2'
DATA_DIR = '/Users/Subho/autonomous_laughter_prediction/training/prosody_fusion_data'
OUT_DIR = '/Users/Subho/autonomous_laughter_prediction/training/prosody_fusion_embeddings'
BATCH_SIZE = 64  # Larger batch - sentence-transformers is optimized

os.makedirs(OUT_DIR, exist_ok=True)

print(f"Loading sentence-transformers model: {MODEL_NAME}...")
model = SentenceTransformer(MODEL_NAME)
print(f"  Model loaded. Embedding dim: {model.get_sentence_embedding_dimension()}")

class TextDataset(Dataset):
    def __init__(self, path):
        self.samples = [json.loads(line) for line in open(path)]
        self.texts = [s['text'] for s in self.samples]
        self.uids = [s['uid'] for s in self.samples]
        self.labels = [s['label'] for s in self.samples]
        self.prosody = [s['prosody'] for s in self.samples]
    def __len__(self): return len(self.texts)
    def __getitem__(self, idx):
        return idx  # Return index, actual data fetched by collation

def extract_embeddings(split_name, dataset_path):
    out_file = os.path.join(OUT_DIR, f'{split_name}_embeddings.npz')
    if os.path.exists(out_file):
        print(f"  {split_name}: already extracted, skipping")
        return
    
    print(f"\nExtracting {split_name} embeddings from {dataset_path}...")
    ds = TextDataset(dataset_path)
    total = len(ds)
    t0 = time.time()
    
    # Encode in batches (sentence-transformers is highly optimized)
    embeddings = model.encode(
        ds.texts, 
        batch_size=BATCH_SIZE, 
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=False  # Keep raw embeddings for fusion
    )
    
    elapsed = time.time() - t0
    np.savez_compressed(
        out_file, 
        embeddings=embeddings,
        uids=np.array(ds.uids),
        labels=np.array(ds.labels),
        prosody=np.array(ds.prosody)
    )
    print(f"  {split_name}: extracted {len(embeddings)} embeddings, shape={embeddings.shape}")
    print(f"  Time: {elapsed:.0f}s ({elapsed/len(embeddings)*1000:.1f}ms/sample)")

# Extract all splits
for split in ['train', 'valid', 'test']:
    path = os.path.join(DATA_DIR, f'{split}.jsonl')
    extract_embeddings(split, path)

print("\n✅ Embedding extraction complete!")
print(f"Embeddings saved to: {OUT_DIR}/")
