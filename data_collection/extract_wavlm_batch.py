#!/usr/bin/env python3
"""
Download audio + Extract WavLM embeddings for all 100 YouTube videos.
Runs in background with incremental saves.
"""

import os
import sys
import json
import subprocess
import numpy as np
from pathlib import Path
from typing import Dict, Optional, List
from google.cloud import storage
import time

# Add project to path
sys.path.insert(0, '/Users/Subho/autonomous_laughter_prediction')

# ============================================================================
# PATHS
# ============================================================================

GCS_PROJECT = 'omniclaw-personal-assistant'
GCS_BUCKET = 'chuckle-net-youtube-20260616'
PROCESSED_DIR = '/Users/Subho/data/chuckle-net-youtube/processed'
WAVLM_DIR = '/Users/Subho/data/chuckle-net-youtube/wavlm_embeddings'
AUDIO_DIR = '/Users/Subho/data/chuckle-net-youtube/audio'
CHECKPOINT_FILE = '/Users/Subho/data/chuckle-net-youtube/wavlm_checkpoint.json'

os.makedirs(WAVLM_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)

# ============================================================================
# GCS
# ============================================================================

def get_gcs_bucket():
    client = storage.Client(project=GCS_PROJECT)
    return client.bucket(GCS_BUCKET)

# ============================================================================
# DOWNLOAD AUDIO
# ============================================================================

def download_audio(video_id: str) -> Optional[str]:
    """Download audio from YouTube using yt-dlp."""
    
    audio_path = os.path.join(AUDIO_DIR, f'{video_id}.wav')
    if os.path.exists(audio_path):
        return audio_path
    
    # Try GCS first
    try:
        bucket = get_gcs_bucket()
        blob = bucket.blob(f'audio/{video_id}.wav')
        if blob.exists():
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
        '--cookies-from-browser', 'chrome',  # Use Chrome cookies for auth
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
                    try:
                        os.remove(downloaded)
                    except:
                        pass
                return audio_path
    except Exception as e:
        print(f"Download error: {e}")
    
    return None

# ============================================================================
# WAVE LM EXTRACTION
# ============================================================================

def extract_wavlm(audio_path: str, utterances: List[Dict]) -> Dict[str, np.ndarray]:
    """Extract WavLM embeddings for all utterances."""
    
    try:
        import librosa
        import torch
        from transformers import Wav2Vec2FeatureExtractor, WavLMForSpeechPrediction
        
        # Load model
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        if not hasattr(extract_wavlm, 'model_loaded'):
            print("  Loading WavLM model...")
            processor = Wav2Vec2FeatureExtractor.from_pretrained('microsoft/wavlm-base')
            model = WavLMForSpeechPrediction.from_pretrained('microsoft/wavlm-base')
            model.to(device)
            model.eval()
            extract_wavlm.processor = processor
            extract_wavlm.model = model
            extract_wavlm.device = device
            print(f"  WavLM loaded on {device}")
        
        processor = extract_wavlm.processor
        model = extract_wavlm.model
        device = extract_wavlm.device
        
        embeddings = {}
        for i, utt in enumerate(utterances):
            uid = utt['utterance_id']
            start = utt['start']
            end = utt['end']
            
            try:
                y, sr = librosa.load(audio_path, sr=16000, offset=start, duration=end-start)
                
                if len(y) < 400:
                    continue
                
                inputs = processor(y, sampling_rate=16000, return_tensors='pt')
                inputs = {k: v.to(device) for k, v in inputs.items()}
                
                with torch.no_grad():
                    outputs = model(**inputs)
                
                hidden_states = outputs.hidden_states
                if hidden_states:
                    embedding = hidden_states[-1][0].mean(dim=0).cpu().numpy()
                else:
                    embedding = outputs.logits[0].mean(dim=0).cpu().numpy()
                
                embeddings[uid] = embedding
                
            except Exception as e:
                continue
        
        return embeddings
    
    except ImportError as e:
        print(f"  Import error: {e}")
        return {}
    except Exception as e:
        print(f"  WavLM error: {e}")
        return {}

# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 60)
    print("WavLM Extraction for 100 YouTube Videos")
    print("=" * 60)
    
    # Load checkpoint
    checkpoint = {'done': [], 'failed': [], 'current': None}
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE) as f:
            checkpoint = json.load(f)
    
    done = set(checkpoint['done'])
    failed = set(checkpoint['failed'])
    print(f"Already done: {len(done)}")
    print(f"Failed: {len(failed)}")
    
    # Get all processed video IDs
    processed_ids = [f.replace('.json', '') for f in os.listdir(PROCESSED_DIR) if f.endswith('.json')]
    print(f"Total to process: {len(processed_ids)}")
    
    to_process = [v for v in processed_ids if v not in done and v not in failed]
    print(f"Remaining: {len(to_process)}")
    
    if not to_process:
        print("Nothing to process!")
        return
    
    # Process each video
    for i, video_id in enumerate(to_process):
        print(f"\n[{i+1}/{len(to_process)}] {video_id}")
        
        try:
            # Load metadata
            meta_path = os.path.join(PROCESSED_DIR, f'{video_id}.json')
            with open(meta_path) as f:
                data = json.load(f)
            
            utterances = data.get('utterances', [])
            print(f"  Utterances: {len(utterances)}")
            
            # Download audio
            print(f"  Downloading audio...")
            audio_path = download_audio(video_id)
            if not audio_path:
                print(f"  ✗ Audio download failed")
                checkpoint['failed'].append(video_id)
                with open(CHECKPOINT_FILE, 'w') as f:
                    json.dump(checkpoint, f, indent=2)
                continue
            
            print(f"  Audio: {os.path.getsize(audio_path) / 1e6:.1f} MB")
            
            # Extract WavLM
            print(f"  Extracting WavLM...")
            embeddings = extract_wavlm(audio_path, utterances)
            
            if not embeddings:
                print(f"  ✗ WavLM extraction failed")
                checkpoint['failed'].append(video_id)
                with open(CHECKPOINT_FILE, 'w') as f:
                    json.dump(checkpoint, f, indent=2)
                continue
            
            # Save embeddings
            output_path = os.path.join(WAVLM_DIR, f'{video_id}.json')
            with open(output_path, 'w') as f:
                json.dump(embeddings, f)
            
            print(f"  ✓ {len(embeddings)} embeddings saved")
            
            # Update checkpoint
            checkpoint['done'].append(video_id)
            with open(CHECKPOINT_FILE, 'w') as f:
                json.dump(checkpoint, f, indent=2)
            
            # Cleanup audio to save space
            try:
                os.remove(audio_path)
                print(f"  Cleaned up audio")
            except:
                pass
            
            # Progress every 10
            if (i + 1) % 10 == 0:
                print(f"\n  === PROGRESS: {i+1}/{len(to_process)} done ===\n")
        
        except Exception as e:
            print(f"  ✗ Error: {e}")
            checkpoint['failed'].append(video_id)
            with open(CHECKPOINT_FILE, 'w') as f:
                json.dump(checkpoint, f, indent=2)
    
    # Final summary
    print("\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)
    print(f"Done: {len(checkpoint['done'])}")
    print(f"Failed: {len(checkpoint['failed'])}")
    print(f"Output: {WAVLM_DIR}")
    
    # Count embeddings
    total_emb = 0
    for f in os.listdir(WAVLM_DIR):
        if f.endswith('.json'):
            with open(os.path.join(WAVLM_DIR, f)) as fp:
                data = json.load(fp)
                total_emb += len(data)
    print(f"Total embeddings: {total_emb}")

if __name__ == '__main__':
    main()
