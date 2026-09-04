#!/usr/bin/env python3
"""
Targeted collection for Singaporean/Malaysian Comedy
These have HIGH success rate with YouTube [laughter] markers.
"""

import sys
sys.path.insert(0, '/Users/Subho/autonomous_laughter_prediction/data_collection')

from collect_youtube_fast import (
    search_youtube_videos, 
    extract_subtitles, 
    process_videos_parallel,
    get_gcs_bucket,
    gcs_upload_json,
    gcs_exists
)

# High-value targets (known to have lots of [laughter] markers)
TARGETS = [
    # Kumar - Singapore's top comedian
    {'query': 'Kumar comedian Singapore standup full show', 'comedian': 'Kumar'},
    {'query': 'Kumar comedy special How Was Your Day', 'comedian': 'Kumar'},
    {'query': 'Kumar 2019 comedy full show Netflix', 'comedian': 'Kumar'},
    {'query': 'Kumar comedian Singapore crowd work', 'comedian': 'Kumar'},
    
    # Jack Neo - Singaporean comedy legend
    {'query': 'Jack Neo comedy full show standup', 'comedian': 'Jack Neo'},
    {'query': 'Jack Neo CNB comedy special', 'comedian': 'Jack Neo'},
    
    # Douglas Lim - Malaysian comedian
    {'query': 'Douglas Lim Malaysia standup comedy full', 'comedian': 'Douglas Lim'},
    {'query': 'Douglas Lim Hamiltonian comedy full', 'comedian': 'Douglas Lim'},
    
    # Other Singaporean/Malaysian
    {'query': 'SG Maniacal comedy club full show', 'comedian': 'SG Maniacal'},
    {'query': 'Adib Kucing comedy Singapore full', 'comedian': 'Adib Kucing'},
    {'query': 'Suhaimi Yusof comedy Singapore full', 'comedian': 'Suhaimi'},
    {'query': 'Nadia KB comedy Brunei full', 'comedian': 'Nadia KB'},
    
    # More general Singapore/Malaysia
    {'query': 'Singtel Comedian of the Year full show', 'comedian': 'SOTY'},
    {'query': 'Mediacorp comedy special full show', 'comedian': 'Mediacorp'},
    {'query': 'Singapore standup comedy club full set', 'comedian': 'SG Standup'},
]

def main():
    print("=== Targeted: Singaporean/Malaysian Comedy ===\n")
    
    all_videos = {}
    
    # Search
    for target in TARGETS:
        print(f"Searching: {target['query']}")
        videos = search_youtube_videos(target['query'], max_results=10)
        for v in videos:
            if v['id'] not in all_videos:
                v['target'] = target['comedian']
                all_videos[v['id']] = v
        print(f"  Found {len(videos)} videos, total unique: {len(all_videos)}")
    
    # Filter by duration (3-90 min)
    good_videos = [v for v in all_videos.values() if 180 <= (v.get('duration') or 0) <= 5400]
    print(f"\nTotal good videos (3-90 min): {len(good_videos)}")
    
    # Check which are already in GCS
    bucket = get_gcs_bucket()
    to_process = []
    already_done = 0
    
    for v in good_videos:
        if gcs_exists(f'metadata/{v["id"]}.json'):
            already_done += 1
        else:
            to_process.append(v)
    
    print(f"Already processed: {already_done}")
    print(f"Need to process: {len(to_process)}")
    
    if not to_process:
        print("\nNothing to collect!")
        return
    
    # Process
    print(f"\nProcessing {len(to_process)} videos...")
    results = process_videos_parallel(to_process, max_workers=8)
    
    # Upload successful ones to GCS
    successful = 0
    for r in results:
        result_data = r.get('result')
        if result_data and result_data.get('status') == 'success':
            video_id = r['video_id']
            gcs_path = f'metadata/{video_id}.json'
            if gcs_upload_json(result_data, gcs_path):
                successful += 1
                laughs = result_data.get('laughter_count', 0)
                utts = result_data.get('total_utterances', 0)
                print(f"  ✓ {video_id}: {laughs} laughs, {utts} utts")
            else:
                print(f"  ✗ {video_id}: GCS upload failed")
        else:
            status = result_data.get('status', 'error') if result_data else 'no_result'
            print(f"  ✗ {r.get('video_id', 'unknown')}: {status}")
    
    print(f"\n=== SUMMARY ===")
    print(f"Successful: {successful}/{len(results)}")
    print(f"GCS: gs://chuckle-net-youtube-20260616/metadata/")

if __name__ == '__main__':
    main()
