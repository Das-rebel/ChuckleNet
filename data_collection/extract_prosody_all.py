#!/usr/bin/env python3
"""
Extract Prosody for ALL YouTube Audio Files
========================================
"""

import os
import sys
import json
import glob
import numpy as np
import librosa
from datetime import datetime

AUDIO_DIR = '/Users/Subho/data/chuckle-net-youtube/audio'
PROSODY_DIR = '/Users/Subho/data/chuckle-net-youtube/prosody'
os.makedirs(PROSODY_DIR, exist_ok=True)

def extract_prosody(audio_path: str, video_id: str) -> dict:
    """Extract 21-dim prosody features."""
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
        
        return {
            'video_id': video_id,
            'duration': duration,
            'utterances': utterances,
            'n_total': len(utterances),
            'extracted_at': datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"Error extracting {video_id}: {e}")
        return None

def main():
    print("="*70)
    print("EXTRACTING PROSODY FOR ALL YOUTUBE AUDIO")
    print("="*70)
    
    # Get audio files
    audio_files = glob.glob(f'{AUDIO_DIR}/*.wav')
    print(f"Audio files: {len(audio_files)}")
    
    # Get already processed
    prosody_ids = set(os.path.basename(f)[:-5] for f in glob.glob(f'{PROSODY_DIR}/*.json'))
    print(f"Already processed: {len(prosody_ids)}")
    
    to_process = [f for f in audio_files 
                   if os.path.basename(f)[:-4] not in prosody_ids]
    print(f"To process: {len(to_process)}")
    
    if not to_process:
        print("Nothing to process!")
        return
    
    # Process
    success = 0
    failed = 0
    total_utts = 0
    
    for i, audio_path in enumerate(to_process):
        vid = os.path.basename(audio_path)[:-4]
        
        result = extract_prosody(audio_path, vid)
        
        if result:
            # Save
            with open(f'{PROSODY_DIR}/{vid}.json', 'w') as f:
                json.dump(result, f)
            
            success += 1
            total_utts += result.get('n_total', 0)
        else:
            failed += 1
        
        if (i + 1) % 20 == 0:
            print(f"  Progress: {i+1}/{len(to_process)} | Success: {success} | Failed: {failed} | Utts: {total_utts}")
    
    print(f"\n{'='*70}")
    print(f"COMPLETE: {success} success, {failed} failed")
    print(f"Total utterances extracted: {total_utts:,}")
    print(f"{'='*70}")

if __name__ == '__main__':
    main()
