#!/usr/bin/env python3
"""
Unified Dataset Builder
======================
Builds a unified training dataset from all available data:
1. Original 71 videos (WavLM + Prosody + Labels)
2. YouTube processed (Prosody + [laughter] markers)
3. YouTube with audio (WavLM + Prosody)

Creates a consistent format with quality metadata.
"""

import os
import sys
import json
import glob
from datetime import datetime
from typing import Dict, List

# ============================================================================
# PATHS
# ============================================================================

# Original data
ORIGINAL_DIR = '/Users/Subho/data/chuckle-net'
ORIGINAL_ALIGNED = f'{ORIGINAL_DIR}/aligned_utterances.jsonl'
ORIGINAL_WAVLM = f'{ORIGINAL_DIR}/wavlm_embeddings'
ORIGINAL_PROSODY = f'{ORIGINAL_DIR}/prosody_phaseD.json'

# YouTube data
YOUTUBE_DIR = '/Users/Subho/data/chuckle-net-youtube'
YOUTUBE_PROCESSED = f'{YOUTUBE_DIR}/processed'
YOUTUBE_WAVLM = f'{YOUTUBE_DIR}/wavlm_embeddings'
YOUTUBE_PROSODY = f'{YOUTUBE_DIR}/prosody'

# Output
OUTPUT_DIR = '/Users/Subho/data/chuckle-net-unified'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ============================================================================
# LOAD ORIGINAL DATA
# ============================================================================

def load_original_data() -> Dict:
    """Load original 71 videos with WavLM and labels."""
    print("Loading original data...")
    
    # Load aligned utterances
    utterances = {}
    with open(ORIGINAL_ALIGNED) as f:
        for line in f:
            try:
                d = json.loads(line.strip())
                vid = d['video_id']
                if vid not in utterances:
                    utterances[vid] = []
                utterances[vid].append(d)
            except:
                pass
    
    print(f"  Loaded {len(utterances)} original videos")
    
    # Load WavLM embeddings (by file)
    wavlm_by_video = {}
    for f in glob.glob(f'{ORIGINAL_WAVLM}/*.json'):
        vid = os.path.basename(f).replace('.json', '')
        try:
            with open(f) as fp:
                data = json.load(fp)
                wavlm_by_video[vid] = data
        except:
            pass
    
    print(f"  Loaded WavLM for {len(wavlm_by_video)} videos")
    
    # Load prosody
    prosody_by_uid = {}
    if os.path.exists(ORIGINAL_PROSODY):
        with open(ORIGINAL_PROSODY) as f:
            prosody_data = json.load(f)
            for d in prosody_data:
                uid = d.get('uid', '')
                if uid:
                    prosody_by_uid[uid] = d
    
    print(f"  Loaded prosody for {len(prosody_by_uid)} utterances")
    
    return {
        'utterances': utterances,
        'wavlm': wavlm_by_video,
        'prosody': prosody_by_uid,
        'source': 'original'
    }

# ============================================================================
# LOAD YOUTUBE DATA
# ============================================================================

def load_youtube_data() -> Dict:
    """Load YouTube processed videos."""
    print("Loading YouTube data...")
    
    processed = {}
    for f in glob.glob(f'{YOUTUBE_PROCESSED}/*.json'):
        vid = os.path.basename(f).replace('.json', '')
        try:
            with open(f) as fp:
                data = json.load(fp)
                processed[vid] = data
        except:
            pass
    
    print(f"  Loaded {len(processed)} YouTube videos")
    
    # Load WavLM embeddings
    wavlm_by_video = {}
    for f in glob.glob(f'{YOUTUBE_WAVLM}/*.json'):
        vid = os.path.basename(f).replace('.json', '')
        try:
            with open(f) as fp:
                data = json.load(fp)
                wavlm_by_video[vid] = data
        except:
            pass
    
    print(f"  Loaded WavLM for {len(wavlm_by_video)} YouTube videos")
    
    # Load prosody
    prosody_by_video = {}
    for f in glob.glob(f'{YOUTUBE_PROSODY}/*.json'):
        vid = os.path.basename(f).replace('.json', '')
        try:
            with open(f) as fp:
                data = json.load(fp)
                prosody_by_video[vid] = data
        except:
            pass
    
    print(f"  Loaded prosody for {len(prosody_by_video)} YouTube videos")
    
    return {
        'processed': processed,
        'wavlm': wavlm_by_video,
        'prosody': prosody_by_video,
        'source': 'youtube'
    }

# ============================================================================
# BUILD UNIFIED DATASET
# ============================================================================

def build_unified_dataset(original: Dict, youtube: Dict) -> List[Dict]:
    """Build unified dataset from both sources."""
    print("\nBuilding unified dataset...")
    
    unified = []
    
    # ============ ORIGINAL DATA ============
    print("  Processing original 71 videos...")
    orig_utts = original['utterances']
    orig_wavlm = original['wavlm']
    orig_prosody = original['prosody']
    
    for vid, utts in orig_utts.items():
        wavlm_data = orig_wavlm.get(vid, {})
        
        for utt in utts:
            uid = utt['utterance_id']
            
            # Get features
            features = {
                'uid': uid,
                'video_id': vid,
                'text': utt.get('text', ''),
                'start': float(utt.get('start', 0)),
                'end': float(utt.get('end', 0)),
                'duration': float(utt.get('duration', 0)),
            }
            
            # WavLM embedding
            if uid in wavlm_data:
                features['wavlm'] = wavlm_data[uid].get('embedding', [])
            else:
                features['wavlm'] = None
            
            # Prosody
            if uid in orig_prosody:
                p = orig_prosody[uid]
                features['prosody'] = p.get('features', p.get('feats', []))
            else:
                features['prosody'] = None
            
            # Label
            features['label_any'] = int(utt.get('label_any', 0))
            features['label_majority'] = int(utt.get('label_majority', 0))
            features['n_positive_words'] = int(utt.get('n_positive_words', 0))
            
            # Source info
            features['source'] = 'original'
            features['comedian'] = vid.split('_')[0] if '_' in vid else vid
            
            unified.append(features)
    
    print(f"    Added {len([u for u in unified if u['source'] == 'original'])} original utterances")
    
    # ============ YOUTUBE DATA ============
    print("  Processing YouTube videos...")
    yt_processed = youtube['processed']
    yt_wavlm = youtube['wavlm']
    yt_prosody = youtube['prosody']
    
    for vid, data in yt_processed.items():
        utts = data.get('utterances', [])
        prosody_data = yt_prosody.get(vid, {})
        wavlm_data = yt_wavlm.get(vid, {})
        
        prosody_by_start = {}
        if 'utterances' in prosody_data:
            for p in prosody_data['utterances']:
                start_key = f"{p.get('start', 0):.2f}"
                prosody_by_start[start_key] = p.get('prosody', [])
        
        wavlm_by_start = {}
        if isinstance(wavlm_data, dict):
            for uid, emb in wavlm_data.items():
                # WavLM UID format: video_id_XXXX
                parts = uid.rsplit('_', 1)
                if len(parts) == 2:
                    start = parts[1]
                    wavlm_by_start[start] = emb.get('embedding', [])
        
        for utt in utts:
            start_key = f"{utt.get('start', 0):.2f}"
            
            features = {
                'uid': f'{vid}_{utt.get("start", 0):.2f}',
                'video_id': vid,
                'text': utt.get('text', ''),
                'start': float(utt.get('start', 0)),
                'end': float(utt.get('end', 0)),
                'duration': float(utt.get('duration', 0)),
            }
            
            # Prosody
            features['prosody'] = prosody_by_start.get(start_key, [0]*21)
            
            # WavLM
            if start_key in wavlm_by_start:
                features['wavlm'] = wavlm_by_start[start_key]
            else:
                features['wavlm'] = None
            
            # Label from [laughter] in text
            text = utt.get('text', '').lower()
            has_laughter = '[laughter]' in text
            features['label_any'] = 1 if has_laughter else 0
            features['label_majority'] = 1 if has_laughter else 0
            features['n_positive_words'] = 0
            
            # Source
            features['source'] = 'youtube'
            features['comedian'] = vid
            
            unified.append(features)
    
    yt_count = len([u for u in unified if u['source'] == 'youtube'])
    print(f"    Added {yt_count} YouTube utterances")
    
    return unified

# ============================================================================
# STATISTICS
# ============================================================================

def print_statistics(unified: List[Dict]):
    """Print dataset statistics."""
    print("\n" + "=" * 70)
    print("UNIFIED DATASET STATISTICS")
    print("=" * 70)
    
    # By source
    by_source = {'original': 0, 'youtube': 0}
    by_label = {0: 0, 1: 0}
    by_wavlm = {'has': 0, 'missing': 0}
    by_prosody = {'has': 0, 'missing': 0}
    
    for u in unified:
        by_source[u['source']] += 1
        by_label[u['label_any']] += 1
        by_wavlm['has' if u['wavlm'] else 'missing'] += 1
        by_prosody['has' if u['prosody'] else 'missing'] += 1
    
    print(f"\nTotal utterances: {len(unified):,}")
    
    print(f"\nBy source:")
    for src, count in by_source.items():
        print(f"  {src}: {count:,} ({count/len(unified)*100:.1f}%)")
    
    print(f"\nLabels:")
    print(f"  Positive (laugh): {by_label[1]:,} ({by_label[1]/len(unified)*100:.1f}%)")
    print(f"  Negative (no laugh): {by_label[0]:,} ({by_label[0]/len(unified)*100:.1f}%)")
    
    print(f"\nFeatures:")
    print(f"  WavLM: {by_wavlm['has']:,} has, {by_wavlm['missing']:,} missing")
    print(f"  Prosody: {by_prosody['has']:,} has, {by_prosody['missing']:,} missing")
    
    # Positive rate by source
    for src in ['original', 'youtube']:
        src_data = [u for u in unified if u['source'] == src]
        if src_data:
            pos = sum(1 for u in src_data if u['label_any'] == 1)
            print(f"  {src} positive rate: {pos/len(src_data)*100:.1f}%")
    
    # Videos by comedian
    comedians = {}
    for u in unified:
        c = u['comedian']
        if c not in comedians:
            comedians[c] = {'total': 0, 'positive': 0}
        comedians[c]['total'] += 1
        comedians[c]['positive'] += u['label_any']
    
    print(f"\nUnique comedians: {len(comedians)}")
    
    # Top comedians by positive rate
    top_comedians = sorted(comedians.items(), 
                          key=lambda x: -x[1]['positive']/x[1]['total'] if x[1]['total'] > 0 else 0)[:10]
    
    print("\nTop comedians by positive rate:")
    for c, stats in top_comedians:
        rate = stats['positive']/stats['total']*100 if stats['total'] > 0 else 0
        print(f"  {rate:>5.1f}% | {stats['positive']:>4}/{stats['total']:>5} | {c[:40]}")

# ============================================================================
# SAVE
# ============================================================================

def save_unified_dataset(unified: List[Dict]):
    """Save unified dataset."""
    output_file = f'{OUTPUT_DIR}/unified_dataset.jsonl'
    
    print(f"\nSaving to {output_file}...")
    with open(output_file, 'w') as f:
        for item in unified:
            f.write(json.dumps(item) + '\n')
    
    # Save summary
    summary_file = f'{OUTPUT_DIR}/dataset_summary.json'
    with open(summary_file, 'w') as f:
        json.dump({
            'total_utterances': len(unified),
            'created_at': datetime.now().isoformat(),
            'sources': {
                'original': len([u for u in unified if u['source'] == 'original']),
                'youtube': len([u for u in unified if u['source'] == 'youtube'])
            },
            'features': {
                'has_wavlm': len([u for u in unified if u['wavlm']]),
                'has_prosody': len([u for u in unified if u['prosody']])
            }
        }, f, indent=2)
    
    print(f"Saved {len(unified):,} utterances")
    print(f"Summary saved to {summary_file}")

# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 70)
    print("UNIFIED DATASET BUILDER")
    print("=" * 70)
    
    # Load data
    original = load_original_data()
    youtube = load_youtube_data()
    
    # Build unified dataset
    unified = build_unified_dataset(original, youtube)
    
    # Statistics
    print_statistics(unified)
    
    # Save
    save_unified_dataset(unified)
    
    print("\n" + "=" * 70)
    print("DONE")
    print("=" * 70)

if __name__ == '__main__':
    main()
