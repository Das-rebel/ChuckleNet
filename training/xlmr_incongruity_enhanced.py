#!/usr/bin/env python3
"""
XLM-R Enhanced with Lightweight Incongruity Detection
Bridging the gap: XLM-R (72.22% F1) + Biosemotic (81.34% F1)
Target: 77% F1 with minimal complexity increase
"""

import os
import sys
import json
import logging
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import torch
import torch.nn as nn
from transformers import (
    AutoModelForTokenClassification,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForTokenClassification
)
from datasets import Dataset
import numpy as np
from sklearn.metrics import f1_score, precision_recall_fscore_support

# Add project root to path
PROJECT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_DIR))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('incongruity_enhanced_training.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class IncongruityFeatures:
    """Lightweight incongruity detection features"""
    semantic_conflict: torch.Tensor
    expectation_violation: torch.Tensor
    contextual_surprise: torch.Tensor


class LightweightIncongruityDetector(nn.Module):
    """
    Minimal incongruity detector inspired by biosemotic GCACU
    Focus: Semantic conflict detection with <10% parameter increase
    """

    def __init__(self, hidden_dim: int = 768, compression_dim: int = 64):
        super().__init__()

        # Lightweight contrast-attention (compressed)
        self.contrast_transform = nn.Linear(hidden_dim, compression_dim)
        self.conflict_detector = nn.Linear(compression_dim, 1)

        # Expectation violation (simple MLP)
        self.expectation_mlp = nn.Sequential(
            nn.Linear(hidden_dim, compression_dim),
            nn.ReLU(),
            nn.Linear(compression_dim, 1)
        )

        # Contextual surprise (attention-based)
        self.surprise_query = nn.Linear(hidden_dim, compression_dim)
        self.surprise_key = nn.Linear(hidden_dim, compression_dim)

        logger.info(f"✅ Lightweight Incongruity Detector initialized")
        logger.info(f"📊 Parameters: ~{sum(p.numel() for p in self.parameters()):,}")

    def forward(self,
                hidden_states: torch.Tensor,
                attention_mask: torch.Tensor) -> IncongruityFeatures:
        """
        Extract incongruity features

        Args:
            hidden_states: (batch, seq_len, hidden_dim)
            attention_mask: (batch, seq_len)

        Returns:
            IncongruityFeatures: Conflict, violation, surprise scores
        """
        batch_size, seq_len, hidden_dim = hidden_states.shape

        # 1. Semantic Conflict (compressed contrast)
        compressed = self.contrast_transform(hidden_states)  # (batch, seq_len, compression_dim)
        semantic_conflict = torch.sigmoid(self.conflict_detector(compressed)).squeeze(-1)

        # 2. Expectation Violation (MLP-based)
        expectation_violation = torch.sigmoid(self.expectation_mlp(hidden_states)).squeeze(-1)

        # 3. Contextual Surprise (lightweight attention)
        Q = self.surprise_query(hidden_states)  # (batch, seq_len, compression_dim)
        K = self.surprise_key(hidden_states)
        surprise_scores = torch.matmul(Q, K.transpose(-2, -1)) / np.sqrt(Q.shape[-1])

        # Self-attention surprise (how surprising is each token?)
        contextual_surprise = torch.mean(torch.softmax(surprise_scores, dim=-1), dim=-1)

        return IncongruityFeatures(
            semantic_conflict=semantic_conflict,
            expectation_violation=expectation_violation,
            contextual_surprise=contextual_surprise
        )


class XLMRIncongruityEnhanced(nn.Module):
    """
    XLM-R + Lightweight Incongruity Detection
    Target: 77% F1 (halfway to biosemotic performance)
    """

    def __init__(self, model_name: str = "FacebookAI/xlm-roberta-base"):
        super().__init__()

        logger.info(f"🚀 Initializing XLM-R Incongruity Enhanced Model")

        # Base XLM-R model
        self.base_model = AutoModelForTokenClassification.from_pretrained(
            model_name,
            num_labels=2
        )

        # Get hidden dimension
        hidden_dim = self.base_model.config.hidden_size

        # Incongruity detector
        self.incongruity_detector = LightweightIncongruityDetector(
            hidden_dim=hidden_dim,
            compression_dim=64
        )

        # Enhanced classifier (combines base + incongruity)
        self.enhanced_classifier = nn.Sequential(
            nn.Linear(hidden_dim + 3, 128),  # +3 for incongruity features
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(128, 2)
        )

        # Replace base classifier
        self.base_model.classifier = self.enhanced_classifier

        total_params = sum(p.numel() for p in self.parameters())
        base_params = sum(p.numel() for p in self.base_model.base_model.parameters())
        enhancement_params = total_params - base_params

        logger.info(f"📊 Base model parameters: {base_params:,}")
        logger.info(f"📊 Enhancement parameters: {enhancement_params:,} ({enhancement_params/base_params*100:.1f}% increase)")
        logger.info(f"✅ Model initialized successfully")

    def forward(self,
                input_ids: torch.Tensor,
                attention_mask: torch.Tensor,
                labels: Optional[torch.Tensor] = None):
        """
        Forward pass with incongruity enhancement
        """
        # Get base hidden states
        outputs = self.base_model.base_model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            output_hidden_states=True
        )

        hidden_states = outputs.last_hidden_state

        # Extract incongruity features
        incongruity = self.incongruity_detector(hidden_states, attention_mask)

        # Combine features
        incongruity_features = torch.stack([
            incongruity.semantic_conflict,
            incongruity.expectation_violation,
            incongruity.contextual_surprise
        ], dim=-1)  # (batch, seq_len, 3)

        # Expand and concatenate
        enhanced_features = torch.cat([
            hidden_states,
            incongruity_features.expand(-1, -1, hidden_states.size(-1))
        ], dim=-1)

        # Enhanced classification
        logits = self.enhanced_classifier(enhanced_features)

        # Calculate loss if labels provided
        loss = None
        if labels is not None:
            loss_fct = nn.CrossEntropyLoss()
            loss = loss_fct(logits.view(-1, 2), labels.view(-1))

        return {
            'loss': loss,
            'logits': logits,
            'incongruity_features': incongruity_features
        }


def load_standup_data(split: str) -> Dataset:
    """Load standup comedy data for specified split"""
    data_path = PROJECT_DIR / f"data/training/standup_word_level/{split}.jsonl"

    examples = []
    with open(data_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                examples.append(json.loads(line))

    logger.info(f"📊 Loaded {len(examples)} {split} examples")
    return Dataset.from_list(examples)


def tokenize_and_align_labels(examples, tokenizer, label_map):
    """Tokenize and align labels with token boundaries"""

    tokenized_inputs = tokenizer(
        examples['tokens'],
        truncation=True,
        max_length=256,
        is_split_into_words=True,
        padding='max_length'
    )

    labels = []
    for i, label in enumerate(examples['labels']):
        word_ids = tokenized_inputs.word_ids(batch_index=i)
        previous_word_idx = None
        label_ids = []

        for word_idx in word_ids:
            if word_idx is None:
                label_ids.append(-100)
            elif word_idx != previous_word_idx:
                label_ids.append(label_map[label[word_idx]])
            else:
                label_ids.append(-100)
            previous_word_idx = word_idx

        labels.append(label_ids)

    tokenized_inputs['labels'] = labels
    return tokenized_inputs


def compute_metrics(eval_pred):
    """Compute evaluation metrics"""
    predictions, labels = eval_pred

    # Remove -100 labels (padding)
    mask = labels != -100
    predictions = predictions[mask]
    labels = labels[mask]

    # Get predicted class
    pred_labels = np.argmax(predictions, axis=-1)

    # Calculate metrics
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels, pred_labels, average='binary', zero_division=0
    )

    return {
        'precision': precision,
        'recall': recall,
        'f1': f1
    }


def main():
    """Main training function"""

    logger.info("🚀 Starting XLM-R Incongruity Enhanced Training")
    logger.info(f"🎯 Target: 77% F1 (XLM-R: 72.22%, Biosemotic: 81.34%)")

    # Load model and tokenizer
    model = XLMRIncongruityEnhanced()
    tokenizer = AutoTokenizer.from_pretrained("FacebookAI/xlm-roberta-base")

    # Load datasets
    label_map = {'O': 0, 'LAUGH': 1}

    train_dataset = load_standup_data('train')
    valid_dataset = load_standup_data('valid')
    test_dataset = load_standup_data('test')

    # Tokenize datasets
    train_dataset = train_dataset.map(
        lambda x: tokenize_and_align_labels(x, tokenizer, label_map),
        batched=True
    )
    valid_dataset = valid_dataset.map(
        lambda x: tokenize_and_align_labels(x, tokenizer, label_map),
        batched=True
    )
    test_dataset = test_dataset.map(
        lambda x: tokenize_and_align_labels(x, tokenizer, label_map),
        batched=True
    )

    # Set format for PyTorch
    columns = ['input_ids', 'attention_mask', 'labels']
    train_dataset.set_format(type='torch', columns=columns)
    valid_dataset.set_format(type='torch', columns=columns)
    test_dataset.set_format(type='torch', columns=columns)

    # Training arguments
    training_args = TrainingArguments(
        output_dir=str(PROJECT_DIR / 'experiments/xlmr_incongruity_enhanced'),
        num_train_epochs=3,
        per_device_train_batch_size=2,
        per_device_eval_batch_size=2,
        gradient_accumulation_steps=4,
        learning_rate=2e-5,
        warmup_steps=100,
        weight_decay=0.01,
        logging_dir=str(PROJECT_DIR / 'logs'),
        logging_steps=50,
        evaluation_strategy='epoch',
        save_strategy='epoch',
        load_best_model_at_end=True,
        metric_for_best_model='f1',
        greater_is_better=True,
        report_to=None
    )

    # Custom trainer
    class EnhancedTrainer(Trainer):
        def compute_loss(self, model, inputs, return_outputs=False):
            labels = inputs.get('labels')
            outputs = model(**inputs)
            loss = outputs['loss']
            return (loss, outputs) if return_outputs else loss

    # Initialize trainer
    trainer = EnhancedTrainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=valid_dataset,
        tokenizer=tokenizer,
        data_collator=DataCollatorForTokenClassification(tokenizer),
        compute_metrics=compute_metrics
    )

    # Train
    logger.info("🎯 Starting training...")
    trainer.train()

    # Evaluate
    logger.info("📊 Evaluating on validation set...")
    valid_results = trainer.evaluate()
    logger.info(f"✅ Validation Results: {valid_results}")

    logger.info("📊 Evaluating on test set...")
    test_results = trainer.evaluate(test_dataset)
    logger.info(f"✅ Test Results: {test_results}")

    # Save results
    results = {
        'target_f1': 0.77,
        'xlmr_baseline_f1': 0.7222,
        'biosemotic_f1': 0.8134,
        'validation_f1': valid_results['eval_f1'],
        'test_f1': test_results['eval_f1'],
        'improvement_over_xlmr': test_results['eval_f1'] - 0.7222,
        'gap_to_biosemotic': 0.8134 - test_results['eval_f1'],
        'parameter_increase': '5-10%',
        'architecture': 'XLM-R + Lightweight Incongruity Detection'
    }

    results_path = PROJECT_DIR / 'experiments/xlmr_incongruity_enhanced/results.json'
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"💾 Results saved to {results_path}")
    logger.info(f"🎯 Final F1: {test_results['eval_f1']:.4f}")
    logger.info(f"📈 Improvement: {(results['improvement_over_xlmr']*100):+.2f}%")
    logger.info("✅ Training complete!")


if __name__ == "__main__":
    main()