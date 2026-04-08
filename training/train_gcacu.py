#!/usr/bin/env python3
"""
GCACU Training Script for Autonomous Laughter Prediction

Trains the GCACU (Gated Contrast-Attention) network on the original 505 dataset
using Adaptive Focal Loss for noisy label handling.
"""

import sys
import json
import argparse
from pathlib import Path
from dataclasses import dataclass, asdict
from types import SimpleNamespace
from typing import Any, Dict, List, Optional, Sequence

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch import Tensor
from torch.optim import AdamW
from torch.utils.data import DataLoader, Dataset
from transformers import AutoModelForTokenClassification, AutoTokenizer, get_linear_schedule_with_warmup

sys.path.insert(0, str(Path(__file__).parent))
from gcacu_network import GCACUTokenClassifier, AdaptiveFocalLoss, create_gcacu_model, GCACUConfig

DATASET_DIR = Path(__file__).parent.parent / "data" / "training"
DEFAULT_MODEL_NAME = "FacebookAI/xlm-roberta-base"


def set_seed(seed: int):
    import random
    random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def choose_device() -> torch.device:
    if torch.backends.mps.is_available():
        return torch.device("mps")
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


@dataclass
class TrainingConfig:
    model_name: str = DEFAULT_MODEL_NAME
    num_labels: int = 2
    max_length: int = 256
    batch_size: int = 16
    eval_batch_size: int = 8
    learning_rate: float = 2e-5
    gcacu_dim: int = 128
    num_heads: int = 4
    gate_scale: float = 0.3
    epochs: int = 5
    warmup_ratio: float = 0.1
    weight_decay: float = 0.01
    focal_gamma: float = 2.0
    positive_class_weight: float = 4.0
    early_stopping_patience: int = 2
    seed: int = 42
    debug: bool = False


class StandupExample:
    def __init__(
        self,
        example_id: str,
        language: str,
        words: List[str],
        labels: List[int],
        **kwargs
    ):
        self.example_id = example_id
        self.language = language
        self.words = words
        self.labels = labels
        for k, v in kwargs.items():
            setattr(self, k, v)


class StandupDataset(Dataset):
    def __init__(self, examples: Sequence[StandupExample], tokenizer: Any, max_length: int):
        self.examples = list(examples)
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self) -> int:
        return len(self.examples)

    def __getitem__(self, index: int) -> Dict[str, Any]:
        example = self.examples[index]
        encoding = self.tokenizer(
            example.words,
            is_split_into_words=True,
            truncation=True,
            max_length=self.max_length,
            padding="max_length",
            return_tensors="pt"
        )

        label_ids = []
        word_ids = encoding.word_ids()
        previous_word_idx = None
        for word_idx in word_ids:
            if word_idx is None:
                label_ids.append(-100)
            elif word_idx != previous_word_idx:
                if word_idx < len(example.labels):
                    label_ids.append(example.labels[word_idx])
                else:
                    label_ids.append(-100)
            else:
                label_ids.append(-100)
            previous_word_idx = word_idx

        return {
            "input_ids": encoding["input_ids"].squeeze(0),
            "attention_mask": encoding["attention_mask"].squeeze(0),
            "labels": torch.tensor(label_ids, dtype=torch.long)
        }


def load_jsonl_examples(path: Path) -> List[StandupExample]:
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")

    examples = []
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw_line.strip():
            continue
        payload = json.loads(raw_line)
        words = payload.get("words", [])
        labels = payload.get("labels", [])

        if len(words) != len(labels):
            continue

        examples.append(StandupExample(
            example_id=str(payload.get("example_id", f"{path.stem}_{line_number}")),
            language=str(payload.get("language", "en")),
            words=[str(w) for w in words],
            labels=[int(l) for l in labels],
        ))

    return examples


def compute_metrics(preds: Tensor, labels: Tensor, attention_mask: Tensor) -> Dict[str, float]:
    mask = attention_mask.view(-1) == 1
    preds_flat = preds.view(-1)[mask]
    labels_flat = labels.view(-1)[mask]

    preds_flat = preds_flat.float()
    labels_flat = labels_flat.float()

    tp = ((preds_flat == 1) & (labels_flat == 1)).sum().item()
    fp = ((preds_flat == 1) & (labels_flat == 0)).sum().item()
    tn = ((preds_flat == 0) & (labels_flat == 0)).sum().item()
    fn = ((preds_flat == 0) & (labels_flat == 1)).sum().item()

    precision = tp / (tp + fp + 1e-8)
    recall = tp / (tp + fn + 1e-8)
    f1 = 2 * precision * recall / (precision + recall + 1e-8)

    iou = tp / (tp + fp + fn + 1e-8)

    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "iou_f1": iou,
        "support": len(labels_flat)
    }


def train_epoch(
    model: nn.Module,
    dataloader: DataLoader,
    optimizer: torch.optim.Optimizer,
    scheduler: Any,
    device: torch.device,
    criterion: nn.Module,
    gcacu_enabled: bool = True
) -> Dict[str, float]:
    model.train()
    total_loss = 0
    all_preds = []
    all_labels = []
    all_masks = []

    for batch in dataloader:
        input_ids = batch["input_ids"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        labels = batch["labels"].to(device)

        optimizer.zero_grad()

        if gcacu_enabled and hasattr(model, 'backbone'):
            outputs = model(input_ids, attention_mask)
        else:
            outputs = model(input_ids, attention_mask)

        logits = outputs.logits

        loss = criterion(logits.view(-1, 2), labels.view(-1))

        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        scheduler.step()

        total_loss += loss.item()

        preds = torch.argmax(logits, dim=-1)
        all_preds.append(preds.cpu())
        all_labels.append(labels.cpu())
        all_masks.append(attention_mask.cpu())

    all_preds = torch.cat(all_preds)
    all_labels = torch.cat(all_labels)
    all_masks = torch.cat(all_masks)

    metrics = compute_metrics(all_preds, all_labels, all_masks)
    metrics["loss"] = total_loss / len(dataloader)

    return metrics


def evaluate(
    model: nn.Module,
    dataloader: DataLoader,
    device: torch.device,
    criterion: nn.Module,
    gcacu_enabled: bool = True
) -> Dict[str, float]:
    model.eval()
    total_loss = 0
    all_preds = []
    all_labels = []
    all_masks = []

    with torch.no_grad():
        for batch in dataloader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"].to(device)

            if gcacu_enabled and hasattr(model, 'backbone'):
                outputs = model(input_ids, attention_mask)
            else:
                outputs = model(input_ids, attention_mask)

            logits = outputs.logits

            loss = criterion(logits.view(-1, 2), labels.view(-1))
            total_loss += loss.item()

            preds = torch.argmax(logits, dim=-1)
            all_preds.append(preds.cpu())
            all_labels.append(labels.cpu())
            all_masks.append(attention_mask.cpu())

    all_preds = torch.cat(all_preds)
    all_labels = torch.cat(all_labels)
    all_masks = torch.cat(all_masks)

    metrics = compute_metrics(all_preds, all_labels, all_masks)
    metrics["loss"] = total_loss / len(dataloader)

    return metrics


def train_gcacu(
    train_file: Path,
    valid_file: Path,
    test_file: Path,
    output_dir: Path,
    config: TrainingConfig
):
    set_seed(config.seed)
    device = choose_device()
    print(f"Using device: {device}")

    output_dir.mkdir(parents=True, exist_ok=True)

    print("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(config.model_name)

    print("Loading datasets...")
    train_examples = load_jsonl_examples(train_file)
    valid_examples = load_jsonl_examples(valid_file)
    test_examples = load_jsonl_examples(test_file)

    print(f"Train: {len(train_examples)}, Valid: {len(valid_examples)}, Test: {len(test_examples)}")

    train_dataset = StandupDataset(train_examples, tokenizer, config.max_length)
    valid_dataset = StandupDataset(valid_examples, tokenizer, config.max_length)
    test_dataset = StandupDataset(test_examples, tokenizer, config.max_length)

    train_loader = DataLoader(train_dataset, batch_size=config.batch_size, shuffle=True)
    valid_loader = DataLoader(valid_dataset, batch_size=config.eval_batch_size)
    test_loader = DataLoader(test_dataset, batch_size=config.eval_batch_size)

    print("Creating GCACU model...")
    backbone = AutoModelForTokenClassification.from_pretrained(
        config.model_name,
        num_labels=config.num_labels
    )
    model = create_gcacu_model(
        backbone,
        gcacu_dim=config.gcacu_dim,
        num_heads=config.num_heads,
        gate_scale=config.gate_scale
    )
    model.to(device)

    criterion = AdaptiveFocalLoss(gamma=config.focal_gamma)

    optimizer = AdamW(model.parameters(), lr=config.learning_rate, weight_decay=config.weight_decay)

    total_steps = len(train_loader) * config.epochs
    warmup_steps = int(total_steps * config.warmup_ratio)
    scheduler = get_linear_schedule_with_warmup(optimizer, warmup_steps, total_steps)

    best_f1 = 0
    patience_counter = 0

    print("\nStarting training...")
    for epoch in range(config.epochs):
        print(f"\nEpoch {epoch + 1}/{config.epochs}")

        train_metrics = train_epoch(model, train_loader, optimizer, scheduler, device, criterion, gcacu_enabled=True)
        print(f"Train - Loss: {train_metrics['loss']:.4f}, F1: {train_metrics['f1']:.4f}, IoU-F1: {train_metrics['iou_f1']:.4f}")

        valid_metrics = evaluate(model, valid_loader, device, criterion, gcacu_enabled=True)
        print(f"Valid - Loss: {valid_metrics['loss']:.4f}, F1: {valid_metrics['f1']:.4f}, IoU-F1: {valid_metrics['iou_f1']:.4f}")

        if valid_metrics['f1'] > best_f1:
            best_f1 = valid_metrics['f1']
            patience_counter = 0

            model.backbone.save_pretrained(output_dir / "best_model")
            tokenizer.save_pretrained(output_dir / "best_model")

            print(f"New best model saved! F1: {best_f1:.4f}")
        else:
            patience_counter += 1
            if patience_counter >= config.early_stopping_patience:
                print(f"Early stopping triggered after {epoch + 1} epochs")
                break

    print("\n" + "=" * 60)
    print("Training complete. Loading best model for final evaluation...")

    backbone = AutoModelForTokenClassification.from_pretrained(output_dir / "best_model", num_labels=2)
    model = create_gcacu_model(backbone, gcacu_dim=config.gcacu_dim, num_heads=config.num_heads, gate_scale=config.gate_scale)
    model.to(device)

    test_metrics = evaluate(model, test_loader, device, criterion, gcacu_enabled=True)
    print(f"\nFinal Test Metrics:")
    print(f"  F1: {test_metrics['f1']:.4f}")
    print(f"  IoU-F1: {test_metrics['iou_f1']:.4f}")
    print(f"  Precision: {test_metrics['precision']:.4f}")
    print(f"  Recall: {test_metrics['recall']:.4f}")

    results = {
        "config": asdict(config),
        "test_metrics": test_metrics,
        "best_validation_f1": best_f1
    }

    with open(output_dir / "training_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to {output_dir / 'training_results.json'}")

    return results


def main():
    parser = argparse.ArgumentParser(description="Train GCACU model for laughter prediction")
    parser.add_argument("--train-file", type=str, default=str(DATASET_DIR / "standup_word_level" / "train.jsonl"))
    parser.add_argument("--valid-file", type=str, default=str(DATASET_DIR / "standup_word_level" / "valid.jsonl"))
    parser.add_argument("--test-file", type=str, default=str(DATASET_DIR / "standup_word_level" / "test.jsonl"))
    parser.add_argument("--output-dir", type=str, default="experiments/gcacu_model")
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--learning-rate", type=float, default=2e-5)
    parser.add_argument("--gcacu-dim", type=int, default=128)
    parser.add_argument("--num-heads", type=int, default=4)
    parser.add_argument("--gate-scale", type=float, default=0.3)
    parser.add_argument("--focal-gamma", type=float, default=2.0)
    parser.add_argument("--seed", type=int, default=42)

    args = parser.parse_args()

    config = TrainingConfig(
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        gcacu_dim=args.gcacu_dim,
        num_heads=args.num_heads,
        gate_scale=args.gate_scale,
        focal_gamma=args.focal_gamma,
        seed=args.seed
    )

    results = train_gcacu(
        train_file=Path(args.train_file),
        valid_file=Path(args.valid_file),
        test_file=Path(args.test_file),
        output_dir=Path(args.output_dir),
        config=config
    )


if __name__ == "__main__":
    main()
