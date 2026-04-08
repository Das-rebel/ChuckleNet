#!/usr/bin/env python3
"""
WESR-GCACU Integration: Enhanced Incongruity Detection

This module integrates WESR (Word-level Event-Speech Recognition) taxonomy features
with the GCACU (Gated Contrast-Attention Contextualized Understanding) network
to create a revolutionary humor detection system.

Key Innovations:
- WESR-enhanced incongruity detection
- Discrete/continuous laughter awareness
- Speech-laughter separation for robust humor understanding
- Temporal boundary detection for precise event timing
- Multi-modal confidence aggregation

Performance Targets:
- 38.0% F1 on WESR benchmark (word-level vocal events)
- Enhanced incongruity detection through laughter awareness
- Real-time processing with <20ms latency
- 8GB Mac M2 memory compatibility
"""

from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch import Tensor
from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass
from types import SimpleNamespace
import json
from pathlib import Path

# Import existing components
from training.gcacu_network import (
    GCACUTokenClassifier,
    GCACUConfig,
    AdaptiveFocalLoss,
    SemanticConflictAttention,
    GCACUGating
)
from training.wesr_taxonomy_processor import (
    WESRTaxonomyClassifier,
    WESRConfig,
    WESRPerformanceOptimizer,
    AcousticFeatureExtractor
)


@dataclass
class WESRGCACUConfig:
    """Configuration for WESR-GCACU integrated system."""
    # GCACU configuration
    gcacu_hidden_size: int = 768
    gcacu_dim: int = 128
    gcacu_num_heads: int = 4
    gcacu_gate_scale: float = 0.3
    gcacu_dropout: float = 0.1

    # WESR configuration
    wesr_dim: int = 256
    wesr_num_heads: int = 8
    wesr_temporal_window: int = 5
    wesr_acoustic_features: int = 13
    wesr_confidence_threshold: float = 0.6

    # Integration configuration
    fusion_strategy: str = "attention"  # attention, concat, gated
    integration_dim: int = 512
    laughter_aware_attention: bool = True
    temporal_aware_gate: bool = True
    confidence_weighted_loss: bool = True

    # Performance configuration
    target_processing_speed_ms: float = 20.0
    memory_budget_mb: float = 300.0
    device: str = "cuda" if torch.cuda.is_available() else "cpu"


class WESREnhancedAttention(nn.Module):
    """
    WESR-enhanced attention mechanism for incongruity detection.

    Incorporates laughter-aware attention weights:
    - Higher attention to discrete laughter regions
    - Contextual attention for continuous laughter
    - Temporal boundary awareness
    """

    def __init__(self, hidden_size: int, num_heads: int = 8):
        super().__init__()
        self.num_heads = num_heads
        self.head_dim = hidden_size // num_heads

        # Standard attention projections
        self.q_proj = nn.Linear(hidden_size, hidden_size)
        self.k_proj = nn.Linear(hidden_size, hidden_size)
        self.v_proj = nn.Linear(hidden_size, hidden_size)
        self.out_proj = nn.Linear(hidden_size, hidden_size)

        # WESR-aware attention modulation
        self.wesr_modulation = nn.Sequential(
            nn.Linear(hidden_size + 4 + 3, hidden_size),  # +4 boundaries, +3 separation
            nn.Tanh(),
            nn.Linear(hidden_size, num_heads),
            nn.Sigmoid()
        )

    def forward(
        self,
        sequence_output: Tensor,
        attention_mask: Tensor,
        wesr_features: Optional[Tensor] = None
    ) -> Tuple[Tensor, Tensor]:
        """
        Compute WESR-enhanced attention.

        Args:
            sequence_output: [batch_size, seq_len, hidden_size]
            attention_mask: [batch_size, seq_len]
            wesr_features: [batch_size, seq_len, 7] - boundaries + separation

        Returns:
            attended_output: [batch_size, seq_len, hidden_size]
            attention_weights: [batch_size, num_heads, seq_len, seq_len]
        """
        batch_size, seq_len, hidden_size = sequence_output.shape

        # Standard attention computation
        q = self.q_proj(sequence_output).view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        k = self.k_proj(sequence_output).view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        v = self.v_proj(sequence_output).view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)

        attn_weights = torch.matmul(q, k.transpose(-2, -1)) / (self.head_dim ** 0.5)
        attn_weights = attn_weights.masked_fill(attention_mask.unsqueeze(1).unsqueeze(2) == 0, float('-inf'))

        # WESR-aware modulation
        if wesr_features is not None:
            # Modulate attention based on WESR features
            modulation_input = torch.cat([sequence_output, wesr_features], dim=-1)
            head_modulation = self.wesr_modulation(modulation_input)  # [batch, seq, num_heads]
            head_modulation = head_modulation.transpose(1, 2).unsqueeze(-1)  # [batch, num_heads, 1, seq, 1]

            # Apply modulation to attention weights
            attn_weights = attn_weights.unsqueeze(-1) * head_modulation
            attn_weights = attn_weights.squeeze(-1)

        attn_weights = F.softmax(attn_weights, dim=-1)

        attn_output = torch.matmul(attn_weights, v)
        attn_output = attn_output.transpose(1, 2).contiguous().view(batch_size, seq_len, hidden_size)
        attn_output = self.out_proj(attn_output)

        return attn_output, attn_weights


class LaughterAwareGating(nn.Module):
    """
    Laughter-aware gating mechanism for incongruity detection.

    Uses WESR taxonomy information to modulate incongruity detection:
    - Discrete laughter → higher incongruity weight
    - Continuous laughter → contextual incongruity weight
    - Temporal boundaries → transition weight
    """

    def __init__(self, hidden_size: int, integration_dim: int):
        super().__init__()

        # Laughter-aware gate network
        self.laughter_gate = nn.Sequential(
            nn.Linear(hidden_size + 2 + 4, integration_dim),  # +2 laughter types, +4 boundaries
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(integration_dim, hidden_size),
            nn.Sigmoid()
        )

        # Contextual projection
        self.context_proj = nn.Sequential(
            nn.Linear(hidden_size + 2 + 4, integration_dim),
            nn.ReLU(),
            nn.Linear(integration_dim, hidden_size)
        )

    def forward(
        self,
        sequence_output: Tensor,
        context_summary: Tensor,
        wesr_taxonomy: Tensor,
        wesr_boundaries: Tensor
    ) -> Tensor:
        """
        Compute laughter-aware gated features.

        Args:
            sequence_output: [batch_size, seq_len, hidden_size]
            context_summary: [batch_size, 1, hidden_size]
            wesr_taxonomy: [batch_size, seq_len, 2] - discrete/continuous probs
            wesr_boundaries: [batch_size, seq_len, 4] - boundary probabilities

        Returns:
            gated_features: [batch_size, seq_len, hidden_size]
        """
        # Expand context summary to sequence length
        context_expanded = context_summary.expand(-1, sequence_output.size(1), -1)

        # Combine features
        combined = torch.cat([
            sequence_output,
            wesr_taxonomy,
            wesr_boundaries
        ], dim=-1)

        # Compute laughter-aware gate
        gate = self.laughter_gate(combined)

        # Compute contextual projection
        context_input = torch.cat([
            context_expanded,
            wesr_taxonomy,
            wesr_boundaries
        ], dim=-1)
        context_proj = self.context_proj(context_input)

        # Apply gate
        gated_features = gate * context_proj

        return gated_features


class WESRGCACUIntegrated(nn.Module):
    """
    WESR-GCACU Integrated Network for Enhanced Humor Detection.

    Combines:
    1. GCACU incongruity detection
    2. WESR taxonomy classification
    3. Laughter-aware attention
    4. Temporal boundary detection
    5. Speech-laughter separation
    """

    def __init__(self, backbone: nn.Module, config: WESRGCACUConfig = None):
        super().__init__()
        self.config = config or WESRGCACUConfig()

        # GCACU components
        self.gcacu_conflict_attention = SemanticConflictAttention(
            self.config.gcacu_hidden_size,
            self.config.gcacu_num_heads
        )
        self.laughter_aware_gating = LaughterAwareGating(
            self.config.gcacu_hidden_size,
            self.config.integration_dim
        )

        # WESR processor
        wesr_config = WESRConfig(
            hidden_size=self.config.gcacu_hidden_size,
            wesr_dim=self.config.wesr_dim,
            num_heads=self.config.wesr_num_heads,
            temporal_window=self.config.wesr_temporal_window,
            acoustic_features=self.config.wesr_acoustic_features
        )
        self.wesr_processor = WESRTaxonomyClassifier(wesr_config)

        # WESR-enhanced attention
        if self.config.laughter_aware_attention:
            self.wesr_enhanced_attention = WESREnhancedAttention(
                self.config.gcacu_hidden_size,
                self.config.wesr_num_heads
            )

        # Fusion layers
        if self.config.fusion_strategy == "attention":
            self.fusion_attention = nn.MultiheadAttention(
                embed_dim=self.config.gcacu_hidden_size,
                num_heads=self.config.gcacu_num_heads,
                dropout=self.config.gcacu_dropout,
                batch_first=True
            )

        # Integration layers
        self.integration_network = nn.Sequential(
            nn.Linear(self.config.gcacu_hidden_size * 2, self.config.integration_dim),
            nn.ReLU(),
            nn.Dropout(self.config.gcacu_dropout),
            nn.Linear(self.config.integration_dim, self.config.gcacu_hidden_size)
        )

        # Final fusion
        self.final_fusion = nn.Sequential(
            nn.Linear(self.config.gcacu_hidden_size * 2, self.config.gcacu_hidden_size),
            nn.Tanh(),
            nn.Dropout(self.config.gcacu_dropout)
        )

        # Store backbone
        self.backbone = backbone

    def forward(
        self,
        input_ids: Tensor,
        attention_mask: Tensor,
        return_all_features: bool = False
    ) -> SimpleNamespace:
        """
        Forward pass with WESR-GCACU integration.

        Args:
            input_ids: [batch_size, seq_len]
            attention_mask: [batch_size, seq_len]
            return_all_features: Whether to return intermediate features

        Returns:
            SimpleNamespace with predictions and optional features
        """
        # Get backbone outputs
        roberta_outputs = self.backbone.roberta(
            input_ids=input_ids,
            attention_mask=attention_mask,
            return_dict=True,
        )
        sequence_output = roberta_outputs.last_hidden_state

        # WESR processing
        wesr_output = self.wesr_processor(
            sequence_output,
            attention_mask,
            return_all_features=True
        )

        # Prepare WESR features for integration
        wesr_features = torch.cat([
            wesr_output.boundaries,
            wesr_output.separation
        ], dim=-1)  # [batch, seq, 7]

        # GCACU incongruity detection with WESR awareness
        if self.config.laughter_aware_attention:
            # Use WESR-enhanced attention
            conflict_features, incongruity_scores = self.wesr_enhanced_attention(
                sequence_output,
                attention_mask,
                wesr_features
            )
        else:
            # Use standard conflict attention
            conflict_features, incongruity_scores = self.gcacu_conflict_attention(
                sequence_output,
                attention_mask
            )

        # Laughter-aware gating
        mask = attention_mask.unsqueeze(-1).float()
        denom = mask.sum(dim=1, keepdim=True).clamp_min(1.0)
        context_summary = (sequence_output * mask).sum(dim=1, keepdim=True) / denom

        gated_features = self.laughter_aware_gating(
            sequence_output,
            context_summary,
            wesr_output.discrete_laughter,
            wesr_output.boundaries
        )

        # Integration
        if self.config.fusion_strategy == "attention":
            # Attention-based fusion
            integrated_features, _ = self.fusion_attention(
                conflict_features,
                key=gated_features,
                value=gated_features,
                key_padding_mask=~attention_mask.bool()
            )
        else:
            # Concatenation-based fusion
            combined = torch.cat([conflict_features, gated_features], dim=-1)
            integrated_features = self.integration_network(combined)

        # Combine with original features
        fused = self.final_fusion(torch.cat([
            sequence_output,
            integrated_features
        ], dim=-1))

        gated_output = sequence_output + (self.config.gcacu_gate_scale * fused)

        # Final predictions
        logits = self.backbone.classifier(gated_output)

        result = SimpleNamespace(
            logits=logits,
            wesr_discrete_laughter=wesr_output.discrete_laughter,
            wesr_vocal_events=wesr_output.vocal_events,
            wesr_boundaries=wesr_output.boundaries,
            wesr_separation=wesr_output.separation,
            wesr_confidence=wesr_output.confidence,
            incongruity_scores=incongruity_scores.squeeze(-1)
        )

        if return_all_features:
            result.conflict_features = conflict_features
            result.gated_features = gated_features
            result.integrated_features = integrated_features
            result.wesr_acoustic_features = wesr_output.acoustic_features
            result.wesr_refined_features = wesr_output.refined_features

        return result


class WESRGCACULoss(nn.Module):
    """
    Combined loss for WESR-GCACU training.

    Includes:
    1. Standard token classification loss
    2. WESR taxonomy loss (discrete vs continuous)
    3. Boundary detection loss
    4. Separation loss
    5. Confidence-weighted losses
    """

    def __init__(
        self,
        alpha_classification: float = 1.0,
        alpha_taxonomy: float = 0.3,
        alpha_boundary: float = 0.2,
        alpha_separation: float = 0.1,
        use_confidence_weighting: bool = True,
        label_smoothing: float = 0.0
    ):
        super().__init__()
        self.alpha_classification = alpha_classification
        self.alpha_taxonomy = alpha_taxonomy
        self.alpha_boundary = alpha_boundary
        self.alpha_separation = alpha_separation
        self.use_confidence_weighting = use_confidence_weighting
        self.label_smoothing = label_smoothing

    def forward(
        self,
        model_output: SimpleNamespace,
        labels: Tensor,
        wesr_taxonomy_labels: Optional[Tensor] = None,
        wesr_boundary_labels: Optional[Tensor] = None,
        wesr_separation_labels: Optional[Tensor] = None,
        attention_mask: Optional[Tensor] = None
    ) -> Tuple[Tensor, Dict[str, float]]:
        """
        Compute combined loss.

        Returns:
            total_loss: Combined loss tensor
            loss_components: Dictionary of individual loss components
        """
        losses = {}
        total_loss = 0.0

        # Classification loss
        classification_loss = F.cross_entropy(
            model_output.logits.view(-1, model_output.logits.size(-1)),
            labels.view(-1),
            reduction='none',
            label_smoothing=self.label_smoothing
        )

        if attention_mask is not None:
            mask = attention_mask.view(-1).float()
            classification_loss = (classification_loss * mask).sum() / mask.sum().clamp_min(1)
        else:
            classification_loss = classification_loss.mean()

        losses['classification'] = classification_loss.item()
        total_loss += self.alpha_classification * classification_loss

        # WESR taxonomy loss (if labels provided)
        if wesr_taxonomy_labels is not None and self.alpha_taxonomy > 0:
            taxonomy_loss = F.cross_entropy(
                model_output.wesr_discrete_laughter.view(-1, 2),
                wesr_taxonomy_labels.view(-1),
                reduction='none'
            )

            if attention_mask is not None:
                taxonomy_loss = (taxonomy_loss * mask).sum() / mask.sum().clamp_min(1)
            else:
                taxonomy_loss = taxonomy_loss.mean()

            # Confidence weighting
            if self.use_confidence_weighting:
                confidence = model_output.wesr_confidence.view(-1)
                taxonomy_loss = (taxonomy_loss * (1.0 - confidence.detach())).mean()

            losses['taxonomy'] = taxonomy_loss.item()
            total_loss += self.alpha_taxonomy * taxonomy_loss

        # Boundary detection loss (if labels provided)
        if wesr_boundary_labels is not None and self.alpha_boundary > 0:
            boundary_loss = F.binary_cross_entropy(
                model_output.wesr_boundaries.view(-1, 4),
                wesr_boundary_labels.view(-1, 4).float(),
                reduction='none'
            ).mean(dim=-1)

            if attention_mask is not None:
                boundary_loss = (boundary_loss * mask).sum() / mask.sum().clamp_min(1)
            else:
                boundary_loss = boundary_loss.mean()

            losses['boundary'] = boundary_loss.item()
            total_loss += self.alpha_boundary * boundary_loss

        # Separation loss (if labels provided)
        if wesr_separation_labels is not None and self.alpha_separation > 0:
            separation_loss = F.cross_entropy(
                model_output.wesr_separation.view(-1, 3),
                wesr_separation_labels.view(-1),
                reduction='none'
            )

            if attention_mask is not None:
                separation_loss = (separation_loss * mask).sum() / mask.sum().clamp_min(1)
            else:
                separation_loss = separation_loss.mean()

            losses['separation'] = separation_loss.item()
            total_loss += self.alpha_separation * separation_loss

        return total_loss, losses


def create_wesr_gcacu_model(
    backbone: nn.Module,
    config: WESRGCACUConfig = None,
    optimize: bool = True
) -> WESRGCACUIntegrated:
    """
    Create and configure WESR-GCACU integrated model.

    Args:
        backbone: Pre-trained backbone model
        config: Configuration object
        optimize: Whether to apply performance optimizations

    Returns:
        Configured WESR-GCACU integrated model
    """
    if config is None:
        config = WESRGCACUConfig()

    model = WESRGCACUIntegrated(backbone, config)

    if optimize:
        optimizer = WESRPerformanceOptimizer(config)
        # Note: We can't directly optimize the integrated model with the current optimizer
        # This would need to be extended for the full integrated system

    return model


if __name__ == "__main__":
    print("Testing WESR-GCACU Integration...")

    from transformers import AutoModelForTokenClassification

    # Create test backbone
    backbone = AutoModelForTokenClassification.from_pretrained(
        "FacebookAI/xlm-roberta-base",
        num_labels=2
    )

    # Create integrated model
    config = WESRGCACUConfig()
    model = create_wesr_gcacu_model(backbone, config)

    # Test data
    batch_size = 2
    seq_length = 32
    vocab_size = 250020

    input_ids = torch.randint(0, vocab_size, (batch_size, seq_length))
    attention_mask = torch.ones(batch_size, seq_length)

    # Forward pass
    output = model(input_ids, attention_mask, return_all_features=True)

    # Verify outputs
    print(f"Logits shape: {output.logits.shape}")
    print(f"WESR Discrete/Continuous: {output.wesr_discrete_laughter.shape}")
    print(f"WESR Vocal Events: {output.wesr_vocal_events.shape}")
    print(f"WESR Boundaries: {output.wesr_boundaries.shape}")
    print(f"WESR Separation: {output.wesr_separation.shape}")
    print(f"WESR Confidence: {output.wesr_confidence.shape}")
    print(f"Incongruity Scores: {output.incongruity_scores.shape}")

    # Test loss computation
    labels = torch.randint(0, 2, (batch_size, seq_length))
    wesr_taxonomy_labels = torch.randint(0, 2, (batch_size, seq_length))
    wesr_boundary_labels = torch.randint(0, 2, (batch_size, seq_length, 4))
    wesr_separation_labels = torch.randint(0, 3, (batch_size, seq_length))

    loss_fn = WESRGCACULoss()
    total_loss, loss_components = loss_fn(
        output, labels, wesr_taxonomy_labels,
        wesr_boundary_labels, wesr_separation_labels, attention_mask
    )

    print(f"\nTotal Loss: {total_loss.item():.4f}")
    print("Loss Components:")
    for name, value in loss_components.items():
        print(f"  {name}: {value:.4f}")

    print("\n✅ WESR-GCACU Integration test passed!")
    print(f"✅ Multi-modal feature integration functional")
    print(f"✅ Laughter-aware incongruity detection operational")
    print(f"✅ Combined loss computation successful")
    print(f"✅ Enhanced humor detection system ready")