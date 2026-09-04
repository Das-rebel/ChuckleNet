#!/usr/bin/env python3
"""Check existing audio files in Google Drive and local storage"""

import json
import os
from pathlib import Path

def load_existing_candidates():
    candidates = []
    with open('data_collection/existing_qualified_candidates.jsonl') as f:
        for line in f:
            if line.strip():
                candidates.append(json.loads(line))
    return candidates

def check_existing_audio(video_id: str):
    """Check if audio exists in Google Drive or local storage."""
    # Check Google Drive
    gd_paths = [
        f"/Users/Subho/Google Drive/My Drive/audio/{video_id}.m4a",
        f"/Users/Subho/Google Drive/My Drive/audio/{video_id}.mp3", 
        f"/Users/Subho/Google Drive/My Drive/audio/{video_id}.wav",
        f"/Users/Subho/Google Drive/My Drive/comedy/audio/{video_id}.m4a",
        f"/Users/Subho/Google Drive/My Drive/data/audio/{video_id}.m4a"
    ]
    
    # Check local
    local_path = Path("data/raw/videos") / f"{video_id}.m4a"
    
    # Check any path
    for path in gd_paths + [str(local_path)]:
        if os.path.exists(path):
            return True, path
    
    return False, None

def main():
    candidates = load_existing_candidates()
    print(f"Checking {len(candidates)} qualified candidates...")
    
    existing = []
    missing = []
    
    for candidate in candidates:
        video_id = candidate.get('video_id')
        exists, path = check_existing_audio(video_id)
        
        if exists:
            existing.append({
                'video_id': video_id,
                'path': path,
                'title': candidate.get('title', '')[:30]
            })
        else:
            missing.append({
                'video_id': video_id,
                'title': candidate.get('title', '')[:30]
            })
    
    print(f"\n✅ Already exist: {len(existing)}")
    print(f"❌ Need to download: {len(missing)}")
    
    if existing:
        print(f"\nSample existing files:")
        for i, item in enumerate(existing[:5]):
            print(f"  {i+1}. {item['video_id']}: {item['path']}")
    
    if missing:
        print(f"\nMissing files - need to download {len(missing)}:")
        for i, item in enumerate(missing[:5]):
            print(f"  {i+1}. {item['video_id']}: {item['title']}...")
        
        # Save missing list for selective download
        with open('data_collection/missing_audio_for_download.jsonl', 'w') as f:
            for item in missing:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        
        print(f"\n💾 Saved missing list to: data_collection/missing_audio_for_download.jsonl")

if __name__ == "__main__":
    main()
