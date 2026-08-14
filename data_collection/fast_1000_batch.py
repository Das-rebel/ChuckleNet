#!/usr/bin/env python3
"""
Fast Batch Collection - Phase 1
=============================
FAST approach to collect 1000 videos:
1. Quickly search YouTube (no subtitle download)
2. Save all candidates to a batch file
3. Later batch-process subtitle checks

This gets candidates fast, then quality-filters later.
"""

import os
import sys
import json
import subprocess
import threading
import queue
from datetime import datetime
from pathlib import Path
from typing import Dict, List

sys.path.insert(0, '/Users/Subho/autonomous_laughter_prediction')

# ============================================================================
# PATHS
# ============================================================================

CANDIDATE_FILE = '/Users/Subho/data/chuckle-net-youtube/candidate_videos.jsonl'
SEARCH_QUERIES = [
    # US/UK Full Specials
    "stand up comedy full special 2024",
    "stand up comedy netflix 2023 2024",
    "comedy central stand up full show",
    "hbo stand up comedy special full",
    "british stand up comedy full special",
    "irish stand up comedy full show",
    "australian stand up comedy full",
    "canadian stand up comedy full",
    
    # Crowd Work
    "stand up comedy crowd work",
    "comedy crowd work interaction",
    "stand up improvisation crowd",
    
    # Singapore/Malaysia
    "singapore stand up comedy full",
    "malaysian comedy special full",
    "新加坡脱口秀全场笑声",
    "马来西亚华人喜剧 full",
    
    # Indian Comedy
    "indian stand up comedy full netflix",
    "bollywood comedy roast full show",
    "vir das stand up comedy full",
    
    # Clean/Wholesome
    "clean stand up comedy full special",
    "family friendly comedy full show",
    
    # Podcast Comedy
    "comedy podcast full episode stand up",
    "late night comedy monologue full",
]

# ============================================================================
# FAST YOUTUBE SEARCH (no subtitle)
# ============================================================================

def fast_search(query: str, max_results: int = 50) -> List[Dict]:
    """Fast YouTube search - no subtitle download."""
    cmd = [
        'yt-dlp',
        '--cookies-from-browser', 'chrome',
        '--quiet',
        '--no-playlist',
        '--print', '%(id)s|%(duration)s|%(title)s|%(channel)s',
        f'--match-filter', f'duration>300 & duration<5400',  # 5min to 90min
        '--', f'ytsearch{max_results}:{query}'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        videos = []
        for line in result.stdout.strip().split('\n'):
            if '|' not in line:
                continue
            parts = line.split('|')
            if len(parts) >= 3:
                vid = parts[0].strip()
                try:
                    duration = int(parts[1]) if parts[1].isdigit() else 0
                except:
                    duration = 0
                title = parts[2].strip() if len(parts) > 2 else ''
                channel = parts[3].strip() if len(parts) > 3 else ''
                
                # Filter out obvious non-standup
                skip_words = ['reaction', 'react to', 'compilation', 'best of', 
                             'top 10', 'trailer', 'interview', 'podcast', 'vlog']
                if any(w in title.lower() for w in skip_words):
                    continue
                
                videos.append({
                    'video_id': vid,
                    'duration': duration,
                    'title': title,
                    'channel': channel,
                    'query': query,
                    'found_at': datetime.now().isoformat()
                })
        return videos
    except Exception as e:
        print(f"  Search error for '{query}': {e}")
        return []

# ============================================================================
# BATCH SAVE
# ============================================================================

def save_candidates(candidates: List[Dict]):
    """Save candidates to JSONL file."""
    os.makedirs(os.path.dirname(CANDIDATE_FILE), exist_ok=True)
    mode = 'a' if os.path.exists(CANDIDATE_FILE) else 'w'
    with open(CANDIDATE_FILE, mode) as f:
        for c in candidates:
            f.write(json.dumps(c) + '\n')

def load_candidates() -> List[Dict]:
    """Load all candidates."""
    if not os.path.exists(CANDIDATE_FILE):
        return []
    candidates = []
    with open(CANDIDATE_FILE) as f:
        for line in f:
            try:
                candidates.append(json.loads(line.strip()))
            except:
                pass
    return candidates

def get_existing_ids() -> set:
    """Get already-known video IDs."""
    candidates = load_candidates()
    return {c['video_id'] for c in candidates}

# ============================================================================
# PARALLEL SEARCH WORKER
# ============================================================================

def search_worker(worker_id: int, queries: List[str], results_queue: queue.Queue):
    """Worker that searches assigned queries."""
    print(f"[Search-{worker_id}] Starting {len(queries)} queries")
    
    for query in queries:
        videos = fast_search(query, max_results=50)
        results_queue.put(('found', len(videos), query))
        
        # Save immediately
        if videos:
            save_candidates(videos)
        
        print(f"[Search-{worker_id}] '{query[:40]}': {len(videos)} videos")
    
    results_queue.put(('done', worker_id, None))

# ============================================================================
# MAIN - PHASE 1: FAST SEARCH
# ============================================================================

def phase1_fast_search(n_workers: int = 5):
    """Phase 1: Quick YouTube search without subtitle download."""
    print("=" * 70)
    print("PHASE 1: FAST YOUTUBE SEARCH")
    print("=" * 70)
    
    # Check existing
    existing = get_existing_ids()
    print(f"Already have: {len(existing)} videos")
    
    # Split queries
    q_per_worker = len(SEARCH_QUERIES) // n_workers + 1
    query_chunks = []
    for i in range(n_workers):
        start = i * q_per_worker
        query_chunks.append(SEARCH_QUERIES[start:start+q_per_worker])
    
    print(f"Searching with {n_workers} workers...")
    print(f"Total queries: {len(SEARCH_QUERIES)}")
    
    # Start workers
    results_queue = queue.Queue()
    threads = []
    
    for i, queries in enumerate(query_chunks):
        t = threading.Thread(target=search_worker, args=(i, queries, results_queue))
        t.start()
        threads.append(t)
    
    # Wait
    total_found = 0
    for t in threads:
        t.join()
    
    # Final count
    candidates = load_candidates()
    new_ids = {c['video_id'] for c in candidates} - existing
    
    print(f"\nPHASE 1 COMPLETE")
    print(f"  Total candidates: {len(candidates)}")
    print(f"  New videos: {len(new_ids)}")
    print(f"  Saved to: {CANDIDATE_FILE}")

# ============================================================================
# MAIN - PHASE 2: BATCH SUBTITLE CHECK
# ============================================================================

def phase2_subtitle_check(batch_size: int = 100):
    """Phase 2: Batch check subtitles for candidates."""
    print("\n" + "=" * 70)
    print("PHASE 2: BATCH SUBTITLE CHECK")
    print("=" * 70)
    
    candidates = load_candidates()
    print(f"Checking subtitles for {len(candidates)} candidates...")
    
    # Import quality filter
    sys.path.insert(0, '/Users/Subho/autonomous_laughter_prediction/data_collection')
    from quality_filter import VideoQualityScorer, QualityCriteria
    
    scorer = VideoQualityScorer(QualityCriteria(
        min_laughs=10,
        target_laughs=50,
        min_duration=180,
        max_duration=5400,
    ))
    
    # Check in batches
    collected = []
    assessed = 0
    
    for i, video in enumerate(candidates[:batch_size]):
        vid = video['video_id']
        
        # Quick subtitle check
        cmd = [
            'yt-dlp',
            '--cookies-from-browser', 'chrome',
            '--skip-download',
            '--write-sub', '--sub-langs', 'en,eng',
            '--sub-format', 'vtt',
            '--output', f'/tmp/{vid}.%(ext)s',
            '--no-playlist',
            '--', f'https://www.youtube.com/watch?v={vid}'
        ]
        
        try:
            subprocess.run(cmd, capture_output=True, timeout=45)
            
            # Count [laughter] markers
            vtt_files = list(Path('/tmp').glob(f'{vid}*.vtt'))
            laugh_count = 0
            for vtt in vtt_files:
                try:
                    content = vtt.read_text()
                    laugh_count += content.count('[laughter]')
                    vtt.unlink()
                except:
                    pass
            
            video['laugh_count'] = laugh_count
            
            # Assess quality
            should_collect, tier, score, reasons = scorer.should_collect(video)
            video['quality_tier'] = tier
            video['quality_score'] = score
            video['should_collect'] = should_collect
            
            if should_collect:
                collected.append(video)
            
            assessed += 1
            
            if assessed % 10 == 0:
                print(f"  Checked {assessed}/{batch_size}: {len(collected)} to collect")
            
        except Exception as e:
            video['laugh_count'] = 0
            video['quality_tier'] = 'rejected'
        
        if assessed >= batch_size:
            break
    
    print(f"\nPHASE 2 COMPLETE")
    print(f"  Assessed: {assessed}")
    print(f"  Ready to collect: {len(collected)}")
    
    # Save quality-assessed candidates
    with open('/Users/Subho/data/chuckle-net-youtube/assessed_candidates.json', 'w') as f:
        json.dump({
            'assessed': assessed,
            'collected': collected,
            'all_candidates': candidates[:batch_size]
        }, f, indent=2)
    
    return collected

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--phase', type=int, default=1, help='Phase 1 or 2')
    parser.add_argument('--workers', type=int, default=5, help='Parallel workers')
    parser.add_argument('--batch', type=int, default=100, help='Batch size for phase 2')
    args = parser.parse_args()
    
    if args.phase == 1:
        phase1_fast_search(args.workers)
    else:
        phase2_subtitle_check(args.batch)
