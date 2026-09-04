#!/usr/bin/env python3
"""
Video Selection Pipeline: Find laughter-rich videos using energy patterns.
Based on finding: rel_energy > 2.0 predicts laughter better than VTT markers.
"""
import numpy as np
import pandas as pd
import json
import os
import time
from pathlib import Path
from collections import defaultdict
import argparse

SR = 16000

def analyze_video_energy(audio_path, utterances):
    """Analyze a video's energy patterns to detect laughter richness."""
    try:
        import librosa
        y, sr = librosa.load(audio_path, sr=SR, mono=True)
    except Exception as e:
        return None
    
    if len(y) < SR:  # Too short
        return None
    
    full_rms = float(np.sqrt(np.mean(y**2)) + 1e-8)
    
    stats = {
        'n_utterances': len(utterances),
        'total_duration': float(len(y)) / SR,
        'full_rms': full_rms,
        'full_rms_db': 20 * np.log10(full_rms + 1e-8),
    }
    
    # Energy per utterance
    rel_energies = []
    for u in utterances:
        s = int(u['start'] * SR)
        e = int(u['end'] * SR)
        if e > len(y):
            e = len(y)
        seg = y[s:e]
        if len(seg) > 0:
            seg_rms = float(np.sqrt(np.mean(seg**2)))
            rel_e = seg_rms / full_rms
            rel_energies.append(rel_e)
    
    if not rel_energies:
        return None
    
    rel_energies = np.array(rel_energies)
    
    # Key metrics for laughter detection
    stats['n_segments'] = len(rel_energies)
    stats['mean_rel_energy'] = float(np.mean(rel_energies))
    stats['max_rel_energy'] = float(np.max(rel_energies))
    stats['std_rel_energy'] = float(np.std(rel_energies))
    
    # Laughter thresholds (based on our findings)
    stats['n_above_1.5'] = int(np.sum(rel_energies > 1.5))
    stats['n_above_2.0'] = int(np.sum(rel_energies > 2.0))
    stats['n_above_2.5'] = int(np.sum(rel_energies > 2.5))
    stats['n_above_3.0'] = int(np.sum(rel_energies > 3.0))
    
    # Positive rate at different thresholds
    stats['rate_1.5'] = float(np.mean(rel_energies > 1.5))
    stats['rate_2.0'] = float(np.mean(rel_energies > 2.0))
    stats['rate_2.5'] = float(np.mean(rel_energies > 2.5))
    stats['rate_3.0'] = float(np.mean(rel_energies > 3.0))
    
    # VTT label rate (if available)
    vtt_labels = [u.get('label', 0) for u in utterances]
    if vtt_labels:
        stats['vtt_positive_rate'] = float(np.mean(vtt_labels))
        stats['n_vtt_positive'] = int(sum(vtt_labels))
    
    # Combined score: videos with high energy AND high VTT = best
    # Videos with high energy but low VTT = might have missed laughter
    if stats.get('vtt_positive_rate', 0) > 0:
        stats['energy_vtt_product'] = stats['rate_2.0'] * stats['vtt_positive_rate']
    else:
        stats['energy_vtt_product'] = 0
    
    return stats

def main():
    import glob
    
    # Paths
    BASE = Path('/Users/Subho/data/utterances')
    AUDIO_DIR = BASE / 'vtt_audio_local'
    UTT_FILE = Path('/Users/Subho/autonomous_laughter_prediction_essential/data/utterances/utterances_clean.jsonl')
    OUTPUT_DIR = Path('/Users/Subho/autonomous_laughter_prediction_essential/data/training')
    
    # Load utterances
    print("Loading utterances...")
    with open(UTT_FILE) as f:
        utterances = [json.loads(l) for l in f]
    
    # Group by video
    utts_by_vid = defaultdict(list)
    for u in utterances:
        utts_by_vid[u['video_id']].append(u)
    
    print(f"Total videos: {len(utts_by_vid)}")
    print(f"Total utterances: {len(utterances)}")
    
    # Find audio files
    audio_files = {}
    for mp4 in AUDIO_DIR.glob('*.m4a'):
        vid = mp4.stem
        audio_files[vid] = str(mp4)
    
    print(f"Audio files found: {len(audio_files)}")
    
    # Find overlap
    overlap = sorted(set(audio_files.keys()) & set(utts_by_vid.keys()))
    print(f"Videos with both audio and utterances: {len(overlap)}")
    
    # Analyze each video
    print("\nAnalyzing videos...")
    results = []
    t0 = time.time()
    
    for i, vid in enumerate(overlap):
        audio_path = audio_files[vid]
        utts = utts_by_vid[vid]
        
        stats = analyze_video_energy(audio_path, utts)
        if stats:
            stats['video_id'] = vid
            stats['audio_path'] = audio_path
            results.append(stats)
        
        if (i+1) % 50 == 0:
            elapsed = time.time() - t0
            rate = (i+1) / elapsed
            remaining = len(overlap) - (i+1)
            eta = remaining / rate
            print(f"  {i+1}/{len(overlap)} | {rate:.1f} videos/sec | ETA: {eta/60:.1f} min")
    
    print(f"\nAnalyzed {len(results)} videos in {(time.time()-t0)/60:.1f} min")
    
    # Create DataFrame
    df = pd.DataFrame(results)
    
    # Score videos by laughter potential
    # Use rate_2.0 (energy > 2.0) as primary indicator
    # Videos with rate_2.0 > 5% are likely to have real laughter
    df['laughter_score'] = df['rate_2.0']
    
    # Sort by laughter score
    df = df.sort_values('laughter_score', ascending=False)
    
    print(f"\n{'='*70}")
    print("TOP 50 LAUGHTER-RICH VIDEOS (by energy > 2.0)")
    print(f"{'='*70}")
    print(f"{'Rank':<5} {'Video ID':<20} {'Rate@2.0':>10} {'VTT Rate':>10} {'Score':>8}")
    print(f"{'-'*70}")
    
    for rank, (_, row) in enumerate(df.head(50).iterrows()):
        print(f"{rank+1:<5} {row['video_id']:<20} {row['rate_2.0']*100:>9.1f}% {row.get('vtt_positive_rate', 0)*100:>9.1f}% {row['laughter_score']:>8.3f}")
    
    # Select best videos for training
    # Criteria: rate_2.0 > 5% (top ~10% of videos)
    threshold = 0.05
    selected = df[df['laughter_score'] >= threshold].copy()
    
    print(f"\n{'='*70}")
    print(f"SELECTED VIDEOS (rate_2.0 >= {threshold*100:.0f}%)")
    print(f"{'='*70}")
    print(f"Total: {len(selected)} videos out of {len(df)} ({len(selected)/len(df)*100:.1f}%)")
    print(f"Average rate_2.0: {selected['rate_2.0'].mean()*100:.1f}%")
    print(f"Average VTT positive rate: {selected['vtt_positive_rate'].mean()*100:.1f}%")
    
    # Show distribution
    print(f"\nDistribution of selected videos by rate_2.0:")
    bins = [(0.05, 0.10), (0.10, 0.15), (0.15, 0.20), (0.20, 0.30), (0.30, 1.0)]
    for lo, hi in bins:
        count = len(selected[(selected['rate_2.0'] >= lo) & (selected['rate_2.0'] < hi)])
        print(f"  {lo*100:.0f}-{hi*100:.0f}%: {count} videos")
    
    # Save results
    output_file = OUTPUT_DIR / 'laughter_rich_videos.json'
    selected_dict = selected.to_dict('records')
    with open(output_file, 'w') as f:
        json.dump(selected_dict, f, indent=2)
    print(f"\nSaved {len(selected_dict)} selected videos to {output_file}")
    
    # Also save full analysis
    full_output = OUTPUT_DIR / 'all_video_analysis.json'
    df.to_json(full_output, orient='records', indent=2)
    print(f"Saved full analysis ({len(df)} videos) to {full_output}")
    
    # Create training-ready dataset
    print(f"\n{'='*70}")
    print("CREATING TRAINING DATASET")
    print(f"{'='*70}")
    
    # For selected videos, create utterance-level dataset with energy labels
    training_data = []
    for _, row in selected.iterrows():
        vid = row['video_id']
        utts = utts_by_vid.get(vid, [])
        
        # Load audio for this video
        try:
            import librosa
            y, sr = librosa.load(row['audio_path'], sr=SR, mono=True)
            full_rms = float(np.sqrt(np.mean(y**2)) + 1e-8)
        except:
            continue
        
        for u in utts:
            s = int(u['start'] * SR)
            e = int(u['end'] * SR)
            if e > len(y):
                e = len(y)
            seg = y[s:e]
            if len(seg) < SR * 0.1:  # Skip < 0.1 sec
                continue
            
            seg_rms = float(np.sqrt(np.mean(seg**2)))
            rel_e = seg_rms / full_rms
            
            # Label: 1 if rel_energy > 2.0, else 0
            label = 1 if rel_e > 2.0 else 0
            
            training_data.append({
                'video_id': vid,
                'start': u['start'],
                'end': u['end'],
                'duration': u['end'] - u['start'],
                'text': u.get('text', ''),
                'n_words': u.get('n_words', 0),
                'rel_energy': rel_e,
                'energy_label': label,
                'vtt_label': u.get('label', 0),
            })
    
    print(f"Training samples: {len(training_data)}")
    pos = sum(1 for d in training_data if d['energy_label'] == 1)
    print(f"Positive (rel_energy > 2.0): {pos} ({pos/len(training_data)*100:.1f}%)")
    
    # Save training data
    train_file = OUTPUT_DIR / 'laughter_rich_training_data.jsonl'
    with open(train_file, 'w') as f:
        for d in training_data:
            f.write(json.dumps(d) + '\n')
    print(f"Saved to {train_file}")
    
    # Summary stats
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print(f"Total video candidates: {len(df)}")
    print(f"Selected laughter-rich videos: {len(selected)} ({len(selected)/len(df)*100:.1f}%)")
    print(f"Total training utterances: {len(training_data)}")
    print(f"Positive rate (energy > 2.0): {pos/len(training_data)*100:.1f}%")
    print(f"\nThis is {(pos/len(training_data)) / 0.02:.1f}x more positive than VTT labels (1.2%)")

if __name__ == '__main__':
    main()
