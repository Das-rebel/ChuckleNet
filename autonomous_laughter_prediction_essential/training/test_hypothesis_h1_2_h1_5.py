#!/usr/bin/env python3
"""
HYPOTHESIS H1.2 + H1.5: Acoustic Feature Extraction from Real Audio
Tests whether:
  H1.2: F0 pitch contour changes precede laughter words
  H1.5: Simple acoustic features (pause from audio, F0) can classify laughter

Extracts from actual MP3 audio files (not subtitle timestamps):
  - F0 mean, std, range, slope (pitch features)
  - RMS energy
  - Actual pause from audio signal (not from subtitles)
  
Then compares laughter vs non-laughter words.
"""

import json
import sys
import os
import numpy as np
from collections import defaultdict
from pathlib import Path
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

try:
    import librosa
    HAS_LIBROSA = True
except ImportError:
    HAS_LIBROSA = False
    print("ERROR: librosa not installed. Run: pip install librosa")
    sys.exit(1)

DATA_DIR = Path("/Users/Subho/autonomous_laughter_prediction_essential/data/audio_comedy")
ALIGNED_FILE = DATA_DIR / "aligned_segments.jsonl"
OUTPUT_DIR = DATA_DIR / "acoustic_features"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Process a subset of videos for speed
MAX_VIDEOS = 5
MAX_WORDS_PER_VIDEO = 5000

def load_segments(path, max_videos=5):
    """Load aligned segments, group by video with existing audio files."""
    by_video = defaultdict(list)
    with open(path) as f:
        for line in f:
            seg = json.loads(line)
            af = seg.get('audio_file', '')
            if os.path.exists(af) and seg.get('start') is not None:
                by_video[seg['video_id']].append(seg)
    
    # Sort within each video by time
    for vid in by_video:
        by_video[vid].sort(key=lambda x: x['start'])
    
    # Take first N videos
    selected = {}
    for i, vid in enumerate(sorted(by_video.keys())):
        if i >= max_videos:
            break
        segs = by_video[vid][:MAX_WORDS_PER_VIDEO]
        if len(segs) > 100:
            selected[vid] = segs
    
    return selected

def extract_acoustic_features(video_segments):
    """
    For each segment, extract acoustic features from the audio:
    - F0 (pitch) features in a window before the word
    - RMS energy
    - Actual pause from audio signal
    """
    audio_file = video_segments[0]['audio_file']
    
    # Load full audio for this video
    try:
        y, sr = librosa.load(audio_file, sr=16000)
    except Exception as e:
        print(f"  ERROR loading {audio_file}: {e}")
        return []
    
    duration = len(y) / sr
    features = []
    
    for seg in video_segments:
        start_s = seg['start']
        end_s = seg['end']
        label = seg['label']
        
        # Window: 500ms before word start (the "pre-punchline" window)
        pre_start = max(0, start_s - 0.5)
        pre_end = start_s
        
        # Convert to samples
        pre_start_samp = int(pre_start * sr)
        pre_end_samp = int(pre_end * sr)
        
        feat = {
            'word': seg['word'],
            'start': start_s,
            'end': end_s,
            'label': label,
        }
        
        # Skip if window is too small
        if pre_end_samp - pre_start_samp < 160:  # min 10ms
            features.append(feat)
            continue
        
        window_y = y[pre_start_samp:pre_end_samp]
        
        # F0 extraction (pitch)
        try:
            f0, voiced_flag, _ = librosa.pyin(window_y, fmin=75, fmax=500, sr=sr)
            f0_clean = f0[~np.isnan(f0)]
            
            if len(f0_clean) > 3:
                feat['f0_mean'] = float(np.mean(f0_clean))
                feat['f0_std'] = float(np.std(f0_clean))
                feat['f0_range'] = float(np.max(f0_clean) - np.min(f0_clean))
                feat['f0_min'] = float(np.min(f0_clean))
                feat['f0_max'] = float(np.max(f0_clean))
                # Slope: is pitch rising or falling?
                if len(f0_clean) > 5:
                    coeffs = np.polyfit(np.arange(len(f0_clean)), f0_clean, 1)
                    feat['f0_slope'] = float(coeffs[0])  # Hz per frame
                feat['voiced_ratio'] = float(np.mean(voiced_flag))
            else:
                feat['voiced_ratio'] = 0.0
        except Exception:
            feat['voiced_ratio'] = 0.0
        
        # RMS energy
        rms = librosa.feature.rms(y=window_y)
        feat['rms_mean'] = float(np.mean(rms))
        
        # Actual pause from audio signal (amplitude-based silence detection)
        if start_s > 0:
            pause_start_samp = int(max(0, start_s - 0.5) * sr)
            pause_end_samp = pre_end_samp
            pause_y = y[pause_start_samp:pause_end_samp]
            # Percentage of frames below silence threshold
            frame_len = 512
            hop = 256
            n_frames = max(1, (len(pause_y) - frame_len) // hop)
            silent_frames = 0
            for j in range(n_frames):
                frame = pause_y[j*hop:j*hop+frame_len]
                if np.sqrt(np.mean(frame**2)) < 0.01:
                    silent_frames += 1
            feat['silence_ratio_before'] = silent_frames / max(n_frames, 1)
        
        features.append(feat)
    
    return features

def run_stat_tests(all_features, feat_name):
    """Run Welch's t-test comparing laughter vs non-laughter."""
    laugh = [f[feat_name] for f in all_features 
             if f['label'] == 1 and feat_name in f and not np.isnan(f.get(feat_name, np.nan))]
    no_laugh = [f[feat_name] for f in all_features 
                if f['label'] == 0 and feat_name in f and not np.isnan(f.get(feat_name, np.nan))]
    
    if len(laugh) < 10 or len(no_laugh) < 10:
        return None
    
    laugh_m = np.mean(laugh)
    no_m = np.mean(no_laugh)
    delta = laugh_m - no_m
    pooled_std = np.sqrt((np.var(laugh) + np.var(no_laugh)) / 2)
    d = delta / pooled_std if pooled_std > 0 else 0
    t, p = stats.ttest_ind(laugh, no_laugh, equal_var=False)
    
    return {
        'laugh_mean': float(laugh_m), 'no_laugh_mean': float(no_m),
        'delta': float(delta), 'cohens_d': float(d),
        'p_value': float(p), 'n_laugh': len(laugh), 'n_no_laugh': len(no_laugh),
        'significant': p < 0.01 and abs(d) > 0.15
    }

def main():
    print("Loading segments and checking audio existence...")
    by_video = load_segments(ALIGNED_FILE, MAX_VIDEOS)
    print(f"Selected {len(by_video)} videos with audio on disk\n")
    
    all_features = []
    for vid, segs in by_video.items():
        af = segs[0]['audio_file']
        n_laugh = sum(1 for s in segs if s['label'] == 1)
        print(f"  {vid}: {len(segs)} words, {n_laugh} laughter ({n_laugh/len(segs)*100:.1f}%), audio={os.path.basename(af)}")
        feats = extract_acoustic_features(segs)
        all_features.extend(feats)
        print(f"    → Extracted features for {len(feats)} words")
    
    print(f"\nTotal features: {len(all_features)}")
    
    # Test each hypothesis
    print(f"\n{'='*70}")
    print(f"H1.2: F0 PITCH CONTOUR CHANGES PRECEDE LAUGHTER WORDS")
    print(f"H1.5: SIMPLE ACOUSTIC FEATURES CAN CLASSIFY LAUGHTER")
    print(f"{'='*70}")
    
    for feat_name in ['f0_mean', 'f0_range', 'f0_slope', 'rms_mean', 'silence_ratio_before', 'voiced_ratio']:
        r = run_stat_tests(all_features, feat_name)
        if r:
            sig = "✅" if r['significant'] else "  "
            direction = "↑" if r['delta'] > 0 else "↓"
            print(f"\n{feat_name}:")
            print(f"  {sig} Laugh: {r['laugh_mean']:.4f} vs No-Laugh: {r['no_laugh_mean']:.4f} ({direction}{abs(r['delta']):.4f})")
            print(f"     Cohen's d = {r['cohens_d']:.3f}, p = {r['p_value']:.2e}")
            
            # Interpret
            d = r['cohens_d']
            if abs(d) < 0.2: effect = "negligible"
            elif abs(d) < 0.5: effect = "small"
            elif abs(d) < 0.8: effect = "medium"
            else: effect = "large"
            
            if r['significant']:
                print(f"     → Significant {effect} effect — acoustic feature differentiates laughter")
            else:
                print(f"     → Not significant / negligible — feature doesn't differentiate")
    
    # H1.5 specific: can simple features classify?
    print(f"\n--- H1.5: Can pause/energy alone predict laughter? ---")
    # Simple threshold classifier
    silence_laugh = [f['silence_ratio_before'] for f in all_features 
                     if 'silence_ratio_before' in f and f['label'] == 1]
    silence_nolaugh = [f['silence_ratio_before'] for f in all_features 
                       if 'silence_ratio_before' in f and f['label'] == 0]
    
    overall_silence = np.mean([f['silence_ratio_before'] for f in all_features if 'silence_ratio_before' in f])
    laugh_silence = np.mean(silence_laugh) if silence_laugh else 0
    print(f"  Overall silence ratio: {overall_silence:.4f}")
    print(f"  Laughter words: {laugh_silence:.4f}")
    if laugh_silence > overall_silence:
        print(f"  ✓ Laughter words preceded by MORE silence ({laugh_silence/overall_silence*100:.0f}% of avg)")
    else:
        print(f"  ✗ Laughter words preceded by LESS silence")
    
    # Save
    results = {
        'hypothesis': 'H1.2_H1.5',
        'n_videos': len(by_video),
        'n_words': len(all_features),
        'features_tested': ['f0_mean', 'f0_range', 'f0_slope', 'rms_mean', 'silence_ratio_before', 'voiced_ratio']
    }
    with open(OUTPUT_DIR / 'h1_2_h1_5_acoustic_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nResults saved.")

if __name__ == "__main__":
    main()
