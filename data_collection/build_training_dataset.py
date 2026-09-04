#!/usr/bin/env python3
"""
Build training dataset from fully processed videos.
Uses aligned utterances (verified labels) + audio-based laughter detection for all others.
"""
import json
import os
import numpy as np
from pathlib import Path
import librosa
import warnings
warnings.filterwarnings('ignore')

# Paths
MANIFEST = "/Users/Subho/autonomous_laughter_prediction/kaggle_extraction/video_manifest.json"
ALIGNED_PATH = "/Users/Subho/data/chuckle-net/aligned_utterances.jsonl"
AUDIO_DIRS = [
    "/Users/Subho/data/chuckle-net/audio_final",
    "/Users/Subho/data/chuckle-net/audio",
    "/Users/Subho/data/chuckle-net/audio_new",
    "/Users/Subho/data/chuckle-net/audio_all"
]
WAVLM_DIR = Path("/Users/Subho/data/chuckle-net/wavlm_embeddings")
OUTPUT_PATH = "/Users/Subho/data/chuckle-net/training_data.jsonl"

# Audio laughter detector parameters
RMS_THRESHOLD = 0.02
ZCR_THRESHOLD = 0.15
SPECTRAL_FLUX_THRESHOLD = 0.05

def extract_audio_features(y, sr):
    """Extract multi-feature vector for laughter detection."""
    features = {}
    
    # RMS Energy
    rms = librosa.feature.rms(y=y)[0]
    features['rms_mean'] = np.mean(rms)
    features['rms_std'] = np.std(rms)
    features['rms_max'] = np.max(rms)
    
    # Zero Crossing Rate
    zcr = librosa.feature.zero_crossing_rate(y)[0]
    features['zcr_mean'] = np.mean(zcr)
    features['zcr_std'] = np.std(zcr)
    
    # Spectral Flux
    spectral_flux = librosa.feature.spectral_flux(y=y)[0]
    features['sf_mean'] = np.mean(spectral_flux)
    features['sf_std'] = np.std(spectral_flux)
    
    # Spectral Centroid
    sc = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    features['sc_mean'] = np.mean(sc)
    features['sc_std'] = np.std(sc)
    
    return features

def detect_laughter_audio(audio_path, start, end):
    """Detect laughter in audio segment using multi-feature approach."""
    try:
        y, sr = librosa.load(audio_path, sr=16000, offset=start, duration=end-start)
        
        if len(y) < 400:
            return 0
        
        features = extract_audio_features(y, sr)
        
        # Multi-feature laughter detection
        score = 0
        
        if features['rms_mean'] > RMS_THRESHOLD:
            score += 1
        if features['rms_max'] > features['rms_mean'] * 2:
            score += 1
        if features['zcr_mean'] > ZCR_THRESHOLD:
            score += 1
        if features['zcr_std'] > features['zcr_mean'] * 0.5:
            score += 1
        if features['sf_mean'] > SPECTRAL_FLUX_THRESHOLD:
            score += 1
        if 1000 < features['sc_mean'] < 3000:
            score += 1
        
        return 1 if score >= 3 else 0
    except:
        return 0

def find_audio(vid):
    """Find audio file for video ID."""
    for d in AUDIO_DIRS:
        for ext in ['.wav', '.mp3', '.m4a']:
            p = Path(d) / f"{vid}{ext}"
            if p.exists():
                return str(p)
    return None

print("=" * 55)
print("📊 BUILDING TRAINING DATASET")
print("=" * 55)

# Load manifest
manifest = json.load(open(MANIFEST))

# Find fully processed videos
all_audio_vids = set()
for d_str in AUDIO_DIRS:
    d = Path(d_str)
    if d.exists():
        for f in d.iterdir():
            all_audio_vids.add(f.stem)

wavlm_vids = {f.stem for f in WAVLM_DIR.glob("*.json") if f.stem}
manifest_vids = {v['video_id'] for v in manifest}
fully_processed = manifest_vids & all_audio_vids & wavlm_vids

print(f"Fully processed videos: {len(fully_processed)}")

# Step 1: Load aligned utterances (verified labels)
print("\n1. Loading aligned utterances (verified labels)...")
aligned_data = []
aligned_vids = set()
with open(ALIGNED_PATH) as f:
    for line in f:
        d = json.loads(line)
        vid = d['video_id']
        if vid in fully_processed:
            d['detection_method'] = 'aligned'
            aligned_data.append(d)
            aligned_vids.add(vid)

print(f"   From aligned: {len(aligned_data)} utterances ({len(aligned_vids)} videos)")
aligned_pos = sum(1 for d in aligned_data if d.get('label_any', 0) == 1)
print(f"   Positive: {aligned_pos} ({aligned_pos/len(aligned_data)*100:.1f}%)")

# Step 2: For remaining processed videos, use audio-based detection
remaining_vids = fully_processed - aligned_vids
print(f"\n2. Processing remaining {len(remaining_vids)} videos with audio detection...")

# Load all_utterances for remaining videos
remaining_utts = []
with open("/Users/Subho/autonomous_laughter_prediction/data/utterances/all_utterances.jsonl") as f:
    for line in f:
        d = json.loads(line)
        vid = d.get('video_id', '').split('.')[0]
        if vid in remaining_vids:
            remaining_utts.append(d)

print(f"   Utterances from remaining: {len(remaining_utts)}")

# Apply audio-based laughter detection
detected_pos = 0
detected_neg = 0
processed = 0

for u in remaining_utts:
    vid = u.get('video_id', '').split('.')[0]
    start = u.get('start', 0)
    end = u.get('end', start + 3)
    
    audio_path = find_audio(vid)
    if audio_path:
        label = detect_laughter_audio(audio_path, start, end)
        u['label'] = label
        u['laughter'] = label
        u['detection_method'] = 'audio'
        if label == 1:
            detected_pos += 1
        else:
            detected_neg += 1
    else:
        u['label'] = 0
        u['laughter'] = 0
        u['detection_method'] = 'no_audio'
        detected_neg += 1
    
    processed += 1
    if processed % 10000 == 0:
        print(f"   Processed {processed}/{len(remaining_utts)}...")

print(f"   Detected positive: {detected_pos} ({detected_pos/len(remaining_utts)*100:.1f}%)")

# Step 3: Combine all data
print("\n3. Combining datasets...")

# Add aligned data
for d in aligned_data:
    d['detection_method'] = 'aligned'

combined = aligned_data + remaining_utts

# Balance - keep 15% positive rate (natural rate from audio detection)
positives = [u for u in combined if u.get('label', 0) == 1]
negatives = [u for u in combined if u.get('label', 0) == 0]

print(f"   Total: {len(combined)}")
print(f"   Positive: {len(positives)} ({len(positives)/len(combined)*100:.1f}%)")
print(f"   Negative: {len(negatives)}")

# Balance to ~15% positive rate
target_pos_rate = 0.15
current_rate = len(positives) / len(combined)
print(f"\n   Current positive rate: {current_rate*100:.1f}%")
print(f"   Target positive rate: {target_pos_rate*100:.1f}%")

if current_rate > target_pos_rate:
    # Too many positives - downsample
    target_pos = int(len(combined) * target_pos_rate)
    np.random.seed(42)
    selected_pos = list(np.random.choice(len(positives), target_pos, replace=False))
    positives = [positives[i] for i in selected_pos]
    print(f"   Downsampled positives to: {len(positives)}")
elif current_rate < target_pos_rate / 2:
    # Too few positives - keep all but cap negatives
    target_neg = int(len(positives) * (1 - target_pos_rate) / target_pos_rate)
    if len(negatives) > target_neg:
        np.random.seed(42)
        selected_neg = list(np.random.choice(len(negatives), target_neg, replace=False))
        negatives = [negatives[i] for i in selected_neg]
        print(f"   Downsampled negatives to: {len(negatives)}")

final_data = positives + negatives
np.random.shuffle(final_data)

print(f"\n   Final dataset: {len(final_data)} utterances")
print(f"   Positive: {len(positives)} ({len(positives)/len(final_data)*100:.1f}%)")
print(f"   Negative: {len(negatives)}")

# Save
print(f"\n4. Saving to {OUTPUT_PATH}...")
with open(OUTPUT_PATH, 'w') as f:
    for u in final_data:
        f.write(json.dumps(u) + '\n')

# Stats
videos_used = set(u.get('video_id', '') for u in final_data)
print(f"\n✅ DONE!")
print(f"   Dataset: {OUTPUT_PATH}")
print(f"   Total utterances: {len(final_data)}")
print(f"   Videos: {len(videos_used)}")
print(f"   Positive rate: {len(positives)/len(final_data)*100:.1f}%")
print("=" * 55)