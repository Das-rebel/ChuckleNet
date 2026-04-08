"""
Evaluation Script for Biosemiotic Humor Classifier

Usage:
    python -m biosemioticai.evaluate \
        --model experiments/biosemotic_humor_bert_lr2e5 \
        --data data/training/reddit_jokes/test.csv
"""

from __future__ import annotations
import argparse
import json
from pathlib import Path

import pandas as pd
import torch
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from transformers import BertForSequenceClassification, BertTokenizer

from biosemioticai.data import HumorDataset


def evaluate(model_path: str, data_path: str, batch_size: int = 16) -> dict:
    """Evaluate model on test data."""
    device = "cuda" if torch.cuda.is_available() else "cpu"

    print(f"Loading model from {model_path}...")
    tokenizer = BertTokenizer.from_pretrained(model_path)
    model = BertForSequenceClassification.from_pretrained(model_path)
    model.to(device)
    model.eval()

    print(f"Loading data from {data_path}...")
    dataset = HumorDataset(data_path, tokenizer)
    loader = torch.utils.data.DataLoader(dataset, batch_size=batch_size)

    all_preds = []
    all_labels = []

    print("Running evaluation...")
    for batch in loader:
        inputs = {k: v.to(device) for k, v in batch.items() if k != "label"}
        labels = batch["label"].to(device)

        with torch.no_grad():
            outputs = model(**inputs)
            preds = torch.argmax(outputs.logits, dim=-1)

        all_preds.extend(preds.cpu().numpy())
        all_labels.extend(labels.cpu().numpy())

    metrics = {
        "accuracy": accuracy_score(all_labels, all_preds),
        "f1": f1_score(all_labels, all_preds, average="binary"),
        "precision": precision_score(all_labels, all_preds, average="binary"),
        "recall": recall_score(all_labels, all_preds, average="binary"),
    }

    return metrics


def main():
    parser = argparse.ArgumentParser(description="Evaluate biosemiotic classifier")
    parser.add_argument("--model", required=True, help="Path to model directory")
    parser.add_argument("--data", required=True, help="Path to test CSV")
    parser.add_argument("--batch-size", type=int, default=16, help="Batch size")
    parser.add_argument("--output", help="Output JSON file for metrics")
    args = parser.parse_args()

    metrics = evaluate(args.model, args.data, args.batch_size)

    print("\n=== Results ===")
    for name, value in metrics.items():
        print(f"{name}: {value:.4f}")

    if args.output:
        Path(args.output).write_text(json.dumps(metrics, indent=2))
        print(f"\nSaved metrics to {args.output}")


if __name__ == "__main__":
    main()
