#!/usr/bin/env python3
"""
Parallel Pipeline Manager for 1000 Video Collection
===================================================
Coordinates multiple collection/processing streams in parallel.
Uses TaskMaster for tracking and GCS for storage.

Usage:
    python3 parallel_pipeline_manager.py --target 1000 --parallel-streams 5
"""

import os
import sys
import json
import time
import subprocess
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Set
import threading
import queue

# Add project to path
sys.path.insert(0, '/Users/Subho/autonomous_laughter_prediction')

# ============================================================================
# PATHS
# ============================================================================

GCS_PROJECT = 'omniclaw-personal-assistant'
GCS_BUCKET = 'chuckle-net-youtube-20260616'
PROCESSED_DIR = '/Users/Subho/data/chuckle-net-youtube/processed'
WAVLM_DIR = '/Users/Subho/data/chuckle-net-youtube/wavlm_embeddings'
AUDIO_DIR = '/Users/Subho/data/chuckle-net-youtube/audio'
CHECKPOINT = '/Users/Subho/data/chuckle-net-youtube/collection_checkpoint.json'

os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(WAVLM_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)

# ============================================================================
# YOUTUBE SEARCH QUERIES (Diverse, targeting downloadable content)
# ============================================================================

YOUTUBE_QUERIES = [
    # US/UK Stand-up Comedy (likely downloadable)
    "stand up comedy full special 2024",
    "stand up comedy Netflix 2023",
    "comedy cellars stand up full",
    "late night comedy special",
    
    # Crowd Work (high laughter potential)
    "stand up crowd work全场爆笑",
    "comedy crowd work interaction",
    "stand up comedy improvisation",
    
    # Regional English Comedy (less blocked)
    "Australian stand up comedy full",
    "Irish stand up comedy full special",
    "British comedy stand up full show",
    "Canadian stand up comedy full",
    
    # Singapore/Malaysia (our best success rate)
    "新加坡脱口秀全场笑声",
    "马来西亚华人喜剧 full",
    "Singapore stand up comedy Netflix",
    " Malaysian comedy special full",
    
    # Indian English Comedy
    "Indian stand up comedy full special",
    " Bollywood comedy roast full",
    
    # Clean Comedy (less likely blocked)
    "clean stand up comedy full",
    "family friendly comedy special",
    
    # Podcast Comedy
    "comedy podcast full episode",
    " Joe Rogan comedy special",
    " podcasts full comedy",
]

# ============================================================================
# CHECKPOINT MANAGEMENT
# ============================================================================

def load_checkpoint() -> Dict:
    """Load collection checkpoint."""
    if os.path.exists(CHECKPOINT):
        with open(CHECKPOINT) as f:
            return json.load(f)
    return {
        'collected_videos': {},
        'processed_videos': {},
        'failed_videos': {},
        'total_collected': 0,
        'total_processed': 0,
        'last_updated': datetime.now().isoformat()
    }

def save_checkpoint(cp: Dict):
    """Save checkpoint."""
    cp['last_updated'] = datetime.now().isoformat()
    with open(CHECKPOINT, 'w') as f:
        json.dump(cp, f, indent=2)

# ============================================================================
# VIDEO COLLECTION
# ============================================================================

def search_youtube_videos(query: str, max_results: int = 30) -> List[Dict]:
    """Search YouTube for videos using yt-dlp."""
    cmd = [
        'yt-dlp',
        '--cookies-from-browser', 'chrome',
        '--quiet',
        '--no-playlist',
        '--print', '%(id)s|%(duration)s|%(title)s|%(channel)s',
        f'--match-filter', f'duration>180 & duration<5400',  # 3min to 90min
        '--', f'ytsearch{max_results}:{query}'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        videos = []
        for line in result.stdout.strip().split('\n'):
            if '|' in line:
                parts = line.split('|')
                if len(parts) >= 3:
                    vid = parts[0]
                    try:
                        duration = int(parts[1]) if parts[1].isdigit() else 0
                    except:
                        duration = 0
                    title = parts[2] if len(parts) > 2 else ''
                    channel = parts[3] if len(parts) > 3 else ''
                    videos.append({
                        'id': vid,
                        'duration': duration,
                        'title': title,
                        'channel': channel,
                        'query': query
                    })
        return videos
    except Exception as e:
        print(f"  Search error for '{query}': {e}")
        return []

def get_video_subtitles(video_id: str) -> Dict:
    """Get subtitles with [laughter] markers for a video."""
    cmd = [
        'yt-dlp',
        '--cookies-from-browser', 'chrome',
        '--skip-download',
        '--write-sub', '--sub-langs', 'en,eng',
        '--sub-format', 'vtt',
        '--output', f'/tmp/{video_id}.%(ext)s',
        '--no-playlist',
        '--', f'https://www.youtube.com/watch?v={video_id}'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        # Look for [laughter] markers in subtitle file
        vtt_files = list(Path('/tmp').glob(f'{video_id}*.vtt'))
        
        subtitle_text = ''
        for vtt_file in vtt_files:
            try:
                with open(vtt_file) as f:
                    subtitle_text += f.read()
                vtt_file.unlink()  # Clean up
            except:
                pass
        
        # Count [laughter] markers
        laugh_count = subtitle_text.count('[laughter]')
        has_laughter_markers = laugh_count > 0
        
        return {
            'has_laughter_markers': has_laughter_markers,
            'laugh_count': laugh_count,
            'video_id': video_id
        }
        
    except Exception as e:
        return {'has_laughter_markers': False, 'laugh_count': 0, 'video_id': video_id, 'error': str(e)}

def collect_video(video_id: str, metadata: Dict) -> Dict:
    """Collect a single video (check subtitles, add to collection)."""
    result = {
        'video_id': video_id,
        'title': metadata.get('title', ''),
        'channel': metadata.get('channel', ''),
        'duration': metadata.get('duration', 0),
        'query': metadata.get('query', ''),
        'timestamp': datetime.now().isoformat(),
        'status': 'unknown'
    }
    
    # Quick subtitle check
    sub_info = get_video_subtitles(video_id)
    result['laugh_count'] = sub_info.get('laugh_count', 0)
    result['has_laughter'] = sub_info.get('has_laughter_markers', False)
    
    if result['has_laughter']:
        result['status'] = 'collected'
    elif result['laugh_count'] > 0:
        result['status'] = 'collected'
    else:
        result['status'] = 'skipped_no_laughter'
    
    return result

# ============================================================================
# PARALLEL COLLECTION WORKER
# ============================================================================

def collection_worker(worker_id: int, queries: List[str], checkpoint: Dict, results_queue: queue.Queue):
    """Worker that collects videos from assigned queries."""
    print(f"[Worker {worker_id}] Starting with {len(queries)} queries")
    
    for query in queries:
        videos = search_youtube_videos(query, max_results=30)
        
        for video in videos:
            vid = video['id']
            
            # Skip already collected
            if vid in checkpoint['collected_videos']:
                continue
            
            # Skip already failed
            if vid in checkpoint['failed_videos']:
                continue
            
            # Collect video
            result = collect_video(vid, video)
            
            if result['status'] == 'collected':
                checkpoint['collected_videos'][vid] = result
                checkpoint['total_collected'] += 1
                results_queue.put(('collected', vid, result))
            else:
                checkpoint['failed_videos'][vid] = result
                results_queue.put(('skipped', vid, result))
        
        # Save checkpoint after each query
        save_checkpoint(checkpoint)
        print(f"[Worker {worker_id}] Query '{query[:30]}...': {len(videos)} videos")
    
    print(f"[Worker {worker_id}] Done")
    results_queue.put(('worker_done', worker_id, None))

# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='Parallel 1000 Video Collector')
    parser.add_argument('--target', type=int, default=1000, help='Target number of videos')
    parser.add_argument('--parallel-streams', type=int, default=5, help='Number of parallel collection streams')
    args = parser.parse_args()
    
    print("=" * 70)
    print(f"PARALLEL VIDEO COLLECTION - TARGET: {args.target} videos")
    print(f"Parallel streams: {args.parallel_streams}")
    print("=" * 70)
    
    # Load checkpoint
    checkpoint = load_checkpoint()
    print(f"\nCheckpoint: {checkpoint['total_collected']} already collected")
    
    # Check how many more we need
    already_done = checkpoint['total_collected']
    remaining = max(0, args.target - already_done)
    
    if remaining <= 0:
        print(f"✅ Already have {already_done} videos! Target reached.")
        return
    
    print(f"Need to collect {remaining} more videos")
    
    # Split queries among workers
    queries_per_worker = len(YOUTUBE_QUERIES) // args.parallel_streams
    query_chunks = []
    for i in range(args.parallel_streams):
        start = i * queries_per_worker
        end = start + queries_per_worker if i < args.parallel_streams - 1 else len(YOUTUBE_QUERIES)
        query_chunks.append(YOUTUBE_QUERIES[start:end])
    
    print(f"\nSplit {len(YOUTUBE_QUERIES)} queries into {args.parallel_streams} streams")
    
    # Results queue
    results_queue = queue.Queue()
    
    # Start workers
    threads = []
    for i, queries in enumerate(query_chunks):
        t = threading.Thread(target=collection_worker, args=(i, queries, checkpoint, results_queue))
        t.start()
        threads.append(t)
        print(f"Started worker {i}")
    
    # Monitor progress
    last_count = checkpoint['total_collected']
    while any(t.is_alive() for t in threads):
        time.sleep(5)
        current = checkpoint['total_collected']
        if current != last_count:
            rate = (current - last_count) / 5
            print(f"  Progress: {current}/{args.target} ({rate:.1f}/sec)")
            last_count = current
            
            if current >= args.target:
                print("✅ Target reached! Stopping workers...")
                break
    
    # Wait for completion
    for t in threads:
        t.join()
    
    # Final stats
    print("\n" + "=" * 70)
    print("COLLECTION COMPLETE")
    print("=" * 70)
    print(f"Total collected: {checkpoint['total_collected']}")
    print(f"Total failed: {len(checkpoint['failed_videos'])}")
    print(f"Checkpoint saved: {CHECKPOINT}")

if __name__ == '__main__':
    main()
