"""
CLoST-GCACU Integration Module
Combines causal reasoning with incongruity detection for enhanced humor understanding

Author: GCACU Autonomous Laughter Prediction System
Date: 2026-04-03
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Tuple, Optional, Any
import numpy as np

# Import CLoST components
from clost_reasoning import (
    CLoSTReasoningFramework,
    ComedyKnowledgeGraph,
    ThoughtLeap,
    CausalAnalysis
)

# Import GCACU components
import sys
sys.path.append('/Users/Subho/autonomous_laughter_prediction/core/gcacu')
from gcacu import GCACUNetwork


class CLoSTGCACUEnhanced(nn.Module):
    """
    Enhanced humor detection combining CLoST causal reasoning with GCACU incongruity detection

    This integrated system provides:
    - Causal reasoning from CLoST framework
    - Incongruity detection from GCACU
    - Enhanced semantic understanding
    - Multi-level humor analysis
    """

    def __init__(self,
                 embedding_dim: int = 768,
                 gcacu_hidden_dim: int = 256,
                 clost_hidden_dim: int = 256,
                 num_heads: int = 8,
                 num_gating_levels: int = 3):
        """
        Initialize enhanced CLoST-GCACU system

        Args:
            embedding_dim: Dimension of input embeddings
            gcacu_hidden_dim: Hidden dimension for GCACU
            clost_hidden_dim: Hidden dimension for CLoST
            num_heads: Number of attention heads for GCACU
            num_gating_levels: Number of gating levels for GCACU
        """
        super().__init__()
        self.embedding_dim = embedding_dim
        self.gcacu_hidden_dim = gcacu_hidden_dim
        self.clost_hidden_dim = clost_hidden_dim

        # Initialize GCACU network
        self.gcacu_network = GCACUNetwork(
            embedding_dim=embedding_dim,
            num_heads=num_heads,
            num_gating_levels=num_gating_levels,
            hidden_dim=gcacu_hidden_dim
        )

        # Initialize CLoST framework
        self.clost_framework = CLoSTReasoningFramework(
            embedding_dim=embedding_dim,
            hidden_dim=clost_hidden_dim
        )

        # Integration layers
        self.feature_integration = self._build_integration_layers()

        # Enhanced prediction head
        self.enhanced_predictor = nn.Sequential(
            nn.Linear(gcacu_hidden_dim + clost_hidden_dim + 128, 256),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 1),
            nn.Sigmoid()
        )

        # Humor mechanism classifier
        self.mechanism_classifier = nn.Sequential(
            nn.Linear(gcacu_hidden_dim + clost_hidden_dim, 128),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(128, 5)  # 5 humor mechanisms
        )

        # Thought leap enhancer
        self.leap_enhancer = nn.Sequential(
            nn.Linear(clost_hidden_dim + 64, 64),
            nn.ReLU(),
            nn.Linear(64, 1),
            nn.Sigmoid()
        )

    def _build_integration_layers(self) -> nn.Module:
        """Build integration layers for combining GCACU and CLoST features"""
        class FeatureIntegration(nn.Module):
            def __init__(self, gcacu_dim: int, clost_dim: int, output_dim: int = 128):
                super().__init__()
                self.gcacu_dim = gcacu_dim
                self.clost_dim = clost_dim
                self.output_dim = output_dim

                # Cross-attention between GCACU and CLoST features
                self.cross_attention = nn.MultiheadAttention(
                    embed_dim=max(gcacu_dim, clost_dim),
                    num_heads=4,
                    batch_first=True
                )

                # Feature fusion
                self.fusion = nn.Sequential(
                    nn.Linear(gcacu_dim + clost_dim, output_dim),
                    nn.ReLU(),
                    nn.Dropout(0.1),
                    nn.Linear(output_dim, output_dim),
                    nn.ReLU()
                )

                # Gating mechanism
                self.gate = nn.Sequential(
                    nn.Linear(gcacu_dim + clost_dim, 1),
                    nn.Sigmoid()
                )

            def forward(self, gcacu_features: torch.Tensor,
                       clost_features: torch.Tensor) -> torch.Tensor:
                """
                Integrate GCACU and CLoST features

                Args:
                    gcacu_features: GCACU conflict features
                    clost_features: CLoST reasoning features

                Returns:
                    Integrated features
                """
                # Ensure both features have same dimension for attention
                max_dim = max(self.gcacu_dim, self.clost_dim)

                if gcacu_features.shape[-1] != max_dim:
                    gcacu_adjusted = F.pad(gcacu_features,
                                         (0, max_dim - gcacu_features.shape[-1]))
                else:
                    gcacu_adjusted = gcacu_features

                if clost_features.shape[-1] != max_dim:
                    clost_adjusted = F.pad(clost_features,
                                         (0, max_dim - clost_features.shape[-1]))
                else:
                    clost_adjusted = clost_features

                # Cross-attention
                attended, _ = self.cross_attention(
                    gcacu_adjusted.unsqueeze(1),
                    clost_adjusted.unsqueeze(1),
                    clost_adjusted.unsqueeze(1)
                )
                attended = attended.squeeze(1)

                # Concatenate original features
                combined = torch.cat([gcacu_features, clost_features], dim=-1)

                # Compute gate
                gate = self.gate(combined)

                # Fuse features
                fused = self.fusion(combined)

                # Apply gate to blend attended and fused features
                integrated = gate * fused + (1 - gate) * attended[:, :self.output_dim]

                return integrated

        return FeatureIntegration(self.gcacu_hidden_dim, self.clost_hidden_dim)

    def forward(self,
                embeddings: torch.Tensor,
                attention_mask: Optional[torch.Tensor] = None) -> Dict[str, Any]:
        """
        Forward pass for enhanced CLoST-GCACU system

        Args:
            embeddings: Text embeddings (batch, seq_len, embedding_dim)
            attention_mask: Optional attention mask

        Returns:
            Dictionary with enhanced predictions and analyses
        """
        batch_size, seq_len, _ = embeddings.shape

        # Step 1: GCACU analysis (incongruity detection)
        gcacu_output = self.gcacu_network(embeddings, attention_mask)
        incongruity_score = gcacu_output['incongruity_score']
        gcacu_features = gcacu_output['conflict_features']

        # Step 2: CLoST analysis (causal reasoning)
        clost_output = self.clost_framework(embeddings, attention_mask)

        # Extract CLoST features from batch results
        if clost_output['batch_results']:
            first_result = clost_output['batch_results'][0]
            thought_leap = first_result['thought_leap']
            causal_strength = first_result['causal_analysis']['causal_strength']
            expectation_violation = first_result['causal_analysis']['expectation_violation']

            # Create CLoST feature vector
            clost_features = torch.tensor([
                thought_leap.leap_score,
                thought_leap.causal_violation,
                thought_leap.semantic_distance,
                expectation_violation,
                causal_strength,
                thought_leap.surprise_level
            ]).unsqueeze(0)

            # Expand to match GCACU feature dimension
            if clost_features.shape[-1] < self.clost_hidden_dim:
                clost_features = F.pad(clost_features,
                                     (0, self.clost_hidden_dim - clost_features.shape[-1]))
            else:
                clost_features = clost_features[:, :self.clost_hidden_dim]
        else:
            # Default CLoST features
            clost_features = torch.zeros(batch_size, self.clost_hidden_dim)

        # Step 3: Integrate features
        integrated_features = self.feature_integration(gcacu_features, clost_features)

        # Step 4: Enhanced prediction
        enhanced_input = torch.cat([gcacu_features, clost_features, integrated_features], dim=-1)
        enhanced_prediction = self.enhanced_predictor(enhanced_input)

        # Step 5: Classify humor mechanism
        mechanism_input = torch.cat([gcacu_features, clost_features], dim=-1)
        mechanism_logits = self.mechanism_classifier(mechanism_input)
        mechanism_probs = F.softmax(mechanism_logits, dim=-1)

        # Step 6: Enhanced thought leap scoring
        leap_input = torch.cat([clost_features, integrated_features[:, :64]], dim=-1)
        enhanced_leap_score = self.leap_enhancer(leap_input)

        # Step 7: Combine predictions
        final_prediction = (
            0.3 * incongruity_score +
            0.3 * enhanced_prediction +
            0.2 * enhanced_leap_score +
            0.2 * mechanism_probs[:, 0:1]  # Incongruity mechanism
        )

        mechanism_types = ['incongruity', 'causal', 'semantic', 'pragmatic', 'cultural']
        detected_mechanism = mechanism_types[torch.argmax(mechanism_probs).item()]

        return {
            'final_prediction': final_prediction,
            'incongruity_score': incongruity_score,
            'enhanced_prediction': enhanced_prediction,
            'thought_leap_score': enhanced_leap_score,
            'mechanism_probs': mechanism_probs,
            'detected_mechanism': detected_mechanism,
            'gcacu_features': gcacu_features,
            'clost_features': clost_features,
            'integrated_features': integrated_features,
            'gcacu_output': gcacu_output,
            'clost_output': clost_output
        }

    def compute_enhanced_loss(self,
                            predictions: Dict[str, torch.Tensor],
                            targets: torch.Tensor,
                            alpha: float = 0.4,
                            beta: float = 0.3,
                            gamma: float = 0.2,
                            delta: float = 0.1) -> torch.Tensor:
        """
        Compute enhanced loss combining multiple components

        Args:
            predictions: Dictionary with all predictions
            targets: Ground truth labels
            alpha: Weight for final prediction loss
            beta: Weight for incongruity loss
            gamma: Weight for thought leap loss
            delta: Weight for mechanism classification loss

        Returns:
            Total enhanced loss
        """
        # Main prediction loss
        main_loss = F.binary_cross_entropy(predictions['final_prediction'], targets)

        # Incongruity loss
        incongruity_loss = F.binary_cross_entropy(predictions['incongruity_score'], targets)

        # Thought leap loss (encourage higher leap scores for positive examples)
        leap_targets = targets * 0.8 + 0.1  # Target 0.9 for positives, 0.1 for negatives
        leap_loss = F.mse_loss(predictions['thought_leap_score'], leap_targets)

        # Mechanism classification loss (use targets as pseudo-labels)
        # For now, assume positives are mostly incongruity-based
        mechanism_targets = torch.zeros(targets.shape[0], 5)
        mechanism_targets[targets.squeeze() == 1, 0] = 1.0  # Incongruity for positives
        mechanism_targets[targets.squeeze() == 0, 1] = 1.0  # Causal for negatives
        mechanism_loss = F.cross_entropy(predictions['mechanism_probs'], mechanism_targets.argmax(dim=1))

        # Total loss
        total_loss = alpha * main_loss + beta * incongruity_loss + gamma * leap_loss + delta * mechanism_loss

        return total_loss


class CLoSTGCACUTrainer:
    """
    Trainer for enhanced CLoST-GCACU system
    """

    def __init__(self,
                 model: CLoSTGCACUEnhanced,
                 learning_rate: float = 1e-4,
                 device: str = 'cpu'):
        """
        Initialize trainer

        Args:
            model: CLoSTGCACUEnhanced model
            learning_rate: Learning rate
            device: Device to train on
        """
        self.model = model.to(device)
        self.device = device
        self.optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
        self.scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer, mode='min', factor=0.5, patience=3
        )

        self.training_history = {
            'train_loss': [],
            'val_loss': [],
            'train_acc': [],
            'val_acc': []
        }

    def train_step(self,
                   embeddings: torch.Tensor,
                   targets: torch.Tensor,
                   attention_mask: Optional[torch.Tensor] = None) -> Dict[str, float]:
        """
        Single training step

        Args:
            embeddings: Input embeddings
            targets: Target labels
            attention_mask: Optional attention mask

        Returns:
            Dictionary with training metrics
        """
        self.model.train()
        self.optimizer.zero_grad()

        # Forward pass
        predictions = self.model(embeddings, attention_mask)

        # Compute loss
        loss = self.model.compute_enhanced_loss(predictions, targets)

        # Backward pass
        loss.backward()

        # Gradient clipping
        torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)

        # Update weights
        self.optimizer.step()

        # Compute accuracy
        with torch.no_grad():
            pred_labels = (predictions['final_prediction'] > 0.5).float()
            accuracy = (pred_labels == targets).float().mean()

        return {
            'loss': loss.item(),
            'accuracy': accuracy.item(),
            'incongruity_score': predictions['incongruity_score'].mean().item(),
            'thought_leap_score': predictions['thought_leap_score'].mean().item()
        }

    def validate(self,
                embeddings: torch.Tensor,
                targets: torch.Tensor,
                attention_mask: Optional[torch.Tensor] = None) -> Dict[str, float]:
        """
        Validation step

        Args:
            embeddings: Input embeddings
            targets: Target labels
            attention_mask: Optional attention mask

        Returns:
            Dictionary with validation metrics
        """
        self.model.eval()

        with torch.no_grad():
            predictions = self.model(embeddings, attention_mask)
            loss = self.model.compute_enhanced_loss(predictions, targets)

            pred_labels = (predictions['final_prediction'] > 0.5).float()
            accuracy = (pred_labels == targets).float().mean()

            # Additional metrics
            predictions_np = predictions['final_prediction'].cpu().numpy()
            targets_np = targets.cpu().numpy()

            # F1 score (simplified)
            tp = ((pred_labels == 1) & (targets == 1)).float().sum()
            fp = ((pred_labels == 1) & (targets == 0)).float().sum()
            fn = ((pred_labels == 0) & (targets == 1)).float().sum()

            precision = tp / (tp + fp + 1e-6)
            recall = tp / (tp + fn + 1e-6)
            f1 = 2 * precision * recall / (precision + recall + 1e-6)

        return {
            'loss': loss.item(),
            'accuracy': accuracy.item(),
            'precision': precision.item(),
            'recall': recall.item(),
            'f1': f1.item()
        }

    def train_epoch(self,
                   train_loader,
                   val_loader=None,
                   epoch: int = 0) -> Dict[str, float]:
        """
        Train for one epoch

        Args:
            train_loader: Training data loader
            val_loader: Optional validation data loader
            epoch: Current epoch number

        Returns:
            Dictionary with epoch metrics
        """
        train_metrics = []
        for batch_idx, batch in enumerate(train_loader):
            embeddings = batch['embeddings'].to(self.device)
            targets = batch['targets'].to(self.device)
            attention_mask = batch.get('attention_mask', None)
            if attention_mask is not None:
                attention_mask = attention_mask.to(self.device)

            metrics = self.train_step(embeddings, targets, attention_mask)
            train_metrics.append(metrics)

            if (batch_idx + 1) % 10 == 0:
                print(f"Epoch {epoch}, Batch {batch_idx + 1}: "
                      f"Loss={metrics['loss']:.4f}, Acc={metrics['accuracy']:.4f}")

        # Compute average training metrics
        avg_train_metrics = {
            key: np.mean([m[key] for m in train_metrics])
            for key in train_metrics[0].keys()
        }

        # Validation
        if val_loader:
            val_metrics = []
            for batch in val_loader:
                embeddings = batch['embeddings'].to(self.device)
                targets = batch['targets'].to(self.device)
                attention_mask = batch.get('attention_mask', None)
                if attention_mask is not None:
                    attention_mask = attention_mask.to(self.device)

                metrics = self.validate(embeddings, targets, attention_mask)
                val_metrics.append(metrics)

            avg_val_metrics = {
                key: np.mean([m[key] for m in val_metrics])
                for key in val_metrics[0].keys()
            }

            # Update learning rate
            self.scheduler.step(avg_val_metrics['loss'])

            # Update history
            self.training_history['train_loss'].append(avg_train_metrics['loss'])
            self.training_history['val_loss'].append(avg_val_metrics['loss'])
            self.training_history['train_acc'].append(avg_train_metrics['accuracy'])
            self.training_history['val_acc'].append(avg_val_metrics['accuracy'])

            return {**avg_train_metrics, **{f'val_{k}': v for k, v in avg_val_metrics.items()}}

        return avg_train_metrics


def test_enhanced_integration():
    """Test enhanced CLoST-GCACU integration"""
    print("🧪 Testing Enhanced CLoST-GCACU Integration")

    # Create sample input
    batch_size = 2
    seq_len = 128
    embedding_dim = 768

    embeddings = torch.randn(batch_size, seq_len, embedding_dim)
    attention_mask = torch.ones(batch_size, seq_len)
    targets = torch.tensor([[1.0], [0.0]])

    # Initialize enhanced model
    enhanced_model = CLoSTGCACUEnhanced(embedding_dim=embedding_dim)

    # Forward pass
    print("🔄 Running forward pass...")
    predictions = enhanced_model(embeddings, attention_mask)

    print(f"📊 Results:")
    print(f"   Final Prediction: {predictions['final_prediction'].squeeze().detach().numpy()}")
    print(f"   Incongruity Score: {predictions['incongruity_score'].squeeze().detach().numpy()}")
    print(f"   Enhanced Prediction: {predictions['enhanced_prediction'].squeeze().detach().numpy()}")
    print(f"   Thought Leap Score: {predictions['thought_leap_score'].squeeze().detach().numpy()}")
    print(f"   Detected Mechanism: {predictions['detected_mechanism']}")
    print(f"   Mechanism Probs: {predictions['mechanism_probs'].detach().numpy()}")

    # Test loss computation
    print("🔧 Testing loss computation...")
    loss = enhanced_model.compute_enhanced_loss(predictions, targets)
    print(f"   Enhanced Loss: {loss.item():.4f}")

    # Test training step
    print("🏋️ Testing training step...")
    trainer = CLoSTGCACUTrainer(enhanced_model)
    train_metrics = trainer.train_step(embeddings, targets, attention_mask)
    print(f"   Training Loss: {train_metrics['loss']:.4f}")
    print(f"   Training Accuracy: {train_metrics['accuracy']:.4f}")

    print("✅ Enhanced CLoST-GCACU Integration Test Complete!")
    return True


if __name__ == "__main__":
    test_enhanced_integration()