#!/usr/bin/env python3
"""
Stream-based prosody extraction - processes audio in chunks to avoid memory issues.
Uses soundfile for efficient loading, extracts features per word segment.

Usage:
    python3 training/extract_prosody_stream.py --limit 50
"""

import argparse
import json
import os
import warnings
import time
from collections import defaultdict

import librosa
import numpy as np
import pandas as pd

warnings.filterwarnings('ignore')


def extract_features_stream(audio_path, segments, output_path, chunk_duration=300):
    """
    Extract features by loading audio in chunks to avoid memory issues.
    Only extracts for segments that fall within loaded chunks.
    """
    print(f"Processing {audio_path}...")
    
    # Get audio duration
    y_full, sr = librosa.load(audio_path, sr=16000, offset=0, duration=None)
    total_duration = len(y_full) / sr
    print(f"  Total duration: {total_duration:.1f}s")
    
    # Sort segments by start time
    segments = sorted(segments, key=lambda x: x['start'])
    
    # Process in chunks
    chunk_size = chunk_duration * sr  # 5 minutes
    features = []
    
    for chunk_start in range(0, len(y_full), chunk_size):
        chunk_end = min(chunk_start + chunk_size, len(y_full))
        y_chunk = y_full[chunk_start:chunk_end]
        
        # Find segments in this chunk
        for seg in segments:
            seg_start_sample = int(seg['start'] * sr)
            seg_end_sample = int(seg['end'] * sr)
            
            # Check if segment is in this chunk
            if seg_start_sample >= chunk_start and seg_end_sample <= chunk_end:
                # Extract features
                start_rel = seg_start_sample - chunk_start
                end_rel = seg_end_sample - chunk_start
                
                word_y = y_chunk[start_rel:end_rel]
                
                if len(word_y) < 512:
                    continue
                
                # F0
                try:
                    f0, voiced, _ = librosa.pyin(word_y[:sr*2], fmin=75, fmax=500, sr=sr)
                    voiced_f0 = f0[~np.isnan(f0)]
                    f0_mean = np.mean(voiced_f0) if len(voiced_f0) > 0 else 0
                    f0_std = np.std(voiced_f0) if len(voiced_f0) > 0 else 0
                except:
                    f0_mean, f0_std = 0, 0
                
                # Energy
                rms = np.mean(librosa.feature.rms(y=word_y, frame_length=512, hop_length=256)[0])
                
                features.append({
                    'video_id': seg.get('video_id', ''),
                    'word': seg.get('word', ''),
                    'start': seg['start'],
                    'end': seg['end'],
                    'label': seg.get('label', 0),
                    'f0_mean': f0_mean,
                    'f0_std': f0_std,
                    'rms_mean': rms,
                    'word_duration': seg['end'] - seg['start'],
                })
        
        # Progress
        print(f"  Chunk {chunk_start//sr//60:.0f}-{chunk_end//sr//60:.0f}min: {len(features)} features so far")
    
    return features


def main():
    parser = argparse.ArgumentParser(description='Stream prosody extraction')
    parser.add_argument('--aligned', default='data/audio_comedy/aligned_segments.jsonl',
                        help='Path to aligned segments')
    parser.add_argument('--audio-dir', default='data/audio_comedy/audio',
                        help='Audio directory')
    parser.add_argument('--output', default='data/audio_comedy/prosody_features.csv',
                        help='Output CSV')
    parser.add_argument('--limit', type=int, default=20, help='Max videos to process')
    args = parser.parse_args()
    
    print("Loading segments...")
    segments = []
    with open(args.aligned) as f:
        for line in f:
            try:
                segments.append(json.loads(line))
            except:
                pass
    print(f"Loaded {len(segments)} segments")
    
    # Group by video
    video_segs = defaultdict(list)
    for seg in segments:
        video_segs[seg['video_id']].append(seg)
    print(f"Unique videos: {len(video_segs)}")
    
    # Find audio files
    audio_files = {}
    for root, dirs, files in os.walk(args.audio_dir):
        for f in files:
            if f.endswith('.mp3'):
                vid = f.replace('.mp3', '')
                audio_files[vid] = os.path.join(root, f)
    print(f"Found {len(audio_files)} audio files")
    
    # Process limited videos
    all_features = []
    processed = 0
    
    for vid, segs in video_segs.items():
        if vid not in audio_files:
            continue
        
        try:
            feats = extract_features_stream(audio_files[vid], segs, None)
            all_features.extend(feats)
        except Exception as e:
            print(f"Error with {vid}: {e}")
        
        processed += 1
        if processed >= args.limit:
            break
        
        print(f"Progress: {processed}/{min(args.limit, len(video_segs))}")
    
    if all_features:
        df = pd.DataFrame(all_features)
        df.to_csv(args.output, index=False)
        print(f"\nSaved {len(df)} features to {args.output}")
        
        # Quick test
        from sklearn.linear_model import LogisticRegression
        from sklearn.metrics import f1_score
        
        feature_cols = ['f0_mean', 'f0_std', 'rms_mean', 'word_duration']
        X = df[feature_cols].fillna(0).values
        y = df['label'].values
        
        clf = LogisticRegression(max_iter=500, class_weight='balanced')
        clf.fit(X, y)
        pred = clf.predict(X)
        f1 = f1_score(y, pred)
        
        print(f"Train F1: {f1:.4f}")
    else:
        print("No features extracted!")


if __name__ == '__main__':
    main()