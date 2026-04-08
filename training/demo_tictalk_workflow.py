#!/usr/bin/env python3
"""
TIC-TALK Dataset Loader - Quick Start Demo

This script demonstrates the complete workflow for using the TIC-TALK
dataset loader with autonomous laughter prediction.

Usage:
    python3 demo_tictalk_workflow.py

Author: Autonomous Laughter Prediction Team
Date: 2025-04-03
"""

import sys
import tempfile
from pathlib import Path

# Add training directory to path
sys.path.insert(0, str(Path(__file__).parent))

from load_tic_talk import (
    TICTalkLoader,
    TICTalkExample,
    create_sample_tictalk_data,
    convert_to_gcacu_format
)

def main():
    """Demonstrate complete TIC-TALK workflow."""
    print("=" * 70)
    print("TIC-TALK Dataset Loader - Quick Start Demo")
    print("=" * 70)

    # Step 1: Create sample data
    print("\n📁 Step 1: Creating sample TIC-TALK data...")
    temp_dir = tempfile.mkdtemp(prefix="tictalk_demo_")
    data_dir = Path(temp_dir)

    create_sample_tictalk_data(data_dir, num_samples=5)
    print(f"✓ Sample data created in: {data_dir}")

    # Step 2: Load dataset
    print("\n🔧 Step 2: Loading TIC-TALK dataset...")
    loader = TICTalkLoader(
        data_dir=data_dir,
        enable_kinematics=True,
        normalize_kinematics=True
    )

    examples = loader.load()
    print(f"✓ Loaded {len(examples)} examples")

    # Display statistics
    print("\n📊 Dataset Statistics:")
    for key, value in loader.stats.items():
        print(f"  • {key}: {value}")

    # Step 3: Examine individual example
    print("\n🔍 Step 3: Examining individual example...")
    example = examples[0]

    print(f"Example ID: {example.example_id}")
    print(f"Language: {example.language}")
    print(f"Words: {len(example.words)}")
    print(f"Labels: {sum(example.labels)} laughter words")
    print(f"Has kinematics: {example.has_kinematics()}")

    # Show first few words and labels
    print("\nFirst 5 words with labels:")
    for i in range(min(5, len(example.words))):
        label_str = "😄" if example.labels[i] else "  "
        print(f"  {i+1}. [{label_str}] {example.words[i]}")

    # Step 4: Examine kinematic data
    if example.has_kinematics():
        print("\n📈 Step 4: Examining kinematic signals...")
        kinematics = example.kinematics

        print(f"Arm spread: {len(kinematics.arm_spread)} samples")
        print(f"  • Mean: {kinematics.arm_spread.mean():.4f}")
        print(f"  • Std: {kinematics.arm_spread.std():.4f}")
        print(f"  • Range: [{kinematics.arm_spread.min():.4f}, {kinematics.arm_spread.max():.4f}]")

        print(f"\nTrunk lean: {len(kinematics.trunk_lean)} samples")
        print(f"  • Mean: {kinematics.trunk_lean.mean():.4f}")
        print(f"  • Std: {kinematics.trunk_lean.std():.4f}")
        print(f"  • Range: [{kinematics.trunk_lean.min():.4f}, {kinematics.trunk_lean.max():.4f}]")

        print(f"\nBody movement: {len(kinematics.body_movement)} samples")
        print(f"  • Mean: {kinematics.body_movement.mean():.4f}")
        print(f"  • Std: {kinematics.body_movement.std():.4f}")
        print(f"  • Range: [{kinematics.body_movement.min():.4f}, {kinematics.body_movement.max():.4f}]")

    # Step 5: Convert to GCACU format
    print("\n🔄 Step 5: Converting to GCACU format...")
    output_file = data_dir / "tictalk_gcacu.jsonl"
    convert_to_gcacu_format(examples, output_file, include_kinematics=True)
    print(f"✓ GCACU format saved to: {output_file}")

    # Show sample of GCACU format
    print("\n📄 Sample GCACU format (first example):")
    import json
    with open(output_file) as f:
        first_line = f.readline()
        record = json.loads(first_line)

    print(f"  • Example ID: {record['example_id']}")
    print(f"  • Language: {record['language']}")
    print(f"  • Words: {len(record['words'])}")
    print(f"  • Labels: {sum(record['labels'])} laughter words")
    print(f"  • Metadata keys: {list(record['metadata'].keys())}")
    if 'kinematics' in record:
        print(f"  • Kinematic keys: {list(record['kinematics'].keys())}")

    # Step 6: Usage examples
    print("\n💡 Step 6: Usage Examples:")
    print("""
# Basic loading:
from training.load_tic_talk import TICTalkLoader
loader = TICTalkLoader(data_dir=Path("data/TIC-TALK"))
examples = loader.load()

# With kinematics:
loader = TICTalkLoader(data_dir=Path("data/TIC-TALK"), enable_kinematics=True)
examples = loader.load()

# Access individual example:
example = examples[0]
print(f"Words: {example.words}")
print(f"Labels: {example.labels}")
print(f"Kinematics: {example.has_kinematics()}")

# Integration with GCACU:
from training.integrate_tictalk_gcacu import create_tictalk_dataloaders
train_loader, val_loader, info = create_tictalk_dataloaders(
    data_dir=Path("data/TIC-TALK"),
    tokenizer=tokenizer,
    use_kinematics=True
)
    """)

    # Cleanup
    print(f"\n🧹 Cleaning up temporary directory: {data_dir}")
    import shutil
    shutil.rmtree(data_dir)

    print("\n✅ Demo completed successfully!")
    print("=" * 70)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)