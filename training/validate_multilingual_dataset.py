#!/usr/bin/env python3
"""
Multilingual Dataset Validation Script
======================================
Validates the three core datasets for the autonomous_laughter_prediction_essential project:
  1. data/final_merged_10k/       (~10,048 examples: en, zh, hi)
  2. data/synthetic_hindi/       (~4,000 examples, when complete)
  3. data/expanded_10k_with_hindi/ (~10,048 examples)

Usage:
    python training/validate_multilingual_dataset.py
    python training/validate_multilingual_dataset.py --verbose
    python training/validate_multilingual_dataset.py --skip-synthetic

Output:
    docs/DATASET_VALIDATION_REPORT.md
"""

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Project root
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATASETS = {
    "final_merged_10k": PROJECT_ROOT / "data" / "final_merged_10k",
    "synthetic_hindi": PROJECT_ROOT / "data" / "synthetic_hindi",
    "expanded_10k_with_hindi": PROJECT_ROOT / "data" / "expanded_10k_with_hindi",
}
SPLITS = ["train", "valid", "test"]
REQUIRED_FIELDS = [
    "example_id",
    "language",
    "words",
    "labels",
]
BIOSEMIOTIC_PREFIXES = [
    "duchenne_",
    "incongruity_",
    "tom_",
]
LAUGHTER_RATE_MIN = 0.30
LAUGHTER_RATE_MAX = 0.45
SUPPORTED_LANGUAGES = {"en", "zh", "hi"}


@dataclass
class ValidationError:
    """Records a single validation error."""
    dataset: str
    split: str
    example_id: str
    field: str
    message: str


@dataclass
class DatasetStats:
    """Aggregated statistics for one dataset split."""
    total_examples: int = 0
    language_counts: Counter = field(default_factory=Counter)
    laughter_rate: float = 0.0
    label_counts: Counter = field(default_factory=Counter)
    word_level_laughter_rates: dict[str, float] = field(default_factory=dict)
    missing_field_counts: Counter = field(default_factory=Counter)
    biosemiotic_coverage: dict[str, float] = field(default_factory=dict)
    # Per-language stats
    language_stats: dict[str, dict[str, Any]] = field(default_factory=dict)


@dataclass
class DatasetReport:
    """Full validation report for one dataset."""
    name: str
    path: Path
    exists: bool
    stats: dict[str, DatasetStats] = field(default_factory=dict)
    errors: list[ValidationError] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def parse_args():
    parser = argparse.ArgumentParser(description="Validate multilingual laughter datasets.")
    parser.add_argument("--verbose", action="store_true", help="Print per-example errors")
    parser.add_argument("--skip-synthetic", action="store_true",
                        help="Skip synthetic_hindi dataset (not yet complete)")
    parser.add_argument("--output", default=str(PROJECT_ROOT / "docs" / "DATASET_VALIDATION_REPORT.md"),
                        help="Output report path")
    return parser.parse_args()


# ------------------------------------------------------------------
# Core validation logic
# ------------------------------------------------------------------

def load_jsonl(filepath: Path) -> list[dict]:
    """Load a JSONL file, returning list of parsed dicts."""
    lines = []
    if not filepath.exists():
        return lines
    with open(filepath, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            try:
                lines.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise ValueError(f"Line {i+1} JSON parse error in {filepath}: {e}") from e
    return lines


def check_format_and_fields(examples: list[dict], dataset: str, split: str) -> tuple[list[ValidationError], DatasetStats]:
    """Validate JSONL format, required fields, and label/word consistency."""
    errors: list[ValidationError] = []
    stats = DatasetStats()
    stats.total_examples = len(examples)

    lang_counts: Counter[str] = Counter()
    label_counts: Counter[int] = Counter()
    word_level_label_totals: dict[str, dict[int, int]] = defaultdict(lambda: {0: 0, 1: 0})
    missing_counts: Counter[str] = Counter()
    biosemiotic_present: Counter[str] = Counter()

    total_biosemiotic = len(BIOSEMIOTIC_PREFIXES)

    for ex in examples:
        eid = ex.get("example_id", f"<unknown:{len(errors)}>")
        stats_example_id = eid

        # Check required fields
        for field_name in REQUIRED_FIELDS:
            if field_name not in ex:
                missing_counts[field_name] += 1
                errors.append(ValidationError(
                    dataset=dataset, split=split, example_id=eid,
                    field=field_name,
                    message=f"Missing required field '{field_name}'"
                ))

        # Collect language
        lang = ex.get("language", "unknown")
        lang_counts[lang] += 1

        # Check words/labels consistency
        words = ex.get("words", [])
        labels = ex.get("labels", [])
        if isinstance(words, list) and isinstance(labels, list):
            if len(words) != len(labels):
                errors.append(ValidationError(
                    dataset=dataset, split=split, example_id=eid,
                    field="labels",
                    message=f"Word/label length mismatch: words={len(words)}, labels={len(labels)}"
                ))
            else:
                # Count word-level labels per language
                for lbl in labels:
                    word_level_label_totals[lang][lbl] += 1

        # Count sentence-level label
        lbl = ex.get("label")
        if lbl is not None:
            try:
                label_counts[int(lbl)] += 1
            except (ValueError, TypeError):
                errors.append(ValidationError(
                    dataset=dataset, split=split, example_id=eid,
                    field="label",
                    message=f"Non-integer sentence label: {lbl}"
                ))

        # Check biosemiotic coverage
        for prefix in BIOSEMIOTIC_PREFIXES:
            for key in ex:
                if key.startswith(prefix):
                    biosemiotic_present[prefix] += 1
                    break

    stats.language_counts = lang_counts
    stats.label_counts = label_counts
    stats.missing_field_counts = missing_counts

    # Compute laughter rates
    total_word_labels = sum(
        word_level_label_totals[lang].get(1, 0) + word_level_label_totals[lang].get(0, 0)
        for lang in word_level_label_totals
    )
    if total_word_labels > 0:
        total_laughter = sum(word_level_label_totals[lang].get(1, 0) for lang in word_level_label_totals)
        stats.laughter_rate = total_laughter / total_word_labels

    # Per-language word-level laughter rates
    for lang, counts in word_level_label_totals.items():
        total = counts.get(0, 0) + counts.get(1, 0)
        if total > 0:
            stats.language_stats[lang] = {
                "word_laughter_rate": counts.get(1, 0) / total,
                "total_words": total,
                "laughter_words": counts.get(1, 0),
            }

    # Biosemiotic coverage (how many examples have at least one feature from each prefix)
    for prefix in BIOSEMIOTIC_PREFIXES:
        stats.biosemiotic_coverage[prefix] = biosemiotic_present.get(prefix, 0) / max(stats.total_examples, 1)

    return errors, stats


def validate_dataset(dataset_name: str, dataset_path: Path, verbose: bool = False) -> DatasetReport:
    """Full validation for one dataset across all splits."""
    report = DatasetReport(name=dataset_name, path=dataset_path, exists=dataset_path.exists())
    report.warnings = []

    if not report.exists:
        report.warnings.append(f"Dataset path does not exist: {dataset_path}")
        return report

    for split in SPLITS:
        filepath = dataset_path / f"{split}.jsonl"
        if not filepath.exists():
            report.warnings.append(f"Missing {split}.jsonl in {dataset_name}")
            continue

        try:
            examples = load_jsonl(filepath)
        except ValueError as e:
            report.errors.append(ValidationError(
                dataset=dataset_name, split=split, example_id="N/A",
                field="file", message=str(e)
            ))
            continue

        errors, stats = check_format_and_fields(examples, dataset_name, split)
        report.stats[split] = stats
        report.errors.extend(errors)

        if verbose and errors:
            print(f"\n=== {dataset_name}/{split} errors ({len(errors)}) ===")
            for err in errors[:20]:
                print(f"  [{err.example_id}] {err.field}: {err.message}")
            if len(errors) > 20:
                print(f"  ... and {len(errors) - 20} more")

    return report


# ------------------------------------------------------------------
# Report generation
# ------------------------------------------------------------------

def format_pct(value: float, decimals: int = 1) -> str:
    return f"{value * 100:.{decimals}f}%"


def generate_markdown(reports: list[DatasetReport], args) -> str:
    """Generate the full Markdown validation report."""
    lines = [
        "# Dataset Validation Report",
        "",
        f"*Generated: 2026-05-04*  ",
        f"*Script: training/validate_multilingual_dataset.py*",
        "",
        "---",
        "",
        "## Executive Summary",
        "",
    ]

    # Quick summary table
    lines.append("| Dataset | Status | Train | Valid | Test | Total | Overall Laughter Rate |")
    lines.append("|---|---|---|---|---|---|---|")

    for r in reports:
        if not r.exists:
            lines.append(f"| {r.name} | **MISSING** | - | - | - | - | - |")
            continue

        total = sum(s.total_examples for s in r.stats.values())
        overall_rate = overall_laughter_rate(r)
        train_n = r.stats.get("train", DatasetStats()).total_examples
        valid_n = r.stats.get("valid", DatasetStats()).total_examples
        test_n = r.stats.get("test", DatasetStats()).total_examples

        status = "OK" if total > 0 else "EMPTY"
        if r.errors:
            status = f"ERRORS ({len(r.errors)})"

        lines.append(f"| {r.name} | {status} | {train_n:,} | {valid_n:,} | {test_n:,} | {total:,} | {format_pct(overall_rate)} |")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Detailed Validation Results")
    lines.append("")

    for r in reports:
        lines.append(f"### Dataset: `{r.name}`")
        lines.append(f"- **Path:** `{r.path}`")
        lines.append(f"- **Exists:** {r.exists}")
        lines.append("")

        if not r.exists:
            lines.append("⚠️ Dataset directory not found.\n")
            continue

        if r.warnings:
            lines.append("#### Warnings")
            for w in r.warnings:
                lines.append(f"- ⚠️ {w}")
            lines.append("")

        if r.errors:
            lines.append(f"#### Errors ({len(r.errors)} total)")
            lines.append("")
            # Group errors by field
            by_field: dict[str, list[ValidationError]] = defaultdict(list)
            for e in r.errors:
                by_field[e.field].append(e)
            for field_name, errs in sorted(by_field.items(), key=lambda x: -len(x[1])):
                lines.append(f"**Field: `{field_name}`** — {len(errs)} error(s)")
                for e in errs[:5]:
                    lines.append(f"- `[{e.split}]` `{e.example_id}`: {e.message}")
                if len(errs) > 5:
                    lines.append(f"  ... and {len(errs) - 5} more")
                lines.append("")
        else:
            lines.append("✅ No format errors detected.")
            lines.append("")

        lines.append("#### Split Breakdown")
        lines.append("")

        for split in SPLITS:
            stats = r.stats.get(split)
            if stats is None:
                continue

            lines.append(f"##### {split.upper()} (n={stats.total_examples:,})")
            lines.append("")

            if stats.total_examples == 0:
                lines.append("*No examples found.*\n")
                continue

            # Language distribution
            lines.append("**Language Distribution:**")
            lines.append("")
            lang_total = sum(stats.language_counts.values())
            for lang, count in sorted(stats.language_counts.items(), key=lambda x: -x[1]):
                lines.append(f"- {lang}: {count:,} ({format_pct(count / lang_total)}")
            lines.append("")

            # Laughter rate
            if stats.laughter_rate > 0:
                rate_flag = "✅" if LAUGHTER_RATE_MIN <= stats.laughter_rate <= LAUGHTER_RATE_MAX else "⚠️"
                lines.append(f"**Word-Level Laughter Rate:** {format_pct(stats.laughter_rate)} {rate_flag}")
                lines.append(f"  (Expected range: {format_pct(LAUGHTER_RATE_MIN)} – {format_pct(LAUGHTER_RATE_MAX)})")
                lines.append("")

            # Per-language stats
            if stats.language_stats:
                lines.append("**Per-Language Word-Level Laughter Rate:**")
                lines.append("")
                lines.append("| Language | Laughter Rate | Total Words | Laughter Words |")
                lines.append("|---|---|---|---|---|")
                for lang, lang_stats in sorted(stats.language_stats.items()):
                    rate = lang_stats.get("word_laughter_rate", 0)
                    flag = "✅" if LAUGHTER_RATE_MIN <= rate <= LAUGHTER_RATE_MAX else "⚠️"
                    lines.append(
                        f"| {lang} | {flag} {format_pct(rate)} | {lang_stats.get('total_words', 0):,} | "
                        f"{lang_stats.get('laughter_words', 0):,} |"
                    )
                lines.append("")

            # Sentence-level label distribution
            if stats.label_counts:
                lines.append("**Sentence-Level Label Distribution:**")
                lines.append("")
                for lbl, count in sorted(stats.label_counts.items()):
                    lines.append(f"- {lbl}: {count:,} ({format_pct(count / stats.total_examples)})")
                lines.append("")

            # Biosemiotic coverage
            if stats.biosemiotic_coverage:
                lines.append("**Biosemiotic Feature Coverage (examples with ≥1 feature per category):**")
                lines.append("")
                for prefix, coverage in stats.biosemiotic_coverage.items():
                    lines.append(f"- `{prefix}`* : {format_pct(coverage)}")
                lines.append("")

            lines.append("---\n")

    # Recommendations section
    lines.append("## Recommendations")
    lines.append("")
    recommendations = generate_recommendations(reports)
    for rec in recommendations:
        lines.append(f"- {rec}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Validation Notes")
    lines.append("")
    lines.append("### Required Fields")
    lines.append("These fields are mandatory for every example:")
    for f in REQUIRED_FIELDS:
        lines.append(f"- `{f}`")
    lines.append("")
    lines.append("### Biosemiotic Feature Categories")
    for prefix in BIOSEMIOTIC_PREFIXES:
        lines.append(f"- `{prefix}`* — all fields starting with this prefix")
    lines.append("")
    lines.append("### Expected Laughter Rate")
    lines.append(f"Word-level laughter labels should fall between **{format_pct(LAUGHTER_RATE_MIN)}** and ")
    lines.append(f"**{format_pct(LAUGHTER_RATE_MAX)}** for each dataset.")
    lines.append("")
    lines.append("---")
    lines.append("*Report generated by `training/validate_multilingual_dataset.py`*")

    return "\n".join(lines)


def overall_laughter_rate(report: DatasetReport) -> float:
    """Compute total laughter rate across all splits."""
    total_words = 0
    total_laughter = 0
    for stats in report.stats.values():
        if stats.language_stats:
            for lang_stats in stats.language_stats.values():
                total_words += lang_stats.get("total_words", 0)
                total_laughter += lang_stats.get("laughter_words", 0)
    return total_laughter / max(total_words, 1)


def generate_recommendations(reports: list[DatasetReport]) -> list[str]:
    """Generate actionable recommendations based on validation results."""
    recs = []

    for r in reports:
        if not r.exists:
            recs.append(f"**[{r.name}]** Create or verify dataset path at `{r.path}`.")
            continue

        for split in SPLITS:
            stats = r.stats.get(split)
            if stats is None or stats.total_examples == 0:
                recs.append(f"**[{r.name}/{split}]** No examples found — check data pipeline.")
                continue

            # Check laughter rate
            if stats.laughter_rate > 0:
                if not (LAUGHTER_RATE_MIN <= stats.laughter_rate <= LAUGHTER_RATE_MAX):
                    recs.append(
                        f"**[{r.name}/{split}]** Laughter rate {format_pct(stats.laughter_rate)} outside "
                        f"expected range ({format_pct(LAUGHTER_RATE_MIN)}-{format_pct(LAUGHTER_RATE_MAX)}) — "
                        "review label distribution."
                    )

            # Per-language check
            for lang, lang_stats in stats.language_stats.items():
                rate = lang_stats.get("word_laughter_rate", 0)
                if rate > 0 and not (LAUGHTER_RATE_MIN <= rate <= LAUGHTER_RATE_MAX):
                    recs.append(
                        f"**[{r.name}/{split}/{lang}]** Language '{lang}' laughter rate "
                        f"{format_pct(rate)} outside expected range."
                    )

            # Missing fields
            for field_name, count in stats.missing_field_counts.items():
                recs.append(
                    f"**[{r.name}/{split}]** {count} example(s) missing field "
                    f"'{field_name}' — fix pipeline to ensure completeness."
                )

        # Check dataset sizes
        for split in ["train", "valid", "test"]:
            stats = r.stats.get(split)
            if stats and stats.total_examples == 0:
                recs.append(f"**[{r.name}/{split}]** Empty split — investigate data pipeline.")

    if not recs:
        recs.append("All datasets pass validation. No immediate action required.")

    return recs


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------

def main():
    args = parse_args()
    verbose = args.verbose

    print("=" * 60)
    print("Multilingual Dataset Validation")
    print("=" * 60)

    datasets_to_validate = [
        ("final_merged_10k", DATASETS["final_merged_10k"]),
        ("expanded_10k_with_hindi", DATASETS["expanded_10k_with_hindi"]),
    ]
    if not args.skip_synthetic:
        datasets_to_validate.append(("synthetic_hindi", DATASETS["synthetic_hindi"]))

    reports = []
    for name, path in datasets_to_validate:
        print(f"\nValidating: {name} ...", end=" ", flush=True)
        report = validate_dataset(name, path, verbose=verbose)
        reports.append(report)
        n_errors = len(report.errors)
        n_total = sum(s.total_examples for s in report.stats.values())
        print(f"{n_total:,} examples, {n_errors} error(s)")

        if report.warnings and verbose:
            for w in report.warnings:
                print(f"  ⚠️ {w}")

    # Generate report
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    md = generate_markdown(reports, args)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(md)

    print(f"\n{'=' * 60}")
    print(f"Report saved to: {output_path}")
    print("=" * 60)

    # Exit with error if any errors found
    total_errors = sum(len(r.errors) for r in reports)
    if total_errors > 0:
        print(f"\n⚠️  {total_errors} validation error(s) found. See report for details.")
        sys.exit(1)
    else:
        print("\n✅ All datasets passed validation.")
        sys.exit(0)


if __name__ == "__main__":
    main()
