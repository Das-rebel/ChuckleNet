#!/usr/bin/env python3
"""
FAST F0 extraction - optimized version.
Uses frame-by-frame pyin on full audio, then slices per utterance.
"""
import json, os, time
import numpy as np
import librosa
from pathlib import Path
from collections import defaultdict

SR = 16000
HOP = 512  # Frame hop for pyin
AUDIO_DIR = Path('/Users/Subho/data/utterances/vtt_audio_local')
UTT_FILE = Path('/Users/Subho/autonomous_laughter_prediction_essential/data/utterances/utterances_clean.jsonl')
OUTPUT_FILE = Path('/Users/Subho/autonomous_laughter_prediction_essential/data/prosody_aligned/f0_all_videos.npz')
CHECKPOINT_FILE = Path('/Users/Subho/autonomous_laughter_prediction_essential/data/prosody_aligned/f0_checkpoint.json')

def extract_f0_from_track(f0_track, voiced_flags, start_s, end_s):
    """Slice F0 track for an utterance and compute 5 features."""
    start_frame = int(start_s * SR / HOP)
    end_frame = int(end_s * SR / HOP)
    
    if end_frame > len(f0_track):
        end_frame = len(f0_track)
    if start_frame >= end_frame:
        return np.zeros(5, dtype=np.float32)
    
    seg_f0 = f0_track[start_frame:end_frame]
    seg_voiced = voiced_flags[start_frame:end_frame]
    f0_clean = seg_f0[~np.isnan(seg_f0)]
    
    return np.array([
        np.mean(f0_clean) if len(f0_clean) > 0 else 0,
        np.std(f0_clean) if len(f0_clean) > 0 else 0,
        np.max(f0_clean) if len(f0_clean) > 0 else 0,
        np.min(f0_clean) if len(f0_clean) > 0 else 0,
        np.sum(seg_voiced) / len(seg_voiced) if len(seg_voiced) > 0 else 0,
    ], dtype=np.float32)

def main():
    print("Loading utterances...")
    utterances_by_video = defaultdict(list)
    with open(UTT_FILE) as f:
        for line in f:
            d = json.loads(line)
            utterances_by_video[d['video_id']].append(d)
    
    local_vids = set(f.replace('.m4a', '') for f in os.listdir(AUDIO_DIR) if f.endswith('.m4a'))
    videos_with_laughter = set()
    for vid, utts in utterances_by_video.items():
        if any(u.get('label', 0) == 1 or u.get('has_laughter', False) for u in utts):
            videos_with_laughter.add(vid)
    target_vids = sorted(videos_with_laughter & local_vids)
    
    # Load checkpoint
    processed = set()
    all_f0, all_labels, all_uids = [], [], []
    if CHECKPOINT_FILE.exists():
        with open(CHECKPOINT_FILE) as f:
            cp = json.load(f)
        processed = set(cp.get('processed', []))
    
    # Load any existing partial output
    if OUTPUT_FILE.exists():
        d = np.load(OUTPUT_FILE, allow_pickle=True)
        all_f0 = list(d['f0_features'])
        all_labels = list(d['labels'])
        all_uids = list(d['uids'])
        print(f"Loaded {len(all_f0)} existing utterances")
    
    remaining = [v for v in target_vids if v not in processed]
    print(f"Total: {len(target_vids)} | Done: {len(processed)} | Remaining: {len(remaining)}")
    
    t0 = time.time()
    failed = 0
    
    for vi, vid in enumerate(remaining):
        audio_path = AUDIO_DIR / f'{vid}.m4a'
        if not audio_path.exists():
            failed += 1
            continue
        
        try:
            # Load audio ONCE
            y, sr = librosa.load(str(audio_path), sr=SR, mono=True)
            
            # Extract F0 for ENTIRE audio in one pass (fast)
            f0_track, voiced_flags = librosa.pyin(
                y, fmin=50, fmax=500, sr=SR,
                frame_length=2048, hop_length=HOP
            )
            voiced_flags = voiced_flags.astype(bool)
            
            # Slice per utterance
            for utt in utterances_by_video.get(vid, []):
                f0_feat = extract_f0_from_track(
                    f0_track, voiced_flags, utt['start'], utt['end']
                )
                label = 1 if utt.get('label', 0) == 1 or utt.get('has_laughter', False) else 0
                
                all_f0.append(f0_feat)
                all_labels.append(label)
                all_uids.append(f"{vid}_{utt['start']:.2f}")
            
            processed.add(vid)
            
        except Exception as e:
            print(f"  Error {vid}: {e}")
            failed += 1
        
        # Progress + checkpoint every 5 videos
        if (vi + 1) % 5 == 0 or vi == len(remaining) - 1:
            elapsed = time.time() - t0
            done_in_batch = vi + 1
            remaining_after = len(remaining) - done_in_batch
            eta = elapsed / done_in_batch * remaining_after / 60
            print(f"  {len(processed)}/{len(target_vids)} | {len(all_f0):,} utts | "
                  f"ETA: {eta:.0f}min | Failed: {failed}")
            
            # Save checkpoint + partial output
            with open(CHECKPOINT_FILE, 'w') as f:
                json.dump({'processed': list(processed)}, f)
            np.savez(OUTPUT_FILE,
                     f0_features=np.array(all_f0, dtype=np.float32),
                     labels=np.array(all_labels, dtype=np.int64),
                     uids=np.array(all_uids, dtype=object))
    
    elapsed = time.time() - t0
    pos_rate = np.mean(all_labels) * 100 if all_labels else 0
    print(f"\n{'='*60}")
    print(f"DONE in {elapsed/60:.1f} min")
    print(f"Videos: {len(processed)} | Utterances: {len(all_f0):,}")
    print(f"Positive: {sum(all_labels):,} ({pos_rate:.1f}%)")
    print(f"Failed: {failed}")
    print(f"Saved: {OUTPUT_FILE}")

if __name__ == '__main__':
    main()
