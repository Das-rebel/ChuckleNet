#!/usr/bin/env python3
"""Extract WavLM embeddings from newly downloaded videos."""

import subprocess
from pathlib import Path
import torch
import numpy as np
from transformers import WavLMModel, WavLMProcessor
import torchaudio

VIDEO_DIR = Path("/Users/Subho/autonomous_laughter_prediction/data/raw/videos")
OUTPUT_DIR = Path("/Users/Subho/autonomous_laughter_prediction_essential/experiments/wavlm_embeddings")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("Loading WavLM model...")
processor = WavLMProcessor.from_pretrained("facebook/wavlm-base-plus")
model = WavLMModel.from_pretrained("facebook/wavlm-base-plus")
model.eval()

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
        wav_path = video_path.with_suffix(".wav")
        
        # Convert to WAV
        subprocess.run([
            "ffmpeg", "-y", "-i", str(video_path),
            "-ar", "16000", "-ac", "1", "-loglevel", "error",
            str(wav_path)
        ], timeout=600)
        
        # Load and process
        waveform, sr = torchaudio.load(wav_path)
        if sr != 16000:
            waveform = torchaudio.functional.resample(waveform, sr, 16000)
        
        # Process in chunks
        chunk_len = 30 * 16000
        embeddings = []
        
        for start in range(0, waveform.shape[1], chunk_len):
            chunk = waveform[:, start:start+chunk_len]
            inputs = processor(chunk.squeeze(), sampling_rate=16000, return_tensors="pt")
            
            with torch.no_grad():
                outputs = model(**inputs)
                emb = outputs.last_hidden_state.mean(dim=1).squeeze().numpy()
                embeddings.append(emb)
        
        # Save
        final_emb = np.concatenate(embeddings) if len(embeddings) > 1 else embeddings[0]
        torch.save(torch.tensor(final_emb), output_path)
        
        # Cleanup
        wav_path.unlink()
        
        print(f"  ✅ Saved: {final_emb.shape}")
        
    except Exception as e:
        print(f"  ❌ Error: {e}")

print("\nDone!")
