#!/usr/bin/env python3
"""
GCACU: Gated Contrast-Attention Contextualized Understanding Network

Simplified implementation based on the plan:
- Dual-path architecture for semantic conflict detection
- Hierarchical gating for incongruity quantification
- Target: 77.0% F1 on textual incongruity tasks
"""

from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch import Tensor
from typing import Optional, Tuple, Dict, List
from dataclasses import dataclass
from types import SimpleNamespace


@dataclass
class GCACUConfig:
    hidden_size: int = 768
    gcacu_dim: int = 128
    num_heads: int = 4
    gate_scale: float = 0.3
    dropout: float = 0.1


class SemanticConflictAttention(nn.Module):
    """Computes semantic conflict attention between token pairs."""

    def __init__(self, hidden_size: int, num_heads: int = 4):
        super().__init__()
        self.num_heads = num_heads
        self.head_dim = hidden_size // num_heads

        self.q_proj = nn.Linear(hidden_size, hidden_size)
        self.k_proj = nn.Linear(hidden_size, hidden_size)
        self.v_proj = nn.Linear(hidden_size, hidden_size)
        self.out_proj = nn.Linear(hidden_size, hidden_size)

        self.conflict_weight = nn.Parameter(torch.ones(num_heads) / num_heads)

    def forward(self, sequence_output: Tensor, attention_mask: Tensor) -> Tuple[Tensor, Tensor]:
        batch_size, seq_len, hidden_size = sequence_output.shape

        q = self.q_proj(sequence_output).view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        k = self.k_proj(sequence_output).view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        v = self.v_proj(sequence_output).view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)

        attn_weights = torch.matmul(q, k.transpose(-2, -1)) / (self.head_dim ** 0.5)
        attn_weights = attn_weights.masked_fill(attention_mask.unsqueeze(1).unsqueeze(2) == 0, float('-inf'))
        attn_weights = F.softmax(attn_weights, dim=-1)

        attn_output = torch.matmul(attn_weights, v)
        attn_output = attn_output.transpose(1, 2).contiguous().view(batch_size, seq_len, self.num_heads, self.head_dim)

        conflict_weights = self.conflict_weight.view(1, 1, self.num_heads, 1)
        weighted_conflict = (attn_output * conflict_weights).sum(dim=2, keepdim=True)

        attn_output = attn_output.contiguous().view(batch_size, seq_len, hidden_size)
        attn_output = self.out_proj(attn_output)

        return attn_output, weighted_conflict


class GCACUGating(nn.Module):
    """Hierarchical gating mechanism for incongruity detection."""

    def __init__(self, hidden_size: int, gcacu_dim: int):
        super().__init__()
        self.gate_net = nn.Sequential(
            nn.Linear(hidden_size * 2, gcacu_dim),
            nn.Tanh(),
            nn.Linear(gcacu_dim, hidden_size),
            nn.Sigmoid()
        )
        self.proj_net = nn.Sequential(
            nn.Linear(hidden_size * 2, gcacu_dim),
            nn.Tanh(),
            nn.Linear(gcacu_dim, hidden_size)
        )

    def forward(self, sequence_output: Tensor, context_summary: Tensor) -> Tensor:
        combined = torch.cat([sequence_output, context_summary.expand(-1, sequence_output.size(1), -1)], dim=-1)
        gate = self.gate_net(combined)
        proj = self.proj_net(combined)
        return gate * proj


class GCACUTokenClassifier(nn.Module):
    """
    Gated Contrast-Attention Contextualized Understanding Network.

    Detects semantic conflicts in comedy transcripts by:
    1. Computing contrastive attention between tokens
    2. Using hierarchical gating to quantify incongruity
    3. Combining signals for laughter prediction
    """

    def __init__(self, backbone: nn.Module, config: GCACUConfig = None):
        super().__init__()
        self.config = config or GCACUConfig()
        self.backbone = backbone

        hidden_size = self.config.hidden_size

        self.conflict_attention = SemanticConflictAttention(hidden_size, self.config.num_heads)
        self.gcacu_gating = GCACUGating(hidden_size, self.config.gcacu_dim)

        self.fusion = nn.Sequential(
            nn.Linear(hidden_size * 2, hidden_size),
            nn.Tanh(),
            nn.Dropout(self.config.dropout)
        )

    def forward(
        self,
        input_ids: Tensor,
        attention_mask: Tensor,
        return_incongruity_scores: bool = False
    ):
        roberta_outputs = self.backbone.roberta(
            input_ids=input_ids,
            attention_mask=attention_mask,
            return_dict=True,
        )
        sequence_output = roberta_outputs.last_hidden_state

        mask = attention_mask.unsqueeze(-1).float()
        denom = mask.sum(dim=1, keepdim=True).clamp_min(1.0)
        context_summary = (sequence_output * mask).sum(dim=1, keepdim=True) / denom

        conflict_features, incongruity_scores = self.conflict_attention(sequence_output, attention_mask)

        gated_features = self.gcacu_gating(sequence_output, context_summary)

        fused = self.fusion(torch.cat([conflict_features, gated_features], dim=-1))

        gated_output = sequence_output + (self.config.gate_scale * fused)

        logits = self.backbone.classifier(gated_output)

        if return_incongruity_scores:
            return SimpleNamespace(
                logits=logits,
                incongruity_scores=incongruity_scores.squeeze(-1),
                conflict_features=conflict_features
            )

        return SimpleNamespace(logits=logits)


class AdaptiveFocalLoss(nn.Module):
    """
    Adaptive Focal Loss for noisy label handling.

    Adapts gamma and alpha based on:
    - Label noise estimation per sample
    - Class difficulty from prediction confidence
    """

    def __init__(self, gamma: float = 2.0, label_smoothing: float = 0.0):
        super().__init__()
        self.gamma = gamma
        self.label_smoothing = label_smoothing

    def estimate_noise(self, logits: Tensor, labels: Tensor) -> Tensor:
        probs = F.softmax(logits, dim=-1)
        max_probs, _ = probs.max(dim=-1)
        return (1.0 - max_probs.detach()).unsqueeze(-1)

    def forward(self, logits: Tensor, labels: Tensor, attention_mask: Optional[Tensor] = None) -> Tensor:
        ce_loss = F.cross_entropy(
            logits.view(-1, logits.size(-1)),
            labels.view(-1),
            reduction='none',
            label_smoothing=self.label_smoothing
        )

        probs = F.softmax(logits, dim=-1)
        pt = torch.where(labels == 1, probs[:, 1], probs[:, 0]).view(-1)

        noise_estimate = self.estimate_noise(logits, labels)
        adaptive_gamma = self.gamma * (1.0 + noise_estimate.view(-1) * 0.5)

        focal_weight = (1 - pt.unsqueeze(-1)) ** adaptive_gamma.unsqueeze(-1)
        focal_weight = focal_weight.squeeze(-1)

        if attention_mask is not None:
            mask = attention_mask.view(-1).float()
            focal_loss = (ce_loss * focal_weight * mask).sum() / mask.sum().clamp_min(1)
        else:
            focal_loss = (ce_loss * focal_weight).mean()

        return focal_loss


def create_gcacu_model(backbone: nn.Module, gcacu_dim: int = 128, num_heads: int = 4, gate_scale: float = 0.3) -> GCACUTokenClassifier:
    config = GCACUConfig(
        hidden_size=int(backbone.config.hidden_size),
        gcacu_dim=gcacu_dim,
        num_heads=num_heads,
        gate_scale=gate_scale
    )
    return GCACUTokenClassifier(backbone, config)


if __name__ == "__main__":
    print("Testing GCACU Network...")

    from transformers import AutoModelForTokenClassification

    backbone = AutoModelForTokenClassification.from_pretrained(
        "FacebookAI/xlm-roberta-base",
        num_labels=2
    )

    model = create_gcacu_model(backbone)

    batch_size = 2
    seq_length = 32
    vocab_size = 250020

    input_ids = torch.randint(0, vocab_size, (batch_size, seq_length))
    attention_mask = torch.ones(batch_size, seq_length)

    output = model(input_ids, attention_mask, return_incongruity_scores=True)

    print(f"Logits shape: {output.logits.shape}")
    print(f"Incongruity scores shape: {output.incongruity_scores.shape}")

    print("GCACU Network test passed!")
