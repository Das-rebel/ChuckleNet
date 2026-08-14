#!/usr/bin/env python3
"""
Rebuild aligned_utterances.jsonl from 549K word segments.
Creates sliding-window utterances with proper labels, text, and audio paths.
Target: ~100K utterances (6.7x more than current 15K).

Strategy: 5-second windows with 2.5-second stride, minimum 5 words.
Label = 1 if ANY word in window has label=1.
"""

import json, os, sys, time
from pathlib import Path
from collections import defaultdict

PROJECT = Path(__file__).resolve().parent.parent
SEGMENTS_FILE = PROJECT / "data" / "audio_comedy" / "aligned_segments.jsonl"
OUTPUT_FILE = PROJECT / "data" / "audio_comedy" / "aligned_utterances_v2.jsonl"
AUDIO_DIR = PROJECT / "data" / "audio_comedy" / "audio"

WINDOW_SEC = 5.0
STRIDE_SEC = 2.5
MIN_WORDS = 5
MIN_POSITIVE_WORDS = 1  # Any positive word → utterance is positive


def main():
    print(f"{'='*60}")
    print("Rebuilding aligned_utterances.jsonl from word segments")
    print(f"Window: {WINDOW_SEC}s | Stride: {STRIDE_SEC}s | Min words: {MIN_WORDS}")
    print(f"{'='*60}")

    # Load all word segments
    print("Loading word segments...")
    with open(SEGMENTS_FILE) as f:
        segments = [json.loads(l) for l in f if l.strip()]
    print(f"Loaded {len(segments):,} word segments")

    # Group by video
    video_words = defaultdict(list)
    for s in segments:
        video_words[s["video_id"]].append(s)

    # Sort each video's words by start time
    for vid in video_words:
        video_words[vid].sort(key=lambda w: w["start"])

    # Find audio files for each video
    print("Finding audio files...")
    audio_map = {}
    for mp3 in AUDIO_DIR.rglob("*.mp3"):
        audio_map[mp3.stem] = str(mp3)

    # Build utterances
    print("Building utterances...")
    utterances = []
    uid_counter = 0
    stats = {"total": 0, "positive": 0, "videos_processed": 0, "skipped_empty": 0}

    for vid, words in sorted(video_words.items()):
        if not words:
            continue

        audio_path = audio_map.get(vid, "")
        if not audio_path:
            # Try to get from segments
            audio_path = words[0].get("audio_file", "")

        max_time = words[-1]["end"]
        t = 0.0

        while t + WINDOW_SEC <= max_time:
            # Find words in this window
            window_words = [
                w for w in words if t <= w["start"] and w["end"] <= t + WINDOW_SEC
            ]

            if len(window_words) < MIN_WORDS:
                t += STRIDE_SEC
                stats["skipped_empty"] += 1
                continue

            # Label: 1 if any word is positive
            label = 1 if any(w["label"] == 1 for w in window_words) else 0

            # Text: join words in order
            text = " ".join(w["word"] for w in window_words)

            # Start/end from first/last word
            utt_start = window_words[0]["start"]
            utt_end = window_words[-1]["end"]

            uid_counter += 1
            utterances.append(
                {
                    "utterance_id": f"w{uid_counter:08d}",
                    "video_id": vid,
                    "audio_file": audio_path,
                    "start": round(utt_start, 3),
                    "end": round(utt_end, 3),
                    "text": text,
                    "label_any": label,
                    "label_majority": label,  # Single label from words
                    "num_words": len(window_words),
                    "source": "word_segments_v2",
                }
            )

            stats["total"] += 1
            stats["positive"] += label
            t += STRIDE_SEC

        stats["videos_processed"] += 1

        if stats["videos_processed"] % 10 == 0:
            print(
                f"  [{stats['videos_processed']}/71] {stats['total']:,} utterances "
                f"({100*stats['positive']/max(stats['total'],1):.1f}% positive)"
            )

    # Save
    print(f"\nWriting {stats['total']:,} utterances...")
    with open(OUTPUT_FILE, "w") as f:
        for u in utterances:
            f.write(json.dumps(u, ensure_ascii=False) + "\n")

    # Compare
    old_count = sum(
        1 for _ in open(PROJECT / "data/audio_comedy/aligned_utterances.jsonl")
    )
    improvement = stats["total"] / old_count

    print(f"\n{'='*60}")
    print(f"Done! {stats['total']:,} utterances")
    print(f"Positive: {stats['positive']} ({100*stats['positive']/max(stats['total'],1):.1f}%)")
    print(f"Videos: {stats['videos_processed']}")
    print(f"Old count: {old_count:,} → New: {stats['total']:,} ({improvement:.1f}x)")
    print(f"Output: {OUTPUT_FILE}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
