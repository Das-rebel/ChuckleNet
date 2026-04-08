"""
UR-FUNNY TED Dataset Setup and Download Guide

This script provides instructions and utilities for setting up the UR-FUNNY TED dataset
for multimodal humor detection benchmark evaluation.

Dataset Details:
- Paper: "UR-FUNNY: A Large-Scale Dataset for Humor Detection in TED Talks"
- Citation: Hasanhussain et al., EMNLP-IJCNLP 2019
- 1,866 TED videos with multimodal features
- 16,514 humor-labeled instances
- Published baseline: 65.23% accuracy (C-MFN)
"""

import os
import json
import shutil
from pathlib import Path
from typing import Dict, List
import urllib.request
import zipfile


def create_ur_funny_dataset_structure(base_path: str = "./data/ur_funny_ted"):
    """
    Create the directory structure for UR-FUNNY TED dataset.

    Expected structure:
    ur_funny_ted/
    ├── annotations/
    │   ├── train.csv
    │   ├── val.csv
    │   └── test.csv
    ├── features/
    │   ├── audio_features.npy
    │   └── visual_features.npy
    ├── videos/ (optional)
    └── audio/ (optional)
    """
    base_path = Path(base_path)
    base_path.mkdir(parents=True, exist_ok=True)

    # Create subdirectories
    (base_path / 'annotations').mkdir(exist_ok=True)
    (base_path / 'features').mkdir(exist_ok=True)
    (base_path / 'videos').mkdir(exist_ok=True)
    (base_path / 'audio').mkdir(exist_ok=True)

    print(f"Created UR-FUNNY TED dataset structure at: {base_path}")
    print("\nExpected structure:")
    print("  annotations/    - Train/val/test split annotations")
    print("  features/       - Precomputed audio and visual features")
    print("  videos/         - Raw video files (optional)")
    print("  audio/          - Raw audio files (optional)")

    return str(base_path)


def create_sample_annotations(data_path: str, split: str = 'train', num_samples: int = 100):
    """
    Create sample annotation files for testing the pipeline.

    This is for development/testing. For actual benchmark evaluation,
    you need the real UR-FUNNY TED dataset from the authors.
    """
    import pandas as pd
    import numpy as np

    data_path = Path(data_path)
    annotations_dir = data_path / 'annotations'
    annotations_dir.mkdir(parents=True, exist_ok=True)

    # Create sample annotations
    samples = []

    for i in range(num_samples):
        sample = {
            'video_id': f'ted_{split}_{i:04d}',
            'text': f"This is a sample transcript from a TED talk for testing the {split} split.",
            'humor': np.random.randint(0, 2),  # Binary humor label
            'speaker': f'speaker_{np.random.randint(1, 20)}',
            'title': f'Sample TED Talk {i}',
            'url': f'https://www.ted.com/talks/sample_{i}',
            'audio_feature_idx': i,
            'feature_idx': i
        }
        samples.append(sample)

    # Create DataFrame and save
    df = pd.DataFrame(samples)
    annotation_file = annotations_dir / f'{split}.csv'
    df.to_csv(annotation_file, index=False)

    print(f"Created sample annotation file: {annotation_file}")
    print(f"  Samples: {num_samples}")
    print(f"  Humor ratio: {df['humor'].mean():.2f}")

    return str(annotation_file)


def create_sample_features(data_path: str, num_samples: int = 100):
    """
    Create sample feature files for testing the pipeline.

    This creates dummy features for development. For real evaluation,
    you need actual extracted features from the UR-FUNNY TED dataset.
    """
    import numpy as np

    data_path = Path(data_path)
    features_dir = data_path / 'features'
    features_dir.mkdir(parents=True, exist_ok=True)

    # Create dummy audio features (MFCC-like: 128 dimensions)
    audio_features = np.random.randn(num_samples, 128).astype(np.float32)
    audio_file = features_dir / 'audio_features.npy'
    np.save(audio_file, audio_features)
    print(f"Created sample audio features: {audio_file}")
    print(f"  Shape: {audio_features.shape}")

    # Create dummy visual features (512 dimensions)
    visual_features = np.random.randn(num_samples, 512).astype(np.float32)
    visual_file = features_dir / 'visual_features.npy'
    np.save(visual_file, visual_features)
    print(f"Created sample visual features: {visual_file}")
    print(f"  Shape: {visual_features.shape}")

    return str(audio_file), str(visual_file)


def create_complete_sample_dataset(base_path: str = "./data/ur_funny_ted_sample"):
    """
    Create a complete sample UR-FUNNY TED dataset for testing.

    This creates dummy data for development and testing.
    For actual benchmark evaluation, obtain the real dataset.
    """
    print("="*70)
    print("Creating Sample UR-FUNNY TED Dataset")
    print("="*70)

    # Create directory structure
    data_path = create_ur_funny_dataset_structure(base_path)

    # Create splits
    splits = {
        'train': 800,
        'val': 200,
        'test': 400
    }

    for split, num_samples in splits.items():
        print(f"\nCreating {split} split...")
        create_sample_annotations(data_path, split, num_samples)

    # Create features (total samples)
    total_samples = sum(splits.values())
    print(f"\nCreating features for {total_samples} samples...")
    create_sample_features(data_path, total_samples)

    print("\n" + "="*70)
    print("Sample dataset created successfully!")
    print(f"Location: {base_path}")
    print("="*70)

    print("\n⚠️  NOTE: This is sample data for testing only.")
    print("For actual benchmark evaluation, you need the real UR-FUNNY TED dataset.")
    print("See get_real_dataset() instructions below.")

    return str(data_path)


def get_real_dataset_instructions():
    """
    Print instructions for obtaining the real UR-FUNNY TED dataset.
    """
    print("\n" + "="*70)
    print("HOW TO OBTAIN THE REAL UR-FUNNY TED DATASET")
    print("="*70)

    print("\n1. Academic Paper Access:")
    print("   Paper: 'UR-FUNNY: A Large-Scale Dataset for Humor Detection'")
    print("   Authors: Hasanhussain et al.")
    print("   Venue: EMNLP-IJCNLP 2019")
    print("   Link: https://aclanthology.org/D19-1211/")

    print("\n2. Dataset Access Options:")
    print("   a) Official Repository:")
    print("      - Check the paper's official code repository")
    print("      - Often available on GitHub")
    print()
    print("   b) Direct Request:")
    print("      - Contact the authors directly")
    print("      - Request access to the dataset")
    print()
    print("   c) Academic Access:")
    print("      - Available through academic databases")
    print("      - Check with your institution's library")

    print("\n3. Dataset Contents (when obtained):")
    print("   - 1,866 TED video IDs")
    print("   - 16,514 humor-labeled instances")
    print("   - Text transcripts")
    print("   - Audio features (precomputed)")
    print("   - Visual features (precomputed)")
    print("   - Train/val/test splits")

    print("\n4. Expected File Format:")
    print("   annotations/train.csv - Columns: video_id, text, humor, speaker, title, url")
    print("   annotations/val.csv   - Same format as train")
    print("   annotations/test.csv  - Same format as train")
    print("   features/audio_features.npy - Shape: [num_samples, 128]")
    print("   features/visual_features.npy - Shape: [num_samples, 512]")

    print("\n5. Setting Up the Real Dataset:")
    print("   a) Download and extract the dataset")
    print("   b) Organize files into the expected structure:")
    print("      mkdir -p data/ur_funny_ted/annotations")
    print("      mkdir -p data/ur_funny_ted/features")
    print("      cp train.csv data/ur_funny_ted/annotations/")
    print("      cp val.csv data/ur_funny_ted/annotations/")
    print("      cp test.csv data/ur_funny_ted/annotations/")
    print("      cp audio_features.npy data/ur_funny_ted/features/")
    print("      cp visual_features.npy data/ur_funny_ted/features/")
    print("   c) Verify the setup:")
    print("      python benchmarks/verify_ur_funny_ted.py --data_path data/ur_funny_ted")

    print("\n6. Citation:")
    print("   If you use this dataset, please cite:")
    print("   @inproceedings{hasanhussain-2019-ur-funny,")
    print("       title={{UR-FUNNY: A Large-Scale Dataset for Humor Detection}},")
    print("       author={Hasanhussain, Mohammed and others},")
    print("       booktitle={Proceedings of EMNLP-IJCNLP},")
    print("       year={2019}")
    print("   }")

    print("\n" + "="*70)


def verify_dataset_setup(data_path: str) -> bool:
    """
    Verify that the UR-FUNNY TED dataset is properly set up.

    Args:
        data_path: Path to UR-FUNNY TED dataset

    Returns:
        True if dataset is properly set up, False otherwise
    """
    data_path = Path(data_path)

    print("\n" + "="*70)
    print("VERIFYING UR-FUNNY TED DATASET SETUP")
    print("="*70)

    required_files = {
        'annotations': ['train.csv', 'val.csv', 'test.csv'],
        'features': ['audio_features.npy', 'visual_features.npy']
    }

    all_present = True

    for subdir, files in required_files.items():
        subdir_path = data_path / subdir
        print(f"\nChecking {subdir}/:")

        if not subdir_path.exists():
            print(f"  ❌ Directory not found: {subdir_path}")
            all_present = False
            continue

        print(f"  ✅ Directory exists: {subdir_path}")

        for file in files:
            file_path = subdir_path / file
            if file_path.exists():
                size = file_path.stat().st_size
                print(f"  ✅ {file} ({size:,} bytes)")
            else:
                print(f"  ❌ {file} NOT FOUND")
                all_present = False

    print("\n" + "="*70)
    if all_present:
        print("✅ Dataset setup verification PASSED")
    else:
        print("❌ Dataset setup verification FAILED")
        print("\nMissing files. Please ensure all required files are present.")
        print("Run get_real_dataset_instructions() for more information.")

    print("="*70)

    return all_present


def print_benchmark_info():
    """Print detailed information about the UR-FUNNY TED benchmark."""
    print("\n" + "="*70)
    print("UR-FUNNY TED BENCHMARK INFORMATION")
    print("="*70)

    print("\n📊 Dataset Statistics:")
    print("  Total Videos: 1,866")
    print("  Total Instances: 16,514")
    print("  Task: Multimodal humor detection (binary classification)")
    print("  Features: Text + Audio + Visual")

    print("\n🎯 Evaluation Metrics:")
    print("  Primary Metric: Binary classification accuracy")
    print("  Published Baseline: 65.23% (C-MFN model)")
    print("  Human Performance: 82.5%")
    print("  Target: Beat or match 65.23%")

    print("\n🔬 Model Architectures:")
    print("  Early Fusion: Concatenate features before classification")
    print("  Late Fusion: Separate modalities with combined prediction")
    print("  Cross-Modal Attention: Attention mechanism across modalities")

    print("\n📋 Evaluation Protocol:")
    print("  1. Load UR-FUNNY TED dataset with proper splits")
    print("  2. Extract/use precomputed multimodal features")
    print("  3. Train multimodal humor detection model")
    print("  4. Evaluate on test set")
    print("  5. Compare accuracy to 65.23% C-MFN baseline")

    print("\n⚡ Quick Start:")
    print("  1. Setup dataset:")
    print("     python benchmarks/setup_ur_funny_ted.py --create_sample")
    print()
    print("  2. Run benchmark:")
    print("     python benchmarks/ur_funny_ted_benchmark.py \\")
    print("       --data_path data/ur_funny_ted_sample \\")
    print("       --model_type early_fusion")
    print()
    print("  3. Get real dataset instructions:")
    print("     python benchmarks/setup_ur_funny_ted.py --real_instructions")

    print("\n" + "="*70)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='UR-FUNNY TED Dataset Setup')
    parser.add_argument('--create_sample', action='store_true',
                       help='Create sample dataset for testing')
    parser.add_argument('--real_instructions', action='store_true',
                       help='Print instructions for obtaining real dataset')
    parser.add_argument('--verify', type=str,
                       help='Verify dataset setup at given path')
    parser.add_argument('--info', action='store_true',
                       help='Print benchmark information')
    parser.add_argument('--base_path', type=str, default='./data/ur_funny_ted_sample',
                       help='Base path for dataset creation')

    args = parser.parse_args()

    if args.info:
        print_benchmark_info()

    elif args.real_instructions:
        get_real_dataset_instructions()

    elif args.create_sample:
        create_complete_sample_dataset(args.base_path)

    elif args.verify:
        verify_dataset_setup(args.verify)

    else:
        # Default: show info
        print_benchmark_info()
        print("\nUse --help to see available options")