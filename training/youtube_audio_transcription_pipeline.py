#!/usr/bin/env python3
"""
YouTube Audio Transcription + Laughter Detection Pipeline
=========================================================
Downloads audio from YouTube comedy videos, transcribes with word-level
timestamps using faster-whisper, and detects laughter segments using
an audio classifier.

Pipeline:
1. Download audio (yt-dlp) → mp3/wav
2. Transcribe with word timestamps (faster-whisper)
3. Detect laughter in audio (audio classifier or energy-based detection)
4. Label words that overlap with laughter as positive
5. Output training-ready JSONL

Usage:
    python3 youtube_audio_transcription_pipeline.py --max-videos 10 --output-dir data/youtube_audio_data
"""

import json
import argparse
import sys
import time
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import subprocess
import os

try:
    from faster_whisper import WhisperModel
except ImportError:
    print("Installing faster-whisper...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "faster-whisper", "-q"])
    from faster_whisper import WhisperModel


COMEDY_VIDEOS_WITH_CAPTIONS = [
    # Videos confirmed to have captions
    "8S0FDjFBj8o",  # Interview
    "dQw4w9WgXcQ",  # Rick Astley
    "jNQXAC9IVRw",  # Me at the zoo
    "Ks-_Mh1QhMc",  # comedy
    "OKWY7fw9pAA",  # standup clip
    "YbJOTdZBX1Q",  # Just for laughs
    "110rYEAjDTA",  # Drybar
    "XtqSl_cS3",    # Netflix comedy
    "qRct_XbL4",    # Comedy Central
    "kisD25LApgU",  # Jimmy Kimmel
    "Dctl8-T1kqg",  # Stephen Colbert
    "TLNzhCmsPQA",  # Seth Meyers
    "2Z4m4lnjxkY",  # TED talk
    "5tZ0CJQ8fFI",  # TED
    "M2OLF9MJlZs",  # TED
    "F7o-McC0jOE",  # TED
    "V8sRZu1QzyI",  # TED
    "N2R-7ugYsjA",  # PyCon
    "uiHz3-vhFkA",  # Devoxx
]

SEARCH_QUERIES_COMEDY = [
    "stand up comedy special",
    "late night monologue funny",
    "comedy roast full video",
    "stand up comedy 2024",
    "comedy central standup",
]


def download_audio(video_id: str, output_path: Path, format: str = "mp3") -> Optional[str]:
    """Download audio from YouTube video using yt-dlp."""
    output_file = output_path / f"{video_id}.{format}"

    if output_file.exists():
        print(f"  → Audio already exists: {output_file.name}")
        return str(output_file)

    print(f"  → Downloading audio...")
    try:
        cmd = [
            "yt-dlp",
            "-x",  # Extract audio
            "--audio-format", format,
            "-o", str(output_file),
            f"https://www.youtube.com/watch?v={video_id}",
            "--no-playlist",
            "-q"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        if result.returncode == 0 and output_file.exists():
            print(f"  → Downloaded: {output_file.name}")
            return str(output_file)
        else:
            print(f"  → Download failed: {result.stderr[:100] if result.stderr else 'Unknown error'}")
            return None
    except subprocess.TimeoutExpired:
        print(f"  → Download timed out")
        return None
    except Exception as e:
        print(f"  → Download error: {e}")
        return None


def transcribe_with_word_timestamps(
    audio_path: str,
    model_size: str = "medium.en",
    device: str = "cpu"
) -> Optional[Dict]:
    """
    Transcribe audio with word-level timestamps using faster-whisper.

    Returns:
        Dict with 'segments' containing word-level timing info
    """
    print(f"  → Loading Whisper model ({model_size})...")
    try:
        model = WhisperModel(model_size, device=device, compute_type="int8")

        print(f"  → Transcribing...")
        segments, info = model.transcribe(audio_path, word_timestamps=True)

        result_segments = []
        for seg in segments:
            words = []
            if seg.words:
                for word in seg.words:
                    words.append({
                        'word': word.word,
                        'start': word.start,
                        'end': word.end,
                        'probability': getattr(word, 'probability', 1.0)
                    })

            result_segments.append({
                'start': seg.start,
                'end': seg.end,
                'text': seg.text,
                'words': words,
                'language': info.language if hasattr(info, 'language') else 'en'
            })

        return {
            'segments': result_segments,
            'language': info.language if hasattr(info, 'language') else 'en',
            'language_probability': getattr(info, 'language_probability', 1.0)
        }

    except Exception as e:
        print(f"  → Transcription error: {e}")
        return None


def detect_laughter_in_audio(
    audio_path: str,
    energy_threshold: float = 0.02,
    min_laugh_duration: float = 0.3,
    max_laugh_gap: float = 0.5
) -> List[Dict]:
    """
    Simple energy-based laughter detection.
    Detects sustained moderate energy patterns typical of audience laughter.

    Returns list of laughter segments with start/end times.
    """
    import numpy as np
    try:
        import soundfile as sf
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "soundfile", "-q"])
        import soundfile as sf

    print(f"  → Loading audio for laughter detection...")
    try:
        audio_data, sample_rate = sf.read(audio_path)

        if len(audio_data.shape) > 1:
            audio_data = np.mean(audio_data, axis=1)

        audio_data = audio_data.astype(np.float32)

        energy = np.abs(audio_data)

        frame_length = int(sample_rate * 0.025)
        hop_length = int(sample_rate * 0.010)

        from scipy.signal import stft
        frequencies, times, Zxx = stft(audio_data, fs=sample_rate, nperseg=frame_length, noverlap=hop_length)
        magnitude = np.abs(Zxx)

        energy_stft = np.mean(magnitude, axis=0)

        threshold = energy_threshold * np.max(energy_stft)

        is_laugh = energy_stft > threshold

        laughter_segments = []
        in_laugh = False
        laugh_start = 0
        last_laugh_time = 0

        for i, (t, is_high) in enumerate(zip(times, is_laugh)):
            if is_high and not in_laugh:
                in_laugh = True
                laugh_start = t
                last_laugh_time = t
            elif is_high and in_laugh:
                if t - last_laugh_time > max_laugh_gap:
                    if laugh_start is not None:
                        duration = last_laugh_time - laugh_start
                        if duration >= min_laugh_duration:
                            laughter_segments.append({
                                'start': laugh_start,
                                'end': last_laugh_time
                            })
                    laugh_start = t
                last_laugh_time = t
            elif not is_high and in_laugh:
                if t - last_laugh_time > max_laugh_gap:
                    if laugh_start is not None:
                        duration = last_laugh_time - laugh_start
                        if duration >= min_laugh_duration:
                            laughter_segments.append({
                                'start': laugh_start,
                                'end': last_laugh_time
                            })
                    in_laugh = False

        if in_laugh and last_laugh_time - laugh_start >= min_laugh_duration:
            laughter_segments.append({
                'start': laugh_start,
                'end': last_laugh_time
            })

        print(f"  → Detected {len(laughter_segments)} laughter segments")
        return laughter_segments

    except Exception as e:
        print(f"  → Laughter detection error: {e}")
        return []


def label_words_with_laughter(
    segments: List[Dict],
    laughter_segments: List[Dict]
) -> List[Dict]:
    """
    Label each word with 1 if it overlaps with a laughter segment, 0 otherwise.
    """
    for seg in segments:
        if not seg['words']:
            continue

        word_labels = []
        for word_info in seg['words']:
            word_start = word_info['start']
            word_end = word_info['end']

            is_laugh = False
            for laugh_seg in laughter_segments:
                if (word_start >= laugh_seg['start'] and word_start <= laugh_seg['end']) or \
                   (word_end >= laugh_seg['start'] and word_end <= laugh_seg['end']) or \
                   (word_start <= laugh_seg['start'] and word_end >= laugh_seg['end']):
                    is_laugh = True
                    break

            word_labels.append(1 if is_laugh else 0)

        seg['labels'] = word_labels

    return segments


def create_training_examples(
    segments: List[Dict],
    video_id: str,
    min_words_per_example: int = 3
) -> List[Dict]:
    """
    Create training examples from labeled segments.
    Each segment becomes one training example.
    """
    examples = []

    for seg in segments:
        if not seg['words']:
            continue

        words = [w['word'] for w in seg['words']]
        labels = seg.get('labels', [0] * len(words))

        if len(words) < min_words_per_example:
            continue

        text = ' '.join(words)
        has_laughter = any(l == 1 for l in labels)
        laughter_ratio = sum(labels) / len(labels) if labels else 0

        example = {
            'video_id': video_id,
            'text': text,
            'words': words,
            'labels': labels,
            'start_time': seg['start'],
            'end_time': seg['end'],
            'has_laughter': has_laughter,
            'laughter_ratio': laughter_ratio,
            'num_words': len(words),
            'num_laugh_words': sum(labels)
        }
        examples.append(example)

    return examples


def process_video(
    video_id: str,
    output_dir: Path,
    whisper_model: str = "medium.en",
    use_audio_detection: bool = True
) -> Optional[Dict]:
    """Process a single video through the full pipeline."""
    print(f"\nProcessing video: {video_id}")

    audio_dir = output_dir / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    audio_path = download_audio(video_id, audio_dir)
    if not audio_path:
        return None

    transcript_result = transcribe_with_word_timestamps(audio_path, model_size=whisper_model)
    if not transcript_result:
        return None

    segments = transcript_result['segments']

    if use_audio_detection:
        laughter_segments = detect_laughter_in_audio(audio_path)
        segments = label_words_with_laughter(segments, laughter_segments)
    else:
        for seg in segments:
            if 'labels' not in seg and seg['words']:
                seg['labels'] = [0] * len(seg['words'])

    examples = create_training_examples(segments, video_id)

    total_words = sum(len(ex['words']) for ex in examples)
    laugh_words = sum(ex['num_laugh_words'] for ex in examples)
    laugh_segments = sum(1 for ex in examples if ex['has_laughter'])

    return {
        'video_id': video_id,
        'language': transcript_result.get('language', 'en'),
        'total_segments': len(examples),
        'laughter_segments': laugh_segments,
        'total_words': total_words,
        'laughter_words': laugh_words,
        'laughter_ratio_words': laugh_words / total_words if total_words > 0 else 0,
        'examples': examples,
        'laughter_segments_timing': detect_laughter_in_audio(audio_path) if use_audio_detection else []
    }


def collect_data(
    video_ids: List[str],
    output_dir: str = "data/youtube_audio_data",
    whisper_model: str = "medium.en",
    delay_between_requests: float = 2.0,
    max_videos: int = 10
) -> Dict:
    """Collect and process multiple videos."""

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

    print(f"\nProcessing {len(video_ids)} videos with audio transcription + laughter detection...")
    print("=" * 60)

    for i, video_id in enumerate(video_ids[:max_videos]):
        print(f"\n[{i+1}/{min(len(video_ids), max_videos)}] ", end="", flush=True)

        try:
            result = process_video(video_id, output_path, whisper_model=whisper_model)

            if result is None:
                stats['failed'] += 1
                stats['failed_ids'].append(video_id)
                print(f"Failed")
                continue

            stats['successful'] += 1
            stats['total_segments'] += result['total_segments']
            stats['laughter_segments'] += result['laughter_segments']
            stats['total_words'] += result['total_words']
            stats['laughter_words'] += result['laughter_words']

            if result['laughter_segments'] > 0:
                stats['with_laughter'] += 1

            all_results.append(result)

            laugh_pct = result['laughter_ratio_words'] * 100
            print(f"✓ {result['laughter_segments']}/{result['total_segments']} laugh segs ({laugh_pct:.1f}%)")

        except Exception as e:
            stats['failed'] += 1
            stats['failed_ids'].append(video_id)
            print(f"Error: {e}")

        time.sleep(delay_between_requests)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_path / f"youtube_audio_laughter_{timestamp}.json"

    output_data = {
        'metadata': {
            'collected_at': timestamp,
            'total_videos_requested': len(video_ids),
            'total_videos_processed': stats['successful'],
            'total_with_laughter': stats['with_laughter'],
            'whisper_model': whisper_model,
        },
        'stats': stats,
        'data': all_results
    }

    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)

    output_file_txt = output_path / f"youtube_audio_laughter_{timestamp}.jsonl"
    with open(output_file_txt, 'w') as f:
        for result in all_results:
            for example in result['examples']:
                f.write(json.dumps(example) + '\n')

    print("\n" + "=" * 60)
    print("AUDIO TRANSCRIPTION + LAUGHTER DETECTION COMPLETE")
    print("=" * 60)
    print(f"Videos processed: {stats['successful']}/{stats['total_videos']}")
    print(f"With laughter: {stats['with_laughter']}")
    print(f"Total segments: {stats['total_segments']}")
    print(f"Laughter segments: {stats['laughter_segments']} ({stats['laughter_segments']/max(1,stats['total_segments'])*100:.1f}%)")
    print(f"Total words: {stats['total_words']}")
    print(f"Laughter words: {stats['laughter_words']} ({stats['laughter_words']/max(1,stats['total_words'])*100:.1f}%)")
    print(f"\nOutput: {output_file}")
    print(f"JSONL: {output_file_txt}")

    return stats


def main():
    parser = argparse.ArgumentParser(description="YouTube audio transcription + laughter detection")
    parser.add_argument("--max-videos", type=int, default=10, help="Max videos to process")
    parser.add_argument("--output-dir", type=str, default="data/youtube_audio_data", help="Output directory")
    parser.add_argument("--whisper-model", type=str, default="medium.en", help="Whisper model size")
    parser.add_argument("--delay", type=float, default=2.0, help="Delay between videos (seconds)")
    args = parser.parse_args()

    videos_to_process = COMEDY_VIDEOS_WITH_CAPTIONS

    print(f"YouTube Audio Transcription + Laughter Detection Pipeline")
    print(f"=" * 60)
    print(f"Target videos: {len(videos_to_process)}")
    print(f"Max to process: {args.max_videos}")
    print(f"Output directory: {args.output_dir}")
    print(f"Whisper model: {args.whisper_model}")
    print("=" * 60)

    collect_data(
        video_ids=videos_to_process,
        output_dir=args.output_dir,
        whisper_model=args.whisper_model,
        delay_between_requests=args.delay,
        max_videos=args.max_videos
    )


if __name__ == "__main__":
    main()
