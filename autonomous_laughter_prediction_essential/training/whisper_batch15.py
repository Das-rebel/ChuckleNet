#!/usr/bin/env python3
"""
Batch transcribe batch15 MP3s with faster-whisper.
Processes 214 MP3s in batch15/ and saves transcripts to transcripts/batch15/

Usage:
    python training/whisper_batch15.py --model tiny --device cpu
    python training/whisper_batch15.py --model base --device cuda
"""

import os
import json
import time
import argparse
from pathlib import Path
from faster_whisper import WhisperModel

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="tiny", choices=["tiny", "base", "small"])
    parser.add_argument("--device", default="cpu", choices=["cpu", "cuda"])
    parser.add_argument("--compute-type", default="int8")
    args = parser.parse_args()
    
    mp3_dir = "data/audio_comedy/audio/batch15"
    output_dir = "data/audio_comedy/transcripts/batch15"
    os.makedirs(output_dir, exist_ok=True)
    
    # Get MP3s
    mp3s = sorted([f for f in os.listdir(mp3_dir) if f.endswith('.mp3')])
    print(f"Found {len(mp3s)} MP3s in {mp3_dir}")
    
    # Load model
    print(f"Loading Whisper {args.model} on {args.device}...")
    t0 = time.time()
    model = WhisperModel(args.model, device=args.device, compute_type=args.compute_type)
    print(f"Loaded in {time.time()-t0:.1f}s")
    
    # Process
    total_words = 0
    total_duration = 0
    success = 0
    failed = 0
    start = time.time()
    
    for i, mp3 in enumerate(mp3s):
        mp3_path = os.path.join(mp3_dir, mp3)
        video_id = mp3.replace('.mp3', '')
        output_path = os.path.join(output_dir, f"{video_id}_transcript.json")
        
        if os.path.exists(output_path):
            print(f"[{i+1:3d}/{len(mp3s)}] {video_id}: exists")
            continue
        
        try:
            segments, info = model.transcribe(mp3_path, word_timestamps=True)
            words = []
            for seg in segments:
                for word in seg.words:
                    words.append({
                        "word": word.word.strip(),
                        "start": word.start,
                        "end": word.end,
                    })
            
            result = {
                "video_id": video_id,
                "language": info.language,
                "duration": info.duration,
                "words": words,
                "word_count": len(words),
            }
            
            with open(output_path, 'w') as f:
                json.dump(result, f)
            
            total_words += len(words)
            total_duration += info.duration
            success += 1
            
            if (i + 1) % 10 == 0:
                elapsed = time.time() - start
                rt = total_duration / elapsed if elapsed > 0 else 0
                print(f"[{i+1:3d}/{len(mp3s)}] {video_id}: {len(words):4d} words | "
                      f"RT={rt:.1f}x | {elapsed/60:.1f}m elapsed")
            else:
                print(f"[{i+1:3d}/{len(mp3s)}] {video_id}: {len(words):4d} words")
                
        except Exception as e:
            failed += 1
            print(f"[{i+1:3d}/{len(mp3s)}] {video_id}: ERROR - {e}")
    
    elapsed = time.time() - start
    print(f"\n{'='*60}")
    print(f"Complete: {success} success, {failed} failed")
    print(f"Total words: {total_words:,}")
    print(f"Total audio: {total_duration/3600:.1f} hours")
    print(f"Time: {elapsed/60:.1f}m")
    print(f"Realtime: {total_duration/elapsed:.1f}x")
    print(f"Output: {output_dir}/")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
