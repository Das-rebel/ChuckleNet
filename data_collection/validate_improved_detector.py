#!/usr/bin/env python3
"""
Validation of the improved audio laughter detector on the existing audio_final/ dataset.
Compares detected laughter against the ground truth from the manifest.
"""
import os
import sys
import json
import numpy as np
from pathlib import Path
from tqdm import tqdm

# Import the detector - function name is extract_laughter_features
sys.path.append('/Users/Subho/autonomous_laughter_prediction/data_collection')
from improved_laughter_detector import extract_laughter_features

# Paths
MANIFEST_PATH = '/Users/Subho/autonomous_laughter_prediction/kaggle_extraction/video_manifest.json'
AUDIO_DIR = Path('/Users/Subho/data/chuckle-net/audio_final')

def main():
    print("🚀 Starting validation of improved laughter detector...")
    
    # 1. Load manifest to get ground truth
    with open(MANIFEST_PATH, 'r') as f:
        manifest = json.load(f)
    
    # Map video_id -> has_laughter (1 or 0)
    ground_truth = {}
    for v in manifest:
        ground_truth[v['video_id']] = 1 if v['n_positive'] > 0 else 0
    
    # 2. Scan audio_final/ for files
    audio_files = list(AUDIO_DIR.glob("*.wav"))
    print(f"🔍 Found {len(audio_files)} audio files in {AUDIO_DIR}")
    
    if not audio_files:
        print("❌ Error: No audio files found in audio_final/")
        return

    # 3. Run detection
    results = []
    print("🎤 Running audio analysis (RMS + ZCR + Periodicity)...")
    
    for audio_path in tqdm(audio_files):
        vid = audio_path.stem
        # Get ground truth (default to 0 if not in manifest)
        truth = ground_truth.get(vid, 0)
        
        # Get detector result (number of laughter clusters)
        detected_count = extract_laughter_features(str(audio_path))
        
        # Decision: Detected laughter if clusters > 0
        prediction = 1 if detected_count > 0 else 0
        
        results.append({
            'vid': vid,
            'truth': truth,
            'pred': prediction,
            'clusters': detected_count
        })

    # 4. Calculate Metrics
    y_true = np.array([r['truth'] for r in results])
    y_pred = np.array([r['pred'] for r in results])
    
    from sklearn.metrics import precision_score, recall_score, f1_score
    
    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    
    # Errors
    false_positives = [r['vid'] for r in results if r['truth'] == 0 and r['pred'] == 1]
    false_negatives = [r['vid'] for r in results if r['truth'] == 1 and r['pred'] == 0]
    true_positives = [r['vid'] for r in results if r['truth'] == 1 and r['pred'] == 1]

    print("\n" + "="*40)
    print("📊 VALIDATION RESULTS")
    print("="*40)
    print(f"Total Samples:    {len(results)}")
    print(f"True Positives:   {len(true_positives)}")
    print(f"False Positives:  {len(false_positives)}")
    print(f"False Negatives:  {len(false_negatives)}")
    print("-" * 40)
    print(f"Precision:        {precision:.3f}")
    print(f"Recall:           {recall:.3f}")
    print(f"F1 Score:         {f1:.3f}")
    print("="*40)
    
    if false_positives:
        print("\n⚠️ Sample False Positives (Noisy audio flagged as laughter):")
        for vid in false_positives[:5]:
            print(f"  - {vid}")
            
    if false_negatives:
        print("\n⚠️ Sample False Negatives (Laughter missed):")
        for vid in false_negatives[:5]:
            print(f"  - {vid}")

    if f1 > 0.5:
        print("\n✅ CONCLUSION: Detector is ready for scaleup collection.")
    else:
        print("\n❌ CONCLUSION: Detector requires threshold tuning or feature refinement.")

if __name__ == "__main__":
    import sys
    main()