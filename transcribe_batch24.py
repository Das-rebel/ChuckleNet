#!/usr/bin/env python3
"""Transcribe batch24 audio files using faster-whisper tiny.en model."""

import os
import json
import time
from faster_whisper import WhisperModel

AUDIO_DIR = "data/audio_comedy/audio/batch24"
WHISPER_DIR = "data/audio_comedy/whisper/batch24"
MAX_FILES = 19

os.makedirs(WHISPER_DIR, exist_ok=True)

# Find untranscribed files
audio_files = sorted([f for f in os.listdir(AUDIO_DIR) if f.endswith('.mp3')])
untranscribed = []
for f in audio_files:
    video_id = f.replace('.mp3', '')
    json_path = os.path.join(WHISPER_DIR, f"{video_id}.json")
    if not os.path.exists(json_path):
        untranscribed.append(f)

print(f"Total audio files: {len(audio_files)}")
print(f"Already transcribed: {len(audio_files) - len(untranscribed)}")
print(f"To transcribe: {len(untranscribed)} (max {MAX_FILES})")

to_process = untranscribed[:MAX_FILES]

print(f"\nLoading tiny.en model...")
model = WhisperModel('tiny.en', device='cpu', compute_type='int8')

completed = 0
failed = []

for i, filename in enumerate(to_process):
    video_id = filename.replace('.mp3', '')
    audio_path = os.path.join(AUDIO_DIR, filename)
    json_path = os.path.join(WHISPER_DIR, f"{video_id}.json")

    print(f"\n[{i+1}/{len(to_process)}] Transcribing {video_id}...")
    start_time = time.time()

    try:
        segments, info = model.transcribe(audio_path, word_timestamps=True)

        segments_list = []
        for seg in segments:
            seg_data = {
                "start": round(seg.start, 3),
                "end": round(seg.end, 3),
                "text": seg.text,
                "words": [
                    {
                        "word": w.word,
                        "start": round(w.start, 3),
                        "end": round(w.end, 3),
                    }
                    for w in (seg.words or [])
                ]
            }
            segments_list.append(seg_data)

        result = {"segments": segments_list}

        with open(json_path, 'w') as f:
            json.dump(result, f, indent=2)

        elapsed = time.time() - start_time
        print(f"  ✓ Done in {elapsed:.1f}s — {len(segments_list)} segments, {sum(len(s['words']) for s in segments_list)} words")
        completed += 1

    except Exception as e:
        elapsed = time.time() - start_time
        print(f"  ✗ FAILED in {elapsed:.1f}s: {e}")
        failed.append((video_id, str(e)))

print(f"\n{'='*60}")
print(f"RESULTS: {completed}/{len(to_process)} completed successfully")
if failed:
    print(f"Failed: {failed}")