#!/usr/bin/env python3
"""
V9 Audio Data Collection Pipeline - ENHANCED
Uses YouTube Transcript API (already installed v1.2.4) + yt-dlp for audio extraction.

Usage:
    python training/audio_data_collector.py --comedian "Dave Chappelle" --max_videos 5
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional, List, Dict

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Check for youtube_transcript_api
try:
    from youtube_transcript_api import YouTubeTranscriptApi
    YOUTUBE_TRANSCRIPT_AVAILABLE = True
except ImportError:
    YOUTUBE_TRANSCRIPT_AVAILABLE = False
    print("⚠️  youtube_transcript_api not found, installing...")


def check_dependencies():
    """Check required dependencies are installed."""
    deps = {
        'ffmpeg': 'ffmpeg -version',
        'yt-dlp': 'yt-dlp --version',
        'whisper': 'python3 -c "import whisper; print(whisper.__version__)"',
    }
    
    missing = []
    for name, cmd in deps.items():
        try:
            subprocess.run(cmd, shell=True, capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            missing.append(name)
    
    if missing:
        print(f"⚠️  Missing dependencies: {', '.join(missing)}")
        print("Install with:")
        print(f"  brew install ffmpeg yt-dlp")
        print(f"  pip install openai-whisper")
        return False
    return True


def ensure_youtube_transcript_api():
    """Ensure youtube-transcript-api is installed."""
    if not YOUTUBE_TRANSCRIPT_AVAILABLE:
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'youtube-transcript-api'], check=True)
        from youtube_transcript_api import YouTubeTranscriptApi
    return True


def search_youtube_comedy(query: str, max_results: int = 5) -> List[Dict]:
    """Search YouTube for comedy videos using yt-dlp."""
    print(f"🔍 Searching YouTube for: {query}")
    
    cmd = [
        'yt-dlp',
        '--flat-playlist',
        '--print', '%(id)s|%(title)s|%(duration)s|%(upload_date)s',
        f'ytsearch{max_results}:{query} stand-up comedy special'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        videos = []
        for line in result.stdout.strip().split('\n'):
            if '|' in line:
                parts = line.split('|')
                if len(parts) >= 3:
                    videos.append({
                        'id': parts[0],
                        'title': parts[1],
                        'duration': parts[2],
                        'date': parts[3] if len(parts) > 3 else None
                    })
        print(f"   Found {len(videos)} videos")
        return videos
    except subprocess.CalledProcessError as e:
        print(f"❌ Search failed: {e}")
        return []


def fetch_youtube_transcript(video_id: str) -> Optional[Dict]:
    """Fetch transcript from YouTube video using YouTubeTranscriptApi."""
    try:
        ytt_api = YouTubeTranscriptApi()
        transcript = ytt_api.fetch(video_id)
        
        words = []
        for entry in transcript:
            words.append({
                'word': entry.text,
                'start': entry.start,
                'end': entry.end,
                'duration': entry.duration
            })
        
        return {
            'video_id': video_id,
            'words': words,
            'language': transcript.language,
            'is_generated': transcript.is_generated
        }
    except Exception as e:
        print(f"   ⚠️  Could not fetch transcript: {e}")
        return None


def download_audio(video_id: str, output_dir: Path) -> Optional[Path]:
    """Download audio from YouTube video."""
    output_path = output_dir / f"{video_id}.mp3"
    
    if output_path.exists():
        print(f"   Audio already exists: {output_path.name}")
        return output_path
    
    cmd = [
        'yt-dlp',
        '-x',  # Extract audio
        '--audio-format', 'mp3',
        '--audio-quality', '0',  # Best quality
        '-o', str(output_path),
        f'https://www.youtube.com/watch?v={video_id}'
    ]
    
    try:
        subprocess.run(cmd, capture_output=True, check=True)
        print(f"   Downloaded: {output_path.name}")
        return output_path
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Download failed: {e}")
        return None


def transcribe_with_whisper(audio_path: Path, model_size: str = "base") -> Optional[Dict]:
    """Fallback transcription with Whisper if YouTube transcript fails."""
    import whisper
    
    print(f"   Transcribing with Whisper ({model_size})...")
    
    model = whisper.load_model(model_size)
    result = model.transcribe(str(audio_path), word_timestamps=True)
    
    return result


def create_audio_dataset(
    comedian: str,
    max_videos: int = 5,
    data_dir: Optional[Path] = None,
    whisper_model: str = "base"
) -> dict:
    """
    Main collection pipeline for one comedian.
    Uses YouTube Transcript API first, falls back to Whisper.
    """
    if data_dir is None:
        data_dir = PROJECT_ROOT / "data" / "audio_comedy"
    
    audio_dir = data_dir / "audio" / comedian.lower().replace(" ", "_")
    transcript_dir = data_dir / "transcripts" / comedian.lower().replace(" ", "_")
    
    audio_dir.mkdir(parents=True, exist_ok=True)
    transcript_dir.mkdir(parents=True, exist_ok=True)
    
    # Ensure YouTube Transcript API is available
    ensure_youtube_transcript_api()
    
    # Search for videos
    videos = search_youtube_comedy(comedian, max_videos)
    
    results = {
        'comedian': comedian,
        'videos_processed': 0,
        'audio_files': [],
        'transcripts': [],
        'youtube_transcripts': 0,
        'whisper_transcripts': 0,
        'dataset_path': str(data_dir)
    }
    
    for video in videos:
        video_id = video['id']
        print(f"\n📹 Processing: {video['title']}")
        print(f"   Video ID: {video_id}")
        
        # Try YouTube Transcript API first (preferred - has timing)
        transcript_data = fetch_youtube_transcript(video_id)
        
        if transcript_data and transcript_data['words']:
            # Save YouTube transcript
            transcript_path = transcript_dir / f"{video_id}_transcript.json"
            with open(transcript_path, 'w') as f:
                json.dump({
                    'video_id': video_id,
                    'title': video['title'],
                    'comedian': comedian,
                    'source': 'youtube_transcript_api',
                    'words': transcript_data['words'],
                    'language': transcript_data.get('language', 'en'),
                    'is_generated': transcript_data.get('is_generated', False)
                }, f, indent=2)
            
            results['youtube_transcripts'] += 1
            results['videos_processed'] += 1
            results['transcripts'].append(str(transcript_path))
            print(f"   ✅ YouTube transcript: {len(transcript_data['words'])} words")
            
            # Download audio for future use (even if we have transcript)
            audio_path = download_audio(video_id, audio_dir)
            if audio_path:
                results['audio_files'].append(str(audio_path))
        else:
            # Fallback: Download audio and transcribe with Whisper
            print(f"   📥 No YouTube transcript, downloading for Whisper...")
            audio_path = download_audio(video_id, audio_dir)
            
            if audio_path:
                results['audio_files'].append(str(audio_path))
                
                # Transcribe with Whisper
                whisper_result = transcribe_with_whisper(audio_path, whisper_model)
                
                if whisper_result:
                    transcript_path = transcript_dir / f"{video_id}_transcript.json"
                    with open(transcript_path, 'w') as f:
                        json.dump({
                            'video_id': video_id,
                            'title': video['title'],
                            'comedian': comedian,
                            'source': 'whisper',
                            'words': whisper_result.get('words', []),
                            'segments': whisper_result.get('segments', []),
                            'language': whisper_result.get('language', 'en')
                        }, f, indent=2)
                    
                    results['whisper_transcripts'] += 1
                    results['videos_processed'] += 1
                    results['transcripts'].append(str(transcript_path))
                    print(f"   ✅ Whisper transcript: {len(whisper_result.get('words', []))} words")
    
    # Save manifest
    manifest_path = data_dir / f"{comedian.lower().replace(' ', '_')}_manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📊 Collection Summary for {comedian}:")
    print(f"   Videos processed: {results['videos_processed']}")
    print(f"   YouTube transcripts: {results['youtube_transcripts']}")
    print(f"   Whisper transcripts: {results['whisper_transcripts']}")
    print(f"   Audio files: {len(results['audio_files'])}")
    print(f"   Manifest: {manifest_path}")
    
    return results


def main():
    parser = argparse.ArgumentParser(description="V9 Audio Data Collection Pipeline")
    parser.add_argument('--comedian', '-c', type=str, required=True,
                        help="Comedian name to search for")
    parser.add_argument('--max_videos', '-n', type=int, default=5,
                        help="Maximum videos to process (default: 5)")
    parser.add_argument('--model', '-m', type=str, default='base',
                        choices=['tiny', 'base', 'small', 'medium', 'large'],
                        help="Whisper model size (default: base)")
    parser.add_argument('--data_dir', '-d', type=str, default=None,
                        help="Output directory (default: data/audio_comedy)")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("V9 AUDIO DATA COLLECTION PIPELINE")
    print("=" * 60)
    print(f"Using YouTube Transcript API + Whisper fallback")
    
    # Check deps
    if not check_dependencies():
        print("\n⚠️  Please install missing dependencies first.")
        sys.exit(1)
    
    # Collect data
    results = create_audio_dataset(
        comedian=args.comedian,
        max_videos=args.max_videos,
        data_dir=Path(args.data_dir) if args.data_dir else None,
        whisper_model=args.model
    )
    
    if results['videos_processed'] > 0:
        print("\n🎉 Collection complete!")
        print(f"   Dataset location: {results['dataset_path']}")
    else:
        print("\n❌ No videos collected. Check YouTube availability.")


if __name__ == '__main__':
    main()
