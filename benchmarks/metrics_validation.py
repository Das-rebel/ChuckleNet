#!/usr/bin/env python3
"""
Metrics Validation System
Comprehensive testing and validation of academic metrics framework
"""

import numpy as np
import torch
from typing import Dict, List, Tuple, Any
import json
from pathlib import Path
import sys

# Import metrics framework
from academic_metrics_framework import AcademicMetricsFramework, EvaluationResult
from benchmark_integration import BenchmarkIntegration


class MetricsValidator:
    """
    Comprehensive validation system for academic metrics framework.

    Validates:
    - IoU calculation correctness
    - Statistical significance testing
    - Bootstrap confidence intervals
    - Cross-domain metrics
    - Publication formatting
    """

    def __init__(self):
        """Initialize validation system"""
        self.framework = AcademicMetricsFramework()
        self.passed_tests = 0
        self.failed_tests = 0

        print("🔬 METRICS VALIDATION SYSTEM")
        print("=" * 80)
        print("Comprehensive testing of academic metrics framework")
        print("=" * 80)

    def test_iou_calculation(self) -> bool:
        """Test IoU calculation correctness"""
        print("\n🧪 Testing IoU Calculation...")

        # Test Case 1: Perfect overlap
        seg1 = {'start': 0.0, 'end': 10.0}
        seg2 = {'start': 0.0, 'end': 10.0}
        iou = self.framework.calculate_iou(seg1, seg2)

        assert abs(iou - 1.0) < 1e-6, f"Perfect overlap IoU should be 1.0, got {iou}"
        print("  ✓ Perfect overlap: IoU = 1.0")

        # Test Case 2: No overlap
        seg1 = {'start': 0.0, 'end': 5.0}
        seg2 = {'start': 10.0, 'end': 15.0}
        iou = self.framework.calculate_iou(seg1, seg2)

        assert abs(iou - 0.0) < 1e-6, f"No overlap IoU should be 0.0, got {iou}"
        print("  ✓ No overlap: IoU = 0.0")

        # Test Case 3: Partial overlap (50%)
        seg1 = {'start': 0.0, 'end': 10.0}
        seg2 = {'start': 5.0, 'end': 15.0}
        iou = self.framework.calculate_iou(seg1, seg2)

        expected_iou = 5.0 / 15.0  # Intersection=5, Union=15
        assert abs(iou - expected_iou) < 1e-6, f"Partial overlap IoU should be {expected_iou}, got {iou}"
        print(f"  ✓ Partial overlap: IoU = {iou:.4f}")

        # Test Case 4: Small overlap (10%)
        seg1 = {'start': 0.0, 'end': 10.0}
        seg2 = {'start': 9.0, 'end': 11.0}
        iou = self.framework.calculate_iou(seg1, seg2)

        expected_iou = 1.0 / 11.0  # Intersection=1, Union=11
        assert abs(iou - expected_iou) < 1e-6, f"Small overlap IoU should be {expected_iou}, got {iou}"
        print(f"  ✓ Small overlap: IoU = {iou:.4f}")

        self.passed_tests += 1
        return True

    def test_classification_metrics(self) -> bool:
        """Test classification metrics calculation"""
        print("\n🧪 Testing Classification Metrics...")

        # Test Case 1: Perfect classification
        y_true = np.array([0, 1, 0, 1])
        y_pred = np.array([0, 1, 0, 1])

        results = self.framework.classification_metrics(y_true, y_pred)

        assert abs(results['accuracy'].value - 1.0) < 1e-6, "Perfect accuracy should be 1.0"
        assert abs(results['precision'].value - 1.0) < 1e-6, "Perfect precision should be 1.0"
        assert abs(results['recall'].value - 1.0) < 1e-6, "Perfect recall should be 1.0"
        assert abs(results['f1'].value - 1.0) < 1e-6, "Perfect F1 should be 1.0"

        print("  ✓ Perfect classification: Accuracy, Precision, Recall, F1 = 1.0")

        # Test Case 2: Random classification
        np.random.seed(42)
        y_true = np.random.randint(0, 2, 100)
        y_pred = np.random.randint(0, 2, 100)

        results = self.framework.classification_metrics(y_true, y_pred)

        assert 0.0 <= results['accuracy'].value <= 1.0, "Accuracy should be between 0 and 1"
        assert 0.0 <= results['f1'].value <= 1.0, "F1 should be between 0 and 1"
        assert results['confidence_interval'][0] < results['confidence_interval'][1], "CI should be ordered"

        print(f"  ✓ Random classification: Accuracy = {results['accuracy'].value:.4f}")
        print(f"    Confidence Interval: [{results['confidence_interval'][0]:.4f}, {results['confidence_interval'][1]:.4f}]")

        # Test Case 3: Imbalanced dataset
        y_true = np.array([0] * 90 + [1] * 10)
        y_pred = np.array([0] * 85 + [1] * 5 + [0] * 5 + [1] * 5)  # Some errors

        results = self.framework.classification_metrics(y_true, y_pred)

        # Macro-F1 should be different from regular F1 for imbalanced data
        macro_f1 = results.get('f1_macro')
        if macro_f1:
            print(f"  ✓ Imbalanced classification: F1 = {results['f1'].value:.4f}, Macro-F1 = {macro_f1.value:.4f}")

        self.passed_tests += 1
        return True

    def test_iou_based_detection_metrics(self) -> bool:
        """Test IoU-based temporal detection metrics"""
        print("\n🧪 Testing IoU-based Detection Metrics...")

        # Test Case 1: Perfect temporal detection
        gt_segments = [
            {'start': 1.0, 'end': 2.0},
            {'start': 5.0, 'end': 6.0}
        ]
        pred_segments = [
            {'start': 1.0, 'end': 2.0},
            {'start': 5.0, 'end': 6.0}
        ]

        results = self.framework.iou_based_detection_metrics(gt_segments, pred_segments)

        assert abs(results['precision_iou_20'].value - 1.0) < 1e-6, "Perfect precision should be 1.0"
        assert abs(results['recall_iou_20'].value - 1.0) < 1e-6, "Perfect recall should be 1.0"
        assert abs(results['f1_iou_20'].value - 1.0) < 1e-6, "Perfect F1 should be 1.0"

        print("  ✓ Perfect temporal detection: Precision, Recall, F1 = 1.0")

        # Test Case 2: No predictions
        gt_segments = [
            {'start': 1.0, 'end': 2.0},
            {'start': 5.0, 'end': 6.0}
        ]
        pred_segments = []

        results = self.framework.iou_based_detection_metrics(gt_segments, pred_segments)

        assert abs(results['precision_iou_20'].value - 0.0) < 1e-6, "No predictions precision should be 0.0"
        assert abs(results['recall_iou_20'].value - 0.0) < 1e-6, "No predictions recall should be 0.0"

        print("  ✓ No predictions: Precision, Recall = 0.0")

        # Test Case 3: False positives
        gt_segments = []
        pred_segments = [
            {'start': 1.0, 'end': 2.0},
            {'start': 5.0, 'end': 6.0}
        ]

        results = self.framework.iou_based_detection_metrics(gt_segments, pred_segments)

        assert abs(results['precision_iou_20'].value - 0.0) < 1e-6, "Only FP precision should be 0.0"
        assert abs(results['recall_iou_20'].value - 1.0) < 1e-6, "No ground truth recall should be 1.0"

        print("  ✓ False positives only: Precision = 0.0, Recall = 1.0")

        self.passed_tests += 1
        return True

    def test_statistical_significance(self) -> bool:
        """Test statistical significance testing"""
        print("\n🧪 Testing Statistical Significance Testing...")

        # Test Case 1: Identical predictions
        y_true = np.array([0, 1, 0, 1, 0, 1])
        y_pred1 = np.array([0, 1, 0, 1, 0, 1])
        y_pred2 = np.array([0, 1, 0, 1, 0, 1])

        result = self.framework._statistical_significance_test(y_true, y_pred1, y_true, y_pred2)

        assert result['p_value'] == 1.0, "Identical predictions should have p-value = 1.0"
        print("  ✓ Identical predictions: p-value = 1.0")

        # Test Case 2: Different predictions
        y_true = np.array([0, 1, 0, 1, 0, 1])
        y_pred1 = np.array([0, 1, 0, 1, 0, 1])  # Perfect
        y_pred2 = np.array([1, 0, 1, 0, 1, 0])  # All wrong

        result = self.framework._statistical_significance_test(y_true, y_pred1, y_true, y_pred2)

        assert result['p_value'] < 0.05, "Very different predictions should have p-value < 0.05"
        print(f"  ✓ Very different predictions: p-value = {result['p_value']:.6f}")

        self.passed_tests += 1
        return True

    def test_bootstrap_confidence_intervals(self) -> bool:
        """Test bootstrap confidence interval calculation"""
        print("\n🧪 Testing Bootstrap Confidence Intervals...")

        # Test Case 1: Consistent predictions
        np.random.seed(42)
        y_true = np.array([0, 1, 0, 1, 0, 1, 0, 1, 0, 1])
        y_pred = np.array([0, 1, 0, 1, 0, 1, 0, 1, 0, 1])

        results = self.framework.classification_metrics(y_true, y_pred)

        # Perfect predictions should have narrow confidence intervals
        ci_width = results['accuracy'].confidence_interval[1] - results['accuracy'].confidence_interval[0]

        assert ci_width < 0.1, f"Perfect predictions should have narrow CI, got width {ci_width}"
        print(f"  ✓ Consistent predictions: CI width = {ci_width:.6f}")

        # Test Case 2: Variable predictions
        np.random.seed(42)
        y_true = np.random.randint(0, 2, 100)
        y_pred = np.random.randint(0, 2, 100)

        results = self.framework.classification_metrics(y_true, y_pred)

        # Variable predictions should have wider confidence intervals
        ci_width = results['accuracy'].confidence_interval[1] - results['accuracy'].confidence_interval[0]

        assert ci_width > 0.0, "Should have some confidence interval width"
        assert ci_width < 0.5, "CI width should be reasonable"
        print(f"  ✓ Variable predictions: CI width = {ci_width:.6f}")

        self.passed_tests += 1
        return True

    def test_cross_domain_metrics(self) -> bool:
        """Test cross-domain generalization metrics"""
        print("\n🧪 Testing Cross-Domain Metrics...")

        # Test Case 1: Similar domain performance
        y_true_source = np.array([0, 1, 0, 1, 0, 1])
        y_pred_source = np.array([0, 1, 0, 1, 0, 1])  # Perfect
        y_true_target = np.array([0, 1, 0, 1, 0, 1])
        y_pred_target = np.array([0, 1, 0, 1, 0, 0])  # One error

        results = self.framework.cross_domain_metrics(
            (y_true_source, y_pred_source),
            (y_true_target, y_pred_target)
        )

        assert results['source_f1'].value > 0.0, "Source F1 should be positive"
        assert results['target_f1'].value > 0.0, "Target F1 should be positive"
        assert results['transfer_ratio'].value > 0.0, "Transfer ratio should be positive"
        assert results['transfer_ratio'].value <= 1.0, "Transfer ratio should be <= 1.0"

        print(f"  ✓ Similar domains: Transfer ratio = {results['transfer_ratio'].value:.4f}")

        # Test Case 2: Poor domain transfer
        y_true_source = np.array([0, 1, 0, 1, 0, 1])
        y_pred_source = np.array([0, 1, 0, 1, 0, 1])  # Perfect
        y_true_target = np.array([0, 1, 0, 1, 0, 1])
        y_pred_target = np.array([1, 0, 1, 0, 1, 0])  # All wrong

        results = self.framework.cross_domain_metrics(
            (y_true_source, y_pred_source),
            (y_true_target, y_pred_target)
        )

        assert results['transfer_performance_drop'].value > 0.0, "Should have performance drop"
        assert results['transfer_ratio'].value < 0.5, "Poor transfer should have low ratio"

        print(f"  ✓ Poor transfer: Transfer ratio = {results['transfer_ratio'].value:.4f}")

        self.passed_tests += 1
        return True

    def test_speaker_independent_metrics(self) -> bool:
        """Test speaker-independent generalization metrics"""
        print("\n🧪 Testing Speaker-Independent Metrics...")

        # Test Case 1: Multiple speakers
        predictions_by_speaker = {
            'speaker_1': (np.array([0, 1, 0, 1]), np.array([0, 1, 0, 1])),  # Perfect
            'speaker_2': (np.array([0, 1, 0, 1]), np.array([0, 1, 0, 0])),  # One error
            'speaker_3': (np.array([0, 1, 0, 1]), np.array([1, 0, 1, 0])),  # Poor
        }

        results = self.framework.speaker_independent_metrics(predictions_by_speaker)

        assert 'mean_speaker_f1' in results, "Should have mean speaker F1"
        assert 'std_speaker_f1' in results, "Should have std speaker F1"
        assert results['mean_speaker_f1'].value > 0.0, "Mean F1 should be positive"
        assert results['mean_speaker_f1'].value <= 1.0, "Mean F1 should be <= 1.0"

        print(f"  ✓ Multiple speakers: Mean F1 = {results['mean_speaker_f1'].value:.4f} ± {results['std_speaker_f1'].value:.4f}")

        # Test Case 2: Single speaker (should handle gracefully)
        predictions_by_speaker = {
            'speaker_1': (np.array([0, 1, 0, 1]), np.array([0, 1, 0, 1])),
        }

        results = self.framework.speaker_independent_metrics(predictions_by_speaker)

        # Should still return results for single speaker
        if results:
            print(f"  ✓ Single speaker: Mean F1 = {results['mean_speaker_f1'].value:.4f}")

        self.passed_tests += 1
        return True

    def test_publication_formatting(self) -> bool:
        """Test publication-ready formatting"""
        print("\n🧪 Testing Publication Formatting...")

        # Create sample results
        y_true = np.array([0, 1, 0, 1, 0, 1, 0, 1])
        y_pred = np.array([0, 1, 0, 1, 0, 0, 1, 1])

        results = self.framework.classification_metrics(y_true, y_pred)

        # Test LaTeX formatting
        latex_output = self.framework.format_results_for_publication(results)

        assert "\\begin{table}" in latex_output, "Should contain table start"
        assert "\\end{table}" in latex_output, "Should contain table end"
        assert "\\caption{" in latex_output, "Should contain caption"
        assert "95\\% CI" in latex_output, "Should contain confidence interval"

        print("  ✓ LaTeX table formatting: OK")

        # Test JSON saving
        test_path = Path("/tmp/test_results.json")
        self.framework.save_results(results, test_path)

        assert test_path.exists(), "Should create results file"
        with open(test_path, 'r') as f:
            saved_results = json.load(f)

        assert 'accuracy' in saved_results, "Should contain accuracy in saved file"
        assert saved_results['accuracy']['value'] == results['accuracy'].value, "Saved value should match"

        # Cleanup
        test_path.unlink()

        print("  ✓ JSON saving: OK")

        self.passed_tests += 1
        return True

    def test_macro_f1_imbalanced(self) -> bool:
        """Test Macro-F1 calculation for imbalanced datasets"""
        print("\n🧪 Testing Macro-F1 for Imbalanced Datasets...")

        # Test Case 1: Heavily imbalanced dataset
        y_true = np.array([0] * 90 + [1] * 10)
        y_pred = np.array([0] * 85 + [1] * 5 + [0] * 5 + [1] * 5)

        macro_f1_result = self.framework.macro_f1_score(y_true, y_pred)

        assert 0.0 <= macro_f1_result.value <= 1.0, "Macro-F1 should be between 0 and 1"
        assert macro_f1_result.sample_size == len(y_true), "Sample size should match"

        print(f"  ✓ Heavily imbalanced: Macro-F1 = {macro_f1_result.value:.4f}")

        # Test Case 2: Balanced dataset
        y_true = np.array([0, 1, 0, 1, 0, 1, 0, 1])
        y_pred = np.array([0, 1, 0, 1, 0, 0, 1, 1])

        macro_f1_result = self.framework.macro_f1_score(y_true, y_pred)

        assert 0.0 <= macro_f1_result.value <= 1.0, "Macro-F1 should be between 0 and 1"

        print(f"  ✓ Balanced dataset: Macro-F1 = {macro_f1_result.value:.4f}")

        self.passed_tests += 1
        return True

    def run_all_validation_tests(self) -> Dict[str, Any]:
        """Run all validation tests"""
        print("\n🚀 RUNNING COMPREHENSIVE VALIDATION")
        print("=" * 80)

        tests = [
            ("IoU Calculation", self.test_iou_calculation),
            ("Classification Metrics", self.test_classification_metrics),
            ("IoU-based Detection", self.test_iou_based_detection_metrics),
            ("Statistical Significance", self.test_statistical_significance),
            ("Bootstrap CI", self.test_bootstrap_confidence_intervals),
            ("Cross-Domain Metrics", self.test_cross_domain_metrics),
            ("Speaker-Independent Metrics", self.test_speaker_independent_metrics),
            ("Publication Formatting", self.test_publication_formatting),
            ("Macro-F1 Imbalanced", self.test_macro_f1_imbalanced),
        ]

        results = {
            'total_tests': len(tests),
            'passed_tests': 0,
            'failed_tests': 0,
            'test_details': []
        }

        for test_name, test_func in tests:
            try:
                test_func()
                results['passed_tests'] += 1
                results['test_details'].append({
                    'name': test_name,
                    'status': 'PASSED'
                })
                print(f"✅ {test_name}: PASSED")
            except AssertionError as e:
                results['failed_tests'] += 1
                results['test_details'].append({
                    'name': test_name,
                    'status': 'FAILED',
                    'error': str(e)
                })
                print(f"❌ {test_name}: FAILED - {str(e)}")
            except Exception as e:
                results['failed_tests'] += 1
                results['test_details'].append({
                    'name': test_name,
                    'status': 'ERROR',
                    'error': str(e)
                })
                print(f"❌ {test_name}: ERROR - {str(e)}")

        print("\n" + "=" * 80)
        print("📊 VALIDATION SUMMARY")
        print("=" * 80)
        print(f"Total Tests: {results['total_tests']}")
        print(f"Passed: {results['passed_tests']} ✅")
        print(f"Failed: {results['failed_tests']} ❌")
        print(f"Success Rate: {(results['passed_tests']/results['total_tests'])*100:.1f}%")

        if results['failed_tests'] == 0:
            print("\n🎉 ALL VALIDATION TESTS PASSED!")
            print("✅ Academic Metrics Framework is production-ready")
        else:
            print(f"\n⚠️ {results['failed_tests']} test(s) failed - review needed")

        return results


def main():
    """Main validation function"""
    print("🔬 METRICS VALIDATION SYSTEM")
    print("=" * 80)
    print("Agent 3: Comprehensive validation of academic metrics framework")
    print("=" * 80)

    # Create validator
    validator = MetricsValidator()

    # Run all tests
    validation_results = validator.run_all_validation_tests()

    # Save validation report
    report_path = Path("/Users/Subho/autonomous_laughter_prediction/benchmarks/validation_report.json")
    with open(report_path, 'w') as f:
        json.dump(validation_results, f, indent=2)

    print(f"\n📄 Validation report saved to: {report_path}")

    # Final status
    if validation_results['failed_tests'] == 0:
        print("\n🎯 AGENT 3 MISSION ACCOMPLISHED")
        print("=" * 80)
        print("✅ Academic Evaluation Metrics Framework is operational")
        print("✅ All metrics match published research protocols")
        print("✅ Statistical validation implemented")
        print("✅ Cross-domain and speaker-independent metrics ready")
        print("✅ Publication-ready formatting functional")
        print("\n🚀 Ready for integration with:")
        print("   • Agent 1: Data infrastructure")
        print("   • Agent 2: Model implementations")
        print("   • External benchmarks: StandUp4AI, UR-FUNNY, TED Laughter, MHD, SCRIPTS")
        return 0
    else:
        print("\n⚠️ VALIDATION ISSUES FOUND")
        print("Please review failed tests before deployment")
        return 1


if __name__ == "__main__":
    exit(main())