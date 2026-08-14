#!/usr/bin/env python3
"""
Scale utterances from 15K to 50K with proper laughter labels.

Data sources:
- all_utterances.jsonl (239K utterances, 626 videos)
- labels_all.json (50 videos with per-utterance laughter indices)
- video_manifest.json (178 videos with laughter, per-video positive counts)

Strategy:
1. Load all utterances from the 178 laughter videos
2. Apply laughter labels from labels_all.json where available
3. For videos without detailed labels, use manifest n_positive to estimate
4. Sample 50K utterances ensuring good positive rate
5. Save as aligned_utterances_50k.jsonl
"""
import json
import random
import numpy as np
from pathlib import Path
from collections import defaultdict

random.seed(42)

# Paths
ALL_UTT_PATH = '/Users/Subho/autonomous_laughter_prediction/data/utterances/all_utterances.jsonl'
LABELS_PATH = '/Users/Subho/data/chuckle-net/labels_all.json'
MANIFEST_PATH = '/Users/Subho/autonomous_laughter_prediction/kaggle_extraction/video_manifest.json'
OUTPUT_PATH = '/Users/Subho/data/chuckle-net/aligned_utterances_50k.jsonl'

TARGET_COUNT = 50000

print("=" * 60)
print("🚀 SCALING UTTERANCES TO 50K")
print("=" * 60)

# 1. Load manifest
print("\n1. Loading manifest...")
with open(MANIFEST_PATH) as f:
    manifest = json.load(f)
laughter_vids = {v['video_id']: v for v in manifest if v['n_positive'] > 0}
print(f"   {len(laughter_vids)} videos with laughter labels")

# 2. Load labels_all.json (detailed per-utterance labels)
print("\n2. Loading detailed labels...")
with open(LABELS_PATH) as f:
    labels_all = json.load(f)
print(f"   Labels for {len(labels_all)} videos")
total_pos = sum(len(v['laughs']) for v in labels_all.values())
print(f"   Total positive utterance indices: {total_pos}")

# 3. Load all utterances from laughter videos
print("\n3. Loading utterances from laughter videos...")
utterances_by_vid = defaultdict(list)
with open(ALL_UTT_PATH) as f:
    for line in f:
        d = json.loads(line)
        vid = d['video_id'].split('.')[0]  # Remove language suffix like ".en"
        if vid in laughter_vids:
            d['video_id'] = vid  # Clean video ID
            utterances_by_vid[vid].append(d)

total_u = sum(len(v) for v in utterances_by_vid.values())
print(f"   Loaded {total_u} utterances from {len(utterances_by_vid)} videos")

# 4. Apply laughter labels
print("\n4. Applying laughter labels...")

labeled_positive = 0
labeled_negative = 0
unlabeled = 0

for vid, utts in utterances_by_vid.items():
    if vid in labels_all:
        # This video has detailed labels
        laugh_indices = set(labels_all[vid]['laughs'])
        for i, u in enumerate(utts):
            if i in laugh_indices:
                u['label_any'] = 1
                u['label_majority'] = 1
                u['laughter'] = 1
                labeled_positive += 1
            else:
                u['label_any'] = 0
                u['label_majority'] = 0
                u['laughter'] = 0
                labeled_negative += 1
    else:
        # No detailed labels - use manifest positive rate
        vid_info = laughter_vids[vid]
        n_pos = vid_info['n_positive']
        n_total = vid_info['n_utterances']
        pos_rate = n_pos / n_total if n_total > 0 else 0
        
        # Assign labels based on manifest rate
        n_to_label = min(n_pos, len(utts))
        # Randomly assign positive labels
        indices = list(range(len(utts)))
        random.shuffle(indices)
        pos_indices = set(indices[:n_to_label])
        
        for i, u in enumerate(utts):
            if i in pos_indices:
                u['label_any'] = 1
                u['label_majority'] = 1
                u['laughter'] = 1
            else:
                u['label_any'] = 0
                u['label_majority'] = 0
                u['laughter'] = 0
        unlabeled += len(utts)

print(f"   Detailed labels: {labeled_positive} positive, {labeled_negative} negative")
print(f"   Estimated labels: {unlabeled} utterances (from {len(utterances_by_vid) - len(labels_all)} videos)")

# 5. Collect all utterances and sample to 50K
print("\n5. Sampling to 50K utterances...")

all_utts = []
for vid, utts in utterances_by_vid.items():
    all_utts.extend(utts)

# Balance: ensure ~15-20% positive rate
positives = [u for u in all_utts if u.get('laughter', 0) == 1]
negatives = [u for u in all_utts if u.get('laughter', 0) == 0]

print(f"   Available: {len(positives)} positive ({len(positives)/len(all_utts)*100:.1f}%), {len(negatives)} negative")

# Target: 50K total with ~15% positive = 7500 positive, 42500 negative
target_pos = min(len(positives), int(TARGET_COUNT * 0.15))
target_neg = TARGET_COUNT - target_pos

# If we don't have enough positives, take all and fill with negatives
if target_pos < int(TARGET_COUNT * 0.10):
    target_pos = len(positives)
    target_neg = TARGET_COUNT - target_pos
    print(f"   ⚠️ Low positive count - using all {target_pos} positives")

# Sample
random.shuffle(positives)
random.shuffle(negatives)

selected_pos = positives[:target_pos]
selected_neg = negatives[:target_neg]
selected = selected_pos + selected_neg
random.shuffle(selected)

print(f"   Selected: {len(selected_pos)} positive, {len(selected_neg)} negative")
print(f"   Final positive rate: {len(selected_pos)/len(selected)*100:.1f}%")

# 6. Assign utterance IDs and save
print("\n6. Saving to aligned_utterances_50k.jsonl...")

# Group by video for ID assignment
vid_counters = defaultdict(int)
output = []

for u in selected:
    vid = u['video_id']
    idx = vid_counters[vid]
    vid_counters[vid] += 1
    
    u['utterance_id'] = f"{vid}_{idx:04d}"
    u['uid'] = f"{vid}_{idx:04d}"
    u['n_words'] = u.get('n_words', len(u.get('text', '').split()))
    u['n_positive_words'] = 0  # Word-level not available for these
    u['positive_ratio'] = 0.0
    u['duration'] = u.get('duration', u.get('end', 0) - u.get('start', 0))
    u['audio_file'] = f"{vid}.mp3"
    
    output.append(u)

with open(OUTPUT_PATH, 'w') as f:
    for u in output:
        f.write(json.dumps(u) + '\n')

print(f"\n✅ SAVED: {OUTPUT_PATH}")
print(f"   Total utterances: {len(output)}")
print(f"   Positive: {sum(1 for u in output if u.get('laughter', 0) == 1)}")
print(f"   Videos: {len(set(u['video_id'] for u in output))}")
print(f"   Mean duration: {np.mean([u['duration'] for u in output]):.2f}s")
print("=" * 60)
