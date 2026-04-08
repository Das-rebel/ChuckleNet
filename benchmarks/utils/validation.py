"""
Data Validation and Quality Assurance System

Comprehensive validation framework for ensuring data integrity,
quality, and consistency across all benchmark datasets.
"""

import os
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass, field
from collections import defaultdict, Counter
import numpy as np
import torch
import torchaudio
import cv2
from PIL import Image


@dataclass
class ValidationResult:
    """Result of a validation check"""
    check_name: str
    passed: bool
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    severity: str = 'error'  # 'error', 'warning', 'info'


@dataclass
class DatasetValidationReport:
    """Comprehensive validation report for a dataset"""
    dataset_name: str
    total_checks: int = 0
    passed_checks: int = 0
    failed_checks: int = 0
    warnings: int = 0
    results: List[ValidationResult] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)

    def add_result(self, result: ValidationResult):
        """Add a validation result"""
        self.results.append(result)
        self.total_checks += 1

        if result.passed:
            self.passed_checks += 1
        elif result.severity == 'warning':
            self.failed_checks += 1
            self.warnings += 1
        else:
            self.failed_checks += 1

    def get_failed_results(self) -> List[ValidationResult]:
        """Get all failed validation results"""
        return [r for r in self.results if not r.passed]

    def get_warnings(self) -> List[ValidationResult]:
        """Get all warning results"""
        return [r for r in self.results if not r.passed and r.severity == 'warning']

    def save_report(self, save_path: Union[str, Path]):
        """Save validation report to file"""
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)

        report_data = {
            'dataset_name': self.dataset_name,
            'summary': {
                'total_checks': self.total_checks,
                'passed_checks': self.passed_checks,
                'failed_checks': self.failed_checks,
                'warnings': self.warnings,
                'success_rate': self.passed_checks / self.total_checks if self.total_checks > 0 else 0
            },
            'results': [
                {
                    'check_name': r.check_name,
                    'passed': r.passed,
                    'message': r.message,
                    'details': r.details,
                    'severity': r.severity
                }
                for r in self.results
            ],
            'recommendations': self.recommendations
        }

        with open(save_path, 'w') as f:
            json.dump(report_data, f, indent=2)

        print(f"Validation report saved to {save_path}")


class DataValidator:
    """Comprehensive data validation system"""

    def __init__(self, dataset_name: str, data_path: Union[str, Path]):
        """
        Initialize data validator.

        Args:
            dataset_name: Name of the dataset being validated
            data_path: Path to dataset directory
        """
        self.dataset_name = dataset_name
        self.data_path = Path(data_path)
        self.report = DatasetValidationReport(dataset_name=dataset_name)

    def validate_all(self,
                    samples: List[Any],
                    checks: Optional[List[str]] = None) -> DatasetValidationReport:
        """
        Run all validation checks.

        Args:
            samples: List of data samples to validate
            checks: List of specific checks to run (None = run all)

        Returns:
            Comprehensive validation report
        """
        print(f"Starting comprehensive validation for {self.dataset_name}...")

        # Define available checks
        all_checks = [
            'file_exists',
            'file_readable',
            'data_integrity',
            'label_consistency',
            'metadata_completeness',
            'audio_quality',
            'video_quality',
            'text_quality',
            'class_balance',
            'duplicate_detection',
            'memory_requirements',
            'data_format_compliance'
        ]

        # Filter checks if specific ones requested
        if checks is not None:
            all_checks = [c for c in all_checks if c in checks]

        # Run validation checks
        for check in all_checks:
            try:
                check_method = getattr(self, f'check_{check}')
                result = check_method(samples)
                self.report.add_result(result)
            except Exception as e:
                print(f"Error running check {check}: {e}")
                self.report.add_result(ValidationResult(
                    check_name=check,
                    passed=False,
                    message=f"Validation check failed with error: {str(e)}",
                    severity='error'
                ))

        # Generate recommendations
        self._generate_recommendations()

        # Print summary
        self._print_summary()

        return self.report

    def check_file_exists(self, samples: List[Any]) -> ValidationResult:
        """Check if all referenced files exist"""
        missing_files = []

        for sample in samples:
            if hasattr(sample, 'audio_path') and sample.audio_path:
                if not Path(sample.audio_path).exists():
                    missing_files.append(sample.audio_path)

            if hasattr(sample, 'video_path') and sample.video_path:
                if not Path(sample.video_path).exists():
                    missing_files.append(sample.video_path)

        passed = len(missing_files) == 0
        message = f"All files exist" if passed else f"Missing {len(missing_files)} files"

        return ValidationResult(
            check_name='file_exists',
            passed=passed,
            message=message,
            details={'missing_files': missing_files[:10]},  # Limit output
            severity='error' if not passed else 'info'
        )

    def check_file_readable(self, samples: List[Any]) -> ValidationResult:
        """Check if all files are readable"""
        unreadable_files = []

        for sample in samples:
            if hasattr(sample, 'audio_path') and sample.audio_path:
                if Path(sample.audio_path).exists():
                    try:
                        torchaudio.load(sample.audio_path)
                    except Exception as e:
                        unreadable_files.append((sample.audio_path, str(e)))

            if hasattr(sample, 'video_path') and sample.video_path:
                if Path(sample.video_path).exists():
                    try:
                        cap = cv2.VideoCapture(str(sample.video_path))
                        if not cap.isOpened():
                            unreadable_files.append((sample.video_path, "Cannot open video"))
                        cap.release()
                    except Exception as e:
                        unreadable_files.append((sample.video_path, str(e)))

        passed = len(unreadable_files) == 0
        message = f"All files are readable" if passed else f"{len(unreadable_files)} files are unreadable"

        return ValidationResult(
            check_name='file_readable',
            passed=passed,
            message=message,
            details={'unreadable_files': unreadable_files[:10]},
            severity='error' if not passed else 'info'
        )

    def check_data_integrity(self, samples: List[Any]) -> ValidationResult:
        """Check data integrity and consistency"""
        issues = []

        for i, sample in enumerate(samples):
            # Check required fields
            if not hasattr(sample, 'text') or not sample.text:
                issues.append(f"Sample {i}: Missing or empty text")

            if not hasattr(sample, 'label') or sample.label is None:
                issues.append(f"Sample {i}: Missing label")

            # Check data types
            if hasattr(sample, 'label') and sample.label is not None:
                if not isinstance(sample.label, (int, float, bool)):
                    issues.append(f"Sample {i}: Invalid label type {type(sample.label)}")

        passed = len(issues) == 0
        message = f"Data integrity check passed" if passed else f"Found {len(issues)} integrity issues"

        return ValidationResult(
            check_name='data_integrity',
            passed=passed,
            message=message,
            details={'issues': issues[:20]},
            severity='error' if not passed else 'info'
        )

    def check_label_consistency(self, samples: List[Any]) -> ValidationResult:
        """Check label consistency and ranges"""
        label_issues = []

        for i, sample in enumerate(samples):
            if hasattr(sample, 'label') and sample.label is not None:
                # Check binary labels
                if isinstance(sample.label, (int, bool)):
                    if sample.label not in [0, 1]:
                        label_issues.append(f"Sample {i}: Binary label {sample.label} not in [0,1]")

                # Check regression labels
                elif isinstance(sample.label, float):
                    if not 0.0 <= sample.label <= 1.0:
                        label_issues.append(f"Sample {i}: Regression label {sample.label} not in [0.0,1.0]")

        passed = len(label_issues) == 0
        message = f"Label consistency check passed" if passed else f"Found {len(label_issues)} label inconsistencies"

        return ValidationResult(
            check_name='label_consistency',
            passed=passed,
            message=message,
            details={'issues': label_issues[:20]},
            severity='error' if not passed else 'info'
        )

    def check_metadata_completeness(self, samples: List[Any]) -> ValidationResult:
        """Check metadata completeness"""
        metadata_issues = []
        samples_without_speaker = 0
        samples_without_show = 0

        for i, sample in enumerate(samples):
            if hasattr(sample, 'speaker_id') and not sample.speaker_id:
                samples_without_speaker += 1

            if hasattr(sample, 'show_id') and not sample.show_id:
                samples_without_show += 1

        # Calculate completeness ratios
        speaker_completeness = 1.0 - (samples_without_speaker / len(samples))
        show_completeness = 1.0 - (samples_without_show / len(samples))

        # Warn if less than 80% complete
        if speaker_completeness < 0.8:
            metadata_issues.append(f"Speaker ID only {speaker_completeness:.1%} complete")
        if show_completeness < 0.8:
            metadata_issues.append(f"Show ID only {show_completeness:.1%} complete")

        passed = len(metadata_issues) == 0
        message = f"Metadata completeness check passed" if passed else f"Found {len(metadata_issues)} metadata issues"

        return ValidationResult(
            check_name='metadata_completeness',
            passed=passed,
            message=message,
            details={
                'issues': metadata_issues,
                'speaker_completeness': speaker_completeness,
                'show_completeness': show_completeness
            },
            severity='warning' if not passed else 'info'
        )

    def check_audio_quality(self, samples: List[Any]) -> ValidationResult:
        """Check audio quality for samples with audio"""
        audio_issues = []
        duration_stats = []

        for sample in samples:
            if hasattr(sample, 'audio_path') and sample.audio_path:
                if Path(sample.audio_path).exists():
                    try:
                        waveform, sample_rate = torchaudio.load(sample.audio_path)
                        duration = waveform.shape[1] / sample_rate
                        duration_stats.append(duration)

                        # Check for very short or long audio
                        if duration < 0.5:
                            audio_issues.append(f"{sample.audio_path}: Very short ({duration:.2f}s)")
                        elif duration > 30:
                            audio_issues.append(f"{sample.audio_path}: Very long ({duration:.2f}s)")

                        # Check for silent audio
                        if torch.max(torch.abs(waveform)) < 1e-6:
                            audio_issues.append(f"{sample.audio_path}: Silent audio")

                    except Exception as e:
                        audio_issues.append(f"{sample.audio_path}: Error loading - {str(e)}")

        passed = len(audio_issues) == 0
        message = f"Audio quality check passed" if passed else f"Found {len(audio_issues)} audio quality issues"

        # Calculate duration statistics
        duration_summary = {}
        if duration_stats:
            duration_summary = {
                'mean': np.mean(duration_stats),
                'std': np.std(duration_stats),
                'min': np.min(duration_stats),
                'max': np.max(duration_stats),
                'median': np.median(duration_stats)
            }

        return ValidationResult(
            check_name='audio_quality',
            passed=passed,
            message=message,
            details={
                'issues': audio_issues[:20],
                'duration_stats': duration_summary
            },
            severity='warning' if not passed else 'info'
        )

    def check_video_quality(self, samples: List[Any]) -> ValidationResult:
        """Check video quality for samples with video"""
        video_issues = []
        resolution_stats = []

        for sample in samples:
            if hasattr(sample, 'video_path') and sample.video_path:
                if Path(sample.video_path).exists():
                    try:
                        cap = cv2.VideoCapture(str(sample.video_path))
                        if cap.isOpened():
                            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                            fps = cap.get(cv2.CAP_PROP_FPS)
                            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

                            resolution_stats.append((width, height))

                            # Check resolution
                            if width < 320 or height < 240:
                                video_issues.append(f"{sample.video_path}: Low resolution ({width}x{height})")

                            # Check FPS
                            if fps < 10 or fps > 60:
                                video_issues.append(f"{sample.video_path}: Unusual FPS {fps}")

                            # Check duration
                            duration = frame_count / fps if fps > 0 else 0
                            if duration < 1.0:
                                video_issues.append(f"{sample.video_path}: Very short ({duration:.2f}s)")

                            cap.release()
                        else:
                            video_issues.append(f"{sample.video_path}: Cannot open video")

                    except Exception as e:
                        video_issues.append(f"{sample.video_path}: Error loading - {str(e)}")

        passed = len(video_issues) == 0
        message = f"Video quality check passed" if passed else f"Found {len(video_issues)} video quality issues"

        # Resolution statistics
        resolution_summary = {}
        if resolution_stats:
            widths = [r[0] for r in resolution_stats]
            heights = [r[1] for r in resolution_stats]
            resolution_summary = {
                'common_resolutions': Counter(resolution_stats).most_common(5),
                'width_range': (min(widths), max(widths)),
                'height_range': (min(heights), max(heights))
            }

        return ValidationResult(
            check_name='video_quality',
            passed=passed,
            message=message,
            details={
                'issues': video_issues[:20],
                'resolution_stats': resolution_summary
            },
            severity='warning' if not passed else 'info'
        )

    def check_text_quality(self, samples: List[Any]) -> ValidationResult:
        """Check text quality"""
        text_issues = []
        text_lengths = []

        for i, sample in enumerate(samples):
            if hasattr(sample, 'text') and sample.text:
                text_length = len(sample.text.split())
                text_lengths.append(text_length)

                # Check for very short or long text
                if text_length == 0:
                    text_issues.append(f"Sample {i}: Empty text")
                elif text_length < 3:
                    text_issues.append(f"Sample {i}: Very short text ({text_length} words)")
                elif text_length > 500:
                    text_issues.append(f"Sample {i}: Very long text ({text_length} words)")

                # Check for special characters or encoding issues
                if any(ord(c) > 127 for c in sample.text):
                    # Non-ASCII characters detected - might be OK but worth noting
                    pass

        passed = len(text_issues) == 0
        message = f"Text quality check passed" if passed else f"Found {len(text_issues)} text quality issues"

        # Text length statistics
        length_summary = {}
        if text_lengths:
            length_summary = {
                'mean': np.mean(text_lengths),
                'std': np.std(text_lengths),
                'min': np.min(text_lengths),
                'max': np.max(text_lengths),
                'median': np.median(text_lengths)
            }

        return ValidationResult(
            check_name='text_quality',
            passed=passed,
            message=message,
            details={
                'issues': text_issues[:20],
                'length_stats': length_summary
            },
            severity='warning' if not passed else 'info'
        )

    def check_class_balance(self, samples: List[Any]) -> ValidationResult:
        """Check class balance for classification tasks"""
        labels = []
        for sample in samples:
            if hasattr(sample, 'label') and sample.label is not None:
                if isinstance(sample.label, (int, bool)):
                    labels.append(int(sample.label))

        if not labels:
            return ValidationResult(
                check_name='class_balance',
                passed=True,
                message="No binary labels found for class balance check",
                details={},
                severity='info'
            )

        # Calculate class distribution
        label_counts = Counter(labels)
        total = len(labels)
        class_0_ratio = label_counts[0] / total
        class_1_ratio = label_counts[1] / total

        # Check for severe imbalance (less than 10% in either class)
        is_imbalanced = class_0_ratio < 0.1 or class_1_ratio < 0.1

        passed = not is_imbalanced
        message = f"Class balance check passed" if passed else f"Severe class imbalance detected"

        return ValidationResult(
            check_name='class_balance',
            passed=passed,
            message=message,
            details={
                'class_distribution': dict(label_counts),
                'class_0_ratio': class_0_ratio,
                'class_1_ratio': class_1_ratio,
                'imbalance_severity': 'severe' if is_imbalanced else 'acceptable'
            },
            severity='warning' if not passed else 'info'
        )

    def check_duplicate_detection(self, samples: List[Any]) -> ValidationResult:
        """Detect duplicate samples"""
        text_hashes = defaultdict(list)
        duplicates = []

        for i, sample in enumerate(samples):
            if hasattr(sample, 'text') and sample.text:
                # Create hash of text for comparison
                text_hash = hashlib.md5(sample.text.encode()).hexdigest()
                text_hashes[text_hash].append(i)

        # Find duplicates
        for text_hash, indices in text_hashes.items():
            if len(indices) > 1:
                duplicates.append({
                    'hash': text_hash,
                    'indices': indices,
                    'text': samples[indices[0]].text[:100]  # First 100 chars
                })

        passed = len(duplicates) == 0
        message = f"No duplicates found" if passed else f"Found {len(duplicates)} duplicate groups"

        return ValidationResult(
            check_name='duplicate_detection',
            passed=passed,
            message=message,
            details={
                'duplicates': duplicates[:10],
                'total_duplicate_samples': sum(len(d['indices']) for d in duplicates) - len(duplicates)
            },
            severity='warning' if not passed else 'info'
        )

    def check_memory_requirements(self, samples: List[Any]) -> ValidationResult:
        """Estimate memory requirements for dataset"""
        total_size = 0
        file_sizes = []

        for sample in samples:
            if hasattr(sample, 'audio_path') and sample.audio_path:
                if Path(sample.audio_path).exists():
                    file_size = Path(sample.audio_path).stat().st_size
                    file_sizes.append(file_size)
                    total_size += file_size

            if hasattr(sample, 'video_path') and sample.video_path:
                if Path(sample.video_path).exists():
                    file_size = Path(sample.video_path).stat().st_size
                    file_sizes.append(file_size)
                    total_size += file_size

        # Convert to GB
        total_size_gb = total_size / (1024 ** 3)

        # Warn if dataset is very large
        is_large = total_size_gb > 10  # More than 10GB

        passed = not is_large
        message = f"Memory requirements acceptable ({total_size_gb:.2f} GB)" if passed else f"Large dataset ({total_size_gb:.2f} GB)"

        return ValidationResult(
            check_name='memory_requirements',
            passed=passed,
            message=message,
            details={
                'total_size_gb': total_size_gb,
                'total_size_mb': total_size / (1024 ** 2),
                'num_files': len(file_sizes),
                'avg_file_size_mb': np.mean(file_sizes) / (1024 ** 2) if file_sizes else 0
            },
            severity='warning' if not passed else 'info'
        )

    def check_data_format_compliance(self, samples: List[Any]) -> ValidationResult:
        """Check compliance with expected data format"""
        compliance_issues = []

        for i, sample in enumerate(samples):
            # Check if sample has required attributes
            required_attrs = ['text', 'label']
            for attr in required_attrs:
                if not hasattr(sample, attr):
                    compliance_issues.append(f"Sample {i}: Missing required attribute {attr}")
                elif getattr(sample, attr) is None and attr != 'audio_path' and attr != 'video_path':
                    compliance_issues.append(f"Sample {i}: {attr} is None")

        passed = len(compliance_issues) == 0
        message = f"Data format compliance check passed" if passed else f"Found {len(compliance_issues)} compliance issues"

        return ValidationResult(
            check_name='data_format_compliance',
            passed=passed,
            message=message,
            details={'issues': compliance_issues[:20]},
            severity='error' if not passed else 'info'
        )

    def _generate_recommendations(self):
        """Generate recommendations based on validation results"""
        for result in self.report.results:
            if not result.passed:
                if result.check_name == 'file_exists':
                    self.report.recommendations.append(
                        "Ensure all referenced files are present in the data directory"
                    )
                elif result.check_name == 'class_balance':
                    self.report.recommendations.append(
                        "Consider class weighting or oversampling techniques to handle imbalance"
                    )
                elif result.check_name == 'audio_quality':
                    self.report.recommendations.append(
                        "Review audio quality and consider audio preprocessing/cleaning"
                    )
                elif result.check_name == 'duplicate_detection':
                    self.report.recommendations.append(
                        "Remove duplicate samples to prevent data leakage"
                    )
                elif result.check_name == 'memory_requirements':
                    self.report.recommendations.append(
                        "Consider data streaming or compression techniques for large datasets"
                    )

    def _print_summary(self):
        """Print validation summary"""
        print(f"\n{'='*60}")
        print(f"Validation Report for {self.dataset_name}")
        print(f"{'='*60}")
        print(f"Total Checks: {self.report.total_checks}")
        print(f"Passed: {self.report.passed_checks} ({self.report.passed_checks/self.report.total_checks*100:.1f}%)")
        print(f"Failed: {self.report.failed_checks}")
        print(f"Warnings: {self.report.warnings}")
        print(f"{'='*60}\n")

        if self.report.recommendations:
            print("Recommendations:")
            for i, rec in enumerate(self.report.recommendations, 1):
                print(f"  {i}. {rec}")
            print()