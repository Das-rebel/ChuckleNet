#!/usr/bin/env python3
"""
YouTube Comedy Video Collection Pipeline - GCS Version

Collects stand-up comedy videos from YouTube, streams to Google Cloud Storage,
transcribes with Whisper, and aligns with VTT for laughter labels.

Usage:
    python3 data_collection/collect_youtube_gcs.py --max-videos 10 --dry-run
"""

import os
import json
import subprocess
import argparse
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Optional
from google.cloud import storage

# ============================================================================
# CONFIGURATION
# ============================================================================

class Config:
    # GCS bucket
    GCS_BUCKET_NAME = 'chuckle-net-youtube-20260616'
    GCS_PROJECT = 'omniclaw-personal-assistant'
    
    # Local temp directory
    TEMP_DIR = Path('/tmp/chuckle-net-yt')
    
    # Paths (local temp)
    AUDIO_DIR = TEMP_DIR / 'audio'
    TRANSCRIPT_DIR = TEMP_DIR / 'transcripts'
    
    # Search queries for finding comedy
    SEARCH_QUERIES = [
        'stand up comedy special full',
        'stand up comedy Netflix',
        'comedy roast battle',
        'improv comedy show',
        'late night comedy monologue',
        'stand up comedy hour',
        'best stand up comedy 2024',
        'best stand up comedy 2023',
    ]
    
    # yt-dlp options
    YTDLP_FORMAT = 'bestaudio/best'
    YTDLP_EXT = 'mp3'
    
    # Whisper model
    WHISPER_MODEL = 'medium'
    
    # Rate limiting
    DOWNLOAD_DELAY = 2
    API_DELAY = 1

# ============================================================================
# GCS UTILITIES
# ============================================================================

def get_gcs_client():
    """Get GCS client."""
    return storage.Client(project=Config.GCS_PROJECT)

def get_gcs_bucket():
    """Get GCS bucket."""
    client = get_gcs_client()
    return client.bucket(Config.GCS_BUCKET_NAME)

def gcs_upload(local_path: Path, gcs_path: str) -> bool:
    """Upload file to GCS."""
    try:
        bucket = get_gcs_bucket()
        blob = bucket.blob(gcs_path)
        blob.upload_from_filename(str(local_path))
        print(f"    Uploaded to GCS: gs://{Config.GCS_BUCKET_NAME}/{gcs_path}")
        return True
    except Exception as e:
        print(f"    GCS upload failed: {e}")
        return False

def gcs_exists(gcs_path: str) -> bool:
    """Check if file exists in GCS."""
    try:
        bucket = get_gcs_bucket()
        blob = bucket.blob(gcs_path)
        return blob.exists()
    except Exception:
        return False

def gcs_download(gcs_path: str, local_path: Path) -> bool:
    """Download file from GCS."""
    try:
        bucket = get_gcs_bucket()
        blob = bucket.blob(gcs_path)
        blob.download_to_filename(str(local_path))
        return True
    except Exception as e:
        print(f"    GCS download failed: {e}")
        return False

# ============================================================================
# YOUTUBE SEARCH
# ============================================================================

def search_youtube_videos(query: str, max_results: int = 50) -> List[Dict]:
    """Search YouTube for videos matching query."""
    cmd = [
        'yt-dlp',
        '--flat-playlist',
        '--dump-json',
        f'ytsearch{max_results}:{query}',
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        videos = []
        for line in result.stdout.strip().split('\n'):
            if line:
                try:
                    data = json.loads(line)
                    videos.append({
                        'id': data.get('id'),
                        'title': data.get('title'),
                        'url': data.get('url') or data.get('webpage_url'),
                        'duration': data.get('duration'),
                        'channel': data.get('channel'),
                        'view_count': data.get('view_count', 0),
                    })
                except json.JSONDecodeError:
                    continue
        return videos
    except Exception as e:
        print(f"Search error: {e}")
        return []

# ============================================================================
# VIDEO DOWNLOAD (to temp, then upload)
# ============================================================================

def download_audio(video_url: str, video_id: str) -> Optional[Path]:
    """
    Download audio from YouTube to temp, then upload to GCS.
    Returns local path if successful, None if failed.
    """
    Config.TEMP_DIR.mkdir(parents=True, exist_ok=True)
    Config.AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    
    # Check GCS
    gcs_audio_path = f'audio/{video_id}.mp3'
    if gcs_exists(gcs_audio_path):
        print(f"  Already in GCS: {video_id}")
        return None
    
    # Check local
    local_path = Config.AUDIO_DIR / f'{video_id}.mp3'
    if local_path.exists():
        print(f"  Already local: {video_id}")
        return local_path
    
    # Download to temp
    cmd = [
        'yt-dlp',
        '-f', Config.YTDLP_FORMAT,
        '--extract-audio',
        '--audio-format', 'mp3',
        '--audio-quality', '5',
        '-o', str(local_path.with_suffix('.%(ext)s')),
        '--no-playlist',
        video_url,
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if result.returncode == 0 and local_path.exists():
            print(f"  Downloaded: {video_id}")
            return local_path
        else:
            print(f"  Download failed: {result.stderr[:200] if result.stderr else 'unknown'}")
            return None
    except subprocess.TimeoutExpired:
        print(f"  Timeout for {video_id}")
        return None
    except Exception as e:
        print(f"  Error: {e}")
        return None

# ============================================================================
# UPLOAD & CLEANUP
# ============================================================================

def upload_and_cleanup(local_path: Path, video_id: str, keep_local: bool = False):
    """Upload audio to GCS and cleanup local if not keeping."""
    if not local_path or not local_path.exists():
        return
    
    # Upload to GCS
    gcs_path = f'audio/{video_id}.mp3'
    gcs_upload(local_path, gcs_path)
    
    # Cleanup local
    if not keep_local:
        try:
            local_path.unlink()
            print(f"    Cleaned up local: {local_path.name}")
        except Exception as e:
            print(f"    Cleanup failed: {e}")

# ============================================================================
# MAIN PIPELINE
# ============================================================================

def collect_videos(max_videos: int = 100, dry_run: bool = False):
    """Main collection pipeline."""
    print(f"=== YouTube Comedy Collection (GCS) ===")
    print(f"Max videos: {max_videos}")
    print(f"Dry run: {dry_run}")
    print(f"GCS bucket: gs://{Config.GCS_BUCKET_NAME}")
    print()
    
    # Create temp directory
    Config.TEMP_DIR.mkdir(parents=True, exist_ok=True)
    Config.AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    
    # Search for videos
    print("Searching for videos...")
    all_videos = {}
    for query in Config.SEARCH_QUERIES:
        print(f"  Query: {query}")
        videos = search_youtube_videos(query, max_results=50)
        for v in videos:
            if v['id'] not in all_videos:
                all_videos[v['id']] = v
        print(f"    Found {len(videos)}, total: {len(all_videos)}")
    
    print(f"\nTotal unique videos: {len(all_videos)}")
    
    if dry_run:
        print("\nDRY RUN - listing first 10 videos:")
        for i, v in enumerate(list(all_videos.values())[:10]):
            print(f"  {i+1}. {v['title'][:60]} ({v['duration']/60:.1f} min)")
        return
    
    # Filter for reasonable duration (3-90 min)
    good_videos = [
        v for v in all_videos.values() 
        if v.get('duration') and 180 <= v['duration'] <= 5400
    ]
    print(f"Videos in range 3-90 min: {len(good_videos)}")
    
    # Download first N videos
    downloaded = 0
    for i, video in enumerate(good_videos[:max_videos]):
        video_id = video['id']
        print(f"\n[{i+1}/{min(max_videos, len(good_videos))}] {video['title'][:50]}...")
        
        # Download
        local_path = download_audio(video['url'], video_id)
        
        if local_path:
            # Upload to GCS and cleanup
            upload_and_cleanup(local_path, video_id, keep_local=False)
            downloaded += 1
        
        print(f"  Progress: {downloaded} downloaded")
    
    print(f"\n=== Complete ===")
    print(f"Downloaded: {downloaded} videos")
    print(f"Storage: gs://{Config.GCS_BUCKET_NAME}/audio/")

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='YouTube Comedy Collection - GCS Version')
    parser.add_argument('--max-videos', type=int, default=100, help='Max videos to download')
    parser.add_argument('--dry-run', action='store_true', help='List videos without downloading')
    args = parser.parse_args()
    
    collect_videos(max_videos=args.max_videos, dry_run=args.dry_run)
