#!/usr/bin/env python3
"""
Extract Prosody for YouTube Audio
================================
Extracts 21-dim prosody features from YouTube audio files.
"""

import os
import sys
import json
import glob
import numpy as np
from datetime import datetime

# Try librosa, fallback to custom
try:
    import librosa
    HAS_LIBROSA = True
except ImportError:
    HAS_LIBROSA = False
    print("librosa not available, will use alternative")

# Paths
AUDIO_DIR = '/Users/Subho/data/chuckle-net-youtube/audio'
PROSODY_DIR = '/Users/Subho/data/chuckle-net-youtube/prosody'
PROCESSED_DIR = '/Users/Subho/data/chuckle-net-youtube/processed'
OUTPUT_FILE = '/Users/Subho/data/chuckle-net-unified/prosody_youtube.jsonl'

os.makedirs(PROSODY_DIR, exist_ok=True)

def extract_prosody(audio_path: str, video_id: str) -> list:
    """Extract 21-dim prosody features from audio file."""
    
    if HAS_LIBROSA:
        try:
            # Load audio
            y, sr = librosa.load(audio_path, sr=16000)
            duration = len(y) / sr
            
            # Segment into ~3 second utterances
            segment_duration = 3.0
            hop_length = 1.0  # 1 second hop
            
            utterances = []
            start = 0.0
            seg_idx = 0
            
            while start < duration - segment_duration:
                end = start + segment_duration
                y_seg = y[int(start * sr):int(end * sr)]
                
                if len(y_seg) < sr:
                    break
                
                # Extract features
                rms = float(np.sqrt(np.mean(y_seg**2)))
                zcr = float(np.mean(librosa.feature.zero_crossing_rate(y_seg)))
                
                try:
                    pitch = librosa.yin(y_seg, fmin=50, fmax=500, sr=sr)
                    pitch_mean = float(np.mean(pitch))
                    pitch_std = float(np.std(pitch))
                    pitch_range = float(np.max(pitch) - np.min(pitch))
                except:
                    pitch_mean = pitch_std = pitch_range = 0.0
                
                mfccs = librosa.feature.mfcc(y=y_seg, sr=sr, n_mfcc=13)
                mfcc_means = [float(np.mean(mfccs[i])) for i in range(13)]
                
                # Build 21-dim feature vector
                feats = [rms, zcr, pitch_mean, pitch_std, pitch_range, segment_duration, 0] + mfcc_means
                
                # Pad to 21
                while len(feats) < 21:
                    feats.append(0.0)
                
                uid = f'{video_id}_{seg_idx:04d}'
                utterances.append({
                    'uid': uid,
                    'video_id': video_id,
                    'start': start,
                    'end': end,
                    'duration': segment_duration,
                    'prosody': feats[:21]
                })
                
                start += hop_length
                seg_idx += 1
            
            return utterances
            
        except Exception as e:
            print(f"Error extracting {video_id}: {e}")
            return []
    else:
        return []

def main():
    print("="*70)
    print("EXTRACTING PROSODY FOR YOUTUBE AUDIO")
    print("="*70)
    
    # Get audio files
    audio_files = glob.glob(f'{AUDIO_DIR}/*.wav')
    print(f"Audio files: {len(audio_files)}")
    
    # Get already processed
    processed = set(os.path.basename(f)[:-4] for f in glob.glob(f'{PROSODY_DIR}/*.json'))
    print(f"Already processed: {len(processed)}")
    
    to_process = [f for f in audio_files if os.path.basename(f)[:-4] not in processed]
    print(f"To process: {len(to_process)}")
    
    if not to_process:
        print("Nothing to process!")
        return
    
    # Check disk space
    import shutil
    free = shutil.disk_usage('/').free / 1e9
    print(f"Free disk: {free:.1f}GB")
    
    all_prosody = []
    
    for i, audio_path in enumerate(to_process[:100]):  # Process 100 at a time
        vid = os.path.basename(audio_path)[:-4]
        
        print(f"  Processing {vid} ({i+1}/{len(to_process[:100])})...")
        
        utts = extract_prosody(audio_path, vid)
        
        if utts:
            # Save individual file
            with open(f'{PROSODY_DIR}/{vid}.json', 'w') as f:
                json.dump({'video_id': vid, 'utterances': utts}, f)
            
            # Add to all
            all_prosody.extend(utts)
            
            print(f"    Extracted {len(utts)} utterances")
    
    # Save combined
    with open(OUTPUT_FILE, 'w') as f:
        for p in all_prosody:
            f.write(json.dumps(p) + '\n')
    
    print(f"\nSaved {len(all_prosody)} prosody entries to {OUTPUT_FILE}")
    print("="*70)

if __name__ == '__main__':
    main()
