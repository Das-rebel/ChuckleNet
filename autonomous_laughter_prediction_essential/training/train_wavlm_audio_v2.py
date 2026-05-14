#!/usr/bin/env python3
"""
Train WavLM-Base+ laughter detection with on-the-fly audio loading.
No pre-extraction needed — loads MP3 segments on demand with caching.

Usage:
  # Phase A: Frozen encoder (fast baseline)
  python training/train_wavlm_audio_v2.py --phase A --max-samples 50000 --epochs 3

  # Phase B: Partial unfreeze (more data)
  python training/train_wavlm_audio_v2.py --phase B --max-samples 200000 --epochs 5 \
      --resume experiments/wavlm_v2_phaseA/best.pt

  # Phase C: Full fine-tune (all data)
  python training/train_wavlm_audio_v2.py --phase C --epochs 10 \
      --resume experiments/wavlm_v2_phaseB/best.pt
"""

import json
import os
import sys
import time
import argparse
from pathlib import Path
from collections import Counter
from functools import lru_cache

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR

import librosa
from transformers import WavLMModel, Wav2Vec2FeatureExtractor
from sklearn.metrics import f1_score, precision_score, recall_score

# ── Config ──────────────────────────────────────────────────────────
SR = 16000
MAX_DURATION = 3.0
CACHE_SIZE = 128  # LRU cache for audio files
DEVICE = torch.device("cuda" if torch.cuda.is_available() else
                      "mps" if torch.backends.mps.is_available() else "cpu")


# ── Audio Cache ─────────────────────────────────────────────────────
@lru_cache(maxsize=CACHE_SIZE)
def load_audio_cached(audio_path: str) -> tuple:
    """Load full audio file, cached for repeated segment extraction."""
    try:
        y, sr = librosa.load(audio_path, sr=SR, mono=True)
        return y, sr
    except Exception as e:
        print(f"Error loading {audio_path}: {e}")
        return None, None


def extract_segment(audio_path: str, start: float, end: float, pad_ms: float = 50) -> np.ndarray:
    """Extract audio segment with padding, using cache."""
    y, sr = load_audio_cached(audio_path)
    if y is None:
        return np.zeros(int(0.3 * SR), dtype=np.float32)  # 300ms silence fallback

    pad_s = pad_ms / 1000.0
    start_sample = int(max(0, start - pad_s) * SR)
    end_sample = int(min(len(y) / SR, end + pad_s) * SR)

    if start_sample >= len(y) or end_sample <= start_sample:
        return np.zeros(int(0.3 * SR), dtype=np.float32)

    segment = y[start_sample:end_sample]

    # Pad if too short
    min_samples = int(0.1 * SR)  # 100ms minimum
    if len(segment) < min_samples:
        segment = np.pad(segment, (0, min_samples - len(segment)), mode='constant')

    return segment.astype(np.float32)


# ── Dataset ─────────────────────────────────────────────────────────
class OnTheFlyAudioDataset(Dataset):
    """Loads segments on-the-fly from aligned_segments.jsonl."""

    def __init__(self, segments_file: str, split: str = "train",
                 max_samples: int = 0, val_ratio: float = 0.1):
        self.extractor = Wav2Vec2FeatureExtractor.from_pretrained("microsoft/wavlm-base-plus")

        # Load segments
        print(f"  Loading segments from {segments_file}...")
        self.samples = []
        with open(segments_file) as f:
            for i, line in enumerate(f):
                if max_samples > 0 and i >= max_samples:
                    break
                d = json.loads(line)
                af = d.get("audio_file", "")
                if not af or not os.path.exists(af):
                    continue
                start = d.get("start")
                end = d.get("end")
                if start is None or end is None or end <= start:
                    continue

                self.samples.append({
                    "audio_file": af,
                    "start": start,
                    "end": end,
                    "label": int(d.get("label", 0)) if str(d.get("label", "0")).isdigit() else 0,
                    "word": d.get("word", ""),
                    "video_id": d.get("video_id", ""),
                })

        # Simple split: deterministic by index
        n = len(self.samples)
        n_val = int(n * val_ratio)

        if split == "train":
            self.samples = self.samples[n_val:]
        else:
            self.samples = self.samples[:n_val]

        labels = Counter(s["label"] for s in self.samples)
        print(f"  [{split}] {len(self.samples):,} segments | "
              f"laugh={labels[1]:,} ({100*labels[1]/len(self.samples):.1f}%) | "
              f"no_laugh={labels[0]:,}")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        s = self.samples[idx]
        audio = extract_segment(s["audio_file"], s["start"], s["end"])

        # Wav2Vec2FeatureExtractor expects list of arrays or single array
        inputs = self.extractor(audio, sampling_rate=SR, return_tensors="pt", padding=True)

        return {
            "input_values": inputs.input_values.squeeze(0),
            "attention_mask": inputs.attention_mask.squeeze(0) if "attention_mask" in inputs else None,
            "label": torch.tensor(s["label"], dtype=torch.long),
        }


def collate_fn(batch):
    """Pad variable-length audio to max in batch."""
    input_values = [b["input_values"] for b in batch]
    labels = torch.stack([b["label"] for b in batch])

    max_len = max(x.shape[0] for x in input_values)
    padded = torch.zeros(len(batch), max_len, dtype=torch.float32)
    attention_mask = torch.zeros(len(batch), max_len, dtype=torch.long)

    for i, x in enumerate(input_values):
        padded[i, :x.shape[0]] = x
        attention_mask[i, :x.shape[0]] = 1

    return {
        "input_values": padded,
        "attention_mask": attention_mask,
        "labels": labels,
    }


# ── Model ───────────────────────────────────────────────────────────
class WavLMLaughterClassifier(nn.Module):
    """WavLM encoder → mean pool → MLP → binary classifier."""

    def __init__(self, hidden_size: int = 768, num_classes: int = 2, dropout: float = 0.2):
        super().__init__()
        self.encoder = WavLMModel.from_pretrained("microsoft/wavlm-base-plus")
        self.classifier = nn.Sequential(
            nn.Linear(hidden_size, 256),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(256, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, num_classes),
        )

    def forward(self, input_values, attention_mask=None):
        outputs = self.encoder(input_values=input_values, attention_mask=attention_mask)
        # Simple mean pooling — WavLM handles padding internally
        pooled = outputs.last_hidden_state.mean(dim=1)
        return self.classifier(pooled)

    def freeze_encoder(self):
        for p in self.encoder.parameters():
            p.requires_grad = False

    def unfreeze_top_layers(self, n_layers: int = 4):
        first_unfreeze = self.encoder.config.num_hidden_layers - n_layers
        for i, layer in enumerate(self.encoder.encoder.layers):
            for p in layer.parameters():
                p.requires_grad = (i >= first_unfreeze)

    def unfreeze_all(self):
        for p in self.encoder.parameters():
            p.requires_grad = True


# ── Training ────────────────────────────────────────────────────────
def train_epoch(model, loader, optimizer, criterion, device, scaler=None):
    model.train()
    total_loss = 0
    all_preds, all_labels = [], []

    for batch in loader:
        input_values = batch["input_values"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        labels = batch["labels"].to(device)

        optimizer.zero_grad()

        if scaler:  # Mixed precision
            with torch.cuda.amp.autocast():
                logits = model(input_values, attention_mask)
                loss = criterion(logits, labels)
            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            scaler.step(optimizer)
            scaler.update()
        else:
            logits = model(input_values, attention_mask)
            loss = criterion(logits, labels)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()

        total_loss += loss.item()
        preds = logits.argmax(dim=1)
        all_preds.extend(preds.cpu().tolist())
        all_labels.extend(labels.cpu().tolist())

    f1 = f1_score(all_labels, all_preds, average="binary", zero_division=0)
    return total_loss / len(loader), f1


@torch.no_grad()
def evaluate(model, loader, criterion, device):
    model.eval()
    total_loss = 0
    all_preds, all_labels = [], []

    for batch in loader:
        input_values = batch["input_values"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        labels = batch["labels"].to(device)

        logits = model(input_values, attention_mask)
        loss = criterion(logits, labels)
        total_loss += loss.item()
        preds = logits.argmax(dim=1)
        all_preds.extend(preds.cpu().tolist())
        all_labels.extend(labels.cpu().tolist())

    f1 = f1_score(all_labels, all_preds, average="binary", zero_division=0)
    p = precision_score(all_labels, all_preds, average="binary", zero_division=0)
    r = recall_score(all_labels, all_preds, average="binary", zero_division=0)
    return total_loss / len(loader), f1, p, r


# ── Main ────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Train WavLM laughter classifier (on-the-fly loading)")
    parser.add_argument("--segments-file", default="data/audio_comedy/aligned_segments.jsonl")
    parser.add_argument("--phase", choices=["A", "B", "C"], default="A")
    parser.add_argument("--resume", type=str, default=None)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--pos-weight", type=float, default=5.0)
    parser.add_argument("--max-samples", type=int, default=50000,
                        help="Max segments to load (0=all, but that's 733K)")
    parser.add_argument("--output-dir", default="experiments/wavlm_v2_phaseA")
    parser.add_argument("--num-workers", type=int, default=4)
    parser.add_argument("--fp16", action="store_true", help="Use mixed precision")
    args = parser.parse_args()

    # Map phase to output dir
    if args.output_dir == "experiments/wavlm_v2_phaseA":
        args.output_dir = f"experiments/wavlm_v2_phase{args.phase}"

    os.makedirs(args.output_dir, exist_ok=True)

    print(f"{'='*60}")
    print(f"WavLM Laughter Classifier v2 — Phase {args.phase}")
    print(f"Device: {DEVICE}")
    print(f"Output: {args.output_dir}")
    print(f"{'='*60}")

    # ── Data ──
    print("\nLoading data (on-the-fly, no pre-extraction)...")
    train_ds = OnTheFlyAudioDataset(args.segments_file, split="train",
                                     max_samples=args.max_samples, val_ratio=0.1)
    val_ds = OnTheFlyAudioDataset(args.segments_file, split="val",
                                   max_samples=args.max_samples, val_ratio=0.1)

    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True,
                              collate_fn=collate_fn, num_workers=args.num_workers,
                              pin_memory=True, persistent_workers=True)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False,
                            collate_fn=collate_fn, num_workers=args.num_workers,
                            pin_memory=True, persistent_workers=True)

    # ── Model ──
    print("\nBuilding model...")
    model = WavLMLaughterClassifier().to(DEVICE)

    if args.phase == "A":
        model.freeze_encoder()
        print("Phase A: Frozen encoder + MLP head")
    elif args.phase == "B":
        model.unfreeze_top_layers(4)
        print("Phase B: Top 4 layers unfrozen")
    else:
        model.unfreeze_all()
        print("Phase C: Full fine-tuning")

    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total = sum(p.numel() for p in model.parameters())
    print(f"Trainable: {trainable:,} / {total:,} ({100*trainable/total:.1f}%)")

    if args.resume:
        print(f"Resuming from {args.resume}")
        model.load_state_dict(torch.load(args.resume, map_location=DEVICE))

    # ── Optimizer ──
    optimizer = AdamW(filter(lambda p: p.requires_grad, model.parameters()),
                      lr=args.lr, weight_decay=0.01)
    scheduler = CosineAnnealingLR(optimizer, T_max=args.epochs)
    criterion = nn.CrossEntropyLoss(weight=torch.tensor([1.0, args.pos_weight]).to(DEVICE))
    scaler = torch.cuda.amp.GradScaler() if args.fp16 and DEVICE.type == "cuda" else None

    # ── Train ──
    best_val_f1 = 0.0
    results = []

    for epoch in range(1, args.epochs + 1):
        t0 = time.time()

        train_loss, train_f1 = train_epoch(model, train_loader, optimizer, criterion, DEVICE, scaler)
        val_loss, val_f1, val_p, val_r = evaluate(model, val_loader, criterion, DEVICE)
        scheduler.step()

        elapsed = time.time() - t0
        print(f"\nEpoch {epoch}/{args.epochs} [{elapsed:.0f}s]")
        print(f"  Train  — loss={train_loss:.4f}  F1={train_f1:.4f}")
        print(f"  Val    — loss={val_loss:.4f}  F1={val_f1:.4f}  P={val_p:.4f}  R={val_r:.4f}")

        results.append({
            "epoch": epoch,
            "train_loss": train_loss, "train_f1": train_f1,
            "val_loss": val_loss, "val_f1": val_f1,
            "val_precision": val_p, "val_recall": val_r,
        })

        if val_f1 > best_val_f1:
            best_val_f1 = val_f1
            torch.save(model.state_dict(), os.path.join(args.output_dir, "best.pt"))
            print(f"  ✅ Saved best model (F1={val_f1:.4f})")

    # ── Save ──
    torch.save(model.state_dict(), os.path.join(args.output_dir, "last.pt"))
    with open(os.path.join(args.output_dir, "results.json"), "w") as f:
        json.dump({"phase": args.phase, "best_val_f1": best_val_f1, "epochs": results}, f, indent=2)

    print(f"\n{'='*60}")
    print(f"Training complete! Best val F1: {best_val_f1:.4f}")
    print(f"Model: {args.output_dir}/best.pt")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
