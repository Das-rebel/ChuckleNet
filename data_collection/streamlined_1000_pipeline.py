#!/usr/bin/env python3
"""
Streamlined 1000 Video Collection Pipeline
==========================================
1. Fast scrape YouTube for comedy videos (done - 709 candidates)
2. Download audio and extract prosody (CPU)
3. Use trained model to predict laughter
4. Keep only high-confidence predictions

This replaces the [laughter] marker approach with model-based prediction.
"""

import os
import sys
import json
import subprocess
import time
import glob
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# ============================================================================
# PATHS
# ============================================================================

CANDIDATE_FILE = '/Users/Subho/data/chuckle-net-youtube/candidates/all_candidates.jsonl'
COLLECTED_DIR = '/Users/Subho/data/chuckle-net-youtube/collected'
PROCESSED_DIR = '/Users/Subho/data/chuckle-net-youtube/processed'
AUDIO_DIR = '/Users/Subho/data/chuckle-net-youtube/audio'
PROSODY_DIR = '/Users/Subho/data/chuckle-net-youtube/prosody'

for d in [COLLECTED_DIR, PROCESSED_DIR, AUDIO_DIR, PROSODY_DIR]:
    os.makedirs(d, exist_ok=True)

# ============================================================================
# LOAD CANDIDATES
# ============================================================================

def load_candidates() -> List[Dict]:
    candidates = []
    with open(CANDIDATE_FILE) as f:
        for line in f:
            try:
                candidates.append(json.loads(line.strip()))
            except:
                pass
    return candidates

# ============================================================================
# DOWNLOAD AUDIO
# ============================================================================

def download_audio(video_id: str) -> bool:
    """Download audio from YouTube using yt-dlp."""
    output_path = os.path.join(AUDIO_DIR, f'{video_id}.wav')
    
    if os.path.exists(output_path):
        return True
    
    # Try yt-dlp first
    cmd = [
        'yt-dlp',
        '-f', 'bestaudio',
        '--extract-audio',
        '--audio-format', 'wav',
        '--audio-quality', '0',
        '--output', f'{AUDIO_DIR}/{video_id}.%(ext)s',
        '--no-playlist',
        '--cookies-from-browser', 'chrome',
        '--', f'https://www.youtube.com/watch?v={video_id}'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        # Find and convert
        for f in os.listdir(AUDIO_DIR):
            if video_id in f and f.endswith(('.m4a', '.webm', '.mp3')):
                src = os.path.join(AUDIO_DIR, f)
                subprocess.run([
                    'ffmpeg', '-i', src,
                    '-ar', '16000', '-ac', '1',
                    output_path, '-y'
                ], capture_output=True, timeout=300)
                try:
                    os.remove(src)
                except:
                    pass
                return os.path.exists(output_path)
        
        return os.path.exists(output_path)
        
    except Exception as e:
        return False

# ============================================================================
# EXTRACT PROSODY (CPU)
# ============================================================================

def extract_prosody(video_id: str) -> bool:
    """Extract prosody features using librosa."""
    import numpy as np
    try:
        import librosa
    except ImportError:
        return False
    
    audio_path = os.path.join(AUDIO_DIR, f'{video_id}.wav')
    prosody_path = os.path.join(PROSODY_DIR, f'{video_id}.json')
    
    if not os.path.exists(audio_path):
        return False
    
    if os.path.exists(prosody_path):
        return True
    
    try:
        # Load audio
        y, sr = librosa.load(audio_path, sr=16000)
        duration = len(y) / sr
        
        # Segment into ~3 second utterances
        segment_duration = 3.0
        hop_length = sr  # 1 second hop
        
        utterances = []
        start = 0.0
        
        while start < duration - segment_duration:
            end = start + segment_duration
            y_seg = y[int(start * sr):int(end * sr)]
            
            if len(y_seg) < sr:  # Less than 1 second
                break
            
            # Extract features
            rms = np.sqrt(np.mean(y_seg**2))
            zcr = np.mean(librosa.feature.zero_crossing_rate(y_seg))
            
            try:
                pitch = librosa.yin(y_seg, fmin=50, fmax=500, sr=sr)
                pitch_mean = np.mean(pitch)
                pitch_std = np.std(pitch)
            except:
                pitch_mean = pitch_std = 0
            
            mfccs = librosa.feature.mfcc(y=y_seg, sr=sr, n_mfcc=13)
            mfcc_means = np.mean(mfccs, axis=1)
            
            feats = [
                float(rms), float(zcr), float(pitch_mean), float(pitch_std),
                float(segment_duration), 0,  # duration, n_words
            ] + [float(x) for x in mfcc_means]
            
            # Pad to 21 dimensions
            while len(feats) < 21:
                feats.append(0)
            
            utterances.append({
                'uid': f'{video_id}_{len(utterances):04d}',
                'video_id': video_id,
                'start': float(start),
                'end': float(end),
                'duration': float(segment_duration),
                'prosody': feats[:21]
            })
            
            start += hop_length
        
        # Save
        with open(prosody_path, 'w') as f:
            json.dump({
                'video_id': video_id,
                'utterances': utterances,
                'n_total': len(utterances),
                'extracted_at': datetime.now().isoformat()
            }, f)
        
        return True
        
    except Exception as e:
        return False

# ============================================================================
# PROCESS VIDEO
# ============================================================================

def process_video(video_id: str) -> Dict:
    """Process a single video: download + extract prosody."""
    result = {
        'video_id': video_id,
        'status': 'unknown',
        'steps': {}
    }
    
    # Step 1: Download audio
    if download_audio(video_id):
        result['steps']['audio'] = 'success'
    else:
        result['steps']['audio'] = 'failed'
        result['status'] = 'audio_failed'
        return result
    
    # Step 2: Extract prosody
    if extract_prosody(video_id):
        result['steps']['prosody'] = 'success'
        result['status'] = 'complete'
    else:
        result['steps']['prosody'] = 'failed'
        result['status'] = 'prosody_failed'
    
    return result

# ============================================================================
# BATCH PROCESS
# ============================================================================

def batch_process(video_ids: List[str], batch_size: int = 50) -> Dict:
    """Process a batch of videos."""
    results = {
        'success': 0,
        'failed': 0,
        'already_done': 0,
        'details': []
    }
    
    for i, vid in enumerate(video_ids):
        # Check if already processed
        prosody_path = os.path.join(PROSODY_DIR, f'{vid}.json')
        if os.path.exists(prosody_path):
            results['already_done'] += 1
            continue
        
        # Process
        result = process_video(vid)
        
        if result['status'] == 'complete':
            results['success'] += 1
        else:
            results['failed'] += 1
        
        results['details'].append(result)
        
        if (i + 1) % 10 == 0:
            print(f"  Progress: {i+1}/{len(video_ids)} | Success: {results['success']} | Failed: {results['failed']}")
    
    return results

# ============================================================================
# MAIN
# ============================================================================

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=100, help='Limit videos to process')
    args = parser.parse_args()
    
    print("=" * 70)
    print("STREAMLINED 1000 VIDEO PIPELINE")
    print("=" * 70)
    
    # Load candidates
    candidates = load_candidates()
    print(f"Total candidates: {len(candidates)}")
    
    # Get video IDs
    all_ids = [c['video_id'] for c in candidates]
    
    # Filter out already processed
    processed = set()
    for f in glob.glob(f'{PROSODY_DIR}/*.json'):
        vid = os.path.basename(f)[:-5]
        processed.add(vid)
    
    to_process = [vid for vid in all_ids if vid not in processed]
    print(f"Already processed: {len(processed)}")
    print(f"To process: {len(to_process)}")
    
    if args.limit > 0 and args.limit < len(to_process):
        to_process = to_process[:args.limit]
        print(f"Limited to: {args.limit}")
    
    if not to_process:
        print("Nothing to process!")
        return
    
    print(f"\nProcessing {len(to_process)} videos...")
    
    # Process
    start_time = time.time()
    results = batch_process(to_process)
    
    elapsed = time.time() - start_time
    
    # Summary
    print("\n" + "=" * 70)
    print("PROCESSING COMPLETE")
    print("=" * 70)
    print(f"Success: {results['success']}")
    print(f"Failed: {results['failed']}")
    print(f"Already done: {results['already_done']}")
    print(f"Time: {elapsed/60:.1f} min ({elapsed/len(to_process):.1f} sec/video)")
    
    # Count total utterances
    total_utts = 0
    for f in glob.glob(f'{PROSODY_DIR}/*.json'):
        try:
            with open(f) as fp:
                data = json.load(fp)
                total_utts += data.get('n_total', 0)
        except:
            pass
    
    print(f"\nTotal utterances collected: {total_utts:,}")

if __name__ == '__main__':
    main()
