#!/usr/bin/env python3
"""
Background prosody extraction - processes videos one at a time with checkpointing.
Can be run with nohup or in background.

Usage:
    python3 training/extract_prosody_background.py --start 0 --end 50 &
"""

import argparse
import json
import os
import time
import pickle
from collections import defaultdict

import librosa
import numpy as np
import pandas as pd

import warnings
warnings.filterwarnings('ignore')

CHECKPOINT_FILE = 'data/audio_comedy/prosody_checkpoint.pkl'

def load_checkpoint():
    """Load checkpoint if exists."""
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, 'rb') as f:
            return pickle.load(f)
    return {'processed': [], 'features': []}

def save_checkpoint(checkpoint):
    """Save checkpoint."""
    with open(CHECKPOINT_FILE, 'wb') as f:
        pickle.dump(checkpoint, f)

def extract_features(y, sr, start, end, prev_end=None):
    """Extract F0, energy, pause features."""
    ctx = 0.1
    start_ctx = max(0, start - ctx)
    end_ctx = min(len(y)/sr, end + ctx)
    
    word_y = y[int(start_ctx*sr):int(end_ctx*sr)]
    if len(word_y) < 512:
        return None
    
    try:
        f0, voiced, _ = librosa.pyin(word_y, fmin=75, fmax=500, sr=sr)
        voiced_f0 = f0[~np.isnan(f0)]
        if len(voiced_f0) > 0:
            f0_mean = float(np.mean(voiced_f0))
            f0_std = float(np.std(voiced_f0))
            f0_range = float(np.max(voiced_f0) - np.min(voiced_f0))
        else:
            f0_mean, f0_std, f0_range = 0, 0, 0
    except:
        f0_mean, f0_std, f0_range = 0, 0, 0
    
    try:
        rms = float(np.mean(librosa.feature.rms(y=word_y, frame_length=512, hop_length=256)[0]))
    except:
        rms = 0
    
    pause = max(0, min(5, start - prev_end)) if prev_end else 0
    word_dur = end - start
    
    return {
        'f0_mean': f0_mean, 'f0_std': f0_std, 'f0_range': f0_range,
        'rms_mean': rms, 'pause_before': pause, 'word_duration': word_dur,
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--start', type=int, default=0)
    parser.add_argument('--end', type=int, default=50)
    parser.add_argument('--chunk-duration', type=int, default=300)
    args = parser.parse_args()
    
    print(f"Starting prosody extraction: videos {args.start} to {args.end}")
    
    # Load checkpoint
    checkpoint = load_checkpoint()
    processed = checkpoint['processed']
    all_features = checkpoint['features']
    print(f"Loaded checkpoint: {len(processed)} videos processed")
    
    # Load aligned segments
    print("Loading segments...")
    segments = []
    with open('data/audio_comedy/aligned_segments.jsonl') as f:
        for line in f:
            try:
                segments.append(json.loads(line))
            except:
                pass
    print(f"Loaded {len(segments)} segments")
    
    video_segs = defaultdict(list)
    for seg in segments:
        video_segs[seg['video_id']].append(seg)
    
    # Find audio files
    audio_files = {}
    for root, dirs, files in os.walk('data/audio_comedy/audio'):
        for f in files:
            if f.endswith('.mp3'):
                vid = f.replace('.mp3', '')
                audio_files[vid] = os.path.join(root, f)
    print(f"Found {len(audio_files)} audio files")
    
    # Get video list
    all_videos = [v for v in video_segs.keys() if v in audio_files]
    videos_to_process = all_videos[args.start:args.end]
    
    print(f"Processing videos {args.start} to {args.end} ({len(videos_to_process)} videos)")
    
    for i, vid in enumerate(videos_to_process):
        if vid in processed:
            continue
        
        try:
            audio_path = audio_files[vid]
            y, sr = librosa.load(audio_path, sr=16000, duration=args.chunk_duration)
            
            segs = sorted(video_segs[vid], key=lambda x: x['start'])
            prev_end = None
            
            for seg in segs:
                # Skip if beyond loaded chunk
                if seg['start'] > args.chunk_duration:
                    break
                
                feats = extract_features(y, sr, seg['start'], seg['end'], prev_end)
                if feats:
                    feats['video_id'] = vid
                    feats['word'] = seg.get('word', '')
                    feats['start'] = seg['start']
                    feats['end'] = seg['end']
                    feats['label'] = seg.get('label', 0)
                    all_features.append(feats)
                    prev_end = seg['end']
            
            processed.append(vid)
            
            # Save checkpoint every 5 videos
            if (i + 1) % 5 == 0:
                checkpoint = {'processed': processed, 'features': all_features}
                save_checkpoint(checkpoint)
                print(f"Progress: {i+1}/{len(videos_to_process)} - {len(all_features)} features")
        
        except Exception as e:
            print(f"Error with {vid}: {e}")
            continue
    
    # Final save
    checkpoint = {'processed': processed, 'features': all_features}
    save_checkpoint(checkpoint)
    
    # Save final CSV
    if all_features:
        df = pd.DataFrame(all_features)
        df.to_csv('data/audio_comedy/prosody_features.csv', index=False)
        print(f"\nSaved {len(df)} features to prosody_features.csv")
    
    print("Done!")

if __name__ == '__main__':
    main()
