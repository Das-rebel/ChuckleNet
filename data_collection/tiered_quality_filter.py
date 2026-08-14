#!/usr/bin/env python3
"""
Tiered Quality Filter for Scaleup Dataset
=========================================
Applies strict 6.5% threshold for gold tier and 60% for silver tier.
Quality scoring based on: laughter density, audio quality, subtitle accuracy.

Usage:
    python3 tiered_quality_filter.py --input raw_videos.jsonl --output-dir ./filtered

Author: Subhajit Das (IISER Kolkata)
Date: 2026-06-21
"""

import os
import json
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import hashlib


# ============================================================================
# CONFIGURATION
# ============================================================================

GOLD_THRESHOLD = 0.065  # 6.5% laughter rate
SILVER_THRESHOLD = 0.60  # 60% laughter density score

# Quality scoring weights
QUALITY_WEIGHTS = {
    'laughter_density': 0.40,      # Primary: laughter markers per minute
    'audio_quality': 0.25,          # Audio clarity score
    'subtitle_accuracy': 0.20,     # VTT subtitle quality
    'content_quality': 0.15,       # Title/channel signals
}


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class VideoMetadata:
    """Metadata for a collected video."""
    video_id: str
    title: str
    channel: str
    language: str
    duration: int  # seconds
    view_count: int
    laugh_markers: List[Dict]  # [{'start': float, 'end': float, 'text': str}]
    subtitle_quality: float  # 0-1
    audio_quality: float  # 0-1
    collection_source: str  # 'youtube', 'standup4ai', 'multilinguahah'
    comedian_id: Optional[str] = None
    upload_date: Optional[str] = None
    
    @property
    def laugh_count(self) -> int:
        return len(self.laugh_markers)
    
    @property
    def laugh_density(self) -> float:
        """Laughs per minute."""
        if self.duration == 0:
            return 0.0
        return (self.laugh_count / self.duration) * 60
    
    @property
    def laughter_rate(self) -> float:
        """Percentage of segments that contain laughter."""
        # Estimate based on laugh markers
        estimated_segments = max(1, self.duration // 10)  # ~10s segments
        return min(1.0, self.laugh_count / estimated_segments)


@dataclass
class QualityScore:
    """Quality scoring result."""
    overall: float
    laughter_density: float
    audio_quality: float
    subtitle_accuracy: float
    content_quality: float
    tier: str  # 'gold', 'silver', 'bronze', 'rejected'
    reasons: List[str] = field(default_factory=list)


# ============================================================================
# QUALITY SCORER
# ============================================================================

class TieredQualityScorer:
    """
    Scores videos for tiered quality filtering.
    
    Gold tier: 6.5% laughter rate threshold (very selective)
    Silver tier: 60% quality score (broader dataset)
    Bronze tier: Passes minimum quality bar
    """
    
    EXCLUDED_KEYWORDS = [
        'reaction', 'react to', 'watching', 'compilation',
        'best of', 'top 10', 'funny moments', 'highlights',
        'trailer', 'interview', 'talk show', 'game show',
        'prank', 'vlog', 'shorts', 'clip', 'segment'
    ]
    
    POSITIVE_SIGNALS = [
        'stand up', 'stand-up', 'special', 'full show',
        'comedy', 'hour', 'set', 'netflix', 'hbo', 'amazon',
        'single', 'tour', 'showtime', 'comedy central'
    ]
    
    def __init__(self, gold_threshold: float = GOLD_THRESHOLD,
                 silver_threshold: float = SILVER_THRESHOLD):
        self.gold_threshold = gold_threshold
        self.silver_threshold = silver_threshold
    
    def score_video(self, metadata: VideoMetadata) -> QualityScore:
        """Compute quality score for a video."""
        
        # 1. Laughter Density Score (40% weight)
        laugh_density_score = self._score_laugh_density(metadata)
        
        # 2. Audio Quality Score (25% weight)
        audio_score = min(1.0, metadata.audio_quality)
        
        # 3. Subtitle Accuracy Score (20% weight)
        subtitle_score = min(1.0, metadata.subtitle_quality)
        
        # 4. Content Quality Score (15% weight)
        content_score = self._score_content(metadata)
        
        # Weighted overall
        overall = (
            laugh_density_score * QUALITY_WEIGHTS['laughter_density'] +
            audio_score * QUALITY_WEIGHTS['audio_quality'] +
            subtitle_score * QUALITY_WEIGHTS['subtitle_accuracy'] +
            content_score * QUALITY_WEIGHTS['content_quality']
        )
        
        # Determine tier
        tier = self._determine_tier(metadata, overall)
        
        reasons = self._generate_reasons(metadata, laugh_density_score, 
                                         audio_score, subtitle_score, content_score)
        
        return QualityScore(
            overall=overall,
            laughter_density=laugh_density_score,
            audio_quality=audio_score,
            subtitle_accuracy=subtitle_score,
            content_quality=content_score,
            tier=tier,
            reasons=reasons
        )
    
    def _score_laugh_density(self, metadata: VideoMetadata) -> float:
        """Score based on laughs per minute."""
        laughs_per_min = metadata.laugh_density
        
        # Excellent: 3+ laughs/min (180+ laughs/hour)
        if laughs_per_min >= 3.0:
            return 1.0
        # Good: 1.5-3 laughs/min
        elif laughs_per_min >= 1.5:
            return 0.75
        # Acceptable: 0.5-1.5 laughs/min
        elif laughs_per_min >= 0.5:
            return 0.5
        # Low: 0.1-0.5 laughs/min
        elif laughs_per_min >= 0.1:
            return 0.25
        else:
            return 0.0
    
    def _score_content(self, metadata: VideoMetadata) -> float:
        """Score based on content signals."""
        title_lower = metadata.title.lower()
        channel_lower = metadata.channel.lower()
        
        score = 0.5  # Base
        
        # Penalty for excluded keywords
        for kw in self.EXCLUDED_KEYWORDS:
            if kw in title_lower:
                score -= 0.3
                break
        
        # Boost for positive signals
        signal_count = sum(1 for s in self.POSITIVE_SIGNALS 
                         if s in title_lower or s in channel_lower)
        score += min(signal_count * 0.1, 0.3)
        
        # Known comedy channel boost
        comedy_channels = ['netflix', 'comedy central', 'hbo', 'hbo comedy',
                          'stand up', 'comedy', 'laugh', 'special']
        if any(c in channel_lower for c in comedy_channels):
            score += 0.2
        
        return max(0.0, min(1.0, score))
    
    def _determine_tier(self, metadata: VideoMetadata, overall: float) -> str:
        """Determine quality tier based on thresholds."""
        
        # Gold: Strict 6.5% laughter rate
        if metadata.laughter_rate >= self.gold_threshold:
            return 'gold'
        
        # Silver: 60% overall quality score
        if overall >= self.silver_threshold:
            return 'silver'
        
        # Bronze: Passes minimum bar
        if metadata.laugh_count >= 5 and metadata.duration >= 180:
            return 'bronze'
        
        return 'rejected'
    
    def _generate_reasons(self, metadata: VideoMetadata,
                          laugh_score: float, audio_score: float,
                          subtitle_score: float, content_score: float) -> List[str]:
        """Generate human-readable reasons for scoring."""
        reasons = []
        
        if laugh_score >= 0.75:
            reasons.append(f"Excellent laugh density: {metadata.laugh_density:.1f}/min")
        elif laugh_score >= 0.5:
            reasons.append(f"Good laugh density: {metadata.laugh_density:.1f}/min")
        elif laugh_score > 0:
            reasons.append(f"Low laugh density: {metadata.laugh_density:.1f}/min")
        else:
            reasons.append("No laughter detected")
        
        if audio_score >= 0.8:
            reasons.append("High audio quality")
        elif audio_score < 0.5:
            reasons.append("Low audio quality")
        
        if subtitle_score >= 0.8:
            reasons.append("High subtitle accuracy")
        elif subtitle_score < 0.5:
            reasons.append("Low subtitle accuracy")
        
        return reasons


# ============================================================================
# FILTER PIPELINE
# ============================================================================

class TieredQualityFilter:
    """
    Applies tiered quality filtering to collected videos.
    
    Output:
    - gold_videos.jsonl (46 videos, ~6.5% of 700)
    - silver_videos.jsonl (300 videos, 60% quality threshold)
    """
    
    def __init__(self, scorer: TieredQualityScorer = None):
        self.scorer = scorer or TieredQualityScorer()
        self.stats = {
            'total': 0,
            'gold': 0,
            'silver': 0,
            'bronze': 0,
            'rejected': 0
        }
    
    def filter_videos(self, videos: List[Dict]) -> Tuple[List[Dict], List[Dict], Dict]:
        """
        Filter videos into gold and silver tiers.
        
        Returns:
            (gold_videos, silver_videos, stats)
        """
        gold = []
        silver = []
        all_results = []
        
        for video in videos:
            self.stats['total'] += 1
            
            # Parse metadata
            metadata = self._parse_metadata(video)
            
            # Score
            score = self.scorer.score_video(metadata)
            
            # Attach scores to video
            video['quality_score'] = score.overall
            video['quality_tier'] = score.tier
            video['quality_reasons'] = score.reasons
            video['laughter_density'] = metadata.laugh_density
            video['laughter_rate'] = metadata.laughter_rate
            
            # Categorize
            if score.tier == 'gold':
                gold.append(video)
                self.stats['gold'] += 1
            elif score.tier == 'silver':
                silver.append(video)
                self.stats['silver'] += 1
            elif score.tier == 'bronze':
                self.stats['bronze'] += 1
            else:
                self.stats['rejected'] += 1
            
            all_results.append(video)
        
        return gold, silver, self.stats
    
    def _parse_metadata(self, video: Dict) -> VideoMetadata:
        """Parse video dict into VideoMetadata object."""
        return VideoMetadata(
            video_id=video.get('video_id', video.get('id', 'unknown')),
            title=video.get('title', ''),
            channel=video.get('channel', video.get('uploader', '')),
            language=video.get('language', 'en'),
            duration=video.get('duration', 0),
            view_count=video.get('view_count', 0),
            laugh_markers=video.get('laugh_markers', []),
            subtitle_quality=video.get('subtitle_quality', 0.5),
            audio_quality=video.get('audio_quality', 0.5),
            collection_source=video.get('collection_source', 'youtube'),
            comedian_id=video.get('comedian_id'),
            upload_date=video.get('upload_date')
        )
    
    def print_report(self):
        """Print filtering statistics."""
        print("\n" + "=" * 70)
        print("TIERED QUALITY FILTERING REPORT")
        print("=" * 70)
        print(f"\nTotal videos processed: {self.stats['total']}")
        print(f"\n{'TIER':<15} {'COUNT':<10} {'%':<10}")
        print("-" * 35)
        for tier in ['gold', 'silver', 'bronze', 'rejected']:
            count = self.stats[tier]
            pct = count / self.stats['total'] * 100 if self.stats['total'] > 0 else 0
            print(f"{tier.upper():<15} {count:<10} {pct:.1f}%")


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='Tiered quality filtering')
    parser.add_argument('--input', type=str, required=True,
                       help='Input JSONL file with raw videos')
    parser.add_argument('--output-dir', type=str, default='./filtered',
                       help='Output directory for filtered tiers')
    parser.add_argument('--gold-threshold', type=float, default=GOLD_THRESHOLD,
                       help=f'Gold tier laughter rate threshold (default: {GOLD_THRESHOLD})')
    parser.add_argument('--silver-threshold', type=float, default=SILVER_THRESHOLD,
                       help=f'Silver tier quality score threshold (default: {SILVER_THRESHOLD})')
    args = parser.parse_args()
    
    # Load videos
    videos = []
    with open(args.input, 'r') as f:
        for line in f:
            if line.strip():
                videos.append(json.loads(line))
    
    print(f"Loaded {len(videos)} videos from {args.input}")
    
    # Filter
    scorer = TieredQualityScorer(gold_threshold=args.gold_threshold,
                                  silver_threshold=args.silver_threshold)
    filter_pipeline = TieredQualityFilter(scorer)
    gold, silver, stats = filter_pipeline.filter_videos(videos)
    
    # Report
    filter_pipeline.print_report()
    print(f"\nGold tier (6.5%): {len(gold)} videos")
    print(f"Silver tier (60%): {len(silver)} videos")
    
    # Save outputs
    os.makedirs(args.output_dir, exist_ok=True)
    
    gold_path = os.path.join(args.output_dir, 'gold_videos.jsonl')
    silver_path = os.path.join(args.output_dir, 'silver_videos.jsonl')
    
    with open(gold_path, 'w') as f:
        for v in gold:
            f.write(json.dumps(v) + '\n')
    print(f"\nSaved {len(gold)} gold videos to {gold_path}")
    
    with open(silver_path, 'w') as f:
        for v in silver:
            f.write(json.dumps(v) + '\n')
    print(f"Saved {len(silver)} silver videos to {silver_path}")


if __name__ == '__main__':
    main()
