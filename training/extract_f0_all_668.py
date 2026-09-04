#!/usr/bin/env python3
"""
Extract F0 (5 features) for ALL 668 videos using utterance-level segments.
Uses librosa.yin (10x faster than pyin) on short segments.
Outputs: data/prosody_aligned/f0_668_videos.npz
"""
import json
import os
import time
import numpy as np
import librosa
from pathlib import Path
from collections import defaultdict

SR = 16000
CHECKPOINT_PATH = 'data/prosody_aligned/f0_668_checkpoint.json'
OUTPUT_PATH = 'data/prosody_aligned/f0_668_videos.npz'

def extract_f0_5dim(y, sr=SR):
    """Extract 5 F0 features from audio segment."""
    if len(y) < sr * 0.1:  # Too short
        return np.zeros(5, dtype=np.float32)
    
    try:
        # Use yin (much faster than pyin)
        f0 = librosa.yin(y, fmin=50, fmax=500, sr=sr)
        f0_clean = f0[f0 > 0]  # Remove unvoiced (yin returns 0 for unvoiced)
        
        if len(f0_clean) == 0:
            return np.zeros(5, dtype=np.float32)
        
        voiced_rate = len(f0_clean) / len(f0)
        
        return np.array([
            np.mean(f0_clean),
            np.std(f0_clean),
            np.max(f0_clean),
            np.min(f0_clean),
            voiced_rate
        ], dtype=np.float32)
    except:
        return np.zeros(5, dtype=np.float32)

def find_audio_file(vid, audio_dirs):
    """Find audio file for video ID."""
    for d in audio_dirs:
        for ext in ['.m4a', '.mp3', '.wav', '.webm']:
            p = os.path.join(d, f'{vid}{ext}')
            if os.path.exists(p):
                return p
    return None

def main():
    print("=" * 70)
    print("F0 EXTRACTION: ALL 668 videos (utterance-level, librosa.yin)")
    print("=" * 70)
    
    # Load utterances
    with open('data/utterances/utterances_clean.jsonl') as f:
        utterances = [json.loads(l) for l in f]
    
    # Group by video
    utts_by_video = defaultdict(list)
    for u in utterances:
        utts_by_video[u['video_id']].append(u)
    
    print(f"Total videos: {len(utts_by_video)}")
    print(f"Total utterances: {len(utterances):,}")
    
    # Audio directories
    audio_dirs = [
        '/Users/Subho/data/utterances/vtt_audio_local',
        'data/utterances/audio',
    ]
    
    # Load checkpoint
    checkpoint = {}
    if os.path.exists(CHECKPOINT_PATH):
        with open(CHECKPOINT_PATH) as f:
            checkpoint = json.load(f)
        print(f"Checkpoint: {len(checkpoint)} videos already processed")
    
    # Process all videos
    all_features = {}
    all_labels = {}
    all_uids = {}
    failed = []
    
    videos = sorted(utts_by_video.keys())
    t0 = time.time()
    
    for vi, vid in enumerate(videos):
        if vid in checkpoint:
            all_features[vid] = np.array(checkpoint[vid]['features'], dtype=np.float32)
            all_labels[vid] = np.array(checkpoint[vid]['labels'])
            all_uids[vid] = checkpoint[vid]['uids']
            continue
        
        audio_path = find_audio_file(vid, audio_dirs)
        if not audio_path:
            failed.append(vid)
            continue
        
        try:
            # Load full audio
            y, sr = librosa.load(audio_path, sr=SR, mono=True)
            
            # Extract F0 for each utterance
            features = []
            labels = []
            uids = []
            
            for u in utts_by_video[vid]:
                start = u['start']
                end = u['end']
                
                start_sample = int(start * SR)
                end_sample = int(end * SR)
                
                if end_sample > len(y):
                    end_sample = len(y)
                
                segment = y[start_sample:end_sample]
                
                f0_feat = extract_f0_5dim(segment, SR)
                features.append(f0_feat)
                labels.append(u.get('label', 0))
                uids.append(f"{vid}_{start:.3f}")
            
            all_features[vid] = np.array(features, dtype=np.float32)
            all_labels[vid] = np.array(labels)
            all_uids[vid] = uids
            
            checkpoint[vid] = {
                'features': [f.tolist() if hasattr(f, 'tolist') else f for f in features],
                'labels': [int(l) for l in labels],
                'uids': uids
            }
            
        except Exception as e:
            print(f"  Error {vid}: {e}")
            failed.append(vid)
        
        # Progress
        if (vi + 1) % 25 == 0:
            elapsed = time.time() - t0
            done = len(all_features)
            rate = done / max(elapsed, 1)
            eta = (len(videos) - done) / max(rate, 0.1)
            print(f"  {done}/{len(videos)} videos | {rate:.1f}/s | ETA: {eta/60:.1f} min | Failed: {len(failed)}")
            
            # Save checkpoint
            with open(CHECKPOINT_PATH, 'w') as f:
                json.dump(checkpoint, f)
    
    # Save final checkpoint
    with open(CHECKPOINT_PATH, 'w') as f:
        json.dump(checkpoint, f)
    
    # Combine all features
    print(f"\n{'='*70}")
    print(f"DONE: {len(all_features)} videos extracted")
    print(f"Failed: {len(failed)}")
    print(f"Time: {(time.time()-t0)/60:.1f} min")
    
    # Save as NPZ
    all_X = []
    all_y = []
    all_u = []
    for vid in all_features:
        all_X.append(all_features[vid])
        all_y.append(all_labels[vid])
        all_u.extend(all_uids[vid])
    
    X = np.vstack(all_X)
    y = np.concatenate(all_y)
    u = np.array(all_u)
    
    np.savez(OUTPUT_PATH, features=X, labels=y, uids=u)
    print(f"\nSaved: {OUTPUT_PATH}")
    print(f"Total: {len(y):,} utterances from {len(all_features)} videos")
    print(f"Positive: {y.sum():,} ({y.mean()*100:.1f}%)")

if __name__ == '__main__':
    main()
