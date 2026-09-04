#!/usr/bin/env python3
"""Known comedy channels and their video IDs for bulk collection."""

import json
from pathlib import Path

# Known comedy channels/playlist URLs to scrape
CHANNEL_URLS = [
    # Dry Bar Comedy (English)
    "https://www.youtube.com/@DryBarComedy/videos",
    # Comedy Central
    "https://www.youtube.com/@ComedyCentral/videos", 
    # Netflix Is A Joke
    "https://www.youtube.com/@NetflixIsAJokeComedy/videos",
    # Indian Comedy Channels
    "https://www.youtube.com/@TheComedyFactory/videos",
    "https://www.youtube.com/@AAForkPlay/videos",
    "https://www.youtube.com/@ComedyLords/videos",
    "https://www.youtube.com/@SB搞笑趣闻/videos",
    # Zakir Khan
    "https://www.youtube.com/@zakirkhanofficial/videos",
    # Kunal Kamra
    "https://www.youtube.com/@KunalKammeru/videos",
    # Biswa Kalyan Rath
    "https://www.youtube.com/@BiswaKalyanRath/videos",
]

def get_channel_videos(url):
    """Get videos from channel using yt-dlp with no-cookies."""
    import subprocess
    cmd = [
        "python3", "-m", "yt_dlp",
        "--no-cookies",
        "--no-check-certificate", 
        "--flat-playlist",
        "--print", "%(id)s",
        url
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        ids = [line.strip() for line in result.stdout.split('\n') if line.strip() and len(line.strip()) == 11]
        return ids
    except Exception as e:
        print(f"  Error: {e}")
        return []

print("Collecting from known channels...")
all_ids = set()

for url in CHANNEL_URLS:
    print(f"Getting: {url.split('/')[-2]}...")
    ids = get_channel_videos(url)
    print(f"  Found {len(ids)} videos")
    all_ids.update(ids)

print(f"\nTotal unique videos: {len(all_ids)}")
print(f"Sample: {list(all_ids)[:5]}")
