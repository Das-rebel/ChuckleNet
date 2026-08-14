#!/usr/bin/env python3
"""
Data Treatment Pipeline - Master Orchestrator
==============================================
Combines all treatment steps: quality filtering, deduplication, normalization, splitting.

Usage:
    python3 data_treatment_pipeline.py \
        --input ./raw/*.jsonl \
        --output-dir ./treated \
        --gold-threshold 0.065 \
        --silver-threshold 0.60

Resume capability:
    python3 data_treatment_pipeline.py --resume --checkpoint-dir ./checkpoints

Author: Subhajit Das (IISER Kolkata)
Date: 2026-06-21
"""

import os
import sys
import json
import argparse
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
import glob


# ============================================================================
# CONFIGURATION
# ============================================================================

BASE_DIR = Path("/Users/Subho/autonomous_laughter_prediction/data/chuckle-net")
DEFAULT_OUTPUT_DIR = BASE_DIR / "treated"
DEFAULT_CHECKPOINT_DIR = BASE_DIR / "checkpoints" / "treatment"

PIPELINE_STAGES = [
    'load',
    'quality_filter',
    'deduplicate_normalize',
    'balanced_split',
    'complete'
]


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class PipelineConfig:
    """Configuration for the treatment pipeline."""
    input_patterns: List[str] = field(default_factory=list)
    output_dir: Path = DEFAULT_OUTPUT_DIR
    checkpoint_dir: Path = DEFAULT_CHECKPOINT_DIR
    
    # Quality filter config
    gold_threshold: float = 0.065
    silver_threshold: float = 0.60
    
    # Split config
    train_ratio: float = 0.70
    val_ratio: float = 0.15
    test_ratio: float = 0.15
    random_seed: int = 42
    
    # Quality tier for source files
    source_quality_tier: Dict[str, str] = field(default_factory=lambda: {
        'youtube': 'silver',
        'standup4ai': 'gold',  # Higher quality curated source
        'multilinguahah': 'silver'
    })


@dataclass
class PipelineStats:
    """Statistics collected during pipeline execution."""
    stage: str = 'init'
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_seconds: float = 0.0
    
    # Load stats
    raw_videos_loaded: int = 0
    by_source: Dict[str, int] = field(default_factory=dict)
    
    # Quality filter stats
    gold_videos: int = 0
    silver_videos: int = 0
    bronze_videos: int = 0
    rejected_videos: int = 0
    
    # Deduplication stats
    total_segments: int = 0
    duplicates_removed: int = 0
    unique_segments: int = 0
    
    # Split stats
    train_count: int = 0
    val_count: int = 0
    test_count: int = 0
    
    # Errors
    errors: List[str] = field(default_factory=list)


@dataclass
class PipelineState:
    """Complete pipeline state for checkpointing."""
    config: Dict[str, Any]
    stage: str
    stats: Dict[str, Any]
    checkpoint_data: Dict[str, Any]  # Stage-specific data
    
    def save(self, checkpoint_dir: Path):
        """Save state to checkpoint directory."""
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        state_file = checkpoint_dir / 'pipeline_state.json'
        with open(state_file, 'w') as f:
            json.dump({
                'config': self.config,
                'stage': self.stage,
                'stats': self.stats,
                'saved_at': datetime.now().isoformat()
            }, f, indent=2, default=str)
        
        # Save stage-specific checkpoint
        if self.checkpoint_data:
            checkpoint_file = checkpoint_dir / f'checkpoint_{self.stage}.json'
            with open(checkpoint_file, 'w') as f:
                json.dump(self.checkpoint_data, f, indent=2, default=str)
    
    @classmethod
    def load(cls, checkpoint_dir: Path) -> Optional['PipelineState']:
        """Load state from checkpoint directory."""
        state_file = checkpoint_dir / 'pipeline_state.json'
        if not state_file.exists():
            return None
        
        with open(state_file, 'r') as f:
            data = json.load(f)
        
        # Load stage-specific checkpoint
        checkpoint_data = {}
        if data['stage'] != 'complete':
            checkpoint_file = checkpoint_dir / f"checkpoint_{data['stage']}.json"
            if checkpoint_file.exists():
                with open(checkpoint_file, 'r') as f:
                    checkpoint_data = json.load(f)
        
        return cls(
            config=data['config'],
            stage=data['stage'],
            stats=data['stats'],
            checkpoint_data=checkpoint_data
        )


# ============================================================================
# PIPELINE STAGES
# ============================================================================

class PipelineStage:
    """Base class for pipeline stages."""
    
    def __init__(self, config: PipelineConfig):
        self.config = config
    
    def execute(self, state: PipelineState) -> Tuple[bool, PipelineState]:
        """Execute stage. Returns (success, updated_state)."""
        raise NotImplementedError


class LoadStage(PipelineStage):
    """Load raw videos from input files."""
    
    def execute(self, state: PipelineState) -> Tuple[bool, PipelineState]:
        print("\n" + "=" * 70)
        print("STAGE 1: LOADING RAW VIDEOS")
        print("=" * 70)
        
        all_files = []
        for pattern in self.config.input_patterns:
            files = glob.glob(pattern)
            all_files.extend(files)
        
        all_files = list(set(all_files))  # Dedupe
        print(f"\nFound {len(all_files)} input files")
        
        all_videos = []
        by_source = defaultdict(int)
        
        for filepath in all_files:
            source = self._infer_source(filepath)
            by_source[source] += 1
            
            # Infer quality tier from source
            quality_tier = self.config.source_quality_tier.get(source, 'silver')
            
            with open(filepath, 'r') as f:
                for line_num, line in enumerate(f):
                    if not line.strip():
                        continue
                    try:
                        video = json.loads(line)
                        video['_source_file'] = str(filepath)
                        video['_source'] = source
                        video['_quality_tier'] = quality_tier
                        all_videos.append(video)
                    except json.JSONDecodeError:
                        continue
            
            print(f"  Loaded {filepath} ({source})")
        
        print(f"\nTotal raw videos loaded: {len(all_videos)}")
        for source, count in sorted(by_source.items()):
            print(f"  {source}: {count}")
        
        # Update state
        state.stats['raw_videos_loaded'] = len(all_videos)
        state.stats['by_source'] = dict(by_source)
        state.checkpoint_data['raw_videos'] = all_videos
        
        return True, state
    
    def _infer_source(self, filepath: str) -> str:
        """Infer source from file path."""
        path_lower = filepath.lower()
        if 'standup4ai' in path_lower or 'standup' in path_lower:
            return 'standup4ai'
        elif 'multi' in path_lower or 'linguahah' in path_lower:
            return 'multilinguahah'
        else:
            return 'youtube'


class QualityFilterStage(PipelineStage):
    """Apply tiered quality filtering."""
    
    def execute(self, state: PipelineState) -> Tuple[bool, PipelineState]:
        print("\n" + "=" * 70)
        print("STAGE 2: TIERED QUALITY FILTERING")
        print("=" * 70)
        
        raw_videos = state.checkpoint_data.get('raw_videos', [])
        print(f"\nFiltering {len(raw_videos)} videos...")
        
        gold = []
        silver = []
        bronze = []
        rejected = []
        
        for video in raw_videos:
            tier = self._score_and_tier(video)
            video['quality_tier'] = tier
            
            if tier == 'gold':
                gold.append(video)
                state.stats['gold_videos'] += 1
            elif tier == 'silver':
                silver.append(video)
                state.stats['silver_videos'] += 1
            elif tier == 'bronze':
                bronze.append(video)
                state.stats['bronze_videos'] += 1
            else:
                rejected.append(video)
                state.stats['rejected_videos'] += 1
        
        print(f"\nQuality filtering results:")
        print(f"  Gold (6.5%): {len(gold)}")
        print(f"  Silver (60%): {len(silver)}")
        print(f"  Bronze: {len(bronze)}")
        print(f"  Rejected: {len(rejected)}")
        
        state.checkpoint_data['gold_videos'] = gold
        state.checkpoint_data['silver_videos'] = silver
        state.checkpoint_data['bronze_videos'] = bronze
        
        return True, state
    
    def _score_and_tier(self, video: Dict) -> str:
        """Score video and determine tier."""
        # Simplified scoring for pipeline
        laugh_markers = video.get('laugh_markers', [])
        duration = video.get('duration', 1)
        subtitle_quality = video.get('subtitle_quality', 0.5)
        audio_quality = video.get('audio_quality', 0.5)
        
        laugh_count = len(laugh_markers)
        laugh_density = (laugh_count / duration) * 60 if duration > 0 else 0
        laughter_rate = min(1.0, laugh_count / max(1, duration // 10))
        
        # Quality score
        quality = (
            min(1.0, laugh_density / 3.0) * 0.4 +
            subtitle_quality * 0.3 +
            audio_quality * 0.3
        )
        
        # Gold: 6.5% laughter rate
        if laughter_rate >= 0.065:
            return 'gold'
        
        # Silver: 60% quality
        if quality >= 0.60:
            return 'silver'
        
        # Bronze: passes minimum bar
        if laugh_count >= 5 and duration >= 180:
            return 'bronze'
        
        return 'rejected'


class DeduplicateNormalizeStage(PipelineStage):
    """Deduplicate and normalize segments."""
    
    def execute(self, state: PipelineState) -> Tuple[bool, PipelineState]:
        print("\n" + "=" * 70)
        print("STAGE 3: DEDUPLICATION AND NORMALIZATION")
        print("=" * 70)
        
        gold = state.checkpoint_data.get('gold_videos', [])
        silver = state.checkpoint_data.get('silver_videos', [])
        
        all_videos = gold + silver
        print(f"\nProcessing {len(all_videos)} gold/silver videos...")
        
        seen_uids = set()
        unique_segments = []
        duplicates = 0
        
        by_language = defaultdict(int)
        
        for video in all_videos:
            source = video.get('_source', 'youtube')
            quality_tier = video.get('quality_tier', 'silver')
            video_id = video.get('video_id', video.get('id', 'unknown'))
            
            # Convert video to segments
            segments = self._video_to_segments(video, source, quality_tier)
            
            for seg in segments:
                uid = seg['uid']
                
                if uid in seen_uids:
                    duplicates += 1
                    continue
                
                seen_uids.add(uid)
                unique_segments.append(seg)
                by_language[seg['language']] += 1
        
        print(f"\nDeduplication results:")
        print(f"  Total segments: {len(seen_uids) + duplicates}")
        print(f"  Duplicates removed: {duplicates}")
        print(f"  Unique segments: {len(unique_segments)}")
        
        print(f"\nBy language:")
        for lang, count in sorted(by_language.items()):
            print(f"  {lang}: {count}")
        
        state.stats['total_segments'] = len(seen_uids) + duplicates
        state.stats['duplicates_removed'] = duplicates
        state.stats['unique_segments'] = len(unique_segments)
        state.checkpoint_data['unique_segments'] = unique_segments
        
        return True, state
    
    def _video_to_segments(self, video: Dict, source: str, quality_tier: str) -> List[Dict]:
        """Convert video to normalized segments."""
        segments = []
        video_id = video.get('video_id', video.get('id', 'unknown'))
        language = video.get('language', 'en')
        comedian_id = video.get('comedian_id', video_id)
        
        # Get words and labels
        words = video.get('words', [])
        labels = video.get('labels', [])
        
        if not words:
            # Create a single segment from the whole video
            return [{
                'uid': f"{source}_{video_id}_000000",
                'source': source,
                'video_id': video_id,
                'language': language,
                'comedian_id': comedian_id,
                'start': 0.0,
                'end': float(video.get('duration', 10)),
                'text': video.get('text', ''),
                'words': words,
                'labels': labels,
                'label': 1 if any(l == 1 for l in labels) else 0,
                'segment_idx': 0,
                'quality_tier': quality_tier
            }]
        
        # Create segments per word (or per N words)
        for idx, (word, label) in enumerate(zip(words, labels)):
            uid = f"{source}_{video_id}_{idx:06d}"
            
            seg = {
                'uid': uid,
                'source': source,
                'video_id': video_id,
                'language': language,
                'comedian_id': comedian_id,
                'start': float(idx * 5),  # Approximate 5s per word
                'end': float((idx + 1) * 5),
                'text': word,
                'words': [word],
                'labels': [label],
                'label': label,
                'segment_idx': idx,
                'quality_tier': quality_tier
            }
            segments.append(seg)
        
        return segments


class BalancedSplitStage(PipelineStage):
    """Create balanced stratified splits."""
    
    def execute(self, state: PipelineState) -> Tuple[bool, PipelineState]:
        print("\n" + "=" * 70)
        print("STAGE 4: BALANCED STRATIFIED SPLITTING")
        print("=" * 70)
        
        segments = state.checkpoint_data.get('unique_segments', [])
        print(f"\nSplitting {len(segments)} unique segments...")
        
        # Group by stratum (language + comedian + tier)
        strata = defaultdict(list)
        for seg in segments:
            key = (seg['language'], seg['comedian_id'], seg['quality_tier'])
            strata[key].append(seg)
        
        print(f"Strata identified: {len(strata)}")
        
        # Assign comedians to splits
        import random
        random.seed(self.config.random_seed)
        
        comedian_splits = {}
        for (lang, comedian, tier), segs in strata.items():
            if comedian not in comedian_splits:
                rand = random.random()
                if rand < self.config.train_ratio:
                    comedian_splits[comedian] = 'train'
                elif rand < self.config.train_ratio + self.config.val_ratio:
                    comedian_splits[comedian] = 'val'
                else:
                    comedian_splits[comedian] = 'test'
        
        # Distribute segments
        train, val, test = [], [], []
        for seg in segments:
            split = comedian_splits.get(seg['comedian_id'], 'train')
            if split == 'train':
                train.append(seg)
            elif split == 'val':
                val.append(seg)
            else:
                test.append(seg)
        
        # Shuffle
        random.shuffle(train)
        random.shuffle(val)
        random.shuffle(test)
        
        print(f"\nSplit results:")
        print(f"  Train: {len(train)} ({len(train)/len(segments)*100:.1f}%)")
        print(f"  Val:   {len(val)} ({len(val)/len(segments)*100:.1f}%)")
        print(f"  Test:  {len(test)} ({len(test)/len(segments)*100:.1f}%)")
        
        # Verify no comedian leakage
        train_comedians = set(s['comedian_id'] for s in train)
        val_comedians = set(s['comedian_id'] for s in val)
        test_comedians = set(s['comedian_id'] for s in test)
        
        overlap = (train_comedians & val_comedians) | (train_comedians & test_comedians) | (val_comedians & test_comedians)
        
        if overlap:
            print(f"\nWARNING: Comedian leakage detected: {len(overlap)} comedians in multiple splits")
        else:
            print(f"\nPASS: No comedian leakage ({len(train_comedians)} train, {len(val_comedians)} val, {len(test_comedians)} test)")
        
        # Update state
        state.stats['train_count'] = len(train)
        state.stats['val_count'] = len(val)
        state.stats['test_count'] = len(test)
        state.checkpoint_data['train'] = train
        state.checkpoint_data['val'] = val
        state.checkpoint_data['test'] = test
        state.checkpoint_data['comedian_splits'] = comedian_splits
        
        return True, state


class OutputStage(PipelineStage):
    """Write final outputs."""
    
    def execute(self, state: PipelineState) -> Tuple[bool, PipelineState]:
        print("\n" + "=" * 70)
        print("STAGE 5: WRITING OUTPUTS")
        print("=" * 70)
        
        output_dir = Path(self.config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Write gold/silver videos
        gold = state.checkpoint_data.get('gold_videos', [])
        silver = state.checkpoint_data.get('silver_videos', [])
        
        with open(output_dir / 'gold_videos.jsonl', 'w') as f:
            for v in gold:
                f.write(json.dumps(v) + '\n')
        print(f"Written {len(gold)} gold videos")
        
        with open(output_dir / 'silver_videos.jsonl', 'w') as f:
            for v in silver:
                f.write(json.dumps(v) + '\n')
        print(f"Written {len(silver)} silver videos")
        
        # Write normalized segments
        segments = state.checkpoint_data.get('unique_segments', [])
        with open(output_dir / 'normalized_segments.jsonl', 'w') as f:
            for s in segments:
                f.write(json.dumps(s) + '\n')
        print(f"Written {len(segments)} normalized segments")
        
        # Write splits
        train = state.checkpoint_data.get('train', [])
        val = state.checkpoint_data.get('val', [])
        test = state.checkpoint_data.get('test', [])
        
        with open(output_dir / 'train.jsonl', 'w') as f:
            for s in train:
                f.write(json.dumps(s) + '\n')
        print(f"Written {len(train)} train segments")
        
        with open(output_dir / 'val.jsonl', 'w') as f:
            for s in val:
                f.write(json.dumps(s) + '\n')
        print(f"Written {len(val)} val segments")
        
        with open(output_dir / 'test.jsonl', 'w') as f:
            for s in test:
                f.write(json.dumps(s) + '\n')
        print(f"Written {len(test)} test segments")
        
        # Write metadata
        metadata = {
            'config': vars(self.config),
            'stats': state.stats,
            'completed_at': datetime.now().isoformat(),
            'comedian_splits': state.checkpoint_data.get('comedian_splits', {})
        }
        
        with open(output_dir / 'treatment_metadata.json', 'w') as f:
            json.dump(metadata, f, indent=2, default=str)
        print(f"Written metadata")
        
        return True, state


# ============================================================================
# MASTER PIPELINE
# ============================================================================

class DataTreatmentPipeline:
    """
    Master pipeline orchestrator.
    
    Combines: Load -> Quality Filter -> Deduplicate/Normalize -> Split -> Output
    """
    
    STAGE_CLASSES = {
        'load': LoadStage,
        'quality_filter': QualityFilterStage,
        'deduplicate_normalize': DeduplicateNormalizeStage,
        'balanced_split': BalancedSplitStage,
        'complete': OutputStage
    }
    
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.state: Optional[PipelineState] = None
        self.stats = PipelineStats()
    
    def run(self, resume: bool = False) -> PipelineState:
        """Run the complete pipeline."""
        print("\n" + "#" * 70)
        print("# DATA TREATMENT PIPELINE")
        print(f"# Started: {datetime.now().isoformat()}")
        print("#" * 70)
        
        # Check for resume
        if resume:
            self.state = PipelineState.load(self.config.checkpoint_dir)
            if self.state:
                print(f"\nResuming from checkpoint: {self.state.stage}")
                print(f"Completed stages: {PIPELINE_STAGES[:PIPELINE_STAGES.index(self.state.stage)]}")
            else:
                print("\nNo checkpoint found, starting fresh")
                self.state = None
        
        # Initialize state if needed
        if self.state is None:
            self.state = PipelineState(
                config=vars(self.config),
                stage='init',
                stats=vars(self.stats),
                checkpoint_data={}
            )
        
        # Run stages
        for stage_name in PIPELINE_STAGES:
            if self.state.stage != 'init' and stage_name != self.state.stage:
                if PIPELINE_STAGES.index(stage_name) <= PIPELINE_STAGES.index(self.state.stage):
                    continue
            
            print(f"\n>>> Executing stage: {stage_name}")
            
            stage_class = self.STAGE_CLASSES.get(stage_name)
            if stage_class is None:
                continue
            
            stage = stage_class(self.config)
            success, self.state = stage.execute(self.state)
            
            self.state.stage = stage_name
            
            if not success:
                print(f"Stage {stage_name} failed!")
                break
            
            # Checkpoint after each stage
            self.state.save(self.config.checkpoint_dir)
            print(f"Checkpoint saved for stage: {stage_name}")
        
        # Mark complete
        self.state.stage = 'complete'
        self.state.stats['completed_at'] = datetime.now().isoformat()
        self.state.save(self.config.checkpoint_dir)
        
        print("\n" + "#" * 70)
        print("# PIPELINE COMPLETE")
        print(f"# Finished: {datetime.now().isoformat()}")
        print("#" * 70)
        
        return self.state
    
    def print_summary(self):
        """Print final summary."""
        print("\n" + "=" * 70)
        print("FINAL SUMMARY")
        print("=" * 70)
        
        stats = self.state.stats if self.state else {}
        
        print(f"\nVideos processed:")
        print(f"  Raw loaded: {stats.get('raw_videos_loaded', 0)}")
        print(f"  Gold tier: {stats.get('gold_videos', 0)}")
        print(f"  Silver tier: {stats.get('silver_videos', 0)}")
        print(f"  Bronze tier: {stats.get('bronze_videos', 0)}")
        print(f"  Rejected: {stats.get('rejected_videos', 0)}")
        
        print(f"\nSegments:")
        print(f"  Total: {stats.get('total_segments', 0)}")
        print(f"  Duplicates: {stats.get('duplicates_removed', 0)}")
        print(f"  Unique: {stats.get('unique_segments', 0)}")
        
        print(f"\nSplits:")
        print(f"  Train: {stats.get('train_count', 0)}")
        print(f"  Val: {stats.get('val_count', 0)}")
        print(f"  Test: {stats.get('test_count', 0)}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='Data Treatment Pipeline')
    parser.add_argument('--input', type=str, nargs='+', required=True,
                       help='Input JSONL files (space-separated or glob)')
    parser.add_argument('--output-dir', type=str, default=str(DEFAULT_OUTPUT_DIR),
                       help='Output directory')
    parser.add_argument('--checkpoint-dir', type=str, default=str(DEFAULT_CHECKPOINT_DIR),
                       help='Checkpoint directory for resume')
    parser.add_argument('--gold-threshold', type=float, default=0.065,
                       help='Gold tier threshold (default: 0.065)')
    parser.add_argument('--silver-threshold', type=float, default=0.60,
                       help='Silver tier threshold (default: 0.60)')
    parser.add_argument('--train-ratio', type=float, default=0.70,
                       help='Train split ratio (default: 0.70)')
    parser.add_argument('--val-ratio', type=float, default=0.15,
                       help='Validation split ratio (default: 0.15)')
    parser.add_argument('--test-ratio', type=float, default=0.15,
                       help='Test split ratio (default: 0.15)')
    parser.add_argument('--seed', type=int, default=42,
                       help='Random seed')
    parser.add_argument('--resume', action='store_true',
                       help='Resume from checkpoint')
    args = parser.parse_args()
    
    # Validate ratios
    total = args.train_ratio + args.val_ratio + args.test_ratio
    if abs(total - 1.0) > 0.001:
        print(f"Error: Ratios must sum to 1.0, got {total}")
        sys.exit(1)
    
    # Create config
    config = PipelineConfig(
        input_patterns=args.input,
        output_dir=Path(args.output_dir),
        checkpoint_dir=Path(args.checkpoint_dir),
        gold_threshold=args.gold_threshold,
        silver_threshold=args.silver_threshold,
        train_ratio=args.train_ratio,
        val_ratio=args.val_ratio,
        test_ratio=args.test_ratio,
        random_seed=args.seed
    )
    
    # Run pipeline
    pipeline = DataTreatmentPipeline(config)
    state = pipeline.run(resume=args.resume)
    
    # Print summary
    pipeline.print_summary()
    
    print(f"\nOutputs written to: {config.output_dir}")


if __name__ == '__main__':
    main()
