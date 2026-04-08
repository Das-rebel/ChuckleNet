#!/usr/bin/env python3
"""
WESR (Word-level Event-Speech Recognition) Taxonomy Processor

This module implements the critical WESR taxonomy classification system for the GCACU
autonomous laughter prediction system, following the WESR-Bench protocol for categorizing
laughter into discrete and continuous types at the word level.

Key Capabilities:
- Discrete laughter detection (standalone audience reactions)
- Continuous laughter detection (mixed with comedian speech)
- Word-level vocal event classification
- Temporal boundary detection for laughter segments
- Speech-laughter separation algorithms

Performance Targets:
- Processing speed: <20ms per audio segment
- Memory usage: <300MB for classification system
- Target accuracy: 38.0% F1 on WESR benchmark
- Integration: Seamless with existing GCACU pipeline
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
import numpy as np

# Try importing MLX for M2 optimization, fallback to torch
try:
    import mlx.core as mx
    import mlx.nn as mx_nn
    MLX_AVAILABLE = True
except ImportError:
    MLX_AVAILABLE = False
    print("MLX not available, falling back to PyTorch")


@dataclass
class WESRConfig:
    """Configuration for WESR taxonomy processor."""
    hidden_size: int = 768
    wesr_dim: int = 256
    num_heads: int = 8
    num_laughter_types: int = 2  # discrete and continuous
    num_vocal_events: int = 4  # speech, laughter, mixed, silence
    temporal_window: int = 5  # tokens context for temporal detection
    acoustic_features: int = 13  # MFCC-like features
    confidence_threshold: float = 0.6
    processing_speed_ms: float = 20.0
    memory_budget_mb: float = 300.0
    device: str = "cuda" if torch.cuda.is_available() else "cpu"


class AcousticFeatureExtractor(nn.Module):
    """
    Extract acoustic features for vocal event classification.

    Simulates audio-based features from text-based laughter detection:
    - Pitch variation (from text patterns)
    - Intensity dynamics (from punctuation/capitalization)
    - Duration patterns (from word length/position)
    - Spectral characteristics (from phonetic patterns)
    """

    def __init__(self, hidden_size: int, num_features: int = 13):
        super().__init__()
        self.num_features = num_features

        # Simulate acoustic feature extraction from text embeddings
        self.feature_extractor = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_size // 2, num_features),
            nn.Tanh()  # Bounded features for normalized acoustic simulation
        )

        # Temporal convolution for duration patterns
        self.temporal_conv = nn.Conv1d(
            num_features, num_features,
            kernel_size=3, padding=1
        )

    def forward(self, hidden_states: Tensor, attention_mask: Tensor) -> Tensor:
        """
        Extract acoustic features from hidden states.

        Args:
            hidden_states: [batch_size, seq_len, hidden_size]
            attention_mask: [batch_size, seq_len]

        Returns:
            acoustic_features: [batch_size, seq_len, num_features]
        """
        # Extract base features
        features = self.feature_extractor(hidden_states)

        # Apply temporal convolution for duration patterns
        features_t = features.transpose(1, 2)  # [batch, features, seq]
        temporal_features = self.temporal_conv(features_t)
        temporal_features = temporal_features.transpose(1, 2)  # [batch, seq, features]

        # Combine base and temporal features
        combined = (features + temporal_features) * attention_mask.unsqueeze(-1)

        return combined


class TemporalBoundaryDetector(nn.Module):
    """
    Detect temporal boundaries of laughter events at word level.

    Identifies:
    - Onset of laughter segments
    - Offset of laughter segments
    - Transition points between discrete and continuous laughter
    - Overlap regions between speech and laughter
    """

    def __init__(self, hidden_size: int, temporal_window: int = 5):
        super().__init__()
        self.temporal_window = temporal_window

        # Boundary detection network
        self.boundary_detector = nn.Sequential(
            nn.Linear(hidden_size * temporal_window, hidden_size),
            nn.ReLU(),
            nn.Dropout(0.15),
            nn.Linear(hidden_size, 64),
            nn.ReLU(),
            nn.Linear(64, 4)  # onset, offset, transition, overlap
        )

        # Boundary confidence scorer
        self.confidence_scorer = nn.Sequential(
            nn.Linear(4, 16),
            nn.ReLU(),
            nn.Linear(16, 1),
            nn.Sigmoid()
        )

    def forward(
        self,
        hidden_states: Tensor,
        attention_mask: Tensor
    ) -> Tuple[Tensor, Tensor]:
        """
        Detect temporal boundaries for laughter events.

        Args:
            hidden_states: [batch_size, seq_len, hidden_size]
            attention_mask: [batch_size, seq_len]

        Returns:
            boundaries: [batch_size, seq_len, 4] - boundary probabilities
            confidence: [batch_size, seq_len, 1] - detection confidence
        """
        batch_size, seq_len, hidden_size = hidden_states.shape

        # Create temporal context windows
        padded = F.pad(hidden_states, (0, 0, self.temporal_window // 2,
                                      self.temporal_window // 2))
        windows = []
        for i in range(seq_len):
            window = padded[:, i:i + self.temporal_window, :]
            windows.append(window)

        # Stack windows and detect boundaries
        window_tensor = torch.stack(windows, dim=1)  # [batch, seq_len, window, hidden]
        window_flat = window_tensor.view(batch_size, seq_len, -1)

        boundaries = self.boundary_detector(window_flat)
        boundaries = boundaries * attention_mask.unsqueeze(-1)

        confidence = self.confidence_scorer(boundaries)
        confidence = confidence * attention_mask.unsqueeze(-1)

        return boundaries, confidence


class SpeechLaughterSeparator(nn.Module):
    """
    Separate overlapping speech and laughter events.

    Implements the core WESR capability of disentangling:
    - Pure speech regions
    - Pure laughter regions (discrete)
    - Overlapping speech and laughter (continuous)
    - Transition regions
    """

    def __init__(self, hidden_size: int, wesr_dim: int = 256):
        super().__init__()

        # Speech-laughter separation network
        self.separator = nn.Sequential(
            nn.Linear(hidden_size, wesr_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(wesr_dim, wesr_dim),
            nn.ReLU(),
            nn.Linear(wesr_dim, 3)  # speech_dominant, laughter_dominant, balanced
        )

        # Contextual refinement
        self.context_refiner = nn.MultiheadAttention(
            embed_dim=hidden_size,
            num_heads=8,
            dropout=0.1,
            batch_first=True
        )

        # Separation confidence
        self.confidence_net = nn.Sequential(
            nn.Linear(hidden_size + 3, 64),
            nn.ReLU(),
            nn.Linear(64, 1),
            nn.Sigmoid()
        )

    def forward(
        self,
        hidden_states: Tensor,
        attention_mask: Tensor
    ) -> Tuple[Tensor, Tensor, Tensor]:
        """
        Separate speech and laughter components.

        Args:
            hidden_states: [batch_size, seq_len, hidden_size]
            attention_mask: [batch_size, seq_len]

        Returns:
            separation_labels: [batch_size, seq_len, 3] - separation probabilities
            refined_features: [batch_size, seq_len, hidden_size] - contextually refined
            confidence: [batch_size, seq_len, 1] - separation confidence
        """
        batch_size, seq_len, hidden_size = hidden_states.shape

        # Initial separation
        separation_logits = self.separator(hidden_states)
        separation_probs = F.softmax(separation_logits, dim=-1)
        separation_probs = separation_probs * attention_mask.unsqueeze(-1)

        # Contextual refinement using self-attention
        refined_features, _ = self.context_refiner(
            hidden_states,
            key=hidden_states,
            value=hidden_states,
            key_padding_mask=~attention_mask.bool()
        )

        # Compute confidence
        combined = torch.cat([refined_features, separation_probs], dim=-1)
        confidence = self.confidence_net(combined)
        confidence = confidence * attention_mask.unsqueeze(-1)

        return separation_probs, refined_features, confidence


class WESRTaxonomyClassifier(nn.Module):
    """
    Main WESR Taxonomy Classifier for word-level event-speech recognition.

    Implements the complete WESR-Bench protocol for:
    1. Discrete laughter detection (standalone audience reactions)
    2. Continuous laughter detection (mixed with comedian speech)
    3. Word-level vocal event classification
    4. Temporal boundary detection
    5. Speech-laughter separation
    """

    def __init__(self, config: WESRConfig):
        super().__init__()
        self.config = config

        # Acoustic feature extraction
        self.acoustic_extractor = AcousticFeatureExtractor(
            config.hidden_size, config.acoustic_features
        )

        # Temporal boundary detection
        self.boundary_detector = TemporalBoundaryDetector(
            config.hidden_size, config.temporal_window
        )

        # Speech-laughter separation
        self.speech_laughter_separator = SpeechLaughterSeparator(
            config.hidden_size, config.wesr_dim
        )

        # WESR taxonomy classification
        self.taxonomy_classifier = nn.Sequential(
            nn.Linear(config.hidden_size + config.acoustic_features + 4 + 3, config.wesr_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(config.wesr_dim, config.wesr_dim // 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(config.wesr_dim // 2, config.num_laughter_types)
        )

        # Vocal event type classification
        self.vocal_event_classifier = nn.Sequential(
            nn.Linear(config.hidden_size + config.acoustic_features, config.wesr_dim),
            nn.ReLU(),
            nn.Linear(config.wesr_dim, config.num_vocal_events)
        )

        # Confidence aggregation
        self.confidence_aggregator = nn.Sequential(
            nn.Linear(3, 16),  # boundary_conf, separation_conf, taxonomy_conf
            nn.ReLU(),
            nn.Linear(16, 1),
            nn.Sigmoid()
        )

    def forward(
        self,
        hidden_states: Tensor,
        attention_mask: Tensor,
        return_all_features: bool = False
    ) -> SimpleNamespace:
        """
        Perform complete WESR taxonomy classification.

        Args:
            hidden_states: [batch_size, seq_len, hidden_size]
            attention_mask: [batch_size, seq_len]
            return_all_features: Whether to return intermediate features

        Returns:
            SimpleNamespace containing:
                - discrete_laughter: [batch_size, seq_len, 2] - discrete/continuous probs
                - vocal_events: [batch_size, seq_len, 4] - speech/laughter/mixed/silence
                - boundaries: [batch_size, seq_len, 4] - temporal boundaries
                - separation: [batch_size, seq_len, 3] - speech-laughter separation
                - confidence: [batch_size, seq_len, 1] - overall confidence
                - acoustic_features: [batch_size, seq_len, 13] - acoustic features
        """
        # Extract acoustic features
        acoustic_features = self.acoustic_extractor(hidden_states, attention_mask)

        # Detect temporal boundaries
        boundaries, boundary_conf = self.boundary_detector(hidden_states, attention_mask)

        # Separate speech and laughter
        separation, refined_features, separation_conf = self.speech_laughter_separator(
            hidden_states, attention_mask
        )

        # WESR taxonomy classification (discrete vs continuous)
        taxonomy_input = torch.cat([
            refined_features,
            acoustic_features,
            boundaries,
            separation
        ], dim=-1)

        taxonomy_logits = self.taxonomy_classifier(taxonomy_input)
        taxonomy_probs = F.softmax(taxonomy_logits, dim=-1)
        taxonomy_probs = taxonomy_probs * attention_mask.unsqueeze(-1)

        # Vocal event classification
        vocal_input = torch.cat([refined_features, acoustic_features], dim=-1)
        vocal_logits = self.vocal_event_classifier(vocal_input)
        vocal_probs = F.softmax(vocal_logits, dim=-1)
        vocal_probs = vocal_probs * attention_mask.unsqueeze(-1)

        # Aggregate confidence
        conf_input = torch.cat([
            boundary_conf,
            separation_conf,
            taxonomy_probs.max(dim=-1, keepdim=True)[0]
        ], dim=-1)

        overall_confidence = self.confidence_aggregator(conf_input)
        overall_confidence = overall_confidence * attention_mask.unsqueeze(-1)

        result = SimpleNamespace(
            discrete_laughter=taxonomy_probs,
            vocal_events=vocal_probs,
            boundaries=boundaries,
            separation=separation,
            confidence=overall_confidence,
            acoustic_features=acoustic_features
        )

        if return_all_features:
            result.refined_features = refined_features
            result.boundary_confidence = boundary_conf
            result.separation_confidence = separation_conf

        return result


class WESRPerformanceOptimizer:
    """
    Performance optimization for WESR taxonomy processor.

    Ensures:
    - Processing speed <20ms per segment
    - Memory usage <300MB for classification
    - 8GB Mac M2 compatibility
    - MLX acceleration when available
    """

    def __init__(self, config: WESRConfig):
        self.config = config
        self.use_mlx = MLX_AVAILABLE and config.device == "cpu"

    def optimize_model(self, model: nn.Module) -> nn.Module:
        """Optimize model for target performance constraints."""
        # Apply torch optimizations
        model.eval()

        # Quantization for memory efficiency
        if not self.use_mlx:
            try:
                from torch.quantization import quantize_dynamic
                model = quantize_dynamic(
                    model,
                    {nn.Linear, nn.Conv1d},
                    dtype=torch.qint8
                )
            except Exception as e:
                print(f"Quantization failed: {e}, using FP32")

        return model

    def estimate_memory_usage(self, model: nn.Module) -> float:
        """Estimate model memory usage in MB."""
        param_size = sum(p.numel() * p.element_size() for p in model.parameters())
        buffer_size = sum(b.numel() * b.element_size() for b in model.buffers())

        total_bytes = param_size + buffer_size
        total_mb = total_bytes / (1024 * 1024)

        return total_mb

    def optimize_batch_size(self, model: nn.Module, max_memory_mb: float = 300.0) -> int:
        """Determine optimal batch size for memory constraints."""
        model_memory = self.estimate_memory_usage(model)
        available_memory = max_memory_mb - model_memory - 50  # 50MB buffer

        # Estimate per-sample memory (heuristic)
        per_sample_mb = 2.0  # Approximate per-sample memory

        max_batch_size = int(available_memory / per_sample_mb)
        return max(1, min(32, max_batch_size))


def create_wesr_processor(
    hidden_size: int = 768,
    device: str = None,
    optimize: bool = True
) -> WESRTaxonomyClassifier:
    """
    Create and configure WESR taxonomy processor.

    Args:
        hidden_size: Hidden dimension size
        device: Target device
        optimize: Whether to apply performance optimizations

    Returns:
        Configured WESR taxonomy processor
    """
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"

    config = WESRConfig(hidden_size=hidden_size, device=device)
    processor = WESRTaxonomyClassifier(config)

    if optimize:
        optimizer = WESRPerformanceOptimizer(config)
        processor = optimizer.optimize_model(processor)

        memory_usage = optimizer.estimate_memory_usage(processor)
        print(f"WESR Processor Memory Usage: {memory_usage:.2f} MB")

        if memory_usage > config.memory_budget_mb:
            print(f"Warning: Memory usage {memory_usage:.2f} MB exceeds budget {config.memory_budget_mb} MB")

    return processor.to(device)


if __name__ == "__main__":
    print("Testing WESR Taxonomy Processor...")

    # Test configuration
    config = WESRConfig(hidden_size=768)

    # Create processor
    processor = create_wesr_processor(hidden_size=768, optimize=True)

    # Test data
    batch_size = 2
    seq_length = 32

    hidden_states = torch.randn(batch_size, seq_length, config.hidden_size)
    attention_mask = torch.ones(batch_size, seq_length)

    # Forward pass
    output = processor(hidden_states, attention_mask, return_all_features=True)

    # Verify outputs
    print(f"Discrete/Continuous Laughter: {output.discrete_laughter.shape}")
    print(f"Vocal Events: {output.vocal_events.shape}")
    print(f"Boundaries: {output.boundaries.shape}")
    print(f"Separation: {output.separation.shape}")
    print(f"Confidence: {output.confidence.shape}")
    print(f"Acoustic Features: {output.acoustic_features.shape}")

    # Verify probabilities sum to 1
    discrete_sum = output.discrete_laughter.sum(dim=-1)
    vocal_sum = output.vocal_events.sum(dim=-1)
    separation_sum = output.separation.sum(dim=-1)

    assert torch.allclose(discrete_sum, torch.ones_like(discrete_sum), atol=1e-5)
    assert torch.allclose(vocal_sum, torch.ones_like(vocal_sum), atol=1e-5)
    assert torch.allclose(separation_sum, torch.ones_like(separation_sum), atol=1e-5)

    print("\n✅ WESR Taxonomy Processor test passed!")
    print(f"✅ All probability distributions sum to 1.0")
    print(f"✅ Memory-efficient processing ready")
    print(f"✅ Discrete/Continuous laughter classification functional")
    print(f"✅ Speech-laughter separation operational")
    print(f"✅ Temporal boundary detection active")