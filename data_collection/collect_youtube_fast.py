#!/usr/bin/env python3
"""
YouTube Comedy Collection - Reliable Multilingual Version

Key insight: Just TRY to download subtitles - don't pre-check languages.
YouTube auto-generates subtitles in many languages.
"""

import os
import json
import subprocess
import argparse
from pathlib import Path
from typing import List, Dict, Optional
from google.cloud import storage
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import re

# ============================================================================
# CONFIGURATION
# ============================================================================

class Config:
    GCS_BUCKET_NAME = 'chuckle-net-youtube-20260616'
    GCS_PROJECT = 'omniclaw-personal-assistant'
    MAX_WORKERS = 8

# ============================================================================
# GCS UTILITIES
# ============================================================================

def get_gcs_bucket():
    client = storage.Client(project=Config.GCS_PROJECT)
    return client.bucket(Config.GCS_BUCKET_NAME)

def gcs_upload_json(data: dict, gcs_path: str) -> bool:
    try:
        bucket = get_gcs_bucket()
        blob = bucket.blob(gcs_path)
        blob.upload_from_string(json.dumps(data, indent=2), content_type='application/json')
        return True
    except Exception as e:
        print(f"    GCS upload failed: {e}")
        return False

def gcs_exists(gcs_path: str) -> bool:
    try:
        bucket = get_gcs_bucket()
        blob = bucket.blob(gcs_path)
        return blob.exists()
    except Exception:
        return False

# ============================================================================
# YOUTUBE SEARCH
# ============================================================================

def search_youtube_videos(query: str, max_results: int = 50) -> List[Dict]:
    cmd = ['yt-dlp', '--flat-playlist', '--dump-json', f'ytsearch{max_results}:{query}']
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        videos = []
        for line in result.stdout.strip().split('\n'):
            if line:
                try:
                    data = json.loads(line)
                    videos.append({
                        'id': data.get('id'),
                        'title': data.get('title'),
                        'url': f"https://www.youtube.com/watch?v={data.get('id')}",
                        'duration': data.get('duration'),
                        'channel': data.get('channel'),
                        'view_count': data.get('view_count', 0),
                    })
                except json.JSONDecodeError:
                    continue
        return videos
    except Exception as e:
        print(f"Search error: {e}")
        return []

# ============================================================================
# SUBTITLE EXTRACTION
# ============================================================================

def extract_subtitles(video_id: str, video_url: str) -> Optional[Dict]:
    """Extract subtitles - try any language, no pre-checking."""
    
    # Check if already processed
    if gcs_exists(f'metadata/{video_id}.json'):
        return {'id': video_id, 'status': 'already_exists'}
    
    # Try to download auto-generated subtitles (they usually have [laughter] markers)
    vtt_base = f'/tmp/{video_id}'
    
    # Just try - don't pre-check languages
    cmd = [
        'yt-dlp',
        '--write-auto-subs',
        '--skip-download',
        '--sub-format', 'vtt',
        '--output', vtt_base,
        '--no-playlist',
        video_url,
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        # Find the VTT file
        vtt_file = None
        for pattern in [f'{vtt_base}.en.vtt', f'{vtt_base}.vtt', f'{vtt_base}.*vtt']:
            import glob
            matches = glob.glob(pattern)
            if matches:
                vtt_file = Path(matches[0])
                break
        
        if vtt_file and vtt_file.exists():
            # Detect language from filename
            lang = 'auto'
            if '.en.' in str(vtt_file):
                lang = 'en'
            elif '.hi.' in str(vtt_file):
                lang = 'hi'
            
            # Parse
            laughter_data = parse_vtt(vtt_file, video_id, lang)
            
            if laughter_data.get('laughter_count', 0) > 0:
                # Upload to GCS
                gcs_upload_json(laughter_data, f'metadata/{video_id}.json')
                bucket = get_gcs_bucket()
                blob = bucket.blob(f'subtitles/{video_id}.vtt')
                blob.upload_from_filename(str(vtt_file))
                
                print(f"    ✓ {laughter_data['laughter_count']} laughter markers, {laughter_data.get('total_utterances', 0)} utterances")
            else:
                print(f"    ✗ No laughter found")
            
            # Cleanup
            vtt_file.unlink()
            return laughter_data
        else:
            print(f"    ✗ No subtitles")
            return None
            
    except Exception as e:
        print(f"    Error: {e}")
        return None

def parse_vtt(vtt_path: Path, video_id: str, lang: str) -> Dict:
    """Parse VTT file and extract laughter markers + utterances."""
    laughter_markers = []
    utterances = []
    
    try:
        with open(vtt_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.strip().split('\n')
        current_start = None
        
        for line in lines:
            line = line.strip()
            
            # Timestamp line
            if '-->' in line:
                parts = line.split('-->')
                if len(parts) == 2:
                    start_str = parts[0].strip().replace(',', '.')
                    current_start = timestamp_to_seconds(start_str)
            
            # Text content (skip tags)
            elif line and current_start is not None:
                # Skip VTT tags
                if line.startswith('<') or line.startswith('WEBVTT'):
                    continue
                
                text = line.strip()
                if text:
                    # Check for laughter
                    has_laughter = '[laughter]' in text.lower()
                    
                    utterances.append({
                        'start': current_start,
                        'end': current_start + estimate_duration(text),
                        'text': text,
                        'has_laughter': has_laughter
                    })
                    
                    if has_laughter:
                        laughter_markers.append({
                            'start': current_start,
                            'end': current_start + estimate_duration(text),
                            'text': text,
                            'has_laughter': True
                        })
                    
                    current_start = None
        
        return {
            'id': video_id,
            'lang': lang,
            'laughter_count': len(laughter_markers),
            'laughter_markers': laughter_markers,
            'total_utterances': len(utterances),
            'utterances': utterances[:500],  # Limit to save space
            'status': 'success'
        }
        
    except Exception as e:
        return {
            'id': video_id,
            'lang': lang,
            'laughter_count': 0,
            'laughter_markers': [],
            'error': str(e),
            'status': 'error'
        }

def timestamp_to_seconds(ts: str) -> float:
    parts = ts.split(':')
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    return 0.0

def estimate_duration(text: str) -> float:
    return max(1.0, len(text.split()) / 3.0)

# ============================================================================
# PARALLEL PROCESSING
# ============================================================================

def process_video(video: Dict) -> Dict:
    video_id = video['id']
    print(f"  {video['title'][:45]}...")
    result = extract_subtitles(video_id, video['url'])
    return {'video_id': video_id, 'title': video['title'], 'result': result}

def process_videos_parallel(videos: List[Dict], max_workers: int = 8) -> List[Dict]:
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_video, v): v for v in videos}
        for future in as_completed(futures):
            try:
                results.append(future.result(timeout=300))
            except Exception as e:
                video = futures[future]
                results.append({'video_id': video.get('id'), 'error': str(e)})
    return results

# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--max-videos', type=int, default=100)
    parser.add_argument('--parallel', type=int, default=8)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    
    print(f"=== YouTube Comedy Collection (Reliable) ===")
    print(f"Method: YouTube auto-subtitles (NO Whisper!)")
    print()
    
    # Search for comedy videos
    all_videos = {}
    queries = [
        # Singaporean/Malaysian English comedy (HIGH SUCCESS - crowd noise → [laughter] markers)
        'Jack Neo comedy special full',
        'Kumar comedian full show',
        'Douglas Lim Malaysia standup',
        'Sarahdon\'s CPR comedy full',
        'Sathu comedy special full',
        '衰仔 comedian Singapore full show',
        'Singapore standup comedy full special',
        'Malaysian comedian full show',
        # US/UK specials (lower success - professional subtitles)
        'netflix comedy special standup full show',
        'hbo comedy special full',
        'comedy central standup full',
        'amazon prime comedy special',
        'stand up comedy full special',
        # More specific: crowd-work and club comedy
        'open mic comedy crowd work',
        'comedy club standup full set',
        'late night monologue comedy full',
    ]
    
    for query in queries:
        videos = search_youtube_videos(query, max_results=30)
        for v in videos:
            if v['id'] not in all_videos:
                all_videos[v['id']] = v
        print(f"  {query}: {len(videos)} videos, total: {len(all_videos)}")
    
    # Filter
    good_videos = [v for v in all_videos.values() if 180 <= v.get('duration', 0) <= 5400]
    print(f"\\nTotal good videos (3-90 min): {len(good_videos)}")
    
    if args.dry_run:
        for i, v in enumerate(good_videos[:10]):
            print(f"  {i+1}. {v['title'][:60]}")
        return
    
    # Process
    videos_to_process = good_videos[:args.max_videos]
    print(f"\\nProcessing {len(videos_to_process)} videos with {args.parallel} workers...")
    
    start = time.time()
    results = process_videos_parallel(videos_to_process, max_workers=args.parallel)
    elapsed = time.time() - start
    
    # Summary
    valid = [r for r in results if r.get('result')]
    success = [r for r in valid if r['result'].get('status') == 'success' and r['result'].get('laughter_count', 0) > 0]
    total_laughter = sum(r['result'].get('laughter_count', 0) for r in success)
    total_utterances = sum(r['result'].get('total_utterances', 0) for r in success)
    
    print(f"\\n=== Complete ===")
    print(f"Time: {elapsed:.0f}s ({len(results)/elapsed:.1f} videos/sec)")
    print(f"Successful: {len(success)}/{len(videos_to_process)}")
    print(f"Laughter markers: {total_laughter}")
    print(f"Utterances: {total_utterances}")
    print(f"GCS: gs://{Config.GCS_BUCKET_NAME}/metadata/")

if __name__ == '__main__':
    main()
