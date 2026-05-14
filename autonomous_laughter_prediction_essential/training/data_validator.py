#!/usr/bin/env python3
"""
StandUp4AI Data Validation and Quality Framework
=================================================

Comprehensive validation system for ensuring dataset quality and integrity.
Provides automated quality checks, statistical analysis, and performance metrics.

Validation Categories:
- Data integrity and consistency
- Label accuracy verification
- Temporal alignment validation
- Cross-dataset compatibility
- Performance benchmarking
- Multilingual coverage analysis

Author: GCACU Team
Date: 2026-04-03
"""

import json
import logging
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
import hashlib
import re
from collections import Counter, defaultdict
import matplotlib.pyplot as plt
import seaborn as sns

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ValidationConfig:
    """Configuration for data validation."""

    # Quality thresholds
    min_confidence_score: float = 0.6
    min_laugh_density: float = 0.05  # 5% minimum laughter density
    max_laugh_density: float = 0.95  # 95% maximum laughter density
    min_word_coverage: float = 0.8   # 80% word coverage

    # Temporal validation
    max_gap_seconds: float = 5.0     # Maximum allowed gap in timestamps
    min_audio_duration: float = 30.0  # Minimum audio duration (seconds)
    max_audio_duration: float = 7200.0  # Maximum audio duration (2 hours)

    # Label consistency
    min_interannotator_agreement: float = 0.7
    min_label_confidence: float = 0.5

    # Multilingual requirements
    min_language_coverage: int = 10    # Minimum languages
    min_cultural_diversity: int = 5    # Minimum cultural contexts

    # Performance benchmarks
    target_f1_score: float = 0.4240    # GCACU multilingual baseline
    min_processing_speed: float = 1.0  # Minimum videos per hour


@dataclass
class ValidationResult:
    """Result of data validation."""

    validation_passed: bool
    validation_date: datetime
    total_checks: int
    passed_checks: int
    failed_checks: int
    warnings: List[str]
    errors: List[str]
    quality_metrics: Dict[str, float]
    recommendations: List[str]

    def get_pass_rate(self) -> float:
        """Calculate pass rate."""
        return self.passed_checks / self.total_checks if self.total_checks > 0 else 0.0

    def get_quality_score(self) -> float:
        """Calculate overall quality score (0-100)."""
        return (self.get_pass_rate() * 100)


class DataIntegrityValidator:
    """Validates data integrity and consistency."""

    def __init__(self, config: ValidationConfig):
        self.config = config

    def validate_file_structure(self, data_dir: Path) -> ValidationResult:
        """Validate directory structure and file existence."""
        checks = []
        passed = 0
        warnings = []
        errors = []

        # Check required directories
        required_dirs = ["audio", "transcripts", "processed"]
        for dir_name in required_dirs:
            dir_path = data_dir / dir_name
            if dir_path.exists():
                passed += 1
                checks.append(f"Directory {dir_name} exists")
            else:
                errors.append(f"Missing required directory: {dir_name}")
                checks.append(f"Directory {dir_name} missing")

        # Check file counts
        audio_files = list((data_dir / "audio").glob("*.wav")) if (data_dir / "audio").exists() else []
        transcript_files = list((data_dir / "transcripts").glob("*.json")) if (data_dir / "transcripts").exists() else []
        processed_files = list((data_dir / "processed").glob("*.jsonl")) if (data_dir / "processed").exists() else []

        checks.extend([
            f"Audio files: {len(audio_files)}",
            f"Transcript files: {len(transcript_files)}",
            f"Processed files: {len(processed_files)}"
        ])

        if len(audio_files) != len(transcript_files):
            warnings.append(f"Audio/transcript count mismatch: {len(audio_files)} vs {len(transcript_files)}")

        return ValidationResult(
            validation_passed=len(errors) == 0,
            validation_date=datetime.now(),
            total_checks=len(checks),
            passed_checks=passed,
            failed_checks=len(errors),
            warnings=warnings,
            errors=errors,
            quality_metrics={"file_integrity_score": passed / len(checks) if checks else 0},
            recommendations=[]
        )

    def validate_json_structure(self, json_file: Path) -> Tuple[bool, List[str]]:
        """Validate JSON file structure."""
        errors = []

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Check required fields
            required_fields = ["metadata", "data"]
            for field in required_fields:
                if field not in data:
                    errors.append(f"Missing required field: {field}")

            # Validate data structure
            if "data" in data:
                if not isinstance(data["data"], list):
                    errors.append("Data field must be a list")
                else:
                    # Check each entry has required fields
                    for i, entry in enumerate(data["data"][:5]):  # Sample first 5
                        required_entry_fields = ["word", "timestamp"]
                        for req_field in required_entry_fields:
                            if req_field not in entry:
                                errors.append(f"Entry {i} missing field: {req_field}")

            return len(errors) == 0, errors

        except json.JSONDecodeError as e:
            return False, [f"Invalid JSON: {str(e)}"]
        except Exception as e:
            return False, [f"Error reading file: {str(e)}"]


class LabelAccuracyValidator:
    """Validates laughter label accuracy and consistency."""

    def __init__(self, config: ValidationConfig):
        self.config = config

    def validate_laughter_labels(self, gcacu_data: Dict) -> ValidationResult:
        """Validate laughter label quality."""
        checks = []
        passed = 0
        warnings = []
        errors = []

        data_entries = gcacu_data.get("data", [])
        if not data_entries:
            errors.append("No data entries found")
            return ValidationResult(
                validation_passed=False,
                validation_date=datetime.now(),
                total_checks=0,
                passed_checks=0,
                failed_checks=1,
                warnings=warnings,
                errors=errors,
                quality_metrics={},
                recommendations=[]
            )

        # Check laughter label coverage
        laughter_entries = [e for e in data_entries if e.get("laughter_type")]
        laugh_density = len(laughter_entries) / len(data_entries)

        checks.append(f"Laughter density: {laugh_density:.3f}")
        if self.config.min_laugh_density <= laugh_density <= self.config.max_laugh_density:
            passed += 1
        else:
            warnings.append(f"Laughter density {laugh_density:.3f} outside recommended range")

        # Check confidence scores
        confidences = [e.get("laughter_confidence", 0.0) for e in laughter_entries]
        if confidences:
            avg_confidence = np.mean(confidences)
            checks.append(f"Average confidence: {avg_confidence:.3f}")
            if avg_confidence >= self.config.min_label_confidence:
                passed += 1
            else:
                errors.append(f"Average confidence {avg_confidence:.3f} below threshold")

        # Check label type distribution
        discrete_count = len([e for e in laughter_entries if e.get("laughter_type") == "discrete"])
        continuous_count = len([e for e in laughter_entries if e.get("laughter_type") == "continuous"])
        total_laughter = len(laughter_entries)

        if total_laughter > 0:
            discrete_ratio = discrete_count / total_laughter
            checks.append(f"Discrete/Continuous ratio: {discrete_ratio:.3f}")

        # Validate WESR taxonomy compliance
        valid_types = ["discrete", "continuous", None]
        invalid_types = [e.get("laughter_type") for e in data_entries if e.get("laughter_type") not in valid_types]
        if invalid_types:
            errors.append(f"Invalid laughter types found: {set(invalid_types)}")
        else:
            passed += 1
            checks.append("WESR taxonomy compliance: OK")

        return ValidationResult(
            validation_passed=len(errors) == 0,
            validation_date=datetime.now(),
            total_checks=len(checks),
            passed_checks=passed,
            failed_checks=len(errors),
            warnings=warnings,
            errors=errors,
            quality_metrics={
                "laugh_density": laugh_density,
                "avg_confidence": np.mean(confidences) if confidences else 0.0,
                "wesr_compliance": 1.0 if not invalid_types else 0.0
            },
            recommendations=self._generate_label_recommendations(laugh_density, confidences)
        )

    def _generate_label_recommendations(self, laugh_density: float, confidences: List[float]) -> List[str]:
        """Generate recommendations based on label quality."""
        recommendations = []

        if laugh_density < self.config.min_laugh_density:
            recommendations.append("Consider adding more laughter labels or reviewing detection thresholds")
        elif laugh_density > self.config.max_laugh_density:
            recommendations.append("High laughter density - consider refining detection criteria")

        if confidences and np.mean(confidences) < self.config.min_label_confidence:
            recommendations.append("Low confidence scores detected - review detection algorithm")

        return recommendations


class TemporalAlignmentValidator:
    """Validates temporal alignment of words and timestamps."""

    def __init__(self, config: ValidationConfig):
        self.config = config

    def validate_timestamps(self, gcacu_data: Dict) -> ValidationResult:
        """Validate timestamp quality and alignment."""
        checks = []
        passed = 0
        warnings = []
        errors = []

        data_entries = gcacu_data.get("data", [])
        if not data_entries:
            errors.append("No data entries for timestamp validation")
            return self._create_result(checks, passed, warnings, errors)

        # Extract timestamps
        timestamps = [e.get("timestamp", 0.0) for e in data_entries]
        timestamps = sorted([t for t in timestamps if t > 0])

        if not timestamps:
            errors.append("No valid timestamps found")
            return self._create_result(checks, passed, warnings, errors)

        # Check timestamp continuity
        gaps = []
        for i in range(1, len(timestamps)):
            gap = timestamps[i] - timestamps[i-1]
            gaps.append(gap)

        avg_gap = np.mean(gaps)
        max_gap = np.max(gaps)

        checks.append(f"Average timestamp gap: {avg_gap:.3f}s")
        checks.append(f"Maximum timestamp gap: {max_gap:.3f}s")

        if max_gap <= self.config.max_gap_seconds:
            passed += 1
        else:
            warnings.append(f"Large timestamp gaps detected (max: {max_gap:.3f}s)")

        # Check timestamp ordering
        is_sorted = all(timestamps[i] <= timestamps[i+1] for i in range(len(timestamps)-1))
        if is_sorted:
            passed += 1
            checks.append("Timestamp ordering: OK")
        else:
            errors.append("Timestamps not in chronological order")

        # Check audio duration consistency
        total_duration = timestamps[-1] - timestamps[0] if timestamps else 0
        checks.append(f"Total audio duration: {total_duration:.1f}s")

        if self.config.min_audio_duration <= total_duration <= self.config.max_audio_duration:
            passed += 1
        else:
            warnings.append(f"Audio duration {total_duration:.1f}s outside recommended range")

        # Check timestamp resolution
        timestamp_precision = len(str(timestamps[0]).split('.')[-1]) if timestamps else 0
        checks.append(f"Timestamp precision: {timestamp_precision} decimal places")

        if timestamp_precision >= 2:  # At least millisecond precision
            passed += 1

        return self._create_result(checks, passed, warnings, errors)

    def _create_result(self, checks: List[str], passed: int, warnings: List[str], errors: List[str]) -> ValidationResult:
        """Create validation result."""
        return ValidationResult(
            validation_passed=len(errors) == 0,
            validation_date=datetime.now(),
            total_checks=len(checks),
            passed_checks=passed,
            failed_checks=len(errors),
            warnings=warnings,
            errors=errors,
            quality_metrics={
                "timestamp_quality": passed / len(checks) if checks else 0,
                "temporal_alignment": 1.0 if len(errors) == 0 else 0.0
            },
            recommendations=[]
        )


class MultilingualCoverageValidator:
    """Validates multilingual and cultural diversity coverage."""

    def __init__(self, config: ValidationConfig):
        self.config = config

    def validate_language_coverage(self, gcacu_data: Dict) -> ValidationResult:
        """Validate language and cultural diversity."""
        checks = []
        passed = 0
        warnings = []
        errors = []

        data_entries = gcacu_data.get("data", [])
        if not data_entries:
            errors.append("No data entries for language validation")
            return self._create_result(checks, passed, warnings, errors)

        # Analyze language distribution
        languages = [e.get("language", "unknown") for e in data_entries]
        language_counts = Counter(languages)

        checks.append(f"Total languages: {len(language_counts)}")
        checks.append(f"Language distribution: {dict(language_counts.most_common(5))}")

        if len(language_counts) >= self.config.min_language_coverage:
            passed += 1
        else:
            warnings.append(f"Language coverage ({len(language_counts)}) below minimum ({self.config.min_language_coverage})")

        # Analyze cultural contexts
        cultural_contexts = [e.get("cultural_context", "unknown") for e in data_entries]
        culture_counts = Counter(cultural_contexts)

        checks.append(f"Total cultural contexts: {len(culture_counts)}")
        checks.append(f"Cultural distribution: {dict(culture_counts.most_common(5))}")

        if len(culture_counts) >= self.config.min_cultural_diversity:
            passed += 1
        else:
            warnings.append(f"Cultural diversity ({len(culture_counts)}) below minimum ({self.config.min_cultural_diversity})")

        # Check comedy styles
        comedy_styles = [e.get("comedy_style", "unknown") for e in data_entries]
        style_counts = Counter(comedy_styles)

        checks.append(f"Comedy styles: {len(style_counts)}")
        checks.append(f"Style distribution: {dict(style_counts)}")

        # Validate language codes
        valid_language_codes = ["en", "hi", "es", "fr", "de", "ja", "ko", "zh", "ar", "pt"]
        invalid_languages = [lang for lang in language_counts.keys() if lang not in valid_language_codes and lang != "unknown"]

        if not invalid_languages:
            passed += 1
            checks.append("Language code validation: OK")
        else:
            warnings.append(f"Unrecognized language codes: {invalid_languages}")

        return self._create_result(checks, passed, warnings, errors)

    def _create_result(self, checks: List[str], passed: int, warnings: List[str], errors: List[str]) -> ValidationResult:
        """Create validation result."""
        return ValidationResult(
            validation_passed=len(errors) == 0,
            validation_date=datetime.now(),
            total_checks=len(checks),
            passed_checks=passed,
            failed_checks=len(errors),
            warnings=warnings,
            errors=errors,
            quality_metrics={
                "language_diversity": passed / len(checks) if checks else 0,
                "cultural_coverage": 1.0 if len(errors) == 0 else 0.0
            },
            recommendations=[]
        )


class PerformanceBenchmark:
    """Benchmarks dataset quality against performance targets."""

    def __init__(self, config: ValidationConfig):
        self.config = config

    def benchmark_gcacu_performance(self, validation_results: List[ValidationResult]) -> Dict:
        """Benchmark dataset quality against GCACU targets."""
        overall_quality = np.mean([r.get_quality_score() for r in validation_results])

        return {
            "dataset_quality_score": overall_quality,
            "target_f1_score": self.config.target_f1_score,
            "expected_f1_range": {
                "min": overall_quality / 100 * self.config.target_f1_score,
                "max": min(overall_quality / 100 * self.config.target_f1_score * 1.2, 1.0)
            },
            "readiness_assessment": self._assess_readiness(overall_quality),
            "recommendations": self._generate_performance_recommendations(overall_quality)
        }

    def _assess_readiness(self, quality_score: float) -> str:
        """Assess dataset readiness for GCACU training."""
        if quality_score >= 90:
            return "EXCELLENT - Ready for production training"
        elif quality_score >= 75:
            return "GOOD - Suitable for training with minor improvements"
        elif quality_score >= 60:
            return "ACCEPTABLE - Usable with recommended improvements"
        else:
            return "NEEDS IMPROVEMENT - Requires significant quality enhancements"

    def _generate_performance_recommendations(self, quality_score: float) -> List[str]:
        """Generate performance improvement recommendations."""
        recommendations = []

        if quality_score < 75:
            recommendations.append("Focus on improving label accuracy and consistency")
            recommendations.append("Increase laughter label coverage for better training")

        if quality_score < 90:
            recommendations.append("Enhance temporal alignment precision")
            recommendations.append("Expand multilingual coverage for better generalization")

        return recommendations


class StandUp4AIValidator:
    """
    Main validation orchestrator for StandUp4AI dataset.

    Provides comprehensive validation framework combining all validators.
    """

    def __init__(self, data_dir: Path, config: ValidationConfig = None):
        self.data_dir = data_dir
        self.config = config or ValidationConfig()

        # Initialize validators
        self.integrity_validator = DataIntegrityValidator(self.config)
        self.label_validator = LabelAccuracyValidator(self.config)
        self.temporal_validator = TemporalAlignmentValidator(self.config)
        self.multilingual_validator = MultilingualCoverageValidator(self.config)
        self.benchmark = PerformanceBenchmark(self.config)

    def validate_full_dataset(self) -> Dict:
        """
        Perform comprehensive dataset validation.

        Returns:
            Comprehensive validation report
        """
        logger.info("Starting comprehensive StandUp4AI dataset validation")

        validation_report = {
            "validation_date": datetime.now().isoformat(),
            "data_directory": str(self.data_dir),
            "validation_summary": {},
            "detailed_results": {},
            "quality_assessment": {},
            "recommendations": []
        }

        # Phase 1: File structure validation
        logger.info("Phase 1: Validating file structure")
        integrity_result = self.integrity_validator.validate_file_structure(self.data_dir)
        validation_report["detailed_results"]["file_integrity"] = integrity_result.__dict__

        # Phase 2: Content validation (sample files)
        logger.info("Phase 2: Validating content quality")
        processed_files = list((self.data_dir / "processed").glob("*.jsonl")) if (self.data_dir / "processed").exists() else []

        if not processed_files:
            logger.warning("No processed files found for content validation")
        else:
            content_results = []
            for sample_file in processed_files[:5]:  # Sample first 5 files
                try:
                    with open(sample_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    # Run all content validators
                    label_result = self.label_validator.validate_laughter_labels(data)
                    temporal_result = self.temporal_validator.validate_timestamps(data)
                    multilingual_result = self.multilingual_validator.validate_language_coverage(data)

                    content_results.extend([label_result, temporal_result, multilingual_result])

                except Exception as e:
                    logger.error(f"Error validating {sample_file}: {e}")

            validation_report["detailed_results"]["content_quality"] = [r.__dict__ for r in content_results]

            # Phase 3: Performance benchmarking
            logger.info("Phase 3: Benchmarking performance")
            benchmark_results = self.benchmark.benchmark_gcacu_performance(content_results)
            validation_report["quality_assessment"] = benchmark_results

        # Generate summary
        total_checks = sum(r.get("total_checks", 0) for r in validation_report["detailed_results"].values() if isinstance(r, dict))
        total_passed = sum(r.get("passed_checks", 0) for r in validation_report["detailed_results"].values() if isinstance(r, dict))

        validation_report["validation_summary"] = {
            "total_checks_performed": total_checks,
            "checks_passed": total_passed,
            "overall_pass_rate": total_passed / total_checks if total_checks > 0 else 0,
            "validation_status": "PASSED" if len(validation_report["detailed_results"].get("file_integrity", {}).get("errors", [])) == 0 else "NEEDS_ATTENTION"
        }

        # Compile recommendations
        all_recommendations = []
        for result in validation_report["detailed_results"].values():
            if isinstance(result, dict) and "recommendations" in result:
                all_recommendations.extend(result["recommendations"])

        validation_report["recommendations"] = list(set(all_recommendations))

        # Save report
        self._save_validation_report(validation_report)

        return validation_report

    def _save_validation_report(self, report: Dict):
        """Save validation report to file."""
        report_file = self.data_dir / f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info(f"Validation report saved to {report_file}")

        # Also create a summary text file
        summary_file = self.data_dir / "validation_summary.txt"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("StandUp4AI Dataset Validation Summary\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Validation Date: {report['validation_date']}\n")
            f.write(f"Data Directory: {report['data_directory']}\n\n")
            f.write("Summary:\n")
            f.write(f"  Total Checks: {report['validation_summary']['total_checks_performed']}\n")
            f.write(f"  Checks Passed: {report['validation_summary']['checks_passed']}\n")
            f.write(f"  Pass Rate: {report['validation_summary']['overall_pass_rate']:.1%}\n")
            f.write(f"  Status: {report['validation_summary']['validation_status']}\n\n")

            if "quality_assessment" in report and "readiness_assessment" in report["quality_assessment"]:
                f.write(f"Readiness: {report['quality_assessment']['readiness_assessment']}\n")

            if report["recommendations"]:
                f.write("\nRecommendations:\n")
                for i, rec in enumerate(report["recommendations"], 1):
                    f.write(f"  {i}. {rec}\n")

        logger.info(f"Validation summary saved to {summary_file}")


def main():
    """Main execution function for data validation."""
    print("🔍 StandUp4AI Data Validation Framework")
    print("=" * 50)

    # Initialize validator
    data_dir = Path("/Users/Subho/autonomous_laughter_prediction_essential/data")
    validator = StandUp4AIValidator(data_dir)

    print("📋 Running comprehensive validation...")
    print("🎯 Validation phases:")
    print("  1. File structure integrity")
    print("  2. Content quality validation")
    print("  3. Performance benchmarking")
    print("  4. Multilingual coverage")
    print("  5. Temporal alignment")
    print()

    # Run validation
    validation_report = validator.validate_full_dataset()

    # Display summary
    print("\n" + "=" * 50)
    print("📊 VALIDATION SUMMARY")
    print("=" * 50)
    print(f"Status: {validation_report['validation_summary']['validation_status']}")
    print(f"Pass Rate: {validation_report['validation_summary']['overall_pass_rate']:.1%}")
    print(f"Checks Passed: {validation_report['validation_summary']['checks_passed']}/{validation_report['validation_summary']['total_checks_performed']}")

    if validation_report.get("quality_assessment", {}).get("readiness_assessment"):
        print(f"\n🎯 Readiness: {validation_report['quality_assessment']['readiness_assessment']}")

    if validation_report["recommendations"]:
        print(f"\n💡 Recommendations:")
        for i, rec in enumerate(validation_report["recommendations"], 1):
            print(f"  {i}. {rec}")

    print(f"\n📁 Detailed reports saved to: {data_dir}")


if __name__ == "__main__":
    main()