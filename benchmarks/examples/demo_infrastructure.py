"""
Comprehensive Demo of Data Infrastructure Framework

This script demonstrates all capabilities of the universal data loading
and preprocessing infrastructure for autonomous laughter prediction.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path to import benchmarks package
sys.path.insert(0, str(Path(__file__).parent.parent))

from benchmarks import (
    # Dataset loading
    get_dataset, list_datasets, get_dataset_info,

    # Base infrastructure
    BaseBenchmarkDataset, DataSample, create_data_loader,

    # Split management
    SplitManager, SplitConfig,

    # Preprocessing
    AudioPreprocessor, VideoPreprocessor, TextPreprocessor,
    MultimodalPreprocessor, AudioConfig, VideoConfig, TextConfig,

    # Validation
    DataValidator, DatasetValidationReport,

    # Data management
    DataManager, CacheConfig
)


def demo_available_datasets():
    """Demonstrate available datasets"""
    print("=" * 80)
    print("AVAILABLE ACADEMIC BENCHMARKS")
    print("=" * 80)

    datasets = list_datasets()
    print(f"\nTotal supported benchmarks: {len(datasets)}")
    print("\nAvailable datasets:")
    for i, dataset_name in enumerate(datasets, 1):
        info = get_dataset_info(dataset_name)
        print(f"\n{i}. {info.get('name', dataset_name).upper()}")
        print(f"   Type: {info.get('type', 'N/A')}")
        print(f"   Task: {info.get('task', 'N/A')}")
        print(f"   Modalities: {', '.join(info.get('modalities', []))}")
        print(f"   Size: {info.get('size', 'N/A')}")
        print(f"   Description: {info.get('description', 'N/A')}")


def demo_split_management():
    """Demonstrate split management capabilities"""
    print("\n" + "=" * 80)
    print("SPLIT MANAGEMENT DEMONSTRATION")
    print("=" * 80)

    # Create sample data
    samples = list(range(100))  # Mock samples
    speaker_ids = [f"speaker_{i % 10}" for i in range(100)]
    show_ids = [f"show_{i % 5}" for i in range(100)]
    labels = [i % 2 for i in range(100)]  # Binary labels

    # Test different split configurations
    configs = [
        ("Speaker-Independent", SplitConfig(speaker_independent=True)),
        ("Show-Independent", SplitConfig(show_independent=True)),
        ("Stratified", SplitConfig(stratified=True)),
        ("Random", SplitConfig())
    ]

    for config_name, config in configs:
        print(f"\n{config_name} Splits:")
        print("-" * 40)

        split_manager = SplitManager(config, "demo_dataset")
        train_idx, val_idx, test_idx = split_manager.create_splits(
            samples, speaker_ids, show_ids, labels
        )

        print(f"  Train: {len(train_idx)} samples ({len(train_idx)/len(samples)*100:.1f}%)")
        print(f"  Val: {len(val_idx)} samples ({len(val_idx)/len(samples)*100:.1f}%)")
        print(f"  Test: {len(test_idx)} samples ({len(test_idx)/len(samples)*100:.1f}%)")

        # Validate splits
        try:
            split_manager.validate_splits(train_idx, val_idx, test_idx)
            print(f"  ✓ Validation passed")
        except Exception as e:
            print(f"  ✗ Validation failed: {e}")


def demo_preprocessing():
    """Demonstrate preprocessing capabilities"""
    print("\n" + "=" * 80)
    print("PREPROCESSING PIPELINE DEMONSTRATION")
    print("=" * 80)

    # Create sample configurations
    audio_config = AudioConfig(
        target_sample_rate=16000,
        n_mels=128,
        max_length=10,
        normalize=True
    )

    video_config = VideoConfig(
        target_fps=25,
        target_size=(224, 224),
        max_frames=250,
        normalize=True
    )

    text_config = TextConfig(
        max_length=512,
        tokenizer='bert-base-uncased',
        lowercase=True
    )

    print("\nAudio Configuration:")
    print(f"  Sample Rate: {audio_config.target_sample_rate} Hz")
    print(f"  Mel Spectrogram Bins: {audio_config.n_mels}")
    print(f"  Max Length: {audio_config.max_length} seconds")
    print(f"  Normalization: {audio_config.normalize}")

    print("\nVideo Configuration:")
    print(f"  Target FPS: {video_config.target_fps}")
    print(f"  Target Size: {video_config.target_size}")
    print(f"  Max Frames: {video_config.max_frames}")
    print(f"  Normalization: {video_config.normalize}")

    print("\nText Configuration:")
    print(f"  Max Length: {text_config.max_length} tokens")
    print(f"  Tokenizer: {text_config.tokenizer}")
    print(f"  Lowercase: {text_config.lowercase}")

    # Demonstrate multimodal preprocessing
    print("\nMultimodal Preprocessor:")
    print("  ✓ Audio feature extraction (mel spectrograms, MFCC, prosodic)")
    print("  ✓ Video frame extraction and normalization")
    print("  ✓ Text tokenization and linguistic features")
    print("  ✓ Cross-modal alignment and synchronization")


def demo_data_validation():
    """Demonstrate data validation capabilities"""
    print("\n" + "=" * 80)
    print("DATA VALIDATION DEMONSTRATION")
    print("=" * 80)

    # Create mock samples
    class MockSample:
        def __init__(self, text, label, speaker_id=None, show_id=None):
            self.text = text
            self.label = label
            self.speaker_id = speaker_id
            self.show_id = show_id
            self.audio_path = None
            self.video_path = None

    samples = [
        MockSample("This is a funny joke about programming", 1, "speaker_1", "show_1"),
        MockSample("Another hilarious comedy moment", 1, "speaker_1", "show_1"),
        MockSample("Serious technical explanation", 0, "speaker_2", "show_2"),
        MockSample("More humorous content", 1, "speaker_3", "show_3"),
        MockSample("Informative but not funny", 0, "speaker_2", "show_2"),
    ]

    # Create validator
    validator = DataValidator("demo_dataset", "/tmp/demo_data")

    # Run validation
    print("\nRunning validation checks...")
    report = validator.validate_all(
        samples,
        checks=[
            'data_integrity',
            'label_consistency',
            'metadata_completeness',
            'class_balance',
            'text_quality'
        ]
    )

    print(f"\nValidation Results:")
    print(f"  Total Checks: {report.total_checks}")
    print(f"  Passed: {report.passed_checks} ({report.passed_checks/report.total_checks*100:.1f}%)")
    print(f"  Failed: {report.failed_checks}")
    print(f"  Warnings: {report.warnings}")

    if report.recommendations:
        print(f"\nRecommendations:")
        for i, rec in enumerate(report.recommendations, 1):
            print(f"  {i}. {rec}")


def demo_data_caching():
    """Demonstrate data caching capabilities"""
    print("\n" + "=" * 80)
    print("DATA CACHING AND MANAGEMENT DEMONSTRATION")
    print("=" * 80)

    # Create cache configuration
    cache_config = CacheConfig(
        enable_cache=True,
        cache_dir="/tmp/demo_cache",
        max_cache_size_gb=5.0,
        compression=True,
        parallel_loading=True,
        num_workers=4
    )

    print("\nCache Configuration:")
    print(f"  Enabled: {cache_config.enable_cache}")
    print(f"  Cache Directory: {cache_config.cache_dir}")
    print(f"  Max Size: {cache_config.max_cache_size_gb} GB")
    print(f"  Compression: {cache_config.compression}")
    print(f"  Parallel Loading: {cache_config.parallel_loading}")
    print(f"  Workers: {cache_config.num_workers}")

    # Create data manager
    data_manager = DataManager(cache_config, "demo_dataset")

    print("\nData Manager Features:")
    print("  ✓ Intelligent caching of preprocessed data")
    print("  ✓ Automatic cache size management")
    print("  ✓ Parallel preprocessing for speed")
    print("  ✓ Cache statistics and monitoring")
    print("  ✓ Data integrity verification")


def demo_integration():
    """Demonstrate complete integration workflow"""
    print("\n" + "=" * 80)
    print("COMPLETE INTEGRATION WORKFLOW")
    print("=" * 80)

    print("\nWorkflow Overview:")
    print("1. Load benchmark dataset using universal loader")
    print("2. Apply standardized preprocessing pipeline")
    print("3. Create proper train/val/test splits")
    print("4. Validate data quality and integrity")
    print("5. Cache preprocessed data for efficiency")
    print("6. Create data loaders for training")

    print("\nExample Code:")
    print("""
    # Load dataset
    dataset = get_dataset(
        'standup4ai',
        data_path='/path/to/standup4ai',
        split='train'
    )

    # Create splits
    split_config = SplitConfig(speaker_independent=True)
    split_manager = SplitManager(split_config, 'standup4ai')
    train_idx, val_idx, test_idx = split_manager.create_splits(
        dataset.samples,
        speaker_ids=[s.speaker_id for s in dataset.samples],
        show_ids=[s.show_id for s in dataset.samples],
        labels=[s.label for s in dataset.samples]
    )

    # Validate data
    validator = DataValidator('standup4ai', '/path/to/standup4ai')
    report = validator.validate_all(dataset.samples)

    # Setup caching
    cache_config = CacheConfig(enable_cache=True)
    data_manager = DataManager(cache_config, 'standup4ai')

    # Create data loaders
    train_loader = create_data_loader(dataset, batch_size=32, shuffle=True)
    """)


def main():
    """Run all demonstrations"""
    print("\n")
    print("*" * 80)
    print("*" + " " * 78 + "*")
    print("*" + "  AUTONOMOUS LAUGHTER PREDICTION - DATA INFRASTRUCTURE DEMO  ".center(78) + "*")
    print("*" + " " * 78 + "*")
    print("*" * 80)

    # Run demonstrations
    demo_available_datasets()
    demo_split_management()
    demo_preprocessing()
    demo_data_validation()
    demo_data_caching()
    demo_integration()

    print("\n" + "=" * 80)
    print("DEMONSTRATION COMPLETE")
    print("=" * 80)

    print("\nKey Infrastructure Components:")
    print("  ✓ Universal data loading for 9 academic benchmarks")
    print("  ✓ Standardized preprocessing pipeline")
    print("  ✓ Proper train/val/test split protocols")
    print("  ✓ Data quality validation and integrity checks")
    print("  ✓ Efficient caching and data management")
    print("  ✓ Cross-domain evaluation support")

    print("\nReady for Agent 2 (StandUp4AI Implementation)!")
    print("\nFor usage examples, see: benchmarks/examples/")

    return 0


if __name__ == "__main__":
    sys.exit(main())