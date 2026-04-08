"""
Engram contextual memory system with disk-backed storage and GDELT enrichment.

The implementation is designed for constrained Apple Silicon laptops where RAM is
scarce. Embeddings are stored as ``float16`` NumPy arrays on disk and retrieved
through hashed buckets to keep memory pressure low while still allowing fast
context reconstruction.
"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Dict, Iterable, List, MutableMapping, Optional, Sequence, Tuple

import numpy as np
import requests

LOGGER = logging.getLogger(__name__)


def _utc_now() -> str:
    """Return an ISO-8601 UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


def _stable_hash(value: str) -> str:
    """Create a stable SHA1 digest used for ids and bucket routing."""
    return hashlib.sha1(value.encode("utf-8")).hexdigest()


def _normalize_embedding(embedding: Sequence[float]) -> np.ndarray:
    """Convert any sequence-like embedding into a normalized ``float16`` vector."""
    vector = np.asarray(embedding, dtype=np.float32).reshape(-1)
    norm = float(np.linalg.norm(vector))
    if norm > 0.0:
        vector = vector / norm
    return vector.astype(np.float16, copy=False)


@dataclass(slots=True)
class MemoryRecord:
    """A single contextual memory item persisted by the Engram system."""

    memory_id: str
    text: str
    created_at: str
    source: str = "local"
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding_file: Optional[str] = None


@dataclass(slots=True)
class EngramConfig:
    """Configuration for the Engram memory system."""

    storage_dir: Path
    bucket_count: int = 128
    cache_size: int = 64
    gdelt_result_limit: int = 5
    external_context_hours: int = 72
    local_candidate_limit: int = 64
    similarity_temperature: float = 0.15
    max_embedding_bytes: int = 2 * 1024 * 1024


class DiskBackedMemoryStore:
    """
    Persist contextual memories on disk while keeping a tiny hot cache in RAM.

    The store uses hashed bucket manifests plus per-record embedding files to
    avoid loading the full memory table into memory.
    """

    def __init__(self, storage_dir: Path, bucket_count: int = 128, cache_size: int = 64):
        self.storage_dir = Path(storage_dir)
        self.bucket_count = max(8, bucket_count)
        self.cache_size = max(4, cache_size)
        self.records_dir = self.storage_dir / "records"
        self.embeddings_dir = self.storage_dir / "embeddings"
        self.records_dir.mkdir(parents=True, exist_ok=True)
        self.embeddings_dir.mkdir(parents=True, exist_ok=True)
        self._cache: "OrderedDict[str, Tuple[MemoryRecord, np.ndarray]]" = OrderedDict()

    def _bucket_id(self, token: str) -> str:
        """Map any token or memory id to a fixed manifest bucket."""
        return f"{int(_stable_hash(token), 16) % self.bucket_count:04d}"

    def _manifest_path(self, bucket_id: str) -> Path:
        """Return the JSON lines manifest path for a bucket."""
        return self.records_dir / f"{bucket_id}.jsonl"

    def _embedding_path(self, memory_id: str) -> Path:
        """Return the embedding path for a memory record."""
        return self.embeddings_dir / f"{memory_id}.npy"

    def put(self, record: MemoryRecord, embedding: Sequence[float]) -> None:
        """Persist a memory record and its normalized embedding."""
        vector = _normalize_embedding(embedding)
        np.save(self._embedding_path(record.memory_id), vector, allow_pickle=False)
        payload = asdict(record)
        payload["embedding_file"] = str(self._embedding_path(record.memory_id).name)
        manifest = self._manifest_path(self._bucket_id(record.memory_id))
        with manifest.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True) + "\n")
        self._set_cache(record.memory_id, record, vector)

    def get(self, memory_id: str) -> Optional[Tuple[MemoryRecord, np.ndarray]]:
        """Load a memory by id, consulting the LRU cache first."""
        cached = self._cache.get(memory_id)
        if cached is not None:
            self._cache.move_to_end(memory_id)
            return cached

        manifest = self._manifest_path(self._bucket_id(memory_id))
        if not manifest.exists():
            return None

        with manifest.open("r", encoding="utf-8") as handle:
            for line in handle:
                payload = json.loads(line)
                if payload["memory_id"] != memory_id:
                    continue
                record = MemoryRecord(**payload)
                vector = np.load(
                    self._embedding_path(record.memory_id),
                    allow_pickle=False,
                    mmap_mode="r",
                )
                self._set_cache(record.memory_id, record, np.asarray(vector, dtype=np.float16))
                return record, np.asarray(vector, dtype=np.float16)
        return None

    def iter_candidates(
        self,
        routing_terms: Optional[Sequence[str]] = None,
        limit: int = 64,
    ) -> Iterable[Tuple[MemoryRecord, np.ndarray]]:
        """
        Yield candidate memories from selected buckets.

        If no routing terms are provided, the first few non-empty buckets are
        scanned. This preserves bounded retrieval work under the 8GB constraint.
        """

        manifests: List[Path] = []
        if routing_terms:
            seen: set[str] = set()
            for term in routing_terms:
                bucket_id = self._bucket_id(term.lower())
                if bucket_id in seen:
                    continue
                seen.add(bucket_id)
                manifests.append(self._manifest_path(bucket_id))
        manifests.extend(
            manifest
            for manifest in sorted(self.records_dir.glob("*.jsonl"))
            if manifest not in manifests
        )
        if not routing_terms:
            manifests = manifests[: max(1, limit // 8)]

        yielded = 0
        for manifest in manifests:
            if not manifest.exists():
                continue
            with manifest.open("r", encoding="utf-8") as handle:
                for line in handle:
                    payload = json.loads(line)
                    record = MemoryRecord(**payload)
                    vector = np.load(
                        self._embedding_path(record.memory_id),
                        allow_pickle=False,
                        mmap_mode="r",
                    )
                    yield record, np.asarray(vector, dtype=np.float16)
                    yielded += 1
                    if yielded >= limit:
                        return

    def _set_cache(self, memory_id: str, record: MemoryRecord, vector: np.ndarray) -> None:
        """Insert an item into the LRU cache."""
        self._cache[memory_id] = (record, vector)
        self._cache.move_to_end(memory_id)
        while len(self._cache) > self.cache_size:
            self._cache.popitem(last=False)


class GDELTClient:
    """Thin GDELT API wrapper with failure-tolerant parsing."""

    def __init__(
        self,
        endpoint: str = "https://api.gdeltproject.org/api/v2/doc/doc",
        session: Optional[requests.Session] = None,
        timeout: float = 10.0,
    ):
        self.endpoint = endpoint
        self.session = session or requests.Session()
        self.timeout = timeout

    def fetch_events(
        self,
        query_terms: Sequence[str],
        max_records: int = 5,
        lookback_hours: int = 72,
    ) -> List[Dict[str, Any]]:
        """Fetch recent external context from GDELT for the provided terms."""
        query = " OR ".join(term.strip() for term in query_terms if term.strip())
        if not query:
            return []

        params = {
            "query": query,
            "mode": "artlist",
            "format": "json",
            "maxrecords": max_records,
            "sort": "datedesc",
            "timespan": f"{max(1, lookback_hours)} hours",
        }
        try:
            response = self.session.get(self.endpoint, params=params, timeout=self.timeout)
            response.raise_for_status()
            payload = response.json()
        except Exception as exc:
            LOGGER.warning("GDELT lookup failed for query '%s': %s", query, exc)
            return []

        articles = payload.get("articles") or payload.get("results") or []
        parsed: List[Dict[str, Any]] = []
        for article in articles[:max_records]:
            parsed.append(
                {
                    "title": article.get("title") or article.get("seendate") or "untitled",
                    "url": article.get("url"),
                    "source": article.get("sourcecountry") or article.get("domain"),
                    "seen_at": article.get("seendate") or _utc_now(),
                    "tone": article.get("tone"),
                }
            )
        return parsed


class EngramMemorySystem:
    """
    Retrieve compact contextual memory with optional GDELT-backed enrichment.

    Retrieval is intentionally bounded. The system only scans a limited set of
    hash buckets and keeps embeddings in ``float16`` to stay well below the
    target memory ceiling.
    """

    def __init__(
        self,
        config: EngramConfig,
        store: Optional[DiskBackedMemoryStore] = None,
        gdelt_client: Optional[GDELTClient] = None,
    ):
        self.config = config
        self.store = store or DiskBackedMemoryStore(
            storage_dir=config.storage_dir,
            bucket_count=config.bucket_count,
            cache_size=config.cache_size,
        )
        self.gdelt_client = gdelt_client or GDELTClient()

    def ingest_memory(
        self,
        text: str,
        embedding: Sequence[float],
        metadata: Optional[MutableMapping[str, Any]] = None,
        source: str = "local",
    ) -> MemoryRecord:
        """Store a new memory entry and return its persisted record."""
        vector = _normalize_embedding(embedding)
        if vector.nbytes > self.config.max_embedding_bytes:
            raise ValueError(
                f"Embedding too large for constrained Engram storage: {vector.nbytes} bytes."
            )

        metadata_dict = dict(metadata or {})
        memory_id = _stable_hash(f"{text}|{json.dumps(metadata_dict, sort_keys=True)}|{source}")
        record = MemoryRecord(
            memory_id=memory_id,
            text=text,
            created_at=_utc_now(),
            source=source,
            metadata=metadata_dict,
        )
        self.store.put(record, vector)
        LOGGER.info("Stored engram memory '%s' from %s", record.memory_id[:8], source)
        return record

    def retrieve_context(
        self,
        query_embedding: Sequence[float],
        context_terms: Optional[Sequence[str]] = None,
        top_k: int = 5,
        include_external: bool = True,
    ) -> Dict[str, Any]:
        """Retrieve local memories and optionally augment them with GDELT events."""
        query = _normalize_embedding(query_embedding).astype(np.float32, copy=False)
        scored: List[Dict[str, Any]] = []

        try:
            candidates = self.store.iter_candidates(
                routing_terms=context_terms,
                limit=self.config.local_candidate_limit,
            )
            for record, vector in candidates:
                similarity = float(np.dot(query, vector.astype(np.float32, copy=False)))
                scored.append(
                    {
                        "memory_id": record.memory_id,
                        "text": record.text,
                        "source": record.source,
                        "similarity": similarity,
                        "metadata": record.metadata,
                        "created_at": record.created_at,
                    }
                )
        except Exception as exc:
            LOGGER.exception("Local Engram retrieval failed: %s", exc)

        local_memories = sorted(scored, key=lambda item: item["similarity"], reverse=True)[:top_k]

        external_context: List[Dict[str, Any]] = []
        if include_external:
            external_context = self.gdelt_client.fetch_events(
                query_terms=context_terms or [],
                max_records=min(top_k, self.config.gdelt_result_limit),
                lookback_hours=self.config.external_context_hours,
            )

        return {
            "local_memories": local_memories,
            "external_context": external_context,
            "retrieved_at": _utc_now(),
            "routing_terms": list(context_terms or []),
        }

    def contextualize(
        self,
        query_text: str,
        query_embedding: Sequence[float],
        context_terms: Optional[Sequence[str]] = None,
        top_k: int = 5,
    ) -> Dict[str, Any]:
        """Generate a compact contextual bundle for downstream reasoning modules."""
        bundle = self.retrieve_context(
            query_embedding=query_embedding,
            context_terms=context_terms,
            top_k=top_k,
            include_external=True,
        )
        bundle["query_text"] = query_text
        bundle["summary"] = self._summarize_bundle(bundle)
        return bundle

    def _summarize_bundle(self, bundle: Dict[str, Any]) -> str:
        """Build a deterministic summary string for logging and prompts."""
        local_summary = "; ".join(
            item["text"][:96] for item in bundle.get("local_memories", [])[:3]
        ) or "no local context"
        external_summary = "; ".join(
            item.get("title", "untitled") for item in bundle.get("external_context", [])[:2]
        ) or "no external context"
        return f"Local: {local_summary}. External: {external_summary}."


def self_test(storage_dir: Path) -> Dict[str, Any]:
    """Run a minimal, dependency-light validation of the Engram system."""

    class _FakeGDELTClient:
        def fetch_events(
            self,
            query_terms: Sequence[str],
            max_records: int = 5,
            lookback_hours: int = 72,
        ) -> List[Dict[str, Any]]:
            return [
                {
                    "title": f"External context for {' '.join(query_terms)}",
                    "url": "https://example.com/article",
                    "source": "test",
                    "seen_at": _utc_now(),
                    "tone": 0.1,
                }
            ][:max_records]

    system = EngramMemorySystem(
        config=EngramConfig(storage_dir=storage_dir),
        gdelt_client=_FakeGDELTClient(),  # type: ignore[arg-type]
    )
    system.ingest_memory(
        text="Audience laughed at callback about airports.",
        embedding=[1.0, 0.0, 0.0],
        metadata={"label": "callback"},
    )
    system.ingest_memory(
        text="Political setup referenced a late-night monologue.",
        embedding=[0.0, 1.0, 0.0],
        metadata={"label": "politics"},
    )
    bundle = system.contextualize(
        query_text="airport callback",
        query_embedding=[0.9, 0.1, 0.0],
        context_terms=["airport", "comedy"],
        top_k=2,
    )
    return {
        "local_count": len(bundle["local_memories"]),
        "external_count": len(bundle["external_context"]),
        "summary": bundle["summary"],
    }
