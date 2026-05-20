#!/usr/bin/env python3
"""
Align Whisper word-level timestamps with laugh labels from YouTube VTT subtitles.

Pipeline:
1. Download VTT subtitles for each video using yt-dlp
2. Parse [laughter]/[applause] markers with timestamps
3. Align laughter timestamps with Whisper word timestamps
4. Output aligned segments: {word, start, end, label, audio_file}

Output: data/audio_comedy/aligned_segments.jsonl
"""

import os
import sys
import json
import re
import subprocess
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TRANSCRIPT_DIR = PROJECT_ROOT / "data" / "audio_comedy" / "transcripts"
AUDIO_DIR = PROJECT_ROOT / "data" / "audio_comedy" / "audio"
OUTPUT_DIR = PROJECT_ROOT / "data" / "audio_comedy"
VTT_DIR = OUTPUT_DIR / "vtt_subtitles"

# Video IDs we have both audio AND Whisper transcripts for
TARGET_VIDEOS = {
    "5S5iZZEtTkg": {"comedian": "john_mulaney", "title": "New in Town"},
    "anUJnsICCXo": {"comedian": "john_mulaney", "title": "25 minutes straight"},
    "QxxLmgleW1s": {"comedian": "ali_wong", "title": "15 Minutes"},
    "seW0_VSzuHg": {"comedian": "ali_wong", "title": "Divorce Reaction"},
    "wY5-8kvMEh0": {"comedian": "ali_wong", "title": "Best of Ali Wong"},
    "0qGd6KXh_ig": {"comedian": "dave_chappelle", "title": "Killin Them Softly"},
}

LAUGHTER_MARKERS = [
    # Bracketed markers
    "[laughter]", "[laugh]", "[Laugh]", "[LAUGHTER]",
    "[applause]", "[Applause]", "[APPLAUSE]",
    "[praise]", "[प्रशंसा]",
    "[Audience laughter]", "[audience laughter]",
    # Parenthesized markers
    "(laughter)", "(laugh)", "(applause)",
    "(audience laughs)", "(audience applause)",
    "(audience laughter)",
    "(audience laughing)",
    "(audience clapping)",
    "(audience clapping and cheering)",
    "(audience cheering)",
    # Case-insensitive matching handled in extract function
]


def log(msg):
    print(msg, flush=True)


def download_vtt(video_id, output_dir):
    """Download VTT subtitles for a YouTube video using yt-dlp."""
    vtt_file = output_dir / f"{video_id}.vtt"
    if vtt_file.exists():
        log(f"  VTT already exists: {vtt_file}")
        return vtt_file

    url = f"https://www.youtube.com/watch?v={video_id}"
    log(f"  Downloading VTT for {video_id}...")

    try:
        # Try with cookies for auth
        result = subprocess.run(
            ["yt-dlp", "--write-auto-sub", "--sub-lang", "en", "--sub-format", "vtt",
             "--skip-download", "-o", str(output_dir / video_id), url],
            capture_output=True, text=True, timeout=60
        )
        # Check if VTT was downloaded
        possible_vtts = list(output_dir.glob(f"{video_id}*.vtt"))
        if possible_vtts:
            # Move to canonical name
            src = possible_vtts[0]
            if src != vtt_file:
                src.rename(vtt_file)
            log(f"  Downloaded: {vtt_file}")
            return vtt_file
        
        # Try manual subtitles
        result = subprocess.run(
            ["yt-dlp", "--write-sub", "--sub-lang", "en", "--sub-format", "vtt",
             "--skip-download", "-o", str(output_dir / video_id), url],
            capture_output=True, text=True, timeout=60
        )
        possible_vtts = list(output_dir.glob(f"{video_id}*.vtt"))
        if possible_vtts:
            src = possible_vtts[0]
            if src != vtt_file:
                src.rename(vtt_file)
            log(f"  Downloaded (manual): {vtt_file}")
            return vtt_file

        log(f"  WARNING: No VTT found for {video_id}")
        log(f"  yt-dlp stderr: {result.stderr[:200]}")
        return None
    except Exception as e:
        log(f"  ERROR downloading VTT for {video_id}: {e}")
        return None


def parse_vtt_timestamps(vtt_path):
    """Parse VTT file and return segments with timestamps and text."""
    if not vtt_path or not vtt_path.exists():
        return []

    with open(vtt_path, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()

    segments = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        # Match timestamp line: 00:00:01.000 --> 00:00:04.000 [optional positioning]
        ts_match = re.match(
            r'(\d{2}:\d{2}:\d{2}[.,]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[.,]\d{3})',
            line
        )
        if ts_match:
            start = parse_timestamp(ts_match.group(1))
            end = parse_timestamp(ts_match.group(2))
            # Collect text lines until next blank line or timestamp
            text_lines = []
            i += 1
            while i < len(lines):
                next_line = lines[i].strip()
                if not next_line:  # blank line = end of block
                    break
                if re.match(r'\d{2}:\d{2}:\d{2}[.,]\d{3}\s*-->', next_line):
                    break  # next timestamp
                text_lines.append(next_line)
                i += 1
            text = ' '.join(text_lines)
            # Remove VTT positioning/styling tags
            text = re.sub(r'<[^>]+>', '', text)
            text = text.strip()
            if text:
                segments.append({"start": start, "end": end, "text": text})
        else:
            i += 1

    return segments


def parse_timestamp(ts_str):
    """Convert VTT timestamp (HH:MM:SS.mmm) to seconds."""
    parts = ts_str.replace(',', '.').split(':')
    h, m = int(parts[0]), int(parts[1])
    s = float(parts[2])
    return h * 3600 + m * 60 + s


def extract_laughter_timestamps(vtt_segments):
    """Extract timestamps of laughter markers from VTT segments."""
    laughter_events = []
    marker_lower = [m.lower() for m in LAUGHTER_MARKERS]
    for seg in vtt_segments:
        text_lower = seg["text"].lower()
        for marker in marker_lower:
            if marker in text_lower:
                laughter_events.append({
                    "start": seg["start"],
                    "end": seg["end"],
                    "marker": marker,
                    "text": seg["text"],
                })
                break  # One marker per segment is enough
    return laughter_events


def load_whisper_words(transcript_path):
    """Load all word-level timestamps from a Whisper transcript."""
    with open(transcript_path) as f:
        data = json.load(f)

    words = []
    for seg in data.get("segments", []):
        for w in seg.get("words", []):
            words.append({
                "word": w["word"].strip(),
                "start": w["start"],
                "end": w["end"],
                "probability": w.get("probability", 0.0),
            })
    return words


def find_audio_file(video_id, comedian):
    """Find the audio file for a given video ID."""
    comedian_dir = AUDIO_DIR / comedian
    if comedian_dir.exists():
        for ext in ["*.mp3", "*.wav", "*.webm"]:
            matches = list(comedian_dir.glob(f"{video_id}{ext[1:]}"))
            if matches:
                return str(matches[0])
    # Check top level
    for ext in ["*.mp3", "*.wav"]:
        matches = list(AUDIO_DIR.glob(f"{video_id}{ext[1:]}"))
        if matches:
            return str(matches[0])
    return None


def align_words_to_laughter(whisper_words, laughter_events, window_sec=5.0):
    """
    Align Whisper word timestamps to laughter events.
    
    Strategy: A word is labeled as "laugh" if:
    1. A laughter event starts within `window_sec` seconds AFTER the word ends
       (comedian says punchline → audience laughs), OR
    2. The word falls WITHIN a laughter event interval (word is surrounded by laughter)
    
    For the pre-laugh trigger word, we extend the label to include a small 
    context window of preceding words (the setup/punchline that caused the laugh).
    """
    if not laughter_events:
        return []

    # Merge overlapping laughter events into intervals
    intervals = []
    for e in sorted(laughter_events, key=lambda x: x["start"]):
        if intervals and e["start"] <= intervals[-1][1] + 1.0:
            intervals[-1] = (intervals[-1][0], max(intervals[-1][1], e["end"]))
        else:
            intervals.append((e["start"], e["end"]))

    # For each word, check if it triggers or is within a laughter interval
    aligned = []
    for w in whisper_words:
        word_start = w["start"]
        word_end = w["end"]
        label = 0
        closest_laugh = None
        closest_dist = float("inf")

        for laugh_start, laugh_end in intervals:
            # Case 1: Word ends just before laughter starts (the trigger word)
            delay = laugh_start - word_end
            if 0 <= delay <= window_sec and delay < closest_dist:
                closest_dist = delay
                closest_laugh = laugh_start
                label = 1

            # Case 2: Word is within the laughter interval
            if word_start >= laugh_start - 0.5 and word_end <= laugh_end + 0.5:
                if closest_laugh is None:
                    closest_laugh = laugh_start
                    closest_dist = word_start - laugh_start
                label = 1

        aligned.append({
            "word": w["word"],
            "start": w["start"],
            "end": w["end"],
            "label": label,
            "closest_laugh": closest_laugh,
            "laugh_delay": round(closest_dist, 3) if closest_laugh is not None else None,
        })

    # Post-process: expand labels to include the ~2 words before each trigger
    # (the punchline usually spans 2-3 words)
    labels = [a["label"] for a in aligned]
    expanded = labels.copy()
    for i, a in enumerate(aligned):
        if a["label"] == 1 and a.get("laugh_delay") is not None and a["laugh_delay"] >= 0:
            # This is a trigger word - expand backwards by 2 words
            for j in range(max(0, i - 2), i):
                if labels[j] == 0:  # Don't overwrite existing labels
                    expanded[j] = 1

    for i in range(len(aligned)):
        aligned[i]["label"] = expanded[i]

    return aligned


def extract_segments_for_audio(aligned_words, audio_file, video_id, comedian):
    """
    Create audio segment records for training.
    Each record specifies: word, start, end, label, audio_file
    plus context window (surrounding words).
    """
    segments = []
    window = 3  # context words on each side

    for i, w in enumerate(aligned_words):
        # Context: surrounding words
        ctx_start = max(0, i - window)
        ctx_end = min(len(aligned_words), i + window + 1)
        context_words = [aligned_words[j]["word"] for j in range(ctx_start, ctx_end)]
        context_labels = [aligned_words[j]["label"] for j in range(ctx_start, ctx_end)]

        segments.append({
            "video_id": video_id,
            "comedian": comedian,
            "audio_file": audio_file,
            "word_index": i,
            "word": w["word"],
            "start": round(w["start"], 3),
            "end": round(w["end"], 3),
            "duration": round(w["end"] - w["start"], 3),
            "label": w["label"],
            "context_words": context_words,
            "context_labels": context_labels,
        })

    return segments


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Align Whisper timestamps with VTT laugh labels")
    parser.add_argument("--window", type=float, default=2.0, help="Seconds after word to look for laughter")
    parser.add_argument("--skip-download", action="store_true", help="Skip VTT download step")
    parser.add_argument("--video-id", type=str, default=None, help="Process only this video")
    args = parser.parse_args()

    VTT_DIR.mkdir(parents=True, exist_ok=True)

    log("=" * 60)
    log("WHISPER ↔ VTT LAUGHTER ALIGNMENT")
    log("=" * 60)

    # Determine which videos to process
    if args.video_id:
        targets = {args.video_id: TARGET_VIDEOS.get(args.video_id, {})}
    else:
        targets = TARGET_VIDEOS

    all_aligned = []
    stats = {}

    for video_id, info in targets.items():
        comedian = info.get("comedian", "unknown")
        title = info.get("title", "?")
        log(f"\n{'─' * 50}")
        log(f"Video: {video_id} ({comedian}) - {title}")

        # 1. Download VTT
        vtt_path = None
        if not args.skip_download:
            vtt_path = download_vtt(video_id, VTT_DIR)

        if not vtt_path:
            # Check if already downloaded
            existing = list(VTT_DIR.glob(f"{video_id}*.vtt"))
            if existing:
                vtt_path = existing[0]
                log(f"  Using existing: {vtt_path}")

        # 2. Find Whisper transcript
        transcript_path = None
        for root, dirs, files in os.walk(TRANSCRIPT_DIR):
            for f in files:
                if video_id in f and f.endswith(".json"):
                    transcript_path = Path(root) / f
                    break

        if not transcript_path:
            log(f"  WARNING: No Whisper transcript for {video_id}, skipping")
            continue

        # 3. Find audio file
        audio_file = find_audio_file(video_id, comedian)
        if audio_file:
            log(f"  Audio: {audio_file}")
        else:
            log(f"  WARNING: No audio file for {video_id}")

        # 4. Load Whisper words
        whisper_words = load_whisper_words(transcript_path)
        log(f"  Whisper words: {len(whisper_words)}")

        # 5. Parse VTT for laughter
        laugh_events = []
        if vtt_path:
            vtt_segments = parse_vtt_timestamps(vtt_path)
            laugh_events = extract_laughter_timestamps(vtt_segments)
            log(f"  VTT segments: {len(vtt_segments)}, laughter events: {len(laugh_events)}")
            
            if not laugh_events:
                log(f"  WARNING: No [laughter] markers found in VTT for {video_id}")
                log(f"  VTT first 5 segments:")
                for seg in vtt_segments[:5]:
                    log(f"    [{seg['start']:.1f}-{seg['end']:.1f}] {seg['text'][:80]}")
        else:
            log(f"  WARNING: No VTT file for {video_id}")

        # 6. Align
        if laugh_events:
            aligned = align_words_to_laughter(whisper_words, laugh_events, window_sec=args.window)
            pos_count = sum(1 for w in aligned if w["label"] == 1)
            log(f"  Aligned: {len(aligned)} words, {pos_count} positive ({pos_count/len(aligned):.1%})")

            # 7. Create segment records
            if audio_file:
                segments = extract_segments_for_audio(aligned, audio_file, video_id, comedian)
                all_aligned.extend(segments)

            stats[video_id] = {
                "comedian": comedian,
                "whisper_words": len(whisper_words),
                "laugh_events": len(laugh_events),
                "aligned_words": len(aligned),
                "positive_words": pos_count,
                "has_audio": audio_file is not None,
                "vtt_path": str(vtt_path) if vtt_path else None,
            }
        else:
            log(f"  SKIPPING alignment (no laughter events)")
            stats[video_id] = {
                "comedian": comedian,
                "whisper_words": len(whisper_words),
                "laugh_events": 0,
                "aligned_words": 0,
                "positive_words": 0,
                "has_audio": audio_file is not None,
                "vtt_path": str(vtt_path) if vtt_path else None,
            }

    # Save results
    log(f"\n{'=' * 60}")
    log("ALIGNMENT SUMMARY")
    log(f"{'=' * 60}")

    total_words = sum(s.get("aligned_words", 0) for s in stats.values())
    total_pos = sum(s.get("positive_words", 0) for s in stats.values())
    total_segments = len(all_aligned)

    for vid, s in stats.items():
        log(f"  {vid} ({s['comedian']}): {s['aligned_words']} words, {s['positive_words']} positive, audio={'✓' if s['has_audio'] else '✗'}")

    log(f"\n  Total aligned words: {total_words}")
    log(f"  Total positive: {total_pos} ({total_pos/max(total_words,1):.1%})")
    log(f"  Total audio segments: {total_segments}")

    # Save aligned segments
    output_path = OUTPUT_DIR / "aligned_segments.jsonl"
    with open(output_path, "w") as f:
        for seg in all_aligned:
            f.write(json.dumps(seg, ensure_ascii=False) + "\n")
    log(f"\n  Saved: {output_path} ({total_segments} segments)")

    # Save stats
    stats_path = OUTPUT_DIR / "alignment_stats.json"
    with open(stats_path, "w") as f:
        json.dump({"videos": stats, "totals": {
            "words": total_words, "positive": total_pos, "segments": total_segments
        }, "window_sec": args.window}, f, indent=2)
    log(f"  Stats: {stats_path}")

    if total_segments >= 10000:
        log(f"\n  ✓ TARGET MET: {total_segments} >= 10,000 audio segments")
    else:
        log(f"\n  ⚠ Below target: {total_segments} / 10,000 audio segments")
        log(f"  Need {max(0, 10000 - total_segments)} more segments")


if __name__ == "__main__":
    main()
