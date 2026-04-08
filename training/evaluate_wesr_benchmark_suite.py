#!/usr/bin/env python3
"""
Evaluate a saved stand-up model across the canonical and WESR-balanced splits.

This gives the repo a taxonomy-aware benchmark summary without changing the
promotion baseline. It is intended to answer:

1. How does the current promoted checkpoint behave on the canonical split?
2. How does it behave on a split where both discrete and continuous laughter
   exist in validation and test?
3. Are the per-type metrics strong enough to treat WESR-style evaluation as a
   meaningful companion benchmark?
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

from training.evaluate_saved_xlmr_model import load_config
from training.xlmr_standup_word_level import (
    build_dataloader,
    choose_device,
    evaluate_model,
    load_jsonl_examples,
    load_saved_model,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate a saved stand-up checkpoint on canonical and WESR-balanced splits.")
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--summary-file", type=Path, required=True)
    parser.add_argument("--canonical-valid-file", type=Path, required=True)
    parser.add_argument("--canonical-test-file", type=Path, required=True)
    parser.add_argument("--wesr-valid-file", type=Path, required=True)
    parser.add_argument("--wesr-test-file", type=Path, required=True)
    parser.add_argument("--companion-name", default=None, help="Optional label for the companion WESR-style benchmark.")
    parser.add_argument("--output-file", type=Path, default=None)
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


def evaluate_split(
    model: Any,
    tokenizer: Any,
    config: Any,
    device: Any,
    path: Path,
) -> Dict[str, Any]:
    examples = load_jsonl_examples(path)
    dataloader = build_dataloader(
        examples,
        tokenizer=tokenizer,
        batch_size=config.eval_batch_size,
        max_length=config.max_length,
        shuffle=False,
        span_aware_radius=config.span_aware_radius,
        span_aware_decay=config.span_aware_decay,
    )
    return evaluate_model(
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


def macro_type_metrics(metrics: Dict[str, Any]) -> Dict[str, Any]:
    per_type = metrics.get("per_laughter_type") or {}
    if not per_type:
        return {
            "taxonomy_usable": False,
            "present_types": [],
            "macro_f1": 0.0,
            "macro_iou_f1": 0.0,
            "min_type_support": 0.0,
        }

    present = sorted(
        type_name
        for type_name, payload in per_type.items()
        if float(payload.get("support", 0.0)) > 0.0
    )
    usable = "continuous" in present and "discrete" in present
    if present:
        macro_f1 = sum(float(per_type[type_name]["f1"]) for type_name in present) / len(present)
        macro_iou_f1 = sum(float(per_type[type_name].get("iou_f1", 0.0)) for type_name in present) / len(present)
        min_type_support = min(float(per_type[type_name]["support"]) for type_name in present)
    else:
        macro_f1 = 0.0
        macro_iou_f1 = 0.0
        min_type_support = 0.0

    return {
        "taxonomy_usable": usable,
        "present_types": present,
        "macro_f1": macro_f1,
        "macro_iou_f1": macro_iou_f1,
        "min_type_support": min_type_support,
    }


def summarize_suite(
    canonical_valid: Dict[str, Any],
    canonical_test: Dict[str, Any],
    wesr_valid: Dict[str, Any],
    wesr_test: Dict[str, Any],
) -> Dict[str, Any]:
    canonical_summary = {
        "valid": macro_type_metrics(canonical_valid),
        "test": macro_type_metrics(canonical_test),
    }
    wesr_summary = {
        "valid": macro_type_metrics(wesr_valid),
        "test": macro_type_metrics(wesr_test),
    }
    return {
        "canonical_taxonomy": canonical_summary,
        "companion_taxonomy": wesr_summary,
        "recommended_companion_gate": {
            "usable": bool(wesr_summary["valid"]["taxonomy_usable"] and wesr_summary["test"]["taxonomy_usable"]),
            "promotion_ready": bool(
                wesr_summary["valid"]["taxonomy_usable"]
                and wesr_summary["test"]["taxonomy_usable"]
                and wesr_summary["valid"]["min_type_support"] >= 10.0
                and wesr_summary["test"]["min_type_support"] >= 10.0
            ),
            "validation_macro_f1": float(wesr_summary["valid"]["macro_f1"]),
            "validation_macro_iou_f1": float(wesr_summary["valid"]["macro_iou_f1"]),
            "test_macro_f1": float(wesr_summary["test"]["macro_f1"]),
            "test_macro_iou_f1": float(wesr_summary["test"]["macro_iou_f1"]),
            "validation_min_type_support": float(wesr_summary["valid"]["min_type_support"]),
            "test_min_type_support": float(wesr_summary["test"]["min_type_support"]),
        },
    }


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

    canonical_valid = evaluate_split(model, tokenizer, config, device, args.canonical_valid_file)
    canonical_test = evaluate_split(model, tokenizer, config, device, args.canonical_test_file)
    wesr_valid = evaluate_split(model, tokenizer, config, device, args.wesr_valid_file)
    wesr_test = evaluate_split(model, tokenizer, config, device, args.wesr_test_file)
    companion_name = args.companion_name or args.wesr_valid_file.parent.name

    output = {
        "model_dir": str(args.model_dir),
        "summary_file": str(args.summary_file),
        "companion_name": companion_name,
        "canonical": {
            "valid_metrics": canonical_valid,
            "test_metrics": canonical_test,
        },
        "companion_benchmark": {
            "valid_metrics": wesr_valid,
            "test_metrics": wesr_test,
        },
        "suite_summary": summarize_suite(canonical_valid, canonical_test, wesr_valid, wesr_test),
    }

    if args.output_file is not None:
        args.output_file.parent.mkdir(parents=True, exist_ok=True)
        args.output_file.write_text(json.dumps(output, indent=2), encoding="utf-8")

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
