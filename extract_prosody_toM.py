#!/usr/bin/env python3
"""
extract_prosody_toM.py — Extract Theory-of-Mind prosody features from audio segments.

Run locally (no GPU needed):
    python3 extract_prosody_toM.py --audio-dir /path/to/audio --output /path/to/output.jsonl

Then upload output.jsonl to Google Drive chuckle_checkpoints/prosody_toM.jsonl
and the notebook will load it instead of re-extracting.

Based on:
    - Purandare 2006: pause >0.8s BEFORE punchline = strongest acoustic humor signal
    - Pickering 2009: audience laughter onset timing
    - Bachorowski 2001: F0 variability = Duchenne (genuine) laughter marker
    - Hasnain 2022: spectral tilt differentiates real vs posed laughter
"""

import argparse, json, os, sys, time
import numpy as np
import librosa
from tqdm import tqdm
from pathlib import Path

SR = 16000

def extract_prosody(audio_path, start_sec, end_sec):
    """
    Extract ~52 Theory-of-Mind prosody features for an utterance.
    
    Feature groups:
      GROUP 1 — Duchenne markers (genuine vs fake laughter)
        f0_mean, f0_std, f0_range, f0_max, f0_min, f0_variability, f0_slope
        spectral_centroid, spectral_bandwidth
        mfcc1-13 (voice quality)
      
      GROUP 2 — Incongruity-Resolution (prosodic surprise)
        delta_f0_max, energy_spike_count, rms_range
        
      GROUP 3 — Theory of Mind (conversational timing)
        pause_max, pause_mean, pause_count, pause_density, pause_total
        long_pause_count (>=0.8s), has_long_pause
        speech_rate, utterance_duration
    """
    try:
        y, sr = librosa.load(
            audio_path, sr=SR, mono=True,
            offset=max(0, start_sec - 0.1),
            duration=(end_sec - start_sec) + 0.2
        )
    except Exception as e:
        y = np.zeros(int(5 * SR), dtype=np.float32)

    feats = {}

    # ─── GROUP 3: PAUSE / SILENCE (ToM #1 — Purandare 2006) ───────────────
    intervals = librosa.effects.split(y, top_db=30, frame_length=1024, hop_length=512)
    if len(intervals) > 0:
        pauses = []
        for i in range(len(intervals) - 1):
            gap_sec = (intervals[i+1][0] - intervals[i][1]) / sr
            pauses.append(gap_sec)
        
        feats['pause_max']      = float(max(pauses)) if pauses else 0.0
        feats['pause_mean']     = float(np.mean(pauses)) if pauses else 0.0
        feats['pause_count']    = float(sum(1 for p in pauses if p > 0.1))
        feats['pause_density'] = feats['pause_count'] / max(len(pauses), 1)
        feats['pause_total']    = float(sum(pauses))
        # Purandare: pause >= 0.8s = strong humor signal
        feats['long_pause_count'] = float(sum(1 for p in pauses if p >= 0.8))
        feats['has_long_pause']   = float(any(p >= 0.8 for p in pauses))
        # Very long pause (>=1.5s) = audience laughter response
        feats['very_long_pause_count'] = float(sum(1 for p in pauses if p >= 1.5))
    else:
        for k in ['pause_max','pause_mean','pause_count','pause_density',
                  'pause_total','long_pause_count','has_long_pause',
                  'very_long_pause_count']:
            feats[k] = 0.0

    # ─── GROUP 1: F0 / PITCH (Duchenne marker) ─────────────────────────────
    try:
        f0, voiced, _ = librosa.pyin(
            y, fmin=75, fmax=500, sr=sr,
            frame_length=2048, hop_length=512
        )
        f0_clean = f0[~np.isnan(f0)]
        if len(f0_clean) > 5:
            feats['f0_mean']        = float(np.mean(f0_clean))
            feats['f0_std']         = float(np.std(f0_clean))
            feats['f0_range']       = float(np.max(f0_clean) - np.min(f0_clean))
            feats['f0_max']         = float(np.max(f0_clean))
            feats['f0_min']         = float(np.min(f0_clean))
            feats['f0_variability'] = feats['f0_std'] / max(feats['f0_mean'], 1)
            # F0 slope = delivery momentum (positive = rising, negative = falling)
            feats['f0_slope']       = float(np.polyfit(range(len(f0_clean)), f0_clean, 1)[0])
            # Voiced ratio = breathiness (Duchenne: higher voiced ratio = more genuine)
            feats['voiced_ratio']   = float(np.mean(voiced[~np.isnan(f0)]))
        else:
            for k in ['f0_mean','f0_std','f0_range','f0_max','f0_min',
                      'f0_variability','f0_slope','voiced_ratio']:
                feats[k] = 0.0
    except Exception:
        for k in ['f0_mean','f0_std','f0_range','f0_max','f0_min',
                  'f0_variability','f0_slope','voiced_ratio']:
            feats[k] = 0.0

    # ─── GROUP 1: SPECTRAL (voice quality) ─────────────────────────────────
    try:
        S = np.abs(librosa.stft(y))
        feats['spectral_centroid_mean']  = float(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr)[0]))
        feats['spectral_bandwidth_mean'] = float(np.mean(librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]))
        feats['spectral_rolloff_mean']   = float(np.mean(librosa.feature.spectral_rolloff(y=y, sr=sr)[0]))
    except Exception:
        for k in ['spectral_centroid_mean','spectral_bandwidth_mean','spectral_rolloff_mean']:
            feats[k] = 0.0

    # ─── GROUP 1: MFCC (voice timbre) ───────────────────────────────────────
    try:
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        for i in range(13):
            feats[f'mfcc{i+1}_mean'] = float(np.mean(mfccs[i]))
            feats[f'mfcc{i+1}_std']  = float(np.std(mfccs[i]))
    except Exception:
        for i in range(13):
            feats[f'mfcc{i+1}_mean'] = 0.0
            feats[f'mfcc{i+1}_std']  = 0.0

    # ─── GROUP 2: ENERGY / RMS (incongruity) ─────────────────────────────────
    try:
        rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=512)[0]
        feats['rms_mean']  = float(np.mean(rms))
        feats['rms_std']   = float(np.std(rms))
        feats['rms_max']   = float(np.max(rms))
        feats['rms_range'] = float(np.max(rms) - np.min(rms))
        # Energy spikes = emphatic delivery or audience laughter
        threshold = np.mean(rms) + 2 * np.std(rms)
        feats['energy_spike_count'] = float(sum(1 for r in rms if r > threshold))
        # Delta RMS (prosodic surprise)
        feats['delta_rms_max'] = float(np.max(np.abs(np.diff(rms)))) if len(rms) > 1 else 0.0
    except Exception:
        for k in ['rms_mean','rms_std','rms_max','rms_range','energy_spike_count','delta_rms_max']:
            feats[k] = 0.0

    # ─── GROUP 3: SPEECH RATE (word duration proxy) ─────────────────────────
    dur = end_sec - start_sec
    n_voiced = sum(1 for v in voiced if v) if 'voiced' in dir() else 0
    feats['speech_rate']          = float(n_voiced / max(dur, 0.1))
    feats['utterance_duration']  = float(dur)

    # ─── GROUP 3: ONSET DETECTION (audience laughter onset) ─────────────────
    try:
        onsets = librosa.onset.onset_detect(y=y, sr=sr, units='time')
        feats['onset_count']    = float(len(onsets))
        feats['onset_density']  = float(len(onsets) / max(dur, 0.1))
    except Exception:
        feats['onset_count']   = 0.0
        feats['onset_density'] = 0.0

    return feats


def main():
    parser = argparse.ArgumentParser(description='Extract ToM prosody features from audio')
    parser.add_argument('--audio-dir', required=True, help='Directory containing MP3 files')
    parser.add_argument('--segments', required=True, help='Path to aligned_utterances.jsonl')
    parser.add_argument('--output', required=True, help='Output .jsonl path')
    parser.add_argument('--limit', type=int, default=None, help='Limit number of segments')
    args = parser.parse_args()

    # Load segments
    print(f'Loading segments from {args.segments}...')
    segments = []
    with open(args.segments) as f:
        for line in f:
            segments.append(json.loads(line))
    if args.limit:
        segments = segments[:args.limit]
    print(f'  {len(segments)} segments')

    # Extract prosody for each segment
    print(f'Extracting prosody from {args.audio_dir}...')
    t0 = time.time()
    output_rows = []
    
    for i, seg in enumerate(tqdm(segments, desc='Extracting prosody')):
        vid = seg['video_id']
        audio_path = os.path.join(args.audio_dir, f'{vid}.mp3')
        
        # Try common subdirectory patterns
        if not os.path.exists(audio_path):
            for subdir in ['batch1', 'batch2', 'batch3', 'batch4', 'batch5',
                           'batch6', 'batch7', 'batch8', 'batch9', 'batch10',
                           'ali_wong', 'batch11', 'batch12', 'batch13', 'batch14',
                           'batch15', 'batch16', 'batch17']:
                candidate = os.path.join(args.audio_dir, subdir, f'{vid}.mp3')
                if os.path.exists(candidate):
                    audio_path = candidate
                    break
        
        feats = extract_prosody(
            audio_path,
            float(seg['start']),
            float(seg['end'])
        )
        feats['uid']       = f"{vid}_{seg['start']:.2f}"
        feats['video_id']  = vid
        feats['label']     = seg.get('label_any', 0)
        feats['text']      = seg.get('text', '')[:100]
        output_rows.append(feats)
        
        if (i + 1) % 1000 == 0:
            elapsed = time.time() - t0
            rate = (i + 1) / elapsed
            eta = (len(segments) - i - 1) / rate / 60
            print(f'  [{i+1}/{len(segments)}] ETA={eta:.1f}min')

    # Save
    with open(args.output, 'w') as f:
        for row in output_rows:
            f.write(json.dumps(row) + '\n')

    elapsed = (time.time() - t0) / 60
    print(f'✅ Done: {len(output_rows)} rows in {elapsed:.1f}min → {args.output}')
    print(f'   Features per row: {len(output_rows[0]) - 4}')  # minus uid, video_id, label, text
    
    # Show top features by variance
    feat_names = [k for k in output_rows[0].keys() if k not in ['uid','video_id','label','text']]
    feat_df = {k: [r.get(k, 0) for r in output_rows] for k in feat_names}
    variances = {k: float(np.var(v)) for k, v in feat_df.items()}
    print('\nTop 10 features by variance (most discriminative):')
    for k, v in sorted(variances.items(), key=lambda x: -x[1])[:10]:
        print(f'  {k:30s}: {v:.4f}')


if __name__ == '__main__':
    main()
