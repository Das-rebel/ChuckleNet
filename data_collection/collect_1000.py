#!/usr/bin/env python3
"""Fast collection of 500+ YouTube comedy candidates."""

import subprocess
import json
from pathlib import Path
import time

OUTPUT = Path("data/chuckle-net/candidates_1000.jsonl")

# Fast search queries - diverse comedy sources
QUERIES = [
    # English standup
    "standup comedy full special 2024",
    "best standup comedy moments compilation", 
    "late night talk show comedy monologue",
    "comedy central roast full",
    "netflix comedy special 2024",
    "bill burr standup full",
    "dave chappelle standup full",
    "john mulaney standup full",
    "Ali Wong standup full",
    "chris rock standup full",
    # Indian comedy
    "indian standup comedy full show",
    "zakir khan standup comedy",
    "vir das standup comedy",
    "all india bakchod comedy",
    "standup comedy hindi 2024",
    "bb ki vines full video",
    # Singapore/Malaysian
    "singapore standup comedy",
    "malaysian comedy show",
    "kumar comedy standup",
    # Chinese comedy
    "chinese comedy standup full",
    "cantonese comedy performance",
]

def search(query, n=30):
    """Search YouTube."""
    cmd = [
        "python3", "-m", "yt_dlp",
        f"ytsearch{n}:{query}",
        "--no-download",
        "--print", "%(id)s|%(duration)s|%(title)s",
        "-o", "/dev/null"
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
        ids = []
        for line in result.stdout.strip().split('\n'):
            if '|' in line:
                parts = line.split('|')
                if len(parts) >= 2:
                    vid_id = parts[0].strip()
                    try:
                        duration = int(parts[1].strip()) if parts[1].strip().isdigit() else 0
                    except:
                        duration = 0
                    title = parts[2].strip() if len(parts) > 2 else ""
                    if duration >= 120:  # At least 2 min
                        ids.append({"video_id": vid_id, "duration": duration, "title": title})
        return ids
    except Exception as e:
        print(f"  Error: {e}")
        return []

# Load existing
existing = set()
existing_file = Path("data/chuckle-net/scaleup_candidates.jsonl")
if existing_file.exists():
    try:
        with open(existing_file) as f:
            data = json.load(f) if f.read(1) else []
        for c in data:
            existing.add(c.get('video_id', ''))
    except:
        pass

# Downloaded
downloaded = set()
for f in Path("data/raw/videos").glob("*.m4a"):
    downloaded.add(f.stem)

print(f"Existing candidates: {len(existing)}")
print(f"Downloaded: {len(downloaded)}")

# Search
all_candidates = {}
for query in QUERIES:
    print(f"\nSearching: {query[:50]}...")
    results = search(query, n=30)
    print(f"  Found {len(results)} videos")
    for r in results:
        vid = r['video_id']
        if vid not in all_candidates and vid not in existing and vid not in downloaded:
            all_candidates[vid] = r
    time.sleep(1)

print(f"\n=== COLLECTION COMPLETE ===")
print(f"Total new candidates: {len(all_candidates)}")

# Save
with open(OUTPUT, 'w') as f:
    for c in all_candidates.values():
        f.write(json.dumps(c) + '\n')

print(f"Saved to {OUTPUT}")
