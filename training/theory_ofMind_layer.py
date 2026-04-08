"""
Production Theory of Mind layer for GCACU-based laughter prediction.

This module models comedian and audience mental states, tracks emotional
trajectories over time, estimates sarcasm and irony, and exposes a
backward-compatible interface for the legacy ToM consumers in this repo.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import time
from typing import Any, Dict, Mapping, Optional, Tuple, Union

import torch
from torch import Tensor, nn
import torch.nn.functional as F


EMOTION_LABELS: Tuple[str, ...] = (
    "joy",
    "surprise",
    "confusion",
    "amusement",
    "skepticism",
)
HUMOR_MECHANISMS: Tuple[str, ...] = (
    "incongruity",
    "relief",
    "superiority",
)


@dataclass(slots=True)
class ToMConfig:
    """Configuration for the Theory of Mind layer.

    The aliases keep older training scripts working:
    - `input_dim` mirrors `embedding_dim`
    - `attention_heads` mirrors `num_heads`
    - `num_belief_states` is retained for compatibility and validation only
    """

    embedding_dim: int = 768
    hidden_dim: int = 256
    num_heads: int = 4
    max_seq_len: int = 512
    dropout: float = 0.1
    trajectory_kernel_size: int = 3
    emotion_labels: Tuple[str, ...] = field(default_factory=lambda: EMOTION_LABELS)
    humor_mechanisms: Tuple[str, ...] = field(default_factory=lambda: HUMOR_MECHANISMS)
    enable_gcacu_fusion: bool = True
    gcacu_feature_dim: int = 768
    low_memory_mode: bool = True
    eps: float = 1e-6

    # Backward-compatible aliases.
    input_dim: Optional[int] = None
    attention_heads: Optional[int] = None
    num_belief_states: int = 4

    def __post_init__(self) -> None:
        if self.input_dim is not None:
            self.embedding_dim = int(self.input_dim)
        if self.attention_heads is not None:
            self.num_heads = int(self.attention_heads)
        self.embedding_dim = int(self.embedding_dim)
        self.hidden_dim = int(self.hidden_dim)
        self.num_heads = max(1, int(self.num_heads))
        self.max_seq_len = max(2, int(self.max_seq_len))
        self.trajectory_kernel_size = max(1, int(self.trajectory_kernel_size))
        if self.trajectory_kernel_size % 2 == 0:
            self.trajectory_kernel_size += 1
        self.dropout = float(self.dropout)
        self.gcacu_feature_dim = int(self.gcacu_feature_dim or self.embedding_dim)
        if self.embedding_dim <= 0 or self.hidden_dim <= 0:
            raise ValueError("embedding_dim and hidden_dim must be positive.")
        if len(self.emotion_labels) != 5:
            raise ValueError("Theory of Mind expects exactly five emotion labels.")
        if len(self.humor_mechanisms) != 3:
            raise ValueError("Humor mechanism classification expects exactly three classes.")

    @property
    def emotion_dim(self) -> int:
        return len(self.emotion_labels)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _resolve_config(
    config_or_embedding_dim: Optional[Union[ToMConfig, int]] = None,
    **kwargs: Any,
) -> ToMConfig:
    if isinstance(config_or_embedding_dim, ToMConfig):
        if kwargs:
            raise ValueError("Pass either a ToMConfig or keyword overrides, not both.")
        return config_or_embedding_dim
    if isinstance(config_or_embedding_dim, int):
        kwargs = dict(kwargs)
        kwargs.setdefault("embedding_dim", config_or_embedding_dim)
    return ToMConfig(**kwargs)


def _validate_embeddings(embeddings: Tensor) -> None:
    if embeddings.dim() != 3:
        raise ValueError(
            "Expected embeddings with shape (batch, seq_len, embedding_dim), "
            f"got {tuple(embeddings.shape)}."
        )


def _ensure_attention_mask(embeddings: Tensor, attention_mask: Optional[Tensor], eps: float) -> Tensor:
    batch_size, seq_len, _ = embeddings.shape
    if attention_mask is None:
        return torch.ones(batch_size, seq_len, device=embeddings.device, dtype=embeddings.dtype)
    if attention_mask.dim() != 2:
        raise ValueError(
            "Expected attention_mask with shape (batch, seq_len), "
            f"got {tuple(attention_mask.shape)}."
        )
    if attention_mask.shape != embeddings.shape[:2]:
        raise ValueError(
            "attention_mask shape must match embeddings shape[:2], "
            f"got {tuple(attention_mask.shape)} vs {tuple(embeddings.shape[:2])}."
        )
    mask = attention_mask.to(device=embeddings.device, dtype=embeddings.dtype)
    if mask.sum(dim=1).min().item() < eps:
        mask = mask.clone()
        empty_rows = mask.sum(dim=1) < eps
        mask[empty_rows, 0] = 1.0
    return mask


def _masked_mean(values: Tensor, mask: Tensor, dim: int = 1, keepdim: bool = False, eps: float = 1e-6) -> Tensor:
    weighted_mask = mask
    while weighted_mask.dim() < values.dim():
        weighted_mask = weighted_mask.unsqueeze(-1)
    numerator = (values * weighted_mask).sum(dim=dim, keepdim=keepdim)
    denominator = weighted_mask.sum(dim=dim, keepdim=keepdim).clamp_min(eps)
    return numerator / denominator


def _masked_max(values: Tensor, mask: Tensor, dim: int = 1) -> Tensor:
    weighted_mask = mask
    while weighted_mask.dim() < values.dim():
        weighted_mask = weighted_mask.unsqueeze(-1)
    masked_values = values.masked_fill(weighted_mask <= 0, float("-inf"))
    result = masked_values.max(dim=dim).values
    return torch.where(torch.isfinite(result), result, torch.zeros_like(result))


def _masked_softmax(logits: Tensor, mask: Tensor, dim: int = -1, eps: float = 1e-6) -> Tensor:
    masked_logits = logits.masked_fill(mask <= 0, float("-inf"))
    if mask.sum(dim=dim).min().item() <= eps:
        masked_logits = torch.where(mask > 0, logits, torch.full_like(logits, -1e4))
    weights = torch.softmax(masked_logits, dim=dim)
    weights = weights * mask
    return weights / weights.sum(dim=dim, keepdim=True).clamp_min(eps)


def _cosine_alignment(a: Tensor, b: Tensor, eps: float = 1e-6) -> Tensor:
    return F.cosine_similarity(a, b, dim=-1, eps=eps).unsqueeze(-1)


class MaskedPooling(nn.Module):
    """Fast masked pooling for mean, max, and boundary summaries."""

    def __init__(self, embedding_dim: int, hidden_dim: int, dropout: float, eps: float) -> None:
        super().__init__()
        self.eps = eps
        self.summary_proj = nn.Sequential(
            nn.Linear(embedding_dim * 4, hidden_dim),
            nn.SiLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, embedding_dim),
        )

    def forward(self, embeddings: Tensor, attention_mask: Tensor) -> Dict[str, Tensor]:
        mean_state = _masked_mean(embeddings, attention_mask, eps=self.eps)
        max_state = _masked_max(embeddings, attention_mask)
        first_state = embeddings[:, 0]
        lengths = attention_mask.sum(dim=1).long().clamp_min(1)
        last_state = embeddings[torch.arange(embeddings.size(0), device=embeddings.device), lengths - 1]
        pooled = torch.cat([mean_state, max_state, first_state, last_state], dim=-1)
        return {
            "mean": mean_state,
            "max": max_state,
            "first": first_state,
            "last": last_state,
            "summary": self.summary_proj(pooled),
        }


class SetupPunchlineSegmenter(nn.Module):
    """Learned soft segmentation for setup and punchline summaries."""

    def __init__(self, embedding_dim: int, max_seq_len: int, dropout: float, eps: float) -> None:
        super().__init__()
        self.max_seq_len = max_seq_len
        self.eps = eps
        self.token_gate = nn.Sequential(
            nn.Linear(embedding_dim, embedding_dim // 2),
            nn.SiLU(),
            nn.Dropout(dropout),
            nn.Linear(embedding_dim // 2, 1),
        )

    def forward(self, embeddings: Tensor, attention_mask: Tensor) -> Dict[str, Tensor]:
        batch_size, seq_len, _ = embeddings.shape
        positions = torch.linspace(
            0.0,
            1.0,
            steps=seq_len,
            device=embeddings.device,
            dtype=embeddings.dtype,
        ).unsqueeze(0).expand(batch_size, -1)
        position_bias = (positions - 0.62) * 4.0
        raw_logits = self.token_gate(embeddings).squeeze(-1) + position_bias
        punchline_weights = _masked_softmax(raw_logits, attention_mask, dim=-1, eps=self.eps)
        setup_logits = -raw_logits
        setup_weights = _masked_softmax(setup_logits, attention_mask, dim=-1, eps=self.eps)
        setup_embedding = _masked_mean(embeddings, setup_weights, eps=self.eps)
        punchline_embedding = _masked_mean(embeddings, punchline_weights, eps=self.eps)
        hard_split = torch.argmax(punchline_weights, dim=-1)
        return {
            "setup_embedding": setup_embedding,
            "punchline_embedding": punchline_embedding,
            "setup_weights": setup_weights,
            "punchline_weights": punchline_weights,
            "split_index": hard_split,
        }


class HitEmotionTrajectory(nn.Module):
    """Light-weight emotional trajectory tracker for comedian and audience states."""

    def __init__(self, config: ToMConfig) -> None:
        super().__init__()
        bottleneck_dim = max(config.hidden_dim // 2, config.emotion_dim * 4)
        self.eps = config.eps
        self.input_proj = nn.Linear(config.embedding_dim, bottleneck_dim)
        self.depthwise_conv = nn.Conv1d(
            bottleneck_dim,
            bottleneck_dim,
            kernel_size=config.trajectory_kernel_size,
            padding=config.trajectory_kernel_size // 2,
            groups=bottleneck_dim,
        )
        self.pointwise_conv = nn.Conv1d(bottleneck_dim, bottleneck_dim, kernel_size=1)
        self.norm = nn.LayerNorm(bottleneck_dim)
        self.dropout = nn.Dropout(config.dropout)
        self.emotion_head = nn.Linear(bottleneck_dim, config.emotion_dim * 2)
        self.summary_head = nn.Sequential(
            nn.Linear(bottleneck_dim + config.emotion_dim * 4 + 2, config.hidden_dim),
            nn.SiLU(),
            nn.Dropout(config.dropout),
            nn.Linear(config.hidden_dim, config.embedding_dim),
        )

    def forward(self, embeddings: Tensor, attention_mask: Tensor) -> Dict[str, Tensor]:
        projected = self.input_proj(embeddings)
        conv_input = projected.transpose(1, 2)
        conv_output = self.pointwise_conv(self.depthwise_conv(conv_input)).transpose(1, 2)
        conv_output = self.norm(conv_output + projected)
        conv_output = self.dropout(F.silu(conv_output))

        token_emotions = torch.sigmoid(self.emotion_head(conv_output))
        emotion_dim = token_emotions.size(-1) // 2
        comedian_token_emotions = token_emotions[..., :emotion_dim]
        audience_token_emotions = token_emotions[..., emotion_dim:]

        comedian_state = _masked_mean(comedian_token_emotions, attention_mask, eps=self.eps)
        audience_state = _masked_mean(audience_token_emotions, attention_mask, eps=self.eps)

        seq_len = embeddings.size(1)
        positions = torch.linspace(
            0.0,
            1.0,
            steps=seq_len,
            device=embeddings.device,
            dtype=embeddings.dtype,
        ).unsqueeze(0)
        early_mask = attention_mask * (positions <= 0.45).to(attention_mask.dtype)
        late_mask = attention_mask * (positions >= 0.55).to(attention_mask.dtype)
        early_mask = torch.where(early_mask.sum(dim=1, keepdim=True) > 0, early_mask, attention_mask)
        late_mask = torch.where(late_mask.sum(dim=1, keepdim=True) > 0, late_mask, attention_mask)

        comedian_shift = _masked_mean(comedian_token_emotions, late_mask, eps=self.eps) - _masked_mean(
            comedian_token_emotions, early_mask, eps=self.eps
        )
        audience_shift = _masked_mean(audience_token_emotions, late_mask, eps=self.eps) - _masked_mean(
            audience_token_emotions, early_mask, eps=self.eps
        )
        comedian_delta = comedian_token_emotions[:, 1:] - comedian_token_emotions[:, :-1]
        audience_delta = audience_token_emotions[:, 1:] - audience_token_emotions[:, :-1]
        transition_mask = attention_mask[:, 1:] * attention_mask[:, :-1]
        comedian_volatility = _masked_mean(comedian_delta.abs(), transition_mask, eps=self.eps)
        audience_volatility = _masked_mean(audience_delta.abs(), transition_mask, eps=self.eps)
        emotional_alignment_score = ((_cosine_alignment(comedian_state, audience_state, self.eps) + 1.0) / 2.0).clamp(0.0, 1.0)
        emotional_distance = (comedian_state - audience_state).abs().mean(dim=-1, keepdim=True)

        summary = self.summary_head(
            torch.cat(
                [
                    _masked_mean(conv_output, attention_mask, eps=self.eps),
                    comedian_state,
                    audience_state,
                    comedian_shift,
                    audience_shift,
                    emotional_alignment_score,
                    emotional_distance,
                ],
                dim=-1,
            )
        )

        return {
            "token_emotions": token_emotions,
            "comedian_token_emotions": comedian_token_emotions,
            "audience_token_emotions": audience_token_emotions,
            "comedian_state": comedian_state,
            "audience_state": audience_state,
            "comedian_shift": comedian_shift,
            "audience_shift": audience_shift,
            "comedian_volatility": comedian_volatility,
            "audience_volatility": audience_volatility,
            "emotional_alignment_score": emotional_alignment_score,
            "emotional_distance": emotional_distance,
            "summary": summary,
        }


class MentalStateReasoner(nn.Module):
    """Projects pooled context into explicit comedian and audience mental states."""

    def __init__(self, config: ToMConfig) -> None:
        super().__init__()
        input_dim = config.embedding_dim * 6 + config.emotion_dim * 4 + 2
        self.eps = config.eps
        self.shared_encoder = nn.Sequential(
            nn.Linear(input_dim, config.hidden_dim),
            nn.SiLU(),
            nn.Dropout(config.dropout),
            nn.Linear(config.hidden_dim, config.hidden_dim),
            nn.SiLU(),
        )
        self.comedian_belief_head = nn.Linear(config.hidden_dim, config.embedding_dim)
        self.comedian_intent_head = nn.Linear(config.hidden_dim, config.embedding_dim)
        self.audience_belief_head = nn.Linear(config.hidden_dim, config.embedding_dim)
        self.audience_expectation_head = nn.Linear(config.hidden_dim, config.embedding_dim)
        self.audience_intent_head = nn.Linear(config.hidden_dim, config.embedding_dim)
        self.emotion_to_embedding = nn.Linear(config.emotion_dim * 2, config.embedding_dim)
        self.state_fusion = nn.Sequential(
            nn.Linear(config.embedding_dim * 5, config.hidden_dim),
            nn.SiLU(),
            nn.Dropout(config.dropout),
            nn.Linear(config.hidden_dim, config.embedding_dim),
        )
        self.false_belief_head = nn.Sequential(
            nn.Linear(config.embedding_dim * 4 + config.emotion_dim * 2, config.hidden_dim),
            nn.SiLU(),
            nn.Dropout(config.dropout),
            nn.Linear(config.hidden_dim, 1),
        )

    def forward(
        self,
        pooled: Mapping[str, Tensor],
        segment_outputs: Mapping[str, Tensor],
        emotion_outputs: Mapping[str, Tensor],
    ) -> Dict[str, Tensor]:
        comedian_emotions = emotion_outputs["comedian_state"]
        audience_emotions = emotion_outputs["audience_state"]
        comedian_shift = emotion_outputs["comedian_shift"]
        audience_shift = emotion_outputs["audience_shift"]
        emotional_alignment_score = emotion_outputs["emotional_alignment_score"]
        emotional_distance = emotion_outputs["emotional_distance"]

        input_features = torch.cat(
            [
                pooled["summary"],
                pooled["mean"],
                segment_outputs["setup_embedding"],
                segment_outputs["punchline_embedding"],
                segment_outputs["punchline_embedding"] - segment_outputs["setup_embedding"],
                (segment_outputs["punchline_embedding"] - segment_outputs["setup_embedding"]).abs(),
                comedian_emotions,
                audience_emotions,
                comedian_shift,
                audience_shift,
                emotional_alignment_score,
                emotional_distance,
            ],
            dim=-1,
        )
        shared = self.shared_encoder(input_features)

        comedian_belief = self.comedian_belief_head(shared)
        comedian_intent = self.comedian_intent_head(shared)
        audience_belief = self.audience_belief_head(shared)
        audience_expectation = self.audience_expectation_head(shared)
        audience_intent = self.audience_intent_head(shared)
        emotion_embedding = self.emotion_to_embedding(torch.cat([comedian_emotions, audience_emotions], dim=-1))
        fused_mental_state = self.state_fusion(
            torch.cat(
                [
                    comedian_belief,
                    comedian_intent,
                    audience_belief,
                    audience_expectation,
                    emotion_embedding,
                ],
                dim=-1,
            )
        )
        false_belief_score = torch.sigmoid(
            self.false_belief_head(
                torch.cat(
                    [
                        comedian_belief,
                        comedian_intent,
                        audience_belief,
                        audience_expectation,
                        comedian_shift,
                        audience_shift,
                    ],
                    dim=-1,
                )
            )
        )

        return {
            "comedian_belief": comedian_belief,
            "comedian_intent": comedian_intent,
            "audience_belief": audience_belief,
            "audience_expectation": audience_expectation,
            "audience_intent": audience_intent,
            "fused_mental_state": fused_mental_state,
            "false_belief_score": false_belief_score,
        }


class CognitiveDynamicsHead(nn.Module):
    """Produces alignment, sarcasm, mechanism, and reaction predictions."""

    def __init__(self, config: ToMConfig) -> None:
        super().__init__()
        gcacu_input_dim = config.embedding_dim if config.enable_gcacu_fusion else 0
        feature_dim = config.embedding_dim * 7 + config.emotion_dim * 4 + 6 + gcacu_input_dim
        self.config = config
        self.feature_encoder = nn.Sequential(
            nn.Linear(feature_dim, config.hidden_dim),
            nn.SiLU(),
            nn.Dropout(config.dropout),
            nn.Linear(config.hidden_dim, config.hidden_dim),
            nn.SiLU(),
        )
        self.causal_projection = nn.Linear(config.hidden_dim, config.hidden_dim)
        self.misalignment_head = nn.Linear(config.hidden_dim, 1)
        self.correction_head = nn.Linear(config.hidden_dim, 1)
        self.alignment_head = nn.Linear(config.hidden_dim, 1)
        self.sarcasm_head = nn.Linear(config.hidden_dim, 1)
        self.reaction_head = nn.Linear(config.hidden_dim, 3)
        self.mechanism_head = nn.Linear(config.hidden_dim, len(config.humor_mechanisms))
        self.humor_head = nn.Linear(config.hidden_dim, 1)

    def forward(
        self,
        mental_states: Mapping[str, Tensor],
        segment_outputs: Mapping[str, Tensor],
        emotion_outputs: Mapping[str, Tensor],
        pooled: Mapping[str, Tensor],
        gcacu_context: Optional[Tensor] = None,
    ) -> Dict[str, Tensor]:
        comedian_belief = mental_states["comedian_belief"]
        comedian_intent = mental_states["comedian_intent"]
        audience_belief = mental_states["audience_belief"]
        audience_expectation = mental_states["audience_expectation"]
        fused_mental_state = mental_states["fused_mental_state"]

        state_divergence = (comedian_intent - audience_belief).abs()
        belief_divergence = (comedian_belief - audience_belief).abs()
        expectation_gap = (comedian_intent - audience_expectation).abs()
        setup_punchline_gap = (segment_outputs["punchline_embedding"] - segment_outputs["setup_embedding"]).abs()
        emotional_gap = (emotion_outputs["comedian_state"] - emotion_outputs["audience_state"]).abs()
        emotional_shift_gap = (emotion_outputs["audience_shift"] - emotion_outputs["comedian_shift"]).abs()

        feature_parts = [
            fused_mental_state,
            comedian_intent,
            audience_belief,
            state_divergence,
            belief_divergence,
            expectation_gap,
            setup_punchline_gap,
            emotion_outputs["comedian_state"],
            emotion_outputs["audience_state"],
            emotional_gap,
            emotional_shift_gap,
            mental_states["false_belief_score"],
            emotion_outputs["emotional_alignment_score"],
            emotion_outputs["emotional_distance"],
            _cosine_alignment(comedian_intent, audience_belief, self.config.eps),
            _cosine_alignment(comedian_belief, audience_belief, self.config.eps),
            _cosine_alignment(segment_outputs["setup_embedding"], segment_outputs["punchline_embedding"], self.config.eps),
        ]
        if self.config.enable_gcacu_fusion:
            if gcacu_context is None:
                gcacu_context = torch.zeros_like(fused_mental_state)
            feature_parts.append(gcacu_context)

        encoded = self.feature_encoder(torch.cat(feature_parts, dim=-1))
        causal_features = self.causal_projection(encoded)

        mental_state_alignment_score = torch.sigmoid(self.alignment_head(encoded))
        misalignment_score = torch.sigmoid(self.misalignment_head(causal_features))
        correction_needed = torch.sigmoid(self.correction_head(causal_features))
        sarcasm_confidence = torch.sigmoid(self.sarcasm_head(encoded))
        humor_mechanism_logits = self.mechanism_head(encoded)
        humor_mechanism_probs = torch.softmax(humor_mechanism_logits, dim=-1)
        audience_reaction_logits = self.reaction_head(encoded)
        audience_reaction_probs = torch.sigmoid(audience_reaction_logits)
        humor_logit = self.humor_head(encoded)
        humor_prediction = torch.sigmoid(humor_logit)

        return {
            "encoded_features": encoded,
            "causal_features": causal_features,
            "mental_state_alignment_score": mental_state_alignment_score,
            "misalignment_score": misalignment_score,
            "correction_needed": correction_needed,
            "sarcasm_confidence": sarcasm_confidence,
            "humor_mechanism_logits": humor_mechanism_logits,
            "humor_mechanism_probs": humor_mechanism_probs,
            "audience_reaction_logits": audience_reaction_logits,
            "audience_reaction_probs": audience_reaction_probs,
            "humor_logit": humor_logit,
            "humor_prediction": humor_prediction,
            "state_divergence": state_divergence,
            "belief_divergence": belief_divergence,
            "expectation_gap": expectation_gap,
            "setup_punchline_gap": setup_punchline_gap,
            "emotional_gap": emotional_gap,
            "emotional_shift_gap": emotional_shift_gap,
        }


class TheoryOfMindLayer(nn.Module):
    """Theory of Mind layer with GCACU-compatible outputs."""

    def __init__(self, config: Optional[Union[ToMConfig, int]] = None, **kwargs: Any) -> None:
        super().__init__()
        self.config = _resolve_config(config, **kwargs)
        self.embedding_dim = self.config.embedding_dim
        self.hidden_dim = self.config.hidden_dim
        self.num_heads = self.config.num_heads
        self.max_seq_len = self.config.max_seq_len
        self.emotion_labels = self.config.emotion_labels
        self.humor_mechanisms = self.config.humor_mechanisms

        self.pooler = MaskedPooling(
            embedding_dim=self.config.embedding_dim,
            hidden_dim=self.config.hidden_dim,
            dropout=self.config.dropout,
            eps=self.config.eps,
        )
        self.segmenter = SetupPunchlineSegmenter(
            embedding_dim=self.config.embedding_dim,
            max_seq_len=self.config.max_seq_len,
            dropout=self.config.dropout,
            eps=self.config.eps,
        )
        self.hit_emotion = HitEmotionTrajectory(self.config)
        self.mental_reasoner = MentalStateReasoner(self.config)
        self.gcacu_adapter = (
            nn.Sequential(
                nn.Linear(self.config.gcacu_feature_dim, self.config.embedding_dim),
                nn.SiLU(),
                nn.Dropout(self.config.dropout),
            )
            if self.config.enable_gcacu_fusion
            else None
        )
        self.cognitive_head = CognitiveDynamicsHead(self.config)

    def extra_memory_mb(self) -> float:
        total_params = sum(parameter.numel() for parameter in self.parameters())
        return float(total_params * 4 / (1024 ** 2))

    @torch.no_grad()
    def benchmark_inference(self, batch_size: int = 1, seq_len: int = 64, runs: int = 25, device: Optional[torch.device] = None) -> float:
        device = device or next(self.parameters()).device
        embeddings = torch.randn(batch_size, seq_len, self.embedding_dim, device=device)
        attention_mask = torch.ones(batch_size, seq_len, device=device)
        for _ in range(3):
            self.forward(embeddings, attention_mask)
        start = time.perf_counter()
        for _ in range(runs):
            self.forward(embeddings, attention_mask)
        return (time.perf_counter() - start) * 1000.0 / max(runs, 1)

    def _prepare_gcacu_context(self, gcacu_outputs: Optional[Union[Tensor, Mapping[str, Tensor]]], pooled_summary: Tensor) -> Optional[Tensor]:
        if not self.config.enable_gcacu_fusion or gcacu_outputs is None:
            return None
        if isinstance(gcacu_outputs, Tensor):
            gcacu_context = gcacu_outputs
        elif isinstance(gcacu_outputs, Mapping):
            gcacu_context = gcacu_outputs.get("contextual_understanding")
            if gcacu_context is None:
                gcacu_context = gcacu_outputs.get("conflict_features")
            if gcacu_context is None:
                gcacu_context = gcacu_outputs.get("final_output")
        else:
            raise TypeError("gcacu_outputs must be a tensor, mapping, or None.")
        if gcacu_context is None:
            return None
        if gcacu_context.dim() == 3:
            gcacu_context = gcacu_context.mean(dim=1)
        if gcacu_context.dim() != 2:
            raise ValueError("GCACU context must have shape (batch, features) or (batch, seq, features).")
        if gcacu_context.size(0) != pooled_summary.size(0):
            raise ValueError("GCACU context batch size must match embeddings batch size.")
        if self.gcacu_adapter is None:
            return gcacu_context
        return self.gcacu_adapter(gcacu_context)

    def forward(
        self,
        embeddings: Tensor,
        attention_mask: Optional[Tensor] = None,
        gcacu_outputs: Optional[Union[Tensor, Mapping[str, Tensor]]] = None,
    ) -> Dict[str, Tensor]:
        _validate_embeddings(embeddings)
        attention_mask = _ensure_attention_mask(embeddings, attention_mask, self.config.eps)

        pooled = self.pooler(embeddings, attention_mask)
        segment_outputs = self.segmenter(embeddings, attention_mask)
        emotion_outputs = self.hit_emotion(embeddings, attention_mask)
        mental_states = self.mental_reasoner(pooled, segment_outputs, emotion_outputs)
        gcacu_context = self._prepare_gcacu_context(gcacu_outputs, pooled["summary"])
        dynamics = self.cognitive_head(mental_states, segment_outputs, emotion_outputs, pooled, gcacu_context=gcacu_context)

        humor_mechanism_index = torch.argmax(dynamics["humor_mechanism_probs"], dim=-1)
        mechanism_names = [
            self.humor_mechanisms[index]
            for index in humor_mechanism_index.detach().cpu().tolist()
        ]
        emotion_name_to_index = {name: idx for idx, name in enumerate(self.emotion_labels)}
        dominant_audience_emotion = torch.argmax(emotion_outputs["audience_state"], dim=-1)
        dominant_comedian_emotion = torch.argmax(emotion_outputs["comedian_state"], dim=-1)

        emotional_trajectory = {
            "token_emotions": emotion_outputs["token_emotions"],
            "comedian_state": emotion_outputs["comedian_state"],
            "audience_state": emotion_outputs["audience_state"],
            "comedian_shift": emotion_outputs["comedian_shift"],
            "audience_shift": emotion_outputs["audience_shift"],
            "comedian_volatility": emotion_outputs["comedian_volatility"],
            "audience_volatility": emotion_outputs["audience_volatility"],
            "alignment_score": emotion_outputs["emotional_alignment_score"],
            "distance": emotion_outputs["emotional_distance"],
        }

        causal_reasoning = {
            "causal_features": dynamics["causal_features"],
            "misalignment_score": dynamics["misalignment_score"],
            "correction_needed": dynamics["correction_needed"],
            "is_humorous": dynamics["humor_prediction"] > 0.5,
            "false_belief_score": mental_states["false_belief_score"],
            "sarcasm_confidence": dynamics["sarcasm_confidence"],
            "mental_state_alignment_score": dynamics["mental_state_alignment_score"],
            "humor_mechanism_logits": dynamics["humor_mechanism_logits"],
            "humor_mechanism_probs": dynamics["humor_mechanism_probs"],
            "audience_reaction_probs": dynamics["audience_reaction_probs"],
            "state_divergence": dynamics["state_divergence"],
            "belief_divergence": dynamics["belief_divergence"],
            "expectation_gap": dynamics["expectation_gap"],
            "setup_punchline_gap": dynamics["setup_punchline_gap"],
            "emotional_gap": dynamics["emotional_gap"],
            "emotional_shift_gap": dynamics["emotional_shift_gap"],
        }

        return {
            "humor_prediction": dynamics["humor_prediction"],
            "humor_logit": dynamics["humor_logit"],
            "mental_states": mental_states,
            "causal_reasoning": causal_reasoning,
            "setup_embedding": segment_outputs["setup_embedding"],
            "punchline_embedding": segment_outputs["punchline_embedding"],
            "setup_weights": segment_outputs["setup_weights"],
            "punchline_weights": segment_outputs["punchline_weights"],
            "split_index": segment_outputs["split_index"],
            "emotional_trajectory": emotional_trajectory,
            "mental_state_alignment_score": dynamics["mental_state_alignment_score"],
            "sarcasm_confidence": dynamics["sarcasm_confidence"],
            "humor_mechanism_logits": dynamics["humor_mechanism_logits"],
            "humor_mechanism_probs": dynamics["humor_mechanism_probs"],
            "humor_mechanism_labels": mechanism_names,
            "audience_reaction_probs": dynamics["audience_reaction_probs"],
            "false_belief_score": mental_states["false_belief_score"],
            "gcacu_context": gcacu_context,
            "performance": {
                "estimated_parameter_memory_mb": self.extra_memory_mb(),
                "designed_for_low_memory": self.config.low_memory_mode,
                "emotion_labels": self.emotion_labels,
                "humor_mechanisms": self.humor_mechanisms,
                "dominant_audience_emotion_index": dominant_audience_emotion,
                "dominant_comedian_emotion_index": dominant_comedian_emotion,
                "dominant_audience_emotion": [
                    self.emotion_labels[index] for index in dominant_audience_emotion.detach().cpu().tolist()
                ],
                "dominant_comedian_emotion": [
                    self.emotion_labels[index] for index in dominant_comedian_emotion.detach().cpu().tolist()
                ],
                "emotion_name_to_index": emotion_name_to_index,
            },
        }

    def compute_loss(
        self,
        predictions: Tensor,
        targets: Tensor,
        mental_states: Optional[Mapping[str, Tensor]] = None,
        causal_reasoning: Optional[Mapping[str, Tensor]] = None,
        alpha: float = 0.7,
        beta: float = 0.3,
        gamma: float = 0.15,
        delta: float = 0.1,
        sarcasm_targets: Optional[Tensor] = None,
        emotion_targets: Optional[Tensor] = None,
        mechanism_targets: Optional[Tensor] = None,
    ) -> Tensor:
        """Compute the production loss while preserving the legacy signature."""

        if targets.dim() == 1:
            targets = targets.unsqueeze(-1)
        targets = targets.to(dtype=predictions.dtype, device=predictions.device)
        predictions = predictions.clamp(0.0, 1.0)
        main_loss = F.binary_cross_entropy(predictions, targets)

        aux_loss = torch.zeros((), device=predictions.device, dtype=predictions.dtype)
        if causal_reasoning is not None:
            misalignment = causal_reasoning.get("misalignment_score")
            if misalignment is not None:
                aux_loss = aux_loss + F.binary_cross_entropy(misalignment.clamp(0.0, 1.0), targets)
            correction_needed = causal_reasoning.get("correction_needed")
            if correction_needed is not None:
                aux_loss = aux_loss + 0.5 * F.binary_cross_entropy(correction_needed.clamp(0.0, 1.0), targets)
            sarcasm_confidence = causal_reasoning.get("sarcasm_confidence")
            if sarcasm_confidence is not None and sarcasm_targets is not None:
                sarcasm_targets = sarcasm_targets.to(dtype=predictions.dtype, device=predictions.device)
                if sarcasm_targets.dim() == 1:
                    sarcasm_targets = sarcasm_targets.unsqueeze(-1)
                aux_loss = aux_loss + gamma * F.binary_cross_entropy(
                    sarcasm_confidence.clamp(0.0, 1.0),
                    sarcasm_targets,
                )
            mechanism_logits = causal_reasoning.get("humor_mechanism_logits")
            if mechanism_logits is not None and mechanism_targets is not None:
                mechanism_targets = mechanism_targets.to(device=predictions.device, dtype=torch.long).view(-1)
                aux_loss = aux_loss + delta * F.cross_entropy(mechanism_logits, mechanism_targets)

        if mental_states is not None:
            fused_state = mental_states.get("fused_mental_state")
            comedian_intent = mental_states.get("comedian_intent")
            audience_belief = mental_states.get("audience_belief")
            false_belief_score = mental_states.get("false_belief_score")
            if fused_state is not None:
                aux_loss = aux_loss + 0.01 * fused_state.pow(2).mean()
            if comedian_intent is not None and audience_belief is not None:
                alignment = _cosine_alignment(comedian_intent, audience_belief, self.config.eps)
                aux_loss = aux_loss + 0.05 * (targets - alignment.clamp(0.0, 1.0)).abs().mean()
            if false_belief_score is not None:
                aux_loss = aux_loss + beta * F.binary_cross_entropy(false_belief_score.clamp(0.0, 1.0), targets)

        if emotion_targets is not None and causal_reasoning is not None:
            audience_reaction_probs = causal_reasoning.get("audience_reaction_probs")
            if audience_reaction_probs is not None:
                emotion_targets = emotion_targets.to(dtype=predictions.dtype, device=predictions.device)
                if emotion_targets.dim() == 1:
                    emotion_targets = emotion_targets.unsqueeze(-1)
                target_width = audience_reaction_probs.size(-1)
                if emotion_targets.size(-1) != target_width:
                    emotion_targets = emotion_targets[..., :target_width]
                    if emotion_targets.size(-1) < target_width:
                        pad_width = target_width - emotion_targets.size(-1)
                        emotion_targets = F.pad(emotion_targets, (0, pad_width))
                aux_loss = aux_loss + gamma * F.mse_loss(audience_reaction_probs, emotion_targets)

        return alpha * main_loss + beta * aux_loss


def test_theory_of_mind() -> bool:
    """Small local smoke test for the ToM layer."""

    batch_size = 2
    seq_len = 48
    embedding_dim = 128
    layer = TheoryOfMindLayer(
        embedding_dim=embedding_dim,
        hidden_dim=96,
        num_heads=4,
        max_seq_len=seq_len,
    )
    embeddings = torch.randn(batch_size, seq_len, embedding_dim)
    attention_mask = torch.ones(batch_size, seq_len)
    outputs = layer(embeddings, attention_mask)
    expected_keys = {
        "humor_prediction",
        "mental_states",
        "causal_reasoning",
        "setup_embedding",
        "punchline_embedding",
        "emotional_trajectory",
        "sarcasm_confidence",
        "humor_mechanism_probs",
    }
    if not expected_keys.issubset(outputs.keys()):
        missing = expected_keys.difference(outputs.keys())
        raise AssertionError(f"Missing expected output keys: {sorted(missing)}")
    if outputs["humor_prediction"].shape != (batch_size, 1):
        raise AssertionError(f"Unexpected humor_prediction shape: {tuple(outputs['humor_prediction'].shape)}")
    if outputs["mental_states"]["fused_mental_state"].shape != (batch_size, embedding_dim):
        raise AssertionError(
            "Unexpected fused_mental_state shape: "
            f"{tuple(outputs['mental_states']['fused_mental_state'].shape)}"
        )
    return True


__all__ = [
    "EMOTION_LABELS",
    "HUMOR_MECHANISMS",
    "ToMConfig",
    "TheoryOfMindLayer",
    "HitEmotionTrajectory",
    "test_theory_of_mind",
]


if __name__ == "__main__":
    passed = test_theory_of_mind()
    print(f"Theory of Mind smoke test passed: {passed}")
