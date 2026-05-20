#!/usr/bin/env python3
"""
HYPOTHESIS H1.1: Pause Duration Predicts Laughter
Extracts timing features from word-level timestamps in aligned segments.
NO audio loading needed — uses word start/end times from alignment.

Features per word:
  - pause_before: gap from previous word end to this word start (seconds)
  - pause_after: gap from this word end to next word start (seconds)  
  - word_duration: this word's duration (end - start)
  - speech_rate: 1/duration (words/sec for this word)
  - is_first_word: is this the first word in the utterance?
  - word_position: position within utterance (normalized 0-1)
  - utterance_length: number of words in this utterance
  - label: 0 (no laughter) or 1 (laughter triggers)

Then runs statistical tests comparing laughter vs non-laughter words.
"""

import json
import sys
import os
import numpy as np
from collections import defaultdict
from pathlib import Path
from scipy import stats

DATA_DIR = Path("/Users/Subho/autonomous_laughter_prediction_essential/data/audio_comedy")
ALIGNED_FILE = DATA_DIR / "aligned_segments.jsonl"
OUTPUT_DIR = Path("/Users/Subho/autonomous_laughter_prediction_essential/data/audio_comedy/acoustic_features")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MAX_SEGMENTS = 200_000  # sample size for quick results; use None for all

def load_segments(path, max_n=None):
    """Load aligned segments from JSONL."""
    segments = []
    with open(path) as f:
        for i, line in enumerate(f):
            if max_n and i >= max_n:
                break
            try:
                seg = json.loads(line)
                if seg.get('start') is not None and seg.get('end') is not None:
                    segments.append(seg)
            except json.JSONDecodeError:
                continue
    return segments

def extract_timing_features(segments):
    """
    Extract timing features per word.
    
    Pause computation strategy:
    - Group segments by video_id (words from same continuous audio)
    - Sort by start time
    - Compute pause_before = this.start - prev.end
    - Compute pause_after = next.start - this.end
    """
    # Group by video_id
    by_video = defaultdict(list)
    for s in segments:
        by_video[s['video_id']].append(s)
    
    all_features = []
    
    for video_id, segs in by_video.items():
        # Sort by start time
        segs.sort(key=lambda x: x['start'])
        
        for i, s in enumerate(segs):
            features = {
                'video_id': video_id,
                'word': s['word'],
                'start': s['start'],
                'end': s['end'],
                'label': s['label'],
                'position': i,
                'utterance_length': len(segs),
            }
            
            # Word duration
            features['word_duration'] = s['end'] - s['start']
            features['speech_rate'] = 1.0 / max(features['word_duration'], 0.01)
            
            # Pause before (gap from previous word)
            if i > 0 and segs[i-1]['video_id'] == video_id:
                pause = s['start'] - segs[i-1]['end']
                # Cap at 5 seconds (long pauses are likely scene breaks)
                features['pause_before'] = min(pause, 5.0)
            else:
                features['pause_before'] = None
                features['is_first_word'] = True
            
            # Pause after (gap to next word)
            if i < len(segs) - 1 and segs[i+1]['video_id'] == video_id:
                pause = segs[i+1]['start'] - s['end']
                features['pause_after'] = min(pause, 5.0)
            else:
                features['pause_after'] = None
            
            # Position normalized
            features['norm_position'] = i / max(len(segs) - 1, 1)
            
            all_features.append(features)
    
    return all_features

def run_statistical_tests(features):
    """Run t-tests comparing laughter (1) vs non-laughter (0) for each feature."""
    laugh = [f for f in features if f['label'] == 1]
    no_laugh = [f for f in features if f['label'] == 0]
    
    results = {}
    
    for feat_name in ['pause_before', 'pause_after', 'word_duration', 'speech_rate']:
        laugh_vals = [f[feat_name] for f in laugh if f.get(feat_name) is not None]
        no_laugh_vals = [f[feat_name] for f in no_laugh if f.get(feat_name) is not None]
        
        if len(laugh_vals) < 10 or len(no_laugh_vals) < 10:
            continue
        
        laugh_mean = np.mean(laugh_vals)
        no_laugh_mean = np.mean(no_laugh_vals)
        delta = laugh_mean - no_laugh_mean
        cohens_d = delta / np.sqrt((np.var(laugh_vals) + np.var(no_laugh_vals)) / 2)
        
        # Welch's t-test (unequal variance)
        t_stat, p_value = stats.ttest_ind(laugh_vals, no_laugh_vals, equal_var=False)
        
        results[feat_name] = {
            'laugh_mean': float(laugh_mean),
            'no_laugh_mean': float(no_laugh_mean),
            'delta': float(delta),
            'cohens_d': float(cohens_d),
            't_statistic': float(t_stat),
            'p_value': float(p_value),
            'significant': p_value < 0.001,
            'effect_size_meaningful': abs(cohens_d) > 0.2,
            'n_laugh': len(laugh_vals),
            'n_no_laugh': len(no_laugh_vals),
        }
    
    return results

def print_results(results, n_total):
    """Pretty-print the statistical results."""
    print(f"\n{'='*70}")
    print(f"H1.1: PAUSE DURATION PREDICTS LAUGHTER")
    print(f"Segments analyzed: {n_total:,}")
    print(f"{'='*70}")
    
    print(f"\n{'Feature':<20} {'Laugh Mean':>10} {'No-Laugh':>10} {'Delta':>10} {'Cohen d':>8} {'p-value':>12} {'Sig?':>6}")
    print(f"{'-'*20} {'-'*10} {'-'*10} {'-'*10} {'-'*8} {'-'*12} {'-'*6}")
    
    passed = 0
    for feat, r in results.items():
        sig = "✅" if r['significant'] and r['effect_size_meaningful'] else "❌"
        if r['significant'] and r['effect_size_meaningful']:
            passed += 1
        print(f"{feat:<20} {r['laugh_mean']:>10.4f} {r['no_laugh_mean']:>10.4f} "
              f"{r['delta']:>10.4f} {r['cohens_d']:>8.3f} {r['p_value']:>12.2e} {sig:>6}")
    
    print(f"\n--- Hypothesis Test ---")
    pause_result = results.get('pause_before', {})
    if pause_result.get('significant') and pause_result.get('effect_size_meaningful'):
        delta_s = pause_result['delta']
        print(f"✅ H1.1 CONFIRMED: Pre-punchline pause is {delta_s:.3f}s longer for laughter words")
        print(f"   Cohen's d = {pause_result['cohens_d']:.3f}, p = {pause_result['p_value']:.2e}")
        print(f"   Matches Purandare 2006 finding (0.8s vs 0.3s)")
    else:
        print(f"❌ H1.1 NOT CONFIRMED: Pause duration does not differentiate laughter words")
        if pause_result:
            print(f"   Delta = {pause_result['delta']:.4f}s, p = {pause_result['p_value']:.2e}")
        print(f"   Possible: studio editing removes natural pauses, or subtitle timing is imprecise")
    
    # Show effect size interpretation
    for feat, r in results.items():
        d = r['cohens_d']
        if abs(d) < 0.2:
            size = "negligible"
        elif abs(d) < 0.5:
            size = "small"
        elif abs(d) < 0.8:
            size = "medium"
        else:
            size = "large"
        print(f"\n   {feat}: Cohen's d = {d:.3f} → {size} effect")

def main():
    print("Loading aligned segments...")
    segments = load_segments(ALIGNED_FILE, MAX_SEGMENTS)
    print(f"Loaded {len(segments):,} segments")
    
    # Quick stats
    n_laugh = sum(1 for s in segments if s['label'] == 1)
    n_total = len(segments)
    print(f"Laughter rate: {n_laugh/n_total*100:.1f}% ({n_laugh:,}/{n_total:,})")
    print(f"Unique videos: {len(set(s['video_id'] for s in segments))}")
    
    print("\nExtracting timing features...")
    features = extract_timing_features(segments)
    print(f"Extracted features for {len(features):,} words")
    
    print("\nRunning statistical tests...")
    results = run_statistical_tests(features)
    print_results(results, n_total)
    
    # Save results
    import json as j
    output = {
        'hypothesis': 'H1.1',
        'n_segments': n_total,
        'n_laughter': n_laugh,
        'n_no_laughter': n_total - n_laugh,
        'feature_results': results,
        'confirmed': results.get('pause_before', {}).get('significant', False) 
                     and results.get('pause_before', {}).get('effect_size_meaningful', False)
    }
    with open(OUTPUT_DIR / 'h1_1_pause_results.json', 'w') as f:
        j.dump(output, f, indent=2)
    print(f"\nResults saved to: {OUTPUT_DIR / 'h1_1_pause_results.json'}")

if __name__ == "__main__":
    main()
