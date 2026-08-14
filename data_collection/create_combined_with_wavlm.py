#!/usr/bin/env python3
"""
Create combined dataset with WavLM + Prosody for all available data.
Fixes: only add YouTube from combined_dataset.jsonl (original already in aligned)
"""

import os
import json
import numpy as np

# Paths
CHUCKLE_DIR = '/Users/Subho/data/chuckle-net'
YOUTUBE_DIR = '/Users/Subho/data/chuckle-net-youtube'
OUTPUT_FILE = f'{YOUTUBE_DIR}/combined_with_wavlm.jsonl'

print("Building combined dataset with WavLM...")

# Load YouTube WavLM embeddings
youtube_wavlm = {}
for f in os.listdir(f'{YOUTUBE_DIR}/wavlm_embeddings'):
    if f.endswith('.json'):
        vid = f.replace('.json', '')
        with open(f'{YOUTUBE_DIR}/wavlm_embeddings/{f}') as fp:
            data = json.load(fp)
            youtube_wavlm[vid] = data

print(f"YouTube WavLM files: {len(youtube_wavlm)}")

# Load original WavLM
original_wavlm = {}
for f in os.listdir(f'{CHUCKLE_DIR}/wavlm_embeddings'):
    if f.endswith('.json'):
        vid = f.replace('.json', '')
        with open(f'{CHUCKLE_DIR}/wavlm_embeddings/{f}') as fp:
            data = json.load(fp)
            original_wavlm[vid] = data

print(f"Original WavLM files: {len(original_wavlm)}")

# Get set of original video IDs
original_video_ids = set(original_wavlm.keys())
print(f"Original video IDs: {len(original_video_ids)}")

# Build dataset
total = 0
youtube_count = 0
original_count = 0
youtube_pos = 0
original_pos = 0

with open(OUTPUT_FILE, 'w') as out:
    
    # Original utterances from aligned_utterances.jsonl (has WavLM)
    with open(f'{CHUCKLE_DIR}/aligned_utterances.jsonl') as f:
        for line in f:
            utt = json.loads(line)
            uid = utt['utterance_id']
            vid = uid.rsplit('_', 1)[0]
            
            if vid in original_wavlm and uid in original_wavlm[vid]:
                utt['has_wavlm'] = True
                emb_data = original_wavlm[vid][uid]
                if isinstance(emb_data, dict) and 'embedding' in emb_data:
                    utt['wavlm'] = emb_data['embedding']
                else:
                    utt['wavlm'] = emb_data
            else:
                utt['has_wavlm'] = False
                utt['wavlm'] = None
            
            utt['source'] = 'original'
            out.write(json.dumps(utt) + '\n')
            total += 1
            original_count += 1
            if utt.get('label_any'):
                original_pos += 1
    
    print(f"Original: {original_count} utts, {original_pos} pos")
    
    # YouTube utterances from combined_dataset.jsonl (ONLY YouTube ones)
    with open(f'{YOUTUBE_DIR}/combined_dataset.jsonl') as f:
        for line in f:
            utt = json.loads(line)
            vid = utt['video_id']
            
            # Skip if this is actually an original video
            if vid in original_video_ids:
                continue
            
            if vid in youtube_wavlm and utt['utterance_id'] in youtube_wavlm[vid]:
                utt['has_wavlm'] = True
                utt['wavlm'] = youtube_wavlm[vid][utt['utterance_id']]
            else:
                utt['has_wavlm'] = False
                utt['wavlm'] = None
            
            utt['source'] = 'youtube'
            out.write(json.dumps(utt) + '\n')
            total += 1
            youtube_count += 1
            if utt.get('label_any'):
                youtube_pos += 1

print(f"\nDataset saved: {OUTPUT_FILE}")
print(f"Total utterances: {total}")
print(f"  Original: {original_count} (pos={original_pos}, {original_pos/original_count*100:.1f}%)")
print(f"  YouTube: {youtube_count} (pos={youtube_pos}, {youtube_pos/youtube_count*100:.1f}%)")
print(f"  Total positive: {original_pos + youtube_pos} ({(original_pos+youtube_pos)/total*100:.1f}%)")
