#!/usr/bin/env python3
"""
Evidence-gated autoresearch loop for the stand-up XLM-R pipeline.

This replaces the old simulated research loop with a real local experiment
runner that:

1. reads the current promoted baseline
2. proposes a small number of safe training variants
3. runs the real XLM-R trainer
4. compares validation metrics against the promoted baseline
5. promotes only if both validation F1 and validation IoU-F1 improve

The loop is intentionally conservative. It optimizes the current stand-up
pipeline instead of simulating unrelated cognitive-architecture experiments.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple


PROJECT_ROOT = Path("/Users/Subho/autonomous_laughter_prediction")
TRAINER = PROJECT_ROOT / "training" / "xlmr_standup_word_level.py"
DEFAULT_TRAIN_FILE = PROJECT_ROOT / "data" / "training" / "standup_word_level" / "train.jsonl"
DEFAULT_VALID_FILE = PROJECT_ROOT / "data" / "training" / "standup_word_level" / "valid.jsonl"
DEFAULT_TEST_FILE = PROJECT_ROOT / "data" / "training" / "standup_word_level" / "test.jsonl"
DEFAULT_BASELINE_SUMMARY = (
    PROJECT_ROOT / "experiments" / "xlmr_standup_baseline_weak_pos5" / "training_summary.json"
)
RESEARCH_LOG = PROJECT_ROOT / "research_log.json"
PROMOTED_MODEL_REGISTRY = PROJECT_ROOT / "experiments" / "promoted_model.json"
AUTORESEARCH_DIR = PROJECT_ROOT / "experiments" / "autoresearch"


@dataclass(slots=True)
class ExperimentCandidate:
    name: str
    rationale: str
    cli_args: List[str]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_research_log(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    payload = load_json(path)
    if isinstance(payload, list):
        return payload
    raise ValueError(f"Research log is not a list: {path}")


def load_jsonl_rows(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def file_sha1(path: Path) -> str:
    digest = hashlib.sha1()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def dataset_fingerprint(train_file: Path, valid_file: Path, test_file: Path) -> str:
    digest = hashlib.sha1()
    for path in (train_file, valid_file, test_file):
        digest.update(str(path.resolve()).encode("utf-8"))
        digest.update(file_sha1(path).encode("utf-8"))
    return digest.hexdigest()


def normalized_word_signature(row: Dict[str, Any]) -> Tuple[str, ...]:
    return tuple(str(word).strip().lower() for word in row.get("words", []))


def split_overlap_report(train_file: Path, valid_file: Path, test_file: Path) -> Dict[str, Any]:
    train_rows = load_jsonl_rows(train_file)
    valid_rows = load_jsonl_rows(valid_file)
    test_rows = load_jsonl_rows(test_file)

    train_signatures = {normalized_word_signature(row): str(row.get("example_id")) for row in train_rows}
    valid_signatures = {normalized_word_signature(row): str(row.get("example_id")) for row in valid_rows}
    test_signatures = {normalized_word_signature(row): str(row.get("example_id")) for row in test_rows}

    def overlap(a: Dict[Tuple[str, ...], str], b: Dict[Tuple[str, ...], str]) -> List[Dict[str, str]]:
        shared = sorted(set(a) & set(b))
        return [
            {
                "left_example_id": a[key],
                "right_example_id": b[key],
                "text": " ".join(key)[:200],
            }
            for key in shared[:10]
        ]

    train_valid_count = len(set(train_signatures) & set(valid_signatures))
    train_test_count = len(set(train_signatures) & set(test_signatures))
    valid_test_count = len(set(valid_signatures) & set(test_signatures))

    return {
        "exact_overlap_counts": {
            "train_valid": train_valid_count,
            "train_test": train_test_count,
            "valid_test": valid_test_count,
        },
        "promotion_safe": train_valid_count == 0 and train_test_count == 0 and valid_test_count == 0,
        "sample_overlaps": {
            "train_valid": overlap(train_signatures, valid_signatures),
            "train_test": overlap(train_signatures, test_signatures),
            "valid_test": overlap(valid_signatures, test_signatures),
        },
    }


def tested_candidate_names(research_log: Sequence[Dict[str, Any]], active_dataset_fingerprint: str) -> set[str]:
    tested: set[str] = set()
    for entry in research_log:
        if entry.get("loop_version") != "real_v1":
            continue
        if entry.get("dataset_fingerprint") != active_dataset_fingerprint:
            continue
        for candidate in entry.get("candidates", []):
            name = candidate.get("name")
            if name:
                tested.add(str(name))
    return tested


def load_promoted_baseline(baseline_summary: Path) -> Dict[str, Any]:
    registry_payload: Optional[Dict[str, Any]] = None
    if PROMOTED_MODEL_REGISTRY.exists():
        registry_payload = load_json(PROMOTED_MODEL_REGISTRY)
        summary_path = Path(registry_payload["summary_path"])
        if summary_path.exists():
            baseline_summary = summary_path

    summary = load_json(baseline_summary)
    validation_f1 = float(summary["best_validation"]["f1"])
    validation_iou_f1 = float(summary["best_validation"]["iou_f1"])
    test_f1 = float(summary["test_metrics"]["f1"]) if summary.get("test_metrics") else None
    test_iou_f1 = float(summary["test_metrics"]["iou_f1"]) if summary.get("test_metrics") else None
    output_dir = str(Path(baseline_summary).parent)
    if registry_payload is not None:
        validation_f1 = float(registry_payload.get("validation_f1", validation_f1))
        validation_iou_f1 = float(registry_payload.get("validation_iou_f1", validation_iou_f1))
        test_f1 = float(registry_payload.get("test_f1", test_f1)) if registry_payload.get("test_f1") is not None else test_f1
        test_iou_f1 = (
            float(registry_payload.get("test_iou_f1", test_iou_f1))
            if registry_payload.get("test_iou_f1") is not None
            else test_iou_f1
        )
        output_dir = str(registry_payload.get("output_dir", output_dir))
    return {
        "summary_path": str(baseline_summary),
        "output_dir": output_dir,
        "validation_f1": validation_f1,
        "validation_iou_f1": validation_iou_f1,
        "test_f1": test_f1,
        "test_iou_f1": test_iou_f1,
        "config": summary["config"],
    }


def build_candidates(
    baseline: Dict[str, Any],
    cycle_index: int,
    max_experiments: int,
    excluded_names: Optional[set[str]] = None,
) -> List[ExperimentCandidate]:
    base_weight = float(baseline["config"].get("positive_class_weight", 1.0))
    base_max_length = int(baseline["config"].get("max_length", 256))
    base_unfreeze = int(baseline["config"].get("unfreeze_last_n_layers", 2))
    base_classifier_lr = float(baseline["config"].get("classifier_learning_rate", 1e-4))
    excluded_names = excluded_names or set()

    def candidate_is_redundant(candidate: ExperimentCandidate) -> bool:
        overrides = parse_overrides(candidate.cli_args)
        config = baseline["config"]
        return (
            ("--positive-class-weight" not in overrides or float(overrides["--positive-class-weight"]) == float(config.get("positive_class_weight", 1.0)))
            and ("--loss-type" not in overrides or str(overrides["--loss-type"]) == str(config.get("loss_type", "cross_entropy")))
            and ("--focal-gamma" not in overrides or float(overrides["--focal-gamma"]) == float(config.get("focal_gamma", 2.0)))
            and ("--max-length" not in overrides or int(overrides["--max-length"]) == int(config.get("max_length", 256)))
            and ("--unfreeze-last-n-layers" not in overrides or int(overrides["--unfreeze-last-n-layers"]) == int(config.get("unfreeze_last_n_layers", 2)))
            and ("--classifier-learning-rate" not in overrides or float(overrides["--classifier-learning-rate"]) == float(config.get("classifier_learning_rate", 1e-4)))
            and ("--epochs" not in overrides or int(overrides["--epochs"]) == int(config.get("epochs", 3)))
        )

    candidate_pool = [
        ExperimentCandidate(
            name="pos4",
            rationale="Slightly reduce positive weighting to check whether precision recovers without losing recall.",
            cli_args=["--positive-class-weight", "4.0"],
        ),
        ExperimentCandidate(
            name="focal_pos5_g15",
            rationale="Use focal loss with the current winning positive weight to focus learning on hard positives.",
            cli_args=[
                "--loss-type",
                "focal",
                "--positive-class-weight",
                f"{base_weight}",
                "--focal-gamma",
                "1.5",
            ],
        ),
        ExperimentCandidate(
            name="pos6",
            rationale="Slightly increase positive weighting above the promoted run to test whether recall can rise further.",
            cli_args=["--positive-class-weight", "6.0"],
        ),
        ExperimentCandidate(
            name="pos5_len320",
            rationale="Increase context length while keeping the current winning weight.",
            cli_args=["--positive-class-weight", f"{base_weight}", "--max-length", str(max(base_max_length, 320))],
        ),
        ExperimentCandidate(
            name="pos5_unfreeze4",
            rationale="Unfreeze more encoder layers to test whether a little more adaptation helps on stand-up phrasing.",
            cli_args=["--positive-class-weight", f"{base_weight}", "--unfreeze-last-n-layers", str(max(base_unfreeze, 4))],
        ),
        ExperimentCandidate(
            name="pos5_cls8e-5",
            rationale="Lower classifier LR to reduce overshooting while preserving the winning weighting setup.",
            cli_args=[
                "--positive-class-weight",
                f"{base_weight}",
                "--classifier-learning-rate",
                f"{min(base_classifier_lr, 8e-5):.6g}",
            ],
        ),
        ExperimentCandidate(
            name="pos5_epochs4",
            rationale="Extend training by one epoch to test whether the clean split still has headroom after the current epoch-3 winner.",
            cli_args=["--positive-class-weight", f"{base_weight}", "--epochs", "4"],
        ),
        ExperimentCandidate(
            name="pos5_cls6e-5",
            rationale="Lower classifier LR further to check whether validation IoU-F1 improves when the classifier head updates more conservatively.",
            cli_args=[
                "--positive-class-weight",
                f"{base_weight}",
                "--classifier-learning-rate",
                "6e-5",
            ],
        ),
        ExperimentCandidate(
            name="pos5_len384",
            rationale="Increase context length beyond 320 to test whether extra local setup helps on longer stand-up segments.",
            cli_args=["--positive-class-weight", f"{base_weight}", "--max-length", "384"],
        ),
        ExperimentCandidate(
            name="focal_pos5_g10",
            rationale="Use a gentler focal-loss gamma than the previous focal run to see whether hard-example emphasis can improve IoU without the same F1 penalty.",
            cli_args=[
                "--loss-type",
                "focal",
                "--positive-class-weight",
                f"{base_weight}",
                "--focal-gamma",
                "1.0",
            ],
        ),
    ]

    if not candidate_pool:
        return []

    start = cycle_index % len(candidate_pool)
    ordered = candidate_pool[start:] + candidate_pool[:start]
    unseen = [
        candidate
        for candidate in ordered
        if candidate.name not in excluded_names and not candidate_is_redundant(candidate)
    ]
    return unseen[: max(1, max_experiments)]


def parse_overrides(cli_args: Sequence[str]) -> Dict[str, str]:
    if len(cli_args) % 2 != 0:
        raise ValueError(f"Candidate overrides must be flag/value pairs: {cli_args}")

    overrides: Dict[str, str] = {}
    for index in range(0, len(cli_args), 2):
        flag = cli_args[index]
        value = cli_args[index + 1]
        overrides[flag] = value
    return overrides


def make_experiment_command(
    train_file: Path,
    valid_file: Path,
    test_file: Path,
    output_dir: Path,
    baseline: Dict[str, Any],
    candidate: ExperimentCandidate,
) -> List[str]:
    config = baseline["config"]
    overrides = parse_overrides(candidate.cli_args)

    def value_for(flag: str, default: str) -> str:
        return overrides.get(flag, default)

    command = [
        sys.executable,
        str(TRAINER),
        "--train-file",
        str(train_file),
        "--valid-file",
        str(valid_file),
        "--test-file",
        str(test_file),
        "--output-dir",
        str(output_dir),
        "--model-name",
        value_for("--model-name", str(config["model_name"])),
        "--batch-size",
        value_for("--batch-size", str(config["batch_size"])),
        "--eval-batch-size",
        value_for("--eval-batch-size", str(config["eval_batch_size"])),
        "--max-length",
        value_for("--max-length", str(config["max_length"])),
        "--epochs",
        value_for("--epochs", str(config["epochs"])),
        "--freeze-encoder-epochs",
        value_for("--freeze-encoder-epochs", str(config["freeze_encoder_epochs"])),
        "--unfreeze-last-n-layers",
        value_for("--unfreeze-last-n-layers", str(config["unfreeze_last_n_layers"])),
        "--learning-rate",
        value_for("--learning-rate", str(config["learning_rate"])),
        "--classifier-learning-rate",
        value_for("--classifier-learning-rate", str(config["classifier_learning_rate"])),
        "--gradient-accumulation-steps",
        value_for("--gradient-accumulation-steps", str(config["gradient_accumulation_steps"])),
        "--loss-type",
        value_for("--loss-type", str(config.get("loss_type", "cross_entropy"))),
        "--positive-class-weight",
        value_for("--positive-class-weight", str(config.get("positive_class_weight", 1.0))),
        "--focal-gamma",
        value_for("--focal-gamma", str(config.get("focal_gamma", 2.0))),
    ]
    return command


def run_experiment(command: Sequence[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(command),
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )


def load_metrics(summary_path: Path) -> Dict[str, float]:
    summary = load_json(summary_path)
    validation = summary["best_validation"]
    test = summary.get("test_metrics") or {}
    return {
        "validation_f1": float(validation["f1"]),
        "validation_iou_f1": float(validation["iou_f1"]),
        "test_f1": float(test["f1"]) if test else 0.0,
        "test_iou_f1": float(test["iou_f1"]) if test else 0.0,
    }


def prune_candidate_checkpoint_weights(output_dir: Path) -> List[str]:
    model_dir = output_dir / "best_model"
    removed: List[str] = []
    for filename in ("model.safetensors", "pytorch_model.bin"):
        candidate_path = model_dir / filename
        if candidate_path.exists():
            candidate_path.unlink()
            removed.append(filename)
    return removed


def should_promote(candidate_metrics: Dict[str, float], baseline_metrics: Dict[str, Any]) -> bool:
    return (
        candidate_metrics["validation_f1"] > float(baseline_metrics["validation_f1"])
        and candidate_metrics["validation_iou_f1"] > float(baseline_metrics["validation_iou_f1"])
    )


def candidate_output_dir(experiments_dir: Path, dataset_fingerprint_value: str, candidate_name: str) -> Path:
    return experiments_dir / f"{dataset_fingerprint_value[:8]}_{candidate_name}"


def registry_payload(output_dir: Path, summary_path: Path, metrics: Dict[str, float], candidate: ExperimentCandidate) -> Dict[str, Any]:
    return {
        "updated_at": datetime.now().isoformat(),
        "output_dir": str(output_dir),
        "summary_path": str(summary_path),
        "selection_reason": candidate.rationale,
        "validation_f1": metrics["validation_f1"],
        "validation_iou_f1": metrics["validation_iou_f1"],
        "test_f1": metrics["test_f1"],
        "test_iou_f1": metrics["test_iou_f1"],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run an evidence-gated stand-up autoresearch cycle.")
    parser.add_argument("--train-file", type=Path, default=DEFAULT_TRAIN_FILE)
    parser.add_argument("--valid-file", type=Path, default=DEFAULT_VALID_FILE)
    parser.add_argument("--test-file", type=Path, default=DEFAULT_TEST_FILE)
    parser.add_argument("--baseline-summary", type=Path, default=DEFAULT_BASELINE_SUMMARY)
    parser.add_argument("--max-experiments", type=int, default=2)
    parser.add_argument("--research-log", type=Path, default=RESEARCH_LOG)
    parser.add_argument("--experiments-dir", type=Path, default=AUTORESEARCH_DIR)
    parser.add_argument(
        "--keep-non-promoted-weights",
        action="store_true",
        help="Keep checkpoint weight files for non-promoted candidates instead of pruning them after metrics are recorded.",
    )
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.experiments_dir.mkdir(parents=True, exist_ok=True)
    research_log = load_research_log(args.research_log)
    active_dataset_fingerprint = dataset_fingerprint(args.train_file, args.valid_file, args.test_file)
    real_cycle_count = sum(
        1
        for item in research_log
        if item.get("loop_version") == "real_v1" and item.get("dataset_fingerprint") == active_dataset_fingerprint
    )
    excluded_names = tested_candidate_names(research_log, active_dataset_fingerprint)
    baseline = load_promoted_baseline(args.baseline_summary)
    overlap_report = split_overlap_report(args.train_file, args.valid_file, args.test_file)
    if not PROMOTED_MODEL_REGISTRY.exists():
        write_json(
            PROMOTED_MODEL_REGISTRY,
            {
                "updated_at": datetime.now().isoformat(),
                "output_dir": baseline["output_dir"],
                "summary_path": baseline["summary_path"],
                "selection_reason": "Seeded from the current promoted baseline before autoresearch.",
                "validation_f1": baseline["validation_f1"],
                "validation_iou_f1": baseline["validation_iou_f1"],
                "test_f1": baseline["test_f1"],
                "test_iou_f1": baseline["test_iou_f1"],
            },
        )
    candidates = build_candidates(
        baseline,
        cycle_index=real_cycle_count,
        max_experiments=args.max_experiments,
        excluded_names=excluded_names,
    )

    cycle_record: Dict[str, Any] = {
        "loop_version": "real_v1",
        "cycle_number": real_cycle_count + 1,
        "timestamp": datetime.now().isoformat(),
        "dataset_fingerprint": active_dataset_fingerprint,
        "baseline": baseline,
        "dataset_overlap_report": overlap_report,
        "candidates": [],
        "promoted": None,
        "status": "in_progress",
    }

    print(
        json.dumps(
            {
                "baseline": baseline,
                "candidate_count": len(candidates),
                "promotion_safe": overlap_report["promotion_safe"],
                "exact_overlap_counts": overlap_report["exact_overlap_counts"],
            },
            indent=2,
        )
    )
    if args.dry_run:
        for candidate in candidates:
            output_dir = candidate_output_dir(args.experiments_dir, active_dataset_fingerprint, candidate.name)
            command = make_experiment_command(
                args.train_file,
                args.valid_file,
                args.test_file,
                output_dir,
                baseline,
                candidate,
            )
            cycle_record["candidates"].append(
                {"name": candidate.name, "rationale": candidate.rationale, "command": command, "dry_run": True}
            )
        cycle_record["status"] = "dry_run"
        print(json.dumps(cycle_record, indent=2))
        return

    promoted_payload: Optional[Dict[str, Any]] = None
    for candidate in candidates:
        output_dir = candidate_output_dir(args.experiments_dir, active_dataset_fingerprint, candidate.name)
        summary_path = output_dir / "training_summary.json"
        command = make_experiment_command(
            args.train_file,
            args.valid_file,
            args.test_file,
            output_dir,
            baseline,
            candidate,
        )
        started_at = time.time()
        run_result = run_experiment(command, cwd=PROJECT_ROOT)
        elapsed = round(time.time() - started_at, 3)
        candidate_record: Dict[str, Any] = {
            "name": candidate.name,
            "rationale": candidate.rationale,
            "command": command,
            "duration_seconds": elapsed,
            "returncode": int(run_result.returncode),
            "stdout_tail": run_result.stdout[-2000:],
            "stderr_tail": run_result.stderr[-2000:],
            "output_dir": str(output_dir),
        }

        if run_result.returncode == 0 and summary_path.exists():
            metrics = load_metrics(summary_path)
            candidate_record["metrics"] = metrics
            candidate_record["promotion_blocked_by_overlap"] = not overlap_report["promotion_safe"]
            candidate_record["promoted"] = overlap_report["promotion_safe"] and should_promote(metrics, baseline)
            if candidate_record["promoted"] and promoted_payload is None:
                promoted_payload = registry_payload(output_dir, summary_path, metrics, candidate)
                cycle_record["promoted"] = {
                    "name": candidate.name,
                    "summary_path": str(summary_path),
                    "metrics": metrics,
                }
                baseline = {
                    **baseline,
                    "summary_path": str(summary_path),
                    "output_dir": str(output_dir),
                    "validation_f1": metrics["validation_f1"],
                    "validation_iou_f1": metrics["validation_iou_f1"],
                    "test_f1": metrics["test_f1"],
                    "test_iou_f1": metrics["test_iou_f1"],
                }
        else:
            candidate_record["metrics"] = None
            candidate_record["promoted"] = False

        if not candidate_record["promoted"] and not args.keep_non_promoted_weights:
            removed_files = prune_candidate_checkpoint_weights(output_dir)
            candidate_record["checkpoint_cleanup"] = {
                "weights_pruned": True,
                "removed_files": removed_files,
            }
        else:
            candidate_record["checkpoint_cleanup"] = {
                "weights_pruned": False,
                "removed_files": [],
            }

        cycle_record["candidates"].append(candidate_record)

    if promoted_payload is not None:
        write_json(PROMOTED_MODEL_REGISTRY, promoted_payload)

    cycle_record["status"] = "completed"
    research_log.append(cycle_record)
    write_json(args.research_log, research_log)
    print(json.dumps(cycle_record, indent=2))


if __name__ == "__main__":
    main()
