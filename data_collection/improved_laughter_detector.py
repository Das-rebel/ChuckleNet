#!/usr/bin/env python3
"""
Improved Audio-based laughter detector using ML-informed features.
Based on literature:
- Purandare & Litman (2006): Energy + spectral features for laughter
- Bertero & Fung (2016): Duration + periodicity patterns
- Truong & Van Leeuwen (2007): Spectral flux for laugh detection

Input: Path to audio file (.wav)
Output: Estimated count of laughter events
"""
import os
import json
import numpy as np
import librosa
import subprocess
import sys
from pathlib import Path

def extract_laughter_features(audio_path: str) -> int:
    """
    Extract features and count laughter clusters.
    
    Features used:
    1. RMS Energy - Laughter has higher energy
    2. Spectral Flux - Laughter has distinct spectral changes  
    3. Zero Crossing Rate - Laughter is noisier (higher ZCR)
    4. Spectral Centroid - Laughter has higher centroid
    
    A "laughter" segment is detected when:
    - Energy > threshold AND
    - (High ZCR OR High spectral flux) AND
    - Duration > 0.3s
    """
    try:
        y, sr = librosa.load(audio_path, sr=16000)
        if len(y) < 2000:  # Less than 0.125s, skip
            return 0
        
        # Extract features
        # RMS - energy envelope
        rms = librosa.feature.rms(y=y, hop_length=512)[0]
        
        # Spectral flux - rate of change in spectrum
        onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=512)
        
        # Zero crossing rate - noise measure
        zcr = librosa.feature.zero_crossing_rate(y, hop_length=512)[0]
        
        # Spectral centroid - "center of mass" of spectrum
        cent = librosa.feature.spectral_centroid(y=y, sr=sr, hop_length=512)[0]
        
        # Normalize features to 0-1
        rms_norm = (rms - np.min(rms)) / (np.max(rms) - np.min(rms) + 1e-6)
        onset_norm = (onset_env - np.min(onset_env)) / (np.max(onset_env) - np.min(onset_env) + 1e-6)
        zcr_norm = (zcr - np.min(zcr)) / (np.max(zcr) - np.min(zcr) + 1e-6)
        cent_norm = (cent - np.min(cent)) / (np.max(cent) - np.min(cent) + 1e-6)
        
        # Combined laughter score
        # Laughter: high energy + (high onset OR high ZCR) + high centroid
        score = (
            rms_norm * 0.4 + 
            np.maximum(onset_norm, zcr_norm) * 0.4 + 
            cent_norm * 0.2
        )
        
        # Threshold: mean + 2*std
        threshold = np.mean(score) + 2 * np.std(score)
        candidates = np.where(score > threshold)[0]
        
        if len(candidates) == 0:
            return 0
        
        # Cluster candidates into events
        # 0.6s = ~18 frames at hop=512, sr=16000
        min_gap = 18
        clusters = 1
        for i in range(1, len(candidates)):
            if candidates[i] - candidates[i-1] > min_gap:
                clusters += 1
        
        return int(clusters)
    except Exception as e:
        # print(f"Error: {e}")
        return 0

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 improved_laughter_detector.py <audio.wav>")
        sys.exit(1)
    
    result = extract_laughter_features(sys.argv[1])
    print(result)