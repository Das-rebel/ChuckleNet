"""
UR-FUNNY Dataset Implementation

UR-FUNNY is a large-scale dataset for humor detection in stand-up comedy,
with laughter annotations from Reddit reaction scores.

Dataset: Available through academic request
Paper: "UR-FUNNY: A Large-Scale Dataset for Humor Detection"
"""

import os
import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import torch

from ..utils.base_dataset import BaseBenchmarkDataset, DataSample


class URFunnyDataset(BaseBenchmarkDataset):
    """
    UR-FUNNY Dataset loader.

    Contains ~22K jokes from stand-up comedy with humor scores
    based on Reddit upvotes/downvotes.
    """

    def __init__(self,
                 data_path: str,
                 split: str = 'train',
                 use_binary_labels: bool = True,
                 humor_threshold: float = 0.5,
                 **kwargs):
        """
        Initialize UR-FUNNY dataset.

        Args:
            data_path: Path to UR-FUNNY data directory
            split: Dataset split ('train', 'val', 'test')
            use_binary_labels: Convert continuous humor scores to binary labels
            humor_threshold: Threshold for binary classification
        """
        self.use_binary_labels = use_binary_labels
        self.humor_threshold = humor_threshold

        super().__init__(data_path, split, **kwargs)

    def _load_data(self):
        """Load UR-FUNNY data samples"""
        data_path = Path(self.data_path)

        # UR-FUNNY typically has this structure:
        # - jokes_train.csv, jokes_val.csv, jokes_test.csv
        # - or combined CSV with split column

        # Try different file formats
        possible_files = [
            data_path / f'jokes_{self.split}.csv',
            data_path / f'{self.split}.csv',
            data_path / 'jokes.csv',
            data_path / 'ur_funny.csv'
        ]

        annotation_file = None
        for file_path in possible_files:
            if file_path.exists():
                annotation_file = file_path
                break

        if annotation_file is None:
            raise FileNotFoundError(f"UR-FUNNY annotation file not found for {self.split} split")

        # Load annotations
        if annotation_file.suffix == '.csv':
            annotations = pd.read_csv(annotation_file)
        elif annotation_file.suffix == '.json':
            with open(annotation_file, 'r') as f:
                annotations = json.load(f)
            annotations = pd.DataFrame(annotations)
        else:
            raise ValueError(f"Unsupported annotation format: {annotation_file.suffix}")

        # Filter by split if needed
        if 'split' in annotations.columns:
            annotations = annotations[annotations['split'] == self.split]

        # Load samples
        for _, row in annotations.iterrows():
            try:
                # Get joke text
                text = row.get('joke', row.get('text', row.get('joke_text', '')))
                if not text or text.isspace():
                    continue

                # Get label (humor score)
                humor_score = row.get('humor_score', row.get('score', row.get('funny_score', 0)))
                if pd.isna(humor_score):
                    humor_score = 0

                # Convert to binary if needed
                if self.use_binary_labels:
                    # Normalize score to [0, 1] and apply threshold
                    if isinstance(humor_score, (int, float)):
                        normalized_score = min(1.0, max(0.0, float(humor_score) / 10.0))  # Assuming 0-10 scale
                        label = 1 if normalized_score >= self.humor_threshold else 0
                    else:
                        label = 0
                else:
                    label = float(humor_score)

                # Get metadata
                metadata = {
                    'comedian': row.get('comedian', row.get('speaker', 'unknown')),
                    'show': row.get('show', 'unknown'),
                    'score': float(humor_score) if not pd.isna(humor_score) else 0.0,
                    'upvotes': row.get('upvotes', 0),
                    'downvotes': row.get('downvotes', 0),
                    'dataset': 'UR-FUNNY'
                }

                # Remove None values
                metadata = {k: v for k, v in metadata.items() if v is not None and not pd.isna(v)}

                # Create sample (text-only for UR-FUNNY)
                sample = DataSample(
                    text=text,
                    audio_path=None,  # UR-FUNNY is text-only
                    video_path=None,
                    label=label,
                    speaker_id=metadata.get('comedian'),
                    show_id=metadata.get('show'),
                    metadata=metadata
                )

                self.samples.append(sample)

            except Exception as e:
                print(f"Warning: Failed to load UR-FUNNY sample: {e}")
                continue

        print(f"Loaded {len(self.samples)} samples from UR-FUNNY {self.split} split")