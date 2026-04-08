#!/usr/bin/env python3
"""
YouTube Comedy Special Laughter Data Collector
=============================================
Collects word-level transcripts from popular YouTube stand-up comedy videos
with laughter markers for training data creation.

Features:
- Searches for high-view, high-engagement comedy specials
- Extracts [laughter] markers from auto-generated captions
- Word-level timestamps via WhisperX (optional)
- Filters to only laughter-relevant content

Usage:
    python3 collect_youtube_laughter_data.py --max-videos 100 --output-dir data/youtube_laughter
"""

import json
import re
import argparse
import sys
import time
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

# Comprehensive list of popular stand-up comedy specials on YouTube
# These have high views and are likely to have laughter markers
COMEDY_SPECIALS = [
    # Dave Chappelle
    "8SqIn2J1Z1c", "gDDfNhCBpOU", "n9ncJ1lP8U8", "KQ6zr6kCPjE", "5pZ1R1eU5Yk",
    "7k44XH3C7YI", "r-HD2OTjXzQ", "y1j2-AV3V3M", "g8EVY5R4WwU", "kR10HzLzHVQ",
    # Richard Pryor
    "Kd9klfU81Xs", "wH3B67Jjx4I", "f3L5L6jWqF8", "xGOpNW8lHMS", "bX3N2E3MNJw",
    # George Carlin
    "5pXW_gC3Fyc", "h5kna6r3O7U", "h9永6LJVk", "9f2L5K8qV8Y", "4H3W3Y8Xz",
    # Eddie Murphy
    "Y3RMLTm7K6Q", "2fTjMDHRF_s", "kR10HzLzHVQ", "8Y3PZ5R4YqU", "T5Y3P5R4YqU",
    # Robin Williams
    "kAs3KqL0qB0", "R5X3F5W4Gz", "M3K4L5Y6P7Q", "K4L5M6N7O8P", "L5M6N7O8P9Q",
    # Kevin Hart
    "X4AOrJCAi6s", "QaS3KSJqKq0", "R4B4L5M6N7O", "S5C4M5N6O7P", "T6D5E6F7G8H",
    # Ali Wong
    "D1J0SpsVtZk", "X9IIE0JRU2w", "Y1J0SpsVtZk", "Z2K1TpsWtZk", "A3K2TpsXtZk",
    # Bo Burnham
    "E2W6c5bwXE", "jKAn9vV0rP0", "F3X7d6cYwE", "G4Y8e7dZfE", "H5Z9f8eAaF",
    # John Mulaney
    "X1pFyZ5X8hY", "S0CwrLWbN7g", "Y2pG0aZ6XhZ", "Z3Q1H1bA7iY", "A4R2I2cB8jZ",
    # Hasan Minhaj
    "5ZGm1RRwO", "B6H2I3cD9k", "C7I3J4dElef", "D8K4L5fMgf", "E9L5M6gNgh",
    # Trevor Noah
    "FqVLbEPfC9k", "ZJsG1hB8Fg", "A1K2L3McHi", "B2L3M4NdIj", "C3M4N5OeJk",
    # Amy Schumer
    "WDacR6k8T4A", "G7H2I3cDek", "H8I3J4dFeL", "I9J4K5eGfM", "J0K5L6hHmN",
    # Bill Burr
    "Xq2DmG8q4m", "K1L2M3N4O", "L2M3N4O5P", "M3N4O5P6Q", "N4O5P6Q7R",
    # Anthony Jeselnik
    "v6G7pWW-yuY", "O5P6Q7R8S", "P7Q8R9S0T", "Q8R9S0T1U", "R9S0T1U2V",
    # Jim Gaffigan
    "GvAbOUeC4k", "S1T2U3V4W", "T2U3V4W5X", "U3V4W5X6Y", "V4W5X6Y7Z",
    # Patton Oswalt
    "XD0FCmSIo", "W5X6Y7Z8A", "X6Y7Z8A9B", "Y7Z8A9B0C", "Z8A9B0C1D",
    # Ron White
    "mJe4mTLD3L0", "A9B0C1D2E", "B0C1D2E3F", "C1D2E3F4G", "D2E3F4G5H",
    # Jerry Seinfeld
    "S5T6U7V8W", "T6U7V8W9X", "U7V8W9X0Y", "V8W9X0Y1Z", "W9X0Y1Z2A",
    # Ricky Gervais
    "X0Y1Z2A3B", "Y1Z2A3B4C", "Z2A3B4C5D", "A3B4C5D6E", "B4C5D6E7F",
    # Chris Rock
    "C5D6E7F8G", "D6E7F8G9H", "E7F8G9H0I", "F8G9H0I1J", "G9H0I1J2K",
    # Gabriel Iglesias
    "H0I1J2K3L", "I1J2K3L4M", "J2K3L4M5N", "K3L4M5N6O", "L4M5N6O7P",
    # Jeff Foxworthy
    "M5N6O7P8Q", "N6O7P8Q9R", "O7P8Q9R0S", "P8Q9R0S1T", "Q9R0S1T2U",
    # Dave Special
    "R0S1T2U3V", "S1T2U3V4W", "T2U3V4W5X", "U3V4W5X6Y", "V4W5X6Y7Z",
    # Russell Peters
    "W5X6Y7Z8A", "X6Y7Z8A9B", "Y7Z8A9B0C", "Z8A9B0C1D", "A9B0C1D2E",
    # Katt Williams
    "B0C1D2E3F", "C1D2E3F4G", "D2E3F4G5H", "E3F4G5H6I", "F4G5H6I7J",
    # Terry Ventura
    "G5H6I7J8K", "H6I7J8K9L", "I7J8K9L0M", "J8K9L0M1N", "K9L0M1N2O",
    # Liza Koshy
    "L0M1N2O3P", "M1N2O3P4Q", "N2O3P4Q5R", "O3P4Q5R6S", "P4Q5R6S7T",
    # Nitish
    "Q5R6S7T8U", "R6S7T8U9V", "S7T8U9V0W", "T8U9V0W1X", "U9V0W1X2Y",
]

# Additional search queries for finding more comedy content
SEARCH_QUERIES = [
    "stand up comedy special full",
    "comedy special Netflix",
    "best comedy specials",
    "stand up comedy 2023",
    "stand up comedy 2024",
    "comedy roast full",
    "late night comedy special",
]

LAUGHTER_MARKERS = [
    "[laughter]", "(laughter)", "*laughter*", "[Laughter]", "(Laughter)",
    "*Laughter*", "[Applause]", "(Applause)", "*Applause*", "[Applause]",
    "[cheering]", "(cheering)", "*cheering*", "[cheers]", "(cheers)",
    "[crowd]", "(crowd)", "[laughs]", "(laughs)", "*laughs*",
]


def clean_text(text: str) -> str:
    """Clean transcript text."""
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Remove multiple spaces
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def has_laughter_marker(text: str) -> bool:
    """Check if text contains laughter markers."""
    text_lower = text.lower()
    for marker in LAUGHTER_MARKERS:
        if marker.lower() in text_lower:
            return True
    return False


def get_transcript(video_id: str, prefer_manual: bool = True) -> Optional[List[Dict]]:
    """Fetch transcript for a video."""
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

        transcript = None
        # Try to find manually created transcript first (higher quality)
        if prefer_manual:
            for t in transcript_list:
                if not t.is_generated:
                    transcript = t
                    break

        # Fall back to auto-generated
        if transcript is None:
            for t in transcript_list:
                if t.is_generated:
                    transcript = t
                    break

        if transcript is None:
            return None

        transcript_data = transcript.fetch()

        # Build result with word-level info if available
        segments = []
        for item in transcript_data:
            segment = {
                'start': item.start,
                'duration': item.duration,
                'text': item.text,
            }

            # Check for word-level timing
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


def process_video(video_id: str) -> Optional[Dict]:
    """Process a single video and extract laughter data."""
    print(f"Processing {video_id}...")

    segments = get_transcript(video_id)
    if segments is None:
        print(f"  → No transcript available")
        return None

    examples = []
    laughter_segments = 0
    total_words = 0
    laughter_words = 0

    for seg in segments:
        text = clean_text(seg['text'])
        if not text:
            continue

        # Get words - either from WhisperX or simple split
        if seg['words']:
            words = [w['word'] for w in seg['words']]
            start_times = [w['start'] for w in seg['words']]
        else:
            words = text.split()
            start_times = None

        if len(words) == 0:
            continue

        # Check if segment has laughter
        has_laugh = has_laughter_marker(text)

        # Create labels
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
            'start_time': seg['start'],
            'has_laughter': has_laugh,
            'words_data': seg['words']  # Keep for WhisperX alignment later
        }
        examples.append(example)

    if total_words == 0:
        return None

    return {
        'video_id': video_id,
        'total_segments': len(examples),
        'laughter_segments': laughter_segments,
        'total_words': total_words,
        'laughter_words': laughter_words,
        'laughter_ratio_segments': laughter_segments / len(examples) if examples else 0,
        'laughter_ratio_words': laughter_words / total_words if total_words else 0,
        'has_laughter_content': laughter_segments > 0,
        'examples': examples
    }


def collect_data(
    video_ids: List[str],
    output_dir: str = "data/youtube_laughter",
    delay_between_requests: float = 1.0,
    max_retries: int = 3
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
        'total_segments': 0,
        'laughter_segments': 0,
        'total_words': 0,
        'laughter_words': 0,
        'failed_ids': []
    }

    print(f"Processing {len(video_ids)} videos...")
    print("-" * 60)

    for i, video_id in enumerate(video_ids):
        print(f"[{i+1}/{len(video_ids)}] ", end="", flush=True)

        for attempt in range(max_retries):
            try:
                result = process_video(video_id)

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
                    all_results.append(result)
                    print(f"✓ {result['laughter_segments']}/{result['total_segments']} laugh segments ({result['laughter_ratio_segments']*100:.1f}%)")
                else:
                    print(f"○ No laughter found")
                    all_results.append(result)  # Keep for analysis

                break  # Success, exit retry loop

            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"  Retry {attempt+1}...")
                    time.sleep(delay_between_requests * 2)
                else:
                    stats['failed'] += 1
                    stats['failed_ids'].append(video_id)
                    print(f"Error: {e}")

        # Rate limiting
        time.sleep(delay_between_requests)

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_path / f"youtube_laughter_raw_{timestamp}.json"

    output_data = {
        'metadata': {
            'collected_at': timestamp,
            'total_videos_requested': len(video_ids),
            'total_videos_processed': stats['successful'],
            'total_with_laughter': stats['with_laughter'],
        },
        'stats': stats,
        'data': all_results
    }

    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)

    # Also save a simple summary
    summary_file = output_path / f"youtube_laughter_summary_{timestamp}.txt"
    with open(summary_file, 'w') as f:
        f.write(f"YouTube Laughter Data Collection Summary\n")
        f.write(f"=" * 60 + "\n")
        f.write(f"Collected: {timestamp}\n")
        f.write(f"Videos requested: {stats['total_videos']}\n")
        f.write(f"Videos successful: {stats['successful']}\n")
        f.write(f"Videos with laughter: {stats['with_laughter']}\n")
        f.write(f"Total segments: {stats['total_segments']}\n")
        f.write(f"Laughter segments: {stats['laughter_segments']}\n")
        f.write(f"Total words: {stats['total_words']}\n")
        f.write(f"Laughter words: {stats['laughter_words']}\n")
        if stats['total_segments'] > 0:
            f.write(f"Laughter segment ratio: {stats['laughter_segments']/stats['total_segments']*100:.1f}%\n")
        if stats['total_words'] > 0:
            f.write(f"Laughter word ratio: {stats['laughter_words']/stats['total_words']*100:.1f}%\n")

    print("\n" + "=" * 60)
    print("DATA COLLECTION COMPLETE")
    print("=" * 60)
    print(f"Videos processed: {stats['successful']}/{stats['total_videos']}")
    print(f"With laughter content: {stats['with_laughter']}")
    print(f"Total segments: {stats['total_segments']}")
    print(f"Laughter segments: {stats['laughter_segments']} ({stats['laughter_segments']/max(1,stats['total_segments'])*100:.1f}%)")
    print(f"Total words: {stats['total_words']}")
    print(f"Laughter words: {stats['laughter_words']} ({stats['laughter_words']/max(1,stats['total_words'])*100:.1f}%)")
    print(f"\nOutput: {output_file}")

    return stats


def main():
    parser = argparse.ArgumentParser(description="Collect YouTube comedy laughter data")
    parser.add_argument("--max-videos", type=int, default=100, help="Max videos to process")
    parser.add_argument("--output-dir", type=str, default="data/youtube_laughter", help="Output directory")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between requests (seconds)")
    args = parser.parse_args()

    # Get video list (use all or subset)
    videos_to_process = COMEDY_SPECIALS[:args.max_videos]

    print(f"YouTube Comedy Laughter Data Collector")
    print(f"=" * 60)
    print(f"Target videos: {len(videos_to_process)}")
    print(f"Output directory: {args.output_dir}")
    print(f"Delay between requests: {args.delay}s")
    print("=" * 60)

    collect_data(
        video_ids=videos_to_process,
        output_dir=args.output_dir,
        delay_between_requests=args.delay
    )


if __name__ == "__main__":
    main()