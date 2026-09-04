#!/usr/bin/env python3
"""Download batch 3 - using Brave browser cookies."""

import json
import subprocess
from pathlib import Path
import time

VIDEO_DIR = Path("data/raw/videos")
CANDIDATES = Path("data/chuckle-net/batch3_valid.jsonl")
LOG_FILE = Path("data/chuckle-net/batch3_download_brave.log")
DELAY = 2

def download_audio(video_id):
    cmd = [
        "python3", "-m", "yt_dlp",
        "-f", "bestaudio[ext=m4a]/bestaudio",
        "--js-runtimes", "node",
        "--cookies-from-browser", "brave",
        "-o", f"{str(VIDEO_DIR)}/{video_id}.%(ext)s",
        "--",
        f"https://www.youtube.com/watch?v={video_id}"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    return result.returncode == 0

# Load candidates
with open(CANDIDATES) as f:
    candidates = [json.loads(line)['video_id'] for line in f if line.strip()]

print(f"Downloading {len(candidates)} videos...")

successful = 0
failed = 0
failed_ids = []

for i, video_id in enumerate(candidates, 1):
    if (VIDEO_DIR / f"{video_id}.m4a").exists():
        successful += 1
        if i % 500 == 0:
            print(f"[{i}/{len(candidates)}] Already have: {successful}, Failed: {failed}")
        continue
    
    if i % 50 == 1:
        print(f"[{i}/{len(candidates)}] {video_id}...", end=" ", flush=True)
    
    if download_audio(video_id):
        successful += 1
        if i % 50 == 0:
            print(f" ✅ ({successful} ok, {failed} fail)")
    else:
        failed += 1
        failed_ids.append(video_id)
        if i % 50 == 0:
            print(f" ❌ ({successful} ok, {failed} fail)")
    
    time.sleep(DELAY)

print(f"\n=== COMPLETE ===")
print(f"Successful: {successful}")
print(f"Failed: {failed}")

with open(LOG_FILE, 'w') as f:
    json.dump({"successful": successful, "failed": failed, "failed_ids": failed_ids[:100]}, f, indent=2)
