#!/usr/bin/env python3
"""
Parallel prosody extraction for 1000+ videos.
Extracts 23-dim prosody (F0, energy, duration, spectral, voice quality)
for all available local audio files in parallel.
"""
import os
import sys
import json
import time
import numpy as np
import librosa
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm

# Audio directories
AUDIO_DIRS = [
    "/Users/Subho/data/utterances/vtt_audio_local",
    "/Users/Subho/autonomous_laughter_prediction_essential/data/utterances/audio",
    "/Users/Subho/autonomous_laughter_prediction/data/utterances/audio",
]

OUTPUT_DIR = Path("data/prosody_aligned")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CHECKPOINT_FILE = OUTPUT_DIR / "prosody_1000_checkpoint.json"
FINAL_FILE = OUTPUT_DIR / "prosody_1000_videos.npz"

SR = 16000

def extract_prosody_23dim(y, sr):
    """Extract 23-dim prosody features."""
    features = []
    
    # 1. F0 (pitch) - 5 dims
    try:
        f0, voiced_flag, voiced_probs = librosa.pyin(y, fmin=50, fmax=500, sr=sr)
        f0_clean = f0[~np.isnan(f0)]
        features.extend([
            np.mean(f0_clean) if len(f0_clean) > 0 else 0,
            np.std(f0_clean) if len(f0_clean) > 0 else 0,
            np.max(f0_clean) if len(f0_clean) > 0 else 0,
            np.min(f0_clean) if len(f0_clean) > 0 else 0,
            np.sum(voiced_flag) / len(voiced_flag) if len(voiced_flag) > 0 else 0
        ])
    except:
        features.extend([0] * 5)
    
    # 2. Energy - 5 dims
    rms = librosa.feature.rms(y=y)[0]
    features.extend([
        np.mean(rms),
        np.std(rms),
        np.max(rms),
        np.min(rms),
        np.max(rms) - np.min(rms)
    ])
    
    # 3. Duration - 2 dims
    features.extend([
        len(y) / sr,
        len(y) / sr / (np.sum(rms > np.mean(rms)) + 1)
    ])
    
    # 4. Spectral - 5 dims
    try:
        spec_cent = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        spec_bw = librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]
        spec_flat = librosa.feature.spectral_flatness(y=y)[0]
        zcr = librosa.feature.zero_crossing_rate(y)[0]
        features.extend([
            np.mean(spec_cent),
            np.mean(spec_bw),
            np.mean(spec_flat),
            np.mean(zcr),
            np.std(zcr)
        ])
    except:
        features.extend([0] * 5)
    
    # 5. Voice quality - 4 dims
    try:
        hnr = librosa.effects.hpss(y)[1]
        hnr_val = np.mean(hnr) / (np.mean(np.abs(y)) + 1e-8)
    except:
        hnr_val = 0
    features.extend([
        hnr_val,
        np.mean(np.abs(y)),
        np.std(y),
        np.max(np.abs(y))
    ])
    
    # 6. Delta features (velocity) - 2 dims
    try:
        delta_rms = np.diff(rms)
        features.extend([
            np.mean(np.abs(delta_rms)),
            np.max(np.abs(delta_rms))
        ])
    except:
        features.extend([0] * 2)
    
    return np.array(features, dtype=np.float32)


def load_audio(path):
    """Load audio file, handling different formats."""
    if path.endswith('.m4a'):
        y, sr = librosa.load(path, sr=SR, mono=True)
    else:
        try:
            import soundfile as sf
            y, sr = sf.read(path, dtype='float32')
            if len(y.shape) > 1:
                y = y.mean(axis=1)
        except:
            y, sr = librosa.load(path, sr=SR, mono=True)
    
    if sr != SR:
        y = librosa.resample(y, orig_sr=sr, target_sr=SR)
    
    return y


def process_video(args):
    """Process a single video - extract prosody for each utterance segment."""
    vid, utt_segments = args
    
    # Find audio file
    audio_path = None
    for audio_dir in AUDIO_DIRS:
        for ext in ['.m4a', '.mp3', '.wav']:
            p = Path(audio_dir) / f"{vid}{ext}"
            if p.exists():
                audio_path = str(p)
                break
        if audio_path:
            break
    
    if audio_path is None:
        return None, vid, 0, "No audio"
    
    try:
        y = load_audio(audio_path)
    except Exception as e:
        return None, vid, 0, f"Audio load error: {e}"
    
    prosody_list = []
    for seg in utt_segments:
        start_s = seg['start']
        end_s = seg['end']
        
        start_sample = int(start_s * SR)
        end_sample = int(end_s * SR)
        
        if end_sample > len(y):
            end_sample = len(y)
        
        y_slice = y[start_sample:end_sample]
        
        if len(y_slice) < SR * 0.1:  # Skip < 100ms
            prosody_list.append(np.zeros(23, dtype=np.float32))
        else:
            try:
                prosody = extract_prosody_23dim(y_slice, SR)
                prosody_list.append(prosody)
            except:
                prosody_list.append(np.zeros(23, dtype=np.float32))
    
    return vid, np.array(prosody_list, dtype=np.float32), len(utt_segments), None


def get_all_local_videos():
    """Get all video IDs with local audio."""
    all_vids = set()
    for audio_dir in AUDIO_DIRS:
        if os.path.exists(audio_dir):
            for f in os.listdir(audio_dir):
                if f.endswith(('.m4a', '.mp3', '.wav')):
                    vid = f.rsplit('.', 1)[0]
                    all_vids.add(vid)
    return sorted(all_vids)


def get_segments_from_utterances(vid):
    """Get utterance segments for a video from utterances_clean.jsonl."""
    import json
    
    utt_file = Path("data/utterances/utterances_clean.jsonl")
    if not utt_file.exists():
        return []
    
    segments = []
    with open(utt_file) as f:
        for line in f:
            try:
                d = json.loads(line)
                if d.get('video_id') == vid:
                    segments.append({
                        'start': d['start'],
                        'end': d['end'],
                        'text': d.get('text', ''),
                        'has_laughter': d.get('has_laughter', False),
                        'label': d.get('label', 0)
                    })
            except:
                pass
    
    return segments


def main():
    print("=" * 60)
    print("PARALLEL PROSODY EXTRACTION FOR 1000+ VIDEOS")
    print("=" * 60)
    
    # Get all local videos
    all_vids = get_all_local_videos()
    print(f"Total videos with audio: {len(all_vids)}")
    
    # Load checkpoint
    checkpoint = {}
    if CHECKPOINT_FILE.exists():
        with open(CHECKPOINT_FILE) as f:
            checkpoint = json.load(f)
        print(f"Checkpoint: {len(checkpoint)} already processed")
    
    # Process videos
    to_process = [v for v in all_vids if v not in checkpoint]
    print(f"To process: {len(to_process)}")
    
    all_prosody = dict(checkpoint)
    failed = []
    
    # Process in parallel
    with ProcessPoolExecutor(max_workers=os.cpu_count()) as executor:
        futures = {}
        
        for vid in to_process[:100]:  # Start with 100 for now
            segments = get_segments_from_utterances(vid)
            if segments:
                future = executor.submit(process_video, (vid, segments))
                futures[future] = vid
        
        for future in tqdm(as_completed(futures), total=len(futures)):
            vid = futures[future]
            result_vid, prosody_arr, n_segs, error = future.result()
            
            if prosody_arr is not None and len(prosody_arr) > 0:
                all_prosody[result_vid] = prosody_arr
                # Save checkpoint every 10 videos
                if len(all_prosody) % 10 == 0:
                    with open(CHECKPOINT_FILE, 'w') as f:
                        json.dump(all_prosody, f)
                    print(f"\nCheckpoint saved: {len(all_prosody)} videos")
            else:
                failed.append((vid, error or "Unknown"))
            
            if len(all_prosody) % 50 == 0:
                print(f"\nProgress: {len(all_prosody)}/{len(to_process[:100])}")
    
    # Save final
    print(f"\nTotal processed: {len(all_prosody)} videos")
    print(f"Failed: {len(failed)}")
    
    # Convert to arrays and save
    all_vids_out = []
    all_prosody_out = []
    all_labels_out = []
    
    for vid in sorted(all_prosody.keys()):
        arr = all_prosody[vid]
        segments = get_segments_from_utterances(vid)
        
        for i, seg in enumerate(segments[:len(arr)]):
            all_vids_out.append(vid)
            all_prosody_out.append(arr[i])
            all_labels_out.append(seg.get('label', 0))
    
    if all_prosody_out:
        np.savez_compressed(
            FINAL_FILE,
            prosody=np.array(all_prosody_out, dtype=np.float32),
            labels=np.array(all_labels_out, dtype=np.int32),
            vids=np.array(all_vids_out),
        )
        print(f"Saved: {FINAL_FILE}")
        print(f"Total utterances: {len(all_prosody_out)}")
        print(f"Positive: {sum(all_labels_out)} ({100*np.mean(all_labels_out):.1f}%)")


if __name__ == "__main__":
    main()
