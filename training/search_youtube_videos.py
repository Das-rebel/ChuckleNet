#!/usr/bin/env python3
"""
Search YouTube for Indian comedy videos using yt-dlp.

This helps find video URLs for the collection script.
"""

import json
import sys
from pathlib import Path
import subprocess

# Search queries for Indian comedians
SEARCH_QUERIES = {
    'Vir Das': [
        'Vir Das standup comedy full show',
        'Vir Das Netflix special',
        'Vir Das Losing It full show'
    ],
    'Zakir Khan': [
        'Zakir Khan standup comedy full show',
        'Zakir Khan Haq Se Single',
        'Zakir Khan Sakht Launda'
    ],
    'Biswa Kalyan Rath': [
        'Biswa Kalyan Rath standup comedy',
        'Biswa Mast Aadmi full show',
        'Biswa Kalyan Rath Prime Video'
    ],
    'Kaneez Surka': [
        'Kaneez Surka comedy',
        'Kaneez Surka standup'
    ],
    'Atul Khatri': [
        'Atul Khatri standup comedy',
        'Atul Khatri full show'
    ],
    'Mir Afsar Ali': [
        'Mir Afsar Ali Bengali standup',
        'Mir Afsar Ali comedy show Bengali'
    ],
    'Sourav Ghosh': [
        'Sourav Ghosh Bengali standup',
        'Sourav Ghosh comedy'
    ],
    'Rohit Ghosh': [
        'Rohit Ghosh Bengali standup',
        'Rohit Ghosh comedy'
    ],
    'Rajat Chakraborty': [
        'Rajat Chakraborty Bengali standup',
        'Rajat Chakraborty comedy'
    ]
}


def search_youtube(query: str, max_results: int = 5) -> list:
    """
    Search YouTube using yt-dlp and return video URLs.
    
    Returns list of (title, url) tuples.
    """
    cmd = [
        'yt-dlp',
        'ytsearch' + str(max_results) + ':' + query,
        '--get-id',
        '--get-title',
        '--no-warnings'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split('\n')
        
        videos = []
        for i in range(0, len(lines), 2):
            if i + 1 < len(lines):
                title = lines[i].strip()
                video_id = lines[i + 1].strip()
                url = f"https://www.youtube.com/watch?v={video_id}"
                videos.append((title, url))
        
        return videos
    
    except subprocess.CalledProcessError as e:
        print(f"❌ Error searching for '{query}': {e}")
        return []


def search_comedian(comedian: str, max_results: int = 5):
    """Search for all queries for a comedian."""
    queries = SEARCH_QUERIES.get(comedian, [comedian + ' standup comedy'])
    
    all_videos = []
    seen_urls = set()
    
    for query in queries:
        print(f"\n🔍 Searching: {query}")
        videos = search_youtube(query, max_results)
        
        for title, url in videos:
            if url not in seen_urls:
                all_videos.append((title, url))
                seen_urls.add(url)
                print(f"   ✓ {title[:60]}...")
                print(f"     {url}")
    
    return all_videos


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Search YouTube for Indian comedy videos")
    parser.add_argument('--comedian', '-c', type=str, default='all',
                       help="Specific comedian to search (default: all)")
    parser.add_argument('--query', '-q', type=str,
                       help="Custom search query")
    parser.add_argument('--max', '-m', type=int, default=5,
                       help="Max results per query (default: 5)")
    parser.add_argument('--output', '-o', type=str,
                       help="Output JSON file with video URLs")
    parser.add_argument('--list', '-l', action='store_true',
                       help="List available comedians")
    
    args = parser.parse_args()
    
    if args.list:
        print("Available comedians:")
        for comedian in SEARCH_QUERIES.keys():
            print(f"  - {comedian}")
        return
    
    print("=" * 60)
    print("YOUTUBE VIDEO SEARCH")
    print("=" * 60)
    
    all_videos = {}
    
    if args.query:
        # Custom query
        print(f"\n🔍 Custom query: {args.query}")
        videos = search_youtube(args.query, args.max)
        for title, url in videos:
            print(f"   ✓ {title[:60]}...")
            print(f"     {url}")
        
        if args.output:
            all_videos['custom'] = [url for _, url in videos]
    
    elif args.comedian == 'all':
        # Search all comedians
        for comedian in SEARCH_QUERIES.keys():
            print(f"\n{'#'*60}")
            print(f"# {comedian.upper()}")
            print(f"{'#'*60}")
            
            videos = search_comedian(comedian, args.max)
            all_videos[comedian] = [url for _, url in videos]
    
    else:
        # Search specific comedian
        videos = search_comedian(args.comedian, args.max)
        all_videos[args.comedian] = [url for _, url in videos]
    
    # Save to JSON if requested
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(all_videos, f, indent=2)
        
        print(f"\n💾 Saved video URLs to: {output_path}")
        
        # Print summary
        total = sum(len(videos) for videos in all_videos.values())
        print(f"📊 Total videos: {total}")


if __name__ == '__main__':
    main()
