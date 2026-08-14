#!/usr/bin/env python3
"""
Parallel Video Processor
========================
Processes collected videos in parallel using multiple threads.
Extracts prosody features and optionally WavLM embeddings.

Usage:
    python3 parallel_processor.py --parallel 4 --wavlm
"""

import os
import sys
import json
import time
import subprocess
import argparse
import threading
import queue
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Add project to path
sys.path.insert(0, '/Users/Subho/autonomous_laughter_prediction')

# ============================================================================
# PATHS
# ============================================================================

PROCESSED_DIR = '/Users/Subho/data/chuckle-net-youtube/processed'
WAVLM_DIR = '/Users/Subho/data/chuckle-net-youtube/wavlm_embeddings'
AUDIO_DIR = '/Users/Subho/data/chuckle-net-youtube/audio'
CHECKPOINT = '/Users/Subho/data/chuckle-net-youtube/collection_checkpoint.json'

os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(WAVLM_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)

# ============================================================================
# AUDIO DOWNLOAD
# ============================================================================

def download_audio(video_id: str) -> Optional[str]:
    """Download audio from YouTube using yt-dlp."""
    audio_path = os.path.join(AUDIO_DIR, f'{video_id}.wav')
    
    if os.path.exists(audio_path):
        return audio_path
    
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
        
        # Find downloaded file
        for f in os.listdir(AUDIO_DIR):
            if video_id in f and f.endswith('.wav'):
                downloaded = os.path.join(AUDIO_DIR, f)
                if downloaded != audio_path:
                    # Convert to 16kHz mono
                    subprocess.run([
                        'ffmpeg', '-i', downloaded,
                        '-ar', '16000', '-ac', '1',
                        audio_path, '-y'
                    ], capture_output=True, timeout=300)
                    try:
                        os.remove(downloaded)
                    except:
                        pass
                return audio_path
    except Exception as e:
        print(f"Download error: {e}")
    
    return None

# ============================================================================
# PROSODY EXTRACTION
# ============================================================================

def extract_prosody(audio_path: str, utterances: List[Dict]) -> List[Dict]:
    """Extract prosody features for utterances."""
    import numpy as np
    try:
        import librosa
    except ImportError:
        print("  librosa not available")
        return []
    
    features_list = []
    
    for utt in utterances:
        start = utt['start']
        end = utt['end']
        
        try:
            y, sr = librosa.load(audio_path, sr=16000, offset=start, duration=end-start)
            
            if len(y) < 400:  # Skip too short
                continue
            
            # Extract features
            rms = np.sqrt(np.mean(y**2))
            zcr = np.mean(librosa.feature.zero_crossing_rate(y))
            
            try:
                pitch = librosa.yin(y, fmin=50, fmax=500, sr=sr)
                pitch_mean = np.mean(pitch)
                pitch_std = np.std(pitch)
                pitch_range = np.max(pitch) - np.min(pitch)
            except:
                pitch_mean = pitch_std = pitch_range = 0
            
            mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            mfcc_means = np.mean(mfccs, axis=1)
            
            feats = [
                rms, zcr, pitch_mean, pitch_std, pitch_range,
                utt['duration'], utt.get('n_words', 0),
            ] + mfcc_means.tolist()
            
            features_list.append({
                'uid': f"{utt['video_id']}_{utt['start']:.2f}",
                'feats': feats
            })
            
        except Exception as e:
            continue
    
    return features_list

# ============================================================================
# VIDEO PROCESSOR
# ============================================================================

def process_video(video_id: str, checkpoint: Dict, extract_wavlm: bool = False) -> Dict:
    """Process a single video: download audio, extract prosody."""
    result = {
        'video_id': video_id,
        'timestamp': datetime.now().isoformat(),
        'status': 'unknown'
    }
    
    meta_path = os.path.join(PROCESSED_DIR, f'{video_id}.json')
    
    # Check if already processed
    if os.path.exists(meta_path):
        with open(meta_path) as f:
            existing = json.load(f)
        result['status'] = 'already_processed'
        result['utterances'] = existing.get('n_total', 0)
        return result
    
    # Download audio
    print(f"  Downloading {video_id}...")
    audio_path = download_audio(video_id)
    
    if not audio_path:
        result['status'] = 'download_failed'
        return result
    
    # Load metadata
    if not os.path.exists(meta_path):
        result['status'] = 'no_metadata'
        return result
    
    with open(meta_path) as f:
        meta = json.load(f)
    
    utterances = meta.get('utterances', [])
    
    if not utterances:
        result['status'] = 'no_utterances'
        return result
    
    # Extract prosody
    print(f"  Extracting prosody for {len(utterances)} utterances...")
    prosody_feats = extract_prosody(audio_path, utterances)
    
    if prosody_feats:
        # Save prosody
        prosody_path = os.path.join(PROCESSED_DIR, f'{video_id}_prosody.json')
        with open(prosody_path, 'w') as f:
            json.dump(prosody_feats, f)
        
        # Update metadata
        meta['prosody_extracted'] = True
        meta['prosody_features'] = len(prosody_feats)
        
        with open(meta_path, 'w') as f:
            json.dump(meta, f)
        
        result['prosody_features'] = len(prosody_feats)
    
    # WavLM extraction (optional, CPU-only)
    if extract_wavlm:
        print(f"  WavLM extraction skipped (CPU too slow, need GPU)")
        # TODO: Implement when GPU available
    
    result['status'] = 'processed'
    result['utterances'] = len(utterances)
    
    return result

# ============================================================================
# PARALLEL PROCESSOR
# ============================================================================

def processor_worker(worker_id: int, video_ids: List[str], checkpoint: Dict, 
                     extract_wavlm: bool, results_queue: queue.Queue):
    """Worker that processes assigned videos."""
    print(f"[Processor {worker_id}] Starting with {len(video_ids)} videos")
    
    for video_id in video_ids:
        result = process_video(video_id, checkpoint, extract_wavlm)
        
        if result['status'] == 'processed':
            checkpoint['processed_videos'][video_id] = result
            checkpoint['total_processed'] += 1
            results_queue.put(('processed', video_id, result))
        elif result['status'] == 'already_processed':
            results_queue.put(('already', video_id, result))
        else:
            checkpoint['failed_videos'][video_id] = result
            results_queue.put(('failed', video_id, result))
        
        # Save checkpoint periodically
        if checkpoint['total_processed'] % 10 == 0:
            save_checkpoint(checkpoint)
    
    print(f"[Processor {worker_id}] Done")
    results_queue.put(('worker_done', worker_id, None))

def save_checkpoint(cp: Dict):
    """Save checkpoint."""
    with open(CHECKPOINT, 'w') as f:
        json.dump(cp, f, indent=2)

# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='Parallel Video Processor')
    parser.add_argument('--parallel', type=int, default=4, help='Number of parallel processors')
    parser.add_argument('--wavlm', action='store_true', help='Also extract WavLM (CPU, slow)')
    args = parser.parse_args()
    
    print("=" * 70)
    print("PARALLEL VIDEO PROCESSOR")
    print("=" * 70)
    
    # Load checkpoint
    if os.path.exists(CHECKPOINT):
        with open(CHECKPOINT) as f:
            checkpoint = json.load(f)
    else:
        checkpoint = {'collected_videos': {}, 'processed_videos': {}, 'failed_videos': {}}
    
    # Get videos to process
    all_collected = set(checkpoint.get('collected_videos', {}).keys())
    all_processed = set(checkpoint.get('processed_videos', {}).keys())
    
    to_process = [v for v in all_collected if v not in all_processed]
    
    print(f"\nCollected: {len(all_collected)}")
    print(f"Processed: {len(all_processed)}")
    print(f"To process: {len(to_process)}")
    
    if not to_process:
        print("Nothing to process!")
        return
    
    # Split among workers
    videos_per_worker = len(to_process) // args.parallel + 1
    video_chunks = []
    for i in range(args.parallel):
        start = i * videos_per_worker
        end = start + videos_per_worker
        video_chunks.append(to_process[start:end])
    
    print(f"\nSplit {len(to_process)} videos into {args.parallel} workers")
    
    # Results queue
    results_queue = queue.Queue()
    
    # Start workers
    threads = []
    for i, videos in enumerate(video_chunks):
        if not videos:
            continue
        t = threading.Thread(target=processor_worker, 
                           args=(i, videos, checkpoint, args.wavlm, results_queue))
        t.start()
        threads.append(t)
        print(f"Started processor {i} with {len(videos)} videos")
    
    # Monitor progress
    last_count = checkpoint['total_processed']
    while any(t.is_alive() for t in threads):
        time.sleep(5)
        current = checkpoint['total_processed']
        if current != last_count:
            print(f"  Progress: {current} processed")
            last_count = current
    
    # Wait for completion
    for t in threads:
        t.join()
    
    # Final stats
    print("\n" + "=" * 70)
    print("PROCESSING COMPLETE")
    print("=" * 70)
    print(f"Total processed: {checkpoint['total_processed']}")

if __name__ == '__main__':
    main()
