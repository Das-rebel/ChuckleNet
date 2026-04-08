#!/usr/bin/env python3
"""
TIC-TALK Dataset Loader for Autonomous Laughter Prediction

This module provides a comprehensive loader for the TIC-TALK dataset which contains:
- 5,400+ segments from 90 comedy specials
- Kinematic signals: arm spread, trunk lean, body movement
- Whisper-AT audio-based laughter detection
- Multimodal features (video + audio + text)

Features:
- Word-level alignment from Whisper-AT timestamps (0.8s resolution)
- Kinematic signal processing and normalization
- Support for both text-only and multimodal modes
- Integration with GCACU pipeline
- Comprehensive error handling and validation

Author: Autonomous Laughter Prediction Team
Date: 2025-04-03
"""

import json
import logging
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class LaughterType(Enum):
    """Types of laughter annotations in TIC-TALK."""
    CONTINUOUS = "continuous"  # Whisper-AT timestamp-based
    DISCRETE = "discrete"      # Word-level binary labels
    PROXIMITY = "proximity"    # Distance-based from laughter peaks


@dataclass
class KinematicSignals:
    """Kinematic signals from TIC-TALK dataset.

    Attributes:
        arm_spread: Arm spread measurements over time
        trunk_lean: Trunk lean angle measurements
        body_movement: Overall body movement intensity
        timestamps: Corresponding timestamps for signals
        confidence: Detection confidence scores
    """
    arm_spread: np.ndarray
    trunk_lean: np.ndarray
    body_movement: np.ndarray
    timestamps: np.ndarray
    confidence: np.ndarray

    def __post_init__(self):
        """Validate and normalize kinematic signals."""
        # Convert to numpy arrays if needed
        if not isinstance(self.arm_spread, np.ndarray):
            self.arm_spread = np.array(self.arm_spread, dtype=np.float32)
        if not isinstance(self.trunk_lean, np.ndarray):
            self.trunk_lean = np.array(self.trunk_lean, dtype=np.float32)
        if not isinstance(self.body_movement, np.ndarray):
            self.body_movement = np.array(self.body_movement, dtype=np.float32)
        if not isinstance(self.timestamps, np.ndarray):
            self.timestamps = np.array(self.timestamps, dtype=np.float32)
        if not isinstance(self.confidence, np.ndarray):
            self.confidence = np.array(self.confidence, dtype=np.float32)

        # Validate shapes
        n_samples = len(self.timestamps)
        if len(self.arm_spread) != n_samples:
            raise ValueError(f"Arm spread length {len(self.arm_spread)} != timestamps {n_samples}")
        if len(self.trunk_lean) != n_samples:
            raise ValueError(f"Trunk lean length {len(self.trunk_lean)} != timestamps {n_samples}")
        if len(self.body_movement) != n_samples:
            raise ValueError(f"Body movement length {len(self.body_movement)} != timestamps {n_samples}")

    def normalize(self) -> 'KinematicSignals':
        """Normalize signals to [0, 1] range.

        Returns:
            Normalized kinematic signals
        """
        def safe_normalize(arr: np.ndarray) -> np.ndarray:
            min_val, max_val = arr.min(), arr.max()
            if max_val - min_val < 1e-8:
                return np.zeros_like(arr)
            return (arr - min_val) / (max_val - min_val)

        return KinematicSignals(
            arm_spread=safe_normalize(self.arm_spread),
            trunk_lean=safe_normalize(self.trunk_lean),
            body_movement=safe_normalize(self.body_movement),
            timestamps=self.timestamps,
            confidence=self.confidence
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "arm_spread": self.arm_spread.tolist(),
            "trunk_lean": self.trunk_lean.tolist(),
            "body_movement": self.body_movement.tolist(),
            "timestamps": self.timestamps.tolist(),
            "confidence": self.confidence.tolist()
        }


@dataclass
class TICTalkExample:
    """Single example from TIC-TALK dataset.

    Attributes:
        example_id: Unique identifier (e.g., "tictalk_special001_seg005")
        words: List of words in the segment
        labels: Word-level laughter labels (0 or 1)
        language: Language code (default "en")
        metadata: Additional metadata
        kinematics: Optional kinematic signals
        word_timestamps: Optional word-level timestamps
        laughter_segments: Laughter segment timestamps from Whisper-AT
    """
    example_id: str
    words: List[str]
    labels: List[int]
    language: str = "en"
    metadata: Dict[str, Any] = field(default_factory=dict)
    kinematics: Optional[KinematicSignals] = None
    word_timestamps: Optional[List[Tuple[float, float]]] = None
    laughter_segments: List[Dict[str, float]] = field(default_factory=list)

    def __post_init__(self):
        """Validate example data."""
        if len(self.words) != len(self.labels):
            raise ValueError(
                f"Words/labels length mismatch for {self.example_id}: "
                f"{len(self.words)} != {len(self.labels)}"
            )

        if self.word_timestamps and len(self.word_timestamps) != len(self.words):
            logger.warning(
                f"Word timestamps length mismatch for {self.example_id}, "
                f"will be recalculated"
            )
            self.word_timestamps = None

    def has_kinematics(self) -> bool:
        """Check if example has kinematic signals."""
        return self.kinematics is not None

    def get_feature_dim(self) -> int:
        """Get total feature dimension for multimodal mode.

        Returns:
            Number of kinematic features (3 if available, 0 otherwise)
        """
        return 3 if self.has_kinematics() else 0


class TICTalkLoader:
    """Enhanced loader for TIC-TALK dataset.

    Expected directory structure:
    data/
        TIC-TALK/
            segments.json          # Main segment data
            kinematics.json        # Kinematic signals (optional)
            metadata.json          # Dataset metadata (optional)
            transcripts/           # Optional transcript files
            kinematics_raw/        # Optional raw kinematic data

    Expected JSON format for segments.json:
    [
        {
            "segment_id": "special001_seg005",
            "special_id": "special001",
            "comedian": "John Doe",
            "words": ["Hello", "world", ...],
            "word_timestamps": [[0.0, 0.5], [0.5, 1.0], ...],
            "laughter_timestamps": [[start, end], ...],
            "whisper_at_confidence": 0.85,
            "language": "en"
        },
        ...
    ]

    Expected JSON format for kinematics.json:
    {
        "special001_seg005": {
            "arm_spread": [0.1, 0.2, ...],
            "trunk_lean": [0.3, 0.4, ...],
            "body_movement": [0.5, 0.6, ...],
            "timestamps": [0.0, 0.1, ...],
            "confidence": [0.9, 0.8, ...]
        },
        ...
    }
    """

    def __init__(
        self,
        data_dir: Union[str, Path],
        enable_kinematics: bool = True,
        normalize_kinematics: bool = True,
        laughter_resolution: float = 0.8,
        cache_kinematics: bool = True
    ):
        """Initialize TIC-TALK loader.

        Args:
            data_dir: Path to TIC-TALK dataset directory
            enable_kinematics: Whether to load kinematic signals
            normalize_kinematics: Whether to normalize kinematic signals
            laughter_resolution: Whisper-AT resolution in seconds
            cache_kinematics: Whether to cache loaded kinematic data
        """
        self.data_dir = Path(data_dir)
        self.enable_kinematics = enable_kinematics
        self.normalize_kinematics = normalize_kinematics
        self.laughter_resolution = laughter_resolution
        self.cache_kinematics = cache_kinematics

        # Validate directory exists
        if not self.data_dir.exists():
            raise FileNotFoundError(f"TIC-TALK data directory not found: {self.data_dir}")

        # Cache for kinematic data
        self._kinematics_cache: Dict[str, KinematicSignals] = {}

        # Statistics
        self.stats = {
            "total_segments": 0,
            "segments_with_kinematics": 0,
            "segments_with_laughter": 0,
            "total_words": 0,
            "laughter_words": 0,
            "avg_segment_length": 0.0
        }

    def load(self) -> List[TICTalkExample]:
        """Load TIC-TALK dataset.

        Returns:
            List of TIC-TALK examples

        Raises:
            FileNotFoundError: If segments.json not found
            ValueError: If data format is invalid
        """
        segments_file = self.data_dir / "segments.json"

        if not segments_file.exists():
            raise FileNotFoundError(
                f"TIC-TALK segments file not found: {segments_file}\n"
                f"Expected structure: {self.data_dir}/segments.json"
            )

        logger.info(f"Loading TIC-TALK dataset from {segments_file}")

        try:
            with open(segments_file, 'r', encoding='utf-8') as f:
                segments = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in segments.json: {e}")

        if not isinstance(segments, list):
            raise ValueError(f"segments.json should contain a list, got {type(segments)}")

        logger.info(f"Found {len(segments)} segments in segments.json")

        # Load kinematic data if enabled
        kinematics_data = {}
        if self.enable_kinematics:
            kinematics_data = self._load_kinematics()

        # Process segments
        examples = []
        for segment in segments:
            try:
                example = self._process_segment(segment, kinematics_data)
                if example:
                    examples.append(example)
            except Exception as e:
                logger.warning(f"Failed to process segment: {e}")
                continue

        # Update statistics
        self._update_statistics(examples)

        logger.info(f"Successfully loaded {len(examples)} TIC-TALK examples")
        logger.info(f"Statistics: {self.stats}")

        return examples

    def _load_kinematics(self) -> Dict[str, KinematicSignals]:
        """Load kinematic signals from kinematics.json.

        Returns:
            Dictionary mapping segment_id to kinematic signals
        """
        kinematics_file = self.data_dir / "kinematics.json"

        if not kinematics_file.exists():
            logger.warning(f"Kinematics file not found: {kinematics_file}")
            return {}

        logger.info(f"Loading kinematic data from {kinematics_file}")

        try:
            with open(kinematics_file, 'r', encoding='utf-8') as f:
                kinematics_data = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in kinematics.json: {e}")
            return {}

        if not isinstance(kinematics_data, dict):
            logger.error(f"kinematics.json should contain a dict, got {type(kinematics_data)}")
            return {}

        logger.info(f"Found kinematic data for {len(kinematics_data)} segments")
        return kinematics_data

    def _process_segment(
        self,
        segment: Dict[str, Any],
        kinematics_data: Dict[str, Any]
    ) -> Optional[TICTalkExample]:
        """Process a single segment into a TICTalkExample.

        Args:
            segment: Segment data from JSON
            kinematics_data: Dictionary of kinematic signals

        Returns:
            TICTalkExample or None if processing fails
        """
        # Extract required fields
        segment_id = segment.get("segment_id")
        if not segment_id:
            logger.warning("Segment missing segment_id, skipping")
            return None

        words = segment.get("words", [])
        if not words:
            logger.warning(f"Segment {segment_id} has no words, skipping")
            return None

        # Extract timestamps and laughter data
        word_timestamps = segment.get("word_timestamps")
        laughter_timestamps = segment.get("laughter_timestamps", [])

        # Generate word-level labels
        if word_timestamps:
            labels = self._timestamps_to_word_labels(
                words, word_timestamps, laughter_timestamps
            )
        else:
            labels = self._timestamps_to_labels_simple(
                words, laughter_timestamps
            )

        # Extract kinematics
        kinematics = None
        if self.enable_kinematics and segment_id in kinematics_data:
            try:
                kinematics = self._process_kinematics(
                    kinematics_data[segment_id],
                    segment_id
                )
                if self.cache_kinematics:
                    self._kinematics_cache[segment_id] = kinematics
            except Exception as e:
                logger.warning(f"Failed to load kinematics for {segment_id}: {e}")

        # Build metadata
        metadata = {
            "source": "TIC-TALK",
            "segment_id": segment_id,
            "special_id": segment.get("special_id", ""),
            "comedian": segment.get("comedian", "Unknown"),
            "laughter_type": LaughterType.CONTINUOUS.value,
            "whisper_at_confidence": segment.get("whisper_at_confidence", 0.0),
            "has_kinematics": kinematics is not None,
            "has_word_timestamps": word_timestamps is not None
        }

        return TICTalkExample(
            example_id=f"tictalk_{segment_id}",
            words=[str(w) for w in words],
            labels=[int(l) for l in labels],
            language=segment.get("language", "en"),
            metadata=metadata,
            kinematics=kinematics,
            word_timestamps=word_timestamps,
            laughter_segments=laughter_timestamps
        )

    def _timestamps_to_word_labels(
        self,
        words: List[str],
        word_timestamps: List[Tuple[float, float]],
        laughter_timestamps: List[Dict[str, float]]
    ) -> List[int]:
        """Convert laughter timestamps to word-level labels using word timestamps.

        Args:
            words: List of words
            word_timestamps: Word-level timestamps [(start, end), ...]
            laughter_timestamps: Laughter segment timestamps

        Returns:
            Word-level labels (0 or 1)
        """
        if len(words) != len(word_timestamps):
            logger.warning(
                f"Word/timestamp mismatch: {len(words)} words, "
                f"{len(word_timestamps)} timestamps"
            )
            return self._timestamps_to_labels_simple(words, laughter_timestamps)

        labels = [0] * len(words)

        for laughter_seg in laughter_timestamps:
            laughter_start = laughter_seg.get("start", 0)
            laughter_end = laughter_seg.get("end", 0)

            # Find words that overlap with laughter
            for i, (word_start, word_end) in enumerate(word_timestamps):
                if self._temporal_overlap(word_start, word_end, laughter_start, laughter_end):
                    labels[i] = 1

        return labels

    def _timestamps_to_labels_simple(
        self,
        words: List[str],
        laughter_timestamps: List[Dict[str, float]]
    ) -> List[int]:
        """Convert laughter timestamps to word-level labels without word timestamps.

        Uses fixed resolution (0.8s) to approximate word positions.

        Args:
            words: List of words
            laughter_timestamps: Laughter segment timestamps

        Returns:
            Word-level labels (0 or 1)
        """
        labels = [0] * len(words)

        for laughter_seg in laughter_timestamps:
            start = laughter_seg.get("start", 0)
            end = laughter_seg.get("end", 0)

            word_start = int(start / self.laughter_resolution)
            word_end = int(end / self.laughter_resolution)

            # Clip to valid range
            word_start = max(0, min(word_start, len(labels) - 1))
            word_end = max(0, min(word_end, len(labels) - 1))

            for i in range(word_start, word_end + 1):
                labels[i] = 1

        return labels

    def _temporal_overlap(
        self,
        word_start: float,
        word_end: float,
        laughter_start: float,
        laughter_end: float
    ) -> bool:
        """Check if word temporally overlaps with laughter.

        Args:
            word_start: Word start time
            word_end: Word end time
            laughter_start: Laughter start time
            laughter_end: Laughter end time

        Returns:
            True if word overlaps with laughter
        """
        return not (word_end < laughter_start or word_start > laughter_end)

    def _process_kinematics(
        self,
        kinematic_data: Dict[str, Any],
        segment_id: str
    ) -> Optional[KinematicSignals]:
        """Process kinematic data for a segment.

        Args:
            kinematic_data: Raw kinematic data dictionary
            segment_id: Segment identifier

        Returns:
            KinematicSignals object or None if processing fails
        """
        try:
            arm_spread = kinematic_data.get("arm_spread", [])
            trunk_lean = kinematic_data.get("trunk_lean", [])
            body_movement = kinematic_data.get("body_movement", [])
            timestamps = kinematic_data.get("timestamps", [])
            confidence = kinematic_data.get("confidence", [])

            if not timestamps:
                logger.warning(f"Kinematics for {segment_id} missing timestamps")
                return None

            # Ensure equal length
            n_samples = len(timestamps)
            if len(arm_spread) != n_samples:
                arm_spread = [0.0] * n_samples
            if len(trunk_lean) != n_samples:
                trunk_lean = [0.0] * n_samples
            if len(body_movement) != n_samples:
                body_movement = [0.0] * n_samples
            if len(confidence) != n_samples:
                confidence = [1.0] * n_samples

            kinematics = KinematicSignals(
                arm_spread=arm_spread,
                trunk_lean=trunk_lean,
                body_movement=body_movement,
                timestamps=timestamps,
                confidence=confidence
            )

            if self.normalize_kinematics:
                kinematics = kinematics.normalize()

            return kinematics

        except Exception as e:
            logger.warning(f"Error processing kinematics for {segment_id}: {e}")
            return None

    def _update_statistics(self, examples: List[TICTalkExample]):
        """Update loading statistics.

        Args:
            examples: List of loaded examples
        """
        self.stats["total_segments"] = len(examples)
        self.stats["segments_with_kinematics"] = sum(
            1 for ex in examples if ex.has_kinematics()
        )
        self.stats["segments_with_laughter"] = sum(
            1 for ex in examples if any(ex.labels)
        )

        total_words = sum(len(ex.words) for ex in examples)
        laughter_words = sum(sum(ex.labels) for ex in examples)

        self.stats["total_words"] = total_words
        self.stats["laughter_words"] = laughter_words
        self.stats["avg_segment_length"] = total_words / len(examples) if examples else 0.0


def convert_to_gcacu_format(
    examples: List[TICTalkExample],
    output_file: Path,
    include_kinematics: bool = False
):
    """Convert TIC-TALK examples to GCACU-compatible JSONL format.

    Args:
        examples: List of TIC-TALK examples
        output_file: Output JSONL file path
        include_kinematics: Whether to include kinematic data
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

            if include_kinematics and ex.has_kinematics():
                record["kinematics"] = ex.kinematics.to_dict()

            f.write(json.dumps(record) + '\n')

    logger.info(f"Saved GCACU format to {output_file}")


def create_sample_tictalk_data(output_dir: Path, num_samples: int = 10):
    """Create sample TIC-TALK data for testing.

    Args:
        output_dir: Output directory for sample data
        num_samples: Number of sample segments to create
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create sample segments
    segments = []
    for i in range(num_samples):
        segment_id = f"special{i:03d}_seg{i:02d}"
        n_words = np.random.randint(10, 30)

        words = [f"word{j}" for j in range(n_words)]
        word_timestamps = [(j * 0.5, (j + 1) * 0.5) for j in range(n_words)]

        # Add some laughter segments
        laughter_segments = []
        if np.random.random() > 0.3:  # 70% have laughter
            n_laughter = np.random.randint(1, 3)
            for _ in range(n_laughter):
                start = np.random.uniform(0, n_words * 0.5 - 2)
                end = start + np.random.uniform(0.5, 2.0)
                laughter_segments.append({"start": start, "end": end})

        segment = {
            "segment_id": segment_id,
            "special_id": f"special{i:03d}",
            "comedian": f"Comedian {i}",
            "words": words,
            "word_timestamps": word_timestamps,
            "laughter_timestamps": laughter_segments,
            "whisper_at_confidence": np.random.uniform(0.7, 0.95),
            "language": "en"
        }
        segments.append(segment)

    # Save segments
    segments_file = output_dir / "segments.json"
    with open(segments_file, 'w', encoding='utf-8') as f:
        json.dump(segments, f, indent=2)

    # Create sample kinematics
    kinematics = {}
    for segment in segments:
        segment_id = segment["segment_id"]
        n_samples = len(segment["words"]) * 2  # Higher sampling rate

        kinematics[segment_id] = {
            "arm_spread": np.random.uniform(0, 1, n_samples).tolist(),
            "trunk_lean": np.random.uniform(-1, 1, n_samples).tolist(),
            "body_movement": np.random.uniform(0, 1, n_samples).tolist(),
            "timestamps": np.linspace(0, n_samples * 0.25, n_samples).tolist(),
            "confidence": np.random.uniform(0.8, 1.0, n_samples).tolist()
        }

    # Save kinematics
    kinematics_file = output_dir / "kinematics.json"
    with open(kinematics_file, 'w', encoding='utf-8') as f:
        json.dump(kinematics, f, indent=2)

    logger.info(f"Created sample TIC-TALK data in {output_dir}")
    logger.info(f"  - {len(segments)} segments")
    logger.info(f"  - {len(kinematics)} kinematic recordings")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="TIC-TALK Dataset Loader")
    parser.add_argument(
        "--data-dir",
        type=str,
        required=True,
        help="Path to TIC-TALK dataset directory"
    )
    parser.add_argument(
        "--output-file",
        type=str,
        default="tictalk_examples.jsonl",
        help="Output JSONL file for GCACU format"
    )
    parser.add_argument(
        "--no-kinematics",
        action="store_true",
        help="Disable kinematic signal loading"
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
        help="Number of sample segments to create"
    )

    args = parser.parse_args()

    if args.create_sample:
        # Create sample data
        create_sample_tictalk_data(Path(args.create_sample), args.num_samples)
        print(f"\nSample data created in {args.create_sample}")
        print("You can now test the loader with:")
        print(f"python load_tic_talk.py --data-dir {args.create_sample}")
    else:
        # Load TIC-TALK dataset
        loader = TICTalkLoader(
            data_dir=Path(args.data_dir),
            enable_kinematics=not args.no_kinematics
        )

        examples = loader.load()

        # Convert to GCACU format
        convert_to_gcacu_format(examples, Path(args.output_file))

        print(f"\n✓ Loaded {len(examples)} examples")
        print(f"✓ Statistics: {loader.stats}")
        print(f"✓ Saved GCACU format to {args.output_file}")

        # Show sample example
        if examples:
            sample = examples[0]
            print(f"\nSample example:")
            print(f"  ID: {sample.example_id}")
            print(f"  Words: {len(sample.words)}")
            print(f"  Laughter labels: {sum(sample.labels)}")
            print(f"  Has kinematics: {sample.has_kinematics()}")
            if sample.has_kinematics():
                print(f"  Kinematic samples: {len(sample.kinematics.timestamps)}")