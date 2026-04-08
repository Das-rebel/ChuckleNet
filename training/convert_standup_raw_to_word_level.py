#!/usr/bin/env python3
"""
Convert existing stand-up transcript files into the XLM-R word-level JSONL schema.

Input assumptions:
- transcript text files live under data/raw
- laughter tags are inline on their own lines, e.g. [laughter], [audience laughs]
- optional *_laughter.json files may exist with coarse taxonomy metadata
- optional alignment artifacts may exist, but this converter prefers transcript
  structure because the checked-in alignment outputs are sparse and partly
  simulated

Output schema:
{
  "example_id": "comedy_transcript_1_observational_seg_000",
  "language": "en",
  "comedian_id": "comedy_transcript_1_observational",
  "show_id": "comedy_transcript_1_observational",
  "words": [...],
  "labels": [...],
  "metadata": {
    "source_transcript": "...",
    "segment_index": 0,
    "next_laughter_tag": "[laughter]",
    "laughter_type": "continuous",
    "conversion_mode": "inline_tag_heuristic"
  }
}
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import DefaultDict, Dict, Iterable, List, Optional, Sequence, Set, Tuple


LAUGHTER_PATTERN = re.compile(r"^\s*\[.*?(?:laugh|laughter|chuckle|giggle).*?\]\s*$", re.IGNORECASE)
TOKEN_PATTERN = re.compile(r"[A-Za-z0-9]+(?:['-][A-Za-z0-9]+)*|['-][A-Za-z0-9]+|[^\w\s]")
TEXT_NORMALIZATION_TABLE = str.maketrans(
    {
        "\u2018": "'",
        "\u2019": "'",
        "\u201b": "'",
        "\u2032": "'",
        "\u00b4": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2013": "-",
        "\u2014": "-",
        "\u2212": "-",
        "\u2026": "...",
        "\u00a0": " ",
    }
)


@dataclass(slots=True)
class SpokenSegment:
    text: str
    next_laughter_tag: Optional[str]
    laughter_type: Optional[str]


@dataclass(slots=True)
class TranscriptBundle:
    transcript_path: Path
    laughter_meta_path: Optional[Path]
    transcript_id: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert raw stand-up transcripts to word-level JSONL.")
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=Path("/Users/Subho/autonomous_laughter_prediction/data/raw"),
        help="Directory containing transcript text files and *_laughter.json files.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("/Users/Subho/autonomous_laughter_prediction/data/training/standup_word_level"),
        help="Directory for train/valid/test JSONL output.",
    )
    parser.add_argument(
        "--context-lines",
        type=int,
        default=1,
        help="Number of previous spoken lines to prepend as context.",
    )
    parser.add_argument(
        "--context-token-policy",
        choices=("full", "lexical_tail", "clause_lexical_tail"),
        default="clause_lexical_tail",
        help="How to represent prepended context. 'full' keeps all previous-line tokens; 'lexical_tail' keeps only the last lexical context tokens; 'clause_lexical_tail' keeps only lexical tokens from the last non-empty clause of the previous line.",
    )
    parser.add_argument(
        "--context-tail-tokens",
        type=int,
        default=6,
        help="Number of lexical context tokens to keep when --context-token-policy is lexical_tail or clause_lexical_tail.",
    )
    parser.add_argument(
        "--min-words",
        type=int,
        default=3,
        help="Drop examples shorter than this many tokens after tokenization.",
    )
    parser.add_argument(
        "--valid-ratio",
        type=float,
        default=0.1,
        help="Validation split ratio at transcript level.",
    )
    parser.add_argument(
        "--test-ratio",
        type=float,
        default=0.1,
        help="Test split ratio at transcript level.",
    )
    parser.add_argument(
        "--split-strategy",
        choices=("overlap_safe", "wesr_balanced", "wesr_advanced"),
        default="overlap_safe",
        help="Component-level split strategy. 'overlap_safe' preserves the current count-targeted assignment; 'wesr_balanced' favors discrete/continuous coverage in valid/test; 'wesr_advanced' prioritizes stronger per-type support in valid/test for benchmark use.",
    )
    return parser.parse_args()


def discover_transcript_bundles(raw_dir: Path) -> List[TranscriptBundle]:
    bundles: List[TranscriptBundle] = []
    for transcript_path in sorted(raw_dir.glob("*.txt")):
        transcript_id = transcript_path.stem
        if transcript_id in {"sample_comedy", "test_comedy_transcript"}:
            continue
        laughter_meta_path = raw_dir / f"{transcript_id}_laughter.json"
        bundles.append(
            TranscriptBundle(
                transcript_path=transcript_path,
                laughter_meta_path=laughter_meta_path if laughter_meta_path.exists() else None,
                transcript_id=transcript_id,
            )
        )
    return bundles


def load_laughter_type_sequence(path: Optional[Path]) -> List[Tuple[str, Optional[str]]]:
    if path is None or not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    segments = payload.get("laughter_segments", [])
    sequence: List[Tuple[str, Optional[str]]] = []
    for item in segments:
        tag_text = str(item.get("text") or "").strip()
        laughter_type = item.get("type")
        if tag_text:
            sequence.append((tag_text, str(laughter_type) if laughter_type is not None else None))
    return sequence


def parse_transcript_segments(bundle: TranscriptBundle) -> List[SpokenSegment]:
    lines = [
        line.strip()
        for line in bundle.transcript_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    laughter_sequence = load_laughter_type_sequence(bundle.laughter_meta_path)
    laughter_index = 0
    segments: List[SpokenSegment] = []

    for index, line in enumerate(lines):
        if LAUGHTER_PATTERN.match(line):
            continue
        next_laughter_tag: Optional[str] = None
        laughter_type: Optional[str] = None
        if index + 1 < len(lines) and LAUGHTER_PATTERN.match(lines[index + 1]):
            next_laughter_tag = lines[index + 1]
            if laughter_index < len(laughter_sequence):
                _, laughter_type = laughter_sequence[laughter_index]
            laughter_index += 1
        segments.append(
            SpokenSegment(
                text=line,
                next_laughter_tag=next_laughter_tag,
                laughter_type=laughter_type,
            )
        )
    return segments


def normalize_text(text: str) -> str:
    return text.translate(TEXT_NORMALIZATION_TABLE)


def tokenize_text(text: str) -> List[str]:
    return TOKEN_PATTERN.findall(normalize_text(text))


def is_punctuation_token(token: str) -> bool:
    return bool(token) and all(not char.isalnum() for char in token)


def extract_last_non_empty_clause_tokens(context_words: Sequence[str]) -> List[str]:
    clause_tokens: List[List[str]] = [[]]
    for token in context_words:
        if is_punctuation_token(token):
            clause_tokens.append([])
            continue
        clause_tokens[-1].append(token)
    non_empty = [clause for clause in clause_tokens if clause]
    return list(non_empty[-1]) if non_empty else []


def apply_context_token_policy(
    context_words: Sequence[str],
    policy: str,
    context_tail_tokens: int,
) -> List[str]:
    if policy == "full":
        return list(context_words)
    if policy == "lexical_tail":
        lexical_words = [word for word in context_words if not is_punctuation_token(word)]
    elif policy == "clause_lexical_tail":
        lexical_words = extract_last_non_empty_clause_tokens(context_words)
    else:
        raise ValueError(f"Unsupported context token policy: {policy}")
    if context_tail_tokens <= 0:
        return []
    return lexical_words[-context_tail_tokens:]


def tokenization_profile(rows: Sequence[Dict[str, object]]) -> Dict[str, int]:
    standalone_apostrophe_examples = 0
    standalone_apostrophe_tokens = 0
    lexical_apostrophe_examples = 0
    lexical_apostrophe_tokens = 0

    for row in rows:
        words = [str(word) for word in row["words"]]
        if "'" in words:
            standalone_apostrophe_examples += 1
            standalone_apostrophe_tokens += words.count("'")
        lexical_with_apostrophe = [word for word in words if "'" in word and word != "'"]
        if lexical_with_apostrophe:
            lexical_apostrophe_examples += 1
            lexical_apostrophe_tokens += len(lexical_with_apostrophe)

    return {
        "standalone_apostrophe_examples": standalone_apostrophe_examples,
        "standalone_apostrophe_tokens": standalone_apostrophe_tokens,
        "lexical_apostrophe_examples": lexical_apostrophe_examples,
        "lexical_apostrophe_tokens": lexical_apostrophe_tokens,
    }


def example_signature(words: Sequence[str]) -> Tuple[str, ...]:
    return tuple(str(word).strip().lower() for word in words)


def build_examples(
    bundle: TranscriptBundle,
    segments: Sequence[SpokenSegment],
    context_lines: int,
    min_words: int,
    context_token_policy: str,
    context_tail_tokens: int,
) -> List[Dict[str, object]]:
    examples: List[Dict[str, object]] = []
    for index, segment in enumerate(segments):
        context_start = max(0, index - max(0, context_lines))
        context_segments = segments[context_start:index]
        context_words: List[str] = []
        for context_segment in context_segments:
            context_words.extend(tokenize_text(context_segment.text))
        context_words = apply_context_token_policy(
            context_words,
            policy=context_token_policy,
            context_tail_tokens=context_tail_tokens,
        )

        current_words = tokenize_text(segment.text)
        if len(current_words) < min_words:
            continue

        words = context_words + current_words
        labels = [0] * len(words)
        if segment.next_laughter_tag and current_words:
            # Mark the last token as positive (discourse boundary = laughter location)
            labels[-1] = 1

        examples.append(
            {
                "example_id": f"{bundle.transcript_id}_seg_{index:03d}",
                "language": "en",
                "comedian_id": bundle.transcript_id,
                "show_id": bundle.transcript_id,
                "words": words,
                "labels": labels,
                "metadata": {
                    "source_transcript": str(bundle.transcript_path),
                    "source_laughter_meta": str(bundle.laughter_meta_path) if bundle.laughter_meta_path else None,
                    "segment_index": index,
                    "next_laughter_tag": segment.next_laughter_tag,
                    "laughter_type": segment.laughter_type,
                    "conversion_mode": "inline_tag_heuristic",
                    "tokenization_mode": "dialect_aware_contraction_v1",
                    "context_token_policy": context_token_policy,
                    "context_tail_tokens": context_tail_tokens,
                    "current_segment_start": len(context_words),
                    "context_lines": context_lines,
                },
            }
        )
    return examples


def build_transcript_overlap_components(
    transcript_examples: Dict[str, List[Dict[str, object]]],
) -> Tuple[Dict[str, str], Dict[str, List[str]]]:
    parent: Dict[str, str] = {transcript_id: transcript_id for transcript_id in transcript_examples}

    def find(transcript_id: str) -> str:
        root = parent[transcript_id]
        while root != parent[root]:
            root = parent[root]
        while transcript_id != root:
            next_id = parent[transcript_id]
            parent[transcript_id] = root
            transcript_id = next_id
        return root

    def union(left: str, right: str) -> None:
        left_root = find(left)
        right_root = find(right)
        if left_root == right_root:
            return
        if left_root < right_root:
            parent[right_root] = left_root
        else:
            parent[left_root] = right_root

    signature_to_transcripts: DefaultDict[Tuple[str, ...], Set[str]] = defaultdict(set)
    for transcript_id, examples in transcript_examples.items():
        for row in examples:
            signature_to_transcripts[example_signature(row["words"])].add(transcript_id)

    for transcript_ids in signature_to_transcripts.values():
        transcript_list = sorted(transcript_ids)
        if len(transcript_list) < 2:
            continue
        first = transcript_list[0]
        for transcript_id in transcript_list[1:]:
            union(first, transcript_id)

    components: DefaultDict[str, List[str]] = defaultdict(list)
    transcript_to_component: Dict[str, str] = {}
    for transcript_id in sorted(transcript_examples):
        root = find(transcript_id)
        components[root].append(transcript_id)
        transcript_to_component[transcript_id] = root

    normalized_components = {
        root: sorted(transcript_ids)
        for root, transcript_ids in sorted(components.items(), key=lambda item: item[0])
    }
    return transcript_to_component, normalized_components


def stable_split_key(value: str) -> float:
    digest = hashlib.sha1(value.encode("utf-8")).hexdigest()[:8]
    return int(digest, 16) / 0xFFFFFFFF


def assign_split(transcript_id: str, valid_ratio: float, test_ratio: float) -> str:
    key = stable_split_key(transcript_id)
    if key < test_ratio:
        return "test"
    if key < test_ratio + valid_ratio:
        return "valid"
    return "train"


def aggregate_component_split_stats(
    assignment: Dict[str, str],
    component_example_counts: Dict[str, int],
    component_laughter_type_counts: Dict[str, Dict[str, int]],
) -> Dict[str, Dict[str, object]]:
    split_stats: Dict[str, Dict[str, object]] = {
        "train": {"example_count": 0, "laughter_type_counts": defaultdict(int)},
        "valid": {"example_count": 0, "laughter_type_counts": defaultdict(int)},
        "test": {"example_count": 0, "laughter_type_counts": defaultdict(int)},
    }
    for component_id, split in assignment.items():
        split_stats[split]["example_count"] += component_example_counts[component_id]
        laughter_counts = component_laughter_type_counts.get(component_id, {})
        for laughter_type, count in laughter_counts.items():
            split_stats[split]["laughter_type_counts"][laughter_type] += count
    return {
        split: {
            "example_count": int(payload["example_count"]),
            "laughter_type_counts": dict(sorted(payload["laughter_type_counts"].items())),
        }
        for split, payload in split_stats.items()
    }


def split_coverage_penalty(split_stats: Dict[str, Dict[str, object]]) -> int:
    penalty = 0
    for split in ("valid", "test"):
        counts = split_stats[split]["laughter_type_counts"]
        if int(counts.get("discrete", 0)) == 0:
            penalty += 1
        if int(counts.get("continuous", 0)) == 0:
            penalty += 1
    return penalty


def split_min_type_support(split_stats: Dict[str, Dict[str, object]]) -> int:
    supports: List[int] = []
    for split in ("valid", "test"):
        counts = split_stats[split]["laughter_type_counts"]
        supports.append(int(counts.get("continuous", 0)))
        supports.append(int(counts.get("discrete", 0)))
    return min(supports) if supports else 0


def split_total_eval_examples(split_stats: Dict[str, Dict[str, object]]) -> int:
    return int(split_stats["valid"]["example_count"]) + int(split_stats["test"]["example_count"])


def split_count_penalty(
    split_stats: Dict[str, Dict[str, object]],
    valid_target: float,
    test_target: float,
) -> float:
    return abs(float(split_stats["valid"]["example_count"]) - valid_target) + abs(
        float(split_stats["test"]["example_count"]) - test_target
    )


def assign_component_splits(
    component_example_counts: Dict[str, int],
    valid_ratio: float,
    test_ratio: float,
    component_laughter_type_counts: Optional[Dict[str, Dict[str, int]]] = None,
    split_strategy: str = "overlap_safe",
) -> Dict[str, str]:
    component_ids = sorted(component_example_counts)
    total_examples = sum(component_example_counts.values())
    target_counts = {
        "valid": total_examples * valid_ratio,
        "test": total_examples * test_ratio,
    }
    require_valid = valid_ratio > 0
    require_test = test_ratio > 0
    component_laughter_type_counts = component_laughter_type_counts or {}

    def assignment_score(assignment: Dict[str, str]) -> Tuple[float, float, float, str]:
        split_stats = aggregate_component_split_stats(
            assignment,
            component_example_counts=component_example_counts,
            component_laughter_type_counts=component_laughter_type_counts,
        )
        count_penalty = split_count_penalty(split_stats, target_counts["valid"], target_counts["test"])
        if split_strategy == "wesr_advanced":
            return (
                float(split_coverage_penalty(split_stats)),
                -float(split_min_type_support(split_stats)),
                -float(split_total_eval_examples(split_stats)),
                count_penalty,
                json.dumps(assignment, sort_keys=True),
            )
        if split_strategy == "wesr_balanced":
            return (
                float(split_coverage_penalty(split_stats)),
                count_penalty,
                abs(float(split_stats["valid"]["example_count"]) - target_counts["valid"])
                + abs(float(split_stats["test"]["example_count"]) - target_counts["test"]),
                json.dumps(assignment, sort_keys=True),
            )
        return (
            count_penalty,
            abs(float(split_stats["valid"]["example_count"]) - target_counts["valid"]),
            abs(float(split_stats["test"]["example_count"]) - target_counts["test"]),
            json.dumps(assignment, sort_keys=True),
        )

    if len(component_ids) <= 15:
        best_assignment: Optional[Dict[str, str]] = None
        best_score: Optional[Tuple[float, float, float, str]] = None

        def recurse(
            index: int,
            current: Dict[str, str],
            counts: Dict[str, int],
            split_component_counts: Dict[str, int],
        ) -> None:
            nonlocal best_assignment, best_score
            if index == len(component_ids):
                if split_component_counts["train"] == 0:
                    return
                if require_valid and split_component_counts["valid"] == 0:
                    return
                if require_test and split_component_counts["test"] == 0:
                    return

                score = assignment_score(current)
                if best_score is None or score < best_score:
                    best_score = score
                    best_assignment = dict(current)
                return

            component_id = component_ids[index]
            examples = component_example_counts[component_id]
            for split in ("train", "valid", "test"):
                current[component_id] = split
                counts[split] += examples
                split_component_counts[split] += 1
                recurse(index + 1, current, counts, split_component_counts)
                split_component_counts[split] -= 1
                counts[split] -= examples
                del current[component_id]

        recurse(
            0,
            current={},
            counts={"train": 0, "valid": 0, "test": 0},
            split_component_counts={"train": 0, "valid": 0, "test": 0},
        )
        if best_assignment is not None:
            return best_assignment

    ordered_ids = sorted(component_ids, key=lambda item: (-component_example_counts[item], item))
    assignment: Dict[str, str] = {}
    split_counts = {"train": 0, "valid": 0, "test": 0}
    split_component_counts = {"train": 0, "valid": 0, "test": 0}
    split_laughter_type_counts: Dict[str, DefaultDict[str, int]] = {
        "train": defaultdict(int),
        "valid": defaultdict(int),
        "test": defaultdict(int),
    }

    for component_id in ordered_ids:
        candidates = ["train", "valid", "test"]
        if require_valid and split_component_counts["valid"] == 0:
            candidates = ["valid", "test", "train"]
        elif require_test and split_component_counts["test"] == 0:
            candidates = ["test", "valid", "train"]

        best_split = "train"
        best_score: Optional[Tuple[float, float, str]] = None
        examples = component_example_counts[component_id]
        for split in candidates:
            split_stats = {
                name: {
                    "example_count": split_counts[name],
                    "laughter_type_counts": dict(split_laughter_type_counts[name]),
                }
                for name in ("train", "valid", "test")
            }
            split_stats[split]["example_count"] += examples
            for laughter_type, count in component_laughter_type_counts.get(component_id, {}).items():
                split_stats[split]["laughter_type_counts"][laughter_type] = (
                    int(split_stats[split]["laughter_type_counts"].get(laughter_type, 0)) + count
                )
            count_penalty = split_count_penalty(split_stats, target_counts["valid"], target_counts["test"])
            if split_strategy == "wesr_advanced":
                score = (
                    float(split_coverage_penalty(split_stats)),
                    -float(split_min_type_support(split_stats)),
                    -float(split_total_eval_examples(split_stats)),
                    count_penalty,
                    split,
                )
            elif split_strategy == "wesr_balanced":
                score = (float(split_coverage_penalty(split_stats)), count_penalty, split)
            else:
                score = (count_penalty, abs(float(split_stats["valid"]["example_count"]) - target_counts["valid"]), split)
            if best_score is None or score < best_score:
                best_score = score
                best_split = split
        assignment[component_id] = best_split
        split_counts[best_split] += examples
        split_component_counts[best_split] += 1
        for laughter_type, count in component_laughter_type_counts.get(component_id, {}).items():
            split_laughter_type_counts[best_split][laughter_type] += count

    return assignment


def write_jsonl(path: Path, rows: Iterable[Dict[str, object]]) -> int:
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=True) + "\n")
            count += 1
    return count


def convert_dataset(
    raw_dir: Path,
    output_dir: Path,
    context_lines: int,
    min_words: int,
    valid_ratio: float,
    test_ratio: float,
    split_strategy: str,
    context_token_policy: str,
    context_tail_tokens: int,
) -> Dict[str, object]:
    bundles = discover_transcript_bundles(raw_dir)
    split_rows: Dict[str, List[Dict[str, object]]] = {"train": [], "valid": [], "test": []}
    transcript_counts: Dict[str, int] = {"train": 0, "valid": 0, "test": 0}
    transcript_examples: Dict[str, List[Dict[str, object]]] = {}

    for bundle in bundles:
        segments = parse_transcript_segments(bundle)
        examples = build_examples(
            bundle,
            segments,
            context_lines=context_lines,
            min_words=min_words,
            context_token_policy=context_token_policy,
            context_tail_tokens=context_tail_tokens,
        )
        transcript_examples[bundle.transcript_id] = examples

    transcript_to_component, components = build_transcript_overlap_components(transcript_examples)
    component_example_counts = {
        component_id: sum(len(transcript_examples[transcript_id]) for transcript_id in transcript_ids)
        for component_id, transcript_ids in components.items()
    }
    def laughter_type_counts(rows: Sequence[Dict[str, object]]) -> Dict[str, int]:
        counts: DefaultDict[str, int] = defaultdict(int)
        for row in rows:
            metadata = row.get("metadata") or {}
            laughter_type = str(metadata.get("laughter_type") or "unknown")
            counts[laughter_type] += 1
        return dict(sorted(counts.items()))

    component_laughter_type_counts = {
        component_id: laughter_type_counts(
            [row for transcript_id in transcript_ids for row in transcript_examples[transcript_id]]
        )
        for component_id, transcript_ids in components.items()
    }
    component_split_map = assign_component_splits(
        component_example_counts,
        valid_ratio=valid_ratio,
        test_ratio=test_ratio,
        component_laughter_type_counts=component_laughter_type_counts,
        split_strategy=split_strategy,
    )

    for bundle in bundles:
        component_id = transcript_to_component[bundle.transcript_id]
        split = component_split_map[component_id]
        examples = transcript_examples[bundle.transcript_id]
        split_rows[split].extend(examples)
        transcript_counts[split] += 1

    def exact_overlap_count(left_rows: Sequence[Dict[str, object]], right_rows: Sequence[Dict[str, object]]) -> int:
        left_signatures = {example_signature(row["words"]) for row in left_rows}
        right_signatures = {example_signature(row["words"]) for row in right_rows}
        return len(left_signatures & right_signatures)

    output_dir.mkdir(parents=True, exist_ok=True)
    counts = {
        split: write_jsonl(output_dir / f"{split}.jsonl", rows)
        for split, rows in split_rows.items()
    }

    summary = {
        "raw_dir": str(raw_dir),
        "output_dir": str(output_dir),
        "transcript_counts": transcript_counts,
        "example_counts": counts,
        "context_lines": context_lines,
        "context_token_policy": context_token_policy,
        "context_tail_tokens": context_tail_tokens,
        "min_words": min_words,
        "valid_ratio": valid_ratio,
        "test_ratio": test_ratio,
        "split_strategy": split_strategy,
        "conversion_mode": "inline_tag_heuristic",
        "tokenization_mode": "dialect_aware_contraction_v1",
        "overlap_component_count": len(components),
        "largest_overlap_component_size": max((len(items) for items in components.values()), default=0),
        "component_example_counts": component_example_counts,
        "component_laughter_type_counts": component_laughter_type_counts,
        "component_split_map": component_split_map,
        "split_laughter_type_counts": {
            split: laughter_type_counts(rows)
            for split, rows in split_rows.items()
        },
        "exact_overlap_counts": {
            "train_valid": exact_overlap_count(split_rows["train"], split_rows["valid"]),
            "train_test": exact_overlap_count(split_rows["train"], split_rows["test"]),
            "valid_test": exact_overlap_count(split_rows["valid"], split_rows["test"]),
        },
        "tokenization_profile": {
            split: tokenization_profile(rows)
            for split, rows in split_rows.items()
        },
    }
    (output_dir / "conversion_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    args = parse_args()
    summary = convert_dataset(
        raw_dir=args.raw_dir,
        output_dir=args.output_dir,
        context_lines=args.context_lines,
        context_token_policy=args.context_token_policy,
        context_tail_tokens=args.context_tail_tokens,
        min_words=args.min_words,
        valid_ratio=args.valid_ratio,
        test_ratio=args.test_ratio,
        split_strategy=args.split_strategy,
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
