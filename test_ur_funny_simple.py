"""
Simple Test for UR-FUNNY TED Dataset Implementation

This script tests the basic functionality without loading heavy dependencies.
"""

import sys
sys.path.append('/Users/Subho/autonomous_laughter_prediction')

import pandas as pd
import numpy as np
from pathlib import Path

def test_dataset_structure():
    """Test that the dataset files were created properly"""

    print("="*70)
    print("TESTING UR-FUNNY TED DATASET STRUCTURE")
    print("="*70)

    data_path = Path("./data/ur_funny_ted_sample")

    # Check directory structure
    print("\n1. Checking directory structure...")
    required_dirs = ['annotations', 'features']
    for dir_name in required_dirs:
        dir_path = data_path / dir_name
        if dir_path.exists():
            print(f"  ✅ {dir_name}/ exists")
        else:
            print(f"  ❌ {dir_name}/ missing")
            return False

    # Check annotation files
    print("\n2. Checking annotation files...")
    required_files = ['train.csv', 'val.csv', 'test.csv']
    for file_name in required_files:
        file_path = data_path / 'annotations' / file_name
        if file_path.exists():
            df = pd.read_csv(file_path)
            print(f"  ✅ {file_name}: {len(df)} samples")
            print(f"     Columns: {list(df.columns)}")
            print(f"     Humor ratio: {df['humor'].mean():.2f}")
        else:
            print(f"  ❌ {file_name} missing")
            return False

    # Check feature files
    print("\n3. Checking feature files...")
    feature_files = ['audio_features.npy', 'visual_features.npy']
    for file_name in feature_files:
        file_path = data_path / 'features' / file_name
        if file_path.exists():
            features = np.load(file_path)
            print(f"  ✅ {file_name}: {features.shape}")
        else:
            print(f"  ❌ {file_name} missing")
            return False

    print("\n" + "="*70)
    print("✅ Dataset structure test PASSED")
    print("="*70)

    return True

def test_annotation_format():
    """Test that annotations have the correct format"""
    print("\n" + "="*70)
    print("TESTING ANNOTATION FORMAT")
    print("="*70)

    data_path = Path("./data/ur_funny_ted_sample")
    train_file = data_path / 'annotations' / 'train.csv'

    df = pd.read_csv(train_file)

    # Check required columns
    required_columns = ['video_id', 'text', 'humor', 'speaker', 'title']
    print("\n1. Checking required columns...")
    for col in required_columns:
        if col in df.columns:
            print(f"  ✅ {col} present")
        else:
            print(f"  ❌ {col} missing")
            return False

    # Check data types and ranges
    print("\n2. Checking data types and ranges...")
    print(f"  text type: {df['text'].dtype}")
    print(f"  humor type: {df['humor'].dtype}")
    print(f"  humor range: [{df['humor'].min()}, {df['humor'].max()}]")
    print(f"  humor values: {df['humor'].unique()}")

    # Check that humor is binary
    if set(df['humor'].unique()) <= {0, 1}:
        print("  ✅ Humor is binary (0/1)")
    else:
        print("  ❌ Humor is not binary")
        return False

    # Check text content
    print("\n3. Checking text content...")
    sample_texts = df['text'].head(3).tolist()
    for i, text in enumerate(sample_texts, 1):
        print(f"  Sample {i}: {text[:80]}...")

    print("\n" + "="*70)
    print("✅ Annotation format test PASSED")
    print("="*70)

    return True

def test_feature_dimensions():
    """Test that features have correct dimensions"""
    print("\n" + "="*70)
    print("TESTING FEATURE DIMENSIONS")
    print("="*70)

    data_path = Path("./data/ur_funny_ted_sample")

    # Load features
    audio_features = np.load(data_path / 'features' / 'audio_features.npy')
    visual_features = np.load(data_path / 'features' / 'visual_features.npy')

    print(f"\n1. Audio features:")
    print(f"  Shape: {audio_features.shape}")
    print(f"  Dtype: {audio_features.dtype}")
    print(f"  Range: [{audio_features.min():.3f}, {audio_features.max():.3f}]")
    print(f"  Mean: {audio_features.mean():.3f}")
    print(f"  Std: {audio_features.std():.3f}")

    print(f"\n2. Visual features:")
    print(f"  Shape: {visual_features.shape}")
    print(f"  Dtype: {visual_features.dtype}")
    print(f"  Range: [{visual_features.min():.3f}, {visual_features.max():.3f}]")
    print(f"  Mean: {visual_features.mean():.3f}")
    print(f"  Std: {visual_features.std():.3f}")

    # Check dimensions
    print("\n3. Checking dimension requirements...")
    if audio_features.shape[1] == 128:
        print("  ✅ Audio features have 128 dimensions (correct)")
    else:
        print(f"  ❌ Audio features have {audio_features.shape[1]} dimensions (expected 128)")
        return False

    if visual_features.shape[1] == 512:
        print("  ✅ Visual features have 512 dimensions (correct)")
    else:
        print(f"  ❌ Visual features have {visual_features.shape[1]} dimensions (expected 512)")
        return False

    # Check that number of samples matches annotations
    train_df = pd.read_csv(data_path / 'annotations' / 'train.csv')
    val_df = pd.read_csv(data_path / 'annotations' / 'val.csv')
    test_df = pd.read_csv(data_path / 'annotations' / 'test.csv')
    total_samples = len(train_df) + len(val_df) + len(test_df)

    print("\n4. Checking sample count consistency...")
    print(f"  Total annotation samples: {total_samples}")
    print(f"  Audio feature samples: {audio_features.shape[0]}")
    print(f"  Visual feature samples: {visual_features.shape[0]}")

    if audio_features.shape[0] == total_samples:
        print("  ✅ Audio features match annotation count")
    else:
        print("  ❌ Audio features don't match annotation count")
        return False

    if visual_features.shape[0] == total_samples:
        print("  ✅ Visual features match annotation count")
    else:
        print("  ❌ Visual features don't match annotation count")
        return False

    print("\n" + "="*70)
    print("✅ Feature dimensions test PASSED")
    print("="*70)

    return True

def main():
    """Run all tests"""
    print("🧪 Running UR-FUNNY TED Dataset Tests\n")

    # Test 1: Dataset structure
    test1_passed = test_dataset_structure()

    # Test 2: Annotation format
    test2_passed = test_annotation_format()

    # Test 3: Feature dimensions
    test3_passed = test_feature_dimensions()

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Dataset Structure Test: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"Annotation Format Test: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    print(f"Feature Dimensions Test: {'✅ PASSED' if test3_passed else '❌ FAILED'}")

    if test1_passed and test2_passed and test3_passed:
        print("\n🎉 All tests passed! UR-FUNNY TED dataset is properly set up.")
        print("\nDataset ready for:")
        print("  - Multimodal humor detection model training")
        print("  - Comparison to 65.23% C-MFN baseline")
        print("  - Full benchmark evaluation")
    else:
        print("\n⚠️  Some tests failed. Please check the dataset setup.")

    print("="*70)

if __name__ == "__main__":
    main()