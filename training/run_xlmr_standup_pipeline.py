#!/usr/bin/env python3
"""
Weekly stand-up pipeline runner.

Stages:
1. Convert raw transcripts to weak word-level labels
2. Optionally refine training labels with a local teacher model
3. Train and evaluate the XLM-R baseline
"""

from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from pathlib import Path
from typing import List


PROJECT_ROOT = Path("/Users/Subho/autonomous_laughter_prediction")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the full stand-up XLM-R pipeline.")
    parser.add_argument("--raw-dir", type=Path, default=PROJECT_ROOT / "data" / "raw")
    parser.add_argument(
        "--dataset-dir",
        type=Path,
        default=PROJECT_ROOT / "data" / "training" / "standup_word_level",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "experiments" / "xlmr_standup_baseline",
    )
    parser.add_argument("--skip-convert", action="store_true")
    parser.add_argument(
        "--split-strategy",
        choices=["overlap_safe", "wesr_balanced"],
        default="overlap_safe",
        help="Dataset conversion split strategy.",
    )
    parser.add_argument(
        "--context-token-policy",
        choices=["full", "lexical_tail", "clause_lexical_tail"],
        default="clause_lexical_tail",
        help="How to represent prepended context during dataset conversion.",
    )
    parser.add_argument(
        "--context-tail-tokens",
        type=int,
        default=6,
        help="Number of lexical context tokens to keep for lexical-tail context policies.",
    )
    parser.add_argument("--skip-refine", action="store_true")
    parser.add_argument("--backend", choices=["openai", "ollama"], default="openai")
    parser.add_argument("--endpoint", default="http://127.0.0.1:1234/v1/chat/completions")
    parser.add_argument("--teacher-model", default="qwen2.5-coder:1.5b")
    parser.add_argument("--teacher-min-confidence", type=float, default=0.6)
    parser.add_argument("--teacher-max-examples", type=int, default=None)
    parser.add_argument("--teacher-write-every", type=int, default=25)
    parser.add_argument("--teacher-progress-every", type=int, default=10)
    parser.add_argument("--teacher-resume", action="store_true")
    parser.add_argument(
        "--refined-train-policy",
        choices=["refined", "safe_hybrid", "weak"],
        default="weak",
        help="How to use teacher outputs during training after refinement completes.",
    )
    parser.add_argument("--safe-hybrid-min-confidence", type=float, default=0.9)
    parser.add_argument("--safe-hybrid-max-absolute-shift", type=int, default=8)
    parser.add_argument("--safe-hybrid-max-note-repair-shift", type=int, default=16)
    parser.add_argument("--safe-hybrid-disable-note-anchored-repair", action="store_true")
    parser.add_argument("--model-name", default="FacebookAI/xlm-roberta-base")
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--eval-batch-size", type=int, default=2)
    parser.add_argument("--max-length", type=int, default=256)
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--freeze-encoder-epochs", type=int, default=1)
    parser.add_argument("--unfreeze-last-n-layers", type=int, default=4)
    parser.add_argument("--learning-rate", type=float, default=2e-5)
    parser.add_argument("--classifier-learning-rate", type=float, default=1e-4)
    parser.add_argument("--gradient-accumulation-steps", type=int, default=4)
    parser.add_argument("--loss-type", choices=["cross_entropy", "focal", "adaptive_focal"], default="cross_entropy")
    parser.add_argument("--positive-class-weight", type=float, default=4.0)
    parser.add_argument("--focal-gamma", type=float, default=2.0)
    parser.add_argument("--decode-strategy", choices=["argmax", "single_best", "topk_span"], default="argmax")
    parser.add_argument("--single-best-min-margin", type=float, default=0.0)
    parser.add_argument("--topk-span-positive-ratio", type=float, default=0.0)
    parser.add_argument("--topk-span-min-tokens", type=int, default=1)
    parser.add_argument("--topk-span-max-tokens", type=int, default=0)
    parser.add_argument("--topk-span-neighbor-margin", type=float, default=-1.5)
    parser.add_argument("--topk-span-max-neighbors", type=int, default=2)
    parser.add_argument("--topk-span-cue-bonus", type=float, default=0.0)
    parser.add_argument("--dialect-adapter-enabled", action="store_true")
    parser.add_argument("--dialect-adapter-dim", type=int, default=32)
    parser.add_argument("--dialect-adapter-scale", type=float, default=0.25)
    parser.add_argument("--contrast-gate-enabled", action="store_true")
    parser.add_argument("--contrast-gate-dim", type=int, default=64)
    parser.add_argument("--contrast-gate-scale", type=float, default=0.25)
    parser.add_argument("--cue-adapter-enabled", action="store_true")
    parser.add_argument("--cue-adapter-dim", type=int, default=16)
    parser.add_argument("--cue-adapter-scale", type=float, default=0.25)
    parser.add_argument("--span-aware-enabled", action="store_true")
    parser.add_argument("--span-aware-radius", type=int, default=2)
    parser.add_argument("--span-aware-decay", type=float, default=0.5)
    parser.add_argument("--span-aware-loss-weight", type=float, default=0.25)
    parser.add_argument("--cue-span-bias-enabled", action="store_true")
    parser.add_argument("--cue-span-bias-strength", type=float, default=0.75)
    parser.add_argument("--gcacu-language-enabled", action="store_true")
    parser.add_argument("--gcacu-language-dim", type=int, default=128)
    parser.add_argument("--gcacu-language-scale", type=float, default=0.5)
    parser.add_argument("--gcacu-incongruity-window", type=int, default=7)
    parser.add_argument("--gcacu-contrast-threshold", type=float, default=0.3)
    parser.add_argument("--uncertainty-aware-upl", action="store_true")
    parser.add_argument("--upl-confidence-threshold", type=float, default=0.7)
    parser.add_argument("--upl-uncertainty-weight", type=float, default=0.5)
    parser.add_argument(
        "--prune-best-model-weights",
        action="store_true",
        help="Delete trainer checkpoint weight files after evaluation to save disk space.",
    )
    parser.add_argument("--device", default=None)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def run_command(command: List[str], dry_run: bool) -> None:
    print("$ " + " ".join(shlex.quote(part) for part in command))
    if dry_run:
        return
    completed = subprocess.run(command, cwd=PROJECT_ROOT)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def main() -> None:
    args = parse_args()
    dataset_dir = args.dataset_dir
    refined_train = dataset_dir / "train_refined.jsonl"
    safe_hybrid_train = dataset_dir / "train_refined_safe_hybrid.jsonl"
    weak_train = dataset_dir / "train.jsonl"
    valid_file = dataset_dir / "valid.jsonl"
    test_file = dataset_dir / "test.jsonl"
    audit_file = dataset_dir / "train_refined_audit.jsonl"
    safe_hybrid_summary = dataset_dir / "train_refined_safe_hybrid_summary.json"

    if not args.skip_convert:
        run_command(
            [
                sys.executable,
                str(PROJECT_ROOT / "training" / "convert_standup_raw_to_word_level.py"),
                "--raw-dir",
                str(args.raw_dir),
                "--output-dir",
                str(dataset_dir),
                "--split-strategy",
                str(args.split_strategy),
                "--context-token-policy",
                str(args.context_token_policy),
                "--context-tail-tokens",
                str(args.context_tail_tokens),
            ],
            dry_run=args.dry_run,
        )

    train_file = weak_train
    if not args.skip_refine:
        run_command(
            [
                sys.executable,
                str(PROJECT_ROOT / "training" / "refine_weak_labels_nemotron.py"),
                "--input-file",
                str(weak_train),
                "--output-file",
                str(refined_train),
                "--audit-file",
                str(audit_file),
                "--backend",
                args.backend,
                "--endpoint",
                args.endpoint,
                "--model",
                args.teacher_model,
                "--min-confidence",
                str(args.teacher_min_confidence),
                "--write-every",
                str(args.teacher_write_every),
                "--progress-every",
                str(args.teacher_progress_every),
                *(["--resume"] if args.teacher_resume else []),
                *(
                    ["--max-examples", str(args.teacher_max_examples)]
                    if args.teacher_max_examples is not None
                    else []
                ),
            ],
            dry_run=args.dry_run,
        )
        if args.refined_train_policy == "refined":
            train_file = refined_train
        elif args.refined_train_policy == "safe_hybrid":
            run_command(
                [
                    sys.executable,
                    str(PROJECT_ROOT / "training" / "build_safe_hybrid_dataset.py"),
                    "--weak-file",
                    str(weak_train),
                    "--refined-file",
                    str(refined_train),
                    "--audit-file",
                    str(audit_file),
                    "--output-file",
                    str(safe_hybrid_train),
                    "--summary-file",
                    str(safe_hybrid_summary),
                    "--min-confidence",
                    str(args.safe_hybrid_min_confidence),
                    "--max-absolute-shift",
                    str(args.safe_hybrid_max_absolute_shift),
                    "--max-note-repair-shift",
                    str(args.safe_hybrid_max_note_repair_shift),
                    *(["--disable-note-anchored-repair"] if args.safe_hybrid_disable_note_anchored_repair else []),
                ],
                dry_run=args.dry_run,
            )
            train_file = safe_hybrid_train
        else:
            train_file = weak_train
    elif args.refined_train_policy == "safe_hybrid":
        run_command(
            [
                sys.executable,
                str(PROJECT_ROOT / "training" / "build_safe_hybrid_dataset.py"),
                "--weak-file",
                str(weak_train),
                "--refined-file",
                str(refined_train),
                "--audit-file",
                str(audit_file),
                "--output-file",
                str(safe_hybrid_train),
                "--summary-file",
                str(safe_hybrid_summary),
                "--min-confidence",
                str(args.safe_hybrid_min_confidence),
                "--max-absolute-shift",
                str(args.safe_hybrid_max_absolute_shift),
                "--max-note-repair-shift",
                str(args.safe_hybrid_max_note_repair_shift),
                *(["--disable-note-anchored-repair"] if args.safe_hybrid_disable_note_anchored_repair else []),
            ],
            dry_run=args.dry_run,
        )
        train_file = safe_hybrid_train

    run_command(
        [
            sys.executable,
            str(PROJECT_ROOT / "training" / "xlmr_standup_word_level.py"),
            "--train-file",
            str(train_file),
            "--valid-file",
            str(valid_file),
            "--test-file",
            str(test_file),
            "--output-dir",
            str(args.output_dir),
            "--model-name",
            args.model_name,
            "--batch-size",
            str(args.batch_size),
            "--eval-batch-size",
            str(args.eval_batch_size),
            "--max-length",
            str(args.max_length),
            "--epochs",
            str(args.epochs),
            "--freeze-encoder-epochs",
            str(args.freeze_encoder_epochs),
            "--unfreeze-last-n-layers",
            str(args.unfreeze_last_n_layers),
            "--learning-rate",
            str(args.learning_rate),
            "--classifier-learning-rate",
            str(args.classifier_learning_rate),
            "--gradient-accumulation-steps",
            str(args.gradient_accumulation_steps),
            "--loss-type",
            str(args.loss_type),
            "--positive-class-weight",
            str(args.positive_class_weight),
            "--focal-gamma",
            str(args.focal_gamma),
            "--decode-strategy",
            str(args.decode_strategy),
            "--single-best-min-margin",
            str(args.single_best_min_margin),
            "--topk-span-positive-ratio",
            str(args.topk_span_positive_ratio),
            "--topk-span-min-tokens",
            str(args.topk_span_min_tokens),
            "--topk-span-max-tokens",
            str(args.topk_span_max_tokens),
            "--topk-span-neighbor-margin",
            str(args.topk_span_neighbor_margin),
            "--topk-span-max-neighbors",
            str(args.topk_span_max_neighbors),
            "--topk-span-cue-bonus",
            str(args.topk_span_cue_bonus),
            *(["--dialect-adapter-enabled"] if args.dialect_adapter_enabled else []),
            "--dialect-adapter-dim",
            str(args.dialect_adapter_dim),
            "--dialect-adapter-scale",
            str(args.dialect_adapter_scale),
            *(["--contrast-gate-enabled"] if args.contrast_gate_enabled else []),
            "--contrast-gate-dim",
            str(args.contrast_gate_dim),
            "--contrast-gate-scale",
            str(args.contrast_gate_scale),
            *(["--cue-adapter-enabled"] if args.cue_adapter_enabled else []),
            "--cue-adapter-dim",
            str(args.cue_adapter_dim),
            "--cue-adapter-scale",
            str(args.cue_adapter_scale),
            *(["--span-aware-enabled"] if args.span_aware_enabled else []),
            "--span-aware-radius",
            str(args.span_aware_radius),
            "--span-aware-decay",
            str(args.span_aware_decay),
            "--span-aware-loss-weight",
            str(args.span_aware_loss_weight),
            *(["--cue-span-bias-enabled"] if args.cue_span_bias_enabled else []),
            "--cue-span-bias-strength",
            str(args.cue_span_bias_strength),
            *(["--gcacu-language-enabled"] if args.gcacu_language_enabled else []),
            "--gcacu-language-dim",
            str(args.gcacu_language_dim),
            "--gcacu-language-scale",
            str(args.gcacu_language_scale),
            "--gcacu-incongruity-window",
            str(args.gcacu_incongruity_window),
            "--gcacu-contrast-threshold",
            str(args.gcacu_contrast_threshold),
            *(["--uncertainty-aware-upl"] if args.uncertainty_aware_upl else []),
            "--upl-confidence-threshold",
            str(args.upl_confidence_threshold),
            "--upl-uncertainty-weight",
            str(args.upl_uncertainty_weight),
            *(["--prune-best-model-weights"] if args.prune_best_model_weights else []),
            *(["--device", args.device] if args.device else []),
        ],
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
