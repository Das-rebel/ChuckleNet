#!/usr/bin/env python3
"""
Fast XLM-R baseline: utterance-level classification with frozen encoder.
Minimal version for quick iteration.

Config: 2000 train examples, batch_size=8, 2 epochs, frozen encoder.

Data: training_format/{train,valid}.jsonl
Output: experiments/xlmr_baseline_retrained/best.pt
"""

import os, sys, json, time, random
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModel, get_linear_schedule_with_warmup
from sklearn.metrics import f1_score, precision_score, recall_score
import numpy as np

# ─── Config ───────────────────────────────────────────────────────────────────
DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "audio_comedy" / "training_format"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "experiments" / "xlmr_baseline_retrained"
MODEL_NAME = "xlm-roberta-base"
MAX_LEN = 128
BATCH_SIZE = 8
EPOCHS = 2
LR = 1e-3
NUM_TRAIN = 2000  # subset for fast iteration
SEED = 42

def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

set_seed(SEED)

def log(msg):
    print(msg, flush=True)


class WordLevelDataset(Dataset):
    """Each example is a window of words with utterance-level label."""
    def __init__(self, examples, tokenizer, max_length=128):
        self.examples = examples
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.examples)

    def __getitem__(self, idx):
        ex = self.examples[idx]
        words = ex.get("words", [])
        label = ex.get("label", 0)

        flat_tokens = []
        for w in words:
            tokens = self.tokenizer.tokenize(w) or [self.tokenizer.unk_token]
            flat_tokens.extend(tokens)

        max_content = self.max_length - 2
        if len(flat_tokens) > max_content:
            flat_tokens = flat_tokens[:max_content]

        input_ids = (
            [self.tokenizer.cls_token_id]
            + self.tokenizer.convert_tokens_to_ids(flat_tokens)
            + [self.tokenizer.sep_token_id]
        )
        attention_mask = [1] * len(input_ids)

        pad_len = self.max_length - len(input_ids)
        input_ids += [self.tokenizer.pad_token_id] * pad_len
        attention_mask += [0] * pad_len

        return {
            "input_ids": torch.tensor(input_ids, dtype=torch.long),
            "attention_mask": torch.tensor(attention_mask, dtype=torch.long),
            "label": torch.tensor(label, dtype=torch.long),
        }


class XLMRClassifier(nn.Module):
    """XLM-R with frozen encoder + trainable classifier head."""
    def __init__(self, model_name="xlm-roberta-base"):
        super().__init__()
        self.encoder = AutoModel.from_pretrained(model_name)
        for p in self.encoder.parameters():
            p.requires_grad = False

        self.proj = nn.Sequential(
            nn.Linear(768, 256),
            nn.GELU(),
            nn.Dropout(0.1),
        )
        self.classifier = nn.Linear(256, 2)

    def forward(self, input_ids, attention_mask):
        out = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        cls = out.last_hidden_state[:, 0, :]
        feat = self.proj(cls)
        return self.classifier(feat)


def load_jsonl(path):
    with open(path) as f:
        return [json.loads(l) for l in f if l.strip()]


def evaluate(model, loader, device):
    model.eval()
    all_preds, all_labels = [], []
    with torch.no_grad():
        for batch in loader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["label"].cpu().numpy()

            logits = model(input_ids, attention_mask)
            preds = logits.argmax(dim=-1).cpu().numpy()

            all_preds.append(preds)
            all_labels.append(labels)

    preds_arr = np.concatenate(all_preds)
    labels_arr = np.concatenate(all_labels)
    f1 = f1_score(labels_arr, preds_arr, average="binary", zero_division=0)
    prec = precision_score(labels_arr, preds_arr, average="binary", zero_division=0)
    rec = recall_score(labels_arr, preds_arr, average="binary", zero_division=0)
    return f1, prec, rec


def main():
    t_start = time.time()

    log(f"\n{'='*60}")
    log("XLM-R Fast Baseline (frozen encoder, 2K examples)")
    log(f"{'='*60}")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    log(f"Device: {device}")
    log(f"Config: bs={BATCH_SIZE}, epochs={EPOCHS}, train_examples={NUM_TRAIN}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # ── Load data ─────────────────────────────────────────────────────────
    log(f"\nLoading data from {DATA_DIR}...")
    train_ex = load_jsonl(DATA_DIR / "train.jsonl")
    valid_ex = load_jsonl(DATA_DIR / "valid.jsonl")
    log(f"Full train: {len(train_ex)}, valid: {len(valid_ex)}")

    # Subset to NUM_TRAIN random examples
    random.shuffle(train_ex)
    train_ex = train_ex[:NUM_TRAIN]

    n_pos = sum(1 for ex in train_ex if ex.get("label", 0) == 1)
    log(f"Train subset: {len(train_ex)} examples, {n_pos} positive ({100*n_pos/len(train_ex):.1f}%)")

    n_pos_val = sum(1 for ex in valid_ex if ex.get("label", 0) == 1)
    log(f"Valid: {len(valid_ex)} examples, {n_pos_val} positive ({100*n_pos_val/len(valid_ex):.1f}%)")

    # ── Tokenize ──────────────────────────────────────────────────────────
    log(f"\nLoading tokenizer: {MODEL_NAME}")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    train_ds = WordLevelDataset(train_ex, tokenizer, MAX_LEN)
    valid_ds = WordLevelDataset(valid_ex, tokenizer, MAX_LEN)

    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True, num_workers=0)
    valid_loader = DataLoader(valid_ds, batch_size=BATCH_SIZE * 2, shuffle=False, num_workers=0)

    # ── Model ─────────────────────────────────────────────────────────────
    log(f"\nLoading model: {MODEL_NAME}")
    model = XLMRClassifier(MODEL_NAME).to(device)

    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total = sum(p.numel() for p in model.parameters())
    log(f"Trainable params: {trainable:,} / {total:,} ({100*trainable/total:.1f}%)")

    optimizer = torch.optim.AdamW(
        [p for p in model.parameters() if p.requires_grad],
        lr=LR, weight_decay=0.01,
    )
    scheduler = get_linear_schedule_with_warmup(
        optimizer,
        num_warmup_steps=len(train_loader),
        num_training_steps=len(train_loader) * EPOCHS,
    )

    pos_w = (len(train_ex) - n_pos) / max(n_pos, 1)
    criterion = nn.CrossEntropyLoss(weight=torch.tensor([1.0, pos_w]).to(device))
    log(f"Positive class weight: {pos_w:.2f}")

    # ── Train ─────────────────────────────────────────────────────────────
    log(f"\n{'='*60}")
    log(f"Training {EPOCHS} epochs, {len(train_loader)} batches/epoch")
    log(f"{'='*60}")

    best_f1 = 0.0

    for epoch in range(EPOCHS):
        ep_start = time.time()
        model.train()
        total_loss = 0

        for step, batch in enumerate(train_loader):
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["label"].to(device)

            optimizer.zero_grad()
            logits = model(input_ids, attention_mask)
            loss = criterion(logits, labels)

            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            scheduler.step()

            total_loss += loss.item()

            if (step + 1) % 100 == 0:
                log(f"  Epoch {epoch+1} Step {step+1}/{len(train_loader)}: loss={total_loss/(step+1):.4f}")

        val_f1, val_prec, val_rec = evaluate(model, valid_loader, device)
        ep_time = time.time() - ep_start
        log(f"\nEpoch {epoch+1}/{EPOCHS} ({ep_time:.0f}s): loss={total_loss/len(train_loader):.4f}")
        log(f"  Val → F1={val_f1:.4f} P={val_prec:.4f} R={val_rec:.4f}")

        if val_f1 > best_f1:
            best_f1 = val_f1
            torch.save({
                "model_state": model.state_dict(),
                "val_f1": best_f1,
                "epoch": epoch,
                "config": {
                    "batch_size": BATCH_SIZE,
                    "epochs": EPOCHS,
                    "lr": LR,
                    "max_len": MAX_LEN,
                    "num_train": len(train_ex),
                    "model_name": MODEL_NAME,
                },
            }, OUTPUT_DIR / "best.pt")
            log(f"  → Saved best checkpoint (F1={best_f1:.4f})")

    total_time = time.time() - t_start
    log(f"\n{'='*60}")
    log(f"✅ Done in {total_time:.0f}s. Best val F1: {best_f1:.4f}")
    log(f"Checkpoint: {OUTPUT_DIR / 'best.pt'}")
    log(f"{'='*60}")

    return best_f1


if __name__ == "__main__":
    main()
