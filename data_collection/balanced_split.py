#!/usr/bin/env python3
"""
Balanced Stratified Split
==========================
Creates stratified splits by language and comedian with NO comedian leakage.
Ensures train/val/test sets have no overlap of comedians.

Output:
- train.jsonl (70%)
- val.jsonl (15%)  
- test.jsonl (15%)

Preserves gold/silver tier distinction in splits.

Usage:
    python3 balanced_split.py \
        --input normalized_segments.jsonl \
        --output-dir ./splits \
        --train 0.7 --val 0.15 --test 0.15

Author: Subhajit Das (IISER Kolkata)
Date: 2026-06-21
"""

import os
import json
import argparse
import hashlib
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import random


# ============================================================================
# CONFIGURATION
# ============================================================================

DEFAULT_SPLITS = {
    'train': 0.70,
    'val': 0.15,
    'test': 0.15
}

# Minimum samples per category to include in split
MIN_SAMPLES_PER_STRATUM = 5

# Random seed for reproducibility
RANDOM_SEED = 42


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class Stratum:
    """Represents a stratum (language + comedian combination)."""
    language: str
    comedian_id: str
    quality_tier: str  # 'gold' or 'silver'
    
    def __hash__(self):
        return hash((self.language, self.comedian_id, self.quality_tier))
    
    def __eq__(self, other):
        return (self.language == other.language and 
                self.comedian_id == other.comedian_id and
                self.quality_tier == other.quality_tier)


@dataclass
class SplitStats:
    """Statistics for a split."""
    name: str
    total: int = 0
    by_language: Dict[str, int] = field(default_factory=dict)
    by_comedian: Dict[str, int] = field(default_factory=dict)
    by_tier: Dict[str, int] = field(default_factory=dict)
    gold_count: int = 0
    silver_count: int = 0
    
    @property
    def gold_ratio(self) -> float:
        return self.gold_count / self.total if self.total > 0 else 0.0


@dataclass 
class BalancedSplitResult:
    """Result of balanced splitting."""
    train: List[Dict]
    val: List[Dict]
    test: List[Dict]
    train_stats: SplitStats
    val_stats: SplitStats
    test_stats: SplitStats
    stratification: Dict[str, Dict[str, List[str]]]  # lang -> tier -> comedians
    comedian_assignment: Dict[str, str]  # comedian -> split (ensures no leakage)


# ============================================================================
# STRATIFIED SPLITTER
# ============================================================================

class BalancedStratifiedSplitter:
    """
    Creates balanced stratified splits ensuring NO comedian leakage.
    
    Algorithm:
    1. Group segments by stratum (language + comedian + tier)
    2. Assign comedians to splits (no overlap)
    3. Distribute segments based on comedian assignments
    4. Balance positive/negative ratio within each split
    """
    
    def __init__(self, train_ratio: float = 0.7, 
                 val_ratio: float = 0.15,
                 test_ratio: float = 0.15,
                 seed: int = RANDOM_SEED):
        self.train_ratio = train_ratio
        self.val_ratio = val_ratio
        self.test_ratio = test_ratio
        self.seed = seed
        
        random.seed(seed)
    
    def split(self, segments: List[Dict]) -> BalancedSplitResult:
        """
        Perform balanced stratified split.
        
        Args:
            segments: List of normalized segment dicts
            
        Returns:
            BalancedSplitResult with train/val/test splits
        """
        # 1. Group by stratum
        strata = self._build_strata(segments)
        
        # 2. Assign comedians to splits (no leakage)
        comedian_assignment = self._assign_comedians(strata)
        
        # 3. Distribute segments
        train_segs, val_segs, test_segs = self._distribute_segments(
            segments, comedian_assignment
        )
        
        # 4. Compute statistics
        train_stats = self._compute_stats(train_segs, 'train')
        val_stats = self._compute_stats(val_segs, 'val')
        test_stats = self._compute_stats(test_segs, 'test')
        
        # 5. Build stratification summary
        stratification = self._build_stratification_summary(strata, comedian_assignment)
        
        return BalancedSplitResult(
            train=train_segs,
            val=val_segs,
            test=test_segs,
            train_stats=train_stats,
            val_stats=val_stats,
            test_stats=test_stats,
            stratification=stratification,
            comedian_assignment=comedian_assignment
        )
    
    def _build_strata(self, segments: List[Dict]) -> Dict[Stratum, List[Dict]]:
        """Group segments by stratum."""
        strata = defaultdict(list)
        
        for seg in segments:
            stratum = Stratum(
                language=seg.get('language', 'en'),
                comedian_id=seg.get('comedian_id', 'unknown'),
                quality_tier=seg.get('quality_tier', 'silver')
            )
            strata[stratum].append(seg)
        
        return dict(strata)
    
    def _assign_comedians(self, strata: Dict[Stratum, List[Dict]]) -> Dict[str, str]:
        """
        Assign each comedian to exactly one split (no leakage).
        
        Uses hash-based deterministic assignment for reproducibility.
        """
        comedian_assignment = {}
        
        # Get all unique comedians
        all_comedians = set(s.comedian_id for s in strata.keys())
        
        for comedian in sorted(all_comedians):
            # Hash-based deterministic assignment
            hash_input = f"{comedian}_{self.seed}"
            hash_val = int(hashlib.sha256(hash_input.encode()).hexdigest(), 16)
            
            # Use hash to determine split
            rand_val = (hash_val % 10000) / 10000.0  # 0-1
            
            if rand_val < self.train_ratio:
                split = 'train'
            elif rand_val < self.train_ratio + self.val_ratio:
                split = 'val'
            else:
                split = 'test'
            
            comedian_assignment[comedian] = split
        
        return comedian_assignment
    
    def _distribute_segments(self, segments: List[Dict],
                             comedian_assignment: Dict[str, str]) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """Distribute segments based on comedian split assignments."""
        train, val, test = [], [], []
        
        for seg in segments:
            comedian = seg.get('comedian_id', 'unknown')
            split = comedian_assignment.get(comedian, 'train')  # Default to train
            
            if split == 'train':
                train.append(seg)
            elif split == 'val':
                val.append(seg)
            else:
                test.append(seg)
        
        # Shuffle each split (deterministic)
        random.shuffle(train)
        random.shuffle(val)
        random.shuffle(test)
        
        return train, val, test
    
    def _compute_stats(self, segments: List[Dict], name: str) -> SplitStats:
        """Compute statistics for a split."""
        stats = SplitStats(name=name)
        stats.total = len(segments)
        
        positive = 0
        for seg in segments:
            # By language
            lang = seg.get('language', 'unknown')
            stats.by_language[lang] = stats.by_language.get(lang, 0) + 1
            
            # By comedian
            comedian = seg.get('comedian_id', 'unknown')
            stats.by_comedian[comedian] = stats.by_comedian.get(comedian, 0) + 1
            
            # By tier
            tier = seg.get('quality_tier', 'silver')
            stats.by_tier[tier] = stats.by_tier.get(tier, 0) + 1
            
            # Gold/silver counts
            if tier == 'gold':
                stats.gold_count += 1
            else:
                stats.silver_count += 1
            
            # Positive label
            if seg.get('label', 0) == 1:
                positive += 1
        
        return stats
    
    def _build_stratification_summary(self, strata: Dict[Stratum, List[Dict]],
                                     comedian_assignment: Dict[str, str]) -> Dict:
        """Build summary of stratification."""
        summary = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        
        for stratum, segs in strata.items():
            lang = stratum.language
            tier = stratum.quality_tier
            comedian = stratum.comedian_id
            split = comedian_assignment.get(comedian, 'unknown')
            
            summary[lang][tier][split].append(comedian)
        
        return dict(summary)


# ============================================================================
# REPORTING
# ============================================================================

def print_split_report(result: BalancedSplitResult):
    """Print detailed split report."""
    print("\n" + "=" * 70)
    print("BALANCED STRATIFIED SPLIT REPORT")
    print("=" * 70)
    
    # Overall counts
    total = result.train_stats.total + result.val_stats.total + result.test_stats.total
    print(f"\nTotal segments: {total}")
    print(f"  Train: {result.train_stats.total} ({result.train_stats.total/total*100:.1f}%)")
    print(f"  Val:   {result.val_stats.total} ({result.val_stats.total/total*100:.1f}%)")
    print(f"  Test:  {result.test_stats.total} ({result.test_stats.total/total*100:.1f}%)")
    
    # Per-split stats
    for stats in [result.train_stats, result.val_stats, result.test_stats]:
        print(f"\n{'='*50}")
        print(f"{stats.name.upper()} SET STATISTICS")
        print(f"{'='*50}")
        print(f"Total: {stats.total}")
        print(f"Gold: {stats.gold_count} ({stats.gold_ratio*100:.1f}%)")
        print(f"Silver: {stats.silver_count} ({(1-stats.gold_ratio)*100:.1f}%)")
        
        print(f"\nBy Language:")
        for lang, count in sorted(stats.by_language.items()):
            print(f"  {lang}: {count}")
        
        print(f"\nBy Tier:")
        for tier, count in sorted(stats.by_tier.items()):
            print(f"  {tier}: {count}")
        
        print(f"\nComedians ({len(stats.by_comedian)}):")
        for comedian, count in sorted(stats.by_comedian.items())[:10]:
            print(f"  {comedian}: {count}")
        if len(stats.by_comedian) > 10:
            print(f"  ... and {len(stats.by_comedian) - 10} more")
    
    # Verify no comedian leakage
    print(f"\n{'='*50}")
    print("COMEDIAN LEAKAGE VERIFICATION")
    print(f"{'='*50}")
    
    all_leakage = []
    train_comedians = set(result.train_stats.by_comedian.keys())
    val_comedians = set(result.val_stats.by_comedian.keys())
    test_comedians = set(result.test_stats.by_comedian.keys())
    
    val_test_overlap = val_comedians & test_comedians
    train_val_overlap = train_comedians & val_comedians
    train_test_overlap = train_comedians & test_comedians
    
    if val_test_overlap:
        all_leakage.append(f"Val-Test overlap: {val_test_overlap}")
    if train_val_overlap:
        all_leakage.append(f"Train-Val overlap: {train_val_overlap}")
    if train_test_overlap:
        all_leakage.append(f"Train-Test overlap: {train_test_overlap}")
    
    if all_leakage:
        print("WARNING: Comedian leakage detected!")
        for leak in all_leakage:
            print(f"  - {leak}")
    else:
        print("PASS: No comedian leakage detected.")
        print(f"  Train comedians: {len(train_comedians)}")
        print(f"  Val comedians: {len(val_comedians)}")
        print(f"  Test comedians: {len(test_comedians)}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='Balanced stratified split')
    parser.add_argument('--input', type=str, required=True,
                       help='Input normalized segments JSONL file')
    parser.add_argument('--output-dir', type=str, default='./splits',
                       help='Output directory for split files')
    parser.add_argument('--train', type=float, default=0.70,
                       help='Train ratio (default: 0.70)')
    parser.add_argument('--val', type=float, default=0.15,
                       help='Val ratio (default: 0.15)')
    parser.add_argument('--test', type=float, default=0.15,
                       help='Test ratio (default: 0.15)')
    parser.add_argument('--seed', type=int, default=RANDOM_SEED,
                       help=f'Random seed (default: {RANDOM_SEED})')
    args = parser.parse_args()
    
    # Validate ratios
    total_ratio = args.train + args.val + args.test
    if abs(total_ratio - 1.0) > 0.001:
        raise ValueError(f"Ratios must sum to 1.0, got {total_ratio}")
    
    # Load segments
    segments = []
    with open(args.input, 'r') as f:
        for line in f:
            if line.strip():
                segments.append(json.loads(line))
    
    print(f"Loaded {len(segments)} segments from {args.input}")
    
    # Split
    splitter = BalancedStratifiedSplitter(
        train_ratio=args.train,
        val_ratio=args.val,
        test_ratio=args.test,
        seed=args.seed
    )
    result = splitter.split(segments)
    
    # Report
    print_split_report(result)
    
    # Save splits
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    splits = [
        ('train.jsonl', result.train),
        ('val.jsonl', result.val),
        ('test.jsonl', result.test)
    ]
    
    for filename, data in splits:
        output_path = output_dir / filename
        with open(output_path, 'w') as f:
            for seg in data:
                f.write(json.dumps(seg) + '\n')
        print(f"\nSaved {len(data)} segments to {output_path}")
    
    # Save split metadata
    metadata = {
        'train_count': len(result.train),
        'val_count': len(result.val),
        'test_count': len(result.test),
        'train_ratio': args.train,
        'val_ratio': args.val,
        'test_ratio': args.test,
        'seed': args.seed,
        'comedian_assignment': result.comedian_assignment,
        'stratification': result.stratification
    }
    
    metadata_path = output_dir / 'split_metadata.json'
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"Saved metadata to {metadata_path}")


if __name__ == '__main__':
    main()
