#!/usr/bin/env python3
"""
Parallel WavLM extraction runner for scaleup pipeline.
Downloads audio → extracts WavLM embeddings → saves to queue.
Runs 5 download workers + 5 extraction workers in parallel.
"""
import os
import sys
import json
import time
import subprocess
import torch
from transformers import Wav2Vec2Model, Wav2Vec2FeatureExtractor
from tqdm import tqdm

# Config
AUDIO_DIR = Path("/Users/Subho/data/chuckle-net/audio_final")
WAVLM_DIR = Path("/Users/Subho/data/chuckle-net/wavlm_embeddings")
NUM_EXTRACT_WORKERS = 5

# Initialize Wav2Vec2 model (use CPU for parallel processing)
print("Loading Wav2Vec2 model...")
device = torch.device("cpu")
feature_extractor = Wav2Vec2FeatureExtractor.from_pretrained("facebook/wav2vec2-large-robust-ft-libri-960h")
model = Wav2Vec2Model.from_pretrained("facebook/wav2vec2-large-robust-ft-libri-960h", gradient_checkpointing=True)
model.to(device)
model.eval()
print("Wav2Vec2 model loaded.")


def extract_wav2vec2(audio_path: str, video_id: str) -> dict:
    """Extract Wav2Vec2 embedding for an audio file."""
    output_path = WAVLM_DIR / f"{video_id}.json"
    if output_path.exists():
        with open(output_path) as f:
            return json.load(f)
    
    try:
        # Load audio in chunks
        y, sr = librosa.load(audio_path, sr=16000)
        if len(y) < 400:
            return None
        
        # Process in 30s chunks
        embeddings = []
        for offset in range(0, len(y), 30*16000):
            chunk = y[offset:offset + 30*16000]
            if len(chunk) < 400:
                continue
            
            inputs = feature_extractor(chunk, sampling_rate=16000, return_tensors="pt")
            inputs = {k: v.to(device) for k, v in inputs.items()}
            with torch.no_grad():
                outputs = model(**inputs).last_hidden_state.mean(dim=1).cpu().numpy()
            embeddings.append(outputs[0])
        
        if not embeddings:
            return None
        
        final_emb = np.mean(embeddings, axis=0)
        result = {"video_id": video_id, "embedding": final_emb.tolist()}
        
        # Save immediately
        with open(output_path, 'w') as f:
            json.dump(result, f)
        
        return result
    except Exception as e:
        print(f"Error extracting {video_id}: {e}")
        return None

# For a robust implementation, we could add the chunking logic from before.
# Let's write the corrected version of extract_wav2vec2