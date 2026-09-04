#!/usr/bin/env python3
"""
Batch transcription pipeline for batch25 videos.
Steps: 1) Download VTT subtitles, 2) Transcribe with faster-whisper, 3) Register in DB
"""

import os
import sys
import json
import sqlite3
import subprocess
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent
AUDIO_DIR = PROJECT_ROOT / "data" / "audio_comedy" / "audio" / "batch25"
TRANSCRIPT_DIR = PROJECT_ROOT / "data" / "audio_comedy" / "transcripts" / "en"
ZH_TRANSCRIPT_DIR = PROJECT_ROOT / "data" / "audio_comedy" / "transcripts" / "zh"
VTT_DIR = PROJECT_ROOT / "data" / "audio_comedy" / "vtt_subtitles"
VTT_EN_DIR = VTT_DIR / "en"
VTT_ZH_DIR = VTT_DIR / "zh"
DB_PATH = PROJECT_ROOT / "data" / "collection_tracking.db"

# Videos to process
BATCH25_VIDEOS = {
    "xrGR6SCbris": {"lang": "zh", "title": "欢乐喜剧人4 贾冰小品合集"},
    "UA4lxMy9ma8": {"lang": "zh", "title": "潘斌龙崔志佳超长小品合集"},
    "mHKw-m0tLFw": {"lang": "en", "title": "60 Minutes of Jokes | Stand-up Comedy"},
    "a5nwhwCleRg": {"lang": "zh", "title": "House最全合集 一战封神 脱口秀大会S5"},
    "TSi5zOfEaQE": {"lang": "en", "title": "Chris D'Elia: Grow Or Die"},
    "YZfyiq8l7j8": {"lang": "zh", "title": "翟佳宁吐槽化工的食物"},
    "7adFztVTSA0": {"lang": "zh", "title": "郭德纲于谦三十而绿"},
    "w2DTEOB5rhk": {"lang": "en", "title": "Devastating Burns from the Roasts"},
    "5bTITZ-4xKg": {"lang": "zh", "title": "郭德纲于谦超经典相声 我要折腾"},
    "jQirKXwDFD8": {"lang": "zh", "title": "年度喜剧社团揭晓 蒋龙张弛"},
}


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def ensure_dirs():
    for d in [TRANSCRIPT_DIR, ZH_TRANSCRIPT_DIR, VTT_EN_DIR, VTT_ZH_DIR]:
        d.mkdir(parents=True, exist_ok=True)


def download_vtt(video_id, lang):
    """Try to download VTT subtitles for a video."""
    if lang == "zh":
        vtt_dir = VTT_ZH_DIR
        sub_langs = ["zh-Hans,zh-CN,zh"]
    else:
        vtt_dir = VTT_EN_DIR
        sub_langs = ["en"]

    # Check if already exists
    existing = list(vtt_dir.glob(f"{video_id}*.vtt"))
    if existing:
        log(f"  VTT already exists: {existing[0]}")
        return str(existing[0])

    url = f"https://www.youtube.com/watch?v={video_id}"
    for sub_lang in sub_langs:
        try:
            result = subprocess.run(
                ["yt-dlp", "--write-auto-sub", "--write-sub",
                 "--sub-lang", sub_lang, "--sub-format", "vtt",
                 "--skip-download", "-o", str(vtt_dir / video_id), url],
                capture_output=True, text=True, timeout=120
            )
            new_vtts = list(vtt_dir.glob(f"{video_id}*.vtt"))
            if new_vtts:
                log(f"  VTT downloaded: {new_vtts[0]}")
                return str(new_vtts[0])
        except Exception as e:
            log(f"  VTT download failed for {sub_lang}: {e}")

    log(f"  No VTT available for {video_id}")
    return None


def transcribe_video(video_id, audio_path, lang):
    """Transcribe audio using faster-whisper with word timestamps."""
    from faster_whisper import WhisperModel

    # Select appropriate model based on language
    # Use "base" for English, "small" for Chinese
    model_size = "base" if lang == "en" else "small"
    
    log(f"  Loading faster-whisper model '{model_size}' (int8)...")
    model = WhisperModel(model_size, compute_type="int8", device="cpu")

    log(f"  Transcribing {video_id} (lang={lang})...")
    
    # Transcribe with word timestamps
    if lang == "zh":
        # Chinese transcription
        segments, info = model.transcribe(
            audio_path, 
            language="zh",
            word_timestamps=True,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500),
        )
    else:
        segments, info = model.transcribe(
            audio_path,
            language="en",
            word_timestamps=True,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500),
        )

    log(f"  Language detected: {info.language} (prob: {info.language_probability:.2f})")
    log(f"  Duration: {info.duration:.1f}s")

    # Collect all words and segments
    all_words = []
    all_segments = []
    
    for seg in segments:
        seg_dict = {
            "id": seg.id,
            "seek": seg.seek,
            "start": seg.start,
            "end": seg.end,
            "text": seg.text,
            "tokens": [],
            "temperature": seg.temperature,
            "avg_logprob": seg.avg_logprob,
            "compression_ratio": seg.compression_ratio,
            "no_speech_prob": seg.no_speech_prob,
            "words": []
        }
        if seg.words:
            for w in seg.words:
                word_dict = {
                    "word": w.word,
                    "start": w.start,
                    "end": w.end,
                    "probability": w.probability,
                }
                seg_dict["words"].append(word_dict)
                all_words.append(word_dict)
        all_segments.append(seg_dict)

    log(f"  Segments: {len(all_segments)}, Words: {len(all_words)}")

    output = {
        "video_id": video_id,
        "language": lang,
        "model": f"faster-whisper-{model_size}",
        "segments": all_segments,
        "words": all_words,
    }
    return output


def save_transcript(video_id, data, lang):
    """Save transcript JSON to appropriate directory."""
    out_dir = ZH_TRANSCRIPT_DIR if lang == "zh" else TRANSCRIPT_DIR
    out_path = out_dir / f"{video_id}_transcript.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    log(f"  Saved transcript: {out_path} ({out_path.stat().st_size / 1024:.1f} KB)")
    return str(out_path)


def register_in_db(video_id, transcript_path, word_count, lang):
    """Register transcript in the tracking database."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT OR REPLACE INTO transcripts 
        (video_id, file_path, word_count, duration_sec, transcription_status, model_used)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (video_id, transcript_path, word_count, 0, "success", "faster-whisper"))
    conn.commit()
    conn.close()
    log(f"  Registered in DB: {video_id}")


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=5, help="Max videos to process")
    parser.add_argument("--skip-vtt", action="store_true", help="Skip VTT download step")
    parser.add_argument("--videos", nargs="+", help="Specific video IDs to process")
    args = parser.parse_args()

    ensure_dirs()

    # Filter videos
    if args.videos:
        videos = {k: v for k, v in BATCH25_VIDEOS.items() if k in args.videos}
    else:
        videos = BATCH25_VIDEOS

    # Prioritize English videos (likely have VTT + more useful)
    sorted_videos = sorted(videos.items(), key=lambda x: (0 if x[1]["lang"] == "en" else 1, x[0]))
    to_process = sorted_videos[:args.limit]

    results = []
    
    for video_id, info in to_process:
        log(f"\n{'='*60}")
        log(f"Processing: {video_id} ({info['lang']}) - {info['title']}")
        log(f"{'='*60}")

        audio_path = AUDIO_DIR / f"{video_id}.mp3"
        if not audio_path.exists():
            log(f"  SKIP: Audio not found at {audio_path}")
            continue

        # Step 1: Download VTT
        vtt_path = None
        if not args.skip_vtt:
            log(f"  Step 1: Downloading VTT subtitles...")
            vtt_path = download_vtt(video_id, info["lang"])

        # Step 2: Transcribe
        log(f"  Step 2: Transcribing with faster-whisper...")
        try:
            transcript = transcribe_video(video_id, str(audio_path), info["lang"])
        except Exception as e:
            log(f"  TRANSCRIPTION FAILED: {e}")
            continue

        # Step 3: Save
        log(f"  Step 3: Saving transcript...")
        saved_path = save_transcript(video_id, transcript, info["lang"])

        # Step 4: Register in DB
        register_in_db(video_id, saved_path, len(transcript["words"]), info["lang"])

        results.append({
            "video_id": video_id,
            "language": info["lang"],
            "title": info["title"],
            "segments": len(transcript["segments"]),
            "words": len(transcript["words"]),
            "vtt_available": vtt_path is not None,
            "transcript_path": saved_path,
        })

    # Summary
    log(f"\n{'='*60}")
    log(f"SUMMARY")
    log(f"{'='*60}")
    total_words = 0
    for r in results:
        log(f"  {r['video_id']}: {r['words']} words, {r['segments']} segments, VTT={r['vtt_available']}")
        total_words += r["words"]
    log(f"\nTotal: {len(results)} videos, {total_words} words")
    log(f"Estimated new segments (~6 words/segment): ~{total_words // 6}")

    if results:
        summary_path = PROJECT_ROOT / "data" / "audio_comedy" / "batch25_transcription_summary.json"
        with open(summary_path, "w") as f:
            json.dump(results, f, indent=2)
        log(f"Summary saved to: {summary_path}")


if __name__ == "__main__":
    main()