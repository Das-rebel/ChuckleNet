#!/usr/bin/env python3
"""
Create a biosemotically filtered humor dataset from the legacy unified humor CSV.

The retained subset is intentionally narrow:
- all Reddit jokes
- high-quality MELD joy utterances with multimodal dialogue context

The output is a positive-only humor-rich subset for feature engineering, not a
drop-in binary classification replacement for the stand-up word-level pipeline.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


TOKEN_RE = re.compile(r"[A-Za-z]+(?:['-][A-Za-z]+)?")
NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")
WHITESPACE_RE = re.compile(r"\s+")

STOPWORDS = {
    "a",
    "about",
    "after",
    "all",
    "also",
    "am",
    "an",
    "and",
    "any",
    "are",
    "as",
    "at",
    "be",
    "because",
    "been",
    "before",
    "being",
    "but",
    "by",
    "can",
    "could",
    "did",
    "do",
    "does",
    "for",
    "from",
    "get",
    "go",
    "had",
    "has",
    "have",
    "he",
    "her",
    "here",
    "him",
    "his",
    "how",
    "i",
    "if",
    "im",
    "in",
    "into",
    "is",
    "it",
    "its",
    "just",
    "me",
    "my",
    "no",
    "not",
    "of",
    "on",
    "or",
    "our",
    "out",
    "she",
    "so",
    "than",
    "that",
    "the",
    "their",
    "them",
    "there",
    "they",
    "this",
    "to",
    "too",
    "up",
    "us",
    "was",
    "we",
    "were",
    "what",
    "when",
    "where",
    "who",
    "why",
    "with",
    "would",
    "you",
    "your",
}

JOY_WORDS = {
    "amazing",
    "awesome",
    "celebrate",
    "delight",
    "enjoy",
    "fun",
    "funny",
    "glad",
    "great",
    "happy",
    "hilarious",
    "joy",
    "laugh",
    "laughing",
    "love",
    "nice",
    "perfect",
    "smile",
    "wonderful",
    "yay",
}

LAUGHTER_MARKERS = {
    "haha",
    "hahaha",
    "hehe",
    "lol",
    "lmao",
    "rofl",
    "laugh",
    "laughed",
    "laughing",
    "funny",
    "hilarious",
    "joke",
    "kidding",
    "smile",
    "smiled",
    "grin",
    "grinning",
}

CONTRAST_MARKERS = {
    "actually",
    "apparently",
    "but",
    "except",
    "instead",
    "meanwhile",
    "though",
    "turns",
    "until",
    "yet",
}

SOCIAL_WORDS = {
    "audience",
    "everybody",
    "everyone",
    "friend",
    "friends",
    "guy",
    "guys",
    "he",
    "her",
    "him",
    "mom",
    "mother",
    "people",
    "roommate",
    "sister",
    "they",
    "we",
    "you",
}

POSITIVE_WORDS = {
    "awesome",
    "best",
    "enjoy",
    "fun",
    "funny",
    "glad",
    "good",
    "great",
    "happy",
    "love",
    "perfect",
    "proud",
    "smart",
    "wonderful",
}

NEGATIVE_WORDS = {
    "angry",
    "bad",
    "cry",
    "dead",
    "destroy",
    "hate",
    "problem",
    "shame",
    "sucks",
    "terrible",
    "worst",
}


@dataclass(slots=True)
class RedditMeta:
    title: str
    body: str
    source_score: float


@dataclass(slots=True)
class MeldContext:
    speaker: str
    dialogue_id: str
    utterance_id: int
    season: int
    episode: int
    start_time: str
    end_time: str
    prev_turns: list[str]
    next_turns: list[str]
    dialogue_turn_count: int
    distinct_speakers: int
    utterance_duration_seconds: float
    response_latency_seconds: float
    multimodal_context_available: int


def normalize_text(text: Any) -> str:
    if text is None:
        return ""
    normalized = str(text)
    normalized = normalized.replace("\ufeff", "")
    normalized = normalized.replace("\r", " ").replace("\n", " ").replace("\t", " ")
    normalized = normalized.replace("“", '"').replace("”", '"')
    normalized = normalized.replace("’", "'").replace("‘", "'")
    normalized = normalized.replace("\u00a0", " ")
    return WHITESPACE_RE.sub(" ", normalized).strip()


def canonicalize(text: str) -> str:
    lowered = normalize_text(text).lower()
    return WHITESPACE_RE.sub(" ", NON_ALNUM_RE.sub(" ", lowered)).strip()


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(normalize_text(text))]


def content_tokens(text: str) -> list[str]:
    return [token for token in tokenize(text) if token not in STOPWORDS]


def clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


def safe_divide(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def parse_timestamp(timestamp: str) -> float:
    value = normalize_text(timestamp)
    if not value:
        return 0.0
    hh, mm, rest = value.split(":")
    ss, ms = rest.split(",")
    return int(hh) * 3600 + int(mm) * 60 + int(ss) + int(ms) / 1000.0


def mean(values: Iterable[float]) -> float:
    sequence = list(values)
    return sum(sequence) / len(sequence) if sequence else 0.0


def percentile(sorted_values: list[float], p: float) -> float:
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return float(sorted_values[0])
    index = (len(sorted_values) - 1) * p
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return float(sorted_values[lower])
    lower_value = float(sorted_values[lower])
    upper_value = float(sorted_values[upper])
    return lower_value + (upper_value - lower_value) * (index - lower)


def numeric_summary(values: list[float]) -> dict[str, float]:
    if not values:
        return {
            "count": 0,
            "min": 0.0,
            "max": 0.0,
            "mean": 0.0,
            "median": 0.0,
            "p10": 0.0,
            "p90": 0.0,
        }
    ordered = sorted(float(value) for value in values)
    return {
        "count": len(ordered),
        "min": round(ordered[0], 4),
        "max": round(ordered[-1], 4),
        "mean": round(sum(ordered) / len(ordered), 4),
        "median": round(percentile(ordered, 0.5), 4),
        "p10": round(percentile(ordered, 0.1), 4),
        "p90": round(percentile(ordered, 0.9), 4),
    }


def pearson(values_a: list[float], values_b: list[float]) -> float:
    if len(values_a) != len(values_b) or len(values_a) < 2:
        return 0.0
    mean_a = mean(values_a)
    mean_b = mean(values_b)
    numerator = sum((a - mean_a) * (b - mean_b) for a, b in zip(values_a, values_b))
    denom_a = math.sqrt(sum((a - mean_a) ** 2 for a in values_a))
    denom_b = math.sqrt(sum((b - mean_b) ** 2 for b in values_b))
    if denom_a == 0.0 or denom_b == 0.0:
        return 0.0
    return numerator / (denom_a * denom_b)


def stable_hash(value: str, seed: int) -> str:
    return hashlib.sha1(f"{seed}:{value}".encode("utf-8")).hexdigest()


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_reddit_metadata(path: Path) -> dict[str, RedditMeta]:
    metadata: dict[str, RedditMeta] = {}
    if not path.exists():
        return metadata
    for row in read_csv_rows(path):
        metadata[str(row["sample_id"])] = RedditMeta(
            title=normalize_text(row.get("title", "")),
            body=normalize_text(row.get("body", "")),
            source_score=float(row.get("source_score", "0") or 0.0),
        )
    return metadata


def load_meld_contexts(meld_dir: Path) -> dict[tuple[str, str], MeldContext]:
    contexts: dict[tuple[str, str], MeldContext] = {}
    split_map = {
        "train_sent_emo.csv": "train",
        "dev_sent_emo.csv": "validation",
        "test_sent_emo.csv": "test",
    }
    dialogue_rows: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    raw_rows: dict[tuple[str, str], dict[str, str]] = {}

    for filename, split in split_map.items():
        path = meld_dir / filename
        if not path.exists():
            continue
        for row in read_csv_rows(path):
            record_id = f"{normalize_text(row['Dialogue_ID'])}_{normalize_text(row['Utterance_ID'])}"
            key = (split, record_id)
            raw_rows[key] = row
            dialogue_key = (split, normalize_text(row["Dialogue_ID"]))
            dialogue_rows[dialogue_key].append(row)

    for (split, dialogue_id), rows in dialogue_rows.items():
        rows.sort(key=lambda row: int(normalize_text(row["Utterance_ID"]) or "0"))
        distinct_speakers = len({normalize_text(row.get("Speaker", "")) for row in rows if normalize_text(row.get("Speaker", ""))})
        for index, row in enumerate(rows):
            utterance_id = int(normalize_text(row["Utterance_ID"]) or "0")
            record_id = f"{dialogue_id}_{utterance_id}"
            prev_turns = [
                f"{normalize_text(prev.get('Speaker', ''))}: {normalize_text(prev.get('Utterance', ''))}".strip(": ")
                for prev in rows[max(0, index - 2):index]
                if normalize_text(prev.get("Utterance", ""))
            ]
            next_turns = [
                f"{normalize_text(nxt.get('Speaker', ''))}: {normalize_text(nxt.get('Utterance', ''))}".strip(": ")
                for nxt in rows[index + 1:index + 3]
                if normalize_text(nxt.get("Utterance", ""))
            ]
            start_seconds = parse_timestamp(normalize_text(row.get("StartTime", "")))
            end_seconds = parse_timestamp(normalize_text(row.get("EndTime", "")))
            next_start = parse_timestamp(normalize_text(rows[index + 1].get("StartTime", ""))) if index + 1 < len(rows) else 0.0
            response_latency = max(0.0, next_start - end_seconds) if next_start else 0.0
            contexts[(split, record_id)] = MeldContext(
                speaker=normalize_text(row.get("Speaker", "")),
                dialogue_id=dialogue_id,
                utterance_id=utterance_id,
                season=int(normalize_text(row.get("Season", "0")) or "0"),
                episode=int(normalize_text(row.get("Episode", "0")) or "0"),
                start_time=normalize_text(row.get("StartTime", "")),
                end_time=normalize_text(row.get("EndTime", "")),
                prev_turns=prev_turns,
                next_turns=next_turns,
                dialogue_turn_count=len(rows),
                distinct_speakers=distinct_speakers,
                utterance_duration_seconds=round(max(0.0, end_seconds - start_seconds), 3),
                response_latency_seconds=round(response_latency, 3),
                multimodal_context_available=1 if start_seconds or end_seconds else 0,
            )
    return contexts


def split_reddit_joke(text: str, meta: RedditMeta | None) -> tuple[str, str]:
    if meta and meta.title and meta.body:
        return meta.title, meta.body
    if "?" in text:
        prefix, suffix = text.rsplit("?", 1)
        if suffix.strip():
            return normalize_text(prefix + "?"), normalize_text(suffix)
    sentences = re.split(r"(?<=[.!?])\s+", text)
    if len(sentences) >= 2:
        return normalize_text(" ".join(sentences[:-1])), normalize_text(sentences[-1])
    tokens = text.split()
    pivot = max(1, int(len(tokens) * 0.6))
    return normalize_text(" ".join(tokens[:pivot])), normalize_text(" ".join(tokens[pivot:]))


def split_meld_joy(text: str, context: MeldContext | None) -> tuple[str, str, str]:
    if context:
        setup = normalize_text(" ".join(context.prev_turns[-2:]))
        audience = normalize_text(" ".join(context.next_turns[:1]))
        return setup, normalize_text(text), audience
    return "", normalize_text(text), ""


def infer_structure_type(source_dataset: str, text: str, setup_text: str, punchline_text: str, context: MeldContext | None) -> str:
    token_count = len(tokenize(text))
    if source_dataset == "reddit_jokes":
        if setup_text.endswith("?"):
            return "question_answer_joke"
        if any(marker in setup_text.lower() for marker in {"i ", "my ", "we ", "when ", "remember ", "yesterday "}):
            return "narrative_reversal"
        if '"' in text or "'" in text:
            return "quoted_dialogue_joke"
        return "setup_punchline_joke"
    if context and context.distinct_speakers >= 2:
        if token_count <= 5:
            return "joyful_reaction"
        if setup_text:
            return "dialogic_banter"
        return "conversational_humor"
    if token_count <= 6:
        return "short_amusement"
    return "generic_humor"


def count_set_hits(tokens: list[str], lexicon: set[str]) -> int:
    return sum(1 for token in tokens if token in lexicon)


def semantic_distance(setup_text: str, punchline_text: str) -> float:
    setup = set(content_tokens(setup_text))
    punchline = set(content_tokens(punchline_text))
    if not setup and not punchline:
        return 0.0
    intersection = len(setup & punchline)
    union = len(setup | punchline)
    return round(1.0 - safe_divide(intersection, union), 4)


def polarity_balance(tokens: list[str]) -> float:
    positive = count_set_hits(tokens, POSITIVE_WORDS)
    negative = count_set_hits(tokens, NEGATIVE_WORDS)
    return safe_divide(abs(positive - negative), positive + negative + 1)


def classify_speaker_intent(source_dataset: str, structure_type: str, text: str, context: MeldContext | None) -> tuple[str, float]:
    lowered = normalize_text(text).lower()
    if source_dataset == "reddit_jokes":
        if structure_type == "question_answer_joke":
            return "joke_delivery", 0.95
        if structure_type == "narrative_reversal":
            return "storytelling", 0.9
        return "comic_observation", 0.88
    if context and context.distinct_speakers >= 2:
        if len(tokenize(text)) <= 5:
            return "reactive_amusement", 0.84
        if "you" in lowered or "we" in lowered:
            return "playful_banter", 0.82
        return "social_response", 0.78
    return "humor_expression", 0.7


def classify_interaction_pattern(source_dataset: str, structure_type: str, context: MeldContext | None) -> tuple[str, float]:
    if source_dataset == "reddit_jokes":
        if structure_type == "question_answer_joke":
            return "call_and_response", 0.94
        if structure_type == "quoted_dialogue_joke":
            return "reported_dialogue", 0.9
        return "monologue", 0.87
    if context and context.distinct_speakers >= 3:
        return "multi_party_banter", 0.85
    if context and context.distinct_speakers >= 2:
        return "dialogue_exchange", 0.83
    return "single_turn", 0.65


def extract_features(
    row: dict[str, str],
    reddit_meta: RedditMeta | None,
    meld_context: MeldContext | None,
) -> dict[str, Any]:
    text = normalize_text(row["text"])
    source_dataset = normalize_text(row["source_dataset"])

    if source_dataset == "reddit_jokes":
        setup_text, punchline_text = split_reddit_joke(text, reddit_meta)
        audience_response_text = ""
    else:
        setup_text, punchline_text, audience_response_text = split_meld_joy(text, meld_context)

    setup_tokens = tokenize(setup_text)
    punchline_tokens = tokenize(punchline_text)
    all_tokens = tokenize(text)
    token_count = len(all_tokens)
    exclamation_count = text.count("!")
    question_count = text.count("?")
    uppercase_ratio = safe_divide(sum(1 for char in text if char.isupper()), len(text))
    laughter_marker_hits = count_set_hits(all_tokens, LAUGHTER_MARKERS)
    joy_hits = count_set_hits(all_tokens, JOY_WORDS)
    contrast_hits = count_set_hits(all_tokens, CONTRAST_MARKERS)
    social_hits = count_set_hits(all_tokens, SOCIAL_WORDS)
    unique_ratio = safe_divide(len(set(all_tokens)), len(all_tokens)) if all_tokens else 0.0

    structure_type = infer_structure_type(source_dataset, text, setup_text, punchline_text, meld_context)
    structure_score = 1.0 if setup_text and punchline_text else 0.55
    if source_dataset == "meld" and meld_context and meld_context.prev_turns:
        structure_score = max(structure_score, 0.86)
    if source_dataset == "reddit_jokes" and reddit_meta and reddit_meta.title and reddit_meta.body:
        structure_score = 1.0

    semantic_shift = semantic_distance(setup_text, punchline_text)
    sentiment_shift = abs(polarity_balance(setup_tokens) - polarity_balance(punchline_tokens))
    question_answer_bonus = 0.2 if structure_type == "question_answer_joke" else 0.0
    expectation_violation = clamp(0.55 * semantic_shift + 0.15 * sentiment_shift + 0.1 * min(1.0, contrast_hits / 2.0) + question_answer_bonus)

    if setup_tokens and punchline_tokens:
        punchline_position_ratio = round(safe_divide(len(setup_tokens), len(setup_tokens) + len(punchline_tokens)), 4)
    else:
        punchline_position_ratio = 0.5
    resolution_time = round(1.0 - punchline_position_ratio, 4)

    sentence_count = max(1, len(re.findall(r"[.!?]+", text)))
    complexity = clamp(
        0.22 * min(1.0, sentence_count / 4.0)
        + 0.18 * min(1.0, unique_ratio)
        + 0.18 * min(1.0, len(setup_tokens) / 20.0)
        + 0.18 * min(1.0, len(punchline_tokens) / 12.0)
        + 0.12 * min(1.0, safe_divide(text.count('"') + text.count("'"), 6))
        + 0.12 * min(1.0, ((meld_context.distinct_speakers - 1) / 4.0) if meld_context else 0.0)
    )

    joy_intensity = clamp(
        0.35 * min(1.0, joy_hits / 3.0)
        + 0.25 * min(1.0, exclamation_count / 3.0)
        + 0.2 * min(1.0, uppercase_ratio * 8.0)
        + 0.2 * min(1.0, (float(row["quality_score"]) - 90.0) / 10.0)
    )

    spontaneous_laughter_markers = round(
        laughter_marker_hits + min(3, exclamation_count) * 0.5 + (0.5 if "[laughter]" in text.lower() else 0.0),
        4,
    )

    speaker_intent_label, speaker_intent_confidence = classify_speaker_intent(source_dataset, structure_type, punchline_text or text, meld_context)
    interaction_pattern, interaction_score = classify_interaction_pattern(source_dataset, structure_type, meld_context)

    audience_perspective_score = clamp(
        0.35 * min(1.0, social_hits / 4.0)
        + 0.25 * (1.0 if "you" in all_tokens or "we" in all_tokens else 0.0)
        + 0.2 * (1.0 if audience_response_text else 0.0)
        + 0.2 * (1.0 if structure_type in {"question_answer_joke", "dialogic_banter"} else 0.0)
    )

    social_context_score = clamp(
        0.3 * min(1.0, social_hits / 4.0)
        + 0.3 * min(1.0, ((meld_context.distinct_speakers - 1) / 4.0) if meld_context else 0.0)
        + 0.2 * (1.0 if setup_text else 0.0)
        + 0.2 * (1.0 if audience_response_text else 0.0)
    )

    source_prior = 0.94 if source_dataset == "reddit_jokes" else 0.68
    genuine_humor_probability = clamp(
        0.42 * source_prior
        + 0.18 * structure_score
        + 0.16 * expectation_violation
        + 0.12 * social_context_score
        + 0.12 * joy_intensity
    )

    if meld_context:
        dialogue_turn_count = meld_context.dialogue_turn_count
        distinct_speakers = meld_context.distinct_speakers
        multimodal_context_available = meld_context.multimodal_context_available
        utterance_duration_seconds = meld_context.utterance_duration_seconds
        response_latency_seconds = meld_context.response_latency_seconds
    else:
        dialogue_turn_count = 1
        distinct_speakers = 1
        multimodal_context_available = 0
        utterance_duration_seconds = 0.0
        response_latency_seconds = 0.0

    biosemiotic_viability = clamp(
        0.2 * genuine_humor_probability
        + 0.16 * expectation_violation
        + 0.16 * joy_intensity
        + 0.16 * structure_score
        + 0.16 * social_context_score
        + 0.16 * interaction_score
    )

    return {
        "setup_text": setup_text,
        "punchline_text": punchline_text,
        "audience_response_text": audience_response_text,
        "humor_structure_type": structure_type,
        "duchenne_joy_intensity": round(joy_intensity, 4),
        "duchenne_genuine_humor_probability": round(genuine_humor_probability, 4),
        "duchenne_spontaneous_laughter_markers": round(spontaneous_laughter_markers, 4),
        "duchenne_setup_punchline_structure": round(structure_score, 4),
        "incongruity_setup_punchline_semantic_distance": round(semantic_shift, 4),
        "incongruity_expectation_violation_score": round(expectation_violation, 4),
        "incongruity_resolution_time": round(resolution_time, 4),
        "incongruity_humor_complexity_score": round(complexity, 4),
        "tom_speaker_intent_label": speaker_intent_label,
        "tom_speaker_intent_confidence": round(speaker_intent_confidence, 4),
        "tom_audience_perspective_score": round(audience_perspective_score, 4),
        "tom_social_context_humor_score": round(social_context_score, 4),
        "tom_character_interaction_pattern": interaction_pattern,
        "tom_character_interaction_score": round(interaction_score, 4),
        "dialogue_turn_count": int(dialogue_turn_count),
        "distinct_speakers": int(distinct_speakers),
        "multimodal_context_available": int(multimodal_context_available),
        "utterance_duration_seconds": round(float(utterance_duration_seconds), 4),
        "response_latency_seconds": round(float(response_latency_seconds), 4),
        "punchline_position_ratio": round(punchline_position_ratio, 4),
        "biosemiotic_viability_score": round(biosemiotic_viability, 4),
    }


def filter_rows(
    unified_rows: list[dict[str, str]],
    reddit_metadata: dict[str, RedditMeta],
    meld_contexts: dict[tuple[str, str], MeldContext],
    meld_quality_threshold: float,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    kept_rows: list[dict[str, Any]] = []
    removed_counts = Counter()
    kept_counts = Counter()

    for row in unified_rows:
        source_dataset = normalize_text(row["source_dataset"])
        sample_id = normalize_text(row["sample_id"])
        keep = False
        keep_reason = ""
        meld_context = None
        reddit_meta = reddit_metadata.get(sample_id)

        if source_dataset == "reddit_jokes":
            keep = True
            keep_reason = "reddit_joke_direct_keep"
        elif source_dataset == "meld":
            source_label_name = normalize_text(row["source_label_name"]).lower()
            quality_score = float(row["quality_score"])
            meld_context = meld_contexts.get((normalize_text(row["source_split"]), normalize_text(row["source_record_id"])))
            if source_label_name == "joy" and quality_score > meld_quality_threshold and meld_context and meld_context.multimodal_context_available:
                keep = True
                keep_reason = "meld_joy_quality_multimodal_keep"

        if not keep:
            removed_counts[source_dataset] += 1
            continue

        features = extract_features(row, reddit_meta, meld_context)
        kept_row = dict(row)
        kept_row["biosemotic_keep_reason"] = keep_reason
        kept_row.update(features)
        kept_rows.append(kept_row)
        kept_counts[source_dataset] += 1

    report = {
        "kept_counts_by_source": dict(kept_counts),
        "removed_counts_by_source": dict(removed_counts),
    }
    return kept_rows, report


def assign_splits(rows: list[dict[str, Any]], seed: int, train_ratio: float, valid_ratio: float) -> None:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        group_key = f"{row['source_dataset']}|{row['humor_structure_type']}"
        grouped[group_key].append(row)

    for group_rows in grouped.values():
        group_rows.sort(key=lambda row: stable_hash(normalize_text(row["sample_id"]), seed))
        count = len(group_rows)
        train_cut = int(round(count * train_ratio))
        valid_cut = int(round(count * valid_ratio))
        if count >= 10:
            valid_cut = max(1, valid_cut)
            test_cut = max(1, count - train_cut - valid_cut)
        else:
            test_cut = max(0, count - train_cut - valid_cut)
        if train_cut + valid_cut + test_cut > count:
            overflow = train_cut + valid_cut + test_cut - count
            train_cut = max(1, train_cut - overflow)
        if count - train_cut - valid_cut - test_cut > 0:
            train_cut += count - train_cut - valid_cut - test_cut

        train_end = train_cut
        valid_end = train_end + valid_cut
        for index, row in enumerate(group_rows):
            if index < train_end:
                row["biosemotic_split"] = "train"
            elif index < valid_end:
                row["biosemotic_split"] = "valid"
            else:
                row["biosemotic_split"] = "test"


def field_order(rows: list[dict[str, Any]]) -> list[str]:
    preferred = [
        "sample_id",
        "text",
        "label",
        "source_dataset",
        "source_split",
        "source_record_id",
        "source_label_name",
        "label_origin",
        "proxy_signal",
        "quality_score",
        "biosemotic_keep_reason",
        "biosemotic_split",
        "setup_text",
        "punchline_text",
        "audience_response_text",
        "humor_structure_type",
        "duchenne_joy_intensity",
        "duchenne_genuine_humor_probability",
        "duchenne_spontaneous_laughter_markers",
        "duchenne_setup_punchline_structure",
        "incongruity_setup_punchline_semantic_distance",
        "incongruity_expectation_violation_score",
        "incongruity_resolution_time",
        "incongruity_humor_complexity_score",
        "tom_speaker_intent_label",
        "tom_speaker_intent_confidence",
        "tom_audience_perspective_score",
        "tom_social_context_humor_score",
        "tom_character_interaction_pattern",
        "tom_character_interaction_score",
        "dialogue_turn_count",
        "distinct_speakers",
        "multimodal_context_available",
        "utterance_duration_seconds",
        "response_latency_seconds",
        "punchline_position_ratio",
        "biosemiotic_viability_score",
    ]
    discovered = set()
    for row in rows:
        discovered.update(row.keys())
    ordered = [field for field in preferred if field in discovered]
    ordered.extend(sorted(discovered - set(ordered)))
    return ordered


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def build_report(rows: list[dict[str, Any]], filter_report: dict[str, Any], output_dir: Path, args: argparse.Namespace) -> dict[str, Any]:
    numeric_fields = [
        "duchenne_joy_intensity",
        "duchenne_genuine_humor_probability",
        "duchenne_spontaneous_laughter_markers",
        "duchenne_setup_punchline_structure",
        "incongruity_setup_punchline_semantic_distance",
        "incongruity_expectation_violation_score",
        "incongruity_resolution_time",
        "incongruity_humor_complexity_score",
        "tom_speaker_intent_confidence",
        "tom_audience_perspective_score",
        "tom_social_context_humor_score",
        "tom_character_interaction_score",
        "dialogue_turn_count",
        "distinct_speakers",
        "multimodal_context_available",
        "utterance_duration_seconds",
        "response_latency_seconds",
        "punchline_position_ratio",
        "biosemiotic_viability_score",
    ]

    source_counts = Counter(normalize_text(row["source_dataset"]) for row in rows)
    split_counts = Counter(normalize_text(row["biosemotic_split"]) for row in rows)
    structure_counts = Counter(normalize_text(row["humor_structure_type"]) for row in rows)
    intent_counts = Counter(normalize_text(row["tom_speaker_intent_label"]) for row in rows)
    interaction_counts = Counter(normalize_text(row["tom_character_interaction_pattern"]) for row in rows)

    numeric_summaries = {
        field: numeric_summary([float(row[field]) for row in rows])
        for field in numeric_fields
    }
    split_source_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    split_structure_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in rows:
        split_source_counts[row["biosemotic_split"]][row["source_dataset"]] += 1
        split_structure_counts[row["biosemotic_split"]][row["humor_structure_type"]] += 1

    correlations = []
    excluded_pairs = {
        frozenset({"incongruity_resolution_time", "punchline_position_ratio"}),
    }
    for index, field_a in enumerate(numeric_fields):
        values_a = [float(row[field_a]) for row in rows]
        for field_b in numeric_fields[index + 1:]:
            if frozenset({field_a, field_b}) in excluded_pairs:
                continue
            values_b = [float(row[field_b]) for row in rows]
            corr = pearson(values_a, values_b)
            correlations.append(
                {
                    "feature_a": field_a,
                    "feature_b": field_b,
                    "pearson": round(corr, 4),
                    "absolute_pearson": round(abs(corr), 4),
                }
            )
    correlations.sort(key=lambda item: item["absolute_pearson"], reverse=True)

    dataset_summary = {
        "rows": len(rows),
        "positive_only_dataset": len({normalize_text(str(row["label"])) for row in rows}) == 1,
        "source_counts": dict(source_counts),
        "split_counts": dict(split_counts),
        "humor_structure_counts": dict(structure_counts),
        "speaker_intent_counts": dict(intent_counts),
        "interaction_pattern_counts": dict(interaction_counts),
        "feature_summaries": numeric_summaries,
        "split_source_counts": {split: dict(counts) for split, counts in split_source_counts.items()},
        "split_structure_counts": {split: dict(counts) for split, counts in split_structure_counts.items()},
        "top_feature_correlations": correlations[:15],
    }

    report = {
        "inputs": {
            "unified_csv": str(args.input_csv),
            "reddit_csv": str(args.reddit_csv),
            "meld_dir": str(args.meld_dir),
            "meld_quality_threshold": args.meld_quality_threshold,
            "seed": args.seed,
        },
        "filtering": filter_report,
        "dataset_summary": dataset_summary,
        "quality_validation": {
            "all_sources_allowed": all(row["source_dataset"] in {"reddit_jokes", "meld"} for row in rows),
            "all_meld_rows_are_joy": all(
                row["source_dataset"] != "meld" or normalize_text(row["source_label_name"]).lower() == "joy"
                for row in rows
            ),
            "all_meld_rows_above_threshold": all(
                row["source_dataset"] != "meld" or float(row["quality_score"]) > args.meld_quality_threshold
                for row in rows
            ),
            "all_meld_rows_have_multimodal_context": all(
                row["source_dataset"] != "meld" or int(row["multimodal_context_available"]) == 1
                for row in rows
            ),
            "biosemiotic_viability_mean": numeric_summaries["biosemiotic_viability_score"]["mean"],
            "single_class_risk": True,
        },
        "artifacts": {
            "dataset_csv": str(output_dir / "biosemotic_dataset.csv"),
            "train_csv": str(output_dir / "train.csv"),
            "valid_csv": str(output_dir / "valid.csv"),
            "test_csv": str(output_dir / "test.csv"),
            "report_json": str(output_dir / "filtering_report.json"),
            "report_markdown": str(output_dir / "filtering_report.md"),
        },
    }
    return report


def build_markdown_report(report: dict[str, Any]) -> str:
    dataset_summary = report["dataset_summary"]
    filtering = report["filtering"]
    lines = [
        "# Biosemotic Dataset Filtering Report",
        "",
        "## Summary",
        f"- Retained rows: `{dataset_summary['rows']}`",
        f"- Source counts: `{dataset_summary['source_counts']}`",
        f"- Split counts: `{dataset_summary['split_counts']}`",
        f"- Removed counts: `{filtering['removed_counts_by_source']}`",
        "",
        "## Filtering Rules",
        "- Keep all `reddit_jokes` rows.",
        f"- Keep only `meld` rows with `source_label_name = joy`, `quality_score > {report['inputs']['meld_quality_threshold']}`, and multimodal timing context present in raw MELD files.",
        "- Drop all remaining sources from the unified humor dataset.",
        "",
        "## Humor Structure Balance",
        f"- Structure counts: `{dataset_summary['humor_structure_counts']}`",
        f"- Speaker intent counts: `{dataset_summary['speaker_intent_counts']}`",
        f"- Interaction pattern counts: `{dataset_summary['interaction_pattern_counts']}`",
        "",
        "## Feature Quality",
        f"- Mean biosemiotic viability: `{report['quality_validation']['biosemiotic_viability_mean']}`",
        f"- Mean genuine humor probability: `{dataset_summary['feature_summaries']['duchenne_genuine_humor_probability']['mean']}`",
        f"- Mean expectation violation: `{dataset_summary['feature_summaries']['incongruity_expectation_violation_score']['mean']}`",
        f"- Mean social context humor score: `{dataset_summary['feature_summaries']['tom_social_context_humor_score']['mean']}`",
        "",
        "## Validation Notes",
        f"- Allowed sources only: `{report['quality_validation']['all_sources_allowed']}`",
        f"- MELD joy-only check: `{report['quality_validation']['all_meld_rows_are_joy']}`",
        f"- MELD quality threshold check: `{report['quality_validation']['all_meld_rows_above_threshold']}`",
        f"- MELD multimodal context check: `{report['quality_validation']['all_meld_rows_have_multimodal_context']}`",
        "- This subset is positive-only and should be treated as a humor-rich feature-engineering corpus rather than a standalone binary classification dataset.",
        "",
        "## Top Numeric Correlations",
    ]
    for item in dataset_summary["top_feature_correlations"][:10]:
        lines.append(
            f"- `{item['feature_a']}` vs `{item['feature_b']}`: `pearson={item['pearson']}`"
        )
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a biosemotic humor dataset.")
    parser.add_argument(
        "--input-csv",
        type=Path,
        default=Path("data/training/final_unified_humor/unified_dataset.csv"),
        help="Path to the unified humor CSV.",
    )
    parser.add_argument(
        "--reddit-csv",
        type=Path,
        default=Path("data/training/reddit_jokes/reddit_jokes_humor.csv"),
        help="Path to the processed Reddit jokes CSV with title/body metadata.",
    )
    parser.add_argument(
        "--meld-dir",
        type=Path,
        default=Path("/Users/Subho/datasets/MELD/data/MELD"),
        help="Directory containing MELD raw CSV files.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/training/biosemotic_humor"),
        help="Directory for the filtered dataset and reports.",
    )
    parser.add_argument(
        "--meld-quality-threshold",
        type=float,
        default=95.0,
        help="Minimum MELD quality score; rows must be strictly greater than this threshold.",
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--train-ratio", type=float, default=0.8)
    parser.add_argument("--valid-ratio", type=float, default=0.1)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.input_csv.exists():
        raise FileNotFoundError(f"Unified dataset not found: {args.input_csv}")

    unified_rows = read_csv_rows(args.input_csv)
    reddit_metadata = load_reddit_metadata(args.reddit_csv)
    meld_contexts = load_meld_contexts(args.meld_dir)

    kept_rows, filter_report = filter_rows(
        unified_rows=unified_rows,
        reddit_metadata=reddit_metadata,
        meld_contexts=meld_contexts,
        meld_quality_threshold=args.meld_quality_threshold,
    )
    assign_splits(kept_rows, seed=args.seed, train_ratio=args.train_ratio, valid_ratio=args.valid_ratio)
    columns = field_order(kept_rows)
    kept_rows.sort(key=lambda row: (normalize_text(row["biosemotic_split"]), normalize_text(row["source_dataset"]), normalize_text(row["sample_id"])))

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "biosemotic_dataset.csv", kept_rows, columns)
    for split_name in ("train", "valid", "test"):
        split_rows = [row for row in kept_rows if row["biosemotic_split"] == split_name]
        write_csv(output_dir / f"{split_name}.csv", split_rows, columns)

    report = build_report(kept_rows, filter_report, output_dir, args)
    (output_dir / "feature_columns.json").write_text(
        json.dumps({"columns": columns}, indent=2) + "\n",
        encoding="utf-8",
    )
    (output_dir / "filtering_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (output_dir / "filtering_report.md").write_text(build_markdown_report(report), encoding="utf-8")

    print(json.dumps({
        "retained_rows": len(kept_rows),
        "source_counts": report["dataset_summary"]["source_counts"],
        "split_counts": report["dataset_summary"]["split_counts"],
        "output_dir": str(output_dir),
    }, indent=2))


if __name__ == "__main__":
    main()
