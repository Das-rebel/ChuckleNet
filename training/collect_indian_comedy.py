#!/usr/bin/env python3
"""
Collect Hindi/Hinglish/Bengali comedy data from YouTube.

Multi-strategy approach:
1. Try YouTubeTranscriptApi (fastest)
2. If blocked/unavailable, fall back to yt-dlp + Whisper transcription
3. Process and save transcripts with language metadata

Comedians to collect:
- Hindi/Hinglish: Vir Das, Zakir Khan, Biswa Kalyan Rath, Kaneez Surka, Atul Khatri
- Bengali: Mir Afsar Ali, Sourav Ghosh, and other Bengali standup
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import time

# Try imports with fallbacks
try:
    from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled
    YOUTUBE_API_AVAILABLE = True
except ImportError:
    YOUTUBE_API_AVAILABLE = False
    print("⚠️ YouTubeTranscriptApi not available, will use yt-dlp + Whisper only")

try:
    import yt_dlp
    YTDLP_AVAILABLE = True
except ImportError:
    YTDLP_AVAILABLE = False
    print("❌ yt-dlp not available. Install with: pip install yt-dlp")

try:
    import whisper
    WHISPER_AVAILABLE = True
    # Load model once for efficiency
    whisper_model = None
except ImportError:
    WHISPER_AVAILABLE = False
    print("❌ Whisper not available. Install with: pip install openai-whisper")

PROJECT_ROOT = Path(__file__).parent.parent
TRANSCRIPT_DIR = PROJECT_ROOT / "data" / "audio_comedy" / "transcripts"
AUDIO_DIR = PROJECT_ROOT / "data" / "audio_comedy" / "audio"

# Language codes and script mapping
LANGUAGE_CONFIG = {
    'hindi_hinglish': {
        'code': 'hi-latn',
        'name': 'Hindi/Hinglish',
        'script': 'Latn',
        'comedians': [
            'Vir Das',
            'Zakir Khan',
            'Biswa Kalyan Rath',
            'Kaneez Surka',
            'Atul Khatri'
        ]
    },
    'bengali': {
        'code': 'bn',
        'name': 'Bengali',
        'script': 'Beng',
        'comedians': [
            'Mir Afsar Ali',
            'Sourav Ghosh',
            'Rohit Ghosh',
            'Rajat Chakraborty'
        ]
    }
}

# Video URLs by comedian (these are examples - expand as needed)
COMEDIAN_VIDEOS = {
    'Vir Das': [
        'https://www.youtube.com/watch?v=xxx',  # Replace with actual URLs
        # Add more Vir Das videos
    ],
    'Zakir Khan': [
        # Add Zakir Khan video URLs
    ],
    'Biswa Kalyan Rath': [
        # Add Biswa Kalyan Rath video URLs
    ],
    'Kaneez Surka': [
        # Add Kaneez Surka video URLs
    ],
    'Atul Khatri': [
        # Add Atul Khatri video URLs
    ],
    'Mir Afsar Ali': [
        # Add Mir Afsar Ali video URLs
    ],
    'Sourav Ghosh': [
        # Add Sourav Ghosh video URLs
    ],
    'Rohit Ghosh': [
        # Add Rohit Ghosh video URLs
    ],
    'Rajat Chakraborty': [
        # Add Rajat Chakraborty video URLs
    ]
}

# Search queries to find videos automatically
SEARCH_QUERIES = {
    'hindi_hinglish': [
        'Vir Das standup comedy full show',
        'Zakir Khan comedy special',
        'Biswa Kalyan Rath standup',
        'Kaneez Surka comedy',
        'Atul Khatri standup comedy'
    ],
    'bengali': [
        'Mir Afsar Ali standup comedy Bengali',
        'Sourav Ghosh Bengali standup',
        'Rohit Ghosh Bengali comedy',
        'Rajat Chakraborty standup Bengali',
        'Bengali standup comedy full show'
    ]
}


def extract_video_id(url: str) -> Optional[str]:
    """Extract YouTube video ID from URL."""
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
        r'^([a-zA-Z0-9_-]{11})$'  # Direct video ID
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None


def load_whisper_model(model_size: str = 'base'):
    """Load Whisper model (lazy loading)."""
    global whisper_model
    
    if not WHISPER_AVAILABLE:
        raise RuntimeError("Whisper not available")
    
    if whisper_model is None:
        print(f"🔄 Loading Whisper model: {model_size}")
        whisper_model = whisper.load_model(model_size)
        print(f"✅ Whisper model loaded")
    
    return whisper_model


def get_youtube_transcript(video_id: str, language_code: str = None) -> Optional[Dict]:
    """
    Get transcript using YouTubeTranscriptApi.
    
    Returns transcript dict with word-level timestamps if available.
    """
    if not YOUTUBE_API_AVAILABLE:
        return None
    
    try:
        # Try to get transcript
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'hi', 'bn'])
        
        # Check if word-level data is available
        try:
            # Try to get word-level transcript
            word_level = YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'hi', 'bn'])
            
            # Note: YouTubeTranscriptApi doesn't always provide word-level timestamps
            # If available, format accordingly
            transcript_data = {
                'text': ' '.join([t['text'] for t in transcript_list]),
                'segments': [
                    {
                        'start': t['start'],
                        'end': t['start'] + t['duration'],
                        'text': t['text'],
                        'words': []  # No word-level data from YouTube API
                    }
                    for t in transcript_list
                ],
                'source': 'youtube_api',
                'language': language_code or 'auto'
            }
            
            return transcript_data
            
        except Exception as e:
            print(f"⚠️ Could not get word-level data: {e}")
            return None
    
    except NoTranscriptFound:
        print(f"⚠️ No transcript found for video {video_id}")
        return None
    except TranscriptsDisabled:
        print(f"⚠️ Transcripts disabled for video {video_id}")
        return None
    except Exception as e:
        print(f"❌ Error fetching YouTube transcript: {e}")
        return None


def download_audio_with_ytdlp(video_id: str, output_dir: Path) -> Optional[Path]:
    """
    Download audio from YouTube using yt-dlp.
    
    Returns path to downloaded audio file.
    """
    if not YTDLP_AVAILABLE:
        return None
    
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{video_id}.wav"
    
    # Skip if already exists
    if output_path.exists():
        print(f"   ✓ Audio already exists: {output_path}")
        return output_path
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
            'preferredquality': '192',
        }],
        'outtmpl': str(output_dir / f"{video_id}.%(ext)s"),
        'quiet': False,
        'no_warnings': False,
    }
    
    url = f"https://www.youtube.com/watch?v={video_id}"
    
    try:
        print(f"   📥 Downloading audio...")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        # Check if file was created
        if output_path.exists():
            print(f"   ✅ Audio downloaded: {output_path}")
            return output_path
        else:
            print(f"   ❌ Audio file not found after download")
            return None
    
    except Exception as e:
        print(f"   ❌ Error downloading audio: {e}")
        return None


def transcribe_audio_with_whisper(audio_path: Path, language_code: str = None) -> Optional[Dict]:
    """
    Transcribe audio using Whisper.
    
    Returns transcript dict with segments and word-level timestamps.
    """
    if not WHISPER_AVAILABLE:
        return None
    
    try:
        model = load_whisper_model('base')
        
        print(f"   🎤 Transcribing with Whisper...")
        result = model.transcribe(
            str(audio_path),
            language=language_code,  # None = auto-detect
            word_timestamps=True,
            fp16=False  # Disable FP16 for compatibility
        )
        
        transcript_data = {
            'text': result['text'],
            'segments': result['segments'],
            'source': 'whisper',
            'language': language_code or result.get('language', 'auto')
        }
        
        print(f"   ✅ Transcription complete: {len(result['segments'])} segments")
        return transcript_data
    
    except Exception as e:
        print(f"   ❌ Error transcribing with Whisper: {e}")
        return None


def process_video(video_url: str, comedian: str, language_config: Dict, 
                  strategy: str = 'auto') -> Optional[Dict]:
    """
    Process a single video with fallback strategy.
    
    Args:
        video_url: YouTube video URL or video ID
        comedian: Comedian name
        language_config: Language configuration dict
        strategy: 'youtube_api', 'whisper', or 'auto' (try both)
    
    Returns:
        Transcript dict or None if failed
    """
    video_id = extract_video_id(video_url)
    if not video_id:
        print(f"❌ Invalid video URL: {video_url}")
        return None
    
    print(f"\n🎬 Processing: {video_id}")
    print(f"   Comedian: {comedian}")
    print(f"   Language: {language_config['name']} ({language_config['code']})")
    
    transcript = None
    
    # Strategy 1: Try YouTube API first
    if strategy in ['auto', 'youtube_api']:
        print(f"   📡 Trying YouTubeTranscriptApi...")
        transcript = get_youtube_transcript(video_id, language_config['code'])
        
        if transcript:
            print(f"   ✅ Got transcript from YouTube API")
            return transcript
        else:
            print(f"   ⚠️ YouTube API failed, trying fallback...")
    
    # Strategy 2: Fallback to Whisper
    if strategy in ['auto', 'whisper']:
        print(f"   🎵 Downloading audio for Whisper transcription...")
        
        # Download audio
        audio_path = download_audio_with_ytdlp(video_id, AUDIO_DIR)
        
        if not audio_path:
            print(f"   ❌ Could not download audio")
            return None
        
        # Transcribe with Whisper
        # Map language code for Whisper
        whisper_lang_map = {
            'hi': 'hi',      # Hindi
            'hi-latn': 'hi', # Hinglish (use Hindi model)
            'bn': 'bn'       # Bengali
        }
        whisper_lang = whisper_lang_map.get(language_config['code'], None)
        
        transcript = transcribe_audio_with_whisper(audio_path, whisper_lang)
        
        if transcript:
            print(f"   ✅ Got transcript from Whisper")
            return transcript
        else:
            print(f"   ❌ Whisper transcription failed")
            return None
    
    return None


def save_transcript(transcript: Dict, video_id: str, comedian: str, 
                   language_config: Dict) -> Path:
    """Save transcript to JSON file."""
    # Create comedian directory
    comedian_dir = TRANSCRIPT_DIR / comedian.lower().replace(' ', '_')
    comedian_dir.mkdir(parents=True, exist_ok=True)
    
    # Add metadata (ensure metadata dict exists)
    if 'metadata' not in transcript:
        transcript['metadata'] = {}
    
    transcript['metadata'].update({
        'video_id': video_id,
        'comedian': comedian,
        'language_code': language_config['code'],
        'language_name': language_config['name'],
        'script': language_config['script'],
        'collected_at': time.strftime('%Y-%m-%d %H:%M:%S')
    })
    
    # Save transcript
    output_path = comedian_dir / f"{video_id}_transcript.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(transcript, f, ensure_ascii=False, indent=2)
    
    print(f"   💾 Saved: {output_path}")
    return output_path


def search_youtube_videos(query: str, max_results: int = 5) -> List[str]:
    """
    Search YouTube for videos matching query.
    
    Note: This requires youtube-search-python or similar.
    For now, return empty list - user should provide URLs.
    """
    # TODO: Implement YouTube search
    # Could use youtube-search-python or yt-dlp's search
    print(f"⚠️ YouTube search not implemented. Please provide video URLs directly.")
    return []


def collect_comedian_videos(comedian: str, videos: List[str], 
                           language_config: Dict, strategy: str = 'auto') -> Dict:
    """
    Collect all videos for a comedian.
    
    Returns summary dict with counts.
    """
    print(f"\n{'='*60}")
    print(f"🎭 Collecting: {comedian}")
    print(f"{'='*60}")
    
    results = {
        'comedian': comedian,
        'language': language_config['code'],
        'total_videos': len(videos),
        'successful': 0,
        'failed': 0,
        'total_words': 0,
        'total_duration': 0
    }
    
    for video_url in videos:
        # Process video
        transcript = process_video(video_url, comedian, language_config, strategy)
        
        if transcript:
            # Get video ID
            video_id = extract_video_id(video_url)
            
            # Save transcript
            save_transcript(transcript, video_id, comedian, language_config)
            
            # Count words
            word_count = len(transcript.get('text', '').split())
            results['total_words'] += word_count
            
            # Estimate duration from segments
            if 'segments' in transcript and transcript['segments']:
                last_segment = transcript['segments'][-1]
                duration = last_segment.get('end', 0)
                results['total_duration'] += duration
            
            results['successful'] += 1
        else:
            results['failed'] += 1
        
        # Rate limiting
        time.sleep(1)
    
    return results


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Collect Indian comedy data from YouTube")
    parser.add_argument('--comedian', '-c', type=str, default='all',
                       help="Specific comedian to collect (default: all)")
    parser.add_argument('--language', '-l', type=str, default='all',
                       choices=['all', 'hindi_hinglish', 'bengali'],
                       help="Language to collect (default: all)")
    parser.add_argument('--strategy', '-s', type=str, default='auto',
                       choices=['auto', 'youtube_api', 'whisper'],
                       help="Transcription strategy (default: auto)")
    parser.add_argument('--videos', '-v', type=str, nargs='+',
                       help="List of video URLs to process")
    parser.add_argument('--config', type=str,
                       help="Path to JSON config file with video URLs")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("INDIAN COMEDY DATA COLLECTION")
    print("=" * 60)
    print(f"Strategy: {args.strategy}")
    print(f"Language: {args.language}")
    print(f"Comedian: {args.comedian}")
    print("=" * 60)
    
    # Create directories
    TRANSCRIPT_DIR.mkdir(parents=True, exist_ok=True)
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load custom video config if provided
    if args.config:
        with open(args.config) as f:
            COMEDIAN_VIDEOS.update(json.load(f))
    
    # If specific videos provided, process them directly
    if args.videos:
        print(f"\n📋 Processing {len(args.videos)} provided videos...")
        
        for video_url in args.videos:
            # Try to detect language from URL or use default
            # For now, default to hindi_hinglish
            lang_config = LANGUAGE_CONFIG['hindi_hinglish']
            
            # Process video (comedian will be 'unknown' if not specified)
            transcript = process_video(video_url, 'unknown', lang_config, args.strategy)
            
            if transcript:
                video_id = extract_video_id(video_url)
                save_transcript(transcript, video_id, 'unknown', lang_config)
        
        return
    
    # Collect by comedian
    all_results = []
    
    for lang_key, lang_config in LANGUAGE_CONFIG.items():
        if args.language != 'all' and args.language != lang_key:
            continue
        
        print(f"\n{'#'*60}")
        print(f"# LANGUAGE: {lang_config['name'].upper()}")
        print(f"{'#'*60}")
        
        for comedian in lang_config['comedians']:
            if args.comedian != 'all' and args.comedian != comedian:
                continue
            
            videos = COMEDIAN_VIDEOS.get(comedian, [])
            
            if not videos:
                print(f"⚠️ No videos configured for {comedian}")
                print(f"   Add videos to COMEDIAN_VIDEOS or use --videos flag")
                continue
            
            result = collect_comedian_videos(comedian, videos, lang_config, args.strategy)
            all_results.append(result)
    
    # Print summary
    print(f"\n{'='*60}")
    print("COLLECTION SUMMARY")
    print(f"{'='*60}")
    
    for result in all_results:
        print(f"\n🎭 {result['comedian']}")
        print(f"   Language: {result['language']}")
        print(f"   Videos: {result['successful']}/{result['total_videos']} successful")
        print(f"   Words: {result['total_words']:,}")
        print(f"   Duration: {result['total_duration']/60:.1f} minutes")
    
    # Totals
    total_successful = sum(r['successful'] for r in all_results)
    total_failed = sum(r['failed'] for r in all_results)
    total_words = sum(r['total_words'] for r in all_results)
    total_duration = sum(r['total_duration'] for r in all_results)
    
    print(f"\n{'='*60}")
    print(f"TOTAL: {total_successful} videos successful, {total_failed} failed")
    print(f"Total words: {total_words:,}")
    print(f"Total duration: {total_duration/60:.1f} minutes")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
