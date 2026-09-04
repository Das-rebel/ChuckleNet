#!/usr/bin/env python3
"""
Extract WavLM for videos that already have audio.
"""

import os
import sys
import json
import numpy as np
import librosa
import torch
from transformers import Wav2Vec2FeatureExtractor, WavLMModel
from pathlib import Path

# Paths
PROCESSED_DIR = '/Users/Subho/data/chuckle-net-youtube/processed'
AUDIO_DIR = '/Users/Subho/data/chuckle-net-youtube/audio'
WAVLM_DIR = '/Users/Subho/data/chuckle-net-youtube/wavlm_embeddings'

os.makedirs(WAVLM_DIR, exist_ok=True)

def extract_wavlm(audio_path: str, utterances: list) -> dict:
    """Extract WavLM embeddings for all utterances."""
    
    # Load model
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    if not hasattr(extract_wavlm, 'model_loaded'):
        print("  Loading WavLM model...")
        processor = Wav2Vec2FeatureExtractor.from_pretrained('microsoft/wavlm-base')
        model = WavLMModel.from_pretrained('microsoft/wavlm-base')
        model.to(device)
        model.eval()
        extract_wavlm.processor = processor
        extract_wavlm.model = model
        extract_wavlm.device = device
        print(f"  WavLM on {device}")
    
    processor = extract_wavlm.processor
    model = extract_wavlm.model
    
    embeddings = {}
    for i, utt in enumerate(utterances):
        uid = utt['utterance_id']
        start = utt['start']
        end = utt['end']
        
        try:
            y, sr = librosa.load(audio_path, sr=16000, offset=start, duration=end-start)
            if len(y) < 400:
                continue
            
            inputs = processor(y, sampling_rate=16000, return_tensors='pt')
            inputs = {k: v.to(device) for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = model(**inputs)
            
            hidden_states = outputs.hidden_states
            if hidden_states is not None and len(hidden_states) > 0:
                embedding = hidden_states[-1][0].mean(dim=0).cpu().numpy()
            else:
                continue
            
            embeddings[uid] = embedding.tolist()
            
        except Exception as e:
            continue
    
    return embeddings

def main():
    print("=" * 60)
    print("WavLM Extraction for Available Audio")
    print("=" * 60)
    
    # Get audio files
    audio_files = sorted([f.replace('.wav', '') for f in os.listdir(AUDIO_DIR) if f.endswith('.wav')])
    print(f"Audio files: {len(audio_files)}")
    
    # Check which already done
    done = set(f.replace('.json', '') for f in os.listdir(WAVLM_DIR) if f.endswith('.json'))
    print(f"Already extracted: {len(done)}")
    
    to_process = [v for v in audio_files if v not in done]
    print(f"To process: {len(to_process)}")
    
    if not to_process:
        print("Nothing to do!")
        return
    
    total_embeddings = 0
    
    for i, video_id in enumerate(to_process):
        print(f"\n[{i+1}/{len(to_process)}] {video_id}")
        
        audio_path = os.path.join(AUDIO_DIR, f'{video_id}.wav')
        meta_path = os.path.join(PROCESSED_DIR, f'{video_id}.json')
        
        if not os.path.exists(meta_path):
            print(f"  No metadata, skipping")
            continue
        
        with open(meta_path) as f:
            data = json.load(f)
        
        utterances = data.get('utterances', [])
        print(f"  Utterances: {len(utterances)}")
        
        # Extract
        print(f"  Extracting...")
        embeddings = extract_wavlm(audio_path, utterances)
        
        if embeddings:
            output_path = os.path.join(WAVLM_DIR, f'{video_id}.json')
            with open(output_path, 'w') as f:
                json.dump(embeddings, f)
            print(f"  ✓ {len(embeddings)} embeddings")
            total_embeddings += len(embeddings)
        else:
            print(f"  ✗ No embeddings")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    total_files = len([f for f in os.listdir(WAVLM_DIR) if f.endswith('.json')])
    print(f"WavLM files: {total_files}")
    print(f"New embeddings: {total_embeddings}")

if __name__ == '__main__':
    main()
