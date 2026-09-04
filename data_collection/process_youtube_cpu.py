#!/usr/bin/env python3
"""
Process YouTube Comedy Dataset - CPU Version

This script:
1. Downloads metadata from GCS
2. Downloads audio from YouTube (using yt-dlp)
3. Extracts prosody features (CPU-friendly)
4. Creates aligned JSONL with labels
5. Saves incrementally per video

For WavLM embeddings, we save raw audio segments for later batch extraction.
"""

import os
import json
import subprocess
import numpy as np
import librosa
from pathlib import Path
from typing import List, Dict, Optional
from google.cloud import storage
import time

# ============================================================================
# CONFIGURATION
# ============================================================================

GCS_BUCKET = 'chuckle-net-youtube-20260616'
GCS_PROJECT = 'omniclaw-personal-assistant'
OUTPUT_DIR = '/Users/Subho/data/chuckle-net-youtube'
AUDIO_DIR = f'{OUTPUT_DIR}/audio'
PROCESSED_DIR = f'{OUTPUT_DIR}/processed'
MANIFEST_FILE = f'{OUTPUT_DIR}/manifest.json'

os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

# ============================================================================
# GCS UTILITIES
# ============================================================================

def get_gcs_bucket():
    client = storage.Client(project=GCS_PROJECT)
    return client.bucket(GCS_BUCKET)

def get_all_video_ids():
    """Get all video IDs from GCS metadata."""
    bucket = get_gcs_bucket()
    blobs = list(bucket.list_blobs(prefix='metadata/'))
    return [b.name.replace('metadata/', '').replace('.json', '') for b in blobs]

def download_metadata(video_id: str) -> Optional[Dict]:
    """Download metadata from GCS."""
    try:
        bucket = get_gcs_bucket()
        blob = bucket.blob(f'metadata/{video_id}.json')
        return json.loads(blob.download_as_string())
    except:
        return None

# ============================================================================
# AUDIO DOWNLOAD
# ============================================================================

def download_audio(video_id: str) -> Optional[str]:
    """Download audio from YouTube."""
    
    audio_path = os.path.join(AUDIO_DIR, f'{video_id}.wav')
    if os.path.exists(audio_path):
        return audio_path
    
    # Try GCS first
    try:
        bucket = get_gcs_bucket()
        blob = bucket.blob(f'audio/{video_id}.wav')
        blob.download_to_filename(audio_path)
        return audio_path
    except:
        pass
    
    # Download from YouTube
    cmd = [
        'yt-dlp',
        '-f', 'bestaudio',
        '--extract-audio',
        '--audio-format', 'wav',
        '--audio-quality', '0',
        '--output', f'{AUDIO_DIR}/{video_id}.%(ext)s',
        '--no-playlist',
        '--', f'https://www.youtube.com/watch?v={video_id}'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        
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
                    os.remove(downloaded)
                return audio_path
    except Exception as e:
        print(f"Download error: {e}")
    
    return None

# ============================================================================
# PROSODY FEATURES
# ============================================================================

def extract_prosody(audio_path: str, start: float, end: float) -> Optional[List[float]]:
    """Extract prosody features for a segment."""
    
    try:
        y, sr = librosa.load(audio_path, sr=16000, offset=start, duration=end-start)
        
        if len(y) < 400:
            return None
        
        # Basic energy
        rms = librosa.feature.rms(y=y)[0].mean()
        
        # Zero crossing rate
        zcr = librosa.feature.zero_crossing_rate(y=y)[0].mean()
        
        # Pitch
        pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
        pitch_max = pitches.max() / 1000
        pitch_mean = pitches[pitches > 0].mean() / 1000 if (pitches > 0).any() else 0
        
        # Spectral
        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0].mean() / 1000
        spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)[0].mean() / 1000
        
        # MFCCs
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        mfcc_mean = mfccs.mean(axis=1) / 100
        
        # Combine (21-dim like existing prosody) - convert to Python floats
        features = [
            float(rms), float(zcr), float(pitch_max), float(pitch_mean),
            float(spectral_centroid), float(spectral_bandwidth)
        ] + [float(x) for x in mfcc_mean]
        
        return features
        
    except Exception as e:
        print(f"Prosody error: {e}")
        return None

# ============================================================================
# PROCESS VIDEO
# ============================================================================

def process_video(video_id: str) -> Dict:
    """Process a single video."""
    
    output_file = os.path.join(PROCESSED_DIR, f'{video_id}.json')
    
    # Skip if already processed
    if os.path.exists(output_file):
        return {'status': 'already_processed', 'id': video_id}
    
    # Download metadata
    metadata = download_metadata(video_id)
    if not metadata:
        return {'status': 'metadata_failed', 'id': video_id}
    
    # Download audio
    audio_path = download_audio(video_id)
    if not audio_path:
        return {'status': 'audio_failed', 'id': video_id}
    
    print(f"Processing: {video_id}")
    
    # Get utterances with laughter labels
    utterances = []
    laughter_markers = metadata.get('laughter_markers', [])
    subtitle_utts = metadata.get('utterances', [])
    
    # Deduplicate laughter markers
    clean_laughter = []
    for m in laughter_markers:
        if not clean_laughter or m['start'] > clean_laughter[-1]['end']:
            clean_laughter.append(m)
    
    for i, utt in enumerate(subtitle_utts):
        start = utt['start']
        end = utt['end']
        text = utt['text']
        
        # Check if overlaps with laughter
        has_laughter = any(
            start < m['end'] and end > m['start']
            for m in clean_laughter
        )
        
        utterances.append({
            'utterance_id': f'{video_id}_{i:04d}',
            'video_id': video_id,
            'text': text,
            'start': start,
            'end': end,
            'duration': end - start,
            'label_any': 1 if has_laughter else 0,
            'label_majority': 1 if has_laughter else 0,
            'n_words': len(text.split()),
            'n_positive_words': sum(1 for _ in text.split() if 'laughter' in _.lower()),
        })
    
    # Extract prosody for each utterance
    prosody = {}
    prosody_dim = None
    
    for utt in utterances:
        uid = utt['utterance_id']
        pros = extract_prosody(audio_path, utt['start'], utt['end'])
        if pros is not None:
            prosody[uid] = pros
            prosody_dim = len(pros)
    
    # Save result
    result = {
        'video_id': video_id,
        'utterances': utterances,
        'prosody': prosody,
        'prosody_dim': prosody_dim or 0,
        'n_total': len(utterances),
        'n_positive': sum(u['label_any'] for u in utterances),
        'n_prosody': len(prosody),
        'status': 'success',
    }
    
    with open(output_file, 'w') as f:
        json.dump(result, f)
    
    # Update manifest
    update_manifest(video_id, audio_path)
    
    return result

def update_manifest(video_id: str, audio_path: str):
    """Update the manifest file."""
    manifest = {}
    if os.path.exists(MANIFEST_FILE):
        with open(MANIFEST_FILE) as f:
            manifest = json.load(f)
    
    manifest[video_id] = {
        'audio_path': audio_path,
        'processed_file': os.path.join(PROCESSED_DIR, f'{video_id}.json'),
        'processed': True,
    }
    
    with open(MANIFEST_FILE, 'w') as f:
        json.dump(manifest, f, indent=2)

# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=== YouTube Comedy Dataset Processing (CPU) ===\n")
    
    # Get all video IDs from GCS
    video_ids = get_all_video_ids()
    print(f"Total videos in GCS: {len(video_ids)}")
    
    # Check already processed (by checking actual files)
    processed_files = set()
    if os.path.exists(PROCESSED_DIR):
        processed_files = set(
            f.replace('.json', '')
            for f in os.listdir(PROCESSED_DIR)
            if f.endswith('.json')
        )
    
    to_process = [v for v in video_ids if v not in processed_files]
    print(f"Already processed: {len(processed_files)}")
    print(f"To process: {len(to_process)}")
    
    if not to_process:
        print("Nothing to process!")
        return
    
    # Process each video - SIMPLE approach, no resume from checkpoint
    # If it stops, just re-run and it will skip already-processed files
    checkpoint_file = f'{OUTPUT_DIR}/checkpoint.json'
    results = []
    
    for i, vid in enumerate(to_process):
        print(f"\n[{i+1}/{len(to_process)}] Processing {vid}...")
        
        result = process_video(vid)
        results.append(result)
        
        status = result['status']
        if status == 'success':
            n_utt = result.get('n_total', 0)
            n_pos = result.get('n_positive', 0)
            n_pro = result.get('n_prosody', 0)
            print(f"  ✓ {vid}: {n_utt} utt, {n_pos} pos, {n_pro} prosody")
            
            # Save checkpoint with ONLY successful videos
            checkpoint = {
                'last_success_index': i,
                'total_processed': len(processed_files) + len([r for r in results if r['status'] == 'success']),
                'last_video': vid,
            }
            with open(checkpoint_file, 'w') as f:
                json.dump(checkpoint, f)
        elif status == 'already_processed':
            print(f"  ○ {vid}: already done")
        else:
            print(f"  ✗ {vid}: {status} - continuing...")
    
    # Summary
    success = [r for r in results if r['status'] == 'success']
    total_utts = sum(r.get('n_total', 0) for r in success)
    total_pos = sum(r.get('n_positive', 0) for r in success)
    total_pro = sum(r.get('n_prosody', 0) for r in success)
    
    print(f"\n=== FINAL SUMMARY ===")
    print(f"Processed: {len(success)}/{len(to_process)}")
    print(f"Total utterances: {total_utts}")
    print(f"Positive: {total_pos} ({total_pos/max(total_utts,1)*100:.1f}%)")
    print(f"Total prosody: {total_pro}")
    print(f"Output dir: {PROCESSED_DIR}")

if __name__ == '__main__':
    main()
