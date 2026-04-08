#!/usr/bin/env python3
"""
Adaptive GCACU - Revolutionary Automatic Complexity Adjustment

Addresses the core issue identified in multilingual experiments:
- Small datasets (4 examples) overfit with complex architectures
- Large datasets underfit with simple architectures
- Optimal complexity varies by data size and language diversity

Key innovation: Automatically adjust model complexity based on:
1. Dataset size (tiny: <100, small: 100-500, medium: 500-2000, large: >2000)
2. Language diversity (monolingual vs multilingual)
3. Data quality indicators (label noise, feature variance)
4. Computational constraints

Target: Work well on both small (100 examples) and large (100K+ examples) datasets
"""

import sys
import json
import logging
import argparse
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple, Any, Optional, Callable
from datetime import datetime
from copy import deepcopy
from collections import defaultdict

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset

sys.path.insert(0, str(Path(__file__).parent))
from gcacu_network import GCACUTokenClassifier, AdaptiveFocalLoss, create_gcacu_model, GCACUConfig


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class DatasetCharacteristics:
    """Analysis of dataset characteristics for adaptive decisions"""
    size: int
    n_languages: int
    avg_sequence_length: float
    label_balance: float  # Ratio of positive to negative labels
    feature_variance: float  # Variance in embeddings
    estimated_noise: float  # Estimated label noise (0-1)
    complexity_score: float  # Overall complexity score (0-1)


@dataclass
class AdaptiveConfig:
    """Adaptively determined configuration"""
    # Model architecture
    gcacu_dim: int
    num_heads: int
    num_gating_levels: int
    hidden_dim: int

    # Training parameters
    learning_rate: float
    batch_size: int
    epochs: int
    warmup_ratio: float

    # Regularization
    dropout: float
    weight_decay: float
    label_smoothing: float

    # Loss function
    focal_gamma: float
    positive_class_weight: float

    # Data augmentation
    use_augmentation: bool
    augmentation_strength: float

    # Architecture adaptations
    use_gradient_checkpointing: bool
    use_mixed_precision: bool
    use_early_stopping: bool


class DatasetAnalyzer:
    """
    Analyze dataset characteristics to inform adaptive decisions
    """

    @staticmethod
    def analyze_characteristics(dataset: List[Dict],
                               tokenizer: Any = None) -> DatasetCharacteristics:
        """
        Comprehensive dataset analysis
        """
        logger.info("Analyzing dataset characteristics...")

        # Basic statistics
        size = len(dataset)
        languages = list(set([ex.get('language', 'en') for ex in dataset]))
        n_languages = len(languages)

        # Sequence length statistics
        sequence_lengths = [len(ex.get('words', [])) for ex in dataset]
        avg_sequence_length = np.mean(sequence_lengths)

        # Label balance
        positive_counts = []
        negative_counts = []
        for ex in dataset:
            labels = ex.get('labels', [])
            positive_counts.append(sum(labels))
            negative_counts.append(len(labels) - sum(labels))

        total_positive = sum(positive_counts)
        total_negative = sum(negative_counts)
        label_balance = total_positive / (total_positive + total_negative + 1e-8)

        # Feature variance (estimated from text diversity)
        word_sets = [set(ex.get('words', [])) for ex in dataset]
        unique_words = set()
        for word_set in word_sets:
            unique_words.update(word_set)
        feature_variance = min(1.0, len(unique_words) / (size * 50))  # Normalized

        # Noise estimation (based on label consistency patterns)
        estimated_noise = DatasetAnalyzer._estimate_noise(dataset)

        # Overall complexity score
        complexity_score = DatasetAnalyzer._compute_complexity_score(
            size, n_languages, avg_sequence_length, label_balance,
            feature_variance, estimated_noise
        )

        characteristics = DatasetCharacteristics(
            size=size,
            n_languages=n_languages,
            avg_sequence_length=avg_sequence_length,
            label_balance=label_balance,
            feature_variance=feature_variance,
            estimated_noise=estimated_noise,
            complexity_score=complexity_score
        )

        logger.info(f"Dataset analysis complete:")
        logger.info(f"  Size: {size}, Languages: {n_languages}")
        logger.info(f"  Label balance: {label_balance:.3f}")
        logger.info(f"  Complexity score: {complexity_score:.3f}")

        return characteristics

    @staticmethod
    def _estimate_noise(dataset: List[Dict]) -> float:
        """
        Estimate label noise based on patterns
        Higher noise = inconsistent labels, outliers
        """
        # Simplified noise estimation
        # In production, this would use more sophisticated methods

        if len(dataset) < 10:
            return 0.5  # High uncertainty for tiny datasets

        # Check for label inconsistencies
        label_ratios = []
        for ex in dataset:
            labels = ex.get('labels', [])
            if len(labels) > 0:
                ratio = sum(labels) / len(labels)
                label_ratios.append(ratio)

        if len(label_ratios) == 0:
            return 0.5

        # High variance in label ratios suggests potential noise
        variance = np.var(label_ratios)
        noise_score = min(1.0, variance * 5)  # Scale to 0-1

        return noise_score

    @staticmethod
    def _compute_complexity_score(size: int, n_languages: int,
                                 avg_seq_length: float, label_balance: float,
                                 feature_variance: float, estimated_noise: float) -> float:
        """
        Compute overall complexity score (0-1)
        Higher score = more complex dataset
        """
        # Size component (logarithmic scaling)
        size_score = min(1.0, np.log10(size + 1) / 4)  # Log scale up to 10K examples

        # Language diversity
        language_score = min(1.0, n_languages / 10)  # Up to 10 languages

        # Sequence length (longer = more complex)
        length_score = min(1.0, avg_seq_length / 200)  # Normalize to 200 words

        # Label imbalance (more imbalance = more complex)
        imbalance_score = abs(label_balance - 0.5) * 2  # 0 when balanced, 1 when extreme

        # Combined score
        complexity = (
            0.3 * size_score +
            0.2 * language_score +
            0.2 * length_score +
            0.15 * imbalance_score +
            0.1 * feature_variance +
            0.05 * estimated_noise
        )

        return complexity


class AdaptiveGCACUController:
    """
    Main controller for adaptive GCACU configuration
    """

    # Predefined configurations for different scenarios
    SCENARIO_CONFIGS = {
        'tiny_monolingual': {  # < 100 examples, 1 language
            'gcacu_dim': 64,
            'num_heads': 2,
            'num_gating_levels': 2,
            'hidden_dim': 128,
            'learning_rate': 1e-5,
            'batch_size': 4,
            'epochs': 3,
            'dropout': 0.4,
            'weight_decay': 0.05,
            'label_smoothing': 0.2,
            'focal_gamma': 3.0,
            'use_augmentation': True,
            'augmentation_strength': 0.7,
            'use_early_stopping': True
        },
        'tiny_multilingual': {  # < 100 examples, multiple languages
            'gcacu_dim': 48,
            'num_heads': 2,
            'num_gating_levels': 2,
            'hidden_dim': 96,
            'learning_rate': 8e-6,
            'batch_size': 2,
            'epochs': 2,
            'dropout': 0.5,
            'weight_decay': 0.08,
            'label_smoothing': 0.3,
            'focal_gamma': 4.0,
            'use_augmentation': True,
            'augmentation_strength': 0.9,
            'use_early_stopping': True
        },
        'small_monolingual': {  # 100-500 examples
            'gcacu_dim': 96,
            'num_heads': 3,
            'num_gating_levels': 2,
            'hidden_dim': 192,
            'learning_rate': 1.5e-5,
            'batch_size': 8,
            'epochs': 4,
            'dropout': 0.3,
            'weight_decay': 0.03,
            'label_smoothing': 0.1,
            'focal_gamma': 2.5,
            'use_augmentation': True,
            'augmentation_strength': 0.5,
            'use_early_stopping': True
        },
        'small_multilingual': {  # 100-500 examples, multiple languages
            'gcacu_dim': 80,
            'num_heads': 3,
            'num_gating_levels': 2,
            'hidden_dim': 160,
            'learning_rate': 1.2e-5,
            'batch_size': 6,
            'epochs': 3,
            'dropout': 0.35,
            'weight_decay': 0.04,
            'label_smoothing': 0.15,
            'focal_gamma': 3.0,
            'use_augmentation': True,
            'augmentation_strength': 0.6,
            'use_early_stopping': True
        },
        'medium_monolingual': {  # 500-2000 examples
            'gcacu_dim': 128,
            'num_heads': 4,
            'num_gating_levels': 3,
            'hidden_dim': 256,
            'learning_rate': 2e-5,
            'batch_size': 12,
            'epochs': 5,
            'dropout': 0.2,
            'weight_decay': 0.02,
            'label_smoothing': 0.05,
            'focal_gamma': 2.0,
            'use_augmentation': True,
            'augmentation_strength': 0.3,
            'use_early_stopping': True
        },
        'medium_multilingual': {  # 500-2000 examples, multiple languages
            'gcacu_dim': 112,
            'num_heads': 4,
            'num_gating_levels': 3,
            'hidden_dim': 224,
            'learning_rate': 1.8e-5,
            'batch_size': 10,
            'epochs': 4,
            'dropout': 0.25,
            'weight_decay': 0.025,
            'label_smoothing': 0.08,
            'focal_gamma': 2.2,
            'use_augmentation': True,
            'augmentation_strength': 0.4,
            'use_early_stopping': True
        },
        'large_monolingual': {  # > 2000 examples
            'gcacu_dim': 192,
            'num_heads': 6,
            'num_gating_levels': 3,
            'hidden_dim': 384,
            'learning_rate': 3e-5,
            'batch_size': 16,
            'epochs': 6,
            'dropout': 0.15,
            'weight_decay': 0.01,
            'label_smoothing': 0.02,
            'focal_gamma': 1.5,
            'use_augmentation': False,
            'augmentation_strength': 0.1,
            'use_early_stopping': False
        },
        'large_multilingual': {  # > 2000 examples, multiple languages
            'gcacu_dim': 176,
            'num_heads': 6,
            'num_gating_levels': 3,
            'hidden_dim': 352,
            'learning_rate': 2.5e-5,
            'batch_size': 14,
            'epochs': 5,
            'dropout': 0.18,
            'weight_decay': 0.015,
            'label_smoothing': 0.03,
            'focal_gamma': 1.8,
            'use_augmentation': False,
            'augmentation_strength': 0.15,
            'use_early_stopping': False
        }
    }

    def __init__(self):
        self.analyzer = DatasetAnalyzer()

    def determine_scenario(self, characteristics: DatasetCharacteristics) -> str:
        """
        Determine the scenario based on dataset characteristics
        """
        size = characteristics.size
        n_languages = characteristics.n_languages

        # Determine size category
        if size < 100:
            size_category = 'tiny'
        elif size < 500:
            size_category = 'small'
        elif size < 2000:
            size_category = 'medium'
        else:
            size_category = 'large'

        # Determine language category
        language_category = 'multilingual' if n_languages > 1 else 'monolingual'

        scenario = f"{size_category}_{language_category}"

        logger.info(f"Determined scenario: {scenario}")
        return scenario

    def interpolate_config(self, characteristics: DatasetCharacteristics) -> AdaptiveConfig:
        """
        Interpolate between predefined configurations based on dataset characteristics
        """
        scenario = self.determine_scenario(characteristics)
        base_config = self.SCENARIO_CONFIGS[scenario].copy()

        # Fine-tune based on specific characteristics
        config = self._fine_tune_config(base_config, characteristics)

        return AdaptiveConfig(**config)

    def _fine_tune_config(self, base_config: Dict,
                         characteristics: DatasetCharacteristics) -> Dict:
        """
        Fine-tune base configuration based on specific dataset characteristics
        """
        config = base_config.copy()

        # Adjust for label imbalance
        if characteristics.label_balance < 0.1:  # Very few positive examples
            config['positive_class_weight'] = 8.0
            config['focal_gamma'] = max(config['focal_gamma'], 3.0)
        elif characteristics.label_balance > 0.9:  # Very few negative examples
            config['positive_class_weight'] = 0.5
        else:
            config['positive_class_weight'] = 4.0

        # Adjust for estimated noise
        if characteristics.estimated_noise > 0.5:  # High noise
            config['label_smoothing'] += 0.1
            config['dropout'] = min(config['dropout'] + 0.1, 0.6)
            config['focal_gamma'] = max(config['focal_gamma'] + 0.5, 4.0)

        # Adjust for complexity score
        if characteristics.complexity_score > 0.7:  # High complexity
            config['epochs'] = max(config['epochs'] + 1, 2)
            config['learning_rate'] *= 0.8  # Lower learning rate for complex data
        elif characteristics.complexity_score < 0.3:  # Low complexity
            config['epochs'] = max(config['epochs'] - 1, 2)
            config['learning_rate'] *= 1.2  # Higher learning rate for simple data

        # Ensure parameters stay within reasonable bounds
        config['learning_rate'] = max(1e-6, min(config['learning_rate'], 1e-3))
        config['dropout'] = max(0.1, min(config['dropout'], 0.6))
        config['epochs'] = max(2, min(config['epochs'], 10))

        return config

    def create_adaptive_model(self,
                             backbone: nn.Module,
                             characteristics: DatasetCharacteristics) -> Tuple[nn.Module, AdaptiveConfig]:
        """
        Create GCACU model with adaptive configuration
        """
        # Determine adaptive configuration
        config = self.interpolate_config(characteristics)

        logger.info(f"Creating adaptive model with config:")
        logger.info(f"  GCACU dim: {config.gcacu_dim}, Heads: {config.num_heads}")
        logger.info(f"  Learning rate: {config.learning_rate:.2e}")
        logger.info(f"  Batch size: {config.batch_size}, Epochs: {config.epochs}")
        logger.info(f"  Dropout: {config.dropout}, Weight decay: {config.weight_decay}")

        # Create GCACU model
        model = create_gcacu_model(
            backbone,
            gcacu_dim=config.gcacu_dim,
            num_heads=config.num_heads,
            gate_scale=0.3  # Could also be made adaptive
        )

        return model, config


class AdaptiveTrainer:
    """
    Training orchestrator with adaptive features
    """

    def __init__(self, model: nn.Module, config: AdaptiveConfig):
        self.model = model
        self.config = config
        self.device = torch.device("cuda" if torch.cuda.is_available() else
                                  ("mps" if torch.backends.mps.is_available() else "cpu"))

    def train(self,
             train_loader: DataLoader,
             valid_loader: DataLoader,
             test_loader: DataLoader) -> Dict:
        """
        Train with adaptive configuration
        """
        logger.info("Starting adaptive training...")

        # Setup optimizer with adaptive parameters
        optimizer = torch.optim.AdamW(
            self.model.parameters(),
            lr=self.config.learning_rate,
            weight_decay=self.config.weight_decay
        )

        # Setup loss function with adaptive parameters
        criterion = AdaptiveFocalLoss(
            gamma=self.config.focal_gamma,
            label_smoothing=self.config.label_smoothing
        )

        # Training loop with adaptive epochs
        best_valid_f1 = 0.0
        patience_counter = 0

        for epoch in range(self.config.epochs):
            logger.info(f"Epoch {epoch + 1}/{self.config.epochs}")

            # Train epoch
            train_metrics = self._train_epoch(train_loader, optimizer, criterion)
            logger.info(f"Train - Loss: {train_metrics['loss']:.4f}, F1: {train_metrics['f1']:.4f}")

            # Validate
            valid_metrics = self._validate(valid_loader, criterion)
            logger.info(f"Valid - Loss: {valid_metrics['loss']:.4f}, F1: {valid_metrics['f1']:.4f}")

            # Check for improvement
            if valid_metrics['f1'] > best_valid_f1 + 0.001:
                best_valid_f1 = valid_metrics['f1']
                patience_counter = 0
                logger.info(f"New best validation F1: {best_valid_f1:.4f}")
            else:
                patience_counter += 1

            # Early stopping if enabled
            if self.config.use_early_stopping and patience_counter >= 3:
                logger.info("Early stopping triggered")
                break

        # Final test evaluation
        test_metrics = self._validate(test_loader, criterion)
        logger.info(f"Test - Loss: {test_metrics['loss']:.4f}, F1: {test_metrics['f1']:.4f}")

        return {
            'train_metrics': train_metrics,
            'valid_metrics': valid_metrics,
            'test_metrics': test_metrics,
            'best_valid_f1': best_valid_f1,
            'config': asdict(self.config)
        }

    def _train_epoch(self, dataloader: DataLoader, optimizer: torch.optim.Optimizer,
                    criterion: nn.Module) -> Dict:
        """Single training epoch"""
        self.model.train()
        total_loss = 0
        all_preds = []
        all_labels = []

        for batch in dataloader:
            # Move to device
            input_ids = batch['input_ids'].to(self.device)
            attention_mask = batch['attention_mask'].to(self.device)
            labels = batch['labels'].to(self.device)

            # Forward pass
            outputs = self.model(input_ids, attention_mask)
            logits = outputs.logits

            # Compute loss
            loss = criterion(logits.view(-1, 2), labels.view(-1))

            # Backward pass
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
            optimizer.step()

            total_loss += loss.item()

            # Collect predictions
            preds = torch.argmax(logits, dim=-1)
            all_preds.append(preds.cpu())
            all_labels.append(labels.cpu())

        # Compute metrics
        all_preds = torch.cat(all_preds)
        all_labels = torch.cat(all_labels)
        f1 = self._compute_f1(all_preds, all_labels)

        return {
            'loss': total_loss / len(dataloader),
            'f1': f1
        }

    def _validate(self, dataloader: DataLoader, criterion: nn.Module) -> Dict:
        """Validation"""
        self.model.eval()
        total_loss = 0
        all_preds = []
        all_labels = []

        with torch.no_grad():
            for batch in dataloader:
                input_ids = batch['input_ids'].to(self.device)
                attention_mask = batch['attention_mask'].to(self.device)
                labels = batch['labels'].to(self.device)

                outputs = self.model(input_ids, attention_mask)
                logits = outputs.logits

                loss = criterion(logits.view(-1, 2), labels.view(-1))
                total_loss += loss.item()

                preds = torch.argmax(logits, dim=-1)
                all_preds.append(preds.cpu())
                all_labels.append(labels.cpu())

        all_preds = torch.cat(all_preds)
        all_labels = torch.cat(all_labels)
        f1 = self._compute_f1(all_preds, all_labels)

        return {
            'loss': total_loss / len(dataloader),
            'f1': f1
        }

    def _compute_f1(self, preds: torch.Tensor, labels: torch.Tensor) -> float:
        """Compute F1 score"""
        tp = ((preds == 1) & (labels == 1)).sum().item()
        fp = ((preds == 1) & (labels == 0)).sum().item()
        fn = ((preds == 0) & (labels == 1)).sum().item()

        precision = tp / (tp + fp + 1e-8)
        recall = tp / (tp + fn + 1e-8)
        f1 = 2 * precision * recall / (precision + recall + 1e-8)

        return f1


def load_jsonl_data(path: Path) -> List[Dict]:
    """Load JSONL dataset"""
    examples = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            examples.append(json.loads(line))
    return examples


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description="Adaptive GCACU System")
    parser.add_argument("--train-file", type=str, required=True)
    parser.add_argument("--valid-file", type=str, required=True)
    parser.add_argument("--test-file", type=str, required=True)
    parser.add_argument("--model-name", type=str, default="FacebookAI/xlm-roberta-base")
    parser.add_argument("--output-dir", type=str, default="adaptive_gcacu_results")

    args = parser.parse_args()

    # Load data
    logger.info("Loading datasets...")
    train_data = load_jsonl_data(Path(args.train_file))
    valid_data = load_jsonl_data(Path(args.valid_file))
    test_data = load_jsonl_data(Path(args.test_file))

    # Combine for analysis
    all_data = train_data + valid_data

    # Create adaptive controller
    controller = AdaptiveGCACUController()

    # Analyze dataset
    characteristics = controller.analyzer.characteristics(all_data)

    # Create backbone model
    logger.info("Loading backbone model...")
    from transformers import AutoModelForTokenClassification
    backbone = AutoModelForTokenClassification.from_pretrained(
        args.model_name,
        num_labels=2
    )

    # Create adaptive model
    model, adaptive_config = controller.create_adaptive_model(backbone, characteristics)

    # Save configuration
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    config_path = output_dir / "adaptive_config.json"
    with open(config_path, 'w') as f:
        json.dump({
            'characteristics': asdict(characteristics),
            'adaptive_config': asdict(adaptive_config)
        }, f, indent=2)

    logger.info(f"Adaptive configuration saved to: {config_path}")
    logger.info("Adaptive GCACU system ready for training!")

    return {
        'characteristics': characteristics,
        'adaptive_config': adaptive_config
    }


if __name__ == "__main__":
    main()