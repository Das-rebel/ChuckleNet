#!/usr/bin/env python3
"""
Reproduce Paper Results

This script reproduces the main results from the biosemiotic laughter prediction paper.

Usage:
    python reproduce_results.py

Requirements:
    - Trained model in experiments/biosemotic_humor_bert_lr2e5
    - Test data in data/training/reddit_jokes/
"""

import argparse
import json
import subprocess
from pathlib import Path


def run_command(cmd: list[str], description: str) -> None:
    """Run a shell command and print results."""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"{'='*60}")
    print(f"Running: {' '.join(cmd)}\n")
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    if result.returncode != 0:
        print(f"Command failed with return code: {result.returncode}")
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description="Reproduce paper results")
    parser.add_argument(
        "--model",
        default="experiments/biosemotic_humor_bert_lr2e5",
        help="Path to trained model",
    )
    parser.add_argument(
        "--data",
        default="data/training/reddit_jokes/reddit_jokes_humor.csv",
        help="Path to test data",
    )
    parser.add_argument(
        "--output-dir",
        default="results",
        help="Directory to save results",
    )
    args = parser.parse_args()

    print("="*60)
    print("BIOSEMIOTIC LAUGHTER PREDICTION - RESULTS REPRODUCTION")
    print("="*60)

    # Check paths
    model_path = Path(args.model)
    data_path = Path(args.data)

    if not model_path.exists():
        print(f"ERROR: Model not found at {model_path}")
        print("Please train the model first:")
        print("  python training/finetune_biosemotic_humor_bert.py \\")
        print("    --epochs 3 --batch-size 8 --learning-rate 2e-5")
        return

    if not data_path.exists():
        print(f"ERROR: Data not found at {data_path}")
        return

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

    # Run evaluation
    success = run_command(
        [
            "python", "-m", "src.biosemioticai.evaluate",
            "--model", str(model_path),
            "--data", str(data_path),
            "--output", str(output_dir / "metrics.json"),
        ],
        "EVALUATING MODEL",
    )

    if success:
        print("\n" + "="*60)
        print("REPRODUCTION COMPLETE")
        print("="*60)
        print(f"\nResults saved to: {output_dir / 'metrics.json'}")

        # Print summary
        metrics = json.loads((output_dir / "metrics.json").read_text())
        print("\nKey Metrics:")
        for name, value in metrics.items():
            print(f"  {name}: {value:.4f}")


if __name__ == "__main__":
    main()
