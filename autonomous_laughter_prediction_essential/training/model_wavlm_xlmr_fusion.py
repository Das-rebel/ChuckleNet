#!/usr/bin/env python3
"""
Gated multimodal fusion model for utterance-level laughter prediction.

Architecture:
    - XLM-R-base text encoder (768-dim)
    - Audio projection: WavLM embedding (768-dim) → 256-dim
    - Text projection: XLM-R [CLS] (768-dim) → 256-dim
    - Gated fusion: sigmoid gate over concat([t, a]) → 256-dim
    - fused = g * t + (1-g) * a
    - Classifier: 256 → 128 → 2

Supports 3 training phases:
    Phase 1: Text-only (XLM-R + classifier, no audio)
    Phase 2: Frozen XLM-R, train audio_proj + gate + classifier
    Phase 3: Joint fine-tune (unfreeze top 2 XLM-R layers)
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import XLMRobertaModel, XLMRobertaConfig


# ---------------------------------------------------------------------------
# Gated Multimodal Fusion Module
# ---------------------------------------------------------------------------

class GatedMultimodalFusion(nn.Module):
    """
    Gated fusion: g = sigmoid(W * concat([t, a]) + b)
                  fused = g * t + (1-g) * a
    
    The gate learns when to trust text vs audio per-utterance.
    For text-heavy jokes: gate → 1 (trust text)
    For prosodic cues (pause, delivery): gate → 0 (trust audio)
    """
    
    def __init__(
        self,
        text_dim: int = 768,
        audio_dim: int = 768,
        fusion_dim: int = 256,
        dropout: float = 0.2,
    ):
        super().__init__()
        
        self.text_proj = nn.Sequential(
            nn.Linear(text_dim, fusion_dim),
            nn.LayerNorm(fusion_dim),
            nn.GELU(),
            nn.Dropout(dropout),
        )
        
        self.audio_proj = nn.Sequential(
            nn.Linear(audio_dim, fusion_dim),
            nn.LayerNorm(fusion_dim),
            nn.GELU(),
            nn.Dropout(dropout),
        )
        
        # Gate: concat([t_proj, a_proj]) → fusion_dim
        self.gate = nn.Sequential(
            nn.Linear(fusion_dim * 2, fusion_dim),
            nn.Sigmoid(),
        )
        
        self.fusion_dim = fusion_dim
    
    def forward(
        self,
        text_features: torch.Tensor,
        audio_features: torch.Tensor,
        return_gate_stats: bool = False,
    ) -> torch.Tensor:
        """
        Args:
            text_features: (batch, text_dim) - XLM-R [CLS] or pooled output
            audio_features: (batch, audio_dim) - WavLM mean-pooled embedding
        
        Returns:
            fused: (batch, fusion_dim)
        """
        t = self.text_proj(text_features)   # (B, fusion_dim)
        a = self.audio_proj(audio_features)  # (B, fusion_dim)
        
        g = self.gate(torch.cat([t, a], dim=-1))  # (B, fusion_dim)
        fused = g * t + (1 - g) * a
        
        if return_gate_stats:
            # Return gate statistics for analysis
            gate_mean = g.mean().detach()
            gate_std = g.std().detach()
            gate_per_sample = g.mean(dim=-1).detach()  # (B,)
            return fused, {
                "gate_mean": gate_mean,
                "gate_std": gate_std,
                "gate_per_sample": gate_per_sample,
                "text_norm": t.norm(dim=-1).mean().detach(),
                "audio_norm": a.norm(dim=-1).mean().detach(),
            }
        
        return fused


# ---------------------------------------------------------------------------
# Classifier Head
# ---------------------------------------------------------------------------

class ClassifierHead(nn.Module):
    """Simple 2-layer classifier with dropout."""
    
    def __init__(self, in_dim: int = 256, hidden_dim: int = 128, num_labels: int = 2, dropout: float = 0.2):
        super().__init__()
        self.layers = nn.Sequential(
            nn.Linear(in_dim, hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, num_labels),
        )
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.layers(x)


# ---------------------------------------------------------------------------
# Full Model: XLM-R + Gated Fusion
# ---------------------------------------------------------------------------

class WavLMXLMRFusionModel(nn.Module):
    """
    Full multimodal model combining XLM-R text encoder with WavLM audio
    via gated fusion.
    
    Training phases:
        phase=1: Text-only. XLM-R → [CLS] → classifier. Audio ignored.
        phase=2: Frozen XLM-R. Train audio_proj + gate + classifier. 
        phase=3: Joint. Unfreeze top 2 XLM-R layers + everything.
    """
    
    def __init__(
        self,
        model_name: str = "FacebookAI/xlm-roberta-base",
        text_dim: int = 768,
        audio_dim: int = 768,
        fusion_dim: int = 256,
        classifier_hidden_dim: int = 128,
        num_labels: int = 2,
        dropout: float = 0.2,
        freeze_layers: int = 8,  # Number of bottom XLM-R layers to freeze
    ):
        super().__init__()
        
        self.text_dim = text_dim
        self.audio_dim = audio_dim
        self.fusion_dim = fusion_dim
        self.num_labels = num_labels
        self.freeze_layers = freeze_layers
        
        # XLM-R encoder
        self.xlmr = XLMRobertaModel.from_pretrained(model_name)
        
        # Fusion module
        self.fusion = GatedMultimodalFusion(
            text_dim=text_dim,
            audio_dim=audio_dim,
            fusion_dim=fusion_dim,
            dropout=dropout,
        )
        
        # Text-only classifier (for phase 1)
        self.text_classifier = ClassifierHead(
            in_dim=fusion_dim,
            hidden_dim=classifier_hidden_dim,
            num_labels=num_labels,
            dropout=dropout,
        )
        
        # Fusion classifier (for phases 2+3)
        self.fusion_classifier = ClassifierHead(
            in_dim=fusion_dim,
            hidden_dim=classifier_hidden_dim,
            num_labels=num_labels,
            dropout=dropout,
        )
        
        # Initialize
        self._init_weights()
    
    def _init_weights(self):
        """Initialize classifier weights with proper scaling."""
        for module in [self.fusion, self.text_classifier, self.fusion_classifier]:
            for name, param in module.named_parameters():
                if "weight" in name and param.dim() >= 2:
                    nn.init.xavier_uniform_(param)
                elif "bias" in name:
                    nn.init.zeros_(param)
    
    def set_phase(self, phase: int):
        """
        Configure model for a specific training phase.
        
        Phase 1: Text-only. All XLM-R frozen. Only text_classifier trains.
        Phase 2: Frozen XLM-R. fusion + fusion_classifier train.
        Phase 3: Top 2 XLM-R layers unfrozen. Everything trains.
        """
        # First, freeze everything
        for param in self.parameters():
            param.requires_grad = False
        
        if phase == 1:
            # Text-only: XLM-R frozen, text_classifier trainable
            # Unfreeze XLM-R last 2 layers + classifier for text baseline
            for param in self.text_classifier.parameters():
                param.requires_grad = True
            # Unfreeze top 2 XLM-R layers for text-only fine-tuning
            for layer in self.xlmr.encoder.layer[-2:]:
                for param in layer.parameters():
                    param.requires_grad = True
            # Also unfreeze pooler
            if hasattr(self.xlmr, 'pooler') and self.xlmr.pooler is not None:
                for param in self.xlmr.pooler.parameters():
                    param.requires_grad = True
        
        elif phase == 2:
            # Frozen XLM-R, train audio path + gate + classifier
            for param in self.fusion.parameters():
                param.requires_grad = True
            for param in self.fusion_classifier.parameters():
                param.requires_grad = True
        
        elif phase == 3:
            # Joint fine-tune: everything trainable
            for param in self.parameters():
                param.requires_grad = True
        
        # Count trainable params
        trainable = sum(p.numel() for p in self.parameters() if p.requires_grad)
        total = sum(p.numel() for p in self.parameters())
        print(f"Phase {phase}: {trainable:,} / {total:,} parameters trainable "
              f"({100*trainable/total:.1f}%)")
    
    def get_xlmr_cls(self, input_ids: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
        """Extract [CLS] / <s> token representation from XLM-R."""
        outputs = self.xlmr(input_ids=input_ids, attention_mask=attention_mask)
        # XLM-R doesn't have a pooler by default, use last hidden state of first token
        cls_vector = outputs.last_hidden_state[:, 0, :]  # (B, 768)
        return cls_vector
    
    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        audio_embeddings: torch.Tensor,
        phase: int = 3,
        return_gate_stats: bool = False,
    ) -> dict:
        """
        Args:
            input_ids: (B, seq_len) - tokenized text
            attention_mask: (B, seq_len) - attention mask
            audio_embeddings: (B, 768) - pre-extracted WavLM embeddings
            phase: Training phase (1=text-only, 2=frozen-text+audio, 3=joint)
            return_gate_stats: Whether to return gate analysis
        
        Returns:
            dict with 'logits', 'gate_stats' (optional)
        """
        # Get text features
        text_features = self.get_xlmr_cls(input_ids, attention_mask)  # (B, 768)
        
        if phase == 1:
            # Text-only mode
            t = self.fusion.text_proj(text_features)  # (B, fusion_dim)
            logits = self.text_classifier(t)
            result = {"logits": logits}
            if return_gate_stats:
                result["gate_stats"] = {"phase": 1, "text_norm": t.norm(dim=-1).mean()}
            return result
        
        # Multimodal mode (phases 2 and 3)
        fused, gate_stats = self.fusion(
            text_features, audio_embeddings,
            return_gate_stats=True,
        )
        logits = self.fusion_classifier(fused)
        
        result = {"logits": logits}
        if return_gate_stats:
            result["gate_stats"] = gate_stats
        
        return result
    
    def predict(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        audio_embeddings: torch.Tensor,
        phase: int = 3,
    ) -> dict:
        """Inference mode: returns logits, predicted labels, and gate statistics."""
        self.eval()
        with torch.no_grad():
            return self.forward(
                input_ids, attention_mask, audio_embeddings,
                phase=phase, return_gate_stats=True,
            )


# ---------------------------------------------------------------------------
# Model Config
# ---------------------------------------------------------------------------

@dataclass
class FusionModelConfig:
    """Configuration for WavLMXLMRFusionModel."""
    model_name: str = "FacebookAI/xlm-roberta-base"
    text_dim: int = 768
    audio_dim: int = 768
    fusion_dim: int = 256
    classifier_hidden_dim: int = 128
    num_labels: int = 2
    dropout: float = 0.2
    freeze_layers: int = 8
    
    max_seq_length: int = 256
    batch_size: int = 16
    eval_batch_size: int = 32
    
    # Phase schedules
    phase1_epochs: int = 3
    phase2_epochs: int = 3
    phase3_epochs: int = 2
    
    # Learning rates per phase
    phase1_lr: float = 2e-5
    phase2_lr: float = 1e-3
    phase3_lr: float = 5e-6
    
    # Weight decay
    weight_decay: float = 0.01
    
    # Label smoothing
    label_smoothing: float = 0.1
    
    # Class weights (will be computed from data)
    pos_weight: float = 1.0
    
    # Warmup
    warmup_ratio: float = 0.1
    
    # Gradient clipping
    max_grad_norm: float = 1.0
    
    # Device
    device: str = "auto"


def create_model(config: Optional[FusionModelConfig] = None) -> WavLMXLMRFusionModel:
    """Create model from config."""
    if config is None:
        config = FusionModelConfig()
    return WavLMXLMRFusionModel(
        model_name=config.model_name,
        text_dim=config.text_dim,
        audio_dim=config.audio_dim,
        fusion_dim=config.fusion_dim,
        classifier_hidden_dim=config.classifier_hidden_dim,
        num_labels=config.num_labels,
        dropout=config.dropout,
        freeze_layers=config.freeze_layers,
    )