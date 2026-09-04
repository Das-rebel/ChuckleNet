#!/usr/bin/env python3
"""
Extract WavLM for videos that have audio but are missing embeddings.
Uses parallel workers for speed.
"""
import json, os, sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import torch
import librosa
import numpy as np
from transformers import WavLMModel

# Config
AUDIO_DIRS = [
    "/Users/Subho/data/chuckle-net/audio_final",
    "/Users/Subho/data/chuckle-net/audio",
    "/Users/Subho/data/chuckle-net/audio_new",
    "/Users/Subho/data/chuckle-net/audio_all"
]
WAVLM_DIR = Path("/Users/Subho/data/chuckle-net/wavlm_embeddings")
INPUT_FILE = "/tmp/remaining_wavlm_vids.json"
LOG_FILE = "/tmp/wavlm_extraction.log"
NUM_WORKERS = int(sys.argv[1]) if len(sys.argv) > 1 else 4

print(f"🚀 Starting WavLM extraction with {NUM_WORKERS} workers at {datetime.now().strftime('%H:%M:%S')}")

# Load video list
need_vids = json.load(open(INPUT_FILE))
print(f"Total videos to process: {len(need_vids)}")

# Load model once (shared across workers)
device = torch.device("cpu")
print("Loading WavLM model...")
model = WavLMModel.from_pretrained("microsoft/wavlm-base-plus")
model.to(device)
model.eval()
print("Model loaded!")

def find_audio(vid):
    """Find audio file for a video ID."""
    for d in AUDIO_DIRS:
        for ext in ['.wav', '.mp3', '.m4a']:
            p = Path(d) / f"{vid}{ext}"
            if p.exists():
                return str(p)
    return None

def extract_one(vid):
    """Extract WavLM embedding for a single video."""
    try:
        # Skip if already exists
        out_path = WAVLM_DIR / f"{vid}.json"
        if out_path.exists():
            return vid, "skip", None
        
        # Find audio
        audio_path = find_audio(vid)
        if not audio_path:
            return vid, "no_audio", None
        
        # Load and process audio
        y, sr = librosa.load(audio_path, sr=16000)
        if len(y) < 400:  # Too short
            return vid, "too_short", None
        
        # Extract embeddings in chunks
        embeddings = []
        chunk_size = 30 * 16000  # 30 seconds
        for offset in range(0, len(y), chunk_size):
            chunk = y[offset:offset+chunk_size]
            if len(chunk) < 400:
                continue
            inputs = torch.FloatTensor(chunk).unsqueeze(0).to(device)
            with torch.no_grad():
                outputs = model(inputs)
            emb = outputs.last_hidden_state.mean(dim=1).squeeze().cpu().numpy()
            embeddings.append(emb)
        
        if not embeddings:
            return vid, "no_embed", None
        
        # Average embeddings
        final_emb = np.mean(embeddings, axis=0)
        
        # Save
        with open(out_path, 'w') as f:
            json.dump({'video_id': vid, 'embedding': final_emb.tolist()}, f)
        
        return vid, "success", len(y)/sr
    except Exception as e:
        return vid, "error", str(e)[:100]

# Process
results = {"success": 0, "skip": 0, "no_audio": 0, "too_short": 0, "no_embed": 0, "error": 0}
start_time = datetime.now()

with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
    futures = {executor.submit(extract_one, vid): vid for vid in need_vids}
    
    for i, future in enumerate(as_completed(futures)):
        vid, status, extra = future.result()
        results[status] = results.get(status, 0) + 1
        
        # Progress every 10
        if (i + 1) % 10 == 0:
            elapsed = (datetime.now() - start_time).total_seconds()
            rate = (i + 1) / elapsed
            remaining = len(futures) - (i + 1)
            eta = remaining / rate if rate > 0 else 0
            print(f"  {i+1}/{len(futures)} - {results['success']} success, {results['error']} errors, ETA: {eta/60:.1f}min")

# Final report
elapsed = (datetime.now() - start_time).total_seconds()
print(f"\n{'='*50}")
print(f"✅ EXTRACTION COMPLETE")
print(f"{'='*50}")
print(f"Time: {elapsed/60:.1f} minutes")
print(f"Results:")
for k, v in results.items():
    if v > 0:
        print(f"  {k}: {v}")

# Verify count
final_count = len(list(WAVLM_DIR.glob("*.json")))
print(f"\nFinal WavLM count: {final_count}")