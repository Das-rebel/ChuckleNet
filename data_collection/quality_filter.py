#!/usr/bin/env python3
"""
High-Quality Video Quality Filter
================================
Strict criteria for selecting laughter-rich comedy videos.
Used to filter candidates before collection/processing.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime
import re

# ============================================================================
# QUALITY CRITERIA
# ============================================================================

@dataclass
class QualityCriteria:
    """Strict quality criteria for video selection."""
    
    # Laugh count thresholds
    min_laughs: int = 10           # Minimum [laughter] markers
    target_laughs: int = 50        # Target for "high quality"
    excellent_laughs: int = 100    # Excellent for model training
    
    # Duration constraints (seconds)
    min_duration: int = 180         # 3 minutes minimum
    max_duration: int = 5400       # 90 minutes maximum
    ideal_min_duration: int = 600   # 10 minutes ideal minimum
    ideal_max_duration: int = 3600   # 60 minutes ideal maximum
    
    # Channel/content filters
    excluded_keywords: List[str] = None
    
    # Quality signals
    min_title_quality_score: float = 0.5
    
    def __post_init__(self):
        if self.excluded_keywords is None:
            self.excluded_keywords = [
                'reaction', 'react to', 'watching', 'compilation',
                'best of', 'top 10', 'funny moments', 'highlights',
                'trailer', 'interview', 'podcast', 'talk show',
                'game show', 'prank', 'vlog', 'shorts'
            ]

# ============================================================================
# QUALITY SCORER
# ============================================================================

class VideoQualityScorer:
    """Scores videos based on quality criteria."""
    
    EXCELLENT = "excellent"      # 100+ laughs, ideal duration
    GOOD = "good"                # 50+ laughs, acceptable duration  
    ACCEPTABLE = "acceptable"    # 10+ laughs, acceptable duration
    LOW = "low"                  # Below threshold
    REJECTED = "rejected"        # Does not meet criteria
    
    def __init__(self, criteria: QualityCriteria = None):
        self.criteria = criteria or QualityCriteria()
    
    def score_video(self, video_info: Dict) -> tuple:
        """
        Score a video and return (quality_tier, score, reasons).
        
        Args:
            video_info: Dict with keys: video_id, title, channel, duration,
                       laugh_count, subtitle_quality, etc.
        
        Returns:
            (tier, score, list_of_reasons)
        """
        score = 0.0
        reasons = []
        video_id = video_info.get('video_id', 'unknown')
        
        # ============ LAUGH COUNT SCORING ============
        laugh_count = video_info.get('laugh_count', 0)
        duration = video_info.get('duration', 0)
        
        if laugh_count >= self.criteria.excellent_laughs:
            score += 0.5
            reasons.append(f"Excellent laugh count: {laugh_count}")
        elif laugh_count >= self.criteria.target_laughs:
            score += 0.35
            reasons.append(f"Good laugh count: {laugh_count}")
        elif laugh_count >= self.criteria.min_laughs:
            score += 0.2
            reasons.append(f"Acceptable laugh count: {laugh_count}")
        elif laugh_count > 0:
            score += 0.05
            reasons.append(f"Low laugh count: {laugh_count}")
        else:
            reasons.append(f"No laughter markers found")
        
        # ============ DURATION SCORING ============
        if duration == 0:
            reasons.append("Unknown duration - might be blocked")
        elif duration < self.criteria.min_duration:
            score -= 0.3
            reasons.append(f"Too short: {duration}s")
        elif duration > self.criteria.max_duration:
            score -= 0.2
            reasons.append(f"Too long: {duration}s")
        elif self.criteria.ideal_min_duration <= duration <= self.criteria.ideal_max_duration:
            score += 0.2
            reasons.append(f"Ideal duration: {duration}s")
        elif duration >= self.criteria.min_duration and duration <= self.criteria.max_duration:
            score += 0.1
            reasons.append(f"Acceptable duration: {duration}s")
        
        # ============ CONTENT QUALITY SCORING ============
        title = video_info.get('title', '').lower()
        channel = video_info.get('channel', '').lower()
        
        # Check for excluded content
        for keyword in self.criteria.excluded_keywords:
            if keyword in title:
                score -= 0.4
                reasons.append(f"Excluded keyword in title: '{keyword}'")
                break
        
        # Check for positive signals
        positive_signals = [
            'stand up', 'stand-up', 'special', 'full show',
            'comedy', 'hour', 'set', 'netflix', 'hbo'
        ]
        
        signal_count = sum(1 for s in positive_signals if s in title)
        score += min(signal_count * 0.05, 0.2)
        
        if signal_count >= 3:
            reasons.append(f"Good content signals: {signal_count}")
        
        # ============ SUBTITLE QUALITY ============
        subtitle_quality = video_info.get('subtitle_quality', 0)
        if subtitle_quality > 0.8:
            score += 0.1
            reasons.append("High subtitle quality")
        elif subtitle_quality < 0.5:
            score -= 0.2
            reasons.append("Low subtitle quality")
        
        # ============ CHANNEL REPUTATION ============
        # Known good channels get a boost
        good_channels = [
            'netflix', 'comedy central', 'hbo', 'netflix comedy',
            'stand up', 'comedy', 'laugh', 'special'
        ]
        
        channel_boost = any(gc in channel for gc in good_channels)
        if channel_boost:
            score += 0.1
            reasons.append("Known comedy channel")
        
        # ============ DETERMINE TIER ============
        if laugh_count >= self.criteria.excellent_laughs and \
           self.criteria.min_duration <= duration <= self.criteria.max_duration:
            tier = self.EXCELLENT
        elif laugh_count >= self.criteria.target_laughs and \
             duration >= self.criteria.min_duration:
            tier = self.GOOD
        elif laugh_count >= self.criteria.min_laughs and \
             duration >= self.criteria.min_duration:
            tier = self.ACCEPTABLE
        elif laugh_count > 0:
            tier = self.LOW
        else:
            tier = self.REJECTED
        
        # Cap score at 1.0
        score = min(max(score, 0.0), 1.0)
        
        return tier, score, reasons
    
    def should_collect(self, video_info: Dict) -> tuple:
        """
        Determine if a video should be collected.
        
        Returns:
            (should_collect, tier, score, reasons)
        """
        tier, score, reasons = self.score_video(video_info)
        
        should_collect = tier in [self.EXCELLENT, self.GOOD, self.ACCEPTABLE]
        
        return should_collect, tier, score, reasons
    
    def filter_batch(self, videos: List[Dict]) -> Dict:
        """
        Filter a batch of videos and return categorized results.
        
        Returns:
            {
                'excellent': [...],
                'good': [...],
                'acceptable': [...],
                'low': [...],
                'rejected': [...],
                'total': N,
                'to_collect': M
            }
        """
        results = {
            'excellent': [],
            'good': [],
            'acceptable': [],
            'low': [],
            'rejected': [],
            'total': len(videos),
            'to_collect_count': 0
        }
        
        for video in videos:
            tier, score, reasons = self.score_video(video)
            video['quality_tier'] = tier
            video['quality_score'] = score
            video['quality_reasons'] = reasons
            video['quality_assessed_at'] = datetime.now().isoformat()
            
            results[tier].append(video)
            
            if tier in [self.EXCELLENT, self.GOOD, self.ACCEPTABLE]:
                results['to_collect_count'] += 1
        
        return results

# ============================================================================
# QUALITY REPORT
# ============================================================================

def print_quality_report(results: Dict):
    """Print a quality assessment report."""
    print("\n" + "=" * 70)
    print("VIDEO QUALITY ASSESSMENT REPORT")
    print("=" * 70)
    
    print(f"\nTotal videos assessed: {results['total']}")
    print(f"Videos to collect: {results['to_collect_count']}")
    
    print(f"\n{'TIER':<15} {'COUNT':<10} {'%':<10}")
    print("-" * 35)
    
    for tier in ['excellent', 'good', 'acceptable', 'low', 'rejected']:
        count = len(results.get(tier, []))
        pct = count / results['total'] * 100 if results['total'] > 0 else 0
        print(f"{tier.upper():<15} {count:<10} {pct:.1f}%")
    
    # Show top excellent videos
    if results['excellent']:
        print(f"\n{'='*70}")
        print("TOP EXCELLENT VIDEOS (100+ laughs)")
        print("="*70)
        for v in sorted(results['excellent'], key=lambda x: -x.get('laugh_count', 0))[:10]:
            print(f"  {v.get('video_id'):<15} {v.get('laugh_count', 0):>5} laughs | {v.get('title', '')[:50]}")
    
    # Show reasons for rejection
    rejected = [v for v in results.get('rejected', []) if v.get('laugh_count', 0) > 0]
    if rejected:
        print(f"\n{'='*70}")
        print(f"REJECTED VIDEOS (with laughs but failed other criteria)")
        print("="*70)
        for v in rejected[:5]:
            print(f"  {v.get('video_id'):<15} {v.get('laugh_count', 0):>5} laughs | {', '.join(v.get('quality_reasons', [])[:2])}")

# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == '__main__':
    # Test with sample data
    scorer = VideoQualityScorer()
    
    test_videos = [
        {
            'video_id': 'ABC123',
            'title': 'Stand Up Comedy Special Full Show - Best of 2024',
            'channel': 'Netflix Comedy',
            'duration': 3600,
            'laugh_count': 150,
            'subtitle_quality': 0.9
        },
        {
            'video_id': 'DEF456',
            'title': 'Comedian Full Special - Netflix',
            'channel': 'Comedy Central',
            'duration': 2700,
            'laugh_count': 75,
            'subtitle_quality': 0.8
        },
        {
            'video_id': 'GHI789',
            'title': 'Funny Compilation - Top 10 Moments',
            'channel': 'Meme Channel',
            'duration': 600,
            'laugh_count': 200,
            'subtitle_quality': 0.3
        },
        {
            'video_id': 'JKL012',
            'title': 'Crowd Work Stand Up Special',
            'channel': 'Comedy Central',
            'duration': 4500,
            'laugh_count': 25,
            'subtitle_quality': 0.7
        },
        {
            'video_id': 'MNO345',
            'title': 'Reaction Video to Stand Up',
            'channel': 'React Channel',
            'duration': 1200,
            'laugh_count': 0,
            'subtitle_quality': 0.0
        },
    ]
    
    results = scorer.filter_batch(test_videos)
    print_quality_report(results)
    
    print("\n\nPER-VIDEO ASSESSMENT:")
    for video in test_videos:
        should, tier, score, reasons = scorer.should_collect(video)
        status = "✅ COLLECT" if should else "❌ SKIP"
        print(f"\n{video['video_id']}: {status}")
        print(f"  Tier: {tier}, Score: {score:.2f}")
        print(f"  Reasons: {reasons}")
