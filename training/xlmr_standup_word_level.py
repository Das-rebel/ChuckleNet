#!/usr/bin/env python3
"""
XLM-R-base baseline for stand-up comedy word-level laughter prediction.

This module is intentionally standalone so it can be used even while the older
benchmark package remains unstable. It targets the stand-up specific setup:

- text-first
- word-level sequence labeling
- speaker/comic-independent splits
- optional language-aware reporting

Expected JSONL schema:
{
  "example_id": "set_001_seg_0001",
  "language": "en",
  "comedian_id": "comic_001",
  "show_id": "special_2024",
  "words": ["so", "i", "walked", "into", "a", "bank"],
  "labels": [0, 0, 0, 0, 0, 1]
}
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import torch
from torch import Tensor
from torch import nn
from torch.nn import functional as F
from torch.optim import AdamW
from torch.utils.data import DataLoader, Dataset
from transformers import AutoModelForTokenClassification, AutoTokenizer, get_linear_schedule_with_warmup


DEFAULT_MODEL_NAME = "FacebookAI/xlm-roberta-base"
ADAPTER_CONFIG_NAME = "dialect_adapter_config.json"
ADAPTER_STATE_NAME = "dialect_adapter_state.pt"
CONTRAST_CONFIG_NAME = "contrast_gate_config.json"
CONTRAST_STATE_NAME = "contrast_gate_state.pt"
CUE_CONFIG_NAME = "cue_adapter_config.json"
CUE_STATE_NAME = "cue_adapter_state.pt"
DIALECT_BUCKETS = ("neutral", "contraction_heavy", "colloquial")
DIALECT_BUCKET_TO_ID = {bucket: index for index, bucket in enumerate(DIALECT_BUCKETS)}
CUE_BUCKETS = ("neutral", "filler", "discourse", "punctuation")
CUE_BUCKET_TO_ID = {bucket: index for index, bucket in enumerate(CUE_BUCKETS)}
GCACU_CONFIG_NAME = "gcacu_language_config.json"
GCACU_STATE_NAME = "gcacu_language_state.pt"
LANGUAGE_DOMAIN_BUCKETS = ("english", "multilingual", "cross_lingual", "standup4ai")
LANGUAGE_DOMAIN_BUCKET_TO_ID = {bucket: index for index, bucket in enumerate(LANGUAGE_DOMAIN_BUCKETS)}


@dataclass(slots=True)
class StandupExample:
    example_id: str
    language: str
    laughter_type: str
    comedian_id: str
    show_id: str
    words: List[str]
    labels: List[int]
    current_segment_start: int = 0


@dataclass(slots=True)
class XLMRStandupConfig:
    model_name: str = DEFAULT_MODEL_NAME
    num_labels: int = 2
    max_length: int = 256
    batch_size: int = 2
    eval_batch_size: int = 2
    learning_rate: float = 2e-5
    classifier_learning_rate: float = 1e-4
    weight_decay: float = 0.01
    warmup_ratio: float = 0.1
    epochs: int = 3
    freeze_encoder_epochs: int = 1
    unfreeze_last_n_layers: int = 2
    gradient_accumulation_steps: int = 4
    loss_type: str = "cross_entropy"
    positive_class_weight: float = 1.0
    focal_gamma: float = 2.0
    decode_strategy: str = "argmax"
    single_best_min_margin: float = 0.0
    topk_span_positive_ratio: float = 0.0
    topk_span_min_tokens: int = 1
    topk_span_max_tokens: int = 0
    topk_span_neighbor_margin: float = -1.5
    topk_span_max_neighbors: int = 2
    topk_span_cue_bonus: float = 0.0
    max_grad_norm: float = 1.0
    seed: int = 42
    iou_threshold: float = 0.2
    device: Optional[str] = None
    dialect_adapter_enabled: bool = False
    dialect_adapter_dim: int = 32
    dialect_adapter_scale: float = 0.25
    contrast_gate_enabled: bool = False
    contrast_gate_dim: int = 64
    contrast_gate_scale: float = 0.25
    cue_adapter_enabled: bool = False
    cue_adapter_dim: int = 16
    cue_adapter_scale: float = 0.25
    span_aware_enabled: bool = False
    span_aware_radius: int = 2
    span_aware_decay: float = 0.5
    span_aware_loss_weight: float = 0.25
    cue_span_bias_enabled: bool = False
    cue_span_bias_strength: float = 0.75
    gcacu_language_enabled: bool = False
    gcacu_language_dim: int = 128
    gcacu_language_scale: float = 0.5
    gcacu_incongruity_window: int = 7
    gcacu_contrast_threshold: float = 0.3
    uncertainty_aware_upl: bool = False
    upl_confidence_threshold: float = 0.7
    upl_uncertainty_weight: float = 0.5
    early_stopping_patience: int = 2
    debug: bool = False


def infer_dialect_bucket(words: Sequence[str]) -> str:
    lower_words = [word.lower() for word in words]
    if not lower_words:
        return "neutral"

    contraction_count = sum("'" in word or "’" in word for word in lower_words)
    colloquial_markers = {
        "gonna",
        "wanna",
        "gotta",
        "ain't",
        "y'all",
        "lemme",
        "kinda",
        "sorta",
        "dunno",
        "nah",
        "yo",
        "bro",
        "dude",
    }
    colloquial_count = sum(word in colloquial_markers for word in lower_words)
    if colloquial_count >= 1:
        return "colloquial"
    if contraction_count >= 2:
        return "contraction_heavy"
    return "neutral"


def infer_cue_bucket(word: str) -> str:
    lowered = word.strip().lower()
    if not lowered:
        return "neutral"

    filler_markers = {
        "um",
        "uh",
        "umm",
        "uhh",
        "erm",
        "hmm",
        "ah",
        "oh",
    }
    discourse_markers = {
        "okay",
        "ok",
        "right",
        "well",
        "like",
        "mean",
        "know",
        "yeah",
        "yes",
        "no",
        "now",
        "so",
        "anyway",
        "actually",
        "literally",
    }

    alpha_numeric = lowered.strip("\"'`“”‘’.,!?;:-()[]{}")
    if alpha_numeric in filler_markers:
        return "filler"
    if alpha_numeric in discourse_markers:
        return "discourse"
    if any(mark in lowered for mark in ("...", "…", "?", "!")):
        return "punctuation"
    if not any(character.isalnum() for character in alpha_numeric):
        return "punctuation"
    return "neutral"


def infer_language_domain_bucket(language: str, dataset_source: str = "internal") -> str:
    """
    Infer language domain bucket for GCACU language adapter.

    This implements the framework's language-aware domain conditioning:
    - english: Pure English content from internal dataset
    - multilingual: Non-English content (fr, es, cs, etc.)
    - cross_lingual: Mixed language content or translated material
    - standup4ai: Content from StandUp4AI external dataset
    """
    if dataset_source == "standup4ai":
        return "standup4ai"

    if language == "en":
        return "english"
    elif language in ("fr", "es", "cs", "de", "it", "pt"):
        return "multilingual"
    else:
        return "cross_lingual"


class DialectConditionedTokenClassifier(nn.Module):
    def __init__(
        self,
        backbone: AutoModelForTokenClassification,
        adapter_dim: int,
        adapter_scale: float,
    ) -> None:
        super().__init__()
        self.backbone = backbone
        hidden_size = int(backbone.config.hidden_size)
        self.dialect_embeddings = nn.Embedding(len(DIALECT_BUCKETS), adapter_dim)
        self.dialect_adapter = nn.Sequential(
            nn.Linear(hidden_size + adapter_dim, adapter_dim),
            nn.Tanh(),
            nn.Linear(adapter_dim, hidden_size),
        )
        self.adapter_scale = float(adapter_scale)

    def forward(
        self,
        input_ids: Tensor,
        attention_mask: Tensor,
        dialect_bucket_ids: Optional[Tensor] = None,
        cue_bucket_ids: Optional[Tensor] = None,
    ) -> SimpleNamespace:
        del cue_bucket_ids
        roberta_outputs = self.backbone.roberta(
            input_ids=input_ids,
            attention_mask=attention_mask,
            return_dict=True,
        )
        sequence_output = roberta_outputs.last_hidden_state
        if dialect_bucket_ids is None:
            dialect_bucket_ids = torch.zeros(sequence_output.size(0), dtype=torch.long, device=sequence_output.device)
        bucket_embedding = self.dialect_embeddings(dialect_bucket_ids)
        bucket_embedding = bucket_embedding.unsqueeze(1).expand(-1, sequence_output.size(1), -1)
        adapter_input = torch.cat([sequence_output, bucket_embedding], dim=-1)
        adapted_output = sequence_output + (self.adapter_scale * self.dialect_adapter(adapter_input))
        logits = self.backbone.classifier(adapted_output)
        return SimpleNamespace(logits=logits)


class ContrastGatedTokenClassifier(nn.Module):
    def __init__(
        self,
        backbone: AutoModelForTokenClassification,
        gate_dim: int,
        gate_scale: float,
    ) -> None:
        super().__init__()
        self.backbone = backbone
        hidden_size = int(backbone.config.hidden_size)
        self.gate_scale = float(gate_scale)
        self.contrast_gate = nn.Sequential(
            nn.Linear(hidden_size * 3, gate_dim),
            nn.Tanh(),
            nn.Linear(gate_dim, hidden_size),
            nn.Sigmoid(),
        )
        self.contrast_projection = nn.Sequential(
            nn.Linear(hidden_size * 3, gate_dim),
            nn.Tanh(),
            nn.Linear(gate_dim, hidden_size),
        )

    def forward(
        self,
        input_ids: Tensor,
        attention_mask: Tensor,
        dialect_bucket_ids: Optional[Tensor] = None,
        cue_bucket_ids: Optional[Tensor] = None,
    ) -> SimpleNamespace:
        del dialect_bucket_ids
        del cue_bucket_ids
        roberta_outputs = self.backbone.roberta(
            input_ids=input_ids,
            attention_mask=attention_mask,
            return_dict=True,
        )
        sequence_output = roberta_outputs.last_hidden_state
        mask = attention_mask.unsqueeze(-1).to(sequence_output.dtype)
        denom = mask.sum(dim=1, keepdim=True).clamp_min(1.0)
        context_summary = (sequence_output * mask).sum(dim=1, keepdim=True) / denom
        context_summary = context_summary.expand(-1, sequence_output.size(1), -1)
        contrast_features = torch.abs(sequence_output - context_summary)
        gate_input = torch.cat([sequence_output, context_summary, contrast_features], dim=-1)
        gate = self.contrast_gate(gate_input)
        projected = self.contrast_projection(gate_input)
        gated_output = sequence_output + (self.gate_scale * gate * projected)
        logits = self.backbone.classifier(gated_output)
        return SimpleNamespace(logits=logits)


class CueConditionedTokenClassifier(nn.Module):
    def __init__(
        self,
        backbone: AutoModelForTokenClassification,
        cue_dim: int,
        cue_scale: float,
    ) -> None:
        super().__init__()
        self.backbone = backbone
        hidden_size = int(backbone.config.hidden_size)
        self.cue_embeddings = nn.Embedding(len(CUE_BUCKETS), cue_dim)
        self.cue_adapter = nn.Sequential(
            nn.Linear(hidden_size + cue_dim, cue_dim),
            nn.Tanh(),
            nn.Linear(cue_dim, hidden_size),
        )
        self.cue_scale = float(cue_scale)

    def forward(
        self,
        input_ids: Tensor,
        attention_mask: Tensor,
        dialect_bucket_ids: Optional[Tensor] = None,
        cue_bucket_ids: Optional[Tensor] = None,
    ) -> SimpleNamespace:
        del dialect_bucket_ids
        roberta_outputs = self.backbone.roberta(
            input_ids=input_ids,
            attention_mask=attention_mask,
            return_dict=True,
        )
        sequence_output = roberta_outputs.last_hidden_state
        if cue_bucket_ids is None:
            cue_bucket_ids = torch.zeros_like(input_ids, dtype=torch.long, device=sequence_output.device)
        cue_embedding = self.cue_embeddings(cue_bucket_ids)
        adapter_input = torch.cat([sequence_output, cue_embedding], dim=-1)
        adapted_output = sequence_output + (self.cue_scale * self.cue_adapter(adapter_input))
        logits = self.backbone.classifier(adapted_output)
        return SimpleNamespace(logits=logits)


class GCACULanguageAwareAdapter(nn.Module):
    """
    Gated Contrast-Attention Contextualized-Understanding (GCACU) Language Adapter

    This implements the framework's cognitive reasoning architecture for humor detection:
    - Language-aware domain conditioning for better cross-lingual transfer
    - Incongruity modeling via contrastive attention windows
    - Domain-specific adaptation for StandUp4AI vs internal data
    """

    def __init__(
        self,
        backbone: AutoModelForTokenClassification,
        language_dim: int,
        language_scale: float,
        incongruity_window: int = 7,
        contrast_threshold: float = 0.3,
    ) -> None:
        super().__init__()
        self.backbone = backbone
        hidden_size = int(backbone.config.hidden_size)

        # Language domain embeddings
        self.language_embeddings = nn.Embedding(len(LANGUAGE_DOMAIN_BUCKETS), language_dim)

        # GCACU: Incongruity modeling with contrastive attention
        self.incongruity_window = incongruity_window
        self.contrast_threshold = contrast_threshold

        # Gated contrast-attention pathway
        self.contrast_gate = nn.Sequential(
            nn.Linear(hidden_size * 2, language_dim),
            nn.Tanh(),
            nn.Linear(language_dim, hidden_size),
            nn.Sigmoid(),
        )

        # Language-specific adapter with residual connection
        self.language_adapter = nn.Sequential(
            nn.Linear(hidden_size + language_dim, language_dim),
            nn.Tanh(),
            nn.Linear(language_dim, hidden_size),
        )

        self.language_scale = float(language_scale)

        # Domain-specific projection for StandUp4AI vs internal
        self.domain_projection = nn.Sequential(
            nn.Linear(hidden_size, language_dim // 2),
            nn.Tanh(),
            nn.Linear(language_dim // 2, hidden_size),
        )

    def forward(
        self,
        input_ids: Tensor,
        attention_mask: Tensor,
        dialect_bucket_ids: Optional[Tensor] = None,
        cue_bucket_ids: Optional[Tensor] = None,
        language_domain_ids: Optional[Tensor] = None,
    ) -> SimpleNamespace:
        del dialect_bucket_ids
        del cue_bucket_ids

        roberta_outputs = self.backbone.roberta(
            input_ids=input_ids,
            attention_mask=attention_mask,
            return_dict=True,
        )
        sequence_output = roberta_outputs.last_hidden_state

        # Default to English if no language domain provided
        if language_domain_ids is None:
            language_domain_ids = torch.zeros(sequence_output.size(0), dtype=torch.long,
                                            device=sequence_output.device)

        # Language domain embedding
        language_embedding = self.language_embeddings(language_domain_ids)
        language_embedding = language_embedding.unsqueeze(1).expand(-1, sequence_output.size(1), -1)

        # GCACU: Incongruity modeling via contrastive attention
        # Compute local context windows for detecting setup-punchline incongruity
        window_size = min(self.incongruity_window, sequence_output.size(1) // 2)
        if window_size > 1:
            # Create sliding window attention for incongruity detection
            # F.pad padding format: (left, right, top, bottom, front, back) for 3D tensor
            padding = (0, 0, window_size, window_size)  # Pad sequence dimension only
            padded_output = F.pad(sequence_output, padding, mode='constant', value=0)

            # Extract local context windows
            context_windows = []
            for i in range(window_size * 2 + 1):
                shifted = padded_output[:, i:i + sequence_output.size(1), :]
                context_windows.append(shifted)

            # Stack windows for parallel processing
            stacked_context = torch.stack(context_windows, dim=-1)  # [batch, seq_len, hidden, window_size]

            # Compute incongruity as variance across windows
            context_mean = stacked_context.mean(dim=-1, keepdim=True)
            context_var = ((stacked_context - context_mean) ** 2).mean(dim=-1)

            # Contrast gate based on incongruity
            contrast_features = torch.cat([sequence_output, context_var], dim=-1)
            gate = self.contrast_gate(contrast_features)

            # Apply gated adaptation
            domain_projected = self.domain_projection(sequence_output)
            adapted_output = sequence_output + (self.language_scale * gate * domain_projected)
        else:
            # Fallback to simple language adapter without incongruity modeling
            adapter_input = torch.cat([sequence_output, language_embedding], dim=-1)
            adapted_output = sequence_output + (self.language_scale * self.language_adapter(adapter_input))

        logits = self.backbone.classifier(adapted_output)
        return SimpleNamespace(logits=logits, gate=gate if window_size > 1 else None)


def set_seed(seed: int) -> None:
    random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def choose_device(explicit: Optional[str] = None) -> torch.device:
    if explicit:
        return torch.device(explicit)
    if torch.backends.mps.is_available():
        return torch.device("mps")
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def is_contrast_gate_model(model: nn.Module) -> bool:
    return isinstance(model, ContrastGatedTokenClassifier)


def is_cue_adapter_model(model: nn.Module) -> bool:
    return isinstance(model, CueConditionedTokenClassifier)


def is_dialect_adapter_model(model: nn.Module) -> bool:
    return isinstance(model, DialectConditionedTokenClassifier)


def is_gcacu_language_model(model: nn.Module) -> bool:
    return isinstance(model, GCACULanguageAwareAdapter)


def is_custom_head_model(model: nn.Module) -> bool:
    return (is_dialect_adapter_model(model) or is_contrast_gate_model(model) or
            is_cue_adapter_model(model) or is_gcacu_language_model(model))


def forward_model(
    model: nn.Module,
    input_ids: Tensor,
    attention_mask: Tensor,
    dialect_bucket_ids: Optional[Tensor] = None,
    cue_bucket_ids: Optional[Tensor] = None,
) -> Any:
    if is_custom_head_model(model):
        return model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            dialect_bucket_ids=dialect_bucket_ids,
            cue_bucket_ids=cue_bucket_ids,
        )
    return model(
        input_ids=input_ids,
        attention_mask=attention_mask,
    )


def load_base_token_classifier(
    model_name_or_path: str | Path,
    num_labels: int,
    local_files_only: bool,
) -> AutoModelForTokenClassification:
    return AutoModelForTokenClassification.from_pretrained(
        model_name_or_path,
        num_labels=num_labels,
        id2label={0: "NO_LAUGHTER", 1: "LAUGHTER"},
        label2id={"NO_LAUGHTER": 0, "LAUGHTER": 1},
        local_files_only=local_files_only,
    )


def create_model(
    config: XLMRStandupConfig,
    local_files_only: bool,
) -> nn.Module:
    backbone = load_base_token_classifier(
        config.model_name,
        num_labels=config.num_labels,
        local_files_only=local_files_only,
    )
    if config.contrast_gate_enabled:
        return ContrastGatedTokenClassifier(
            backbone=backbone,
            gate_dim=config.contrast_gate_dim,
            gate_scale=config.contrast_gate_scale,
        )
    if config.cue_adapter_enabled:
        return CueConditionedTokenClassifier(
            backbone=backbone,
            cue_dim=config.cue_adapter_dim,
            cue_scale=config.cue_adapter_scale,
        )
    if config.dialect_adapter_enabled:
        return DialectConditionedTokenClassifier(
            backbone=backbone,
            adapter_dim=config.dialect_adapter_dim,
            adapter_scale=config.dialect_adapter_scale,
        )
    return backbone


def save_model(model: nn.Module, tokenizer: Any, output_dir: Path, config: XLMRStandupConfig) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    if is_contrast_gate_model(model):
        model.backbone.save_pretrained(output_dir)
        contrast_payload = {
            "contrast_gate_enabled": True,
            "contrast_gate_dim": config.contrast_gate_dim,
            "contrast_gate_scale": config.contrast_gate_scale,
        }
        (output_dir / CONTRAST_CONFIG_NAME).write_text(json.dumps(contrast_payload, indent=2), encoding="utf-8")
        torch.save(
            {
                "contrast_gate": model.contrast_gate.state_dict(),
                "contrast_projection": model.contrast_projection.state_dict(),
            },
            output_dir / CONTRAST_STATE_NAME,
        )
    elif is_cue_adapter_model(model):
        model.backbone.save_pretrained(output_dir)
        cue_payload = {
            "cue_adapter_enabled": True,
            "cue_adapter_dim": config.cue_adapter_dim,
            "cue_adapter_scale": config.cue_adapter_scale,
            "cue_buckets": list(CUE_BUCKETS),
        }
        (output_dir / CUE_CONFIG_NAME).write_text(json.dumps(cue_payload, indent=2), encoding="utf-8")
        torch.save(
            {
                "cue_embeddings": model.cue_embeddings.state_dict(),
                "cue_adapter": model.cue_adapter.state_dict(),
            },
            output_dir / CUE_STATE_NAME,
        )
    elif is_dialect_adapter_model(model):
        model.backbone.save_pretrained(output_dir)
        adapter_payload = {
            "dialect_adapter_enabled": True,
            "dialect_adapter_dim": config.dialect_adapter_dim,
            "dialect_adapter_scale": config.dialect_adapter_scale,
            "dialect_buckets": list(DIALECT_BUCKETS),
        }
        (output_dir / ADAPTER_CONFIG_NAME).write_text(json.dumps(adapter_payload, indent=2), encoding="utf-8")
        torch.save(
            {
                "dialect_embeddings": model.dialect_embeddings.state_dict(),
                "dialect_adapter": model.dialect_adapter.state_dict(),
            },
            output_dir / ADAPTER_STATE_NAME,
        )
    else:
        model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)


def load_saved_model(
    model_dir: Path,
    device: torch.device,
    fallback_config: Optional[XLMRStandupConfig] = None,
) -> nn.Module:
    contrast_config_path = model_dir / CONTRAST_CONFIG_NAME
    cue_config_path = model_dir / CUE_CONFIG_NAME
    adapter_config_path = model_dir / ADAPTER_CONFIG_NAME
    local_files_only = True
    if contrast_config_path.exists():
        contrast_payload = json.loads(contrast_config_path.read_text(encoding="utf-8"))
        backbone = load_base_token_classifier(model_dir, num_labels=2, local_files_only=local_files_only)
        model = ContrastGatedTokenClassifier(
            backbone=backbone,
            gate_dim=int(contrast_payload.get("contrast_gate_dim", 64)),
            gate_scale=float(contrast_payload.get("contrast_gate_scale", 0.25)),
        )
        state_payload = torch.load(model_dir / CONTRAST_STATE_NAME, map_location=device)
        model.contrast_gate.load_state_dict(state_payload["contrast_gate"])
        model.contrast_projection.load_state_dict(state_payload["contrast_projection"])
    elif cue_config_path.exists():
        cue_payload = json.loads(cue_config_path.read_text(encoding="utf-8"))
        backbone = load_base_token_classifier(model_dir, num_labels=2, local_files_only=local_files_only)
        model = CueConditionedTokenClassifier(
            backbone=backbone,
            cue_dim=int(cue_payload.get("cue_adapter_dim", 16)),
            cue_scale=float(cue_payload.get("cue_adapter_scale", 0.25)),
        )
        state_payload = torch.load(model_dir / CUE_STATE_NAME, map_location=device)
        model.cue_embeddings.load_state_dict(state_payload["cue_embeddings"])
        model.cue_adapter.load_state_dict(state_payload["cue_adapter"])
    elif adapter_config_path.exists():
        adapter_payload = json.loads(adapter_config_path.read_text(encoding="utf-8"))
        backbone = load_base_token_classifier(model_dir, num_labels=2, local_files_only=local_files_only)
        model = DialectConditionedTokenClassifier(
            backbone=backbone,
            adapter_dim=int(adapter_payload.get("dialect_adapter_dim", 32)),
            adapter_scale=float(adapter_payload.get("dialect_adapter_scale", 0.25)),
        )
        state_payload = torch.load(model_dir / ADAPTER_STATE_NAME, map_location=device)
        model.dialect_embeddings.load_state_dict(state_payload["dialect_embeddings"])
        model.dialect_adapter.load_state_dict(state_payload["dialect_adapter"])
    else:
        num_labels = fallback_config.num_labels if fallback_config is not None else 2
        model = load_base_token_classifier(model_dir, num_labels=num_labels, local_files_only=local_files_only)
    model.to(device)
    return model


def load_jsonl_examples(path: Path) -> List[StandupExample]:
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(f"Dataset file not found: {source}")

    examples: List[StandupExample] = []
    for line_number, raw_line in enumerate(source.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw_line.strip():
            continue
        payload = json.loads(raw_line)
        words = payload.get("words")
        labels = payload.get("labels")
        if not isinstance(words, list) or not isinstance(labels, list):
            raise ValueError(f"{source}:{line_number} must contain 'words' and 'labels' lists.")
        if len(words) != len(labels):
            raise ValueError(
                f"{source}:{line_number} has mismatched word and label counts "
                f"({len(words)} != {len(labels)})."
            )
        examples.append(
            StandupExample(
                example_id=str(payload.get("example_id") or f"{source.stem}_{line_number}"),
                language=str(payload.get("language") or "en"),
                laughter_type=str((payload.get("metadata") or {}).get("laughter_type") or payload.get("laughter_type") or "unknown"),
                comedian_id=str(payload.get("comedian_id") or "unknown_comedian"),
                show_id=str(payload.get("show_id") or "unknown_show"),
                words=[str(word) for word in words],
                labels=[int(label) for label in labels],
                current_segment_start=max(0, int((payload.get("metadata") or {}).get("current_segment_start") or 0)),
            )
        )
    if not examples:
        raise ValueError(f"No examples found in {source}")
    return examples


class StandupWordLevelDataset(Dataset[Dict[str, Any]]):
    def __init__(
        self,
        examples: Sequence[StandupExample],
        tokenizer: Any,
        max_length: int,
        span_aware_radius: int = 2,
        span_aware_decay: float = 0.5,
        cue_span_bias_enabled: bool = False,
        cue_span_bias_strength: float = 0.75,
    ):
        self.examples = list(examples)
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.span_aware_radius = span_aware_radius
        self.span_aware_decay = span_aware_decay
        self.cue_span_bias_enabled = cue_span_bias_enabled
        self.cue_span_bias_strength = cue_span_bias_strength

    def __len__(self) -> int:
        return len(self.examples)

    def __getitem__(self, index: int) -> Dict[str, Any]:
        example = self.examples[index]
        dialect_bucket = infer_dialect_bucket(example.words)
        word_cue_ids = [CUE_BUCKET_TO_ID[infer_cue_bucket(word)] for word in example.words]
        encoding = self.tokenizer(
            example.words,
            is_split_into_words=True,
            truncation=True,
            max_length=self.max_length,
            return_attention_mask=True,
        )
        word_ids = encoding.word_ids()
        labels = align_word_labels(example.labels, word_ids, example.current_segment_start)
        cue_bucket_ids = align_word_cue_ids(word_cue_ids, word_ids)
        span_targets = build_span_targets(
            example.labels,
            word_ids,
            example.current_segment_start,
            radius=self.span_aware_radius,
            decay=self.span_aware_decay,
            word_cue_ids=word_cue_ids,
            cue_span_bias_enabled=self.cue_span_bias_enabled,
            cue_span_bias_strength=self.cue_span_bias_strength,
        )
        return {
            "example_id": example.example_id,
            "language": example.language,
            "laughter_type": example.laughter_type,
            "comedian_id": example.comedian_id,
            "show_id": example.show_id,
            "words": example.words,
            "dialect_bucket": dialect_bucket,
            "dialect_bucket_id": DIALECT_BUCKET_TO_ID[dialect_bucket],
            "current_segment_start": example.current_segment_start,
            "input_ids": encoding["input_ids"],
            "attention_mask": encoding["attention_mask"],
            "labels": labels,
            "cue_bucket_ids": cue_bucket_ids,
            "span_targets": span_targets,
        }


def align_word_labels(
    word_labels: Sequence[int],
    word_ids: Sequence[Optional[int]],
    current_segment_start: int,
) -> List[int]:
    aligned: List[int] = []
    previous_word_id: Optional[int] = None
    for word_id in word_ids:
        if word_id is None:
            aligned.append(-100)
        elif word_id < current_segment_start:
            aligned.append(-100)
        elif word_id != previous_word_id:
            aligned.append(int(word_labels[word_id]) if word_id < len(word_labels) else 0)
        else:
            aligned.append(-100)
        previous_word_id = word_id
    return aligned


def build_span_targets(
    word_labels: Sequence[int],
    word_ids: Sequence[Optional[int]],
    current_segment_start: int,
    radius: int,
    decay: float,
    word_cue_ids: Optional[Sequence[int]] = None,
    cue_span_bias_enabled: bool = False,
    cue_span_bias_strength: float = 0.75,
) -> List[float]:
    aligned: List[float] = []
    previous_word_id: Optional[int] = None
    positive_indices = [index for index, label in enumerate(word_labels) if label == 1 and index >= current_segment_start]
    clamped_radius = max(0, int(radius))
    clamped_decay = min(max(float(decay), 0.0), 1.0)
    clamped_cue_strength = min(max(float(cue_span_bias_strength), 0.0), 1.0)
    cue_bias_ids = {
        CUE_BUCKET_TO_ID["filler"],
        CUE_BUCKET_TO_ID["discourse"],
        CUE_BUCKET_TO_ID["punctuation"],
    }

    for word_id in word_ids:
        if word_id is None:
            aligned.append(-1.0)
        elif word_id < current_segment_start:
            aligned.append(-1.0)
        elif word_id != previous_word_id:
            if word_id < len(word_labels) and int(word_labels[word_id]) == 1:
                aligned.append(1.0)
            elif positive_indices and clamped_radius > 0:
                nearest_distance = min(abs(word_id - positive_index) for positive_index in positive_indices)
                if nearest_distance <= clamped_radius:
                    target = clamped_decay ** nearest_distance
                    if (
                        cue_span_bias_enabled
                        and word_cue_ids is not None
                        and word_id < len(word_cue_ids)
                        and int(word_cue_ids[word_id]) in cue_bias_ids
                    ):
                        target = min(1.0, target + (clamped_cue_strength * (clamped_decay ** nearest_distance)))
                    aligned.append(target)
                else:
                    aligned.append(0.0)
            else:
                aligned.append(0.0)
        else:
            aligned.append(-1.0)
        previous_word_id = word_id
    return aligned


def align_word_cue_ids(
    word_cue_ids: Sequence[int],
    word_ids: Sequence[Optional[int]],
) -> List[int]:
    aligned: List[int] = []
    for word_id in word_ids:
        if word_id is None or word_id >= len(word_cue_ids):
            aligned.append(CUE_BUCKET_TO_ID["neutral"])
        else:
            aligned.append(int(word_cue_ids[word_id]))
    return aligned


def collate_batch(batch: Sequence[Dict[str, Any]], pad_token_id: int) -> Dict[str, Any]:
    max_len = max(len(item["input_ids"]) for item in batch)
    input_ids: List[List[int]] = []
    attention_mask: List[List[int]] = []
    labels: List[List[int]] = []
    cue_bucket_ids: List[List[int]] = []
    span_targets: List[List[float]] = []

    for item in batch:
        pad_len = max_len - len(item["input_ids"])
        input_ids.append(item["input_ids"] + [pad_token_id] * pad_len)
        attention_mask.append(item["attention_mask"] + [0] * pad_len)
        labels.append(item["labels"] + [-100] * pad_len)
        cue_bucket_ids.append(item["cue_bucket_ids"] + [CUE_BUCKET_TO_ID["neutral"]] * pad_len)
        span_targets.append(item["span_targets"] + [-1.0] * pad_len)

    return {
        "example_id": [item["example_id"] for item in batch],
        "language": [item["language"] for item in batch],
        "laughter_type": [item["laughter_type"] for item in batch],
        "comedian_id": [item["comedian_id"] for item in batch],
        "show_id": [item["show_id"] for item in batch],
        "words": [item["words"] for item in batch],
        "dialect_bucket": [item["dialect_bucket"] for item in batch],
        "current_segment_start": [item["current_segment_start"] for item in batch],
        "input_ids": torch.tensor(input_ids, dtype=torch.long),
        "attention_mask": torch.tensor(attention_mask, dtype=torch.long),
        "dialect_bucket_ids": torch.tensor([item["dialect_bucket_id"] for item in batch], dtype=torch.long),
        "cue_bucket_ids": torch.tensor(cue_bucket_ids, dtype=torch.long),
        "labels": torch.tensor(labels, dtype=torch.long),
        "span_targets": torch.tensor(span_targets, dtype=torch.float),
    }


def build_dataloader(
    examples: Sequence[StandupExample],
    tokenizer: Any,
    batch_size: int,
    max_length: int,
    shuffle: bool,
    span_aware_radius: int = 2,
    span_aware_decay: float = 0.5,
    cue_span_bias_enabled: bool = False,
    cue_span_bias_strength: float = 0.75,
) -> DataLoader:
    dataset = StandupWordLevelDataset(
        examples=examples,
        tokenizer=tokenizer,
        max_length=max_length,
        span_aware_radius=span_aware_radius,
        span_aware_decay=span_aware_decay,
        cue_span_bias_enabled=cue_span_bias_enabled,
        cue_span_bias_strength=cue_span_bias_strength,
    )
    pad_token_id = tokenizer.pad_token_id if tokenizer.pad_token_id is not None else 1
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        collate_fn=lambda batch: collate_batch(batch, pad_token_id),
    )


def freeze_encoder(model: nn.Module) -> None:
    base_model = model.backbone.roberta if is_custom_head_model(model) else model.roberta
    for param in base_model.parameters():
        param.requires_grad = False
    classifier = model.backbone.classifier if is_custom_head_model(model) else model.classifier
    for param in classifier.parameters():
        param.requires_grad = True
    if is_dialect_adapter_model(model):
        for param in model.dialect_embeddings.parameters():
            param.requires_grad = True
        for param in model.dialect_adapter.parameters():
            param.requires_grad = True
    if is_cue_adapter_model(model):
        for param in model.cue_embeddings.parameters():
            param.requires_grad = True
        for param in model.cue_adapter.parameters():
            param.requires_grad = True
    if is_contrast_gate_model(model):
        for param in model.contrast_gate.parameters():
            param.requires_grad = True
        for param in model.contrast_projection.parameters():
            param.requires_grad = True


def unfreeze_top_layers(model: nn.Module, last_n_layers: int) -> None:
    base_model = model.backbone.roberta if is_custom_head_model(model) else model.roberta
    for param in base_model.parameters():
        param.requires_grad = False
    if last_n_layers > 0:
        for layer in base_model.encoder.layer[-last_n_layers:]:
            for param in layer.parameters():
                param.requires_grad = True
    for param in base_model.embeddings.parameters():
        param.requires_grad = False
    classifier = model.backbone.classifier if is_custom_head_model(model) else model.classifier
    for param in classifier.parameters():
        param.requires_grad = True
    if is_dialect_adapter_model(model):
        for param in model.dialect_embeddings.parameters():
            param.requires_grad = True
        for param in model.dialect_adapter.parameters():
            param.requires_grad = True
    if is_cue_adapter_model(model):
        for param in model.cue_embeddings.parameters():
            param.requires_grad = True
        for param in model.cue_adapter.parameters():
            param.requires_grad = True
    if is_contrast_gate_model(model):
        for param in model.contrast_gate.parameters():
            param.requires_grad = True
        for param in model.contrast_projection.parameters():
            param.requires_grad = True


def build_optimizer(model: nn.Module, config: XLMRStandupConfig) -> AdamW:
    classifier_params = []
    encoder_params = []
    for name, param in model.named_parameters():
        if not param.requires_grad:
            continue
        if any(tag in name for tag in ("classifier", "dialect_embeddings", "dialect_adapter", "cue_embeddings", "cue_adapter", "contrast_gate", "contrast_projection")):
            classifier_params.append(param)
        else:
            encoder_params.append(param)
    parameter_groups = []
    if encoder_params:
        parameter_groups.append(
            {"params": encoder_params, "lr": config.learning_rate, "weight_decay": config.weight_decay}
        )
    if classifier_params:
        parameter_groups.append(
            {
                "params": classifier_params,
                "lr": config.classifier_learning_rate,
                "weight_decay": config.weight_decay,
            }
        )
    return AdamW(parameter_groups)


def compute_token_loss(
    logits: Tensor,
    labels: Tensor,
    positive_class_weight: float,
    loss_type: str,
    focal_gamma: float,
    span_targets: Optional[Tensor] = None,
    span_aware_loss_weight: float = 0.0,
) -> Tensor:
    flat_logits = logits.view(-1, logits.size(-1))
    flat_labels = labels.view(-1)
    valid_mask = flat_labels != -100
    if not torch.any(valid_mask):
        return flat_logits.sum() * 0.0

    flat_logits = flat_logits[valid_mask]
    flat_labels = flat_labels[valid_mask]

    weight = None
    if positive_class_weight > 1.0:
        weight = torch.tensor([1.0, positive_class_weight], device=logits.device, dtype=logits.dtype)

    if loss_type in {"focal", "adaptive_focal"}:
        ce_loss = F.cross_entropy(flat_logits, flat_labels, reduction="none", weight=weight)
        pt = torch.exp(-ce_loss)
        gamma = max(0.0, focal_gamma)
        if loss_type == "adaptive_focal":
            positive_rate = float(flat_labels.float().mean().item()) if flat_labels.numel() else 0.0
            # Increase focusing pressure when positive labels are sparse, but
            # avoid collapsing to zero on less-skewed batches.
            gamma = max(0.5, focal_gamma * (1.0 - positive_rate))
        focal_factor = (1.0 - pt).pow(gamma)
        primary_loss = (focal_factor * ce_loss).mean()
    else:
        primary_loss = F.cross_entropy(flat_logits, flat_labels, weight=weight)

    if span_targets is None or span_aware_loss_weight <= 0.0:
        return primary_loss

    flat_span_targets = span_targets.view(-1)
    span_mask = flat_span_targets >= 0.0
    if not torch.any(span_mask):
        return primary_loss

    positive_logits = (logits[..., 1] - logits[..., 0]).reshape(-1)[span_mask]
    flat_span_targets = flat_span_targets[span_mask].to(device=logits.device, dtype=logits.dtype)
    auxiliary_loss = F.binary_cross_entropy_with_logits(positive_logits, flat_span_targets)
    return primary_loss + (span_aware_loss_weight * auxiliary_loss)


def compute_upl_weighted_loss(
    logits: Tensor,
    labels: Tensor,
    positive_class_weight: float,
    loss_type: str,
    focal_gamma: float,
    confidence_threshold: float = 0.7,
    uncertainty_weight: float = 0.5,
) -> Tensor:
    """
    Uncertainty-Aware Pseudo-Labeling (UPL) loss computation.

    This implements the framework's UPL algorithm for handling noisy labels:
    - Computes model confidence using prediction probabilities
    - Down-weights uncertain/noisy examples
    - Maintains gradient flow for high-confidence examples
    """
    flat_logits = logits.view(-1, logits.size(-1))
    flat_labels = labels.view(-1)
    valid_mask = flat_labels != -100
    if not torch.any(valid_mask):
        return flat_logits.sum() * 0.0

    flat_logits = flat_logits[valid_mask]
    flat_labels = flat_labels[valid_mask]

    # Compute prediction probabilities for uncertainty estimation
    probs = F.softmax(flat_logits, dim=-1)
    max_probs = probs.max(dim=-1)[0]  # Model confidence

    # Compute uncertainty weights: high confidence -> low uncertainty weight
    uncertainty_weights = torch.where(
        max_probs >= confidence_threshold,
        torch.ones_like(max_probs),  # Certain examples: full weight
        torch.ones_like(max_probs) * uncertainty_weight,  # Uncertain examples: reduced weight
    )

    # Standard loss computation
    weight = None
    if positive_class_weight > 1.0:
        weight = torch.tensor([1.0, positive_class_weight], device=logits.device, dtype=logits.dtype)

    if loss_type in {"focal", "adaptive_focal"}:
        ce_loss = F.cross_entropy(flat_logits, flat_labels, reduction="none", weight=weight)
        pt = torch.exp(-ce_loss)
        gamma = max(0.0, focal_gamma)
        if loss_type == "adaptive_focal":
            positive_rate = float(flat_labels.float().mean().item()) if flat_labels.numel() else 0.0
            gamma = max(0.5, focal_gamma * (1.0 - positive_rate))
        focal_factor = (1.0 - pt).pow(gamma)
        base_loss = focal_factor * ce_loss
    else:
        base_loss = F.cross_entropy(flat_logits, flat_labels, reduction="none", weight=weight)

    # Apply uncertainty-aware weighting
    weighted_loss = (base_loss * uncertainty_weights).mean()
    return weighted_loss


def extract_binary_sequences(predictions: Sequence[int], labels: Sequence[int]) -> Tuple[List[int], List[int]]:
    pred_seq: List[int] = []
    label_seq: List[int] = []
    for pred, label in zip(predictions, labels):
        if label == -100:
            continue
        pred_seq.append(int(pred))
        label_seq.append(int(label))
    return pred_seq, label_seq


def compute_binary_metrics(predictions: Sequence[int], labels: Sequence[int]) -> Dict[str, float]:
    tp = sum(1 for pred, label in zip(predictions, labels) if pred == 1 and label == 1)
    fp = sum(1 for pred, label in zip(predictions, labels) if pred == 1 and label == 0)
    fn = sum(1 for pred, label in zip(predictions, labels) if pred == 0 and label == 1)
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    support = sum(1 for label in labels if label == 1)
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "support": float(support),
    }


def extract_intervals(labels: Sequence[int]) -> List[Tuple[int, int]]:
    intervals: List[Tuple[int, int]] = []
    start: Optional[int] = None
    for index, label in enumerate(labels):
        if label == 1 and start is None:
            start = index
        elif label == 0 and start is not None:
            intervals.append((start, index - 1))
            start = None
    if start is not None:
        intervals.append((start, len(labels) - 1))
    return intervals


def compute_iou(interval_a: Tuple[int, int], interval_b: Tuple[int, int]) -> float:
    start_a, end_a = interval_a
    start_b, end_b = interval_b
    intersection = max(0, min(end_a, end_b) - max(start_a, start_b) + 1)
    union = max(end_a, end_b) - min(start_a, start_b) + 1
    return intersection / union if union else 0.0


def compute_interval_f1(
    pred_intervals: Sequence[Tuple[int, int]],
    true_intervals: Sequence[Tuple[int, int]],
    threshold: float,
) -> float:
    if not pred_intervals and not true_intervals:
        return 1.0
    if not pred_intervals or not true_intervals:
        return 0.0

    matched_true: set[int] = set()
    tp = 0
    for pred_interval in pred_intervals:
        best_idx: Optional[int] = None
        best_iou = 0.0
        for index, true_interval in enumerate(true_intervals):
            if index in matched_true:
                continue
            score = compute_iou(pred_interval, true_interval)
            if score > best_iou:
                best_iou = score
                best_idx = index
        if best_idx is not None and best_iou >= threshold:
            matched_true.add(best_idx)
            tp += 1
    fp = len(pred_intervals) - tp
    fn = len(true_intervals) - tp
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    return 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0


def decode_predictions(
    logits: Tensor,
    labels: Tensor,
    strategy: str,
    single_best_min_margin: float,
    cue_bucket_ids: Optional[Tensor] = None,
    topk_span_positive_ratio: float = 0.0,
    topk_span_min_tokens: int = 1,
    topk_span_max_tokens: int = 0,
    topk_span_neighbor_margin: float = -1.5,
    topk_span_max_neighbors: int = 2,
    topk_span_cue_bonus: float = 0.0,
) -> Tensor:
    if strategy == "argmax":
        return logits.argmax(dim=-1).cpu()

    if strategy == "single_best":
        logits_cpu = logits.detach().cpu()
        labels_cpu = labels.detach().cpu()
        predictions: List[Tensor] = []
        for batch_index in range(logits_cpu.size(0)):
            valid_mask = labels_cpu[batch_index] != -100
            decoded = torch.zeros(logits_cpu.size(1), dtype=torch.long)
            if torch.any(valid_mask):
                margins = logits_cpu[batch_index, :, 1] - logits_cpu[batch_index, :, 0]
                valid_indices = torch.nonzero(valid_mask, as_tuple=False).squeeze(-1)
                best_relative_index = int(torch.argmax(margins[valid_mask]).item())
                best_index = int(valid_indices[best_relative_index].item())
                if float(margins[best_index].item()) > single_best_min_margin:
                    decoded[best_index] = 1
            predictions.append(decoded)
        return torch.stack(predictions, dim=0)

    if strategy != "topk_span":
        raise ValueError(f"Unsupported decode strategy: {strategy}")

    logits_cpu = logits.detach().cpu()
    labels_cpu = labels.detach().cpu()
    cue_bucket_ids_cpu = cue_bucket_ids.detach().cpu() if cue_bucket_ids is not None else None
    predictions: List[Tensor] = []
    for batch_index in range(logits_cpu.size(0)):
        valid_mask = labels_cpu[batch_index] != -100
        decoded = torch.zeros(logits_cpu.size(1), dtype=torch.long)
        if torch.any(valid_mask):
            margins = logits_cpu[batch_index, :, 1] - logits_cpu[batch_index, :, 0]
            adjusted_margins = margins.clone()
            if cue_bucket_ids_cpu is not None and topk_span_cue_bonus != 0.0:
                cue_mask = torch.zeros_like(valid_mask, dtype=torch.bool)
                for cue_bucket in ("filler", "discourse", "punctuation"):
                    cue_mask |= cue_bucket_ids_cpu[batch_index] == CUE_BUCKET_TO_ID[cue_bucket]
                adjusted_margins[cue_mask] = adjusted_margins[cue_mask] + float(topk_span_cue_bonus)
            valid_indices = torch.nonzero(valid_mask, as_tuple=False).squeeze(-1)
            valid_count = int(valid_indices.numel())
            seed_count = max(0, int(math.ceil(valid_count * max(0.0, topk_span_positive_ratio))))
            seed_count = max(seed_count, max(0, int(topk_span_min_tokens)))
            if topk_span_max_tokens > 0:
                seed_count = min(seed_count, int(topk_span_max_tokens))
            seed_count = min(seed_count, valid_count)
            if seed_count > 0:
                ranked_relative = torch.argsort(adjusted_margins[valid_mask], descending=True)[:seed_count]
                seed_indices = [int(valid_indices[index].item()) for index in ranked_relative.tolist()]
                for seed_index in seed_indices:
                    decoded[seed_index] = 1
                    for direction in (-1, 1):
                        for step in range(1, max(0, int(topk_span_max_neighbors)) + 1):
                            neighbor_index = seed_index + (direction * step)
                            if neighbor_index < 0 or neighbor_index >= logits_cpu.size(1):
                                break
                            if not bool(valid_mask[neighbor_index]):
                                break
                            if float(adjusted_margins[neighbor_index].item()) < float(topk_span_neighbor_margin):
                                break
                            decoded[neighbor_index] = 1
        predictions.append(decoded)
    return torch.stack(predictions, dim=0)


def evaluate_model(
    model: nn.Module,
    dataloader: DataLoader,
    device: torch.device,
    iou_threshold: float,
    positive_class_weight: float,
    loss_type: str,
    focal_gamma: float,
    decode_strategy: str,
    single_best_min_margin: float,
    topk_span_positive_ratio: float = 0.0,
    topk_span_min_tokens: int = 1,
    topk_span_max_tokens: int = 0,
    topk_span_neighbor_margin: float = -1.5,
    topk_span_max_neighbors: int = 2,
    topk_span_cue_bonus: float = 0.0,
    span_aware_loss_weight: float = 0.0,
) -> Dict[str, Any]:
    model.eval()
    losses: List[float] = []
    all_predictions: List[int] = []
    all_labels: List[int] = []
    language_buckets: Dict[str, List[Dict[str, float]]] = {}
    laughter_type_buckets: Dict[str, List[Dict[str, float]]] = {}
    dialect_buckets: Dict[str, List[Dict[str, float]]] = {}
    interval_scores: List[float] = []

    with torch.no_grad():
        for batch in dataloader:
            outputs = forward_model(
                model=model,
                input_ids=batch["input_ids"].to(device),
                attention_mask=batch["attention_mask"].to(device),
                dialect_bucket_ids=batch["dialect_bucket_ids"].to(device) if is_dialect_adapter_model(model) else None,
                cue_bucket_ids=batch["cue_bucket_ids"].to(device) if is_cue_adapter_model(model) else None,
            )
            labels_tensor = batch["labels"].to(device)
            losses.append(
                float(
                    compute_token_loss(
                        outputs.logits,
                        labels_tensor,
                        positive_class_weight,
                        loss_type,
                        focal_gamma,
                        span_targets=batch["span_targets"].to(device),
                        span_aware_loss_weight=span_aware_loss_weight,
                    ).item()
                )
            )
            predictions = decode_predictions(
                outputs.logits,
                batch["labels"],
                strategy=decode_strategy,
                single_best_min_margin=single_best_min_margin,
                cue_bucket_ids=batch["cue_bucket_ids"],
                topk_span_positive_ratio=topk_span_positive_ratio,
                topk_span_min_tokens=topk_span_min_tokens,
                topk_span_max_tokens=topk_span_max_tokens,
                topk_span_neighbor_margin=topk_span_neighbor_margin,
                topk_span_max_neighbors=topk_span_max_neighbors,
                topk_span_cue_bonus=topk_span_cue_bonus,
            )
            labels = batch["labels"]
            for index in range(predictions.size(0)):
                pred_seq, label_seq = extract_binary_sequences(
                    predictions[index].tolist(),
                    labels[index].tolist(),
                )
                metrics = compute_binary_metrics(pred_seq, label_seq)
                interval_f1 = compute_interval_f1(
                    extract_intervals(pred_seq),
                    extract_intervals(label_seq),
                    threshold=iou_threshold,
                )
                metrics["iou_f1"] = interval_f1
                language = batch["language"][index]
                laughter_type = batch["laughter_type"][index]
                dialect_bucket = batch["dialect_bucket"][index]
                language_buckets.setdefault(language, []).append(metrics)
                laughter_type_buckets.setdefault(laughter_type, []).append(metrics)
                dialect_buckets.setdefault(dialect_bucket, []).append(metrics)
                all_predictions.extend(pred_seq)
                all_labels.extend(label_seq)
                interval_scores.append(interval_f1)

    overall = compute_binary_metrics(all_predictions, all_labels)
    per_language = {
        language: {
            "precision": mean(item["precision"] for item in items),
            "recall": mean(item["recall"] for item in items),
            "f1": mean(item["f1"] for item in items),
            "iou_f1": mean(item["iou_f1"] for item in items),
            "support": sum(item["support"] for item in items),
        }
        for language, items in sorted(language_buckets.items())
    }
    per_laughter_type = {
        laughter_type: {
            "precision": mean(item["precision"] for item in items),
            "recall": mean(item["recall"] for item in items),
            "f1": mean(item["f1"] for item in items),
            "iou_f1": mean(item["iou_f1"] for item in items),
            "support": sum(item["support"] for item in items),
        }
        for laughter_type, items in sorted(laughter_type_buckets.items())
    }
    per_dialect_bucket = {
        bucket: {
            "precision": mean(item["precision"] for item in items),
            "recall": mean(item["recall"] for item in items),
            "f1": mean(item["f1"] for item in items),
            "iou_f1": mean(item["iou_f1"] for item in items),
            "support": sum(item["support"] for item in items),
        }
        for bucket, items in sorted(dialect_buckets.items())
    }
    return {
        "loss": mean(losses),
        "precision": overall["precision"],
        "recall": overall["recall"],
        "f1": overall["f1"],
        "iou_f1": mean(interval_scores),
        "support": overall["support"],
        "decode_strategy": decode_strategy,
        "single_best_min_margin": single_best_min_margin,
        "topk_span_positive_ratio": topk_span_positive_ratio,
        "topk_span_min_tokens": topk_span_min_tokens,
        "topk_span_max_tokens": topk_span_max_tokens,
        "topk_span_neighbor_margin": topk_span_neighbor_margin,
        "topk_span_max_neighbors": topk_span_max_neighbors,
        "topk_span_cue_bonus": topk_span_cue_bonus,
        "per_language": per_language,
        "per_laughter_type": per_laughter_type,
        "per_dialect_bucket": per_dialect_bucket,
    }


def mean(values: Iterable[float]) -> float:
    sequence = list(values)
    return sum(sequence) / len(sequence) if sequence else 0.0


def prune_checkpoint_weights(model_dir: Path) -> List[str]:
    removed: List[str] = []
    for filename in ("model.safetensors", "pytorch_model.bin"):
        path = model_dir / filename
        if path.exists():
            path.unlink()
            removed.append(filename)
    return removed


def train(
    train_examples: Sequence[StandupExample],
    valid_examples: Sequence[StandupExample],
    test_examples: Optional[Sequence[StandupExample]],
    output_dir: Path,
    config: XLMRStandupConfig,
    prune_best_model_weights: bool = False,
) -> Dict[str, Any]:
    set_seed(config.seed)
    device = choose_device(config.device)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Prefer cached model artifacts so weekly runs do not depend on network access.
    local_files_only = os.environ.get("XLMR_LOCAL_FILES_ONLY", "1") != "0"
    tokenizer = AutoTokenizer.from_pretrained(
        config.model_name,
        use_fast=True,
        local_files_only=local_files_only,
    )
    model = create_model(config=config, local_files_only=local_files_only)
    model.to(device)

    train_loader = build_dataloader(
        train_examples,
        tokenizer=tokenizer,
        batch_size=config.batch_size,
        max_length=config.max_length,
        shuffle=True,
        span_aware_radius=config.span_aware_radius,
        span_aware_decay=config.span_aware_decay,
        cue_span_bias_enabled=config.cue_span_bias_enabled,
        cue_span_bias_strength=config.cue_span_bias_strength,
    )
    valid_loader = build_dataloader(
        valid_examples,
        tokenizer=tokenizer,
        batch_size=config.eval_batch_size,
        max_length=config.max_length,
        shuffle=False,
        span_aware_radius=config.span_aware_radius,
        span_aware_decay=config.span_aware_decay,
        cue_span_bias_enabled=config.cue_span_bias_enabled,
        cue_span_bias_strength=config.cue_span_bias_strength,
    )
    test_loader = None
    if test_examples:
        test_loader = build_dataloader(
            test_examples,
            tokenizer=tokenizer,
            batch_size=config.eval_batch_size,
            max_length=config.max_length,
            shuffle=False,
            span_aware_radius=config.span_aware_radius,
            span_aware_decay=config.span_aware_decay,
            cue_span_bias_enabled=config.cue_span_bias_enabled,
            cue_span_bias_strength=config.cue_span_bias_strength,
        )

    total_optimizer_steps = max(
        1,
        math.ceil((len(train_loader) * max(1, config.epochs)) / max(1, config.gradient_accumulation_steps)),
    )

    best_metrics: Dict[str, Any] = {"f1": -1.0, "iou_f1": -1.0}
    training_history: List[Dict[str, Any]] = []
    best_f1: float = -1.0
    best_iou_f1: float = -1.0
    epochs_without_improvement: int = 0

    # Debug output: print sample word-label pairs from training data
    if config.debug:
        print("\n" + "=" * 60)
        print("DEBUG: Sample word-label pairs from training data")
        print("=" * 60)
        for i, example in enumerate(train_examples[:5]):
            positive_indices = [idx for idx, label in enumerate(example.labels) if label == 1]
            print(f"\nExample {i}: {example.example_id}")
            print(f"  Words ({len(example.words)}): {example.words[:20]}...")
            print(f"  Labels ({len(example.labels)}): {example.labels[:20]}...")
            print(f"  Positive indices: {positive_indices}")
            if positive_indices:
                pos = positive_indices[0]
                if pos < len(example.words):
                    print(f"  Positive word at index {pos}: '{example.words[pos]}'")

    for epoch in range(config.epochs):
        if epoch < config.freeze_encoder_epochs:
            freeze_encoder(model)
        else:
            unfreeze_top_layers(model, config.unfreeze_last_n_layers)

        optimizer = build_optimizer(model, config)
        scheduler = get_linear_schedule_with_warmup(
            optimizer,
            num_warmup_steps=max(1, int(total_optimizer_steps * config.warmup_ratio)),
            num_training_steps=total_optimizer_steps,
        )

        model.train()
        epoch_loss = 0.0
        optimizer.zero_grad()

        for step, batch in enumerate(train_loader, start=1):
            outputs = forward_model(
                model=model,
                input_ids=batch["input_ids"].to(device),
                attention_mask=batch["attention_mask"].to(device),
                dialect_bucket_ids=batch["dialect_bucket_ids"].to(device) if is_dialect_adapter_model(model) else None,
                cue_bucket_ids=batch["cue_bucket_ids"].to(device) if is_cue_adapter_model(model) else None,
            )

            # Debug: print prediction distribution on first batch (epoch 0, step 1)
            if config.debug and epoch == 0 and step == 1:
                print("\n" + "=" * 60)
                print("DEBUG: Prediction distribution on first batch (before training)")
                print("=" * 60)
                logits = outputs.logits.detach().cpu()
                labels = batch["labels"]

                # Per-class prediction counts
                predictions = logits.argmax(dim=-1)
                for batch_idx in range(min(predictions.size(0), 3)):
                    valid_mask = labels[batch_idx] != -100
                    valid_preds = predictions[batch_idx][valid_mask]
                    valid_labels = labels[batch_idx][valid_mask]

                    pos_preds = (valid_preds == 1).sum().item()
                    neg_preds = (valid_preds == 0).sum().item()
                    pos_labels = (valid_labels == 1).sum().item()
                    neg_labels = (valid_labels == 0).sum().item()

                    print(f"\nBatch {batch_idx}:")
                    print(f"  Predictions: {len(valid_preds)} valid tokens")
                    print(f"    Predicted positive (1): {pos_preds}")
                    print(f"    Predicted negative (0): {neg_preds}")
                    print(f"  Labels: {len(valid_labels)} valid tokens")
                    print(f"    Actual positive (1): {pos_labels}")
                    print(f"    Actual negative (0): {neg_labels}")

                    # Show first 10 word/pred/label pairs
                    print(f"  First 10 word/pred/label pairs:")
                    word_ids = None
                    if hasattr(tokenizer, 'decode'):
                        for tok_idx in range(min(10, len(valid_preds))):
                            tok_id = batch["input_ids"][batch_idx][tok_idx].item()
                            word = tokenizer.decode([tok_id])
                            pred = valid_preds[tok_idx].item()
                            label = valid_labels[tok_idx].item()
                            marker = " ***" if label == 1 else ""
                            print(f"    {tok_idx}: pred={pred} label={label} word={word!r}{marker}")

            loss = compute_token_loss(
                outputs.logits,
                batch["labels"].to(device),
                config.positive_class_weight,
                config.loss_type,
                config.focal_gamma,
                span_targets=batch["span_targets"].to(device),
                span_aware_loss_weight=config.span_aware_loss_weight if config.span_aware_enabled else 0.0,
            )
            scaled_loss = loss / max(1, config.gradient_accumulation_steps)
            scaled_loss.backward()
            epoch_loss += float(loss.item())

            if step % config.gradient_accumulation_steps == 0 or step == len(train_loader):
                torch.nn.utils.clip_grad_norm_(model.parameters(), config.max_grad_norm)
                optimizer.step()
                scheduler.step()
                optimizer.zero_grad()

        metrics = evaluate_model(
            model=model,
            dataloader=valid_loader,
            device=device,
            iou_threshold=config.iou_threshold,
            positive_class_weight=config.positive_class_weight,
            loss_type=config.loss_type,
            focal_gamma=config.focal_gamma,
            decode_strategy=config.decode_strategy,
            single_best_min_margin=config.single_best_min_margin,
            topk_span_positive_ratio=config.topk_span_positive_ratio,
            topk_span_min_tokens=config.topk_span_min_tokens,
            topk_span_max_tokens=config.topk_span_max_tokens,
            topk_span_neighbor_margin=config.topk_span_neighbor_margin,
            topk_span_max_neighbors=config.topk_span_max_neighbors,
            topk_span_cue_bonus=config.topk_span_cue_bonus,
            span_aware_loss_weight=config.span_aware_loss_weight if config.span_aware_enabled else 0.0,
        )
        metrics["epoch"] = epoch + 1
        metrics["train_loss"] = epoch_loss / max(1, len(train_loader))
        training_history.append(metrics)

        current_f1 = float(metrics["f1"])
        current_iou_f1 = float(metrics["iou_f1"])
        if current_f1 > best_f1:
            best_f1 = current_f1
            best_iou_f1 = current_iou_f1
            best_metrics = dict(metrics)
            epochs_without_improvement = 0
            save_model(model, tokenizer, output_dir / "best_model", config)
        else:
            epochs_without_improvement += 1

        if epochs_without_improvement >= config.early_stopping_patience:
            print(f"Early stopping triggered after {epoch + 1} epochs with no improvement in F1 (best F1: {best_f1:.4f}).")
            break

    test_metrics = None
    if test_loader is not None and (output_dir / "best_model").exists():
        best_model = load_saved_model(output_dir / "best_model", device=device, fallback_config=config)
        test_metrics = evaluate_model(
            model=best_model,
            dataloader=test_loader,
            device=device,
            iou_threshold=config.iou_threshold,
            positive_class_weight=config.positive_class_weight,
            loss_type=config.loss_type,
            focal_gamma=config.focal_gamma,
            decode_strategy=config.decode_strategy,
            single_best_min_margin=config.single_best_min_margin,
            topk_span_positive_ratio=config.topk_span_positive_ratio,
            topk_span_min_tokens=config.topk_span_min_tokens,
            topk_span_max_tokens=config.topk_span_max_tokens,
            topk_span_neighbor_margin=config.topk_span_neighbor_margin,
            topk_span_max_neighbors=config.topk_span_max_neighbors,
            topk_span_cue_bonus=config.topk_span_cue_bonus,
            span_aware_loss_weight=config.span_aware_loss_weight if config.span_aware_enabled else 0.0,
        )

    removed_checkpoint_files: List[str] = []
    if prune_best_model_weights and (output_dir / "best_model").exists():
        removed_checkpoint_files = prune_checkpoint_weights(output_dir / "best_model")

    summary = {
        "config": asdict(config),
        "best_validation": best_metrics,
        "test_metrics": test_metrics,
        "history": training_history,
        "checkpoint_artifacts": {
            "best_model_dir": str(output_dir / "best_model"),
            "weights_pruned": prune_best_model_weights,
            "removed_files": removed_checkpoint_files,
            "dialect_adapter_enabled": config.dialect_adapter_enabled,
            "cue_adapter_enabled": config.cue_adapter_enabled,
            "cue_span_bias_enabled": config.cue_span_bias_enabled,
        },
        "early_stopping": {
            "patience": config.early_stopping_patience,
            "best_f1": best_f1,
            "best_iou_f1": best_iou_f1,
            "epochs_without_improvement": epochs_without_improvement,
        },
    }
    (output_dir / "training_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train XLM-R-base on stand-up word-level laughter labels.")
    parser.add_argument("--train-file", type=Path, required=True, help="JSONL training file.")
    parser.add_argument("--valid-file", type=Path, required=True, help="JSONL validation file.")
    parser.add_argument("--test-file", type=Path, default=None, help="Optional JSONL test file.")
    parser.add_argument("--output-dir", type=Path, required=True, help="Directory for checkpoints and metrics.")
    parser.add_argument("--model-name", default=DEFAULT_MODEL_NAME, help="HF model name.")
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--eval-batch-size", type=int, default=2)
    parser.add_argument("--max-length", type=int, default=256)
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--freeze-encoder-epochs", type=int, default=1)
    parser.add_argument("--unfreeze-last-n-layers", type=int, default=2)
    parser.add_argument("--learning-rate", type=float, default=2e-5)
    parser.add_argument("--classifier-learning-rate", type=float, default=1e-4)
    parser.add_argument("--gradient-accumulation-steps", type=int, default=4)
    parser.add_argument("--loss-type", choices=["cross_entropy", "focal", "adaptive_focal"], default="cross_entropy")
    parser.add_argument("--positive-class-weight", type=float, default=1.0)
    parser.add_argument("--focal-gamma", type=float, default=2.0)
    parser.add_argument("--decode-strategy", choices=["argmax", "single_best", "topk_span"], default="argmax")
    parser.add_argument("--single-best-min-margin", type=float, default=0.0)
    parser.add_argument("--topk-span-positive-ratio", type=float, default=0.0)
    parser.add_argument("--topk-span-min-tokens", type=int, default=1)
    parser.add_argument("--topk-span-max-tokens", type=int, default=0)
    parser.add_argument("--topk-span-neighbor-margin", type=float, default=-1.5)
    parser.add_argument("--topk-span-max-neighbors", type=int, default=2)
    parser.add_argument("--topk-span-cue-bonus", type=float, default=0.0)
    parser.add_argument("--iou-threshold", type=float, default=0.2)
    parser.add_argument("--dialect-adapter-enabled", action="store_true")
    parser.add_argument("--dialect-adapter-dim", type=int, default=32)
    parser.add_argument("--dialect-adapter-scale", type=float, default=0.25)
    parser.add_argument("--contrast-gate-enabled", action="store_true")
    parser.add_argument("--contrast-gate-dim", type=int, default=64)
    parser.add_argument("--contrast-gate-scale", type=float, default=0.25)
    parser.add_argument("--cue-adapter-enabled", action="store_true")
    parser.add_argument("--cue-adapter-dim", type=int, default=16)
    parser.add_argument("--cue-adapter-scale", type=float, default=0.25)
    parser.add_argument("--span-aware-enabled", action="store_true")
    parser.add_argument("--span-aware-radius", type=int, default=2)
    parser.add_argument("--span-aware-decay", type=float, default=0.5)
    parser.add_argument("--span-aware-loss-weight", type=float, default=0.25)
    parser.add_argument("--cue-span-bias-enabled", action="store_true")
    parser.add_argument("--cue-span-bias-strength", type=float, default=0.75)
    parser.add_argument("--early-stopping-patience", type=int, default=2, help=" epochs with no IoU-F1 improvement before early stopping.")
    parser.add_argument("--device", default=None)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--prune-best-model-weights",
        action="store_true",
        help="Delete model weight files from best_model after summary/test metrics are written.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug output: print sample word-label pairs, prediction distribution, and per-class counts.",
    )
    parser.add_argument("--gcacu-language-enabled", action="store_true")
    parser.add_argument("--gcacu-language-dim", type=int, default=128)
    parser.add_argument("--gcacu-language-scale", type=float, default=0.5)
    parser.add_argument("--gcacu-incongruity-window", type=int, default=7)
    parser.add_argument("--gcacu-contrast-threshold", type=float, default=0.3)
    parser.add_argument("--uncertainty-aware-upl", action="store_true")
    parser.add_argument("--upl-confidence-threshold", type=float, default=0.7)
    parser.add_argument("--upl-uncertainty-weight", type=float, default=0.5)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = XLMRStandupConfig(
        model_name=args.model_name,
        batch_size=args.batch_size,
        eval_batch_size=args.eval_batch_size,
        max_length=args.max_length,
        epochs=args.epochs,
        freeze_encoder_epochs=args.freeze_encoder_epochs,
        unfreeze_last_n_layers=args.unfreeze_last_n_layers,
        learning_rate=args.learning_rate,
        classifier_learning_rate=args.classifier_learning_rate,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        loss_type=args.loss_type,
        positive_class_weight=args.positive_class_weight,
        focal_gamma=args.focal_gamma,
        decode_strategy=args.decode_strategy,
        single_best_min_margin=args.single_best_min_margin,
        topk_span_positive_ratio=args.topk_span_positive_ratio,
        topk_span_min_tokens=args.topk_span_min_tokens,
        topk_span_max_tokens=args.topk_span_max_tokens,
        topk_span_neighbor_margin=args.topk_span_neighbor_margin,
        topk_span_max_neighbors=args.topk_span_max_neighbors,
        topk_span_cue_bonus=args.topk_span_cue_bonus,
        iou_threshold=args.iou_threshold,
        seed=args.seed,
        device=args.device,
        dialect_adapter_enabled=args.dialect_adapter_enabled,
        dialect_adapter_dim=args.dialect_adapter_dim,
        dialect_adapter_scale=args.dialect_adapter_scale,
        contrast_gate_enabled=args.contrast_gate_enabled,
        contrast_gate_dim=args.contrast_gate_dim,
        contrast_gate_scale=args.contrast_gate_scale,
        cue_adapter_enabled=args.cue_adapter_enabled,
        cue_adapter_dim=args.cue_adapter_dim,
        cue_adapter_scale=args.cue_adapter_scale,
        span_aware_enabled=args.span_aware_enabled,
        span_aware_radius=args.span_aware_radius,
        span_aware_decay=args.span_aware_decay,
        span_aware_loss_weight=args.span_aware_loss_weight,
        cue_span_bias_enabled=args.cue_span_bias_enabled,
        cue_span_bias_strength=args.cue_span_bias_strength,
        early_stopping_patience=args.early_stopping_patience,
        debug=args.debug,
        gcacu_language_enabled=args.gcacu_language_enabled,
        gcacu_language_dim=args.gcacu_language_dim,
        gcacu_language_scale=args.gcacu_language_scale,
        gcacu_incongruity_window=args.gcacu_incongruity_window,
        gcacu_contrast_threshold=args.gcacu_contrast_threshold,
        uncertainty_aware_upl=args.uncertainty_aware_upl,
        upl_confidence_threshold=args.upl_confidence_threshold,
        upl_uncertainty_weight=args.upl_uncertainty_weight,
    )
    train_examples = load_jsonl_examples(args.train_file)
    valid_examples = load_jsonl_examples(args.valid_file)
    test_examples = load_jsonl_examples(args.test_file) if args.test_file else None
    summary = train(
        train_examples=train_examples,
        valid_examples=valid_examples,
        test_examples=test_examples,
        output_dir=args.output_dir,
        config=config,
        prune_best_model_weights=args.prune_best_model_weights,
    )
    print(json.dumps(summary["best_validation"], indent=2))
    if summary["test_metrics"] is not None:
        print(json.dumps(summary["test_metrics"], indent=2))


if __name__ == "__main__":
    main()
