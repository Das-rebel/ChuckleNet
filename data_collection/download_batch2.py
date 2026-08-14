#!/usr/bin/env python3
"""Download batch 2 of comedy videos - AUDIO ONLY (.m4a)."""

import subprocess
import json
from pathlib import Path
import time

VIDEO_DIR = Path("data/raw/videos")
CANDIDATES_FILE = Path("data/chuckle-net/new_candidates.jsonl")
LOG_FILE = Path("data/chuckle-net/batch2_download.log")
DELAY = 2

def download_audio(video_id):
    """Download audio only using no-cookies method."""
    output = str(VIDEO_DIR / video_id)
    
    cmd = [
        "python3", "-m", "yt_dlp",
        "-f", "bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio",
        "--no-cookies",
        "--no-check-certificate",
        "-o", f"{output}.%(ext)s",
        f"https://www.youtube.com/watch?v={video_id}"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    return result.returncode == 0, result.stdout.strip(), result.stderr.strip()

# Load candidates
with open(CANDIDATES_FILE) as f:
    candidates = [json.loads(line) for line in f]

print(f"Downloading {len(candidates)} videos (audio only)...")

successful = 0
failed = 0
failed_ids = []

for i, cand in enumerate(candidates, 1):
    video_id = cand.get('video_id', '')
    
    # Skip if already downloaded
    if (VIDEO_DIR / f"{video_id}.m4a").exists():
        print(f"[{i}/{len(candidates)}] {video_id}: Already exists")
        successful += 1
        continue
    
    print(f"[{i}/{len(candidates)}] Downloading: {video_id}...", end=" ", flush=True)
    
    success, stdout, stderr = download_audio(video_id)
    
    if success:
        successful += 1
        print("✅")
    else:
        failed += 1
        failed_ids.append(video_id)
        print(f"❌ ({stderr[:50] if stderr else 'error'})")
    
    time.sleep(DELAY)

print(f"\n=== COMPLETE ===")
print(f"Successful: {successful}")
print(f"Failed: {failed}")

with open(LOG_FILE, 'w') as f:
    json.dump({"successful": successful, "failed": failed, "failed_ids": failed_ids}, f, indent=2)
