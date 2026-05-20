#!/usr/bin/env python3
"""
Train XLM-R word-level laughter detection on the combined_multilingual dataset.

Sequence labeling approach: predict per-token laughter label using XLM-R
with context window, positive class weighting, and unfreezing of top layers.

Data: data/combined_multilingual/{train,valid,test}.jsonl
Each example: {"words": [...], "labels": [0|1, ...], "language": "en"|"zh"|"hi", ...}
"""

import os
import sys
import json
import time
import random
import argparse
from collections import defaultdict
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from transformers import AutoModel, AutoTokenizer, get_linear_schedule_with_warmup
from torch.optim import AdamW
from sklearn.metrics import f1_score, precision_score, recall_score

# ─── Config ───────────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "combined_multilingual"
MODEL_NAME = "xlm-roberta-base"  # cached locally
SEED = 42


def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def log(msg):
    print(msg, flush=True)


# ─── Dataset ──────────────────────────────────────────────────────────────────

class WordLevelSequenceDataset(Dataset):
    """Token-level sequence labeling dataset from word-level JSONL."""

    def __init__(self, examples, tokenizer, max_length=128):
        self.examples = examples
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.examples)

    def __getitem__(self, idx):
        ex = self.examples[idx]
        words = ex["words"]
        labels = ex["labels"]

        # Tokenize word-by-word to maintain alignment
        word_tokens = []
        word_labels = []
        for word, label in zip(words, labels):
            tokens = self.tokenizer.tokenize(word)
            if not tokens:
                tokens = [self.tokenizer.unk_token]
            # Label only the first subword token; rest get -100 (ignored in loss)
            word_tokens.extend(tokens)
            word_labels.append(label)
            word_labels.extend([-100] * (len(tokens) - 1))

        # Truncate
        max_content = self.max_length - 2  # [CLS] and [SEP]
        if len(word_tokens) > max_content:
            word_tokens = word_tokens[:max_content]
            word_labels = word_labels[:max_content]

        # Build input with special tokens
        input_ids = (
            [self.tokenizer.cls_token_id]
            + self.tokenizer.convert_tokens_to_ids(word_tokens)
            + [self.tokenizer.sep_token_id]
        )
        attention_mask = [1] * len(input_ids)
        label_ids = [-100] + word_labels + [-100]  # -100 for [CLS] and [SEP]

        # Pad
        pad_len = self.max_length - len(input_ids)
        input_ids += [self.tokenizer.pad_token_id] * pad_len
        attention_mask += [0] * pad_len
        label_ids += [-100] * pad_len

        return {
            "input_ids": torch.tensor(input_ids, dtype=torch.long),
            "attention_mask": torch.tensor(attention_mask, dtype=torch.long),
            "labels": torch.tensor(label_ids, dtype=torch.long),
            "language": ex.get("language", "unknown"),
        }


# ─── Model ────────────────────────────────────────────────────────────────────

class XLMRSequenceLabeler(nn.Module):
    """XLM-R for token classification with optional layer unfreezing."""

    def __init__(self, model_name=MODEL_NAME, num_labels=2, unfreeze_last_n=0, dropout=0.1):
        super().__init__()
        self.encoder = AutoModel.from_pretrained(model_name)
        self.dropout = nn.Dropout(dropout)
        self.classifier = nn.Linear(self.encoder.config.hidden_size, num_labels)

        # Freeze all encoder layers first
        for param in self.encoder.parameters():
            param.requires_grad = False

        # Unfreeze last N transformer layers + embeddings if requested
        if unfreeze_last_n > 0:
            # Unfreeze the last N encoder layers
            encoder_layers = self.encoder.encoder.layer
            n_layers = len(encoder_layers)
            for i in range(max(0, n_layers - unfreeze_last_n), n_layers):
                for param in encoder_layers[i].parameters():
                    param.requires_grad = True
            log(f"  Unfroze last {min(unfreeze_last_n, n_layers)} / {n_layers} encoder layers")

    def forward(self, input_ids, attention_mask):
        outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        sequence_output = outputs.last_hidden_state  # (batch, seq_len, hidden)
        sequence_output = self.dropout(sequence_output)
        logits = self.classifier(sequence_output)  # (batch, seq_len, num_labels)
        return logits


# ─── Metrics ──────────────────────────────────────────────────────────────────

def compute_metrics(all_labels, all_preds, all_langs=None):
    """Compute token-level metrics, ignoring -100."""
    # Filter out ignored positions
    mask = np.array(all_labels) != -100
    filtered_labels = np.array(all_labels)[mask]
    filtered_preds = np.array(all_preds)[mask]

    if len(filtered_labels) == 0 or filtered_labels.sum() == 0:
        return {"f1": 0.0, "precision": 0.0, "recall": 0.0, "support": int(mask.sum())}

    metrics = {
        "f1": f1_score(filtered_labels, filtered_preds, pos_label=1, zero_division=0),
        "precision": precision_score(filtered_labels, filtered_preds, pos_label=1, zero_division=0),
        "recall": recall_score(filtered_labels, filtered_preds, pos_label=1, zero_division=0),
        "support": int(mask.sum()),
        "pos_count": int(filtered_labels.sum()),
        "pred_pos_count": int(filtered_preds.sum()),
    }

    # Per-language metrics
    if all_langs is not None:
        lang_metrics = {}
        for lang in sorted(set(all_langs)):
            lang_mask = np.array([l == lang for l in all_langs]) & mask
            if lang_mask.sum() == 0:
                continue
            lang_labels = np.array(all_labels)[lang_mask]
            lang_preds = np.array(all_preds)[lang_mask]
            if lang_labels.sum() == 0:
                continue
            lang_metrics[lang] = {
                "f1": f1_score(lang_labels, lang_preds, pos_label=1, zero_division=0),
                "support": int(lang_mask.sum()),
                "pos_count": int(lang_labels.sum()),
            }
        metrics["per_language"] = lang_metrics

    return metrics


# ─── Training ─────────────────────────────────────────────────────────────────

def train_epoch(model, dataloader, optimizer, scheduler, device, pos_weight):
    model.train()
    loss_fn = nn.CrossEntropyLoss(
        weight=torch.tensor([1.0, pos_weight], device=device),
        ignore_index=-100,
    )
    total_loss = 0
    all_preds, all_labels, all_langs = [], [], []

    for step, batch in enumerate(dataloader):
        optimizer.zero_grad()
        input_ids = batch["input_ids"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        labels = batch["labels"].to(device)

        logits = model(input_ids, attention_mask)  # (B, seq_len, 2)
        loss = loss_fn(logits.view(-1, 2), labels.view(-1))
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        scheduler.step()

        total_loss += loss.item()
        preds = logits.argmax(dim=-1).cpu().numpy().flatten()
        lbls = labels.cpu().numpy().flatten()
        langs = []
        for lang in batch["language"]:
            langs.extend([lang] * labels.shape[1])
        all_preds.extend(preds.tolist())
        all_labels.extend(lbls.tolist())
        all_langs.extend(langs)

        if (step + 1) % 100 == 0:
            log(f"    Step {step+1}/{len(dataloader)}, loss={loss.item():.4f}")

    avg_loss = total_loss / max(len(dataloader), 1)
    metrics = compute_metrics(all_labels, all_preds, all_langs)
    return avg_loss, metrics


@torch.no_grad()
def evaluate(model, dataloader, device):
    model.eval()
    all_preds, all_labels, all_langs = [], [], []

    for batch in dataloader:
        input_ids = batch["input_ids"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        labels = batch["labels"]

        logits = model(input_ids, attention_mask)
        preds = logits.argmax(dim=-1).cpu().numpy().flatten()
        lbls = labels.numpy().flatten()
        langs = []
        for lang in batch["language"]:
            langs.extend([lang] * labels.shape[1])

        all_preds.extend(preds.tolist())
        all_labels.extend(lbls.tolist())
        all_langs.extend(langs)

    return compute_metrics(all_labels, all_preds, all_langs)


# ─── Data Loading ─────────────────────────────────────────────────────────────

def load_jsonl(path):
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def main():
    parser = argparse.ArgumentParser(description="Train XLM-R on combined_multilingual")
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--lr", type=float, default=5e-5)
    parser.add_argument("--max-length", type=int, default=128)
    parser.add_argument("--pos-weight", type=float, default=5.0)
    parser.add_argument("--unfreeze", type=int, default=4, help="Unfreeze last N encoder layers")
    parser.add_argument("--output-dir", type=str, default=None)
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()

    set_seed(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Output dir
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = PROJECT_ROOT / "experiments" / f"xlmr_combined_pos{int(args.pos_weight)}_uf{args.unfreeze}"
    output_dir.mkdir(parents=True, exist_ok=True)

    log("=" * 60)
    log("XLM-R COMBINED MULTILINGUAL TRAINING")
    log("=" * 60)
    log(f"  Device: {device}")
    log(f"  Output: {output_dir}")
    log(f"  Config: epochs={args.epochs}, bs={args.batch_size}, lr={args.lr}")
    log(f"  pos_weight={args.pos_weight}, unfreeze={args.unfreeze}, max_len={args.max_length}")

    # Load data
    log("\nLoading data...")
    train_data = load_jsonl(DATA_DIR / "train.jsonl")
    valid_data = load_jsonl(DATA_DIR / "valid.jsonl")
    test_data = load_jsonl(DATA_DIR / "test.jsonl")
    log(f"  Train: {len(train_data)}, Valid: {len(valid_data)}, Test: {len(test_data)}")

    # Quick stats
    for name, data in [("train", train_data), ("valid", valid_data), ("test", test_data)]:
        pos = sum(sum(1 for l in e["labels"] if l == 1) for e in data)
        total = sum(len(e["labels"]) for e in data)
        langs = defaultdict(int)
        for e in data:
            langs[e.get("language", "?")] += 1
        log(f"  {name}: {total} tokens, {pos} positive ({pos/total:.1%}), langs={dict(langs)}")

    # Tokenizer & model
    log("\nLoading XLM-R...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = XLMRSequenceLabeler(
        model_name=MODEL_NAME,
        num_labels=2,
        unfreeze_last_n=args.unfreeze,
    ).to(device)

    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total_params = sum(p.numel() for p in model.parameters())
    log(f"  Trainable: {trainable:,} / {total_params:,} params ({trainable/total_params:.1%})")

    # Datasets & loaders
    train_dataset = WordLevelSequenceDataset(train_data, tokenizer, args.max_length)
    valid_dataset = WordLevelSequenceDataset(valid_data, tokenizer, args.max_length)
    test_dataset = WordLevelSequenceDataset(test_data, tokenizer, args.max_length)

    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True, drop_last=False)
    valid_loader = DataLoader(valid_dataset, batch_size=args.batch_size)
    test_loader = DataLoader(test_dataset, batch_size=args.batch_size)

    # Optimizer
    optimizer = AdamW(
        [p for p in model.parameters() if p.requires_grad],
        lr=args.lr,
        weight_decay=0.01,
    )
    total_steps = len(train_loader) * args.epochs
    scheduler = get_linear_schedule_with_warmup(
        optimizer,
        num_warmup_steps=int(total_steps * 0.1),
        num_training_steps=total_steps,
    )

    # Training loop
    best_val_f1 = 0
    best_state = None
    history = []

    log(f"\nTraining for {args.epochs} epochs ({total_steps} steps)...")
    t0 = time.time()

    for epoch in range(args.epochs):
        ep_start = time.time()
        train_loss, train_metrics = train_epoch(
            model, train_loader, optimizer, scheduler, device, args.pos_weight
        )
        val_metrics = evaluate(model, valid_loader, device)

        ep_time = time.time() - ep_start
        log(f"\nEpoch {epoch+1}/{args.epochs} ({ep_time:.1f}s)")
        log(f"  Train: loss={train_loss:.4f}, F1={train_metrics['f1']:.4f}, "
            f"P={train_metrics['precision']:.4f}, R={train_metrics['recall']:.4f}")
        log(f"  Valid: F1={val_metrics['f1']:.4f}, "
            f"P={val_metrics['precision']:.4f}, R={val_metrics['recall']:.4f}")

        if "per_language" in val_metrics:
            for lang, lm in sorted(val_metrics["per_language"].items()):
                log(f"    {lang}: F1={lm['f1']:.4f} (n={lm['support']}, pos={lm['pos_count']})")

        record = {
            "epoch": epoch + 1,
            "train_loss": train_loss,
            "train_f1": train_metrics["f1"],
            "val_f1": val_metrics["f1"],
            "val_precision": val_metrics["precision"],
            "val_recall": val_metrics["recall"],
        }
        history.append(record)

        if val_metrics["f1"] > best_val_f1:
            best_val_f1 = val_metrics["f1"]
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
            log(f"  ★ New best val F1: {best_val_f1:.4f}")

    total_time = time.time() - t0
    log(f"\nTraining complete in {total_time:.1f}s")

    # Final evaluation on best model
    if best_state is None:
        best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}

    model.load_state_dict(best_state)
    final_val = evaluate(model, valid_loader, device)
    final_test = evaluate(model, test_loader, device)

    log("\n" + "=" * 60)
    log("FINAL RESULTS (Best Model)")
    log("=" * 60)
    log(f"  Validation F1: {final_val['f1']:.4f}  P={final_val['precision']:.4f}  R={final_val['recall']:.4f}")
    log(f"  Test F1:       {final_test['f1']:.4f}  P={final_test['precision']:.4f}  R={final_test['recall']:.4f}")

    if "per_language" in final_test:
        log("\n  Per-language test F1:")
        for lang, lm in sorted(final_test["per_language"].items()):
            log(f"    {lang}: F1={lm['f1']:.4f} (pos={lm['pos_count']})")

    # Save
    torch.save(best_state, output_dir / "best_model.pt")
    log(f"\n  Model saved: {output_dir / 'best_model.pt'}")

    summary = {
        "config": {
            "epochs": args.epochs,
            "batch_size": args.batch_size,
            "lr": args.lr,
            "pos_weight": args.pos_weight,
            "unfreeze": args.unfreeze,
            "max_length": args.max_length,
            "seed": args.seed,
            "model_name": MODEL_NAME,
        },
        "data": {
            "train": len(train_data),
            "valid": len(valid_data),
            "test": len(test_data),
        },
        "best_val_f1": best_val_f1,
        "final_val": {k: v for k, v in final_val.items() if k != "per_language"},
        "final_test": {k: v for k, v in final_test.items() if k != "per_language"},
        "per_language_test": final_test.get("per_language", {}),
        "history": history,
        "training_time_s": total_time,
    }
    with open(output_dir / "training_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    log(f"  Summary saved: {output_dir / 'training_summary.json'}")
    log("\nDone!")


if __name__ == "__main__":
    main()
