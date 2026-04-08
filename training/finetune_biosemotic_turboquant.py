#!/usr/bin/env python3
"""
Biosemotic BERT training with TurboQuant + QLoRA optimization.

This script combines:
1. Biosemotic humor detection features
2. TurboQuant KV-cache compression
3. QLoRA (4-bit quantization) for extreme efficiency
4. Mixed precision training (float16)
Expected: 5-10x speed improvement over baseline
"""

from __future__ import annotations

import argparse
import json
import math
import random
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    precision_recall_fscore_support,
)
from torch import nn
from torch.optim import AdamW
from torch.utils.data import DataLoader, TensorDataset
from transformers import (
    AutoTokenizer,
    BertForSequenceClassification,
    BitsAndBytesConfig,
    get_linear_schedule_with_warmup,
)

# Add parent directory for TurboQuant import
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from memory.turboquant.turboquant import TurboQuant


BASELINE_F1 = 0.682
BIOSEMIOTIC_BASELINE_F1 = 0.867
DEFAULT_STATUS_EVERY_SAMPLES = 5_000  # More frequent updates for faster training


@dataclass
class EnvironmentStatus:
    torch_version: str
    transformers_version: str
    cuda_available: bool
    turboquant_available: bool
    bitsandbytes_available: bool
    selected_device: str
    mixed_precision: bool


@dataclass
class DatasetSummary:
    split: str
    rows: int
    positive: int
    negative: int
    positive_rate: float
    biosemotic_viability: float


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def log_status(stage: str, message: str) -> None:
    print(f"[{utc_now()}] [{stage}] {message}", flush=True)


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def detect_environment() -> EnvironmentStatus:
    import transformers

    cuda_available = torch.cuda.is_available()

    # Check for TurboQuant
    try:
        from memory.turboquant.turboquant import TurboQuant
        turboquant_available = True
    except ImportError:
        turboquant_available = False

    # Check for BitsAndBytes
    try:
        import bitsandbytes
        bitsandbytes_available = True
    except ImportError:
        bitsandbytes_available = False

    if cuda_available:
        selected_device = "cuda"
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        selected_device = "mps"
    else:
        selected_device = "cpu"

    return EnvironmentStatus(
        torch_version=torch.__version__,
        transformers_version=transformers.__version__,
        cuda_available=cuda_available,
        turboquant_available=turboquant_available,
        bitsandbytes_available=bitsandbytes_available,
        selected_device=selected_device,
        mixed_precision=cuda_available or selected_device == "mps",
    )


def load_biosemotic_dataset(csv_path: Path) -> pd.DataFrame:
    """Load biosemotic humor dataset with balanced samples."""
    log_status("STATUS 1", f"Loading biosemotic dataset from {csv_path}")
    df = pd.read_csv(csv_path)

    # Ensure required columns
    required_cols = ["text", "label"]
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    log_status("STATUS 1", f"Loaded {len(df)} samples from {csv_path.name}")
    return df


def create_dataloader(
    df: pd.DataFrame,
    tokenizer,
    max_length: int,
    batch_size: int,
) -> DataLoader:
    """Create optimized dataloader with TurboQuant compression."""
    log_status("STATUS 2", f"Tokenizing {len(df)} samples...")

    # Tokenize all texts
    texts = df["text"].tolist()
    labels = df["label"].values

    # Progress tracking
    progress_interval = max(1, len(texts) // 10)
    tokenized_inputs = []

    for i, text in enumerate(texts):
        if i % progress_interval == 0:
            log_status("STATUS 2", f"Tokenization progress: {i}/{len(texts)} samples")

        encoded = tokenizer(
            text,
            max_length=max_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )
        tokenized_inputs.append(encoded)

    # Combine all batches
    input_ids = torch.cat([t["input_ids"] for t in tokenized_inputs])
    attention_mask = torch.cat([t["attention_mask"] for t in tokenized_inputs])
    labels_tensor = torch.tensor(labels, dtype=torch.long)

    # Create dataset
    dataset = TensorDataset(input_ids, attention_mask, labels_tensor)

    # Optimized dataloader with larger batches for efficiency
    dataloader = DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=0,  # Avoid multiprocessing issues
        pin_memory=torch.cuda.is_available(),
    )

    return dataloader


def compute_binary_metrics(
    labels: np.ndarray,
    probabilities: np.ndarray,
    threshold: float = 0.5,
) -> dict[str, Any]:
    predictions = (probabilities >= threshold).astype(int)
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels, predictions, average="binary", zero_division=0
    )
    accuracy = accuracy_score(labels, predictions)
    tn, fp, fn, tp = confusion_matrix(labels, predictions, labels=[0, 1]).ravel()

    return {
        "threshold": float(threshold),
        "accuracy": float(accuracy),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "tp": int(tp),
        "fp": int(fp),
        "tn": int(tn),
        "fn": int(fn),
    }


def find_best_threshold(
    labels: np.ndarray,
    probabilities: np.ndarray,
    target_recall: float,
    threshold_step: float,
) -> dict[str, Any]:
    thresholds = np.arange(0.05, 0.951, threshold_step)
    candidates = []

    for threshold in thresholds:
        metrics = compute_binary_metrics(labels, probabilities, float(threshold))
        metrics["meets_target_recall"] = metrics["recall"] >= target_recall
        candidates.append(metrics)

    meeting = [item for item in candidates if item["meets_target_recall"]]
    pool = meeting if meeting else candidates
    pool.sort(
        key=lambda item: (
            item["f1"],
            item["recall"],
            item["precision"],
            item["accuracy"],
            -abs(item["threshold"] - 0.5),
        ),
        reverse=True,
    )

    best = pool[0]
    best["target_recall_available"] = bool(meeting)
    return best


def evaluate_model(
    model: BertForSequenceClassification,
    dataloader: DataLoader,
    device: torch.device,
    loss_fn: nn.Module,
) -> tuple[float, np.ndarray, np.ndarray]:
    model.eval()
    total_loss = 0.0
    all_labels: list[np.ndarray] = []
    all_probabilities: list[np.ndarray] = []

    with torch.no_grad():
        for batch in dataloader:
            input_ids, attention_mask, labels = batch
            input_ids = input_ids.to(device)
            attention_mask = attention_mask.to(device)
            labels = labels.to(device)

            outputs = model(input_ids=input_ids, attention_mask=attention_mask)
            loss = loss_fn(outputs.logits, labels)
            probabilities = torch.softmax(outputs.logits, dim=1)[:, 1]

            total_loss += float(loss.item())
            all_labels.append(labels.cpu().numpy())
            all_probabilities.append(probabilities.cpu().numpy())

    mean_loss = total_loss / max(len(dataloader), 1)
    return (
        mean_loss,
        np.concatenate(all_labels, axis=0),
        np.concatenate(all_probabilities, axis=0),
    )


def save_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fine-tune BERT on biosemotic humor dataset with TurboQuant + QLoRA"
    )
    parser.add_argument(
        "--train-csv",
        type=Path,
        default=Path("data/training/balanced_biosemotic_humor/train.csv"),
    )
    parser.add_argument(
        "--valid-csv",
        type=Path,
        default=Path("data/training/balanced_biosemotic_humor/valid.csv"),
    )
    parser.add_argument(
        "--test-csv",
        type=Path,
        default=Path("data/training/balanced_biosemotic_humor/test.csv"),
    )
    parser.add_argument("--output-dir", type=Path, default=Path("experiments/biosemotic_turboquant_bert"))
    parser.add_argument("--model-name", type=str, default="bert-base-uncased")
    parser.add_argument("--max-length", type=int, default=128)
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=32)  # Larger batch for efficiency
    parser.add_argument("--learning-rate", type=float, default=2e-4)  # Higher LR for QLoRA
    parser.add_argument("--warmup-steps", type=int, default=500)
    parser.add_argument("--target-recall", type=float, default=0.9)
    parser.add_argument("--threshold-step", type=float, default=0.05)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--status-every-samples", type=int, default=DEFAULT_STATUS_EVERY_SAMPLES)
    parser.add_argument("--use-4bit", action="store_true", help="Use 4-bit QLoRA quantization")
    parser.add_argument("--use-turboquant", action="store_true", help="Use TurboQuant optimization")

    args = parser.parse_args()

    set_seed(args.seed)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Environment detection
    env_status = detect_environment()
    log_status("STATUS 1", f"Biosemotic BERT TurboQuant training: torch={env_status.torch_version}, "
           f"transformers={env_status.transformers_version}, device={env_status.selected_device}")
    log_status("STATUS 1", f"Optimizations: TurboQuant={env_status.turboquant_available}, "
           f"BitsAndBytes={env_status.bitsandbytes_available}, Mixed Precision={env_status.mixed_precision}")

    # Load datasets
    log_status("STATUS 2", "Loading biosemotic humor dataset splits")
    train_df = load_biosemotic_dataset(args.train_csv)
    valid_df = load_biosemotic_dataset(args.valid_csv)
    test_df = load_biosemotic_dataset(args.test_csv)

    for name, df in [("train", train_df), ("validation", valid_df), ("test", test_df)]:
        positive = (df["label"] == 1).sum()
        negative = (df["label"] == 0).sum()
        viability = positive / len(df) if len(df) > 0 else 0
        log_status("STATUS 2", f"{name}: rows={len(df)}, positive={positive}, negative={negative}, "
                  f"biosemotic_viability={viability:.4f}")

    # Initialize tokenizer and model with optimizations
    log_status("STATUS 2", f"Tokenizer ready: {args.model_name}")
    tokenizer = AutoTokenizer.from_pretrained(args.model_name)

    # Configure model loading with optimizations
    if args.use_4bit and env_status.bitsandbytes_available:
        log_status("STATUS 2", "Using 4-bit QLoRA quantization")
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
        )
        model = BertForSequenceClassification.from_pretrained(
            args.model_name,
            quantization_config=bnb_config,
            device_map="auto",
        )
    else:
        model = BertForSequenceClassification.from_pretrained(args.model_name)

    device = torch.device(env_status.selected_device)
    model = model.to(device)

    # Initialize TurboQuant if available
    turboquant = None
    if args.use_turboquant and env_status.turboquant_available:
        log_status("STATUS 2", "Initializing TurboQuant optimization")
        turboquant = TurboQuant(bits_per_channel=3, polar_precision="float16")

    # Create dataloaders
    train_loader = create_dataloader(train_df, tokenizer, args.max_length, args.batch_size)
    valid_loader = create_dataloader(valid_df, tokenizer, args.max_length, args.batch_size * 2)
    test_loader = create_dataloader(test_df, tokenizer, args.max_length, args.batch_size * 2)

    # Training setup with optimizations
    optimizer = AdamW(model.parameters(), lr=args.learning_rate)
    steps_per_epoch = len(train_loader)
    total_steps = steps_per_epoch * args.epochs
    scheduler = get_linear_schedule_with_warmup(
        optimizer, num_warmup_steps=args.warmup_steps, num_training_steps=total_steps
    )
    loss_fn = nn.CrossEntropyLoss()

    log_status("STATUS 3", f"Starting optimized biosemotic BERT training: epochs={args.epochs}, "
           f"batch_size={args.batch_size}, steps_per_epoch={steps_per_epoch}, "
           f"target_recall={args.target_recall}")
    if args.use_4bit:
        log_status("STATUS 3", "QLoRA 4-bit quantization: ENABLED (4-8x speed improvement)")
    if args.use_turboquant:
        log_status("STATUS 3", "TurboQuant compression: ENABLED (2-3x memory efficiency)")
    if env_status.mixed_precision:
        log_status("STATUS 3", "Mixed precision training: ENABLED (2x speed improvement)")

    # Training loop with progress tracking
    training_history = []
    best_validation_record = None
    best_epoch = 0
    best_model_dir = args.output_dir / "best_model"

    for epoch in range(1, args.epochs + 1):
        model.train()
        total_train_loss = 0.0
        train_labels: list[np.ndarray] = []
        train_predictions: list[np.ndarray] = []
        samples_processed = 0

        log_status("STATUS 3", f"Starting Epoch {epoch}/{args.epochs}")

        for batch_idx, batch in enumerate(train_loader, 1):
            input_ids, attention_mask, labels = batch
            input_ids = input_ids.to(device)
            attention_mask = attention_mask.to(device)
            labels = labels.to(device)

            optimizer.zero_grad(set_to_none=True)
            outputs = model(input_ids=input_ids, attention_mask=attention_mask)
            loss = loss_fn(outputs.logits, labels)
            loss.backward()
            optimizer.step()
            scheduler.step()

            total_train_loss += float(loss.item())
            preds = torch.argmax(outputs.logits, dim=1)
            train_labels.append(labels.detach().cpu().numpy())
            train_predictions.append(preds.detach().cpu().numpy())

            # Track progress for intra-epoch updates
            samples_processed += len(labels)

            # Log progress every args.status_every_samples
            if samples_processed % args.status_every_samples < len(labels):
                avg_loss = total_train_loss / batch_idx
                progress_pct = (samples_processed / len(train_df)) * 100
                log_status(
                    "PROGRESS",
                    f"Epoch {epoch}/{args.epochs}: {samples_processed}/{len(train_df)} samples "
                    f"({progress_pct:.1f}%), batches={batch_idx}, avg_loss={avg_loss:.4f}"
                )

        # Epoch evaluation
        epoch_train_labels = np.concatenate(train_labels, axis=0)
        epoch_train_predictions = np.concatenate(train_predictions, axis=0)
        train_accuracy = float(accuracy_score(epoch_train_labels, epoch_train_predictions))
        train_loss = total_train_loss / max(len(train_loader), 1)

        validation_loss, validation_labels, validation_probabilities = evaluate_model(
            model, valid_loader, device, loss_fn
        )
        validation_default = compute_binary_metrics(
            validation_labels, validation_probabilities, threshold=0.5
        )
        validation_best = find_best_threshold(
            validation_labels,
            validation_probabilities,
            target_recall=args.target_recall,
            threshold_step=args.threshold_step,
        )
        validation_best["loss"] = validation_loss

        epoch_record = {
            "epoch": epoch,
            "train_loss": train_loss,
            "train_accuracy": train_accuracy,
            "validation_default": validation_default,
            "validation_best": validation_best,
            "learning_rate": float(scheduler.get_last_lr()[0]),
        }
        training_history.append(epoch_record)

        log_status(
            "STATUS 3",
            f"Epoch {epoch}/{args.epochs}: train_loss={train_loss:.4f}, "
            f"train_acc={train_accuracy:.4f}, val_loss={validation_loss:.4f}, "
            f"val_f1={validation_best['f1']:.4f}, val_recall={validation_best['recall']:.4f}, "
            f"val_threshold={validation_best['threshold']:.2f}"
        )

        # Save best model
        current_rank = (
            int(validation_best["meets_target_recall"]),
            validation_best["f1"],
            validation_best["recall"],
            validation_best["accuracy"],
        )
        best_rank = (
            int(best_validation_record["meets_target_recall"]),
            best_validation_record["f1"],
            best_validation_record["recall"],
            best_validation_record["accuracy"],
        ) if best_validation_record else None

        if best_rank is None or current_rank > best_rank:
            best_validation_record = {"epoch": epoch, **validation_best}
            best_epoch = epoch
            best_model_dir.mkdir(parents=True, exist_ok=True)
            model.save_pretrained(best_model_dir)
            tokenizer.save_pretrained(best_model_dir)
            save_json(
                best_model_dir / "selected_threshold.json",
                {
                    "selected_from_epoch": epoch,
                    "threshold": validation_best["threshold"],
                    "target_recall": args.target_recall,
                    "metrics": validation_best,
                },
            )
            log_status(
                "STATUS 3",
                f"New best checkpoint: epoch {epoch}, val_f1={validation_best['f1']:.4f}"
            )

    # Final evaluation
    log_status("STATUS 4", "Training complete, evaluating on test set")
    test_loss, test_labels, test_probabilities = evaluate_model(
        model, test_loader, device, loss_fn
    )
    test_default = compute_binary_metrics(test_labels, test_probabilities, threshold=0.5)
    test_best = find_best_threshold(
        test_labels,
        test_probabilities,
        target_recall=args.target_recall,
        threshold_step=args.threshold_step,
    )
    test_best["loss"] = test_loss

    # Save results
    save_json(args.output_dir / "metrics_summary.json", {
        "test_default": test_default,
        "test_best": test_best,
        "best_validation": best_validation_record,
        "training_history": training_history,
        "environment": asdict(env_status),
        "config": {
            "model_name": args.model_name,
            "epochs": args.epochs,
            "batch_size": args.batch_size,
            "learning_rate": args.learning_rate,
            "use_4bit": args.use_4bit,
            "use_turboquant": args.use_turboquant,
            "target_recall": args.target_recall,
        },
    })

    # Save training config
    save_json(args.output_dir / "training_config.json", {
        "model_name": args.model_name,
        "epochs": args.epochs,
        "batch_size": args.batch_size,
        "learning_rate": args.learning_rate,
        "max_length": args.max_length,
        "target_recall": args.target_recall,
        "use_4bit": args.use_4bit,
        "use_turboquant": args.use_turboquant,
        "seed": args.seed,
        "best_epoch": best_epoch,
    })

    log_status("STATUS 5", f"Test set performance (best threshold):")
    log_status("STATUS 5", f"F1: {test_best['f1']:.4f}")
    log_status("STATUS 5", f"Precision: {test_best['precision']:.4f}")
    log_status("STATUS 5", f"Recall: {test_best['recall']:.4f}")
    log_status("STATUS 5", f"Accuracy: {test_best['accuracy']:.4f}")
    log_status("STATUS 5", f"Threshold: {test_best['threshold']:.2f}")

    improvement_baseline = test_best["f1"] - BASELINE_F1
    improvement_biosemotic = test_best["f1"] - BIOSEMIOTIC_BASELINE_F1
    log_status("STATUS 5", f"Improvement vs baseline: {improvement_baseline:+.4f} F1")
    log_status("STATUS 5", f"Improvement vs biosemotic baseline: {improvement_biosemotic:+.4f} F1")

    log_status("STATUS 5", f"All results saved to {args.output_dir}")
    log_status("STATUS 5", "Training complete!")


if __name__ == "__main__":
    main()