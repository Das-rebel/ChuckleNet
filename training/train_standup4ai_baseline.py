#!/usr/bin/env python3
"""
Train XLM-R baseline on StandUp4AI pre-labeled data (laugh-1.6)

Data: /tmp/standup4ai_dataset/Examples_label/
- -1FrUOEswOk.csv (French)
- 0g7nezWZyfY.csv (English)
- 1xvwYZwm8Ig.csv (English)
- 6JQzl2LlXbQ.csv (Spanish)

Total: ~3,203 words with L=laughter, O=other labels
"""

import os
import sys
import csv
import json
import random
import gc
import time
from pathlib import Path
from collections import defaultdict

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from transformers import AutoModel, AutoTokenizer, get_linear_schedule_with_warmup
from torch.optim import AdamW
from sklearn.metrics import f1_score
import numpy as np

# Force CPU
os.environ["CUDA_VISIBLE_DEVICES"] = ""

# Paths
DATA_DIR = Path("/tmp/standup4ai_dataset/Examples_label")
OUTPUT_DIR = Path("/Users/Subho/autonomous_laughter_prediction_essential/experiments/standup4ai_baseline")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Config - optimized for CPU
MODEL_NAME = "xlm-roberta-base"
MAX_LEN = 16  # Very short since we're classifying single words
BATCH_SIZE = 32
EPOCHS = 3
LR = 5e-5
SEED = 42

# Language mapping
LANG_MAP = {
    "-1FrUOEswOk.csv": "fr",
    "0g7nezWZyfY.csv": "en",
    "1xvwYZwm8Ig.csv": "en",
    "6JQzl2LlXbQ.csv": "es"
}

# Label mapping
LABEL_MAP = {"L": 1, "O": 0}


def log(msg):
    """Print with flush."""
    print(msg)
    sys.stdout.flush()


class StandUp4AIDataset(Dataset):
    """Word-level laughter detection dataset."""

    def __init__(self, samples, tokenizer, max_len=MAX_LEN):
        self.samples = samples
        self.tokenizer = tokenizer
        self.max_len = max_len

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        sample = self.samples[idx]
        word = sample["word"]
        label = sample["label"]

        encoding = self.tokenizer(
            word,
            add_special_tokens=True,
            max_length=self.max_len,
            padding="max_length",
            truncation=True,
            return_tensors="pt"
        )

        return {
            "input_ids": encoding["input_ids"].flatten(),
            "attention_mask": encoding["attention_mask"].flatten(),
            "labels": torch.tensor(label, dtype=torch.long),
            "word": word,
            "language": sample["language"]
        }


class XLMRLaughterClassifier(nn.Module):
    """XLM-R based word-level laughter classifier."""

    def __init__(self, model_name=MODEL_NAME, dropout=0.1):
        super().__init__()
        self.encoder = AutoModel.from_pretrained(model_name)
        self.dropout = nn.Dropout(dropout)
        self.classifier = nn.Linear(768, 2)

    def forward(self, input_ids, attention_mask):
        outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        cls_output = outputs.last_hidden_state[:, 0, :]
        cls_output = self.dropout(cls_output)
        logits = self.classifier(cls_output)
        return logits


def load_csv_data():
    """Load all CSV files."""
    all_samples = []
    lang_counts = defaultdict(int)

    for csv_file in DATA_DIR.glob("*.csv"):
        lang = LANG_MAP.get(csv_file.name, "unknown")
        log(f"Loading {csv_file.name} ({lang})...")

        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                word = row["text"].strip()
                label_str = row["label"].strip()
                if word and label_str in LABEL_MAP:
                    all_samples.append({
                        "word": word,
                        "label": LABEL_MAP[label_str],
                        "language": lang,
                        "source": csv_file.name
                    })
                    lang_counts[lang] += 1

    log(f"\nTotal samples: {len(all_samples)}")
    for lang, count in sorted(lang_counts.items()):
        log(f"  {lang}: {count}")

    return all_samples, lang_counts


def split_data(samples, val_ratio=0.2, seed=SEED):
    """Split data by language."""
    random.seed(seed)

    by_lang = defaultdict(list)
    for s in samples:
        by_lang[s["language"]].append(s)

    train_samples = []
    val_samples = []

    for lang, lang_samples in by_lang.items():
        random.shuffle(lang_samples)
        split_idx = int(len(lang_samples) * (1 - val_ratio))
        train_samples.extend(lang_samples[:split_idx])
        val_samples.extend(lang_samples[split_idx:])

    random.shuffle(train_samples)
    random.shuffle(val_samples)

    log(f"\nSplit: train={len(train_samples)}, val={len(val_samples)}")
    return train_samples, val_samples


def train_epoch(model, dataloader, optimizer, scheduler, device, pos_weight):
    """Train one epoch."""
    model.train()
    total_loss = 0
    all_preds = []
    all_labels = []
    # Use weighted cross-entropy for imbalanced classes
    loss_fn = nn.CrossEntropyLoss(weight=torch.tensor([1.0, pos_weight]).to(device))

    for i, batch in enumerate(dataloader):
        optimizer.zero_grad()

        input_ids = batch["input_ids"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        labels = batch["labels"].to(device)

        logits = model(input_ids, attention_mask)
        loss = loss_fn(logits, labels)

        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        scheduler.step()

        total_loss += loss.item()
        preds = torch.argmax(logits, dim=1).cpu().numpy()
        all_preds.extend(preds)
        all_labels.extend(labels.cpu().numpy())

        if (i + 1) % 20 == 0:
            log(f"  Batch {i+1}/{len(dataloader)}, loss={loss.item():.4f}")

    avg_loss = total_loss / len(dataloader)
    f1 = f1_score(all_labels, all_preds, average="binary", pos_label=1)
    return avg_loss, f1


def evaluate(model, dataloader, device):
    """Evaluate model and return per-language metrics."""
    model.eval()
    all_preds = []
    all_labels = []
    all_langs = []

    with torch.no_grad():
        for batch in dataloader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"].to(device)

            logits = model(input_ids, attention_mask)
            preds = torch.argmax(logits, dim=1).cpu().numpy()

            all_preds.extend(preds)
            all_labels.extend(labels.cpu().numpy())
            all_langs.extend(batch["language"])

    overall_f1 = f1_score(all_labels, all_preds, average="binary", pos_label=1)

    lang_metrics = {}
    for lang in set(all_langs):
        lang_idx = [j for j, l in enumerate(all_langs) if l == lang]
        lang_preds = [all_preds[j] for j in lang_idx]
        lang_labels = [all_labels[j] for j in lang_idx]
        lang_f1 = f1_score(lang_labels, lang_preds, average="binary", pos_label=1)
        lang_metrics[lang] = {"f1": lang_f1, "support": len(lang_idx)}

    return overall_f1, lang_metrics, all_preds, all_labels


def main():
    log("=" * 60)
    log("STANDUP4AI BASELINE TRAINING (XLM-R)")
    log("=" * 60)

    random.seed(SEED)
    np.random.seed(SEED)
    torch.manual_seed(SEED)

    device = torch.device("cpu")
    log(f"Device: {device}\n")

    # Load data
    samples, lang_counts = load_csv_data()

    # Split data
    train_samples, val_samples = split_data(samples)

    # Save split info
    split_info = {
        "train_count": len(train_samples),
        "val_count": len(val_samples),
        "language_counts": dict(lang_counts)
    }
    with open(OUTPUT_DIR / "split_info.json", "w") as f:
        json.dump(split_info, f, indent=2)

    # Initialize tokenizer and model
    log("\nLoading XLM-R tokenizer and model...")
    start_time = time.time()
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = XLMRLaughterClassifier(MODEL_NAME).to(device)
    log(f"Model loaded in {time.time() - start_time:.1f}s")

    # Create datasets
    train_dataset = StandUp4AIDataset(train_samples, tokenizer)
    val_dataset = StandUp4AIDataset(val_samples, tokenizer)

    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE)

    # Optimizer and scheduler
    optimizer = AdamW(model.parameters(), lr=LR)
    total_steps = len(train_loader) * EPOCHS
    scheduler = get_linear_schedule_with_warmup(
        optimizer, num_warmup_steps=total_steps // 10, num_training_steps=total_steps
    )

    # Training loop
    best_val_f1 = 0
    best_model_state = None

    log("\nStarting training...")
    for epoch in range(EPOCHS):
        epoch_start = time.time()
        train_loss, train_f1 = train_epoch(model, train_loader, optimizer, scheduler, device, pos_weight=3.0)
        val_f1, lang_metrics, _, _ = evaluate(model, val_loader, device)

        log(f"\nEpoch {epoch+1}/{EPOCHS} ({time.time() - epoch_start:.1f}s)")
        log(f"  Train Loss: {train_loss:.4f}, Train F1: {train_f1:.4f}")
        log(f"  Val F1: {val_f1:.4f}")

        for lang in sorted(lang_metrics.keys()):
            m = lang_metrics[lang]
            log(f"    {lang}: F1={m['f1']:.4f} (n={m['support']})")

        if val_f1 > best_val_f1:
            best_val_f1 = val_f1
            best_model_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
            log(f"  -> New best! Val F1: {best_val_f1:.4f}")

    if best_model_state is None:
        best_model_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
        log("No improvement found, using final model state")

        gc.collect()

    # Final evaluation
    log("\n" + "=" * 60)
    log("FINAL EVALUATION (Best Model)")
    log("=" * 60)

    model.load_state_dict(best_model_state)
    final_f1, final_lang_metrics, _, _ = evaluate(model, val_loader, device)

    log(f"\nOverall Val F1: {final_f1:.4f}")
    log("\nPer-language F1:")
    for lang in sorted(final_lang_metrics.keys()):
        m = final_lang_metrics[lang]
        status = "✓" if m['f1'] >= 0.70 else "✗"
        log(f"  {status} {lang}: F1={m['f1']:.4f} (n={m['support']})")

    all_lang_ok = all(m['f1'] >= 0.70 for m in final_lang_metrics.values())
    if all_lang_ok and final_f1 >= 0.70:
        log("\n✓ SUCCESS: All languages >= 0.70 F1")
    else:
        log(f"\n✗ Target not met: overall={final_f1:.4f}")

    # Save model
    torch.save(best_model_state, OUTPUT_DIR / "best_model.pt")
    log(f"\nModel saved to: {OUTPUT_DIR / 'best_model.pt'}")

    # Save metrics
    metrics = {
        "overall_val_f1": final_f1,
        "per_language_f1": {lang: m['f1'] for lang, m in final_lang_metrics.items()},
        "best_val_f1": best_val_f1,
        "epochs": EPOCHS,
        "batch_size": BATCH_SIZE,
        "learning_rate": LR
    }
    with open(OUTPUT_DIR / "metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    log(f"\nMetrics saved to: {OUTPUT_DIR / 'metrics.json'}")
    log("\nDone!")


if __name__ == "__main__":
    main()
