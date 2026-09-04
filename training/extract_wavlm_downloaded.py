#!/usr/bin/env python3
"""Extract WavLM embeddings from downloaded videos."""

import json
import subprocess
from pathlib import Path
import torch
from transformers import WavLMForAudioFrame, WavLMProcessor
import torchaudio

# Paths
VIDEO_DIR = Path("/Users/Subho/autonomous_laughter_prediction/data/raw/videos")
OUTPUT_DIR = Path("/Users/Subho/autonomous_laughter_prediction/data/chuckle-net/wavlm_embeddings")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Load model
print("Loading WavLM model...")
processor = WavLMProcessor.from_pretrained("facebook/wavlm-base-plus")
model = WavLMForAudioFrame.from_pretrained("facebook/wavlm-base-plus")
model.eval()

# Get downloaded videos
videos = list(VIDEO_DIR.glob("*.m4a"))
print(f"Found {len(videos)} downloaded videos")

# Extract embeddings
for video_path in videos:
    video_id = video_path.stem
    output_path = OUTPUT_DIR / f"{video_id}.pt"
    
    if output_path.exists():
        print(f"  Already done: {video_id}")
        continue
    
    print(f"  Processing: {video_id}")
    
    try:
        # Convert to WAV (required for WavLM)
        wav_path = video_path.with_suffix(".wav")
        
        # Extract audio using ffmpeg
        subprocess.run([
            "ffmpeg", "-y", "-i", str(video_path),
            "-ar", "16000", "-ac", "1", "-loglevel", "error",
            str(wav_path)
        ], timeout=300)
        
        # Load audio
        waveform, sample_rate = torchaudio.load(wav_path)
        
        # Resample if needed
        if sample_rate != 16000:
            waveform = torchaudio.functional.resample(waveform, sample_rate, 16000)
            sample_rate = 16000
        
        # Process in 30-second chunks
        chunk_size = 30 * sample_rate
        embeddings = []
        
        for start in range(0, waveform.shape[1], chunk_size):
            end = min(start + chunk_size, waveform.shape[1])
            chunk = waveform[:, start:end]
            
            inputs = processor(chunk.squeeze(), sampling_rate=sample_rate, return_tensors="pt")
            
            with torch.no_grad():
                outputs = model(**inputs)
                # Use audio frame hidden states (average over frames)
                hidden = outputs.hidden_states[0]  # [batch, frames, dim]
                emb = hidden.mean(dim=1).squeeze().numpy()
                embeddings.append(emb)
        
        # Save embedding
        import numpy as np
        embedding = np.concatenate(embeddings) if len(embeddings) > 1 else embeddings[0]
        torch.save(torch.tensor(embedding), output_path)
        
        # Cleanup WAV
        wav_path.unlink()
        
        print(f"    ✅ Saved: {embedding.shape}")
        
    except Exception as e:
        print(f"    ❌ Error: {e}")

print(f"\nDone! Embeddings saved to {OUTPUT_DIR}")
