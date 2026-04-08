#!/usr/bin/env python3
"""
Test Suite for TIC-TALK Dataset Loader

Comprehensive testing of TIC-TALK dataset functionality including:
- Data loading and validation
- Word-level alignment accuracy
- Kinematic signal processing
- GCACU pipeline integration
- Edge cases and error handling

Author: Autonomous Laughter Prediction Team
Date: 2025-04-03
"""

import sys
import json
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any

import torch
import numpy as np
from transformers import AutoTokenizer

# Add training directory to path
sys.path.insert(0, str(Path(__file__).parent))

from load_tic_talk import (
    TICTalkLoader,
    TICTalkExample,
    KinematicSignals,
    LaughterType,
    convert_to_gcacu_format,
    create_sample_tictalk_data
)


class TICTalkTestSuite:
    """Comprehensive test suite for TIC-TALK loader."""

    def __init__(self, verbose: bool = True):
        """Initialize test suite.

        Args:
            verbose: Whether to print detailed test results
        """
        self.verbose = verbose
        self.test_results = []
        self.temp_dir = None

    def setup(self):
        """Create temporary test data directory."""
        self.temp_dir = tempfile.mkdtemp(prefix="tictalk_test_")
        if self.verbose:
            print(f"Created test directory: {self.temp_dir}")

    def teardown(self):
        """Clean up temporary test data."""
        if self.temp_dir and Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
            if self.verbose:
                print(f"Cleaned up test directory: {self.temp_dir}")

    def run_test(self, test_name: str, test_func) -> bool:
        """Run a single test and record result.

        Args:
            test_name: Name of the test
            test_func: Test function to execute

        Returns:
            True if test passed, False otherwise
        """
        try:
            test_func()
            self.test_results.append((test_name, "PASSED", None))
            if self.verbose:
                print(f"✓ {test_name}")
            return True
        except Exception as e:
            self.test_results.append((test_name, "FAILED", str(e)))
            if self.verbose:
                print(f"✗ {test_name}: {e}")
            return False

    def print_summary(self):
        """Print test summary."""
        passed = sum(1 for _, status, _ in self.test_results if status == "PASSED")
        total = len(self.test_results)

        print(f"\n{'='*60}")
        print(f"Test Summary: {passed}/{total} tests passed")
        print(f"{'='*60}")

        if passed < total:
            print("\nFailed tests:")
            for name, status, error in self.test_results:
                if status == "FAILED":
                    print(f"  - {name}: {error}")

    def test_sample_data_creation(self):
        """Test 1: Sample data creation."""
        create_sample_tictalk_data(Path(self.temp_dir), num_samples=5)

        segments_file = Path(self.temp_dir) / "segments.json"
        kinematics_file = Path(self.temp_dir) / "kinematics.json"

        assert segments_file.exists(), "segments.json not created"
        assert kinematics_file.exists(), "kinematics.json not created"

        with open(segments_file) as f:
            segments = json.load(f)
        assert len(segments) == 5, f"Expected 5 segments, got {len(segments)}"

        with open(kinematics_file) as f:
            kinematics = json.load(f)
        assert len(kinematics) == 5, f"Expected 5 kinematic entries, got {len(kinematics)}"

    def test_basic_loading(self):
        """Test 2: Basic dataset loading."""
        create_sample_tictalk_data(Path(self.temp_dir), num_samples=10)

        loader = TICTalkLoader(data_dir=Path(self.temp_dir))
        examples = loader.load()

        assert len(examples) > 0, "No examples loaded"
        assert len(examples) <= 10, f"Loaded too many examples: {len(examples)}"

        # Verify example structure
        example = examples[0]
        assert hasattr(example, 'example_id'), "Missing example_id"
        assert hasattr(example, 'words'), "Missing words"
        assert hasattr(example, 'labels'), "Missing labels"
        assert len(example.words) == len(example.labels), "Words/labels length mismatch"

    def test_kinematic_loading(self):
        """Test 3: Kinematic signal loading."""
        create_sample_tictalk_data(Path(self.temp_dir), num_samples=5)

        loader = TICTalkLoader(
            data_dir=Path(self.temp_dir),
            enable_kinematics=True
        )
        examples = loader.load()

        kinematic_count = sum(1 for ex in examples if ex.has_kinematics())
        assert kinematic_count > 0, "No examples with kinematics loaded"

        # Verify kinematic structure
        example_with_kinematics = next(
            (ex for ex in examples if ex.has_kinematics()), None
        )
        assert example_with_kinematics is not None, "No example with kinematics found"

        kinematics = example_with_kinematics.kinematics
        assert isinstance(kinematics, KinematicSignals), "Wrong kinematics type"
        assert len(kinematics.arm_spread) > 0, "Empty arm_spread"
        assert len(kinematics.trunk_lean) > 0, "Empty trunk_lean"
        assert len(kinematics.body_movement) > 0, "Empty body_movement"

    def test_word_level_alignment(self):
        """Test 4: Word-level laughter label alignment."""
        # Create test data with known alignment
        segments_file = Path(self.temp_dir) / "segments.json"

        test_segments = [{
            "segment_id": "test_alignment",
            "special_id": "test_special",
            "comedian": "Test Comedian",
            "words": ["hello", "world", "laughter", "here", "more", "words"],
            "word_timestamps": [(0.0, 0.5), (0.5, 1.0), (1.0, 1.5), (1.5, 2.0), (2.0, 2.5), (2.5, 3.0)],
            "laughter_timestamps": [
                {"start": 0.8, "end": 1.7}  # Should overlap "world" and "laughter"
            ],
            "whisper_at_confidence": 0.9,
            "language": "en"
        }]

        with open(segments_file, 'w') as f:
            json.dump(test_segments, f)

        loader = TICTalkLoader(data_dir=Path(self.temp_dir))
        examples = loader.load()

        assert len(examples) == 1, f"Expected 1 example, got {len(examples)}"

        example = examples[0]
        # Words "world" (index 1) and "laughter" (index 2) should have laughter
        assert example.labels[1] == 1, f"Expected label 1 at index 1, got {example.labels[1]}"
        assert example.labels[2] == 1, f"Expected label 1 at index 2, got {example.labels[2]}"
        assert example.labels[0] == 0, f"Expected label 0 at index 0, got {example.labels[0]}"

    def test_kinematic_normalization(self):
        """Test 5: Kinematic signal normalization."""
        # Create kinematic data with different scales
        kinematics = KinematicSignals(
            arm_spread=np.array([100, 200, 150], dtype=np.float32),
            trunk_lean=np.array([0.5, 1.0, 0.75], dtype=np.float32),
            body_movement=np.array([1000, 2000, 1500], dtype=np.float32),
            timestamps=np.array([0.0, 0.5, 1.0], dtype=np.float32),
            confidence=np.array([0.8, 0.9, 0.85], dtype=np.float32)
        )

        normalized = kinematics.normalize()

        # Check that all values are in [0, 1] range
        assert np.all(normalized.arm_spread >= 0) and np.all(normalized.arm_spread <= 1), \
            "Arm spread not normalized"
        assert np.all(normalized.trunk_lean >= 0) and np.all(normalized.trunk_lean <= 1), \
            "Trunk lean not normalized"
        assert np.all(normalized.body_movement >= 0) and np.all(normalized.body_movement <= 1), \
            "Body movement not normalized"

    def test_gcacu_conversion(self):
        """Test 6: GCACU format conversion."""
        create_sample_tictalk_data(Path(self.temp_dir), num_samples=3)

        loader = TICTalkLoader(data_dir=Path(self.temp_dir))
        examples = loader.load()

        output_file = Path(self.temp_dir) / "test_output.jsonl"
        convert_to_gcacu_format(examples, output_file)

        assert output_file.exists(), "Output file not created"

        with open(output_file) as f:
            lines = f.readlines()

        assert len(lines) == len(examples), f"Expected {len(examples)} lines, got {len(lines)}"

        # Verify JSON format
        for line in lines:
            record = json.loads(line)
            assert "example_id" in record, "Missing example_id"
            assert "words" in record, "Missing words"
            assert "labels" in record, "Missing labels"
            assert "metadata" in record, "Missing metadata"

    def test_error_handling(self):
        """Test 7: Error handling for invalid data."""
        # Test with missing segments file
        try:
            loader = TICTalkLoader(data_dir=Path(self.temp_dir))
            examples = loader.load()
            assert False, "Should have raised FileNotFoundError"
        except FileNotFoundError:
            pass  # Expected

        # Test with invalid JSON
        segments_file = Path(self.temp_dir) / "segments.json"
        with open(segments_file, 'w') as f:
            f.write("invalid json {{{")

        try:
            loader = TICTalkLoader(data_dir=Path(self.temp_dir))
            examples = loader.load()
            assert False, "Should have raised ValueError for invalid JSON"
        except ValueError:
            pass  # Expected

    def test_statistics_tracking(self):
        """Test 8: Statistics tracking."""
        create_sample_tictalk_data(Path(self.temp_dir), num_samples=10)

        loader = TICTalkLoader(
            data_dir=Path(self.temp_dir),
            enable_kinematics=True
        )
        examples = loader.load()

        # Verify statistics
        assert "total_segments" in loader.stats, "Missing total_segments"
        assert "segments_with_kinematics" in loader.stats, "Missing segments_with_kinematics"
        assert "total_words" in loader.stats, "Missing total_words"

        assert loader.stats["total_segments"] == len(examples), \
            f"Statistics mismatch: {loader.stats['total_segments']} != {len(examples)}"

    def test_multimodal_integration(self):
        """Test 9: Integration with GCACU training pipeline."""
        try:
            from integrate_tictalk_gcacu import (
                TICTalkGCACUDataset,
                convert_to_gcacu_examples
            )
        except ImportError:
            print("Skipping multimodal integration test (integrate_tictalk_gcacu not available)")
            return

        create_sample_tictalk_data(Path(self.temp_dir), num_samples=5)

        loader = TICTalkLoader(
            data_dir=Path(self.temp_dir),
            enable_kinematics=True
        )
        examples = loader.load()

        # Test GCACU conversion
        gcacu_examples = convert_to_gcacu_examples(examples)
        assert len(gcacu_examples) == len(examples), "GCACU conversion failed"

        # Test PyTorch dataset creation
        tokenizer = AutoTokenizer.from_pretrained("FacebookAI/xlm-roberta-base")

        dataset = TICTalkGCACUDataset(
            examples=examples,
            tokenizer=tokenizer,
            use_kinematics=True
        )

        assert len(dataset) > 0, "Empty dataset created"

        # Test single item retrieval
        item = dataset[0]
        assert "input_ids" in item, "Missing input_ids"
        assert "attention_mask" in item, "Missing attention_mask"
        assert "labels" in item, "Missing labels"
        assert "kinematic_features" in item, "Missing kinematic_features"

    def test_edge_cases(self):
        """Test 10: Edge cases and boundary conditions."""
        segments_file = Path(self.temp_dir) / "segments.json"

        # Test empty segment
        test_segments = [{
            "segment_id": "empty_segment",
            "special_id": "test",
            "comedian": "Test",
            "words": [],
            "word_timestamps": [],
            "laughter_timestamps": [],
            "language": "en"
        }]

        with open(segments_file, 'w') as f:
            json.dump(test_segments, f)

        loader = TICTalkLoader(data_dir=Path(self.temp_dir))
        examples = loader.load()

        # Empty segments should be filtered out
        assert len(examples) == 0, "Empty segment should be filtered"

        # Test segment with no laughter
        test_segments = [{
            "segment_id": "no_laughter",
            "special_id": "test",
            "comedian": "Test",
            "words": ["hello", "world"],
            "word_timestamps": [(0.0, 0.5), (0.5, 1.0)],
            "laughter_timestamps": [],
            "language": "en"
        }]

        with open(segments_file, 'w') as f:
            json.dump(test_segments, f)

        loader = TICTalkLoader(data_dir=Path(self.temp_dir))
        examples = loader.load()

        assert len(examples) == 1, "No laughter segment should load"
        assert all(label == 0 for label in examples[0].labels), \
            "All labels should be 0 for no laughter"

    def run_all_tests(self):
        """Run all tests in the suite."""
        print("Running TIC-TALK Test Suite...")
        print(f"{'='*60}")

        self.setup()

        # Define all tests
        tests = [
            ("Sample Data Creation", self.test_sample_data_creation),
            ("Basic Loading", self.test_basic_loading),
            ("Kinematic Loading", self.test_kinematic_loading),
            ("Word-level Alignment", self.test_word_level_alignment),
            ("Kinematic Normalization", self.test_kinematic_normalization),
            ("GCACU Conversion", self.test_gcacu_conversion),
            ("Error Handling", self.test_error_handling),
            ("Statistics Tracking", self.test_statistics_tracking),
            ("Multimodal Integration", self.test_multimodal_integration),
            ("Edge Cases", self.test_edge_cases)
        ]

        # Run all tests
        for test_name, test_func in tests:
            self.run_test(test_name, test_func)

        self.teardown()
        self.print_summary()

        # Return success status
        passed = sum(1 for _, status, _ in self.test_results if status == "PASSED")
        return passed == len(self.test_results)


def run_quick_validation(data_dir: str) -> bool:
    """Quick validation of TIC-TALK dataset directory.

    Args:
        data_dir: Path to TIC-TALK dataset directory

    Returns:
        True if validation passes, False otherwise
    """
    data_path = Path(data_dir)

    print(f"Validating TIC-TALK dataset at: {data_path}")

    # Check directory exists
    if not data_path.exists():
        print("✗ Directory does not exist")
        return False

    # Check required files
    segments_file = data_path / "segments.json"
    if not segments_file.exists():
        print("✗ Missing required file: segments.json")
        return False

    # Check JSON validity
    try:
        with open(segments_file) as f:
            segments = json.load(f)
        print(f"✓ Found {len(segments)} segments")
    except json.JSONDecodeError as e:
        print(f"✗ Invalid JSON in segments.json: {e}")
        return False

    # Check for kinematics (optional)
    kinematics_file = data_path / "kinematics.json"
    if kinematics_file.exists():
        try:
            with open(kinematics_file) as f:
                kinematics = json.load(f)
            print(f"✓ Found kinematic data for {len(kinematics)} segments")
        except json.JSONDecodeError as e:
            print(f"✗ Invalid JSON in kinematics.json: {e}")
            return False
    else:
        print("⚠ No kinematics.json found (optional)")

    print("✓ Dataset validation passed")
    return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="TIC-TALK Test Suite")
    parser.add_argument(
        "--validate",
        type=str,
        metavar="DIR",
        help="Validate TIC-TALK dataset directory"
    )
    parser.add_argument(
        "--full-suite",
        action="store_true",
        help="Run full test suite"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Reduce output verbosity"
    )

    args = parser.parse_args()

    if args.validate:
        # Quick validation mode
        success = run_quick_validation(args.validate)
        sys.exit(0 if success else 1)
    elif args.full_suite:
        # Full test suite
        suite = TICTalkTestSuite(verbose=not args.quiet)
        success = suite.run_all_tests()
        sys.exit(0 if success else 1)
    else:
        # Default: run full suite
        suite = TICTalkTestSuite(verbose=True)
        success = suite.run_all_tests()
        sys.exit(0 if success else 1)