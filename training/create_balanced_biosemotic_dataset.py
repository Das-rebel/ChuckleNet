#!/usr/bin/env python3
"""
Create balanced biosemotic dataset for binary classification.

This script creates a proper training dataset by combining:
1. Biosemotic positive samples (Reddit jokes + MELD joy)
2. Representative negative samples from the original unified dataset
"""

import json
import random
from pathlib import Path
from typing import Any

import pandas as pd
from sklearn.model_selection import train_test_split

def main() -> None:
    random.seed(42)

    # Paths
    biosemotic_path = Path("data/training/biosemotic_humor/biosemotic_dataset.csv")
    unified_path = Path("data/training/final_unified_humor/unified_dataset.csv")
    output_dir = Path("data/training/balanced_biosemotic_humor")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Loading biosemotic positive samples...")
    biosemotic_df = pd.read_csv(biosemotic_path)
    biosemotic_df["label"] = 1  # Ensure all are labeled as positive

    print(f"Biosemotic positives: {len(biosemotic_df):,}")

    print("Loading unified dataset for negative samples...")
    unified_df = pd.read_csv(unified_path)

    # Get negative samples from unified dataset (excluding sources that are in biosemotic)
    # We want negatives that are clearly non-humorous
    negative_sources = ["hf_humor_proxy", "meld"]
    negative_df = unified_df[
        (unified_df["label"] == 0) &
        (~unified_df["source_dataset"].isin(["reddit_jokes"]))
    ].copy()

    # Sample negatives to match positive count (1:1 ratio)
    target_negatives = len(biosemotic_df)
    if len(negative_df) > target_negatives:
        negative_df = negative_df.sample(n=target_negatives, random_state=42)

    print(f"Selected negatives: {len(negative_df):,}")

    # Combine and shuffle
    balanced_df = pd.concat([biosemotic_df, negative_df], axis=0)
    balanced_df = balanced_df.sample(frac=1.0, random_state=42).reset_index(drop=True)

    # Ensure we have the required columns
    required_cols = ["text", "label"]
    for col in required_cols:
        if col not in balanced_df.columns:
            raise ValueError(f"Missing required column: {col}")

    # Fill missing biosemotic features with defaults for negative samples
    biosemotic_cols = [
        "biosemotic_viability_score",
        "duchenne_genuine_humor_probability",
        "incongruity_expectation_violation_score"
    ]

    for col in biosemotic_cols:
        if col not in balanced_df.columns:
            balanced_df[col] = 0.5  # Neutral value for negatives
        else:
            # Fill missing values for negatives with neutral scores
            balanced_df[col] = balanced_df[col].fillna(0.5)

    # Split into train/validation/test (80/10/10)
    train_df, temp_df = train_test_split(
        balanced_df,
        test_size=0.2,
        random_state=42,
        stratify=balanced_df["label"]
    )

    val_df, test_df = train_test_split(
        temp_df,
        test_size=0.5,
        random_state=42,
        stratify=temp_df["label"]
    )

    print(f"\nDataset splits:")
    print(f"Train: {len(train_df):,} rows (positive: {train_df['label'].sum():,})")
    print(f"Validation: {len(val_df):,} rows (positive: {val_df['label'].sum():,})")
    print(f"Test: {len(test_df):,} rows (positive: {test_df['label'].sum():,})")

    # Save splits
    train_path = output_dir / "train.csv"
    val_path = output_dir / "valid.csv"
    test_path = output_dir / "test.csv"

    train_df.to_csv(train_path, index=False)
    val_df.to_csv(val_path, index=False)
    test_df.to_csv(test_path, index=False)

    print(f"\nSaved balanced biosemotic dataset to {output_dir}")

    # Create filtering report
    report = {
        "dataset_type": "balanced_biosemotic",
        "total_rows": len(balanced_df),
        "positive_rows": int(balanced_df["label"].sum()),
        "negative_rows": int(len(balanced_df) - balanced_df["label"].sum()),
        "positive_rate": float(balanced_df["label"].mean()),
        "splits": {
            "train": {
                "rows": len(train_df),
                "positive": int(train_df["label"].sum()),
                "negative": int(len(train_df) - train_df["label"].sum()),
                "positive_rate": float(train_df["label"].mean())
            },
            "validation": {
                "rows": len(val_df),
                "positive": int(val_df["label"].sum()),
                "negative": int(len(val_df) - val_df["label"].sum()),
                "positive_rate": float(val_df["label"].mean())
            },
            "test": {
                "rows": len(test_df),
                "positive": int(test_df["label"].sum()),
                "negative": int(len(test_df) - test_df["label"].sum()),
                "positive_rate": float(test_df["label"].mean())
            }
        },
        "biosemotic_features": {
            "avg_biosemotic_viability": float(balanced_df["biosemotic_viability_score"].mean()),
            "avg_duchenne_probability": float(balanced_df["duchenne_genuine_humor_probability"].mean()),
            "avg_incongruity_score": float(balanced_df["incongruity_expectation_violation_score"].mean())
        },
        "sources": {
            "positive_sources": ["reddit_jokes", "meld"],
            "negative_sources": list(negative_df["source_dataset"].unique())
        }
    }

    report_path = output_dir / "balance_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"Balance report saved to {report_path}")

if __name__ == "__main__":
    main()