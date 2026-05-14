#!/usr/bin/env python3
"""
Find comedy videos on YouTube with [laughter] markers in subtitles.
Outputs video candidates per language to data/video_candidates/{lang}.json

Usage:
    python training/find_comedy_videos.py --lang en --target 417
    python training/find_comedy_videos.py --lang zh --target 556
    python training/find_comedy_videos.py --lang hi-latn --target 667
"""

import json
import os
import re
import time
import argparse
import subprocess
from pathlib import Path
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

import urllib.request

# ── Config ──────────────────────────────────────────────────────────
SEARCH_QUERIES = {
    "en": [
        "stand up comedy special full",
        "comedy special netflix",
        "comedian full show",
        "stand up comedy 2024",
        "comedy central special",
    ],
    "zh": [
        "单口相声",
        "脱口秀",
        "相声大会",
        "中国喜剧",
        "喜剧演员",
    ],
    "hi-latn": [
        "hindi stand up comedy zakir khan",
        "hinglish comedy special",
        "indian comedy show",
        "hindi hasya kavi sammelan",
        "desi comedy",
    ],
}

LAUGHTER_MARKERS = {
    "en": ["[laughter]", "[laughing]", "[applause]", "[Applause]", "(audience laughing)", "(audience laughs)"],
    "zh": ["[笑声]", "[笑]", "[掌声]", "[鼓掌]", "(观众笑)"],
    "hi-latn": ["[हंसी]", "[ताली]", "[हंसते]", "[प्रशंसा]", "(दर्शक हंसते हैं)"],
}

MIN_Laugh_MARKERS = 20
MIN_DURATION_MIN = 10
MAX_DURATION_MIN = 120


def run_yt_dlp(args: list, timeout: int = 60) -> dict:
    """Run yt-dlp and return parsed JSON output."""
    cmd = ["yt-dlp"] + args
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        if result.returncode != 0:
            return {"error": result.stderr[:200]}
        return json.loads(result.stdout)
    except subprocess.TimeoutExpired:
        return {"error": "timeout"}
    except Exception as e:
        return {"error": str(e)[:200]}


def search_videos(query: str, max_results: int = 50) -> list:
    """Search YouTube for videos matching query."""
    # Use yt-dlp ytsearch
    args = [
        f"ytsearch{max_results}:{query}",
        "--flat-playlist",
        "--dump-single-json",
        "--playlist-end", str(max_results),
    ]
    result = run_yt_dlp(args)
    if "error" in result:
        return []
    
    entries = result.get("entries", [])
    videos = []
    for entry in entries:
        if entry.get("_type") == "url":
            videos.append({
                "id": entry.get("id", ""),
                "title": entry.get("title", ""),
                "duration": entry.get("duration", 0),
                "url": entry.get("url", ""),
            })
    return videos


def check_subtitles(video_id: str, lang: str) -> dict:
    """Check if video has auto-subs and count laugh markers."""
    url = f"https://www.youtube.com/watch?v={video_id}"
    
    # List available subtitles
    list_args = [
        "--list-subs",
        "--skip-download",
        url,
    ]
    result = run_yt_dlp(list_args, timeout=30)
    
    # Check for auto-generated subs
    has_auto_subs = "auto" in result.get("stdout", "") or "generated" in result.get("stdout", "")
    
    if not has_auto_subs:
        return {"has_subs": False, "laugh_count": 0}
    
    # Download subtitle to check laugh markers
    sub_args = [
        "--skip-download",
        "--write-auto-sub",
        "--sub-langs", "en" if lang == "en" else lang[:2],
        "--convert-subs", "vtt",
        "--output", f"/tmp/{video_id}",
        url,
    ]
    sub_result = run_yt_dlp(sub_args, timeout=60)
    
    if "error" in sub_result:
        return {"has_subs": False, "laugh_count": 0}
    
    # Read subtitle file and count laugh markers
    vtt_path = f"/tmp/{video_id}.en.vtt"
    if not os.path.exists(vtt_path):
        vtt_path = f"/tmp/{video_id}.{lang[:2]}.vtt"
    
    if not os.path.exists(vtt_path):
        return {"has_subs": False, "laugh_count": 0}
    
    try:
        with open(vtt_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        
        # Count laugh markers
        laugh_count = 0
        for marker in LAUGHTER_MARKERS.get(lang, LAUGHTER_MARKERS["en"]):
            laugh_count += content.lower().count(marker.lower())
        
        # Cleanup
        os.remove(vtt_path)
        
        return {"has_subs": True, "laugh_count": laugh_count}
    except Exception as e:
        return {"has_subs": False, "laugh_count": 0, "error": str(e)}


def process_video(video: dict, lang: str) -> dict:
    """Process a single video: check subs, count laughs."""
    video_id = video.get("id", "")
    duration = video.get("duration", 0)
    
    # Filter by duration
    if duration < MIN_DURATION_MIN * 60 or duration > MAX_DURATION_MIN * 60:
        return None
    
    # Check subtitles
    sub_info = check_subtitles(video_id, lang)
    
    if not sub_info.get("has_subs") or sub_info.get("laugh_count", 0) < MIN_Laugh_MARKERS:
        return None
    
    return {
        "id": video_id,
        "title": video.get("title", ""),
        "duration_min": duration / 60,
        "laugh_markers": sub_info["laugh_count"],
        "url": f"https://youtube.com/watch?v={video_id}",
        "language": lang,
    }


def main():
    parser = argparse.ArgumentParser(description="Find comedy videos with laugh markers")
    parser.add_argument("--lang", choices=["en", "zh", "hi-latn"], required=True)
    parser.add_argument("--target", type=int, required=True, help="Target number of videos")
    parser.add_argument("--output-dir", default="data/video_candidates")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between requests (seconds)")
    args = parser.parse_args()
    
    os.makedirs(args.output_dir, exist_ok=True)
    output_file = os.path.join(args.output_dir, f"{args.lang}.json")
    
    print(f"Finding {args.target} {args.lang} comedy videos...")
    print(f"Output: {output_file}")
    
    # Load existing candidates
    candidates = []
    if os.path.exists(output_file):
        with open(output_file) as f:
            candidates = json.load(f)
        print(f"Loaded {len(candidates)} existing candidates")
    
    if len(candidates) >= args.target:
        print(f"Already have {len(candidates)} candidates, skipping")
        return
    
    # Search queries
    queries = SEARCH_QUERIES.get(args.lang, SEARCH_QUERIES["en"])
    
    found_videos = []
    for query in queries:
        if len(found_videos) >= args.target * 2:  # Get extra for filtering
            break
        
        print(f"\nSearching: {query}")
        videos = search_videos(query, max_results=50)
        print(f"  Found {len(videos)} videos")
        
        # Process videos in parallel
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            futures = {executor.submit(process_video, v, args.lang): v for v in videos}
            
            for future in as_completed(futures):
                result = future.result()
                if result:
                    found_videos.append(result)
                    print(f"  ✓ {result['id']}: {result['laugh_markers']} laughs, {result['duration_min']:.1f}min")
                
                time.sleep(args.delay)  # Rate limiting
        
        print(f"  Total valid: {len(found_videos)}")
    
    # Merge with existing and dedupe
    all_videos = {v["id"]: v for v in candidates}
    for v in found_videos:
        all_videos[v["id"]] = v
    
    final_list = list(all_videos.values())[:args.target]
    
    # Save
    with open(output_file, "w") as f:
        json.dump(final_list, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"Saved {len(final_list)} candidates to {output_file}")
    print(f"Languages: {args.lang}")
    print(f"Total laugh markers: {sum(v['laugh_markers'] for v in final_list)}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
