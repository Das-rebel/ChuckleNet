#!/usr/bin/env python3
"""
Process the local Reddit jokes dump into a filtered humor training CSV.

Features:
- Streaming JSON parsing for top-level arrays and NDJSON.
- Duplicate removal using a punctuation-insensitive canonical form.
- Quality filtering for English, length, offensiveness, and low-signal text.
- CSV output plus JSON/Markdown processing reports.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Iterator


TOKEN_RE = re.compile(r"[A-Za-z]+(?:['-][A-Za-z]+)?")
URL_RE = re.compile(r"(https?://|www\.)", re.IGNORECASE)
EMAIL_RE = re.compile(r"\b\S+@\S+\.\S+\b")
PLACEHOLDER_RE = re.compile(r"\b(?:n/?a|none|null|lorem ipsum|test test)\b", re.IGNORECASE)
REPEATED_CHAR_RE = re.compile(r"(.)\1{4,}")
DELETED_RE = re.compile(r"^\s*\[(?:removed|deleted)\]\s*$", re.IGNORECASE)
OFFENSIVE_RE = re.compile(
    r"\b(?:"
    r"nigg(?:a|er)s?|fag(?:got|s)?|kikes?|spics?|chinks?|trann(?:y|ies)|"
    r"rape|rapist|molest(?:er|ed|ing)?|pedoph(?:ile|ilia)|"
    r"incest|bestiality|necrophilia|gas\s+chamber|holocaust|lynch(?:ed|ing)?"
    r")\b",
    re.IGNORECASE,
)
EXPLICIT_RE = re.compile(
    r"\b(?:"
    r"blowjob|deepthroat|gangbang|cumshot|orgasm|masturbat(?:e|ing|ion)|"
    r"anal\s+sex|semen|clitoris|penis|vagina"
    r")\b",
    re.IGNORECASE,
)

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


def normalize_text(text: Any) -> str:
    if text is None:
        return ""
    normalized = str(text)
    normalized = normalized.replace("\ufeff", "")
    normalized = normalized.replace("\r", " ").replace("\n", " ").replace("\t", " ")
    normalized = normalized.replace("“", '"').replace("”", '"')
    normalized = normalized.replace("’", "'").replace("‘", "'")
    normalized = normalized.replace("\u00a0", " ")
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


def truncated(text: str, max_chars: int = 180) -> str:
    text = normalize_text(text)
    if len(text) <= max_chars:
        return text
    return f"{text[: max_chars - 3]}..."


def add_rejection_sample(
    bucket: dict[str, list[dict[str, Any]]],
    reason: str,
    row: dict[str, Any],
    text: str,
    limit: int = 3,
) -> None:
    samples = bucket[reason]
    if len(samples) >= limit:
        return
    samples.append(
        {
            "source_id": row.get("id"),
            "score": row.get("score"),
            "title": truncated(str(row.get("title", ""))),
            "body": truncated(str(row.get("body", ""))),
            "text": truncated(text),
        }
    )


def iter_json_array_objects(path: Path, chunk_size: int = 1024 * 1024) -> Iterator[tuple[str, int]]:
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        started_array = False
        capturing = False
        in_string = False
        escape_next = False
        brace_depth = 0
        current: list[str] = []
        first_non_ws: str | None = None
        bytes_consumed = 0

        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            bytes_consumed += len(chunk.encode("utf-8"))
            for char in chunk:
                if first_non_ws is None and not char.isspace():
                    first_non_ws = char
                    if char != "[":
                        raise ValueError("JSON array parser expected '[' as the first non-whitespace character")
                    started_array = True
                    continue

                if not started_array:
                    if char.isspace():
                        continue
                    if char == "[":
                        started_array = True
                        continue
                    raise ValueError("JSON array parser could not find the opening '['")

                if not capturing:
                    if char == "{":
                        capturing = True
                        brace_depth = 1
                        in_string = False
                        escape_next = False
                        current = ["{"]
                    elif char == "]":
                        return
                    else:
                        continue
                    continue

                current.append(char)
                if in_string:
                    if escape_next:
                        escape_next = False
                    elif char == "\\":
                        escape_next = True
                    elif char == '"':
                        in_string = False
                    continue

                if char == '"':
                    in_string = True
                elif char == "{":
                    brace_depth += 1
                elif char == "}":
                    brace_depth -= 1
                    if brace_depth == 0:
                        yield "".join(current), bytes_consumed
                        current = []
                        capturing = False

        if capturing and current:
            raise ValueError("JSON array parser reached EOF while reading an object")


def iter_ndjson_lines(path: Path) -> Iterator[tuple[str, int]]:
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        bytes_consumed = 0
        for line in handle:
            text = line.strip()
            bytes_consumed += len(line.encode("utf-8"))
            if text:
                yield text, bytes_consumed


def iter_json_objects(path: Path) -> tuple[str, Iterable[tuple[str, int]]]:
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        first_non_ws = ""
        while True:
            char = handle.read(1)
            if not char:
                break
            if char in {"\ufeff"}:
                continue
            if not char.isspace():
                first_non_ws = char
                break

    if first_non_ws == "[":
        return "json_array_stream", iter_json_array_objects(path)

    return "ndjson", iter_ndjson_lines(path)


def clean_segment(text: Any) -> str:
    cleaned = normalize_text(text)
    if DELETED_RE.match(cleaned):
        return ""
    return cleaned


def build_combined_text(title: str, body: str) -> str:
    if title and body:
        if title.casefold() == body.casefold():
            return title
        return f"{title} {body}"
    return title or body


def canonicalize_text(text: str) -> str:
    collapsed = re.sub(r"[^a-z0-9]+", " ", text.casefold())
    return re.sub(r"\s+", " ", collapsed).strip()


def print_status(message: str) -> None:
    print(message, flush=True)


def write_checkpoint(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def assess_text_quality(
    text: str,
    min_chars: int,
    max_chars: int,
    min_score: int,
    reddit_score: int,
    quality_threshold: float,
) -> dict[str, Any]:
    text_length = len(text)
    tokens = [token.lower() for token in TOKEN_RE.findall(text)]
    alpha_chars = sum(1 for char in text if char.isalpha())
    ascii_chars = sum(1 for char in text if ord(char) < 128)
    punctuation_chars = sum(1 for char in text if not char.isalnum() and not char.isspace())
    digit_chars = sum(1 for char in text if char.isdigit())
    unique_ratio = (len(set(tokens)) / len(tokens)) if tokens else 0.0
    alpha_ratio = alpha_chars / text_length if text_length else 0.0
    ascii_ratio = ascii_chars / text_length if text_length else 0.0
    punctuation_ratio = punctuation_chars / text_length if text_length else 0.0
    digit_ratio = digit_chars / text_length if text_length else 0.0
    english_hits = sum(1 for token in tokens if token in ENGLISH_FUNCTION_WORDS)

    length_ok = min_chars <= text_length <= max_chars
    length_score = 100
    if text_length < min_chars:
        length_score = max(0, 100 - (min_chars - text_length) * 8)
    elif text_length > max_chars:
        length_score = max(0, 100 - min(100, text_length - max_chars))

    english_score = 0
    if ascii_ratio >= 0.98:
        english_score += 35
    elif ascii_ratio >= 0.95:
        english_score += 25
    elif ascii_ratio >= 0.90:
        english_score += 10

    if alpha_ratio >= 0.60:
        english_score += 25
    elif alpha_ratio >= 0.50:
        english_score += 15

    if english_hits >= 3:
        english_score += 30
    elif english_hits == 2:
        english_score += 25
    elif english_hits == 1:
        english_score += 15
    elif len(tokens) >= 4:
        english_score += 5

    if tokens and all(token.isascii() for token in tokens):
        english_score += 10
    language_ok = english_score >= 70 and bool(tokens)

    content_score = 100
    if len(tokens) < 4 or len(tokens) > 100:
        content_score -= 35
    if alpha_ratio < 0.55:
        content_score -= 20
    if punctuation_ratio > 0.25:
        content_score -= 15
    if unique_ratio < 0.38 and len(tokens) >= 8:
        content_score -= 20
    if digit_ratio > 0.20:
        content_score -= 15
    if URL_RE.search(text) or EMAIL_RE.search(text):
        content_score -= 35
    if PLACEHOLDER_RE.search(text):
        content_score -= 30
    if REPEATED_CHAR_RE.search(text):
        content_score -= 15
    if len(re.findall(r"[.!?]", text)) == 0 and len(tokens) > 20:
        content_score -= 10
    content_score = max(0, content_score)
    content_ok = content_score >= 70

    reddit_score_ok = reddit_score >= min_score

    rejection_reasons: list[str] = []
    if not length_ok:
        rejection_reasons.append("length")
    if not language_ok:
        rejection_reasons.append("language")
    if not content_ok:
        rejection_reasons.append("content")
    if not reddit_score_ok:
        rejection_reasons.append("reddit_score")

    quality_score = round(length_score * 0.25 + english_score * 0.35 + content_score * 0.40, 2)

    return {
        "char_length": text_length,
        "word_count": len(tokens),
        "alpha_ratio": round(alpha_ratio, 4),
        "ascii_ratio": round(ascii_ratio, 4),
        "punctuation_ratio": round(punctuation_ratio, 4),
        "digit_ratio": round(digit_ratio, 4),
        "unique_token_ratio": round(unique_ratio, 4),
        "english_function_hits": english_hits,
        "length_score": round(length_score, 2),
        "english_score": round(float(english_score), 2),
        "content_score": round(float(content_score), 2),
        "quality_score": quality_score,
        "length_ok": length_ok,
        "language_ok": language_ok,
        "content_ok": content_ok,
        "reddit_score_ok": reddit_score_ok,
        "quality_pass": not rejection_reasons and quality_score >= quality_threshold,
        "rejection_reasons": rejection_reasons,
    }


def build_markdown_report(report: dict[str, Any]) -> str:
    validation = report["validation"]
    parsing = report["parsing"]
    outputs = report["outputs"]
    success = report["success_criteria"]
    examples = report["example_samples"]

    lines = [
        "# Reddit Jokes Processing Report",
        "",
        "## Validation",
        "",
        f"- Input file: `{validation['input_file']}`",
        f"- Input exists: `{validation['input_exists']}`",
        f"- Input size (MB): `{validation['input_size_mb']}`",
        f"- Parser mode: `{parsing['parser_mode']}`",
        f"- Total parsed rows: `{parsing['parsed_rows']}`",
        f"- Malformed rows skipped: `{parsing['malformed_rows']}`",
        "",
        "## Filters",
        "",
        f"- Length range: `{validation['min_chars']}` to `{validation['max_chars']}` characters",
        f"- Minimum Reddit score: `{validation['min_reddit_score']}`",
        f"- Quality threshold: `{validation['quality_threshold']}`",
        "- English-only heuristic: `ascii/function-word/alpha-ratio composite`",
        "- Offensive filter: `hate-slur + explicit-harm + explicit-sexual term blocklist`",
        "- Duplicate filter: `punctuation-insensitive canonical text hash`",
        "",
        "## Output Counts",
        "",
        f"- Accepted jokes: `{outputs['accepted_rows']}`",
        f"- Label 1 rows: `{outputs['label_counts']['1']}`",
        f"- Unique canonical jokes kept: `{outputs['unique_canonical_texts']}`",
        f"- Mean quality score: `{outputs['quality_score_summary']['mean']}`",
        f"- Mean character length: `{outputs['char_length_summary']['mean']}`",
        f"- Mean word count: `{outputs['word_count_summary']['mean']}`",
        "",
        "## Rejection Counts",
        "",
    ]

    for reason, count in outputs["rejection_counts"].items():
        lines.append(f"- {reason}: `{count}`")

    lines.extend(
        [
            "",
            "## Success Criteria",
            "",
            f"- Minimum 50,000 high-quality jokes: `{success['minimum_50k_met']}`",
            f"- Mean quality score >= 90: `{success['quality_over_90_met']}`",
            f"- CSV created: `{success['csv_created']}`",
            f"- JSON report created: `{success['json_report_created']}`",
            f"- Markdown report created: `{success['markdown_report_created']}`",
            "",
            "## Files",
            "",
        ]
    )

    for name, path in outputs["files"].items():
        lines.append(f"- {name}: `{path}`")

    lines.extend(["", "## Sample Accepted Jokes", ""])
    for sample in examples["accepted"]:
        lines.append(f"- `{sample['source_id']}`: {sample['text']}")

    lines.extend(["", "## Sample Rejections", ""])
    for reason, samples in examples["rejected"].items():
        for sample in samples:
            lines.append(f"- {reason}: `{sample['source_id']}`: {sample['text']}")

    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-file",
        default="~/datasets/manual_acquisition/reddit-jokes/download.json",
        help="Path to the Reddit jokes dump.",
    )
    parser.add_argument(
        "--output-dir",
        default="data/training/reddit_jokes",
        help="Directory for the cleaned CSV and reports.",
    )
    parser.add_argument(
        "--min-chars",
        type=int,
        default=20,
        help="Minimum character length allowed.",
    )
    parser.add_argument(
        "--max-chars",
        type=int,
        default=500,
        help="Maximum character length allowed.",
    )
    parser.add_argument(
        "--min-reddit-score",
        type=int,
        default=1,
        help="Minimum Reddit score required to keep a joke.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Optional row limit for smoke tests.",
    )
    parser.add_argument(
        "--quality-threshold",
        type=float,
        default=87.0,
        help="Minimum composite quality score required after all boolean filters pass.",
    )
    args = parser.parse_args()

    input_file = Path(args.input_file).expanduser()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    cleaned_csv = output_dir / "reddit_jokes_humor.csv"
    report_json = output_dir / "reddit_jokes_processing_report.json"
    report_md = output_dir / "reddit_jokes_processing_report.md"
    checkpoints_dir = output_dir / "checkpoints"
    checkpoints_dir.mkdir(parents=True, exist_ok=True)
    latest_checkpoint = checkpoints_dir / "latest_checkpoint.json"

    parser_mode = "unknown"
    parsed_rows = 0
    malformed_rows = 0
    accepted_rows = 0
    rejected_rows = 0
    last_progress_bucket = 0
    last_batch_report_rows = 0
    last_batch_accepted_rows = 0
    last_batch_rejected_rows = 0
    next_checkpoint_at = 20000
    start_time = time.time()
    input_size_bytes = input_file.stat().st_size if input_file.exists() else 0

    rejection_counts: Counter[str] = Counter()
    batch_rejection_counts: Counter[str] = Counter()
    accepted_lengths: list[float] = []
    accepted_word_counts: list[float] = []
    accepted_quality_scores: list[float] = []
    accepted_score_values: list[float] = []
    seen_canonical_hashes: set[str] = set()
    accepted_examples: list[dict[str, Any]] = []
    rejected_examples: dict[str, list[dict[str, Any]]] = defaultdict(list)
    batch_accepted_lengths: list[float] = []
    batch_quality_scores: list[float] = []

    csv_columns = [
        "sample_id",
        "text",
        "label",
        "source_dataset",
        "source_id",
        "source_score",
        "title",
        "body",
        "char_length",
        "word_count",
        "quality_score",
        "english_score",
        "content_score",
        "canonical_text_sha1",
    ]

    with cleaned_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=csv_columns)
        writer.writeheader()

        parser_mode, object_iter = iter_json_objects(input_file)
        print_status(
            f"STATUS 1: validated input={input_file} size_mb={round(input_size_bytes / (1024 * 1024), 2)} parser={parser_mode}"
        )
        print_status("STATUS 2: starting streamed parse with 10k-row updates and 20k-row checkpoints")

        for raw_text, bytes_consumed in object_iter:
            if args.limit and parsed_rows >= args.limit:
                break

            parsed_rows += 1
            progress_percent = 0
            if input_size_bytes > 0:
                progress_percent = min(100, int((min(bytes_consumed, input_size_bytes) * 100) / input_size_bytes))
            try:
                raw_value = json.loads(raw_text)
            except json.JSONDecodeError:
                malformed_rows += 1
                rejection_counts["malformed_json"] += 1
                batch_rejection_counts["malformed_json"] += 1
                rejected_rows += 1
            else:
                if not isinstance(raw_value, dict):
                    malformed_rows += 1
                    rejection_counts["invalid_row_type"] += 1
                    batch_rejection_counts["invalid_row_type"] += 1
                    rejected_rows += 1
                else:
                    title = clean_segment(raw_value.get("title"))
                    body = clean_segment(raw_value.get("body"))
                    text = build_combined_text(title, body)
                    if not text:
                        rejection_counts["empty_text"] += 1
                        batch_rejection_counts["empty_text"] += 1
                        rejected_rows += 1
                        add_rejection_sample(rejected_examples, "empty_text", raw_value, text)
                    elif OFFENSIVE_RE.search(text) or EXPLICIT_RE.search(text):
                        rejection_counts["offensive_or_inappropriate"] += 1
                        batch_rejection_counts["offensive_or_inappropriate"] += 1
                        rejected_rows += 1
                        add_rejection_sample(rejected_examples, "offensive_or_inappropriate", raw_value, text)
                    else:
                        canonical_text = canonicalize_text(text)
                        if not canonical_text:
                            rejection_counts["empty_canonical_text"] += 1
                            batch_rejection_counts["empty_canonical_text"] += 1
                            rejected_rows += 1
                            add_rejection_sample(rejected_examples, "empty_canonical_text", raw_value, text)
                        else:
                            canonical_hash = hashlib.sha1(canonical_text.encode("utf-8")).hexdigest()
                            if canonical_hash in seen_canonical_hashes:
                                rejection_counts["duplicate"] += 1
                                batch_rejection_counts["duplicate"] += 1
                                rejected_rows += 1
                                add_rejection_sample(rejected_examples, "duplicate", raw_value, text)
                            else:
                                seen_canonical_hashes.add(canonical_hash)

                                try:
                                    reddit_score = int(raw_value.get("score", 0) or 0)
                                except (TypeError, ValueError):
                                    reddit_score = 0

                                quality = assess_text_quality(
                                    text=text,
                                    min_chars=args.min_chars,
                                    max_chars=args.max_chars,
                                    min_score=args.min_reddit_score,
                                    reddit_score=reddit_score,
                                    quality_threshold=args.quality_threshold,
                                )
                                if not quality["quality_pass"]:
                                    rejected_rows += 1
                                    for reason in quality["rejection_reasons"]:
                                        rejection_counts[reason] += 1
                                        batch_rejection_counts[reason] += 1
                                        add_rejection_sample(rejected_examples, reason, raw_value, text)
                                    if not quality["rejection_reasons"] and quality["quality_score"] < args.quality_threshold:
                                        rejection_counts["quality_threshold"] += 1
                                        batch_rejection_counts["quality_threshold"] += 1
                                        add_rejection_sample(rejected_examples, "quality_threshold", raw_value, text)
                                else:
                                    sample_id = f"reddit_jokes_{parsed_rows:06d}"
                                    writer.writerow(
                                        {
                                            "sample_id": sample_id,
                                            "text": text,
                                            "label": 1,
                                            "source_dataset": "reddit_jokes",
                                            "source_id": raw_value.get("id", ""),
                                            "source_score": reddit_score,
                                            "title": title,
                                            "body": body,
                                            "char_length": quality["char_length"],
                                            "word_count": quality["word_count"],
                                            "quality_score": quality["quality_score"],
                                            "english_score": quality["english_score"],
                                            "content_score": quality["content_score"],
                                            "canonical_text_sha1": canonical_hash,
                                        }
                                    )

                                    accepted_rows += 1
                                    accepted_lengths.append(float(quality["char_length"]))
                                    accepted_word_counts.append(float(quality["word_count"]))
                                    accepted_quality_scores.append(float(quality["quality_score"]))
                                    accepted_score_values.append(float(reddit_score))
                                    batch_accepted_lengths.append(float(quality["char_length"]))
                                    batch_quality_scores.append(float(quality["quality_score"]))

                                    if len(accepted_examples) < 5:
                                        accepted_examples.append(
                                            {
                                                "source_id": raw_value.get("id"),
                                                "score": reddit_score,
                                                "text": truncated(text),
                                            }
                                        )

            if progress_percent >= last_progress_bucket + 10:
                last_progress_bucket = (progress_percent // 10) * 10
                elapsed = max(0.001, time.time() - start_time)
                rows_per_second = parsed_rows / elapsed
                print_status(
                    "STATUS 2: "
                    f"progress={last_progress_bucket}% parsed={parsed_rows} accepted={accepted_rows} "
                    f"rejected={rejected_rows} malformed={malformed_rows} rows_per_sec={rows_per_second:.1f}"
                )

            if parsed_rows - last_batch_report_rows >= 10000:
                batch_parsed_rows = parsed_rows - last_batch_report_rows
                batch_accepted_rows = accepted_rows - last_batch_accepted_rows
                batch_rejected_rows = rejected_rows - last_batch_rejected_rows
                last_batch_report_rows = parsed_rows
                last_batch_accepted_rows = accepted_rows
                last_batch_rejected_rows = rejected_rows
                batch_quality_mean = round(sum(batch_quality_scores) / len(batch_quality_scores), 2) if batch_quality_scores else 0.0
                batch_length_mean = round(sum(batch_accepted_lengths) / len(batch_accepted_lengths), 2) if batch_accepted_lengths else 0.0
                print_status(
                    "STATUS 3: "
                    f"processed={parsed_rows} batch_parsed={batch_parsed_rows} batch_accepted={batch_accepted_rows} "
                    f"batch_rejected={batch_rejected_rows} batch_quality_mean={batch_quality_mean} "
                    f"batch_char_len_mean={batch_length_mean} batch_rejections={dict(sorted(batch_rejection_counts.items()))}"
                )
                batch_rejection_counts.clear()
                batch_accepted_lengths.clear()
                batch_quality_scores.clear()

            if parsed_rows >= next_checkpoint_at:
                handle.flush()
                checkpoint_payload = {
                    "parsed_rows": parsed_rows,
                    "accepted_rows": accepted_rows,
                    "rejected_rows": rejected_rows,
                    "malformed_rows": malformed_rows,
                    "parser_mode": parser_mode,
                    "progress_percent": progress_percent,
                    "rejection_counts": dict(sorted(rejection_counts.items())),
                    "output_csv": str(cleaned_csv),
                    "updated_at_epoch": round(time.time(), 3),
                }
                checkpoint_path = checkpoints_dir / f"checkpoint_{parsed_rows:06d}.json"
                write_checkpoint(checkpoint_path, checkpoint_payload)
                write_checkpoint(latest_checkpoint, checkpoint_payload)
                print_status(
                    f"STATUS 2: checkpoint saved rows={parsed_rows} path={checkpoint_path}"
                )
                next_checkpoint_at += 20000

        handle.flush()

    report = {
        "validation": {
            "input_file": str(input_file),
            "input_exists": input_file.exists(),
            "input_size_mb": round(input_size_bytes / (1024 * 1024), 2) if input_file.exists() else 0.0,
            "min_chars": args.min_chars,
            "max_chars": args.max_chars,
            "min_reddit_score": args.min_reddit_score,
            "quality_threshold": args.quality_threshold,
        },
        "parsing": {
            "parser_mode": parser_mode,
            "parsed_rows": parsed_rows,
            "malformed_rows": malformed_rows,
        },
        "outputs": {
            "accepted_rows": accepted_rows,
            "rejected_rows": rejected_rows,
            "label_counts": {"1": accepted_rows},
            "unique_canonical_texts": accepted_rows,
            "rejection_counts": dict(sorted(rejection_counts.items())),
            "char_length_summary": numeric_summary(accepted_lengths),
            "word_count_summary": numeric_summary(accepted_word_counts),
            "quality_score_summary": numeric_summary(accepted_quality_scores),
            "reddit_score_summary": numeric_summary(accepted_score_values),
            "files": {
                "cleaned_csv": str(cleaned_csv),
                "report_json": str(report_json),
                "report_markdown": str(report_md),
                "latest_checkpoint": str(latest_checkpoint),
            },
        },
        "example_samples": {
            "accepted": accepted_examples,
            "rejected": {reason: samples for reason, samples in sorted(rejected_examples.items())},
        },
        "success_criteria": {
            "minimum_50k_met": accepted_rows >= 50000,
            "quality_over_90_met": numeric_summary(accepted_quality_scores)["mean"] >= 90.0,
            "csv_created": cleaned_csv.exists(),
            "json_report_created": False,
            "markdown_report_created": False,
        },
    }

    report_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    report["success_criteria"]["json_report_created"] = report_json.exists()

    report_md.write_text(build_markdown_report(report), encoding="utf-8")
    report["success_criteria"]["markdown_report_created"] = report_md.exists()

    report_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_checkpoint(
        latest_checkpoint,
        {
            "parsed_rows": parsed_rows,
            "accepted_rows": accepted_rows,
            "rejected_rows": rejected_rows,
            "malformed_rows": malformed_rows,
            "parser_mode": parser_mode,
            "progress_percent": 100,
            "rejection_counts": dict(sorted(rejection_counts.items())),
            "output_csv": str(cleaned_csv),
            "report_json": str(report_json),
            "report_markdown": str(report_md),
            "updated_at_epoch": round(time.time(), 3),
        },
    )

    print_status(f"STATUS 4: text normalization and cleaning complete accepted={accepted_rows}")
    print_status(f"STATUS 5: labeled humor dataset written csv={cleaned_csv} label_1_rows={accepted_rows}")
    print_status(
        "STATUS 6: "
        f"report_ready json={report_json} markdown={report_md} "
        f"mean_quality={report['outputs']['quality_score_summary']['mean']}"
    )

    print(json.dumps(report["outputs"], indent=2))


if __name__ == "__main__":
    main()
