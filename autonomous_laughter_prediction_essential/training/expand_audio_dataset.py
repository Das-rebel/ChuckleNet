#!/usr/bin/env python3
"""
Expand audio dataset: download audio + VTT + run Whisper + align for new videos.

Pipeline per video:
1. Download audio (MP3) via yt-dlp
2. Download VTT subtitles (for laugh labels)
3. Run Whisper to get word-level timestamps
4. Align Whisper timestamps with VTT laugh markers
5. Output aligned segments to data/audio_comedy/aligned_segments.jsonl

Usage:
    python training/expand_audio_dataset.py --videos UvANWG6cQi8 OLGrx-m-0iA zKUpf1Vx0vs
    python training/expand_audio_dataset.py --top 5  # download top 5 candidates
"""

import os
import sys
import json
import subprocess
import argparse
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path(__file__).resolve().parent.parent
AUDIO_DIR = PROJECT_ROOT / "data" / "audio_comedy" / "audio"
VTT_DIR = PROJECT_ROOT / "data" / "audio_comedy" / "vtt_subtitles"
TRANSCRIPT_DIR = PROJECT_ROOT / "data" / "audio_comedy" / "transcripts"
ALIGNED_OUTPUT = PROJECT_ROOT / "data" / "audio_comedy" / "aligned_segments.jsonl"
STATS_OUTPUT = PROJECT_ROOT / "data" / "audio_comedy" / "alignment_stats.json"

# Pre-screened candidates ranked by laughter marker density
CANDIDATES = [
    {"id": "UvANWG6cQi8", "title": "Best Of Stand-Up Compilation", "vtt_lines": 19552, "laugh_markers": 366},
    {"id": "OLGrx-m-0iA", "title": "2 Hours All Killer Comedy", "vtt_lines": 26912, "laugh_markers": 115},
    {"id": "zKUpf1Vx0vs", "title": "Shane Gillis Live In Austin", "vtt_lines": 9784, "laugh_markers": 80},
    {"id": "fDANtIrT3T8", "title": "30 Viral Jokes Compilation", "vtt_lines": 8144, "laugh_markers": 73},
    {"id": "GxqAHM79xs8", "title": "Best Of Matt Rife", "vtt_lines": 9688, "laugh_markers": 64},
    {"id": "mDjDBWukuCk", "title": "Comedy Roadshow Compilation", "vtt_lines": 22160, "laugh_markers": 60},
    {"id": "5mvq4yvbw-s", "title": "32 Viral Jokes Vol 2", "vtt_lines": 9296, "laugh_markers": 36},
    {"id": "4UQTaw6yXa4", "title": "Ricky Gervais 25 min", "vtt_lines": 4632, "laugh_markers": 9},
]

# Already processed videos (skip these)
DONE_VIDEOS = {"5S5iZZEtTkg", "anUJnsICCXo", "wY5-8kvMEh0", "0qGd6KXh_ig", "seW0_VSzuHg"}


def log(msg):
    print(msg, flush=True)


def run_cmd(cmd, timeout=120):
    """Run a command and return result."""
    result = subprocess.run(
        cmd, capture_output=True, text=True, timeout=timeout,
        env={**os.environ, "PATH": f"{os.path.expanduser('~/.deno/bin')}:{os.environ.get('PATH', '')}"}
    )
    return result


def download_audio(video_id, output_dir):
    """Download audio as MP3."""
    mp3_file = output_dir / f"{video_id}.mp3"
    if mp3_file.exists():
        log(f"  Audio exists: {mp3_file}")
        return mp3_file

    log(f"  Downloading audio...")
    result = run_cmd([
        "yt-dlp", "-x", "--audio-format", "mp3", "--audio-quality", "5",
        "-o", str(output_dir / f"{video_id}.%(ext)s"),
        f"https://www.youtube.com/watch?v={video_id}"
    ], timeout=300)

    if mp3_file.exists():
        size_mb = mp3_file.stat().st_size / 1024 / 1024
        log(f"  Downloaded: {mp3_file} ({size_mb:.0f}MB)")
        return mp3_file

    # Check for other formats
    for ext in ["mp3", "webm", "m4a", "wav"]:
        alt = output_dir / f"{video_id}.{ext}"
        if alt.exists():
            log(f"  Downloaded (alt): {alt}")
            return alt

    log(f"  ERROR: Audio download failed for {video_id}")
    log(f"  stderr: {result.stderr[:300]}")
    return None


def download_vtt(video_id, output_dir):
    """Download VTT subtitles."""
    # Try multiple possible filenames
    possible = [
        output_dir / f"{video_id}.vtt",
        output_dir / f"{video_id}.en.vtt",
    ]
    for p in possible:
        if p.exists():
            log(f"  VTT exists: {p}")
            return p

    log(f"  Downloading VTT...")
    result = run_cmd([
        "yt-dlp", "--write-auto-sub", "--sub-lang", "en", "--sub-format", "vtt",
        "--skip-download", "-o", str(output_dir / video_id),
        f"https://www.youtube.com/watch?v={video_id}"
    ], timeout=60)

    # Check what was downloaded
    for pattern in [f"{video_id}*.vtt"]:
        matches = list(output_dir.glob(pattern))
        if matches:
            vtt = matches[0]
            log(f"  Downloaded: {vtt}")
            return vtt

    # Try manual subtitles
    result = run_cmd([
        "yt-dlp", "--write-sub", "--sub-lang", "en", "--sub-format", "vtt",
        "--skip-download", "-o", str(output_dir / video_id),
        f"https://www.youtube.com/watch?v={video_id}"
    ], timeout=60)

    for pattern in [f"{video_id}*.vtt"]:
        matches = list(output_dir.glob(pattern))
        if matches:
            vtt = matches[0]
            log(f"  Downloaded (manual): {vtt}")
            return vtt

    log(f"  WARNING: No VTT for {video_id}")
    return None


def run_whisper(audio_path, output_dir, video_id):
    """Run Whisper to get word-level timestamps."""
    transcript_file = output_dir / f"{video_id}_transcript.json"
    if transcript_file.exists():
        log(f"  Transcript exists: {transcript_file}")
        return transcript_file

    log(f"  Running Whisper (this may take a while)...")
    # Use Python whisper if available, otherwise skip
    try:
        import whisper
        model = whisper.load_model("base")
        result = whisper.transcribe(
            str(audio_path),
            word_timestamps=True,
            language="en",
        )

        # Save transcript
        transcript = {
            "video_id": video_id,
            "title": "",
            "comedian": "unknown",
            "language": "en",
            "segments": result.get("segments", []),
            "words": [],
        }
        with open(transcript_file, "w") as f:
            json.dump(transcript, f, indent=2, ensure_ascii=False)

        word_count = sum(len(s.get("words", [])) for s in result.get("segments", []))
        log(f"  Whisper: {word_count} words transcribed")
        return transcript_file

    except ImportError:
        log(f"  Whisper not installed. Attempting pip install...")
        run_cmd(["pip3", "install", "openai-whisper"], timeout=120)
        log(f"  Retrying Whisper...")
        try:
            import whisper
            return run_whisper(audio_path, output_dir, video_id)
        except Exception as e:
            log(f"  ERROR: Whisper failed: {e}")
            return None
    except Exception as e:
        log(f"  ERROR: Whisper transcription failed: {e}")
        return None


def process_video(video_id, title, skip_whisper=False):
    """Full pipeline for a single video."""
    log(f"\n{'─' * 50}")
    log(f"Processing: {video_id} - {title}")

    # Create comedian directory
    comedian_dir = "downloaded"
    audio_subdir = AUDIO_DIR / comedian_dir
    audio_subdir.mkdir(parents=True, exist_ok=True)
    transcript_subdir = TRANSCRIPT_DIR / comedian_dir
    transcript_subdir.mkdir(parents=True, exist_ok=True)
    VTT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Download audio
    audio_path = download_audio(video_id, audio_subdir)
    if not audio_path:
        return None

    # 2. Download VTT
    vtt_path = download_vtt(video_id, VTT_DIR)

    # 3. Run Whisper
    transcript_path = None
    if not skip_whisper:
        transcript_path = run_whisper(audio_path, transcript_subdir, video_id)
        if not transcript_path:
            # Check if transcript already exists elsewhere
            for root, dirs, files in os.walk(TRANSCRIPT_DIR):
                for f in files:
                    if video_id in f and f.endswith(".json"):
                        transcript_path = Path(root) / f
                        log(f"  Found existing transcript: {transcript_path}")
                        break
                if transcript_path:
                    break
    else:
        for root, dirs, files in os.walk(TRANSCRIPT_DIR):
            for f in files:
                if video_id in f and f.endswith(".json"):
                    transcript_path = Path(root) / f
                    break
            if transcript_path:
                break

    return {
        "video_id": video_id,
        "title": title,
        "audio_path": str(audio_path) if audio_path else None,
        "vtt_path": str(vtt_path) if vtt_path else None,
        "transcript_path": str(transcript_path) if transcript_path else None,
    }


def main():
    parser = argparse.ArgumentParser(description="Expand audio dataset with new comedy videos")
    parser.add_argument("--videos", nargs="+", help="Specific video IDs to process")
    parser.add_argument("--top", type=int, help="Process top N candidates by laughter density")
    parser.add_argument("--skip-whisper", action="store_true", help="Skip Whisper (use existing transcripts)")
    parser.add_argument("--download-only", action="store_true", help="Only download audio+VTT, no Whisper/alignment")
    args = parser.parse_args()

    # Determine videos to process
    if args.videos:
        videos = [{"id": v, "title": "unknown"} for v in args.videos]
    elif args.top:
        videos = CANDIDATES[:args.top]
    else:
        videos = CANDIDATES[:5]  # Default: top 5

    # Filter out already-done videos
    videos = [v for v in videos if v["id"] not in DONE_VIDEOS]

    log("=" * 60)
    log("AUDIO DATASET EXPANSION")
    log("=" * 60)
    log(f"Videos to process: {len(videos)}")
    for v in videos:
        log(f"  {v['id']}: {v.get('title', '?')} ({v.get('laugh_markers', '?')} laugh markers)")

    results = []
    for v in videos:
        result = process_video(v["id"], v.get("title", ""), skip_whisper=args.skip_whisper)
        if result:
            results.append(result)

    # Summary
    log(f"\n{'=' * 60}")
    log("EXPANSION SUMMARY")
    log(f"{'=' * 60}")

    has_audio = sum(1 for r in results if r["audio_path"])
    has_vtt = sum(1 for r in results if r["vtt_path"])
    has_transcript = sum(1 for r in results if r["transcript_path"])

    log(f"  Processed: {len(results)} videos")
    log(f"  Audio downloaded: {has_audio}")
    log(f"  VTT downloaded: {has_vtt}")
    log(f"  Whisper transcripts: {has_transcript}")

    if not args.download_only and has_vtt > 0 and has_transcript > 0:
        log(f"\n  Ready for alignment! Run:")
        log(f"  python training/align_whisper_to_vtt.py --window 5.0")
    elif has_audio > 0 and has_vtt > 0:
        log(f"\n  Audio + VTT downloaded. Run Whisper next, then alignment.")

    # Save results
    results_path = PROJECT_ROOT / "data" / "audio_comedy" / "expansion_results.json"
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    log(f"\n  Results: {results_path}")


if __name__ == "__main__":
    main()
