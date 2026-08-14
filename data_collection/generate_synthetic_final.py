#!/usr/bin/env python3
"""
Generate Synthetic Laughter Data
==============================
Expands dataset with synthetic laughter samples using audio transformations.
"""

import os
import sys
import json
import numpy as np
import glob
from datetime import datetime

# Paths
ORIGINAL_DIR = '/Users/Subho/data/chuckle-net'
YOUTUBE_PROSODY_DIR = '/Users/Subho/data/chuckle-net-youtube/prosody'
OUTPUT_DIR = '/Users/Subho/data/chuckle-net-synthetic'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ============================================================================
# SYNTHETIC LAUGHTER TRANSFORMATIONS
# ============================================================================

class SyntheticLaughGenerator:
    """Generates synthetic laughter samples from real data."""
    
    def __init__(self, seed=42):
        self.np = np.random.RandomState(seed)
    
    def transform_prosody_to_laugh(self, prosody: list) -> list:
        """Transform prosody features to simulate laughter characteristics."""
        if not prosody or len(prosody) < 7:
            return [0.0] * 21
        
        f = np.array(prosody).copy()
        
        # 1. Duration: laughs are often longer
        if len(f) > 5:
            f[5] = f[5] * self.np.uniform(1.2, 1.8)
        
        # 2. Pitch: laughs have distinctive pitch
        if len(f) > 2 and f[2] > 0:
            f[2] = f[2] * self.np.uniform(0.9, 1.3)
        if len(f) > 3:
            f[3] = f[3] * self.np.uniform(1.3, 1.8)
        if len(f) > 4:
            f[4] = f[4] * self.np.uniform(1.2, 1.5)
        
        # 3. Energy: laughs have rhythmic energy
        if len(f) > 0:
            f[0] = f[0] * self.np.uniform(0.8, 1.4)
        
        # 4. MFCCs
        for i in range(7, min(12, len(f))):
            f[i] = f[i] * self.np.uniform(1.1, 1.4)
        for i in range(12, min(20, len(f))):
            f[i] = f[i] * self.np.uniform(0.9, 1.1)
        
        return f[:21].tolist()
    
    def generate_negative_variant(self, prosody: list) -> list:
        """Generate slightly modified negative (still negative)."""
        if not prosody or len(prosody) < 7:
            return [0.0] * 21
        
        f = np.array(prosody).copy()
        for i in range(min(len(f), 21)):
            f[i] = f[i] * self.np.normal(1.0, 0.03)
        
        return f[:21].tolist()

# ============================================================================
# MAIN
# ============================================================================

def main():
    print("="*70)
    print("SYNTHETIC LAUGHTER DATA GENERATION")
    print("="*70)
    
    generator = SyntheticLaughGenerator()
    
    # Load original prosody
    print("\n1. Loading original 71 videos with prosody...")
    prosody_file = f'{ORIGINAL_DIR}/prosody_phaseD.json'
    
    # Load prosody - keyed by uid
    prosody_by_uid = {}
    with open(prosody_file) as f:
        prosody_data = json.load(f)
    
    for p in prosody_data:
        uid = p.get('uid', '')
        feats = p.get('feats', [])
        if uid and feats and len(feats) >= 7:
            prosody_by_uid[uid] = feats
    
    print(f"   Loaded prosody for {len(prosody_by_uid):,} utterances")
    
    # Load aligned data for labels
    print("   Loading labels from aligned data...")
    aligned_file = f'{ORIGINAL_DIR}/aligned_utterances.jsonl'
    
    # uid mapping: utterance_id -> label
    uid_to_label = {}
    uid_to_vid = {}
    
    with open(aligned_file) as f:
        for line in f:
            try:
                d = json.loads(line.strip())
                # Build uid from start time
                vid = d.get('video_id', '')
                start = float(d.get('start', 0))
                uid = f"{vid}_{start:.2f}"
                uid_to_label[uid] = int(d.get('label_any', 0))
                uid_to_vid[uid] = vid
            except:
                pass
    
    print(f"   Loaded {len(uid_to_label):,} labels")
    
    # Separate by label
    positive_samples = []
    negative_samples = []
    
    for uid, feats in prosody_by_uid.items():
        if uid in uid_to_label:
            label = uid_to_label[uid]
            if label == 1:
                positive_samples.append({'uid': uid, 'prosody': feats, 'label': 1})
            else:
                negative_samples.append({'uid': uid, 'prosody': feats, 'label': 0})
    
    print(f"\n   Positive samples: {len(positive_samples):,}")
    print(f"   Negative samples: {len(negative_samples):,}")
    
    # Load YouTube prosody
    print("\n2. Loading YouTube prosody...")
    yt_prosody = []
    yt_files = glob.glob(f'{YOUTUBE_PROSODY_DIR}/*.json')
    
    for f in yt_files:
        try:
            with open(f) as fp:
                data = json.load(fp)
                utts = data.get('utterances', [])
                for u in utts:
                    feats = u.get('prosody', [])
                    if feats and len(feats) >= 7:
                        yt_prosody.append({
                            'uid': u['uid'],
                            'prosody': feats,
                            'video_id': u.get('video_id', '')
                        })
        except:
            pass
    
    print(f"   YouTube prosody samples: {len(yt_prosody):,}")
    
    # Generate synthetic data
    print("\n3. Generating synthetic laughter samples...")
    
    synthetic = []
    
    # From positive samples (each -> 3 synthetic)
    print(f"   Processing {len(positive_samples)} positive samples...")
    for p in positive_samples:
        for i in range(3):
            synth_prosody = generator.transform_prosody_to_laugh(p['prosody'])
            synthetic.append({
                'uid': f"SYNTH_POS_{p['uid']}_{i}",
                'prosody': synth_prosody,
                'wavlm': None,
                'label_any': 1,
                'label_majority': 1,
                'is_synthetic': True,
                'generation_method': 'positive_transform',
                'source_uid': p['uid']
            })
    
    # From YouTube samples (each -> 1 synthetic, limit to 5000)
    print(f"   Processing {min(len(yt_prosody), 5000)} YouTube samples...")
    for y in yt_prosody[:5000]:
        synth_prosody = generator.transform_prosody_to_laugh(y['prosody'])
        synthetic.append({
            'uid': f"SYNTH_YT_{y['uid']}_0",
            'prosody': synth_prosody,
            'wavlm': None,
            'label_any': 1,
            'label_majority': 1,
            'is_synthetic': True,
            'generation_method': 'youtube_transform',
            'source_uid': y['uid']
        })
    
    # From negative samples (each -> 1 synthetic variant)
    print(f"   Processing {min(len(negative_samples), 5000)} negative samples...")
    for n in negative_samples[:5000]:
        neg_prosody = generator.generate_negative_variant(n['prosody'])
        synthetic.append({
            'uid': f"SYNTH_NEG_{n['uid']}_0",
            'prosody': neg_prosody,
            'wavlm': None,
            'label_any': 0,
            'label_majority': 0,
            'is_synthetic': True,
            'generation_method': 'negative_variant',
            'source_uid': n['uid']
        })
    
    print(f"\nTotal synthetic samples: {len(synthetic):,}")
    
    synth_pos = sum(1 for s in synthetic if s['label_any'] == 1)
    synth_neg = sum(1 for s in synthetic if s['label_any'] == 0)
    print(f"   Synthetic positive: {synth_pos:,}")
    print(f"   Synthetic negative: {synth_neg:,}")
    
    # Save
    synthetic_file = f'{OUTPUT_DIR}/synthetic_dataset.jsonl'
    with open(synthetic_file, 'w') as f:
        for item in synthetic:
            f.write(json.dumps(item) + '\n')
    
    print(f"\nSaved to {synthetic_file}")
    
    # Statistics
    print("\n" + "="*70)
    print("COMBINED DATASET SUMMARY")
    print("="*70)
    
    orig_pos = len(positive_samples)
    orig_neg = len(negative_samples)
    orig_total = orig_pos + orig_neg
    
    synth_total = len(synthetic)
    combined_pos = orig_pos + synth_pos
    combined_neg = orig_neg + synth_neg
    combined_total = combined_pos + combined_neg
    
    print(f"\nORIGINAL (71 videos with prosody):")
    print(f"  Total: {orig_total:,}")
    print(f"  Positive: {orig_pos:,} ({orig_pos/orig_total*100:.1f}%)" if orig_total > 0 else "  Positive: 0")
    print(f"  Negative: {orig_neg:,} ({orig_neg/orig_total*100:.1f}%)" if orig_total > 0 else "  Negative: 0")
    
    print(f"\nSYNTHETIC:")
    print(f"  Total: {synth_total:,}")
    print(f"  Positive (transformed): {synth_pos:,}")
    print(f"  Negative (variants): {synth_neg:,}")
    
    print(f"\nCOMBINED:")
    print(f"  Total: {combined_total:,}")
    print(f"  Positive: {combined_pos:,} ({combined_pos/combined_total*100:.1f}%)" if combined_total > 0 else f"  Positive: 0")
    print(f"  Negative: {combined_neg:,} ({combined_neg/combined_total*100:.1f}%)" if combined_total > 0 else f"  Negative: 0")
    
    print("\n" + "="*70)
    print("DONE!")
    print("="*70)

if __name__ == '__main__':
    main()
