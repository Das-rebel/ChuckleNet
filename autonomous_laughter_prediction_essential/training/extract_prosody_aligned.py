#!/usr/bin/env python3
"""
Extract prosody features from audio files matched with aligned segments.
Aligns audio with word-level labels from aligned_segments.jsonl.

Usage:
    python3 training/extract_prosody_aligned.py --output data/audio_comedy/prosody_features.csv
"""

import argparse
import json
import os
import sys
import warnings
from collections import defaultdict
from pathlib import Path

import librosa
import numpy as np
import pandas as pd

warnings.filterwarnings('ignore')


def extract_f0_features(y, sr, start_sec, end_sec):
    """Extract F0 statistics from a time window."""
    start_sample = max(0, int(start_sec * sr))
    end_sample = min(len(y), int(end_sec * sr))
    segment = y[start_sample:end_sample]
    
    if len(segment) < sr * 0.05:  # too short (< 50ms)
        return {k: 0.0 for k in [
            'f0_mean', 'f0_std', 'f0_range', 'f0_min', 'f0_max', 'f0_slope', 'f0_voiced_ratio'
        ]}

    f0, voiced_flag, _ = librosa.pyin(segment, fmin=75, fmax=500, sr=sr,
                                       frame_length=2048, hop_length=512)
    voiced = f0[~np.isnan(f0)]

    if len(voiced) == 0:
        return {
            'f0_mean': 0.0, 'f0_std': 0.0, 'f0_range': 0.0,
            'f0_min': 0.0, 'f0_max': 0.0, 'f0_slope': 0.0,
            'f0_voiced_ratio': 0.0
        }

    slope = 0.0
    if len(voiced) > 2:
        slope = np.polyfit(np.arange(len(voiced)), voiced, 1)[0]

    return {
        'f0_mean': float(np.mean(voiced)),
        'f0_std': float(np.std(voiced)),
        'f0_range': float(np.max(voiced) - np.min(voiced)),
        'f0_min': float(np.min(voiced)),
        'f0_max': float(np.max(voiced)),
        'f0_slope': float(slope),
        'f0_voiced_ratio': float(len(voiced) / len(f0)),
    }


def extract_energy_features(y, sr, start_sec, end_sec):
    """Extract RMS energy statistics."""
    start_sample = max(0, int(start_sec * sr))
    end_sample = min(len(y), int(end_sec * sr))
    segment = y[start_sample:end_sample]
    
    if len(segment) < 512:
        return {k: 0.0 for k in ['rms_mean', 'rms_std', 'rms_max', 'rms_range']}

    rms = librosa.feature.rms(y=segment, frame_length=2048, hop_length=512)[0]
    return {
        'rms_mean': float(np.mean(rms)),
        'rms_std': float(np.std(rms)),
        'rms_max': float(np.max(rms)),
        'rms_range': float(np.max(rms) - np.min(rms)),
    }


def compute_pause_before(y, sr, word_start_sec, prev_word_end_sec):
    """Compute pause duration between two words."""
    if prev_word_end_sec is None:
        return 0.0
    pause = word_start_sec - prev_word_end_sec
    return float(max(0, min(5, pause)))  # clip at 5s


def extract_features_for_segment(y, sr, word_info, prev_word_end=None):
    """Extract all prosody features for one word segment."""
    start = word_info['start']
    end = word_info['end']
    
    # Context window (200ms before and after)
    ctx = 0.2
    ctx_start = max(0, start - ctx)
    ctx_end = min(len(y) / sr, end + ctx)
    
    features = {}
    
    # F0 features
    f0_feats = extract_f0_features(y, sr, ctx_start, ctx_end)
    features.update(f0_feats)
    
    # Energy features
    energy_feats = extract_energy_features(y, sr, ctx_start, ctx_end)
    features.update(energy_feats)
    
    # Pause before
    features['pause_before'] = compute_pause_before(y, sr, start, prev_word_end)
    
    # Word duration
    features['word_duration'] = end - start
    
    # Speech rate (words per second approximation)
    features['speech_rate'] = 1.0 / (end - start) if (end - start) > 0.01 else 0.0
    
    return features


def main():
    parser = argparse.ArgumentParser(description='Extract prosody from aligned segments')
    parser.add_argument('--aligned', default='data/audio_comedy/aligned_segments.jsonl',
                        help='Path to aligned segments JSONL')
    parser.add_argument('--audio-dir', default='data/audio_comedy/audio',
                        help='Directory containing audio files')
    parser.add_argument('--output', default='data/audio_comedy/prosody_features.csv',
                        help='Output CSV path')
    parser.add_argument('--limit', type=int, default=0, help='Limit files (0=all)')
    args = parser.parse_args()
    
    # Load aligned segments
    print(f"Loading aligned segments from {args.aligned}...")
    segments = []
    with open(args.aligned) as f:
        for line in f:
            try:
                segments.append(json.loads(line))
            except:
                pass
    print(f"Loaded {len(segments)} segments")
    
    # Group by video
    video_segments = defaultdict(list)
    for seg in segments:
        video_segments[seg['video_id']].append(seg)
    
    print(f"Unique videos: {len(video_segments)}")
    
    # Find audio files
    audio_files = {}
    for root, dirs, files in os.walk(args.audio_dir):
        for f in files:
            if f.endswith('.mp3'):
                video_id = f.replace('.mp3', '')
                audio_files[video_id] = os.path.join(root, f)
    
    print(f"Found {len(audio_files)} audio files")
    
    # Extract features
    all_features = []
    processed = 0
    
    for video_id, segs in video_segments.items():
        if video_id not in audio_files:
            continue
        
        audio_path = audio_files[video_id]
        
        print(f"Processing {video_id} ({processed+1}/{len(video_segments)})...")
        
        try:
            # Load audio
            y, sr = librosa.load(audio_path, sr=16000)
            
            # Sort segments by start time
            segs_sorted = sorted(segs, key=lambda x: x['start'])
            
            for i, seg in enumerate(segs_sorted):
                prev_end = segs_sorted[i-1]['end'] if i > 0 else None
                
                feats = extract_features_for_segment(y, sr, seg, prev_end)
                feats['video_id'] = video_id
                feats['word'] = seg.get('word', '')
                feats['start'] = seg['start']
                feats['end'] = seg['end']
                feats['label'] = seg.get('label', 0)
                
                all_features.append(feats)
                
        except Exception as e:
            print(f"  Error processing {video_id}: {e}")
        
        processed += 1
        if args.limit > 0 and processed >= args.limit:
            break
    
    # Save to CSV
    if all_features:
        df = pd.DataFrame(all_features)
        df.to_csv(args.output, index=False)
        print(f"\nWrote {len(df)} features to {args.output}")
        print(f"Columns: {list(df.columns)}")
        
        # Print summary
        print(f"\nFeature summary:")
        for col in df.columns:
            if col not in ['video_id', 'word', 'start', 'end', 'label']:
                print(f"  {col}: mean={df[col].mean():.3f}, std={df[col].std():.3f}")
    else:
        print("No features extracted!")


if __name__ == '__main__':
    main()