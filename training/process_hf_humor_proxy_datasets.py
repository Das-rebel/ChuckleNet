#!/usr/bin/env python3
"""
Process locally saved Hugging Face datasets into a high-quality humor proxy corpus.

Outputs:
- Per-source positive and negative CSVs
- Unified train/validation/test CSVs
- Combined full CSV
- JSON and Markdown quality reports
"""

from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd
from datasets import DatasetDict, load_from_disk


ENGLISH_FUNCTION_WORDS = {
    "a",
    "about",
    "after",
    "all",
    "also",
    "am",
    "an",
    "and",
    "any",
    "are",
    "as",
    "at",
    "be",
    "because",
    "been",
    "before",
    "being",
    "but",
    "by",
    "can",
    "could",
    "did",
    "do",
    "does",
    "dont",
    "down",
    "even",
    "every",
    "feel",
    "for",
    "from",
    "get",
    "go",
    "going",
    "had",
    "has",
    "have",
    "he",
    "her",
    "here",
    "him",
    "his",
    "how",
    "i",
    "id",
    "if",
    "ill",
    "im",
    "in",
    "into",
    "is",
    "it",
    "its",
    "ive",
    "just",
    "know",
    "like",
    "made",
    "make",
    "me",
    "more",
    "most",
    "my",
    "need",
    "no",
    "not",
    "now",
    "of",
    "on",
    "one",
    "only",
    "or",
    "our",
    "out",
    "really",
    "she",
    "should",
    "so",
    "some",
    "than",
    "that",
    "the",
    "their",
    "them",
    "then",
    "there",
    "they",
    "this",
    "to",
    "up",
    "very",
    "was",
    "we",
    "were",
    "what",
    "when",
    "which",
    "who",
    "will",
    "with",
    "would",
    "you",
    "your",
}

TOKEN_RE = re.compile(r"[A-Za-z]+(?:['-][A-Za-z]+)?")
URL_RE = re.compile(r"(https?://|www\.)", re.IGNORECASE)
EMAIL_RE = re.compile(r"\b\S+@\S+\.\S+\b")
PLACEHOLDER_RE = re.compile(r"\b(?:n/?a|none|null|lorem ipsum|test test)\b", re.IGNORECASE)
REPEATED_CHAR_RE = re.compile(r"(.)\1{4,}")


def normalize_text(text: Any) -> str:
    if text is None:
        return ""
    normalized = str(text).replace("\n", " ").replace("\t", " ")
    return re.sub(r"\s+", " ", normalized).strip()


def percentile(sorted_values: list[float], p: float) -> float:
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return float(sorted_values[0])
    index = (len(sorted_values) - 1) * p
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return float(sorted_values[lower])
    lower_value = float(sorted_values[lower])
    upper_value = float(sorted_values[upper])
    return lower_value + (upper_value - lower_value) * (index - lower)


def numeric_summary(values: list[float]) -> dict[str, float]:
    if not values:
        return {
            "count": 0,
            "min": 0.0,
            "max": 0.0,
            "mean": 0.0,
            "median": 0.0,
            "p10": 0.0,
            "p90": 0.0,
        }
    ordered = sorted(float(v) for v in values)
    return {
        "count": len(ordered),
        "min": round(ordered[0], 2),
        "max": round(ordered[-1], 2),
        "mean": round(sum(ordered) / len(ordered), 2),
        "median": round(percentile(ordered, 0.5), 2),
        "p10": round(percentile(ordered, 0.1), 2),
        "p90": round(percentile(ordered, 0.9), 2),
    }


def assess_text_quality(text: str, min_chars: int, max_chars: int) -> dict[str, Any]:
    text_length = len(text)
    tokens = [token.lower() for token in TOKEN_RE.findall(text)]
    alpha_chars = sum(1 for char in text if char.isalpha())
    ascii_chars = sum(1 for char in text if ord(char) < 128)
    punctuation_chars = sum(1 for char in text if not char.isalnum() and not char.isspace())
    unique_ratio = (len(set(tokens)) / len(tokens)) if tokens else 0.0
    alpha_ratio = alpha_chars / text_length if text_length else 0.0
    ascii_ratio = ascii_chars / text_length if text_length else 0.0
    punctuation_ratio = punctuation_chars / text_length if text_length else 0.0
    english_hits = sum(1 for token in tokens if token in ENGLISH_FUNCTION_WORDS)

    length_ok = min_chars <= text_length <= max_chars
    length_score = 100
    if text_length < min_chars:
        length_score = max(0, 100 - (min_chars - text_length) * 10)
    elif text_length > max_chars:
        length_score = max(0, 100 - min(100, (text_length - max_chars)))

    english_score = 0
    if ascii_ratio >= 0.98:
        english_score += 35
    elif ascii_ratio >= 0.95:
        english_score += 25
    elif ascii_ratio >= 0.9:
        english_score += 10

    if alpha_ratio >= 0.6:
        english_score += 25
    elif alpha_ratio >= 0.5:
        english_score += 15

    if english_hits >= 2:
        english_score += 30
    elif english_hits == 1:
        english_score += 20
    elif len(tokens) >= 3:
        english_score += 10

    if tokens and all(token.isascii() for token in tokens):
        english_score += 10
    language_ok = english_score >= 70 and bool(tokens)

    content_score = 100
    if len(tokens) < 3 or len(tokens) > 100:
        content_score -= 35
    if alpha_ratio < 0.55:
        content_score -= 20
    if punctuation_ratio > 0.25:
        content_score -= 15
    if unique_ratio < 0.35 and len(tokens) >= 6:
        content_score -= 20
    if URL_RE.search(text) or EMAIL_RE.search(text):
        content_score -= 35
    if PLACEHOLDER_RE.search(text):
        content_score -= 30
    if REPEATED_CHAR_RE.search(text):
        content_score -= 15
    content_score = max(0, content_score)
    content_ok = content_score >= 70

    rejection_reasons = []
    if not length_ok:
        rejection_reasons.append("length")
    if not language_ok:
        rejection_reasons.append("language")
    if not content_ok:
        rejection_reasons.append("content")

    quality_score = round(length_score * 0.3 + english_score * 0.35 + content_score * 0.35, 2)
    quality_pass = length_ok and language_ok and content_ok and quality_score >= 85.0

    return {
        "normalized_text": text,
        "char_length": text_length,
        "word_count": len(tokens),
        "alpha_ratio": round(alpha_ratio, 4),
        "ascii_ratio": round(ascii_ratio, 4),
        "punctuation_ratio": round(punctuation_ratio, 4),
        "unique_token_ratio": round(unique_ratio, 4),
        "english_function_hits": english_hits,
        "length_score": round(length_score, 2),
        "english_score": round(float(english_score), 2),
        "content_score": round(float(content_score), 2),
        "quality_score": quality_score,
        "length_ok": length_ok,
        "language_ok": language_ok,
        "content_ok": content_ok,
        "quality_pass": quality_pass,
        "rejection_reasons": rejection_reasons,
    }


def validate_dataset(
    dataset_name: str,
    dataset: DatasetDict,
    text_column: str,
    label_column: str,
    positive_label_name: str,
) -> dict[str, Any]:
    split_names = list(dataset.keys())
    if not split_names:
        raise ValueError(f"{dataset_name}: no splits found")

    sample_split = dataset[split_names[0]]
    if text_column not in sample_split.column_names:
        raise ValueError(f"{dataset_name}: missing text column {text_column!r}")
    if label_column not in sample_split.column_names:
        raise ValueError(f"{dataset_name}: missing label column {label_column!r}")

    features = sample_split.features
    label_feature = features[label_column]
    if not hasattr(label_feature, "names"):
        raise ValueError(f"{dataset_name}: label column {label_column!r} is not a ClassLabel")
    label_names = list(label_feature.names)
    if positive_label_name not in label_names:
        raise ValueError(
            f"{dataset_name}: positive label {positive_label_name!r} not found in {label_names}"
        )

    return {
        "dataset_name": dataset_name,
        "splits": split_names,
        "text_column": text_column,
        "label_column": label_column,
        "label_names": label_names,
        "positive_label_name": positive_label_name,
        "positive_label_id": label_names.index(positive_label_name),
        "num_rows": {split: len(dataset[split]) for split in split_names},
    }


def collect_rows(
    dataset_name: str,
    dataset: DatasetDict,
    text_column: str,
    label_column: str,
    label_names: list[str],
    positive_label_id: int,
    min_chars: int,
    max_chars: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    accepted_rows: list[dict[str, Any]] = []
    quality_scores: list[float] = []
    positive_scores: list[float] = []
    negative_scores: list[float] = []
    split_counts_before: Counter[str] = Counter()
    split_counts_after: Counter[str] = Counter()
    class_counts_before: Counter[str] = Counter()
    class_counts_after: Counter[str] = Counter()
    rejection_counts: Counter[str] = Counter()

    for split_name, split_dataset in dataset.items():
        for row_index, row in enumerate(split_dataset):
            raw_text = row[text_column]
            normalized_text = normalize_text(raw_text)
            quality = assess_text_quality(normalized_text, min_chars=min_chars, max_chars=max_chars)
            label_id = int(row[label_column])
            label_name = label_names[label_id]
            humor_label = 1 if label_id == positive_label_id else 0
            target_quality_scores = positive_scores if humor_label == 1 else negative_scores

            split_counts_before[split_name] += 1
            class_counts_before[str(humor_label)] += 1

            if not quality["quality_pass"]:
                for reason in quality["rejection_reasons"]:
                    rejection_counts[f"{dataset_name}:{reason}"] += 1
                continue

            record = {
                "sample_id": f"{dataset_name}_{split_name}_{row_index:06d}",
                "text": normalized_text,
                "label": humor_label,
                "source_dataset": dataset_name,
                "source_split": split_name,
                "source_label_id": label_id,
                "source_label_name": label_name,
                "proxy_signal": "positive_proxy" if humor_label == 1 else "negative_proxy",
                "char_length": quality["char_length"],
                "word_count": quality["word_count"],
                "quality_score": quality["quality_score"],
                "length_score": quality["length_score"],
                "english_score": quality["english_score"],
                "content_score": quality["content_score"],
                "language_ok": quality["language_ok"],
                "content_ok": quality["content_ok"],
                "alpha_ratio": quality["alpha_ratio"],
                "ascii_ratio": quality["ascii_ratio"],
                "punctuation_ratio": quality["punctuation_ratio"],
                "unique_token_ratio": quality["unique_token_ratio"],
                "english_function_hits": quality["english_function_hits"],
            }
            accepted_rows.append(record)

            score = float(quality["quality_score"])
            quality_scores.append(score)
            target_quality_scores.append(score)
            split_counts_after[split_name] += 1
            class_counts_after[str(humor_label)] += 1

    metrics = {
        "dataset_name": dataset_name,
        "split_counts_before": dict(split_counts_before),
        "split_counts_after": dict(split_counts_after),
        "class_counts_before": dict(class_counts_before),
        "class_counts_after": dict(class_counts_after),
        "quality_score_summary": numeric_summary(quality_scores),
        "positive_quality_score_summary": numeric_summary(positive_scores),
        "negative_quality_score_summary": numeric_summary(negative_scores),
        "rejection_counts": dict(sorted(rejection_counts.items())),
    }
    return accepted_rows, metrics


def build_markdown_report(report: dict[str, Any]) -> str:
    validation = report["validation"]
    outputs = report["outputs"]
    success = report["success_criteria"]
    dataset_validation = report["dataset_validation"]

    lines = [
        "# Hugging Face Humor Proxy Dataset Report",
        "",
        "## Validation Summary",
        "",
        f"- Emotion dataset path: `{validation['emotion_path']}`",
        f"- SST-2 dataset path: `{validation['sst2_path']}`",
        f"- Emotion label mapping: `{dataset_validation['emotion']['label_names']}`",
        f"- Emotion positive label used: `{dataset_validation['emotion']['positive_label_name']}` "
        f"(id `{dataset_validation['emotion']['positive_label_id']}`)",
        f"- SST-2 positive label used: `{dataset_validation['sst2']['positive_label_name']}` "
        f"(id `{dataset_validation['sst2']['positive_label_id']}`)",
        f"- Quality filter: min chars `{validation['min_chars']}`, max chars `{validation['max_chars']}`, "
        "English-only heuristic, quality score threshold `85.0`",
        "",
        "## Output Counts",
        "",
        f"- Unified rows: `{outputs['unified_row_count']}`",
        f"- Humor rows: `{outputs['label_counts']['1']}`",
        f"- Non-humor rows: `{outputs['label_counts']['0']}`",
        f"- Mean quality score: `{outputs['quality_score_summary']['mean']}`",
        "",
        "## Split Counts",
        "",
        f"- Train: `{outputs['split_counts'].get('train', 0)}`",
        f"- Validation: `{outputs['split_counts'].get('validation', 0)}`",
        f"- Test: `{outputs['split_counts'].get('test', 0)}`",
        "",
        "## Success Criteria",
        "",
        f"- Minimum 15,000 positive samples: `{success['positive_sample_target_met']}` "
        f"({outputs['label_counts']['1']} available)",
        f"- Mean quality score > 85: `{success['quality_score_target_met']}` "
        f"({outputs['quality_score_summary']['mean']})",
        f"- Ready-to-train files created: `{success['ready_to_train_files_created']}`",
        "",
        "## Files",
        "",
    ]
    for name, path in outputs["files"].items():
        lines.append(f"- {name}: `{path}`")
    lines.extend(["", "## Rejection Counts", ""])
    for dataset_name, metrics in report["source_metrics"].items():
        rejection_counts = metrics["rejection_counts"]
        if not rejection_counts:
            lines.append(f"- {dataset_name}: none")
            continue
        summary = ", ".join(f"{reason}={count}" for reason, count in rejection_counts.items())
        lines.append(f"- {dataset_name}: {summary}")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--emotion-path",
        default="/Users/Subho/datasets/manual_acquisition/emotion",
        help="Path to the locally saved emotion dataset.",
    )
    parser.add_argument(
        "--sst2-path",
        default="/Users/Subho/datasets/manual_acquisition/sst2",
        help="Path to the locally saved SST-2 dataset.",
    )
    parser.add_argument(
        "--output-dir",
        default="data/training/hf_humor_proxy",
        help="Directory for processed CSVs and reports.",
    )
    parser.add_argument(
        "--min-chars",
        type=int,
        default=10,
        help="Minimum character length allowed.",
    )
    parser.add_argument(
        "--max-chars",
        type=int,
        default=500,
        help="Maximum character length allowed.",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    emotion = load_from_disk(args.emotion_path)
    sst2 = load_from_disk(args.sst2_path)

    emotion_validation = validate_dataset(
        dataset_name="emotion",
        dataset=emotion,
        text_column="text",
        label_column="label",
        positive_label_name="joy",
    )
    sst2_validation = validate_dataset(
        dataset_name="sst2",
        dataset=sst2,
        text_column="sentence",
        label_column="label",
        positive_label_name="positive",
    )

    emotion_rows, emotion_metrics = collect_rows(
        dataset_name="emotion",
        dataset=emotion,
        text_column=emotion_validation["text_column"],
        label_column=emotion_validation["label_column"],
        label_names=emotion_validation["label_names"],
        positive_label_id=emotion_validation["positive_label_id"],
        min_chars=args.min_chars,
        max_chars=args.max_chars,
    )
    sst2_rows, sst2_metrics = collect_rows(
        dataset_name="sst2",
        dataset=sst2,
        text_column=sst2_validation["text_column"],
        label_column=sst2_validation["label_column"],
        label_names=sst2_validation["label_names"],
        positive_label_id=sst2_validation["positive_label_id"],
        min_chars=args.min_chars,
        max_chars=args.max_chars,
    )

    all_rows = emotion_rows + sst2_rows
    unified_df = pd.DataFrame(all_rows).sort_values(
        by=["source_split", "label", "source_dataset", "sample_id"],
        ascending=[True, False, True, True],
    )

    emotion_df = pd.DataFrame(emotion_rows)
    sst2_df = pd.DataFrame(sst2_rows)
    if unified_df.empty:
        raise RuntimeError("No rows passed quality validation; no output was written.")

    files = {
        "emotion_positive_csv": str(output_dir / "emotion_joy_humor.csv"),
        "emotion_negative_csv": str(output_dir / "emotion_non_joy_non_humor.csv"),
        "sst2_positive_csv": str(output_dir / "sst2_positive_humor.csv"),
        "sst2_negative_csv": str(output_dir / "sst2_negative_non_humor.csv"),
        "unified_csv": str(output_dir / "hf_humor_proxy_unified.csv"),
        "train_csv": str(output_dir / "hf_humor_proxy_train.csv"),
        "validation_csv": str(output_dir / "hf_humor_proxy_validation.csv"),
        "test_csv": str(output_dir / "hf_humor_proxy_test.csv"),
        "quality_report_json": str(output_dir / "quality_report.json"),
        "quality_report_md": str(output_dir / "quality_report.md"),
    }

    emotion_df[emotion_df["label"] == 1].to_csv(files["emotion_positive_csv"], index=False)
    emotion_df[emotion_df["label"] == 0].to_csv(files["emotion_negative_csv"], index=False)
    sst2_df[sst2_df["label"] == 1].to_csv(files["sst2_positive_csv"], index=False)
    sst2_df[sst2_df["label"] == 0].to_csv(files["sst2_negative_csv"], index=False)
    unified_df.to_csv(files["unified_csv"], index=False)

    split_frames = {split: frame for split, frame in unified_df.groupby("source_split")}
    for split_name in ["train", "validation", "test"]:
        split_path = files[f"{split_name}_csv"]
        split_frames.get(split_name, unified_df.iloc[0:0]).to_csv(split_path, index=False)

    label_counts = Counter(str(int(label)) for label in unified_df["label"].tolist())
    split_counts = Counter(unified_df["source_split"].tolist())
    quality_scores = unified_df["quality_score"].astype(float).tolist()
    source_quality = {
        dataset_name: numeric_summary(frame["quality_score"].astype(float).tolist())
        for dataset_name, frame in unified_df.groupby("source_dataset")
    }

    report = {
        "validation": {
            "emotion_path": args.emotion_path,
            "sst2_path": args.sst2_path,
            "min_chars": args.min_chars,
            "max_chars": args.max_chars,
            "language_detector": "heuristic_english_v1",
            "quality_threshold": 85.0,
        },
        "dataset_validation": {
            "emotion": emotion_validation,
            "sst2": sst2_validation,
        },
        "source_metrics": {
            "emotion": emotion_metrics,
            "sst2": sst2_metrics,
        },
        "outputs": {
            "unified_row_count": len(unified_df),
            "label_counts": {
                "1": int(label_counts.get("1", 0)),
                "0": int(label_counts.get("0", 0)),
            },
            "split_counts": dict(split_counts),
            "quality_score_summary": numeric_summary(quality_scores),
            "source_quality_score_summary": source_quality,
            "files": files,
        },
        "success_criteria": {
            "positive_sample_target_met": int(label_counts.get("1", 0)) >= 15000,
            "quality_score_target_met": numeric_summary(quality_scores)["mean"] > 85.0,
            "ready_to_train_files_created": False,
        },
    }

    with open(files["quality_report_json"], "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
    with open(files["quality_report_md"], "w", encoding="utf-8") as handle:
        handle.write(build_markdown_report(report))
    report["success_criteria"]["ready_to_train_files_created"] = all(
        Path(path).exists() for path in files.values()
    )
    with open(files["quality_report_json"], "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
    with open(files["quality_report_md"], "w", encoding="utf-8") as handle:
        handle.write(build_markdown_report(report))

    print(json.dumps(report["outputs"], indent=2))


if __name__ == "__main__":
    main()
