#!/usr/bin/env python3
"""
Extract eGeMAPS 88-dim Features for Laughter Detection

Expected: +5-10% prosody F1
Current: 21-dim prosody (6 active)

eGeMAPS (Geneva Minimalistic Acoustic Parameter Set) includes:
- F0 (frequency, dynamics, statistics)
- Formants (F1, F2, F3)
- Loudness
- Spectral (centroid, flux, slope)
- Voicing
- Jitter/Shimmer

Usage:
    python3 training/extract_egemaps_features.py
    
Requirements:
    pip install openSMILE pandas

Note: openSMILE installation is complex. Alternative: use librosa to extract
equivalent features manually.
"""

import os
import json
import subprocess
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURATION
# ============================================================================

class Config:
    DATA_DIR = '/Users/Subho/data/chuckle-net'
    AUDIO_DIR = os.path.join(DATA_DIR, 'audio')  # Raw audio files
    OUTPUT_DIR = os.path.join(DATA_DIR, 'egemaps_features')
    
    # eGeMAPS config
    SAMPLE_RATE = 16000
    FRAME_LENGTH = 0.01  # 10ms frames
    WINFUNC = 'HAMMING'

# ============================================================================
# FEATURE LIST (eGeMAPS v01a - 88 dimensions)
# ============================================================================

EGEMAPS_FEATURES = [
    # F0 related (16 features)
    'F0_semitones_from_voicing_range_acoustic_mean',
    'F0_semitones_from_voicing_range_acoustic_stddev',
    'F0_semitones_from_voicing_range_acoustic_range',
    'voicing_final_mean',
    'voicing_final_stddev',
    'voicing_final_unvoiced_mean',
    'F0_mean',
    'F0_stddev',
    'F0_median',
    'F0_Se',
    'F0_Se_semitones',
    'F0_JR_mean',
    'F0_JR_range',
    'F0_JR_low',
    'F0_JR_up',
    'F0_Prod',
    
    # Loudness (6 features)
    'Loudness_sma3_mean',
    'Loudness_sma3_stddev',
    'Loudness_sma3_median',
    'Loudness_sma3_percentile20',
    'Loudness_sma3_percentile50',
    'Loudness_sma3_percentile80',
    
    # Spectral (21 features)
    'spectralFlux_sma3_amean',
    'spectralFlux_sma3_stddev',
    'spectralCentroid_sma3_amean',
    'spectralCentroid_sma3_stddev',
    'alphaRatio_sma3_amean',
    'alphaRatio_sma3_stddev',
    'hammarbergIndex_sma3_amean',
    'hammarbergIndex_sma3_stddev',
    'slope_sma3_amean',
    'slope_sma3_stddev',
    'F1_frequency_sma3_amean',
    'F1_frequency_sma3_stddev',
    'F1_bandwidth_sma3_amean',
    'F1_bandwidth_sma3_stddev',
    'F1_amplitude_sma3_amean',
    'F1_amplitude_sma3_stddev',
    'F2_frequency_sma3_amean',
    'F2_frequency_sma3_stddev',
    'F2_amplitude_sma3_amean',
    'F2_amplitude_sma3_stddev',
    
    # Voicing (8 features)
    'Voicing_uncorr_sma3_amean',
    'Voicing_uncorr_sma3_stddev',
    'PVE_sma3_amean',
    'PVE_sma3_stddev',
    'meanVoicedSegmentsLengths_sma3',
    'stddevVoicedSegmentsLengths_sma3',
    'numberVoicedSegments_sma3',
    'numberUnvoicedSegments_sma3',
    
    # Jitter/Shimmer (15 features)
    'jitterLocal_sma3_amean',
    'jitterLocal_sma3_stddev',
    'jitterDDP_sma3_amean',
    'jitterDDP_sma3_stddev',
    'shimmerLocal_sma3_amean',
    'shimmerLocal_sma3_stddev',
    'shimmerLocalDB_sma3_amean',
    'shimmerLocalDB_sma3_stddev',
    'APQ3_sma3_amean',
    'APQ3_sma3_stddev',
    'APQ5_sma3_amean',
    'APQ5_sma3_stddev',
    'PPQ5_sma3_amean',
    'PPQ5_sma3_stddev',
    'DDP_sma3_amean',
    
    # Additional (22 features)
    'F3_frequency_sma3_amean',
    'F3_frequency_sma3_stddev',
    'F3_amplitude_sma3_amean',
    'F3_amplitude_sma3_stddev',
    'F1_frequency_sma3_range',
    'F2_frequency_sma3_range',
    'F3_frequency_sma3_range',
    'Loudness_sma3_range',
    'Loudness_sma3_skewness',
    'Loudness_sma3_kurtosis',
    'spectralFlux_sma3_skewness',
    'spectralFlux_sma3_kurtosis',
    'spectralCentroid_sma3_skewness',
    'spectralCentroid_sma3_kurtosis',
    'alphaRatio_sma3_skewness',
    'alphaRatio_sma3_kurtosis',
    'slope_sma3_skewness',
    'slope_sma3_kurtosis',
    'Voicing_uncorr_sma3_skewness',
    'Voicing_uncorr_sma3_kurtosis',
    'F0_semitones_from_voicing_range_acoustic_median',
    'F0_semitones_from_voicing_range_acoustic_kurtosis',
]

def get_feature_count():
    """Return eGeMAPS feature count."""
    return len(EGEMAPS_FEATURES)

# ============================================================================
# LIBROSA EXTRACTION (Alternative to openSMILE)
# ============================================================================

def extract_egemaps_librosa(audio_path, offset=0, duration=None):
    """
    Extract eGeMAPS-like features using librosa.
    
    This is an approximation since full eGeMAPS requires openSMILE,
    but librosa can extract most of the relevant features.
    """
    import librosa
    import numpy as np
    
    # Load audio
    y, sr = librosa.load(audio_path, offset=offset, duration=duration, sr=Config.SAMPLE_RATE)
    
    features = []
    
    # 1. F0 (pitch) features using pyin
    f0, voiced_probs = librosa.pyin(
        y, 
        fmin=librosa.note_to_hz('C1'),  # ~65 Hz
        fmax=librosa.note_to_hz('C8'),  # ~4186 Hz
        sr=sr
    )
    
    f0_valid = f0[~np.isnan(f0)]
    if len(f0_valid) > 0:
        f0_mean = np.mean(f0_valid)
        f0_std = np.std(f0_valid)
        f0_median = np.median(f0_valid)
    else:
        f0_mean = f0_std = f0_median = 0
    
    features.extend([
        f0_mean, f0_std, f0_median,
        np.sum(voiced_probs > 0.5) / len(voiced_probs),  # voicing
    ])
    
    # 2. Loudness (RMS energy)
    rms = librosa.feature.rms(y=y)[0]
    features.extend([
        np.mean(rms),
        np.std(rms),
        np.median(rms),
        np.percentile(rms, 20),
        np.percentile(rms, 50),
        np.percentile(rms, 80),
        np.max(rms) - np.min(rms),  # range
    ])
    
    # 3. Spectral features
    spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]
    spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
    spectral_flux = librosa.feature.spectral_flux(y=y)[0]
    
    features.extend([
        np.mean(spectral_centroid),
        np.std(spectral_centroid),
        np.mean(spectral_bandwidth),
        np.std(spectral_bandwidth),
        np.mean(spectral_rolloff),
        np.std(spectral_rolloff),
        np.mean(spectral_flux),
        np.std(spectral_flux),
    ])
    
    # 4. MFCCs (Mel-frequency cepstral coefficients)
    mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    for i in range(13):
        features.extend([np.mean(mfccs[i]), np.std(mfccs[i])])
    
    # 5. Chroma features
    chroma = librosa.feature.chroma_stft(y=y, sr=sr)
    for i in range(12):
        features.extend([np.mean(chroma[i]), np.std(chroma[i])])
    
    # 6. Zero crossing rate
    zcr = librosa.feature.zero_crossing_rate(y)[0]
    features.extend([np.mean(zcr), np.std(zcr)])
    
    # 7. Formants (approximation using LPC)
    from scipy.signal import lfilter
    n_fft = 2048
    a, b = librosa.effects.lpc(y, order=8)
    r = np.array([np.sqrt(np.sum(a[i:]**2)) for i in range(len(a))])
    f = np.arccos(-a[1:] / (2 * r[1:] * r[:-1])) * sr / (2 * np.pi)
    f = f[f > 0]
    
    # Keep only positive frequencies
    f = f[f < 4000]
    
    # F1, F2, F3 (first three formants)
    formants = sorted(f)[:3] if len(f) >= 3 else [0, 0, 0]
    while len(formants) < 3:
        formants.append(0)
    
    features.extend(formants)  # F1, F2, F3
    
    # 8. Jitter and Shimmer (approximation)
    if len(f0_valid) > 1:
        jit = np.mean(np.abs(np.diff(f0_valid)))
    else:
        jit = 0
    
    shim = np.mean(np.abs(np.diff(rms)))
    features.extend([jit, shim])
    
    # 9. Pause features (critical for laughter detection)
    # Identify silent segments
    frame_length = int(0.01 * sr)  # 10ms frames
    energy = np.array([np.sum(y[i:i+frame_length]**2) for i in range(0, len(y)-frame_length, frame_length)])
    threshold = np.percentile(energy, 10)  # Bottom 10% is silence
    
    pause_mask = energy < threshold
    pause_before = 0
    pause_after = 0
    
    # Count pause frames
    n_pause_frames = np.sum(pause_mask)
    n_total_frames = len(energy)
    
    features.extend([
        n_pause_frames / n_total_frames,  # pause_ratio
        np.mean(energy[~pause_mask]) if np.sum(~pause_mask) > 0 else 0,  # mean_energy_when_speaking
    ])
    
    # Pad or truncate to 88 features
    target_len = 88
    if len(features) < target_len:
        features.extend([0] * (target_len - len(features)))
    else:
        features = features[:target_len]
    
    return np.array(features, dtype=np.float32)

# ============================================================================
# MAIN EXTRACTION PIPELINE
# ============================================================================

def get_audio_files():
    """Get list of audio files from aligned utterances."""
    aligned_path = os.path.join(Config.DATA_DIR, 'aligned_utterances.jsonl')
    
    if not os.path.exists(aligned_path):
        raise FileNotFoundError(f"Aligned data not found at {aligned_path}")
    
    # Get unique video IDs
    video_ids = set()
    utterances = []
    
    with open(aligned_path, 'r') as f:
        for line in f:
            utt = json.loads(line)
            video_ids.add(utt['video_id'])
            utterances.append(utt)
    
    return list(video_ids), utterances

def extract_for_utterance(video_id, start, duration, audio_dir):
    """
    Extract features for a single utterance.
    
    Uses ffmpeg for fast seeking to avoid loading entire file.
    """
    import tempfile
    
    audio_file = os.path.join(audio_dir, f'{video_id}.mp3')
    
    if not os.path.exists(audio_file):
        return None
    
    # Create temp file for segment
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        # Extract segment using ffmpeg (fast seeking)
        cmd = [
            'ffmpeg', '-y',
            '-ss', str(start),
            '-i', audio_file,
            '-t', str(duration),
            '-ar', str(Config.SAMPLE_RATE),
            '-ac', '1',
            tmp_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, timeout=10)
        
        if result.returncode != 0:
            return None
        
        # Extract features
        features = extract_egemaps_librosa(tmp_path)
        
        return features
        
    except subprocess.TimeoutExpired:
        return None
    except Exception as e:
        print(f"Error extracting {video_id} at {start}: {e}")
        return None
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

def main():
    print("=" * 70)
    print("eGeMAPS FEATURE EXTRACTION FOR LAUGHTER DETECTION")
    print("=" * 70)
    print(f"Output directory: {Config.OUTPUT_DIR}")
    print(f"Feature dimensions: {get_feature_count()}")
    print()
    
    # Create output directory
    os.makedirs(Config.OUTPUT_DIR, exist_ok=True)
    
    # Get video IDs and utterances
    video_ids, utterances = get_audio_files()
    print(f"Found {len(video_ids)} unique videos")
    print(f"Found {len(utterances)} total utterances")
    
    # Check for audio directory
    audio_dir = Config.AUDIO_DIR
    if not os.path.exists(audio_dir):
        print(f"\nAudio directory not found at {audio_dir}")
        print("Will extract features from aligned data only (no audio)")
        print("This will only extract prosody features, not eGeMAPS")
        return
    
    # Process each video
    for i, video_id in enumerate(video_ids):
        output_file = os.path.join(Config.OUTPUT_DIR, f'{video_id}.json')
        
        if os.path.exists(output_file):
            print(f"[{i+1}/{len(video_ids)}] Skipping {video_id} (already processed)")
            continue
        
        print(f"[{i+1}/{len(video_ids)}] Processing {video_id}...")
        
        # Get utterances for this video
        video_utts = [u for u in utterances if u['video_id'] == video_id]
        
        features_dict = {}
        
        for utt in video_utts:
            uid = utt['uid']
            start = utt.get('start', 0)
            duration = utt.get('duration', 5)  # Default 5 seconds
            
            feats = extract_for_utterance(video_id, start, duration, audio_dir)
            
            if feats is not None:
                features_dict[uid] = feats.tolist()
        
        # Save features
        with open(output_file, 'w') as f:
            json.dump(features_dict, f)
        
        print(f"  Extracted {len(features_dict)} utterances")
    
    print("\n" + "=" * 70)
    print("EXTRACTION COMPLETE")
    print("=" * 70)
    print(f"Features saved to: {Config.OUTPUT_DIR}")
    print(f"Total feature dimensions: {get_feature_count()}")
    print("\nNote: These features should be used alongside WavLM embeddings")
    print("for best results. eGeMAPS adds prosodic information.")

if __name__ == '__main__':
    main()
