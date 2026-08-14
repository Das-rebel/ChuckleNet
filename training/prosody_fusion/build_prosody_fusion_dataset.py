#!/usr/bin/env python3
"""
Build prosody-fusion dataset from aligned_utterances + prosody cache.
Late fusion: XLM-R [CLS] embedding + 21-dim prosody → MLP classifier.

Output: train.jsonl, valid.jsonl, test.jsonl in prosody_fusion_data/
Each line: {"uid": video_id_start, "text": ..., "label": 0|1, "prosody": [21 floats]}
"""
import json, os, sys, statistics
from collections import defaultdict
from sklearn.model_selection import train_test_split

# Paths
PROSODY_PATH = '/Users/Subho/Downloads/prosody_phaseD.json'
AU_PATH = '/Users/Subho/autonomous_laughter_prediction_essential/data/audio_comedy/aligned_utterances.jsonl'
OUT_DIR = '/Users/Subho/autonomous_laughter_prediction/training/prosody_fusion_data'
os.makedirs(OUT_DIR, exist_ok=True)

# Held-out comedians (Bill Burr, Dave Chappelle, Russell Peters)
HELD_OUT = {'BFIHCzw3itk', 'BAD4askmGgk', '1Nb3_os4RSA'}

# Load prosody cache
print("Loading prosody cache...")
with open(PROSODY_PATH) as f:
    prosody_raw = json.load(f)
prosody_map = {d['uid']: d['feats'] for d in prosody_raw}
print(f"  {len(prosody_map)} prosody entries, dim={len(prosody_raw[0]['feats'])}")

# Analyze prosody distribution for normalization
all_vals = [v for feats in prosody_map.values() for v in feats]
prosody_min = min(all_vals)
prosody_max = max(all_vals)
print(f"  Prosody range: {prosody_min:.3f} – {prosody_max:.3f}, mean={statistics.mean(all_vals):.3f}")

# Normalize prosody to [0, 1]
def normalize_prosody(feats):
    return [(f - prosody_min) / (prosody_max - prosody_min + 1e-8) for f in feats]

# Load utterances
print("\nLoading utterances...")
utterances = [json.loads(line) for line in open(AU_PATH)]
print(f"  {len(utterances)} total utterances")

# Build dataset: only real examples with matching prosody
print("\nBuilding dataset (real examples only)...")
dataset = []
no_prosody = 0
for u in utterances:
    uid = f"{u['video_id']}_{u['start']:.2f}"
    if uid not in prosody_map:
        no_prosody += 1
        continue
    
    # Get normalized prosody
    prosody = normalize_prosody(prosody_map[uid])
    
    dataset.append({
        'uid': uid,
        'video_id': u['video_id'],
        'start': u['start'],
        'text': u['text'],
        'label': int(u['label_any']),  # 0 or 1
        'prosody': prosody,  # 21 normalized features
        'comedian_id': u.get('comedian_id', 'unknown'),
    })

print(f"  {len(dataset)} examples with prosody match")
print(f"  {no_prosody} missing prosody (skipped)")
pos = sum(1 for d in dataset if d['label'] == 1)
print(f"  Positive: {pos}/{len(dataset)} ({100*pos/len(dataset):.1f}%)")

# Split by video
print("\nSplitting by video...")
video_examples = defaultdict(list)
for d in dataset:
    video_examples[d['video_id']].append(d)

train_videos, temp_videos = [], []
for vid, examples in video_examples.items():
    if vid in HELD_OUT:
        continue  # held-out → test only
    train_videos.append(vid)

# 85/15 train/val split on non-held-out videos
train_vids, val_vids = train_test_split(train_videos, test_size=0.15, random_state=42)
test_vids = list(HELD_OUT & video_examples.keys())

print(f"  Train videos: {len(train_vids)}, Val videos: {len(val_vids)}, Test videos: {len(test_vids)}")

train_data = [ex for vid in train_vids for ex in video_examples[vid]]
val_data = [ex for vid in val_vids for ex in video_examples[vid]]
test_data = [ex for vid in test_vids for ex in video_examples[vid]]

print(f"  Train: {len(train_data)} ({sum(d['label'] for d in train_data)} positive)")
print(f"  Val:   {len(val_data)} ({sum(d['label'] for d in val_data)} positive)")
print(f"  Test:  {len(test_data)} ({sum(d['label'] for d in test_data)} positive)")

# Write output
for split_name, data in [('train', train_data), ('valid', val_data), ('test', test_data)]:
    out_path = os.path.join(OUT_DIR, f'{split_name}.jsonl')
    with open(out_path, 'w') as f:
        for ex in data:
            # Remove video_id/start from output (uid is sufficient)
            row = {k: v for k, v in ex.items() if k not in ('video_id', 'start', 'comedian_id')}
            f.write(json.dumps(row) + '\n')
    print(f"  Wrote {out_path}: {len(data)} examples")

print(f"\nDataset ready at: {OUT_DIR}/")
print(f"  Prosody dim: 21 (normalized to [0,1])")
print(f"  Split: {len(train_data)} train / {len(val_data)} val / {len(test_data)} test")
print(f"  Held-out comedians: {sorted(HELD_OUT & video_examples.keys())}")
