#!/usr/bin/env python3
"""
Quick acoustic feature extraction for standup comedy audio.
Extracts prosodic features aligned with VTT word timestamps.

Based on: ACOUSTIC_FEATURES_RESEARCH.md
Validated features: F0, pauses, speech rate, MFCCs, RMS energy, spectral features

Usage:
    python3 extract_prosody_v1.py --audio-dir data/audio_comedy/audio --vtt-dir data/youtube_scraped --output prosody_features.csv
"""

import argparse
import json
import os
import sys
import warnings
from pathlib import Path

import librosa
import numpy as np

warnings.filterwarnings("ignore")


def extract_f0_features(y, sr, frame_start, frame_end):
    """Extract F0 statistics from a window."""
    segment = y[frame_start:frame_end]
    if len(segment) < sr * 0.05:  # too short (< 50ms)
        return {k: 0.0 for k in [
            'f0_mean', 'f0_std', 'f0_range', 'f0_min', 'f0_max', 'f0_slope', 'f0_voiced_ratio'
        ]}

    f0, voiced_flag, _ = librosa.pyin(segment, fmin=75, fmax=500, sr=sr,
                                       frame_length=2048, hop_length=512)
    voiced = f0[~np.isnan(f0)]

    if len(voiced) == 0:
        return {
            'f0_mean': 0.0, 'f0_std': 0.0, 'f0_range': 0.0,
            'f0_min': 0.0, 'f0_max': 0.0, 'f0_slope': 0.0,
            'f0_voiced_ratio': 0.0
        }

    slope = 0.0
    if len(voiced) > 2:
        slope = np.polyfit(np.arange(len(voiced)), voiced, 1)[0]

    return {
        'f0_mean': float(np.mean(voiced)),
        'f0_std': float(np.std(voiced)),
        'f0_range': float(np.max(voiced) - np.min(voiced)),
        'f0_min': float(np.min(voiced)),
        'f0_max': float(np.max(voiced)),
        'f0_slope': float(slope),
        'f0_voiced_ratio': float(len(voiced) / len(f0)),
    }


def extract_energy_features(y, sr, frame_start, frame_end):
    """Extract RMS energy statistics."""
    segment = y[frame_start:frame_end]
    if len(segment) < 512:
        return {k: 0.0 for k in ['rms_mean', 'rms_std', 'rms_max', 'rms_range']}

    rms = librosa.feature.rms(y=segment, frame_length=2048, hop_length=512)[0]
    return {
        'rms_mean': float(np.mean(rms)),
        'rms_std': float(np.std(rms)),
        'rms_max': float(np.max(rms)),
        'rms_range': float(np.max(rms) - np.min(rms)),
    }


def extract_mfcc_features(y, sr, frame_start, frame_end, n_mfcc=13):
    """Extract MFCC statistics."""
    segment = y[frame_start:frame_end]
    if len(segment) < 2048:
        return {f'mfcc_{i}_mean': 0.0 for i in range(n_mfcc)}

    mfccs = librosa.feature.mfcc(y=segment, sr=sr, n_mfcc=n_mfcc,
                                   n_fft=2048, hop_length=512)
    return {f'mfcc_{i}_mean': float(np.mean(mfccs[i])) for i in range(n_mfcc)}


def extract_spectral_features(y, sr, frame_start, frame_end):
    """Extract spectral shape features."""
    segment = y[frame_start:frame_end]
    if len(segment) < 2048:
        return {k: 0.0 for k in [
            'spectral_centroid', 'spectral_bandwidth', 'spectral_rolloff', 'spectral_flux'
        ]}

    centroid = librosa.feature.spectral_centroid(y=segment, sr=sr, n_fft=2048, hop_length=512)[0]
    bandwidth = librosa.feature.spectral_bandwidth(y=segment, sr=sr, n_fft=2048, hop_length=512)[0]
    rolloff = librosa.feature.spectral_rolloff(y=segment, sr=sr, n_fft=2048, hop_length=512)[0]

    return {
        'spectral_centroid': float(np.mean(centroid)),
        'spectral_bandwidth': float(np.mean(bandwidth)),
        'spectral_rolloff': float(np.mean(rolloff)),
    }


def compute_pause_before(y, sr, word_start_sec, window_sec=2.0):
    """Estimate silence duration before a word onset."""
    window_samples = int(window_sec * sr)
    start_sample = max(0, int(word_start_sec * sr) - window_samples)
    end_sample = int(word_start_sec * sr)

    if end_sample <= start_sample:
        return 0.0

    segment = y[start_sample:end_sample]
    rms = librosa.feature.rms(y=segment, frame_length=2048, hop_length=512)[0]
    threshold = np.mean(rms) + 0.5 * np.std(rms)

    # Count consecutive silent frames from the end
    silent_frames = 0
    for i in range(len(rms) - 1, -1, -1):
        if rms[i] < threshold:
            silent_frames += 1
        else:
            break

    return float(silent_frames * 512 / sr)  # convert frames to seconds


def extract_features_for_word(y, sr, word_start, word_end, context_sec=0.5):
    """Extract all acoustic features for one word."""
    sr = int(sr)
    # Add context window around the word
    ctx_samples = int(context_sec * sr)
    start_sample = max(0, int(word_start * sr) - ctx_samples)
    end_sample = min(len(y), int(word_end * sr) + ctx_samples)

    features = {}
    features.update(extract_f0_features(y, sr, start_sample, end_sample))
    features.update(extract_energy_features(y, sr, start_sample, end_sample))
    features.update(extract_mfcc_features(y, sr, start_sample, end_sample))
    features.update(extract_spectral_features(y, sr, start_sample, end_sample))
    features['pause_before'] = compute_pause_before(y, sr, word_start)
    features['word_duration'] = word_end - word_start
    features['speech_rate'] = 1.0 / (word_end - word_start) if (word_end - word_start) > 0 else 0.0

    return features


def load_vtt_words(vtt_path):
    """Load word-level timestamps from a VTT subtitle file or JSON transcript."""
    words = []
    if vtt_path.endswith('.json'):
        with open(vtt_path) as f:
            data = json.load(f)
        for seg in data.get('segments', data if isinstance(data, list) else []):
            if isinstance(seg, dict) and 'start' in seg:
                words.append({
                    'word': seg.get('word', seg.get('text', '')),
                    'start': float(seg['start']),
                    'end': float(seg['end']),
                })
    elif vtt_path.endswith('.vtt'):
        import re
        with open(vtt_path) as f:
            content = f.read()
        # Parse VTT cues
        blocks = re.split(r'\n\n+', content.strip())
        for block in blocks:
            time_match = re.search(
                r'(\d{2}):(\d{2}):(\d{2})\.(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})\.(\d{3})',
                block
            )
            if time_match:
                g = time_match.groups()
                start = int(g[0])*3600 + int(g[1])*60 + int(g[2]) + int(g[3])/1000
                end = int(g[4])*3600 + int(g[5])*60 + int(g[6]) + int(g[7])/1000
                text = block.split('\n')[-1].strip()
                # Split into individual words (approximate timestamps)
                word_list = text.split()
                if word_list:
                    word_dur = (end - start) / len(word_list)
                    for i, w in enumerate(word_list):
                        words.append({
                            'word': w,
                            'start': start + i * word_dur,
                            'end': start + (i + 1) * word_dur,
                        })
    return words


def process_file(audio_path, vtt_path, output_path=None):
    """Process one audio file with its transcript."""
    print(f"Loading audio: {audio_path}")
    y, sr = librosa.load(audio_path, sr=16000)
    print(f"  Duration: {len(y)/sr:.1f}s, SR: {sr}")

    words = load_vtt_words(vtt_path)
    print(f"  Words from transcript: {len(words)}")

    results = []
    for i, w in enumerate(words):
        if i % 100 == 0:
            print(f"  Processing word {i}/{len(words)}...")

        feats = extract_features_for_word(y, sr, w['start'], w['end'])
        feats['word'] = w['word']
        feats['start'] = w['start']
        feats['end'] = w['end']
        feats['audio_file'] = os.path.basename(audio_path)
        results.append(feats)

    return results


def main():
    parser = argparse.ArgumentParser(description='Extract prosodic features from comedy audio')
    parser.add_argument('--audio-dir', required=True, help='Directory containing audio files')
    parser.add_argument('--vtt-dir', required=True, help='Directory containing VTT/JSON transcripts')
    parser.add_argument('--output', default='prosody_features.csv', help='Output CSV path')
    parser.add_argument('--limit', type=int, default=0, help='Limit number of files (0=all)')
    args = parser.parse_args()

    import pandas as pd

    # Find audio-transcript pairs
    audio_files = []
    for root, dirs, files in os.walk(args.audio_dir):
        for f in files:
            if f.endswith(('.mp3', '.wav', '.webm', '.m4a')):
                audio_files.append(os.path.join(root, f))

    print(f"Found {len(audio_files)} audio files")

    all_results = []
    processed = 0

    for audio_path in audio_files:
        base = os.path.splitext(os.path.basename(audio_path))[0]

        # Find matching transcript
        vtt_candidates = [
            os.path.join(args.vtt_dir, base + '.vtt'),
            os.path.join(args.vtt_dir, base + '.json'),
        ]
        # Also search in subdirectories
        for root, dirs, files in os.walk(args.vtt_dir):
            for f in files:
                if f.startswith(base) and f.endswith(('.vtt', '.json')):
                    vtt_candidates.append(os.path.join(root, f))

        vtt_path = None
        for c in vtt_candidates:
            if os.path.exists(c):
                vtt_path = c
                break

        if not vtt_path:
            print(f"  No transcript found for {base}, skipping")
            continue

        results = process_file(audio_path, vtt_path)
        all_results.extend(results)
        processed += 1

        if args.limit > 0 and processed >= args.limit:
            break

    if all_results:
        df = pd.DataFrame(all_results)
        df.to_csv(args.output, index=False)
        print(f"\nWrote {len(df)} word-level features to {args.output}")
        print(f"Columns: {list(df.columns)}")
    else:
        print("No features extracted. Check audio-transcript alignment.")


if __name__ == '__main__':
    main()
