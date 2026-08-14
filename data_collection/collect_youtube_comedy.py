#!/usr/bin/env python3
"""
YouTube Comedy Video Collection Pipeline

Collects stand-up comedy videos from YouTube, transcribes with Whisper,
and aligns with VTT for laughter labels.

Usage:
    python3 data_collection/collect_youtube_comedy.py --max-videos 100
"""

import os
import json
import subprocess
import argparse
from pathlib import Path
from typing import List, Dict, Optional
import time

# ============================================================================
# CONFIGURATION
# ============================================================================

class Config:
    # Paths
    DATA_DIR = Path('/Users/Subho/data/chuckle-net')
    AUDIO_DIR = DATA_DIR / 'youtube_audio'
    TRANSCRIPT_DIR = DATA_DIR / 'youtube_transcripts'
    OUTPUT_DIR = DATA_DIR / 'youtube_utterances'
    
    # YouTube channels/playlists for comedy
    COMEDY_SOURCES = [
        # Stand-up comedy specials
        'UCpBGlNYCRnwsqW7$UUALStandUp',  # Netflix Is a Joke
        'UCvjgEDvS4i6x4QVsAQT3gWw',       # Comedy Central
        'UCJHA_jMfFEnvNnln1G1fCbg',       # Laugh Boston
        'UC8Cb5Q9ixF-Z-Bnmj3_6ALA',       # Dry Bar Comedy
        
        # Talk shows with comedy segments
        'UCvjgEDvS4i6x4QVsAQT3gWw',       # The Tonight Show
        'UCwWhs_6V42-IqzG8Z1XcEaQ',       # Jimmy Kimmel Live
        
        # Comedy podcasts (video)
        'UCMHat3mHzVqjTGj高度vEh4lw',     # Your Mom's House
        'UCmS9ozSyDHLZ9o学好$Z8mFVw',     # TigerBelly
    ]
    
    # Search queries for finding comedy
    SEARCH_QUERIES = [
        'stand up comedy special full',
        'stand up comedy Netflix',
        'comedy roast battle',
        'improv comedy show',
        'late night comedy monologue',
        'stand up comedy hour',
    ]
    
    # yt-dlp options
    YTDLP_FORMAT = 'bestaudio/best'
    YTDLP_EXT = 'mp3'
    
    # Whisper model
    WHISPER_MODEL = 'medium'  # Options: tiny, base, small, medium, large
    
    # Rate limiting
    DOWNLOAD_DELAY = 2  # seconds between downloads
    API_DELAY = 1  # seconds between API calls

# ============================================================================
# YOUTUBE SEARCH & DISCOVERY
# ============================================================================

def search_youtube_videos(query: str, max_results: int = 50) -> List[Dict]:
    """
    Search YouTube for videos matching query.
    Uses yt-dlp to search.
    """
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

def get_video_metadata(video_id: str) -> Optional[Dict]:
    """Get detailed metadata for a video."""
    cmd = [
        'yt-dlp',
        '--dump-json',
        f'https://www.youtube.com/watch?v={video_id}',
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.stdout:
            data = json.loads(result.stdout)
            return {
                'id': data.get('id'),
                'title': data.get('title'),
                'description': data.get('description', '')[:500],
                'duration': data.get('duration'),
                'channel': data.get('channel'),
                'tags': data.get('tags', [])[:10],
                'categories': data.get('categories', []),
                'language': data.get('language'),
            }
    except Exception as e:
        print(f"Metadata error for {video_id}: {e}")
    return None

# ============================================================================
# VIDEO DOWNLOAD
# ============================================================================

def download_audio(video_url: str, output_path: Path, video_id: str) -> bool:
    """
    Download audio from YouTube video.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Check if already downloaded
    if output_path.exists():
        print(f"  Already exists: {output_path.name}")
        return True
    
    cmd = [
        'yt-dlp',
        '-f', Config.YTDLP_FORMAT,
        '--extract-audio',
        '--audio-format', 'mp3',
        '--audio-quality', '5',  # Lower = better quality
        '-o', str(output_path),
        '--no-playlist',
        video_url,
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode == 0 and output_path.exists():
            print(f"  Downloaded: {output_path.name}")
            return True
        else:
            print(f"  Download failed: {result.stderr[:200]}")
            return False
    except subprocess.TimeoutExpired:
        print(f"  Timeout for {video_id}")
        return False
    except Exception as e:
        print(f"  Error: {e}")
        return False

# ============================================================================
# TRANSCRIPTION
# ============================================================================

def transcribe_audio(audio_path: Path, output_path: Path) -> bool:
    """
    Transcribe audio using Whisper.
    """
    if output_path.exists():
        print(f"  Transcript exists: {output_path.name}")
        return True
    
    cmd = [
        'whisper',
        str(audio_path),
        '--model', Config.WHISPER_MODEL,
        '--output_dir', str(output_path.parent),
        '--output_format', 'json',
        '--language', 'en',
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)  # 1 hour timeout
        if result.returncode == 0:
            print(f"  Transcribed: {output_path.name}")
            return True
        else:
            print(f"  Transcription failed: {result.stderr[:200]}")
            return False
    except subprocess.TimeoutExpired:
        print(f"  Transcription timeout for {audio_path.name}")
        return False
    except Exception as e:
        print(f"  Error: {e}")
        return False

# ============================================================================
# VTT ALIGNMENT
# ============================================================================

def get_vtt_subtitles(video_id: str) -> Optional[str]:
    """
    Get VTT subtitles for a video (YouTube auto-generated or manual).
    """
    cmd = [
        'yt-dlp',
        '--write-auto-sub',
        '--sub-lang', 'en',
        '--skip-download',
        '--output', str(Config.TRANSCRIPT_DIR / video_id),
        f'https://www.youtube.com/watch?v={video_id}',
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        vtt_path = Config.TRANSCRIPT_DIR / f'{video_id}.en.vtt'
        if vtt_path.exists():
            return str(vtt_path)
    except Exception as e:
        print(f"  VTT error: {e}")
    return None

def parse_vtt(vtt_path: str) -> List[Dict]:
    """
    Parse VTT file into timestamped segments.
    """
    segments = []
    
    try:
        with open(vtt_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Simple VTT parser
        import re
        timestamp_pattern = r'(\d{2}:\d{2}:\d{2}\.\d{3}) --> (\d{2}:\d{2}:\d{2}\.\d{3})'
        
        matches = re.finditer(timestamp_pattern, content)
        for match in matches:
            start = match.group(1)
            end = match.group(2)
            
            # Get text after timestamp
            start_pos = match.end()
            next_match = next(matches, None)
            end_pos = next_match.start() if next_match else len(content)
            
            text = content[start_pos:end_pos].strip()
            text = re.sub(r'<[^>]+>', '', text)  # Remove HTML tags
            text = text.replace('\n', ' ').strip()
            
            if text:
                segments.append({
                    'start': start,
                    'end': end,
                    'text': text
                })
        
        return segments
    except Exception as e:
        print(f"VTT parse error: {e}")
        return []

def detect_laughter_in_vtt(vtt_path: str) -> List[Dict]:
    """
    Detect laughter markers in VTT (e.g., [laughter], [Applause]).
    """
    laughter_markers = [
        '[laughter]',
        '[Laughter]',
        '[LAUGHTER]',
        '[applause]',
        '[Applause]',
        '[cheering]',
    ]
    
    try:
        with open(vtt_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        import re
        segments = []
        
        for marker in laughter_markers:
            if marker in content:
                # Find segments with this marker
                pattern = r'(\d{2}:\d{2}:\d{2}\.\d{3}) --> (\d{2}:\d{2}:\d{2}\.\d{3})(.*?)' + re.escape(marker)
                matches = re.finditer(pattern, content, re.DOTALL)
                
                for match in matches:
                    start = match.group(1)
                    end = match.group(2)
                    text = match.group(3).strip()
                    text = re.sub(r'<[^>]+>', '', text)
                    text = text.replace('\n', ' ').strip()
                    
                    segments.append({
                        'start': start,
                        'end': end,
                        'text': text,
                        'laughter': True
                    })
        
        return segments
    except Exception as e:
        print(f"Laughter detection error: {e}")
        return []

# ============================================================================
# MAIN PIPELINE
# ============================================================================

def process_video(video_info: Dict) -> Optional[Dict]:
    """
    Process a single video: download, transcribe, align.
    """
    video_id = video_info['id']
    video_url = video_info['url']
    
    print(f"\nProcessing: {video_info['title']}")
    print(f"  ID: {video_id}")
    
    # Step 1: Download audio
    audio_path = Config.AUDIO_DIR / f'{video_id}.mp3'
    if not download_audio(video_url, audio_path, video_id):
        return None
    
    time.sleep(Config.DOWNLOAD_DELAY)
    
    # Step 2: Get subtitles
    vtt_path = get_vtt_subtitles(video_id)
    
    # Step 3: Transcribe
    transcript_path = Config.TRANSCRIPT_DIR / f'{video_id}.json'
    if not transcribe_audio(audio_path, transcript_path):
        return None
    
    # Step 4: Load transcript
    if transcript_path.exists():
        with open(transcript_path, 'r') as f:
            transcript = json.load(f)
    else:
        return None
    
    # Step 5: Align and extract utterances
    utterances = []
    
    for segment in transcript.get('segments', []):
        start = segment.get('start', 0)
        end = segment.get('end', 0)
        text = segment.get('text', '').strip()
        
        if not text:
            continue
        
        # Check if this segment has laughter nearby (in VTT)
        has_laughter = False
        if vtt_path:
            laughter_segments = detect_laughter_in_vtt(vtt_path)
            for laff in laughter_segments:
                # Check if laughter is within 5 seconds of this segment
                laff_start = parse_timestamp(laff['start'])
                if abs(laff_start - start) < 5:
                    has_laughter = True
                    break
        
        utterances.append({
            'uid': f"{video_id}_{start:.2f}",
            'video_id': video_id,
            'video_title': video_info['title'],
            'start': start,
            'end': end,
            'text': text,
            'laughter': has_laughter,
            'duration': end - start,
        })
    
    return {
        'video_id': video_id,
        'video_info': video_info,
        'utterances': utterances,
        'vtt_path': vtt_path,
    }

def parse_timestamp(ts: str) -> float:
    """Parse VTT timestamp to seconds."""
    import re
    match = re.match(r'(\d{2}):(\d{2}):(\d{2})\.(\d{3})', ts)
    if match:
        h, m, s, ms = match.groups()
        return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000
    return 0.0

def save_video_data(video_data: Dict):
    """Save processed video data."""
    video_id = video_data['video_id']
    output_path = Config.OUTPUT_DIR / f'{video_id}.json'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(video_data, f, indent=2)
    
    print(f"  Saved: {output_path.name}")

def get_collection_stats() -> Dict:
    """Get statistics on collected data."""
    stats = {
        'total_videos': 0,
        'total_utterances': 0,
        'total_duration_hours': 0,
        'laughter_count': 0,
    }
    
    if not Config.OUTPUT_DIR.exists():
        return stats
    
    for video_file in Config.OUTPUT_DIR.glob('*.json'):
        with open(video_file, 'r') as f:
            data = json.load(f)
        
        stats['total_videos'] += 1
        stats['total_utterances'] += len(data.get('utterances', []))
        
        for utt in data.get('utterances', []):
            stats['total_duration_hours'] += utt.get('duration', 0) / 3600
            if utt.get('laughter'):
                stats['laughter_count'] += 1
    
    return stats

# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='Collect YouTube comedy videos')
    parser.add_argument('--max-videos', type=int, default=50, help='Maximum videos to collect')
    parser.add_argument('--search-only', action='store_true', help='Only search, no download')
    parser.add_argument('--resume', action='store_true', help='Resume from existing collection')
    args = parser.parse_args()
    
    print("=" * 70)
    print("YOUTUBE COMEDY VIDEO COLLECTION PIPELINE")
    print("=" * 70)
    
    # Create directories
    Config.AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    Config.TRANSCRIPT_DIR.mkdir(parents=True, exist_ok=True)
    Config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Get current stats
    stats = get_collection_stats()
    print(f"\nCurrent collection:")
    print(f"  Videos: {stats['total_videos']}")
    print(f"  Utterances: {stats['total_utterances']}")
    print(f"  Duration: {stats['total_duration_hours']:.1f} hours")
    print(f"  Laughter segments: {stats['laughter_count']}")
    
    if args.search_only:
        # Just search and list videos
        all_videos = []
        for query in Config.SEARCH_QUERIES:
            print(f"\nSearching: {query}")
            videos = search_youtube_videos(query, max_results=50)
            print(f"  Found {len(videos)} videos")
            all_videos.extend(videos)
        
        # Remove duplicates
        seen = set()
        unique_videos = []
        for v in all_videos:
            if v['id'] not in seen:
                seen.add(v['id'])
                unique_videos.append(v)
        
        print(f"\nTotal unique videos: {len(unique_videos)}")
        
        # Save video list
        list_path = Config.DATA_DIR / 'youtube_video_list.json'
        with open(list_path, 'w') as f:
            json.dump(unique_videos, f, indent=2)
        print(f"Saved to: {list_path}")
        
        return
    
    # Collect videos
    print(f"\nTarget: {args.max_videos} new videos")
    
    all_videos = []
    for query in Config.SEARCH_QUERIES:
        print(f"\nSearching: {query}")
        videos = search_youtube_videos(query, max_results=50)
        print(f"  Found {len(videos)} videos")
        all_videos.extend(videos)
    
    # Remove duplicates and already-processed
    seen = set()
    processed = set()
    
    if args.resume:
        for video_file in Config.OUTPUT_DIR.glob('*.json'):
            processed.add(video_file.stem)
    
    unique_videos = []
    for v in all_videos:
        if v['id'] not in seen and v['id'] not in processed:
            seen.add(v['id'])
            unique_videos.append(v)
    
    print(f"\nNew unique videos to process: {len(unique_videos)}")
    
    # Process videos
    success_count = 0
    for i, video in enumerate(unique_videos[:args.max_videos]):
        print(f"\n[{i+1}/{min(args.max_videos, len(unique_videos))}]")
        
        try:
            video_data = process_video(video)
            if video_data:
                save_video_data(video_data)
                success_count += 1
        except Exception as e:
            print(f"  Error: {e}")
        
        time.sleep(Config.DOWNLOAD_DELAY)
    
    # Final stats
    print("\n" + "=" * 70)
    print("COLLECTION COMPLETE")
    print("=" * 70)
    
    stats = get_collection_stats()
    print(f"\nFinal collection:")
    print(f"  Videos: {stats['total_videos']}")
    print(f"  Utterances: {stats['total_utterances']}")
    print(f"  Duration: {stats['total_duration_hours']:.1f} hours")
    print(f"  Laughter segments: {stats['laughter_count']}")
    print(f"  Success rate: {success_count}/{min(args.max_videos, len(unique_videos))}")

if __name__ == '__main__':
    main()
