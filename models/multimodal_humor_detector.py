"""
Multimodal Humor Detection Model for UR-FUNNY TED Benchmark

This module implements multimodal deep learning architectures for humor detection
in TED talks, combining text, audio, and visual features to achieve the target
65.23% baseline accuracy (C-MFN).

Model Architectures:
1. Early Fusion: Concatenate features before classification
2. Late Fusion: Separate modalities with combined prediction
3. Cross-Modal Attention: Attention mechanism across modalities
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import BertModel, BertTokenizer
from typing import Dict, Optional, Tuple
import numpy as np


class TextEncoder(nn.Module):
    """Text encoder using BERT for processing TED talk transcripts"""

    def __init__(self, pretrained_model: str = 'bert-base-uncased', dropout: float = 0.1):
        super().__init__()
        self.bert = BertModel.from_pretrained(pretrained_model)
        self.dropout = nn.Dropout(dropout)
        self.output_dim = 768  # BERT base hidden size

    def forward(self, input_ids, attention_mask):
        # Get BERT outputs
        outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)

        # Use [CLS] token representation
        pooled_output = outputs.pooler_output
        pooled_output = self.dropout(pooled_output)

        return pooled_output


class AudioEncoder(nn.Module):
    """Audio encoder for processing acoustic features"""

    def __init__(self, input_dim: int = 128, hidden_dims: list = [256, 128], dropout: float = 0.1):
        super().__init__()

        layers = []
        prev_dim = input_dim

        for hidden_dim in hidden_dims:
            layers.extend([
                nn.Linear(prev_dim, hidden_dim),
                nn.ReLU(),
                nn.Dropout(dropout)
            ])
            prev_dim = hidden_dim

        self.encoder = nn.Sequential(*layers)
        self.output_dim = hidden_dims[-1]

    def forward(self, audio_features):
        # Audio features: [batch_size, input_dim]
        encoded = self.encoder(audio_features)
        return encoded


class VisualEncoder(nn.Module):
    """Visual encoder for processing video/frame features"""

    def __init__(self, input_dim: int = 512, hidden_dims: list = [256, 128], dropout: float = 0.1):
        super().__init__()

        layers = []
        prev_dim = input_dim

        for hidden_dim in hidden_dims:
            layers.extend([
                nn.Linear(prev_dim, hidden_dim),
                nn.ReLU(),
                nn.Dropout(dropout)
            ])
            prev_dim = hidden_dim

        self.encoder = nn.Sequential(*layers)
        self.output_dim = hidden_dims[-1]

    def forward(self, visual_features):
        # Visual features: [batch_size, input_dim]
        encoded = self.encoder(visual_features)
        return encoded


class EarlyFusionHumorDetector(nn.Module):
    """
    Early Fusion Multimodal Humor Detector

    Concatenates features from all modalities before classification.
    Simple but effective baseline approach.
    """

    def __init__(self,
                 text_encoder: TextEncoder,
                 audio_encoder: AudioEncoder,
                 visual_encoder: VisualEncoder,
                 hidden_dim: int = 256,
                 num_classes: int = 2,
                 dropout: float = 0.1):
        super().__init__()

        self.text_encoder = text_encoder
        self.audio_encoder = audio_encoder
        self.visual_encoder = visual_encoder

        # Calculate fused dimension
        fused_dim = (
            text_encoder.output_dim +
            audio_encoder.output_dim +
            visual_encoder.output_dim
        )

        # Fusion classifier
        self.classifier = nn.Sequential(
            nn.Linear(fused_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, num_classes)
        )

    def forward(self, text_input_ids, text_attention_mask, audio_features, visual_features):
        # Encode each modality
        text_encoded = self.text_encoder(text_input_ids, text_attention_mask)
        audio_encoded = self.audio_encoder(audio_features)
        visual_encoded = self.visual_encoder(visual_features)

        # Concatenate features
        fused_features = torch.cat([text_encoded, audio_encoded, visual_encoded], dim=1)

        # Classify
        logits = self.classifier(fused_features)

        return logits


class LateFusionHumorDetector(nn.Module):
    """
    Late Fusion Multimodal Humor Detector

    Processes each modality separately and combines predictions.
    More robust to missing modalities.
    """

    def __init__(self,
                 text_encoder: TextEncoder,
                 audio_encoder: AudioEncoder,
                 visual_encoder: VisualEncoder,
                 hidden_dim: int = 128,
                 num_classes: int = 2,
                 dropout: float = 0.1):
        super().__init__()

        self.text_encoder = text_encoder
        self.audio_encoder = audio_encoder
        self.visual_encoder = visual_encoder

        # Modality-specific classifiers
        self.text_classifier = nn.Sequential(
            nn.Linear(text_encoder.output_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, num_classes)
        )

        self.audio_classifier = nn.Sequential(
            nn.Linear(audio_encoder.output_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, num_classes)
        )

        self.visual_classifier = nn.Sequential(
            nn.Linear(visual_encoder.output_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, num_classes)
        )

        # Fusion weights (learnable importance of each modality)
        self.fusion_weights = nn.Parameter(torch.ones(3) / 3.0)

    def forward(self, text_input_ids, text_attention_mask, audio_features, visual_features):
        # Encode each modality
        text_encoded = self.text_encoder(text_input_ids, text_attention_mask)
        audio_encoded = self.audio_encoder(audio_features)
        visual_encoded = self.visual_encoder(visual_features)

        # Get modality-specific predictions
        text_logits = self.text_classifier(text_encoded)
        audio_logits = self.audio_classifier(audio_encoded)
        visual_logits = self.visual_classifier(visual_encoded)

        # Get probabilities
        text_probs = F.softmax(text_logits, dim=1)
        audio_probs = F.softmax(audio_logits, dim=1)
        visual_probs = F.softmax(visual_logits, dim=1)

        # Normalize fusion weights
        weights = F.softmax(self.fusion_weights, dim=0)

        # Weighted combination
        combined_probs = (
            weights[0] * text_probs +
            weights[1] * audio_probs +
            weights[2] * visual_probs
        )

        # Convert back to logits
        logits = torch.log(combined_probs + 1e-8)

        return logits


class CrossModalAttentionHumorDetector(nn.Module):
    """
    Cross-Modal Attention Multimodal Humor Detector

    Uses attention mechanism to let modalities interact before classification.
    More sophisticated approach for capturing cross-modal dependencies.
    """

    def __init__(self,
                 text_encoder: TextEncoder,
                 audio_encoder: AudioEncoder,
                 visual_encoder: VisualEncoder,
                 hidden_dim: int = 256,
                 num_heads: int = 8,
                 num_classes: int = 2,
                 dropout: float = 0.1):
        super().__init__()

        self.text_encoder = text_encoder
        self.audio_encoder = audio_encoder
        self.visual_encoder = visual_encoder

        # Project all modalities to same dimension
        self.text_projection = nn.Linear(text_encoder.output_dim, hidden_dim)
        self.audio_projection = nn.Linear(audio_encoder.output_dim, hidden_dim)
        self.visual_projection = nn.Linear(visual_encoder.output_dim, hidden_dim)

        # Cross-modal attention
        self.cross_attention = nn.MultiheadAttention(
            embed_dim=hidden_dim,
            num_heads=num_heads,
            dropout=dropout,
            batch_first=True
        )

        # Feed-forward network
        self.feed_forward = nn.Sequential(
            nn.Linear(hidden_dim * 3, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, num_classes)
        )

    def forward(self, text_input_ids, text_attention_mask, audio_features, visual_features):
        # Encode each modality
        text_encoded = self.text_encoder(text_input_ids, text_attention_mask)
        audio_encoded = self.audio_encoder(audio_features)
        visual_encoded = self.visual_encoder(visual_features)

        # Project to common dimension
        text_proj = self.text_projection(text_encoded)  # [batch, hidden_dim]
        audio_proj = self.audio_projection(audio_encoded)
        visual_proj = self.visual_projection(visual_encoded)

        # Stack modalities for attention
        # Shape: [batch, 3, hidden_dim] (3 modalities)
        modalities = torch.stack([text_proj, audio_proj, visual_proj], dim=1)

        # Apply cross-modal attention
        attended_modalities, attention_weights = self.cross_attention(
            modalities, modalities, modalities
        )

        # Flatten attended features
        attended_flat = attended_modalities.reshape(attended_modalities.size(0), -1)

        # Classify
        logits = self.feed_forward(attended_flat)

        return logits


class URFunnyTEDModel:
    """
    Main model class for UR-FUNNY TED humor detection.

    Supports different fusion strategies and provides training/evaluation interface.
    """

    def __init__(self,
                 model_type: str = 'early_fusion',
                 device: str = 'cuda',
                 learning_rate: float = 2e-5,
                 weight_decay: float = 0.01):
        """
        Initialize UR-FUNNY TED model.

        Args:
            model_type: Type of fusion ('early_fusion', 'late_fusion', 'attention')
            device: Device to run model on
            learning_rate: Learning rate for optimization
            weight_decay: Weight decay for regularization
        """
        self.device = device
        self.model_type = model_type

        # Initialize encoders
        text_encoder = TextEncoder().to(device)
        audio_encoder = AudioEncoder().to(device)
        visual_encoder = VisualEncoder().to(device)

        # Initialize fusion model
        if model_type == 'early_fusion':
            self.model = EarlyFusionHumorDetector(
                text_encoder, audio_encoder, visual_encoder
            ).to(device)
        elif model_type == 'late_fusion':
            self.model = LateFusionHumorDetector(
                text_encoder, audio_encoder, visual_encoder
            ).to(device)
        elif model_type == 'attention':
            self.model = CrossModalAttentionHumorDetector(
                text_encoder, audio_encoder, visual_encoder
            ).to(device)
        else:
            raise ValueError(f"Unknown model type: {model_type}")

        # Initialize optimizer and loss function
        self.optimizer = torch.optim.AdamW(
            self.model.parameters(),
            lr=learning_rate,
            weight_decay=weight_decay
        )

        self.criterion = nn.CrossEntropyLoss()

        # Training history
        self.history = {
            'train_loss': [],
            'train_acc': [],
            'val_loss': [],
            'val_acc': []
        }

    def train_epoch(self, train_loader, epoch: int) -> Tuple[float, float]:
        """Train for one epoch"""
        self.model.train()
        total_loss = 0
        correct = 0
        total = 0

        for batch_idx, batch in enumerate(train_loader):
            # Move batch to device
            text_input_ids = batch['text_input_ids'].to(self.device)
            text_attention_mask = batch['text_attention_mask'].to(self.device)
            audio_features = batch.get('audio', torch.zeros(text_input_ids.size(0), 128)).to(self.device)
            visual_features = batch.get('visual', torch.zeros(text_input_ids.size(0), 512)).to(self.device)
            labels = batch['label'].to(self.device)

            # Forward pass
            self.optimizer.zero_grad()
            logits = self.model(text_input_ids, text_attention_mask, audio_features, visual_features)
            loss = self.criterion(logits, labels)

            # Backward pass
            loss.backward()
            self.optimizer.step()

            # Calculate accuracy
            total_loss += loss.item()
            _, predicted = torch.max(logits, 1)
            correct += (predicted == labels).sum().item()
            total += labels.size(0)

            # Print progress
            if (batch_idx + 1) % 10 == 0:
                print(f'Epoch {epoch}, Batch {batch_idx + 1}/{len(train_loader)}, '
                      f'Loss: {loss.item():.4f}, '
                      f'Acc: {100 * correct / total:.2f}%')

        avg_loss = total_loss / len(train_loader)
        accuracy = 100 * correct / total

        return avg_loss, accuracy

    def evaluate(self, val_loader) -> Tuple[float, float]:
        """Evaluate the model"""
        self.model.eval()
        total_loss = 0
        correct = 0
        total = 0

        with torch.no_grad():
            for batch in val_loader:
                # Move batch to device
                text_input_ids = batch['text_input_ids'].to(self.device)
                text_attention_mask = batch['text_attention_mask'].to(self.device)
                audio_features = batch.get('audio', torch.zeros(text_input_ids.size(0), 128)).to(self.device)
                visual_features = batch.get('visual', torch.zeros(text_input_ids.size(0), 512)).to(self.device)
                labels = batch['label'].to(self.device)

                # Forward pass
                logits = self.model(text_input_ids, text_attention_mask, audio_features, visual_features)
                loss = self.criterion(logits, labels)

                # Calculate accuracy
                total_loss += loss.item()
                _, predicted = torch.max(logits, 1)
                correct += (predicted == labels).sum().item()
                total += labels.size(0)

        avg_loss = total_loss / len(val_loader)
        accuracy = 100 * correct / total

        return avg_loss, accuracy

    def train(self, train_loader, val_loader, num_epochs: int, early_stopping_patience: int = 5):
        """Train the model with early stopping"""
        best_val_acc = 0
        patience_counter = 0

        for epoch in range(1, num_epochs + 1):
            print(f'\nEpoch {epoch}/{num_epochs}')
            print('-' * 50)

            # Train
            train_loss, train_acc = self.train_epoch(train_loader, epoch)
            self.history['train_loss'].append(train_loss)
            self.history['train_acc'].append(train_acc)

            # Validate
            val_loss, val_acc = self.evaluate(val_loader)
            self.history['val_loss'].append(val_loss)
            self.history['val_acc'].append(val_acc)

            print(f'Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.2f}%')
            print(f'Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.2f}%')

            # Early stopping
            if val_acc > best_val_acc:
                best_val_acc = val_acc
                patience_counter = 0
                # Save best model
                torch.save(self.model.state_dict(), 'best_ur_funny_model.pth')
                print(f'New best validation accuracy: {best_val_acc:.2f}%')
            else:
                patience_counter += 1
                if patience_counter >= early_stopping_patience:
                    print(f'Early stopping after {epoch} epochs')
                    break

        print(f'\nTraining complete. Best validation accuracy: {best_val_acc:.2f}%')

        # Load best model
        self.model.load_state_dict(torch.load('best_ur_funny_model.pth'))

        return best_val_acc

    def predict(self, batch) -> Tuple[torch.Tensor, torch.Tensor]:
        """Make predictions on a batch"""
        self.model.eval()

        with torch.no_grad():
            # Move batch to device
            text_input_ids = batch['text_input_ids'].to(self.device)
            text_attention_mask = batch['text_attention_mask'].to(self.device)
            audio_features = batch.get('audio', torch.zeros(text_input_ids.size(0), 128)).to(self.device)
            visual_features = batch.get('visual', torch.zeros(text_input_ids.size(0), 512)).to(self.device)

            # Forward pass
            logits = self.model(text_input_ids, text_attention_mask, audio_features, visual_features)
            probabilities = F.softmax(logits, dim=1)
            predictions = torch.argmax(probabilities, dim=1)

        return predictions, probabilities

    def compare_to_baseline(self, test_accuracy: float) -> Dict[str, float]:
        """Compare model performance to published baseline"""
        baseline_accuracy = 65.23  # C-MFN baseline
        human_performance = 82.5

        improvement = test_accuracy - baseline_accuracy
        gap_to_human = human_performance - test_accuracy

        comparison = {
            'test_accuracy': test_accuracy,
            'baseline_accuracy': baseline_accuracy,
            'human_performance': human_performance,
            'improvement_over_baseline': improvement,
            'gap_to_human_performance': gap_to_human,
            'percentage_of_human_performance': (test_accuracy / human_performance) * 100
        }

        return comparison


def create_ur_funny_model(model_type: str = 'early_fusion',
                         device: str = 'cuda') -> URFunnyTEDModel:
    """
    Factory function to create UR-FUNNY TED model.

    Args:
        model_type: Type of fusion architecture
        device: Device to run model on

    Returns:
        Initialized URFunnyTEDModel
    """
    return URFunnyTEDModel(model_type=model_type, device=device)


if __name__ == "__main__":
    # Example usage
    print("Creating UR-FUNNY TED model...")

    # Create model
    model = create_ur_funny_model(model_type='early_fusion', device='cpu')

    print(f"Model type: {model.model_type}")
    print(f"Device: {model.device}")
    print("Model created successfully!")