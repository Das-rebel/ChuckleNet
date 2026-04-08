#!/usr/bin/env python3
"""
Analyze overlap-safe split assignments for WESR-style laughter taxonomy balance.

This script does not change the canonical dataset split. It evaluates all
component-level assignments and reports whether a better discrete/continuous
coverage tradeoff exists without reintroducing transcript overlap.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from itertools import product
from pathlib import Path
from typing import Any, Dict, List, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from training.convert_standup_raw_to_word_level import (
    assign_component_splits,
    build_examples,
    build_transcript_overlap_components,
    discover_transcript_bundles,
    parse_transcript_segments,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze WESR laughter-type balance across overlap-safe splits.")
    parser.add_argument("--raw-dir", type=Path, required=True)
    parser.add_argument("--report-file", type=Path, default=None)
    parser.add_argument("--summary-file", type=Path, default=None)
    parser.add_argument("--context-lines", type=int, default=1)
    parser.add_argument("--min-words", type=int, default=3)
    parser.add_argument("--valid-ratio", type=float, default=0.1)
    parser.add_argument("--test-ratio", type=float, default=0.1)
    return parser.parse_args()


def component_stats(
    raw_dir: Path,
    context_lines: int,
    min_words: int,
) -> Dict[str, Dict[str, Any]]:
    bundles = discover_transcript_bundles(raw_dir)
    transcript_examples: Dict[str, List[Dict[str, object]]] = {}
    for bundle in bundles:
        segments = parse_transcript_segments(bundle)
        transcript_examples[bundle.transcript_id] = build_examples(
            bundle,
            segments,
            context_lines=context_lines,
            min_words=min_words,
        )

    _, components = build_transcript_overlap_components(transcript_examples)
    stats: Dict[str, Dict[str, Any]] = {}
    for component_id, transcript_ids in sorted(components.items()):
        counts = Counter()
        total = 0
        for transcript_id in transcript_ids:
            for row in transcript_examples[transcript_id]:
                total += 1
                laughter_type = str((row.get("metadata") or {}).get("laughter_type") or "unknown")
                counts[laughter_type] += 1
        stats[component_id] = {
            "transcript_ids": transcript_ids,
            "example_count": total,
            "laughter_type_counts": dict(sorted(counts.items())),
        }
    return stats


def aggregate_split_stats(
    assignment: Dict[str, str],
    stats: Dict[str, Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    split_counts = {
        "train": {"example_count": 0, "laughter_type_counts": Counter()},
        "valid": {"example_count": 0, "laughter_type_counts": Counter()},
        "test": {"example_count": 0, "laughter_type_counts": Counter()},
    }
    for component_id, split in assignment.items():
        split_counts[split]["example_count"] += int(stats[component_id]["example_count"])
        split_counts[split]["laughter_type_counts"].update(stats[component_id]["laughter_type_counts"])
    return {
        split: {
            "example_count": payload["example_count"],
            "laughter_type_counts": dict(sorted(payload["laughter_type_counts"].items())),
        }
        for split, payload in split_counts.items()
    }


def coverage_penalty(split_stats: Dict[str, Dict[str, Any]]) -> int:
    penalty = 0
    for split in ("valid", "test"):
        counts = split_stats[split]["laughter_type_counts"]
        if counts.get("discrete", 0) == 0:
            penalty += 1
        if counts.get("continuous", 0) == 0:
            penalty += 1
    return penalty


def count_penalty(
    split_stats: Dict[str, Dict[str, Any]],
    valid_target: float,
    test_target: float,
) -> float:
    return abs(split_stats["valid"]["example_count"] - valid_target) + abs(split_stats["test"]["example_count"] - test_target)


def enumerate_assignments(
    stats: Dict[str, Dict[str, Any]],
    valid_ratio: float,
    test_ratio: float,
) -> List[Dict[str, Any]]:
    component_ids = sorted(stats)
    total_examples = sum(int(item["example_count"]) for item in stats.values())
    valid_target = total_examples * valid_ratio
    test_target = total_examples * test_ratio
    results: List[Dict[str, Any]] = []

    for splits in product(("train", "valid", "test"), repeat=len(component_ids)):
        assignment = dict(zip(component_ids, splits))
        if set(assignment.values()) != {"train", "valid", "test"}:
            continue
        split_stats = aggregate_split_stats(assignment, stats)
        result = {
            "assignment": assignment,
            "split_stats": split_stats,
            "coverage_penalty": coverage_penalty(split_stats),
            "count_penalty": count_penalty(split_stats, valid_target, test_target),
        }
        results.append(result)
    results.sort(
        key=lambda item: (
            item["coverage_penalty"],
            item["count_penalty"],
            json.dumps(item["assignment"], sort_keys=True),
        )
    )
    return results


def render_report(summary: Dict[str, Any]) -> str:
    lines = [
        "# WESR Split Balance",
        "",
        "This report compares the current overlap-safe split assignment against the best assignment that also favors discrete/continuous coverage in validation and test.",
        "",
        "## Current assignment",
        "",
        f"- coverage penalty: `{summary['current_assignment']['coverage_penalty']}`",
        f"- count penalty: `{summary['current_assignment']['count_penalty']:.1f}`",
        f"- split stats: `{json.dumps(summary['current_assignment']['split_stats'], sort_keys=True)}`",
        "",
        "## Recommended assignment",
        "",
        f"- coverage penalty: `{summary['recommended_assignment']['coverage_penalty']}`",
        f"- count penalty: `{summary['recommended_assignment']['count_penalty']:.1f}`",
        f"- split stats: `{json.dumps(summary['recommended_assignment']['split_stats'], sort_keys=True)}`",
        f"- component map: `{json.dumps(summary['recommended_assignment']['assignment'], sort_keys=True)}`",
        "",
        "## Interpretation",
        "",
        summary["interpretation"],
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    stats = component_stats(args.raw_dir, context_lines=args.context_lines, min_words=args.min_words)
    component_example_counts = {
        component_id: int(payload["example_count"])
        for component_id, payload in stats.items()
    }
    current_assignment = assign_component_splits(
        component_example_counts,
        valid_ratio=args.valid_ratio,
        test_ratio=args.test_ratio,
    )
    current_split_stats = aggregate_split_stats(current_assignment, stats)
    total_examples = sum(component_example_counts.values())
    valid_target = total_examples * args.valid_ratio
    test_target = total_examples * args.test_ratio

    all_assignments = enumerate_assignments(stats, valid_ratio=args.valid_ratio, test_ratio=args.test_ratio)
    recommended = all_assignments[0]

    interpretation = (
        "A better WESR-balanced overlap-safe split exists and should be considered before using discrete/continuous metrics as a promotion gate."
        if recommended["coverage_penalty"] < coverage_penalty(current_split_stats)
        else "The current overlap-safe split is already as good as possible for discrete/continuous coverage under the current component constraints."
    )

    summary = {
        "component_stats": stats,
        "current_assignment": {
            "assignment": current_assignment,
            "split_stats": current_split_stats,
            "coverage_penalty": coverage_penalty(current_split_stats),
            "count_penalty": count_penalty(current_split_stats, valid_target, test_target),
        },
        "recommended_assignment": recommended,
        "interpretation": interpretation,
    }

    if args.summary_file is not None:
        args.summary_file.parent.mkdir(parents=True, exist_ok=True)
        args.summary_file.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    if args.report_file is not None:
        args.report_file.parent.mkdir(parents=True, exist_ok=True)
        args.report_file.write_text(render_report(summary), encoding="utf-8")

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
