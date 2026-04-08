#!/usr/bin/env python3
"""
Ensemble evaluation script for XLM-R laughter prediction models.

Loads multiple trained models, averages their predictions, and compares
ensemble performance against individual models.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import torch
from torch import nn
from torch.utils.data import DataLoader

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from training.xlmr_standup_word_level import (
    XLMRStandupConfig,
    StandupWordLevelDataset,
    build_dataloader,
    choose_device,
    evaluate_model,
    load_jsonl_examples,
    load_saved_model,
)


# Available models for ensemble
MODEL_CONFIGS = {
    "xlmr_augmented": {
        "model_dir": "experiments/xlmr_augmented/best_model",
        "summary_file": "experiments/xlmr_augmented/training_summary.json",
    },
    "xlmr_multilingual_balanced": {
        "model_dir": "experiments/xlmr_multilingual_balanced/best_model",
        "summary_file": "experiments/xlmr_multilingual_balanced/training_summary.json",
    },
}

# Note: xlmr_large_22k has no trained model (training timed out on CPU)
UNAVAILABLE_MODELS = ["xlmr_large_22k"]


def load_model_config(summary_file: Path) -> XLMRStandupConfig:
    """Load model configuration from training summary."""
    payload = json.loads(summary_file.read_text(encoding="utf-8"))
    config_dict = dict(payload["config"])
    return XLMRStandupConfig(**config_dict)


def forward_with_logits(
    model: nn.Module,
    batch: Dict[str, Any],
    device: torch.device,
) -> torch.Tensor:
    """Get raw logits from model for a batch."""
    model.eval()
    with torch.no_grad():
        from training.xlmr_standup_word_level import forward_model, is_dialect_adapter_model, is_cue_adapter_model

        outputs = forward_model(
            model=model,
            input_ids=batch["input_ids"].to(device),
            attention_mask=batch["attention_mask"].to(device),
            dialect_bucket_ids=batch["dialect_bucket_ids"].to(device) if is_dialect_adapter_model(model) else None,
            cue_bucket_ids=batch["cue_bucket_ids"].to(device) if is_cue_adapter_model(model) else None,
        )
    return outputs.logits


def get_model_predictions(
    model: nn.Module,
    dataloader: DataLoader,
    device: torch.device,
) -> Tuple[List[torch.Tensor], List[torch.Tensor]]:
    """
    Get softmax predictions from a model for all batches.
    Returns tuple of (all_logits, all_predictions).
    """
    model.eval()
    all_logits = []
    all_predictions = []

    with torch.no_grad():
        for batch in dataloader:
            logits = forward_with_logits(model, batch, device)
            # Apply softmax to get probabilities
            probs = torch.softmax(logits, dim=-1)
            # Get predictions (argmax over labels)
            preds = torch.argmax(probs, dim=-1)

            all_logits.append(probs.cpu())
            all_predictions.append(preds.cpu())

    return all_logits, all_predictions


def ensemble_predictions(
    model_predictions: List[List[torch.Tensor]],
) -> List[torch.Tensor]:
    """
    Average predictions from multiple models.
    model_predictions: list of lists of tensors, each inner list contains predictions from one model
    """
    num_models = len(model_predictions)
    ensemble_probs = []

    # For each batch position
    num_batches = len(model_predictions[0])
    for batch_idx in range(num_batches):
        # Stack predictions from all models for this batch
        stacked = torch.stack([model_predictions[m][batch_idx] for m in range(num_models)], dim=0)
        # Average across models
        avg_probs = stacked.mean(dim=0)
        ensemble_probs.append(avg_probs)

    return ensemble_probs


def decode_ensemble_predictions(
    ensemble_probs: List[torch.Tensor],
    dataloader: DataLoader,
    decode_strategy: str = "argmax",
) -> torch.Tensor:
    """Decode ensemble probabilities to binary predictions."""
    decoded_preds = []

    for batch_idx, probs in enumerate(ensemble_probs):
        # Get binary predictions (label 1 if prob > 0.5)
        preds = (probs[:, 1] > 0.5).long()
        decoded_preds.append(preds)

    return torch.cat(decoded_preds, dim=0)


def evaluate_single_model(
    model: nn.Module,
    dataloader: DataLoader,
    device: torch.device,
    config: XLMRStandupConfig,
) -> Dict[str, Any]:
    """Evaluate a single model using the standard evaluation function."""
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


def main() -> None:
    print("=" * 70)
    print("ENSEMBLE EVALUATION FOR XLM-R LAUGHTER PREDICTION")
    print("=" * 70)

    # Check available models
    available_models = {}
    for model_name, model_config in MODEL_CONFIGS.items():
        model_dir = PROJECT_ROOT / model_config["model_dir"]
        if model_dir.exists() and (model_dir / "model.safetensors").exists():
            available_models[model_name] = model_config
        else:
            print(f"WARNING: Model not found: {model_name} at {model_dir}")

    print(f"\nAvailable models for ensemble: {list(available_models.keys())}")
    print(f"Unavailable models: {UNAVAILABLE_MODELS}")

    if len(available_models) < 2:
        print("\nERROR: Need at least 2 models for ensemble evaluation.")
        print("Only found:", list(available_models.keys()))
        sys.exit(1)

    # Determine device
    device = choose_device(None)
    print(f"\nUsing device: {device}")

    # Load data - use the standard standup_word_level data
    data_dir = PROJECT_ROOT / "data" / "training" / "standup_word_level"
    valid_file = data_dir / "valid.jsonl"
    test_file = data_dir / "test.jsonl"

    if not valid_file.exists():
        print(f"\nERROR: Validation file not found: {valid_file}")
        sys.exit(1)

    print(f"\nLoading data from {data_dir}")
    valid_examples = load_jsonl_examples(valid_file)
    print(f"Validation examples: {len(valid_examples)}")

    test_examples = []
    if test_file.exists():
        test_examples = load_jsonl_examples(test_file)
        print(f"Test examples: {len(test_examples)}")

    # Load first model's config and tokenizer (all models use same base config)
    first_model_name = list(available_models.keys())[0]
    first_config = load_model_config(PROJECT_ROOT / available_models[first_model_name]["summary_file"])
    first_model_dir = PROJECT_ROOT / available_models[first_model_name]["model_dir"]

    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(first_model_dir, use_fast=True, local_files_only=True)

    # Build dataloaders
    valid_loader = build_dataloader(
        valid_examples,
        tokenizer=tokenizer,
        batch_size=first_config.eval_batch_size,
        max_length=first_config.max_length,
        shuffle=False,
    )

    test_loader = None
    if test_examples:
        test_loader = build_dataloader(
            test_examples,
            tokenizer=tokenizer,
            batch_size=first_config.eval_batch_size,
            max_length=first_config.max_length,
            shuffle=False,
        )

    # Load all models
    print("\n" + "=" * 70)
    print("LOADING MODELS")
    print("=" * 70)

    models = {}
    configs = {}
    for model_name, model_config in available_models.items():
        print(f"\nLoading {model_name}...")
        model_dir = PROJECT_ROOT / model_config["model_dir"]
        summary_file = PROJECT_ROOT / model_config["summary_file"]

        config = load_model_config(summary_file)
        model = load_saved_model(model_dir, device=device, fallback_config=config)
        model.to(device)

        models[model_name] = model
        configs[model_name] = config

        print(f"  Model loaded: {model_name}")

    # Evaluate each model individually
    print("\n" + "=" * 70)
    print("SINGLE MODEL EVALUATION")
    print("=" * 70)

    single_model_results = {}
    for model_name, model in models.items():
        print(f"\nEvaluating {model_name} on validation set...")
        config = configs[model_name]
        metrics = evaluate_single_model(model, valid_loader, device, config)
        single_model_results[model_name] = metrics

        print(f"  Val F1: {metrics['f1']:.4f}")
        print(f"  Val IoU F1: {metrics['iou_f1']:.4f}")
        print(f"  Val Precision: {metrics['precision']:.4f}")
        print(f"  Val Recall: {metrics['recall']:.4f}")

    # Evaluate ensemble on validation set
    print("\n" + "=" * 70)
    print("ENSEMBLE EVALUATION (Validation Set)")
    print("=" * 70)

    # Get predictions from all models
    model_probs = {}
    for model_name, model in models.items():
        print(f"\nGetting predictions from {model_name}...")
        probs, _ = get_model_predictions(model, valid_loader, device)
        model_probs[model_name] = probs

    # Create ensemble by averaging probabilities
    model_prob_list = [model_probs[name] for name in models.keys()]
    ensemble_probs = ensemble_predictions(model_prob_list)

    # Decode ensemble predictions
    ensemble_preds = decode_ensemble_predictions(ensemble_probs, valid_loader)

    # Get all labels for validation
    all_labels = []
    for batch in valid_loader:
        all_labels.append(batch["labels"])

    all_labels_flat = torch.cat([l.flatten() for l in all_labels], dim=0)

    # Calculate ensemble metrics manually
    from training.xlmr_standup_word_level import (
        compute_binary_metrics,
        extract_binary_sequences,
        compute_interval_f1,
        extract_intervals,
    )

    ensemble_pred_list = ensemble_preds.flatten().tolist()
    ensemble_label_list = all_labels_flat.tolist()

    ensemble_metrics = compute_binary_metrics(ensemble_pred_list, ensemble_label_list)
    ensemble_interval_f1 = compute_interval_f1(
        extract_intervals(ensemble_pred_list),
        extract_intervals(ensemble_label_list),
        threshold=0.2,
    )

    print(f"\nEnsemble (averaged probabilities) Results:")
    print(f"  Val F1: {ensemble_metrics['f1']:.4f}")
    print(f"  Val IoU F1: {ensemble_interval_f1:.4f}")
    print(f"  Val Precision: {ensemble_metrics['precision']:.4f}")
    print(f"  Val Recall: {ensemble_metrics['recall']:.4f}")

    # Compare single models vs ensemble
    print("\n" + "=" * 70)
    print("COMPARISON: SINGLE MODELS vs ENSEMBLE")
    print("=" * 70)

    print(f"\n{'Model':<30} {'Val F1':>10} {'Val IoU F1':>12} {'Val Prec':>10} {'Val Rec':>10}")
    print("-" * 75)

    for model_name, metrics in single_model_results.items():
        print(f"{model_name:<30} {metrics['f1']:>10.4f} {metrics['iou_f1']:>12.4f} {metrics['precision']:>10.4f} {metrics['recall']:>10.4f}")

    print("-" * 75)
    print(f"{'ENSEMBLE (avg probs)':<30} {ensemble_metrics['f1']:>10.4f} {ensemble_interval_f1:>12.4f} {ensemble_metrics['precision']:>10.4f} {ensemble_metrics['recall']:>10.4f}")

    # Calculate improvement
    best_single_f1 = max(m['f1'] for m in single_model_results.values())
    ensemble_f1 = ensemble_metrics['f1']
    improvement = ensemble_f1 - best_single_f1

    print("\n" + "=" * 70)
    print("ANALYSIS")
    print("=" * 70)
    print(f"Best single model F1: {best_single_f1:.4f}")
    print(f"Ensemble F1: {ensemble_f1:.4f}")
    print(f"Ensemble improvement: {improvement:+.4f} ({improvement/best_single_f1*100:+.2f}%)")

    # If test set is available, evaluate there too
    if test_loader:
        print("\n" + "=" * 70)
        print("TEST SET EVALUATION")
        print("=" * 70)

        # Get test predictions
        test_model_probs = {}
        for model_name, model in models.items():
            print(f"\nGetting predictions from {model_name}...")
            probs, _ = get_model_predictions(model, test_loader, device)
            test_model_probs[model_name] = probs

        # Create ensemble
        test_model_prob_list = [test_model_probs[name] for name in models.keys()]
        test_ensemble_probs = ensemble_predictions(test_model_prob_list)
        test_ensemble_preds = decode_ensemble_predictions(test_ensemble_probs, test_loader)

        # Get test labels
        test_all_labels = []
        for batch in test_loader:
            test_all_labels.append(batch["labels"])
        test_all_labels_flat = torch.cat([l.flatten() for l in test_all_labels], dim=0)

        # Calculate test metrics
        test_pred_list = test_ensemble_preds.flatten().tolist()
        test_label_list = test_all_labels_flat.tolist()

        test_ensemble_metrics = compute_binary_metrics(test_pred_list, test_label_list)
        test_ensemble_interval_f1 = compute_interval_f1(
            extract_intervals(test_pred_list),
            extract_intervals(test_label_list),
            threshold=0.2,
        )

        print(f"\nEnsemble Test Results:")
        print(f"  Test F1: {test_ensemble_metrics['f1']:.4f}")
        print(f"  Test IoU F1: {test_ensemble_interval_f1:.4f}")
        print(f"  Test Precision: {test_ensemble_metrics['precision']:.4f}")
        print(f"  Test Recall: {test_ensemble_metrics['recall']:.4f}")

        # Compare with individual model test results from training summaries
        print("\nTest Results from Training Summaries:")
        for model_name, model_config in available_models.items():
            summary = json.loads((PROJECT_ROOT / model_config["summary_file"]).read_text())
            if "test_metrics" in summary:
                tm = summary["test_metrics"]
                print(f"  {model_name}: F1={tm['f1']:.4f}, IoU F1={tm['iou_f1']:.4f}")

    # Save results
    results = {
        "available_models": list(available_models.keys()),
        "unavailable_models": UNAVAILABLE_MODELS,
        "single_model_results": {
            name: {
                "f1": m["f1"],
                "iou_f1": m["iou_f1"],
                "precision": m["precision"],
                "recall": m["recall"],
            }
            for name, m in single_model_results.items()
        },
        "ensemble_results": {
            "validation": {
                "f1": ensemble_metrics["f1"],
                "iou_f1": ensemble_interval_f1,
                "precision": ensemble_metrics["precision"],
                "recall": ensemble_metrics["recall"],
            }
        },
        "best_single_model_f1": best_single_f1,
        "ensemble_improvement": improvement,
        "ensemble_improvement_percent": (improvement / best_single_f1 * 100) if best_single_f1 > 0 else 0,
    }

    output_file = PROJECT_ROOT / "ensemble_results.json"
    output_file.write_text(json.dumps(results, indent=2))
    print(f"\nResults saved to: {output_file}")

    print("\n" + "=" * 70)
    print("ENSEMBLE EVALUATION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()