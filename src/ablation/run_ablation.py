#!/usr/bin/env python3
"""
Ablation Study Runner

Trains all 6 model variants on identical data splits to determine
which biosemiotic components independently contribute to humor recognition.

Variants:
1. BaselineBERT - Pure BERT fine-tuning
2. DuchenneOnly - BERT + Duchenne laughter detection
3. GCACUOnly - BERT + Incongruity detection
4. TOMOnly - BERT + Theory of Mind modeling
5. CulturalOnly - BERT + Cultural adaptation
6. FullBiosemiotic - All components combined

Run with:
    python -m src.ablation.run_ablation --epochs 3 --batch-size 8
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import accuracy_score, f1_score, precision_recall_fscore_support
from torch import nn
from torch.optim import AdamW
from torch.utils.data import DataLoader, TensorDataset
from transformers import AutoTokenizer, get_linear_schedule_with_warmup

from .baseline_model import BaselineBERT, create_baseline
from .duchenne_only import DuchenneOnly, create_duchenne_only
from .gcacu_only import GCACUOnly, create_gcacu_only
from .tom_only import TOMOnly, create_tom_only
from .cultural_only import CulturalOnly, create_cultural_only
from .full_model import FullBiosemiotic, create_full_model


MODELS = {
    "baseline": BaselineBERT,
    "duchenne_only": DuchenneOnly,
    "gcacu_only": GCACUOnly,
    "tom_only": TOMOnly,
    "cultural_only": CulturalOnly,
    "full_biosemiotic": FullBiosemiotic,
}


@dataclass
class AblationResult:
    model_name: str
    accuracy: float
    precision: float
    recall: float
    f1: float
    parameters: int
    training_time: float


def load_data(data_path: str = "data/training/reddit_jokes"):
    """Load and preprocess training data."""
    train_df = pd.read_csv(f"{data_path}/train.csv")
    val_df = pd.read_csv(f"{data_path}/validation.csv")
    test_df = pd.read_csv(f"{data_path}/test.csv")

    return train_df, val_df, test_df


def create_dataloaders(df: pd.DataFrame, tokenizer, batch_size: int = 8, max_length: int = 128):
    """Create PyTorch dataloader from dataframe."""
    texts = df["text"].tolist()
    labels = df["humor"].tolist()

    inputs = tokenizer(
        texts,
        padding=True,
        truncation=True,
        max_length=max_length,
        return_tensors="pt",
    )

    dataset = TensorDataset(
        inputs["input_ids"],
        inputs["attention_mask"],
        torch.tensor(labels, dtype=torch.long),
    )

    return DataLoader(dataset, batch_size=batch_size, shuffle=True)


def train_model(
    model: nn.Module,
    train_loader: DataLoader,
    val_loader: DataLoader,
    epochs: int = 3,
    lr: float = 2e-5,
    device: str = "cpu",
) -> dict[str, Any]:
    """Train a model and return metrics."""
    optimizer = AdamW(model.parameters(), lr=lr)
    total_steps = len(train_loader) * epochs
    scheduler = get_linear_schedule_with_warmup(
        optimizer,
        num_warmup_steps=500,
        num_training_steps=total_steps,
    )

    best_val_f1 = 0.0
    best_model_state = None

    for epoch in range(epochs):
        model.train()
        total_loss = 0

        for batch_idx, (input_ids, attention_mask, labels) in enumerate(train_loader):
            input_ids = input_ids.to(device)
            attention_mask = attention_mask.to(device)
            labels = labels.to(device)

            optimizer.zero_grad()

            loss, logits, *_ = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                labels=labels,
            )

            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            scheduler.step()

            total_loss += loss.item()

            if batch_idx % 100 == 0:
                print(f"  Epoch {epoch+1}, Batch {batch_idx}/{len(train_loader)}, Loss: {loss.item():.4f}")

        avg_loss = total_loss / len(train_loader)

        val_metrics = evaluate_model(model, val_loader, device)
        print(f"  Epoch {epoch+1}: Val Acc={val_metrics['accuracy']:.4f}, Val F1={val_metrics['f1']:.4f}")

        if val_metrics["f1"] > best_val_f1:
            best_val_f1 = val_metrics["f1"]
            best_model_state = model.state_dict().copy()

    model.load_state_dict(best_model_state)
    return {"best_val_f1": best_val_f1, "final_train_loss": avg_loss}


def evaluate_model(model: nn.Module, data_loader: DataLoader, device: str = "cpu") -> dict[str, float]:
    """Evaluate model on data loader."""
    model.eval()
    all_preds = []
    all_labels = []

    with torch.no_grad():
        for input_ids, attention_mask, labels in data_loader:
            input_ids = input_ids.to(device)
            attention_mask = attention_mask.to(device)
            labels = labels.to(device)

            _, logits, *_ = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
            )

            preds = torch.argmax(logits, dim=-1)
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())

    accuracy = accuracy_score(all_labels, all_preds)
    precision, recall, f1, _ = precision_recall_fscore_support(
        all_labels, all_preds, average="binary", zero_division=0
    )

    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def run_ablation(
    data_path: str = "data/training/reddit_jokes",
    output_dir: str = "experiments/ablation",
    epochs: int = 3,
    batch_size: int = 8,
    learning_rate: float = 2e-5,
    device: str = "cpu",
):
    """Run full ablation study."""
    print("=" * 60)
    print("BIOSEMIOTIC ABLATION STUDY")
    print("=" * 60)
    print(f"Data: {data_path}")
    print(f"Epochs: {epochs}, Batch Size: {batch_size}, LR: {learning_rate}")
    print(f"Device: {device}")
    print()

    tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")

    train_df, val_df, test_df = load_data(data_path)
    print(f"Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}")

    train_loader = create_dataloaders(train_df, tokenizer, batch_size)
    val_loader = create_dataloaders(val_df, tokenizer, batch_size)
    test_loader = create_dataloaders(test_df, tokenizer, batch_size)

    results = []

    for model_name, model_class in MODELS.items():
        print(f"\n{'='*40}")
        print(f"Training: {model_name}")
        print(f"{'='*40}")

        model = model_class().to(device)
        param_count = sum(p.numel() for p in model.parameters())
        print(f"Parameters: {param_count:,}")

        import time
        start_time = time.time()

        metrics = train_model(
            model,
            train_loader,
            val_loader,
            epochs=epochs,
            lr=learning_rate,
            device=device,
        )

        training_time = time.time() - start_time

        test_metrics = evaluate_model(model, test_loader, device)

        result = AblationResult(
            model_name=model_name,
            accuracy=test_metrics["accuracy"],
            precision=test_metrics["precision"],
            recall=test_metrics["recall"],
            f1=test_metrics["f1"],
            parameters=param_count,
            training_time=training_time,
        )
        results.append(result)

        print(f"\nTest Results for {model_name}:")
        print(f"  Accuracy: {test_metrics['accuracy']:.4f}")
        print(f"  Precision: {test_metrics['precision']:.4f}")
        print(f"  Recall: {test_metrics['recall']:.4f}")
        print(f"  F1: {test_metrics['f1']:.4f}")
        print(f"  Training Time: {training_time:.1f}s")

        model_path = Path(output_dir) / model_name / "best_model.pt"
        model_path.parent.mkdir(parents=True, exist_ok=True)
        torch.save(model.state_dict(), model_path)

    results_df = pd.DataFrame([{
        "model": r.model_name,
        "accuracy": r.accuracy,
        "precision": r.precision,
        "recall": r.recall,
        "f1": r.f1,
        "parameters": r.parameters,
        "training_time": r.training_time,
    } for r in results])

    results_path = Path(output_dir) / "ablation_results.csv"
    results_df.to_csv(results_path, index=False)
    print(f"\nResults saved to: {results_path}")

    print("\n" + "=" * 60)
    print("ABLATION STUDY SUMMARY")
    print("=" * 60)
    print(results_df.to_string(index=False))

    baseline_f1 = results_df[results_df["model"] == "baseline"]["f1"].values[0]

    print(f"\nBaseline F1: {baseline_f1:.4f}")
    print("\nImprovement over baseline:")
    for _, row in results_df.iterrows():
        if row["model"] != "baseline":
            delta = row["f1"] - baseline_f1
            sig = "*" if delta > 0.01 else ""
            print(f"  {row['model']}: {delta:+.4f}{sig}")

    summary = {
        "timestamp": datetime.now().isoformat(),
        "baseline_f1": baseline_f1,
        "best_model": results_df.loc[results_df["f1"].idxmax(), "model"],
        "best_f1": results_df["f1"].max(),
        "results": results_df.to_dict(orient="records"),
    }

    summary_path = Path(output_dir) / "ablation_summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    return results


def main():
    parser = argparse.ArgumentParser(description="Run biosemiotic ablation study")
    parser.add_argument("--data-path", default="data/training/reddit_jokes")
    parser.add_argument("--output-dir", default="experiments/ablation")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--learning-rate", type=float, default=2e-5)
    parser.add_argument("--device", default="cpu")

    args = parser.parse_args()

    run_ablation(
        data_path=args.data_path,
        output_dir=args.output_dir,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        device=args.device,
    )


if __name__ == "__main__":
    main()