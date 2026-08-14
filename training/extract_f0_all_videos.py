#!/usr/bin/env python3
"""
Extract 5 F0 (pitch) features for ALL videos with laughter.
Fast CPU-only extraction - no GPU, no Colab needed.

Features: f0_mean, f0_std, f0_max, f0_min, voiced_rate
"""
import json
import os
import time
import numpy as np
import librosa
from pathlib import Path
from collections import defaultdict

SR = 16000
AUDIO_DIR = Path('/Users/Subho/data/utterances/vtt_audio_local')
UTT_FILE = Path('/Users/Subho/autonomous_laughter_prediction_essential/data/utterances/utterances_clean.jsonl')
OUTPUT_FILE = Path('/Users/Subho/autonomous_laughter_prediction_essential/data/prosody_aligned/f0_all_videos.npz')
CHECKPOINT_FILE = Path('/Users/Subho/autonomous_laughter_prediction_essential/data/prosody_aligned/f0_checkpoint.json')

def extract_f0_5dim(y, sr=SR):
    """Extract 5 F0 features from audio segment."""
    try:
        if len(y) < sr * 0.05:  # Skip very short segments
            return np.zeros(5, dtype=np.float32)
        
        f0, voiced_flag, voiced_probs = librosa.pyin(
            y, fmin=50, fmax=500, sr=sr,
            frame_length=2048
        )
        f0_clean = f0[~np.isnan(f0)]
        
        return np.array([
            np.mean(f0_clean) if len(f0_clean) > 0 else 0,
            np.std(f0_clean) if len(f0_clean) > 0 else 0,
            np.max(f0_clean) if len(f0_clean) > 0 else 0,
            np.min(f0_clean) if len(f0_clean) > 0 else 0,
            np.sum(voiced_flag) / len(voiced_flag) if len(voiced_flag) > 0 else 0,
        ], dtype=np.float32)
    except:
        return np.zeros(5, dtype=np.float32)

def main():
    # Load utterances
    print("Loading utterances...")
    utterances_by_video = defaultdict(list)
    with open(UTT_FILE) as f:
        for line in f:
            d = json.loads(line)
            utterances_by_video[d['video_id']].append(d)
    
    # Find videos with laughter + local audio
    local_vids = set(f.replace('.m4a', '') for f in os.listdir(AUDIO_DIR) if f.endswith('.m4a'))
    
    # Get videos with at least 1 positive utterance
    videos_with_laughter = set()
    for vid, utts in utterances_by_video.items():
        if any(u.get('label', 0) == 1 or u.get('has_laughter', False) for u in utts):
            videos_with_laughter.add(vid)
    
    target_vids = videos_with_laughter & local_vids
    print(f"Videos with laughter + audio: {len(target_vids)}")
    
    # Load checkpoint
    processed = set()
    if CHECKPOINT_FILE.exists():
        with open(CHECKPOINT_FILE) as f:
            cp = json.load(f)
        processed = set(cp.get('processed', []))
    print(f"Already processed: {len(processed)}")
    
    # Extract
    all_f0 = []
    all_labels = []
    all_uids = []
    all_vids = []
    failed = 0
    t0 = time.time()
    
    for vi, vid in enumerate(sorted(target_vids)):
        if vid in processed:
            continue
        
        audio_path = AUDIO_DIR / f'{vid}.m4a'
        if not audio_path.exists():
            failed += 1
            continue
        
        try:
            # Load full audio
            y_full, sr = librosa.load(str(audio_path), sr=SR, mono=True)
            
            # Extract F0 for each utterance
            for utt in utterances_by_video[vid]:
                start = utt['start']
                end = utt['end']
                label = 1 if utt.get('label', 0) == 1 or utt.get('has_laughter', False) else 0
                
                start_sample = int(start * SR)
                end_sample = int(end * SR)
                
                if end_sample > len(y_full):
                    end_sample = len(y_full)
                if start_sample >= end_sample:
                    continue
                
                y_seg = y_full[start_sample:end_sample]
                f0_features = extract_f0_5dim(y_seg, SR)
                
                all_f0.append(f0_features)
                all_labels.append(label)
                all_uids.append(f"{vid}_{start:.2f}")
                all_vids.append(vid)
            
            processed.add(vid)
            
        except Exception as e:
            print(f"  Error {vid}: {e}")
            failed += 1
        
        # Checkpoint every 10 videos
        if (vi + 1) % 10 == 0:
            elapsed = time.time() - t0
            done = len(processed)
            remaining = len(target_vids) - done
            eta = elapsed / max(done, 1) * remaining / 60
            print(f"  {done}/{len(target_vids)} videos | {len(all_f0):,} utterances | "
                  f"ETA: {eta:.0f} min | Failed: {failed}")
            
            # Save checkpoint
            with open(CHECKPOINT_FILE, 'w') as f:
                json.dump({'processed': list(processed)}, f)
    
    # Save final
    all_f0 = np.array(all_f0, dtype=np.float32)
    all_labels = np.array(all_labels, dtype=np.int64)
    all_uids = np.array(all_uids, dtype=object)
    
    np.savez(OUTPUT_FILE,
             f0_features=all_f0,
             labels=all_labels,
             uids=all_uids)
    
    elapsed = time.time() - t0
    pos_rate = all_labels.mean() * 100 if len(all_labels) > 0 else 0
    
    print(f"\n{'='*60}")
    print(f"DONE in {elapsed/60:.1f} min")
    print(f"{'='*60}")
    print(f"Videos: {len(processed)}")
    print(f"Utterances: {len(all_f0):,}")
    print(f"Positive: {all_labels.sum():,} ({pos_rate:.1f}%)")
    print(f"Failed: {failed}")
    print(f"Saved to: {OUTPUT_FILE}")
    
    # Final checkpoint
    with open(CHECKPOINT_FILE, 'w') as f:
        json.dump({'processed': list(processed)}, f)

if __name__ == '__main__':
    main()
