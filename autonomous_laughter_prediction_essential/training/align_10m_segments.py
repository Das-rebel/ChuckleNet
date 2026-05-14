#!/usr/bin/env python3
"""
Align VTT laughter markers with Whisper word timestamps to create 10M labeled segments.

Usage:
    python training/align_10m_segments.py --lang en --output gdrive:laughter_prediction/aligned/en.jsonl
    python training/align_10m_segments.py --lang zh --output gdrive:laughter_prediction/aligned/zh.jsonl
"""

import json
import os
import re
import argparse
from pathlib import Path
from collections import Counter
from datetime import timedelta

# ── Config ──────────────────────────────────────────────────────────
LAUGHTER_PATTERNS = {
    "en": [
        r"\[laughter\]",
        r"\[laughing\]",
        r"\[applause\]",
        r"\[Applause\]",
        r"\(audience laughing\)",
        r"\(audience laughs\)",
        r"\(audience clapping\)",
        r"\(audience cheering\)",
    ],
    "zh": [
        r"\[笑声\]",
        r"\[笑\]",
        r"\[掌声\]",
        r"\[鼓掌\]",
        r"\(观众笑\)",
        r"\(观众鼓掌\)",
    ],
    "hi-latn": [
        r"\[हंसी\]",
        r"\[ताली\]",
        r"\[हंसत\]",
        r"\[प्रशंसा\]",
        r"\(दर्शक हंसते हैं\)",
        r"\(तालियाँ\)",
    ],
}

WINDOW_BEFORE = 5.0  # seconds before laugh marker to label as laugh
WINDOW_AFTER = 0.5   # seconds after laugh marker
CONTEXT_WORDS = 4    # words of context to include


def parse_vtt_timestamp(ts: str) -> float:
    """Convert VTT timestamp to seconds."""
    # Handle both HH:MM:SS.mmm and MM:SS.mmm
    ts = ts.strip()
    parts = ts.split(":")
    if len(parts) == 3:
        h, m, s = parts
        return int(h) * 3600 + int(m) * 60 + float(s)
    elif len(parts) == 2:
        m, s = parts
        return int(m) * 60 + float(s)
    else:
        return float(parts[0])


def parse_vtt(vtt_path: str, lang: str) -> list:
    """Parse VTT file and extract laughter events with timestamps."""
    if not os.path.exists(vtt_path):
        return []
    
    try:
        with open(vtt_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except:
        return []
    
    patterns = LAUGHTER_PATTERNS.get(lang, LAUGHTER_PATTERNS["en"])
    events = []
    
    # Parse VTT cues
    cues = re.findall(
        r"(\d{2}:\d{2}:\d{2}\.\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}\.\d{3})\s*\n(.*?)(?=\n\n|\Z)",
        content,
        re.DOTALL
    )
    
    for start_ts, end_ts, text in cues:
        text_clean = text.strip().lower()
        
        # Check for laughter markers
        for pattern in patterns:
            if re.search(pattern, text_clean, re.IGNORECASE):
                start = parse_vtt_timestamp(start_ts)
                end = parse_vtt_timestamp(end_ts)
                events.append({
                    "start": start,
                    "end": end,
                    "text": text.strip(),
                    "type": "laughter",
                })
                break
    
    return events


def align_words_with_laughter(words: list, laughter_events: list) -> list:
    """Label each word based on proximity to laughter events."""
    aligned = []
    
    for i, word in enumerate(words):
        word_start = word.get("start", 0)
        word_end = word.get("end", word_start + 0.5)
        
        # Check if word overlaps with or is near any laughter event
        label = 0
        for event in laughter_events:
            # Word is during laughter
            if word_start >= event["start"] and word_end <= event["end"]:
                label = 1
                break
            # Word is within WINDOW_BEFORE seconds before laughter
            if event["start"] - WINDOW_BEFORE <= word_end <= event["start"] + WINDOW_AFTER:
                label = 1
                break
        
        # Get context words
        context_start = max(0, i - CONTEXT_WORDS)
        context_end = min(len(words), i + CONTEXT_WORDS + 1)
        context_words = [w["word"] for w in words[context_start:context_end]]
        context_labels = [aligned[j]["label"] if j < len(aligned) else 0 
                         for j in range(context_start, context_end)]
        
        aligned.append({
            "word": word["word"],
            "start": word_start,
            "end": word_end,
            "duration": word_end - word_start,
            "label": label,
            "context_words": context_words,
            "context_labels": context_labels,
        })
    
    return aligned


def process_video(video_id: str, lang: str, audio_base: str, transcript_base: str, vtt_base: str) -> list:
    """Process single video: load transcript, VTT, align."""
    # Load Whisper transcript
    transcript_path = f"{transcript_base}/{video_id}_transcript.json"
    if not os.path.exists(transcript_path):
        return []
    
    try:
        with open(transcript_path) as f:
            transcript = json.load(f)
    except:
        return []
    
    words = transcript.get("words", [])
    if not words:
        return []
    
    # Load VTT
    vtt_path = f"{vtt_base}/{video_id}.en.vtt"
    if lang == "zh":
        vtt_path = f"{vtt_base}/{video_id}.zh.vtt"
    elif lang == "hi-latn":
        vtt_path = f"{vtt_base}/{video_id}.hi.vtt"
    
    laughter_events = parse_vtt(vtt_path, lang)
    
    # Align
    aligned = align_words_with_laughter(words, laughter_events)
    
    # Add metadata
    for seg in aligned:
        seg["video_id"] = video_id
        seg["language"] = lang
        seg["audio_file"] = f"{audio_base}/{video_id}.mp3"
    
    return aligned


def main():
    parser = argparse.ArgumentParser(description="Align VTT laughter markers with Whisper timestamps")
    parser.add_argument("--lang", choices=["en", "zh", "hi-latn"], required=True)
    parser.add_argument("--audio-dir", required=True, help="Base directory with audio files")
    parser.add_argument("--transcript-dir", required=True, help="Base directory with Whisper transcripts")
    parser.add_argument("--vtt-dir", required=True, help="Base directory with VTT subtitles")
    parser.add_argument("--output", required=True, help="Output JSONL file path")
    parser.add_argument("--batch-size", type=int, default=100, help="Progress report every N videos")
    args = parser.parse_args()
    
    print(f"Aligning {args.lang} segments...")
    print(f"Audio: {args.audio_dir}")
    print(f"Transcripts: {args.transcript_dir}")
    print(f"VTT: {args.vtt_dir}")
    print(f"Output: {args.output}")
    
    # Find all transcript files
    transcript_files = list(Path(args.transcript_dir).glob("*_transcript.json"))
    print(f"\nFound {len(transcript_files)} transcript files")
    
    # Process each video
    total_segments = 0
    total_laughs = 0
    stats = Counter()
    
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    with open(args.output, "w") as out_f:
        for i, transcript_path in enumerate(transcript_files):
            video_id = transcript_path.stem.replace("_transcript", "")
            
            segments = process_video(
                video_id,
                args.lang,
                args.audio_dir,
                args.transcript_dir,
                args.vtt_dir
            )
            
            if segments:
                stats["ok"] += 1
                total_segments += len(segments)
                total_laughs += sum(s["label"] for s in segments)
                
                # Write to JSONL
                for seg in segments:
                    out_f.write(json.dumps(seg) + "\n")
            else:
                stats["failed"] += 1
            
            # Progress report
            if (i + 1) % args.batch_size == 0:
                print(f"  {i+1}/{len(transcript_files)} videos | "
                      f"{total_segments:,} segments | "
                      f"{total_laughs:,} laughs ({100*total_laughs/total_segments:.1f}%)")
    
    print(f"\n{'='*60}")
    print(f"Alignment complete!")
    print(f"Videos processed: {len(transcript_files)}")
    print(f"Success: {stats['ok']}")
    print(f"Failed: {stats['failed']}")
    print(f"Total segments: {total_segments:,}")
    print(f"Laugh labels: {total_laughs:,} ({100*total_laughs/total_segments:.1f}%)")
    print(f"Output: {args.output}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
