"""
TurboQuant: KV-cache compression utilities for constrained training.

The implementation favors predictable behavior and bounded allocations over
maximum compression. It combines light-weight polar quantization with optional
1-bit residual correction so the rest of the framework can profile and test
compression behavior on 8GB machines.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import torch
from torch import Tensor, nn


@dataclass(slots=True)
class ResidualEncoding:
    """Compact residual representation used by ``QuantizedJL``."""

    signs: Tensor
    scale: Tensor


class PolarQuant:
    """Convert vectors into radius plus unit-direction form."""

    def __init__(self, precision: str = "float16"):
        self.precision = precision
        self.dtype = self._resolve_dtype(precision)

    def _resolve_dtype(self, precision: str) -> torch.dtype:
        mapping = {
            "float16": torch.float16,
            "bfloat16": torch.bfloat16,
            "float32": torch.float32,
        }
        return mapping.get(precision, torch.float16)

    def cartesian_to_polar(self, x: Tensor) -> Tuple[Tensor, Tensor]:
        radius = torch.norm(x, p=2, dim=-1, keepdim=True).clamp_min(1e-8)
        angle = x / radius
        return radius.to(self.dtype), angle.to(self.dtype)

    def polar_to_cartesian(self, radius: Tensor, angle: Tensor) -> Tensor:
        return radius.float() * angle.float()

    def compress(self, x: Tensor) -> Tuple[Tensor, Tensor]:
        return self.cartesian_to_polar(x)

    def decompress(self, radius: Tensor, angle: Tensor) -> Tensor:
        return self.polar_to_cartesian(radius, angle)


class QuantizedJL:
    """
    Minimal residual encoder inspired by sign-based Johnson-Lindenstrauss schemes.

    The goal here is stable low-memory residual correction, not an exact research
    reproduction.
    """

    def compress(self, residual: Tensor) -> ResidualEncoding:
        scale = residual.abs().mean(dim=-1, keepdim=True).clamp_min(1e-6)
        normalized = residual / scale
        signs = (torch.sign(normalized).clamp(min=-1, max=1) > 0).to(torch.uint8)
        return ResidualEncoding(signs=signs, scale=scale.to(torch.float16))

    def decompress(self, encoded: ResidualEncoding) -> Tensor:
        signed = encoded.signs.float() * 2.0 - 1.0
        return signed * encoded.scale.float()


class TurboQuant:
    """Main compression entrypoint used by the training pipeline."""

    def __init__(
        self,
        bits_per_channel: int = 3,
        polar_precision: str = "float16",
        enable_qjl: bool = True,
        target_compression_ratio: float = 6.0,
    ):
        self.bits_per_channel = bits_per_channel
        self.enable_qjl = enable_qjl
        self.target_compression_ratio = target_compression_ratio
        self.polar_quant = PolarQuant(polar_precision)
        self.qjl = QuantizedJL() if enable_qjl else None
        self.reset_stats()

    def compress_kv_cache(self, key_cache: Tensor, value_cache: Tensor) -> Dict[str, object]:
        original_size = self._tensor_bytes(key_cache) + self._tensor_bytes(value_cache)

        k_radius, k_angle = self.polar_quant.compress(key_cache)
        v_radius, v_angle = self.polar_quant.compress(value_cache)
        compressed: Dict[str, object] = {
            "k_radius": k_radius,
            "k_angle": k_angle,
            "v_radius": v_radius,
            "v_angle": v_angle,
        }

        if self.enable_qjl and self.qjl is not None:
            k_residual = key_cache.float() - self.polar_quant.decompress(k_radius, k_angle)
            v_residual = value_cache.float() - self.polar_quant.decompress(v_radius, v_angle)
            compressed["k_residual"] = self.qjl.compress(k_residual)
            compressed["v_residual"] = self.qjl.compress(v_residual)

        compressed_size = self._payload_bytes(compressed)
        ratio = float(original_size / max(1, compressed_size))
        self.stats = {
            "original_size": original_size,
            "compressed_size": compressed_size,
            "compression_ratio": ratio,
            "memory_saved": max(0, original_size - compressed_size),
            "target_compression_ratio": self.target_compression_ratio,
        }
        return compressed

    def decompress_kv_cache(self, compressed_data: Dict[str, object]) -> Tuple[Tensor, Tensor]:
        key_cache = self.polar_quant.decompress(
            compressed_data["k_radius"],  # type: ignore[index]
            compressed_data["k_angle"],  # type: ignore[index]
        )
        value_cache = self.polar_quant.decompress(
            compressed_data["v_radius"],  # type: ignore[index]
            compressed_data["v_angle"],  # type: ignore[index]
        )

        if self.enable_qjl and self.qjl is not None:
            k_residual = compressed_data.get("k_residual")
            v_residual = compressed_data.get("v_residual")
            if isinstance(k_residual, ResidualEncoding):
                key_cache = key_cache + self.qjl.decompress(k_residual)
            if isinstance(v_residual, ResidualEncoding):
                value_cache = value_cache + self.qjl.decompress(v_residual)

        return key_cache, value_cache

    def get_compression_stats(self) -> Dict[str, float]:
        return dict(self.stats)

    def reset_stats(self) -> None:
        self.stats = {
            "original_size": 0,
            "compressed_size": 0,
            "compression_ratio": 0.0,
            "memory_saved": 0,
            "target_compression_ratio": 0.0,
        }

    def _tensor_bytes(self, tensor: Tensor) -> int:
        return tensor.numel() * tensor.element_size()

    def _payload_bytes(self, payload: object) -> int:
        if isinstance(payload, Tensor):
            return self._tensor_bytes(payload)
        if isinstance(payload, ResidualEncoding):
            return self._tensor_bytes(payload.signs) + self._tensor_bytes(payload.scale)
        if isinstance(payload, dict):
            return sum(self._payload_bytes(value) for value in payload.values())
        return 0


class TurboQuantKVCache(nn.Module):
    """Wrapper that stores the latest compressed KV payload."""

    def __init__(
        self,
        embed_dim: int,
        num_heads: int,
        turbo_quant: Optional[TurboQuant] = None,
    ):
        super().__init__()
        self.embed_dim = embed_dim
        self.num_heads = num_heads
        self.head_dim = embed_dim // num_heads
        self.turbo_quant = turbo_quant or TurboQuant()
        self._compressed_payload: Optional[Dict[str, object]] = None

    def compress_and_store(self, key: Tensor, value: Tensor) -> None:
        self._compressed_payload = self.turbo_quant.compress_kv_cache(key, value)

    def retrieve_and_decompress(self) -> Tuple[Tensor, Tensor]:
        if self._compressed_payload is None:
            shape = (0, self.num_heads, 0, self.head_dim)
            empty = torch.empty(shape)
            return empty, empty
        return self.turbo_quant.decompress_kv_cache(self._compressed_payload)


def self_test() -> Dict[str, float]:
    """Small deterministic smoke test used by unit tests and demos."""
    generator = torch.Generator().manual_seed(11)
    key_cache = torch.randn(1, 4, 16, 8, generator=generator)
    value_cache = torch.randn(1, 4, 16, 8, generator=generator)
    compressor = TurboQuant(bits_per_channel=3, enable_qjl=True)
    compressed = compressor.compress_kv_cache(key_cache, value_cache)
    restored_key, restored_value = compressor.decompress_kv_cache(compressed)
    return {
        "compression_ratio": compressor.get_compression_stats()["compression_ratio"],
        "key_error": float((key_cache - restored_key).abs().mean().item()),
        "value_error": float((value_cache - restored_value).abs().mean().item()),
    }

