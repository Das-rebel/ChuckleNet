#!/usr/bin/env python3
"""
Batch collection script for Indian comedy data.

This script automates the collection process for multiple comedians
and languages, providing progress tracking and statistics.
"""

import json
import sys
import time
from pathlib import Path
from typing import Dict, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from collect_indian_comedy import (
    extract_video_id,
    process_video,
    save_transcript,
    LANGUAGE_CONFIG,
    COMEDIAN_VIDEOS,
    TRANSCRIPT_DIR,
    AUDIO_DIR
)


class CollectionStats:
    """Track collection statistics."""
    
    def __init__(self):
        self.total_videos = 0
        self.successful = 0
        self.failed = 0
        self.total_words = 0
        self.total_duration = 0
        self.by_language = {}
        self.by_comedian = {}
        self.errors = []
    
    def add_success(self, comedian: str, language: str, word_count: int, duration: float):
        self.successful += 1
        self.total_words += word_count
        self.total_duration += duration
        
        # By language
        if language not in self.by_language:
            self.by_language[language] = {'count': 0, 'words': 0, 'duration': 0}
        self.by_language[language]['count'] += 1
        self.by_language[language]['words'] += word_count
        self.by_language[language]['duration'] += duration
        
        # By comedian
        if comedian not in self.by_comedian:
            self.by_comedian[comedian] = {'count': 0, 'words': 0, 'duration': 0}
        self.by_comedian[comedian]['count'] += 1
        self.by_comedian[comedian]['words'] += word_count
        self.by_comedian[comedian]['duration'] += duration
    
    def add_failure(self, comedian: str, language: str, error: str):
        self.failed += 1
        self.errors.append({
            'comedian': comedian,
            'language': language,
            'error': error,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        })
    
    def print_summary(self):
        """Print collection summary."""
        print(f"\n{'='*70}")
        print("COLLECTION SUMMARY")
        print(f"{'='*70}")
        print(f"Total videos attempted: {self.total_videos}")
        print(f"Successful: {self.successful}")
        print(f"Failed: {self.failed}")
        print(f"Success rate: {self.successful/max(self.total_videos, 1)*100:.1f}%")
        print(f"\nTotal words collected: {self.total_words:,}")
        print(f"Total duration: {self.total_duration/60:.1f} minutes")
        
        if self.by_language:
            print(f"\n{'='*70}")
            print("BY LANGUAGE")
            print(f"{'='*70}")
            for lang, stats in self.by_language.items():
                print(f"{lang}:")
                print(f"  Videos: {stats['count']}")
                print(f"  Words: {stats['words']:,}")
                print(f"  Duration: {stats['duration']/60:.1f} minutes")
        
        if self.by_comedian:
            print(f"\n{'='*70}")
            print("BY COMEDIAN")
            print(f"{'='*70}")
            for comedian, stats in sorted(self.by_comedian.items()):
                print(f"{comedian}:")
                print(f"  Videos: {stats['count']}")
                print(f"  Words: {stats['words']:,}")
                print(f"  Duration: {stats['duration']/60:.1f} minutes")
        
        if self.errors:
            print(f"\n{'='*70}")
            print("ERRORS ({len(self.errors)})")
            print(f"{'='*70}")
            for i, error in enumerate(self.errors[:10], 1):  # Show first 10
                print(f"{i}. {error['comedian']} ({error['language']}): {error['error']}")
            if len(self.errors) > 10:
                print(f"... and {len(self.errors) - 10} more errors")
    
    def save_report(self, output_path: Path):
        """Save detailed report to JSON."""
        report = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'summary': {
                'total_videos': self.total_videos,
                'successful': self.successful,
                'failed': self.failed,
                'success_rate': self.successful/max(self.total_videos, 1)*100,
                'total_words': self.total_words,
                'total_duration_minutes': self.total_duration/60
            },
            'by_language': self.by_language,
            'by_comedian': self.by_comedian,
            'errors': self.errors
        }
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n💾 Report saved to: {output_path}")


def collect_language(language_key: str, comedians: List[str], 
                     strategy: str = 'whisper', stats: CollectionStats = None,
                     max_videos_per_comedian: int = None) -> CollectionStats:
    """
    Collect data for a specific language.
    
    Args:
        language_key: Language key (e.g., 'hindi_hinglish', 'bengali')
        comedians: List of comedians to collect
        strategy: Transcription strategy
        stats: Existing stats object (or create new)
        max_videos_per_comedian: Max videos per comedian (None = all)
    
    Returns:
        CollectionStats object
    """
    if stats is None:
        stats = CollectionStats()
    
    if language_key not in LANGUAGE_CONFIG:
        print(f"❌ Unknown language: {language_key}")
        return stats
    
    lang_config = LANGUAGE_CONFIG[language_key]
    
    print(f"\n{'#'*70}")
    print(f"# COLLECTING: {lang_config['name'].upper()}")
    print(f"{'#'*70}")
    print(f"Language code: {lang_config['code']}")
    print(f"Script: {lang_config['script']}")
    print(f"Comedians: {', '.join(comedians)}")
    print(f"Strategy: {strategy}")
    print(f"{'#'*70}")
    
    for comedian in comedians:
        videos = COMEDIAN_VIDEOS.get(comedian, [])
        
        if not videos:
            print(f"\n⚠️ No videos configured for {comedian}")
            continue
        
        # Limit videos if requested
        if max_videos_per_comedian:
            videos = videos[:max_videos_per_comedian]
        
        print(f"\n🎭 {comedian} ({len(videos)} videos)")
        print(f"   Language: {lang_config['name']}")
        
        for i, video_url in enumerate(videos, 1):
            stats.total_videos += 1
            print(f"\n   [{i}/{len(videos)}] Processing video...")
            
            # Process video
            transcript = process_video(video_url, comedian, lang_config, strategy)
            
            if transcript:
                # Get video ID
                video_id = extract_video_id(video_url)
                
                # Save transcript
                save_transcript(transcript, video_id, comedian, lang_config)
                
                # Calculate stats
                word_count = len(transcript.get('text', '').split())
                
                # Estimate duration
                duration = 0
                if 'segments' in transcript and transcript['segments']:
                    last_segment = transcript['segments'][-1]
                    duration = last_segment.get('end', 0)
                
                stats.add_success(comedian, lang_config['code'], word_count, duration)
                
                print(f"   ✅ Success: {word_count} words, {duration/60:.1f} minutes")
            else:
                stats.add_failure(comedian, lang_config['code'], 'Transcription failed')
                print(f"   ❌ Failed: Transcription failed")
            
            # Rate limiting
            time.sleep(2)
    
    return stats


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Batch collect Indian comedy data")
    parser.add_argument('--language', '-l', type=str, default='all',
                       choices=['all', 'hindi_hinglish', 'bengali'],
                       help="Language to collect (default: all)")
    parser.add_argument('--comedian', '-c', type=str, default='all',
                       help="Specific comedian (default: all)")
    parser.add_argument('--strategy', '-s', type=str, default='whisper',
                       choices=['auto', 'youtube_api', 'whisper'],
                       help="Transcription strategy (default: whisper)")
    parser.add_argument('--max', '-m', type=int,
                       help="Max videos per comedian")
    parser.add_argument('--config', type=str,
                       help="Path to JSON config with video URLs")
    parser.add_argument('--report', '-r', type=str,
                       default='collection_report.json',
                       help="Report output file (default: collection_report.json)")
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("BATCH INDIAN COMEDY COLLECTION")
    print("=" * 70)
    print(f"Language: {args.language}")
    print(f"Comedian: {args.comedian}")
    print(f"Strategy: {args.strategy}")
    if args.max:
        print(f"Max videos per comedian: {args.max}")
    print("=" * 70)
    
    # Load custom config if provided
    if args.config:
        with open(args.config) as f:
            COMEDIAN_VIDEOS.update(json.load(f))
    
    # Create directories
    TRANSCRIPT_DIR.mkdir(parents=True, exist_ok=True)
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    
    # Initialize stats
    stats = CollectionStats()
    
    # Collect by language
    if args.language == 'all':
        # Collect all languages
        for lang_key, lang_config in LANGUAGE_CONFIG.items():
            comedians = lang_config['comedians']
            
            # Filter by comedian if specified
            if args.comedian != 'all':
                if args.comedian in comedians:
                    comedians = [args.comedian]
                else:
                    continue
            
            stats = collect_language(
                lang_key, comedians, args.strategy, stats, args.max
            )
    else:
        # Collect specific language
        lang_config = LANGUAGE_CONFIG[args.language]
        comedians = lang_config['comedians']
        
        # Filter by comedian if specified
        if args.comedian != 'all':
            if args.comedian in comedians:
                comedians = [args.comedian]
            else:
                print(f"❌ Comedian '{args.comedian}' not found in {args.language}")
                return
        
        stats = collect_language(
            args.language, comedians, args.strategy, stats, args.max
        )
    
    # Print and save report
    stats.print_summary()
    stats.save_report(Path(args.report))
    
    # Check targets
    print(f"\n{'='*70}")
    print("TARGET CHECK")
    print(f"{'='*70}")
    
    hindi_words = stats.by_language.get('hi-latn', {}).get('words', 0)
    bengali_words = stats.by_language.get('bn', {}).get('words', 0)
    
    print(f"Hindi/Hinglish target: 1,000+ words")
    print(f"  Current: {hindi_words:,} words")
    print(f"  Status: {'✅ REACHED' if hindi_words >= 1000 else '⚠️ NOT REACHED'}")
    
    print(f"\nBengali target: 500+ words")
    print(f"  Current: {bengali_words:,} words")
    print(f"  Status: {'✅ REACHED' if bengali_words >= 500 else '⚠️ NOT REACHED'}")
    
    print(f"\n{'='*70}")
    if hindi_words >= 1000 and bengali_words >= 500:
        print("🎉 ALL TARGETS REACHED!")
    else:
        print("⚠️ SOME TARGETS NOT REACHED - COLLECT MORE VIDEOS")
    print(f"{'='*70}")


if __name__ == '__main__':
    main()
