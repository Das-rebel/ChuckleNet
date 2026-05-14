#!/usr/bin/env python3
"""
Download audio and subtitles from YouTube videos in batches.
Uses yt-dlp with parallel workers for speed.

Usage:
    python training/download_audio_batch.py --lang en --video-list data/video_candidates/en.json
    python training/download_audio_batch.py --lang zh --video-list data/video_candidates/zh.json --workers 4
"""

import json
import os
import time
import argparse
import subprocess
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from collections import Counter

# ── Config ──────────────────────────────────────────────────────────
GDRIVE_BASE = "gdrive:laughter_prediction"
AUDIO_QUALITY = "5"  # 0=best, 5=128k, 10=worst
AUDIO_FORMAT = "mp3"


def download_video(args: tuple) -> dict:
    """Download single video audio + VTT subtitles."""
    video, lang, output_base = args
    
    video_id = video.get("id", "")
    if not video_id:
        return {"status": "no_id", "video_id": "unknown"}
    
    # Check if already downloaded
    audio_path = f"{output_base}/audio/{lang}/{video_id}.{AUDIO_FORMAT}"
    vtt_path = f"{output_base}/vtt/{lang}/{video_id}.en.vtt"
    
    # Check via rclone
    check_cmd = ["rclone", "lsf", audio_path]
    try:
        result = subprocess.run(check_cmd, capture_output=True, timeout=10)
        if result.returncode == 0 and result.stdout.strip():
            return {"status": "exists", "video_id": video_id}
    except:
        pass
    
    url = f"https://youtube.com/watch?v={video_id}"
    
    # Download audio
    audio_args = [
        "yt-dlp",
        "-x",  # extract audio
        "--audio-format", AUDIO_FORMAT,
        "--audio-quality", AUDIO_QUALITY,
        "-o", f"{output_base}/audio/{lang}/%(id)s.%(ext)s",
        "--download-archive", f"{output_base}/downloaded_{lang}.txt",
        url,
    ]
    
    try:
        result = subprocess.run(audio_args, capture_output=True, timeout=300)
        audio_success = result.returncode == 0
    except subprocess.TimeoutExpired:
        return {"status": "audio_timeout", "video_id": video_id}
    except Exception as e:
        return {"status": "audio_error", "video_id": video_id, "error": str(e)[:100]}
    
    # Download VTT subtitles
    sub_lang = "en" if lang == "en" else lang[:2]
    vtt_args = [
        "yt-dlp",
        "--skip-download",
        "--write-auto-sub",
        "--sub-langs", sub_lang,
        "--convert-subs", "vtt",
        "-o", f"{output_base}/vtt/{lang}/%(id)s",
        url,
    ]
    
    try:
        result = subprocess.run(vtt_args, capture_output=True, timeout=60)
        vtt_success = result.returncode == 0
    except:
        vtt_success = False
    
    return {
        "status": "ok" if audio_success else "partial",
        "video_id": video_id,
        "audio": audio_success,
        "vtt": vtt_success,
    }


def download_local(args: tuple) -> dict:
    """Download to local disk (fallback if no rclone)."""
    video, lang, output_dir = args
    
    video_id = video.get("id", "")
    if not video_id:
        return {"status": "no_id"}
    
    audio_dir = os.path.join(output_dir, "audio", lang)
    vtt_dir = os.path.join(output_dir, "vtt", lang)
    os.makedirs(audio_dir, exist_ok=True)
    os.makedirs(vtt_dir, exist_ok=True)
    
    audio_path = os.path.join(audio_dir, f"{video_id}.{AUDIO_FORMAT}")
    vtt_path = os.path.join(vtt_dir, f"{video_id}.{lang[:2]}.vtt")
    
    if os.path.exists(audio_path):
        return {"status": "exists", "video_id": video_id}
    
    url = f"https://youtube.com/watch?v={video_id}"
    
    # Download audio
    audio_args = [
        "yt-dlp",
        "-x",
        "--audio-format", AUDIO_FORMAT,
        "--audio-quality", AUDIO_QUALITY,
        "-o", os.path.join(audio_dir, "%(id)s.%(ext)s"),
        "--download-archive", os.path.join(output_dir, f"downloaded_{lang}.txt"),
        url,
    ]
    
    try:
        result = subprocess.run(audio_args, capture_output=True, timeout=300)
        audio_success = result.returncode == 0
    except Exception as e:
        return {"status": "audio_error", "video_id": video_id, "error": str(e)[:100]}
    
    # Download VTT
    sub_lang = "en" if lang == "en" else lang[:2]
    vtt_args = [
        "yt-dlp",
        "--skip-download",
        "--write-auto-sub",
        "--sub-langs", sub_lang,
        "--convert-subs", "vtt",
        "-o", os.path.join(vtt_dir, "%(id)s"),
        url,
    ]
    
    try:
        result = subprocess.run(vtt_args, capture_output=True, timeout=60)
        vtt_success = result.returncode == 0
    except:
        vtt_success = False
    
    return {
        "status": "ok" if audio_success else "partial",
        "video_id": video_id,
        "audio": audio_success,
        "vtt": vtt_success,
    }


def main():
    parser = argparse.ArgumentParser(description="Download audio batches from YouTube")
    parser.add_argument("--lang", choices=["en", "zh", "hi-latn"], required=True)
    parser.add_argument("--video-list", required=True, help="JSON file with video IDs")
    parser.add_argument("--output-dir", default="data/audio_comedy")
    parser.add_argument("--gdrive", action="store_true", help="Upload to GDrive via rclone")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--batch-size", type=int, default=100, help="Save progress every N videos")
    args = parser.parse_args()
    
    # Load videos
    with open(args.video_list) as f:
        videos = json.load(f)
    
    print(f"Downloading {len(videos)} {args.lang} videos...")
    print(f"Workers: {args.workers}")
    print(f"Destination: {'GDrive' if args.gdrive else args.output_dir}")
    
    # Prepare tasks
    if args.gdrive:
        output_base = GDRIVE_BASE
        download_fn = download_video
    else:
        output_base = args.output_dir
        download_fn = download_local
    
    tasks = [(v, args.lang, output_base) for v in videos]
    
    # Download in parallel
    stats = Counter()
    start = time.time()
    
    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(download_fn, t): t for t in tasks}
        
        for i, future in enumerate(as_completed(futures)):
            result = future.result()
            stats[result["status"]] += 1
            
            if result["status"] == "ok":
                print(f"  ✓ {result['video_id']}")
            elif result["status"] == "exists":
                print(f"  ○ {result['video_id']} (exists)")
            else:
                print(f"  ✗ {result['video_id']}: {result['status']}")
            
            if (i + 1) % args.batch_size == 0:
                elapsed = time.time() - start
                rate = (i + 1) / elapsed
                eta = (len(tasks) - i - 1) / rate if rate > 0 else 0
                print(f"\n  Progress: {i+1}/{len(tasks)} | {rate:.1f} vid/s | ETA {eta/60:.0f}m")
                print(f"  Stats: {dict(stats)}\n")
    
    elapsed = time.time() - start
    print(f"\n{'='*60}")
    print(f"Download complete in {elapsed/60:.1f}m")
    print(f"Stats: {dict(stats)}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
