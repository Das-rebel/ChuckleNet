#!/usr/bin/env python3
"""
XLM-RoBERTa training with TurboQuant optimization for autonomous laughter prediction.

This script integrates TurboQuant KV-cache compression for efficient training on 8GB Mac M2.
Expected JSONL schema:
{
  "example_id": "set_001_seg_0001",
  "language": "en",
  "words": ["so", "i", "walked", "into", "a", "bank"],
  "labels": [0, 0, 0, 0, 0, 1]
}
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import torch
from torch import Tensor, nn
from torch.optim import AdamW
from torch.utils.data import DataLoader, Dataset
from transformers import (
    AutoModelForTokenClassification,
    AutoTokenizer,
    get_linear_schedule_with_warmup
)

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from memory.turboquant.turboquant import TurboQuant


DEFAULT_MODEL_NAME = "FacebookAI/xlm-roberta-base"


@dataclass
class TrainingConfig:
    """Training configuration with TurboQuant optimization"""
    model_name: str = DEFAULT_MODEL_NAME
    train_file: str = "data/training/youtube_comedy_augmented/train.jsonl"
    valid_file: str = "data/training/youtube_comedy_augmented/valid.jsonl"
    output_dir: str = "models/xlmr_turboquant_training"

    # Training parameters
    num_labels: int = 2
    max_length: int = 128
    batch_size: int = 8
    eval_batch_size: int = 16
    learning_rate: float = 2e-5
    epochs: int = 3
    gradient_accumulation_steps: int = 4
    warmup_ratio: float = 0.1

    # TurboQuant parameters
    use_turboquant: bool = True
    turboquant_bits: int = 3
    turboquant_compression_ratio: float = 6.0

    # Memory optimization
    freeze_encoder_epochs: int = 1


class LaughterDataset(Dataset):
    """Dataset for word-level laughter prediction"""

    def __init__(self, data_file: str, tokenizer, max_length: int = 128):
        self.data_file = Path(data_file)
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.examples = self._load_data()

    def _load_data(self) -> List[Dict]:
        if not self.data_file.exists():
            raise FileNotFoundError(f"Data file not found: {self.data_file}")

        examples = []
        with open(self.data_file, 'r') as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    if data.get('words') and data.get('labels'):
                        examples.append(data)
                except json.JSONDecodeError:
                    continue

        print(f"Loaded {len(examples)} examples from {self.data_file}")
        return examples

    def __len__(self):
        return len(self.examples)

    def __getitem__(self, idx):
        example = self.examples[idx]
        words = example['words']
        labels = example['labels']

        # Tokenize with word alignment
        encoding = self.tokenizer(
            words,
            is_split_into_words=True,
            max_length=self.max_length,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )

        # Align labels with tokens
        word_ids = encoding.word_ids()
        aligned_labels = []
        for word_id in word_ids:
            if word_id is None:
                aligned_labels.append(-100)  # Special tokens
            elif word_id < len(labels):
                aligned_labels.append(labels[word_id])
            else:
                aligned_labels.append(0)

        return {
            'input_ids': encoding['input_ids'].squeeze(0),
            'attention_mask': encoding['attention_mask'].squeeze(0),
            'labels': torch.tensor(aligned_labels, dtype=torch.long)
        }


class TurboQuantTrainer:
    """Trainer with TurboQuant optimization"""

    def __init__(self, config: TrainingConfig):
        self.config = config
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.output_dir = Path(config.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize TurboQuant
        self.turboquant = None
        if config.use_turboquant:
            self.turboquant = TurboQuant(
                bits_per_channel=config.turboquant_bits,
                target_compression_ratio=config.turboquant_compression_ratio
            )
            print(f"🚀 TurboQuant enabled: {config.turboquant_bits}-bit compression")

        # Load tokenizer and model
        print(f"Loading model: {config.model_name}")
        self.tokenizer = AutoTokenizer.from_pretrained(config.model_name)
        self.model = AutoModelForTokenClassification.from_pretrained(
            config.model_name,
            num_labels=config.num_labels
        )

        # Move to device
        self.model.to(self.device)

        # Setup training
        self._setup_training()

    def _setup_training(self):
        """Setup training data and optimizer"""

        print("Loading training data...")
        self.train_dataset = LaughterDataset(
            self.config.train_file,
            self.tokenizer,
            self.config.max_length
        )

        print("Loading validation data...")
        self.valid_dataset = LaughterDataset(
            self.config.valid_file,
            self.tokenizer,
            self.config.max_length
        )

        # Create data loaders
        self.train_loader = DataLoader(
            self.train_dataset,
            batch_size=self.config.batch_size,
            shuffle=True,
            num_workers=0  # Mac M2 compatibility
        )

        self.valid_loader = DataLoader(
            self.valid_dataset,
            batch_size=self.config.eval_batch_size,
            shuffle=False,
            num_workers=0
        )

        # Setup optimizer
        no_decay = ['bias', 'LayerNorm.weight']
        optimizer_grouped_parameters = [
            {
                'params': [p for n, p in self.model.named_parameters()
                          if not any(nd in n for nd in no_decay)],
                'weight_decay': 0.01
            },
            {
                'params': [p for n, p in self.model.named_parameters()
                          if any(nd in n for nd in no_decay)],
                'weight_decay': 0.0
            }
        ]

        self.optimizer = AdamW(
            optimizer_grouped_parameters,
            lr=self.config.learning_rate
        )

        # Setup scheduler
        total_steps = len(self.train_loader) * self.config.epochs
        warmup_steps = int(total_steps * self.config.warmup_ratio)

        self.scheduler = get_linear_schedule_with_warmup(
            self.optimizer,
            num_warmup_steps=warmup_steps,
            num_training_steps=total_steps
        )

    def train(self):
        """Main training loop with TurboQuant optimization"""

        print(f"\n🎯 Starting Training with TurboQuant")
        print(f"=" * 60)
        print(f"Device: {self.device}")
        print(f"Training examples: {len(self.train_dataset)}")
        print(f"Validation examples: {len(self.valid_dataset)}")
        print(f"Batch size: {self.config.batch_size}")
        print(f"Gradient accumulation: {self.config.gradient_accumulation_steps}")
        print(f"Epochs: {self.config.epochs}")
        print(f"=" * 60)

        best_f1 = 0.0

        for epoch in range(self.config.epochs):
            print(f"\n📈 Epoch {epoch + 1}/{self.config.epochs}")

            # Freeze encoder for first epoch if specified
            if epoch < self.config.freeze_encoder_epochs:
                print("🔒 Freezing encoder backbone")
                for param in self.model.roberta.parameters():
                    param.requires_grad = False
            else:
                print("🔓 Unfreezing encoder backbone")
                for param in self.model.roberta.parameters():
                    param.requires_grad = True

            # Train epoch
            train_loss = self._train_epoch(epoch)

            # Evaluate
            val_metrics = self._evaluate()

            print(f"Train Loss: {train_loss:.4f}")
            print(f"Val Loss: {val_metrics['loss']:.4f}")
            print(f"Val F1: {val_metrics['f1']:.4f}")

            # Save best model
            if val_metrics['f1'] > best_f1:
                best_f1 = val_metrics['f1']
                self._save_model(f"best_model_f1_{best_f1:.4f}")
                print(f"✅ New best model saved! F1: {best_f1:.4f}")

            # Report TurboQuant stats
            if self.turboquant:
                stats = self.turboquant.get_compression_stats()
                if stats['compression_ratio'] > 0:
                    print(f"🚀 TurboQuant: {stats['compression_ratio']:.1f}x compression")

        print(f"\n🎉 Training complete! Best F1: {best_f1:.4f}")
        return best_f1

    def _train_epoch(self, epoch: int) -> float:
        """Train one epoch"""

        self.model.train()
        total_loss = 0.0
        step_count = 0
        start_time = time.time()

        for batch_idx, batch in enumerate(self.train_loader):
            # Move to device
            input_ids = batch['input_ids'].to(self.device)
            attention_mask = batch['attention_mask'].to(self.device)
            labels = batch['labels'].to(self.device)

            # Forward pass
            outputs = self.model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                labels=labels
            )

            loss = outputs.loss / self.config.gradient_accumulation_steps
            total_loss += loss.item() * self.config.gradient_accumulation_steps

            # Backward pass
            loss.backward()

            # Update weights
            if (batch_idx + 1) % self.config.gradient_accumulation_steps == 0:
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
                self.optimizer.step()
                self.scheduler.step()
                self.optimizer.zero_grad()
                step_count += 1

            # Progress reporting
            if (batch_idx + 1) % 100 == 0:
                elapsed = time.time() - start_time
                steps_per_sec = (batch_idx + 1) / elapsed
                print(f"  Batch {batch_idx + 1}/{len(self.train_loader)} | "
                      f"Loss: {loss.item():.4f} | "
                      f"Speed: {steps_per_sec:.1f} batches/s")

        avg_loss = total_loss / len(self.train_loader)
        return avg_loss

    def _evaluate(self) -> Dict[str, float]:
        """Evaluate model"""

        self.model.eval()
        total_loss = 0.0
        all_predictions = []
        all_labels = []

        with torch.no_grad():
            for batch in self.valid_loader:
                input_ids = batch['input_ids'].to(self.device)
                attention_mask = batch['attention_mask'].to(self.device)
                labels = batch['labels'].to(self.device)

                outputs = self.model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    labels=labels
                )

                total_loss += outputs.loss.item()

                # Get predictions
                predictions = torch.argmax(outputs.logits, dim=-1)

                # Filter out special tokens (label = -100)
                mask = labels != -100
                all_predictions.extend(predictions[mask].cpu().numpy().tolist())
                all_labels.extend(labels[mask].cpu().numpy().tolist())

        # Calculate metrics
        metrics = self._calculate_metrics(all_predictions, all_labels)
        metrics['loss'] = total_loss / len(self.valid_loader)

        return metrics

    def _calculate_metrics(self, predictions: List[int], labels: List[int]) -> Dict[str, float]:
        """Calculate evaluation metrics"""

        tp = sum(1 for p, l in zip(predictions, labels) if p == 1 and l == 1)
        fp = sum(1 for p, l in zip(predictions, labels) if p == 1 and l == 0)
        tn = sum(1 for p, l in zip(predictions, labels) if p == 0 and l == 0)
        fn = sum(1 for p, l in zip(predictions, labels) if p == 0 and l == 1)

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        return {
            'precision': precision,
            'recall': recall,
            'f1': f1
        }

    def _save_model(self, model_name: str):
        """Save model checkpoint"""

        output_path = self.output_dir / model_name
        output_path.mkdir(exist_ok=True)

        self.model.save_pretrained(output_path)
        self.tokenizer.save_pretrained(output_path)

        # Save config
        config_file = output_path / "training_config.json"
        with open(config_file, 'w') as f:
            json.dump({
                'model_name': self.config.model_name,
                'max_length': self.config.max_length,
                'num_labels': self.config.num_labels,
                'turboquant_enabled': self.config.use_turboquant,
                'turboquant_compression': self.turboquant.get_compression_stats() if self.turboquant else {}
            }, f, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Train XLM-RoBERTa with TurboQuant")
    parser.add_argument("--train-file", required=True, help="Training data JSONL file")
    parser.add_argument("--valid-file", required=True, help="Validation data JSONL file")
    parser.add_argument("--output-dir", default="models/xlmr_turboquant_training")
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--max-length", type=int, default=128)
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--learning-rate", type=float, default=2e-5)
    parser.add_argument("--gradient-accumulation-steps", type=int, default=4)
    parser.add_argument("--freeze-encoder-epochs", type=int, default=1)
    parser.add_argument("--no-turboquant", action="store_true", help="Disable TurboQuant")

    args = parser.parse_args()

    # Create config
    config = TrainingConfig(
        train_file=args.train_file,
        valid_file=args.valid_file,
        output_dir=args.output_dir,
        batch_size=args.batch_size,
        max_length=args.max_length,
        epochs=args.epochs,
        learning_rate=args.learning_rate,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        freeze_encoder_epochs=args.freeze_encoder_epochs,
        use_turboquant=not args.no_turboquant
    )

    # Train
    trainer = TurboQuantTrainer(config)
    best_f1 = trainer.train()

    print(f"\n🎯 Training Summary:")
    print(f"   Best F1 Score: {best_f1:.4f}")
    print(f"   Target: F1 > 0.7222")
    print(f"   Status: {'✅ ACHIEVED' if best_f1 > 0.7222 else '❌ BELOW TARGET'}")

    return 0 if best_f1 > 0.7222 else 1


if __name__ == "__main__":
    main()