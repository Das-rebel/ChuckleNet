#!/usr/bin/env python3
"""
Comprehensive Test Suite for YouTube Comedy Dataset Integration
==============================================================
Tests all aspects of the YouTube comedy data pipeline including:
- Dataset loading and parsing
- Word-level laughter alignment
- Data cleaning and deduplication
- YouTube metadata integration
- GCACU format export
- Data augmentation
- Virality prediction features

Revolutionary Feature Testing:
- YouTube virality prediction accuracy
- Metadata-enhanced training data
- Engagement rate calculations
"""

import unittest
import tempfile
import shutil
import json
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from training.load_youtube_comedy import (
    YouTubeComedyLoader,
    ComedyDataAugmentor,
    YouTubeComedyExporter,
    YouTubeMetadata,
    ComedySegment,
    GCACUFormatter
)


class TestYouTubeMetadata(unittest.TestCase):
    """Test YouTube metadata and virality prediction"""

    def test_metadata_creation(self):
        """Test YouTube metadata creation"""
        metadata = YouTubeMetadata(
            video_id="test123",
            title="Test Comedy Special",
            channel="Test Channel",
            view_count=1000000,
            like_count=50000,
            comment_count=10000
        )

        self.assertEqual(metadata.video_id, "test123")
        self.assertEqual(metadata.view_count, 1000000)

    def test_engagement_rate_calculation(self):
        """Test engagement rate calculation"""
        metadata = YouTubeMetadata(
            video_id="test123",
            title="Test Video",
            view_count=1000000,
            like_count=50000,
            comment_count=10000
        )

        expected_rate = (50000 + 10000) / 1000000
        self.assertAlmostEqual(metadata.engagement_rate, expected_rate)

    def test_virality_score_calculation(self):
        """Test virality score calculation"""
        # High virality video
        high_virality = YouTubeMetadata(
            video_id="viral123",
            title="Viral Video",
            view_count=10000000,  # 10M views
            like_count=500000,
            comment_count=100000
        )

        # Low virality video
        low_virality = YouTubeMetadata(
            video_id="normal123",
            title="Normal Video",
            view_count=10000,
            like_count=100,
            comment_count=10
        )

        self.assertGreater(high_virality.virality_score, low_virality.virality_score)
        self.assertLessEqual(high_virality.virality_score, 1.0)
        self.assertGreaterEqual(low_virality.virality_score, 0.0)


class TestComedySegment(unittest.TestCase):
    """Test comedy segment processing"""

    def test_segment_creation(self):
        """Test comedy segment creation"""
        segment = ComedySegment(
            text="This is a funny joke about dogs",
            words=["This", "is", "a", "funny", "joke", "about", "dogs"],
            labels=[0, 0, 0, 1, 1, 0, 0]
        )

        self.assertTrue(segment.has_laughter)
        self.assertEqual(segment.laughter_ratio, 2/7)
        self.assertEqual(segment.word_count, 7)

    def test_no_laughter_segment(self):
        """Test segment without laughter"""
        segment = ComedySegment(
            text="This is not funny",
            words=["This", "is", "not", "funny"],
            labels=[0, 0, 0, 0]
        )

        self.assertFalse(segment.has_laughter)
        self.assertEqual(segment.laughter_ratio, 0.0)


class TestYouTubeComedyLoader(unittest.TestCase):
    """Test YouTube comedy data loader"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.loader = YouTubeComedyLoader(data_dir=self.test_dir, cache_dir=self.test_dir)

        # Create test data files
        self._create_test_data()

    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir)

    def _create_test_data(self):
        """Create test data files"""
        # Test scraped_comedy_transcripts.json
        test_data_1 = [
            {
                "url": "https://scrapsfromtheloft.com/comedy/test-special/",
                "title": "Test Comedy Special",
                "laughter_count": 2,
                "laughter_types": ["[laughter]", "[chuckles]"],
                "content": "This is a joke [laughter] This is setup [chuckles] More content",
                "word_count": 15
            }
        ]

        with open(Path(self.test_dir) / "scraped_comedy_transcripts.json", 'w') as f:
            json.dump(test_data_1, f)

        # Test scraped_from_scraps_from_loft.json
        test_data_2 = [
            {
                "url": "https://scrapsfromtheloft.com/comedy/test2/",
                "title": "Another Test",
                "laughter_count": 1,
                "laughter_types": ["[applause]"],
                "content": "Setup punchline [applause] End of joke"
            }
        ]

        with open(Path(self.test_dir) / "scraped_from_scraps_from_loft.json", 'w') as f:
            json.dump(test_data_2, f)

    def test_text_normalization(self):
        """Test text normalization"""
        text = "  This   is   a   TEST  with  Ümlauts  "
        normalized = self.loader.normalize_text(text)

        self.assertEqual(normalized, "this is a test with umlauts")

    def test_duplicate_detection(self):
        """Test duplicate detection"""
        text1 = "This is the same content"
        text2 = "This is the same content"

        self.assertFalse(self.loader.is_duplicate(text1))
        self.assertTrue(self.loader.is_duplicate(text2))

    def test_laughter_tag_extraction(self):
        """Test laughter tag extraction"""
        text = "Some text [laughter] more text [chuckles] end [applause]"
        tags = self.loader.extract_laughter_tags(text)

        self.assertEqual(len(tags), 3)
        self.assertIn("[laughter]", [t[0] for t in tags])
        self.assertIn("[chuckles]", [t[0] for t in tags])

    def test_laughter_type_detection(self):
        """Test laughter type detection"""
        self.assertEqual(self.loader.detect_laughter_type("[chuckles]"), "discrete")
        self.assertEqual(self.loader.detect_laughter_type("[laughter]"), "continuous")
        self.assertEqual(self.loader.detect_laughter_type("[applause]"), "applause")

    def test_load_scraped_comedy_transcripts(self):
        """Test loading scraped comedy transcripts"""
        segments = list(self.loader.load_scraped_comedy_transcripts())

        self.assertGreater(len(segments), 0)

        # Check that laughter segments are properly labeled
        laughter_segments = [s for s in segments if s.has_laughter]
        self.assertGreater(len(laughter_segments), 0)

    def test_youtube_metadata_integration(self):
        """Test YouTube metadata integration"""
        # Add test metadata
        metadata = YouTubeMetadata(
            video_id="test123",
            title="Test Video",
            view_count=1000000,
            like_count=50000,
            comment_count=10000
        )

        self.loader.add_youtube_metadata("test123", metadata)

        # Test retrieval
        retrieved = self.loader.get_youtube_metadata("test123")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.view_count, 1000000)

    def test_video_id_extraction(self):
        """Test YouTube video ID extraction"""
        url1 = "https://www.youtube.com/watch?v=test123"
        url2 = "https://youtu.be/test456"
        url3 = "https://youtube.com/embed/test789"

        self.assertEqual(self.loader.extract_video_id_from_url(url1), "test123")
        self.assertEqual(self.loader.extract_video_id_from_url(url2), "test456")
        self.assertEqual(self.loader.extract_video_id_from_url(url3), "test789")


class TestComedyDataAugmentor(unittest.TestCase):
    """Test comedy data augmentation"""

    def setUp(self):
        """Set up test environment"""
        self.augmentor = ComedyDataAugmentor(augmentation_factor=3)

    def test_synonym_replacement(self):
        """Test synonym replacement augmentation"""
        text = "This is a funny joke that makes people laugh"
        augmented = self.augmentor._synonym_replacement(text)

        # Check that some comedy terms were replaced
        self.assertNotEqual(text, augmented)
        # Should contain either replacements or have modifications
        augmented_lower = augmented.lower()
        has_changes = (
            "hilarious" in augmented_lower or
            "amusing" in augmented_lower or
            "gag" in augmented_lower or
            "bit" in augmented_lower or
            "chuckle" in augmented_lower or
            "giggle" in augmented_lower or
            "crack up" in augmented_lower
        )
        self.assertTrue(has_changes, f"Expected synonym replacement but got: {augmented}")

    def test_noise_addition(self):
        """Test noise addition augmentation"""
        text = "This is a test"
        augmented = self.augmentor._add_noise(text, noise_rate=1.0)

        # With high noise rate, should likely be different
        self.assertIsInstance(augmented, str)

    def test_light_paraphrase(self):
        """Test light paraphrasing augmentation"""
        text = "I mean, actually, this is funny"
        augmented = self.augmentor._light_paraphrase(text)

        self.assertNotEqual(text, augmented)
        # The paraphrase should remove some filler words (but might not get all)
        original_parts = ["i mean", "actually"]
        removed_parts = [part for part in original_parts if part not in augmented.lower()]
        self.assertGreater(len(removed_parts), 0, f"Expected some filler words to be removed. Got: {augmented}")

    def test_segment_augmentation(self):
        """Test segment-level augmentation"""
        segment = ComedySegment(
            text="This is a funny joke",
            words=["This", "is", "a", "funny", "joke"],
            labels=[0, 0, 0, 1, 1],
            source="test"
        )

        augmented = self.augmentor.augment_segment(segment)

        # Should return original + augmented versions
        self.assertGreater(len(augmented), 1)
        self.assertEqual(augmented[0], segment)  # First should be original

    def test_label_adjustment(self):
        """Test label array adjustment"""
        original_labels = [1, 0, 1, 0]

        # Test shortening
        shortened = self.augmentor._adjust_labels(original_labels, 2)
        self.assertEqual(shortened, [1, 0])

        # Test lengthening
        lengthened = self.augmentor._adjust_labels(original_labels, 6)
        self.assertEqual(lengthened, [1, 0, 1, 0, 0, 0])


class TestGCACUFormatter(unittest.TestCase):
    """Test GCACU formatting"""

    def setUp(self):
        """Set up test environment"""
        self.formatter = GCACUFormatter(include_metadata=True)

    def test_segment_formatting(self):
        """Test comedy segment formatting for GCACU"""
        segment = ComedySegment(
            text="This is funny",
            words=["This", "is", "funny"],
            labels=[0, 0, 1],
            source="test_source",
            metadata={"test_key": "test_value"}
        )

        formatted = self.formatter.format_segment(
            segment,
            video_id="test123",
            comedian_id="test_comedian",
            show_id="test_show"
        )

        self.assertIn("example_id", formatted)
        self.assertIn("words", formatted)
        self.assertIn("labels", formatted)
        self.assertEqual(formatted["words"], ["This", "is", "funny"])
        self.assertEqual(formatted["labels"], [0, 0, 1])

    def test_metadata_inclusion(self):
        """Test metadata inclusion in formatted output"""
        segment = ComedySegment(
            text="Test",
            words=["Test"],
            labels=[1],
            metadata={"original_metadata": "value"}
        )

        formatted = self.formatter.format_segment(segment)

        self.assertIn("metadata", formatted)
        self.assertEqual(formatted["metadata"]["original_metadata"], "value")


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete pipeline"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()

        # Create comprehensive test data
        self._create_comprehensive_test_data()

    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir)

    def _create_comprehensive_test_data(self):
        """Create comprehensive test data"""
        test_data = {
            "title": "Integration Test Special",
            "type": "standup",
            "source": "scraps_from_loft",
            "transcript_number": 1,
            "laughter_segments": [
                {"text": "[laughter]", "type": "continuous"},
                {"text": "[chuckles]", "type": "discrete"}
            ],
            "total_laughter_count": 2,
            "discrete_laughter": 1,
            "continuous_laughter": 1,
            "full_text": "Setup line with actual content here [laughter] Punchline here with more text [chuckles] More content that continues the joke",
            "url": "https://scrapsfromtheloft.com/comedy/integration-test/",
            "word_count": 20
        }

        test_dataset = [test_data]

        with open(Path(self.test_dir) / "scraped_comprehensive_dataset.json", 'w') as f:
            json.dump(test_dataset, f)

        # Also create scraped_comedy_transcripts.json for better testing
        test_data_2 = [
            {
                "url": "https://scrapsfromtheloft.com/comedy/test2/",
                "title": "Another Test Special",
                "laughter_count": 1,
                "laughter_types": ["[laughter]"],
                "content": "This is a test with some content [laughter] And more content here",
                "word_count": 12
            }
        ]

        with open(Path(self.test_dir) / "scraped_comedy_transcripts.json", 'w') as f:
            json.dump(test_data_2, f)

    def test_full_pipeline(self):
        """Test complete data pipeline"""
        # Initialize components with fresh cache for this test
        import tempfile
        fresh_cache_dir = tempfile.mkdtemp()
        loader = YouTubeComedyLoader(data_dir=self.test_dir, cache_dir=fresh_cache_dir)
        augmentor = ComedyDataAugmentor(augmentation_factor=2)
        exporter = YouTubeComedyExporter(loader, augmentor)

        # Load data
        segments = list(loader.load_all_datasets())
        self.assertGreater(len(segments), 0)

        # Export data
        output_dir = Path(self.test_dir) / "output"
        exporter.export_for_gcacu(str(output_dir), apply_augmentation=False)

        # Check output files exist
        self.assertTrue((output_dir / "train.jsonl").exists())
        self.assertTrue((output_dir / "valid.jsonl").exists())
        self.assertTrue((output_dir / "test.jsonl").exists())
        self.assertTrue((output_dir / "export_statistics.json").exists())

        # Check statistics
        with open(output_dir / "export_statistics.json", 'r') as f:
            stats = json.load(f)

        self.assertIn("total_segments", stats)
        self.assertIn("laughter_segments", stats)
        self.assertGreater(stats["total_segments"], 0)

    def test_augmented_pipeline(self):
        """Test pipeline with data augmentation"""
        loader = YouTubeComedyLoader(data_dir=self.test_dir)
        augmentor = ComedyDataAugmentor(augmentation_factor=2)
        exporter = YouTubeComedyExporter(loader, augmentor)

        # Export with augmentation
        output_dir = Path(self.test_dir) / "output_augmented"
        exporter.export_for_gcacu(str(output_dir), apply_augmentation=True)

        # Check that augmentation was applied
        with open(output_dir / "export_statistics.json", 'r') as f:
            stats = json.load(f)

        self.assertTrue(stats["augmentation_applied"])


def run_tests():
    """Run all tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestYouTubeMetadata))
    suite.addTests(loader.loadTestsFromTestCase(TestComedySegment))
    suite.addTests(loader.loadTestsFromTestCase(TestYouTubeComedyLoader))
    suite.addTests(loader.loadTestsFromTestCase(TestComedyDataAugmentor))
    suite.addTests(loader.loadTestsFromTestCase(TestGCACUFormatter))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("=" * 70)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)