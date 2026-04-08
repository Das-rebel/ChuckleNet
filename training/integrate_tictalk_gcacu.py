#!/usr/bin/env python3
"""
TIC-TALK Integration with GCACU Training Pipeline

This module provides integration utilities to use TIC-TALK dataset
with the existing GCACU training infrastructure.

Features:
- Convert TIC-TALK examples to GCACU StandupExample format
- Create PyTorch datasets with optional kinematic features
- Support for both text-only and multimodal training
- Data augmentation and preprocessing utilities
- Batch processing with proper alignment

Author: Autonomous Laughter Prediction Team
Date: 2025-04-03
"""

import sys
import torch
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from torch.utils.data import Dataset

# Add training directory to path
sys.path.insert(0, str(Path(__file__).parent))

from load_tic_talk import (
    TICTalkLoader,
    TICTalkExample,
    KinematicSignals,
    LaughterType
)
from gcacu_network import GCACUConfig


class TICTalkGCACUDataset(Dataset):
    """PyTorch Dataset for TIC-TALK examples compatible with GCACU training.

    This dataset handles both text-only and multimodal modes, with proper
    tokenization and label alignment.
    """

    def __init__(
        self,
        examples: List[TICTalkExample],
        tokenizer,
        max_length: int = 256,
        use_kinematics: bool = False,
        kinematic_feature_dim: int = 64,
        label_noise_prob: float = 0.0
    ):
        """Initialize TIC-TALK GCACU dataset.

        Args:
            examples: List of TIC-TALK examples
            tokenizer: HuggingFace tokenizer
            max_length: Maximum sequence length
            use_kinematics: Whether to use kinematic features
            kinematic_feature_dim: Dimension for kinematic feature projection
            label_noise_prob: Probability of flipping labels (for robustness)
        """
        self.examples = examples
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.use_kinematics = use_kinematics
        self.kinematic_feature_dim = kinematic_feature_dim
        self.label_noise_prob = label_noise_prob

        # Filter examples based on kinematic requirement
        if use_kinematics:
            self.examples = [ex for ex in examples if ex.has_kinematics()]
            if len(self.examples) < len(examples):
                print(f"Filtered to {len(self.examples)} examples with kinematics "
                      f"(from {len(examples)} total)")

        if not self.examples:
            raise ValueError("No examples remaining after filtering")

    def __len__(self) -> int:
        return len(self.examples)

    def __getitem__(self, index: int) -> Dict[str, Any]:
        """Get a single training example.

        Returns:
            Dictionary with input_ids, attention_mask, labels, and optional kinematics
        """
        example = self.examples[index]

        # Tokenize words
        encoding = self.tokenizer(
            example.words,
            is_split_into_words=True,
            truncation=True,
            max_length=self.max_length,
            padding='max_length',
            return_tensors='pt'
        )

        # Align labels with tokens
        labels = self._align_labels_with_tokens(
            example.labels,
            encoding.word_ids()
        )

        # Apply optional label noise
        if self.label_noise_prob > 0:
            labels = self._apply_label_noise(labels)

        item = {
            'input_ids': encoding['input_ids'].squeeze(0),
            'attention_mask': encoding['attention_mask'].squeeze(0),
            'labels': torch.tensor(labels, dtype=torch.long),
            'example_ids': example.example_id
        }

        # Add kinematic features if enabled
        if self.use_kinematics and example.has_kinematics():
            kinematic_features = self._process_kinematics(example.kinematics)
            item['kinematic_features'] = kinematic_features
        else:
            item['kinematic_features'] = torch.zeros(
                self.kinematic_feature_dim,
                dtype=torch.float
            )

        return item

    def _align_labels_with_tokens(
        self,
        word_labels: List[int],
        word_ids: List[Optional[int]]
    ) -> List[int]:
        """Align word-level labels with token-level labels.

        Args:
            word_labels: Word-level labels
            word_ids: Token to word mapping from tokenizer

        Returns:
            Token-level labels aligned with input tokens
        """
        label_map = {i: label for i, label in enumerate(word_labels)}
        labels = []

        for word_id in word_ids:
            if word_id is None:
                # Special tokens (CLS, SEP, padding)
                labels.append(-100)  # PyTorch ignore index
            else:
                labels.append(label_map.get(word_id, 0))

        return labels

    def _apply_label_noise(self, labels: List[int]) -> List[int]:
        """Apply random label noise for robustness training.

        Args:
            labels: Original labels

        Returns:
            Labels with random noise applied
        """
        if self.label_noise_prob <= 0:
            return labels

        noisy_labels = []
        for label in labels:
            if label != -100 and torch.rand(1).item() < self.label_noise_prob:
                # Flip label (0 -> 1, 1 -> 0)
                noisy_labels.append(1 - label)
            else:
                noisy_labels.append(label)

        return noisy_labels

    def _process_kinematics(self, kinematics: KinematicSignals) -> torch.Tensor:
        """Process kinematic signals into feature vector.

        Args:
            kinematics: Kinematic signals

        Returns:
            Feature tensor of shape (kinematic_feature_dim,)
        """
        # Compute statistical features from kinematic signals
        features = []

        # Arm spread features
        features.extend([
            kinematics.arm_spread.mean(),
            kinematics.arm_spread.std(),
            kinematics.arm_spread.max(),
            kinematics.arm_spread.min(),
            np.percentile(kinematics.arm_spread, 25),
            np.percentile(kinematics.arm_spread, 75)
        ])

        # Trunk lean features
        features.extend([
            kinematics.trunk_lean.mean(),
            kinematics.trunk_lean.std(),
            kinematics.trunk_lean.max(),
            kinematics.trunk_lean.min(),
            np.percentile(kinematics.trunk_lean, 25),
            np.percentile(kinematics.trunk_lean, 75)
        ])

        # Body movement features
        features.extend([
            kinematics.body_movement.mean(),
            kinematics.body_movement.std(),
            kinematics.body_movement.max(),
            kinematics.body_movement.min(),
            np.percentile(kinematics.body_movement, 25),
            np.percentile(kinematics.body_movement, 75)
        ])

        # Confidence features
        features.extend([
            kinematics.confidence.mean(),
            kinematics.confidence.std(),
            kinematics.confidence.min()
        ])

        # Temporal features
        if len(kinematics.timestamps) > 1:
            duration = kinematics.timestamps[-1] - kinematics.timestamps[0]
            features.extend([duration, len(kinematics.timestamps)])
        else:
            features.extend([0.0, 1])

        # Convert to tensor and pad/truncate to target dimension
        feature_tensor = torch.tensor(features, dtype=torch.float)

        if len(features) < self.kinematic_feature_dim:
            # Pad with zeros
            padding = torch.zeros(
                self.kinematic_feature_dim - len(features),
                dtype=torch.float
            )
            feature_tensor = torch.cat([feature_tensor, padding])
        elif len(features) > self.kinematic_feature_dim:
            # Truncate
            feature_tensor = feature_tensor[:self.kinematic_feature_dim]

        return feature_tensor


def convert_to_gcacu_examples(tictalk_examples: List[TICTalkExample]) -> List:
    """Convert TIC-TALK examples to GCACU StandupExample format.

    Args:
        tictalk_examples: List of TIC-TALK examples

    Returns:
        List of StandupExample objects compatible with GCACU training
    """
    from train_gcacu import StandupExample

    gcacu_examples = []
    for ex in tictalk_examples:
        # Create GCACU-compatible example
        gcacu_ex = StandupExample(
            example_id=ex.example_id,
            language=ex.language,
            words=ex.words,
            labels=ex.labels,
            **ex.metadata
        )
        gcacu_examples.append(gcacu_ex)

    return gcacu_examples


def create_tictalk_dataloaders(
    data_dir: Path,
    tokenizer,
    batch_size: int = 16,
    eval_batch_size: int = 8,
    max_length: int = 256,
    use_kinematics: bool = False,
    train_split: float = 0.8,
    seed: int = 42
) -> tuple:
    """Create training and validation dataloaders for TIC-TALK.

    Args:
        data_dir: Path to TIC-TALK data directory
        tokenizer: HuggingFace tokenizer
        batch_size: Training batch size
        eval_batch_size: Evaluation batch size
        max_length: Maximum sequence length
        use_kinematics: Whether to use kinematic features
        train_split: Training data split ratio
        seed: Random seed for reproducibility

    Returns:
        Tuple of (train_dataloader, eval_dataloader, dataset_info)
    """
    import torch
    from torch.utils.data import DataLoader, random_split

    # Set seed for reproducibility
    torch.manual_seed(seed)

    # Load TIC-TALK dataset
    loader = TICTalkLoader(
        data_dir=data_dir,
        enable_kinematics=use_kinematics,
        normalize_kinematics=True
    )

    examples = loader.load()

    if not examples:
        raise ValueError(f"No examples loaded from {data_dir}")

    # Create dataset
    dataset = TICTalkGCACUDataset(
        examples=examples,
        tokenizer=tokenizer,
        max_length=max_length,
        use_kinematics=use_kinematics
    )

    # Split into train and validation
    train_size = int(train_split * len(dataset))
    val_size = len(dataset) - train_size

    train_dataset, val_dataset = random_split(
        dataset,
        [train_size, val_size],
        generator=torch.Generator().manual_seed(seed)
    )

    # Create dataloaders
    train_dataloader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=0
    )

    val_dataloader = DataLoader(
        val_dataset,
        batch_size=eval_batch_size,
        shuffle=False,
        num_workers=0
    )

    # Dataset info
    dataset_info = {
        "total_examples": len(examples),
        "train_examples": train_size,
        "val_examples": val_size,
        "kinematic_usage": sum(1 for ex in examples if ex.has_kinematics()),
        "stats": loader.stats
    }

    return train_dataloader, val_dataloader, dataset_info


def update_gcacu_config_for_multimodal(base_config: GCACUConfig) -> GCACUConfig:
    """Update GCACU configuration to support multimodal input.

    Args:
        base_config: Base GCACU configuration

    Returns:
        Updated configuration with kinematic support
    """
    # Add kinematic-related parameters
    config_dict = base_config.__dict__.copy()

    config_dict.update({
        'use_kinematics': True,
        'kinematic_input_dim': 64,  # Match TICTalkGCACUDataset
        'kinematic_hidden_dim': 128,
        'kinematic_dropout': 0.1,
        'multimodal_fusion': 'concat'  # Options: 'concat', 'attention', 'gate'
    })

    return GCACUConfig(**config_dict)


def prepare_tictalk_for_training(
    data_dir: Path,
    output_dir: Path,
    model_name: str = "FacebookAI/xlm-roberta-base",
    use_kinematics: bool = False
) -> Dict[str, Any]:
    """Prepare TIC-TALK dataset for GCACU training.

    This is a convenience function that handles the entire preparation pipeline:
    1. Load TIC-TALK data
    2. Convert to GCACU format
    3. Save processed data
    4. Generate training configuration

    Args:
        data_dir: Path to TIC-TALK data directory
        output_dir: Path to save processed data
        model_name: HuggingFace model name for tokenizer
        use_kinematics: Whether to use kinematic features

    Returns:
        Dictionary with preparation results and configuration
    """
    from transformers import AutoTokenizer
    import json

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Preparing TIC-TALK dataset from {data_dir}")

    # Load dataset
    loader = TICTalkLoader(
        data_dir=data_dir,
        enable_kinematics=use_kinematics
    )

    examples = loader.load()

    if not examples:
        raise ValueError(f"No examples loaded from {data_dir}")

    # Initialize tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    # Create dataset
    dataset = TICTalkGCACUDataset(
        examples=examples,
        tokenizer=tokenizer,
        use_kinematics=use_kinematics
    )

    # Convert to GCACU format
    gcacu_examples = convert_to_gcacu_examples(examples)

    # Save examples
    output_file = output_dir / "tictalk_gcacu_examples.jsonl"
    from load_tic_talk import convert_to_gcacu_format
    convert_to_gcacu_format(
        examples,
        output_file,
        include_kinematics=use_kinematics
    )

    # Save dataset info
    dataset_info = {
        "data_dir": str(data_dir),
        "total_examples": len(examples),
        "kinematic_examples": sum(1 for ex in examples if ex.has_kinematics()),
        "use_kinematics": use_kinematics,
        "model_name": model_name,
        "max_length": 256,
        "statistics": loader.stats,
        "output_file": str(output_file)
    }

    info_file = output_dir / "dataset_info.json"
    with open(info_file, 'w') as f:
        json.dump(dataset_info, f, indent=2)

    # Generate training config
    config = update_gcacu_config_for_multimodal(GCACUConfig())

    print(f"✓ Prepared {len(examples)} examples")
    print(f"✓ Saved to {output_dir}")
    print(f"  - Examples: {output_file.name}")
    print(f"  - Info: {info_file.name}")
    print(f"  - Kinematics: {dataset_info['kinematic_examples']} examples")

    return {
        "examples": examples,
        "gcacu_examples": gcacu_examples,
        "dataset": dataset,
        "config": config,
        "info": dataset_info
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Integrate TIC-TALK with GCACU training pipeline"
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        required=True,
        help="Path to TIC-TALK dataset directory"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/tictalk_prepared",
        help="Output directory for prepared data"
    )
    parser.add_argument(
        "--model-name",
        type=str,
        default="FacebookAI/xlm-roberta-base",
        help="HuggingFace model name"
    )
    parser.add_argument(
        "--use-kinematics",
        action="store_true",
        help="Enable kinematic features"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=16,
        help="Batch size for dataloaders"
    )

    args = parser.parse_args()

    # Prepare dataset
    result = prepare_tictalk_for_training(
        data_dir=Path(args.data_dir),
        output_dir=Path(args.output_dir),
        model_name=args.model_name,
        use_kinematics=args.use_kinematics
    )

    print(f"\n✓ Dataset prepared successfully!")
    print(f"  Configuration: {result['config']}")
    print(f"  Ready for training with train_gcacu.py")