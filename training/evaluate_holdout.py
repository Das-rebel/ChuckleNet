#!/usr/bin/env python3
"""
Held-out Comedian Evaluation Script
====================================
Evaluates a trained XLM-R model on held-out comedian utterances
to determine if F1=0.82 is real generalization or in-distribution overfitting.

Usage:
    python training/evaluate_holdout.py \
        --checkpoint experiments/fusion_v3_phase1/phase1_best.pt \
        --data data/audio_comedy/aligned_utterances.jsonl \
        --holdout data/training/holdout_comedians.txt \
        --output results/holdout_evaluation.json
"""

import argparse
import json
import torch
from pathlib import Path
from transformers import XLMRobertaTokenizer, XLMRobertaForSequenceClassification
from sklearn.metrics import f1_score, precision_recall_fscore_support
import numpy as np

# Comedian IDs to hold out (from data/training/holdout_comedians.txt)
HOLDOUT_COMEDIANS = {
    "BFIHCzw3itk",  # Bill Burr
    "BAD4askmGgk",  # Dave Chappelle  
    "1Nb3_os4RSA",  # Russell Peters
}


def load_holdout_set(holdout_file: str) -> set:
    """Load held-out comedian IDs from file."""
    holdout_ids = set()
    with open(holdout_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                # Format: video_id [count] [positive]
                parts = line.split()
                if parts:
                    holdout_ids.add(parts[0])
    return holdout_ids


def load_data(data_file: str, holdout_ids: set):
    """Load utterances, splitting into holdout and remaining sets."""
    holdout_data = []
    remaining_data = []
    
    with open(data_file) as f:
        for line in f:
            d = json.loads(line)
            video_id = d.get("video_id", "")
            
            # Reconstruct word-level example from utterance
            words = d.get("text", "").split()
            n_positive = d.get("n_positive_words", 0)
            
            # Binary label: if any positive words, label=1
            label = 1 if n_positive > 0 else 0
            
            example = {
                "video_id": video_id,
                "words": words,
                "label": label,
                "n_positive": n_positive,
                "utterance_id": d.get("utterance_id", "")
            }
            
            if video_id in holdout_ids:
                holdout_data.append(example)
            else:
                remaining_data.append(example)
    
    return holdout_data, remaining_data


def evaluate_model(model, tokenizer, examples, device="cuda"):
    """Run model on examples and compute predictions."""
    model.eval()
    predictions = []
    labels = []
    
    for ex in examples:
        words = ex["words"]
        label = ex["label"]
        
        # Tokenize (simulate word-level with [CLS] word embedding)
        text = " ".join(words[:128])  # Truncate to 128 tokens
        
        encoding = tokenizer(
            text,
            truncation=True,
            max_length=128,
            padding="max_length",
            return_tensors="pt"
        )
        
        input_ids = encoding["input_ids"].to(device)
        attention_mask = encoding["attention_mask"].to(device)
        
        with torch.no_grad():
            outputs = model(input_ids=input_ids, attention_mask=attention_mask)
            logits = outputs.logits
            pred = torch.argmax(logits, dim=-1).item()
        
        predictions.append(pred)
        labels.append(label)
    
    return np.array(predictions), np.array(labels)


def compute_metrics(predictions, labels):
    """Compute F1, precision, recall with IoU-style F1."""
    f1 = f1_score(labels, predictions, average="binary")
    precision, recall, _ = precision_recall_fscore_support(
        labels, predictions, average="binary", zero_division=0
    )
    
    # IoU-style F1 (Jaccard-inspired)
    tp = np.sum((predictions == 1) & (labels == 1))
    fp = np.sum((predictions == 1) & (labels == 0))
    fn = np.sum((predictions == 0) & (labels == 1))
    
    iou_f1 = 2 * tp / (2 * tp + fp + fn) if (tp + fp + fn) > 0 else 0
    
    return {
        "f1": float(f1),
        "precision": float(precision),
        "recall": float(recall),
        "iou_f1": float(iou_f1),
        "tp": int(tp),
        "fp": int(fp),
        "fn": int(fn),
        "n_positive": int(np.sum(labels)),
        "n_negative": int(len(labels) - np.sum(labels))
    }


def main():
    parser = argparse.ArgumentParser(description="Evaluate on held-out comedians")
    parser.add_argument("--checkpoint", required=True, help="Path to model checkpoint")
    parser.add_argument("--data", required=True, help="Path to aligned_utterances.jsonl")
    parser.add_argument("--holdout", required=True, help="Path to holdout_comedians.txt")
    parser.add_argument("--output", required=True, help="Output JSON path")
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    args = parser.parse_args()
    
    # Load holdout IDs
    holdout_ids = load_holdout_set(args.holdout)
    print(f"Loaded {len(holdout_ids)} held-out comedian IDs")
    
    # Load data
    holdout_data, remaining_data = load_data(args.data, holdout_ids)
    print(f"Holdout set: {len(holdout_data)} utterances")
    print(f"Remaining: {len(remaining_data)} utterances")
    
    # Count positives
    holdout_pos = sum(1 for d in holdout_data if d["label"] == 1)
    remaining_pos = sum(1 for d in remaining_data if d["label"] == 1)
    print(f"Holdout positives: {holdout_pos} ({holdout_pos/len(holdout_data)*100:.1f}%)")
    print(f"Remaining positives: {remaining_pos} ({remaining_pos/len(remaining_data)*100:.1f}%)")
    
    # Load model
    print(f"\nLoading model from {args.checkpoint}...")
    device = torch.device(args.device)
    
    tokenizer = XLMRobertaTokenizer.from_pretrained("xlm-roberta-base")
    model = XLMRobertaForSequenceClassification.from_pretrained(
        "xlm-roberta-base",
        num_labels=2
    )
    
    # Load checkpoint (adjust keys based on training script)
    state_dict = torch.load(args.checkpoint, map_location=device)
    model.load_state_dict(state_dict)
    model.to(device)
    
    # Evaluate on holdout set
    print("\nEvaluating on holdout set...")
    holdout_preds, holdout_labels = evaluate_model(model, tokenizer, holdout_data, device)
    holdout_metrics = compute_metrics(holdout_preds, holdout_labels)
    
    print(f"\nHoldout Results:")
    print(f"  F1: {holdout_metrics['f1']:.4f}")
    print(f"  IoU-F1: {holdout_metrics['iou_f1']:.4f}")
    print(f"  Precision: {holdout_metrics['precision']:.4f}")
    print(f"  Recall: {holdout_metrics['recall']:.4f}")
    
    # Evaluate on remaining (in-distribution) set
    print("\nEvaluating on remaining (in-distribution) set...")
    remaining_preds, remaining_labels = evaluate_model(model, tokenizer, remaining_data, device)
    remaining_metrics = compute_metrics(remaining_preds, remaining_labels)
    
    print(f"\nIn-Distribution Results:")
    print(f"  F1: {remaining_metrics['f1']:.4f}")
    print(f"  IoU-F1: {remaining_metrics['iou_f1']:.4f}")
    print(f"  Precision: {remaining_metrics['precision']:.4f}")
    print(f"  Recall: {remaining_metrics['recall']:.4f}")
    
    # Compute gap
    f1_gap = holdout_metrics['f1'] - remaining_metrics['f1']
    
    # Save results
    results = {
        "holdout_comedians": list(holdout_ids),
        "holdout_set": {
            "n_utterances": len(holdout_data),
            "n_positive": holdout_metrics["n_positive"],
            "n_negative": holdout_metrics["n_negative"],
            "f1": holdout_metrics['f1'],
            "iou_f1": holdout_metrics['iou_f1'],
            "precision": holdout_metrics['precision'],
            "recall": holdout_metrics['recall'],
        },
        "in_distribution": {
            "n_utterances": len(remaining_data),
            "n_positive": remaining_metrics["n_positive"],
            "n_negative": remaining_metrics["n_negative"],
            "f1": remaining_metrics['f1'],
            "iou_f1": remaining_metrics['iou_f1'],
            "precision": remaining_metrics['precision'],
            "recall": remaining_metrics['recall'],
        },
        "f1_gap": f1_gap,
        "conclusion": (
            "MODEL GENERALIZES" if f1_gap > -0.05 else "MODEL OVERFITS TO IN-DISTRIBUTION"
        )
    }
    
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to {output_path}")
    print(f"Conclusion: {results['conclusion']}")
    print(f"F1 Gap (holdout - in-dist): {f1_gap:.4f}")
    
    return results


if __name__ == "__main__":
    main()