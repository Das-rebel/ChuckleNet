#!/usr/bin/env python3
"""Extract WavLM embeddings from all 512 videos."""

import subprocess
import numpy as np
from pathlib import Path
import torch
from transformers import WavLMModel
import librosa
import time

VIDEO_DIR = Path("/Users/Subho/autonomous_laughter_prediction/data/raw/videos")
OUTPUT_DIR = Path("/Users/Subho/autonomous_laughter_prediction_essential/experiments/wavlm_embeddings")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {DEVICE}")

print("Loading WavLM...")
wavlm = WavLMModel.from_pretrained("microsoft/wavlm-base-plus").to(DEVICE).eval()
print("WavLM loaded")

videos = sorted([f for f in VIDEO_DIR.glob("*.m4a")])
print(f"Processing {len(videos)} videos...")

t0 = time.time()
for i, video_path in enumerate(videos, 1):
    video_id = video_path.stem
    output_path = OUTPUT_DIR / f"{video_id}.pt"
    
    if output_path.exists():
        print(f"[{i}/{len(videos)}] {video_id}: Already done")
        continue
    
    t1 = time.time()
    print(f"[{i}/{len(videos)}] {video_id}: Processing...", end=" ", flush=True)
    
    try:
        waveform, sr = librosa.load(str(video_path), sr=16000, mono=True)
        
        chunk_samples = 30 * 16000
        embeddings = []
        
        for start in range(0, len(waveform), chunk_samples):
            end = min(start + chunk_samples, len(waveform))
            chunk = waveform[start:end]
            inputs = torch.tensor(chunk).unsqueeze(0).to(DEVICE)
            
            with torch.no_grad():
                outputs = wavlm(inputs)
                emb = outputs.last_hidden_state.mean(dim=1).squeeze().cpu().numpy()
                embeddings.append(emb)
        
        final_emb = np.concatenate(embeddings) if len(embeddings) > 1 else embeddings[0]
        torch.save(torch.tensor(final_emb), output_path)
        
        elapsed = time.time() - t1
        print(f"✅ ({final_emb.shape}, {elapsed:.1f}s)")
        
    except Exception as e:
        print(f"❌ {e}")

total = time.time() - t0
print(f"\n=== EXTRACTION COMPLETE ===")
print(f"Total time: {total/60:.1f} minutes")
print(f"Embeddings: {len(list(OUTPUT_DIR.glob('*.pt')))}")
