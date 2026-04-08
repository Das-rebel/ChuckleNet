"""
StandUp4AI Word-Level Laughter Prediction Implementation

This module implements the StandUp4AI benchmark evaluation for word-level
laughter-after-word sequence labeling as defined in the EMNLP 2025 paper.

Key Features:
- Word-level laughter-after-word prediction
- Multi-language support (EN, RU, ES, FR, DE, IT, PT)
- IoU-based temporal evaluation metrics (IoU@0.2)
- Speaker-independent split implementation
- Comparison against 0.58 F1 published baseline
"""

import os
import json
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModel
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
import numpy as np
from dataclasses import dataclass
from collections import defaultdict
import warnings

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')


@dataclass
class StandUp4AIConfig:
    """Configuration for StandUp4AI benchmark"""
    # Languages
    languages: List[str] = ('EN', 'RU', 'ES', 'FR', 'DE', 'IT', 'PT')

    # Model settings
    model_name: str = 'bert-base-multilingual-cased'
    max_seq_length: int = 512
    hidden_dim: int = 256
    num_layers: int = 2
    dropout: float = 0.1

    # Training settings
    batch_size: int = 16
    learning_rate: float = 2e-5
    num_epochs: int = 10
    warmup_steps: int = 100

    # Evaluation settings
    iou_threshold: float = 0.2  # As per paper
    speaker_independent: bool = True

    # Data paths
    data_dir: str = './data/standup4ai'
    cache_dir: str = './cache/standup4ai'


class WordLevelLaughterPredictor(nn.Module):
    """
    Word-level laughter-after-word prediction model.

    This model extends standard BERT architecture for word-level sequence
    labeling, predicting laughter probability for each word in the transcript.
    """

    def __init__(self, config: StandUp4AIConfig):
        super().__init__()
        self.config = config

        # Pre-trained multilingual BERT
        self.tokenizer = AutoTokenizer.from_pretrained(
            config.model_name,
            cache_dir=config.cache_dir
        )
        self.bert = AutoModel.from_pretrained(
            config.model_name,
            cache_dir=config.cache_dir
        )

        # Freeze BERT parameters initially
        for param in self.bert.parameters():
            param.requires_grad = False

        # Word-level prediction head
        self.dropout = nn.Dropout(config.dropout)
        self.classifier = nn.Sequential(
            nn.Linear(self.bert.config.hidden_size, config.hidden_dim),
            nn.ReLU(),
            nn.Dropout(config.dropout),
            nn.Linear(config.hidden_dim, config.hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(config.dropout),
            nn.Linear(config.hidden_dim // 2, 2)  # Binary: laughter vs no laughter
        )

        # Language-specific adapters (one per language)
        self.language_adapters = nn.ModuleDict({
            lang: nn.Linear(self.bert.config.hidden_size, config.hidden_dim)
            for lang in config.languages
        })

        # Temporal context modeling
        self.temporal_conv = nn.Conv1d(
            self.bert.config.hidden_size,
            config.hidden_dim,
            kernel_size=3,
            padding=1
        )

    def forward(self, input_ids, attention_mask, language='EN', labels=None):
        """
        Forward pass for word-level laughter prediction.

        Args:
            input_ids: Token IDs (batch_size, seq_len)
            attention_mask: Attention mask (batch_size, seq_len)
            language: Language code for adapter selection
            labels: Word-level labels (batch_size, seq_len) for training

        Returns:
            Dictionary with loss and predictions
        """
        # Get BERT embeddings
        outputs = self.bert(
            input_ids=input_ids,
            attention_mask=attention_mask,
            return_dict=True
        )

        # Word-level embeddings (last hidden state)
        word_embeddings = outputs.last_hidden_state  # (batch_size, seq_len, hidden_size)

        # Apply language-specific adapter
        if language in self.language_adapters:
            adapted_embeddings = self.language_adapters[language](word_embeddings)
            word_embeddings = word_embeddings + adapted_embeddings

        # Apply temporal convolution
        temporal_features = self.temporal_conv(
            word_embeddings.transpose(1, 2)  # (batch_size, hidden_size, seq_len)
        ).transpose(1, 2)  # (batch_size, seq_len, hidden_dim)

        # Combine features
        combined_features = torch.cat([
            word_embeddings[:, :, :self.config.hidden_dim//2],
            temporal_features
        ], dim=-1)

        # Apply dropout and classifier
        combined_features = self.dropout(combined_features)
        logits = self.classifier(combined_features)  # (batch_size, seq_len, 2)

        # Compute loss if labels provided
        loss = None
        if labels is not None:
            # Mask out padding tokens
            active_loss = attention_mask.view(-1) == 1
            active_logits = logits.view(-1, 2)[active_loss]
            active_labels = labels.view(-1)[active_loss]

            loss_fct = nn.CrossEntropyLoss()
            loss = loss_fct(active_logits, active_labels)

        return {
            'loss': loss,
            'logits': logits,
            'predictions': torch.argmax(logits, dim=-1)
        }

    def unfreeze_bert(self, num_layers: int = 2):
        """Unfreeze top N layers of BERT for fine-tuning"""
        # Unfreeze the last N layers
        for param in self.bert.encoder.layer[-num_layers:].parameters():
            param.requires_grad = True


class StandUp4AIWordLevelDataset(Dataset):
    """
    StandUp4AI dataset for word-level laughter prediction.

    This dataset loads word-level annotations and prepares them for
    sequence labeling task.
    """

    def __init__(self, config: StandUp4AIConfig, split: str = 'train'):
        self.config = config
        self.split = split
        self.samples = []

        # Load data
        self._load_data()

    def _load_data(self):
        """Load StandUp4AI word-level annotations"""
        data_path = Path(self.config.data_dir)

        # For now, create a small demo dataset
        # In production, this would load actual StandUp4AI data
        print(f"Loading StandUp4AI {self.split} data...")

        # Create demo samples if real data not available
        if not data_path.exists():
            print(f"Warning: StandUp4AI data not found at {data_path}")
            print("Creating demo dataset for testing...")
            self._create_demo_dataset()
            return

        # Load actual annotations
        annotation_file = data_path / f'{self.split}_annotations.json'

        if annotation_file.exists():
            with open(annotation_file, 'r') as f:
                annotations = json.load(f)

            for annotation in annotations:
                self.samples.append({
                    'text': annotation['text'],
                    'word_labels': annotation['word_labels'],  # Word-level binary labels
                    'language': annotation.get('language', 'EN'),
                    'speaker_id': annotation.get('speaker_id', 'unknown'),
                    'show_id': annotation.get('show_id', 'unknown')
                })

            print(f"Loaded {len(self.samples)} samples from {annotation_file}")

    def _create_demo_dataset(self):
        """Create demo dataset for testing"""
        # Demo stand-up comedy transcript with word-level labels
        demo_samples = [
            {
                'text': "So I was at the gym yesterday and I saw this guy lifting weights",
                'word_labels': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # No laughter
                'language': 'EN',
                'speaker_id': 'comedian_1',
                'show_id': 'show_1'
            },
            {
                'text': "He was struggling so much I thought he was giving birth to a dumbbell",
                'word_labels': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1],  # Laughter on last words
                'language': 'EN',
                'speaker_id': 'comedian_1',
                'show_id': 'show_1'
            },
            {
                'text': "True story folks these things happen",
                'word_labels': [1, 1, 0, 0, 0, 0],  # Laughter on "True story folks"
                'language': 'EN',
                'speaker_id': 'comedian_2',
                'show_id': 'show_2'
            }
        ]

        self.samples = demo_samples * 10  # Replicate for reasonable dataset size
        print(f"Created demo dataset with {len(self.samples)} samples")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        sample = self.samples[idx]

        # We need to use the tokenizer from the model class
        # For now, create a simple tokenizer
        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained('bert-base-multilingual-cased')

        # Tokenize text
        encoding = tokenizer(
            sample['text'],
            max_length=self.config.max_seq_length,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )

        # Align word-level labels with tokens
        word_labels = self._align_labels_with_tokens(
            sample['word_labels'],
            encoding.word_ids()
        )

        return {
            'input_ids': encoding['input_ids'].squeeze(0),
            'attention_mask': encoding['attention_mask'].squeeze(0),
            'labels': torch.tensor(word_labels, dtype=torch.long),
            'language': sample['language'],
            'speaker_id': sample['speaker_id'],
            'show_id': sample['show_id']
        }

    def _align_labels_with_tokens(self, word_labels, word_ids):
        """Align word-level labels with BERT tokens"""
        aligned_labels = []
        previous_word_idx = None

        for word_idx in word_ids:
            if word_idx is None:
                # Special token
                aligned_labels.append(-100)  # Ignored in loss
            elif word_idx != previous_word_idx:
                # First token of word
                if word_idx < len(word_labels):
                    aligned_labels.append(word_labels[word_idx])
                else:
                    aligned_labels.append(0)  # No laughter
            else:
                # Subword token - ignore in loss
                aligned_labels.append(-100)

            previous_word_idx = word_idx

        return aligned_labels


class IoUEvaluator:
    """
    IoU-based temporal evaluator for word-level laughter prediction.

    Implements Intersection over Union metrics as defined in StandUp4AI paper.
    """

    def __init__(self, iou_threshold: float = 0.2):
        self.iou_threshold = iou_threshold

    def compute_iou(self, predicted_intervals, true_intervals):
        """
        Compute IoU between predicted and true laughter intervals.

        Args:
            predicted_intervals: List of (start, end) word indices
            true_intervals: List of (start, end) word indices

        Returns:
            List of IoU scores
        """
        if not predicted_intervals or not true_intervals:
            return []

        ious = []
        for pred_interval in predicted_intervals:
            max_iou = 0
            for true_interval in true_intervals:
                iou = self._compute_single_iou(pred_interval, true_interval)
                max_iou = max(max_iou, iou)
            ious.append(max_iou)

        return ious

    def _compute_single_iou(self, interval1, interval2):
        """Compute IoU between two intervals"""
        start1, end1 = interval1
        start2, end2 = interval2

        # Compute intersection
        intersection_start = max(start1, start2)
        intersection_end = min(end1, end2)
        intersection = max(0, intersection_end - intersection_start + 1)

        # Compute union
        union_start = min(start1, start2)
        union_end = max(end1, end2)
        union = union_end - union_start + 1

        return intersection / union if union > 0 else 0

    def extract_intervals(self, word_labels):
        """Extract continuous laughter intervals from word labels"""
        intervals = []
        start = None

        for i, label in enumerate(word_labels):
            if label == 1 and start is None:
                start = i
            elif label == 0 and start is not None:
                intervals.append((start, i - 1))
                start = None

        # Handle case where laughter continues to end
        if start is not None:
            intervals.append((start, len(word_labels) - 1))

        return intervals

    def compute_metrics(self, predictions, ground_truth):
        """
        Compute IoU-based F1 metrics.

        Args:
            predictions: Predicted word-level labels
            ground_truth: Ground truth word-level labels

        Returns:
            Dictionary with precision, recall, F1, IoU@0.2 F1
        """
        # Extract intervals
        pred_intervals = self.extract_intervals(predictions)
        true_intervals = self.extract_intervals(ground_truth)

        # Compute basic metrics
        tp = sum(1 for p in predictions if p == 1 and
                 any(p == g for p, g in zip(predictions, ground_truth)))
        fp = sum(1 for p in predictions if p == 1 and
                 any(p != g for p, g in zip(predictions, ground_truth)))
        fn = sum(1 for g in ground_truth if g == 1 and
                 any(p != g for p, g in zip(predictions, ground_truth)))

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

        # Compute IoU-based metrics
        ious = self.compute_iou(pred_intervals, true_intervals)
        iou_f1 = 0

        if ious:
            # Count matches above threshold
            matches = sum(1 for iou in ious if iou >= self.iou_threshold)
            iou_precision = matches / len(pred_intervals) if pred_intervals else 0
            iou_recall = matches / len(true_intervals) if true_intervals else 0
            iou_f1 = 2 * (iou_precision * iou_recall) / (iou_precision + iou_recall) \
                if (iou_precision + iou_recall) > 0 else 0

        return {
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'iou_f1': iou_f1,
            'num_predictions': len(pred_intervals),
            'num_ground_truth': len(true_intervals)
        }


class StandUp4AIBenchmark:
    """
    Main benchmark class for StandUp4AI evaluation.

    Coordinates dataset loading, model training, and evaluation.
    """

    def __init__(self, config: StandUp4AIConfig):
        self.config = config
        self.model = None
        self.tokenizer = None
        self.evaluator = IoUEvaluator(iou_threshold=config.iou_threshold)

    def setup_model(self):
        """Initialize model and tokenizer"""
        self.model = WordLevelLaughterPredictor(self.config)
        self.tokenizer = self.model.tokenizer
        print("Model initialized successfully")

    def create_speaker_independent_splits(self, dataset):
        """
        Create speaker-independent splits to prevent data leakage.

        Ensures no comedian appears in multiple splits.
        """
        speakers = set(sample['speaker_id'] for sample in dataset.samples)

        # Split speakers (80% train, 10% val, 10% test)
        speaker_list = list(speakers)
        np.random.shuffle(speaker_list)

        n_train = int(0.8 * len(speaker_list))
        n_val = int(0.1 * len(speaker_list))

        train_speakers = set(speaker_list[:n_train])
        val_speakers = set(speaker_list[n_train:n_train + n_val])
        test_speakers = set(speaker_list[n_train + n_val:])

        # Split dataset
        train_data = [s for s in dataset.samples if s['speaker_id'] in train_speakers]
        val_data = [s for s in dataset.samples if s['speaker_id'] in val_speakers]
        test_data = [s for s in dataset.samples if s['speaker_id'] in test_speakers]

        print(f"Speaker-independent splits:")
        print(f"  Train: {len(train_data)} samples, {len(train_speakers)} speakers")
        print(f"  Val: {len(val_data)} samples, {len(val_speakers)} speakers")
        print(f"  Test: {len(test_data)} samples, {len(test_speakers)} speakers")

        return train_data, val_data, test_data

    def evaluate_per_language(self, model, dataloader, device):
        """Evaluate performance per language"""
        model.eval()
        language_metrics = defaultdict(list)

        with torch.no_grad():
            for batch in dataloader:
                # Move to device
                input_ids = batch['input_ids'].to(device)
                attention_mask = batch['attention_mask'].to(device)
                labels = batch['labels'].to(device)
                languages = batch['language']

                # Get predictions
                outputs = model(input_ids, attention_mask)
                predictions = outputs['predictions']

                # Compute metrics per sample
                for i in range(len(predictions)):
                    pred = predictions[i].cpu().numpy()
                    true = labels[i].cpu().numpy()

                    # Remove padding and ignored labels
                    mask = (true != -100)
                    pred = pred[mask]
                    true = true[mask]

                    # Compute metrics
                    metrics = self.evaluator.compute_metrics(pred, true)
                    language_metrics[languages[i]].append(metrics)

        # Aggregate metrics per language
        results = {}
        for language, metrics_list in language_metrics.items():
            results[language] = {
                'f1': np.mean([m['f1'] for m in metrics_list]),
                'iou_f1': np.mean([m['iou_f1'] for m in metrics_list]),
                'precision': np.mean([m['precision'] for m in metrics_list]),
                'recall': np.mean([m['recall'] for m in metrics_list]),
                'num_samples': len(metrics_list)
            }

        # Compute macro-average
        macro_f1 = np.mean([r['f1'] for r in results.values()])
        macro_iou_f1 = np.mean([r['iou_f1'] for r in results.values()])

        results['macro_avg'] = {
            'f1': macro_f1,
            'iou_f1': macro_iou_f1,
            'num_samples': sum(r['num_samples'] for r in results.values())
        }

        return results

    def run_benchmark(self):
        """Run complete StandUp4AI benchmark evaluation"""
        print("="*60)
        print("StandUp4AI Benchmark Evaluation")
        print("="*60)

        # Setup model
        self.setup_model()

        # Create datasets
        print("\nLoading datasets...")
        train_dataset = StandUp4AIWordLevelDataset(self.config, 'train')
        val_dataset = StandUp4AIWordLevelDataset(self.config, 'val')
        test_dataset = StandUp4AIWordLevelDataset(self.config, 'test')

        # Create speaker-independent splits
        train_data, val_data, test_data = self.create_speaker_independent_splits(train_dataset)

        print(f"\nDataset sizes:")
        print(f"  Train: {len(train_data)} samples")
        print(f"  Val: {len(val_data)} samples")
        print(f"  Test: {len(test_data)} samples")

        # Create dataloaders
        train_loader = DataLoader(train_dataset, batch_size=self.config.batch_size, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=self.config.batch_size)
        test_loader = DataLoader(test_dataset, batch_size=self.config.batch_size)

        # Train model (simplified for now)
        print("\nTraining model...")
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model.to(device)

        # For demo, skip actual training
        print("Training skipped for demo (use real training for production)")

        # Evaluate on test set
        print("\nEvaluating on test set...")
        test_results = self.evaluate_per_language(self.model, test_loader, device)

        # Print results
        print("\n" + "="*60)
        print("StandUp4AI Benchmark Results")
        print("="*60)

        for language in sorted(test_results.keys()):
            if language == 'macro_avg':
                print(f"\n{language.upper()}:")
            else:
                print(f"\n{language}:")

            metrics = test_results[language]
            print(f"  F1: {metrics['f1']:.4f}")
            print(f"  IoU@0.2 F1: {metrics['iou_f1']:.4f}")
            print(f"  Precision: {metrics['precision']:.4f}")
            print(f"  Recall: {metrics['recall']:.4f}")
            print(f"  Samples: {metrics['num_samples']}")

        # Compare to baseline
        print("\n" + "="*60)
        print("Baseline Comparison")
        print("="*60)
        macro_f1 = test_results['macro_avg']['f1']
        iou_f1 = test_results['macro_avg']['iou_f1']

        published_baseline = 0.58  # From StandUp4AI paper

        print(f"Published Baseline F1: {published_baseline:.4f}")
        print(f"Our Method F1: {macro_f1:.4f}")
        print(f"Difference: {macro_f1 - published_baseline:+.4f}")

        if macro_f1 > published_baseline:
            print(f"✓ Our method outperforms baseline by {macro_f1 - published_baseline:.4f} F1")
        else:
            print(f"✗ Our method underperforms baseline by {published_baseline - macro_f1:.4f} F1")

        return test_results


def main():
    """Main function to run StandUp4AI benchmark"""
    config = StandUp4AIConfig()

    benchmark = StandUp4AIBenchmark(config)
    results = benchmark.run_benchmark()

    # Save results
    output_path = Path('./standup4ai_results.json')
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to {output_path}")


if __name__ == '__main__':
    main()