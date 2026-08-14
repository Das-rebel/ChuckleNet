#!/usr/bin/env python3
"""
Extract per-word .wav clips from aligned segments using ffmpeg.
Each clip: source MP3 → word-level start/end → output .wav
"""

import json
import os
import subprocess
from pathlib import Path
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SEGMENTS_FILE = PROJECT_ROOT / "data/audio_comedy/aligned_segments.jsonl"
OUTPUT_BASE = PROJECT_ROOT / "data/audio_comedy/extracted_clips"

# Per-video clip count tracking
CLIP_COUNTS_FILE = OUTPUT_BASE / "clip_counts.json"


def load_clip_counts():
    if CLIP_COUNTS_FILE.exists():
        return json.loads(CLIP_COUNTS_FILE.read_text())
    return {}


def save_clip_counts(counts):
    CLIP_COUNTS_FILE.write_text(json.dumps(counts, indent=2))


def extract_clip(seg, output_dir):
    """Extract a single .wav clip using ffmpeg."""
    audio_file = seg["audio_file"]
    if not audio_file or not os.path.exists(audio_file):
        return None

    start = seg["start"]
    end = seg["end"]
    duration = seg["duration"]
    word = seg["word"].strip().replace("/", "_").replace(" ", "_")[:40]
    video_id = seg["video_id"]
    word_idx = seg["word_index"]

    # Output: extracted_clips/{video_id}/{word_idx}_{word}.wav
    out_name = f"{word_idx:06d}_{word}.wav"
    out_path = output_dir / out_name

    if out_path.exists():
        return out_path

    output_dir.mkdir(parents=True, exist_ok=True)

    # ffmpeg: cut from source audio at start, for duration
    # Using short duration tolerance
    cmd = [
        "ffmpeg", "-y",
        "-i", audio_file,
        "-ss", str(start),
        "-t", str(duration + 0.05),  # slight extra to avoid truncation
        "-ar", "16000",  # 16kHz for Wav2Vec2
        "-ac", "1",      # mono
        "-c:a", "pcm_s16le",
        str(out_path)
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            # Try alternate approach with -t instead of duration
            cmd[-1] = str(end - start + 0.05)
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0 and out_path.exists():
            return out_path
        return None
    except Exception:
        return None


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--max-clips", type=int, default=0, help="Max clips to extract (0=all)")
    args = parser.parse_args()

    # Load segments
    print("Loading segments...")
    segments = []
    with open(SEGMENTS_FILE) as f:
        for line in f:
            seg = json.loads(line)
            if seg.get("audio_file"):
                segments.append(seg)

    print(f"Total segments with audio: {len(segments)}")

    # Load existing clip counts
    existing = load_clip_counts()

    # Filter: only process clips that don't exist yet
    pending = []
    for seg in segments:
        vid = seg["video_id"]
        idx = seg["word_index"]
        output_dir = OUTPUT_BASE / vid
        word = seg["word"].strip().replace("/", "_").replace(" ", "_")[:40]
        out_name = f"{idx:06d}_{word}.wav"
        out_path = output_dir / out_name
        if not out_path.exists():
            pending.append(seg)

    print(f"Already extracted: {len(segments) - len(pending)}")
    print(f"Pending extraction: {len(pending)}")

    if not pending:
        print("All clips already extracted!")
        return

    if args.max_clips > 0:
        pending = pending[:args.max_clips]
        print(f"Limiting to {args.max_clips} clips")

    # Extract in parallel
    print(f"Extracting with {args.workers} workers...")
    t0 = __import__("time").time()
    done = 0
    failed = 0

    def track_extract(seg):
        return extract_clip(seg, OUTPUT_BASE / seg["video_id"])

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(track_extract, seg): seg for seg in pending}
        for future in as_completed(futures):
            result = future.result()
            if result:
                done += 1
            else:
                failed += 1
            if (done + failed) % 500 == 0:
                print(f"  {done + failed}/{len(pending)} done ({done} OK, {failed} failed)")

    elapsed = __import__("time").time() - t0
    print(f"\nDone: {done} clips extracted, {failed} failed in {elapsed:.0f}s")
    print(f"Output: {OUTPUT_BASE}/")


if __name__ == "__main__":
    main()
