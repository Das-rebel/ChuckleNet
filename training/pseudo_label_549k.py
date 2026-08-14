#!/usr/bin/env python3
"""
Pseudo-label 549K word segments using fine-tuned XLM-R (F1=0.5).
Runs locally on Mac CPU. Output: pseudo_labels.pt (labels + confidences).

Time estimate: ~2-3 hours for 549K examples on M1 CPU.
Resume-safe: saves checkpoint every 50K.
"""

import json, os, sys, time, gc
from pathlib import Path
from collections import defaultdict

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from tqdm import tqdm

PROJECT = Path(__file__).resolve().parent.parent
SEGMENTS_FILE = PROJECT / "data" / "audio_comedy" / "aligned_segments.jsonl"
CKPT_PATH = PROJECT / "experiments" / "xlmr_baseline_retrained" / "best.pt"
OUTPUT = PROJECT / "data" / "audio_comedy" / "pseudo_labels.pt"

BS = 64  # Batch size for CPU
CONF_THRESHOLD = 0.7  # Only keep predictions with confidence > this


def main():
    print(f"{'='*60}")
    print("Pseudo-Label 549K Segments with Fine-Tuned XLM-R")
    print(f"{'='*60}")

    # Device
    device = torch.device("cpu")
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        device = torch.device("mps")
    print(f"Device: {device}")

    # Load segments
    print(f"Loading {SEGMENTS_FILE}...")
    with open(SEGMENTS_FILE) as f:
        segments = [json.loads(l) for l in f if l.strip()]
    print(f"Loaded {len(segments):,} segments")

    # Resume
    start_idx = 0
    all_labels = []
    all_confs = []
    if OUTPUT.exists():
        saved = torch.load(OUTPUT, map_location='cpu', weights_only=True)
        all_labels = saved['labels']
        all_confs = saved['confs']
        start_idx = len(all_labels)
        print(f"Resuming from {start_idx:,} / {len(segments):,}")

    # Load model
    print("Loading XLM-R model...")
    from transformers import AutoTokenizer, AutoModel

    tokenizer = AutoTokenizer.from_pretrained("FacebookAI/xlm-roberta-base")

    class XLMRClassifier(nn.Module):
        def __init__(self):
            super().__init__()
            self.encoder = AutoModel.from_pretrained("FacebookAI/xlm-roberta-base")
            self.proj = nn.Sequential(nn.Linear(768, 256), nn.GELU(), nn.Dropout(0.1))
            self.classifier = nn.Linear(256, 2)

        def forward(self, ids, mask):
            x = self.encoder(input_ids=ids, attention_mask=mask).last_hidden_state[:, 0, :]
            x = self.proj(x)
            return self.classifier(x)

    model = XLMRClassifier().to(device)
    ck = torch.load(CKPT_PATH, map_location=device, weights_only=True)
    model.load_state_dict(ck["model_state"])
    model.eval()
    print(f"Loaded! val_f1={ck.get('val_f1', '?')}")

    # Process
    remaining = len(segments) - start_idx
    print(f"\nProcessing {remaining:,} segments...")
    t0 = time.time()

    for i in tqdm(range(start_idx, len(segments), BS), desc="Pseudo-label", unit="batch"):
        batch = segments[i : i + BS]
        # Use context words (3 left + word + 3 right)
        texts = []
        for s in batch:
            ctx = s.get("context_words", [s["word"]])
            # Take word + up to 3 context words each side
            word_idx = len(ctx) // 2 if len(ctx) > 1 else 0
            start_c = max(0, word_idx - 3)
            end_c = min(len(ctx), word_idx + 4)
            texts.append(" ".join(ctx[start_c:end_c]))

        encoded = tokenizer(
            texts,
            max_length=64,
            padding=True,
            truncation=True,
            return_tensors="pt",
        )

        with torch.no_grad():
            logits = model(
                encoded["input_ids"].to(device), encoded["attention_mask"].to(device)
            )
            probs = torch.softmax(logits, dim=-1)
            preds = logits.argmax(-1)
            confs = probs.max(-1).values

        all_labels.extend(preds.cpu().tolist())
        all_confs.extend(confs.cpu().tolist())

        # Checkpoint every 50K
        if len(all_labels) % 50000 == 0:
            torch.save({"labels": all_labels, "confs": all_confs}, OUTPUT)
            elapsed = time.time() - t0
            rate = len(all_labels) / max(elapsed, 1)
            eta = (len(segments) - len(all_labels)) / max(rate, 0.01)
            n_pos = sum(all_labels)
            n_high = sum(1 for c in all_confs if c > CONF_THRESHOLD)
            print(
                f"\n  [{len(all_labels):,}] pos={n_pos} ({100*n_pos/len(all_labels):.1f}%)  "
                f"high_conf={n_high} ({100*n_high/len(all_labels):.1f}%)  "
                f"rate={rate:.0f}/s  ETA={eta/60:.0f}min"
            )

        # Clear cache periodically
        if i % 5000 == 0:
            gc.collect()

    # Final save
    torch.save({"labels": all_labels, "confs": all_confs}, OUTPUT)

    elapsed = time.time() - t0
    n_pos = sum(all_labels)
    n_high = sum(1 for c in all_confs if c > CONF_THRESHOLD)

    print(f"\n{'='*60}")
    print(f"Done! {len(all_labels):,} segments in {elapsed/60:.1f} min")
    print(f"Positive: {n_pos} ({100*n_pos/len(all_labels):.1f}%)")
    print(f"High confidence (>0.7): {n_high} ({100*n_high/len(all_labels):.1f}%)")
    print(f"Output: {OUTPUT} ({os.path.getsize(OUTPUT)/1e6:.1f} MB)")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
