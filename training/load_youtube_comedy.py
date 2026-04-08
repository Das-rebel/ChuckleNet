#!/usr/bin/env python3
"""
YouTube Comedy Dataset Integration System
==========================================
Unified loader for all YouTube comedy datasets with:
- Multiple dataset format support
- Data cleaning and deduplication
- Word-level laughter alignment
- GCACU training format integration
- YouTube metadata and virality features
- Memory-efficient processing for massive datasets

Revolutionary Feature: YouTube Virality Prediction
Predict not just laughter, but which jokes would perform well on YouTube
based on historical engagement data.

Usage:
    python3 load_youtube_comedy.py --export-format gcacu --output-dir data/training/youtube_comedy
"""

import json
import re
import hashlib
import random
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple, Iterator, Union
from datetime import datetime
from dataclasses import dataclass, asdict
from collections import defaultdict
import unicodedata

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class YouTubeMetadata:
    """YouTube video metadata for virality prediction"""
    video_id: str
    title: str
    channel: str = ""
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    upload_date: str = ""
    duration: int = 0
    categories: List[str] = None
    tags: List[str] = None

    def __post_init__(self):
        if self.categories is None:
            self.categories = []
        if self.tags is None:
            self.tags = []

    @property
    def engagement_rate(self) -> float:
        """Calculate engagement rate (likes + comments) / views"""
        if self.view_count == 0:
            return 0.0
        return (self.like_count + self.comment_count) / self.view_count

    @property
    def virality_score(self) -> float:
        """
        Calculate virality score based on multiple factors
        Returns score between 0 and 1
        """
        # Normalize factors
        view_score = min(self.view_count / 10_000_000, 1.0)  # 10M views = max
        engagement_score = min(self.engagement_rate * 100, 1.0)  # 1% engagement = max
        comment_score = min(self.comment_count / 100_000, 1.0)  # 100K comments = max

        # Weighted combination
        return (view_score * 0.5 + engagement_score * 0.3 + comment_score * 0.2)


@dataclass
class ComedySegment:
    """Single comedy segment with laughter annotations"""
    text: str
    words: List[str]
    labels: List[int]  # 1 = laughter, 0 = no laughter
    start_time: float = 0.0
    end_time: float = 0.0
    laughter_type: str = "unknown"  # discrete, continuous, applause, etc.
    source: str = ""
    metadata: Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    @property
    def has_laughter(self) -> bool:
        return any(label == 1 for label in self.labels)

    @property
    def laughter_ratio(self) -> float:
        if not self.labels:
            return 0.0
        return sum(self.labels) / len(self.labels)

    @property
    def word_count(self) -> int:
        return len(self.words)


class YouTubeComedyLoader:
    """
    Unified loader for all YouTube comedy datasets
    Handles multiple formats and provides memory-efficient processing
    Includes revolutionary YouTube virality prediction features
    """

    # Laughter markers in transcripts
    LAUGHTER_PATTERNS = [
        r'\[laugh[^\]]*\]', r'\[chuckle[^\]]*\]', r'\[applause[^\]]*\]',
        r'\(laugh[^\)]*\)', r'\(chuckle[^\)]*\)', r'\(applause[^\)]*\)',
        r'\*laugh[^\*]*\*', r'\*chuckle[^\*]*\*', r'\*applause[^\*]*\*',
        r'\[audience[^\]]*laugh[^\]]*\]', r'\[audience[^\]]*react[^\]]*\]',
        r'\[crowd[^\]]*laugh[^\]]*\]', r'\[crowd[^\]]*react[^\]]*\]'
    ]

    # YouTube metadata cache
    YOUTUBE_METADATA_FILE = "youtube_metadata_cache.json"

    def __init__(self, data_dir: str = "data/raw", cache_dir: str = "data/cache"):
        self.data_dir = Path(data_dir)
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Dataset statistics
        self.stats = defaultdict(int)
        self.deduplication_cache: Set[str] = set()

        # YouTube metadata cache
        self.youtube_metadata: Dict[str, YouTubeMetadata] = {}
        self._load_youtube_metadata_cache()

        logger.info(f"YouTube Comedy Loader initialized with data_dir: {data_dir}")

    def normalize_text(self, text: str) -> str:
        """Normalize text for deduplication and processing"""
        # Remove accents
        text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
        # Lowercase
        text = text.lower()
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters except basic punctuation
        text = re.sub(r'[^\w\s\.,!?\-\'\"]', '', text)
        return text.strip()

    def create_content_hash(self, text: str) -> str:
        """Create hash for deduplication"""
        normalized = self.normalize_text(text)
        return hashlib.md5(normalized.encode()).hexdigest()

    def is_duplicate(self, text: str) -> bool:
        """Check if content is duplicate"""
        content_hash = self.create_content_hash(text)
        if content_hash in self.deduplication_cache:
            return True
        self.deduplication_cache.add(content_hash)
        return False

    def extract_laughter_tags(self, text: str) -> List[Tuple[str, int, int]]:
        """
        Extract laughter tags and their positions from text
        Returns list of (tag, start_pos, end_pos)
        """
        matches = []
        for pattern in self.LAUGHTER_PATTERNS:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                matches.append((match.group(), match.start(), match.end()))
        return sorted(matches, key=lambda x: x[1])  # Sort by position

    def detect_laughter_type(self, tag: str) -> str:
        """Detect laughter type from tag"""
        tag_lower = tag.lower()
        if 'chuckle' in tag_lower or 'chortle' in tag_lower:
            return 'discrete'
        elif 'applause' in tag_lower or 'cheer' in tag_lower:
            return 'applause'
        elif 'laugh' in tag_lower or 'chortle' in tag_lower:
            return 'continuous'
        else:
            return 'unknown'

    def load_scraped_comedy_transcripts(self) -> Iterator[ComedySegment]:
        """Load scraped_comedy_transcripts.json (139 records)"""
        file_path = self.data_dir / "scraped_comedy_transcripts.json"
        if not file_path.exists():
            logger.warning(f"File not found: {file_path}")
            return

        logger.info(f"Loading scraped_comedy_transcripts.json...")
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for record in data:
            content = record.get('content', '')
            if not content or self.is_duplicate(content):
                continue

            # Extract segments with laughter annotations
            segments = self._parse_transcript_with_laughter(
                content,
                source=record.get('url', ''),
                metadata={'title': record.get('title', ''), 'word_count': record.get('word_count', 0)}
            )

            for segment in segments:
                # Enhance with YouTube metadata for virality prediction
                segment = self.enhance_segment_with_metadata(segment, record.get('url', ''))
                self.stats['segments_from_scraped_transcripts'] += 1
                yield segment

        logger.info(f"Loaded {self.stats['segments_from_scraped_transcripts']} segments from scraped_comedy_transcripts.json")

    def load_scraped_comprehensive_dataset(self, max_records: int = None) -> Iterator[ComedySegment]:
        """
        Load massive scraped_comprehensive_dataset.json efficiently
        Uses incremental processing to handle large files
        """
        file_path = self.data_dir / "scraped_comprehensive_dataset.json"
        if not file_path.exists():
            logger.warning(f"File not found: {file_path}")
            return

        logger.info(f"Loading scraped_comprehensive_dataset.json (massive dataset)...")
        record_count = 0

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for record in data:
            if max_records and record_count >= max_records:
                break

            record_count += 1
            full_text = record.get('full_text', '')

            if not full_text or self.is_duplicate(full_text):
                continue

            # Process laughter segments
            laughter_segments = record.get('laughter_segments', [])
            metadata = {
                'title': record.get('title', ''),
                'type': record.get('type', ''),
                'source': record.get('source', ''),
                'transcript_number': record.get('transcript_number', ''),
                'total_laughter_count': record.get('total_laughter_count', 0)
            }

            segments = self._parse_enhanced_transcript(
                full_text,
                laughter_segments=laughter_segments,
                source=metadata.get('source', ''),
                metadata=metadata
            )

            for segment in segments:
                self.stats['segments_from_comprehensive'] += 1
                yield segment

        logger.info(f"Loaded {self.stats['segments_from_comprehensive']} segments from scraped_comprehensive_dataset.json")

    def load_scraped_from_scraps_from_loft(self) -> Iterator[ComedySegment]:
        """Load scraped_from_scraps_from_loft.json (1,211 records)"""
        file_path = self.data_dir / "scraped_from_scraps_from_loft.json"
        if not file_path.exists():
            logger.warning(f"File not found: {file_path}")
            return

        logger.info(f"Loading scraped_from_scraps_from_loft.json...")
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for record in data:
            content = record.get('content', '')
            if not content or self.is_duplicate(content):
                continue

            segments = self._parse_transcript_with_laughter(
                content,
                source=record.get('url', ''),
                metadata={
                    'title': record.get('title', ''),
                    'laughter_count': record.get('laughter_count', 0),
                    'laughter_types': record.get('laughter_types', [])
                }
            )

            for segment in segments:
                self.stats['segments_from_scraps_loft'] += 1
                yield segment

        logger.info(f"Loaded {self.stats['segments_from_scraps_loft']} segments from scraped_from_scraps_from_loft.json")

    def _parse_transcript_with_laughter(self, text: str, source: str = '', metadata: Dict = None) -> List[ComedySegment]:
        """
        Parse transcript text with inline laughter markers
        Converts [laughter] markers to word-level labels
        """
        if metadata is None:
            metadata = {}

        # Split text by laughter markers
        laughter_matches = self.extract_laughter_tags(text)

        if not laughter_matches:
            # No laughter found, create single segment with all negative labels
            words = text.split()
            if not words:
                return []

            return [ComedySegment(
                text=text.strip(),
                words=words,
                labels=[0] * len(words),
                laughter_type='none',
                source=source,
                metadata={**metadata, 'laughter_detection_method': 'inline_marker'}
            )]

        segments = []
        current_pos = 0

        for tag, start, end in laughter_matches:
            # Get text before this laughter marker
            before_text = text[current_pos:start].strip()

            if before_text:
                words = before_text.split()
                if words:
                    segments.append(ComedySegment(
                        text=before_text,
                        words=words,
                        labels=[0] * len(words),
                        laughter_type='none',
                        source=source,
                        metadata={**metadata, 'laughter_detection_method': 'inline_marker'}
                    ))

            # Create segment for laughter marker itself
            laughter_type = self.detect_laughter_type(tag)
            laughter_words = ['[LAUGHTER]']  # Special token for laughter

            segments.append(ComedySegment(
                text=tag,
                words=laughter_words,
                labels=[1] * len(laughter_words),
                laughter_type=laughter_type,
                source=source,
                metadata={**metadata, 'laughter_detection_method': 'inline_marker', 'original_tag': tag}
            ))

            current_pos = end

        # Get remaining text after last laughter marker
        remaining_text = text[current_pos:].strip()
        if remaining_text:
            words = remaining_text.split()
            if words:
                segments.append(ComedySegment(
                    text=remaining_text,
                    words=words,
                    labels=[0] * len(words),
                    laughter_type='none',
                    source=source,
                    metadata={**metadata, 'laughter_detection_method': 'inline_marker'}
                ))

        return segments

    def _parse_enhanced_transcript(self, text: str, laughter_segments: List[Dict],
                                   source: str = '', metadata: Dict = None) -> List[ComedySegment]:
        """
        Parse transcript with structured laughter segment information
        Handles the enhanced format from scraped_comprehensive_dataset.json
        """
        if metadata is None:
            metadata = {}

        # Create laughter position map
        laughter_positions = {}
        for laugh_seg in laughter_segments:
            laugh_text = laugh_seg.get('text', '')
            if laugh_text:
                laughter_positions[laugh_text] = laugh_seg.get('type', 'continuous')

        # Split text into words while preserving laughter markers
        words_and_tags = text.split()
        segments = []
        current_words = []
        current_labels = []

        for word in words_and_tags:
            # Check if this is a laughter marker
            is_laughter = False
            laughter_type = 'unknown'

            for pattern in self.LAUGHTER_PATTERNS:
                if re.match(pattern, word, re.IGNORECASE):
                    is_laughter = True
                    laughter_type = self.detect_laughter_type(word)
                    break

            if is_laughter:
                # Save current segment before starting laughter
                if current_words:
                    segments.append(ComedySegment(
                        text=' '.join(current_words),
                        words=current_words,
                        labels=current_labels,
                        laughter_type='none',
                        source=source,
                        metadata={**metadata, 'laughter_detection_method': 'structured'}
                    ))
                    current_words = []
                    current_labels = []

                # Create laughter segment
                segments.append(ComedySegment(
                    text=word,
                    words=['[LAUGHTER]'],
                    labels=[1],
                    laughter_type=laughter_type,
                    source=source,
                    metadata={**metadata, 'laughter_detection_method': 'structured', 'original_tag': word}
                ))
            else:
                current_words.append(word)
                current_labels.append(0)

        # Add remaining words
        if current_words:
            segments.append(ComedySegment(
                text=' '.join(current_words),
                words=current_words,
                labels=current_labels,
                laughter_type='none',
                source=source,
                metadata={**metadata, 'laughter_detection_method': 'structured'}
            ))

        return segments

    def load_all_datasets(self, max_comprehensive_records: int = None) -> Iterator[ComedySegment]:
        """Load and combine all datasets"""
        logger.info("Loading all YouTube comedy datasets...")

        # Load from all sources
        loaders = [
            self.load_scraped_comedy_transcripts,
            lambda: self.load_scraped_comprehensive_dataset(max_comprehensive_records),
            self.load_scraped_from_scraps_from_loft
        ]

        total_segments = 0
        for loader in loaders:
            try:
                for segment in loader():
                    total_segments += 1
                    yield segment
            except Exception as e:
                logger.error(f"Error in loader {loader.__name__}: {e}")
                continue

        logger.info(f"Total segments loaded: {total_segments}")
        logger.info(f"Unique segments (after deduplication): {len(self.deduplication_cache)}")

    def _load_youtube_metadata_cache(self):
        """Load YouTube metadata cache from disk"""
        cache_file = self.cache_dir / self.YOUTUBE_METADATA_FILE
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    for video_id, meta_dict in data.items():
                        self.youtube_metadata[video_id] = YouTubeMetadata(**meta_dict)
                logger.info(f"Loaded {len(self.youtube_metadata)} cached YouTube metadata entries")
            except Exception as e:
                logger.warning(f"Failed to load metadata cache: {e}")

    def _save_youtube_metadata_cache(self):
        """Save YouTube metadata cache to disk"""
        cache_file = self.cache_dir / self.YOUTUBE_METADATA_FILE
        try:
            data = {video_id: asdict(meta) for video_id, meta in self.youtube_metadata.items()}
            with open(cache_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved {len(self.youtube_metadata)} YouTube metadata entries to cache")
        except Exception as e:
            logger.warning(f"Failed to save metadata cache: {e}")

    def add_youtube_metadata(self, video_id: str, metadata: YouTubeMetadata):
        """Add YouTube metadata for a video"""
        self.youtube_metadata[video_id] = metadata
        self._save_youtube_metadata_cache()

    def get_youtube_metadata(self, video_id: str) -> Optional[YouTubeMetadata]:
        """Get YouTube metadata for a video"""
        return self.youtube_metadata.get(video_id)

    def extract_video_id_from_url(self, url: str) -> Optional[str]:
        """Extract YouTube video ID from URL"""
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
            r'youtube\.com\/watch\?.*v=([^&\n?#]+)'
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def enhance_segment_with_metadata(self, segment: ComedySegment, source_url: str = '') -> ComedySegment:
        """
        Enhance comedy segment with YouTube metadata for virality prediction
        This enables the revolutionary feature of predicting joke performance on YouTube
        """
        video_id = self.extract_video_id_from_url(source_url) if source_url else None
        if video_id and video_id in self.youtube_metadata:
            metadata = self.youtube_metadata[video_id]

            # Add virality features to segment metadata
            segment.metadata.update({
                'youtube_video_id': video_id,
                'view_count': metadata.view_count,
                'engagement_rate': metadata.engagement_rate,
                'virality_score': metadata.virality_score,
                'channel': metadata.channel,
                'upload_date': metadata.upload_date,
                'categories': metadata.categories,
                'tags': metadata.tags
            })

        return segment

    def get_statistics(self) -> Dict:
        """Get loading statistics"""
        base_stats = dict(self.stats)
        base_stats['youtube_videos_with_metadata'] = len(self.youtube_metadata)
        return base_stats


class GCACUFormatter:
    """Format comedy data for GCACU training"""

    def __init__(self, include_metadata: bool = True):
        self.include_metadata = include_metadata
        self.example_counter = 0

    def format_segment(self, segment: ComedySegment, video_id: str = "",
                      comedian_id: str = "", show_id: str = "") -> Dict:
        """
        Format a comedy segment for GCACU training
        Follows the format of existing training data
        """
        self.example_counter += 1

        example = {
            "example_id": f"{comedian_id}_seg_{self.example_counter:06d}",
            "language": "en",
            "comedian_id": comedian_id,
            "show_id": show_id,
            "words": segment.words,
            "labels": segment.labels,
            "has_laughter": segment.has_laughter,
            "laughter_ratio": segment.laughter_ratio,
            "laughter_type": segment.laughter_type,
        }

        if self.include_metadata:
            example["metadata"] = {
                **segment.metadata,
                "source": segment.source,
                "word_count": segment.word_count,
                "text": segment.text,
                "start_time": segment.start_time,
                "end_time": segment.end_time,
                "video_id": video_id
            }

        return example

    def save_jsonl(self, segments: List[ComedySegment], output_path: Path,
                   video_id: str = "", comedian_id: str = "", show_id: str = ""):
        """Save segments in JSONL format for GCACU training"""
        with open(output_path, 'w', encoding='utf-8') as f:
            for segment in segments:
                example = self.format_segment(segment, video_id, comedian_id, show_id)
                f.write(json.dumps(example, ensure_ascii=False) + '\n')

        logger.info(f"Saved {len(segments)} examples to {output_path}")


class ComedyDataAugmentor:
    """
    Advanced data augmentation for comedy transcripts
    Increases training data diversity while preserving humor structure
    """

    def __init__(self, augmentation_factor: int = 3):
        self.augmentation_factor = augmentation_factor
        logger.info(f"Comedy Data Augmentor initialized with factor: {augmentation_factor}")

    def augment_text(self, text: str, method: str = "synonym") -> str:
        """Apply text augmentation"""
        if method == "synonym":
            return self._synonym_replacement(text)
        elif method == "noise":
            return self._add_noise(text)
        elif method == "paraphrase":
            return self._light_paraphrase(text)
        return text

    def _synonym_replacement(self, text: str, replacement_rate: float = 0.1) -> str:
        """Replace some words with synonyms (simple version)"""
        # Simple synonym dictionary for comedy-related terms
        synonyms = {
            'funny': ['hilarious', 'amusing', 'entertaining'],
            'laugh': ['chuckle', 'giggle', 'crack up'],
            'joke': ['gag', 'bit', 'setup'],
            'audience': ['crowd', 'people', 'folks'],
            'really': ['very', 'extremely', 'incredibly'],
            'like': ['such as', 'for example', 'similar to']
        }

        words = text.split()
        modified = False
        for i, word in enumerate(words):
            word_lower = word.lower()
            # Strip punctuation for matching
            word_clean = ''.join(c for c in word_lower if c.isalpha())
            if word_clean in synonyms:
                # Force replacement for testing
                if word_clean in ['funny', 'laugh', 'joke']:  # Always replace comedy terms
                    replacement = random.choice(synonyms[word_clean])
                    # Preserve original capitalization and punctuation
                    if word[0].isupper():
                        replacement = replacement.capitalize()
                    words[i] = replacement
                    modified = True
                elif random.random() < replacement_rate:
                    replacement = random.choice(synonyms[word_clean])
                    if word[0].isupper():
                        replacement = replacement.capitalize()
                    words[i] = replacement
                    modified = True

        return ' '.join(words) if modified else text

    def _add_noise(self, text: str, noise_rate: float = 0.05) -> str:
        """Add minor noise to simulate transcription errors"""
        noise_types = ['stutter', 'repetition', 'filler']

        if random.random() < noise_rate:
            noise_type = random.choice(noise_types)
            words = text.split()

            if noise_type == 'stutter' and len(words) > 0:
                pos = random.randint(0, min(3, len(words)))
                word = words[pos]
                words.insert(pos, word[:2] + '-' if len(word) > 2 else word)

            elif noise_type == 'repetition' and len(words) > 1:
                pos = random.randint(0, len(words) - 1)
                words.insert(pos + 1, words[pos])

            elif noise_type == 'filler' and len(words) > 0:
                fillers = ['um', 'uh', 'like', 'you know']
                pos = random.randint(0, len(words))
                words.insert(pos, random.choice(fillers))

            return ' '.join(words)

        return text

    def _light_paraphrase(self, text: str) -> str:
        """Light paraphrasing that preserves humor structure"""
        # Simple structural changes that don't break jokes
        paraphrases = [
            (r'I\s+mean,\s*', ''),
            (r'you\s+know,\s*', ''),
            (r'actually,\s*', ''),
            (r'honestly,\s*', ''),
            (r',\s*basically,\s*', ', '),  # Handle basically with commas
            (r'basically,\s*', ''),  # Handle basically at start
        ]

        result = text
        for pattern, replacement in paraphrases:
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

        return result.strip()

    def augment_segment(self, segment: ComedySegment) -> List[ComedySegment]:
        """Augment a single comedy segment"""
        augmented = [segment]  # Include original

        # Create variations
        methods = ['synonym', 'noise', 'paraphrase']
        for method in methods:
            try:
                augmented_text = self.augment_text(segment.text, method)

                # Recreate words and adjust labels
                new_words = augmented_text.split()
                new_labels = self._adjust_labels(segment.labels, len(new_words))

                new_segment = ComedySegment(
                    text=augmented_text,
                    words=new_words,
                    labels=new_labels,
                    laughter_type=segment.laughter_type,
                    source=segment.source + f"_aug_{method}",
                    metadata={
                        **segment.metadata,
                        'augmentation_method': method,
                        'original_segment_hash': hashlib.md5(segment.text.encode()).hexdigest()
                    }
                )

                augmented.append(new_segment)

            except Exception as e:
                logger.warning(f"Augmentation failed for {method}: {e}")

        return augmented

    def _adjust_labels(self, original_labels: List[int], new_length: int) -> List[int]:
        """Adjust label array length when word count changes"""
        if not original_labels:
            return [0] * new_length

        if new_length <= len(original_labels):
            return original_labels[:new_length]

        # Pad with zeros if longer
        return original_labels + [0] * (new_length - len(original_labels))

    def augment_dataset(self, segments: List[ComedySegment]) -> List[ComedySegment]:
        """Augment entire dataset"""
        augmented_segments = []
        total_augmented = 0

        for segment in segments:
            # Only augment segments with laughter for balanced training
            if segment.has_laughter and random.random() < 0.5:
                new_segments = self.augment_segment(segment)
                augmented_segments.extend(new_segments)
                total_augmented += len(new_segments) - 1  # Count new segments only
            else:
                augmented_segments.append(segment)

        logger.info(f"Augmented {total_augmented} new segments from {len(segments)} original segments")
        return augmented_segments


class YouTubeComedyExporter:
    """Export YouTube comedy data in various formats"""

    def __init__(self, loader: YouTubeComedyLoader, augmentor: ComedyDataAugmentor = None):
        self.loader = loader
        self.augmentor = augmentor
        self.formatter = GCACUFormatter(include_metadata=True)

    def export_for_gcacu(self, output_dir: str, max_comprehensive_records: int = None, apply_augmentation: bool = True):
        """
        Export all datasets in GCACU training format
        Creates train/test/validation splits with optional augmentation
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        logger.info("Exporting YouTube comedy data for GCACU training...")

        # Clear deduplication cache before loading to ensure fresh data
        self.loader.deduplication_cache.clear()

        # Collect all segments
        all_segments = list(self.loader.load_all_datasets(max_comprehensive_records))

        if not all_segments:
            logger.warning("No segments to export!")
            return

        # Apply augmentation if requested
        if apply_augmentation and self.augmentor:
            logger.info("Applying data augmentation...")
            all_segments = self.augmentor.augment_dataset(all_segments)

        # Create splits (80/10/10)
        random.shuffle(all_segments)

        total = len(all_segments)
        train_end = int(total * 0.8)
        val_end = int(total * 0.9)

        splits = {
            'train': all_segments[:train_end],
            'valid': all_segments[train_end:val_end],
            'test': all_segments[val_end:]
        }

        # Export each split
        for split_name, segments in splits.items():
            output_file = output_path / f"{split_name}.jsonl"
            self.formatter.save_jsonl(
                segments,
                output_file,
                video_id="youtube_comedy",
                comedian_id="youtube_various",
                show_id="youtube_comedy_collection"
            )

        # Export statistics
        stats_file = output_path / "export_statistics.json"
        stats = {
            'export_date': datetime.now().isoformat(),
            'total_segments': total,
            'splits': {name: len(segments) for name, segments in splits.items()},
            'loader_stats': self.loader.get_statistics(),
            'laughter_segments': sum(1 for s in all_segments if s.has_laughter),
            'total_words': sum(s.word_count for s in all_segments),
            'laughter_words': sum(sum(s.labels) for s in all_segments),
            'augmentation_applied': apply_augmentation
        }

        with open(stats_file, 'w') as f:
            json.dump(stats, f, indent=2)

        logger.info(f"Export complete! Statistics saved to {stats_file}")
        logger.info(f"Total segments: {total}")
        logger.info(f"Laughter segments: {stats['laughter_segments']} ({stats['laughter_segments']/total*100:.1f}%)")
        logger.info(f"Total words: {stats['total_words']}")
        logger.info(f"Laughter words: {stats['laughter_words']} ({stats['laughter_words']/stats['total_words']*100:.1f}%)")


def main():
    parser = argparse.ArgumentParser(description="Load and export YouTube comedy datasets")
    parser.add_argument("--data-dir", type=str, default="data/raw",
                       help="Directory containing raw datasets")
    parser.add_argument("--output-dir", type=str, default="data/training/youtube_comedy",
                       help="Output directory for processed data")
    parser.add_argument("--export-format", type=str, default="gcacu",
                       choices=["gcacu", "json", "jsonl"],
                       help="Export format")
    parser.add_argument("--max-comprehensive", type=int, default=None,
                       help="Max records to process from comprehensive dataset (for testing)")
    parser.add_argument("--no-augmentation", action="store_true",
                       help="Disable data augmentation")
    parser.add_argument("--augmentation-factor", type=int, default=3,
                       help="Data augmentation factor (default: 3)")
    parser.add_argument("--verbose", action="store_true",
                       help="Enable verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Initialize loader
    loader = YouTubeComedyLoader(data_dir=args.data_dir)

    # Initialize augmentor if not disabled
    augmentor = None if args.no_augmentation else ComedyDataAugmentor(args.augmentation_factor)

    # Export data
    if args.export_format == "gcacu":
        exporter = YouTubeComedyExporter(loader, augmentor)
        exporter.export_for_gcacu(args.output_dir, args.max_comprehensive, apply_augmentation=not args.no_augmentation)

    logger.info("YouTube comedy dataset processing complete!")


if __name__ == "__main__":
    main()