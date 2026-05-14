#!/usr/bin/env python3
"""
Fast audio segment extraction using ffmpeg (100× faster than librosa seeking).
Converts MP3s to temporary WAVs first, then extracts segments with direct seeking.

Usage:
    python training/extract_audio_segments_fast.py --workers 8
    python training/extract_audio_segments_fast.py --batch-size 10000 --workers 16
"""

import json
import os
import sys
import time
import argparse
import subprocess
import tempfile
from pathlib import Path
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
import shutil

SR = 16000
PAD_MS = 50


def convert_mp3_to_wav(mp3_path: str, wav_path: str) -> bool:
    """Convert MP3 to WAV using ffmpeg (fast, seekable)."""
    try:
        cmd = [
            "ffmpeg", "-y", "-i", mp3_path,
            "-ar", str(SR), "-ac", "1", "-f", "wav",
            wav_path
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=300)
        return result.returncode == 0 and os.path.exists(wav_path)
    except Exception as e:
        print(f"  Error converting {mp3_path}: {e}")
        return False


def extract_segment_ffmpeg(args: tuple) -> dict:
    """Extract single segment using ffmpeg (fast seek)."""
    segment, output_dir, temp_wav_path, idx = args

    video_id = segment.get("video_id", "unknown")
    word_idx = segment.get("word_index", idx)
    start = segment.get("start", 0)
    end = segment.get("end", 0)
    label = segment.get("label", 0)
    word = segment.get("word", "")

    out_dir = os.path.join(output_dir, video_id)
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{word_idx:08d}.wav")

    if os.path.exists(out_path):
        return {"status": "exists", "idx": idx}

    pad_s = PAD_MS / 1000.0
    offset = max(0, start - pad_s)
    duration = (end - start) + 2 * pad_s

    try:
        # ffmpeg fast seek: -ss before -i is input seeking (fast)
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(offset),
            "-t", str(duration),
            "-i", temp_wav_path,
            "-ar", str(SR), "-ac", "1", "-f", "wav",
            out_path
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=30)

        if result.returncode != 0 or not os.path.exists(out_path):
            return {"status": "ffmpeg_error", "idx": idx}

        # Write metadata
        meta = {
            "video_id": video_id,
            "word_idx": word_idx,
            "word": word,
            "start": start,
            "end": end,
            "duration": end - start,
            "label": label,
            "label_int": int(label) if str(label).isdigit() else 0,
        }
        with open(out_path.replace(".wav", ".json"), "w") as f:
            json.dump(meta, f)

        return {
            "status": "ok",
            "idx": idx,
            "duration": end - start,
            "label": meta["label_int"]
        }

    except Exception as e:
        return {"status": "error", "idx": idx, "error": str(e)[:100]}


def process_video_batch(video_id: str, segments: list, output_dir: str, temp_dir: str) -> dict:
    """Process all segments for one video (convert once, extract many)."""
    if not segments:
        return {"status": "no_segments", "video_id": video_id}

    # Get first segment's audio file
    af = segments[0].get("audio_file", "")
    if not af or not os.path.exists(af):
        return {"status": "missing_audio", "video_id": video_id, "count": len(segments)}

    # Convert MP3 to temp WAV (one conversion per video)
    temp_wav = os.path.join(temp_dir, f"{video_id}_{os.getpid()}.wav")

    if not convert_mp3_to_wav(af, temp_wav):
        return {"status": "convert_failed", "video_id": video_id, "count": len(segments)}

    # Extract all segments from this video
    results = []
    for i, seg in enumerate(segments):
        result = extract_segment_ffmpeg((seg, output_dir, temp_wav, i))
        results.append(result)

    # Cleanup temp file
    try:
        os.remove(temp_wav)
    except:
        pass

    # Aggregate results
    stats = Counter(r["status"] for r in results)
    labels = Counter(r.get("label", 0) for r in results if r["status"] == "ok")
    total_dur = sum(r.get("duration", 0) for r in results if r["status"] == "ok")

    return {
        "status": "batch_complete",
        "video_id": video_id,
        "total": len(segments),
        "stats": dict(stats),
        "labels": dict(labels),
        "duration": total_dur,
    }


def main():
    parser = argparse.ArgumentParser(description="Fast audio extraction with ffmpeg")
    parser.add_argument("--input", default="data/audio_comedy/aligned_segments.jsonl")
    parser.add_argument("--output-dir", default="data/audio_comedy/extracted_clips_fast")
    parser.add_argument("--max-videos", type=int, default=0)
    parser.add_argument("--workers", type=int, default=min(8, os.cpu_count() or 4))
    parser.add_argument("--temp-dir", default="/tmp/laughter_extraction")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    os.makedirs(args.temp_dir, exist_ok=True)

    # Load and group by video
    print(f"Loading {args.input}...")
    t0 = time.time()

    videos = defaultdict(list)
    total = 0
    with open(args.input) as f:
        for line in f:
            d = json.loads(line)
            af = d.get("audio_file", "")
            if not af or not os.path.exists(af):
                continue
            vid = d.get("video_id", "unknown")
            videos[vid].append(d)
            total += 1

    load_time = time.time() - t0
    print(f"Loaded {total:,} segments across {len(videos)} videos in {load_time:.1f}s")

    if args.max_videos > 0:
        videos = dict(list(videos.items())[:args.max_videos])
        print(f"Limited to {len(videos)} videos for testing")

    # Process videos in parallel
    print(f"\nExtracting to {args.output_dir}/ with {args.workers} workers...")
    print("(Converting MP3→WAV once per video, then extracting segments with fast seek)")
    start = time.time()

    video_list = list(videos.items())
    total_stats = Counter()
    total_labels = Counter()
    total_dur = 0.0

    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(process_video_batch, vid, segs, args.output_dir, args.temp_dir): vid
            for vid, segs in video_list
        }

        for i, future in enumerate(as_completed(futures)):
            result = future.result()
            vid = futures[future]

            if result["status"] == "batch_complete":
                for k, v in result["stats"].items():
                    total_stats[k] += v
                for k, v in result["labels"].items():
                    total_labels[k] += v
                total_dur += result["duration"]

            if (i + 1) % 10 == 0 or i == len(video_list) - 1:
                elapsed = time.time() - start
                rate = (i + 1) / elapsed
                eta = (len(video_list) - i - 1) / rate if rate > 0 else 0
                print(f"  {i+1}/{len(video_list)} videos | "
                      f"{total_stats.get('ok', 0):,} segs | "
                      f"{rate:.1f} vid/s | ETA {eta/60:.0f}m")

    elapsed = time.time() - start
    print(f"\nDone in {elapsed/60:.1f}m")
    print(f"\nStats: {dict(total_stats)}")
    print(f"Label distribution: {dict(total_labels)}")
    print(f"Total audio: {total_dur/3600:.1f} hours")
    print(f"Output: {args.output_dir}/")


if __name__ == "__main__":
    main()
