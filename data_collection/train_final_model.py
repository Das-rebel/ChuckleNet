#!/usr/bin/env python3
"""
Train on Unified Dataset
=======================
Trains laughter detection model on combined original + synthetic data.
"""

import os
import sys
import json
import numpy as np
import pickle
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score, precision_score, recall_score, classification_report

# Paths
DATA_DIR = '/Users/Subho/data/chuckle-net-final'
OUTPUT_DIR = '/Users/Subho/data/chuckle-net-final/models'
os.makedirs(OUTPUT_DIR, exist_ok=True)

def load_dataset():
    """Load unified dataset."""
    print("Loading dataset...")
    
    file_path = f'{DATA_DIR}/final_unified_dataset.jsonl'
    samples = []
    
    with open(file_path) as f:
        for line in f:
            try:
                samples.append(json.loads(line.strip()))
            except:
                pass
    
    print(f"Loaded {len(samples):,} samples")
    return samples

def prepare_features(samples, feature_type='prosody'):
    """Prepare features from samples."""
    X = []
    y = []
    has_feature = 0
    
    for s in samples:
        if feature_type == 'prosody':
            feats = s.get('prosody', [])
            if feats and any(v != 0 for v in feats[:7]):
                X.append(feats[:21])
                y.append(s.get('label_any', 0))
                has_feature += 1
        elif feature_type == 'wavlm':
            wavlm = s.get('wavlm')
            if wavlm and len(wavlm) > 0:
                X.append(wavlm)
                y.append(s.get('label_any', 0))
                has_feature += 1
    
    print(f"  {feature_type}: {has_feature:,} samples with features")
    
    return np.array(X), np.array(y)

def train_model(X_train, y_train, X_val, y_val, X_test, y_test):
    """Train and evaluate model."""
    print("\nTraining Logistic Regression...")
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    X_test_scaled = scaler.transform(X_test)
    
    # Train model
    model = LogisticRegression(
        max_iter=1000,
        class_weight='balanced',
        C=1.0,
        random_state=42
    )
    
    model.fit(X_train_scaled, y_train)
    
    # Evaluate
    y_val_pred = model.predict(X_val_scaled)
    y_test_pred = model.predict(X_test_scaled)
    
    val_f1 = f1_score(y_val, y_val_pred)
    test_f1 = f1_score(y_test, y_test_pred)
    
    val_f1_weighted = f1_score(y_val, y_val_pred, average='weighted')
    test_f1_weighted = f1_score(y_test, y_test_pred, average='weighted')
    
    print(f"\nValidation F1: {val_f1:.4f} (weighted: {val_f1_weighted:.4f})")
    print(f"Test F1: {test_f1:.4f} (weighted: {test_f1_weighted:.4f})")
    
    # Detailed report
    print("\nTest Classification Report:")
    print(classification_report(y_test, y_test_pred, target_names=['No Laugh', 'Laugh']))
    
    return model, scaler, val_f1, test_f1

def main():
    print("="*70)
    print("TRAINING ON UNIFIED DATASET")
    print("="*70)
    
    # Load data
    samples = load_dataset()
    
    # Split by source
    original = [s for s in samples if s['source'] == 'original']
    synthetic = [s for s in samples if s['source'] == 'synthetic']
    
    print(f"\nData split:")
    print(f"  Original: {len(original):,}")
    print(f"  Synthetic: {len(synthetic):,}")
    
    # Train on ORIGINAL ONLY (for comparison)
    print("\n" + "="*70)
    print("TRAINING ON ORIGINAL DATA ONLY")
    print("="*70)
    
    X_orig, y_orig = prepare_features(original, 'prosody')
    print(f"  Shape: {X_orig.shape}")
    
    # Split
    X_train, X_temp, y_train, y_temp = train_test_split(
        X_orig, y_orig, test_size=0.3, random_state=42, stratify=y_orig
    )
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.5, random_state=42, stratify=y_temp
    )
    
    print(f"  Train: {len(X_train):,}, Val: {len(X_val):,}, Test: {len(X_test):,}")
    
    model_orig, scaler_orig, val_f1_orig, test_f1_orig = train_model(
        X_train, y_train, X_val, y_val, X_test, y_test
    )
    
    # Save original model
    with open(f'{OUTPUT_DIR}/model_original.pkl', 'wb') as f:
        pickle.dump(model_orig, f)
    with open(f'{OUTPUT_DIR}/scaler_original.pkl', 'wb') as f:
        pickle.dump(scaler_orig, f)
    print(f"\nSaved original model to {OUTPUT_DIR}/model_original.pkl")
    
    # Train on COMBINED (original + synthetic)
    print("\n" + "="*70)
    print("TRAINING ON COMBINED DATA (Original + Synthetic)")
    print("="*70)
    
    # Prepare combined data - use prosody
    X_comb, y_comb = prepare_features(samples, 'prosody')
    print(f"  Shape: {X_comb.shape}")
    
    # Split (same split for fair comparison)
    X_train_c, X_temp_c, y_train_c, y_temp_c = train_test_split(
        X_comb, y_comb, test_size=0.3, random_state=42, stratify=y_comb
    )
    X_val_c, X_test_c, y_val_c, y_test_c = train_test_split(
        X_temp_c, y_temp_c, test_size=0.5, random_state=42, stratify=y_temp_c
    )
    
    print(f"  Train: {len(X_train_c):,}, Val: {len(X_val_c):,}, Test: {len(X_test_c):,}")
    
    model_comb, scaler_comb, val_f1_comb, test_f1_comb = train_model(
        X_train_c, y_train_c, X_val_c, y_val_c, X_test_c, y_test_c
    )
    
    # Save combined model
    with open(f'{OUTPUT_DIR}/model_combined.pkl', 'wb') as f:
        pickle.dump(model_comb, f)
    with open(f'{OUTPUT_DIR}/scaler_combined.pkl', 'wb') as f:
        pickle.dump(scaler_comb, f)
    print(f"\nSaved combined model to {OUTPUT_DIR}/model_combined.pkl")
    
    # Final comparison
    print("\n" + "="*70)
    print("RESULTS COMPARISON")
    print("="*70)
    print(f"\n{'Model':<25} {'Val F1':<12} {'Test F1':<12}")
    print("-"*50)
    print(f"{'Original (15K)':<25} {val_f1_orig:<12.4f} {test_f1_orig:<12.4f}")
    print(f"{'Combined (39K)':<25} {val_f1_comb:<12.4f} {test_f1_comb:<12.4f}")
    
    improvement = (test_f1_comb - test_f1_orig) / test_f1_orig * 100
    print(f"\nSynthetic data improvement: {improvement:+.1f}%")
    
    # Save results
    results = {
        'original': {
            'samples': len(original),
            'val_f1': val_f1_orig,
            'test_f1': test_f1_orig
        },
        'combined': {
            'samples': len(samples),
            'val_f1': val_f1_comb,
            'test_f1': test_f1_comb
        },
        'improvement_pct': improvement
    }
    
    with open(f'{OUTPUT_DIR}/training_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\n" + "="*70)
    print("TRAINING COMPLETE!")
    print("="*70)

if __name__ == '__main__':
    main()
