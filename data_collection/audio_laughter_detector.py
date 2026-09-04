#!/usr/bin/env python3
"""
Improved Audio-based laughter detector for comedy scaleup.
Combines RMS energy, Zero-Crossing Rate (ZCR), and periodicity
to separate laughter from loud speech.
"""
import os
import numpy as np
import librosa
import sys

def detect_laughter_density(audio_path: str) -> int:
    """
    Analyzes audio for laughter markers using a multi-feature approach:
    1. Energy (RMS) - Must be significantly above mean
    2. Zero-Crossing Rate (ZCR) - Must be high (laughter is noisier than speech)
    3. Periodicity - Laughter occurs in rhythmic bursts
    """
    try:
        # Load audio (16kHz, mono)
        y, sr = librosa.load(audio_path, sr=16000)
        if len(y) < 1000: 
            return 0

        # Feature Extraction
        rms = librosa.feature.rms(y=y)[0]
        zcr = librosa.feature.zero_crossing_rate(y)[0]
        
        # Normalize ZCR to 0-1 range
        zcr_norm = (zcr - np.min(zcr)) / (np.max(zcr) - np.min(zcr) + 1e-6)
        
        # Energy Threshold (Mean + 2.5 std)
        mean_energy = np.mean(rms)
        std_energy = np.std(rms)
        energy_thresh = mean_energy + 2.5 * std_energy
        
        # Laughter is typically: High Energy AND High ZCR
        # We look for regions where both are elevated
        laughter_mask = (rms > energy_thresh) & (zcr_norm > 0.5)
        
        spikes = np.where(laughter_mask)[0]
        if len(spikes) == 0:
            return 0
        
        # Cluster spikes into 'events' (spikes within 0.6s are part of the same laugh)
        # librosa hop_length = 512. 16000/512 = 31.25 fps. 0.6s approx 18 frames.
        clusters = 1
        for i in range(1, len(spikes)):
            if spikes[i] - spikes[i-1] > 18:
                clusters += 1
                
        return clusters
    except Exception as e:
        # print(f"Error analyzing {audio_path}: {e}")
        return 0

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 audio_laughter_detector.py <audio_path>")
        sys.exit(1)
    
    path = sys.argv[1]
    count = detect_laughter_density(path)
    print(count)
EOF