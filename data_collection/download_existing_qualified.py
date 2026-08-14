#!/usr/bin/env python3
"""Download existing qualified candidates with >=10 laughter markers"""

import json
import subprocess
from pathlib import Path

def load_existing_candidates():
    candidates = []
    with open('data_collection/existing_qualified_candidates.jsonl') as f:
        for line in f:
            if line.strip():
                candidates.append(json.loads(line))
    return candidates

def download_audio(video_id: str, title: str) -> bool:
    raw_dir = Path("/Users/Subho/autonomous_laughter_prediction/data/raw/videos")
    raw_dir.mkdir(parents=True, exist_ok=True)
    output_path = raw_dir / f"{video_id}.m4a"
    
    if output_path.exists():
        return True
    
    try:
        cmd = [
            "python3", "-m", "yt_dlp",
            "-f", "bestaudio[ext=m4a]/bestaudio/best",
            "--audio-format", "m4a",
            "--audio-quality", "0", 
            "-o", str(output_path),
            "--no-playlist",
            "--cookies-from-browser", "chrome",
            f"https://youtube.com/watch?v={video_id}"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        return result.returncode == 0 and output_path.exists()
    except:
        return False

def main():
    print("=" * 70)
    print("DOWNLOADING EXISTING QUALIFIED CANDIDATES")
    print("=" * 70)
    
    candidates = load_existing_candidates()
    print(f"Found {len(candidates)} qualified candidates with >=10 laughter markers")
    
    successful = []
    failed = []
    
    for i, candidate in enumerate(candidates, 1):
        video_id = candidate.get('video_id')
        title = candidate.get('title', '')
        laugh_count = candidate.get('laugh_markers', 0)
        
        print(f"\n[{i}/{len(candidates)}] {video_id[:15]}...")
        print(f"  Title: {title[:50]}...")
        print(f"  Laughter markers: {laugh_count}")
        
        success = download_audio(video_id, title)
        if success:
            print(f"  ✅ Downloaded")
            successful.append(candidate)
        else:
            print(f"  ❌ Failed")
            failed.append(video_id)
    
    print("\n" + "=" * 70)
    print("DOWNLOAD COMPLETE")
    print("=" * 70)
    print(f"✅ Successfully downloaded: {len(successful)}")
    print(f"❌ Failed downloads: {len(failed)}")
    
    if failed:
        print(f"\nFailed video IDs: {failed[:10]}...")
        print(f"  (showing first 10 of {len(failed)})")
    
    print(f"\nOutput directory: /Users/Subho/autonomous_laughter_prediction/data/raw/videos")

if __name__ == "__main__":
    main()
