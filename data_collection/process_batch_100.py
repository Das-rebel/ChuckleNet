#!/usr/bin/env python3
"""Process specific videos to reach 100 total."""

import os
import sys
sys.path.insert(0, '/Users/Subho/autonomous_laughter_prediction/data_collection')

from process_youtube_cpu import process_video, download_audio, download_metadata

TARGETS = [
    'zKUpf1Vx0vs',  # 30 laughs
    'eyC_y-4Fl5A',  # 22 laughs
    'UDLNrYTsdJo',  # 16 laughs
    'eJbn083RQr0',  # 11 laughs
    'FIN-rmn7vVs',  # 7 laughs
    'Hmd49V-XYEs',  # 7 laughs
    'IXTHHUng5xU',  # 7 laughs
    'jmJy-aUgz8Q',  # 5 laughs
    'glMXEpFkH_0',  # 4 laughs
]

def main():
    PROCESSED_DIR = '/Users/Subho/data/chuckle-net-youtube/processed'
    
    # Check what's already done
    done = set(f.replace('.json', '') for f in os.listdir(PROCESSED_DIR) if f.endswith('.json'))
    to_do = [v for v in TARGETS if v not in done]
    
    print(f"Already done: {len(done)}")
    print(f"To process: {len(to_do)}")
    
    for i, vid in enumerate(to_do):
        print(f"\n[{i+1}/{len(to_do)}] Processing {vid}...")
        result = process_video(vid)
        status = result.get('status')
        if status == 'success':
            print(f"  ✓ {vid}: {result.get('n_total')} utt, {result.get('n_positive')} pos")
        else:
            print(f"  ✗ {vid}: {status}")
    
    # Final count
    done_now = set(f.replace('.json', '') for f in os.listdir(PROCESSED_DIR) if f.endswith('.json'))
    print(f"\n=== TOTAL: {len(done_now)} videos processed ===")

if __name__ == '__main__':
    main()
