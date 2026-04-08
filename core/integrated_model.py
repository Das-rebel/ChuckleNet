"""
Integrated laughter model and lightweight transcript preprocessing.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, MutableMapping, Optional, Sequence

import csv
import torch
from torch import Tensor, nn
from torch.utils.data import Dataset

from core.clost.clost import CLoSTLayer
from core.gcacu.gcacu import GCACUNetwork
from core.sevade.sevade import SEVADEEvaluator
from core.tom.theory_of_mind import TheoryOfMindLayer
from memory.mhc.mhc import ManifoldConstrainedHyperConnections
from memory.turboquant.turboquant import TurboQuant


def safe_logit(probabilities: Tensor, eps: float = 1e-4) -> Tensor:
    clipped = probabilities.clamp(eps, 1.0 - eps)
    return torch.log(clipped / (1.0 - clipped))


@dataclass(slots=True)
class TranscriptRecord:
    """Serializable transcript example."""

    record_id: str
    text: str
    label: float
    metadata: Dict[str, Any]


def load_transcript_records(path: Path) -> List[TranscriptRecord]:
    """Load transcript rows from JSON, JSONL, or CSV."""
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(f"Transcript data not found: {source}")

    suffix = source.suffix.lower()
    if suffix == ".jsonl":
        records = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines() if line.strip()]
    elif suffix == ".json":
        payload = json.loads(source.read_text(encoding="utf-8"))
        records = payload if isinstance(payload, list) else payload.get("records", [])
    elif suffix == ".csv":
        with source.open("r", encoding="utf-8", newline="") as handle:
            records = list(csv.DictReader(handle))
    else:
        raise ValueError(f"Unsupported data format: {source.suffix}")

    normalized: List[TranscriptRecord] = []
    for index, row in enumerate(records):
        if not isinstance(row, MutableMapping):
            raise TypeError("Each transcript row must be a mapping.")
        text = str(row.get("text") or row.get("transcript") or "").strip()
        if not text:
            continue
        raw_label = row.get("label", row.get("laughter", row.get("is_funny", 0)))
        label = float(bool(raw_label)) if isinstance(raw_label, bool) else float(raw_label)
        normalized.append(
            TranscriptRecord(
                record_id=str(row.get("id") or row.get("record_id") or index),
                text=text,
                label=1.0 if label >= 0.5 else 0.0,
                metadata={key: value for key, value in row.items() if key not in {"id", "record_id", "text", "transcript", "label", "laughter", "is_funny"}},
            )
        )
    if not normalized:
        raise ValueError(f"No valid transcript rows found in {source}")
    return normalized


class DeterministicTextEmbedder:
    """Hash-based token embedding generator with a small in-memory cache."""

    def __init__(self, embedding_dim: int):
        self.embedding_dim = embedding_dim
        self._cache: Dict[str, Tensor] = {}

    def encode(self, text: str, max_seq_len: int) -> Dict[str, Tensor]:
        tokens = [token for token in text.lower().replace("\n", " ").split() if token][:max_seq_len]
        embeddings = torch.zeros(max_seq_len, self.embedding_dim)
        attention_mask = torch.zeros(max_seq_len, dtype=torch.float32)
        for index, token in enumerate(tokens):
            embeddings[index] = self._token_embedding(token)
            attention_mask[index] = 1.0
        if not tokens:
            embeddings[0] = self._token_embedding("<empty>")
            attention_mask[0] = 1.0
        return {"embeddings": embeddings, "attention_mask": attention_mask}

    def _token_embedding(self, token: str) -> Tensor:
        cached = self._cache.get(token)
        if cached is not None:
            return cached
        digest = hashlib.sha1(token.encode("utf-8")).hexdigest()
        seed = int(digest[:16], 16) % (2 ** 31)
        generator = torch.Generator().manual_seed(seed)
        vector = torch.randn(self.embedding_dim, generator=generator)
        vector = vector / vector.norm(p=2).clamp_min(1e-6)
        self._cache[token] = vector
        return vector


class ComedyTranscriptDataset(Dataset[Dict[str, Tensor]]):
    """Dataset returning fixed-width transcript embeddings for training."""

    def __init__(
        self,
        records: Sequence[TranscriptRecord],
        embedder: DeterministicTextEmbedder,
        max_seq_len: int,
    ):
        self.records = list(records)
        self.embedder = embedder
        self.max_seq_len = max_seq_len

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, index: int) -> Dict[str, Tensor]:
        record = self.records[index]
        encoded = self.embedder.encode(record.text, self.max_seq_len)
        encoded["targets"] = torch.tensor([record.label], dtype=torch.float32)
        return encoded


class IntegratedLaughterModel(nn.Module):
    """Combine ToM, CLoST, GCACU, SEVADE, TurboQuant, and mHC."""

    def __init__(
        self,
        embedding_dim: int = 64,
        hidden_dim: int = 64,
        num_heads: int = 4,
        mhc_low_rank: int = 4,
        turboquant_heads: int = 4,
        memory_budget_gb: float = 8.0,
    ):
        super().__init__()
        if embedding_dim % num_heads != 0:
            raise ValueError("embedding_dim must be divisible by num_heads.")
        if embedding_dim % turboquant_heads != 0:
            raise ValueError("embedding_dim must be divisible by turboquant_heads.")

        self.embedding_dim = embedding_dim
        self.num_heads = num_heads
        self.turboquant_heads = turboquant_heads
        self.tom = TheoryOfMindLayer(embedding_dim=embedding_dim, num_heads=num_heads, hidden_dim=hidden_dim)
        self.clost = CLoSTLayer(embedding_dim=embedding_dim, hidden_dim=hidden_dim)
        self.gcacu = GCACUNetwork(
            embedding_dim=embedding_dim,
            num_heads=num_heads,
            hidden_dim=hidden_dim,
            num_gating_levels=3,
        )
        self.mhc = ManifoldConstrainedHyperConnections(
            stream_dim=embedding_dim,
            num_streams=3,
            low_rank=mhc_low_rank,
            memory_budget_gb=memory_budget_gb,
        )
        self.sevade = SEVADEEvaluator(stream_dim=embedding_dim, num_architectures=3, hidden_dim=hidden_dim)
        self.final_head = nn.Sequential(
            nn.Linear(embedding_dim + 3, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1),
        )
        self.turboquant = TurboQuant(bits_per_channel=3, enable_qjl=True)

    def forward(self, inputs: Any) -> Dict[str, Any]:
        if isinstance(inputs, Tensor):
            embeddings = inputs
            attention_mask = torch.ones(inputs.shape[:2], dtype=inputs.dtype, device=inputs.device)
        elif isinstance(inputs, MutableMapping):
            embeddings = inputs["embeddings"]
            attention_mask = inputs.get("attention_mask")
            if attention_mask is None:
                attention_mask = torch.ones(embeddings.shape[:2], dtype=embeddings.dtype, device=embeddings.device)
        else:
            raise TypeError("IntegratedLaughterModel expects a tensor or mapping input.")

        tom_output = self.tom(embeddings, attention_mask)
        gcacu_output = self.gcacu(embeddings, attention_mask)
        gcacu_stream = gcacu_output.get("contextual_understanding")
        if gcacu_stream is None:
            gcacu_stream = embeddings.mean(dim=1)

        clost_probabilities: List[Tensor] = []
        clost_streams: List[Tensor] = []
        for sample_index in range(embeddings.size(0)):
            valid_tokens = self._valid_tokens(embeddings[sample_index], attention_mask[sample_index])
            split_point = max(1, int(valid_tokens.size(0) * 0.6))
            setup = valid_tokens[:split_point]
            punchline = valid_tokens[split_point:] if split_point < valid_tokens.size(0) else valid_tokens[-1:].clone()
            clost_output = self.clost(setup, punchline, attention_mask=None)
            humor_prediction = clost_output["humor_prediction"].reshape(1)
            clost_probabilities.append(humor_prediction)
            clost_streams.append((setup.mean(dim=0) + punchline.mean(dim=0)) / 2.0)

        clost_probability = torch.stack(clost_probabilities, dim=0).to(embeddings.device)
        clost_stream = torch.stack(clost_streams, dim=0).to(embeddings.device)

        architecture_scores = torch.cat(
            [
                tom_output["humor_prediction"],
                gcacu_output["incongruity_score"],
                clost_probability,
            ],
            dim=1,
        )
        architecture_streams = torch.stack(
            [
                tom_output["mental_states"]["fused_mental_state"],
                gcacu_stream,
                clost_stream,
            ],
            dim=1,
        )

        mhc_output = self.mhc(architecture_streams)
        sevade_output = self.sevade(mhc_output["mixed_streams"], architecture_scores)
        pooled_stream = mhc_output["mixed_streams"].mean(dim=1)
        fused_logits = self.final_head(torch.cat([pooled_stream, architecture_scores], dim=-1))
        logits = fused_logits + 0.5 * sevade_output["logits"] + 0.1 * safe_logit(architecture_scores.mean(dim=1, keepdim=True))
        turboquant_stats = self._compress_streams(mhc_output["mixed_streams"].detach())

        return {
            "logits": logits,
            "probabilities": torch.sigmoid(logits),
            "architecture_scores": architecture_scores,
            "architecture_streams": architecture_streams,
            "mhc": mhc_output,
            "sevade": sevade_output,
            "turboquant": turboquant_stats,
            "tom": tom_output,
            "gcacu": gcacu_output,
            "clost_probability": clost_probability,
        }

    def _valid_tokens(self, sample_embeddings: Tensor, sample_mask: Tensor) -> Tensor:
        if sample_mask is None:
            return sample_embeddings
        valid = sample_embeddings[sample_mask.bool()]
        return valid if valid.numel() else sample_embeddings[:1]

    def _compress_streams(self, streams: Tensor) -> Dict[str, float]:
        head_dim = self.embedding_dim // self.turboquant_heads
        cache = streams.reshape(streams.size(0), streams.size(1), self.turboquant_heads, head_dim)
        cache = cache.permute(0, 2, 1, 3).contiguous()
        self.turboquant.compress_kv_cache(cache, cache)
        return self.turboquant.get_compression_stats()

    def estimate_peak_memory_bytes(self, batch_size: int, seq_len: int) -> int:
        parameter_bytes = sum(parameter.numel() * parameter.element_size() for parameter in self.parameters())
        activation_bytes = batch_size * seq_len * self.embedding_dim * 4 * 8
        return parameter_bytes + activation_bytes


def make_dataloader(
    records: Sequence[TranscriptRecord],
    embedding_dim: int,
    max_seq_len: int,
    batch_size: int,
    shuffle: bool,
) -> torch.utils.data.DataLoader:
    embedder = DeterministicTextEmbedder(embedding_dim)
    dataset = ComedyTranscriptDataset(records, embedder=embedder, max_seq_len=max_seq_len)
    return torch.utils.data.DataLoader(dataset, batch_size=batch_size, shuffle=shuffle)
