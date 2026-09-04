#!/usr/bin/env python3
"""
Extract 21-dim prosody features for the 555 video dataset.
Then combine with existing WavLM embeddings to create complete training data.
"""

import json
import os
import numpy as np
import librosa
from pathlib import Path
from tqdm import tqdm
import time
import warnings
warnings.filterwarnings('ignore')

# Paths
AUDIO_DIR = Path("/Users/Subho/data/chuckle-net")
DATA_555 = "/tmp/chuckle_555/wavlm_555_videos.npz"
OUTPUT_FILE = "/Users/Subho/autonomous_laughter_prediction/data/prosody_555_completed.npz"

print("=" * 60)
print("Prosody Extraction for 555 Videos Dataset")
print("=" * 60)

def extract_prosody(audio_path, start, end, sr=16000):
    """
    Extract 21-dim prosody features for an audio segment.
    
    Features (21 dims):
    - F0/pitch (5): mean, std, max, min, voiced_rate
    - Energy (5): mean, std, max, min, range  
    - Duration (2): duration_s, speech_rate
    - Spectral (5): spectral_centroid, spectral_bandwidth, spectral_rolloff, 
                    spectral_contrast, spectral_flatness
    - Voice quality (4): zcr, jitter_approx, shimmer_approx, voiced_seg_ratio
    """
    try:
        # Load audio segment
        y, sr = librosa.load(audio_path, sr=sr, mono=True, offset=start, duration=end-start)
        
        if len(y) < sr * 0.05:  # Skip if too short
            return None
        
        feats = []
        
        # 1. F0/pitch features (5 dims)
        try:
            f0, voiced_flag, voiced_probs = librosa.pyin(
                y, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'), sr=sr
            )
            f0_values = f0[~np.isnan(f0)]
            if len(f0_values) > 0:
                feats.extend([
                    np.mean(f0_values),    # f0_mean
                    np.std(f0_values),    # f0_std
                    np.max(f0_values),    # f0_max
                    np.min(f0_values),    # f0_min
                    np.mean(voiced_flag), # voiced_rate
                ])
            else:
                feats.extend([0, 0, 0, 0, 0])
        except:
            feats.extend([0, 0, 0, 0, 0])
        
        # 2. Energy features (5 dims)
        try:
            rms = librosa.feature.rms(y=y)[0]
            feats.extend([
                np.mean(rms),      # energy_mean
                np.std(rms),       # energy_std
                np.max(rms),       # energy_max
                np.min(rms),       # energy_min
                np.max(rms) - np.min(rms),  # energy_range
            ])
        except:
            feats.extend([0, 0, 0, 0, 0])
        
        # 3. Duration features (2 dims)
        duration = len(y) / sr
        speech_rate = 1 / duration if duration > 0 else 0
        feats.extend([duration, speech_rate])
        
        # 4. Spectral features (5 dims)
        try:
            spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]
            spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
            spectral_contrast = librosa.feature.spectral_contrast(y=y, sr=sr)[0]
            spectral_flatness = librosa.feature.spectral_flatness(y=y)[0]
            
            feats.extend([
                np.mean(spectral_centroid),
                np.mean(spectral_bandwidth),
                np.mean(spectral_rolloff),
                np.mean(spectral_contrast),
                np.mean(spectral_flatness),
            ])
        except:
            feats.extend([0, 0, 0, 0, 0])
        
        # 5. Voice quality features (4 dims)
        try:
            zcr = librosa.feature.zero_crossing_rate(y)[0]
            # Jitter (pitch variation)
            f0_values = f0[~np.isnan(f0)]
            if len(f0_values) > 1:
                jitter = np.mean(np.abs(np.diff(f0_values))) / np.mean(f0_values)
            else:
                jitter = 0
            # Shimmer (amplitude variation)
            if len(rms) > 1:
                shimmer = np.mean(np.abs(np.diff(rms))) / np.mean(rms)
            else:
                shimmer = 0
            
            feats.extend([
                np.mean(zcr),         # zcr
                jitter,               # jitter
                shimmer,              # shimmer
                np.mean(voiced_flag), # voiced_seg_ratio
            ])
        except:
            feats.extend([0, 0, 0, 0])
        
        return np.array(feats[:21], dtype=np.float32)
        
    except Exception as e:
        return None

# Load the 555 dataset
print("\nLoading 555 dataset...")
data_555 = np.load(DATA_555, allow_pickle=True)
embeddings = data_555['embeddings']
labels = data_555['labels']
uids = data_555['uids']

print(f"Total samples: {len(uids)}")
print(f"Embeddings shape: {embeddings.shape}")
print(f"Labels shape: {labels.shape}")

# Build video_id -> audio file mapping
print("\nBuilding audio file map...")
audio_files = {}
for ext in ['*.wav', '*.m4a', '*.mp3']:
    for f in AUDIO_DIR.rglob(ext):
        vid = f.stem
        audio_files[vid] = str(f)

print(f"Found {len(audio_files)} audio files")

# Extract prosody for each sample
print("\nExtracting prosody features...")
prosody_features = []
missing_count = 0
error_count = 0

start_time = time.time()

for i, uid in enumerate(tqdm(uids, desc="Extracting prosody")):
    if i % 5000 == 0:
        elapsed = time.time() - start_time
        rate = (i + 1) / elapsed if elapsed > 0 else 0
        eta = (len(uids) - i) / rate / 60 if rate > 0 else 0
        print(f"\n  Progress: {i}/{len(uids)}, ETA: {eta:.1f} min")
    
    # Parse UID: video_id_starttime
    parts = uid.rsplit('_', 1)
    if len(parts) != 2:
        prosody_features.append(np.zeros(21, dtype=np.float32))
        error_count += 1
        continue
    
    video_id = parts[0]
    start_time_utt = float(parts[1])
    
    # Find audio file
    if video_id not in audio_files:
        prosody_features.append(np.zeros(21, dtype=np.float32))
        missing_count += 1
        continue
    
    audio_path = audio_files[video_id]
    
    # Estimate end time (next utterance starts ~2-3s later typically)
    # We'll use a fixed window of 3 seconds
    end_time = start_time_utt + 3.0
    
    # Extract prosody
    prosody = extract_prosody(audio_path, start_time_utt, end_time)
    
    if prosody is None:
        prosody_features.append(np.zeros(21, dtype=np.float32))
        error_count += 1
    else:
        prosody_features.append(prosody)

elapsed = time.time() - start_time
print(f"\nExtraction complete in {elapsed/60:.1f} min")
print(f"Missing audio: {missing_count}")
print(f"Errors: {error_count}")

# Convert to array
prosody_array = np.array(prosody_features, dtype=np.float32)
print(f"Prosody shape: {prosody_array.shape}")

# Save combined dataset
print("\nSaving combined dataset...")
combined = {
    'embeddings': embeddings,
    'prosody': prosody_array,
    'labels': labels,
    'uids': uids
}
np.savez_compressed(OUTPUT_FILE, **combined)
print(f"Saved to: {OUTPUT_FILE}")

# Summary statistics
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"Total samples: {len(uids)}")
print(f"Positive labels: {np.sum(labels == 1)} ({np.sum(labels == 1)/len(labels)*100:.2f}%)")
print(f"Prosody dimensions: {prosody_array.shape[1]}")
print(f"WavLM dimensions: {embeddings.shape[1]}")
print(f"Combined features: {prosody_array.shape[1] + embeddings.shape[1]}")

# Validate some samples
print("\nSample prosody (first 5):")
for i in range(5):
    print(f"  {uids[i]}: label={labels[i]}, prosody_mean={prosody_array[i].mean():.4f}")

print("\n✅ Prosody extraction complete!")