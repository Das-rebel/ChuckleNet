#!/usr/bin/env python3
"""
Prepare Kaggle dataset from Google Drive data.
Run this in Colab to create a zip file for Kaggle upload.

Steps:
1. Mount Google Drive
2. Copy aligned_utterances.jsonl, prosody_phaseD.json, and all audio/*.mp3
3. Create a clean dataset directory with relative paths
4. Zip and save to Drive for download
"""

import os
import json
import shutil
from pathlib import Path

# === CONFIG ===
BASE = '/content/drive/MyDrive/chuckle_checkpoints'
AUDIO_DIR = f'{BASE}/audio'
PROSODY_PATH = f'{BASE}/prosody_phaseD.json'
ALIGNED_PATH = f'{BASE}/aligned_utterances.jsonl'
OUTPUT_DIR = '/content/kaggle_dataset'
ZIP_PATH = '/content/drive/MyDrive/chuckle_kaggle_dataset.zip'

print("=== Kaggle Dataset Preparation ===\n")

# Create clean directory structure
os.makedirs(f'{OUTPUT_DIR}/audio', exist_ok=True)

# 1. Copy aligned_utterances.jsonl with cleaned paths
print("Processing aligned_utterances.jsonl...")
count = 0
with open(ALIGNED_PATH) as fin, open(f'{OUTPUT_DIR}/aligned_utterances.jsonl', 'w') as fout:
    for line in fin:
        d = json.loads(line)
        # Replace absolute paths with just video_id.mp3
        d['audio_file'] = f"{d['video_id']}.mp3"
        fout.write(json.dumps(d) + '\n')
        count += 1
print(f"  Wrote {count} entries")

# 2. Copy prosody_phaseD.json
print("Copying prosody_phaseD.json...")
shutil.copy2(PROSODY_PATH, f'{OUTPUT_DIR}/prosody_phaseD.json')
size_mb = os.path.getsize(f'{OUTPUT_DIR}/prosody_phaseD.json') / 1024**2
print(f"  Copied ({size_mb:.1f} MB)")

# 3. Copy audio files
print("Copying audio files...")
audio_files = sorted(Path(AUDIO_DIR).glob('*.mp3'))
total_size = 0
for i, src in enumerate(audio_files):
    dst = f'{OUTPUT_DIR}/audio/{src.name}'
    shutil.copy2(src, dst)
    total_size += src.stat().st_size
    if (i + 1) % 10 == 0:
        print(f"  Copied {i+1}/{len(audio_files)} files ({total_size/1024**3:.1f} GB)")

print(f"  Total: {len(audio_files)} files, {total_size/1024**3:.1f} GB")

# 4. Create dataset-metadata.json for Kaggle
metadata = {
    "title": "chuckle-net-phase-a-prosody",
    "id": "chuckle-net-phase-a-prosody",
    "licenses": [{"name": "CC0-1.0"}]
}
with open(f'{OUTPUT_DIR}/dataset-metadata.json', 'w') as f:
    json.dump(metadata, f, indent=2)
print("  Created dataset-metadata.json")

# 5. Zip it up
print(f"\nCreating zip archive...")
shutil.make_archive(ZIP_PATH.replace('.zip', ''), 'zip', OUTPUT_DIR)
zip_size = os.path.getsize(ZIP_PATH) / 1024**3
print(f"  Created: {ZIP_PATH} ({zip_size:.1f} GB)")

# 6. Print summary
print(f"\n=== Summary ===")
print(f"Dataset: {OUTPUT_DIR}")
print(f"  aligned_utterances.jsonl: {count} entries")
print(f"  audio/: {len(audio_files)} files, {total_size/1024**3:.1f} GB")
print(f"  prosody_phaseD.json: {size_mb:.1f} MB")
print(f"Zip: {ZIP_PATH} ({zip_size:.1f} GB)")
print(f"\nNext steps:")
print(f"1. Download {ZIP_PATH} from Google Drive")
print(f"2. Go to kaggle.com/datasets/create")
print(f"3. Upload the zip file")
print(f"4. Add the dataset to your notebook via + Add Data")
