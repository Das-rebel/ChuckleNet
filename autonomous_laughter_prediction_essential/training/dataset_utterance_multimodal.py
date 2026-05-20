#!/usr/bin/env python3
"""
Utterance-level multimodal dataset for WavLM + XLM-R fusion training.

Loads utterances from aligned_utterances.jsonl, tokenizes text with XLM-R
tokenizer, loads pre-extracted WavLM embeddings from .pt file, and returns
batch-ready dicts with per-video train/val/test splits (no data leakage).

Data format (aligned_utterances.jsonl):
{
    "utterance_id": "45VWTm3ldJ8_0000",
    "video_id": "45VWTm3ldJ8",
    "text": "Hello everyone...",
    "start": 0.0,
    "end": 11.16,
    "duration": 11.16,
    "n_words": 24,
    "n_positive_words": 16,
    "positive_ratio": 0.667,
    "label_any": 1,
    "label_majority": 1,
    "audio_file": "data/audio_comedy/audio/batch1/45VWTm3ldJ8.mp3"
}
"""

from __future__ import annotations

import json
import os
import random
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import torch
from torch.utils.data import Dataset, Subset
from transformers import AutoTokenizer

# ---------------------------------------------------------------------------
# Dataset
# ---------------------------------------------------------------------------

class UtteranceMultimodalDataset(Dataset):
    """
    Multimodal utterance dataset combining text (XLM-R) + audio (WavLM).
    
    Each item returns:
        input_ids: (max_seq_length,) - tokenized text
        attention_mask: (max_seq_length,) - attention mask
        audio_embedding: (768,) - WavLM mean-pooled embedding (or zero vector)
        label: int - 0 or 1 (label_any)
        utterance_id: str
        video_id: str
        metadata: dict - duration, positive_ratio, etc.
    """
    
    def __init__(
        self,
        utterances_path: str,
        wavlm_embeddings_path: Optional[str] = None,
        tokenizer_name: str = "FacebookAI/xlm-roberta-base",
        max_seq_length: int = 256,
        label_key: str = "label_any",
        load_embeddings: bool = True,
    ):
        """
        Args:
            utterances_path: Path to aligned_utterances.jsonl
            wavlm_embeddings_path: Path to wavlm_utterance_embeddings.pt
            tokenizer_name: XLM-R tokenizer name
            max_seq_length: Max token sequence length
            label_key: Which label to use ('label_any' or 'label_majority')
            load_embeddings: Whether to load WavLM embeddings (False for text-only)
        """
        super().__init__()
        
        self.max_seq_length = max_seq_length
        self.label_key = label_key
        self.load_embeddings = load_embeddings
        
        # Load tokenizer
        print(f"Loading tokenizer: {tokenizer_name}")
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)
        
        # Load utterances
        print(f"Loading utterances from {utterances_path}...")
        self.utterances: List[dict] = []
        self.video_ids: List[str] = []
        self.utterance_id_to_idx: Dict[str, int] = {}
        
        with open(utterances_path) as f:
            for i, line in enumerate(f):
                d = json.loads(line.strip())
                self.utterances.append(d)
                self.video_ids.append(d["video_id"])
                self.utterance_id_to_idx[d["utterance_id"]] = i
        
        print(f"Loaded {len(self.utterances)} utterances")
        
        # Compute stats
        labels = [u[label_key] for u in self.utterances]
        pos = sum(labels)
        neg = len(labels) - pos
        print(f"Label distribution ({label_key}): {pos} positive ({100*pos/len(labels):.1f}%), "
              f"{neg} negative ({100*neg/len(labels):.1f}%)")
        
        unique_videos = set(self.video_ids)
        print(f"Unique videos: {len(unique_videos)}")
        
        # Load WavLM embeddings
        self.wavlm_embeddings: Dict[str, torch.Tensor] = {}
        if load_embeddings and wavlm_embeddings_path and os.path.exists(wavlm_embeddings_path):
            print(f"Loading WavLM embeddings from {wavlm_embeddings_path}...")
            loaded = torch.load(wavlm_embeddings_path, map_location="cpu", weights_only=False)
            if isinstance(loaded, dict):
                self.wavlm_embeddings = loaded
            else:
                print(f"  [WARN] Unexpected embeddings format: {type(loaded)}")
            
            # Check coverage
            found = sum(1 for u in self.utterances if u["utterance_id"] in self.wavlm_embeddings)
            print(f"Embedding coverage: {found}/{len(self.utterances)} "
                  f"({100*found/len(self.utterances):.1f}%)")
            
            # Embedding dimension
            for k, v in self.wavlm_embeddings.items():
                print(f"Embedding dimension: {v.shape[-1]}")
                break
        elif load_embeddings and wavlm_embeddings_path:
            print(f"[WARN] Embeddings file not found: {wavlm_embeddings_path}")
            print("  Will use zero vectors for all audio embeddings")
        
        # Determine embedding dimension
        self.embedding_dim = 768  # WavLM-base-plus default
        if self.wavlm_embeddings:
            sample_key = next(iter(self.wavlm_embeddings))
            self.embedding_dim = self.wavlm_embeddings[sample_key].shape[-1]
    
    def __len__(self) -> int:
        return len(self.utterances)
    
    def __getitem__(self, idx: int) -> dict:
        utt = self.utterances[idx]
        uid = utt["utterance_id"]
        
        # Tokenize text
        encoding = self.tokenizer(
            utt["text"],
            max_length=self.max_seq_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )
        
        input_ids = encoding["input_ids"].squeeze(0)  # (max_seq_length,)
        attention_mask = encoding["attention_mask"].squeeze(0)  # (max_seq_length,)
        
        # Get audio embedding
        if uid in self.wavlm_embeddings:
            audio_emb = self.wavlm_embeddings[uid].float()
        else:
            audio_emb = torch.zeros(self.embedding_dim)
        
        label = utt[self.label_key]
        
        return {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "audio_embedding": audio_emb,
            "label": torch.tensor(label, dtype=torch.long),
            "utterance_id": uid,
            "video_id": utt["video_id"],
            "duration": utt.get("duration", 0.0),
            "positive_ratio": utt.get("positive_ratio", 0.0),
        }


# ---------------------------------------------------------------------------
# Video-level GroupKFold splits (no data leakage)
# ---------------------------------------------------------------------------

def create_video_splits(
    dataset: UtteranceMultimodalDataset,
    n_splits: int = 5,
    test_size: float = 0.15,
    val_size: float = 0.15,
    seed: int = 42,
) -> List[dict]:
    """
    Create per-video train/val/test splits. No video appears in more than one split.
    
    Returns list of split dicts, each with 'train', 'val', 'test' index lists.
    """
    from sklearn.model_selection import GroupKFold
    
    # Group by video_id
    unique_videos = sorted(set(dataset.video_ids))
    video_to_indices = defaultdict(list)
    for i, vid in enumerate(dataset.video_ids):
        video_to_indices[vid].append(i)
    
    # Compute video-level label stats for stratified splitting
    video_stats = {}
    for vid, indices in video_to_indices.items():
        labels = [dataset.utterances[i][dataset.label_key] for i in indices]
        video_stats[vid] = {
            "n_utterances": len(indices),
            "pos_rate": sum(labels) / len(labels) if labels else 0,
            "indices": indices,
        }
    
    rng = random.Random(seed)
    rng.shuffle(unique_videos)
    
    # Split videos: test, val, train
    n_test = max(1, int(len(unique_videos) * test_size))
    n_val = max(1, int(len(unique_videos) * val_size))
    
    test_videos = set(unique_videos[:n_test])
    val_videos = set(unique_videos[n_test:n_test + n_val])
    train_videos = set(unique_videos[n_test + n_val:])
    
    train_indices = []
    val_indices = []
    test_indices = []
    
    for vid in sorted(unique_videos):
        indices = video_to_indices[vid]
        if vid in test_videos:
            test_indices.extend(indices)
        elif vid in val_videos:
            val_indices.extend(indices)
        else:
            train_indices.extend(indices)
    
    print(f"\nVideo-level split:")
    print(f"  Train: {len(train_videos)} videos, {len(train_indices)} utterances")
    print(f"  Val:   {len(val_videos)} videos, {len(val_indices)} utterances")
    print(f"  Test:  {len(test_videos)} videos, {len(test_indices)} utterances")
    
    # Label distribution per split
    for name, indices in [("Train", train_indices), ("Val", val_indices), ("Test", test_indices)]:
        labels = [dataset.utterances[i][dataset.label_key] for i in indices]
        pos = sum(labels)
        neg = len(labels) - pos
        print(f"  {name} labels: {pos} pos ({100*pos/len(labels):.1f}%), {neg} neg")
    
    return {
        "train": train_indices,
        "val": val_indices,
        "test": test_indices,
        "train_videos": sorted(train_videos),
        "val_videos": sorted(val_videos),
        "test_videos": sorted(test_videos),
    }


def create_group_kfold(
    dataset: UtteranceMultimodalDataset,
    n_splits: int = 5,
    seed: int = 42,
) -> List[dict]:
    """
    Create GroupKFold splits where groups = video_id.
    Returns list of {train_indices, val_indices} for each fold.
    """
    from sklearn.model_selection import GroupKFold
    
    X = list(range(len(dataset)))
    y = [dataset.utterances[i][dataset.label_key] for i in X]
    groups = dataset.video_ids
    
    gkf = GroupKFold(n_splits=n_splits)
    
    folds = []
    for fold_idx, (train_idx, val_idx) in enumerate(gkf.split(X, y, groups=groups)):
        train_idx = train_idx.tolist()
        val_idx = val_idx.tolist()
        
        train_labels = [dataset.utterances[i][dataset.label_key] for i in train_idx]
        val_labels = [dataset.utterances[i][dataset.label_key] for i in val_idx]
        
        train_videos = set(dataset.video_ids[i] for i in train_idx)
        val_videos = set(dataset.video_ids[i] for i in val_idx)
        
        print(f"\nFold {fold_idx + 1}/{n_splits}:")
        print(f"  Train: {len(train_videos)} videos, {len(train_idx)} utterances, "
              f"pos rate: {sum(train_labels)/len(train_labels):.3f}")
        print(f"  Val:   {len(val_videos)} videos, {len(val_idx)} utterances, "
              f"pos rate: {sum(val_labels)/len(val_labels):.3f}")
        print(f"  Video overlap: {len(train_videos & val_videos)} (should be 0)")
        
        folds.append({
            "train": train_idx,
            "val": val_idx,
            "train_videos": sorted(train_videos),
            "val_videos": sorted(val_videos),
        })
    
    return folds


# ---------------------------------------------------------------------------
# Collate function
# ---------------------------------------------------------------------------

def collate_fn(batch: List[dict]) -> dict:
    """Collate a list of dicts into a batch dict."""
    return {
        "input_ids": torch.stack([item["input_ids"] for item in batch]),
        "attention_mask": torch.stack([item["attention_mask"] for item in batch]),
        "audio_embedding": torch.stack([item["audio_embedding"] for item in batch]),
        "labels": torch.stack([item["label"] for item in batch]),
        "utterance_ids": [item["utterance_id"] for item in batch],
        "video_ids": [item["video_id"] for item in batch],
        "durations": [item["duration"] for item in batch],
        "positive_ratios": [item["positive_ratio"] for item in batch],
    }


# ---------------------------------------------------------------------------
# Quick test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    utterances_path = "autonomous_laughter_prediction_essential/data/audio_comedy/aligned_utterances.jsonl"
    embeddings_path = "data/audio_comedy/wavlm_utterance_embeddings.pt"
    
    print("Testing UtteranceMultimodalDataset...")
    ds = UtteranceMultimodalDataset(
        utterances_path=utterances_path,
        wavlm_embeddings_path=embeddings_path,
        load_embeddings=True,
    )
    
    # Test single item
    item = ds[0]
    print(f"\nSample item:")
    print(f"  input_ids shape: {item['input_ids'].shape}")
    print(f"  attention_mask shape: {item['attention_mask'].shape}")
    print(f"  audio_embedding shape: {item['audio_embedding'].shape}")
    print(f"  label: {item['label'].item()}")
    print(f"  utterance_id: {item['utterance_id']}")
    print(f"  video_id: {item['video_id']}")
    
    # Test collation
    from torch.utils.data import DataLoader
    loader = DataLoader(ds, batch_size=8, shuffle=False, collate_fn=collate_fn)
    batch = next(iter(loader))
    print(f"\nBatch shapes:")
    print(f"  input_ids: {batch['input_ids'].shape}")
    print(f"  attention_mask: {batch['attention_mask'].shape}")
    print(f"  audio_embedding: {batch['audio_embedding'].shape}")
    print(f"  labels: {batch['labels'].shape}")
    
    # Test video splits
    print("\n\nCreating video-level splits...")
    splits = create_video_splits(ds)
    
    print("\nCreating GroupKFold splits...")
    folds = create_group_kfold(ds, n_splits=3)  # Quick test with 3 folds