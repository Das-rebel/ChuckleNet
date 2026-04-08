"""
SEVADE: decoupled evaluator for architecture consensus and calibration.
"""

from __future__ import annotations

from typing import Dict

import torch
from torch import Tensor, nn


def _binary_entropy(probabilities: Tensor) -> Tensor:
    clipped = probabilities.clamp(1e-5, 1.0 - 1e-5)
    return -(clipped * clipped.log() + (1.0 - clipped) * (1.0 - clipped).log())


class _AgentHead(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, 1),
        )

    def forward(self, features: Tensor) -> Tensor:
        return self.network(features)


class SEVADEEvaluator(nn.Module):
    """
    Fuse residual streams and architecture votes into a calibrated logit.

    The evaluator keeps three decoupled heads so disagreement can be surfaced to
    tests and the autonomous loop.
    """

    def __init__(self, stream_dim: int, num_architectures: int, hidden_dim: int = 128):
        super().__init__()
        feature_dim = stream_dim + num_architectures + 2
        self.skeptic = _AgentHead(feature_dim, hidden_dim)
        self.verifier = _AgentHead(feature_dim, hidden_dim)
        self.calibrator = _AgentHead(feature_dim, hidden_dim)
        self.consensus = nn.Sequential(
            nn.Linear(feature_dim + 3, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1),
        )

    def forward(self, residual_streams: Tensor, architecture_scores: Tensor) -> Dict[str, Tensor]:
        if residual_streams.ndim != 3:
            raise ValueError("Expected residual_streams with shape (batch, streams, dim).")
        if architecture_scores.ndim != 2:
            raise ValueError("Expected architecture_scores with shape (batch, streams).")

        pooled = residual_streams.mean(dim=1)
        disagreement = architecture_scores.std(dim=1, keepdim=True, unbiased=False)
        entropy = _binary_entropy(architecture_scores).mean(dim=1, keepdim=True)
        features = torch.cat([pooled, architecture_scores, disagreement, entropy], dim=-1)

        skeptic_logit = self.skeptic(features)
        verifier_logit = self.verifier(features)
        calibrator_logit = self.calibrator(features)
        agent_logits = torch.cat([skeptic_logit, verifier_logit, calibrator_logit], dim=-1)
        consensus_logit = self.consensus(torch.cat([features, agent_logits], dim=-1))

        return {
            "logits": consensus_logit,
            "probability": torch.sigmoid(consensus_logit),
            "agent_logits": agent_logits,
            "disagreement": disagreement,
            "entropy": entropy,
        }

    def summarize_batch(self, outputs: Dict[str, Tensor]) -> Dict[str, float]:
        return {
            "mean_probability": float(outputs["probability"].mean().item()),
            "mean_disagreement": float(outputs["disagreement"].mean().item()),
            "mean_entropy": float(outputs["entropy"].mean().item()),
        }

