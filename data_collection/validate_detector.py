#!/usr/bin/env python3
"""
Validation script for audio-based laughter detection.
Tests the detector against ground truth from video_manifest.json.
"""
import os
import json
import numpy as np
import librosa
from pathlib import Path

# Paths
MANIFEST_PATH = '/Users/Subho/autonomous_laughter_prediction/kaggle_extraction/video_manifest.json'
AUDIO_DIR = Path('/Users/Subho/data/chuckle-net/audio_final')

def detect_laughter_density(audio_path: str) -> int:
    """Same logic as audio_laughter_detector.py"""
    try:
        y, sr = librosa.load(audio_path, sr=16000)
        if len(y) < 1000: return 0
        rms = librosa.feature.rms(y=y)[0]
        mean_energy = np.mean(rms)
        std_energy = np.std(rms)
        threshold = mean_energy + 3 * std_energy
        spikes = np.where(rms > threshold)[0]
        if len(spikes) == 0: return 0
        clusters = 1
        for i in range(1, len(spikes)):
            if spikes[i] - spikes[i-1] > 15:
                clusters += 1
        return clusters
    except Exception:
        return 0

def main():
    with open(MANIFEST_PATH, 'r') as f:
        manifest = json.load(f)

    positives = [v for v in manifest if v['n_positive'] > 0]
    negatives = [v for v in manifest if v['n_positive'] == 0]

    # Sample a few that have audio files
    test_set = []
    
    # Get 10 positives with audio
    count = 0
    for v in positives:
        path = AUDIO_DIR / f"{v['video_id']}.wav"
        if path.exists():
            test_set.append({'vid': v['video_id'], 'label': 'POS', 'truth': v['n_positive'], 'path': str(path)})
            count += 1
        if count >= 10: break

    # Get 10 negatives with audio
    count = 0
    for v in negatives:
        path = AUDIO_DIR / f"{v['video_id']}.wav"
        if path.exists():
            test_set.append({'vid': v['video_id'], 'label': 'NEG', 'truth': v['n_positive'], 'path': str(path)})
            count += 1
        if count >= 10: break

    print(f"{'Video ID':<15} | {'Truth':<10} | {'Detected':<10} | {'Match'}")
    print("-" * 50)
    
    matches = 0
    for item in test_set:
        detected = detect_laughter_density(item['path'])
        # Match if POS and detected > 0, or NEG and detected == 0 (simplified)
        is_match = (item['label'] == 'POS' and detected > 0) or (item['label'] == 'NEG' and detected == 0)
        if is_match: matches += 1
        print(f"{item['vid']:<15} | {item['truth']:<10} | {detected:<10} | {'✅' if is_match else '❌'}")

    print("-" * 50)
    print(f"Accuracy: {matches/len(test_set) if test_set else 0:.2%}")

if __name__ == "__main__":
    main()
EOF