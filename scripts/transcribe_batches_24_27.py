#!/usr/bin/env python3
"""Transcribe audio files from batches 24-27 using faster-whisper tiny.en model.

For each mp3 in data/audio_comedy/audio/batch{N}/ that doesn't have a
corresponding .json in data/audio_comedy/whisper/batch{N}/, run
transcription with word-level timestamps and save the result.
"""

import json
import os
import sys
import time
import traceback

from faster_whisper import WhisperModel

BASE_DIR = "/Users/Subho/autonomous_laughter_prediction"
AUDIO_DIR = os.path.join(BASE_DIR, "data/audio_comedy/audio")
WHISPER_DIR = os.path.join(BASE_DIR, "data/audio_comedy/whisper")
BATCHES = [24, 25, 26, 27]
SKIP_VIDEO_IDS = {"{VIDEO_ID}"}  # placeholder filenames to skip


def get_pending_files():
    """Return list of (audio_path, output_path) for files needing transcription."""
    pending = []
    for batch_num in BATCHES:
        audio_batch = os.path.join(AUDIO_DIR, f"batch{batch_num}")
        whisper_batch = os.path.join(WHISPER_DIR, f"batch{batch_num}")
        os.makedirs(whisper_batch, exist_ok=True)

        if not os.path.isdir(audio_batch):
            print(f"  [SKIP] {audio_batch} does not exist")
            continue

        for fname in sorted(os.listdir(audio_batch)):
            if not fname.endswith(".mp3"):
                continue
            video_id = fname[:-4]  # strip .mp3
            if video_id in SKIP_VIDEO_IDS:
                print(f"  [SKIP] {fname} is a placeholder")
                continue

            audio_path = os.path.join(audio_batch, fname)
            output_path = os.path.join(whisper_batch, f"{video_id}.json")

            if os.path.exists(output_path):
                # Check if it's a valid JSON with content
                try:
                    with open(output_path) as f:
                        data = json.load(f)
                    if data.get("segments"):
                        print(f"  [DONE] {fname} already transcribed")
                        continue
                except (json.JSONDecodeError, IOError):
                    pass  # Re-transcribe corrupt files

            pending.append((audio_path, output_path, batch_num, video_id))

    return pending


def transcribe_file(model, audio_path, output_path):
    """Transcribe a single audio file and save result as JSON."""
    start = time.time()
    
    segments, info = model.transcribe(audio_path, word_timestamps=True)
    
    # Force iteration to get all segments
    segment_list = list(segments)
    
    result = {
        "language": info.language,
        "language_probability": info.language_probability,
        "duration": info.duration,
        "text": " ".join([seg.text.strip() for seg in segment_list]),
        "segments": [
            {
                "id": i,
                "start": round(seg.start, 3),
                "end": round(seg.end, 3),
                "text": seg.text.strip(),
                "words": [
                    {
                        "word": w.word.strip(),
                        "start": round(w.start, 3),
                        "end": round(w.end, 3),
                        "probability": round(w.probability, 4),
                    }
                    for w in (seg.words or [])
                ],
            }
            for i, seg in enumerate(segment_list)
        ],
    }
    
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)
    
    elapsed = time.time() - start
    duration_min = info.duration / 60.0
    speed = duration_min / (elapsed / 60.0) if elapsed > 0 else 0
    n_words = sum(len(s.get("words", [])) for s in result["segments"])
    n_segs = len(result["segments"])
    
    return {
        "duration_s": round(info.duration, 1),
        "elapsed_s": round(elapsed, 1),
        "speed_x": round(speed, 1),
        "n_segments": n_segs,
        "n_words": n_words,
        "language": info.language,
    }


def main():
    print("=" * 70)
    print("FASTER-WHISPER TRANSCRIPTION: batches 24-27")
    print("=" * 70)
    
    # Load model once
    print("\nLoading tiny.en model (CPU, int8)...")
    t0 = time.time()
    model = WhisperModel("tiny.en", device="cpu", compute_type="int8")
    print(f"Model loaded in {time.time()-t0:.1f}s\n")
    
    # Get pending files
    pending = get_pending_files()
    print(f"\nFound {len(pending)} files to transcribe\n")
    
    if not pending:
        print("Nothing to do!")
        return
    
    # Track results
    completed = []
    errors = []
    total_start = time.time()
    
    for idx, (audio_path, output_path, batch_num, video_id) in enumerate(pending, 1):
        remaining = len(pending) - idx + 1
        est_time = remaining * 45  # rough estimate: 45s per file
        print(f"[{idx}/{len(pending)}] batch{batch_num}/{video_id} "
              f"(~{est_time//60}m remaining)")
        
        try:
            stats = transcribe_file(model, audio_path, output_path)
            completed.append((batch_num, video_id, stats))
            print(f"  ✓ {stats['duration_s']}s audio → {stats['elapsed_s']}s "
                  f"({stats['speed_x']}x realtime, {stats['n_words']} words, "
                  f"{stats['n_segments']} segments, lang={stats['language']})")
        except Exception as e:
            errors.append((batch_num, video_id, str(e)))
            print(f"  ✗ ERROR: {e}")
            traceback.print_exc()
    
    total_elapsed = time.time() - total_start
    
    # Summary
    print("\n" + "=" * 70)
    print("TRANSCRIPTION COMPLETE")
    print("=" * 70)
    print(f"  Completed: {len(completed)}/{len(pending)}")
    print(f"  Errors:    {len(errors)}")
    print(f"  Total time: {total_elapsed:.0f}s ({total_elapsed/60:.1f}min)")
    
    if completed:
        total_audio = sum(s["duration_s"] for _, _, s in completed)
        total_words = sum(s["n_words"] for _, _, s in completed)
        print(f"  Total audio transcribed: {total_audio:.0f}s ({total_audio/60:.1f}min)")
        print(f"  Total words: {total_words}")
        avg_speed = total_audio / total_elapsed if total_elapsed > 0 else 0
        print(f"  Average speed: {avg_speed:.1f}x realtime")
    
    if errors:
        print(f"\n  ERROR DETAILS:")
        for batch_num, video_id, err in errors:
            print(f"    batch{batch_num}/{video_id}: {err}")
    
    # Per-batch summary
    print(f"\n  PER-BATCH BREAKDOWN:")
    for batch_num in BATCHES:
        batch_completed = [s for b, _, s in completed if b == batch_num]
        batch_errors = [(v, e) for b, v, e in errors if b == batch_num]
        if batch_completed:
            audio = sum(s["duration_s"] for s in batch_completed)
            words = sum(s["n_words"] for s in batch_completed)
            print(f"    batch{batch_num}: {len(batch_completed)} files, "
                  f"{audio/60:.1f}min audio, {words} words")
        if batch_errors:
            print(f"    batch{batch_num}: {len(batch_errors)} errors")


if __name__ == "__main__":
    main()