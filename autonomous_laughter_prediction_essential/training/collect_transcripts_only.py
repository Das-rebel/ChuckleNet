#!/usr/bin/env python3
"""
Fast transcript-only collector for YouTube comedy videos.
No audio download, no Whisper - just fetch transcripts.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "audio_comedy"
TRANSCRIPT_DIR = DATA_DIR / "transcripts"

def check_youtube_transcript_api():
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        return True
    except ImportError:
        return False

def search_youtube(query: str, max_results: int = 5):
    """Search YouTube for videos using yt-dlp."""
    print(f"  Searching for: {query}")
    cmd = [
        'yt-dlp', '--flat-playlist',
        '--print', '%(id)s|%(title)s|%(duration)s',
        f'ytsearch{max_results}:{query} stand-up comedy special'
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, check=True)
        videos = []
        for line in result.stdout.strip().split('\n'):
            if '|' in line:
                parts = line.split('|')
                if len(parts) >= 2:
                    videos.append({
                        'id': parts[0],
                        'title': parts[1],
                        'duration': parts[2] if len(parts) > 2 else 'unknown'
                    })
        return videos
    except Exception as e:
        print(f"  Search failed: {e}")
        return []

def fetch_transcript(video_id: str, title: str, comedian: str):
    """Fetch YouTube transcript for a video."""
    from youtube_transcript_api import YouTubeTranscriptApi
    
    try:
        ytt = YouTubeTranscriptApi()
        transcript = ytt.fetch(video_id)
        
        # Iterate to get all entries (fetch returns a generator)
        words = []
        for entry in transcript:
            words.append({
                'word': entry.text,
                'start': entry.start,
                'end': getattr(entry, 'end', entry.start + getattr(entry, 'duration', 0.5)),
                'duration': getattr(entry, 'duration', 0.5)
            })
        
        return {
            'video_id': video_id,
            'title': title,
            'comedian': comedian,
            'source': 'youtube_transcript_api',
            'words': words,
            'language': transcript.language,
            'is_generated': transcript.is_generated
        }
    except Exception as e:
        print(f"    Failed: {str(e)[:60]}")
        return None

def collect_comedian(comedian: str, max_videos: int = 5):
    """Collect transcripts for one comedian."""
    
    comedian_dir = TRANSCRIPT_DIR / comedian.lower().replace(' ', '_')
    comedian_dir.mkdir(parents=True, exist_ok=True)
    
    # Search for videos
    videos = search_youtube(comedian, max_videos)
    
    if not videos:
        print(f"  No videos found for {comedian}")
        return {'collected': 0, 'failed': 0}
    
    print(f"  Found {len(videos)} videos")
    
    collected = 0
    failed = 0
    total_words = 0
    
    for video in videos[:max_videos]:
        video_id = video['id']
        title = video['title']
        
        transcript_path = comedian_dir / f"{video_id}_transcript.json"
        
        if transcript_path.exists():
            print(f"  Already exists: {title[:40]}...")
            collected += 1
            continue
        
        print(f"  Fetching: {title[:40]}...")
        
        transcript = fetch_transcript(video_id, title, comedian)
        
        if transcript and transcript['words']:
            with open(transcript_path, 'w') as f:
                json.dump(transcript, f, indent=2)
            print(f"    Saved {len(transcript['words'])} words")
            collected += 1
            total_words += len(transcript['words'])
        else:
            print(f"    No transcript available")
            failed += 1
    
    return {'collected': collected, 'failed': failed, 'total': len(videos[:max_videos]), 'words': total_words}

def main():
    parser = argparse.ArgumentParser(description="Collect YouTube transcripts (transcript-only)")
    parser.add_argument('--comedian', '-c', type=str, required=True,
                       help="Comedian name (use 'all' for all comedians)")
    parser.add_argument('--max_videos', '-n', type=int, default=3,
                       help="Max videos per comedian (default: 3)")
    
    args = parser.parse_args()
    
    if not check_youtube_transcript_api():
        print("ERROR: youtube_transcript_api not installed")
        sys.exit(1)
    
    # Pre-found working video IDs for better results
    WORKING_VIDEOS = {
        'Jerry Seinfeld': ['nQDJpZoCWmo', '984VkHzXl8w', 'JAm4fFJDqW8', 'HAsBk9Eia8A'],
        'Jim Gaffigan': ['xJAxRVeKnTE', 'CjNii7LAwzg', 'tA34Ml__rOY'],
        'Kevin James': ['cedCUzWEBsQ', 'GNfwKnLUKIk'],
        'Hasan Minhaj': ['qqZ_SH9N3Xo', 'mS9CFBlLOcg'],
        'Bill Burr': ['Vn6MHmDo_Ck', 'uCJDLgQ6xFk', 'C67I8okPfB0'],
    }
    
    if args.comedian == 'all':
        comedians = list(WORKING_VIDEOS.keys())
    else:
        comedians = [args.comedian]
    
    print("=" * 60)
    print("TRANSCRIPT-ONLY COLLECTION")
    print("=" * 60)
    
    total_words = 0
    for comedian in comedians:
        print(f"\n🎭 {comedian}:")
        
        # Use working video IDs if available
        if comedian in WORKING_VIDEOS:
            video_ids = WORKING_VIDEOS[comedian][:args.max_videos]
            comedian_dir = TRANSCRIPT_DIR / comedian.lower().replace(' ', '_')
            comedian_dir.mkdir(parents=True, exist_ok=True)
            
            collected = 0
            words_count = 0
            for video_id in video_ids:
                transcript_path = comedian_dir / f"{video_id}_transcript.json"
                if transcript_path.exists():
                    print(f"  Already exists: {video_id}")
                    collected += 1
                    continue
                
                print(f"  Fetching {video_id}...")
                transcript = fetch_transcript(video_id, video_id, comedian)
                
                if transcript and transcript['words']:
                    with open(transcript_path, 'w') as f:
                        json.dump(transcript, f, indent=2)
                    print(f"    Saved {len(transcript['words'])} words")
                    collected += 1
                    words_count += len(transcript['words'])
            
            total_words += words_count
            print(f"  Result: {collected} collected, {words_count} words")
        else:
            result = collect_comedian(comedian, args.max_videos)
            total_words += result.get('words', 0)
            print(f"  Result: {result['collected']} collected, {result.get('failed', 0)} failed")
    
    print(f"\nTotal words collected: {total_words}")

if __name__ == '__main__':
    main()