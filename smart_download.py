#!/usr/bin/env python3
"""Smart download - skip videos that already have embeddings"""

import json
import os
import subprocess
from pathlib import Path

def load_missing_list():
    missing = []
    with open('data_collection/missing_audio_for_download.jsonl') as f:
        for line in f:
            if line.strip():
                missing.append(json.loads(line))
    return missing

def has_embeddings(video_id):
    """Check if video already has processed embeddings."""
    embedding_paths = [
        f'/Users/Subho/autonomous_laughter_prediction_essential/experiments/wavlm_embeddings_v2/{video_id}.pt',
        f'/Users/Subho/autonomous_laughter_prediction_essential/experiments/wavlm_embeddings/{video_id}.pt'
    ]
    
    for path in embedding_paths:
        if os.path.exists(path):
            return True, path
    return False, None

def download_audio(video_id: str, title: str) -> bool:
    """Download audio if not already exists."""
    raw_dir = Path("data/raw/videos")
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
    print("SMART DOWNLOAD - Skip already processed videos")
    print("=" * 70)
    
    missing = load_missing_list()
    print(f"Total qualified candidates: {len(missing)}")
    
    # Check which have embeddings
    with_embeddings = []
    need_download = []
    
    for item in missing:
        video_id = item['video_id']
        has_emb, emb_path = has_embeddings(video_id)
        
        if has_emb:
            with_embeddings.append({
                'video_id': video_id,
                'title': item['title'],
                'embedding_path': emb_path
            })
        else:
            need_download.append(item)
    
    print(f"✅ Already have embeddings: {len(with_embeddings)}")
    print(f"📥 Need to download audio: {len(need_download)}")
    
    # Download only those that need audio
    successful = []
    failed = []
    
    for i, item in enumerate(need_download, 1):
        video_id = item['video_id']
        title = item['title']
        
        print(f"\n[{i}/{len(need_download)}] Downloading {video_id[:15]}...")
        print(f"  Title: {title[:50]}...")
        
        success = download_audio(video_id, title)
        if success:
            print(f"  ✅ Downloaded")
            successful.append(item)
        else:
            print(f"  ❌ Failed")
            failed.append(video_id)
    
    print("\n" + "=" * 70)
    print("SMART DOWNLOAD COMPLETE")
    print("=" * 70)
    print(f"🎯 Total qualified: {len(missing)}")
    print(f"✅ Already had embeddings: {len(with_embeddings)}")
    print(f"✅ Successfully downloaded audio: {len(successful)}")
    print(f"❌ Failed downloads: {len(failed)}")
    
    if with_embeddings:
        print(f"\n📊 Videos that only needed audio (already had embeddings): {len(with_embeddings)}")
    
    print(f"\n📁 Output directory: data/raw/videos")

if __name__ == "__main__":
    main()
