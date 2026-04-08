#!/usr/bin/env python3
"""
UR-FUNNY Dataset Loader - Quick Demo and Usage Guide

This script demonstrates how to use the UR-FUNNY dataset loader for
autonomous laughter prediction with GCACU pipeline integration.

Usage Examples:
1. Create sample data and test the loader
2. Load real UR-FUNNY data (if available)
3. Convert to GCACU format for training
4. Extract punchline patterns for humor analysis

Author: Autonomous Laughter Prediction Team
Date: 2026-04-03
"""

import sys
import json
import tempfile
from pathlib import Path
import numpy as np

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from load_ur_funny import (
    URFunnyLoader,
    URFunnyExample,
    create_sample_ur_funny_data,
    convert_to_gcacu_format,
    HumorType,
    AlignmentFormat
)


def demo_sample_data_workflow():
    """Demonstrate complete workflow with sample data."""
    print("="*70)
    print("UR-FUNNY DATASET LOADER - SAMPLE DATA WORKFLOW")
    print("="*70)

    # Create temporary directory for sample data
    temp_dir = tempfile.mkdtemp()
    data_dir = Path(temp_dir) / "ur_funny_sample"

    print(f"\n📁 Creating sample data in: {data_dir}")

    # Step 1: Create sample data
    print("\n🔧 Step 1: Creating sample UR-FUNNY data...")
    create_sample_ur_funny_data(data_dir, num_samples=10)
    print("✓ Sample data created successfully")

    # Step 2: Initialize loader
    print("\n🔧 Step 2: Initializing UR-FUNNY loader...")
    loader = URFunnyLoader(
        data_dir=data_dir,
        enable_alignment=True,
        enable_punchlines=True,
        alignment_format="p2fa"
    )
    print("✓ Loader initialized")

    # Step 3: Load training data
    print("\n🔧 Step 3: Loading training data...")
    train_examples = loader.load(split="train")
    print(f"✓ Loaded {len(train_examples)} training examples")

    # Step 4: Analyze loaded data
    print("\n🔧 Step 4: Analyzing loaded data...")
    analyze_dataset(train_examples, "Training")

    # Step 5: Show example analysis
    print("\n🔧 Step 5: Analyzing sample examples...")
    show_example_analysis(train_examples[:3])

    # Step 6: Extract punchline patterns
    print("\n🔧 Step 6: Extracting punchline patterns...")
    extract_punchline_patterns(train_examples)

    # Step 7: Convert to GCACU format
    print("\n🔧 Step 7: Converting to GCACU format...")
    output_file = Path(temp_dir) / "urfunny_gcacu.jsonl"
    convert_to_gcacu_format(
        train_examples,
        output_file,
        include_alignment=True,
        include_punchlines=True
    )
    print(f"✓ GCACU format saved to: {output_file}")

    # Step 8: Validate GCACU format
    print("\n🔧 Step 8: Validating GCACU format...")
    validate_gcacu_format(output_file)

    print("\n" + "="*70)
    print("WORKFLOW COMPLETED SUCCESSFULLY!")
    print("="*70)

    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)

    return True


def analyze_dataset(examples, split_name):
    """Analyze dataset characteristics."""
    if not examples:
        print(f"⚠️  No examples to analyze for {split_name}")
        return

    print(f"\n📊 {split_name} Dataset Analysis:")
    print("-" * 50)

    # Basic statistics
    total_words = sum(len(ex.words) for ex in examples)
    total_laughter = sum(sum(ex.labels) for ex in examples)

    print(f"  Total examples: {len(examples)}")
    print(f"  Total words: {total_words:,}")
    print(f"  Laughter words: {total_laughter:,} ({100*total_laughter/total_words:.1f}%)")
    print(f"  Avg words/example: {total_words/len(examples):.1f}")

    # Alignment statistics
    with_alignment = sum(1 for ex in examples if ex.has_alignment())
    print(f"  With alignment: {with_alignment} ({100*with_alignment/len(examples):.1f}%)")

    # Punchline statistics
    with_punchlines = sum(1 for ex in examples if ex.has_punchlines())
    total_punchlines = sum(len(ex.punchlines) for ex in examples)
    print(f"  With punchlines: {with_punchlines} ({100*with_punchlines/len(examples):.1f}%)")
    print(f"  Total punchlines: {total_punchlines}")

    # Humor score distribution
    humor_scores = [
        ex.metadata.get("humor_score", 0.0)
        for ex in examples
        if "humor_score" in ex.metadata
    ]
    if humor_scores:
        print(f"  Avg humor score: {np.mean(humor_scores):.3f}")
        print(f"  Min/Max humor: {np.min(humor_scores):.3f} / {np.max(humor_scores):.3f}")

    # Language distribution
    languages = {}
    for ex in examples:
        lang = ex.language
        languages[lang] = languages.get(lang, 0) + 1

    print(f"  Languages: {', '.join(f'{k}({v})' for k, v in languages.items())}")


def show_example_analysis(examples):
    """Show detailed analysis of sample examples."""
    for i, ex in enumerate(examples, 1):
        print(f"\n🔍 Example {i}: {ex.example_id}")
        print("-" * 40)

        # Basic info
        print(f"  Words: {len(ex.words)}")
        print(f"  Laughter labels: {sum(ex.labels)} ({100*sum(ex.labels)/len(ex.labels):.1f}%)")
        print(f"  Language: {ex.language}")

        # Alignment info
        if ex.has_alignment():
            print(f"  Alignment: ✓")
            print(f"    Duration: {ex.alignment.get_total_duration():.2f}s")
            print(f"    Words: {len(ex.alignment.words)}")
            avg_confidence = np.mean(ex.alignment.confidence)
            print(f"    Avg confidence: {avg_confidence:.3f}")
        else:
            print(f"  Alignment: ✗")

        # Punchline info
        if ex.has_punchlines():
            print(f"  Punchlines: {len(ex.punchlines)}")
            for j, pl in enumerate(ex.punchlines, 1):
                punchline_words = pl.get_punchline_words(ex.words)
                print(f"    [{j}] Position: [{pl.punchline_start}:{pl.punchline_end}]")
                print(f"        Humor score: {pl.humor_score:.3f}")
                print(f"        Laughter intensity: {pl.laughter_intensity:.3f}")
                print(f"        Text: {' '.join(punchline_words)}")
        else:
            print(f"  Punchlines: ✗")

        # Laughter segments
        segments = ex.get_laughter_segments()
        if segments:
            print(f"  Laughter segments: {len(segments)}")
            for j, seg in enumerate(segments, 1):
                print(f"    [{j}] Words {seg['start_word']}-{seg['end_word']}: {' '.join(seg['words'])}")

        # Show first few words
        preview_words = ex.words[:10]
        preview_labels = ex.labels[:10]
        print(f"  Preview: {' '.join(f'{w}({l})' for w, l in zip(preview_words, preview_labels))}")


def extract_punchline_patterns(examples):
    """Extract and analyze punchline patterns."""
    examples_with_punchlines = [ex for ex in examples if ex.has_punchlines()]

    if not examples_with_punchlines:
        print("⚠️  No punchlines found in dataset")
        return

    print(f"\n🎯 Punchline Pattern Analysis ({len(examples_with_punchlines)} examples):")
    print("-" * 50)

    # Collect punchline statistics
    punchline_lengths = []
    context_lengths = []
    humor_scores = []
    laughter_intensities = []

    for ex in examples_with_punchlines:
        for pl in ex.punchlines:
            punchline_length = pl.punchline_end - pl.punchline_start + 1
            context_length = pl.context_end - pl.context_start + 1

            punchline_lengths.append(punchline_length)
            context_lengths.append(context_length)
            humor_scores.append(pl.humor_score)
            laughter_intensities.append(pl.laughter_intensity)

    print(f"  Punchline length: {np.mean(punchline_lengths):.1f} ± {np.std(punchline_lengths):.1f} words")
    print(f"  Context length: {np.mean(context_lengths):.1f} ± {np.std(context_lengths):.1f} words")
    print(f"  Humor scores: {np.mean(humor_scores):.3f} ± {np.std(humor_scores):.3f}")
    print(f"  Laughter intensity: {np.mean(laughter_intensities):.3f} ± {np.std(laughter_intensities):.3f}")

    # Context window analysis
    print(f"\n📝 Context Window Analysis:")
    for ex in examples_with_punchlines[:3]:  # Show first 3 examples
        contexts = ex.get_context_windows(window_size=5)
        if contexts:
            print(f"  {ex.example_id}:")
            for j, ctx in enumerate(contexts[:2], 1):  # Show first 2 contexts
                punchline_start = ctx['punchline_start_rel']
                punchline_end = ctx['punchline_end_rel']
                punchline_text = ' '.join(ctx['context_words'][punchline_start:punchline_end+1])
                print(f"    Context {j}: ...{' '.join(ctx['context_words'][:punchline_start])} "
                      f"[{punchline_text}] "
                      f"{' '.join(ctx['context_words'][punchline_end+1:])}...")


def validate_gcacu_format(output_file):
    """Validate GCACU format output."""
    if not output_file.exists():
        print(f"❌ Output file not found: {output_file}")
        return False

    print(f"✓ GCACU file exists: {output_file}")

    # Read and validate format
    with open(output_file, 'r') as f:
        lines = f.readlines()

    print(f"✓ Total records: {len(lines)}")

    # Validate first few records
    valid_records = 0
    for i, line in enumerate(lines[:5], 1):
        try:
            record = json.loads(line.strip())

            # Check required fields
            required_fields = ["example_id", "language", "words", "labels", "metadata"]
            if all(field in record for field in required_fields):
                valid_records += 1

                # Show sample record structure
                if i == 1:
                    print(f"✓ Sample record structure:")
                    print(f"    example_id: {record['example_id']}")
                    print(f"    words: {len(record['words'])}")
                    print(f"    labels: {len(record['labels'])}")
                    print(f"    metadata keys: {list(record['metadata'].keys())}")
                    if "alignment" in record:
                        print(f"    alignment: ✓ ({len(record['alignment']['words'])} words)")
                    if "punchlines" in record:
                        print(f"    punchlines: ✓ ({len(record['punchlines'])} punchlines)")

        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in record {i}: {e}")
            continue

    print(f"✓ Validated {valid_records}/{min(5, len(lines))} sample records")

    return True


def demo_usage_guide():
    """Print usage guide for UR-FUNNY loader."""
    print("\n" + "="*70)
    print("UR-FUNNY DATASET LOADER - USAGE GUIDE")
    print("="*70)

    print("\n📚 BASIC USAGE:")
    print("-" * 50)
    print("""
from load_ur_funny import URFunnyLoader, convert_to_gcacu_format
from pathlib import Path

# Initialize loader
loader = URFunnyLoader(
    data_dir=Path("path/to/ur_funny"),
    enable_alignment=True,    # Load P2FA forced alignments
    enable_punchlines=True,   # Load punchline annotations
    alignment_format="p2fa"   # Format: p2fa, json, csv, textgrid
)

# Load dataset
train_examples = loader.load(split="train")
val_examples = loader.load(split="val")

# Convert to GCACU format
convert_to_gcacu_format(
    train_examples,
    Path("urfunny_train.jsonl"),
    include_alignment=True,
    include_punchlines=True
)
    """)

    print("\n🔧 ADVANCED FEATURES:")
    print("-" * 50)
    print("""
# Extract punchline patterns
for example in examples:
    if example.has_punchlines():
        contexts = example.get_context_windows(window_size=5)
        for context in contexts:
            punchline_text = ' '.join(
                context['context_words'][
                    context['punchline_start_rel']:
                    context['punchline_end_rel']+1
                ]
            )
            print(f"Punchline: {punchline_text}")
            print(f"Humor score: {context['humor_score']}")

# Analyze laughter segments
for example in examples:
    segments = example.get_laughter_segments()
    for segment in segments:
        if 'start_time' in segment:
            print(f"Laughter: {segment['start_time']:.2f}s - "
                  f"{segment['end_time']:.2f}s")

# Work with forced alignments
for example in examples:
    if example.has_alignment():
        alignment = example.alignment
        for i, word in enumerate(alignment.words):
            duration = alignment.get_word_duration(i)
            print(f"{word}: {duration:.3f}s")
    """)

    print("\n📊 DATASET STRUCTURE:")
    print("-" * 50)
    print("""
Expected directory structure:
ur_funny/
├── annotations/
│   ├── train.csv
│   ├── val.csv
│   └── test.csv
├── p2fa_alignments/          # Forced alignment data
│   ├── ted_1234.json
│   ├── ted_5678.json
│   └── ...
├── punchline_annotations.json # Punchline/context data
└── features/                  # Optional multimodal features
    ├── audio_features.npy
    └── visual_features.npy
    """)

    print("\n🎯 INTEGRATION WITH GCACU:")
    print("-" * 50)
    print("""
# The loader produces examples compatible with GCACU pipeline:
# - Word-level text features
# - Binary laughter labels
# - Multilingual support
# - Metadata preservation

# Use with GCACU training:
from core.gcacu.gcacu import GCACU

# Load and convert data
examples = loader.load(split="train")
convert_to_gcacu_format(examples, "train_data.jsonl")

# Train GCACU model
model = GCACU.load_config("gcacu_config.json")
model.train("train_data.jsonl", "val_data.jsonl")
    """)

    print("\n🔬 RESEARCH APPLICATIONS:")
    print("-" * 50)
    print("""
# 1. Professional Humor Analysis
# Study humor patterns in TED talks vs stand-up comedy

# 2. Cross-Domain Transfer Learning
# Train on UR-FUNNY, test on stand-up comedy datasets

# 3. Temporal Humor Dynamics
# Use forced alignment to study timing in humor delivery

# 4. Context Window Analysis
# Analyze how context setup affects punchline effectiveness

# 5. Laughter Prediction Modeling
# Predict audience laughter from text and timing features
    """)

    print("\n" + "="*70)


def main():
    """Main demo function."""
    import argparse

    parser = argparse.ArgumentParser(description="UR-FUNNY Dataset Loader Demo")
    parser.add_argument(
        '--demo',
        action='store_true',
        help='Run complete workflow demo with sample data'
    )
    parser.add_argument(
        '--guide',
        action='store_true',
        help='Print usage guide and examples'
    )
    parser.add_argument(
        '--data-dir',
        type=str,
        help='Path to real UR-FUNNY dataset'
    )
    parser.add_argument(
        '--split',
        type=str,
        default='train',
        choices=['train', 'val', 'test'],
        help='Dataset split to load'
    )

    args = parser.parse_args()

    if args.guide:
        demo_usage_guide()
    elif args.demo:
        success = demo_sample_data_workflow()
        if success:
            print("\n✨ Demo completed successfully!")
            print("💡 Run with --guide to see usage examples")
    elif args.data_dir:
        # Load real data
        print(f"Loading UR-FUNNY data from: {args.data_dir}")

        loader = URFunnyLoader(
            data_dir=Path(args.data_dir),
            enable_alignment=True,
            enable_punchlines=True
        )

        examples = loader.load(split=args.split)

        if examples:
            analyze_dataset(examples, args.split.upper())
            show_example_analysis(examples[:3])

            # Convert to GCACU format
            output_file = Path(f"urfunny_{args.split}.jsonl")
            convert_to_gcacu_format(examples, output_file)
            print(f"\n✓ Saved {len(examples)} examples to {output_file}")
        else:
            print("❌ No examples loaded")
    else:
        # Default: show guide
        demo_usage_guide()
        print("\n💡 Run with --demo to see the workflow in action")
        print("💡 Run with --data-dir PATH to load real UR-FUNNY data")


if __name__ == "__main__":
    main()