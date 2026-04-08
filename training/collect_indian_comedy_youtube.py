#!/usr/bin/env python3
"""
YouTube Hindi/Hinglish Comedy Laughter Data Collector
=====================================================
Collects word-level transcripts from Indian stand-up comedy YouTube videos
with laughter markers for training data creation.

Target Comedians:
- Abhishek Upmanyu
- Aakash Gupta
- Biswa Kalyan Rath
- Rahul Subramanian
- Kanan Gill
- Sapan Verma
- Varun Thakur
- Dhruv Rathee (comedy)
- other Indian stand-up comedians

APIs Used:
- YouTube Transcript API (primary)
- SARVAM STT (fallback for Hindi transcription)
- ElevenLabs (optional TTS for synthesis)

Usage:
    python3 collect_indian_comedy_youtube.py --max-videos 50 --output-dir data/indian_comedy
"""

import json
import re
import argparse
import sys
import time
import os
import base64
import requests
from pathlib import Path
from typing import List, Dict, Optional, Set
from datetime import datetime

try:
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api._errors import (
        TranscriptsDisabled,
        NoTranscriptFound,
        VideoUnavailable,
    )
except ImportError:
    print("Installing youtube-transcript-api...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "youtube-transcript-api", "-q"])
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api._errors import (
        TranscriptsDisabled,
        NoTranscriptFound,
        VideoUnavailable,
    )


SARVAM_API_KEY = os.getenv("SARVAM_API_KEY", "sk_0ct1mbzm_wsoETmHdputtlGmsowQgnd7K")
SARVAM_STT_URL = "https://api.sarvam.ai/speech-to-text"

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")


class SARVAM_STT:
    """SARVAM AI Speech-to-Text for Hindi/Hinglish transcription."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or SARVAM_API_KEY
        self.url = SARVAM_STT_URL

    def transcribe(self, audio_path: Path) -> Optional[Dict]:
        """Transcribe audio file using SARVAM STT API."""
        if not self.api_key:
            print("    SARVAM API key not available")
            return None

        try:
            with open(audio_path, 'rb') as f:
                audio_data = f.read()

            base64_audio = base64.b64encode(audio_data).decode('utf-8')

            headers = {
                'api-subscription-key': self.api_key,
                'Content-Type': 'application/json'
            }

            payload = {
                'audio': base64_audio,
                'model': 'saarika:v2',
                'language_code': 'hi-IN'
            }

            response = requests.post(self.url, json=payload, headers=headers, timeout=60)

            if response.status_code == 200:
                result = response.json()
                return {
                    'text': result.get('transcript', ''),
                    'language': 'hi-IN',
                    ' confidence': result.get('confidence', 0.0)
                }
            else:
                print(f"    SARVAM API error: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            print(f"    SARVAM transcription error: {e}")
            return None


class ElevenLabsTTS:
    """ElevenLabs TTS for potential synthesis tasks."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or ELEVENLABS_API_KEY
        self.url = "https://api.elevenlabs.io/v1/text-to-speech"

    def synthesize(self, text: str, voice_id: str = "rachel") -> Optional[bytes]:
        """Synthesize speech using ElevenLabs TTS."""
        if not self.api_key:
            return None

        try:
            headers = {
                'xi-api-key': self.api_key,
                'Content-Type': 'application/json'
            }

            payload = {
                'text': text,
                'voice_id': voice_id
            }

            response = requests.post(self.url, json=payload, headers=headers, timeout=30)

            if response.status_code == 200:
                return response.content
            else:
                return None

        except Exception:
            return None


INDIAN_COMEDIAN_CHANNELS = {
    "Abhishek Upmanyu": [
        "UCvjgEDvS2I8_5w6Gr1wqrvg",
        "AbhishekUpmanyu",
    ],
    "Aakash Gupta": [
        "UC8mDFyup9CkPhMDAeIVS5XQ",
        "AakashGupta",
    ],
    "Biswa Kalyan Rath": [
        "UC9jtmsyE5wVs5Pu-ZKGRvqA",
        "BiswaKalyanRath",
    ],
    "Rahul Subramanian": [
        "UC7qEXVBOY-E6WkA3lJe5gDQ",
        "RahulSubramanian",
    ],
    "Kanan Gill": [
        "UC3DoKAd7y6HP3_3NvT3VzkA",
        "KananGill",
    ],
    "Sapan Verma": [
        "UCEmtB1u_VllR2LpLtc0Cy8Q",
        "SapanVerma",
    ],
    "Varun Thakur": [
        "UC6M6g4yE8R0qDVqG4cgX6KA",
        "VarunThakur",
    ],
    "Dhruv Rathee": [
        "UCBq-U4Rk6TeC7l1L8BQqy1w",
        "DhruvRathee",
    ],
    "Comedy Store": [
        "UC6NYE-YhJtF8GnEG-9HUn5A",
        "ComedyStore",
    ],
    "Eros Now": [
        "UCQ5m22-7Xgc-pcFNumhnTWQ",
        "ErosNow",
    ],
}


COMEDY_SPECIALS = [
    "8SqIn2J1Z1c", "gDDfNhCBpOU", "n9ncJ1lP8U8",
]


SEARCH_QUERIES = [
    "hindi stand up comedy full",
    "hinglish comedy special",
    "indian comedy special full",
    "abhishek upmanyu full special",
    "aakash gupta comedy special",
    "biswa kalyan rath stand up",
]


LAUGHTER_MARKERS = [
    "[laughter]", "(laughter)", "*laughter*", "[Laughter]", "(Laughter)",
    "*Laughter*", "[Applause]", "(Applause]", "*Applause*", "[Applause]",
    "[cheering]", "(cheering)", "*cheering*", "[cheers]", "(cheers]",
    "[crowd]", "(crowd]", "[laughs]", "(laughs]", "*laughs*",
    "[haha]", "(haha)", "*haha*", "[lol]", "(lol)",
    "haha", "hehe", "lol", "rofl",
]


def clean_text(text: str) -> str:
    """Clean transcript text."""
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def has_laughter_marker(text: str) -> bool:
    """Check if text contains laughter markers."""
    text_lower = text.lower()
    for marker in LAUGHTER_MARKERS:
        if marker.lower() in text_lower:
            return True
    return False


def detect_hindi_hinglish(text: str) -> bool:
    """Detect if text contains Hindi/Hinglish content."""
    hindi_chars = len(re.findall(r'[\u0900-\u097F]', text))
    hinglish_patterns = [
        r'\b(mera|tera|teri|meri|apna|unka|hamara|kya|hai|nahi|to|phir|baat|kiya)\b',
        r'\b(achha|theek|haan|nahi|bilkul|bas|matlab|yahan|wahan)\b',
        r'\b(sirf|lekin|aur|ya|woh|yeh|agar|toh|voh)\b',
        r'\b(standup|comedy|show|special|punchline|joke|inflation|dekh|bhai)\b',
    ]

    hinglish_count = 0
    for pattern in hinglish_patterns:
        hinglish_count += len(re.findall(pattern, text.lower()))

    return hindi_chars > 5 or hinglish_count >= 2


def get_transcript(video_id: str, prefer_manual: bool = True) -> Optional[List[Dict]]:
    """Fetch transcript for a video."""
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

        transcript = None
        if prefer_manual:
            for t in transcript_list:
                if not t.is_generated:
                    transcript = t
                    break

        if transcript is None:
            for t in transcript_list:
                if t.is_generated:
                    transcript = t
                    break

        if transcript is None:
            return None

        transcript_data = transcript.fetch()

        segments = []
        for item in transcript_data:
            segment = {
                'start': item.start,
                'duration': item.duration,
                'text': item.text,
            }

            if hasattr(item, 'words') and item.words:
                segment['words'] = [
                    {
                        'word': w.word,
                        'start': w.start,
                        'end': w.end,
                        'confidence': getattr(w, 'confidence', 1.0)
                    }
                    for w in item.words
                ]
            else:
                segment['words'] = None

            segments.append(segment)

        return segments

    except (TranscriptsDisabled, NoTranscriptFound, VideoUnavailable) as e:
        return None
    except Exception as e:
        print(f"    Error fetching {video_id}: {e}")
        return None


def process_video(
    video_id: str,
    comedian: str = "unknown",
    use_sarvam_fallback: bool = True,
    audio_cache_dir: Path = None
) -> Optional[Dict]:
    """Process a single video and extract laughter data."""
    print(f"Processing {video_id} ({comedian})...")

    segments = get_transcript(video_id)

    if segments is None and use_sarvam_fallback:
        print(f"  -> YouTube transcript unavailable, trying SARVAM STT...")
        segments = get_sarvam_transcript(video_id, audio_cache_dir)

    if segments is None:
        print(f"  -> No transcript available (YouTube or SARVAM)")
        return None

    examples = []
    laughter_segments = 0
    total_words = 0
    laughter_words = 0
    hindi_hinglish_segments = 0

    for seg in segments:
        text = clean_text(seg['text'])
        if not text:
            continue

        if seg.get('words'):
            words = [w['word'] for w in seg['words']]
            start_times = [w['start'] for w in seg['words']]
        else:
            words = text.split()
            start_times = None

        if len(words) == 0:
            continue

        has_laugh = has_laughter_marker(text)
        is_hindi = detect_hindi_hinglish(text)

        if is_hindi:
            hindi_hinglish_segments += 1

        if has_laugh:
            labels = [1] * len(words)
            laughter_segments += 1
            laughter_words += len(words)
        else:
            labels = [0] * len(words)

        total_words += len(words)

        example = {
            'text': text,
            'words': words,
            'labels': labels,
            'start_time': seg.get('start', 0),
            'has_laughter': has_laugh,
            'is_hindi_hinglish': is_hindi,
            'comedian': comedian,
            'words_data': seg.get('words')
        }
        examples.append(example)

    if total_words == 0:
        return None

    return {
        'video_id': video_id,
        'comedian': comedian,
        'total_segments': len(examples),
        'laughter_segments': laughter_segments,
        'hindi_hinglish_segments': hindi_hinglish_segments,
        'total_words': total_words,
        'laughter_words': laughter_words,
        'laughter_ratio_segments': laughter_segments / len(examples) if examples else 0,
        'laughter_ratio_words': laughter_words / total_words if total_words else 0,
        'has_laughter_content': laughter_segments > 0,
        'has_hindi_content': hindi_hinglish_segments > 0,
        'examples': examples
    }


def get_sarvam_transcript(video_id: str, audio_cache_dir: Path = None) -> Optional[List[Dict]]:
    """Download audio and transcribe using SARVAM STT."""
    try:
        import yt_dlp
    except ImportError:
        print("    Installing yt-dlp for audio download...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp", "-q"])
        import yt_dlp

    if audio_cache_dir is None:
        audio_cache_dir = Path("data/indian_comedy/audio_cache")

    audio_cache_dir.mkdir(parents=True, exist_ok=True)
    audio_path = audio_cache_dir / f"{video_id}.wav"

    try:
        ydl_opts = {
            'format': 'wav/best',
            'outtmpl': str(audio_cache_dir / video_id),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
            }],
            'quiet': True,
            'no_warnings': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([f"https://www.youtube.com/watch?v={video_id}"])

        if not audio_path.exists():
            return None

        sarvam = SARVAM_STT()
        result = sarvam.transcribe(audio_path)

        if result and result.get('text'):
            return [{
                'start': 0,
                'duration': 0,
                'text': result['text'],
                'words': None
            }]

    except Exception as e:
        print(f"    SARVAM fallback error: {e}")

    return None


def collect_data(
    video_ids: List[str],
    output_dir: str = "data/indian_comedy",
    delay_between_requests: float = 1.0,
    max_retries: int = 3,
    comedian_map: Dict[str, str] = None
) -> Dict:
    """Collect laughter data from multiple videos."""

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    all_results = []
    stats = {
        'total_videos': len(video_ids),
        'successful': 0,
        'failed': 0,
        'with_laughter': 0,
        'with_hindi': 0,
        'total_segments': 0,
        'laughter_segments': 0,
        'total_words': 0,
        'laughter_words': 0,
        'failed_ids': []
    }

    print(f"Processing {len(video_ids)} videos...")
    print("-" * 60)

    for i, video_id in enumerate(video_ids):
        comedian = comedian_map.get(video_id, "unknown") if comedian_map else "unknown"
        print(f"[{i+1}/{len(video_ids)}] ", end="", flush=True)

        for attempt in range(max_retries):
            try:
                result = process_video(video_id, comedian)

                if result is None:
                    stats['failed'] += 1
                    stats['failed_ids'].append(video_id)
                    print(f"Failed (no transcript)")
                    break

                stats['successful'] += 1
                stats['total_segments'] += result['total_segments']
                stats['laughter_segments'] += result['laughter_segments']
                stats['total_words'] += result['total_words']
                stats['laughter_words'] += result['laughter_words']

                if result['has_laughter_content']:
                    stats['with_laughter'] += 1

                if result['has_hindi_content']:
                    stats['with_hindi'] += 1

                all_results.append(result)
                print(f"✓ {result['laughter_segments']}/{result['total_segments']} laugh, {result.get('hindi_hinglish_segments', 0)} hindi")

                break

            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"  Retry {attempt+1}...")
                    time.sleep(delay_between_requests * 2)
                else:
                    stats['failed'] += 1
                    stats['failed_ids'].append(video_id)
                    print(f"Error: {e}")

        time.sleep(delay_between_requests)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_path / f"indian_comedy_raw_{timestamp}.json"

    output_data = {
        'metadata': {
            'collected_at': timestamp,
            'total_videos_requested': len(video_ids),
            'total_videos_processed': stats['successful'],
            'total_with_laughter': stats['with_laughter'],
            'total_with_hindi': stats['with_hindi'],
            'comedians': list(set(comedian_map.values())) if comedian_map else []
        },
        'stats': stats,
        'data': all_results
    }

    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)

    summary_file = output_path / f"indian_comedy_summary_{timestamp}.txt"
    with open(summary_file, 'w') as f:
        f.write(f"Indian Comedy Laughter Data Collection Summary\n")
        f.write(f"=" * 60 + "\n")
        f.write(f"Collected: {timestamp}\n")
        f.write(f"Videos requested: {stats['total_videos']}\n")
        f.write(f"Videos successful: {stats['successful']}\n")
        f.write(f"Videos with laughter: {stats['with_laughter']}\n")
        f.write(f"Videos with Hindi/Hinglish: {stats['with_hindi']}\n")
        f.write(f"Total segments: {stats['total_segments']}\n")
        f.write(f"Laughter segments: {stats['laughter_segments']}\n")
        f.write(f"Total words: {stats['total_words']}\n")
        f.write(f"Laughter words: {stats['laughter_words']}\n")

    print("\n" + "=" * 60)
    print("DATA COLLECTION COMPLETE")
    print("=" * 60)
    print(f"Videos processed: {stats['successful']}/{stats['total_videos']}")
    print(f"With laughter content: {stats['with_laughter']}")
    print(f"With Hindi/Hinglish content: {stats['with_hindi']}")
    print(f"Total segments: {stats['total_segments']}")
    print(f"Laughter segments: {stats['laughter_segments']}")
    print(f"\nOutput: {output_file}")

    return stats


def convert_to_training_format(
    raw_data_path: Path,
    output_dir: Path,
    min_seq_length: int = 5,
    max_seq_length: int = 256
):
    """Convert collected data to JSONL training format."""
    with open(raw_data_path, 'r') as f:
        data = json.load(f)

    output_dir.mkdir(parents=True, exist_ok=True)

    for split in ['train', 'valid', 'test']:
        split_file = output_dir / f"{split}.jsonl"
        if split_file.exists():
            split_file.unlink()

    all_examples = []

    for video in data.get('data', []):
        video_id = video['video_id']
        comedian = video.get('comedian', 'unknown')

        for example in video.get('examples', []):
            if len(example['words']) < min_seq_length:
                continue

            all_examples.append({
                'example_id': f"indian_comedy_{video_id}_{len(all_examples)}",
                'language': 'hi',  # Hindi/Hinglish
                'words': example['words'],
                'labels': example['labels'],
                'metadata': {
                    'source': 'indian_comedy_youtube',
                    'video_id': video_id,
                    'comedian': comedian,
                    'laughter_type': 'word_level',
                    'is_hindi_hinglish': example.get('is_hindi_hinglish', False)
                }
            })

    total = len(all_examples)
    train_end = int(total * 0.8)
    valid_end = int(total * 0.9)

    splits = {
        'train': all_examples[:train_end],
        'valid': all_examples[train_end:valid_end],
        'test': all_examples[valid_end:]
    }

    for split_name, examples in splits.items():
        output_file = output_dir / f"{split_name}.jsonl"
        with open(output_file, 'w') as f:
            for ex in examples:
                f.write(json.dumps(ex) + "\n")
        print(f"{split_name}: {len(examples)} examples")

    return {'train': len(splits['train']), 'valid': len(splits['valid']), 'test': len(splits['test'])}


def main():
    parser = argparse.ArgumentParser(description="Collect Indian comedy YouTube laughter data")
    parser.add_argument("--max-videos", type=int, default=100, help="Max videos to process")
    parser.add_argument("--output-dir", type=str, default="data/indian_comedy", help="Output directory")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between requests (seconds)")
    parser.add_argument("--convert", action="store_true", help="Convert to training format")
    args = parser.parse_args()

    print(f"Indian Comedy Laughter Data Collector (Hindi/Hinglish)")
    print(f"=" * 60)
    print(f"Target comedians: {list(INDIAN_COMEDIAN_CHANNELS.keys())}")
    print(f"Max videos: {args.max_videos}")
    print(f"Output directory: {args.output_dir}")
    print(f"Delay between requests: {args.delay}s")
    print("=" * 60)

    video_list = COMEDY_SPECIALS[:args.max_videos]

    comedian_map = {vid: "Abhishek Upmanyu" for vid in COMEDY_SPECIALS}

    collect_data(
        video_ids=video_list,
        output_dir=args.output_dir,
        delay_between_requests=args.delay,
        comedian_map=comedian_map
    )

    if args.convert:
        raw_files = list(Path(args.output_dir).glob("*.json"))
        if raw_files:
            latest = max(raw_files, key=lambda p: p.stat().st_mtime)
            print(f"\nConverting {latest} to training format...")
            result = convert_to_training_format(latest, Path(args.output_dir) / "training")
            print(f"\nConversion complete: {result}")


if __name__ == "__main__":
    main()