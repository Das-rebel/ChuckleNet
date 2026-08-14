#!/usr/bin/env python3
"""Collect next batch of YouTube comedy candidates."""

import subprocess
import json
from pathlib import Path

# Search queries for more videos
QUERIES = [
    "standup comedy full show",
    "crowd work compilation",
    "funniest moments standup",
    "indian standup comedy",
    "chinese comedy show",
]

print(f"Searching for {len(QUERIES)} query types...")

for query in QUERIES:
    print(f"\nQuery: {query}")
    cmd = [
        "python3", "-m", "yt_dlp",
        f"ytsearch50:{query}",
        "--format", "bestaudio[ext=m4a]/best",
        "--no-download",
        "--print", "%(id)s|%(title)s|%(duration)s|%(view_count)s|%(uploader)s",
        "--skip-download",
        "-o", "/dev/null"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    
    # Save results
    results = result.stdout.strip().split('\n')
    for line in results[:10]:  # First 10
        if line and '|' in line:
            parts = line.split('|')
            if len(parts) >= 5:
                print(f"  Found: {parts[0]} - {parts[1][:50]}")
