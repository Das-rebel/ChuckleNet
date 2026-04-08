#!/usr/bin/env python3
"""
Cognitive Pipeline: Train IntegratedLaughterModel with ToM, CLoST, SEVADE, GCACU

This script integrates the cognitive components (Theory of Mind, CLoST, SEVADE, GCACU)
into the training pipeline using the IntegratedLaughterModel.

Expected JSONL schema:
{
  "id": "example_001",
  "text": "I walked into a bank yesterday...",
  "label": 1.0,
  "metadata": {"source": "standup"}
}

Or CSV/JSON with text and label columns.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import torch
from torch import Tensor
from torch import nn
from torch.nn import functional as F
from torch.optim import AdamW
from torch.utils.data import DataLoader
from tqdm import tqdm

# Add project root to path
project_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_dir))
os.chdir(str(project_dir))

from core.integrated_model import (
    ComedyTranscriptDataset,
    DeterministicTextEmbedder,
    IntegratedLaughterModel,
    load_transcript_records,
    make_dataloader,
    TranscriptRecord,
)


DEFAULT_EMBEDDING_DIM = 64
DEFAULT_HIDDEN_DIM = 64
DEFAULT_NUM_HEADS = 4
DEFAULT_MAX_SEQ_LEN = 128
DEFAULT_BATCH_SIZE = 8
DEFAULT_EVAL_BATCH_SIZE = 16
DEFAULT_LEARNING_RATE = 1e-4
DEFAULT_EPOCHS = 3
DEFAULT_SEED = 42


def set_seed(seed: int) -> None:
    random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def choose_device(explicit: Optional[str] = None) -> torch.device:
    if explicit:
        return torch.device(explicit)
    if torch.backends.mps.is_available():
        return torch.device("mps")
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def compute_binary_metrics(predictions: Sequence[int], labels: Sequence[int]) -> Dict[str, float]:
    tp = sum(1 for pred, label in zip(predictions, labels) if pred == 1 and label == 1)
    fp = sum(1 for pred, label in zip(predictions, labels) if pred == 1 and label == 0)
    fn = sum(1 for pred, label in zip(predictions, labels) if pred == 0 and label == 1)
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    support = sum(1 for label in labels if label == 1)
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "support": float(support),
    }


def mean(values: List[float]) -> float:
    sequence = list(values)
    return sum(sequence) / len(sequence) if sequence else 0.0


def train_epoch(
    model: nn.Module,
    dataloader: DataLoader,
    optimizer: AdamW,
    device: torch.device,
    gradient_accumulation_steps: int = 1,
    max_grad_norm: float = 1.0,
) -> Dict[str, float]:
    model.train()
    total_loss = 0.0
    all_predictions: List[int] = []
    all_labels: List[int] = []

    optimizer.zero_grad()
    for step, batch in enumerate(tqdm(dataloader, desc="Training")):
        inputs = {
            "embeddings": batch["embeddings"].to(device),
            "attention_mask": batch["attention_mask"].to(device),
        }
        targets = batch["targets"].to(device).squeeze(-1)

        outputs = model(inputs)
        logits = outputs["logits"].squeeze(-1)

        # Binary cross-entropy loss
        loss = F.binary_cross_entropy_with_logits(logits, targets)
        scaled_loss = loss / gradient_accumulation_steps
        scaled_loss.backward()

        total_loss += float(loss.item())

        # Collect predictions
        predictions = (torch.sigmoid(logits) > 0.5).long().cpu().tolist()
        labels = targets.long().cpu().tolist()
        all_predictions.extend(predictions)
        all_labels.extend(labels)

        if (step + 1) % gradient_accumulation_steps == 0:
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_grad_norm)
            optimizer.step()
            optimizer.zero_grad()

    # Final step if not aligned with accumulation
    if (step + 1) % gradient_accumulation_steps != 0:
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_grad_norm)
        optimizer.step()
        optimizer.zero_grad()

    metrics = compute_binary_metrics(all_predictions, all_labels)
    metrics["loss"] = total_loss / max(1, len(dataloader))
    return metrics


def evaluate(
    model: nn.Module,
    dataloader: DataLoader,
    device: torch.device,
) -> Dict[str, float]:
    model.eval()
    total_loss = 0.0
    all_predictions: List[int] = []
    all_labels: List[int] = []

    with torch.no_grad():
        for batch in tqdm(dataloader, desc="Evaluating"):
            inputs = {
                "embeddings": batch["embeddings"].to(device),
                "attention_mask": batch["attention_mask"].to(device),
            }
            targets = batch["targets"].to(device).squeeze(-1)

            outputs = model(inputs)
            logits = outputs["logits"].squeeze(-1)

            loss = F.binary_cross_entropy_with_logits(logits, targets)
            total_loss += float(loss.item())

            predictions = (torch.sigmoid(logits) > 0.5).long().cpu().tolist()
            labels = targets.long().cpu().tolist()
            all_predictions.extend(predictions)
            all_labels.extend(labels)

    metrics = compute_binary_metrics(all_predictions, all_labels)
    metrics["loss"] = total_loss / max(1, len(dataloader))
    return metrics


def save_model(model: nn.Module, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), output_dir / "cognitive_model.pt")
    print(f"Model saved to {output_dir}")


def train(
    train_records: Sequence[TranscriptRecord],
    valid_records: Sequence[TranscriptRecord],
    output_dir: Path,
    embedding_dim: int = DEFAULT_EMBEDDING_DIM,
    hidden_dim: int = DEFAULT_HIDDEN_DIM,
    num_heads: int = DEFAULT_NUM_HEADS,
    max_seq_len: int = DEFAULT_MAX_SEQ_LEN,
    batch_size: int = DEFAULT_BATCH_SIZE,
    eval_batch_size: int = DEFAULT_EVAL_BATCH_SIZE,
    learning_rate: float = DEFAULT_LEARNING_RATE,
    epochs: int = DEFAULT_EPOCHS,
    seed: int = DEFAULT_SEED,
    device: Optional[str] = None,
    mhc_low_rank: int = 4,
    turboquant_heads: int = 4,
    memory_budget_gb: float = 8.0,
    gradient_accumulation_steps: int = 1,
    max_grad_norm: float = 1.0,
) -> Dict[str, Any]:
    set_seed(seed)
    device = choose_device(device)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create model
    model = IntegratedLaughterModel(
        embedding_dim=embedding_dim,
        hidden_dim=hidden_dim,
        num_heads=num_heads,
        mhc_low_rank=mhc_low_rank,
        turboquant_heads=turboquant_heads,
        memory_budget_gb=memory_budget_gb,
    )
    model.to(device)

    # Create dataloaders
    train_loader = make_dataloader(
        records=list(train_records),
        embedding_dim=embedding_dim,
        max_seq_len=max_seq_len,
        batch_size=batch_size,
        shuffle=True,
    )
    valid_loader = make_dataloader(
        records=list(valid_records),
        embedding_dim=embedding_dim,
        max_seq_len=max_seq_len,
        batch_size=eval_batch_size,
        shuffle=False,
    )

    # Optimizer
    optimizer = AdamW(model.parameters(), lr=learning_rate)

    best_f1 = -1.0
    training_history: List[Dict[str, Any]] = []

    for epoch in range(epochs):
        print(f"\nEpoch {epoch + 1}/{epochs}")

        train_metrics = train_epoch(
            model=model,
            dataloader=train_loader,
            optimizer=optimizer,
            device=device,
            gradient_accumulation_steps=gradient_accumulation_steps,
            max_grad_norm=max_grad_norm,
        )

        valid_metrics = evaluate(
            model=model,
            dataloader=valid_loader,
            device=device,
        )

        print(f"Train Loss: {train_metrics['loss']:.4f}, Train F1: {train_metrics['f1']:.4f}")
        print(f"Valid Loss: {valid_metrics['loss']:.4f}, Valid F1: {valid_metrics['f1']:.4f}")

        epoch_metrics = {
            "epoch": epoch + 1,
            "train": train_metrics,
            "valid": valid_metrics,
        }
        training_history.append(epoch_metrics)

        if valid_metrics["f1"] > best_f1:
            best_f1 = valid_metrics["f1"]
            save_model(model, output_dir / "best_model")

    # Save training summary
    summary = {
        "best_validation_f1": best_f1,
        "history": training_history,
        "config": {
            "embedding_dim": embedding_dim,
            "hidden_dim": hidden_dim,
            "num_heads": num_heads,
            "max_seq_len": max_seq_len,
            "batch_size": batch_size,
            "learning_rate": learning_rate,
            "epochs": epochs,
            "seed": seed,
        },
    }
    (output_dir / "training_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train Cognitive Laughter Model (ToM + CLoST + SEVADE + GCACU)"
    )
    parser.add_argument("--train-file", type=Path, required=True, help="Training data file (JSONL/JSON/CSV)")
    parser.add_argument("--valid-file", type=Path, required=True, help="Validation data file (JSONL/JSON/CSV)")
    parser.add_argument("--test-file", type=Path, default=None, help="Optional test data file")
    parser.add_argument("--output-dir", type=Path, required=True, help="Output directory for checkpoints")
    parser.add_argument("--embedding-dim", type=int, default=DEFAULT_EMBEDDING_DIM)
    parser.add_argument("--hidden-dim", type=int, default=DEFAULT_HIDDEN_DIM)
    parser.add_argument("--num-heads", type=int, default=DEFAULT_NUM_HEADS)
    parser.add_argument("--max-seq-len", type=int, default=DEFAULT_MAX_SEQ_LEN)
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument("--eval-batch-size", type=int, default=DEFAULT_EVAL_BATCH_SIZE)
    parser.add_argument("--learning-rate", type=float, default=DEFAULT_LEARNING_RATE)
    parser.add_argument("--epochs", type=int, default=DEFAULT_EPOCHS)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--device", default=None)
    parser.add_argument("--mhc-low-rank", type=int, default=4)
    parser.add_argument("--turboquant-heads", type=int, default=4)
    parser.add_argument("--memory-budget-gb", type=float, default=8.0)
    parser.add_argument("--gradient-accumulation-steps", type=int, default=1)
    parser.add_argument("--max-grad-norm", type=float, default=1.0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    print("Loading training data...")
    train_records = load_transcript_records(args.train_file)
    print(f"Loaded {len(train_records)} training examples")

    print("Loading validation data...")
    valid_records = load_transcript_records(args.valid_file)
    print(f"Loaded {len(valid_records)} validation examples")

    test_records = None
    if args.test_file:
        print("Loading test data...")
        test_records = load_transcript_records(args.test_file)
        print(f"Loaded {len(test_records)} test examples")

    summary = train(
        train_records=train_records,
        valid_records=valid_records,
        output_dir=args.output_dir,
        embedding_dim=args.embedding_dim,
        hidden_dim=args.hidden_dim,
        num_heads=args.num_heads,
        max_seq_len=args.max_seq_len,
        batch_size=args.batch_size,
        eval_batch_size=args.eval_batch_size,
        learning_rate=args.learning_rate,
        epochs=args.epochs,
        seed=args.seed,
        device=args.device,
        mhc_low_rank=args.mhc_low_rank,
        turboquant_heads=args.turboquant_heads,
        memory_budget_gb=args.memory_budget_gb,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        max_grad_norm=args.max_grad_norm,
    )

    print("\nTraining complete!")
    print(f"Best validation F1: {summary['best_validation_f1']:.4f}")

    if test_records is not None:
        print("\nEvaluating on test set...")
        device = choose_device(args.device)
        model = IntegratedLaughterModel(
            embedding_dim=args.embedding_dim,
            hidden_dim=args.hidden_dim,
            num_heads=args.num_heads,
            mhc_low_rank=args.mhc_low_rank,
            turboquant_heads=args.turboquant_heads,
            memory_budget_gb=args.memory_budget_gb,
        )
        model.load_state_dict(torch.load(args.output_dir / "best_model" / "cognitive_model.pt", map_location=device))
        model.to(device)

        test_loader = make_dataloader(
            records=list(test_records),
            embedding_dim=args.embedding_dim,
            max_seq_len=args.max_seq_len,
            batch_size=args.eval_batch_size,
            shuffle=False,
        )
        test_metrics = evaluate(model, test_loader, device)
        print(f"Test F1: {test_metrics['f1']:.4f}")


if __name__ == "__main__":
    main()