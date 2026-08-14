#!/usr/bin/env python3
"""
Create combined dataset by matching on (video_id, start, end).
"""

import json
import os

# ============================================================================
# PATHS
# ============================================================================

YOUTUBE_DIR = '/Users/Subho/data/chuckle-net-youtube/processed'
ORIGINAL_ALIGNED = '/Users/Subho/data/chuckle-net/aligned_utterances.jsonl'
ORIGINAL_PROSODY = '/Users/Subho/data/chuckle-net/prosody_phaseD.json'
OUTPUT_FILE = '/Users/Subho/data/chuckle-net-youtube/combined_dataset.jsonl'

# ============================================================================
# LOAD ORIGINAL PROSODY - INDEX BY (video_id, start)
# ============================================================================

print("Loading original prosody...")
with open(ORIGINAL_PROSODY) as f:
    original_prosody_list = json.load(f)

# Index by (video_id, rounded_start)
original_prosody = {}
for item in original_prosody_list:
    uid = item['uid']
    # uid format: {video_id}_{start:.2f}
    parts = uid.rsplit('_', 1)
    if len(parts) == 2:
        video_id = parts[0]
        try:
            start = float(parts[1])
            key = (video_id, round(start * 100) / 100)  # Round to 2 decimal
            original_prosody[key] = item['feats']
        except:
            pass

print(f"Original prosody: {len(original_prosody)} entries")
print(f"Sample keys: {list(original_prosody.keys())[:3]}")

# ============================================================================
# LOAD ORIGINAL ALIGNED UTTERANCES
# ============================================================================

print("Loading original aligned utterances...")
original_utts = {}
with open(ORIGINAL_ALIGNED) as f:
    for line in f:
        data = json.loads(line)
        uid = data['utterance_id']
        # Match by (video_id, start)
        key = (data['video_id'], round(data['start'] * 100) / 100)
        data['_prosody_key'] = key
        original_utts[key] = data

print(f"Original utterances: {len(original_utts)} entries")

# Match prosody to utterances
matched_prosody = 0
for key, utt in original_utts.items():
    if key in original_prosody:
        utt['_prosody'] = original_prosody[key]
        matched_prosody += 1

print(f"Matched prosody: {matched_prosody}/{len(original_utts)}")

# ============================================================================
# LOAD YOUTUBE PROCESSED DATA
# ============================================================================

print("Loading YouTube processed data...")
youtube_files = [f for f in os.listdir(YOUTUBE_DIR) if f.endswith('.json')]
youtube_utts = {}

for fname in youtube_files:
    with open(os.path.join(YOUTUBE_DIR, fname)) as f:
        data = json.load(f)
    
    video_id = data['video_id']
    prosody = data['prosody']
    
    for utt in data['utterances']:
        uid = utt['utterance_id']
        key = (video_id, round(utt['start'] * 100) / 100)
        utt['_prosody_key'] = key
        utt['_prosody'] = prosody.get(uid)
        youtube_utts[key] = utt

print(f"YouTube utterances: {len(youtube_utts)} entries")

# ============================================================================
# PAD YOUTUBE PROSODY FROM 19 TO 21 DIM
# ============================================================================

def pad_prosody(prosody_19):
    """Pad 19-dim prosody to 21-dim to match original."""
    if prosody_19 is None:
        return None
    if len(prosody_19) == 21:
        return prosody_19
    if len(prosody_19) == 19:
        return prosody_19 + [0.0, 0.0]
    return prosody_19

# ============================================================================
# COMBINE DATASETS
# ============================================================================

print("Combining datasets...")

combined = []
skipped_no_prosody = 0

# Add YouTube utterances
for key, utt in youtube_utts.items():
    prosody = pad_prosody(utt.get('_prosody'))
    if prosody is None:
        skipped_no_prosody += 1
        continue
    
    combined.append({
        'utterance_id': utt['utterance_id'],
        'video_id': utt['video_id'],
        'text': utt['text'],
        'start': utt['start'],
        'end': utt['end'],
        'duration': utt['duration'],
        'n_words': utt['n_words'],
        'label_any': utt['label_any'],
        'label_majority': utt['label_majority'],
        'prosody': prosody,
        'prosody_dim': 21,
        'source': 'youtube',
        'has_wavlm': False,
    })

# Add original utterances
for key, utt in original_utts.items():
    prosody = utt.get('_prosody')
    if prosody is None:
        skipped_no_prosody += 1
        continue
    
    if not utt.get('text', '').strip():
        continue
    
    combined.append({
        'utterance_id': utt['utterance_id'],
        'video_id': utt['video_id'],
        'text': utt['text'],
        'start': utt['start'],
        'end': utt['end'],
        'duration': utt['duration'],
        'n_words': utt['n_words'],
        'label_any': utt['label_any'],
        'label_majority': utt['label_majority'],
        'prosody': prosody,
        'prosody_dim': 21,
        'source': 'original',
        'has_wavlm': True,
    })

print(f"Combined: {len(combined)} utterances")
print(f"Skipped (no prosody): {skipped_no_prosody}")

# ============================================================================
# STATISTICS
# ============================================================================

total = len(combined)
positive = sum(1 for c in combined if c['label_any'] == 1)
youtube_count = sum(1 for c in combined if c['source'] == 'youtube')
original_count = sum(1 for c in combined if c['source'] == 'original')
has_wavlm = sum(1 for c in combined if c['has_wavlm'])

print(f"\n=== COMBINED DATASET STATS ===")
print(f"Total: {total}")
print(f"YouTube: {youtube_count} (no WavLM)")
print(f"Original: {original_count} ({has_wavlm} with WavLM)")
print(f"Positive: {positive} ({positive/max(total,1)*100:.1f}%)")
print(f"Negative: {total - positive}")

# ============================================================================
# SAVE
# ============================================================================

print(f"\nSaving to {OUTPUT_FILE}...")
with open(OUTPUT_FILE, 'w') as f:
    for item in combined:
        f.write(json.dumps(item) + '\n')

print(f"Saved {len(combined)} utterances")

# Metadata
meta = {
    'total': len(combined),
    'youtube_count': youtube_count,
    'original_count': original_count,
    'has_wavlm': has_wavlm,
    'positive': positive,
    'negative': total - positive,
    'prosody_dim': 21,
}
meta_file = OUTPUT_FILE.replace('.jsonl', '_meta.json')
with open(meta_file, 'w') as f:
    json.dump(meta, f, indent=2)
print(f"Metadata: {meta_file}")
print("Done!")
