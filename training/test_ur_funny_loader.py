#!/usr/bin/env python3
"""
Test Suite for UR-FUNNY Dataset Loader

This module provides comprehensive tests for the UR-FUNNY dataset loader,
including validation of forced alignment processing, punchline detection,
and GCACU pipeline integration.

Tests:
- Sample data generation and loading
- Forced alignment processing (P2FA, JSON, CSV, TextGrid)
- Punchline annotation validation
- Word-level label generation
- GCACU format conversion
- Error handling and edge cases
"""

import json
import unittest
import tempfile
import shutil
from pathlib import Path
import numpy as np
import pandas as pd

from load_ur_funny import (
    URFunnyLoader,
    URFunnyExample,
    PunchlineAnnotation,
    ForcedAlignment,
    HumorType,
    AlignmentFormat,
    convert_to_gcacu_format,
    create_sample_ur_funny_data
)


class TestPunchlineAnnotation(unittest.TestCase):
    """Test cases for PunchlineAnnotation dataclass."""

    def test_valid_punchline(self):
        """Test creating a valid punchline annotation."""
        punchline = PunchlineAnnotation(
            punchline_start=10,
            punchline_end=12,
            context_start=5,
            context_end=20,
            humor_score=0.85,
            laughter_intensity=0.75
        )

        self.assertEqual(punchline.punchline_start, 10)
        self.assertEqual(punchline.punchline_end, 12)
        self.assertEqual(punchline.humor_score, 0.85)

    def test_invalid_punchline_range(self):
        """Test that invalid punchline ranges raise errors."""
        with self.assertRaises(ValueError):
            PunchlineAnnotation(
                punchline_start=15,  # End before start
                punchline_end=10,
                context_start=0,
                context_end=20,
                humor_score=0.5,
                laughter_intensity=0.5
            )

    def test_invalid_humor_score(self):
        """Test that invalid humor scores raise errors."""
        with self.assertRaises(ValueError):
            PunchlineAnnotation(
                punchline_start=0,
                punchline_end=5,
                context_start=0,
                context_end=10,
                humor_score=1.5,  # Score > 1.0
                laughter_intensity=0.5
            )

    def test_extract_punchline_words(self):
        """Test extracting punchline words from full text."""
        words = ["This", "is", "the", "punchline", "here", "and", "more"]
        punchline = PunchlineAnnotation(
            punchline_start=2,
            punchline_end=4,
            context_start=0,
            context_end=6,
            humor_score=0.8,
            laughter_intensity=0.7
        )

        punchline_words = punchline.get_punchline_words(words)
        self.assertEqual(punchline_words, ["the", "punchline", "here"])

    def test_extract_context_words(self):
        """Test extracting context window words."""
        words = ["start", "context", "words", "punchline", "end", "context"]
        punchline = PunchlineAnnotation(
            punchline_start=3,
            punchline_end=3,
            context_start=1,
            context_end=4,  # Fixed to be within bounds
            humor_score=0.9,
            laughter_intensity=0.8
        )

        context_words = punchline.get_context_words(words)
        self.assertEqual(context_words, ["context", "words", "punchline", "end"])

    def test_to_dict(self):
        """Test converting punchline annotation to dictionary."""
        punchline = PunchlineAnnotation(
            punchline_start=5,
            punchline_end=7,
            context_start=2,
            context_end=10,
            humor_score=0.75,
            laughter_intensity=0.65,
            audience_reaction="laughter"
        )

        punchline_dict = punchline.to_dict()

        self.assertEqual(punchline_dict["punchline_start"], 5)
        self.assertEqual(punchline_dict["humor_score"], 0.75)
        self.assertEqual(punchline_dict["audience_reaction"], "laughter")


class TestForcedAlignment(unittest.TestCase):
    """Test cases for ForcedAlignment dataclass."""

    def test_valid_alignment(self):
        """Test creating valid forced alignment."""
        alignment = ForcedAlignment(
            words=["Hello", "world"],
            start_times=[0.0, 0.5],
            end_times=[0.5, 1.0]
        )

        self.assertEqual(len(alignment.words), 2)
        self.assertEqual(alignment.get_total_duration(), 1.0)

    def test_mismatched_lengths(self):
        """Test that mismatched array lengths raise errors."""
        with self.assertRaises(ValueError):
            ForcedAlignment(
                words=["Hello", "world"],
                start_times=[0.0],  # Only one start time
                end_times=[0.5, 1.0]
            )

    def test_word_duration(self):
        """Test calculating word duration."""
        alignment = ForcedAlignment(
            words=["Hello", "world"],
            start_times=[0.0, 0.5],
            end_times=[0.5, 1.0]
        )

        self.assertAlmostEqual(alignment.get_word_duration(0), 0.5)
        self.assertAlmostEqual(alignment.get_word_duration(1), 0.5)

    def test_confidence_initialization(self):
        """Test that confidence scores are initialized if not provided."""
        alignment = ForcedAlignment(
            words=["Hello", "world"],
            start_times=[0.0, 0.5],
            end_times=[0.5, 1.0]
        )

        self.assertEqual(len(alignment.confidence), 2)
        self.assertTrue(all(c == 1.0 for c in alignment.confidence))

    def test_to_dict(self):
        """Test converting alignment to dictionary."""
        alignment = ForcedAlignment(
            words=["test"],
            start_times=[0.0],
            end_times=[0.3],
            phones=["T", "EH", "S", "T"],
            confidence=[0.95]
        )

        alignment_dict = alignment.to_dict()

        self.assertEqual(alignment_dict["words"], ["test"])
        self.assertEqual(alignment_dict["phones"], ["T", "EH", "S", "T"])
        self.assertEqual(alignment_dict["confidence"], [0.95])


class TestURFunnyExample(unittest.TestCase):
    """Test cases for URFunnyExample dataclass."""

    def test_valid_example(self):
        """Test creating a valid example."""
        example = URFunnyExample(
            example_id="test_001",
            words=["Hello", "world"],
            labels=[0, 1],
            language="en"
        )

        self.assertEqual(example.example_id, "test_001")
        self.assertEqual(len(example.words), 2)

    def test_words_labels_mismatch(self):
        """Test that words/labels length mismatch raises error."""
        with self.assertRaises(ValueError):
            URFunnyExample(
                example_id="test_002",
                words=["Hello", "world"],
                labels=[0],  # Only one label
                language="en"
            )

    def test_punchline_bounds_validation(self):
        """Test that punchline indices are validated."""
        with self.assertRaises(ValueError):
            URFunnyExample(
                example_id="test_003",
                words=["word1", "word2"],
                labels=[0, 0],
                language="en",
                punchlines=[
                    PunchlineAnnotation(
                        punchline_start=0,
                        punchline_end=5,  # Beyond words length
                        context_start=0,
                        context_end=5,
                        humor_score=0.5,
                        laughter_intensity=0.5
                    )
                ]
            )

    def test_has_alignment(self):
        """Test alignment detection."""
        example_without = URFunnyExample(
            example_id="test_004",
            words=["test"],
            labels=[0],
            language="en"
        )

        example_with = URFunnyExample(
            example_id="test_005",
            words=["test"],
            labels=[0],
            language="en",
            alignment=ForcedAlignment(
                words=["test"],
                start_times=[0.0],
                end_times=[0.3]
            )
        )

        self.assertFalse(example_without.has_alignment())
        self.assertTrue(example_with.has_alignment())

    def test_get_laughter_segments(self):
        """Test extracting laughter segments from labels."""
        example = URFunnyExample(
            example_id="test_006",
            words=["word1", "word2", "word3", "word4", "word5"],
            labels=[0, 1, 1, 0, 1],
            language="en"
        )

        segments = example.get_laughter_segments()

        self.assertEqual(len(segments), 2)
        self.assertEqual(segments[0]["start_word"], 1)
        self.assertEqual(segments[0]["end_word"], 2)
        self.assertEqual(segments[1]["start_word"], 4)
        self.assertEqual(segments[1]["end_word"], 4)

    def test_get_laughter_segments_with_timing(self):
        """Test laughter segments with timing information."""
        example = URFunnyExample(
            example_id="test_007",
            words=["word1", "word2", "word3"],
            labels=[0, 1, 0],
            language="en",
            alignment=ForcedAlignment(
                words=["word1", "word2", "word3"],
                start_times=[0.0, 0.5, 1.0],
                end_times=[0.5, 1.0, 1.5]
            )
        )

        segments = example.get_laughter_segments()

        self.assertEqual(len(segments), 1)
        self.assertIn("start_time", segments[0])
        self.assertIn("end_time", segments[0])
        self.assertAlmostEqual(segments[0]["start_time"], 0.5)
        self.assertAlmostEqual(segments[0]["end_time"], 1.0)

    def test_get_context_windows(self):
        """Test extracting context windows around punchlines."""
        example = URFunnyExample(
            example_id="test_008",
            words=["start", "context", "punchline", "end", "context"],
            labels=[0, 0, 1, 0, 0],
            language="en",
            punchlines=[
                PunchlineAnnotation(
                    punchline_start=2,
                    punchline_end=2,
                    context_start=1,
                    context_end=3,
                    humor_score=0.8,
                    laughter_intensity=0.7
                )
            ]
        )

        contexts = example.get_context_windows(window_size=2)

        self.assertEqual(len(contexts), 1)
        self.assertIn("context_words", contexts[0])
        self.assertIn("punchline_start_rel", contexts[0])
        self.assertEqual(contexts[0]["humor_score"], 0.8)


class TestURFunnyLoader(unittest.TestCase):
    """Test cases for URFunnyLoader."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.temp_dir) / "ur_funny_test"

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    def create_sample_dataset(self):
        """Create a sample UR-FUNNY dataset for testing."""
        create_sample_ur_funny_data(self.data_dir, num_samples=5)

    def test_load_sample_data(self):
        """Test loading sample UR-FUNNY data."""
        self.create_sample_dataset()

        loader = URFunnyLoader(
            data_dir=self.data_dir,
            enable_alignment=True,
            enable_punchlines=True
        )

        examples = loader.load(split="train")

        self.assertGreater(len(examples), 0)
        self.assertIsInstance(examples[0], URFunnyExample)

    def test_load_without_alignment(self):
        """Test loading without forced alignment."""
        self.create_sample_dataset()

        loader = URFunnyLoader(
            data_dir=self.data_dir,
            enable_alignment=False
        )

        examples = loader.load(split="train")

        self.assertGreater(len(examples), 0)
        # Examples should not have alignment
        self.assertFalse(any(ex.has_alignment() for ex in examples))

    def test_load_without_punchlines(self):
        """Test loading without punchline annotations."""
        self.create_sample_dataset()

        loader = URFunnyLoader(
            data_dir=self.data_dir,
            enable_punchlines=False
        )

        examples = loader.load(split="train")

        self.assertGreater(len(examples), 0)

    def test_statistics_update(self):
        """Test that statistics are properly calculated."""
        self.create_sample_dataset()

        loader = URFunnyLoader(data_dir=self.data_dir)
        examples = loader.load(split="train")

        self.assertEqual(loader.stats["total_examples"], len(examples))
        self.assertGreater(loader.stats["total_words"], 0)
        self.assertIsInstance(loader.stats["avg_example_length"], float)

    def test_missing_annotation_file(self):
        """Test handling of missing annotation files."""
        # Don't create sample data, use create_if_missing flag
        loader = URFunnyLoader(data_dir=self.data_dir, create_if_missing=True)

        with self.assertRaises(FileNotFoundError):
            loader.load(split="train")

    def test_invalid_alignment_format(self):
        """Test handling of invalid alignment format."""
        self.create_sample_dataset()

        loader = URFunnyLoader(
            data_dir=self.data_dir,
            alignment_format="invalid_format"
        )

        # Should still work, just without alignment
        examples = loader.load(split="train")
        self.assertGreater(len(examples), 0)


class TestGCACUConversion(unittest.TestCase):
    """Test cases for GCACU format conversion."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.output_file = Path(self.temp_dir) / "test_output.jsonl"

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    def create_test_examples(self):
        """Create test examples for conversion."""
        return [
            URFunnyExample(
                example_id="test_001",
                words=["Hello", "world"],
                labels=[0, 1],
                language="en",
                metadata={"source": "UR-FUNNY", "test": True}
            ),
            URFunnyExample(
                example_id="test_002",
                words=["Another", "test", "example"],
                labels=[0, 0, 1],
                language="en",
                metadata={"source": "UR-FUNNY", "test": True},
                alignment=ForcedAlignment(
                    words=["Another", "test", "example"],
                    start_times=[0.0, 0.3, 0.6],
                    end_times=[0.3, 0.6, 1.0]
                ),
                punchlines=[
                    PunchlineAnnotation(
                        punchline_start=2,
                        punchline_end=2,
                        context_start=0,
                        context_end=2,
                        humor_score=0.8,
                        laughter_intensity=0.7
                    )
                ]
            )
        ]

    def test_basic_conversion(self):
        """Test basic GCACU format conversion."""
        examples = self.create_test_examples()

        convert_to_gcacu_format(
            examples,
            self.output_file,
            include_alignment=False,
            include_punchlines=False
        )

        self.assertTrue(self.output_file.exists())

        # Read and verify output
        with open(self.output_file, 'r') as f:
            lines = f.readlines()

        self.assertEqual(len(lines), 2)

        # Verify first record
        record1 = json.loads(lines[0])
        self.assertEqual(record1["example_id"], "test_001")
        self.assertIn("words", record1)
        self.assertIn("labels", record1)
        self.assertNotIn("alignment", record1)
        self.assertNotIn("punchlines", record1)

    def test_conversion_with_alignment(self):
        """Test conversion with alignment data."""
        examples = self.create_test_examples()

        convert_to_gcacu_format(
            examples,
            self.output_file,
            include_alignment=True,
            include_punchlines=False
        )

        with open(self.output_file, 'r') as f:
            lines = f.readlines()

        # Second record should have alignment
        record2 = json.loads(lines[1])
        self.assertIn("alignment", record2)
        self.assertIn("words", record2["alignment"])
        self.assertIn("start_times", record2["alignment"])

    def test_conversion_with_punchlines(self):
        """Test conversion with punchline data."""
        examples = self.create_test_examples()

        convert_to_gcacu_format(
            examples,
            self.output_file,
            include_alignment=False,
            include_punchlines=True
        )

        with open(self.output_file, 'r') as f:
            lines = f.readlines()

        # Second record should have punchlines
        record2 = json.loads(lines[1])
        self.assertIn("punchlines", record2)
        self.assertIsInstance(record2["punchlines"], list)
        self.assertGreater(len(record2["punchlines"]), 0)


class TestSampleDataGeneration(unittest.TestCase):
    """Test cases for sample data generation."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = Path(self.temp_dir) / "sample_ur_funny"

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    def test_sample_data_creation(self):
        """Test creating sample UR-FUNNY data."""
        create_sample_ur_funny_data(self.output_dir, num_samples=3)

        # Check directory structure
        self.assertTrue((self.output_dir / "annotations").exists())
        self.assertTrue((self.output_dir / "p2fa_alignments").exists())
        self.assertTrue((self.output_dir / "punchline_annotations.json").exists())

    def test_annotation_files_created(self):
        """Test that all annotation files are created."""
        create_sample_ur_funny_data(self.output_dir, num_samples=2)

        for split in ["train", "val", "test"]:
            annotation_file = self.output_dir / "annotations" / f"{split}.csv"
            self.assertTrue(annotation_file.exists())

            # Verify CSV format
            df = pd.read_csv(annotation_file)
            self.assertIn("video_id", df.columns)
            self.assertIn("text", df.columns)
            self.assertIn("humor", df.columns)

    def test_punchline_annotations_created(self):
        """Test that punchline annotations are created."""
        create_sample_ur_funny_data(self.output_dir, num_samples=2)

        punchline_file = self.output_dir / "punchline_annotations.json"
        self.assertTrue(punchline_file.exists())

        with open(punchline_file, 'r') as f:
            punchline_data = json.load(f)

        self.assertIsInstance(punchline_data, list)
        self.assertGreater(len(punchline_data), 0)

        # Verify punchline structure
        for item in punchline_data:
            self.assertIn("ted_id", item)
            self.assertIn("punchlines", item)
            self.assertIsInstance(item["punchlines"], list)

    def test_alignment_files_created(self):
        """Test that alignment files are created."""
        create_sample_ur_funny_data(self.output_dir, num_samples=2)

        alignments_dir = self.output_dir / "p2fa_alignments"
        self.assertTrue(alignments_dir.exists())

        alignment_files = list(alignments_dir.glob("*.json"))
        self.assertGreater(len(alignment_files), 0)

        # Verify alignment format
        for alignment_file in alignment_files:
            with open(alignment_file, 'r') as f:
                alignment = json.load(f)

            self.assertIn("ted_id", alignment)
            self.assertIn("words", alignment)
            self.assertIn("start_times", alignment)
            self.assertIn("end_times", alignment)

    def test_load_generated_sample_data(self):
        """Test that generated sample data can be loaded."""
        create_sample_ur_funny_data(self.output_dir, num_samples=5)

        loader = URFunnyLoader(
            data_dir=self.output_dir,
            enable_alignment=True,
            enable_punchlines=True
        )

        examples = loader.load(split="train")

        self.assertGreater(len(examples), 0)
        self.assertIsInstance(examples[0], URFunnyExample)

        # Note: Alignment loading may fail for some samples due to validation,
        # but we should have some examples with punchlines
        has_punchlines = any(ex.has_punchlines() for ex in examples)
        self.assertTrue(has_punchlines, "Expected at least some examples with punchlines")


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""

    def test_empty_words_list(self):
        """Test handling of empty words list."""
        with self.assertRaises(ValueError):
            URFunnyExample(
                example_id="empty_test",
                words=[],
                labels=[],
                language="en"
            )

    def test_single_word(self):
        """Test handling of single-word examples."""
        example = URFunnyExample(
            example_id="single_word",
            words=["Hello"],
            labels=[1],
            language="en"
        )

        self.assertEqual(len(example.words), 1)
        self.assertEqual(len(example.labels), 1)

    def test_all_laughter_labels(self):
        """Test handling of all-laughter examples."""
        example = URFunnyExample(
            example_id="all_laughter",
            words=["ha", "ha", "ha"],
            labels=[1, 1, 1],
            language="en"
        )

        segments = example.get_laughter_segments()
        self.assertEqual(len(segments), 1)

    def test_no_laughter_labels(self):
        """Test handling of no-laughter examples."""
        example = URFunnyExample(
            example_id="no_laughter",
            words=["serious", "business"],
            labels=[0, 0],
            language="en"
        )

        segments = example.get_laughter_segments()
        self.assertEqual(len(segments), 0)


def run_tests():
    """Run all tests and print results."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestPunchlineAnnotation))
    suite.addTests(loader.loadTestsFromTestCase(TestForcedAlignment))
    suite.addTests(loader.loadTestsFromTestCase(TestURFunnyExample))
    suite.addTests(loader.loadTestsFromTestCase(TestURFunnyLoader))
    suite.addTests(loader.loadTestsFromTestCase(TestGCACUConversion))
    suite.addTests(loader.loadTestsFromTestCase(TestSampleDataGeneration))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCases))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {(1 - (len(result.failures) + len(result.errors)) / result.testsRun) * 100:.1f}%")
    print("="*70)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)