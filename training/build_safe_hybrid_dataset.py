#!/usr/bin/env python3
"""
Build a guarded hybrid training set from weak labels plus teacher refinement.

Policy:
- keep the weak-label example by default
- preserve teacher edits when the target stayed in place
- accept moved teacher edits only when they are high-confidence, lexical, and
  within a bounded shift window
- recover dropped examples back to their weak-label version

This keeps the proven weak-label baseline intact while allowing a narrow subset
of teacher changes that look structurally plausible.
"""

from __future__ import annotations

import argparse
import json
import re
import string
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple


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
CONTRACTION_FRAGMENTS = {"d", "ll", "m", "re", "s", "t", "ve"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a safe hybrid train set from weak and refined labels.")
    parser.add_argument("--weak-file", type=Path, required=True)
    parser.add_argument("--refined-file", type=Path, required=True)
    parser.add_argument("--audit-file", type=Path, required=True)
    parser.add_argument("--output-file", type=Path, required=True)
    parser.add_argument("--summary-file", type=Path, default=None)
    parser.add_argument("--min-confidence", type=float, default=0.9)
    parser.add_argument("--max-absolute-shift", type=int, default=8)
    parser.add_argument(
        "--disable-note-anchored-repair",
        action="store_true",
        help="Disable note-guided lexical recovery for bad moved teacher targets.",
    )
    parser.add_argument(
        "--max-note-repair-shift",
        type=int,
        default=16,
        help="Maximum weak-label shift allowed after note-anchored lexical repair.",
    )
    return parser.parse_args()


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def append_jsonl(path: Path, rows: Sequence[Dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=True) + "\n")


def positive_index(labels: Sequence[Any]) -> Optional[int]:
    for index, label in enumerate(labels):
        if int(label) == 1:
            return index
    return None


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


def normalize_text_tokens(text: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def repairable_note_token(token: str) -> bool:
    return len(token) > 1 and token not in STOPWORDS and token not in CONTRACTION_FRAGMENTS


def extract_quoted_spans(text: str) -> List[str]:
    spans: List[str] = []
    stack: List[Tuple[str, int]] = []
    for index, char in enumerate(text):
        if char not in {"'", '"'}:
            continue
        previous = text[index - 1] if index > 0 else " "
        following = text[index + 1] if index + 1 < len(text) else " "
        previous_is_word = previous.isalnum()
        following_is_word = following.isalnum()

        if stack and stack[-1][0] == char:
            # Ignore apostrophes inside contractions like I'm or don't.
            if previous_is_word and following_is_word:
                continue
            _, start = stack.pop()
            content = text[start + 1 : index].strip()
            if content:
                spans.append(content)
            continue

        if previous_is_word and following_is_word:
            continue
        if following_is_word or following in {"'", '"'}:
            stack.append((char, index))
    return spans


def normalized_word_entries(words: Sequence[str]) -> List[Tuple[int, str]]:
    entries: List[Tuple[int, str]] = []
    for index, word in enumerate(words):
        parts = normalize_text_tokens(word)
        if not parts:
            continue
        for part in parts:
            entries.append((index, part))
    return entries


def find_subsequence_matches(words: Sequence[str], tokens: Sequence[str]) -> List[List[int]]:
    if not tokens:
        return []
    entries = normalized_word_entries(words)
    normalized_values = [value for _, value in entries]
    match_count = len(tokens)
    matches: List[List[int]] = []
    for start in range(len(normalized_values) - match_count + 1):
        if normalized_values[start : start + match_count] != list(tokens):
            continue
        matches.append([entries[position][0] for position in range(start, start + match_count)])
    return matches


def choose_note_repair_index(
    *,
    words: Sequence[str],
    note: str,
    weak_index: Optional[int],
) -> Tuple[Optional[int], Optional[str]]:
    spans = extract_quoted_spans(note)
    ranked_spans: List[Tuple[int, int, str, List[str]]] = []
    for order, span in enumerate(spans):
        tokens = normalize_text_tokens(span)
        if tokens:
            ranked_spans.append((len(tokens), order, span, tokens))

    ranked_spans.sort()
    fallback_target = weak_index if weak_index is not None else 0

    for _, _, span, tokens in ranked_spans:
        matches = find_subsequence_matches(words, tokens)
        if matches:
            matches.sort(
                key=lambda match: (
                    abs(match[-1] - fallback_target),
                    -match[-1],
                )
            )
            best_match = matches[0]
            lexical_candidates = [
                index
                for index in best_match
                if classify_token(words[index]) == "lexical" and words[index].strip().lower() not in STOPWORDS
            ]
            if lexical_candidates:
                return lexical_candidates[-1], span

        # If the exact phrase is not alignable, fall back to the strongest
        # single lexical token from the quoted span that still appears in the
        # transcript near the weak label.
        candidate_token_matches: List[Tuple[int, int, int, int, str]] = []
        for token in tokens:
            if not repairable_note_token(token):
                continue
            for match in find_subsequence_matches(words, [token]):
                index = match[-1]
                candidate_token_matches.append(
                    (
                        abs(index - fallback_target),
                        -index,
                        -len(token),
                        index,
                        token,
                    )
                )
        if candidate_token_matches:
            candidate_token_matches.sort()
            _, _, _, index, _ = candidate_token_matches[0]
            return index, span
    return None, None


def with_hybrid_metadata(
    row: Dict[str, Any],
    *,
    source: str,
    weak_index: Optional[int],
    selected_index: Optional[int],
    decision: Optional[Dict[str, Any]],
    note: str,
    extra_metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    updated = dict(row)
    metadata = dict(updated.get("metadata") or {})
    metadata.update(
        {
            "hybrid_label_source": source,
            "hybrid_note": note,
            "hybrid_weak_positive_index": weak_index,
            "hybrid_selected_positive_index": selected_index,
        }
    )
    if decision is not None:
        metadata.update(
            {
                "hybrid_teacher_confidence": decision.get("confidence"),
                "hybrid_teacher_reason_tags": decision.get("reason_tags"),
                "hybrid_teacher_action": decision.get("action"),
            }
        )
    if extra_metadata:
        metadata.update(extra_metadata)
    updated["metadata"] = metadata
    return updated


def main() -> None:
    args = parse_args()
    weak_rows = load_jsonl(args.weak_file)
    refined_rows = load_jsonl(args.refined_file)
    audit_rows = load_jsonl(args.audit_file)

    refined_by_id = {str(row["example_id"]): row for row in refined_rows}
    audit_by_id = {str(row["example_id"]): row for row in audit_rows}

    output_rows: List[Dict[str, Any]] = []
    decisions = Counter()
    moved_accept_categories = Counter()
    moved_reject_categories = Counter()
    note_repair_categories = Counter()

    for weak_row in weak_rows:
        example_id = str(weak_row["example_id"])
        audit_row = audit_by_id.get(example_id)
        weak_index = positive_index(weak_row.get("labels", []))

        if audit_row is None:
            decisions["fallback_missing_audit"] += 1
            output_rows.append(
                with_hybrid_metadata(
                    weak_row,
                    source="weak",
                    weak_index=weak_index,
                    selected_index=weak_index,
                    decision=None,
                    note="No audit row found; kept weak label.",
                )
            )
            continue

        decision = audit_row.get("decision") or {}
        kept = bool(audit_row.get("kept"))
        refined_row = refined_by_id.get(example_id)

        if not kept or refined_row is None:
            reason_tags = [str(tag) for tag in decision.get("reason_tags", [])]
            if "request_error" in reason_tags:
                decisions["recovered_request_error_drop"] += 1
                note = "Recovered weak label because teacher request failed."
            else:
                decisions["recovered_teacher_drop"] += 1
                note = "Recovered weak label instead of trusting a teacher drop."
            output_rows.append(
                with_hybrid_metadata(
                    weak_row,
                    source="weak",
                    weak_index=weak_index,
                    selected_index=weak_index,
                    decision=decision,
                    note=note,
                )
            )
            continue

        refined_index = positive_index(refined_row.get("labels", []))
        refined_token = safe_token(refined_row.get("words", []), refined_index)
        refined_category = classify_token(refined_token)
        confidence = float(decision.get("confidence") or 0.0)

        if refined_index == weak_index:
            decisions["accepted_same_index_teacher"] += 1
            output_rows.append(
                with_hybrid_metadata(
                    refined_row,
                    source="teacher_same_index",
                    weak_index=weak_index,
                    selected_index=refined_index,
                    decision=decision,
                    note="Accepted teacher output because the positive index did not move.",
                )
            )
            continue

        shift = None
        if weak_index is not None and refined_index is not None:
            shift = abs(refined_index - weak_index)

        note_repair_index = None
        note_repair_span = None
        note_repair_shift = None
        if not args.disable_note_anchored_repair:
            note_repair_index, note_repair_span = choose_note_repair_index(
                words=refined_row.get("words", []),
                note=str(decision.get("note") or ""),
                weak_index=weak_index,
            )
            if note_repair_index is not None and weak_index is not None:
                note_repair_shift = abs(note_repair_index - weak_index)

        if (
            note_repair_index is not None
            and note_repair_shift is not None
            and note_repair_shift <= args.max_note_repair_shift
            and confidence >= args.min_confidence
        ):
            repaired_row = dict(refined_row)
            repaired_labels = [0] * len(repaired_row.get("labels", []))
            repaired_labels[note_repair_index] = 1
            repaired_row["labels"] = repaired_labels
            repaired_token = safe_token(repaired_row.get("words", []), note_repair_index)
            repaired_category = classify_token(repaired_token)
            if repaired_category == "lexical":
                decisions["accepted_moved_teacher_note_repair"] += 1
                note_repair_categories[repaired_token.strip().lower()] += 1
                output_rows.append(
                    with_hybrid_metadata(
                        repaired_row,
                        source="teacher_note_repaired",
                        weak_index=weak_index,
                        selected_index=note_repair_index,
                        decision=decision,
                        note="Accepted note-anchored lexical repair for moved teacher target.",
                        extra_metadata={
                            "hybrid_original_teacher_positive_index": refined_index,
                            "hybrid_original_teacher_positive_category": refined_category,
                            "hybrid_note_repair_quote": note_repair_span,
                            "hybrid_note_repair_shift": note_repair_shift,
                        },
                    )
                )
                continue

        if refined_category != "lexical":
            decisions["rejected_moved_teacher_nonlexical"] += 1
            moved_reject_categories[refined_category] += 1
            output_rows.append(
                with_hybrid_metadata(
                    weak_row,
                    source="weak",
                    weak_index=weak_index,
                    selected_index=weak_index,
                    decision=decision,
                    note=f"Rejected moved teacher target because category was {refined_category}.",
                )
            )
            continue

        if confidence < args.min_confidence:
            decisions["rejected_moved_teacher_low_confidence"] += 1
            moved_reject_categories["low_confidence"] += 1
            output_rows.append(
                with_hybrid_metadata(
                    weak_row,
                    source="weak",
                    weak_index=weak_index,
                    selected_index=weak_index,
                    decision=decision,
                    note="Rejected moved teacher target because confidence was below threshold.",
                )
            )
            continue

        if shift is None or shift > args.max_absolute_shift:
            decisions["rejected_moved_teacher_large_shift"] += 1
            moved_reject_categories["large_shift"] += 1
            output_rows.append(
                with_hybrid_metadata(
                    weak_row,
                    source="weak",
                    weak_index=weak_index,
                    selected_index=weak_index,
                    decision=decision,
                    note="Rejected moved teacher target because the index shift was too large.",
                )
            )
            continue

        decisions["accepted_moved_teacher_lexical"] += 1
        moved_accept_categories[refined_category] += 1
        output_rows.append(
            with_hybrid_metadata(
                refined_row,
                source="teacher_moved_lexical",
                weak_index=weak_index,
                selected_index=refined_index,
                decision=decision,
                note="Accepted moved teacher target because it was lexical, high-confidence, and bounded.",
            )
        )

    args.output_file.parent.mkdir(parents=True, exist_ok=True)
    append_jsonl(args.output_file, output_rows)

    summary = {
        "input_examples": len(weak_rows),
        "output_examples": len(output_rows),
        "config": {
            "min_confidence": args.min_confidence,
            "max_absolute_shift": args.max_absolute_shift,
            "note_anchored_repair_enabled": not args.disable_note_anchored_repair,
            "max_note_repair_shift": args.max_note_repair_shift,
        },
        "decisions": dict(decisions),
        "accepted_moved_teacher_categories": dict(moved_accept_categories),
        "rejected_moved_teacher_categories": dict(moved_reject_categories),
        "note_repair_tokens": dict(note_repair_categories),
    }

    if args.summary_file is not None:
        args.summary_file.parent.mkdir(parents=True, exist_ok=True)
        args.summary_file.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
