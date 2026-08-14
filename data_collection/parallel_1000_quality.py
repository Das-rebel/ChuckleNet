#!/usr/bin/env python3
"""
High-Quality Parallel 1000 Video Collection
==========================================
Parallel collection with strict quality filtering.
Only collects videos that meet quality thresholds.

Quality Criteria:
- Minimum 10 [laughter] markers
- Duration 3-90 minutes
- No reaction videos, compilations, etc.
- Target: 50+ laughs for "high quality"

Usage:
    python3 parallel_1000_quality.py --target 1000 --parallel 5
"""

import os
import sys
import json
import time
import subprocess
import argparse
import threading
import queue
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, '/Users/Subho/autonomous_laughter_prediction')

# Import quality filter
from quality_filter import VideoQualityScorer, QualityCriteria, print_quality_report

# ============================================================================
# PATHS
# ============================================================================

GCS_PROJECT = 'omniclaw-personal-assistant'
GCS_BUCKET = 'chuckle-net-youtube-20260616'
PROCESSED_DIR = '/Users/Subho/data/chuckle-net-youtube/processed'
WAVLM_DIR = '/Users/Subho/data/chuckle-net-youtube/wavlm_embeddings'
AUDIO_DIR = '/Users/Subho/data/chuckle-net-youtube/audio'
CHECKPOINT = '/Users/Subho/data/chuckle-net-youtube/quality_checkpoint.json'

os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(WAVLM_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)

# ============================================================================
# QUALITY CONFIG
# ============================================================================

QUALITY_CRITERIA = QualityCriteria(
    min_laughs=10,        # Minimum to collect
    target_laughs=50,     # Target for training
    excellent_laughs=100, # Excellent quality
    min_duration=180,     # 3 min minimum
    max_duration=5400,    # 90 min maximum
)

scorer = VideoQualityScorer(QUALITY_CRITERIA)

# ============================================================================
# CHECKPOINT MANAGEMENT
# ============================================================================

def load_checkpoint() -> Dict:
    if os.path.exists(CHECKPOINT):
        with open(CHECKPOINT) as f:
            return json.load(f)
    return {
        'collected_videos': {},    # video_id -> video_info with quality scores
        'assessed_videos': {},    # All videos assessed
        'total_collected': 0,
        'quality_stats': {
            'excellent': 0,
            'good': 0,
            'acceptable': 0,
            'low': 0,
            'rejected': 0,
        },
        'started_at': datetime.now().isoformat(),
        'last_updated': datetime.now().isoformat()
    }

def save_checkpoint(cp: Dict):
    cp['last_updated'] = datetime.now().isoformat()
    with open(CHECKPOINT, 'w') as f:
        json.dump(cp, f, indent=2)

# ============================================================================
# YOUTUBE SEARCH (DIVERSE, TARGETING DOWNLOADABLE)
# ============================================================================

SEARCH_QUERIES = [
    # US/UK Full Specials (likely downloadable)
    ("US Full Special", "stand up comedy full special 2024 netflix"),
    ("US Comedy Central", "comedy central stand up full show"),
    ("US HBO", "hbo stand up comedy special full"),
    ("UK Comedy", "british stand up comedy full special"),
    ("Irish Comedy", "irish stand up comedy full show"),
    ("Australian Comedy", "australian stand up comedy full special"),
    
    # Crowd Work (high laughs)
    ("Crowd Work 1", "stand up comedy crowd work全场爆笑"),
    ("Crowd Work 2", "comedy crowd work interaction special"),
    ("Crowd Work 3", "stand up comedy improvisation crowd"),
    
    # Singapore/Malaysia (best success rate with subtitles)
    ("SG Comedy 1", "新加坡脱口秀全场笑声 full"),
    ("SG Comedy 2", "马来西亚华人喜剧 full show"),
    ("SG Comedy 3", "singapore stand up comedy netflix special"),
    ("MY Comedy", "malaysian comedy special full show"),
    
    # Indian English (diverse accents)
    ("Indian Comedy 1", "indian stand up comedy full special netflix"),
    ("Indian Comedy 2", "bollywood comedy roast full show"),
    ("Indian Comedy 3", "vir das stand up comedy full"),
    
    # Clean/Wholesome (less blocking)
    ("Clean 1", "clean stand up comedy full special"),
    ("Clean 2", "family friendly comedy full show"),
    ("Clean 3", "wholesome stand up comedy special"),
    
    # Podcast Comedy
    ("Podcast 1", "comedy podcast full episode stand up"),
    ("Podcast 2", "joe rogan stand up comedy full special"),
]

# ============================================================================
# YOUTUBE API (via yt-dlp)
# ============================================================================

def search_youtube(query: str, max_results: int = 30) -> List[Dict]:
    """Search YouTube for videos."""
    cmd = [
        'yt-dlp',
        '--cookies-from-browser', 'chrome',
        '--quiet',
        '--no-playlist',
        '--print', '%(id)s|%(duration)s|%(title)s|%(channel)s',
        f'--match-filter', f'duration>180 & duration<5400',
        '--', f'ytsearch{max_results}:{query}'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        videos = []
        for line in result.stdout.strip().split('\n'):
            if '|' in line:
                parts = line.split('|')
                if len(parts) >= 3:
                    try:
                        duration = int(parts[1]) if parts[1].isdigit() else 0
                    except:
                        duration = 0
                    videos.append({
                        'video_id': parts[0],
                        'duration': duration,
                        'title': parts[2] if len(parts) > 2 else '',
                        'channel': parts[3] if len(parts) > 3 else '',
                        'query': query,
                        'discovered_at': datetime.now().isoformat()
                    })
        return videos
    except Exception as e:
        print(f"  Search error: {e}")
        return []

def get_subtitle_laugh_count(video_id: str) -> int:
    """Get [laughter] marker count from subtitles."""
    # Try to download subtitles only (fast)
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
        subprocess.run(cmd, capture_output=True, timeout=45)
        
        # Check for laughter markers
        vtt_files = list(Path('/tmp').glob(f'{video_id}*.vtt'))
        laugh_count = 0
        
        for vtt in vtt_files:
            try:
                content = vtt.read_text()
                laugh_count += content.count('[laughter]')
                vtt.unlink()  # Clean up
            except:
                pass
        
        return laugh_count
        
    except Exception as e:
        return 0

# ============================================================================
# FAST QUALITY ASSESSMENT (no download)
# ============================================================================

def assess_video_fast(video: Dict) -> Dict:
    """
    Fast quality assessment using metadata only.
    Returns video with quality_tier, quality_score.
    """
    # Get laugh count from subtitles (already have it from collection)
    video['laugh_count'] = video.get('laugh_count', 0)
    
    # Assess quality
    should_collect, tier, score, reasons = scorer.should_collect(video)
    
    video['quality_tier'] = tier
    video['quality_score'] = score
    video['quality_reasons'] = reasons
    video['quality_assessed_at'] = datetime.now().isoformat()
    video['should_collect'] = should_collect
    
    return video

# ============================================================================
# COLLECTION WORKER (single thread)
# ============================================================================

def collection_worker(worker_id: int, queries: List[tuple], checkpoint: Dict, 
                    results_queue: queue.Queue):
    """
    Worker that collects and assesses videos from assigned queries.
    Only collects videos that meet quality criteria.
    """
    print(f"[Worker {worker_id}] Starting with {len(queries)} queries")
    
    collected_this_worker = 0
    
    for query_name, query in queries:
        # Search
        videos = search_youtube(query, max_results=30)
        print(f"[Worker {worker_id}] '{query_name}': found {len(videos)} videos")
        
        for video in videos:
            vid = video['video_id']
            
            # Skip if already assessed
            if vid in checkpoint['assessed_videos']:
                continue
            
            # Quick subtitle check for laugh count
            laugh_count = get_subtitle_laugh_count(vid)
            video['laugh_count'] = laugh_count
            
            # Assess quality
            video = assess_video_fast(video)
            
            # Record assessment
            checkpoint['assessed_videos'][vid] = {
                'video_id': vid,
                'title': video.get('title', ''),
                'channel': video.get('channel', ''),
                'duration': video.get('duration', 0),
                'laugh_count': laugh_count,
                'quality_tier': video['quality_tier'],
                'quality_score': video['quality_score'],
                'should_collect': video['should_collect'],
                'query': query_name,
                'assessed_at': datetime.now().isoformat()
            }
            
            # Update quality stats
            if video['quality_tier'] in checkpoint['quality_stats']:
                checkpoint['quality_stats'][video['quality_tier']] += 1
            
            # Collect if quality passes
            if video['should_collect']:
                checkpoint['collected_videos'][vid] = checkpoint['assessed_videos'][vid]
                checkpoint['total_collected'] += 1
                collected_this_worker += 1
                results_queue.put(('collected', vid, video['quality_tier']))
            else:
                results_queue.put(('skipped', vid, video['quality_tier']))
        
        # Save checkpoint after each query
        save_checkpoint(checkpoint)
    
    print(f"[Worker {worker_id}] Done. Collected {collected_this_worker} videos")
    results_queue.put(('worker_done', worker_id, collected_this_worker))

# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='High-Quality 1000 Video Collector')
    parser.add_argument('--target', type=int, default=1000, help='Target number of videos')
    parser.add_argument('--parallel', type=int, default=5, help='Number of parallel workers')
    args = parser.parse_args()
    
    print("=" * 70)
    print(f"HIGH-QUALITY PARALLEL VIDEO COLLECTION")
    print(f"Target: {args.target} videos | Workers: {args.parallel}")
    print("=" * 70)
    
    # Load checkpoint
    checkpoint = load_checkpoint()
    
    already_done = checkpoint['total_collected']
    remaining = max(0, args.target - already_done)
    
    print(f"\nCheckpoint: {already_done} already collected")
    print(f"Need: {remaining} more videos")
    print(f"Quality criteria: ≥{QUALITY_CRITERIA.min_laughs} laughs, {QUALITY_CRITERIA.min_duration}s-{QUALITY_CRITERIA.max_duration}s duration")
    
    # Show quality stats
    print(f"\nQuality breakdown of assessed videos:")
    stats = checkpoint['quality_stats']
    total_assessed = sum(stats.values())
    if total_assessed > 0:
        for tier in ['excellent', 'good', 'acceptable', 'low', 'rejected']:
            count = stats.get(tier, 0)
            pct = count / total_assessed * 100
            print(f"  {tier}: {count} ({pct:.1f}%)")
    
    if remaining <= 0:
        print(f"✅ Target already reached!")
        return
    
    # Split queries among workers
    queries_per_worker = len(SEARCH_QUERIES) // args.parallel
    query_chunks = []
    for i in range(args.parallel):
        start = i * queries_per_worker
        end = start + queries_per_worker if i < args.parallel - 1 else len(SEARCH_QUERIES)
        query_chunks.append(SEARCH_QUERIES[start:end])
    
    print(f"\nSplit {len(SEARCH_QUERIES)} queries into {args.parallel} workers")
    
    # Results queue
    results_queue = queue.Queue()
    
    # Start workers
    threads = []
    for i, queries in enumerate(query_chunks):
        t = threading.Thread(
            target=collection_worker,
            args=(i, queries, checkpoint, results_queue)
        )
        t.start()
        threads.append(t)
        print(f"Started worker {i}")
    
    # Monitor progress
    last_total = checkpoint['total_collected']
    last_time = time.time()
    
    while any(t.is_alive() for t in threads):
        time.sleep(10)
        current = checkpoint['total_collected']
        total_assessed = len(checkpoint['assessed_videos'])
        
        if current != last_total:
            elapsed = time.time() - last_time
            rate = (current - last_total) / elapsed if elapsed > 0 else 0
            eta_min = (args.target - current) / rate / 60 if rate > 0 else 0
            
            print(f"  Progress: {current}/{args.target} ({rate:.2f}/sec, ETA: {eta_min:.0f}min)")
            last_total = current
            last_time = time.time()
            
            if current >= args.target:
                print("✅ Target reached!")
                break
    
    # Wait for workers
    for t in threads:
        t.join()
    
    # Final stats
    print("\n" + "=" * 70)
    print("COLLECTION COMPLETE")
    print("=" * 70)
    print(f"Total collected: {checkpoint['total_collected']}")
    print(f"Total assessed: {len(checkpoint['assessed_videos'])}")
    
    final_stats = checkpoint['quality_stats']
    print(f"\nFinal quality distribution:")
    for tier in ['excellent', 'good', 'acceptable', 'low', 'rejected']:
        count = final_stats.get(tier, 0)
        print(f"  {tier}: {count}")
    
    save_checkpoint(checkpoint)
    print(f"\nCheckpoint saved: {CHECKPOINT}")

if __name__ == '__main__':
    main()
