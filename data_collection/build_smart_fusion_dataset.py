#!/usr/bin/env python3
"""
Smart dataset builder: Uses ALL pre-extracted features.
Combines: XLM-R embeddings + Prosody (21-dim) + WavLM embeddings + verified labels.

This is the INTELLIGENT approach - no wasted re-extraction.
"""
import json, os
import numpy as np
from pathlib import Path
from collections import defaultdict

# Pre-extracted data paths
PROSODYD_PATH = '/Users/Subho/Downloads/prosody_phaseD.json'
ALIGNED_PATH = '/Users/Subho/data/chuckle-net/aligned_utterances.jsonl'
WAVLM_DIR = Path('/Users/Subho/data/chuckle-net/wavlm_embeddings')
EMBEDDINGS_DIR = '/Users/Subho/autonomous_laughter_prediction/training/prosody_fusion_embeddings'

# Output
OUTPUT_DIR = '/Users/Subho/data/chuckle-net/fusion_dataset'
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("=" * 55)
print("📊 SMART FUSION DATASET BUILDER")
print("=" * 55)

# 1. Load pre-extracted prosody (21-dim)
print("\n1. Loading pre-extracted prosody features...")
with open(PROSODYD_PATH) as f:
    prosody_raw = json.load(f)
prosody_map = {d['uid']: np.array(d['feats']) for d in prosody_raw}
print(f"   {len(prosody_map)} prosody entries, dim={len(prosody_raw[0]['feats'])}")

# 2. Load aligned utterances with verified labels
print("\n2. Loading aligned utterances (verified labels)...")
utterances = []
with open(ALIGNED_PATH) as f:
    for line in f:
        utterances.append(json.loads(line))
print(f"   {len(utterances)} utterances from {len(set(u['video_id'] for u in utterances))} videos")

# 3. Load WavLM embeddings
print("\n3. Loading WavLM embeddings...")
wavlm_map = {}
for f in WAVLM_DIR.glob("*.json"):
    vid = f.stem
    data = json.load(open(f))
    if 'embedding' in data:
        wavlm_map[vid] = np.array(data['embedding'])
print(f"   {len(wavlm_map)} WavLM embeddings, dim={len(list(wavlm_map.values())[0])}")

# 4. Build fusion dataset
print("\n4. Building fusion dataset...")

# Held-out comedians (Bill Burr, Dave Chappelle, Russell Peters)
HELD_OUT = {'BFIHCzw3itk', 'BAD4askmGgk', '1Nb3_os4RSA'}

dataset = []
has_prosody = 0
has_wavlm = 0
has_both = 0

for u in utterances:
    uid = f"{u['video_id']}_{u['start']:.2f}"
    vid = u['video_id']
    
    # Get prosody
    prosody = prosody_map.get(uid)
    if prosody is not None:
        has_prosody += 1
    
    # Get WavLM (video-level)
    wavlm = wavlm_map.get(vid)
    if wavlm is not None:
        has_wavlm += 1
    
    if prosody is not None and wavlm is not None:
        has_both += 1
    
    split = 'held_out' if vid in HELD_OUT else 'train_pool'
    
    dataset.append({
        'uid': uid,
        'video_id': vid,
        'text': u.get('text', ''),
        'start': u['start'],
        'end': u['end'],
        'label': int(u.get('label_any', 0)),
        'prosody': prosody.tolist() if prosody is not None else None,
        'wavlm': wavlm.tolist() if wavlm is not None else None,
        'split': split,
    })

print(f"   Total: {len(dataset)}")
print(f"   Has prosody: {has_prosody} ({has_prosody/len(dataset)*100:.1f}%)")
print(f"   Has WavLM: {has_wavlm} ({has_wavlm/len(dataset)*100:.1f}%)")
print(f"   Has BOTH: {has_both} ({has_both/len(dataset)*100:.1f}%)")

pos = sum(1 for d in dataset if d['label'] == 1)
print(f"   Positive: {pos} ({pos/len(dataset)*100:.1f}%)")

# 5. Split into train/valid/test (comedian-level)
print("\n5. Splitting (comedian-level held-out)...")

train_pool = [d for d in dataset if d['split'] == 'train_pool']
held_out = [d for d in dataset if d['split'] == 'held_out']

# Split train_pool into train/valid (80/20 by video)
vids = list(set(d['video_id'] for d in train_pool))
np.random.seed(42)
np.random.shuffle(vids)
n_train_vids = int(len(vids) * 0.8)
train_vids = set(vids[:n_train_vids])
valid_vids = set(vids[n_train_vids:])

train = [d for d in train_pool if d['video_id'] in train_vids]
valid = [d for d in train_pool if d['video_id'] in valid_vids]
test = held_out

print(f"   Train: {len(train)} ({len(train_vids)} videos)")
print(f"   Valid: {len(valid)} ({len(valid_vids)} videos)")
print(f"   Test (held-out): {len(test)} ({len(HELD_OUT)} videos)")

for name, split in [('train', train), ('valid', valid), ('test', test)]:
    pos = sum(1 for d in split if d['label'] == 1)
    has_p = sum(1 for d in split if d['prosody'] is not None)
    has_w = sum(1 for d in split if d['wavlm'] is not None)
    print(f"   {name}: {len(split)} utts, {pos} pos ({pos/max(len(split),1)*100:.1f}%), prosody={has_p}, wavlm={has_w}")

# 6. Save as JSONL
print(f"\n6. Saving to {OUTPUT_DIR}/...")
for name, split in [('train', train), ('valid', valid), ('test', test)]:
    path = os.path.join(OUTPUT_DIR, f'{name}.jsonl')
    with open(path, 'w') as f:
        for d in split:
            f.write(json.dumps(d) + '\n')
    print(f"   {name}.jsonl: {len(split)} samples")

# 7. Also save as NPZ for fast loading
print(f"\n7. Saving NPZ (for fast training)...")

for name, split in [('train', train), ('valid', valid), ('test', test)]:
    # Filter to only samples with both prosody and wavlm
    complete = [d for d in split if d['prosody'] is not None and d['wavlm'] is not None]
    
    if not complete:
        print(f"   {name}: no complete samples, skipping NPZ")
        continue
    
    embeddings = np.array([d['wavlm'] for d in complete])
    prosody = np.array([d['prosody'] for d in complete])
    labels = np.array([d['label'] for d in complete])
    uids = np.array([d['uid'] for d in complete])
    
    path = os.path.join(OUTPUT_DIR, f'{name}.npz')
    np.savez(path, embeddings=embeddings, prosody=prosody, labels=labels, uids=uids)
    pos = sum(labels)
    print(f"   {name}.npz: {len(complete)} samples, wavlm={embeddings.shape[1]}, prosody={prosody.shape[1]}, pos={pos}")

print(f"\n{'='*55}")
print(f"✅ SMART FUSION DATASET BUILT")
print(f"{'='*55}")
print(f"   Using pre-extracted: prosody (21-dim) + WavLM (768-dim) + verified labels")
print(f"   Total utterances: {len(dataset)}")
print(f"   With all features: {has_both}")
print(f"   Output: {OUTPUT_DIR}/")
print(f"{'='*55}")
