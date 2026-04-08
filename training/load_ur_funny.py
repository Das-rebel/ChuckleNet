#!/usr/bin/env python3
"""
UR-FUNNY Dataset Loader for Autonomous Laughter Prediction

This module provides a comprehensive loader for the UR-FUNNY dataset which contains:
- TED talks with word-level forced alignment via P2FA
- Punchline/context annotations for humor detection
- Professional presentation humor patterns (different from stand-up comedy)
- 1,866 TED videos with 16,514 humor-labeled instances

Features:
- Word-level alignment using P2FA (Penn Phonetics Lab Forced Aligner) output
- Punchline detection with context window extraction
- Support for both binary humor classification and word-level laughter prediction
- Integration with GCACU pipeline
- Comprehensive error handling and validation
- Professional presentation humor pattern analysis

Dataset Structure:
- annotations/train.csv, val.csv, test.csv - Main annotations
- features/audio_features.npy, visual_features.npy - Precomputed features
- p2fa_alignments/ - Word-level forced alignment data
- punchline_annotations.json - Punchline and context data

Author: Autonomous Laughter Prediction Team
Date: 2026-04-03
"""

import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class HumorType(Enum):
    """Types of humor annotations in UR-FUNNY."""
    PUNCHLINE = "punchline"          # Explicit punchline annotations
    CONTEXT = "context"              # Context windows around punchlines
    BINARY = "binary"                # Binary humor classification
    WORD_LEVEL = "word_level"        # Word-level laughter labels


class AlignmentFormat(Enum):
    """Types of forced alignment formats."""
    P2FA = "p2fa"                    # Penn Phonetics Lab Forced Aligner
    TEXTGRID = "textgrid"            # Praat TextGrid format
    JSON = "json"                    # JSON alignment format
    CSV = "csv"                      # CSV alignment format


@dataclass
class PunchlineAnnotation:
    """Punchline annotation from UR-FUNNY dataset.

    Attributes:
        punchline_start: Start word index of punchline
        punchline_end: End word index of punchline
        context_start: Start word index of context window
        context_end: End word index of context window
        humor_score: Continuous humor score (0-1)
        laughter_intensity: Laughter intensity annotation (0-1)
        audience_reaction: Audience reaction type
    """
    punchline_start: int
    punchline_end: int
    context_start: int
    context_end: int
    humor_score: float
    laughter_intensity: float
    audience_reaction: str = "laughter"

    def __post_init__(self):
        """Validate punchline annotation."""
        if self.punchline_start < 0 or self.punchline_end < self.punchline_start:
            raise ValueError(f"Invalid punchline range: [{self.punchline_start}, {self.punchline_end}]")

        if self.context_start < 0 or self.context_end < self.context_start:
            raise ValueError(f"Invalid context range: [{self.context_start}, {self.context_end}]")

        if not 0.0 <= self.humor_score <= 1.0:
            raise ValueError(f"Humor score must be in [0, 1], got {self.humor_score}")

        if not 0.0 <= self.laughter_intensity <= 1.0:
            raise ValueError(f"Laughter intensity must be in [0, 1], got {self.laughter_intensity}")

    def get_punchline_words(self, words: List[str]) -> List[str]:
        """Extract punchline words from full text."""
        return words[self.punchline_start:self.punchline_end + 1]

    def get_context_words(self, words: List[str]) -> List[str]:
        """Extract context window words from full text."""
        return words[self.context_start:min(self.context_end + 1, len(words))]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "punchline_start": self.punchline_start,
            "punchline_end": self.punchline_end,
            "context_start": self.context_start,
            "context_end": self.context_end,
            "humor_score": self.humor_score,
            "laughter_intensity": self.laughter_intensity,
            "audience_reaction": self.audience_reaction
        }


@dataclass
class ForcedAlignment:
    """Word-level forced alignment from P2FA.

    Attributes:
        words: List of words
        start_times: Word start times in seconds
        end_times: Word end times in seconds
        phones: Phone-level alignments (optional)
        confidence: Alignment confidence scores
    """
    words: List[str]
    start_times: List[float]
    end_times: List[float]
    phones: Optional[List[str]] = None
    confidence: List[float] = field(default_factory=list)

    def __post_init__(self):
        """Validate alignment data."""
        n_words = len(self.words)
        if len(self.start_times) != n_words:
            raise ValueError(f"Start times length {len(self.start_times)} != words {n_words}")
        if len(self.end_times) != n_words:
            raise ValueError(f"End times length {len(self.end_times)} != words {n_words}")

        # Ensure no overlapping times
        for i in range(n_words - 1):
            if self.end_times[i] > self.start_times[i + 1]:
                logger.warning(
                    f"Overlapping times at word {i}: "
                    f"end_time[{i}]={self.end_times[i]} > start_time[{i+1}]={self.start_times[i+1]}"
                )

        # Initialize confidence if not provided
        if not self.confidence:
            self.confidence = [1.0] * n_words

    def get_word_duration(self, word_idx: int) -> float:
        """Get duration of a specific word."""
        return self.end_times[word_idx] - self.start_times[word_idx]

    def get_total_duration(self) -> float:
        """Get total duration of the aligned segment."""
        return self.end_times[-1] - self.start_times[0] if self.end_times else 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "words": self.words,
            "start_times": self.start_times,
            "end_times": self.end_times,
            "phones": self.phones,
            "confidence": self.confidence
        }


@dataclass
class URFunnyExample:
    """Single example from UR-FUNNY dataset.

    Attributes:
        example_id: Unique identifier (e.g., "urfunny_ted_1234")
        words: List of words in the segment
        labels: Word-level laughter labels (0 or 1)
        language: Language code (default "en")
        metadata: Additional metadata
        alignment: Optional forced alignment data
        punchlines: List of punchline annotations
        humor_type: Type of humor annotation
        ted_id: Original TED talk ID
        speaker: Speaker name
        title: Talk title
    """
    example_id: str
    words: List[str]
    labels: List[int]
    language: str = "en"
    metadata: Dict[str, Any] = field(default_factory=dict)
    alignment: Optional[ForcedAlignment] = None
    punchlines: List[PunchlineAnnotation] = field(default_factory=list)
    humor_type: str = HumorType.WORD_LEVEL.value
    ted_id: str = ""
    speaker: str = ""
    title: str = ""

    def __post_init__(self):
        """Validate example data."""
        if len(self.words) != len(self.labels):
            raise ValueError(
                f"Words/labels length mismatch for {self.example_id}: "
                f"{len(self.words)} != {len(self.labels)}"
            )

        # Reject empty examples
        if len(self.words) == 0:
            raise ValueError(f"Empty words list for {self.example_id}")

        # Validate punchline indices are within bounds
        for punchline in self.punchlines:
            if punchline.punchline_end >= len(self.words):
                raise ValueError(
                    f"Punchline end {punchline.punchline_end} >= words length {len(self.words)}"
                )
            if punchline.context_end >= len(self.words):
                raise ValueError(
                    f"Context end {punchline.context_end} >= words length {len(self.words)}"
                )

    def has_alignment(self) -> bool:
        """Check if example has forced alignment."""
        return self.alignment is not None

    def has_punchlines(self) -> bool:
        """Check if example has punchline annotations."""
        return len(self.punchlines) > 0

    def get_laughter_segments(self) -> List[Dict[str, Any]]:
        """Extract laughter segments from word-level labels."""
        segments = []
        in_laughter = False
        start_idx = 0

        for i, label in enumerate(self.labels):
            if label == 1 and not in_laughter:
                # Start of laughter segment
                in_laughter = True
                start_idx = i
            elif label == 0 and in_laughter:
                # End of laughter segment
                in_laughter = False
                end_idx = i - 1

                # Add timing info if available
                segment = {
                    "start_word": start_idx,
                    "end_word": end_idx,
                    "words": self.words[start_idx:end_idx + 1]
                }

                if self.alignment:
                    segment["start_time"] = self.alignment.start_times[start_idx]
                    segment["end_time"] = self.alignment.end_times[end_idx]

                segments.append(segment)

        # Handle segment that continues to end
        if in_laughter:
            segment = {
                "start_word": start_idx,
                "end_word": len(self.labels) - 1,
                "words": self.words[start_idx:]
            }

            if self.alignment:
                segment["start_time"] = self.alignment.start_times[start_idx]
                segment["end_time"] = self.alignment.end_times[-1]

            segments.append(segment)

        return segments

    def get_context_windows(self, window_size: int = 5) -> List[Dict[str, Any]]:
        """Extract context windows around punchlines.

        Args:
            window_size: Number of words before and after punchline

        Returns:
            List of context windows with words and labels
        """
        contexts = []

        for punchline in self.punchlines:
            # Extract context window
            context_start = max(0, punchline.punchline_start - window_size)
            context_end = min(len(self.words), punchline.punchline_end + window_size + 1)

            context_words = self.words[context_start:context_end]
            context_labels = self.labels[context_start:context_end]

            # Get punchline position relative to context
            punchline_start_rel = punchline.punchline_start - context_start
            punchline_end_rel = punchline.punchline_end - context_start

            contexts.append({
                "context_words": context_words,
                "context_labels": context_labels,
                "punchline_start_rel": punchline_start_rel,
                "punchline_end_rel": punchline_end_rel,
                "humor_score": punchline.humor_score,
                "laughter_intensity": punchline.laughter_intensity
            })

        return contexts


class URFunnyLoader:
    """Enhanced loader for UR-FUNNY dataset.

    Expected directory structure:
    data/
        UR-FUNNY/
            annotations/
                train.csv
                val.csv
                test.csv
            features/
                audio_features.npy
                visual_features.npy
            p2fa_alignments/
                ted_1234.json
                ted_5678.json
                ...
            punchline_annotations.json
            metadata.json

    Expected CSV format for annotations:
    video_id,text,humor,speaker,title,url,feature_idx
    ted_1234,"Sample text...",1,"Speaker Name","Talk Title","http://...",0

    Expected JSON format for P2FA alignments:
    {
        "ted_id": "ted_1234",
        "words": ["Hello", "world", ...],
        "start_times": [0.0, 0.5, ...],
        "end_times": [0.5, 1.0, ...],
        "phones": [["HH", "AH", "L", "OW"], ["W", "ER", "L", "D"], ...],
        "confidence": [0.98, 0.95, ...]
    }

    Expected JSON format for punchline annotations:
    [
        {
            "ted_id": "ted_1234",
            "punchlines": [
                {
                    "punchline_start": 10,
                    "punchline_end": 12,
                    "context_start": 5,
                    "context_end": 20,
                    "humor_score": 0.85,
                    "laughter_intensity": 0.75,
                    "audience_reaction": "laughter"
                }
            ]
        },
        ...
    ]
    """

    def __init__(
        self,
        data_dir: Union[str, Path],
        enable_alignment: bool = True,
        enable_punchlines: bool = True,
        alignment_format: str = "p2fa",
        humor_threshold: float = 0.5,
        cache_alignments: bool = True,
        create_if_missing: bool = False
    ):
        """Initialize UR-FUNNY loader.

        Args:
            data_dir: Path to UR-FUNNY dataset directory
            enable_alignment: Whether to load forced alignment data
            enable_punchlines: Whether to load punchline annotations
            alignment_format: Format of alignment data ('p2fa', 'textgrid', 'json', 'csv')
            humor_threshold: Threshold for binary humor classification
            cache_alignments: Whether to cache loaded alignment data
            create_if_missing: If True, don't raise error if directory doesn't exist
        """
        self.data_dir = Path(data_dir)
        self.enable_alignment = enable_alignment
        self.enable_punchlines = enable_punchlines
        self.alignment_format = alignment_format
        self.humor_threshold = humor_threshold
        self.cache_alignments = cache_alignments

        # Validate directory exists (unless create_if_missing is True)
        if not self.data_dir.exists() and not create_if_missing:
            raise FileNotFoundError(f"UR-FUNNY data directory not found: {self.data_dir}")

        # Cache for alignment data
        self._alignment_cache: Dict[str, ForcedAlignment] = {}

        # Statistics
        self.stats = {
            "total_examples": 0,
            "examples_with_alignment": 0,
            "examples_with_punchlines": 0,
            "total_words": 0,
            "laughter_words": 0,
            "total_punchlines": 0,
            "avg_example_length": 0.0,
            "avg_humor_score": 0.0
        }

    def load(self, split: str = "train") -> List[URFunnyExample]:
        """Load UR-FUNNY dataset.

        Args:
            split: Dataset split ('train', 'val', 'test')

        Returns:
            List of UR-FUNNY examples

        Raises:
            FileNotFoundError: If annotation file not found
            ValueError: If data format is invalid
        """
        annotation_file = self.data_dir / "annotations" / f"{split}.csv"

        if not annotation_file.exists():
            # Try alternative location
            annotation_file = self.data_dir / f"{split}.csv"
            if not annotation_file.exists():
                raise FileNotFoundError(
                    f"UR-FUNNY annotation file not found for {split} split\n"
                    f"Expected: {self.data_dir}/annotations/{split}.csv"
                )

        logger.info(f"Loading UR-FUNNY {split} split from {annotation_file}")

        try:
            annotations = pd.read_csv(annotation_file)
        except Exception as e:
            raise ValueError(f"Failed to read annotation file: {e}")

        logger.info(f"Found {len(annotations)} annotations in {split}.csv")

        # Load punchline annotations if enabled
        punchline_data = {}
        if self.enable_punchlines:
            punchline_data = self._load_punchline_annotations()

        # Load alignment data if enabled
        alignment_cache = {}
        if self.enable_alignment:
            alignment_cache = self._load_alignments()

        # Process annotations
        examples = []
        for idx, row in annotations.iterrows():
            try:
                example = self._process_annotation(
                    row, punchline_data, alignment_cache, split
                )
                if example:
                    examples.append(example)
            except Exception as e:
                logger.warning(f"Failed to process annotation {idx}: {e}")
                continue

        # Update statistics
        self._update_statistics(examples)

        logger.info(f"Successfully loaded {len(examples)} UR-FUNNY examples from {split} split")
        logger.info(f"Statistics: {self.stats}")

        return examples

    def _load_punchline_annotations(self) -> Dict[str, List[PunchlineAnnotation]]:
        """Load punchline annotations from JSON file.

        Returns:
            Dictionary mapping ted_id to list of punchline annotations
        """
        punchline_file = self.data_dir / "punchline_annotations.json"

        if not punchline_file.exists():
            logger.warning(f"Punchline annotation file not found: {punchline_file}")
            return {}

        logger.info(f"Loading punchline annotations from {punchline_file}")

        try:
            with open(punchline_file, 'r', encoding='utf-8') as f:
                punchline_data = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in punchline_annotations.json: {e}")
            return {}

        # Process punchline annotations
        punchline_map = {}
        for item in punchline_data:
            ted_id = item.get("ted_id")
            if not ted_id:
                continue

            punchlines = []
            for pl_data in item.get("punchlines", []):
                try:
                    punchline = PunchlineAnnotation(
                        punchline_start=pl_data.get("punchline_start", 0),
                        punchline_end=pl_data.get("punchline_end", 0),
                        context_start=pl_data.get("context_start", 0),
                        context_end=pl_data.get("context_end", 0),
                        humor_score=pl_data.get("humor_score", 0.5),
                        laughter_intensity=pl_data.get("laughter_intensity", 0.5),
                        audience_reaction=pl_data.get("audience_reaction", "laughter")
                    )
                    punchlines.append(punchline)
                except Exception as e:
                    logger.warning(f"Failed to load punchline annotation: {e}")
                    continue

            punchline_map[ted_id] = punchlines

        logger.info(f"Loaded punchline annotations for {len(punchline_map)} TED talks")
        return punchline_map

    def _load_alignments(self) -> Dict[str, ForcedAlignment]:
        """Load forced alignment data from P2FA files.

        Returns:
            Dictionary mapping ted_id to alignment data
        """
        alignments_dir = self.data_dir / "p2fa_alignments"

        if not alignments_dir.exists():
            logger.warning(f"P2FA alignments directory not found: {alignments_dir}")
            return {}

        logger.info(f"Loading P2FA alignments from {alignments_dir}")

        alignment_map = {}

        # Try different alignment formats
        if self.alignment_format == "json":
            alignment_files = list(alignments_dir.glob("*.json"))
        elif self.alignment_format == "csv":
            alignment_files = list(alignments_dir.glob("*.csv"))
        elif self.alignment_format == "textgrid":
            alignment_files = list(alignments_dir.glob("*.TextGrid"))
        else:
            logger.warning(f"Unknown alignment format: {self.alignment_format}")
            return {}

        logger.info(f"Found {len(alignment_files)} alignment files")

        for alignment_file in alignment_files:
            try:
                if self.alignment_format == "json":
                    alignment = self._load_json_alignment(alignment_file)
                elif self.alignment_format == "csv":
                    alignment = self._load_csv_alignment(alignment_file)
                elif self.alignment_format == "textgrid":
                    alignment = self._load_textgrid_alignment(alignment_file)
                else:
                    continue

                if alignment:
                    # Extract ted_id from filename
                    ted_id = alignment_file.stem
                    alignment_map[ted_id] = alignment

                    if self.cache_alignments:
                        self._alignment_cache[ted_id] = alignment

            except Exception as e:
                logger.warning(f"Failed to load alignment from {alignment_file}: {e}")
                continue

        logger.info(f"Loaded alignments for {len(alignment_map)} TED talks")
        return alignment_map

    def _load_json_alignment(self, file_path: Path) -> Optional[ForcedAlignment]:
        """Load alignment from JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            return ForcedAlignment(
                words=data.get("words", []),
                start_times=data.get("start_times", []),
                end_times=data.get("end_times", []),
                phones=data.get("phones"),
                confidence=data.get("confidence", [])
            )
        except Exception as e:
            logger.warning(f"Failed to load JSON alignment from {file_path}: {e}")
            return None

    def _load_csv_alignment(self, file_path: Path) -> Optional[ForcedAlignment]:
        """Load alignment from CSV file."""
        try:
            df = pd.read_csv(file_path)

            # Expected columns: word, start_time, end_time, phone, confidence
            words = df.get("word", []).tolist()
            start_times = df.get("start_time", []).tolist()
            end_times = df.get("end_time", []).tolist()
            phones = df.get("phone", []).tolist() if "phone" in df else None
            confidence = df.get("confidence", []).tolist() if "confidence" in df else []

            return ForcedAlignment(
                words=words,
                start_times=start_times,
                end_times=end_times,
                phones=phones,
                confidence=confidence
            )
        except Exception as e:
            logger.warning(f"Failed to load CSV alignment from {file_path}: {e}")
            return None

    def _load_textgrid_alignment(self, file_path: Path) -> Optional[ForcedAlignment]:
        """Load alignment from Praat TextGrid file."""
        try:
            # Simple TextGrid parser
            # In production, use textgrid library for proper parsing
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract intervals (simplified parsing)
            words = []
            start_times = []
            end_times = []

            # This is a simplified parser - proper implementation would use
            # praatio-parselmouth or similar library
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if 'xmin = ' in line:
                    start_times.append(float(line.split('=')[1].strip()))
                elif 'xmax = ' in line:
                    end_times.append(float(line.split('=')[1].strip()))
                elif 'text = "' in line:
                    text = line.split('"')[1]
                    if text and text != '':  # Skip empty intervals
                        words.append(text)

            # Align lengths
            min_len = min(len(words), len(start_times), len(end_times))
            words = words[:min_len]
            start_times = start_times[:min_len]
            end_times = end_times[:min_len]

            return ForcedAlignment(
                words=words,
                start_times=start_times,
                end_times=end_times
            )
        except Exception as e:
            logger.warning(f"Failed to load TextGrid alignment from {file_path}: {e}")
            return None

    def _process_annotation(
        self,
        row: pd.Series,
        punchline_data: Dict[str, List[PunchlineAnnotation]],
        alignment_cache: Dict[str, ForcedAlignment],
        split: str
    ) -> Optional[URFunnyExample]:
        """Process a single annotation into a URFunnyExample.

        Args:
            row: Pandas Series with annotation data
            punchline_data: Dictionary of punchline annotations
            alignment_cache: Dictionary of alignment data
            split: Dataset split name

        Returns:
            URFunnyExample or None if processing fails
        """
        # Extract required fields
        video_id = row.get("video_id", row.get("id", ""))
        if not video_id:
            logger.warning("Annotation missing video_id, skipping")
            return None

        # Extract text and process into words
        text = row.get("text", row.get("transcript", row.get("caption", "")))
        if not text or text.isspace():
            logger.warning(f"Annotation {video_id} has no text, skipping")
            return None

        words = text.split()

        # Get binary humor label
        humor_score = row.get("humor", row.get("funny", row.get("label", 0)))
        if pd.isna(humor_score):
            humor_score = 0

        # Generate word-level labels from punchlines if available
        punchlines = punchline_data.get(video_id, [])
        if punchlines:
            labels = self._punchlines_to_labels(words, punchlines)
        else:
            # Fall back to binary label applied to all words
            binary_label = 1 if float(humor_score) >= self.humor_threshold else 0
            labels = [binary_label] * len(words)

        # Extract alignment if available
        alignment = None
        if self.enable_alignment and video_id in alignment_cache:
            alignment = alignment_cache[video_id]

        # Build metadata
        metadata = {
            "source": "UR-FUNNY",
            "split": split,
            "video_id": video_id,
            "ted_id": video_id,
            "speaker": row.get("speaker", row.get("presenter", "Unknown")),
            "title": row.get("title", row.get("description", "")),
            "url": row.get("url", ""),
            "humor_score": float(humor_score) if not pd.isna(humor_score) else 0.0,
            "has_alignment": alignment is not None,
            "has_punchlines": len(punchlines) > 0,
            "punchline_count": len(punchlines),
            "laughter_type": HumorType.PUNCHLINE.value if punchlines else HumorType.BINARY.value
        }

        return URFunnyExample(
            example_id=f"urfunny_{video_id}",
            words=[str(w) for w in words],
            labels=[int(l) for l in labels],
            language=row.get("language", "en"),
            metadata=metadata,
            alignment=alignment,
            punchlines=punchlines,
            humor_type=metadata["laughter_type"],
            ted_id=video_id,
            speaker=metadata["speaker"],
            title=metadata["title"]
        )

    def _punchlines_to_labels(
        self,
        words: List[str],
        punchlines: List[PunchlineAnnotation]
    ) -> List[int]:
        """Convert punchline annotations to word-level labels.

        Args:
            words: List of words
            punchlines: List of punchline annotations

        Returns:
            Word-level labels (0 or 1)
        """
        labels = [0] * len(words)

        for punchline in punchlines:
            # Mark punchline words as laughter
            start = max(0, punchline.punchline_start)
            end = min(len(words), punchline.punchline_end + 1)

            for i in range(start, end):
                labels[i] = 1

        return labels

    def _update_statistics(self, examples: List[URFunnyExample]):
        """Update loading statistics.

        Args:
            examples: List of loaded examples
        """
        self.stats["total_examples"] = len(examples)
        self.stats["examples_with_alignment"] = sum(
            1 for ex in examples if ex.has_alignment()
        )
        self.stats["examples_with_punchlines"] = sum(
            1 for ex in examples if ex.has_punchlines()
        )

        total_words = sum(len(ex.words) for ex in examples)
        laughter_words = sum(sum(ex.labels) for ex in examples)
        total_punchlines = sum(len(ex.punchlines) for ex in examples)

        self.stats["total_words"] = total_words
        self.stats["laughter_words"] = laughter_words
        self.stats["total_punchlines"] = total_punchlines
        self.stats["avg_example_length"] = total_words / len(examples) if examples else 0.0

        # Calculate average humor score
        humor_scores = [
            ex.metadata.get("humor_score", 0.0)
            for ex in examples
            if "humor_score" in ex.metadata
        ]
        self.stats["avg_humor_score"] = sum(humor_scores) / len(humor_scores) if humor_scores else 0.0


def convert_to_gcacu_format(
    examples: List[URFunnyExample],
    output_file: Path,
    include_alignment: bool = False,
    include_punchlines: bool = False
):
    """Convert UR-FUNNY examples to GCACU-compatible JSONL format.

    Args:
        examples: List of UR-FUNNY examples
        output_file: Output JSONL file path
        include_alignment: Whether to include alignment data
        include_punchlines: Whether to include punchline annotations
    """
    logger.info(f"Converting {len(examples)} examples to GCACU format")

    with open(output_file, 'w', encoding='utf-8') as f:
        for ex in examples:
            record = {
                "example_id": ex.example_id,
                "language": ex.language,
                "words": ex.words,
                "labels": ex.labels,
                "metadata": ex.metadata
            }

            if include_alignment and ex.has_alignment():
                record["alignment"] = ex.alignment.to_dict()

            if include_punchlines and ex.has_punchlines():
                record["punchlines"] = [pl.to_dict() for pl in ex.punchlines]

            f.write(json.dumps(record) + '\n')

    logger.info(f"Saved GCACU format to {output_file}")


def create_sample_ur_funny_data(output_dir: Path, num_samples: int = 10):
    """Create sample UR-FUNNY data for testing.

    Args:
        output_dir: Output directory for sample data
        num_samples: Number of sample TED talks to create
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create annotations directory
    annotations_dir = output_dir / "annotations"
    annotations_dir.mkdir(exist_ok=True)

    # Create sample annotations
    samples = []
    for i in range(num_samples):
        ted_id = f"ted_{i:04d}"
        n_words = np.random.randint(20, 50)

        words = [f"word{j}" for j in range(n_words)]
        text = " ".join(words)

        # Add some punchlines
        num_punchlines = np.random.randint(1, 4)
        punchline_starts = np.random.choice(range(5, n_words - 5), num_punchlines, replace=False)

        humor_score = np.random.uniform(0.3, 0.9)

        sample = {
            "video_id": ted_id,
            "text": text,
            "humor": humor_score,
            "speaker": f"Speaker {i}",
            "title": f"Sample TED Talk {i}",
            "url": f"https://www.ted.com/talks/sample_{i}",
            "feature_idx": i
        }
        samples.append(sample)

    # Save annotations
    for split in ["train", "val", "test"]:
        df = pd.DataFrame(samples)
        annotation_file = annotations_dir / f"{split}.csv"
        df.to_csv(annotation_file, index=False)
        logger.info(f"Created sample annotation file: {annotation_file}")

    # Create punchline annotations
    punchline_data = []
    for i, sample in enumerate(samples):
        ted_id = sample["video_id"]
        words = sample["text"].split()
        n_words = len(words)

        num_punchlines = np.random.randint(1, 4)
        punchline_starts = np.random.choice(range(5, n_words - 5), num_punchlines, replace=False)

        punchlines = []
        for start in punchline_starts:
            end = min(start + np.random.randint(2, 5), n_words - 1)
            context_start = max(0, start - np.random.randint(3, 8))
            context_end = min(n_words, end + np.random.randint(3, 8))

            punchlines.append({
                "punchline_start": int(start),
                "punchline_end": int(end),
                "context_start": int(context_start),
                "context_end": int(context_end),
                "humor_score": float(np.random.uniform(0.6, 0.95)),
                "laughter_intensity": float(np.random.uniform(0.5, 0.9)),
                "audience_reaction": "laughter"
            })

        punchline_data.append({
            "ted_id": ted_id,
            "punchlines": punchlines
        })

    # Save punchline annotations
    punchline_file = output_dir / "punchline_annotations.json"
    with open(punchline_file, 'w', encoding='utf-8') as f:
        json.dump(punchline_data, f, indent=2)
    logger.info(f"Created punchline annotations: {punchline_file}")

    # Create P2FA alignments directory
    alignments_dir = output_dir / "p2fa_alignments"
    alignments_dir.mkdir(exist_ok=True)

    # Create sample alignments
    for sample in samples:
        ted_id = sample["video_id"]
        words = sample["text"].split()

        # Generate realistic timing data
        n_words = len(words)
        start_times = []
        end_times = []
        current_time = 0.0

        for word in words:
            duration = np.random.uniform(0.2, 0.8)  # Word duration 200-800ms
            start_times.append(current_time)
            current_time += duration
            end_times.append(current_time)

        # Add small pauses between phrases
        for i in range(len(start_times)):
            if i % 8 == 0 and i > 0:  # Pause every ~8 words
                pause = np.random.uniform(0.1, 0.3)
                for j in range(i, len(start_times)):
                    start_times[j] += pause
                    end_times[j] += pause

        alignment = {
            "ted_id": ted_id,
            "words": words,
            "start_times": [round(t, 3) for t in start_times],
            "end_times": [round(t, 3) for t in end_times],
            "confidence": [round(np.random.uniform(0.85, 0.99), 3) for _ in words]
        }

        alignment_file = alignments_dir / f"{ted_id}.json"
        with open(alignment_file, 'w', encoding='utf-8') as f:
            json.dump(alignment, f, indent=2)

    logger.info(f"Created sample alignments in {alignments_dir}")

    logger.info(f"Created sample UR-FUNNY data in {output_dir}")
    logger.info(f"  - {len(samples)} TED talks")
    logger.info(f"  - Annotations for train/val/test splits")
    logger.info(f"  - Punchline annotations")
    logger.info(f"  - P2FA forced alignments")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="UR-FUNNY Dataset Loader")
    parser.add_argument(
        "--data-dir",
        type=str,
        required=True,
        help="Path to UR-FUNNY dataset directory"
    )
    parser.add_argument(
        "--split",
        type=str,
        default="train",
        choices=["train", "val", "test"],
        help="Dataset split to load"
    )
    parser.add_argument(
        "--output-file",
        type=str,
        default="urfunny_examples.jsonl",
        help="Output JSONL file for GCACU format"
    )
    parser.add_argument(
        "--no-alignment",
        action="store_true",
        help="Disable forced alignment loading"
    )
    parser.add_argument(
        "--no-punchlines",
        action="store_true",
        help="Disable punchline annotation loading"
    )
    parser.add_argument(
        "--alignment-format",
        type=str,
        default="p2fa",
        choices=["p2fa", "textgrid", "json", "csv"],
        help="Format of alignment data"
    )
    parser.add_argument(
        "--create-sample",
        type=str,
        metavar="DIR",
        help="Create sample data in specified directory"
    )
    parser.add_argument(
        "--num-samples",
        type=int,
        default=10,
        help="Number of sample TED talks to create"
    )

    args = parser.parse_args()

    if args.create_sample:
        # Create sample data
        create_sample_ur_funny_data(Path(args.create_sample), args.num_samples)
        print(f"\nSample data created in {args.create_sample}")
        print("You can now test the loader with:")
        print(f"python load_ur_funny.py --data-dir {args.create_sample} --split train")
    else:
        # Load UR-FUNNY dataset
        loader = URFunnyLoader(
            data_dir=Path(args.data_dir),
            enable_alignment=not args.no_alignment,
            enable_punchlines=not args.no_punchlines,
            alignment_format=args.alignment_format
        )

        examples = loader.load(split=args.split)

        # Convert to GCACU format
        convert_to_gcacu_format(examples, Path(args.output_file))

        print(f"\n✓ Loaded {len(examples)} examples from {args.split} split")
        print(f"✓ Statistics: {loader.stats}")
        print(f"✓ Saved GCACU format to {args.output_file}")

        # Show sample example
        if examples:
            sample = examples[0]
            print(f"\nSample example:")
            print(f"  ID: {sample.example_id}")
            print(f"  Words: {len(sample.words)}")
            print(f"  Laughter labels: {sum(sample.labels)}")
            print(f"  Has alignment: {sample.has_alignment()}")
            print(f"  Has punchlines: {sample.has_punchlines()}")
            print(f"  Punchline count: {len(sample.punchlines)}")

            if sample.has_punchlines():
                print(f"  Sample punchline:")
                pl = sample.punchlines[0]
                print(f"    Position: [{pl.punchline_start}:{pl.punchline_end}]")
                print(f"    Humor score: {pl.humor_score:.2f}")
                punchline_words = pl.get_punchline_words(sample.words)
                print(f"    Text: {' '.join(punchline_words)}")

                if sample.has_alignment():
                    print(f"  Alignment available:")
                    print(f"    Words: {len(sample.alignment.words)}")
                    print(f"    Duration: {sample.alignment.get_total_duration():.2f}s")