#!/usr/bin/env python3
"""
Fast training dataset builder.
Strategy: Load each video's audio ONCE, detect laughter across all utterances.
"""
import json, os, sys
import numpy as np
from pathlib import Path
import librosa
import warnings
warnings.filterwarnings('ignore')

MANIFEST = "/Users/Subho/autonomous_laughter_prediction/kaggle_extraction/video_manifest.json"
ALIGNED_PATH = "/Users/Subho/data/chuckle-net/aligned_utterances.jsonl"
ALL_UTT_PATH = "/Users/Subho/autonomous_laughter_prediction/data/utterances/all_utterances.jsonl"
AUDIO_DIRS = [
    "/Users/Subho/data/chuckle-net/audio_final",
    "/Users/Subho/data/chuckle-net/audio",
    "/Users/Subho/data/chuckle-net/audio_new",
    "/Users/Subho/data/chuckle-net/audio_all"
]
WAVLM_DIR = Path("/Users/Subho/data/chuckle-net/wavlm_embeddings")
OUTPUT_PATH = "/Users/Subho/data/chuckle-net/training_data.jsonl"

def find_audio(vid):
    for d in AUDIO_DIRS:
        for ext in ['.wav', '.mp3', '.m4a']:
            p = Path(d) / f"{vid}{ext}"
            if p.exists():
                return str(p)
    return None

print("=" * 55)
print("📊 FAST TRAINING DATASET BUILDER")
print("=" * 55)

# Load manifest
manifest = json.load(open(MANIFEST))
manifest_lookup = {v['video_id']: v for v in manifest}

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

# Step 1: Load aligned utterances (verified VTT labels)
print("\n1. Loading aligned utterances (verified labels)...")
aligned = []
aligned_vids = set()
with open(ALIGNED_PATH) as f:
    for line in f:
        d = json.loads(line)
        if d['video_id'] in fully_processed:
            d['label'] = d.get('label_any', 0)
            d['laughter'] = d['label']
            d['source'] = 'aligned'
            aligned.append(d)
            aligned_vids.add(d['video_id'])

print(f"   {len(aligned)} utterances from {len(aligned_vids)} videos")
print(f"   Positive: {sum(1 for d in aligned if d['label']==1)}")

# Step 2: Load all utterances grouped by video
print("\n2. Loading utterances from remaining videos...")
utts_by_vid = {}
with open(ALL_UTT_PATH) as f:
    for line in f:
        d = json.loads(line)
        vid = d.get('video_id', '').split('.')[0]
        if vid in fully_processed and vid not in aligned_vids:
            utts_by_vid.setdefault(vid, []).append(d)

remaining_vids = list(utts_by_vid.keys())
total_remaining = sum(len(v) for v in utts_by_vid.values())
print(f"   {total_remaining} utterances from {len(remaining_vids)} videos")

# Step 3: For each video, load audio ONCE and detect laughter for all utterances
print(f"\n3. Audio-based laughter detection (per-video)...")
detected = []
detected_pos = 0
videos_done = 0

for vid in remaining_vids:
    utts = utts_by_vid[vid]
    audio_path = find_audio(vid)
    
    if not audio_path:
        # No audio - label using manifest positive rate
        vinfo = manifest_lookup.get(vid, {})
        n_pos = vinfo.get('n_positive', 0)
        n_total = vinfo.get('n_utterances', len(utts))
        indices = set(np.random.choice(len(utts), min(n_pos, len(utts)), replace=False).tolist())
        for i, u in enumerate(utts):
            u['label'] = 1 if i in indices else 0
            u['laughter'] = u['label']
            u['source'] = 'manifest'
            detected.append(u)
            if u['label'] == 1:
                detected_pos += 1
    else:
        # Load audio ONCE for this video
        try:
            y, sr = librosa.load(audio_path, sr=16000)
            total_samples = len(y)
            
            for u in utts:
                start = u.get('start', 0)
                end = u.get('end', start + 3)
                start_sample = int(start * sr)
                end_sample = int(end * sr)
                
                # Extract segment
                if end_sample > total_samples:
                    end_sample = total_samples
                if start_sample >= total_samples or start_sample >= end_sample:
                    u['label'] = 0
                    u['laughter'] = 0
                    u['source'] = 'audio'
                    detected.append(u)
                    continue
                
                segment = y[start_sample:end_sample]
                
                if len(segment) < 400:
                    u['label'] = 0
                    u['laughter'] = 0
                    u['source'] = 'audio'
                    detected.append(u)
                    continue
                
                # Fast multi-feature detection
                rms = np.sqrt(np.mean(segment**2))
                zcr = np.mean(np.abs(np.diff(np.sign(segment))) > 0)
                
                # Spectral features (compute once for segment)
                spec = np.abs(np.fft.rfft(segment))
                centroid = np.sum(np.arange(len(spec)) * spec) / (np.sum(spec) + 1e-10) * sr / len(segment) / 2
                
                # Laughter scoring
                score = 0
                if rms > 0.02: score += 1
                if zcr > 0.15: score += 1
                if 500 < centroid < 4000: score += 1
                
                label = 1 if score >= 2 else 0
                u['label'] = label
                u['laughter'] = label
                u['source'] = 'audio'
                detected.append(u)
                if label == 1:
                    detected_pos += 1
        except Exception as e:
            # Fallback to manifest labeling
            vinfo = manifest_lookup.get(vid, {})
            n_pos = vinfo.get('n_positive', 0)
            indices = set(np.random.choice(len(utts), min(n_pos, len(utts)), replace=False).tolist())
            for i, u in enumerate(utts):
                u['label'] = 1 if i in indices else 0
                u['laughter'] = u['label']
                u['source'] = 'manifest_fallback'
                detected.append(u)
                if u['label'] == 1:
                    detected_pos += 1
    
    videos_done += 1
    if videos_done % 50 == 0:
        print(f"   {videos_done}/{len(remaining_vids)} videos, {len(detected)} utts, {detected_pos} pos")

print(f"   Done: {len(detected)} utterances, {detected_pos} positive ({detected_pos/max(len(detected),1)*100:.1f}%)")

# Step 4: Combine
print("\n4. Combining datasets...")
combined = aligned + detected

positives = [u for u in combined if u.get('label', 0) == 1]
negatives = [u for u in combined if u.get('label', 0) == 0]

print(f"   Total: {len(combined)}")
print(f"   Positive: {len(positives)} ({len(positives)/len(combined)*100:.1f}%)")
print(f"   Negative: {len(negatives)}")

# Balance to ~15% positive
if len(positives) / len(combined) > 0.20:
    target_pos = int(len(combined) * 0.15)
    np.random.seed(42)
    keep = set(np.random.choice(len(positives), target_pos, replace=False).tolist())
    positives = [positives[i] for i in keep]
    print(f"   Downsampled positives to {len(positives)}")

final_data = positives + negatives
np.random.seed(42)
np.random.shuffle(final_data)

# Save
print(f"\n5. Saving to {OUTPUT_PATH}...")
with open(OUTPUT_PATH, 'w') as f:
    for u in final_data:
        f.write(json.dumps(u) + '\n')

videos_used = set(u.get('video_id', '') for u in final_data)
print(f"\n{'='*55}")
print(f"✅ TRAINING DATASET BUILT")
print(f"{'='*55}")
print(f"   Total utterances: {len(final_data)}")
print(f"   Positive: {len(positives)} ({len(positives)/len(final_data)*100:.1f}%)")
print(f"   Videos: {len(videos_used)}")
print(f"   Sources: aligned={sum(1 for u in final_data if u.get('source')=='aligned')}, audio={sum(1 for u in final_data if u.get('source')=='audio')}, manifest={sum(1 for u in final_data if u.get('source','').startswith('manifest'))}")
print(f"{'='*55}")
