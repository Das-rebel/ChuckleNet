#!/usr/bin/env python3
"""
StandUp4AI Dataset Converter

Converts StandUp4AI CSV format to JSONL for training.
Format: text,timestamp,label (O=non-laughter, L=laughter)
"""

import csv
import json
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class StandUp4AIConfig:
    data_dir: Path
    output_dir: Path
    min_seq_length: int = 5
    max_seq_length: int = 256
    language: str = "all"
    split_ratio: tuple = (0.8, 0.1, 0.1)


def load_standup4ai_csv(csv_path: Path) -> List[Dict[str, Any]]:
    records = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(row)
    return records


def group_into_segments(records: List[Dict[str, Any]], max_length: int = 256) -> List[Dict[str, Any]]:
    segments = []
    current_words = []
    current_labels = []
    current_timestamps = []

    for record in records:
        word = record['text'].strip()
        label = 1 if record['label'] == 'L' else 0
        timestamp = record['timestamp']

        if not word:
            continue

        current_words.append(word)
        current_labels.append(label)
        current_timestamps.append(timestamp)

        if len(current_words) >= max_length:
            segments.append({
                'words': current_words.copy(),
                'labels': current_labels.copy(),
                'timestamps': current_timestamps.copy()
            })
            current_words = []
            current_labels = []
            current_timestamps = []

    if current_words:
        segments.append({
            'words': current_words.copy(),
            'labels': current_labels.copy(),
            'timestamps': current_timestamps.copy()
        })

    return segments


def convert_video_to_jsonl(csv_path: Path, video_id: str, output_dir: Path, split: str = "train"):
    records = load_standup4ai_csv(csv_path)
    segments = group_into_segments(records)

    output_file = output_dir / f"{split}.jsonl"
    count = 0

    with open(output_file, 'a') as f:
        for seg_idx, segment in enumerate(segments):
            if len(segment['words']) < 5:
                continue

            example = {
                "example_id": f"standup4ai_{video_id}_seg_{seg_idx}",
                "language": "en",
                "words": segment['words'],
                "labels": segment['labels'],
                "metadata": {
                    "source": "StandUp4AI",
                    "video_id": video_id,
                    "laughter_type": "word_level",
                    "split": split
                }
            }
            f.write(json.dumps(example) + "\n")
            count += 1

    return count


def convert_standup4ai_dataset(
    examples_dir: Path,
    output_dir: Path,
    split_ratio: tuple = (0.8, 0.1, 0.1),
    languages: List[str] = None,
    master_csv: Path = None
):
    output_dir.mkdir(parents=True, exist_ok=True)

    for split in ['train', 'valid', 'test']:
        split_file = output_dir / f"{split}.jsonl"
        if split_file.exists():
            split_file.unlink()

    english_video_ids = set()
    if master_csv and master_csv.exists():
        print(f"Filtering for English only from {master_csv}")
        with open(master_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                lang = row.get('lang', '')
                if lang in ['en', 'en_us', 'en_uk']:
                    video_id = row.get('url', '').split('watch?v=')[-1] if 'watch?v=' in row.get('url', '') else row.get('url', '')
                    if video_id:
                        english_video_ids.add(video_id)
        print(f"Found {len(english_video_ids)} English videos (en, en_us, en_uk)")

    csv_files = list(examples_dir.glob("*.csv"))
    print(f"Found {len(csv_files)} CSV files in {examples_dir}")

    total_train = 0
    total_valid = 0
    total_test = 0
    skipped = 0

    for csv_file in csv_files:
        video_id = csv_file.stem

        if english_video_ids and video_id not in english_video_ids:
            skipped += 1
            continue

        total = convert_video_to_jsonl(csv_file, video_id, output_dir, "train")
        print(f"Converted {video_id}: {total} segments")

    if skipped > 0:
        print(f"Skipped {skipped} non-English videos")

    train_count = sum(1 for _ in open(output_dir / "train.jsonl")) if (output_dir / "train.jsonl").exists() else 0
    print(f"\nTotal train segments: {train_count}")
    print(f"Output directory: {output_dir}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Convert StandUp4AI CSV to JSONL (English only)")
    parser.add_argument("--input-dir", type=str,
                        default="data/StandUp4AI/Examples_label",
                        help="Directory with CSV files")
    parser.add_argument("--output-dir", type=str,
                        default="data/training/standup4ai",
                        help="Output directory for JSONL files")
    parser.add_argument("--max-length", type=int, default=256,
                        help="Maximum sequence length")
    parser.add_argument("--master-csv", type=str,
                        default="data/StandUp4AI/CSV_clean/StandUp4AI_v1.csv",
                        help="Master CSV for language filtering")
    parser.add_argument("--english-only", action="store_true", default=True,
                        help="Filter to English only (en, en_us, en_uk)")

    args = parser.parse_args()

    master_csv_path = Path(args.master_csv) if args.english_only else None

    convert_standup4ai_dataset(
        examples_dir=Path(args.input_dir),
        output_dir=Path(args.output_dir),
        master_csv=master_csv_path
    )