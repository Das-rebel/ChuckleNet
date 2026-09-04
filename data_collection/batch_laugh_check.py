#!/usr/bin/env python3
"""
Batch Laughter Checker
=====================
Checks [laughter] markers for many videos using curl (fast).
"""

import os
import sys
import json
import subprocess
import time
import threading
import queue
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# ============================================================================
# PATHS
# ============================================================================

CANDIDATE_FILE = '/Users/Subho/data/chuckle-net-youtube/candidates/all_candidates.jsonl'
QUALITY_FILE = '/Users/Subho/data/chuckle-net-youtube/candidates/quality_assessed.jsonl'
CHECKPOINT = '/Users/Subho/data/chuckle-net-youtube/candidates/checkpoint.json'

# ============================================================================
# QUALITY CRITERIA
# ============================================================================

MIN_LAUGHS = 10
MIN_DURATION = 180  # 3 min
MAX_DURATION = 5400  # 90 min

# ============================================================================
# LOAD/SAVE
# ============================================================================

def load_candidates() -> List[Dict]:
    candidates = []
    with open(CANDIDATE_FILE) as f:
        for line in f:
            try:
                candidates.append(json.loads(line.strip()))
            except:
                pass
    return candidates

def load_checked() -> set:
    if not os.path.exists(QUALITY_FILE):
        return set()
    checked = set()
    with open(QUALITY_FILE) as f:
        for line in f:
            try:
                data = json.loads(line.strip())
                checked.add(data['video_id'])
            except:
                pass
    return checked

def save_result(result: Dict):
    with open(QUALITY_FILE, 'a') as f:
        f.write(json.dumps(result) + '\n')

def save_checkpoint(done: int, total: int):
    with open(CHECKPOINT, 'w') as f:
        json.dump({'done': done, 'total': total, 'time': datetime.now().isoformat()}, f)

# ============================================================================
# GET SUBTITLES VIA CURL
# ============================================================================

def get_subtitle_info(video_id: str) -> Dict:
    """Get subtitle info for a video using curl."""
    # Try to get subtitles via YouTube API or page scrape
    url = f'https://www.youtube.com/watch?v={video_id}'
    
    headers = [
        '-H', 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        '-H', 'Accept: text/html,application/xhtml+xml',
    ]
    
    try:
        # Get video page
        cmd = ['curl', '-s'] + headers + ['--max-time', '10', '--', url]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        html = result.stdout
        
        # Extract caption count hint
        import re
        
        # Look for caption info
        caption_count = 0
        has_captions = 'caption' in html.lower() or 'subtitle' in html.lower()
        
        # Try to find engagement signals (likes, views - indirect laugh signals)
        view_match = re.search(r'"viewCount":"(\d+)"', html)
        like_match = re.search(r'"likeCount":"(\d+)"', html)
        
        views = int(view_match.group(1)) if view_match else 0
        likes = int(like_match.group(1)) if like_match else 0
        
        # Get duration from page
        duration_match = re.search(r'"lengthSeconds":"(\d+)"', html)
        duration = int(duration_match.group(1)) if duration_match else 0
        
        # Get title
        title_match = re.search(r'"title":"([^"]+)"', html)
        title = title_match.group(1)[:100] if title_match else ''
        
        return {
            'video_id': video_id,
            'duration': duration,
            'views': views,
            'likes': likes,
            'has_captions': has_captions,
            'title': title,
            'checked_at': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {'video_id': video_id, 'error': str(e)}

def check_laugh_markers(video_id: str) -> Dict:
    """Check for [laughter] markers in subtitles."""
    # Try to get subtitles via yt-dlp (if available)
    cmd = [
        'curl', '-s', '--max-time', '5',
        f'https://youtubesubtitle.com/get?id={video_id}'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if '[laughter]' in result.stdout.lower():
            return {'video_id': video_id, 'laugh_count': result.stdout.lower().count('[laughter]')}
    except:
        pass
    
    return {'video_id': video_id, 'laugh_count': 0}

# ============================================================================
# QUALITY FILTER
# ============================================================================

def assess_quality(info: Dict) -> Dict:
    """Assess video quality based on available signals."""
    video_id = info['video_id']
    duration = info.get('duration', 0)
    views = info.get('views', 0)
    likes = info.get('likes', 0)
    
    # Indirect laugh signals:
    # - High view-to-like ratio suggests engaging content
    # - Comedy videos with captions often have laughter
    # - Duration in range suggests full specials
    
    score = 0.0
    reasons = []
    
    # Duration check
    if duration > 0:
        if duration < MIN_DURATION:
            score -= 0.5
            reasons.append(f'Too short: {duration}s')
        elif duration > MAX_DURATION:
            score -= 0.3
            reasons.append(f'Too long: {duration}s')
        else:
            score += 0.2
            reasons.append(f'Good duration: {duration}s')
    
    # Caption signal
    if info.get('has_captions'):
        score += 0.3
        reasons.append('Has captions (likely has laughter)')
    
    # Engagement signal
    if views > 100000:
        score += 0.2
        reasons.append(f'Popular: {views//1000}K views')
    
    if likes > 1000:
        score += 0.1
        reasons.append(f'Well-liked: {likes//1000}K likes')
    
    # Determine tier
    if duration >= MIN_DURATION and duration <= MAX_DURATION and info.get('has_captions'):
        tier = 'good'
    elif duration >= MIN_DURATION and duration <= MAX_DURATION:
        tier = 'acceptable'
    elif duration > 0:
        tier = 'low'
    else:
        tier = 'unknown'
    
    return {
        'video_id': video_id,
        'tier': tier,
        'score': min(max(score, 0.0), 1.0),
        'reasons': reasons,
        'duration': duration,
        'views': views,
        'likes': likes,
        'has_captions': info.get('has_captions', False),
        'title': info.get('title', ''),
        'assessed_at': datetime.now().isoformat()
    }

# ============================================================================
# PARALLEL CHECKER
# ============================================================================

def checker_worker(worker_id: int, video_ids: List[str], results_queue: queue.Queue):
    """Worker that checks assigned videos."""
    checked_ids = load_checked()
    
    for i, vid in enumerate(video_ids):
        if vid in checked_ids:
            continue
        
        # Get info
        info = get_subtitle_info(vid)
        
        # Assess quality
        result = assess_quality(info)
        
        # Save
        save_result(result)
        checked_ids.add(vid)
        
        if (i + 1) % 20 == 0:
            results_queue.put(('progress', len(checked_ids), vid))
        
        # Rate limit
        time.sleep(0.3)
    
    results_queue.put(('done', worker_id, len(video_ids)))

# ============================================================================
# MAIN
# ============================================================================

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--workers', type=int, default=5)
    parser.add_argument('--limit', type=int, default=0, help='Limit videos to check (0=all)')
    args = parser.parse_args()
    
    print("=" * 70)
    print("BATCH QUALITY CHECKER")
    print("=" * 70)
    
    # Load candidates
    candidates = load_candidates()
    print(f"Total candidates: {len(candidates)}")
    
    # Load already checked
    checked_ids = load_checked()
    print(f"Already checked: {len(checked_ids)}")
    
    # Filter to unchecked
    unchecked = [c for c in candidates if c['video_id'] not in checked_ids]
    print(f"To check: {len(unchecked)}")
    
    if args.limit > 0:
        unchecked = unchecked[:args.limit]
        print(f"Limited to: {args.limit}")
    
    if not unchecked:
        print("Nothing to check!")
        return
    
    # Split among workers
    vids_per_worker = len(unchecked) // args.workers + 1
    vid_chunks = []
    for i in range(args.workers):
        start = i * vids_per_worker
        vid_chunks.append([c['video_id'] for c in unchecked[start:start+vids_per_worker]])
    
    # Start workers
    results_queue = queue.Queue()
    threads = []
    
    for i, chunk in enumerate(vid_chunks):
        if not chunk:
            continue
        t = threading.Thread(target=checker_worker, args=(i, chunk, results_queue))
        t.start()
        threads.append(t)
        print(f"Started worker {i} with {len(chunk)} videos")
    
    # Monitor
    start_time = time.time()
    last_done = len(checked_ids)
    
    while any(t.is_alive() for t in threads):
        time.sleep(3)
        try:
            msg, count, info = results_queue.get_nowait()
            if msg == 'progress':
                elapsed = time.time() - start_time
                rate = (count - last_done) / 3 if elapsed > 3 else 0
                print(f"  Checked: {count}/{len(unchecked)} ({rate:.1f}/sec)")
                last_done = count
        except:
            pass
    
    for t in threads:
        t.join()
    
    # Final stats
    final_checked = load_checked()
    
    # Count by tier
    tiers = {'excellent': 0, 'good': 0, 'acceptable': 0, 'low': 0, 'unknown': 0}
    with open(QUALITY_FILE) as f:
        for line in f:
            try:
                data = json.loads(line.strip())
                t = data.get('tier', 'unknown')
                if t in tiers:
                    tiers[t] += 1
            except:
                pass
    
    print("\n" + "=" * 70)
    print("QUALITY ASSESSMENT COMPLETE")
    print("=" * 70)
    print(f"Total checked: {len(final_checked)}")
    print("\nQuality distribution:")
    for tier, count in tiers.items():
        print(f"  {tier}: {count}")

if __name__ == '__main__':
    main()
