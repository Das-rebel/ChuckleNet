#!/usr/bin/env python3
"""
Analyze unresolved moved-teacher cases after safe-hybrid note repair.

This script explains what still fails after the current guarded repair path so
future work can target the real remaining error modes instead of repeating
already-solved punctuation/quote issues.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from training.build_safe_hybrid_dataset import (  # noqa: E402
    choose_note_repair_index,
    classify_token,
    load_jsonl,
    positive_index,
    safe_token,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze unresolved moved teacher targets after note repair.")
    parser.add_argument("--weak-file", type=Path, required=True)
    parser.add_argument("--refined-file", type=Path, required=True)
    parser.add_argument("--audit-file", type=Path, required=True)
    parser.add_argument("--min-confidence", type=float, default=0.9)
    parser.add_argument("--max-note-repair-shift", type=int, default=16)
    parser.add_argument("--summary-file", type=Path, default=None)
    parser.add_argument("--report-file", type=Path, default=None)
    return parser.parse_args()


def unresolved_cases(
    weak_file: Path,
    refined_file: Path,
    audit_file: Path,
    min_confidence: float,
    max_note_repair_shift: int,
) -> List[Dict[str, Any]]:
    weak_rows = load_jsonl(weak_file)
    refined_rows = load_jsonl(refined_file)
    audit_rows = load_jsonl(audit_file)

    refined_by_id = {str(row["example_id"]): row for row in refined_rows}
    audit_by_id = {str(row["example_id"]): row for row in audit_rows}
    rows: List[Dict[str, Any]] = []

    for weak_row in weak_rows:
        example_id = str(weak_row["example_id"])
        audit_row = audit_by_id.get(example_id)
        if audit_row is None or not audit_row.get("kept"):
            continue

        refined_row = refined_by_id.get(example_id)
        if refined_row is None:
            continue

        weak_index = positive_index(weak_row.get("labels", []))
        refined_index = positive_index(refined_row.get("labels", []))
        if weak_index == refined_index:
            continue

        decision = audit_row.get("decision") or {}
        confidence = float(decision.get("confidence") or 0.0)
        note = str(decision.get("note") or "")
        refined_token = safe_token(refined_row.get("words", []), refined_index)
        refined_category = classify_token(refined_token)

        note_repair_index, note_repair_span = choose_note_repair_index(
            words=refined_row.get("words", []),
            note=note,
            weak_index=weak_index,
        )
        note_repair_shift: Optional[int] = None
        if note_repair_index is not None and weak_index is not None:
            note_repair_shift = abs(note_repair_index - weak_index)
        note_repair_token = safe_token(refined_row.get("words", []), note_repair_index)
        note_repair_category = classify_token(note_repair_token)

        note_repair_accepted = (
            note_repair_index is not None
            and note_repair_shift is not None
            and note_repair_shift <= max_note_repair_shift
            and confidence >= min_confidence
            and note_repair_category == "lexical"
        )
        if note_repair_accepted:
            continue

        if refined_category == "lexical" and confidence >= min_confidence:
            continue

        rows.append(
            {
                "example_id": example_id,
                "weak_index": weak_index,
                "weak_word": safe_token(weak_row.get("words", []), weak_index),
                "refined_index": refined_index,
                "refined_word": refined_token,
                "refined_category": refined_category,
                "confidence": confidence,
                "note": note,
                "note_repair_index": note_repair_index,
                "note_repair_word": note_repair_token,
                "note_repair_category": note_repair_category,
                "note_repair_shift": note_repair_shift,
                "note_repair_span": note_repair_span,
                "words": list(weak_row.get("words", [])),
            }
        )

    return rows


def build_summary(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    refined_categories = Counter(str(row["refined_category"]) for row in rows)
    quoted_note_targets = Counter()
    weak_words = Counter()
    template_texts = Counter()

    for row in rows:
        note = str(row["note"])
        weak_words[str(row["weak_word"]).lower()] += 1
        template_texts[" ".join(row["words"])] += 1
        if row.get("note_repair_span"):
            quoted_note_targets[str(row["note_repair_span"]).lower()] += 1
        else:
            # Recover the original stopword quote when no repair span is usable.
            parts = note.split("'")
            if len(parts) >= 3:
                quoted_note_targets[parts[1].lower()] += 1
            else:
                quoted_note_targets["<none>"] += 1

    top_examples = [
        {
            "example_id": row["example_id"],
            "weak_word": row["weak_word"],
            "refined_word": row["refined_word"],
            "note": row["note"],
        }
        for row in rows[:5]
    ]

    interpretation = "No unresolved moved-teacher cases remain after the current note-repair policy."
    if rows:
        dominant_target = quoted_note_targets.most_common(1)[0][0]
        dominant_template = template_texts.most_common(1)[0][0]
        dominant_category = refined_categories.most_common(1)[0][0]
        interpretation = (
            "The remaining unresolved moved-teacher cases collapse to a small repeated pattern. "
            f"The dominant quoted note target is `{dominant_target}`, the dominant raw refined category is "
            f"`{dominant_category}`, and the dominant template is `{dominant_template}`. "
            "This suggests the next improvement, if needed, should be a targeted repair for this one phrase/template "
            "rather than another broad heuristic."
        )

    return {
        "unresolved_count": len(rows),
        "refined_category_counts": dict(sorted(refined_categories.items())),
        "quoted_note_target_counts": dict(sorted(quoted_note_targets.items())),
        "weak_word_counts": dict(sorted(weak_words.items())),
        "template_text_counts": dict(sorted(template_texts.items())),
        "top_examples": top_examples,
        "interpretation": interpretation,
    }


def render_report(summary: Dict[str, Any]) -> str:
    lines = [
        "# Remaining Teacher Repair Gaps",
        "",
        "This report explains the moved-teacher cases that still fall back to weak labels after the current note-anchored safe-hybrid repair path.",
        "",
        f"- unresolved cases: `{summary['unresolved_count']}`",
        f"- refined categories: `{json.dumps(summary['refined_category_counts'], sort_keys=True)}`",
        f"- quoted note targets: `{json.dumps(summary['quoted_note_target_counts'], sort_keys=True)}`",
        f"- weak fallback words: `{json.dumps(summary['weak_word_counts'], sort_keys=True)}`",
        "",
        "## Interpretation",
        "",
        summary["interpretation"],
        "",
        "## Examples",
        "",
    ]
    for example in summary["top_examples"]:
        lines.append(
            f"- `{example['example_id']}`: weak `{example['weak_word']}`, refined `{example['refined_word']}`, note `{example['note']}`"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    rows = unresolved_cases(
        weak_file=args.weak_file,
        refined_file=args.refined_file,
        audit_file=args.audit_file,
        min_confidence=args.min_confidence,
        max_note_repair_shift=args.max_note_repair_shift,
    )
    summary = build_summary(rows)

    if args.summary_file is not None:
        args.summary_file.parent.mkdir(parents=True, exist_ok=True)
        args.summary_file.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    if args.report_file is not None:
        args.report_file.parent.mkdir(parents=True, exist_ok=True)
        args.report_file.write_text(render_report(summary), encoding="utf-8")

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
