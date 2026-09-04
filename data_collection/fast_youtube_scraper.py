#!/usr/bin/env python3
"""
Fast YouTube Video Scraper
==========================
Uses curl to quickly scrape YouTube search results for comedy videos.
Fast - no JavaScript/chrome needed.
"""

import os
import sys
import json
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Set
import threading
import queue

# ============================================================================
# PATHS
# ============================================================================

CANDIDATE_DIR = '/Users/Subho/data/chuckle-net-youtube/candidates'
CANDIDATE_FILE = f'{CANDIDATE_DIR}/all_candidates.jsonl'
CHECKPOINT = f'{CANDIDATE_DIR}/checkpoint.json'

os.makedirs(CANDIDATE_DIR, exist_ok=True)

# ============================================================================
# SEARCH QUERIES (Diverse, high-quality)
# ============================================================================

SEARCH_QUERIES = [
    # US/UK Full Specials
    "stand up comedy full special netflix 2024",
    "comedy central stand up full show",
    "hbo stand up comedy special",
    "british stand up comedy full special",
    "late night comedy monologue full",
    
    # Crowd Work
    "stand up comedy crowd work全场爆笑",
    "comedy crowd work interaction",
    "crowd work stand up netflix",
    
    # Singapore/Malaysia
    "singapore stand up comedy netflix",
    "malaysian comedy special full",
    "新加坡脱口秀全场笑声",
    "kumar stand up comedy singapore",
    
    # Indian English
    "indian stand up comedy full special",
    "vir das stand up comedy full",
    "comedian full show netflix india",
    
    # Clean/Wholesome
    "clean stand up comedy full special",
    "family comedy show full episode",
    
    # Australian/Irish
    "australian stand up comedy full",
    "irish stand up comedy special",
    "canadian comedy full show",
    
    # More specific high-quality
    "bill burr stand up full special",
    "dave chappelle stand up full",
    "ricky gervais stand up full",
    "john mulaney stand up full",
    "bo burnham comedy special full",
]

# ============================================================================
# FAST CURL SCRAPER
# ============================================================================

def scrape_youtube_search(query: str, max_results: int = 50) -> List[Dict]:
    """Scrape YouTube search results using curl."""
    import urllib.parse
    
    encoded_query = urllib.parse.quote(query)
    url = f"https://www.youtube.com/results?search_query={encoded_query}"
    
    headers = [
        '-H', 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        '-H', 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        '-H', 'Accept-Language: en-US,en;q=0.9',
    ]
    
    cmd = ['curl', '-s'] + headers + ['--max-time', '15', '--', url]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        html = result.stdout
        
        # Extract video IDs
        video_ids = []
        import re
        for match in re.findall(r'"videoId":"([^"]+)"', html):
            if match not in video_ids:
                video_ids.append(match)
        
        # Get video details from results
        videos = []
        for vid in video_ids[:max_results]:
            videos.append({
                'video_id': vid,
                'query': query,
                'url': f'https://www.youtube.com/watch?v={vid}',
                'found_at': datetime.now().isoformat()
            })
        
        return videos
        
    except Exception as e:
        return []

def scrape_channel_videos(channel_url: str, max_results: int = 50) -> List[Dict]:
    """Scrape all videos from a YouTube channel."""
    headers = [
        '-H', 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        '-H', 'Accept: text/html,application/xhtml+xml',
    ]
    
    cmd = ['curl', '-s'] + headers + ['--max-time', '15', '--', channel_url]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        html = result.stdout
        
        import re
        video_ids = []
        for match in re.findall(r'"videoId":"([^"]+)"', html):
            if match not in video_ids:
                video_ids.append(match)
        
        videos = []
        for vid in video_ids[:max_results]:
            videos.append({
                'video_id': vid,
                'channel_url': channel_url,
                'url': f'https://www.youtube.com/watch?v={vid}',
                'found_at': datetime.now().isoformat()
            })
        
        return videos
        
    except Exception as e:
        return []

# ============================================================================
# SAVE/LOAD
# ============================================================================

def load_existing_ids() -> Set[str]:
    """Load existing video IDs."""
    if not os.path.exists(CANDIDATE_FILE):
        return set()
    
    ids = set()
    with open(CANDIDATE_FILE) as f:
        for line in f:
            try:
                data = json.loads(line.strip())
                if 'video_id' in data:
                    ids.add(data['video_id'])
            except:
                pass
    return ids

def save_candidates(candidates: List[Dict], existing_ids: Set[str]):
    """Save new candidates to JSONL."""
    new_count = 0
    with open(CANDIDATE_FILE, 'a') as f:
        for c in candidates:
            if c['video_id'] not in existing_ids:
                f.write(json.dumps(c) + '\n')
                existing_ids.add(c['video_id'])
                new_count += 1
    return new_count

# ============================================================================
# PARALLEL SCRAPER
# ============================================================================

def scraper_worker(worker_id: int, queries: List[str], results_queue: queue.Queue):
    """Worker that scrapes assigned queries."""
    existing_ids = load_existing_ids()
    total_new = 0
    
    for query in queries:
        videos = scrape_youtube_search(query, max_results=30)
        new_count = save_candidates(videos, existing_ids)
        total_new += new_count
        
        results_queue.put(('found', new_count, query))
        
        # Rate limit
        time.sleep(0.5)
    
    results_queue.put(('done', worker_id, total_new))

# ============================================================================
# MAIN
# ============================================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Fast YouTube Video Scraper')
    parser.add_argument('--workers', type=int, default=5, help='Parallel workers')
    parser.add_argument('--queries', type=int, default=0, help='Number of queries (0=all)')
    args = parser.parse_args()
    
    print("=" * 70)
    print("FAST YOUTUBE VIDEO SCRAPER")
    print("=" * 70)
    
    # Load existing
    existing_ids = load_existing_ids()
    print(f"Already have: {len(existing_ids)} videos")
    
    # Select queries
    queries = SEARCH_QUERIES[:args.queries] if args.queries > 0 else SEARCH_QUERIES
    print(f"Scraping: {len(queries)} queries")
    
    # Split queries
    q_per_worker = len(queries) // args.workers + 1
    query_chunks = []
    for i in range(args.workers):
        start = i * q_per_worker
        query_chunks.append(queries[start:start+q_per_worker])
    
    # Start workers
    results_queue = queue.Queue()
    threads = []
    
    for i, chunk in enumerate(query_chunks):
        t = threading.Thread(target=scraper_worker, args=(i, chunk, results_queue))
        t.start()
        threads.append(t)
        print(f"Started worker {i}")
    
    # Monitor
    total_found = 0
    start_time = time.time()
    
    while any(t.is_alive() for t in threads):
        time.sleep(2)
        try:
            msg, count, info = results_queue.get_nowait()
            if msg == 'found':
                total_found += count
                elapsed = time.time() - start_time
                rate = total_found / elapsed if elapsed > 0 else 0
                print(f"  Progress: {total_found} new videos ({rate:.1f}/sec) | Last: {info[:40]}")
        except:
            pass
    
    for t in threads:
        t.join()
    
    # Final count
    final_ids = load_existing_ids()
    
    print("\n" + "=" * 70)
    print("SCRAPING COMPLETE")
    print("=" * 70)
    print(f"Total unique videos: {len(final_ids)}")
    print(f"New videos this run: {len(final_ids) - len(existing_ids)}")
    print(f"Saved to: {CANDIDATE_FILE}")

if __name__ == '__main__':
    main()
