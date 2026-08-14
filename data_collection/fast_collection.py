#!/usr/bin/env python3
"""Fast collection of YouTube comedy videos - NO laughter check."""

import subprocess
import json
from pathlib import Path
import time

OUTPUT_FILE = Path("data/chuckle-net/fast_collection.jsonl")

def get_playlist_videos(playlist_url):
    """Get all video IDs from a playlist/channel."""
    cmd = [
        "python3", "-m", "yt_dlp",
        "--no-cookies", "--no-check-certificate",
        "--flat-playlist", "--print", "%(id)s",
        playlist_url
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        ids = [line.strip() for line in result.stdout.split('\n') if line.strip() and len(line.strip()) == 11]
        return ids
    except:
        return []

# Sources that give downloadable videos
SOURCES = [
    # Dry Bar Comedy (clean comedy, all ages)
    "https://www.youtube.com/@DryBarComedy/videos",
    # Comedy Central Standup
    "https://www.youtube.com/c/ComedyCentralStandup/videos",
    "https://www.youtube.com/c/ComedyCentral/videos",
    # Netflix Is A Joke (official)
    "https://www.youtube.com/@NetflixIsAJokeTV/videos",
    # Some Indian comedy
    "https://www.youtube.com/@ComedyLords/videos",
    "https://www.youtube.com/@TheComedyFactory/videos",
]

# Get already downloaded
downloaded = set(f.stem for f in Path("data/raw/videos").glob("*.m4a"))
existing = set()

# Load existing candidates
for f in ["scaleup_candidates.jsonl", "new_candidates.jsonl"]:
    try:
        with open(f"data/chuckle-net/{f}") as file:
            try:
                data = json.load(file)
                for c in data:
                    existing.add(c.get('video_id', ''))
            except:
                file.seek(0)
                for line in file:
                    try:
                        existing.add(json.loads(line).get('video_id', ''))
                    except:
                        pass
    except:
        pass

print(f"Downloaded: {len(downloaded)}")
print(f"Existing candidates: {len(existing)}")

# Collect
all_ids = set()
for source in SOURCES:
    name = source.split('/')[-2]
    print(f"\nCollecting from {name}...")
    ids = get_playlist_videos(source)
    print(f"  Found {len(ids)} videos")
    
    new_count = 0
    for vid in ids:
        if vid not in downloaded and vid not in existing:
            all_ids.add(vid)
            new_count += 1
    
    print(f"  New (not downloaded): {new_count}")
    time.sleep(1)

print(f"\n=== COLLECTION COMPLETE ===")
print(f"Total new candidates: {len(all_ids)}")

# Save as JSONL
with open(OUTPUT_FILE, 'w') as f:
    for vid in sorted(all_ids):
        f.write(json.dumps({"video_id": vid}) + '\n')

print(f"Saved to {OUTPUT_FILE}")
