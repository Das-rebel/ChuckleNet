#!/usr/bin/env python3
"""
Fine-tune bert-base-uncased on the final unified humor dataset.

This script is intentionally explicit about status logging because it is meant
to support long-running training in constrained environments.
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
    get_linear_schedule_with_warmup,
)


BASELINE_F1 = 0.682
DEFAULT_STATUS_EVERY_SAMPLES = 20_000


@dataclass
class EnvironmentStatus:
    torch_version: str
    transformers_version: str
    cuda_available: bool
    cuda_device_count: int
    cuda_devices: list[str]
    mps_available: bool
    selected_device: str


@dataclass
class DatasetSummary:
    split: str
    rows: int
    positive: int
    negative: int
    positive_rate: float
    avg_quality_score: float
    avg_word_count: float
    max_word_count: int


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
    cuda_devices = []
    if cuda_available:
        cuda_devices = [
            torch.cuda.get_device_name(idx) for idx in range(torch.cuda.device_count())
        ]
        selected_device = "cuda"
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        selected_device = "mps"
    else:
        selected_device = "cpu"

    return EnvironmentStatus(
        torch_version=torch.__version__,
        transformers_version=transformers.__version__,
        cuda_available=cuda_available,
        cuda_device_count=torch.cuda.device_count() if cuda_available else 0,
        cuda_devices=cuda_devices,
        mps_available=bool(
            hasattr(torch.backends, "mps") and torch.backends.mps.is_available()
        ),
        selected_device=selected_device,
    )


def load_split(
    csv_path: Path,
    split_name: str,
    max_samples: int | None = None,
    seed: int = 42,
) -> tuple[pd.DataFrame, DatasetSummary]:
    df = pd.read_csv(csv_path)
    if max_samples is not None:
        if max_samples <= 0:
            raise ValueError("max_samples must be positive when provided")
        if max_samples < len(df):
            df = stratified_sample(df, max_samples, seed)

    df["text"] = df["text"].fillna("").astype(str)
    df["label"] = df["label"].astype(int)

    positive = int(df["label"].sum())
    rows = int(len(df))
    summary = DatasetSummary(
        split=split_name,
        rows=rows,
        positive=positive,
        negative=rows - positive,
        positive_rate=float(positive / rows) if rows else 0.0,
        avg_quality_score=float(df["quality_score"].mean()) if rows else 0.0,
        avg_word_count=float(df["word_count"].mean()) if rows else 0.0,
        max_word_count=int(df["word_count"].max()) if rows else 0,
    )
    return df, summary


def stratified_sample(df: pd.DataFrame, max_samples: int, seed: int) -> pd.DataFrame:
    label_counts = df["label"].value_counts().sort_index()
    total_rows = len(df)
    target_counts: dict[int, int] = {}
    remainders: list[tuple[float, int]] = []
    assigned = 0

    for label, count in label_counts.items():
        exact_target = (count / total_rows) * max_samples
        take = int(math.floor(exact_target))
        take = min(max(take, 1), count)
        target_counts[int(label)] = take
        assigned += take
        remainders.append((exact_target - take, int(label)))

    while assigned < max_samples:
        remainders.sort(reverse=True)
        for _, label in remainders:
            if assigned >= max_samples:
                break
            available = int(label_counts[label])
            if target_counts[label] < available:
                target_counts[label] += 1
                assigned += 1

    while assigned > max_samples:
        removable = sorted(
            ((count, label) for label, count in target_counts.items() if count > 1),
            reverse=True,
        )
        if not removable:
            break
        _, label = removable[0]
        target_counts[label] -= 1
        assigned -= 1

    sampled_parts = []
    for label, group in df.groupby("label"):
        sampled_parts.append(
            group.sample(
                n=target_counts[int(label)],
                random_state=seed,
            )
        )

    sampled = (
        pd.concat(sampled_parts, axis=0)
        .sample(frac=1.0, random_state=seed)
        .reset_index(drop=True)
    )
    return sampled


def tokenize_split(
    df: pd.DataFrame,
    tokenizer: AutoTokenizer,
    split_name: str,
    max_length: int,
    status_every: int,
    batch_tokenize_size: int,
) -> TensorDataset:
    total_rows = len(df)
    input_ids_batches: list[torch.Tensor] = []
    attention_mask_batches: list[torch.Tensor] = []
    labels_batches: list[torch.Tensor] = []
    next_log = min(status_every, total_rows) if total_rows else 0
    last_logged = 0

    texts = df["text"].tolist()
    labels = df["label"].tolist()

    for start in range(0, total_rows, batch_tokenize_size):
        end = min(start + batch_tokenize_size, total_rows)
        encodings = tokenizer(
            texts[start:end],
            max_length=max_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )

        input_ids_batches.append(encodings["input_ids"])
        attention_mask_batches.append(encodings["attention_mask"])
        labels_batches.append(torch.tensor(labels[start:end], dtype=torch.long))

        processed = end
        if processed >= next_log:
            log_status(
                "STATUS 2",
                f"{split_name} preprocessing progress: {processed:,}/{total_rows:,} samples tokenized",
            )
            last_logged = processed
            next_log += status_every

    if total_rows and last_logged != total_rows:
        log_status(
            "STATUS 2",
            f"{split_name} preprocessing progress: {total_rows:,}/{total_rows:,} samples tokenized",
        )

    return TensorDataset(
        torch.cat(input_ids_batches, dim=0),
        torch.cat(attention_mask_batches, dim=0),
        torch.cat(labels_batches, dim=0),
    )


def create_dataloader(
    dataset: TensorDataset,
    batch_size: int,
    shuffle: bool,
    device: str,
) -> DataLoader:
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        num_workers=0,
        pin_memory=(device == "cuda"),
    )


def tensor_batch_to_device(batch: tuple[torch.Tensor, ...], device: torch.device) -> tuple[torch.Tensor, ...]:
    return tuple(item.to(device) for item in batch)


def compute_binary_metrics(
    labels: np.ndarray,
    probabilities: np.ndarray,
    threshold: float,
) -> dict[str, Any]:
    predictions = (probabilities >= threshold).astype(int)
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels,
        predictions,
        average="binary",
        zero_division=0,
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
            input_ids, attention_mask, labels = tensor_batch_to_device(batch, device)
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


def write_markdown_report(
    output_path: Path,
    environment: EnvironmentStatus,
    summaries: list[DatasetSummary],
    config: dict[str, Any],
    training_history: list[dict[str, Any]],
    best_validation: dict[str, Any],
    test_metrics: dict[str, Any],
    test_oracle_metrics: dict[str, Any],
    saved_files: list[str],
) -> None:
    summary_lookup = {item.split: item for item in summaries}
    improvement = test_metrics["f1"] - BASELINE_F1

    lines = [
        "# Final Unified Humor BERT Fine-Tuning Report",
        "",
        "## Environment",
        f"- Device: `{environment.selected_device}`",
        f"- Torch: `{environment.torch_version}`",
        f"- Transformers: `{environment.transformers_version}`",
        f"- CUDA available: `{environment.cuda_available}`",
        f"- MPS available: `{environment.mps_available}`",
        "",
        "## Dataset",
        f"- Train rows: `{summary_lookup['train'].rows:,}`",
        f"- Validation rows: `{summary_lookup['validation'].rows:,}`",
        f"- Test rows: `{summary_lookup['test'].rows:,}`",
        f"- Train positive rate: `{summary_lookup['train'].positive_rate:.4f}`",
        "",
        "## Training Configuration",
        f"- Model: `{config['model_name']}`",
        f"- Max sequence length: `{config['max_length']}`",
        f"- Batch size: `{config['batch_size']}`",
        f"- Epochs requested: `{config['epochs']}`",
        f"- Learning rate: `{config['learning_rate']}`",
        f"- Warmup steps: `{config['warmup_steps']}`",
        f"- Weight decay: `{config['weight_decay']}`",
        f"- Target recall: `{config['target_recall']}`",
        "",
        "## Best Validation",
        f"- Epoch: `{best_validation['epoch']}`",
        f"- Threshold: `{best_validation['threshold']:.2f}`",
        f"- F1: `{best_validation['f1']:.4f}`",
        f"- Precision: `{best_validation['precision']:.4f}`",
        f"- Recall: `{best_validation['recall']:.4f}`",
        f"- Accuracy: `{best_validation['accuracy']:.4f}`",
        "",
        "## Test Metrics Using Validation Threshold",
        f"- Threshold: `{test_metrics['threshold']:.2f}`",
        f"- F1: `{test_metrics['f1']:.4f}`",
        f"- Precision: `{test_metrics['precision']:.4f}`",
        f"- Recall: `{test_metrics['recall']:.4f}`",
        f"- Accuracy: `{test_metrics['accuracy']:.4f}`",
        f"- Baseline F1: `{BASELINE_F1:.4f}`",
        f"- Absolute F1 improvement: `{improvement:+.4f}`",
        "",
        "## Oracle Test Threshold For Analysis Only",
        f"- Threshold: `{test_oracle_metrics['threshold']:.2f}`",
        f"- F1: `{test_oracle_metrics['f1']:.4f}`",
        f"- Precision: `{test_oracle_metrics['precision']:.4f}`",
        f"- Recall: `{test_oracle_metrics['recall']:.4f}`",
        "",
        "## Epoch History",
        "",
    ]

    for record in training_history:
        lines.append(
            "- "
            f"Epoch `{record['epoch']}`: train loss `{record['train_loss']:.4f}`, "
            f"train accuracy `{record['train_accuracy']:.4f}`, "
            f"val F1 `{record['validation_best']['f1']:.4f}`, "
            f"val recall `{record['validation_best']['recall']:.4f}`, "
            f"val threshold `{record['validation_best']['threshold']:.2f}`"
        )

    lines.extend(
        [
            "",
            "## Saved Files",
        ]
    )

    for saved_file in saved_files:
        lines.append(f"- `{saved_file}`")

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--train-csv",
        type=Path,
        default=Path("data/training/final_unified_humor/train.csv"),
    )
    parser.add_argument(
        "--validation-csv",
        type=Path,
        default=Path("data/training/final_unified_humor/validation.csv"),
    )
    parser.add_argument(
        "--test-csv",
        type=Path,
        default=Path("data/training/final_unified_humor/test.csv"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("experiments/final_unified_humor_bert_base"),
    )
    parser.add_argument("--model-name", default="bert-base-uncased")
    parser.add_argument("--max-length", type=int, default=128)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--learning-rate", type=float, default=2e-5)
    parser.add_argument("--weight-decay", type=float, default=0.01)
    parser.add_argument("--warmup-steps", type=int, default=500)
    parser.add_argument("--positive-class-weight", type=float, default=1.25)
    parser.add_argument("--target-recall", type=float, default=0.85)
    parser.add_argument("--threshold-step", type=float, default=0.01)
    parser.add_argument("--early-stopping-patience", type=int, default=1)
    parser.add_argument(
        "--status-every-samples",
        type=int,
        default=DEFAULT_STATUS_EVERY_SAMPLES,
    )
    parser.add_argument("--batch-tokenize-size", type=int, default=2048)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--allow-remote-model-download",
        action="store_true",
        help="Allow Hugging Face to fetch model/tokenizer files from the network if missing locally.",
    )
    parser.add_argument("--max-train-samples", type=int)
    parser.add_argument("--max-validation-samples", type=int)
    parser.add_argument("--max-test-samples", type=int)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    set_seed(args.seed)

    environment = detect_environment()
    log_status(
        "STATUS 1",
        "Environment setup validated: "
        f"torch={environment.torch_version}, transformers={environment.transformers_version}, "
        f"device={environment.selected_device}, cuda={environment.cuda_available}, "
        f"mps={environment.mps_available}",
    )

    log_status("STATUS 2", "Loading unified humor dataset splits")
    train_df, train_summary = load_split(
        args.train_csv,
        "train",
        max_samples=args.max_train_samples,
        seed=args.seed,
    )
    validation_df, validation_summary = load_split(
        args.validation_csv,
        "validation",
        max_samples=args.max_validation_samples,
        seed=args.seed,
    )
    test_df, test_summary = load_split(
        args.test_csv,
        "test",
        max_samples=args.max_test_samples,
        seed=args.seed,
    )
    summaries = [train_summary, validation_summary, test_summary]

    for summary in summaries:
        log_status(
            "STATUS 2",
            f"{summary.split} split loaded: rows={summary.rows:,}, "
            f"positive={summary.positive:,}, negative={summary.negative:,}, "
            f"positive_rate={summary.positive_rate:.4f}, avg_quality={summary.avg_quality_score:.2f}",
        )

    tokenizer = AutoTokenizer.from_pretrained(
        args.model_name,
        use_fast=True,
        local_files_only=not args.allow_remote_model_download,
    )
    log_status(
        "STATUS 2",
        f"Tokenizer ready: {args.model_name} with max_length={args.max_length}",
    )

    train_dataset = tokenize_split(
        train_df,
        tokenizer,
        "train",
        args.max_length,
        args.status_every_samples,
        args.batch_tokenize_size,
    )
    validation_dataset = tokenize_split(
        validation_df,
        tokenizer,
        "validation",
        args.max_length,
        args.status_every_samples,
        args.batch_tokenize_size,
    )
    test_dataset = tokenize_split(
        test_df,
        tokenizer,
        "test",
        args.max_length,
        args.status_every_samples,
        args.batch_tokenize_size,
    )

    device = torch.device(environment.selected_device)
    train_loader = create_dataloader(train_dataset, args.batch_size, True, environment.selected_device)
    validation_loader = create_dataloader(
        validation_dataset,
        args.batch_size,
        False,
        environment.selected_device,
    )
    test_loader = create_dataloader(test_dataset, args.batch_size, False, environment.selected_device)

    model = BertForSequenceClassification.from_pretrained(
        args.model_name,
        num_labels=2,
        local_files_only=not args.allow_remote_model_download,
    ).to(device)

    class_weights = torch.tensor(
        [1.0, args.positive_class_weight],
        dtype=torch.float32,
        device=device,
    )
    loss_fn = nn.CrossEntropyLoss(weight=class_weights)
    optimizer = AdamW(
        model.parameters(),
        lr=args.learning_rate,
        weight_decay=args.weight_decay,
    )

    steps_per_epoch = math.ceil(len(train_dataset) / args.batch_size)
    total_steps = max(steps_per_epoch * args.epochs, 1)
    warmup_steps = min(args.warmup_steps, max(total_steps // 2, 1))
    scheduler = get_linear_schedule_with_warmup(
        optimizer,
        num_warmup_steps=warmup_steps,
        num_training_steps=total_steps,
    )

    config_snapshot = {
        "model_name": args.model_name,
        "max_length": args.max_length,
        "batch_size": args.batch_size,
        "epochs": args.epochs,
        "learning_rate": args.learning_rate,
        "weight_decay": args.weight_decay,
        "warmup_steps": warmup_steps,
        "positive_class_weight": args.positive_class_weight,
        "target_recall": args.target_recall,
        "threshold_step": args.threshold_step,
        "seed": args.seed,
        "class_weights": [float(value) for value in class_weights.detach().cpu().tolist()],
        "train_csv": str(args.train_csv),
        "validation_csv": str(args.validation_csv),
        "test_csv": str(args.test_csv),
    }

    best_validation_record: dict[str, Any] | None = None
    best_epoch = 0
    epochs_without_improvement = 0
    training_history: list[dict[str, Any]] = []
    best_model_dir = args.output_dir / "best_model"

    log_status(
        "STATUS 3",
        f"Starting BERT fine-tuning: epochs={args.epochs}, batch_size={args.batch_size}, "
        f"steps_per_epoch={steps_per_epoch}, warmup_steps={warmup_steps}",
    )

    for epoch in range(1, args.epochs + 1):
        model.train()
        total_train_loss = 0.0
        train_labels: list[np.ndarray] = []
        train_predictions: list[np.ndarray] = []

        for batch in train_loader:
            input_ids, attention_mask, labels = tensor_batch_to_device(batch, device)
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

        epoch_train_labels = np.concatenate(train_labels, axis=0)
        epoch_train_predictions = np.concatenate(train_predictions, axis=0)
        train_accuracy = float(accuracy_score(epoch_train_labels, epoch_train_predictions))
        train_loss = total_train_loss / max(len(train_loader), 1)

        validation_loss, validation_labels, validation_probabilities = evaluate_model(
            model,
            validation_loader,
            device,
            loss_fn,
        )
        validation_default = compute_binary_metrics(
            validation_labels,
            validation_probabilities,
            threshold=0.5,
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
            f"train_accuracy={train_accuracy:.4f}, val_loss={validation_loss:.4f}, "
            f"val_f1={validation_best['f1']:.4f}, val_precision={validation_best['precision']:.4f}, "
            f"val_recall={validation_best['recall']:.4f}, val_accuracy={validation_best['accuracy']:.4f}, "
            f"best_threshold={validation_best['threshold']:.2f}, "
            f"recall_target_met={validation_best['meets_target_recall']}",
        )

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
            epochs_without_improvement = 0
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
                f"New best checkpoint saved from epoch {epoch} with validation F1={validation_best['f1']:.4f}",
            )
        else:
            epochs_without_improvement += 1
            if epochs_without_improvement >= args.early_stopping_patience:
                log_status(
                    "STATUS 3",
                    f"Early stopping triggered after epoch {epoch}; best epoch remains {best_epoch}",
                )
                break

    if best_validation_record is None:
        raise RuntimeError("Training finished without producing a validation checkpoint")

    model = BertForSequenceClassification.from_pretrained(best_model_dir).to(device)

    validation_loss, validation_labels, validation_probabilities = evaluate_model(
        model,
        validation_loader,
        device,
        loss_fn,
    )
    selected_validation_metrics = compute_binary_metrics(
        validation_labels,
        validation_probabilities,
        threshold=best_validation_record["threshold"],
    )
    selected_validation_metrics["loss"] = validation_loss
    selected_validation_metrics["epoch"] = best_validation_record["epoch"]

    test_loss, test_labels, test_probabilities = evaluate_model(
        model,
        test_loader,
        device,
        loss_fn,
    )
    test_metrics = compute_binary_metrics(
        test_labels,
        test_probabilities,
        threshold=best_validation_record["threshold"],
    )
    test_metrics["loss"] = test_loss
    test_metrics["baseline_f1"] = BASELINE_F1
    test_metrics["absolute_f1_gain"] = test_metrics["f1"] - BASELINE_F1
    test_metrics["relative_f1_gain_pct"] = (
        (test_metrics["f1"] - BASELINE_F1) / BASELINE_F1 * 100.0
    )
    test_metrics["recall_target_met"] = test_metrics["recall"] >= args.target_recall

    test_oracle_metrics = find_best_threshold(
        test_labels,
        test_probabilities,
        target_recall=args.target_recall,
        threshold_step=args.threshold_step,
    )
    test_oracle_metrics["loss"] = test_loss

    log_status(
        "STATUS 4",
        f"Evaluation complete: test_f1={test_metrics['f1']:.4f}, "
        f"precision={test_metrics['precision']:.4f}, recall={test_metrics['recall']:.4f}, "
        f"accuracy={test_metrics['accuracy']:.4f}, threshold={test_metrics['threshold']:.2f}, "
        f"baseline_f1={BASELINE_F1:.4f}, absolute_gain={test_metrics['absolute_f1_gain']:+.4f}",
    )
    log_status(
        "STATUS 4",
        f"Threshold optimization summary: validation threshold={best_validation_record['threshold']:.2f}, "
        f"validation target recall met={best_validation_record['meets_target_recall']}, "
        f"test target recall met={test_metrics['recall_target_met']}",
    )

    artifacts = {
        "environment": asdict(environment),
        "dataset_summaries": [asdict(item) for item in summaries],
        "config": config_snapshot,
        "training_history": training_history,
        "best_validation": best_validation_record,
        "selected_validation_metrics": selected_validation_metrics,
        "test_metrics": test_metrics,
        "test_oracle_metrics": test_oracle_metrics,
    }

    save_json(args.output_dir / "metrics_summary.json", artifacts)
    save_json(args.output_dir / "environment_status.json", asdict(environment))
    save_json(
        args.output_dir / "dataset_summary.json",
        {"summaries": [asdict(item) for item in summaries]},
    )
    save_json(args.output_dir / "training_history.json", {"history": training_history})
    save_json(
        args.output_dir / "deployment_manifest.json",
        {
            "model_dir": str(best_model_dir),
            "threshold_file": str(best_model_dir / "selected_threshold.json"),
            "tokenizer_dir": str(best_model_dir),
            "metrics_summary": str(args.output_dir / "metrics_summary.json"),
        },
    )

    write_markdown_report(
        args.output_dir / "evaluation_report.md",
        environment=environment,
        summaries=summaries,
        config=config_snapshot,
        training_history=training_history,
        best_validation=best_validation_record,
        test_metrics=test_metrics,
        test_oracle_metrics=test_oracle_metrics,
        saved_files=[],
    )

    saved_files = sorted(
        str(path.relative_to(args.output_dir))
        for path in args.output_dir.rglob("*")
        if path.is_file()
    )
    write_markdown_report(
        args.output_dir / "evaluation_report.md",
        environment=environment,
        summaries=summaries,
        config=config_snapshot,
        training_history=training_history,
        best_validation=best_validation_record,
        test_metrics=test_metrics,
        test_oracle_metrics=test_oracle_metrics,
        saved_files=saved_files,
    )

    log_status(
        "STATUS 5",
        f"Model artifacts saved under {args.output_dir} with deployable checkpoint at {best_model_dir}",
    )
    log_status(
        "STATUS 5",
        "Saved files: "
        + ", ".join(saved_files),
    )


if __name__ == "__main__":
    main()
