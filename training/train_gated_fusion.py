#!/usr/bin/env python3
"""
3-Phase Training for Gated Multimodal Fusion (XLM-R + WavLM)

Phase 1: Text-only baseline → establish text F1 ≈ 0.75-0.80
Phase 2: Frozen XLM-R, train audio_proj + gate → audio learns complement
Phase 3: Joint fine-tune (unfreeze top-2 XLM-R layers) → Target F1 > 0.85

Usage:
    # Phase 1 (text baseline — no audio needed)
    python training/train_gated_fusion.py --phase 1 --output_dir experiments/gated_fusion_v1

    # Phase 2 (frozen fusion — needs WavLM embeddings)
    python training/train_gated_fusion.py --phase 2 --wavlm-dir experiments/wavlm_embeddings/ --output_dir experiments/gated_fusion_v1

    # Phase 3 (joint)
    python training/train_gated_fusion.py --phase 3 --wavlm-dir experiments/wavlm_embeddings/ --output_dir experiments/gated_fusion_v1

    # Resume from checkpoint
    python training/train_gated_fusion.py --phase 2 --resume experiments/gated_fusion_v1/phase2_latest.pt ...
"""

import os
import sys
import json
import time
import random
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader
from torch.optim import AdamW
from torch.cuda.amp import autocast, GradScaler
from transformers import AutoTokenizer, AutoModel, get_linear_schedule_with_warmup
from sklearn.metrics import f1_score, precision_score, recall_score

from model_gated_fusion import WavLMXLMRFusionModel, PHASE_CONFIGS


# ─── Config ───────────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA = PROJECT_ROOT / "data" / "audio_comedy" / "aligned_utterances.jsonl"
DEFAULT_WAVLM = PROJECT_ROOT / "experiments" / "wavlm_embeddings"
DEFAULT_OUTPUT = PROJECT_ROOT / "experiments" / "gated_fusion_v1"

XLM_MODEL = "xlm-roberta-base"
WAVLM_MODEL = "microsoft/wavlm-base-plus"

SEED = 42


def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def log(msg, fp=None):
    print(msg, flush=True)
    if fp:
        fp.write(msg + "\n")
        fp.flush()


# ─── Dataset ──────────────────────────────────────────────────────────────────

class WordLevelDataset(Dataset):
    """Word-level sequence labeling from aligned_utterances.jsonl.
    
    Format per line: {"utterance_id": "...", "video_id": "...", "text": "word1 word2 ...",
                      "start": float, "end": float, "duration": float,
                      "n_words": int, "n_positive_words": int,
                      "positive_ratio": float, "label_any": 0|1, "label_majority": 0|1, ...}
    """
    
    def __init__(self, examples: List[Dict], tokenizer, max_length: int = 128):
        self.examples = examples
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.examples)

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        ex = self.examples[idx]
        
        # Split text into words (whitespace tokenization)
        text = ex.get("text", "")
        words = text.split() if text else []
        
        if not words:
            words = [""]
        
        # Label: majority vote at word level
        n_words = len(words)
        n_pos = ex.get("n_positive_words", 0)
        
        # Per-word labels from positive_ratio
        positive_ratio = ex.get("positive_ratio", 0.0)
        if positive_ratio > 0:
            n_pos = int(positive_ratio * n_words)
        
        word_labels = []
        for i in range(n_words):
            # Words in first n_pos are labeled 1, rest 0 (within utterance window)
            # We use utterance-level label for all words (coarse supervision)
            word_labels.append(ex.get("label_majority", ex.get("label_any", 0)))
        
        # Tokenize preserving word alignment
        flat_tokens = []
        flat_labels = []
        for w_idx, (w, label) in enumerate(zip(words, word_labels)):
            tokens = self.tokenizer.tokenize(w) or [self.tokenizer.unk_token]
            flat_tokens.extend(tokens)
            flat_labels.append(label)
            flat_labels.extend([-100] * (len(tokens) - 1))
        
        # Truncate
        max_content = self.max_length - 2
        if len(flat_tokens) > max_content:
            flat_tokens = flat_tokens[:max_content]
            flat_labels = flat_labels[:max_content]
        
        # Build input
        input_ids = (
            [self.tokenizer.cls_token_id]
            + self.tokenizer.convert_tokens_to_ids(flat_tokens)
            + [self.tokenizer.sep_token_id]
        )
        attention_mask = [1] * len(input_ids)
        label_ids = [-100] + flat_labels + [-100]
        
        # Pad
        pad_len = self.max_length - len(input_ids)
        input_ids += [self.tokenizer.pad_token_id] * pad_len
        attention_mask += [0] * pad_len
        label_ids += [-100] * pad_len
        
        return {
            "input_ids": torch.tensor(input_ids, dtype=torch.long),
            "attention_mask": torch.tensor(attention_mask, dtype=torch.long),
            "labels": torch.tensor(label_ids, dtype=torch.long),
            "utterance_id": ex.get("utterance_id", f"{ex.get('video_id','')}_{ex.get('start',0)}"),
        }


class MultimodalDataset(Dataset):
    """Word-level dataset with audio embeddings."""
    
    def __init__(self, examples, tokenizer, wavlm_cache: Dict, max_length: int = 128):
        self.examples = examples
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.wavlm_cache = wavlm_cache  # {utterance_id: tensor(768)}
    
    def __len__(self):
        return len(self.examples)
    
    def __getitem__(self, idx: int) -> Dict:
        ex = self.examples[idx]
        
        text = ex.get("text", "")
        words = text.split() if text else [""]
        
        n_words = len(words)
        word_label = ex.get("label_majority", ex.get("label_any", 0))
        word_labels = [word_label] * n_words
        
        # Tokenize
        flat_tokens = []
        flat_labels = []
        for w, label in zip(words, word_labels):
            tokens = self.tokenizer.tokenize(w) or [self.tokenizer.unk_token]
            flat_tokens.extend(tokens)
            flat_labels.append(label)
            flat_labels.extend([-100] * (len(tokens) - 1))
        
        max_content = self.max_length - 2
        if len(flat_tokens) > max_content:
            flat_tokens = flat_tokens[:max_content]
            flat_labels = flat_labels[:max_content]
        
        input_ids = (
            [self.tokenizer.cls_token_id]
            + self.tokenizer.convert_tokens_to_ids(flat_tokens)
            + [self.tokenizer.sep_token_id]
        )
        attention_mask = [1] * len(input_ids)
        label_ids = [-100] + flat_labels + [-100]
        
        pad_len = self.max_length - len(input_ids)
        input_ids += [self.tokenizer.pad_token_id] * pad_len
        attention_mask += [0] * pad_len
        label_ids += [-100] * pad_len
        
        # Audio embedding
        uid = ex.get("utterance_id", f"{ex.get('video_id')}_{ex.get('start',0)}")
        audio_emb = self.wavlm_cache.get(uid, torch.zeros(768))
        
        return {
            "input_ids": torch.tensor(input_ids, dtype=torch.long),
            "attention_mask": torch.tensor(attention_mask, dtype=torch.long),
            "labels": torch.tensor(label_ids, dtype=torch.long),
            "audio_emb": audio_emb,
            "utterance_id": uid,
        }


def load_data(data_path: str, split_ratios=(0.8, 0.1, 0.1), seed=42):
    """Load utterances and split by video_id hash."""
    with open(data_path, "r") as f:
        all_examples = [json.loads(line) for line in f]
    
    # Split by video_id to prevent leakage
    video_ids = list(set(ex["video_id"] for ex in all_examples))
    random.seed(seed)
    random.shuffle(video_ids)
    
    n = len(video_ids)
    n_train = int(n * split_ratios[0])
    n_val = int(n * split_ratios[1])
    
    train_vids = set(video_ids[:n_train])
    val_vids = set(video_ids[n_train:n_train + n_val])
    test_vids = set(video_ids[n_train + n_val:])
    
    splits = {
        "train": [ex for ex in all_examples if ex["video_id"] in train_vids],
        "valid": [ex for ex in all_examples if ex["video_id"] in val_vids],
        "test": [ex for ex in all_examples if ex["video_id"] in test_vids],
    }
    
    return splits


# ─── Metrics ─────────────────────────────────────────────────────────────────

def compute_word_level_f1(preds: np.ndarray, labels: np.ndarray) -> Dict:
    """Compute word-level F1, precision, recall."""
    preds_flat = preds.flatten()
    labels_flat = labels.flatten()
    
    mask = labels_flat != -100  # Ignore padding/ignored
    preds_flat = preds_flat[mask]
    labels_flat = labels_flat[mask]
    
    f1 = f1_score(labels_flat, preds_flat, average="binary", zero_division=0)
    prec = precision_score(labels_flat, preds_flat, average="binary", zero_division=0)
    rec = recall_score(labels_flat, preds_flat, average="binary", zero_division=0)
    
    return {"f1": f1, "precision": prec, "recall": rec}


def compute_iou_f1(preds: np.ndarray, labels: np.ndarray, min_length: int = 3) -> float:
    """Compute span-level IoU-F1 (only counts spans ≥ min_length)."""
    spans_pred = extract_spans(preds, min_length)
    spans_label = extract_spans(labels, min_length)
    
    if not spans_pred and not spans_label:
        return 1.0
    if not spans_pred or not spans_label:
        return 0.0
    
    ious = []
    for sp in spans_label:
        best_iou = max((compute_iou(sp, rp) for rp in spans_pred), default=0.0)
        ious.append(best_iou)
    
    tp = sum(1 for iou in ious if iou >= 0.5)
    fp = len(spans_pred) - tp
    fn = len(spans_label) - tp
    
    prec = tp / (tp + fp) if (tp + fp) > 0 else 0
    rec = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0
    
    return f1


def extract_spans(arr: np.ndarray, min_length: int = 3) -> List[Tuple[int, int]]:
    """Extract contiguous positive regions."""
    spans = []
    in_span = False
    start = 0
    
    for i, v in enumerate(arr):
        if v == 1 and not in_span:
            start = i
            in_span = True
        elif v == 0 and in_span:
            if i - start >= min_length:
                spans.append((start, i - 1))
            in_span = False
    
    if in_span and len(arr) - start >= min_length:
        spans.append((start, len(arr) - 1))
    
    return spans


def compute_iou(span1: Tuple[int, int], span2: Tuple[int, int]) -> float:
    """IoU between two spans."""
    s1, e1 = span1
    s2, e2 = span2
    inter = max(0, min(e1, e2) - max(s1, s2) + 1)
    union = max(e1, e2) - min(s1, s2) + 1
    return inter / union if union > 0 else 0


# ─── Training ─────────────────────────────────────────────────────────────────

def train_phase1(
    model,
    train_loader,
    val_loader,
    output_dir,
    epochs=5,
    lr=5e-5,
    warmup_ratio=0.1,
    max_grad_norm=1.0,
    device="cuda",
    fp16=True,
):
    """Phase 1: Text-only baseline, full XLM-R fine-tuning."""
    set_seed(SEED)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Freeze audio (not used in phase 1)
    for param in model.wavlm.parameters():
        param.requires_grad = False
    
    # Optimizer
    optimizer = AdamW(
        [p for p in model.parameters() if p.requires_grad],
        lr=lr,
        weight_decay=0.01,
    )
    
    total_steps = len(train_loader) * epochs
    warmup_steps = int(total_steps * warmup_ratio)
    scheduler = get_linear_schedule_with_warmup(optimizer, warmup_steps, total_steps)
    
    scaler = GradScaler() if fp16 else None
    pos_weight = torch.tensor([1.0, 5.0]).to(device)  # Class imbalance
    
    best_val_f1 = 0.0
    log_path = output_dir / "phase1_log.txt"
    
    with open(log_path, "w") as log_fp:
        log(f"[Phase 1] Text-only baseline, {epochs} epochs, lr={lr}", log_fp)
        
        for epoch in range(epochs):
            model.train()
            total_loss = 0
            
            for step, batch in enumerate(train_loader):
                input_ids = batch["input_ids"].to(device)
                attention_mask = batch["attention_mask"].to(device)
                labels = batch["labels"].to(device)
                
                optimizer.zero_grad()
                
                with autocast(enabled=fp16):
                    # Text only forward pass
                    text_outputs = model.xlmr(input_ids=input_ids, attention_mask=attention_mask)
                    text_emb = text_outputs.last_hidden_state[:, 0, :]
                    
                    # Project and classify (no audio)
                    t = model.fusion.text_proj(text_emb)
                    logits = model.fusion.classifier(t)
                    
                    # Compute loss (word-level)
                    loss = F.cross_entropy(
                        logits.view(-1, 2),
                        labels.view(-1),
                        ignore_index=-100,
                        reduction="mean",
                    )
                
                if scaler:
                    scaler.scale(loss).backward()
                    scaler.unscale_(optimizer)
                    torch.nn.utils.clip_grad_norm_(model.parameters(), max_grad_norm)
                    scaler.step(optimizer)
                    scaler.update()
                else:
                    loss.backward()
                    torch.nn.utils.clip_grad_norm_(model.parameters(), max_grad_norm)
                    optimizer.step()
                
                scheduler.step()
                total_loss += loss.item()
                
                if (step + 1) % 100 == 0:
                    avg_loss = total_loss / (step + 1)
                    log(f"  Step {step+1}: loss={avg_loss:.4f}", log_fp)
            
            # Validation
            val_metrics = evaluate_word_level(model, val_loader, device)
            log(f"Phase 1 Epoch {epoch+1}: val_f1={val_metrics['f1']:.4f} iou_f1={val_metrics.get('iou_f1', 0):.4f}", log_fp)
            
            if val_metrics["f1"] > best_val_f1:
                best_val_f1 = val_metrics["f1"]
                torch.save({
                    "epoch": epoch,
                    "model_state": model.state_dict(),
                    "optimizer_state": optimizer.state_dict(),
                    "val_f1": best_val_f1,
                }, output_dir / "phase1_best.pt")
                log(f"  → New best: {best_val_f1:.4f}", log_fp)
        
        log(f"[Phase 1] Best val_f1: {best_val_f1:.4f}", log_fp)
    
    return best_val_f1


def train_phase2(
    model,
    train_loader,
    val_loader,
    output_dir,
    epochs=10,
    lr_audio=1e-3,
    lr_fusion=1e-3,
    warmup_ratio=0.05,
    max_grad_norm=1.0,
    device="cuda",
    fp16=True,
):
    """Phase 2: Frozen XLM-R, train audio_proj + gate."""
    set_seed(SEED)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Freeze XLM-R completely
    for param in model.xlmr.parameters():
        param.requires_grad = False
    
    # Unfreeze audio encoder
    for param in model.wavlm.parameters():
        param.requires_grad = True
    
    # Only train fusion + audio_proj
    trainable_params = (
        list(model.fusion.parameters()) +
        list(model.wavlm.parameters())
    )
    
    optimizer = AdamW(trainable_params, lr=lr_audio, weight_decay=0.01)
    
    total_steps = len(train_loader) * epochs
    warmup_steps = int(total_steps * warmup_ratio)
    scheduler = get_linear_schedule_with_warmup(optimizer, warmup_steps, total_steps)
    
    scaler = GradScaler() if fp16 else None
    log_path = output_dir / "phase2_log.txt"
    
    with open(log_path, "w") as log_fp:
        log(f"[Phase 2] Frozen XLM-R, train audio+gate, {epochs} epochs", log_fp)
        
        for epoch in range(epochs):
            model.train()
            total_loss = 0
            gate_values = []
            
            for step, batch in enumerate(train_loader):
                input_ids = batch["input_ids"].to(device)
                attention_mask = batch["attention_mask"].to(device)
                audio_emb = batch["audio_emb"].to(device)
                labels = batch["labels"].to(device)
                
                optimizer.zero_grad()
                
                with autocast(enabled=fp16):
                    # Text encoding (frozen)
                    with torch.no_grad():
                        text_outputs = model.xlmr(input_ids=input_ids, attention_mask=attention_mask)
                        text_emb = text_outputs.last_hidden_state[:, 0, :]
                    
                    # Audio encoding (trainable)
                    # audio_emb comes from dataloader (pre-extracted)
                    a = model.fusion.audio_proj(audio_emb)
                    t = model.fusion.text_proj(text_emb)
                    
                    # Gate
                    gate_input = torch.cat([t, a], dim=-1)
                    gate_logit = model.fusion.gate(gate_input)
                    g = torch.sigmoid(gate_logit)
                    
                    # Fused
                    fused = g * a + (1 - g) * t
                    logits = model.fusion.classifier(fused)
                    
                    loss = F.cross_entropy(logits.view(-1, 2), labels.view(-1), ignore_index=-100)
                
                if scaler:
                    scaler.scale(loss).backward()
                    scaler.unscale_(optimizer)
                    torch.nn.utils.clip_grad_norm_(trainable_params, max_grad_norm)
                    scaler.step(optimizer)
                    scaler.update()
                else:
                    loss.backward()
                    torch.nn.utils.clip_grad_norm_(trainable_params, max_grad_norm)
                    optimizer.step()
                
                scheduler.step()
                total_loss += loss.item()
                gate_values.append(g.detach().cpu().mean().item())
                
                if (step + 1) % 100 == 0:
                    avg_loss = total_loss / (step + 1)
                    avg_gate = np.mean(gate_values[-100:])
                    log(f"  Step {step+1}: loss={avg_loss:.4f} gate_mean={avg_gate:.3f}", log_fp)
            
            # Validation
            val_metrics = evaluate_multimodal(model, val_loader, device)
            avg_gate = np.mean(gate_values)
            log(f"Phase 2 Epoch {epoch+1}: val_f1={val_metrics['f1']:.4f} gate={avg_gate:.3f}", log_fp)
            
            if val_metrics["f1"] > 0:
                torch.save({
                    "epoch": epoch,
                    "model_state": model.state_dict(),
                    "optimizer_state": optimizer.state_dict(),
                    "val_f1": val_metrics["f1"],
                    "gate_mean": avg_gate,
                }, output_dir / "phase2_latest.pt")
            
            # Check gate collapse
            if avg_gate < 0.05 or avg_gate > 0.95:
                log(f"  ⚠️ Gate collapse: g={avg_gate:.3f}", log_fp)
        
        log(f"[Phase 2] Done. Best: see log.", log_fp)
    
    return


def train_phase3(
    model,
    train_loader,
    val_loader,
    output_dir,
    checkpoint_path=None,
    epochs=5,
    lr_text=2e-5,
    lr_audio=5e-4,
    lr_fusion=5e-4,
    max_grad_norm=1.0,
    device="cuda",
    fp16=True,
):
    """Phase 3: Joint fine-tune, unfreeze top-2 XLM-R layers."""
    set_seed(SEED)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if checkpoint_path:
        ckpt = torch.load(checkpoint_path, map_location=device)
        model.load_state_dict(ckpt["model_state"])
        log(f"Loaded checkpoint from {checkpoint_path}")
    
    # Unfreeze top-2 XLM-R layers
    model.unfreeze_xlmr_top_n(2)
    
    # All parameters trainable
    all_params = list(model.xlmr.parameters()) + list(model.wavlm.parameters()) + list(model.fusion.parameters())
    
    optimizer = AdamW(all_params, lr=lr_text, weight_decay=0.01)
    
    total_steps = len(train_loader) * epochs
    scheduler = get_linear_schedule_with_warmup(optimizer, int(total_steps * 0.1), total_steps)
    
    scaler = GradScaler() if fp16 else None
    log_path = output_dir / "phase3_log.txt"
    
    best_f1 = 0.0
    
    with open(log_path, "w") as log_fp:
        log(f"[Phase 3] Joint fine-tune, {epochs} epochs", log_fp)
        
        for epoch in range(epochs):
            model.train()
            total_loss = 0
            
            for step, batch in enumerate(train_loader):
                input_ids = batch["input_ids"].to(device)
                attention_mask = batch["attention_mask"].to(device)
                audio_emb = batch["audio_emb"].to(device)
                labels = batch["labels"].to(device)
                
                optimizer.zero_grad()
                
                with autocast(enabled=fp16):
                    text_outputs = model.xlmr(input_ids=input_ids, attention_mask=attention_mask)
                    text_emb = text_outputs.last_hidden_state[:, 0, :]
                    
                    a = model.fusion.audio_proj(audio_emb)
                    t = model.fusion.text_proj(text_emb)
                    
                    gate_input = torch.cat([t, a], dim=-1)
                    g = torch.sigmoid(model.fusion.gate(gate_input))
                    
                    fused = g * a + (1 - g) * t
                    logits = model.fusion.classifier(fused)
                    
                    loss = F.cross_entropy(logits.view(-1, 2), labels.view(-1), ignore_index=-100)
                
                if scaler:
                    scaler.scale(loss).backward()
                    scaler.unscale_(optimizer)
                    torch.nn.utils.clip_grad_norm_(all_params, max_grad_norm)
                    scaler.step(optimizer)
                    scaler.update()
                else:
                    loss.backward()
                    torch.nn.utils.clip_grad_norm_(all_params, max_grad_norm)
                    optimizer.step()
                
                scheduler.step()
                total_loss += loss.item()
                
                if (step + 1) % 100 == 0:
                    log(f"  Step {step+1}: loss={total_loss/(step+1):.4f}", log_fp)
            
            val_metrics = evaluate_multimodal(model, val_loader, device)
            log(f"Phase 3 Epoch {epoch+1}: val_f1={val_metrics['f1']:.4f} iou_f1={val_metrics.get('iou_f1', 0):.4f}", log_fp)
            
            if val_metrics["f1"] > best_f1:
                best_f1 = val_metrics["f1"]
                torch.save({
                    "epoch": epoch,
                    "model_state": model.state_dict(),
                    "val_f1": best_f1,
                }, output_dir / "phase3_best.pt")
                log(f"  → Saved best: {best_f1:.4f}", log_fp)
        
        log(f"[Phase 3] Best: {best_f1:.4f}", log_fp)
    
    return best_f1


# ─── Evaluation ──────────────────────────────────────────────────────────────

def evaluate_word_level(model, data_loader, device):
    """Evaluate word-level sequence labeling (Phase 1)."""
    model.eval()
    all_preds = []
    all_labels = []
    
    with torch.no_grad():
        for batch in data_loader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"].to(device)
            
            text_outputs = model.xlmr(input_ids=input_ids, attention_mask=attention_mask)
            text_emb = text_outputs.last_hidden_state[:, 0, :]
            t = model.fusion.text_proj(text_emb)
            logits = model.fusion.classifier(t)
            
            preds = logits.argmax(dim=-1).cpu().numpy()
            all_preds.append(preds)
            all_labels.append(labels.cpu().numpy())
    
    preds_arr = np.concatenate(all_preds, axis=0)
    labels_arr = np.concatenate(all_labels, axis=0)
    
    metrics = compute_word_level_f1(preds_arr, labels_arr)
    metrics["iou_f1"] = compute_iou_f1(preds_arr, labels_arr)
    
    return metrics


def evaluate_multimodal(model, data_loader, device):
    """Evaluate multimodal model (Phase 2/3)."""
    model.eval()
    all_preds = []
    all_labels = []
    gate_values = []
    
    with torch.no_grad():
        for batch in data_loader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            audio_emb = batch["audio_emb"].to(device)
            labels = batch["labels"].to(device)
            
            text_outputs = model.xlmr(input_ids=input_ids, attention_mask=attention_mask)
            text_emb = text_outputs.last_hidden_state[:, 0, :]
            
            a = model.fusion.audio_proj(audio_emb)
            t = model.fusion.text_proj(text_emb)
            
            gate_input = torch.cat([t, a], dim=-1)
            g = torch.sigmoid(model.fusion.gate(gate_input))
            
            fused = g * a + (1 - g) * t
            logits = model.fusion.classifier(fused)
            
            preds = logits.argmax(dim=-1).cpu().numpy()
            all_preds.append(preds)
            all_labels.append(labels.cpu().numpy())
            gate_values.append(g.cpu().mean().item())
    
    preds_arr = np.concatenate(all_preds, axis=0)
    labels_arr = np.concatenate(all_labels, axis=0)
    
    metrics = compute_word_level_f1(preds_arr, labels_arr)
    metrics["iou_f1"] = compute_iou_f1(preds_arr, labels_arr)
    metrics["gate_mean"] = np.mean(gate_values)
    
    return metrics


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", type=int, choices=[1, 2, 3], required=True)
    parser.add_argument("--data", type=str, default=str(DEFAULT_DATA))
    parser.add_argument("--wavlm-dir", type=str, default=None)
    parser.add_argument("--output-dir", type=str, default=str(DEFAULT_OUTPUT))
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--max-length", type=int, default=128)
    parser.add_argument("--epochs", type=int, default=None)
    parser.add_argument("--lr", type=float, default=None)
    parser.add_argument("--resume", type=str, default=None)
    parser.add_argument("--device", type=str, default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--no-fp16", action="store_true")
    args = parser.parse_args()
    
    fp16 = not args.no_fp16 and args.device == "cuda"
    set_seed(SEED)
    
    log(f"\n{'='*60}")
    log(f"Gated Multimodal Fusion — Phase {args.phase}")
    log(f"{'='*60}")
    
    # Load data
    splits = load_data(args.data)
    
    log(f"Data: {args.data}")
    for k, v in splits.items():
        n_pos = sum(1 for ex in v if ex.get("label_majority", 0) == 1)
        log(f"  {k}: {len(v)} utterances, {n_pos} positive ({100*n_pos/len(v):.1f}%)")
    
    tokenizer = AutoTokenizer.from_pretrained(XLM_MODEL)
    
    if args.phase == 1:
        # Phase 1: Text-only, no audio needed
        train_ds = WordLevelDataset(splits["train"], tokenizer, args.max_length)
        val_ds = WordLevelDataset(splits["valid"], tokenizer, args.max_length)
        
        train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, num_workers=0)
        val_loader = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False, num_workers=0)
        
        model = WavLMXLMRFusionModel()
        model = model.to(args.device)
        
        best_f1 = train_phase1(
            model, train_loader, val_loader,
            output_dir=args.output_dir,
            epochs=args.epochs or 5,
            lr=args.lr or 5e-5,
            device=args.device,
            fp16=fp16,
        )
        log(f"\n✓ Phase 1 complete. Best val F1: {best_f1:.4f}")
    
    elif args.phase == 2:
        # Phase 2: Multimodal (needs WavLM embeddings)
        if not args.wavlm_dir:
            log("ERROR: --wavlm-dir required for Phase 2")
            sys.exit(1)
        
        # Load WavLM cache
        wavlm_dir = Path(args.wavlm_dir)
        wavlm_cache = {}
        
        if wavlm_dir.exists():
            for pf in wavlm_dir.glob("*.pt"):
                try:
                    data = torch.load(pf, map_location="cpu", weights_only=True)
                    embs = data["embs"]
                    ids = data["ids"]
                    for i, uid in enumerate(ids):
                        wavlm_cache[uid] = embs[i]
                except Exception as e:
                    log(f"  Warning: {pf} failed: {e}")
            log(f"Loaded {len(wavlm_cache)} WavLM embeddings")
        else:
            log(f"Warning: {wavlm_dir} not found — using zero embeddings")
        
        train_ds = MultimodalDataset(splits["train"], tokenizer, wavlm_cache, args.max_length)
        val_ds = MultimodalDataset(splits["valid"], tokenizer, wavlm_cache, args.max_length)
        
        train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, num_workers=0)
        val_loader = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False, num_workers=0)
        
        model = WavLMXLMRFusionModel()
        model = model.to(args.device)
        
        if args.resume:
            ckpt = torch.load(args.resume, map_location=args.device)
            model.load_state_dict(ckpt["model_state"])
            log(f"Loaded from {args.resume}")
        
        train_phase2(
            model, train_loader, val_loader,
            output_dir=args.output_dir,
            epochs=args.epochs or 10,
            lr_audio=args.lr or 1e-3,
            lr_fusion=args.lr or 1e-3,
            device=args.device,
            fp16=fp16,
        )
        log("\n✓ Phase 2 complete")
    
    elif args.phase == 3:
        # Phase 3: Joint fine-tune
        if not args.wavlm_dir:
            log("ERROR: --wavlm-dir required for Phase 3")
            sys.exit(1)
        
        wavlm_dir = Path(args.wavlm_dir)
        wavlm_cache = {}
        
        if wavlm_dir.exists():
            for pf in wavlm_dir.glob("*.pt"):
                try:
                    data = torch.load(pf, map_location="cpu", weights_only=True)
                    for i, uid in enumerate(data["ids"]):
                        wavlm_cache[uid] = data["embs"][i]
                except:
                    pass
            log(f"Loaded {len(wavlm_cache)} WavLM embeddings")
        
        train_ds = MultimodalDataset(splits["train"], tokenizer, wavlm_cache, args.max_length)
        val_ds = MultimodalDataset(splits["valid"], tokenizer, wavlm_cache, args.max_length)
        
        train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, num_workers=0)
        val_loader = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False, num_workers=0)
        
        model = WavLMXLMRFusionModel()
        model = model.to(args.device)
        
        best_f1 = train_phase3(
            model, train_loader, val_loader,
            output_dir=args.output_dir,
            checkpoint_path=args.resume,
            epochs=args.epochs or 5,
            lr_text=args.lr or 2e-5,
            lr_audio=args.lr or 5e-4 if not args.lr else None,
            device=args.device,
            fp16=fp16,
        )
        log(f"\n✓ Phase 3 complete. Best: {best_f1:.4f}")


if __name__ == "__main__":
    main()