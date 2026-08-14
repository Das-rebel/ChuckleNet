#!/usr/bin/env python3
"""Extract WavLM embeddings from videos without aligned utterances."""

import subprocess
import numpy as np
from pathlib import Path
import torch
from transformers import WavLMModel
import librosa

VIDEO_DIR = Path("/Users/Subho/autonomous_laughter_prediction/data/raw/videos")
OUTPUT_DIR = Path("/Users/Subho/autonomous_laughter_prediction_essential/experiments/wavlm_embeddings")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {DEVICE}")

print("Loading WavLM...")
wavlm = WavLMModel.from_pretrained("microsoft/wavlm-base-plus").to(DEVICE).eval()
print("WavLM loaded")

videos = list(VIDEO_DIR.glob("*.m4a"))
print(f"Processing {len(videos)} videos...")

for i, video_path in enumerate(videos, 1):
    video_id = video_path.stem
    output_path = OUTPUT_DIR / f"{video_id}.pt"
    
    if output_path.exists():
        print(f"[{i}/{len(videos)}] {video_id}: Already done")
        continue
    
    print(f"[{i}/{len(videos)}] {video_id}: Processing...")
    
    try:
        # Load audio with librosa (returns float32 numpy array)
        waveform, sr = librosa.load(str(video_path), sr=16000, mono=True)
        
        # Process in 30-second chunks
        chunk_samples = 30 * 16000
        embeddings = []
        
        for start in range(0, len(waveform), chunk_samples):
            end = min(start + chunk_samples, len(waveform))
            chunk = waveform[start:end]
            
            # Convert to tensor
            inputs = torch.tensor(chunk).unsqueeze(0).to(DEVICE)
            
            with torch.no_grad():
                outputs = wavlm(inputs)
                emb = outputs.last_hidden_state.mean(dim=1).squeeze().cpu().numpy()
                embeddings.append(emb)
        
        # Concatenate and save
        final_emb = np.concatenate(embeddings) if len(embeddings) > 1 else embeddings[0]
        torch.save(torch.tensor(final_emb), output_path)
        
        print(f"  ✅ Saved: {final_emb.shape}")
        
    except Exception as e:
        print(f"  ❌ Error: {e}")

print("\nDone!")
