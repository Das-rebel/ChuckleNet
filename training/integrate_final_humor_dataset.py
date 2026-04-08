#!/usr/bin/env python3
"""
Build a unified humor-classification dataset from local source corpora.

Sources:
- MELD utterances mapped with joy -> humor proxy
- Existing Hugging Face humor proxy CSV
- Filtered Reddit jokes CSV
- Synthetic humor CSV
- Real-world YouTube comedy validation split

Outputs:
- Unified deduplicated CSV
- Stratified train/validation/test CSVs
- External-source snapshot CSV
- JSON/Markdown quality reports
- Per-source metrics CSV
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import pandas as pd


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
BRACKET_ONLY_RE = re.compile(r"^(?:\[[^\]]+\]\s*)+$")
NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")

SOURCE_PRIORITY = {
    "real_world_youtube_validation": 4,
    "reddit_jokes": 4,
    "hf_humor_proxy": 3,
    "meld": 2,
    "synthetic_humor": 1,
}

LABEL_ORIGIN_PRIORITY = {
    "direct": 4,
    "weak": 3,
    "proxy": 2,
    "synthetic": 1,
}

REPORT_WORD_LIMIT = 12


@dataclass
class SourceSpec:
    name: str
    expected_rows: int | None
    path: Path
    enabled: bool = True


def normalize_text(text: Any) -> str:
    if text is None:
        return ""
    normalized = str(text)
    normalized = normalized.replace("\ufeff", "")
    normalized = normalized.replace("\r", " ").replace("\n", " ").replace("\t", " ")
    normalized = normalized.replace("“", '"').replace("”", '"')
    normalized = normalized.replace("’", "'").replace("‘", "'")
    normalized = normalized.replace("\u00a0", " ")
    normalized = normalized.replace("…", "...")
    return re.sub(r"\s+", " ", normalized).strip()


def detokenize_words(words: Iterable[str]) -> str:
    text = " ".join(normalize_text(word) for word in words if normalize_text(word))
    text = re.sub(r"\s+([,.;:!?%])", r"\1", text)
    text = re.sub(r"([(\[{])\s+", r"\1", text)
    text = re.sub(r"\s+([)\]}])", r"\1", text)
    text = text.replace(" n't", "n't")
    text = text.replace(" ’s", "'s").replace(" 's", "'s")
    text = text.replace(" ’re", "'re").replace(" 're", "'re")
    text = text.replace(" ’ve", "'ve").replace(" 've", "'ve")
    text = text.replace(" ’ll", "'ll").replace(" 'll", "'ll")
    text = text.replace(" ’d", "'d").replace(" 'd", "'d")
    return normalize_text(text)


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


def canonicalize_for_dedup(text: str) -> str:
    normalized = normalize_text(text).lower()
    canonical = NON_ALNUM_RE.sub(" ", normalized)
    canonical = re.sub(r"\s+", " ", canonical).strip()
    return canonical


def assess_text_quality(text: str, label_origin: str) -> dict[str, Any]:
    text_length = len(text)
    tokens = [token.lower() for token in TOKEN_RE.findall(text)]
    alpha_chars = sum(1 for char in text if char.isalpha())
    ascii_chars = sum(1 for char in text if ord(char) < 128)
    punctuation_chars = sum(1 for char in text if not char.isalnum() and not char.isspace())
    unique_ratio = (len(set(tokens)) / len(tokens)) if tokens else 0.0
    alpha_ratio = (alpha_chars / text_length) if text_length else 0.0
    ascii_ratio = (ascii_chars / text_length) if text_length else 0.0
    punctuation_ratio = (punctuation_chars / text_length) if text_length else 0.0
    english_hits = sum(1 for token in tokens if token in ENGLISH_FUNCTION_WORDS)

    min_chars = 6 if label_origin in {"weak", "synthetic"} else 8
    max_chars = 2000
    length_ok = min_chars <= text_length <= max_chars

    if text_length < min_chars:
        length_score = max(0, 100 - (min_chars - text_length) * 18)
    elif text_length > max_chars:
        length_score = max(0, 100 - min(100, (text_length - max_chars) // 4))
    else:
        length_score = 100

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
    language_ok = english_score >= 65 and bool(tokens)

    content_score = 100
    if len(tokens) < 2 or len(tokens) > 320:
        content_score -= 35
    if alpha_ratio < 0.45:
        content_score -= 20
    if punctuation_ratio > 0.35:
        content_score -= 15
    if unique_ratio < 0.3 and len(tokens) >= 6:
        content_score -= 20
    if URL_RE.search(text) or EMAIL_RE.search(text):
        content_score -= 35
    if PLACEHOLDER_RE.search(text):
        content_score -= 30
    if REPEATED_CHAR_RE.search(text):
        content_score -= 15
    if BRACKET_ONLY_RE.fullmatch(text):
        content_score -= 50
    content_score = max(0, content_score)
    content_ok = content_score >= 60

    rejection_reasons = []
    if not length_ok:
        rejection_reasons.append("length")
    if not language_ok:
        rejection_reasons.append("language")
    if not content_ok:
        rejection_reasons.append("content")

    quality_score = round(length_score * 0.25 + english_score * 0.35 + content_score * 0.4, 2)
    quality_pass = length_ok and language_ok and content_ok and quality_score >= 70.0

    return {
        "char_length": text_length,
        "word_count": len(tokens),
        "alpha_ratio": round(alpha_ratio, 4),
        "ascii_ratio": round(ascii_ratio, 4),
        "punctuation_ratio": round(punctuation_ratio, 4),
        "unique_token_ratio": round(unique_ratio, 4),
        "english_function_hits": english_hits,
        "length_score": round(length_score, 2),
        "english_score": round(english_score, 2),
        "content_score": round(content_score, 2),
        "quality_score": quality_score,
        "quality_pass": quality_pass,
        "rejection_reasons": rejection_reasons,
    }


def print_status(message: str) -> None:
    print(message, flush=True)


def load_meld(spec: SourceSpec) -> list[dict[str, Any]]:
    split_map = {
        "train_sent_emo.csv": "train",
        "dev_sent_emo.csv": "validation",
        "test_sent_emo.csv": "test",
    }
    rows: list[dict[str, Any]] = []
    for filename, split in split_map.items():
        path = spec.path / filename
        df = pd.read_csv(path)
        for idx, row in df.iterrows():
            emotion = normalize_text(row.get("Emotion"))
            text = normalize_text(row.get("Utterance"))
            rows.append(
                {
                    "sample_id": f"meld_{split}_{idx + 1:06d}",
                    "text": text,
                    "label": 1 if emotion.lower() == "joy" else 0,
                    "source_dataset": "meld",
                    "source_split": split,
                    "source_record_id": f"{row.get('Dialogue_ID')}_{row.get('Utterance_ID')}",
                    "source_label_name": emotion,
                    "label_origin": "proxy",
                    "proxy_signal": "emotion_joy_proxy",
                }
            )
    return rows


def load_hf_humor_proxy(spec: SourceSpec) -> list[dict[str, Any]]:
    df = pd.read_csv(spec.path)
    rows: list[dict[str, Any]] = []
    for row in df.to_dict(orient="records"):
        rows.append(
            {
                "sample_id": str(row["sample_id"]),
                "text": normalize_text(row["text"]),
                "label": int(row["label"]),
                "source_dataset": "hf_humor_proxy",
                "source_split": normalize_text(row.get("source_split", "")) or "unknown",
                "source_record_id": str(row["sample_id"]),
                "source_label_name": normalize_text(row.get("source_label_name", "")),
                "label_origin": "proxy",
                "proxy_signal": normalize_text(row.get("proxy_signal", "")) or "proxy",
            }
        )
    return rows


def load_reddit_jokes(spec: SourceSpec) -> list[dict[str, Any]]:
    df = pd.read_csv(spec.path)
    rows: list[dict[str, Any]] = []
    for row in df.to_dict(orient="records"):
        rows.append(
            {
                "sample_id": str(row["sample_id"]),
                "text": normalize_text(row["text"]),
                "label": int(row["label"]),
                "source_dataset": "reddit_jokes",
                "source_split": "unified",
                "source_record_id": str(row.get("source_id", row["sample_id"])),
                "source_label_name": "humor",
                "label_origin": "direct",
                "proxy_signal": "direct_joke",
            }
        )
    return rows


def load_synthetic_humor(spec: SourceSpec) -> list[dict[str, Any]]:
    df = pd.read_csv(spec.path)
    rows: list[dict[str, Any]] = []
    for idx, row in enumerate(df.to_dict(orient="records"), start=1):
        rows.append(
            {
                "sample_id": f"synthetic_{idx:06d}",
                "text": normalize_text(row["text"]),
                "label": int(row["label"]),
                "source_dataset": "synthetic_humor",
                "source_split": "synthetic",
                "source_record_id": str(row.get("variation", idx)),
                "source_label_name": "humor" if int(row["label"]) == 1 else "non_humor",
                "label_origin": "synthetic",
                "proxy_signal": normalize_text(row.get("source", "")) or "synthetic",
            }
        )
    return rows


def load_real_world_youtube_validation(spec: SourceSpec) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with spec.path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            label = 1 if record.get("has_laughter") or any(record.get("labels", [])) else 0
            text = detokenize_words(record.get("words", []))
            rows.append(
                {
                    "sample_id": str(record["example_id"]),
                    "text": text,
                    "label": int(label),
                    "source_dataset": "real_world_youtube_validation",
                    "source_split": "validation",
                    "source_record_id": str(record["example_id"]),
                    "source_label_name": normalize_text(record.get("laughter_type", "")) or ("laughter" if label else "no_laughter"),
                    "label_origin": "weak",
                    "proxy_signal": "laughter_segment",
                }
            )
    return rows


def load_sources(source_specs: list[SourceSpec]) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    loaders = {
        "meld": load_meld,
        "hf_humor_proxy": load_hf_humor_proxy,
        "reddit_jokes": load_reddit_jokes,
        "synthetic_humor": load_synthetic_humor,
        "real_world_youtube_validation": load_real_world_youtube_validation,
    }

    all_rows: list[dict[str, Any]] = []
    source_metrics: dict[str, dict[str, Any]] = {}

    print_status("STATUS 1: Loading datasets")
    for spec in source_specs:
        if not spec.enabled:
            source_metrics[spec.name] = {
                "status": "disabled",
                "path": str(spec.path),
                "expected_rows": spec.expected_rows,
            }
            continue
        if not spec.path.exists():
            source_metrics[spec.name] = {
                "status": "missing",
                "path": str(spec.path),
                "expected_rows": spec.expected_rows,
            }
            print_status(f"  - {spec.name}: missing at {spec.path}")
            continue
        loader = loaders[spec.name]
        rows = loader(spec)
        all_rows.extend(rows)
        source_metrics[spec.name] = {
            "status": "loaded",
            "path": str(spec.path),
            "expected_rows": spec.expected_rows,
            "rows_loaded": len(rows),
        }
        print_status(f"  - {spec.name}: loaded {len(rows):,} rows from {spec.path}")
    print_status(f"STATUS 1 COMPLETE: loaded {len(all_rows):,} total rows")
    return all_rows, source_metrics


def validate_and_score_rows(
    rows: list[dict[str, Any]],
    source_metrics: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    print_status("STATUS 2: Performing cross-dataset validation")
    validated_rows: list[dict[str, Any]] = []
    rejection_counts = Counter()
    source_internal_seen: dict[str, set[str]] = defaultdict(set)
    source_internal_duplicates = Counter()

    for row in rows:
        source = row["source_dataset"]
        source_metrics.setdefault(source, {})
        source_metrics[source].setdefault("rows_loaded", 0)
        source_metrics[source].setdefault("rows_with_valid_binary_label", 0)
        source_metrics[source].setdefault("rows_quality_pass", 0)
        source_metrics[source].setdefault("rows_rejected_quality", 0)
        source_metrics[source].setdefault("internal_duplicate_rows", 0)
        source_metrics[source].setdefault("raw_positive_rows", 0)
        source_metrics[source].setdefault("raw_negative_rows", 0)
        source_metrics[source].setdefault("quality_scores", [])

        label = row.get("label")
        if label not in {0, 1}:
            rejection_counts["invalid_label"] += 1
            continue

        source_metrics[source]["rows_with_valid_binary_label"] += 1
        if label == 1:
            source_metrics[source]["raw_positive_rows"] += 1
        else:
            source_metrics[source]["raw_negative_rows"] += 1

        text = normalize_text(row.get("text"))
        if not text:
            rejection_counts["empty_text"] += 1
            source_metrics[source]["rows_rejected_quality"] += 1
            continue

        quality = assess_text_quality(text, str(row.get("label_origin", "proxy")))
        row["text"] = text
        row.update(quality)
        row["canonical_text"] = canonicalize_for_dedup(text)
        row["canonical_text_sha1"] = hashlib.sha1(row["canonical_text"].encode("utf-8")).hexdigest()

        if row["canonical_text_sha1"] in source_internal_seen[source]:
            source_internal_duplicates[source] += 1
        else:
            source_internal_seen[source].add(row["canonical_text_sha1"])

        source_metrics[source]["quality_scores"].append(row["quality_score"])

        if not row["quality_pass"]:
            source_metrics[source]["rows_rejected_quality"] += 1
            for reason in row["rejection_reasons"]:
                rejection_counts[f"quality_{reason}"] += 1
            continue

        source_metrics[source]["rows_quality_pass"] += 1
        validated_rows.append(row)

    for source, count in source_internal_duplicates.items():
        source_metrics[source]["internal_duplicate_rows"] = count

    print_status(f"  - binary-label valid rows: {sum(1 for row in rows if row.get('label') in {0, 1}):,}")
    print_status(f"  - quality-pass rows: {len(validated_rows):,}")
    for source, metrics in source_metrics.items():
        if metrics.get("status") != "loaded":
            continue
        print_status(
            "  - "
            f"{source}: loaded={metrics['rows_loaded']:,}, "
            f"quality_pass={metrics.get('rows_quality_pass', 0):,}, "
            f"positives={metrics.get('raw_positive_rows', 0):,}, "
            f"negatives={metrics.get('raw_negative_rows', 0):,}, "
            f"internal_dupes={metrics.get('internal_duplicate_rows', 0):,}"
        )

    return validated_rows, {
        "quality_rejection_counts": dict(rejection_counts),
    }


def deduplicate_rows(
    rows: list[dict[str, Any]],
    source_metrics: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["canonical_text_sha1"]].append(row)

    retained_rows: list[dict[str, Any]] = []
    duplicate_rows_removed = 0
    conflicting_rows_removed = 0
    duplicate_groups = 0
    conflicting_groups = 0
    integrated = 0

    print_status("STATUS 2 UPDATE: deduplicating cross-dataset rows")

    for group_rows in grouped.values():
        labels = {row["label"] for row in group_rows}
        sources = sorted({row["source_dataset"] for row in group_rows})

        if len(group_rows) > 1:
            duplicate_groups += 1

        if len(labels) > 1:
            conflicting_groups += 1
            conflicting_rows_removed += len(group_rows)
            for row in group_rows:
                metrics = source_metrics[row["source_dataset"]]
                metrics["conflicting_rows_removed"] = metrics.get("conflicting_rows_removed", 0) + 1
            continue

        ranked = sorted(
            group_rows,
            key=lambda row: (
                row["quality_score"],
                LABEL_ORIGIN_PRIORITY.get(str(row["label_origin"]), 0),
                SOURCE_PRIORITY.get(row["source_dataset"], 0),
                -row["char_length"],
            ),
            reverse=True,
        )
        kept = dict(ranked[0])
        kept["merged_sources"] = ";".join(sources)
        kept["duplicate_group_size"] = len(group_rows)
        kept["cross_dataset_duplicate"] = len(group_rows) > 1
        retained_rows.append(kept)

        if len(group_rows) > 1:
            duplicate_rows_removed += len(group_rows) - 1
            for row in group_rows[1:]:
                metrics = source_metrics[row["source_dataset"]]
                metrics["duplicate_rows_removed"] = metrics.get("duplicate_rows_removed", 0) + 1

        metrics = source_metrics[kept["source_dataset"]]
        metrics["rows_retained"] = metrics.get("rows_retained", 0) + 1
        if kept["label"] == 1:
            metrics["retained_positive_rows"] = metrics.get("retained_positive_rows", 0) + 1
        else:
            metrics["retained_negative_rows"] = metrics.get("retained_negative_rows", 0) + 1

        integrated += 1
        if integrated % 20000 == 0:
            print_status(f"STATUS 3 UPDATE: integrated {integrated:,} samples into unified corpus")

    retained_rows.sort(key=lambda row: (row["source_dataset"], row["sample_id"]))

    total_quality_rows = len(rows)
    label_consistency = 100.0
    if total_quality_rows:
        label_consistency = round(
            ((total_quality_rows - conflicting_rows_removed) / total_quality_rows) * 100.0,
            2,
        )

    print_status(
        "STATUS 2 COMPLETE: "
        f"retained={len(retained_rows):,}, "
        f"duplicate_rows_removed={duplicate_rows_removed:,}, "
        f"conflicting_rows_removed={conflicting_rows_removed:,}, "
        f"label_consistency={label_consistency:.2f}%"
    )

    return retained_rows, {
        "quality_pass_rows": total_quality_rows,
        "retained_rows": len(retained_rows),
        "duplicate_groups": duplicate_groups,
        "duplicate_rows_removed": duplicate_rows_removed,
        "conflicting_groups": conflicting_groups,
        "conflicting_rows_removed": conflicting_rows_removed,
        "label_consistency_percent": label_consistency,
    }


def stratified_split(
    rows: list[dict[str, Any]],
    train_ratio: float,
    validation_ratio: float,
    test_ratio: float,
    seed: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    rng = random.Random(seed)
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[f"{row['source_dataset']}|{row['label']}"].append(row)

    train_rows: list[dict[str, Any]] = []
    validation_rows: list[dict[str, Any]] = []
    test_rows: list[dict[str, Any]] = []

    for group_rows in groups.values():
        shuffled = list(group_rows)
        rng.shuffle(shuffled)
        n = len(shuffled)
        n_train = int(round(n * train_ratio))
        n_validation = int(round(n * validation_ratio))
        n_test = n - n_train - n_validation

        if n >= 3:
            n_train = max(1, min(n - 2, n_train))
            n_validation = max(1, min(n - n_train - 1, n_validation))
            n_test = n - n_train - n_validation
        elif n == 2:
            n_train = 1
            n_validation = 0
            n_test = 1
        elif n == 1:
            n_train = 1
            n_validation = 0
            n_test = 0

        train_rows.extend(shuffled[:n_train])
        validation_rows.extend(shuffled[n_train : n_train + n_validation])
        test_rows.extend(shuffled[n_train + n_validation :])

    return train_rows, validation_rows, test_rows


def dataframe_from_rows(rows: list[dict[str, Any]]) -> pd.DataFrame:
    columns = [
        "sample_id",
        "text",
        "label",
        "source_dataset",
        "source_split",
        "source_record_id",
        "source_label_name",
        "label_origin",
        "proxy_signal",
        "quality_score",
        "length_score",
        "english_score",
        "content_score",
        "char_length",
        "word_count",
        "alpha_ratio",
        "ascii_ratio",
        "punctuation_ratio",
        "unique_token_ratio",
        "english_function_hits",
        "canonical_text_sha1",
        "merged_sources",
        "duplicate_group_size",
        "cross_dataset_duplicate",
    ]
    normalized_rows = []
    for row in rows:
        normalized_rows.append({column: row.get(column) for column in columns})
    return pd.DataFrame(normalized_rows)


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    labels = Counter(row["label"] for row in rows)
    sources = Counter(row["source_dataset"] for row in rows)
    label_origins = Counter(str(row["label_origin"]) for row in rows)
    quality_scores = [float(row["quality_score"]) for row in rows]
    char_lengths = [float(row["char_length"]) for row in rows]
    word_counts = [float(row["word_count"]) for row in rows]

    return {
        "rows": len(rows),
        "label_distribution": {str(key): value for key, value in sorted(labels.items())},
        "source_distribution": dict(sorted(sources.items())),
        "label_origin_distribution": dict(sorted(label_origins.items())),
        "quality_score_summary": numeric_summary(quality_scores),
        "char_length_summary": numeric_summary(char_lengths),
        "word_count_summary": numeric_summary(word_counts),
    }


def write_markdown_report(
    output_path: Path,
    source_metrics: dict[str, dict[str, Any]],
    validation_summary: dict[str, Any],
    dataset_summary: dict[str, Any],
    split_summary: dict[str, Any],
    performance_projection: dict[str, Any],
    source_inventory: list[dict[str, Any]],
) -> None:
    lines = [
        "# Final Unified Humor Dataset Report",
        "",
        "## Source Inventory",
        "",
    ]

    for source in source_inventory:
        lines.append(
            f"- `{source['source_dataset']}`: status={source['status']}, "
            f"loaded={source.get('rows_loaded', 0):,}, "
            f"path=`{source['path']}`"
        )

    lines.extend(
        [
            "",
            "## Validation Summary",
            "",
            f"- Quality-pass rows: `{validation_summary['quality_pass_rows']:,}`",
            f"- Retained rows: `{validation_summary['retained_rows']:,}`",
            f"- Duplicate rows removed: `{validation_summary['duplicate_rows_removed']:,}`",
            f"- Conflicting rows removed: `{validation_summary['conflicting_rows_removed']:,}`",
            f"- Label consistency: `{validation_summary['label_consistency_percent']:.2f}%`",
            "",
            "## Unified Dataset",
            "",
            f"- Total rows: `{dataset_summary['rows']:,}`",
            f"- Labels: `{dataset_summary['label_distribution']}`",
            f"- Sources: `{dataset_summary['source_distribution']}`",
            f"- Quality mean: `{dataset_summary['quality_score_summary']['mean']}`",
            "",
            "## Splits",
            "",
            f"- Train: `{split_summary['train']['rows']:,}`",
            f"- Validation: `{split_summary['validation']['rows']:,}`",
            f"- Test: `{split_summary['test']['rows']:,}`",
            "",
            "## Training Recommendations",
            "",
            "- Use class weighting or focal loss because Reddit introduces a positive-heavy distribution.",
            "- Treat `meld` and `hf_humor_proxy` as proxy-labeled sources and consider source-aware sampling.",
            "- Keep `real_world_youtube_validation` available as a separate evaluation slice if you want a stricter external benchmark.",
            "",
            "## Performance Projection",
            "",
            f"- Conservative projected F1: `{performance_projection['conservative_f1']:.3f}`",
            f"- Target-band projected F1: `{performance_projection['target_band']}`",
            f"- Basis: {performance_projection['basis']}",
            "",
            "## Per-Source Metrics",
            "",
        ]
    )

    for source, metrics in sorted(source_metrics.items()):
        if metrics.get("status") != "loaded":
            lines.append(f"- `{source}`: status={metrics.get('status')}")
            continue
        mean_quality = numeric_summary(metrics.get("quality_scores", []))["mean"]
        lines.append(
            f"- `{source}`: loaded={metrics.get('rows_loaded', 0):,}, "
            f"quality_pass={metrics.get('rows_quality_pass', 0):,}, "
            f"retained={metrics.get('rows_retained', 0):,}, "
            f"duplicates_removed={metrics.get('duplicate_rows_removed', 0):,}, "
            f"conflicts_removed={metrics.get('conflicting_rows_removed', 0):,}, "
            f"mean_quality={mean_quality}"
        )

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def compute_performance_projection(dataset_summary: dict[str, Any]) -> dict[str, Any]:
    total_rows = dataset_summary["rows"]
    positive_rows = int(dataset_summary["label_distribution"].get("1", 0))
    negative_rows = int(dataset_summary["label_distribution"].get("0", 0))
    proxy_rows = int(dataset_summary["label_origin_distribution"].get("proxy", 0))
    weak_rows = int(dataset_summary["label_origin_distribution"].get("weak", 0))
    direct_rows = int(dataset_summary["label_origin_distribution"].get("direct", 0))
    quality_mean = float(dataset_summary["quality_score_summary"]["mean"])

    diversity_factor = min(0.06, total_rows / 3_000_000)
    direct_signal_factor = min(0.04, (direct_rows + weak_rows) / max(total_rows, 1) * 0.06)
    proxy_penalty = min(0.02, proxy_rows / max(total_rows, 1) * 0.02)
    quality_bonus = max(0.0, min(0.02, (quality_mean - 90.0) / 500.0))
    base_f1 = 0.682
    conservative_f1 = round(base_f1 + diversity_factor + direct_signal_factor + quality_bonus - proxy_penalty, 3)
    optimistic_f1 = round(min(0.85, conservative_f1 + 0.055), 3)

    basis = (
        "Inference from dataset scale, label-origin mix, and retained average quality. "
        "This is a planning estimate, not a measured benchmark."
    )
    return {
        "base_f1": base_f1,
        "conservative_f1": conservative_f1,
        "optimistic_f1": optimistic_f1,
        "target_band": f"{conservative_f1:.3f}-{optimistic_f1:.3f}",
        "basis": basis,
        "class_balance_note": f"positives={positive_rows:,}, negatives={negative_rows:,}",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/training/final_unified_humor"),
        help="Directory for final dataset outputs.",
    )
    parser.add_argument(
        "--meld-dir",
        type=Path,
        default=Path("/Users/Subho/datasets/MELD/data/MELD"),
        help="Directory containing MELD CSV files.",
    )
    parser.add_argument(
        "--hf-csv",
        type=Path,
        default=Path("data/training/hf_humor_proxy/hf_humor_proxy_unified.csv"),
        help="Unified Hugging Face humor proxy CSV.",
    )
    parser.add_argument(
        "--reddit-csv",
        type=Path,
        default=Path("data/training/reddit_jokes/reddit_jokes_humor.csv"),
        help="Processed Reddit jokes CSV.",
    )
    parser.add_argument(
        "--synthetic-csv",
        type=Path,
        default=Path("/Users/Subho/datasets/manual_acquisition/synthetic_humor_dataset.csv"),
        help="Synthetic humor CSV.",
    )
    parser.add_argument(
        "--real-world-jsonl",
        type=Path,
        default=Path("data/training/youtube_comedy_production/valid.jsonl"),
        help="Real-world validation JSONL source.",
    )
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    source_specs = [
        SourceSpec("meld", 13708, args.meld_dir),
        SourceSpec("real_world_youtube_validation", 3000, args.real_world_jsonl),
        SourceSpec("hf_humor_proxy", 77526, args.hf_csv),
        SourceSpec("reddit_jokes", 101609, args.reddit_csv),
        SourceSpec("synthetic_humor", 391, args.synthetic_csv),
    ]

    all_rows, source_metrics = load_sources(source_specs)
    validated_rows, validation_meta = validate_and_score_rows(all_rows, source_metrics)
    retained_rows, dedup_meta = deduplicate_rows(validated_rows, source_metrics)

    print_status("STATUS 3: Creating unified training dataset")
    train_rows, validation_rows, test_rows = stratified_split(
        retained_rows,
        train_ratio=0.8,
        validation_ratio=0.1,
        test_ratio=0.1,
        seed=args.seed,
    )
    print_status(
        "STATUS 3 COMPLETE: "
        f"train={len(train_rows):,}, validation={len(validation_rows):,}, test={len(test_rows):,}"
    )

    print_status("STATUS 4: Generating comprehensive quality report")
    unified_df = dataframe_from_rows(retained_rows)
    train_df = dataframe_from_rows(train_rows)
    validation_df = dataframe_from_rows(validation_rows)
    test_df = dataframe_from_rows(test_rows)
    real_world_df = unified_df[unified_df["source_dataset"] == "real_world_youtube_validation"].copy()

    unified_csv = output_dir / "unified_dataset.csv"
    train_csv = output_dir / "train.csv"
    validation_csv = output_dir / "validation.csv"
    test_csv = output_dir / "test.csv"
    real_world_csv = output_dir / "real_world_validation_snapshot.csv"
    source_metrics_csv = output_dir / "source_metrics.csv"
    quality_report_json = output_dir / "quality_report.json"
    quality_report_md = output_dir / "quality_report.md"
    metadata_json = output_dir / "metadata.json"

    unified_df.to_csv(unified_csv, index=False, quoting=csv.QUOTE_MINIMAL)
    train_df.to_csv(train_csv, index=False, quoting=csv.QUOTE_MINIMAL)
    validation_df.to_csv(validation_csv, index=False, quoting=csv.QUOTE_MINIMAL)
    test_df.to_csv(test_csv, index=False, quoting=csv.QUOTE_MINIMAL)
    real_world_df.to_csv(real_world_csv, index=False, quoting=csv.QUOTE_MINIMAL)

    source_metrics_rows = []
    for source, metrics in sorted(source_metrics.items()):
        source_metrics_rows.append(
            {
                "source_dataset": source,
                "status": metrics.get("status"),
                "path": metrics.get("path"),
                "expected_rows": metrics.get("expected_rows"),
                "rows_loaded": metrics.get("rows_loaded", 0),
                "rows_with_valid_binary_label": metrics.get("rows_with_valid_binary_label", 0),
                "rows_quality_pass": metrics.get("rows_quality_pass", 0),
                "rows_rejected_quality": metrics.get("rows_rejected_quality", 0),
                "internal_duplicate_rows": metrics.get("internal_duplicate_rows", 0),
                "duplicate_rows_removed": metrics.get("duplicate_rows_removed", 0),
                "conflicting_rows_removed": metrics.get("conflicting_rows_removed", 0),
                "rows_retained": metrics.get("rows_retained", 0),
                "raw_positive_rows": metrics.get("raw_positive_rows", 0),
                "raw_negative_rows": metrics.get("raw_negative_rows", 0),
                "retained_positive_rows": metrics.get("retained_positive_rows", 0),
                "retained_negative_rows": metrics.get("retained_negative_rows", 0),
                "mean_quality_score": numeric_summary(metrics.get("quality_scores", []))["mean"],
            }
        )
    pd.DataFrame(source_metrics_rows).to_csv(source_metrics_csv, index=False)

    dataset_summary = summarize_rows(retained_rows)
    split_summary = {
        "train": summarize_rows(train_rows),
        "validation": summarize_rows(validation_rows),
        "test": summarize_rows(test_rows),
    }
    performance_projection = compute_performance_projection(dataset_summary)

    report = {
        "generated_at": pd.Timestamp.utcnow().isoformat(),
        "sources": {
            spec.name: {
                "path": str(spec.path),
                "expected_rows": spec.expected_rows,
                "status": source_metrics.get(spec.name, {}).get("status", "unknown"),
                "rows_loaded": source_metrics.get(spec.name, {}).get("rows_loaded", 0),
            }
            for spec in source_specs
        },
        "validation_summary": {
            **validation_meta,
            **dedup_meta,
        },
        "dataset_summary": dataset_summary,
        "split_summary": split_summary,
        "source_metrics": source_metrics_rows,
        "performance_projection": performance_projection,
        "success_criteria": {
            "minimum_150k_rows": dataset_summary["rows"] >= 150000,
            "label_consistency_over_95": dedup_meta["label_consistency_percent"] > 95.0,
            "average_quality_over_90": dataset_summary["quality_score_summary"]["mean"] > 90.0,
            "real_world_source_loaded": source_metrics.get("real_world_youtube_validation", {}).get("status") == "loaded",
        },
        "notes": [
            "The requested real-world validation source was resolved to data/training/youtube_comedy_production/valid.jsonl with 3,004 rows on 2026-04-05.",
            "The requested synthetic dataset count was resolved to 390 rows from /Users/Subho/datasets/manual_acquisition/synthetic_humor_dataset.csv, not 391.",
            "MELD and hf_humor_proxy are proxy-labeled sources and should be treated differently from direct joke or laughter supervision during training.",
        ],
    }
    quality_report_json.write_text(json.dumps(report, indent=2), encoding="utf-8")

    write_markdown_report(
        output_path=quality_report_md,
        source_metrics=source_metrics,
        validation_summary=report["validation_summary"],
        dataset_summary=dataset_summary,
        split_summary=split_summary,
        performance_projection=performance_projection,
        source_inventory=source_metrics_rows,
    )

    metadata = {
        "files": {
            "unified_csv": str(unified_csv),
            "train_csv": str(train_csv),
            "validation_csv": str(validation_csv),
            "test_csv": str(test_csv),
            "real_world_validation_snapshot_csv": str(real_world_csv),
            "source_metrics_csv": str(source_metrics_csv),
            "quality_report_json": str(quality_report_json),
            "quality_report_md": str(quality_report_md),
        },
        "split_policy": {
            "train_ratio": 0.8,
            "validation_ratio": 0.1,
            "test_ratio": 0.1,
            "stratification": "source_dataset + label",
            "seed": args.seed,
        },
        "columns": list(unified_df.columns),
    }
    metadata_json.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print_status("STATUS 4 COMPLETE: report and metadata written")
    print_status("STATUS 5: Final training-ready files created")
    print_status(f"  - unified dataset: {unified_csv}")
    print_status(f"  - train split: {train_csv}")
    print_status(f"  - validation split: {validation_csv}")
    print_status(f"  - test split: {test_csv}")
    print_status(f"  - quality report: {quality_report_json}")
    print_status(
        "FINAL SUMMARY: "
        f"rows={dataset_summary['rows']:,}, "
        f"label_consistency={dedup_meta['label_consistency_percent']:.2f}%, "
        f"mean_quality={dataset_summary['quality_score_summary']['mean']}, "
        f"projected_f1_band={performance_projection['target_band']}"
    )


if __name__ == "__main__":
    main()
