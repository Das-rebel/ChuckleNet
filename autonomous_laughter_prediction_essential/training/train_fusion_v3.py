#!/usr/bin/env python3
"""
Three-phase training script for WavLM + XLM-R fusion.

Phase 1: Text-only baseline (XLM-R → classifier)
Phase 2: Frozen XLM-R, train audio_proj + gate + classifier
Phase 3: Joint fine-tune (unfreeze top 2 XLM-R layers)

Usage:
    # Phase 1: Text-only baseline
    python training/train_fusion_v3.py --phase 1 --epochs 5

    # Phase 2: Frozen text, train fusion
    python training/train_fusion_v3.py --phase 2 --epochs 10 --resume checkpoints/phase1_best.pt

    # Phase 3: Joint fine-tune
    python training/train_fusion_v3.py --phase 3 --epochs 5 --resume checkpoints/phase2_best.pt

    # 5-fold cross-validation
    python training/train_fusion_v3.py --phase 3 --cv 5
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.optim import AdamW
from torch.utils.data import DataLoader, Subset
from sklearn.metrics import f1_score, precision_score, recall_score
from transformers import get_scheduler, get_linear_schedule_with_warmup

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dataset_utterance_multimodal import (
    UtteranceMultimodalDataset,
    collate_fn,
    create_video_splits,
    create_group_kfold,
)
from model_wavlm_xlmr_fusion import (
    WavLMXLMRFusionModel,
    FusionModelConfig,
    create_model,
)


def train_epoch(
    model: nn.Module,
    dataloader: DataLoader,
    optimizer: torch.optim.Optimizer,
    scheduler,
    device: torch.device,
    phase: int = 3,
    pos_weight: float = 2.0,
    max_grad_norm: float = 1.0,
):
    """Train for one epoch."""
    model.train()
    total_loss = 0
    all_preds = []
    all_labels = []
    gate_stats_list = []
    
    # Class weights: [neg, pos]
    class_weights = torch.tensor([1.0, pos_weight], device=device)
    criterion = nn.CrossEntropyLoss(weight=class_weights)
    
    for batch_idx, batch in enumerate(dataloader):
        input_ids = batch["input_ids"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        audio_emb = batch["audio_embedding"].to(device)
        labels = batch["labels"].to(device)
        
        # Forward
        outputs = model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            audio_embeddings=audio_emb,
            phase=phase,
            return_gate_stats=True,
        )
        
        logits = outputs["logits"]
        loss = criterion(logits, labels)
        
        # Backward
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_grad_norm)
        optimizer.step()
        scheduler.step()
        optimizer.zero_grad()
        
        # Track metrics
        total_loss += loss.item()
        preds = logits.argmax(dim=-1).cpu().numpy()
        all_preds.extend(preds)
        all_labels.extend(labels.cpu().numpy())
        
        if "gate_stats" in outputs:
            gs = outputs["gate_stats"]
            gate_stats_list.append({
                "gate_mean": gs["gate_mean"].item() if torch.is_tensor(gs["gate_mean"]) else gs["gate_mean"],
                "gate_std": gs["gate_std"].item() if torch.is_tensor(gs["gate_std"]) else gs["gate_std"],
            })
    
    avg_loss = total_loss / len(dataloader)
    f1 = f1_score(all_labels, all_preds, zero_division=0)
    
    # Average gate stats
    if gate_stats_list and phase > 1:
        avg_gate_mean = np.mean([g["gate_mean"] for g in gate_stats_list])
        avg_gate_std = np.mean([g["gate_std"] for g in gate_stats_list])
    else:
        avg_gate_mean = 0.0
        avg_gate_std = 0.0
    
    return {
        "loss": avg_loss,
        "f1": f1,
        "gate_mean": avg_gate_mean,
        "gate_std": avg_gate_std,
    }


@torch.no_grad()
def evaluate(
    model: nn.Module,
    dataloader: DataLoader,
    device: torch.device,
    phase: int = 3,
    pos_weight: float = 2.0,
):
    """Evaluate model."""
    model.eval()
    all_preds = []
    all_labels = []
    all_logits = []
    gate_stats_list = []
    
    class_weights = torch.tensor([1.0, pos_weight], device=device)
    criterion = nn.CrossEntropyLoss(weight=class_weights)
    total_loss = 0
    
    for batch in dataloader:
        input_ids = batch["input_ids"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        audio_emb = batch["audio_embedding"].to(device)
        labels = batch["labels"].to(device)
        
        outputs = model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            audio_embeddings=audio_emb,
            phase=phase,
            return_gate_stats=True,
        )
        
        logits = outputs["logits"]
        loss = criterion(logits, labels)
        total_loss += loss.item()
        
        preds = logits.argmax(dim=-1).cpu().numpy()
        all_preds.extend(preds)
        all_labels.extend(labels.cpu().numpy())
        all_logits.extend(logits.softmax(dim=-1)[:, 1].cpu().numpy())
        
        if "gate_stats" in outputs:
            gs = outputs["gate_stats"]
            gate_stats_list.append({
                "gate_mean": gs["gate_mean"].item() if torch.is_tensor(gs["gate_mean"]) else gs["gate_mean"],
                "gate_std": gs["gate_std"].item() if torch.is_tensor(gs["gate_std"]) else gs["gate_std"],
            })
    
    f1 = f1_score(all_labels, all_preds, zero_division=0)
    precision = precision_score(all_labels, all_preds, zero_division=0)
    recall = recall_score(all_labels, all_preds, zero_division=0)
    
    avg_gate_mean = np.mean([g["gate_mean"] for g in gate_stats_list]) if gate_stats_list else 0
    avg_gate_std = np.mean([g["gate_std"] for g in gate_stats_list]) if gate_stats_list else 0
    
    return {
        "loss": total_loss / len(dataloader),
        "f1": f1,
        "precision": precision,
        "recall": recall,
        "gate_mean": avg_gate_mean,
        "gate_std": avg_gate_std,
        "preds": all_preds,
        "labels": all_labels,
        "logits": all_logits,
    }


def main():
    parser = argparse.ArgumentParser(description="Train WavLM + XLM-R fusion model")
    parser.add_argument("--phase", type=int, required=True, choices=[1, 2, 3],
                       help="Training phase: 1=text-only, 2=frozen fusion, 3=joint")
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--lr", type=float, default=None,
                       help="Learning rate (auto-set per phase if not specified)")
    parser.add_argument("--resume", type=str, default=None,
                       help="Path to checkpoint to resume from")
    parser.add_argument("--cv", type=int, default=0,
                       help="Number of cross-validation folds (0=no CV)")
    parser.add_argument("--device", type=str, default="auto")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-dir", type=str, default="experiments/fusion_v3")
    
    # Data paths
    parser.add_argument("--utterances", type=str,
                       default="data/audio_comedy/aligned_utterances.jsonl")
    parser.add_argument("--embeddings", type=str,
                       default="data/audio_comedy/wavlm_utterance_embeddings.pt")
    parser.add_argument("--label-key", type=str, default="label_any",
                       choices=["label_any", "label_majority"])
    
    # Model params
    parser.add_argument("--fusion-dim", type=int, default=256)
    parser.add_argument("--dropout", type=float, default=0.2)
    parser.add_argument("--freeze-layers", type=int, default=8)
    parser.add_argument("--max-seq-length", type=int, default=128)
    
    args = parser.parse_args()
    
    # Device
    if args.device == "auto":
        device = torch.device("cuda" if torch.cuda.is_available() else
                             "mps" if hasattr(torch.backends, "mps") and torch.backends.mps.is_available() else
                             "cpu")
    else:
        device = torch.device(args.device)
    
    print(f"Using device: {device}")
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Set learning rate per phase
    if args.lr is None:
        lr_map = {1: 2e-5, 2: 1e-3, 3: 5e-6}
        args.lr = lr_map[args.phase]
    
    # Load data
    print(f"\n{'='*70}")
    print(f"PHASE {args.phase}: Training WavLM + XLM-R Fusion")
    print(f"{'='*70}")
    print(f"Epochs: {args.epochs}, LR: {args.lr}, Device: {device}")
    
    dataset = UtteranceMultimodalDataset(
        utterances_path=args.utterances,
        wavlm_embeddings_path=args.embeddings,
        max_seq_length=args.max_seq_length,
        label_key=args.label_key,
        load_embeddings=(args.phase > 1),  # Only load embeddings for phase 2+
    )
    
    # Create splits
    splits = create_video_splits(dataset)
    
    train_dataset = Subset(dataset, splits["train"])
    val_dataset = Subset(dataset, splits["val"])
    test_dataset = Subset(dataset, splits["test"])
    
    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True, collate_fn=collate_fn)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size * 2, shuffle=False, collate_fn=collate_fn)
    test_loader = DataLoader(test_dataset, batch_size=args.batch_size * 2, shuffle=False, collate_fn=collate_fn)
    
    # Compute class weights
    train_labels = [dataset.utterances[i][args.label_key] for i in splits["train"]]
    pos_rate = sum(train_labels) / len(train_labels)
    pos_weight = min((1 - pos_rate) / max(pos_rate, 0.01), 5.0)
    print(f"Class balance: {pos_rate:.3f} positive, pos_weight={pos_weight:.2f}")
    
    # Create model
    config = FusionModelConfig(
        fusion_dim=args.fusion_dim,
        dropout=args.dropout,
        freeze_layers=args.freeze_layers,
        device=str(device),
    )
    model = create_model(config).to(device)
    
    # Resume from checkpoint if specified
    if args.resume:
        print(f"Resuming from {args.resume}")
        state_dict = torch.load(args.resume, map_location=device, weights_only=False)
        model.load_state_dict(state_dict, strict=False)
    
    # Set training phase
    model.set_phase(args.phase)
    
    # Optimizer and scheduler
    optimizer = AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)
    total_steps = len(train_loader) * args.epochs
    scheduler = get_linear_schedule_with_warmup(
        optimizer, num_warmup_steps=int(0.1 * total_steps), num_training_steps=total_steps
    )
    
    # Training loop
    best_val_f1 = 0.0
    best_epoch = 0
    results_history = []
    
    for epoch in range(args.epochs):
        print(f"\n--- Epoch {epoch+1}/{args.epochs} ---")
        
        # Train
        train_metrics = train_epoch(
            model, train_loader, optimizer, scheduler, device,
            phase=args.phase, pos_weight=pos_weight,
        )
        
        # Validate
        val_metrics = evaluate(
            model, val_loader, device,
            phase=args.phase, pos_weight=pos_weight,
        )
        
        print(f"  Train Loss: {train_metrics['loss']:.4f}, F1: {train_metrics['f1']:.4f}")
        print(f"  Val   Loss: {val_metrics['loss']:.4f}, F1: {val_metrics['f1']:.4f}, "
              f"P: {val_metrics['precision']:.4f}, R: {val_metrics['recall']:.4f}")
        if args.phase > 1:
            print(f"  Gate: mean={val_metrics['gate_mean']:.3f}, std={val_metrics['gate_std']:.3f}")
        
        # Save best model
        if val_metrics["f1"] > best_val_f1:
            best_val_f1 = val_metrics["f1"]
            best_epoch = epoch + 1
            save_path = os.path.join(args.output_dir, f"phase{args.phase}_best.pt")
            torch.save(model.state_dict(), save_path)
            print(f"  ✅ New best! Saved to {save_path}")
        
        results_history.append({
            "epoch": epoch + 1,
            "phase": args.phase,
            "train_loss": train_metrics["loss"],
            "train_f1": train_metrics["f1"],
            "val_loss": val_metrics["loss"],
            "val_f1": val_metrics["f1"],
            "val_precision": val_metrics["precision"],
            "val_recall": val_metrics["recall"],
            "gate_mean": val_metrics.get("gate_mean", 0),
            "gate_std": val_metrics.get("gate_std", 0),
        })
    
    # Final evaluation on test set
    print(f"\n{'='*70}")
    print("FINAL TEST EVALUATION")
    print(f"{'='*70}")
    
    # Load best model
    best_path = os.path.join(args.output_dir, f"phase{args.phase}_best.pt")
    if os.path.exists(best_path):
        model.load_state_dict(torch.load(best_path, map_location=device, weights_only=False))
    
    test_metrics = evaluate(
        model, test_loader, device,
        phase=args.phase, pos_weight=pos_weight,
    )
    
    print(f"Test F1: {test_metrics['f1']:.4f}")
    print(f"Test Precision: {test_metrics['precision']:.4f}")
    print(f"Test Recall: {test_metrics['recall']:.4f}")
    if args.phase > 1:
        print(f"Gate: mean={test_metrics['gate_mean']:.3f}, std={test_metrics['gate_std']:.3f}")
    
    # Save results
    results = {
        "phase": args.phase,
        "best_val_f1": best_val_f1,
        "best_epoch": best_epoch,
        "test_f1": test_metrics["f1"],
        "test_precision": test_metrics["precision"],
        "test_recall": test_metrics["recall"],
        "history": results_history,
        "config": {
            "fusion_dim": args.fusion_dim,
            "dropout": args.dropout,
            "freeze_layers": args.freeze_layers,
            "lr": args.lr,
            "epochs": args.epochs,
            "batch_size": args.batch_size,
            "label_key": args.label_key,
        },
    }
    
    results_path = os.path.join(args.output_dir, f"phase{args.phase}_results.json")
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to {results_path}")
    
    # Compare with baselines
    print(f"\n{'='*70}")
    print("COMPARISON WITH BASELINES")
    print(f"{'='*70}")
    print(f"  Pause-only (word-level):      F1 = 0.11")
    print(f"  F0+Energy+Pause (word-level): F1 = 0.29")
    print(f"  All 49 acoustic features:       F1 = 0.27")
    print(f"  TF-IDF text (word-level):      F1 = 0.73")
    print(f"  XLM-R text (word-level):      F1 = 0.82")
    print(f"  WavLM audio (utterance):       F1 = {test_metrics['f1']:.4f}")
    
    if test_metrics["f1"] > 0.55:
        print(f"\n✅ WavLM BREAKS THE 0.30 CEILING!")
    elif test_metrics["f1"] > 0.40:
        print(f"\n⚠️ PARTIAL improvement over librosa features")
    else:
        print(f"\n❌ WavLM below target. Need fusion with text.")
    
    return results


if __name__ == "__main__":
    main()