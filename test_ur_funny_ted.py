"""
Test UR-FUNNY TED Dataset Implementation

This script tests the UR-FUNNY TED dataset loader and basic functionality.
"""

import sys
sys.path.append('/Users/Subho/autonomous_laughter_prediction')

from benchmarks.datasets.ur_funny_ted import URFunnyTEDDataset
from benchmarks.utils.base_dataset import create_data_loader

def test_ur_funny_ted_dataset():
    """Test the UR-FUNNY TED dataset loader"""

    print("="*70)
    print("TESTING UR-FUNNY TED DATASET LOADER")
    print("="*70)

    # Test with sample data
    data_path = "./data/ur_funny_ted_sample"

    try:
        # Test each split
        for split in ['train', 'val', 'test']:
            print(f"\nTesting {split} split...")
            print("-" * 50)

            # Create dataset
            dataset = URFunnyTEDDataset(
                data_path=data_path,
                split=split,
                feature_type='multimodal',
                use_precomputed_features=True
            )

            # Get dataset info
            info = dataset.get_split_info()
            print(f"Dataset: {info['dataset_name']}")
            print(f"Split: {info['split']}")
            print(f"Samples: {info['num_samples']}")
            print(f"Speakers: {info['num_speakers']}")
            print(f"Data path: {info['data_path']}")

            # Get statistics
            stats = dataset.get_statistics()
            print(f"Statistics:")
            print(f"  Total samples: {stats['total_samples']}")
            print(f"  Samples with labels: {stats['num_with_labels']}")

            if 'label_distribution' in stats:
                dist = stats['label_distribution']
                print(f"  Label distribution:")
                print(f"    Humorous: {dist['laughter']}")
                print(f"    Not humorous: {dist['no_laughter']}")
                print(f"    Humor ratio: {stats['laughter_ratio']:.2f}")

            # Get baseline comparison
            baseline = dataset.get_baseline_comparison()
            print(f"Baseline comparison:")
            print(f"  C-MFN baseline: {baseline['c_mfn_baseline']:.2f}%")
            print(f"  Human performance: {baseline['human_performance']:.2f}%")
            print(f"  Majority baseline: {baseline['majority_class']:.2f}%")

            # Test data loading
            if len(dataset) > 0:
                print(f"\nTesting sample loading...")
                sample = dataset[0]
                print(f"  Sample keys: {list(sample.keys())}")

                if 'text_input_ids' in sample:
                    print(f"  Text input shape: {sample['text_input_ids'].shape}")
                if 'label' in sample:
                    print(f"  Label: {sample['label']}")
                if 'metadata' in sample:
                    print(f"  Metadata keys: {list(sample['metadata'].keys())}")

        print("\n" + "="*70)
        print("✅ UR-FUNNY TED dataset test PASSED")
        print("="*70)

        return True

    except Exception as e:
        print(f"\n❌ UR-FUNNY TED dataset test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_data_loader():
    """Test creating dataloaders"""
    print("\n" + "="*70)
    print("TESTING DATALOADER CREATION")
    print("="*70)

    try:
        data_path = "./data/ur_funny_ted_sample"

        # Create train dataset
        dataset = URFunnyTEDDataset(
            data_path=data_path,
            split='train',
            feature_type='multimodal',
            use_precomputed_features=True
        )

        # Create dataloader
        dataloader = create_data_loader(
            dataset=dataset,
            batch_size=8,
            shuffle=True,
            num_workers=0
        )

        print(f"Created dataloader with {len(dataloader)} batches")

        # Test batch loading
        print("\nTesting batch loading...")
        for batch_idx, batch in enumerate(dataloader):
            if batch_idx >= 2:  # Test first 2 batches
                break

            print(f"\nBatch {batch_idx + 1}:")
            print(f"  Batch keys: {list(batch.keys())}")

            if 'text_input_ids' in batch:
                print(f"  Text input shape: {batch['text_input_ids'].shape}")
            if 'label' in batch:
                print(f"  Labels shape: {batch['label'].shape}")
                print(f"  Labels: {batch['label'][:4]}")  # First 4 labels
            if 'metadata' in batch:
                print(f"  Metadata length: {len(batch['metadata'])}")

        print("\n" + "="*70)
        print("✅ Dataloader test PASSED")
        print("="*70)

        return True

    except Exception as e:
        print(f"\n❌ Dataloader test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🧪 Running UR-FUNNY TED Implementation Tests\n")

    # Test 1: Dataset loading
    test1_passed = test_ur_funny_ted_dataset()

    # Test 2: Dataloader creation
    test2_passed = test_data_loader()

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Dataset Loading Test: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"Dataloader Creation Test: {'✅ PASSED' if test2_passed else '❌ FAILED'}")

    if test1_passed and test2_passed:
        print("\n🎉 All tests passed! UR-FUNNY TED implementation is working.")
        print("\nNext steps:")
        print("1. Obtain the real UR-FUNNY TED dataset")
        print("2. Run the full benchmark evaluation")
        print("3. Compare results to 65.23% C-MFN baseline")
    else:
        print("\n⚠️  Some tests failed. Please check the implementation.")

    print("="*70)

if __name__ == "__main__":
    main()