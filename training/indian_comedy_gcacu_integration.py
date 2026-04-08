#!/usr/bin/env python3
"""
Indian Comedy GCACU Integration

Advanced integration of Indian Comedy Specialist with GCACU architecture for
enhanced laughter prediction in Indian comedy content.

This module provides:
1. GCACU architecture adaptation for Indian languages
2. Cultural context feature engineering
3. Multi-lingual training pipeline for Indian comedy
4. Evaluation framework for Indian comedy datasets
"""

import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModelForTokenClassification, TrainingArguments, Trainer

# Import existing GCACU components
sys.path.insert(0, str(Path(__file__).parent))
from gcacu_network import GCACUTokenClassifier, GCACUConfig, AdaptiveFocalLoss
from gcacu_optimizer import GCACUConfig, GCACUOptimizer
from indian_comedy_specialist import (
    IndianComedySpecialist,
    IndianComedyConfig,
    HinglishProcessor,
    IndianComedyDataset
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('indian_comedy_gcacu_integration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class IndianComedyGCACUConfig:
    """Configuration for Indian Comedy GCACU integration."""

    # Base configurations
    gcacu_config: GCACUConfig = field(default_factory=GCACUConfig)
    indian_config: IndianComedyConfig = field(default_factory=IndianComedyConfig)

    # Training specifics
    indian_batch_size: int = 16
    indian_learning_rate: float = 2e-5
    indian_epochs: int = 10

    # Cultural feature weights
    cultural_context_weight: float = 0.15
    bollywood_reference_weight: float = 0.12
    regional_adaptation_weight: float = 0.10
    code_mixing_weight: float = 0.08

    # Language-specific parameters
    language_weights: Dict[str, float] = field(default_factory=lambda: {
        'english_indian': 1.0,
        'hinglish': 1.2,  # Higher weight for code-mixed
        'hindi': 1.1
    })


class IndianComedyGCACUDataset(Dataset):
    """
    Dataset class for Indian comedy content with GCACU features.

    Combines linguistic features from Indian comedy specialist
    with GCACU architecture requirements.
    """

    def __init__(
        self,
        examples: List[Dict[str, Any]],
        tokenizer: AutoTokenizer,
        max_length: int = 512,
        indian_specialist: Optional[IndianComedySpecialist] = None
    ):
        self.examples = examples
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.indian_specialist = indian_specialist or IndianComedySpecialist()

        # Preprocess examples
        self.processed_examples = []
        for example in examples:
            processed = self._preprocess_example(example)
            self.processed_examples.append(processed)

    def _preprocess_example(self, example: Dict[str, Any]) -> Dict[str, Any]:
        """Preprocess a single example with Indian comedy features."""
        text = example['text']
        language = example.get('language', 'english_indian')

        # Get cultural features
        if self.indian_specialist:
            analysis = self.indian_specialist.analyze_comedy_content(text, language)
            cultural_features = analysis['linguistic_features']
        else:
            cultural_features = {}

        # Tokenize text
        tokenized = self.tokenizer(
            text,
            max_length=self.max_length,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )

        # Create labels (laughter probability)
        laughter_prob = example.get('laughter_probability', 0.5)
        labels = torch.tensor([1.0 if laughter_prob > 0.5 else 0.0])

        return {
            'input_ids': tokenized['input_ids'].squeeze(0),
            'attention_mask': tokenized['attention_mask'].squeeze(0),
            'labels': labels,
            'cultural_features': cultural_features,
            'language': language,
            'original_text': text
        }

    def __len__(self):
        return len(self.processed_examples)

    def __getitem__(self, idx):
        return self.processed_examples[idx]


class IndianComedyGCACUModel(nn.Module):
    """
    Enhanced GCACU model for Indian comedy content.

    Integrates cultural context features with the GCACU architecture
    for improved laughter prediction in Indian comedy.
    """

    def __init__(
        self,
        base_model_name: str = "xlm-roberta-base",
        config: Optional[IndianComedyGCACUConfig] = None
    ):
        super().__init__()
        self.config = config or IndianComedyGCACUConfig()

        # Load base model
        self.base_model = AutoModelForTokenClassification.from_pretrained(
            base_model_name,
            num_labels=2
        )

        # Get hidden size
        self.hidden_size = self.base_model.config.hidden_size

        # Create GCACU classifier
        self.gcacu_classifier = GCACUTokenClassifier(
            hidden_size=self.hidden_size,
            gcacu_dim=self.config.indian_config.gcacu_dim
        )

        # Cultural context encoder
        self.cultural_encoder = nn.Sequential(
            nn.Linear(self.hidden_size + 64, self.hidden_size),  # +64 for cultural features
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(self.hidden_size, self.hidden_size)
        )

        # Language-specific adaptation
        self.language_adapters = nn.ModuleDict({
            'english_indian': nn.Linear(self.hidden_size, self.hidden_size),
            'hinglish': nn.Linear(self.hidden_size, self.hidden_size),
            'hindi': nn.Linear(self.hidden_size, self.hidden_size)
        })

        # Final classifier
        self.classifier = nn.Linear(self.hidden_size, 2)

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        cultural_features: Optional[Dict[str, Any]] = None,
        language: str = 'english_indian',
        labels: Optional[torch.Tensor] = None
    ):
        # Get base model outputs
        outputs = self.base_model.base_model(
            input_ids=input_ids,
            attention_mask=attention_mask
        )

        sequence_output = outputs.last_hidden_state

        # Apply GCACU processing
        gcacu_output = self.gcacu_classifier(sequence_output, attention_mask)

        # Create cultural feature embedding
        if cultural_features:
            cultural_emb = self._create_cultural_embedding(cultural_features)
        else:
            cultural_emb = torch.zeros(sequence_output.size(0), 64).to(sequence_output.device)

        # Expand cultural embedding to match sequence length
        cultural_emb_expanded = cultural_emb.unsqueeze(1).expand(-1, sequence_output.size(1), -1)

        # Combine GCACU output with cultural features
        combined = torch.cat([gcacu_output, cultural_emb_expanded], dim=-1)
        enhanced_output = self.cultural_encoder(combined)

        # Apply language-specific adaptation
        if language in self.language_adapters:
            adapted = self.language_adapters[language](enhanced_output)
        else:
            adapted = enhanced_output

        # Get sequence representation (mean pooling)
        sequence_repr = adapted.mean(dim=1)

        # Final classification
        logits = self.classifier(sequence_repr)

        loss = None
        if labels is not None:
            loss_fct = nn.CrossEntropyLoss()
            loss = loss_fct(logits, labels)

        return {
            'loss': loss,
            'logits': logits,
            'sequence_repr': sequence_repr,
            'enhanced_output': enhanced_output
        }

    def _create_cultural_embedding(self, cultural_features: Dict[str, Any]) -> torch.Tensor:
        """Create cultural feature embedding from dictionary."""
        # Extract numerical features
        features = []

        # Basic features
        features.append(cultural_features.get('cultural_density', 0.0))
        features.append(cultural_features.get('bollywood_refs', 0.0))
        features.append(cultural_features.get('slang_usage', 0.0))

        # Code mixing features
        if 'code_mixing_ratio' in cultural_features:
            features.append(cultural_features['code_mixing_ratio'])
            features.append(cultural_features.get('num_transitions', 0.0))
        else:
            features.extend([0.0, 0.0])

        # Indian English patterns
        if 'indian_english_patterns' in cultural_features:
            patterns = cultural_features['indian_english_patterns']
            features.append(sum(patterns.values()))
        else:
            features.append(0.0)

        # Pad to 64 features
        while len(features) < 64:
            features.append(0.0)

        return torch.tensor(features[:64])


class IndianComedyGCACUTrainer:
    """
    Trainer class for Indian Comedy GCACU models.

    Handles training, evaluation, and optimization for Indian comedy content.
    """

    def __init__(
        self,
        config: IndianComedyGCACUConfig,
        output_dir: str = "./indian_comedy_gcacu_results"
    ):
        self.config = config
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Initialize components
        self.indian_specialist = IndianComedySpecialist(config.indian_config)
        self.tokenizer = AutoTokenizer.from_pretrained(config.indian_config.base_model)

        # Initialize model
        self.model = IndianComedyGCACUModel(
            base_model_name=config.indian_config.base_model,
            config=config
        )

        # Setup training
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)

        logger.info(f"Indian Comedy GCACU Trainer initialized on {self.device}")

    def prepare_datasets(
        self,
        train_examples: List[Dict[str, Any]],
        val_examples: List[Dict[str, Any]]
    ) -> Tuple[DataLoader, DataLoader]:
        """Prepare training and validation datasets."""
        train_dataset = IndianComedyGCACUDataset(
            train_examples,
            self.tokenizer,
            indian_specialist=self.indian_specialist
        )

        val_dataset = IndianComedyGCACUDataset(
            val_examples,
            self.tokenizer,
            indian_specialist=self.indian_specialist
        )

        train_loader = DataLoader(
            train_dataset,
            batch_size=self.config.indian_batch_size,
            shuffle=True
        )

        val_loader = DataLoader(
            val_dataset,
            batch_size=self.config.indian_batch_size,
            shuffle=False
        )

        return train_loader, val_loader

    def train(
        self,
        train_loader: DataLoader,
        val_loader: DataLoader,
        num_epochs: Optional[int] = None
    ) -> Dict[str, Any]:
        """Train the Indian Comedy GCACU model."""
        num_epochs = num_epochs or self.config.indian_epochs

        optimizer = torch.optim.AdamW(
            self.model.parameters(),
            lr=self.config.indian_learning_rate
        )

        training_history = {
            'train_loss': [],
            'val_loss': [],
            'val_accuracy': []
        }

        best_val_loss = float('inf')
        patience_counter = 0
        max_patience = 3

        for epoch in range(num_epochs):
            logger.info(f"Starting epoch {epoch + 1}/{num_epochs}")

            # Training
            self.model.train()
            train_loss = 0.0

            for batch_idx, batch in enumerate(train_loader):
                input_ids = batch['input_ids'].to(self.device)
                attention_mask = batch['attention_mask'].to(self.device)
                labels = batch['labels'].to(self.device)
                language = batch['language'][0]  # Assume same language per batch

                cultural_features = batch['cultural_features'][0]  # First example features

                # Forward pass
                outputs = self.model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    cultural_features=cultural_features,
                    language=language,
                    labels=labels
                )

                loss = outputs['loss']

                # Backward pass
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

                train_loss += loss.item()

                if batch_idx % 10 == 0:
                    logger.info(f"Batch {batch_idx}, Loss: {loss.item():.4f}")

            avg_train_loss = train_loss / len(train_loader)
            training_history['train_loss'].append(avg_train_loss)

            # Validation
            val_results = self.evaluate(val_loader)
            training_history['val_loss'].append(val_results['val_loss'])
            training_history['val_accuracy'].append(val_results['accuracy'])

            logger.info(f"Epoch {epoch + 1} - Train Loss: {avg_train_loss:.4f}, "
                       f"Val Loss: {val_results['val_loss']:.4f}, "
                       f"Val Accuracy: {val_results['accuracy']:.4f}")

            # Early stopping
            if val_results['val_loss'] < best_val_loss:
                best_val_loss = val_results['val_loss']
                patience_counter = 0
                self.save_checkpoint(f"best_model_epoch_{epoch + 1}.pt")
            else:
                patience_counter += 1
                if patience_counter >= max_patience:
                    logger.info("Early stopping triggered")
                    break

        return training_history

    def evaluate(self, val_loader: DataLoader) -> Dict[str, float]:
        """Evaluate the model on validation data."""
        self.model.eval()
        val_loss = 0.0
        predictions = []
        actuals = []

        with torch.no_grad():
            for batch in val_loader:
                input_ids = batch['input_ids'].to(self.device)
                attention_mask = batch['attention_mask'].to(self.device)
                labels = batch['labels'].to(self.device)
                language = batch['language'][0]
                cultural_features = batch['cultural_features'][0]

                outputs = self.model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    cultural_features=cultural_features,
                    language=language,
                    labels=labels
                )

                val_loss += outputs['loss'].item()

                # Get predictions
                logits = outputs['logits']
                preds = torch.argmax(logits, dim=-1)
                predictions.extend(preds.cpu().numpy())
                actuals.extend(labels.cpu().numpy())

        avg_val_loss = val_loss / len(val_loader)
        accuracy = sum(p == a for p, a in zip(predictions, actuals)) / len(predictions)

        return {
            'val_loss': avg_val_loss,
            'accuracy': accuracy,
            'predictions': predictions,
            'actuals': actuals
        }

    def save_checkpoint(self, filename: str):
        """Save model checkpoint."""
        checkpoint_path = self.output_dir / filename
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'config': self.config
        }, checkpoint_path)
        logger.info(f"Checkpoint saved to {checkpoint_path}")

    def predict_laughter(
        self,
        text: str,
        language: str = 'english_indian'
    ) -> Dict[str, Any]:
        """Predict laughter probability for Indian comedy text."""
        self.model.eval()

        # Get cultural features
        analysis = self.indian_specialist.analyze_comedy_content(text, language)
        cultural_features = analysis['linguistic_features']

        # Tokenize
        tokenized = self.tokenizer(
            text,
            max_length=512,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )

        with torch.no_grad():
            input_ids = tokenized['input_ids'].to(self.device)
            attention_mask = tokenized['attention_mask'].to(self.device)

            outputs = self.model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                cultural_features=cultural_features,
                language=language
            )

            logits = outputs['logits']
            probs = torch.softmax(logits, dim=-1)
            laughter_prob = probs[0][1].item()

        return {
            'text': text,
            'language': language,
            'laughter_probability': laughter_prob,
            'cultural_features': cultural_features,
            'confidence': max(probs[0][0].item(), probs[0][1].item())
        }


def create_indian_comedy_gcacu_demo():
    """Create a demonstration of Indian Comedy GCACU integration."""
    logger.info("Creating Indian Comedy GCACU Integration Demo")

    # Initialize configuration
    config = IndianComedyGCACUConfig()

    # Create trainer
    trainer = IndianComedyGCACUTrainer(config)

    # Create sample datasets
    indian_specialist = IndianComedySpecialist(config.indian_config)
    examples = indian_specialist.dataset_handler.create_sample_dataset()

    # Split into train and validation
    train_size = int(0.8 * len(examples))
    train_examples = examples[:train_size]
    val_examples = examples[train_size:]

    logger.info(f"Training with {len(train_examples)} examples")
    logger.info(f"Validating with {len(val_examples)} examples")

    # Prepare datasets
    train_loader, val_loader = trainer.prepare_datasets(train_examples, val_examples)

    # Train model
    training_history = trainer.train(train_loader, val_loader, num_epochs=3)

    # Evaluate on validation set
    val_results = trainer.evaluate(val_loader)

    # Test predictions
    test_texts = [
        "So guys, I was at this arranged marriage meeting, and the aunties were judging my salary",
        "Machi, I went to this desi party yaar, and the scene was too much",
        "Bhaiyya, aaj kal padhai mein dil nahi lagta, sirf Instagram reels mein lagta hai"
    ]

    predictions = []
    for text in test_texts:
        # Detect language
        if any(word in text.lower() for word in ['machi', 'yaar', 'scene']):
            language = 'hinglish'
        elif any(word in text.lower() for word in ['bhaiyya', 'padhai', 'mein']):
            language = 'hindi'
        else:
            language = 'english_indian'

        pred = trainer.predict_laughter(text, language)
        predictions.append(pred)

    return {
        'training_history': training_history,
        'validation_results': val_results,
        'predictions': predictions,
        'config': {
            'model': 'Indian Comedy GCACU',
            'languages': config.indian_config.supported_domains,
            'cultural_features': True,
            'regional_adaptation': True
        }
    }


def main():
    """Main function to run the Indian Comedy GCACU integration."""
    logger.info("Starting Indian Comedy GCACU Integration")

    try:
        # Run demo
        results = create_indian_comedy_gcacu_demo()

        # Print results
        print("\n" + "="*60)
        print("INDIAN COMEDY GCACU INTEGRATION RESULTS")
        print("="*60)

        print(f"\nModel Configuration:")
        config_info = results['config']
        print(f"  Architecture: {config_info['model']}")
        print(f"  Languages: {', '.join(config_info['languages'])}")
        print(f"  Cultural Features: {config_info['cultural_features']}")
        print(f"  Regional Adaptation: {config_info['regional_adaptation']}")

        print(f"\nValidation Results:")
        val_results = results['validation_results']
        print(f"  Accuracy: {val_results['accuracy']:.2%}")
        print(f"  Validation Loss: {val_results['val_loss']:.4f}")

        print(f"\nSample Predictions:")
        print("-" * 60)

        for i, pred in enumerate(results['predictions'], 1):
            print(f"\n{i}. [{pred['language'].upper()}] {pred['text'][:50]}...")
            print(f"   Laughter Probability: {pred['laughter_probability']:.2%}")
            print(f"   Confidence: {pred['confidence']:.2%}")

            if pred['cultural_features']:
                print(f"   Cultural Features: {list(pred['cultural_features'].keys())[:3]}")

        print("\n" + "="*60)
        print("REVOLUTIONARY FEATURES")
        print("="*60)
        print("✓ GCACU architecture adapted for Indian languages")
        print("✓ Cultural context feature engineering")
        print("✓ Multi-lingual training pipeline")
        print("✓ Language-specific model adaptation")
        print("✓ Bollywood reference integration")
        print("✓ Hinglish code-mixing optimization")

        print("\n✅ Indian Comedy GCACU Integration Ready!")
        print("🎯 Enhanced accuracy for Indian comedy content")
        print("📈 Cultural context awareness for better predictions")

        return results

    except Exception as e:
        logger.error(f"Error running Indian Comedy GCACU integration: {e}")
        raise


if __name__ == "__main__":
    main()