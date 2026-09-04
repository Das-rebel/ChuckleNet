#!/usr/bin/env python3
"""
Verify Laughter Markers
=======================
Downloads actual subtitles for quality-checked videos to verify
[laughter] markers exist.
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

QUALITY_FILE = '/Users/Subho/data/chuckle-net-youtube/candidates/quality_assessed.jsonl'
VERIFIED_FILE = '/Users/Subho/data/chuckle-net-youtube/candidates/verified_laughter.jsonl'
PROCESSED_DIR = '/Users/Subho/data/chuckle-net-youtube/processed'

os.makedirs(PROCESSED_DIR, exist_ok=True)

# ============================================================================
# QUALITY THRESHOLDS
# ============================================================================

MIN_LAUGHS = 10
MIN_DURATION = 180

# ============================================================================
# LOAD
# ============================================================================

def load_assessed():
    assessed = []
    with open(QUALITY_FILE) as f:
        for line in f:
            try:
                assessed.append(json.loads(line.strip()))
            except:
                pass
    return assessed

def load_verified() -> set:
    verified = set()
    if os.path.exists(VERIFIED_FILE):
        with open(VERIFIED_FILE) as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    verified.add(data['video_id'])
                except:
                    pass
    return verified

def save_verified(result: Dict):
    with open(VERIFIED_FILE, 'a') as f:
        f.write(json.dumps(result) + '\n')

# ============================================================================
# CHECK SUBTITLES VIA YT-DLP
# ============================================================================

def check_subtitle_markers(video_id: str) -> Dict:
    """Download subtitles and count [laughter] markers."""
    output_template = f'/tmp/{video_id}.%(ext)s'
    
    cmd = [
        'yt-dlp',
        '--cookies-from-browser', 'chrome',
        '--skip-download',
        '--write-sub', '--sub-langs', 'en,eng',
        '--sub-format', 'vtt',
        '--output', output_template,
        '--no-playlist',
        '--', f'https://www.youtube.com/watch?v={video_id}'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        # Check downloaded subtitle files
        vtt_files = list(Path('/tmp').glob(f'{video_id}*.vtt'))
        
        laugh_count = 0
        subtitle_text = ''
        
        for vtt in vtt_files:
            try:
                content = vtt.read_text()
                subtitle_text += content
                laugh_count += content.count('[laughter]')
                vtt.unlink()  # Clean up
            except:
                pass
        
        return {
            'video_id': video_id,
            'laugh_count': laugh_count,
            'has_laughter': laugh_count >= MIN_LAUGHS,
            'checked_at': datetime.now().isoformat(),
            'stderr': result.stderr[:500] if result.stderr else ''
        }
        
    except Exception as e:
        return {
            'video_id': video_id,
            'laugh_count': 0,
            'has_laughter': False,
            'error': str(e),
            'checked_at': datetime.now().isoformat()
        }

# ============================================================================
# PARALLEL CHECKER
# ============================================================================

def worker(worker_id: int, video_ids: list, results_queue: queue.Queue):
    """Worker that checks subtitles for assigned videos."""
    verified = load_verified()
    
    for vid in video_ids:
        if vid in verified:
            continue
        
        result = check_subtitle_markers(vid)
        save_verified(result)
        
        if result.get('has_laughter'):
            results_queue.put(('found', vid, result['laugh_count']))
        else:
            results_queue.put(('none', vid, result.get('laugh_count', 0)))
        
        time.sleep(0.5)  # Rate limit
    
    results_queue.put(('done', worker_id, None))

# ============================================================================
# MAIN
# ============================================================================

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--workers', type=int, default=3)
    parser.add_argument('--min-laughs', type=int, default=10)
    args = parser.parse_args()
    
    global MIN_LAUGHS
    MIN_LAUGHS = args.min_laughs
    
    print("=" * 70)
    print("VERIFY LAUGHTER MARKERS")
    print("=" * 70)
    
    # Load assessed
    assessed = load_assessed()
    print(f"Total assessed: {len(assessed)}")
    
    # Filter to "good" tier
    good = [a for a in assessed if a.get('tier') == 'good' and a.get('duration', 0) >= MIN_DURATION]
    print(f"Good videos to verify: {len(good)}")
    
    # Load already verified
    verified = load_verified()
    print(f"Already verified: {len(verified)}")
    
    # Filter to unverified
    to_verify = [v['video_id'] for v in good if v['video_id'] not in verified]
    print(f"To verify: {len(to_verify)}")
    
    if not to_verify:
        print("Nothing to verify!")
        return
    
    # Split among workers
    per_worker = len(to_verify) // args.workers + 1
    chunks = []
    for i in range(args.workers):
        start = i * per_worker
        chunks.append(to_verify[start:start+per_worker])
    
    # Start workers
    results_queue = queue.Queue()
    threads = []
    
    for i, chunk in enumerate(chunks):
        if not chunk:
            continue
        t = threading.Thread(target=worker, args=(i, chunk, results_queue))
        t.start()
        threads.append(t)
        print(f"Started worker {i} with {len(chunk)} videos")
    
    # Monitor
    found_count = 0
    while any(t.is_alive() for t in threads):
        time.sleep(3)
        try:
            msg, vid, count = results_queue.get_nowait()
            if msg == 'found':
                found_count += 1
                print(f"  ✅ {vid}: {count} laughs")
            elif msg == 'none':
                print(f"  ❌ {vid}: {count} laughs")
        except:
            pass
    
    for t in threads:
        t.join()
    
    # Final stats
    verified = load_verified()
    
    # Count by laugh count
    with_laughs = 0
    without_laughs = 0
    
    with open(VERIFIED_FILE) as f:
        for line in f:
            try:
                data = json.loads(line.strip())
                if data.get('has_laughter'):
                    with_laughs += 1
                else:
                    without_laughs += 1
            except:
                pass
    
    print("\n" + "=" * 70)
    print("VERIFICATION COMPLETE")
    print("=" * 70)
    print(f"With 10+ laughs: {with_laughs}")
    print(f"Below threshold: {without_laughs}")
    print(f"Total verified: {with_laughs + without_laughs}")

if __name__ == '__main__':
    main()
