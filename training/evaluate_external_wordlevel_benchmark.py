#!/usr/bin/env python3
"""
Evaluate a saved stand-up word-level model on an external benchmark file.

This bridges the current XLM-R pipeline to external word-level benchmarks such
as StandUp4AI without relying on the older placeholder-heavy benchmark stack.
Supported input formats:

1. JSONL rows already matching the internal word-level schema:
   {"words": [...], "labels": [...], ...}
2. JSON or JSONL rows with:
   - text + word_labels
   - text + positive_word_indices
   - words + laughter_after_word
3. CSV with the same logical columns, where list-like fields are JSON strings.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from training.xlmr_standup_word_level import (
    StandupExample,
    XLMRStandupConfig,
    build_dataloader,
    choose_device,
    evaluate_model,
    load_saved_model,
)


PUBLISHED_BASELINES: Dict[str, Dict[str, float]] = {
    "standup4ai": {
        "f1": 0.58,
        "iou_f1": 0.58,
    }
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate a saved word-level checkpoint on an external benchmark file.")
    parser.add_argument("--model-dir", type=Path, required=True, help="Directory containing the saved model/tokenizer.")
    parser.add_argument("--summary-file", type=Path, required=True, help="Training summary used to recover eval config.")
    parser.add_argument("--benchmark-file", type=Path, required=True, help="JSON/JSONL/CSV benchmark annotation file.")
    parser.add_argument("--benchmark-name", default="external", help="Benchmark name, e.g. standup4ai.")
    parser.add_argument("--output-file", type=Path, default=None, help="Optional JSON output path.")
    parser.add_argument("--decode-strategy", choices=["argmax", "single_best", "topk_span"], default=None)
    parser.add_argument("--single-best-min-margin", type=float, default=None)
    parser.add_argument("--topk-span-positive-ratio", type=float, default=None)
    parser.add_argument("--topk-span-min-tokens", type=int, default=None)
    parser.add_argument("--topk-span-max-tokens", type=int, default=None)
    parser.add_argument("--topk-span-neighbor-margin", type=float, default=None)
    parser.add_argument("--topk-span-max-neighbors", type=int, default=None)
    parser.add_argument("--topk-span-cue-bonus", type=float, default=None)
    parser.add_argument("--max-length-override", type=int, default=None, help="Optional evaluation max_length override.")
    parser.add_argument(
        "--chunk-word-window",
        type=int,
        default=None,
        help="Optional word-level chunk size for evaluating long transcripts across full coverage.",
    )
    parser.add_argument(
        "--chunk-word-stride",
        type=int,
        default=None,
        help="Optional word-level stride for chunked evaluation. Defaults to chunk window when omitted.",
    )
    parser.add_argument(
        "--fail-on-degenerate-benchmark",
        action="store_true",
        help="Exit with an error when the benchmark contains no positive labels or no usable supervision.",
    )
    parser.add_argument("--device", default=None)
    return parser.parse_args()


def parse_jsonish(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    stripped = value.strip()
    if not stripped:
        return value
    if stripped[0] not in "[{":
        return value
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        return value


def parse_word_labels(payload: Dict[str, Any], words: Sequence[str]) -> List[int]:
    if isinstance(payload.get("labels"), list):
        return [int(label) for label in payload["labels"]]

    word_labels = parse_jsonish(payload.get("word_labels"))
    if isinstance(word_labels, list):
        return [int(label) for label in word_labels]

    positive_indices = parse_jsonish(payload.get("positive_word_indices"))
    if isinstance(positive_indices, list):
        labels = [0] * len(words)
        for index in positive_indices:
            index_int = int(index)
            if 0 <= index_int < len(labels):
                labels[index_int] = 1
        return labels

    laughter_after_word = parse_jsonish(payload.get("laughter_after_word"))
    if isinstance(laughter_after_word, list):
        return [int(label) for label in laughter_after_word]

    raise ValueError("Could not infer word-level labels from benchmark row.")


def parse_words(payload: Dict[str, Any]) -> List[str]:
    words = parse_jsonish(payload.get("words"))
    if isinstance(words, list):
        return [str(word) for word in words]
    text = str(payload.get("text") or payload.get("transcript") or payload.get("caption") or "").strip()
    if not text:
        raise ValueError("Benchmark row missing both 'words' and 'text'.")
    return text.split()


def load_rows(path: Path) -> List[Dict[str, Any]]:
    suffix = path.suffix.lower()
    if suffix == ".jsonl":
        rows: List[Dict[str, Any]] = []
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            if raw_line.strip():
                rows.append(json.loads(raw_line))
        return rows
    if suffix == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict):
            for key in ("samples", "annotations", "data", "items"):
                value = payload.get(key)
                if isinstance(value, list):
                    return value
        raise ValueError(f"Unsupported JSON payload shape in {path}")
    if suffix == ".csv":
        with path.open("r", encoding="utf-8", newline="") as handle:
            return [dict(row) for row in csv.DictReader(handle)]
    raise ValueError(f"Unsupported benchmark file format: {path.suffix}")


def normalize_rows(rows: Iterable[Dict[str, Any]], benchmark_name: str) -> List[StandupExample]:
    examples: List[StandupExample] = []
    normalized_benchmark = benchmark_name.lower()
    for index, payload in enumerate(rows, start=1):
        words = parse_words(payload)
        labels = parse_word_labels(payload, words)
        if len(words) != len(labels):
            raise ValueError(f"Row {index} has mismatched words/labels lengths ({len(words)} != {len(labels)}).")

        metadata = payload.get("metadata") or {}
        laughter_type = (
            payload.get("laughter_type")
            or metadata.get("laughter_type")
            or payload.get("event_type")
            or "unknown"
        )

        examples.append(
            StandupExample(
                example_id=str(payload.get("example_id") or payload.get("sample_id") or f"{normalized_benchmark}_{index:05d}"),
                language=str(payload.get("language") or metadata.get("language") or "en").lower(),
                laughter_type=str(laughter_type).lower(),
                comedian_id=str(payload.get("comedian_id") or payload.get("speaker_id") or payload.get("comedian") or "unknown_comedian"),
                show_id=str(payload.get("show_id") or payload.get("show") or payload.get("performance") or normalized_benchmark),
                words=words,
                labels=labels,
                current_segment_start=max(0, int(metadata.get("current_segment_start") or 0)),
            )
        )
    if not examples:
        raise ValueError("No benchmark examples were loaded.")
    return examples


def load_config(
    summary_file: Path,
    explicit_device: Optional[str],
    decode_strategy: Optional[str],
    single_best_min_margin: Optional[float],
    topk_span_positive_ratio: Optional[float],
    topk_span_min_tokens: Optional[int],
    topk_span_max_tokens: Optional[int],
    topk_span_neighbor_margin: Optional[float],
    topk_span_max_neighbors: Optional[int],
    topk_span_cue_bonus: Optional[float],
    max_length_override: Optional[int],
) -> XLMRStandupConfig:
    payload = json.loads(summary_file.read_text(encoding="utf-8"))
    config: Dict[str, Any] = dict(payload["config"])
    if explicit_device is not None:
        config["device"] = explicit_device
    if decode_strategy is not None:
        config["decode_strategy"] = decode_strategy
    if single_best_min_margin is not None:
        config["single_best_min_margin"] = single_best_min_margin
    if topk_span_positive_ratio is not None:
        config["topk_span_positive_ratio"] = topk_span_positive_ratio
    if topk_span_min_tokens is not None:
        config["topk_span_min_tokens"] = topk_span_min_tokens
    if topk_span_max_tokens is not None:
        config["topk_span_max_tokens"] = topk_span_max_tokens
    if topk_span_neighbor_margin is not None:
        config["topk_span_neighbor_margin"] = topk_span_neighbor_margin
    if topk_span_max_neighbors is not None:
        config["topk_span_max_neighbors"] = topk_span_max_neighbors
    if topk_span_cue_bonus is not None:
        config["topk_span_cue_bonus"] = topk_span_cue_bonus
    if max_length_override is not None:
        config["max_length"] = max_length_override
    return XLMRStandupConfig(**config)


def baseline_reference(benchmark_name: str, metrics: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    published = PUBLISHED_BASELINES.get(benchmark_name.lower())
    if not published:
        return None
    reference: Dict[str, Any] = {"published": published}
    comparisons: Dict[str, float] = {}
    for key in ("f1", "iou_f1"):
        if key in published:
            comparisons[key] = float(metrics[key]) - float(published[key])
    reference["delta"] = comparisons
    return reference


def analyze_benchmark_quality(examples: Sequence[StandupExample]) -> Dict[str, Any]:
    positive_token_count = sum(sum(example.labels) for example in examples)
    positive_example_count = sum(1 for example in examples if any(example.labels))
    laughter_types = sorted({example.laughter_type for example in examples})
    languages = sorted({example.language for example in examples})

    issues: List[str] = []
    if positive_token_count == 0:
        issues.append("no_positive_tokens")
    if positive_example_count == 0:
        issues.append("no_positive_examples")

    return {
        "example_count": len(examples),
        "positive_token_count": int(positive_token_count),
        "positive_example_count": int(positive_example_count),
        "languages": languages,
        "laughter_types": laughter_types,
        "benchmark_usable": not issues,
        "issues": issues,
    }


def chunk_examples(
    examples: Sequence[StandupExample],
    chunk_word_window: Optional[int],
    chunk_word_stride: Optional[int],
) -> List[StandupExample]:
    if chunk_word_window is None or chunk_word_window <= 0:
        return list(examples)

    stride = chunk_word_stride if chunk_word_stride is not None and chunk_word_stride > 0 else chunk_word_window
    chunked: List[StandupExample] = []
    for example in examples:
        total_words = len(example.words)
        if total_words <= chunk_word_window:
            chunked.append(example)
            continue

        start = 0
        chunk_index = 0
        while start < total_words:
            end = min(total_words, start + chunk_word_window)
            chunked.append(
                StandupExample(
                    example_id=f"{example.example_id}__chunk_{chunk_index:03d}",
                    language=example.language,
                    laughter_type=example.laughter_type,
                    comedian_id=example.comedian_id,
                    show_id=example.show_id,
                    words=example.words[start:end],
                    labels=example.labels[start:end],
                    current_segment_start=max(0, example.current_segment_start - start),
                )
            )
            if end >= total_words:
                break
            start += stride
            chunk_index += 1
    return chunked


def main() -> None:
    args = parse_args()
    config = load_config(
        args.summary_file,
        args.device,
        args.decode_strategy,
        args.single_best_min_margin,
        args.topk_span_positive_ratio,
        args.topk_span_min_tokens,
        args.topk_span_max_tokens,
        args.topk_span_neighbor_margin,
        args.topk_span_max_neighbors,
        args.topk_span_cue_bonus,
        args.max_length_override,
    )
    device = choose_device(config.device)
    rows = load_rows(args.benchmark_file)
    base_examples = normalize_rows(rows, benchmark_name=args.benchmark_name)
    quality = analyze_benchmark_quality(base_examples)
    if args.fail_on_degenerate_benchmark and not quality["benchmark_usable"]:
        raise SystemExit(
            f"Benchmark quality check failed for {args.benchmark_file}: {', '.join(quality['issues'])}"
        )
    examples = chunk_examples(base_examples, args.chunk_word_window, args.chunk_word_stride)

    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(args.model_dir, use_fast=True, local_files_only=True)
    model = load_saved_model(args.model_dir, device=device, fallback_config=config)
    dataloader = build_dataloader(
        examples,
        tokenizer=tokenizer,
        batch_size=config.eval_batch_size,
        max_length=config.max_length,
        shuffle=False,
    )
    metrics = evaluate_model(
        model=model,
        dataloader=dataloader,
        device=device,
        iou_threshold=config.iou_threshold,
        positive_class_weight=config.positive_class_weight,
        loss_type=config.loss_type,
        focal_gamma=config.focal_gamma,
        decode_strategy=config.decode_strategy,
        single_best_min_margin=config.single_best_min_margin,
        topk_span_positive_ratio=config.topk_span_positive_ratio,
        topk_span_min_tokens=config.topk_span_min_tokens,
        topk_span_max_tokens=config.topk_span_max_tokens,
        topk_span_neighbor_margin=config.topk_span_neighbor_margin,
        topk_span_max_neighbors=config.topk_span_max_neighbors,
        topk_span_cue_bonus=config.topk_span_cue_bonus,
        span_aware_loss_weight=config.span_aware_loss_weight if config.span_aware_enabled else 0.0,
    )

    output: Dict[str, Any] = {
        "benchmark_name": args.benchmark_name,
        "benchmark_file": str(args.benchmark_file),
        "model_dir": str(args.model_dir),
        "summary_file": str(args.summary_file),
        "example_count": len(examples),
        "base_example_count": len(base_examples),
        "benchmark_quality": quality,
        "chunking": {
            "enabled": args.chunk_word_window is not None,
            "chunk_word_window": args.chunk_word_window,
            "chunk_word_stride": args.chunk_word_stride if args.chunk_word_window is not None else None,
            "evaluated_chunk_count": len(examples),
        },
        "metrics": metrics,
        "baseline_reference": baseline_reference(args.benchmark_name, metrics),
    }

    if args.output_file is not None:
        args.output_file.parent.mkdir(parents=True, exist_ok=True)
        args.output_file.write_text(json.dumps(output, indent=2), encoding="utf-8")

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
