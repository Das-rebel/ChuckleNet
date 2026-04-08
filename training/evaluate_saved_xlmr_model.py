#!/usr/bin/env python3
"""
Evaluate a saved XLM-R stand-up model on validation/test files.

This is useful when the evaluation schema changes, such as adding WESR-style
per-laughter-type reporting, without retraining the underlying checkpoint.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from transformers import AutoTokenizer

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from training.xlmr_standup_word_level import (
    XLMRStandupConfig,
    build_dataloader,
    choose_device,
    evaluate_model,
    load_jsonl_examples,
    load_saved_model,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate a saved XLM-R stand-up checkpoint.")
    parser.add_argument("--model-dir", type=Path, required=True, help="Directory containing the saved model/tokenizer.")
    parser.add_argument("--summary-file", type=Path, required=True, help="Training summary used to recover eval config.")
    parser.add_argument("--valid-file", type=Path, required=True)
    parser.add_argument("--test-file", type=Path, default=None)
    parser.add_argument("--output-file", type=Path, default=None, help="Optional JSON output path.")
    parser.add_argument("--decode-strategy", choices=["argmax", "single_best", "topk_span"], default=None)
    parser.add_argument("--single-best-min-margin", type=float, default=None)
    parser.add_argument("--topk-span-positive-ratio", type=float, default=None)
    parser.add_argument("--topk-span-min-tokens", type=int, default=None)
    parser.add_argument("--topk-span-max-tokens", type=int, default=None)
    parser.add_argument("--topk-span-neighbor-margin", type=float, default=None)
    parser.add_argument("--topk-span-max-neighbors", type=int, default=None)
    parser.add_argument("--topk-span-cue-bonus", type=float, default=None)
    parser.add_argument("--device", default=None)
    return parser.parse_args()


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
    return XLMRStandupConfig(**config)


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
    )
    device = choose_device(config.device)

    tokenizer = AutoTokenizer.from_pretrained(args.model_dir, use_fast=True, local_files_only=True)
    model = load_saved_model(args.model_dir, device=device, fallback_config=config)

    valid_examples = load_jsonl_examples(args.valid_file)
    valid_loader = build_dataloader(
        valid_examples,
        tokenizer=tokenizer,
        batch_size=config.eval_batch_size,
        max_length=config.max_length,
        shuffle=False,
    )
    valid_metrics = evaluate_model(
        model=model,
        dataloader=valid_loader,
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
        "model_dir": str(args.model_dir),
        "summary_file": str(args.summary_file),
        "valid_metrics": valid_metrics,
        "test_metrics": None,
    }

    if args.test_file is not None:
        test_examples = load_jsonl_examples(args.test_file)
        test_loader = build_dataloader(
            test_examples,
            tokenizer=tokenizer,
            batch_size=config.eval_batch_size,
            max_length=config.max_length,
            shuffle=False,
        )
        output["test_metrics"] = evaluate_model(
            model=model,
            dataloader=test_loader,
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

    if args.output_file is not None:
        args.output_file.parent.mkdir(parents=True, exist_ok=True)
        args.output_file.write_text(json.dumps(output, indent=2), encoding="utf-8")

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
