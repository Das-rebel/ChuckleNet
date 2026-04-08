#!/usr/bin/env python3
"""
Audit how teacher-refined labels differ from the weak-label training set.

This script compares:
- the weak-label training file
- the refined training file
- the teacher audit log

It summarizes keep/drop rates, target-index movement, label-position drift, and
token-category shifts so we can explain why the refined-label run collapsed.
"""

from __future__ import annotations

import argparse
import json
import statistics
import string
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence


STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "but",
    "by",
    "for",
    "from",
    "he",
    "her",
    "him",
    "i",
    "if",
    "in",
    "is",
    "it",
    "its",
    "me",
    "my",
    "not",
    "of",
    "on",
    "or",
    "our",
    "she",
    "so",
    "that",
    "the",
    "their",
    "them",
    "there",
    "they",
    "this",
    "to",
    "us",
    "was",
    "we",
    "what",
    "who",
    "why",
    "you",
    "your",
}


@dataclass(slots=True)
class ExampleRecord:
    example_id: str
    words: List[str]
    positive_index: Optional[int]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit refined-label shifts against the weak-label baseline.")
    parser.add_argument("--weak-file", type=Path, required=True)
    parser.add_argument("--refined-file", type=Path, required=True)
    parser.add_argument("--audit-file", type=Path, required=True)
    parser.add_argument("--report-file", type=Path, default=None)
    parser.add_argument("--summary-file", type=Path, default=None)
    parser.add_argument("--sample-limit", type=int, default=8)
    return parser.parse_args()


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def positive_index(labels: Sequence[Any]) -> Optional[int]:
    for index, label in enumerate(labels):
        if int(label) == 1:
            return index
    return None


def load_examples(path: Path) -> Dict[str, ExampleRecord]:
    records: Dict[str, ExampleRecord] = {}
    for row in load_jsonl(path):
        example_id = str(row["example_id"])
        words = [str(word) for word in row["words"]]
        records[example_id] = ExampleRecord(
            example_id=example_id,
            words=words,
            positive_index=positive_index(row["labels"]),
        )
    return records


def safe_token(words: Sequence[str], index: Optional[int]) -> Optional[str]:
    if index is None or index < 0 or index >= len(words):
        return None
    return str(words[index])


def classify_token(token: Optional[str]) -> str:
    if token is None:
        return "missing"
    stripped = token.strip()
    if not stripped:
        return "empty"
    if all(char in string.punctuation for char in stripped):
        return "punctuation"
    lowered = stripped.lower()
    if lowered in STOPWORDS:
        return "stopword"
    if any(char.isalpha() for char in stripped):
        return "lexical"
    if any(char.isdigit() for char in stripped):
        return "numeric"
    return "other"


def position_ratio(index: Optional[int], length: int) -> Optional[float]:
    if index is None or length <= 0:
        return None
    if length == 1:
        return 1.0
    return index / float(length - 1)


def mean_or_none(values: Iterable[float]) -> Optional[float]:
    items = list(values)
    if not items:
        return None
    return statistics.mean(items)


def median_or_none(values: Iterable[float]) -> Optional[float]:
    items = list(values)
    if not items:
        return None
    return statistics.median(items)


def top_counter(counter: Counter[str], limit: int = 10) -> List[Dict[str, Any]]:
    return [{"value": value, "count": count} for value, count in counter.most_common(limit)]


def format_top_items(items: Sequence[Dict[str, Any]], limit: int) -> str:
    selected = items[:limit]
    if not selected:
        return "n/a"
    return ", ".join(f"{item['value']} ({item['count']})" for item in selected)


def percent(part: int, whole: int) -> float:
    if whole <= 0:
        return 0.0
    return (part / whole) * 100.0


def analyze(
    weak_examples: Dict[str, ExampleRecord],
    refined_examples: Dict[str, ExampleRecord],
    audit_rows: Sequence[Dict[str, Any]],
    sample_limit: int,
) -> Dict[str, Any]:
    weak_token_counter: Counter[str] = Counter()
    refined_token_counter: Counter[str] = Counter()
    weak_category_counter: Counter[str] = Counter()
    refined_category_counter: Counter[str] = Counter()
    keep_reason_counter: Counter[str] = Counter()
    drop_reason_counter: Counter[str] = Counter()
    keep_confidences: List[float] = []
    drop_confidences: List[float] = []
    shifts: List[int] = []
    absolute_shifts: List[int] = []
    weak_position_ratios: List[float] = []
    refined_position_ratios: List[float] = []
    suspicious_moves: List[Dict[str, Any]] = []

    unchanged = 0
    moved = 0
    moved_to_punctuation = 0
    moved_to_stopword = 0
    weak_punctuation = 0
    refined_punctuation = 0
    dropped = 0
    kept = 0

    for audit_row in audit_rows:
        example_id = str(audit_row["example_id"])
        decision = audit_row.get("decision") or {}
        weak_record = weak_examples.get(example_id)
        refined_record = refined_examples.get(example_id)

        if weak_record is None:
            continue

        weak_index = weak_record.positive_index
        weak_token = safe_token(weak_record.words, weak_index)
        weak_category = classify_token(weak_token)
        weak_ratio = position_ratio(weak_index, len(weak_record.words))
        if weak_ratio is not None:
            weak_position_ratios.append(weak_ratio)
        weak_token_counter[(weak_token or "<missing>").lower()] += 1
        weak_category_counter[weak_category] += 1
        if weak_category == "punctuation":
            weak_punctuation += 1

        kept_flag = bool(audit_row.get("kept"))
        reason_tags = [str(tag) for tag in decision.get("reason_tags", [])]
        confidence = float(decision.get("confidence") or 0.0)

        if kept_flag and refined_record is not None:
            kept += 1
            keep_confidences.append(confidence)
            keep_reason_counter.update(reason_tags)

            refined_index = refined_record.positive_index
            refined_token = safe_token(refined_record.words, refined_index)
            refined_category = classify_token(refined_token)
            refined_ratio = position_ratio(refined_index, len(refined_record.words))
            if refined_ratio is not None:
                refined_position_ratios.append(refined_ratio)
            refined_token_counter[(refined_token or "<missing>").lower()] += 1
            refined_category_counter[refined_category] += 1
            if refined_category == "punctuation":
                refined_punctuation += 1

            if weak_index == refined_index:
                unchanged += 1
            else:
                moved += 1
                if weak_index is not None and refined_index is not None:
                    delta = refined_index - weak_index
                    shifts.append(delta)
                    absolute_shifts.append(abs(delta))
                if refined_category == "punctuation":
                    moved_to_punctuation += 1
                if refined_category == "stopword":
                    moved_to_stopword += 1
                if refined_category in {"punctuation", "stopword"}:
                    suspicious_moves.append(
                        {
                            "example_id": example_id,
                            "weak_index": weak_index,
                            "weak_token": weak_token,
                            "refined_index": refined_index,
                            "refined_token": refined_token,
                            "refined_category": refined_category,
                            "confidence": confidence,
                            "reason_tags": reason_tags,
                            "note": str(decision.get("note") or ""),
                        }
                    )
        else:
            dropped += 1
            drop_confidences.append(confidence)
            drop_reason_counter.update(reason_tags)

    suspicious_moves.sort(
        key=lambda item: (
            0 if item["refined_category"] == "punctuation" else 1,
            -item["confidence"],
            item["example_id"],
        )
    )

    total_audited = kept + dropped
    summary = {
        "totals": {
            "weak_examples": len(weak_examples),
            "audited_examples": total_audited,
            "refined_examples": len(refined_examples),
            "kept_examples": kept,
            "dropped_examples": dropped,
            "keep_rate_pct": round(percent(kept, total_audited), 2),
            "drop_rate_pct": round(percent(dropped, total_audited), 2),
        },
        "target_shift": {
            "unchanged_examples": unchanged,
            "moved_examples": moved,
            "moved_rate_within_kept_pct": round(percent(moved, kept), 2),
            "avg_signed_shift_tokens": round(mean_or_none(shifts) or 0.0, 3),
            "median_signed_shift_tokens": round(median_or_none(shifts) or 0.0, 3),
            "avg_absolute_shift_tokens": round(mean_or_none(absolute_shifts) or 0.0, 3),
            "median_absolute_shift_tokens": round(median_or_none(absolute_shifts) or 0.0, 3),
        },
        "position_drift": {
            "weak_avg_position_ratio": round(mean_or_none(weak_position_ratios) or 0.0, 4),
            "refined_avg_position_ratio": round(mean_or_none(refined_position_ratios) or 0.0, 4),
        },
        "token_categories": {
            "weak": dict(weak_category_counter),
            "refined": dict(refined_category_counter),
            "weak_punctuation_pct": round(percent(weak_punctuation, len(weak_examples)), 2),
            "refined_punctuation_pct": round(percent(refined_punctuation, kept), 2),
            "moved_to_punctuation": moved_to_punctuation,
            "moved_to_stopword": moved_to_stopword,
        },
        "confidence": {
            "keep_avg": round(mean_or_none(keep_confidences) or 0.0, 4),
            "drop_avg": round(mean_or_none(drop_confidences) or 0.0, 4),
        },
        "top_tokens": {
            "weak": top_counter(weak_token_counter),
            "refined": top_counter(refined_token_counter),
        },
        "reason_tags": {
            "keep": top_counter(keep_reason_counter),
            "drop": top_counter(drop_reason_counter),
        },
        "suspicious_moves": suspicious_moves[:sample_limit],
    }
    return summary


def render_report(summary: Dict[str, Any]) -> str:
    totals = summary["totals"]
    shifts = summary["target_shift"]
    positions = summary["position_drift"]
    categories = summary["token_categories"]
    reasons = summary["reason_tags"]
    suspicious_moves = summary["suspicious_moves"]

    lines = [
        "# Refined Label Audit",
        "",
        "This report compares the weak-label training set against the teacher-refined set and audit log.",
        "",
        "## Summary",
        "",
        f"- Weak examples: `{totals['weak_examples']}`",
        f"- Audited examples: `{totals['audited_examples']}`",
        f"- Refined examples kept: `{totals['kept_examples']}` ({totals['keep_rate_pct']}%)",
        f"- Examples dropped: `{totals['dropped_examples']}` ({totals['drop_rate_pct']}%)",
        f"- Kept examples with moved target index: `{shifts['moved_examples']}` ({shifts['moved_rate_within_kept_pct']}% of kept examples)",
        f"- Average absolute target shift: `{shifts['avg_absolute_shift_tokens']}` tokens",
        f"- Weak average target position ratio: `{positions['weak_avg_position_ratio']}`",
        f"- Refined average target position ratio: `{positions['refined_avg_position_ratio']}`",
        f"- Weak punctuation targets: `{categories['weak_punctuation_pct']}%`",
        f"- Refined punctuation targets: `{categories['refined_punctuation_pct']}%`",
        f"- Moved targets landing on punctuation: `{categories['moved_to_punctuation']}`",
        f"- Moved targets landing on stopwords: `{categories['moved_to_stopword']}`",
        "",
        "## Top Teacher Reason Tags",
        "",
        f"- Keep: `{format_top_items(reasons['keep'], 5)}`",
        f"- Drop: `{format_top_items(reasons['drop'], 5)}`",
        "",
        "## Top Positive Tokens",
        "",
        f"- Weak: `{format_top_items(summary['top_tokens']['weak'], 8)}`",
        f"- Refined: `{format_top_items(summary['top_tokens']['refined'], 8)}`",
        "",
        "## Suspicious Moved Targets",
        "",
    ]

    if not suspicious_moves:
        lines.append("- No suspicious punctuation/stopword moves found.")
    else:
        for item in suspicious_moves:
            lines.append(
                "- "
                f"`{item['example_id']}` weak `{item['weak_token']}`@{item['weak_index']} -> "
                f"refined `{item['refined_token']}`@{item['refined_index']} "
                f"({item['refined_category']}, confidence={item['confidence']}, "
                f"tags={','.join(item['reason_tags']) or 'n/a'})"
            )
            if item["note"]:
                lines.append(f"  note: {item['note']}")

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- If punctuation or stopword targets rise sharply, the teacher is likely relocating positives onto syntactically weak trigger positions.",
            "- If many kept examples move the target index, the refined set is not just filtering examples; it is changing the supervision geometry the model learns from.",
            "- If the refined average position shifts earlier in the sentence, that is consistent with recall loss when weak labels were originally anchored near laughter-adjacent endings.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    weak_examples = load_examples(args.weak_file)
    refined_examples = load_examples(args.refined_file)
    audit_rows = load_jsonl(args.audit_file)
    summary = analyze(weak_examples, refined_examples, audit_rows, sample_limit=args.sample_limit)

    if args.summary_file is not None:
        args.summary_file.parent.mkdir(parents=True, exist_ok=True)
        args.summary_file.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    report = render_report(summary)
    if args.report_file is not None:
        args.report_file.parent.mkdir(parents=True, exist_ok=True)
        args.report_file.write_text(report, encoding="utf-8")

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
