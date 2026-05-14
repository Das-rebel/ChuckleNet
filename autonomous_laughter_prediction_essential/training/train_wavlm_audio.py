#!/usr/bin/env python3
"""
Train WavLM-Base+ laughter detection model on extracted audio segments.

Three-phase training:
  Phase A: Frozen WavLM + MLP classifier (quick baseline)
  Phase B: Unfreeze top 4 layers (refinement)
  Phase C: Full fine-tuning (best performance)

Usage:
  # Phase A: Quick baseline
  python training/train_wavlm_audio.py --phase A --epochs 5

  # Phase B: Partial unfreeze
  python training/train_wavlm_audio.py --phase B --epochs 5 --resume experiments/wavlm_phaseA/best.pt

  # Phase C: Full fine-tune
  python training/train_wavlm_audio.py --phase C --epochs 5 --resume experiments/wavlm_phaseB/best.pt
"""

import json
import os
import sys
import time
import argparse
from pathlib import Path
from collections import Counter

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR

import librosa
from transformers import WavLMModel, Wav2Vec2FeatureExtractor
from sklearn.metrics import f1_score, precision_score, recall_score

# ── Config ──────────────────────────────────────────────────────────
SR = 16000
MAX_DURATION = 3.0  # max segment duration in seconds
DEVICE = torch.device("cuda" if torch.cuda.is_available() else
                      "mps" if torch.backends.mps.is_available() else "cpu")


# ── Dataset ─────────────────────────────────────────────────────────
class LaughterAudioDataset(Dataset):
    """Loads extracted WAV clips + labels."""

    def __init__(self, segments_dir: str, split: str = "train", max_samples: int = 0):
        self.segments_dir = Path(segments_dir)
        self.extractor = Wav2Vec2FeatureExtractor.from_pretrained("microsoft/wavlm-base-plus")

        # Collect all WAV files with their metadata
        self.samples = []
        for video_dir in sorted(self.segments_dir.iterdir()):
            if not video_dir.is_dir():
                continue
            for wav_path in sorted(video_dir.glob("*.wav")):
                meta_path = wav_path.with_suffix(".json")
                if meta_path.exists():
                    with open(meta_path) as f:
                        meta = json.load(f)
                    self.samples.append({
                        "wav": str(wav_path),
                        "label": meta.get("label_int", 0),
                        "word": meta.get("word", ""),
                        "duration": meta.get("duration", 0),
                    })

        if max_samples > 0 and len(self.samples) > max_samples:
            self.samples = self.samples[:max_samples]

        labels = Counter(s["label"] for s in self.samples)
        print(f"  [{split}] {len(self.samples):,} segments | "
              f"laugh={labels[1]:,} ({100*labels[1]/len(self.samples):.1f}%) | "
              f"no_laugh={labels[0]:,}")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        s = self.samples[idx]
        try:
            y, _ = librosa.load(s["wav"], sr=SR)
            # Truncate or pad
            max_samples = int(MAX_DURATION * SR)
            if len(y) > max_samples:
                y = y[:max_samples]
        except Exception:
            y = np.zeros(int(0.3 * SR), dtype=np.float32)  # fallback: 300ms silence

        inputs = self.extractor(y, sampling_rate=SR, return_tensors="pt", padding="max_length",
                                max_length=max_samples, truncation=True)
        return {
            "input_values": inputs.input_values.squeeze(0),
            "attention_mask": inputs.attention_mask.squeeze(0) if "attention_mask" in inputs else None,
            "label": torch.tensor(s["label"], dtype=torch.long),
        }


def collate_fn(batch):
    """Pad variable-length audio to max in batch."""
    input_values = [b["input_values"] for b in batch]
    labels = torch.stack([b["label"] for b in batch])

    # Pad to max length in batch
    max_len = max(x.shape[0] for x in input_values)
    padded = torch.zeros(len(batch), max_len, dtype=torch.float32)
    attention_mask = torch.zeros(len(batch), max_len, dtype=torch.long)
    for i, x in enumerate(input_values):
        padded[i, :x.shape[0]] = x
        attention_mask[i, :x.shape[0]] = 1

    return {"input_values": padded, "attention_mask": attention_mask, "labels": labels}


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
        # Mean pool over time dimension
        if attention_mask is not None:
            # Masked mean pooling
            mask_expanded = attention_mask.unsqueeze(-1).float()
            pooled = (outputs.last_hidden_state * mask_expanded).sum(dim=1) / mask_expanded.sum(dim=1).clamp(min=1)
        else:
            pooled = outputs.last_hidden_state.mean(dim=1)
        return self.classifier(pooled)

    def freeze_encoder(self):
        for p in self.encoder.parameters():
            p.requires_grad = False

    def unfreeze_top_layers(self, n_layers: int = 4):
        """Unfreeze the last n transformer layers."""
        first_unfreeze = self.encoder.config.num_hidden_layers - n_layers
        for i, layer in enumerate(self.encoder.encoder.layers):
            for p in layer.parameters():
                p.requires_grad = (i >= first_unfreeze)

    def unfreeze_all(self):
        for p in self.encoder.parameters():
            p.requires_grad = True


# ── Training ────────────────────────────────────────────────────────
def train_epoch(model, loader, optimizer, criterion, device):
    model.train()
    total_loss = 0
    all_preds, all_labels = [], []

    for batch in loader:
        input_values = batch["input_values"].to(device)
        attention_mask = batch["attention_mask"].to(device) if batch["attention_mask"] is not None else None
        labels = batch["labels"].to(device)

        optimizer.zero_grad()
        logits = model(input_values, attention_mask)
        loss = criterion(logits, labels)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()

        total_loss += loss.item()
        preds = logits.argmax(dim=1)
        all_preds.extend(preds.cpu().tolist())
        all_labels.extend(labels.cpu().tolist())

    f1 = f1_score(all_labels, all_preds, average="binary")
    return total_loss / len(loader), f1


@torch.no_grad()
def evaluate(model, loader, criterion, device):
    model.eval()
    total_loss = 0
    all_preds, all_labels = [], []

    for batch in loader:
        input_values = batch["input_values"].to(device)
        attention_mask = batch["attention_mask"].to(device) if batch["attention_mask"] is not None else None
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
    parser = argparse.ArgumentParser(description="Train WavLM laughter classifier")
    parser.add_argument("--segments-dir", default="data/audio_comedy/extracted_clips",
                        help="Directory with extracted WAV clips")
    parser.add_argument("--phase", choices=["A", "B", "C"], default="A",
                        help="A=frozen, B=partial unfreeze, C=full fine-tune")
    parser.add_argument("--resume", type=str, default=None,
                        help="Resume from checkpoint")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--pos-weight", type=float, default=5.0,
                        help="Positive class weight for imbalance")
    parser.add_argument("--max-samples", type=int, default=0,
                        help="Max samples (0=all)")
    parser.add_argument("--output-dir", default="experiments/wavlm_phaseA",
                        help="Output directory")
    parser.add_argument("--num-workers", type=int, default=min(4, os.cpu_count() or 1))
    args = parser.parse_args()

    # Map phase to output dir
    phase_outputs = {"A": "experiments/wavlm_phaseA", "B": "experiments/wavlm_phaseB", "C": "experiments/wavlm_phaseC"}
    if args.output_dir == "experiments/wavlm_phaseA":
        args.output_dir = phase_outputs[args.phase]

    os.makedirs(args.output_dir, exist_ok=True)

    print(f"{'='*60}")
    print(f"WavLM Laughter Classifier — Phase {args.phase}")
    print(f"Device: {DEVICE}")
    print(f"Output: {args.output_dir}")
    print(f"{'='*60}")

    # ── Data ──
    print("\nLoading data...")
    ds = LaughterAudioDataset(args.segments_dir, split="train", max_samples=args.max_samples)

    # Simple 80/20 split
    n = len(ds)
    n_train = int(0.8 * n)
    train_ds = torch.utils.data.Subset(ds, range(n_train))
    val_ds = torch.utils.data.Subset(ds, range(n_train, n))

    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True,
                              collate_fn=collate_fn, num_workers=args.num_workers, pin_memory=True)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False,
                            collate_fn=collate_fn, num_workers=args.num_workers, pin_memory=True)

    # ── Model ──
    print("\nBuilding model...")
    model = WavLMLaughterClassifier().to(DEVICE)

    if args.phase == "A":
        model.freeze_encoder()
        print("Phase A: Frozen encoder")
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
    optimizer = AdamW(filter(lambda p: p.requires_grad, model.parameters()), lr=args.lr, weight_decay=0.01)
    scheduler = CosineAnnealingLR(optimizer, T_max=args.epochs)
    pos_weight = torch.tensor([args.pos_weight]).to(DEVICE)
    criterion = nn.CrossEntropyLoss(weight=torch.tensor([1.0, args.pos_weight]).to(DEVICE))

    # ── Train ──
    best_val_f1 = 0.0
    results = []

    for epoch in range(1, args.epochs + 1):
        t0 = time.time()

        train_loss, train_f1 = train_epoch(model, train_loader, optimizer, criterion, DEVICE)
        val_loss, val_f1, val_p, val_r = evaluate(model, val_loader, criterion, DEVICE)
        scheduler.step()

        elapsed = time.time() - t0
        print(f"\nEpoch {epoch}/{args.epochs} [{elapsed:.0f}s]")
        print(f"  Train  — loss={train_loss:.4f}  F1={train_f1:.4f}")
        print(f"  Val    — loss={val_loss:.4f}  F1={val_f1:.4f}  P={val_p:.4f}  R={val_r:.4f}")

        results.append({"epoch": epoch, "train_loss": train_loss, "train_f1": train_f1,
                        "val_loss": val_loss, "val_f1": val_f1, "val_precision": val_p, "val_recall": val_r})

        if val_f1 > best_val_f1:
            best_val_f1 = val_f1
            torch.save(model.state_dict(), os.path.join(args.output_dir, "best.pt"))
            print(f"  ✅ Saved best model (F1={val_f1:.4f})")

    # ── Save ──
    torch.save(model.state_dict(), os.path.join(args.output_dir, "last.pt"))
    with open(os.path.join(args.output_dir, "results.json"), "w") as f:
        json.dump({"phase": args.phase, "best_val_f1": best_val_f1, "epochs": results}, f, indent=2)

    print(f"\n{'='*60}")
    print(f"Training complete!")
    print(f"Best val F1: {best_val_f1:.4f}")
    print(f"Model: {args.output_dir}/best.pt")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
