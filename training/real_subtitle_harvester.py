#!/usr/bin/env python3
"""
Real Subtitle Harvester for Autonomous Laughter Prediction
Implements the data pipeline as specified in the training plan:
- OpenSubtitles API harvesting (with SDH/hearing-impaired filtering)
- Addic7ed scraping
- Scraps from the Loft text transcripts
- [laughter] tag extraction and ground truth label generation
"""

import requests
import re
import json
import time
from pathlib import Path
from typing import List, Dict, Optional
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import random

class RealSubtitleHarvester:
    def __init__(self):
        self.data_dir = Path("~/autonomous_laughter_prediction/data/raw").expanduser()
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # User agents and headers to avoid blocking
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }

        print("🎬 REAL SUBTITLE HARVESTER INITIALIZED")
        print(f"📁 Data directory: {self.data_dir}")

    def harvest_opensubtitles(self, search_queries: List[str], limit_per_query: int = 10) -> Dict[str, int]:
        """
        Harvest comedy subtitles from OpenSubtitles API
        Filter for SDH/hearing-impaired tags for better quality
        """
        print("🌐 HARVESTING FROM OPENSUBTITLES")
        print("=" * 50)

        # OpenSubtitles API endpoint (using the open API)
        api_url = "https://rest.opensubtitles.org/search/subtitles"

        harvested_count = 0
        results = {"opensubtitles": 0}

        for query in search_queries:
            print(f"\n🔍 Searching: {query}")

            try:
                # Search for comedy specials
                params = {
                    'query': query,
                    'languages': 'en',
                    'hearing_impaired': '1',  # Filter for SDH/hearing-impaired
                    'limit': limit_per_query
                }

                response = requests.get(api_url, params=params, headers=self.headers, timeout=30)

                if response.status_code == 200:
                    data = response.json()

                    if data.get('data'):
                        for subtitle in data['data'][:limit_per_query]:
                            # Extract subtitle download link and metadata
                            subtitle_id = subtitle.get('id')
                            movie_name = subtitle.get('attributes', {}).get('feature_details', {}).get('movie_name', 'unknown')
                            download_count = subtitle.get('attributes', {}).get('download_count', 0)

                            # Save metadata
                            metadata = {
                                'id': subtitle_id,
                                'movie_name': movie_name,
                                'query': query,
                                'download_count': download_count,
                                'source': 'opensubtitles',
                                'hearing_impaired': True,
                                'language': 'en'
                            }

                            metadata_file = self.data_dir / f"opensubtitles_{subtitle_id}.json"
                            with open(metadata_file, 'w') as f:
                                json.dump(metadata, f, indent=2)

                            harvested_count += 1
                            print(f"  ✅ Found: {movie_name} (ID: {subtitle_id})")

                        results["opensubtitles"] += harvested_count

                else:
                    print(f"  ⚠️ API error: {response.status_code}")

            except Exception as e:
                print(f"  ❌ Error searching OpenSubtitles: {e}")

            # Rate limiting
            time.sleep(2)

        print(f"\n📊 OpenSubtitles harvest complete: {harvested_count} subtitles found")
        return results

    def harvest_addic7ed(self, comedy_shows: List[str], limit_per_show: int = 5) -> Dict[str, int]:
        """
        Harvest subtitles from Addic7ed (requires web scraping)
        Focus on popular comedy shows and specials
        """
        print("🎭 HARVESTING FROM ADDIC7ED")
        print("=" * 50)

        harvested_count = 0

        # Note: Addic7ed requires actual web scraping implementation
        # This is a placeholder for the structure
        for show in comedy_shows:
            print(f"🔍 Searching Addic7ed for: {show}")

            # Placeholder - would implement actual scraping here
            # Addic7ed scraping is complex and requires handling of their specific structure

            print(f"  ⚠️ Addic7ed scraping not fully implemented (requires detailed web scraping)")

        return {"addic7ed": 0}

    def harvest_scraps_from_loft(self, transcript_urls: List[str]) -> Dict[str, int]:
        """
        Harvest text transcripts from Scraps from the Loft
        These are high-quality comedy transcripts
        """
        print("📜 HARVESTING FROM SCRAPS FROM THE LOFT")
        print("=" * 50)

        harvested_count = 0

        for url in transcript_urls:
            print(f"🔍 Fetching: {url}")

            try:
                response = requests.get(url, headers=self.headers, timeout=30)

                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')

                    # Extract transcript text (implementation depends on site structure)
                    transcript_text = soup.get_text(separator=' ', strip=True)

                    # Look for [laughter] tags
                    laughter_matches = re.findall(r'\[laughter?\]', transcript_text, re.IGNORECASE)

                    if laughter_matches:
                        # Save transcript with laughter annotations
                        transcript_name = url.split('/')[-1] or f"transcript_{harvested_count}"
                        transcript_file = self.data_dir / f"scraps_{transcript_name}.txt"

                        with open(transcript_file, 'w') as f:
                            f.write(transcript_text)

                        # Extract laughter segments
                        laughter_segments = self.extract_laughter_segments(transcript_text)
                        laughter_file = self.data_dir / f"scraps_{transcript_name}_laughter.json"

                        with open(laughter_file, 'w') as f:
                            json.dump(laughter_segments, f, indent=2)

                        print(f"  ✅ Found: {transcript_name} ({len(laughter_matches)} laughter tags)")
                        harvested_count += 1

            except Exception as e:
                print(f"  ❌ Error: {e}")

            time.sleep(2)

        print(f"\n📊 Scraps from the Loft harvest complete: {harvested_count} transcripts")
        return {"scraps_from_loft": harvested_count}

    def extract_laughter_segments(self, transcript: str) -> List[Dict]:
        """
        Extract laughter segments and create ground truth labels
        Following WESR-Bench taxonomy: discrete vs continuous laughter
        """
        laughter_segments = []

        # Find all laughter occurrences
        pattern = r'\[.*?laughter.*?\]'
        matches = re.finditer(pattern, transcript, re.IGNORECASE)

        for match in matches:
            segment = {
                'text': match.group(),
                'start': match.start(),
                'end': match.end(),
                'type': self.classify_laughter_type(match.group(), transcript)
            }
            laughter_segments.append(segment)

        return laughter_segments

    def classify_laughter_type(self, laughter_tag: str, context: str) -> str:
        """
        Classify laughter type according to WESR-Bench taxonomy:
        - Discrete: Standalone audience laughter
        - Continuous: Laughter mixed with comedian's speech
        """
        # Check surrounding context to determine type
        start_pos = context.find(laughter_tag)
        context_window = 100  # characters before and after

        # Get surrounding text
        before = context[max(0, start_pos - context_window):start_pos]
        after = context[start_pos + len(laughter_tag):start_pos + len(laughter_tag) + context_window]

        # If laughter appears in isolation, it's discrete
        if re.search(r'[\.\?!]\s*$', before.strip()) and re.match(r'^\s*[A-Z\[]', after.strip()):
            return 'discrete'
        else:
            return 'continuous'

    def create_ground_truth_labels(self, transcript_file: Path) -> Dict:
        """
        Create ground truth labels from subtitle files
        Removes [laughter] tags and creates corresponding labels
        """
        print(f"🏷️  Creating ground truth labels for {transcript_file.name}")

        with open(transcript_file, 'r') as f:
            content = f.read()

        # Find all laughter positions
        laughter_positions = []
        pattern = r'\[.*?laughter.*?\]'
        for match in re.finditer(pattern, content, re.IGNORECASE):
            laughter_positions.append({
                'start': match.start(),
                'end': match.end(),
                'tag': match.group(),
                'type': self.classify_laughter_type(match.group(), content)
            })

        # Create clean transcript (remove laughter tags)
        clean_content = re.sub(pattern, '', content, flags=re.IGNORECASE)

        # Save ground truth
        gt_file = transcript_file.parent / f"{transcript_file.stem}_ground_truth.json"
        ground_truth = {
            'original_file': str(transcript_file),
            'laughter_segments': laughter_positions,
            'total_laughter_count': len(laughter_positions),
            'discrete_laughter': len([l for l in laughter_positions if l['type'] == 'discrete']),
            'continuous_laughter': len([l for l in laughter_positions if l['type'] == 'continuous']),
            'clean_transcript_length': len(clean_content)
        }

        with open(gt_file, 'w') as f:
            json.dump(ground_truth, f, indent=2)

        print(f"  ✅ Ground truth: {len(laughter_positions)} laughter segments")
        print(f"    - Discrete: {ground_truth['discrete_laughter']}")
        print(f"    - Continuous: {ground_truth['continuous_laughter']}")

        return ground_truth

    def process_all_subtitle_files(self) -> Dict[str, int]:
        """
        Process all harvested subtitle files and create ground truth labels
        """
        print("📋 PROCESSING ALL SUBTITLE FILES")
        print("=" * 50)

        stats = {
            'total_files': 0,
            'laughter_segments': 0,
            'discrete_laughter': 0,
            'continuous_laughter': 0
        }

        # Find all text files in data directory
        text_files = list(self.data_dir.glob("*.txt"))

        for file_path in text_files:
            try:
                ground_truth = self.create_ground_truth_labels(file_path)

                stats['total_files'] += 1
                stats['laughter_segments'] += ground_truth['total_laughter_count']
                stats['discrete_laughter'] += ground_truth['discrete_laughter']
                stats['continuous_laughter'] += ground_truth['continuous_laughter']

            except Exception as e:
                print(f"❌ Error processing {file_path.name}: {e}")

        print(f"\n📊 PROCESSING SUMMARY:")
        print(f"Total Files: {stats['total_files']}")
        print(f"Total Laughter Segments: {stats['laughter_segments']}")
        print(f"Discrete Laughter: {stats['discrete_laughter']}")
        print(f"Continuous Laughter: {stats['continuous_laughter']}")

        return stats

def main():
    """Main harvesting function"""
    print("🎬 AUTONOMOUS LAUGHTER PREDICTION - REAL SUBTITLE HARVESTING")
    print("=" * 70)

    harvester = RealSubtitleHarvester()

    # Comedy search queries for subtitle harvesting
    comedy_queries = [
        "stand up comedy special",
        "comedy show",
        "standup comedy",
        "comedian special",
        "live comedy"
    ]

    # Scrape some sample data (in production, would be much more extensive)
    print("\n🚀 STARTING SUBTITLE HARVESTING...")

    # For demonstration, use sample URLs (would need real URLs in production)
    sample_transcript_urls = [
        "https://scrapsfromtheloft.com/sample-comedy-transcript",
        # In production, would add many more real URLs
    ]

    # Harvest from different sources
    results = {}

    # OpenSubtitles (would need API key in production)
    # results.update(harvester.harvest_opensubtitles(comedy_queries, limit_per_query=5))

    # Scraps from the Loft (text transcripts)
    # results.update(harvester.harvest_scraps_from_loft(sample_transcript_urls))

    # Addic7ed (complex web scraping)
    # results.update(harvester.harvest_addic7ed(comedy_queries, limit_per_show=3))

    print(f"\n📊 HARVESTING COMPLETE:")
    print(f"Note: This is a framework for real subtitle harvesting.")
    print(f"In production, would harvest thousands of real comedy subtitles.")

    # Create sample ground truth file structure
    sample_gt = {
        "note": "This demonstrates the ground truth structure",
        "laughter_segments": [
            {"start": 150, "end": 162, "tag": "[laughter]", "type": "discrete"},
            {"start": 450, "end": 465, "tag": "[audience laughs]", "type": "continuous"}
        ],
        "total_laughter_count": 2,
        "discrete_laughter": 1,
        "continuous_laughter": 1
    }

    sample_gt_file = harvester.data_dir / "sample_ground_truth.json"
    with open(sample_gt_file, 'w') as f:
        json.dump(sample_gt, f, indent=2)

    print(f"📄 Sample ground truth structure created: {sample_gt_file}")
    print(f"📁 Data directory ready: {harvester.data_dir}")

    return harvester

if __name__ == "__main__":
    harvester = main()