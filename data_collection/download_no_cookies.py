#!/usr/bin/env python3
"""Download videos WITHOUT cookies - YouTube doesn't challenge public videos."""

import json
import subprocess
from pathlib import Path

# Load existing qualified candidates
qualified = []
with open('data_collection/existing_qualified_candidates.jsonl') as f:
    for line in f:
        if line.strip():
            qualified.append(json.loads(line))

print(f"Found {len(qualified)} qualified candidates")

# Download audio for each
output_dir = Path("data/raw/videos")
output_dir.mkdir(parents=True, exist_ok=True)

successful = []
failed = []

for i, video in enumerate(qualified, 1):
    video_id = video['video_id']
    title = video.get('title', '')[:50]
    laugh_markers = video.get('laugh_markers', 0)
    
    output_path = output_dir / f"{video_id}.m4a"
    
    if output_path.exists():
        print(f"[{i}/{len(qualified)}] {video_id}: Already exists")
        successful.append(video)
        continue
    
    print(f"[{i}/{len(qualified)}] Downloading {video_id} ({laugh_markers} markers)...")
    print(f"  Title: {title}...")
    
    # NO cookies - public video download
    try:
        cmd = [
            "python3", "-m", "yt_dlp",
            "-f", "bestaudio[ext=m4a]/bestaudio/best",
            "--audio-format", "m4a",
            "--audio-quality", "0",
            "-o", str(output_path),
            "--no-playlist",
            f"https://youtube.com/watch?v={video_id}"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        
        if result.returncode == 0 and output_path.exists():
            print(f"  ✅ Downloaded")
            successful.append(video)
        else:
            print(f"  ❌ Failed: {result.stderr[:100]}")
            failed.append(video_id)
    except Exception as e:
        print(f"  ❌ Error: {e}")
        failed.append(video_id)

print(f"\n{'='*60}")
print(f"COMPLETE")
print(f"{'='*60}")
print(f"✅ Successful: {len(successful)}")
print(f"❌ Failed: {len(failed)}")
if failed:
    print(f"\nFailed IDs: {failed[:10]}...")
