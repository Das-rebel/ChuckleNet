#!/usr/bin/env python3
"""Fast collection of YouTube comedy videos - no laughter filter."""

import subprocess
import json
from pathlib import Path
import time

# Fast search queries
QUERIES = [
    "standup comedy full show english",
    "best standup comedy moments",
    "crowd work standup compilation",
    "late night talk show comedy",
    "comedy central roast",
    "netflix comedy special",
    "comedy club performance",
]

OUTPUT_FILE = Path("data/chuckle-net/fast_candidates.txt")

def search_youtube(query, n=50):
    """Search YouTube for videos."""
    cmd = [
        "python3", "-m", "yt_dlp",
        f"ytsearch{n}:{query}",
        "--no-download",
        "--print", "%(id)s",
        "-o", "/dev/null"
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        ids = [line.strip() for line in result.stdout.split('\n') if line.strip()]
        return ids
    except:
        return []

# Search
all_ids = set()
for query in QUERIES:
    print(f"Searching: {query}")
    ids = search_youtube(query, n=50)
    print(f"  Found {len(ids)} videos")
    all_ids.update(ids)
    time.sleep(1)

# Load existing
existing = set()
candidates_file = Path("data/chuckle-net/scaleup_candidates.jsonl")
if candidates_file.exists():
    with open(candidates_file) as f:
        for line in f:
            obj = json.loads(line)
            existing.add(obj.get('video_id', ''))

# New candidates
new_ids = all_ids - existing
print(f"\nTotal found: {len(all_ids)}")
print(f"Existing: {len(existing)}")
print(f"New candidates: {len(new_ids)}")

# Save
with open(OUTPUT_FILE, 'w') as f:
    for vid in sorted(new_ids):
        f.write(f"{vid}\n")

print(f"\nSaved {len(new_ids)} new candidates to {OUTPUT_FILE}")
