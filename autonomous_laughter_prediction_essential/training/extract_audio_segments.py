#!/usr/bin/env python3
"""
Extract audio waveform segments from aligned_segments.jsonl.
Uses existing MP3 files + word timestamps → individual WAV clips.

Usage:
    python training/extract_audio_segments.py
    python training/extract_audio_segments.py --max-segments 10000
    python training/extract_audio_segments.py --output-dir data/audio_comedy/extracted_clips
"""

import json
import os
import sys
import time
import argparse
from pathlib import Path
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np
import librosa
import soundfile as sf

# ── Config ──────────────────────────────────────────────────────────
SR = 16000
PAD_MS = 50  # pad each segment by 50ms on each side for context


def extract_segment(args: tuple) -> dict:
    """Extract a single audio segment. Returns status dict."""
    segment, output_dir, idx = args

    af = segment.get("audio_file", "")
    start = segment.get("start")
    end = segment.get("end")

    # Validate
    if not af or not os.path.exists(af):
        return {"status": "missing_audio", "idx": idx}
    if start is None or end is None or end <= start:
        return {"status": "bad_timestamps", "idx": idx}

    # Output path: extracted_clips/{video_id}/{word_idx:08d}.wav
    video_id = segment.get("video_id", "unknown")
    word_idx = segment.get("word_index", idx)
    out_dir = os.path.join(output_dir, video_id)
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{word_idx:08d}.wav")

    # Skip if already extracted
    if os.path.exists(out_path):
        return {"status": "exists", "idx": idx}

    try:
        # Load with padding
        pad_s = PAD_MS / 1000.0
        offset = max(0, start - pad_s)
        duration = (end - start) + 2 * pad_s
        y, sr = librosa.load(af, sr=SR, offset=offset, duration=duration)

        # Skip if too short (< 0.1s)
        if len(y) < SR * 0.1:
            return {"status": "too_short", "idx": idx}

        # Save as WAV
        sf.write(out_path, y, SR)

        # Also write metadata JSON
        meta = {
            "video_id": video_id,
            "word_idx": word_idx,
            "word": segment.get("word", ""),
            "start": start,
            "end": end,
            "duration": end - start,
            "label": segment.get("label", 0),
            # Handle both int and str labels
            "label_int": int(segment.get("label", 0)) if str(segment.get("label", "0")).isdigit() else 0,
            "audio_file": af,
            "samples": len(y),
        }
        meta_path = out_path.replace(".wav", ".json")
        with open(meta_path, "w") as f:
            json.dump(meta, f)

        return {"status": "ok", "idx": idx, "duration": end - start, "label": meta["label_int"]}

    except Exception as e:
        return {"status": "error", "idx": idx, "error": str(e)[:100]}


def main():
    parser = argparse.ArgumentParser(description="Extract audio segments from aligned JSONL")
    parser.add_argument("--input", default="data/audio_comedy/aligned_segments.jsonl",
                        help="Aligned segments JSONL file")
    parser.add_argument("--output-dir", default="data/audio_comedy/extracted_clips",
                        help="Output directory for WAV clips")
    parser.add_argument("--max-segments", type=int, default=0,
                        help="Max segments to process (0 = all)")
    parser.add_argument("--workers", type=int, default=os.cpu_count() or 4,
                        help="Parallel workers")
    parser.add_argument("--batch-size", type=int, default=1000,
                        help="Batch size for progress reporting")
    args = parser.parse_args()

    # Load segments
    print(f"Loading {args.input}...")
    t0 = time.time()
    segments = []
    with open(args.input) as f:
        for i, line in enumerate(f):
            if args.max_segments and i >= args.max_segments:
                break
            segments.append(json.loads(line))
    load_time = time.time() - t0
    print(f"Loaded {len(segments):,} segments in {load_time:.1f}s")

    # Filter to segments with valid audio files
    valid = [s for s in segments if s.get("audio_file") and os.path.exists(s["audio_file"])]
    missing = len(segments) - len(valid)
    print(f"Valid audio files: {len(valid):,} ({missing:,} missing)")

    # Extract
    print(f"\nExtracting to {args.output_dir}/ with {args.workers} workers...")
    os.makedirs(args.output_dir, exist_ok=True)

    tasks = [(seg, args.output_dir, i) for i, seg in enumerate(valid)]
    stats = Counter()
    total_dur = 0.0
    labels = Counter()
    start = time.time()

    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(extract_segment, t): t for t in tasks}
        for i, future in enumerate(as_completed(futures)):
            result = future.result()
            stats[result["status"]] += 1
            if result["status"] == "ok":
                total_dur += result.get("duration", 0)
                labels[result.get("label", 0)] += 1
            if (i + 1) % args.batch_size == 0:
                elapsed = time.time() - start
                rate = (i + 1) / elapsed
                eta = (len(tasks) - i - 1) / rate if rate > 0 else 0
                print(f"  {i+1:,}/{len(tasks):,} ({100*(i+1)/len(tasks):.1f}%) "
                      f"| {rate:.0f} seg/s | ETA {eta/60:.0f}m")

    elapsed = time.time() - start
    print(f"\nDone in {elapsed/60:.1f}m ({len(tasks)/elapsed:.0f} seg/s)")
    print(f"\nStats:")
    for status, count in stats.most_common():
        print(f"  {status}: {count:,}")
    print(f"\nTotal audio extracted: {total_dur/3600:.1f} hours")
    print(f"Label distribution: laugh={labels[1]:,} ({100*labels[1]/sum(labels.values()):.1f}%), "
          f"no_laugh={labels[0]:,} ({100*labels[0]/sum(labels.values()):.1f}%)")
    print(f"Output: {args.output_dir}/ ({stats['ok']:,} WAV files)")


if __name__ == "__main__":
    main()
