#!/usr/bin/env python3
"""
Expand training dataset from 15K to 60K+ using labels_all.json.
Maps laugh indices to utterances for 43 additional videos.
"""
import json
import numpy as np
from pathlib import Path
from collections import defaultdict

# Paths
LABELS_ALL_PATH = '/Users/Subho/data/chuckle-net/labels_all.json'
ALIGNED_PATH = '/Users/Subho/data/chuckle-net/aligned_utterances.jsonl'
ALL_UTT_PATH = '/Users/Subho/autonomous_laughter_prediction/data/utterances/all_utterances.jsonl'
WAVLM_DIR = Path('/Users/Subho/data/chuckle-net/wavlm_embeddings')
OUTPUT_PATH = '/Users/Subho/data/chuckle-net/expanded_dataset.jsonl'

print("=" * 55)
print("🚀 EXPANDING DATASET FROM 15K → 60K+")
print("=" * 55)

# 1. Load existing aligned (15K with verified labels)
print("\n1. Loading aligned_utterances (verified)...")
aligned = []
aligned_vids = set()
with open(ALIGNED_PATH) as f:
    for line in f:
        d = json.loads(line)
        aligned.append(d)
        aligned_vids.add(d['video_id'])
print(f"   {len(aligned)} from {len(aligned_vids)} videos")

# 2. Load labels_all.json
print("\n2. Loading labels_all.json...")
labels_all = json.load(open(LABELS_ALL_PATH))
print(f"   {len(labels_all)} videos with laugh markers")

# 3. Find videos with labels but not in aligned
extra_vids = set(labels_all.keys()) - aligned_vids
print(f"   Videos with labels NOT in aligned: {len(extra_vids)}")

# 4. Load all_utterances for these extra videos
print("\n3. Loading utterances for extra videos...")
extra_utts_by_vid = defaultdict(list)
with open(ALL_UTT_PATH) as f:
    for line in f:
        d = json.loads(line)
        vid = d.get('video_id', '').split('.')[0]
        if vid in extra_vids:
            extra_utts_by_vid[vid].append(d)

total_extra = sum(len(v) for v in extra_utts_by_vid.values())
print(f"   {total_extra} utterances from {len(extra_utts_by_vid)} videos")

# 5. Label utterances using laugh indices
print("\n4. Labeling utterances with laugh indices...")
new_labeled = []
total_new_pos = 0

for vid, utts in extra_utts_by_vid.items():
    laugh_indices = set(labels_all[vid].get('laughs', []))
    
    for i, u in enumerate(utts):
        is_laugh = i in laugh_indices
        u['video_id'] = vid  # Clean ID
        u['label_any'] = 1 if is_laugh else 0
        u['label_majority'] = 1 if is_laugh else 0
        u['laughter'] = 1 if is_laugh else 0
        u['source'] = 'labels_all'
        u['uid'] = f"{vid}_{u.get('start', 0):.2f}"
        u['n_words'] = u.get('n_words', len(u.get('text', '').split()))
        u['duration'] = u.get('duration', u.get('end', 0) - u.get('start', 0))
        new_labeled.append(u)
        if is_laugh:
            total_new_pos += 1

print(f"   Labeled: {len(new_labeled)} utterances")
print(f"   Positive: {total_new_pos} ({total_new_pos/len(new_labeled)*100:.1f}%)")

# 6. Also add videos from all_utterances that have has_laughter=True
print("\n5. Adding utterances with has_laughter=True from all videos...")
aligned_and_extra = aligned_vids | extra_vids

has_laugh_utts = []
has_laugh_pos = 0
with open(ALL_UTT_PATH) as f:
    for line in f:
        d = json.loads(line)
        vid = d.get('video_id', '').split('.')[0]
        # Only from processed videos not already covered
        if vid not in aligned_and_extra and d.get('has_laughter') == True:
            d['video_id'] = vid
            d['label_any'] = 1
            d['label_majority'] = 1
            d['laughter'] = 1
            d['source'] = 'has_laughter'
            d['uid'] = f"{vid}_{d.get('start', 0):.2f}"
            has_laugh_utts.append(d)
            has_laugh_pos += 1

# Also add some negatives from these videos (1:5 ratio)
neg_from_has_laugh_vids = defaultdict(list)
has_laugh_vids = set(d['video_id'] for d in has_laugh_utts)
with open(ALL_UTT_PATH) as f:
    for line in f:
        d = json.loads(line)
        vid = d.get('video_id', '').split('.')[0]
        if vid in has_laugh_vids and d.get('has_laughter') != True:
            neg_from_has_laugh_vids[vid].append(d)

# Sample 5x negatives for each positive
import random
random.seed(42)
for vid, negs in neg_from_has_laugh_vids.items():
    n_pos = sum(1 for d in has_laugh_utts if d['video_id'] == vid)
    n_sample = min(len(negs), n_pos * 5)
    sampled = random.sample(negs, n_sample)
    for d in sampled:
        d['video_id'] = vid
        d['label_any'] = 0
        d['label_majority'] = 0
        d['laughter'] = 0
        d['source'] = 'has_laughter_neg'
        d['uid'] = f"{vid}_{d.get('start', 0):.2f}"
        has_laugh_utts.append(d)

print(f"   From has_laughter: {len(has_laugh_utts)} utts ({has_laugh_pos} pos)")

# 7. Combine all
print("\n6. Combining all data sources...")
combined = aligned + new_labeled + has_laugh_utts

# Deduplicate by uid
seen = set()
deduped = []
for d in combined:
    uid = d.get('uid', d.get('utterance_id', ''))
    if uid not in seen:
        seen.add(uid)
        deduped.append(d)

combined = deduped
total_pos = sum(1 for d in combined if d.get('label_any', 0) == 1)
total_vids = len(set(d['video_id'] for d in combined))

print(f"   Combined: {len(combined)} utterances")
print(f"   Positive: {total_pos} ({total_pos/len(combined)*100:.1f}%)")
print(f"   Videos: {total_vids}")

# 8. Check WavLM coverage
wavlm_vids = {f.stem for f in WAVLM_DIR.glob("*.json") if f.stem}
has_wavlm = sum(1 for d in combined if d['video_id'] in wavlm_vids)
print(f"   Has WavLM: {has_wavlm} ({has_wavlm/len(combined)*100:.1f}%)")

# 9. Save
print(f"\n7. Saving to {OUTPUT_PATH}...")
with open(OUTPUT_PATH, 'w') as f:
    for d in combined:
        f.write(json.dumps(d) + '\n')

# Summary by source
sources = defaultdict(int)
for d in combined:
    sources[d.get('source', 'aligned')] += 1

print(f"\n{'='*55}")
print(f"✅ EXPANDED DATASET BUILT")
print(f"{'='*55}")
print(f"   Total: {len(combined)} utterances (was 15K)")
print(f"   Positive: {total_pos} ({total_pos/len(combined)*100:.1f}%)")
print(f"   Videos: {total_vids}")
print(f"   Sources:")
for s, c in sorted(sources.items()):
    print(f"      {s}: {c}")
print(f"{'='*55}")
