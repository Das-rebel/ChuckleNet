"""
Manifold-Constrained Hyper-Connections (mHC).

This module projects learned stream-mixing weights onto the Birkhoff polytope
with Sinkhorn-Knopp normalization, then blends them with the identity matrix to
preserve stable residual routing during training.
"""

from __future__ import annotations

import math
from typing import Dict, Optional

import torch
from torch import Tensor, nn


def sinkhorn_knopp(logits: Tensor, num_iters: int = 8, eps: float = 1e-6) -> Tensor:
    """Project unconstrained weights toward a doubly stochastic matrix."""
    if logits.ndim != 2:
        raise ValueError("Sinkhorn-Knopp expects a 2D matrix.")
    matrix = torch.exp(logits - logits.max()).clamp_min(eps)
    for _ in range(max(1, num_iters)):
        matrix = matrix / matrix.sum(dim=-1, keepdim=True).clamp_min(eps)
        matrix = matrix / matrix.sum(dim=-2, keepdim=True).clamp_min(eps)
    return matrix


def project_to_birkhoff(matrix: Tensor, num_iters: int = 8, eps: float = 1e-6) -> Tensor:
    """Normalize a non-negative matrix onto the Birkhoff polytope."""
    return sinkhorn_knopp(matrix.clamp_min(eps).log(), num_iters=num_iters, eps=eps)


class ManifoldConstrainedHyperConnections(nn.Module):
    """Memory-efficient mixing of wide residual streams from multiple architectures."""

    def __init__(
        self,
        stream_dim: int,
        num_streams: int,
        low_rank: int = 4,
        sinkhorn_iters: int = 8,
        identity_weight: float = 0.35,
        memory_budget_gb: float = 8.0,
        chunk_size: Optional[int] = None,
    ):
        super().__init__()
        self.stream_dim = stream_dim
        self.num_streams = num_streams
        self.low_rank = max(1, low_rank)
        self.sinkhorn_iters = sinkhorn_iters
        self.identity_weight = float(min(0.95, max(0.0, identity_weight)))
        self.memory_budget_gb = memory_budget_gb
        self.chunk_size = chunk_size
        self.left_factor = nn.Parameter(torch.randn(num_streams, self.low_rank) * 0.02)
        self.right_factor = nn.Parameter(torch.randn(self.low_rank, num_streams) * 0.02)
        self.register_buffer("identity", torch.eye(num_streams), persistent=False)

    def connection_logits(self) -> Tensor:
        return (self.left_factor @ self.right_factor) / math.sqrt(self.low_rank)

    def connection_matrix(self) -> Tensor:
        stochastic = sinkhorn_knopp(self.connection_logits(), num_iters=self.sinkhorn_iters)
        blended = (1.0 - self.identity_weight) * stochastic + self.identity_weight * self.identity
        return project_to_birkhoff(blended, num_iters=max(2, self.sinkhorn_iters // 2))

    def forward(self, streams: Tensor) -> Dict[str, Tensor]:
        if streams.ndim != 3:
            raise ValueError("Expected streams with shape (batch, num_streams, stream_dim).")
        if streams.size(1) != self.num_streams:
            raise ValueError(
                f"Expected {self.num_streams} residual streams, received {streams.size(1)}."
            )

        matrix = self.connection_matrix().to(device=streams.device, dtype=streams.dtype)
        chunk_size = self._resolve_chunk_size(streams)
        mixed_chunks = []
        for start in range(0, streams.size(-1), chunk_size):
            end = min(streams.size(-1), start + chunk_size)
            mixed_chunks.append(torch.einsum("ij,bjd->bid", matrix, streams[:, :, start:end]))
        mixed = torch.cat(mixed_chunks, dim=-1)
        identity_penalty = torch.mean((matrix - self.identity.to(matrix)) ** 2)
        return {
            "mixed_streams": mixed,
            "connection_matrix": matrix,
            "identity_penalty": identity_penalty.unsqueeze(0),
        }

    def _resolve_chunk_size(self, streams: Tensor) -> int:
        if self.chunk_size is not None:
            return max(1, self.chunk_size)
        bytes_per_value = max(2, streams.element_size())
        budget_bytes = self.memory_budget_gb * (1024 ** 3)
        per_feature_cost = max(1, streams.size(0) * streams.size(1) * self.num_streams * bytes_per_value)
        inferred = int(budget_bytes // max(per_feature_cost, 1))
        return max(16, min(self.stream_dim, inferred))

