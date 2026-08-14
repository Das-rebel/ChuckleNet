#!/usr/bin/env python3
"""
Process YouTube Comedy Dataset

Pipeline:
1. Download audio for each video
2. Split into utterances based on subtitle timestamps
3. Extract WavLM embeddings per utterance
4. Extract prosody features per utterance
5. Create labels based on [laughter] markers
6. Save as aligned JSONL
"""

import os
import json
import subprocess
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional
from google.cloud import storage
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import torch

# ============================================================================
# CONFIGURATION
# ============================================================================

GCS_BUCKET = 'chuckle-net-youtube-20260616'
GCS_PROJECT = 'omniclaw-personal-assistant'
LOCAL_AUDIO_DIR = '/tmp/youtube_audio'
LOCAL_EMBEDDINGS_DIR = '/tmp/youtube_embeddings'
OUTPUT_DIR = '/Users/Subho/data/chuckle-net-youtube'

os.makedirs(LOCAL_AUDIO_DIR, exist_ok=True)
os.makedirs(LOCAL_EMBEDDINGS_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ============================================================================
# GCS UTILITIES
# ============================================================================

def get_gcs_bucket():
    client = storage.Client(project=GCS_PROJECT)
    return client.bucket(GCS_BUCKET)

def gcs_exists(gcs_path: str) -> bool:
    try:
        bucket = get_gcs_bucket()
        return bucket.blob(gcs_path).exists()
    except:
        return False

# ============================================================================
# AUDIO DOWNLOAD
# ============================================================================

def download_audio(video_id: str) -> Optional[str]:
    """Download audio from YouTube video."""
    
    output_path = os.path.join(LOCAL_AUDIO_DIR, f'{video_id}.wav')
    if os.path.exists(output_path):
        return output_path
    
    # Check GCS
    if gcs_exists(f'audio/{video_id}.wav'):
        bucket = get_gcs_bucket()
        blob = bucket.blob(f'audio/{video_id}.wav')
        blob.download_to_filename(output_path)
        return output_path
    
    # Download from YouTube
    cmd = [
        'yt-dlp',
        '-f', 'bestaudio',
        '--extract-audio',
        '--audio-format', 'wav',
        '--audio-quality', '0',
        '--output', f'{LOCAL_AUDIO_DIR}/{video_id}.%(ext)s',
        '--no-playlist',
        '--', f'https://www.youtube.com/watch?v={video_id}'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        
        # Find downloaded file
        for f in os.listdir(LOCAL_AUDIO_DIR):
            if video_id in f and f.endswith('.wav'):
                downloaded = os.path.join(LOCAL_AUDIO_DIR, f)
                if downloaded != output_path:
                    # Convert to 16kHz mono
                    subprocess.run([
                        'ffmpeg', '-i', downloaded, 
                        '-ar', '16000', '-ac', '1',
                        output_path, '-y'
                    ], capture_output=True, timeout=300)
                    os.remove(downloaded)
                return output_path
    except Exception as e:
        print(f"    Download error: {e}")
    
    return None

# ============================================================================
# UTTERANCE EXTRACTION
# ============================================================================

def extract_utterances_from_metadata(video_id: str, metadata: Dict) -> List[Dict]:
    """Create utterance list from video metadata with labels."""
    
    utterances = []
    laughter_markers = metadata.get('laughter_markers', [])
    
    # Deduplicate overlapping laughter markers
    clean_laughter = []
    for m in laughter_markers:
        if not clean_laughter or m['start'] > clean_laughter[-1]['end']:
            clean_laughter.append(m)
    
    # Create utterances from subtitle segments
    subtitle_utterances = metadata.get('utterances', [])
    
    for i, utt in enumerate(subtitle_utterances):
        start = utt['start']
        end = utt['end']
        text = utt['text']
        
        # Check if this utterance overlaps with laughter
        has_laughter = False
        for lm in clean_laughter:
            if (start < lm['end'] and end > lm['start']):
                has_laughter = True
                break
        
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
        })
    
    return utterances

# ============================================================================
# WavLM EMBEDDING EXTRACTION
# ============================================================================

def extract_wavlm_embedding(audio_path: str, start: float, end: float) -> Optional[np.ndarray]:
    """Extract WavLM embedding for a time segment."""
    
    try:
        from transformers import Wav2Vec2FeatureExtractor, WavLMForSpeechPrediction
        import torch
        import librosa
        
        # Load model (lazy load)
        if not hasattr(extract_wavlm_embedding, 'model'):
            print("    Loading WavLM model...")
            extract_wavlm_embedding.processor = Wav2Vec2FeatureExtractor.from_pretrained(
                'microsoft/wavlm-base'
            )
            extract_wavlm_embedding.model = WavLMForSpeechPrediction.from_pretrained(
                'microsoft/wavlm-base'
            )
            extract_wavlm_embedding.model.eval()
        
        # Load audio segment
        y, sr = librosa.load(audio_path, sr=16000, offset=start, duration=end-start)
        
        if len(y) < 400:  # Too short
            return None
        
        # Extract features
        inputs = extract_wavlm_embedding.processor(y, sampling_rate=16000, return_tensors='pt')
        
        with torch.no_grad():
            outputs = extract_wavlm_embedding.model(**inputs)
        
        # Mean pooling over time
        hidden_states = outputs.hidden_states  # tuple of (batch, time, hidden)
        if hidden_states:
            embedding = hidden_states[-1][0].mean(dim=0).numpy()
        else:
            embedding = outputs.logits[0].mean(dim=0).numpy()
        
        return embedding
        
    except Exception as e:
        print(f"    WavLM error: {e}")
        return None

# ============================================================================
# PROSODY FEATURE EXTRACTION
# ============================================================================

def extract_prosody(audio_path: str, start: float, end: float) -> Optional[Dict]:
    """Extract prosody features for a time segment."""
    
    try:
        import librosa
        
        y, sr = librosa.load(audio_path, sr=16000, offset=start, duration=end-start)
        
        if len(y) < 400:
            return None
        
        # Basic features
        rms = librosa.feature.rms(y=y)[0].mean()
        zcr = librosa.feature.zero_crossing_rate(y=y)[0].mean()
        
        # Pitch features
        pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
        pitch_max = pitches.max() if pitches.max() > 0 else 0
        pitch_mean = pitches[pitches > 0].mean() if (pitches > 0).any() else 0
        
        # Formants (simplified)
        n_fft = 512
        spec = np.abs(librosa.stft(y, n_fft=n_fft))
        spec_db = librosa.amplitude_to_db(spec)
        
        # Spectral features
        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0].mean()
        spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)[0].mean()
        
        # MFCC (first 13 coefficients)
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        mfcc_mean = mfccs.mean(axis=1)
        
        # Combine into feature vector
        features = [
            rms, zcr, pitch_max / 1000, pitch_mean / 1000,
            spectral_centroid / 1000, spectral_bandwidth / 1000,
        ] + list(mfcc_mean / 100)
        
        return {
            'prosody_features': features,
            'prosody_rms': rms,
            'prosody_zcr': zcr,
            'prosody_pitch_max': pitch_max,
        }
        
    except Exception as e:
        print(f"    Prosody error: {e}")
        return None

# ============================================================================
# MAIN PROCESSING
# ============================================================================

def process_video(video_id: str) -> Dict:
    """Process a single video: download audio, extract features, create utterances."""
    
    print(f"Processing: {video_id}")
    
    # Check if already processed
    output_file = os.path.join(LOCAL_EMBEDDINGS_DIR, f'{video_id}.json')
    if os.path.exists(output_file):
        print(f"  Already processed, skipping")
        return {'id': video_id, 'status': 'already_processed'}
    
    # Get metadata from GCS
    bucket = get_gcs_bucket()
    try:
        blob = bucket.blob(f'metadata/{video_id}.json')
        metadata = json.loads(blob.download_as_string())
    except Exception as e:
        print(f"  Failed to get metadata: {e}")
        return {'id': video_id, 'status': 'metadata_failed'}
    
    # Download audio
    audio_path = download_audio(video_id)
    if not audio_path:
        print(f"  Failed to download audio")
        return {'id': video_id, 'status': 'audio_failed'}
    
    print(f"  Audio: {audio_path}")
    
    # Extract utterances with labels
    utterances = extract_utterances_from_metadata(video_id, metadata)
    print(f"  Utterances: {len(utterances)}")
    
    # Extract features for each utterance (sample first 100 for speed)
    embeddings = {}
    prosody = {}
    
    sample_utts = utterances[:100]  # Limit for speed
    for utt in sample_utts:
        uid = utt['utterance_id']
        
        # WavLM embedding
        emb = extract_wavlm_embedding(audio_path, utt['start'], utt['end'])
        if emb is not None:
            embeddings[uid] = emb.tolist()
        
        # Prosody features
        pros = extract_prosody(audio_path, utt['start'], utt['end'])
        if pros is not None:
            prosody[uid] = pros
    
    print(f"  Extracted: {len(embeddings)} embeddings, {len(prosody)} prosody")
    
    # Save
    result = {
        'video_id': video_id,
        'utterances': utterances[:100],
        'embeddings': embeddings,
        'prosody': prosody,
        'n_utterances': len(utterances),
        'n_positive': sum(u['label_any'] for u in utterances[:100]),
    }
    
    with open(output_file, 'w') as f:
        json.dump(result, f)
    
    # Upload to GCS
    try:
        blob = bucket.blob(f'processed/{video_id}.json')
        blob.upload_from_filename(output_file)
    except:
        pass
    
    return result

def main():
    print("=== YouTube Comedy Dataset Processing ===")
    print()
    
    # Get all video IDs from GCS
    bucket = get_gcs_bucket()
    metadata_blobs = list(bucket.list_blobs(prefix='metadata/'))
    
    video_ids = []
    for blob in metadata_blobs:
        video_id = blob.name.replace('metadata/', '').replace('.json', '')
        video_ids.append(video_id)
    
    print(f"Total videos to process: {len(video_ids)}")
    print(f"Audio dir: {LOCAL_AUDIO_DIR}")
    print(f"Embeddings dir: {LOCAL_EMBEDDINGS_DIR}")
    print()
    
    # Process first 10 as test
    test_ids = video_ids[:10]
    print(f"Processing test batch: {len(test_ids)} videos")
    
    results = []
    for vid in test_ids:
        result = process_video(vid)
        results.append(result)
        print()
    
    # Summary
    success = [r for r in results if r.get('status') == 'already_processed' or 'embeddings' in r]
    n_utts = sum(r.get('n_utterances', 0) for r in results)
    n_pos = sum(r.get('n_positive', 0) for r in results)
    
    print(f"=== Test Complete ===")
    print(f"Processed: {len(success)}/{len(test_ids)}")
    print(f"Utterances: {n_utts}")
    print(f"Positive: {n_pos}")
    print(f"Output: {LOCAL_EMBEDDINGS_DIR}")

if __name__ == '__main__':
    main()
