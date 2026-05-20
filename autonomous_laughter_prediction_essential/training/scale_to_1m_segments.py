#!/usr/bin/env python3
"""
Scale audio segments to 1M (333K per language: en, zh, hi-latn).
Pipeline: search → download audio → download VTT → Whisper → align → extract clips

Target: 1M segments, 10%+ positive rate
Languages: English (en), Chinese (zh), Hindi (hi-latn)
"""

import os
import sys
import json
import subprocess
import time
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path(__file__).resolve().parent.parent
AUDIO_DIR = PROJECT_ROOT / "data" / "audio_comedy"
VTT_DIR = AUDIO_DIR / "vtt_subtitles"
TRANSCRIPT_DIR = AUDIO_DIR / "transcripts"
ALIGNED_FILE = AUDIO_DIR / "aligned_segments.jsonl"
CLIPS_DIR = AUDIO_DIR / "extracted_clips"
STATS_FILE = AUDIO_DIR / "scale_stats.json"

os.environ["PATH"] = f"{os.path.expanduser('~/.deno/bin')}:{os.environ.get('PATH', '')}"

# ─── Video Candidates per Language ─────────────────────────────────────────

CANDIDATES = {
    "en": [
        # Already have 50K en clips
        # Add more high-laugh-density compilations
        {"id": "UvANWG6cQi8", "title": "Best Of Stand-Up", "comedian": "downloaded", "done": True},
        {"id": "OLGrx-m-0iA", "title": "2hr Killer Comedy", "comedian": "downloaded", "done": True},
        {"id": "GxqAHM79xs8", "title": "Matt Rife Best Of", "comedian": "downloaded", "done": True},
        {"id": "fDANtIrT3T8", "title": "30 Viral Jokes", "comedian": "downloaded", "done": True},
        {"id": "zKUpf1Vx0vs", "title": "Shane Gillis", "comedian": "downloaded", "done": True},
        # New candidates - search results with known laugh markers
        {"id": "4UQTaw6yXa4", "title": "Ricky Gervais 25min", "comedian": "downloaded"},
        {"id": "k6WNXMLTB5o", "title": "60 Jokes 60min", "comedian": "downloaded"},
        {"id": "5mvq4yvbw-s", "title": "32 Viral Jokes Vol2", "comedian": "downloaded"},
        {"id": "mDjDBWukuCk", "title": "Comedy Roadshow", "comedian": "downloaded"},
        {"id": "OLGrx-m-0iA", "title": "2hr Killer", "comedian": "downloaded"},
    ],
    "zh": [
        # Chinese comedy - StandUp4AI has 70h of Chinese
        # Need to get audio + VTT for StandUp4AI Chinese videos
        {"id": "standup4ai_zh", "title": "StandUp4AI Chinese", "comedian": "standup4ai"},
    ],
    "hi-latn": [
        # Hindi/Hinglish - Zakir Khan + others from existing collection
        # Zakir Khan: kWj8DQ5GTxM (has audio, needs Whisper + VTT)
        {"id": "kWj8DQ5GTxM", "title": "Zakir Khan", "comedian": "zakir_khan"},
        # Also search for more Hindi comedy
        {"id": "hindi_comedy_search", "title": "Hindi Search", "comedian": "hindi"},
    ],
}


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def run_cmd(cmd, timeout=120):
    env = os.environ.copy()
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env)


def search_videos(query, n=10):
    """Search YouTube for comedy videos."""
    result = run_cmd([
        "yt-dlp", "--flat-playlist", "--print", "%(id)s %(title)s",
        f"ytsearch{n}:{query}"
    ], timeout=30)
    videos = []
    for line in result.stdout.strip().split("\n"):
        if line.strip():
            parts = line.split(" ", 1)
            if len(parts) == 2:
                vid, title = parts
                videos.append({"id": vid, "title": title[:60]})
    return videos


def check_vtt_laugh_density(video_id):
    """Download VTT and count laugh markers."""
    vtt_path = VTT_DIR / f"{video_id}.vtt"
    if not vtt_path.exists():
        result = run_cmd([
            "yt-dlp", "--write-auto-sub", "--sub-lang", "en-US",
            "--sub-format", "vtt", "--skip-download",
            "-o", str(VTT_DIR / video_id),
            f"https://www.youtube.com/watch?v={video_id}"
        ], timeout=30)
        # Find downloaded
        matches = list(VTT_DIR.glob(f"{video_id}*.vtt"))
        if matches:
            vtt_path = matches[0]

    if not vtt_path.exists():
        return 0

    with open(vtt_path, encoding="utf-8", errors="replace") as f:
        content = f.read().lower()

    laugh_count = content.count("laughter") + content.count("applause") + content.count("laughing")
    return laugh_count


def download_audio(video_id, comedian_dir):
    """Download MP3 audio."""
    out_dir = AUDIO_DIR / comedian_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    # Check existing
    for ext in ["mp3", "wav", "webm"]:
        existing = out_dir / f"{video_id}.{ext}"
        if existing.exists():
            return existing

    result = run_cmd([
        "yt-dlp", "-x", "--audio-format", "mp3", "--audio-quality", "5",
        "-o", str(out_dir / f"%(id)s.%(ext)s"),
        f"https://www.youtube.com/watch?v={video_id}"
    ], timeout=300)

    # Find downloaded
    for ext in ["mp3", "wav", "webm"]:
        matches = list(out_dir.glob(f"{video_id}.{ext}"))
        if matches:
            return matches[0]
    return None


def run_whisper(audio_path, video_id, comedian="unknown"):
    """Run faster-whisper for word timestamps."""
    from faster_whisper import WhisperModel

    output = TRANSCRIPT_DIR / comedian / f"{video_id}_transcript.json"
    if output.exists():
        return output

    try:
        model = WhisperModel("tiny", device="cpu", compute_type="int8")
        segments, info = model.transcribe(str(audio_path), word_timestamps=True, language="en")

        seg_list = list(segments)
        word_count = sum(len(s.words) for s in seg_list)

        transcript = {
            "video_id": video_id,
            "title": "",
            "comedian": comedian,
            "language": "en",
            "segments": [
                {
                    "id": i, "seek": 0, "start": s.start, "end": s.end,
                    "text": s.text, "tokens": [], "temperature": 0.0,
                    "avg_logprob": getattr(s, "avg_logprob", 0),
                    "compression_ratio": getattr(s, "compression_ratio", 0),
                    "no_speech_prob": getattr(s, "no_speech_prob", 0),
                    "words": [
                        {"word": w.word, "start": w.start, "end": w.end, "probability": w.probability}
                        for w in s.words
                    ]
                }
                for i, s in enumerate(seg_list)
            ],
            "words": []
        }

        TRANSCRIPT_DIR.mkdir(parents=True, exist_ok=True)
        with open(output, "w") as f:
            json.dump(transcript, f, indent=2, ensure_ascii=False)

        log(f"  Whisper: {info.duration:.0f}s → {word_count} words")
        return output
    except Exception as e:
        log(f"  Whisper error: {e}")
        return None


def parse_vtt(vtt_path):
    """Parse VTT into segments with text."""
    import re
    segments = []
    with open(vtt_path, encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        ts_match = re.match(r'(\d{2}:\d{2}:\d{2}[.,]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[.,]\d{3})', line)
        if ts_match:
            start = parse_ts(ts_match.group(1))
            end = parse_ts(ts_match.group(2))
            text_lines = []
            i += 1
            while i < len(lines) and lines[i].strip():
                nxt = lines[i].strip()
                if re.match(r'\d{2}:\d{2}:\d{2}', nxt):
                    break
                text_lines.append(re.sub(r'<[^>]+>', '', nxt))
                i += 1
            text = " ".join(text_lines).strip()
            if text:
                segments.append({"start": start, "end": end, "text": text})
        else:
            i += 1
    return segments


def parse_ts(s):
    """Parse VTT timestamp to seconds."""
    s = s.replace(",", ".")
    parts = s.split(":")
    return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])


def extract_laugh_events(vtt_segments):
    """Extract laughter events from VTT segments."""
    events = []
    lower_markers = ["laughter", "applause", "laughing", "clapping", "cheering"]
    for seg in vtt_segments:
        text_lower = seg["text"].lower()
        for marker in lower_markers:
            if marker in text_lower:
                events.append({"start": seg["start"], "end": seg["end"], "text": seg["text"]})
                break
    return events


def align_and_save(video_id, comedian):
    """Run alignment and save segments."""
    # Find VTT
    vtt_path = None
    for p in VTT_DIR.glob(f"{video_id}*.vtt"):
        vtt_path = p; break

    # Find transcript
    transcript_path = None
    for root, dirs, files in os.walk(TRANSCRIPT_DIR):
        for f in files:
            if video_id in f and f.endswith("_transcript.json"):
                transcript_path = Path(root) / f; break

    if not vtt_path or not transcript_path:
        return 0

    # Load words
    with open(transcript_path) as f:
        data = json.load(f)
    words = []
    for seg in data.get("segments", []):
        for w in seg.get("words", []):
            words.append({"word": w["word"], "start": w["start"], "end": w["end"]})

    # Parse VTT and extract laughs
    vtt_segs = parse_vtt(vtt_path)
    laughs = extract_laugh_events(vtt_segs)

    if not laughs:
        return 0

    # Find audio file
    audio_file = None
    for ext in ["mp3", "wav", "webm"]:
        p = AUDIO_DIR / comedian / f"{video_id}.{ext}"
        if p.exists():
            audio_file = str(p); break

    # Align with 5s window
    laugh_starts = sorted([l["start"] for l in laughs])
    intervals = []
    for l in sorted(laughs, key=lambda x: x["start"]):
        if intervals and l["start"] <= intervals[-1][1] + 1.0:
            intervals[-1] = (intervals[-1][0], max(intervals[-1][1], l["end"]))
        else:
            intervals.append((l["start"], l["end"]))

    aligned = []
    for w in words:
        label = 0
        for ls, le in intervals:
            if ls - 0.5 <= w["start"] <= le + 0.5:
                label = 1; break
            if 0 <= ls - w["end"] <= 5.0:
                label = 1; break

        window = 3
        ctx_words = words[max(0, words.index(w)-window):words.index(w)+window+1]
        aligned.append({
            "video_id": video_id, "comedian": comedian,
            "audio_file": audio_file,
            "word_index": words.index(w),
            "word": w["word"], "start": w["start"], "end": w["end"],
            "duration": w["end"] - w["start"],
            "label": label,
            "context_words": [x["word"] for x in ctx_words],
            "context_labels": [0] * len(ctx_words),
        })

    # Expand labels backward
    labels = [a["label"] for a in aligned]
    expanded = labels[:]
    for i, a in enumerate(aligned):
        if a["label"] == 1:
            for j in range(max(0, i-2), i):
                if expanded[j] == 0:
                    expanded[j] = 1
    for i in range(len(aligned)):
        aligned[i]["label"] = expanded[i]

    # Save to aligned file
    with open(ALIGNED_FILE, "a") as f:
        for seg in aligned:
            f.write(json.dumps(seg, ensure_ascii=False) + "\n")

    return len(aligned)


def scale_to_1M():
    """Main scaling loop."""
    log("=" * 60)
    log("SCALE TO 1M AUDIO SEGMENTS")
    log("=" * 60)

    # Load current stats
    if STATS_FILE.exists():
        stats = json.loads(STATS_FILE.read_text())
    else:
        stats = {"total": 0, "by_lang": {}, "by_comedian": {}}

    def get_total():
        if ALIGNED_FILE.exists():
            return sum(1 for _ in open(ALIGNED_FILE))
        return 0

    current = get_total()
    log(f"Current segments: {current:,}")

    # Phase 1: Complete remaining transcription
    # - OLGrx-m-0iA (still running)
    # - Zakir Khan kWj8DQ5GTxM (needs Whisper + VTT)
    # - Jerry Seinfeld ppR78fk1gHc (needs VTT with auth)
    # - Chappelle 0qGd6KXh_ig (needs audio with auth)

    # Phase 2: Search and add new English videos
    log("\n=== Phase 2: Finding new English videos ===")
    new_en = search_videos("stand up comedy funny compilation english", n=20)
    log(f"Found {len(new_en)} new English candidates")

    for v in new_en[:10]:
        density = check_vtt_laugh_density(v["id"])
        if density >= 20:
            log(f"  {v['id']}: {density} laugh markers ✓")
        else:
            log(f"  {v['id']}: {density} laugh markers ✗")

    # Phase 3: Chinese StandUp4AI
    log("\n=== Phase 3: Chinese StandUp4AI ===")
    # Check if StandUp4AI Chinese data is accessible
    standup4ai_zh = Path("/tmp/standup4ai_dataset/Examples_label/")
    if standup4ai_zh.exists():
        csvs = list(standup4ai_zh.glob("*.csv"))
        log(f"  StandUp4AI CSVs: {len(csvs)}")
        # Filter for Chinese-related (check filename patterns)
        # Actually StandUp4AI has en/fr/es/cs only, no Chinese
        log(f"  Note: StandUp4AI has no Chinese labeled data")
        log(f"  Strategy: Search YouTube for Chinese comedy with auto-subs")

    # Phase 4: Hindi/Hinglish expansion
    log("\n=== Phase 4: Hindi/Hinglish expansion ===")
    new_hi = search_videos("hindi stand up comedy zakir khan biswa", n=15)
    log(f"Found {len(new_hi)} Hindi candidates")

    for v in new_hi[:5]:
        log(f"  {v['id']}: {v['title']}")

    log(f"\n=== Progress: {current:,} / 1,000,000 ===")
    log("Pipeline ready. Next: download → transcribe → align → extract")

    # Save current state
    stats["total"] = current
    STATS_FILE.write_text(json.dumps(stats, indent=2))


if __name__ == "__main__":
    scale_to_1M()