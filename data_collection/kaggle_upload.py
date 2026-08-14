#!/usr/bin/env python3
"""
Kaggle Upload Script for WavLM Feature Extraction Dataset.

Uploads:
1. prosody_aligned_features.jsonl (15K utterances with prosody labels)
2. WavLM_Extraction.ipynb (GPU notebook for Kaggle)
3. metadata.json (dataset metadata)

Usage:
    python kaggle_upload.py                    # Full upload
    python kaggle_upload.py --test            # Test with sample
    python kaggle_upload.py --public           # Make publicly accessible
"""

import os
import sys
import json
import time
import argparse
import subprocess
from pathlib import Path

# ============================================================================
# PATHS
# ============================================================================

PROJECT_ROOT = Path(__file__).parent.parent
PROSODY_FILE = PROJECT_ROOT / "data/prosody_aligned/prosody_aligned_features.jsonl"
NOTEBOOK_FILE = PROJECT_ROOT / "Kaggle_WavLM_Extraction.ipynb"
OUTPUT_DIR = PROJECT_ROOT / "data_collection"
KAGGLE_SLUG = "autonomous-laughter-prediction"  # dataset slug
KAGGLE_USERNAME = "subhajitdas"

# ============================================================================
# STEP 1: Verify files exist
# ============================================================================

def verify_files(test_mode=False):
    """Verify all required files exist."""
    print("=" * 60)
    print("STEP 1: Verifying files")
    print("=" * 60)

    errors = []

    if not PROSODY_FILE.exists():
        errors.append(f"Missing: {PROSODY_FILE}")
    else:
        size_mb = os.path.getsize(PROSODY_FILE) / 1e6
        # Count lines
        with open(PROSODY_FILE) as f:
            n_lines = sum(1 for _ in f)
        print(f"  Prosody file: {PROSODY_FILE} ({size_mb:.1f} MB, {n_lines:,} lines)")

    if not NOTEBOOK_FILE.exists():
        errors.append(f"Missing: {NOTEBOOK_FILE}")
    else:
        size_kb = os.path.getsize(NOTEBOOK_FILE) / 1e3
        print(f"  Notebook: {NOTEBOOK_FILE} ({size_kb:.1f} KB)")

    if errors:
        for e in errors:
            print(f"  ERROR: {e}")
        return False
    return True


# ============================================================================
# STEP 2: Check/create Kaggle dataset metadata
# ============================================================================

def get_dataset_metadata():
    """Create dataset metadata dict."""
    return {
        "title": "Autonomous Laughter Prediction - WavLM Features",
        "id": f"{KAGGLE_USERNAME}/{KAGGLE_SLUG}",
        "subtitle": "WavLM-Base-Plus audio embeddings + prosody features for standup comedy laughter detection",
        "description": """# WavLM Feature Extraction Dataset

## Overview
This dataset contains **15,000 utterances** from standup comedy videos with pre-computed WavLM-Base-Plus audio embeddings and prosody features for **laughter detection**.

## Files
- `prosody_aligned_features.jsonl` - 15K utterances with 10-dim prosody features
- `WavLM_Extraction.ipynb` - Kaggle GPU notebook for full WavLM embedding extraction

## Features
- **WavLM embeddings**: 768-dim per utterance (facebook/wavlm-base-plus)
- **Prosody features**: 10-dim (F0 mean/range, pause duration, speech rate, RMS energy, MFCCs)
- **Labels**: laughter vs non-laughter (binary)

## Run on Kaggle
1. Add this dataset to your Kaggle notebook
2. Enable GPU accelerator (P100/T4)
3. Run the `WavLM_Extraction.ipynb` notebook
4. Extract embeddings for all 15K utterances (~2-3 hours on P100)

## Source
From the Autonomous Laughter Prediction project:
https://github.com/Das-rebel/autonomous_laughter_prediction

## Citation
```bibtex
@misc{autonomous_laughter_prediction,
  author = {Subhojit Das},
  title = {Autonomous Laughter Prediction from Standup Comedy Audio},
  year = {2026},
  url = {https://github.com/Das-rebel/autonomous_laughter_prediction}
}
```
""",
        "keywords": ["wavlm", "laughter", "audio", "feature-extraction", "standup-comedy", "prosody"],
        "collaborators": [],
        "logistics": {
            "uploaded": time.strftime("%Y-%m-%d"),
            "license": "cc-by-sa-4.0",
            "is_private": True,
            "enable_on_kaggle": True,
            "kaggle_type": "dataset"
        }
    }


# ============================================================================
# STEP 3: Create/Upload to Kaggle
# ============================================================================

def kaggle_check():
    """Verify Kaggle CLI is configured."""
    print("Checking Kaggle CLI...")
    result = subprocess.run(
        ["kaggle", "datasets", "list", "-s", "laughter", "--max-size", "1"],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        print(f"  Kaggle CLI error: {result.stderr.strip()}")
        return False
    print("  Kaggle CLI: OK")
    return True


def create_dataset(test_mode=False):
    """Create Kaggle dataset."""
    print("\n" + "=" * 60)
    print("STEP 2: Creating Kaggle Dataset")
    print("=" * 60)

    dataset_id = f"{KAGGLE_USERNAME}/{KAGGLE_SLUG}"

    # Check if dataset already exists
    print(f"Checking if dataset '{dataset_id}' exists...")
    result = subprocess.run(
        ["kaggle", "datasets", "metadata", "-p", "/tmp/kaggle_ds_check", dataset_id],
        capture_output=True, text=True, timeout=30
    )

    if result.returncode == 0:
        print(f"  Dataset already exists. Will update.")
        return dataset_id

    # Create new dataset
    print(f"Creating new dataset: {dataset_id}")

    # Create metadata file
    metadata_dir = Path("/tmp/kaggle_dataset_metadata")
    metadata_dir.mkdir(exist_ok=True)

    metadata_content = f"""Dataset ID: {dataset_id}
Title: Autonomous Laughter Prediction - WavLM Features
Scenario: Upload
Environment: Standard
"""

    (metadata_dir / "dataset-metadata.json").write_text(metadata_content)

    # Create dataset via API
    cmd = [
        "kaggle", "datasets", "create",
        "--dir-fast",
        "--public",
        "-p", str(metadata_dir),
        "-m", "initial upload"
    ]

    if test_mode:
        print(f"  TEST MODE: would run: {' '.join(cmd)}")
        return dataset_id

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        print(f"  Create error: {result.stderr}")
        return None
    print(f"  Dataset created: {dataset_id}")
    return dataset_id


def upload_files(test_mode=False):
    """Upload files to existing Kaggle dataset."""
    print("\n" + "=" * 60)
    print("STEP 3: Uploading Files to Kaggle")
    print("=" * 60)

    dataset_id = f"{KAGGLE_USERNAME}/{KAGGLE_SLUG}"

    if test_mode:
        # Test mode: verify files exist and show sizes
        print(f"  TEST MODE: would upload to {dataset_id}")
        print(f"    - {PROSODY_FILE} ({os.path.getsize(PROSODY_FILE)/1e6:.1f} MB)")
        print(f"    - {NOTEBOOK_FILE} ({os.path.getsize(NOTEBOOK_FILE)/1e3:.1f} KB)")
        return True

    # Upload prosody file
    print(f"Uploading prosody file...")
    result = subprocess.run(
        ["kaggle", "datasets", "upload", "-p", str(PROSODY_FILE.parent), "-f", PROSODY_FILE.name, "-q"],
        capture_output=True, text=True, timeout=300
    )
    if result.returncode != 0:
        print(f"  Upload error: {result.stderr}")
        return False
    print(f"  Prosody file uploaded.")

    return True


def upload_notebook(test_mode=False):
    """Upload notebook to Kaggle dataset."""
    print(f"Uploading notebook...")

    if test_mode:
        print(f"  TEST MODE: would upload {NOTEBOOK_FILE}")
        return True

    # Copy notebook to a temp dir for upload
    import shutil
    nb_dir = Path("/tmp/kaggle_nb_upload")
    nb_dir.mkdir(exist_ok=True)
    shutil.copy(NOTEBOOK_FILE, nb_dir / NOTEBOOK_FILE.name)

    result = subprocess.run(
        ["kaggle", "datasets", "upload", "-p", str(nb_dir), "-f", NOTEBOOK_FILE.name, "-q"],
        capture_output=True, text=True, timeout=120
    )
    if result.returncode != 0:
        print(f"  Notebook upload error: {result.stderr}")
        return False
    print(f"  Notebook uploaded.")
    return True


def set_public():
    """Make dataset publicly accessible."""
    print("\n" + "=" * 60)
    print("STEP 4: Setting Dataset to Public")
    print("=" * 60)

    dataset_id = f"{KAGGLE_USERNAME}/{KAGGLE_SLUG}"

    # Update dataset to public
    result = subprocess.run(
        ["kaggle", "datasets", "metadata", "--update", "-p", "/tmp/kaggle_ds_update", dataset_id],
        capture_output=True, text=True, timeout=60
    )
    if result.returncode != 0:
        print(f"  Public update error (may be expected): {result.stderr.strip()[:200]}")
    else:
        print(f"  Dataset set to public.")

    # Also try the datasets permissions command
    result2 = subprocess.run(
        ["kaggle", "datasets", "metadata", "-p", "/tmp/kaggle_ds_pub", dataset_id],
        capture_output=True, text=True, timeout=30
    )
    if result2.returncode == 0:
        # Update the metadata to make it public
        meta_path = Path("/tmp/kaggle_ds_pub/dataset-metadata.json")
        if meta_path.exists():
            meta = json.loads(meta_path.read_text())
            if "is_private" in meta:
                meta["is_private"] = False
                meta_path.write_text(json.dumps(meta, indent=2))
                result3 = subprocess.run(
                    ["kaggle", "datasets", "metadata", "--update", "-p", "/tmp/kaggle_ds_pub", dataset_id],
                    capture_output=True, text=True, timeout=60
                )
                if result3.returncode == 0:
                    print(f"  is_private=False set successfully.")
                else:
                    print(f"  is_private update: {result3.stderr.strip()[:200]}")
    return True


def verify_dataset():
    """Verify the dataset was created."""
    print("\n" + "=" * 60)
    print("STEP 5: Verifying Dataset")
    print("=" * 60)

    dataset_id = f"{KAGGLE_USERNAME}/{KAGGLE_SLUG}"

    result = subprocess.run(
        ["kaggle", "datasets", "metadata", "-p", "/tmp/kaggle_verify", dataset_id],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode == 0:
        print(f"  Dataset verified: {dataset_id}")
        print(f"  URL: https://www.kaggle.com/datasets/{KAGGLE_USERNAME}/{KAGGLE_SLUG}")
        return True
    print(f"  Verification failed: {result.stderr}")
    return False


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Upload WavLM dataset to Kaggle")
    parser.add_argument("--test", action="store_true", help="Test mode (don't actually upload)")
    parser.add_argument("--public", action="store_true", help="Make dataset publicly accessible")
    parser.add_argument("--skip-notebook", action="store_true", help="Skip notebook upload")
    args = parser.parse_args()

    print("\n" + "#" * 60)
    print("# KAGGLE DATASET UPLOAD - WavLM Feature Extraction")
    print("#" * 60)

    if not verify_files(test_mode=args.test):
        return 1

    if not kaggle_check():
        return 1

    if not create_dataset(test_mode=args.test):
        print("Failed to create dataset.")
        return 1

    if not upload_files(test_mode=args.test):
        print("Failed to upload files.")
        return 1

    if not args.skip_notebook:
        if not upload_notebook(test_mode=args.test):
            print("Failed to upload notebook.")
            return 1

    if args.public:
        set_public()

    if not verify_dataset():
        print("Warning: dataset verification failed.")

    dataset_id = f"{KAGGLE_USERNAME}/{KAGGLE_SLUG}"
    print(f"\n{'=' * 60}")
    print(f"SUCCESS: Dataset at https://www.kaggle.com/datasets/{dataset_id}")
    print(f"{'=' * 60}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
