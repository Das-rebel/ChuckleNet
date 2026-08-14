#!/usr/bin/env python3
"""
Synthetic Laughter Data Generator
================================
Generates synthetic laughter data by:
1. Taking real negative examples (non-laugh utterances)
2. Applying audio transformations that simulate laugh characteristics
3. Using the trained model to validate synthetic samples

This expands the dataset with high-quality synthetic positive samples.
"""

import os
import sys
import json
import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass

# ============================================================================
# PATHS
# ============================================================================

OUTPUT_DIR = '/Users/Subho/data/chuckle-net-synthetic'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ============================================================================
# SYNTHETIC LAUGHTER TRANSFORMATIONS
# ============================================================================

@dataclass
class LaughCharacteristics:
    """Characteristics of laughter vs speech."""
    # Duration expansion (laughs are often longer)
    duration_scale: Tuple[float, float] = (1.2, 1.8)  # 20-80% longer
    
    # Pitch characteristics (laughs have distinctive pitch patterns)
    pitch_shift: Tuple[float, float] = (0.8, 1.2)  # Semi-tones shift
    pitch_oscillation: Tuple[float, float] = (0.05, 0.15)  # Periodic pitch variation
    
    # Energy characteristics (laughs have rhythmic energy bursts)
    energy_modulation: Tuple[float, float] = (0.7, 1.3)  # Amplitude variation
    burst_interval: Tuple[float, float] = (0.3, 0.8)  # Seconds between bursts
    
    # Spectral characteristics (laughs have different spectral shape)
    spectral_tilt: float = 0.85  # More low-frequency energy
    spectral_boost: float = 1.2  # 20% boost to laugh frequency bands

def generate_synthetic_laugh_features(
    prosody_features: List[float],
    char: LaughCharacteristics = None
) -> List[float]:
    """
    Generate synthetic laugh features from prosody features.
    
    Prosody features (21-dim): [RMS, ZCR, pitch_mean, pitch_std, pitch_range,
                                duration, n_words, MFCC1-13]
    """
    if char is None:
        char = LaughCharacteristics()
    
    if prosody_features is None or len(prosody_features) < 7:
        return [0.0] * 21
    
    features = prosody_features.copy()
    
    # 1. Duration scaling (index 5)
    duration_scale = np.random.uniform(*char.duration_scale)
    features[5] = features[5] * duration_scale
    
    # 2. Pitch characteristics - make laughs more variable
    if features[2] > 0:  # pitch_mean exists
        pitch_shift = np.random.uniform(*char.pitch_shift)
        features[2] = features[2] * pitch_shift  # Shift pitch
        
        # Increase pitch variability
        features[3] = features[3] * np.random.uniform(1.2, 1.5)  # pitch_std
        features[4] = features[4] * np.random.uniform(1.1, 1.3)  # pitch_range
    
    # 3. Energy modulation - rhythmic bursts
    rms_scale = np.random.uniform(*char.energy_modulation)
    features[0] = features[0] * rms_scale  # RMS
    
    # 4. MFCC modifications for laugh-like spectral shape
    # MFCCs are indices 7-19 (13 coefficients)
    for i in range(7, min(20, len(features))):
        # Boost lower MFCCs (more periodic/voiced for laughs)
        if i < 12:
            features[i] = features[i] * np.random.uniform(1.0, 1.3)
        else:
            features[i] = features[i] * np.random.uniform(0.9, 1.1)
    
    return features[:21]

def generate_synthetic_samples_from_prosody(
    prosody_samples: List[Dict],
    n_synthetic_per_sample: int = 5,
    char: LaughCharacteristics = None
) -> List[Dict]:
    """
    Generate multiple synthetic laugh samples from real prosody samples.
    """
    if char is None:
        char = LaughCharacteristics()
    
    synthetic = []
    
    for sample in prosody_samples:
        prosody = sample.get('prosody', [])
        
        if not prosody or len(prosody) < 7:
            continue
        
        # Generate multiple variants
        for i in range(n_synthetic_per_sample):
            synth_prosody = generate_synthetic_laugh_features(prosody, char)
            
            synthetic.append({
                'uid': f"SYNTH_{sample['uid']}_{i}",
                'video_id': sample['video_id'],
                'source_video_id': sample['video_id'],  # Original source
                'text': f"[synthetic_laugh_{i}]",  # Marker for synthetic
                'start': sample['start'],
                'end': sample['end'],
                'duration': synth_prosody[5] if len(synth_prosody) > 5 else sample['duration'],
                'prosody': synth_prosody,
                'wavlm': sample.get('wavlm'),  # Can be None for synthetic
                'label_any': 1,  # POSITIVE - this is synthetic laugh
                'label_majority': 1,
                'is_synthetic': True,
                'synthetic_variant': i,
                'generation_method': 'prosody_transform'
            })
    
    return synthetic

def generate_synthetic_negative_samples(
    prosody_samples: List[Dict],
    n_synthetic: int = 1000
) -> List[Dict]:
    """
    Generate negative (non-laugh) samples for balance.
    These are slightly modified versions of real negatives.
    """
    synthetic = []
    
    # Sample from real negatives
    indices = np.random.choice(
        len(prosody_samples), 
        min(n_synthetic, len(prosody_samples)), 
        replace=True
    )
    
    for idx in indices:
        sample = prosody_samples[idx]
        prosody = sample.get('prosody', [])
        
        if not prosody or len(prosody) < 7:
            continue
        
        # Apply very slight modifications (should still be negative)
        features = prosody.copy()
        for i in range(len(features)):
            # Small noise (< 5%)
            noise = np.random.normal(1.0, 0.02)
            features[i] = features[i] * noise
        
        synthetic.append({
            'uid': f"SYNTH_NEG_{sample['uid']}",
            'video_id': f"neg_{sample['video_id']}",
            'source_video_id': sample['video_id'],
            'text': f"[synthetic_negative]",
            'start': sample['start'],
            'end': sample['end'],
            'duration': features[5] if len(features) > 5 else sample['duration'],
            'prosody': features[:21],
            'wavlm': None,
            'label_any': 0,  # NEGATIVE
            'label_majority': 0,
            'is_synthetic': True,
            'synthetic_variant': 0,
            'generation_method': 'negative_augment'
        })
    
    return synthetic

# ============================================================================
# MODEL-BASED FILTERING
# ============================================================================

def load_trained_model():
    """Load the trained laughter detection model."""
    import pickle
    
    model_path = '/Users/Subho/data/chuckle-net/models/lr_prosody.pkl'
    scaler_path = '/Users/Subho/data/chuckle-net/models/scaler_prosody.pkl'
    
    if not os.path.exists(model_path):
        return None, None
    
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    
    with open(scaler_path, 'rb') as f:
        scaler = pickle.load(f)
    
    return model, scaler

def filter_synthetic_with_model(
    synthetic_samples: List[Dict],
    model,
    scaler,
    threshold: float = 0.5
) -> Tuple[List[Dict], List[Dict]]:
    """
    Use trained model to filter synthetic samples.
    Keep only high-confidence positive samples.
    """
    if model is None or scaler is None:
        return synthetic_samples, []
    
    accepted = []
    rejected = []
    
    for sample in synthetic_samples:
        prosody = sample.get('prosody', [])
        
        if not prosody or len(prosody) < 21:
            rejected.append(sample)
            continue
        
        # Scale and predict
        X = np.array(prosody[:21]).reshape(1, -1)
        X_scaled = scaler.transform(X)
        prob = model.predict_proba(X_scaled)[0, 1]
        
        if prob >= threshold:
            sample['model_confidence'] = float(prob)
            sample['passed_model_filter'] = True
            accepted.append(sample)
        else:
            sample['model_confidence'] = float(prob)
            sample['passed_model_filter'] = False
            rejected.append(sample)
    
    return accepted, rejected

# ============================================================================
# MAIN GENERATION
# ============================================================================

def main():
    import glob
    import pickle
    
    print("=" * 70)
    print("SYNTHETIC LAUGHTER DATA GENERATOR")
    print("=" * 70)
    
    # Load unified dataset
    unified_file = '/Users/Subho/data/chuckle-net-unified/unified_dataset.jsonl'
    
    if not os.path.exists(unified_file):
        print("❌ Unified dataset not found. Run build_unified_dataset.py first.")
        return
    
    print("\nLoading unified dataset...")
    unified = []
    with open(unified_file) as f:
        for line in f:
            unified.append(json.loads(line.strip()))
    
    print(f"Loaded {len(unified):,} utterances")
    
    # Separate by label
    positive = [u for u in unified if u.get('label_any') == 1]
    negative = [u for u in unified if u.get('label_any') == 0]
    
    print(f"\nOriginal distribution:")
    print(f"  Positive: {len(positive):,} ({len(positive)/len(unified)*100:.1f}%)")
    print(f"  Negative: {len(negative):,} ({len(negative)/len(unified)*100:.1f}%)")
    
    # Get samples with prosody
    positive_with_prosody = [p for p in positive if p.get('prosody') and len(p.get('prosody', [])) >= 7]
    negative_with_prosody = [n for n in negative if n.get('prosody') and len(n.get('prosody', [])) >= 7]
    
    print(f"\nWith prosody features:")
    print(f"  Positive: {len(positive_with_prosody):,}")
    print(f"  Negative: {len(negative_with_prosody):,}")
    
    # Load model
    print("\nLoading trained model...")
    model, scaler = load_trained_model()
    
    if model:
        print("✅ Model loaded for filtering")
    else:
        print("⚠️ Model not found, skipping model-based filtering")
    
    # Generate synthetic positives
    print("\nGenerating synthetic positive samples...")
    n_per_sample = 3  # 3 synthetic per positive sample
    
    # Sample subset for efficiency
    sample_size = min(2000, len(positive_with_prosody))
    sample_indices = np.random.choice(len(positive_with_prosody), sample_size, replace=False)
    sampled_positive = [positive_with_prosody[i] for i in sample_indices]
    
    synthetic_positives = generate_synthetic_samples_from_prosody(
        sampled_positive, 
        n_synthetic_per_sample=n_per_sample
    )
    
    print(f"Generated {len(synthetic_positives):,} synthetic positives")
    
    # Filter with model
    if model:
        print("\nFiltering with trained model...")
        filtered_positives, rejected = filter_synthetic_with_model(
            synthetic_positives, model, scaler, threshold=0.4
        )
        print(f"  Accepted: {len(filtered_positives):,}")
        print(f"  Rejected: {len(rejected):,}")
        synthetic_positives = filtered_positives
    
    # Generate synthetic negatives (for balance)
    print("\nGenerating synthetic negative samples...")
    n_neg = min(3000, len(negative_with_prosody))
    synthetic_negatives = generate_synthetic_negative_samples(
        negative_with_prosody, 
        n_synthetic=n_neg
    )
    print(f"Generated {len(synthetic_negatives):,} synthetic negatives")
    
    # Combine
    final_synthetic = synthetic_positives + synthetic_negatives
    
    # Save
    synthetic_file = f'{OUTPUT_DIR}/synthetic_dataset.jsonl'
    with open(synthetic_file, 'w') as f:
        for item in final_synthetic:
            f.write(json.dumps(item) + '\n')
    
    print(f"\n✅ Saved {len(final_synthetic):,} synthetic samples")
    print(f"   File: {synthetic_file}")
    
    # Summary
    synth_pos = len([s for s in final_synthetic if s.get('label_any') == 1])
    synth_neg = len([s for s in final_synthetic if s.get('label_any') == 0])
    
    print(f"\nSynthetic distribution:")
    print(f"  Positive: {synth_pos:,}")
    print(f"  Negative: {synth_neg:,}")
    
    # Combined stats
    total_orig = len(unified)
    total_synth = len(final_synthetic)
    total_combined = total_orig + total_synth
    
    new_pos = synth_pos
    new_neg = synth_neg
    
    print(f"\n" + "=" * 70)
    print("COMBINED DATASET SUMMARY")
    print("=" * 70)
    print(f"Original: {total_orig:,} utterances")
    print(f"Synthetic: {total_synth:,} utterances")
    print(f"Combined: {total_combined:,} utterances")
    print(f"\nOriginal positive rate: {len(positive)/len(unified)*100:.1f}%")
    
    # Calculate combined rate
    orig_pos = len(positive)
    orig_neg = len(negative)
    combined_pos = orig_pos + new_pos
    combined_neg = orig_neg + new_neg
    combined_rate = combined_pos / (combined_pos + combined_neg) * 100
    
    print(f"Synthetic positive rate: {new_pos/len(final_synthetic)*100:.1f}%")
    print(f"Combined positive rate: {combined_rate:.1f}%")

if __name__ == '__main__':
    main()
