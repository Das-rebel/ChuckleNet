#!/usr/bin/env python3
"""
Phase 1: Acoustic Feature Extraction at Utterance Level.

Extracts eGeMAPS 88 + prosodic + voice quality + spectral + energy features
for each utterance in aligned_utterances.jsonl.

Based on PRD v5.0 and Jenni V2 Validation Report.
"""

import json
import argparse
import warnings
import subprocess
import tempfile
from pathlib import Path
from collections import defaultdict

import numpy as np
import soundfile as sf

warnings.filterwarnings('ignore')

# Feature extractors
import opensmile
import librosa


def extract_audio_clip(mp3_path: str, start: float, end: float, 
                       sr: int = 16000, tmpdir: str = None) -> np.ndarray | None:
    """Extract audio clip from MP3 using ffmpeg."""
    duration = end - start
    if duration <= 0:
        return None
    
    try:
        # Use ffmpeg to extract clip as raw PCM
        cmd = [
            'ffmpeg', '-y', '-loglevel', 'quiet',
            '-ss', str(start),
            '-t', str(duration),
            '-i', mp3_path,
            '-ac', '1',           # mono
            '-ar', str(sr),       # sample rate
            '-f', 'wav',          # WAV format
            'pipe:1'              # stdout
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=30)
        
        if result.returncode != 0 or len(result.stdout) < 44:
            return None
        
        # Parse WAV from stdout
        audio, _ = sf.read(
            tempfile.NamedTemporaryFile(suffix='.wav', delete=True),
            # Read from bytes
        )
        return audio
        
    except Exception:
        # Fallback: use soundfile directly
        try:
            info = sf.info(mp3_path)
            start_frame = int(start * info.samplerate)
            n_frames = int(duration * info.samplerate)
            audio, _ = sf.read(mp3_path, start=start_frame, frames=n_frames, dtype='float32')
            if len(audio.shape) > 1:
                audio = audio.mean(axis=1)  # mono
            # Resample if needed
            if info.samplerate != sr:
                audio = librosa.resample(audio, orig_sr=info.samplerate, target_sr=sr)
            return audio
        except Exception:
            return None


def extract_egemaps(audio: np.ndarray, sr: int = 16000) -> dict:
    """Extract eGeMAPS v02 88 features using openSMILE."""
    smile = opensmile.Smile(
        feature_set=opensmile.FeatureSet.eGeMAPSv02,
        feature_level=opensmile.FeatureLevel.Functionals,
    )
    try:
        features = smile.process_signal(audio, sr)
        return features.iloc[0].to_dict()
    except Exception:
        return {}


def extract_prosodic(audio: np.ndarray, sr: int = 16000) -> dict:
    """Extract prosodic features: F0, pause, speech rate."""
    features = {}
    
    # F0 (fundamental frequency)
    f0, voiced_flags, voiced_probs = librosa.piptrack(
        y=audio, sr=sr, fmin=75, fmax=500
    )
    f0_vals = f0[voiced_flags > 0] if voiced_flags.any() else []
    if len(f0_vals) > 0:
        f0_vals = f0_vals[f0_vals > 0]
    
    if len(f0_vals) > 0:
        features['f0_mean'] = float(np.mean(f0_vals))
        features['f0_std'] = float(np.std(f0_vals))
        features['f0_range'] = float(np.max(f0_vals) - np.min(f0_vals))
        features['f0_min'] = float(np.min(f0_vals))
        features['f0_max'] = float(np.max(f0_vals))
    else:
        features['f0_mean'] = 0.0
        features['f0_std'] = 0.0
        features['f0_range'] = 0.0
        features['f0_min'] = 0.0
        features['f0_max'] = 0.0
    
    # Speech rate (zero crossing rate as proxy)
    zcr = librosa.feature.zero_crossing_rate(audio, frame_length=2048, hop_length=512)
    features['speech_rate_zcr'] = float(np.mean(zcr))
    
    return features


def extract_voice_quality(audio: np.ndarray, sr: int = 16000) -> dict:
    """Extract voice quality: HNR, spectral centroid."""
    features = {}
    
    # Harmonics-to-Noise Ratio (HNR)
    try:
        # Use librosa's spectral flatness as HNR proxy
        S = np.abs(librosa.stft(audio, n_fft=2048, hop_length=512))
        flatness = librosa.feature.spectral_flatness(S=S)
        # HNR ≈ -10 * log10(flatness) (approximation)
        hnr_approx = -10 * np.log10(np.mean(flatness) + 1e-10)
        features['hnr_approx'] = float(hnr_approx)
        features['hnr_std'] = float(np.std(-10 * np.log10(flatness.flatten() + 1e-10)))
    except Exception:
        features['hnr_approx'] = 0.0
        features['hnr_std'] = 0.0
    
    return features


def extract_spectral(audio: np.ndarray, sr: int = 16000) -> dict:
    """Extract spectral features: MFCC, centroid, bandwidth, rolloff, ZCR."""
    features = {}
    
    # MFCC (13 coefficients + delta + delta-delta)
    mfcc = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=13, n_fft=2048, hop_length=512)
    for i in range(13):
        features[f'mfcc_{i}_mean'] = float(np.mean(mfcc[i]))
        features[f'mfcc_{i}_std'] = float(np.std(mfcc[i]))
    
    # MFCC delta
    mfcc_delta = librosa.feature.delta(mfcc)
    for i in range(13):
        features[f'mfcc_delta_{i}_mean'] = float(np.mean(mfcc_delta[i]))
    
    # Spectral centroid
    centroid = librosa.feature.spectral_centroid(y=audio, sr=sr, n_fft=2048, hop_length=512)
    features['spectral_centroid_mean'] = float(np.mean(centroid))
    features['spectral_centroid_std'] = float(np.std(centroid))
    
    # Spectral bandwidth
    bandwidth = librosa.feature.spectral_bandwidth(y=audio, sr=sr, n_fft=2048, hop_length=512)
    features['spectral_bandwidth_mean'] = float(np.mean(bandwidth))
    features['spectral_bandwidth_std'] = float(np.std(bandwidth))
    
    # Spectral rolloff
    rolloff = librosa.feature.spectral_rolloff(y=audio, sr=sr, n_fft=2048, hop_length=512)
    features['spectral_rolloff_mean'] = float(np.mean(rolloff))
    features['spectral_rolloff_std'] = float(np.std(rolloff))
    
    # Zero crossing rate
    zcr = librosa.feature.zero_crossing_rate(audio, frame_length=2048, hop_length=512)
    features['zcr_mean'] = float(np.mean(zcr))
    features['zcr_std'] = float(np.std(zcr))
    
    return features


def extract_energy(audio: np.ndarray, sr: int = 16000) -> dict:
    """Extract energy features: RMS, loudness."""
    features = {}
    
    # RMS energy
    rms = librosa.feature.rms(y=audio, frame_length=2048, hop_length=512)
    features['rms_mean'] = float(np.mean(rms))
    features['rms_std'] = float(np.std(rms))
    features['rms_max'] = float(np.max(rms))
    features['rms_min'] = float(np.min(rms))
    
    return features


def extract_all_features(audio: np.ndarray, sr: int = 16000) -> dict:
    """Extract all acoustic features for one utterance."""
    features = {}
    
    # Duration
    features['duration_s'] = len(audio) / sr
    
    # eGeMAPS 88 features
    egemaps = extract_egemaps(audio, sr)
    for k, v in egemaps.items():
        features[f'egemaps_{k}'] = v
    
    # Prosodic (5 features)
    features.update(extract_prosodic(audio, sr))
    
    # Voice quality (2 features)
    features.update(extract_voice_quality(audio, sr))
    
    # Spectral (42 features)
    features.update(extract_spectral(audio, sr))
    
    # Energy (4 features)
    features.update(extract_energy(audio, sr))
    
    return features


def main():
    parser = argparse.ArgumentParser(description='Phase 1: Acoustic Feature Extraction')
    parser.add_argument('--input', default='data/audio_comedy/aligned_utterances.jsonl')
    parser.add_argument('--output', default='data/audio_comedy/utterance_features.jsonl')
    parser.add_argument('--limit', type=int, default=0, help='Max utterances to process (0=all)')
    parser.add_argument('--skip-existing', action='store_true', help='Skip already processed')
    parser.add_argument('--sr', type=int, default=16000, help='Sample rate')
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load utterances
    utterances = []
    with open(input_path) as f:
        for line in f:
            utterances.append(json.loads(line))
    
    if args.limit > 0:
        utterances = utterances[:args.limit]
    
    # Skip existing
    processed_ids = set()
    if args.skip_existing and output_path.exists():
        with open(output_path) as f:
            for line in f:
                r = json.loads(line)
                processed_ids.add(r['utterance_id'])
    
    print(f"Processing {len(utterances)} utterances ({len(processed_ids)} already done)")
    
    # Audio file cache (avoid re-opening same MP3)
    audio_cache = {}
    
    results = []
    failed = 0
    no_audio = 0
    
    # Open output in append mode if skip_existing
    mode = 'a' if args.skip_existing and processed_ids else 'w'
    out_f = open(output_path, mode)
    
    import sys
    
    for i, utt in enumerate(utterances):
        uid = utt['utterance_id']
        
        if uid in processed_ids:
            continue
        
        # Progress
        if (i + 1) % 500 == 0 or i == 0:
            print(f"  [{i+1}/{len(utterances)}] Processing {uid}...", 
                  flush=True)
        
        mp3_path = utt.get('audio_file', '')
        if not mp3_path or not Path(mp3_path).exists():
            no_audio += 1
            continue
        
        # Extract audio clip
        try:
            # Use ffmpeg for precise extraction
            start = max(0, utt['start'])
            end = utt['end']
            duration = end - start
            
            cmd = [
                'ffmpeg', '-y', '-loglevel', 'quiet',
                '-ss', str(start), '-t', str(duration),
                '-i', mp3_path, '-ac', '1', '-ar', str(args.sr),
                '-f', 'wav', 'pipe:1'
            ]
            result = subprocess.run(cmd, capture_output=True, timeout=30)
            
            if result.returncode != 0 or len(result.stdout) < 44:
                failed += 1
                continue
            
            # Write to temp file and read
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                tmp.write(result.stdout)
                tmp_path = tmp.name
            
            audio, sr = sf.read(tmp_path, dtype='float32')
            Path(tmp_path).unlink()
            
        except Exception as e:
            failed += 1
            continue
        
        if len(audio) < sr * 0.1:  # Less than 100ms
            failed += 1
            continue
        
        # Extract features
        try:
            features = extract_all_features(audio, sr)
            
            # Combine with metadata
            record = {
                'utterance_id': uid,
                'video_id': utt['video_id'],
                'text': utt['text'],
                'start': utt['start'],
                'end': utt['end'],
                'duration': utt['duration'],
                'n_words': utt['n_words'],
                'n_positive_words': utt['n_positive_words'],
                'positive_ratio': utt['positive_ratio'],
                'label_any': utt['label_any'],
                'label_majority': utt['label_majority'],
                'n_features': len(features),
                'features': features,
            }
            
            out_f.write(json.dumps(record) + '\n')
            out_f.flush()
            results.append(record)
            
        except Exception as e:
            failed += 1
    
    out_f.close()
    
    # Summary
    print(f"\n{'='*60}")
    print(f"PHASE 1: FEATURE EXTRACTION COMPLETE")
    print(f"{'='*60}")
    print(f"Processed: {len(results):,}")
    print(f"Failed: {failed:,}")
    print(f"No audio: {no_audio:,}")
    print(f"Output: {output_path}")
    
    if results:
        # Feature statistics
        all_feature_keys = set()
        for r in results:
            all_feature_keys.update(r['features'].keys())
        
        print(f"\nTotal features per utterance: {len(all_feature_keys)}")
        
        # Quick Cohen's d analysis
        pos_features = [r['features'] for r in results if r['label_any'] == 1]
        neg_features = [r['features'] for r in results if r['label_any'] == 0]
        
        print(f"\nQuick Cohen's d analysis (label_any):")
        print(f"  Positive: {len(pos_features)}, Negative: {len(neg_features)}")
        
        significant_features = []
        for key in sorted(all_feature_keys):
            pos_vals = [f[key] for f in pos_features if key in f and f[key] is not None and not (isinstance(f[key], float) and np.isnan(f[key]))]
            neg_vals = [f[key] for f in neg_features if key in f and f[key] is not None and not (isinstance(f[key], float) and np.isnan(f[key]))]
            
            if len(pos_vals) < 10 or len(neg_vals) < 10:
                continue
            
            pos_arr = np.array(pos_vals, dtype=float)
            neg_arr = np.array(neg_vals, dtype=float)
            
            # Cohen's d
            pooled_std = np.sqrt((np.std(pos_arr)**2 + np.std(neg_arr)**2) / 2)
            if pooled_std > 0:
                d = (np.mean(pos_arr) - np.mean(neg_arr)) / pooled_std
            else:
                d = 0.0
            
            if abs(d) > 0.3:  # Moderate effect size
                significant_features.append((key, d, np.mean(pos_arr), np.mean(neg_arr)))
        
        significant_features.sort(key=lambda x: abs(x[1]), reverse=True)
        print(f"\n  Features with |d| > 0.3 (moderate effect):")
        for key, d, pos_mean, neg_mean in significant_features[:20]:
            print(f"    {key[:60]:60s} d={d:+.3f} pos={pos_mean:.3f} neg={neg_mean:.3f}")


if __name__ == '__main__':
    main()
