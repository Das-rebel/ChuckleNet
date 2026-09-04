#!/usr/bin/env python3
"""Prepare WavLM embeddings for training with laughter labels."""

import json
import numpy as np
import torch
from pathlib import Path
from collections import defaultdict

WAVLM_DIR = Path("/Users/Subho/autonomous_laughter_prediction_essential/experiments/wavlm_embeddings")
PROSODY_FILE = Path("data/prosody_aligned/prosody_aligned_features.jsonl")
OUTPUT_FILE = Path("data/prosody_aligned/wavlm_training_data.npz")

print("Loading WavLM embeddings...")
wavlm_embeddings = {}
for pt_file in WAVLM_DIR.glob("*.pt"):
    video_id = pt_file.stem
    data = torch.load(pt_file, map_location='cpu')
    
    if isinstance(data, torch.Tensor):
        if data.dim() == 1:
            flat = data.numpy()
            if len(flat) % 768 == 0:
                n_frames = len(flat) // 768
                emb = flat.reshape(n_frames, 768)
            else:
                emb = flat.reshape(1, 768)
        else:
            emb = data.numpy()
    elif isinstance(data, dict) and 'embs' in data:
        emb = data['embs'].numpy()
    else:
        continue
    
    wavlm_embeddings[video_id] = emb
    
print(f"Total WavLM embeddings: {len(wavlm_embeddings)}")

print("\nLoading prosody features...")
prosody_by_video = defaultdict(list)
with open(PROSODY_FILE) as f:
    for line in f:
        obj = json.loads(line)
        video_id = obj.get("video_id", "")
        if video_id:
            prosody_by_video[video_id].append(obj)

print(f"Total prosody utterances: {sum(len(v) for v in prosody_by_video.values())}")
print(f"Prosody videos: {len(prosody_by_video)}")

# Check overlap
common_videos = set(wavlm_embeddings.keys()) & set(prosody_by_video.keys())
print(f"Videos with both WavLM and prosody: {len(common_videos)}")

if common_videos:
    # Create aligned dataset
    embeddings_list = []
    prosody_list = []
    labels_list = []
    uids_list = []

    for video_id in common_videos:
        wavlm_emb = wavlm_embeddings[video_id]
        prosody_segs = prosody_by_video[video_id]
        
        if len(wavlm_emb.shape) > 1:
            wavlm_avg = wavlm_emb.mean(axis=0)
        else:
            wavlm_avg = wavlm_emb
        
        for seg in prosody_segs:
            embeddings_list.append(wavlm_avg)
            prosody = np.array(seg.get("prosody_10dim", [0]*10))
            prosody_full = np.zeros(23)
            prosody_full[:len(prosody)] = prosody
            prosody_list.append(prosody_full)
            labels_list.append(seg.get("label_any", 0))
            uids_list.append(seg.get("uid", f"{video_id}_unknown"))

    embeddings_arr = np.array(embeddings_list)
    prosody_arr = np.array(prosody_list)
    labels_arr = np.array(labels_list)
    uids_arr = np.array(uids_list)

    print(f"\nAligned dataset:")
    print(f"  Embeddings: {embeddings_arr.shape}")
    print(f"  Prosody: {prosody_arr.shape}")
    print(f"  Labels: {labels_arr.shape}")
    print(f"  Positive rate: {labels_arr.mean():.3f}")

    np.savez(OUTPUT_FILE, 
             embeddings=embeddings_arr, 
             prosody=prosody_arr, 
             labels=labels_arr, 
             uids=uids_arr)
    print(f"\nSaved to {OUTPUT_FILE}")
else:
    print("\nNo overlap - checking what we have...")
    print(f"WavLM samples: {list(wavlm_embeddings.keys())[:3]}")
    print(f"Prosody samples: {list(prosody_by_video.keys())[:3]}")
