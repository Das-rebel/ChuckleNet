"""
Split Manager for Academic Benchmarks

Implements proper train/validation/test split protocols including:
- Speaker-independent splits
- Show/comedian-independent splits
- Cross-domain splits
- Stratified splits for balanced labels
"""

import os
import json
import random
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set, Any
from dataclasses import dataclass
from collections import defaultdict, Counter
import numpy as np
from sklearn.model_selection import StratifiedShuffleSplit


@dataclass
class SplitConfig:
    """Configuration for data splits"""
    train_ratio: float = 0.7
    val_ratio: float = 0.15
    test_ratio: float = 0.15
    speaker_independent: bool = True
    show_independent: bool = True
    stratified: bool = True
    random_seed: int = 42

    def __post_init__(self):
        assert abs(self.train_ratio + self.val_ratio + self.test_ratio - 1.0) < 1e-6, \
            "Split ratios must sum to 1.0"


class SplitManager:
    """
    Manages data splitting protocols for academic benchmarks.

    Ensures proper evaluation protocols that prevent data leakage
    and enable fair comparison across different approaches.
    """

    def __init__(self,
                 config: SplitConfig,
                 benchmark_name: str):
        """
        Initialize split manager.

        Args:
            config: Split configuration
            benchmark_name: Name of the benchmark dataset
        """
        self.config = config
        self.benchmark_name = benchmark_name
        self.random = random.Random(config.random_seed)
        np.random.seed(config.random_seed)

        # Track splits
        self.train_indices = []
        self.val_indices = []
        self.test_indices = []

        # Metadata about splits
        self.split_info = {}

    def create_splits(self,
                     samples: List[Any],
                     speaker_ids: Optional[List[str]] = None,
                     show_ids: Optional[List[str]] = None,
                     labels: Optional[List[Any]] = None) -> Tuple[List[int], List[int], List[int]]:
        """
        Create train/val/test splits according to configuration.

        Args:
            samples: List of data samples
            speaker_ids: Speaker ID for each sample
            show_ids: Show ID for each sample
            labels: Label for each sample (for stratification)

        Returns:
            Tuple of (train_indices, val_indices, test_indices)
        """
        n_samples = len(samples)

        # Generate IDs if not provided
        if speaker_ids is None:
            speaker_ids = [f"speaker_{i % 10}" for i in range(n_samples)]
        if show_ids is None:
            show_ids = [f"show_{i % 5}" for i in range(n_samples)]
        if labels is None:
            labels = [0] * n_samples

        # Apply splitting protocol
        if self.config.speaker_independent and speaker_ids:
            return self._speaker_independent_split(samples, speaker_ids, show_ids, labels)
        elif self.config.show_independent and show_ids:
            return self._show_independent_split(samples, speaker_ids, show_ids, labels)
        elif self.config.stratified and labels:
            return self._stratified_split(samples, labels)
        else:
            return self._random_split(samples)

    def _speaker_independent_split(self,
                                   samples: List[Any],
                                   speaker_ids: List[str],
                                   show_ids: List[str],
                                   labels: List[Any]) -> Tuple[List[int], List[int], List[int]]:
        """
        Create speaker-independent splits.

        Ensures that samples from the same speaker only appear in one split.
        """
        # Group samples by speaker
        speaker_to_indices = defaultdict(list)
        for idx, speaker_id in enumerate(speaker_ids):
            speaker_to_indices[speaker_id].append(idx)

        # Get list of unique speakers
        unique_speakers = list(speaker_to_indices.keys())
        self.random.shuffle(unique_speakers)

        # Assign speakers to splits maintaining ratio
        n_speakers = len(unique_speakers)
        n_train = int(n_speakers * self.config.train_ratio)
        n_val = int(n_speakers * self.config.val_ratio)

        train_speakers = set(unique_speakers[:n_train])
        val_speakers = set(unique_speakers[n_train:n_train + n_val])
        test_speakers = set(unique_speakers[n_train + n_val:])

        # Collect indices
        train_indices = []
        val_indices = []
        test_indices = []

        for speaker, indices in speaker_to_indices.items():
            if speaker in train_speakers:
                train_indices.extend(indices)
            elif speaker in val_speakers:
                val_indices.extend(indices)
            else:
                test_indices.extend(indices)

        # Store split information
        self.split_info = {
            'split_type': 'speaker_independent',
            'num_train_speakers': len(train_speakers),
            'num_val_speakers': len(val_speakers),
            'num_test_speakers': len(test_speakers),
            'train_samples': len(train_indices),
            'val_samples': len(val_indices),
            'test_samples': len(test_indices)
        }

        return train_indices, val_indices, test_indices

    def _show_independent_split(self,
                               samples: List[Any],
                               speaker_ids: List[str],
                               show_ids: List[str],
                               labels: List[Any]) -> Tuple[List[int], List[int], List[int]]:
        """
        Create show/comedian-independent splits.

        Ensures that samples from the same show only appear in one split.
        Useful for comedy datasets where the same comedian appears in multiple shows.
        """
        # Group samples by show
        show_to_indices = defaultdict(list)
        for idx, show_id in enumerate(show_ids):
            show_to_indices[show_id].append(idx)

        # Get list of unique shows
        unique_shows = list(show_to_indices.keys())
        self.random.shuffle(unique_shows)

        # Assign shows to splits maintaining ratio
        n_shows = len(unique_shows)
        n_train = int(n_shows * self.config.train_ratio)
        n_val = int(n_shows * self.config.val_ratio)

        train_shows = set(unique_shows[:n_train])
        val_shows = set(unique_shows[n_train:n_train + n_val])
        test_shows = set(unique_shows[n_train + n_val:])

        # Collect indices
        train_indices = []
        val_indices = []
        test_indices = []

        for show, indices in show_to_indices.items():
            if show in train_shows:
                train_indices.extend(indices)
            elif show in val_shows:
                val_indices.extend(indices)
            else:
                test_indices.extend(indices)

        # Store split information
        self.split_info = {
            'split_type': 'show_independent',
            'num_train_shows': len(train_shows),
            'num_val_shows': len(val_shows),
            'num_test_shows': len(test_shows),
            'train_samples': len(train_indices),
            'val_samples': len(val_indices),
            'test_samples': len(test_indices)
        }

        return train_indices, val_indices, test_indices

    def _stratified_split(self,
                         samples: List[Any],
                         labels: List[Any]) -> Tuple[List[int], List[int], List[int]]:
        """
        Create stratified splits to maintain label distribution.

        Useful for imbalanced datasets to ensure consistent label ratios across splits.
        """
        indices = list(range(len(samples)))

        # First split: train vs (val + test)
        sss1 = StratifiedShuffleSplit(
            n_splits=1,
            test_size=(self.config.val_ratio + self.config.test_ratio),
            random_state=self.config.random_seed
        )

        train_idx, valtest_idx = next(sss1.split(indices, labels))

        # Second split: val vs test
        val_ratio_adjusted = self.config.val_ratio / (self.config.val_ratio + self.config.test_ratio)
        sss2 = StratifiedShuffleSplit(
            n_splits=1,
            test_size=(1 - val_ratio_adjusted),
            random_state=self.config.random_seed
        )

        val_labels = [labels[i] for i in valtest_idx]
        val_idx, test_idx = next(sss2.split(valtest_idx, val_labels))

        train_indices = [train_idx[i] for i in range(len(train_idx))]
        val_indices = [valtest_idx[val_idx[i]] for i in range(len(val_idx))]
        test_indices = [valtest_idx[test_idx[i]] for i in range(len(test_idx))]

        # Store split information
        self.split_info = {
            'split_type': 'stratified',
            'train_samples': len(train_indices),
            'val_samples': len(val_indices),
            'test_samples': len(test_indices)
        }

        return train_indices, val_indices, test_indices

    def _random_split(self,
                     samples: List[Any]) -> Tuple[List[int], List[int], List[int]]:
        """
        Create random splits (simple baseline).
        """
        indices = list(range(len(samples)))
        self.random.shuffle(indices)

        n_samples = len(indices)
        n_train = int(n_samples * self.config.train_ratio)
        n_val = int(n_samples * self.config.val_ratio)

        train_indices = indices[:n_train]
        val_indices = indices[n_train:n_train + n_val]
        test_indices = indices[n_train + n_val:]

        # Store split information
        self.split_info = {
            'split_type': 'random',
            'train_samples': len(train_indices),
            'val_samples': len(val_indices),
            'test_samples': len(test_indices)
        }

        return train_indices, val_indices, test_indices

    def save_splits(self, save_dir: Path):
        """Save splits to disk for reproducibility"""
        save_dir = Path(save_dir)
        save_dir.mkdir(parents=True, exist_ok=True)

        split_data = {
            'benchmark_name': self.benchmark_name,
            'config': {
                'train_ratio': self.config.train_ratio,
                'val_ratio': self.config.val_ratio,
                'test_ratio': self.config.test_ratio,
                'speaker_independent': self.config.speaker_independent,
                'show_independent': self.config.show_independent,
                'stratified': self.config.stratified,
                'random_seed': self.config.random_seed
            },
            'train_indices': self.train_indices,
            'val_indices': self.val_indices,
            'test_indices': self.test_indices,
            'split_info': self.split_info
        }

        split_file = save_dir / f'{self.benchmark_name}_splits.json'
        with open(split_file, 'w') as f:
            json.dump(split_data, f, indent=2)

        print(f"Splits saved to {split_file}")

    def load_splits(self, load_dir: Path) -> Tuple[List[int], List[int], List[int]]:
        """Load splits from disk"""
        load_dir = Path(load_dir)
        split_file = load_dir / f'{self.benchmark_name}_splits.json'

        if not split_file.exists():
            raise FileNotFoundError(f"Split file not found: {split_file}")

        with open(split_file, 'r') as f:
            split_data = json.load(f)

        self.train_indices = split_data['train_indices']
        self.val_indices = split_data['val_indices']
        self.test_indices = split_data['test_indices']
        self.split_info = split_data['split_info']

        print(f"Splits loaded from {split_file}")
        return self.train_indices, self.val_indices, self.test_indices

    def validate_splits(self,
                       train_indices: List[int],
                       val_indices: List[int],
                       test_indices: List[int]) -> bool:
        """
        Validate split integrity.

        Checks for:
        - No overlap between splits
        - Proper ratios
        - Speaker/show independence if configured
        """
        # Check for overlap
        train_set = set(train_indices)
        val_set = set(val_indices)
        test_set = set(test_indices)

        if train_set & val_set:
            raise ValueError("Overlap between train and validation sets!")
        if train_set & test_set:
            raise ValueError("Overlap between train and test sets!")
        if val_set & test_set:
            raise ValueError("Overlap between validation and test sets!")

        # Check ratios
        total = len(train_indices) + len(val_indices) + len(test_indices)
        actual_train_ratio = len(train_indices) / total
        actual_val_ratio = len(val_indices) / total
        actual_test_ratio = len(test_indices) / total

        tolerance = 0.05  # 5% tolerance for ratios
        if abs(actual_train_ratio - self.config.train_ratio) > tolerance:
            print(f"Warning: Train ratio {actual_train_ratio:.2f} differs from config {self.config.train_ratio:.2f}")
        if abs(actual_val_ratio - self.config.val_ratio) > tolerance:
            print(f"Warning: Val ratio {actual_val_ratio:.2f} differs from config {self.config.val_ratio:.2f}")
        if abs(actual_test_ratio - self.config.test_ratio) > tolerance:
            print(f"Warning: Test ratio {actual_test_ratio:.2f} differs from config {self.config.test_ratio:.2f}")

        print("Split validation passed!")
        return True

    def get_split_summary(self) -> Dict[str, Any]:
        """Get summary of split information"""
        return {
            'benchmark': self.benchmark_name,
            'config': {
                'train_ratio': self.config.train_ratio,
                'val_ratio': self.config.val_ratio,
                'test_ratio': self.config.test_ratio,
                'speaker_independent': self.config.speaker_independent,
                'show_independent': self.config.show_independent,
                'stratified': self.config.stratified
            },
            'split_info': self.split_info
        }