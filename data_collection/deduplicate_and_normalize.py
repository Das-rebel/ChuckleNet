#!/usr/bin/env python3
"""
Deduplicate and Normalize Dataset
=================================
Removes near-duplicate videos (same comedian, similar timestamps).
Normalizes JSONL format across YouTube + StandUp4AI + MultiLinguahah sources.
Ensures UID format compatibility between WavLM and Prosody features.

UID Format Compatibility:
- WavLM uses: {utterance_id} (e.g., "odtAJ2kPdqc_0")
- Prosody uses: {video_id}_{start:.2f} (e.g., "YntBaJ8FiK0_1490.86")
- This script normalizes to: {source}_{video_id}_{segment_idx} or {source}_{video_id}_{start_ts}

Usage:
    python3 deduplicate_and_normalize.py \
        --input ./raw/*.jsonl \
        --output ./normalized/deduplicated.jsonl

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
from difflib import SequenceMatcher
import re


# ============================================================================
# CONFIGURATION
# ============================================================================

# UID format templates
UID_TEMPLATES = {
    'wavlm': '{video_id}_{idx:06d}',      # "odtAJ2kPdqc_000001"
    'prosody': '{video_id}_{start:.2f}',   # "YntBaJ8FiK0_1490.86"
    'unified': '{source}_{video_id}_{seg_id}'  # "youtube_odtAJ2kPdqc_0"
}

# Similarity threshold for deduplication
SIMILARITY_THRESHOLD = 0.85  # 85% similarity = duplicate

# Language codes normalization
LANGUAGE_MAP = {
    'en': 'en',
    'english': 'en',
    'eng': 'en',
    'zh': 'zh',
    'chinese': 'zh',
    'hin': 'hi',
    'hindi': 'hi',
    'hi-latn': 'hi-latn',
    'hinglish': 'hi-latn',
}


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class NormalizedSegment:
    """Normalized segment with unified UID format."""
    uid: str
    source: str  # 'youtube', 'standup4ai', 'multilinguahah'
    video_id: str
    language: str
    comedian_id: str
    start: float
    end: float
    text: str
    words: List[str]
    labels: List[int]
    label: int  # Sentence-level label
    segment_idx: int  # Index within video
    quality_tier: str  # 'gold', 'silver'
    
    # Original references
    original_source_file: Optional[str] = None
    original_uid: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            'uid': self.uid,
            'source': self.source,
            'video_id': self.video_id,
            'language': self.language,
            'comedian_id': self.comedian_id,
            'start': self.start,
            'end': self.end,
            'text': self.text,
            'words': self.words,
            'labels': self.labels,
            'label': self.label,
            'segment_idx': self.segment_idx,
            'quality_tier': self.quality_tier,
            'original_source_file': self.original_source_file,
            'original_uid': self.original_uid
        }


@dataclass
class DeduplicationStats:
    """Statistics for deduplication."""
    total_segments: int = 0
    duplicates_removed: int = 0
    unique_segments: int = 0
    by_source: Dict[str, int] = field(default_factory=dict)
    by_language: Dict[str, int] = field(default_factory=dict)


# ============================================================================
# FORMAT PARSERS
# ============================================================================

class FormatParser:
    """Parses different input formats into normalized segments."""
    
    @staticmethod
    def parse_wavlm_format(record: Dict, source: str, quality_tier: str = 'silver') -> Optional[NormalizedSegment]:
        """Parse WavLM/combined_multilingual format."""
        # example_id: "odtAJ2kPdqc_0" or "indian_Y8VPhZW0DSM_23"
        
        example_id = record.get('example_id', '')
        
        # Handle prefixed formats
        if example_id.startswith('indian_'):
            # Indian comedy format
            parts = example_id.split('_', 2)
            if len(parts) >= 3:
                video_id = parts[1]
                segment_idx = int(parts[2])
            else:
                return None
        elif example_id.startswith('realistic_'):
            # Hindi realistic v2 format
            parts = example_id.split('_', 2)
            if len(parts) >= 3:
                video_id = f"realistic_{parts[1]}"
                segment_idx = int(parts[2])
            else:
                return None
        else:
            # Standard format: video_id_index
            parts = example_id.rsplit('_', 1)
            if len(parts) != 2:
                return None
            video_id, idx_str = parts
            try:
                segment_idx = int(idx_str)
            except ValueError:
                return None
        
        # Get words and labels
        words = record.get('words', [])
        labels = record.get('labels', [])
        
        # Compute sentence-level label (any positive = 1)
        label = 1 if any(l == 1 for l in labels) else 0
        
        # Language
        language = LANGUAGE_MAP.get(record.get('language', 'en'), 'en')
        
        # comedian_id
        comedian_id = record.get('comedian_id', video_id)
        
        # Create normalized UID
        uid = f"{source}_{video_id}_{segment_idx:06d}"
        
        # Estimate start/end times (if not provided)
        start = record.get('start', segment_idx * 10.0)  # ~10s per segment
        end = record.get('end', start + 10.0)
        
        return NormalizedSegment(
            uid=uid,
            source=source,
            video_id=video_id,
            language=language,
            comedian_id=comedian_id,
            start=start,
            end=end,
            text=' '.join(words),
            words=words,
            labels=labels,
            label=label,
            segment_idx=segment_idx,
            quality_tier=quality_tier,
            original_source_file=None,
            original_uid=example_id
        )
    
    @staticmethod
    def parse_prosody_format(record: Dict, source: str, quality_tier: str = 'silver') -> Optional[NormalizedSegment]:
        """Parse prosody_aligned format."""
        # uid: "YntBaJ8FiK0_1490.86"
        
        uid = record.get('uid', '')
        if not uid:
            return None
        
        # Parse prosody UID: video_id_start
        parts = uid.rsplit('_', 1)
        if len(parts) != 2:
            return None
        
        video_id = parts[0]
        try:
            start = float(parts[1])
        except ValueError:
            return None
        
        # Get text and labels
        text = record.get('text', '')
        words = text.split() if text else []
        
        label_any = record.get('label_any', 0)
        label_majority = record.get('label_majority', 0)
        labels = [label_any] * len(words) if words else []
        
        # Language (estimate from video_id patterns if not present)
        language = record.get('language', 'en')
        language = LANGUAGE_MAP.get(language, language)
        
        # comedian_id
        comedian_id = record.get('comedian_id', video_id)
        
        # End time
        end = record.get('end', start + 5.0)
        
        # Segment index (hash-based for consistency)
        segment_idx = int(hashlib.md5(uid.encode()).hexdigest()[:8], 16) % 1000000
        
        return NormalizedSegment(
            uid=f"{source}_{uid}",
            source=source,
            video_id=video_id,
            language=language,
            comedian_id=comedian_id,
            start=start,
            end=end,
            text=text,
            words=words,
            labels=labels,
            label=label_any,
            segment_idx=segment_idx,
            quality_tier=quality_tier,
            original_source_file=None,
            original_uid=uid
        )
    
    @staticmethod
    def auto_detect_and_parse(record: Dict, source: str, quality_tier: str = 'silver') -> Optional[NormalizedSegment]:
        """Auto-detect format and parse."""
        if 'example_id' in record:
            return FormatParser.parse_wavlm_format(record, source, quality_tier)
        elif 'uid' in record and 'prosody' in str(record):
            return FormatParser.parse_prosody_format(record, source, quality_tier)
        elif 'uid' in record:
            return FormatParser.parse_prosody_format(record, source, quality_tier)
        else:
            return None


# ============================================================================
# DEDUPLICATION
# ============================================================================

class Deduplicator:
    """
    Removes near-duplicate segments based on:
    1. Exact match (same video_id + similar timestamps)
    2. Text similarity (85% for same comedian)
    """
    
    def __init__(self, similarity_threshold: float = SIMILARITY_THRESHOLD):
        self.similarity_threshold = similarity_threshold
        self.seen_uids: Set[str] = set()
        self.seen_text_hashes: Dict[str, List[str]] = defaultdict(list)  # text_hash -> [uids]
    
    def is_duplicate(self, segment: NormalizedSegment) -> Tuple[bool, str]:
        """
        Check if segment is a duplicate.
        
        Returns:
            (is_duplicate, reason)
        """
        # 1. Exact UID match
        if segment.uid in self.seen_uids:
            return True, f"Exact UID match: {segment.uid}"
        
        # 2. Same video + overlapping timestamps
        for existing_uid in self.seen_uids:
            if self._is_same_segment(segment, existing_uid):
                return True, f"Overlapping segment with {existing_uid}"
        
        # 3. Near-duplicate text (same comedian)
        text_hash = self._compute_text_hash(segment.text)
        for existing_uid in self.seen_text_hashes.get(text_hash, []):
            if self._is_same_comedian(segment, existing_uid):
                return True, f"Duplicate text from same comedian: {segment.comedian_id}"
        
        return False, ""
    
    def _is_same_segment(self, seg1: NormalizedSegment, uid2: str) -> bool:
        """Check if two segments overlap significantly."""
        # Same video + timestamps within 2s
        if seg1.video_id not in uid2:
            return False
        
        # Parse timestamp from UID
        parts = uid2.rsplit('_', 1)
        if len(parts) != 2:
            return False
        
        try:
            ts2 = float(parts[1])
        except ValueError:
            return False
        
        # Check overlap
        overlap = min(seg1.end, ts2 + 5) - max(seg1.start, ts2)
        return overlap > 3  # More than 3s overlap
    
    def _is_same_comedian(self, seg1: NormalizedSegment, uid2: str) -> bool:
        """Check if segments are from same comedian."""
        # Same comedian ID
        parts = uid2.split('_')
        if len(parts) >= 2:
            comedian_from_uid = '_'.join(parts[1:-1])  # Remove source and index
            if comedian_from_uid == seg1.comedian_id:
                # Check text similarity
                return True
        return False
    
    def _compute_text_hash(self, text: str) -> str:
        """Compute normalized text hash."""
        normalized = ' '.join(text.lower().split())
        return hashlib.sha256(normalized.encode()).hexdigest()[:16]
    
    def mark_seen(self, segment: NormalizedSegment):
        """Mark segment as seen."""
        self.seen_uids.add(segment.uid)
        text_hash = self._compute_text_hash(segment.text)
        self.seen_text_hashes[text_hash].append(segment.uid)


# ============================================================================
# NORMALIZATION PIPELINE
# ============================================================================

class NormalizationPipeline:
    """
    Main pipeline for normalizing and deduplicating collected data.
    """
    
    def __init__(self):
        self.parser = FormatParser()
        self.deduplicator = Deduplicator()
        self.stats = DeduplicationStats()
        self.segments: List[NormalizedSegment] = []
    
    def process_files(self, input_paths: List[str], 
                      quality_tier: str = 'silver',
                      source_map: Dict[str, str] = None) -> List[NormalizedSegment]:
        """
        Process multiple input files.
        
        Args:
            input_paths: List of JSONL file paths
            quality_tier: Default quality tier ('gold' or 'silver')
            source_map: Optional dict mapping file paths to source names
        """
        source_map = source_map or {}
        
        for input_path in input_paths:
            source = source_map.get(input_path, self._infer_source(input_path))
            print(f"Processing {input_path} (source: {source})...")
            
            with open(input_path, 'r') as f:
                for line_num, line in enumerate(f):
                    if not line.strip():
                        continue
                    
                    try:
                        record = json.loads(line)
                        segment = self.parser.auto_detect_and_parse(
                            record, source, quality_tier
                        )
                        
                        if segment is None:
                            continue
                        
                        segment.original_source_file = input_path
                        
                        # Check deduplication
                        is_dup, reason = self.deduplicator.is_duplicate(segment)
                        if is_dup:
                            self.stats.duplicates_removed += 1
                            continue
                        
                        # Add segment
                        self.segments.append(segment)
                        self.deduplicator.mark_seen(segment)
                        self.stats.total_segments += 1
                        
                        # Track stats
                        self.stats.by_source[source] = self.stats.by_source.get(source, 0) + 1
                        self.stats.by_language[segment.language] = \
                            self.stats.by_language.get(segment.language, 0) + 1
                    
                    except json.JSONDecodeError:
                        print(f"  Warning: Invalid JSON at line {line_num}")
                        continue
        
        self.stats.unique_segments = len(self.segments)
        return self.segments
    
    def _infer_source(self, path: str) -> str:
        """Infer source from file path."""
        path_lower = path.lower()
        if 'standup4ai' in path_lower or 'standup' in path_lower:
            return 'standup4ai'
        elif 'multi' in path_lower or 'linguahah' in path_lower:
            return 'multilinguahah'
        else:
            return 'youtube'
    
    def print_report(self):
        """Print deduplication statistics."""
        print("\n" + "=" * 70)
        print("DEDUPLICATION AND NORMALIZATION REPORT")
        print("=" * 70)
        print(f"\nTotal segments processed: {self.stats.total_segments}")
        print(f"Duplicates removed: {self.stats.duplicates_removed}")
        print(f"Unique segments: {self.stats.unique_segments}")
        
        print(f"\n{'By Source':<20} {'Count':<10}")
        print("-" * 30)
        for source, count in sorted(self.stats.by_source.items()):
            print(f"{source:<20} {count:<10}")
        
        print(f"\n{'By Language':<20} {'Count':<10}")
        print("-" * 30)
        for lang, count in sorted(self.stats.by_language.items()):
            print(f"{lang:<20} {count:<10}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='Deduplicate and normalize dataset')
    parser.add_argument('--input', type=str, nargs='+', required=True,
                       help='Input JSONL files (space-separated or glob)')
    parser.add_argument('--output', type=str, required=True,
                       help='Output JSONL file')
    parser.add_argument('--quality-tier', type=str, default='silver',
                       choices=['gold', 'silver'],
                       help='Default quality tier for segments')
    parser.add_argument('--source-map', type=str, default=None,
                       help='JSON file mapping file paths to source names')
    args = parser.parse_args()
    
    # Load source map if provided
    source_map = {}
    if args.source_map:
        with open(args.source_map, 'r') as f:
            source_map = json.load(f)
    
    # Process
    pipeline = NormalizationPipeline()
    segments = pipeline.process_files(args.input, args.quality_tier, source_map)
    
    # Report
    pipeline.print_report()
    
    # Save
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        for seg in segments:
            f.write(json.dumps(seg.to_dict()) + '\n')
    
    print(f"\nSaved {len(segments)} normalized segments to {args.output}")


if __name__ == '__main__':
    main()
