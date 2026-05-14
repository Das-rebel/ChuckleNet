#!/usr/bin/env python3
"""
Batch transcribe audio files with faster-whisper.
Processes files from GDrive or local, saves transcripts to GDrive.

Usage:
    python training/whisper_batch_gdrive.py --lang en --model tiny
    python training/whisper_batch_gdrive.py --lang zh --model base --device cuda
    python training/whisper_batch_gdrive.py --lang hi-latn --model large-v3 --resume
"""

import json
import os
import time
import argparse
from pathlib import Path
from collections import Counter

import torch
from faster_whisper import WhisperModel

# ── Config ──────────────────────────────────────────────────────────
GDRIVE_BASE = "gdrive:laughter_prediction"
DEFAULT_DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
COMPUTE_TYPE = "float16" if torch.cuda.is_available() else "int8"


def transcribe_audio(model: WhisperModel, audio_path: str, output_path: str) -> dict:
    """Transcribe single audio file with word timestamps."""
    try:
        segments, info = model.transcribe(
            audio_path,
            word_timestamps=True,
            condition_on_previous_text=False,
            initial_prompt="This is a comedy performance with audience laughter.",
        )
        
        # Convert to our format
        words = []
        for segment in segments:
            for word in segment.words:
                words.append({
                    "word": word.word.strip(),
                    "start": word.start,
                    "end": word.end,
                    "confidence": getattr(word, "probability", 1.0),
                })
        
        result = {
            "language": info.language,
            "language_probability": info.language_probability,
            "duration": info.duration,
            "words": words,
            "transcript": " ".join(w["word"] for w in words),
        }
        
        # Save transcript
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(result, f, indent=2)
        
        return {"status": "ok", "words": len(words), "duration": info.duration}
        
    except Exception as e:
        return {"status": "error", "error": str(e)[:200]}


def main():
    parser = argparse.ArgumentParser(description="Batch Whisper transcription")
    parser.add_argument("--lang", choices=["en", "zh", "hi-latn"], required=True)
    parser.add_argument("--model", default="tiny",
                        choices=["tiny", "base", "small", "medium", "large-v1", "large-v2", "large-v3"])
    parser.add_argument("--device", default=DEFAULT_DEVICE)
    parser.add_argument("--compute-type", default=COMPUTE_TYPE)
    parser.add_argument("--audio-dir", default=None, help="Local audio dir (default: GDrive)")
    parser.add_argument("--output-dir", default=None, help="Output dir (default: GDrive)")
    parser.add_argument("--workers", type=int, default=1, help="Parallel workers (1 = sequential)")
    parser.add_argument("--batch-size", type=int, default=10, help="Progress report every N files")
    parser.add_argument("--resume", action="store_true", help="Skip existing transcripts")
    args = parser.parse_args()
    
    # Determine paths
    if args.audio_dir:
        audio_base = args.audio_dir
        local_mode = True
    else:
        audio_base = f"{GDRIVE_BASE}/audio/{args.lang}"
        local_mode = False
    
    if args.output_dir:
        output_base = args.output_dir
    else:
        output_base = f"{GDRIVE_BASE}/transcripts/{args.lang}"
    
    print(f"Whisper batch transcription")
    print(f"Model: {args.model} | Device: {args.device} | Compute: {args.compute_type}")
    print(f"Language: {args.lang}")
    print(f"Audio: {audio_base}")
    print(f"Output: {output_base}")
    
    # Load Whisper model
    print(f"\nLoading Whisper {args.model}...")
    t0 = time.time()
    model = WhisperModel(args.model, device=args.device, compute_type=args.compute_type)
    load_time = time.time() - t0
    print(f"Loaded in {load_time:.1f}s")
    
    # Get list of audio files
    if local_mode:
        audio_files = list(Path(audio_base).glob(f"*.{args.lang}/*.mp3")) + \
                      list(Path(audio_base).glob(f"*.{args.lang}/*.m4a")) + \
                      list(Path(audio_base).glob(f"*.{args.lang}/*.wav"))
        audio_files += list(Path(audio_base).glob("*.mp3"))
    else:
        # Use rclone to list files
        import subprocess
        result = subprocess.run(
            ["rclone", "lsf", audio_base],
            capture_output=True, text=True
        )
        audio_files = [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]
        audio_files = [f for f in audio_files if f.endswith((".mp3", ".m4a", ".wav"))]
    
    print(f"\nFound {len(audio_files)} audio files")
    
    # Process files
    stats = Counter()
    total_duration = 0.0
    total_words = 0
    start = time.time()
    
    for i, audio_file in enumerate(audio_files):
        # Determine paths
        if isinstance(audio_file, Path):
            audio_path = str(audio_file)
            video_id = audio_file.stem
        else:
            audio_path = f"{audio_base}/{audio_file}"
            video_id = Path(audio_file).stem
        
        output_path = f"{output_base}/{video_id}_transcript.json"
        
        # Check if exists
        if args.resume:
            if local_mode and os.path.exists(output_path):
                stats["skipped"] += 1
                continue
            # For GDrive, would need rclone check (omitted for speed)
        
        # Transcribe
        result = transcribe_audio(model, audio_path, output_path)
        stats[result["status"]] += 1
        
        if result["status"] == "ok":
            total_duration += result["duration"]
            total_words += result["words"]
            print(f"  ✓ {video_id}: {result['words']} words, {result['duration']:.1f}s")
        else:
            print(f"  ✗ {video_id}: {result.get('error', 'unknown')}")
        
        # Progress report
        if (i + 1) % args.batch_size == 0:
            elapsed = time.time() - start
            rate = (i + 1) / elapsed
            eta = (len(audio_files) - i - 1) / rate
            realtime_factor = total_duration / elapsed if elapsed > 0 else 0
            print(f"\n  Progress: {i+1}/{len(audio_files)}")
            print(f"  Speed: {rate:.1f} files/s | Realtime: {realtime_factor:.1f}x")
            print(f"  ETA: {eta/60:.0f}m | Total audio: {total_duration/3600:.1f}h")
            print(f"  Stats: {dict(stats)}\n")
    
    elapsed = time.time() - start
    print(f"\n{'='*60}")
    print(f"Transcription complete!")
    print(f"Files: {len(audio_files)}")
    print(f"Success: {stats['ok']}")
    print(f"Failed: {stats.get('error', 0)}")
    print(f"Total audio: {total_duration/3600:.1f} hours")
    print(f"Total words: {total_words:,}")
    print(f"Time: {elapsed/60:.1f}m")
    print(f"Realtime factor: {total_duration/elapsed:.1f}x")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
