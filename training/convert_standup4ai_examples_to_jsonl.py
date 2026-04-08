#!/usr/bin/env python3
"""
Convert StandUp4AI example label CSVs into the internal word-level JSONL schema.

The public StandUp4AI repository ships a few labeled example files under
`Examples_label/`. They are not the full benchmark, but they are real
word-level laughter labels and are sufficient for a small external sanity check.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Dict, List


LANGUAGE_HINTS = {
    "-1FrUOEswOk": "fr",
    "0g7nezWZyfY": "en",
    "1xvwYZwm8Ig": "cs",
    "6JQzl2LlXbQ": "es",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert StandUp4AI example label CSVs to internal JSONL format.")
    parser.add_argument("--input-dir", type=Path, required=True, help="Directory containing StandUp4AI example label CSVs.")
    parser.add_argument("--output-file", type=Path, required=True, help="Output JSONL file.")
    parser.add_argument("--summary-file", type=Path, default=None, help="Optional summary JSON output.")
    return parser.parse_args()


def load_example(csv_path: Path) -> Dict[str, object]:
    words: List[str] = []
    labels: List[int] = []
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            token = str(row.get("text") or "").strip()
            if not token:
                continue
            label = 1 if str(row.get("label") or "").strip().upper() == "L" else 0
            words.append(token)
            labels.append(label)

    stem = csv_path.stem
    return {
        "example_id": f"standup4ai_example_{stem}",
        "language": LANGUAGE_HINTS.get(stem, "unknown"),
        "laughter_type": "unknown",
        "comedian_id": f"standup4ai_{stem}",
        "show_id": "standup4ai_examples",
        "words": words,
        "labels": labels,
        "metadata": {
            "source_dataset": "standup4ai_examples",
            "source_file": csv_path.name,
            "current_segment_start": 0,
        },
    }


def main() -> None:
    args = parse_args()
    csv_files = sorted(args.input_dir.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {args.input_dir}")

    records = [load_example(csv_path) for csv_path in csv_files]
    args.output_file.parent.mkdir(parents=True, exist_ok=True)
    with args.output_file.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    if args.summary_file is not None:
        language_counts = Counter(record["language"] for record in records)
        summary = {
            "input_dir": str(args.input_dir),
            "output_file": str(args.output_file),
            "example_count": len(records),
            "positive_example_count": sum(1 for record in records if any(record["labels"])),
            "positive_token_count": sum(sum(int(label) for label in record["labels"]) for record in records),
            "language_counts": dict(sorted(language_counts.items())),
            "source_files": [record["metadata"]["source_file"] for record in records],
        }
        args.summary_file.parent.mkdir(parents=True, exist_ok=True)
        args.summary_file.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(json.dumps({"output_file": str(args.output_file), "example_count": len(records)}, indent=2))


if __name__ == "__main__":
    main()
