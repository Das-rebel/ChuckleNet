#!/usr/bin/env python3
"""
Test richer acoustic features beyond F0/RMS for laughter prediction.
Evaluates MFCCs, spectral centroid, ZCR, HNR on top of baseline F0+Energy+Pause.

Uses per-video split to avoid data leakage.
Features extracted from actual audio files using librosa.
"""

import warnings
warnings.filterwarnings('ignore')

import os
import glob
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score, classification_report
from sklearn.preprocessing import StandardScaler
import librosa
from collections import defaultdict
import time

# ─── Config ───
CSV_PATH = 'autonomous_laughter_prediction_essential/data/audio_comedy/prosody_features_50videos.csv'
AUDIO_ROOT = 'autonomous_laughter_prediction_essential/data/audio_comedy/audio'
SR = 16000  # target sample rate

# ─── Load existing features ───
print("Loading existing prosody features...")
df = pd.read_csv(CSV_PATH)
print(f"  Total rows: {len(df):,}")
print(f"  Label=1 (laugh): {df['label'].sum():,} ({df['label'].mean()*100:.1f}%)")
print(f"  Unique videos: {df['video_id'].nunique()}")

# ─── Build audio path map ───
audio_files = glob.glob(os.path.join(AUDIO_ROOT, '**/*.mp3'), recursive=True)
audio_map = {}
for f in audio_files:
    vid = os.path.splitext(os.path.basename(f))[0]
    audio_map[vid] = f

matched_videos = set(df['video_id'].unique()) & set(audio_map.keys())
print(f"  Videos with audio: {len(matched_videos)}/{df['video_id'].nunique()}")

# Filter to matched videos
df = df[df['video_id'].isin(matched_videos)].reset_index(drop=True)
print(f"  Rows after filter: {len(df):,}")


# ─── Feature extraction functions ───

def extract_mfcc_stats(y_segment, sr, n_mfcc=13):
    """Extract MFCC statistics (mean, std) for n_mfcc coefficients."""
    mfccs = librosa.feature.mfcc(y=y_segment, sr=sr, n_mfcc=n_mfcc, hop_length=256)
    stats = {}
    for i in range(n_mfcc):
        stats[f'mfcc_{i}_mean'] = np.mean(mfccs[i])
        stats[f'mfcc_{i}_std'] = np.std(mfccs[i])
    return stats

def extract_spectral_centroid(y_segment, sr):
    """Extract spectral centroid statistics."""
    sc = librosa.feature.spectral_centroid(y=y_segment, sr=sr, hop_length=256)[0]
    return {
        'spectral_centroid_mean': np.mean(sc),
        'spectral_centroid_std': np.std(sc),
        'spectral_centroid_max': np.max(sc),
    }

def extract_zcr(y_segment, sr):
    """Extract zero-crossing rate statistics."""
    zcr = librosa.feature.zero_crossing_rate(y=y_segment, frame_length=512, hop_length=256)[0]
    return {
        'zcr_mean': np.mean(zcr),
        'zcr_std': np.std(zcr),
        'zcr_max': np.max(zcr),
    }

def extract_hnr(y_segment, sr):
    """Estimate harmonics-to-noise ratio using autocorrelation method."""
    # Simple HNR estimation via autocorrelation
    # Normalize
    y_norm = y_segment / (np.max(np.abs(y_segment)) + 1e-10)
    
    if len(y_norm) < sr * 0.01:  # too short
        return {'hnr_mean': 0, 'hnr_std': 0}
    
    # Compute short-time HNR
    frame_len = int(sr * 0.03)  # 30ms frames
    hop = int(sr * 0.01)  # 10ms hop
    hnr_vals = []
    
    for start in range(0, len(y_norm) - frame_len, hop):
        frame = y_norm[start:start + frame_len]
        if np.max(np.abs(frame)) < 1e-8:
            hnr_vals.append(0)
            continue
        
        # Autocorrelation
        corr = np.correlate(frame, frame, mode='full')
        corr = corr[len(corr)//2:]
        
        if corr[0] < 1e-10:
            hnr_vals.append(0)
            continue
        
        # Find first peak after zero lag
        min_lag = int(sr * 0.005)  # ~200Hz max fundamental
        max_lag = int(sr * 0.02)   # ~50Hz min fundamental
        
        if max_lag >= len(corr):
            hnr_vals.append(0)
            continue
            
        search_region = corr[min_lag:max_lag]
        if len(search_region) == 0:
            hnr_vals.append(0)
            continue
            
        peak_idx = np.argmax(search_region) + min_lag
        r_peak = corr[peak_idx]
        r_zero = corr[0]
        
        if r_zero > 0:
            hnr_val = r_peak / r_zero
            hnr_vals.append(hnr_val)
        else:
            hnr_vals.append(0)
    
    hnr_arr = np.array(hnr_vals)
    return {
        'hnr_mean': np.mean(hnr_arr) if len(hnr_arr) > 0 else 0,
        'hnr_std': np.std(hnr_arr) if len(hnr_arr) > 0 else 0,
    }


# ─── Extract richer features per video ───
print("\n" + "="*60)
print("EXTRACTING RICHER ACOUSTIC FEATURES")
print("="*60)

all_features = []
videos = sorted(df['video_id'].unique())
total_videos = len(videos)

for vi, vid in enumerate(videos):
    t0 = time.time()
    vid_df = df[df['video_id'] == vid]
    audio_path = audio_map[vid]
    
    print(f"\n[{vi+1}/{total_videos}] {vid} ({len(vid_df)} words) ...", end='', flush=True)
    
    # Load full audio
    try:
        y_full, sr = librosa.load(audio_path, sr=SR)
    except Exception as e:
        print(f" FAILED to load: {e}")
        continue
    
    # Extract features per word
    vid_features = []
    skipped = 0
    for _, row in vid_df.iterrows():
        start_sample = int(row['start'] * sr)
        end_sample = int(row['end'] * sr)
        
        # Bounds check
        start_sample = max(0, start_sample)
        end_sample = min(len(y_full), end_sample)
        
        if end_sample - start_sample < 512:  # too short
            skipped += 1
            feat = {
                **extract_mfcc_stats(np.zeros(512), sr),
                **extract_spectral_centroid(np.zeros(512), sr),
                **extract_zcr(np.zeros(512), sr),
                **extract_hnr(np.zeros(512), sr),
            }
            feat['video_id'] = vid
            feat['idx'] = row.name  # original index
            vid_features.append(feat)
            continue
        
        y_segment = y_full[start_sample:end_sample]
        
        feat = {}
        try:
            feat.update(extract_mfcc_stats(y_segment, sr))
        except:
            feat.update({f'mfcc_{i}_{s}': 0 for i in range(13) for s in ['mean', 'std']})
        
        try:
            feat.update(extract_spectral_centroid(y_segment, sr))
        except:
            feat.update({f'spectral_centroid_{s}': 0 for s in ['mean', 'std', 'max']})
        
        try:
            feat.update(extract_zcr(y_segment, sr))
        except:
            feat.update({f'zcr_{s}': 0 for s in ['mean', 'std', 'max']})
        
        try:
            feat.update(extract_hnr(y_segment, sr))
        except:
            feat.update({f'hnr_{s}': 0 for s in ['mean', 'std']})
        
        feat['video_id'] = vid
        feat['idx'] = row.name
        vid_features.append(feat)
    
    all_features.extend(vid_features)
    elapsed = time.time() - t0
    print(f" done ({elapsed:.1f}s, skipped={skipped})")

features_df = pd.DataFrame(all_features)
print(f"\nTotal features extracted: {len(features_df):,}")

# ─── Merge with original DataFrame ───
features_df = features_df.set_index('idx')
df_merged = df.join(features_df, on=df.index.name if df.index.name else 'index', rsuffix='_new')
# Drop duplicate video_id column
if 'video_id_new' in df_merged.columns:
    df_merged = df_merged.drop(columns=['video_id_new'])

print(f"Merged DataFrame: {len(df_merged):,} rows, {len(df_merged.columns)} columns")
print(f"Columns: {list(df_merged.columns)}")

# ─── Check for NaN/inf ───
numeric_cols = df_merged.select_dtypes(include=[np.number]).columns
df_merged[numeric_cols] = df_merged[numeric_cols].replace([np.inf, -np.inf], np.nan)
nan_counts = df_merged[numeric_cols].isna().sum()
print(f"\nNaN counts per column:")
print(nan_counts[nan_counts > 0].to_string())
df_merged[numeric_cols] = df_merged[numeric_cols].fillna(0)


# ─── Define feature sets ───

BASELINE_COLS = ['f0_mean', 'f0_std', 'f0_range', 'f0_max', 'f0_min',
                 'rms_mean', 'rms_std', 'rms_max', 'pause_before', 'word_duration']

MFCC_COLS = [f'mfcc_{i}_{s}' for i in range(13) for s in ['mean', 'std']]

SPECTRAL_COLS = ['spectral_centroid_mean', 'spectral_centroid_std', 'spectral_centroid_max']

ZCR_COLS = ['zcr_mean', 'zcr_std', 'zcr_max']

HNR_COLS = ['hnr_mean', 'hnr_std']

feature_sets = {
    'Baseline (F0+Energy+Pause)': BASELINE_COLS,
    '+ MFCCs': BASELINE_COLS + MFCC_COLS,
    '+ Spectral Centroid': BASELINE_COLS + SPECTRAL_COLS,
    '+ ZCR': BASELINE_COLS + ZCR_COLS,
    '+ HNR': BASELINE_COLS + HNR_COLS,
    'All Combined': BASELINE_COLS + MFCC_COLS + SPECTRAL_COLS + ZCR_COLS + HNR_COLS,
}


# ─── Train and evaluate with per-video split ───

print("\n" + "="*60)
print("EVALUATION: PER-VIDEO SPLIT (5-fold CV by video)")
print("="*60)

from sklearn.model_selection import GroupKFold

videos = df_merged['video_id'].values
labels = df_merged['label'].values

gkf = GroupKFold(n_splits=5)

results = {}

for feat_name, feat_cols in feature_sets.items():
    # Verify columns exist
    missing = [c for c in feat_cols if c not in df_merged.columns]
    if missing:
        print(f"  MISSING columns for {feat_name}: {missing}")
        continue
    
    X = df_merged[feat_cols].values
    y = df_merged['label'].values
    
    fold_f1s = []
    fold_details = []
    
    for fold, (train_idx, test_idx) in enumerate(gkf.split(X, y, groups=videos)):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        # Scale
        scaler = StandardScaler()
        X_train = scaler.fit_transform(X_train)
        X_test = scaler.transform(X_test)
        
        # Train RF (same as baseline setup)
        clf = RandomForestClassifier(
            n_estimators=200,
            max_depth=15,
            min_samples_leaf=5,
            class_weight='balanced',
            random_state=42,
            n_jobs=-1
        )
        clf.fit(X_train, y_train)
        y_pred = clf.predict(X_test)
        
        f1 = f1_score(y_test, y_pred, zero_division=0)
        fold_f1s.append(f1)
        
        # Per-class detail
        from sklearn.metrics import precision_score, recall_score
        prec = precision_score(y_test, y_pred, zero_division=0)
        rec = recall_score(y_test, y_pred, zero_division=0)
        
        n_pos_train = y_train.sum()
        n_pos_test = y_test.sum()
        fold_details.append({
            'fold': fold,
            'f1': f1,
            'precision': prec,
            'recall': rec,
            'n_train_pos': n_pos_train,
            'n_test_pos': n_pos_test,
        })
    
    mean_f1 = np.mean(fold_f1s)
    std_f1 = np.std(fold_f1s)
    results[feat_name] = {
        'mean_f1': mean_f1,
        'std_f1': std_f1,
        'fold_f1s': fold_f1s,
        'fold_details': fold_details,
    }
    
    print(f"\n{feat_name}:")
    print(f"  F1 = {mean_f1:.4f} ± {std_f1:.4f}")
    print(f"  Fold F1s: {[f'{f:.4f}' for f in fold_f1s]}")
    for d in fold_details:
        print(f"    Fold {d['fold']}: F1={d['f1']:.4f}, P={d['precision']:.4f}, R={d['recall']:.4f}")


# ─── Summary table ───

print("\n" + "="*60)
print("SUMMARY: Feature Set Comparison")
print("="*60)
print(f"{'Feature Set':<30} {'F1':>8} {'± std':>8} {'# feats':>8}")
print("-"*56)

baseline_f1 = results.get('Baseline (F0+Energy+Pause)', {}).get('mean_f1', 0)

for feat_name, feat_cols in feature_sets.items():
    if feat_name in results:
        r = results[feat_name]
        delta = r['mean_f1'] - baseline_f1
        print(f"{feat_name:<30} {r['mean_f1']:>8.4f} {r['std_f1']:>8.4f} {len(feat_cols):>8}  (Δ={delta:+.4f})")


# ─── Feature importance for best model ───

print("\n" + "="*60)
print("FEATURE IMPORTANCE (All Combined, trained on full data)")
print("="*60)

feat_cols = feature_sets['All Combined']
X_all = df_merged[feat_cols].values
y_all = df_merged['label'].values

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_all)

clf_final = RandomForestClassifier(
    n_estimators=200, max_depth=15, min_samples_leaf=5,
    class_weight='balanced', random_state=42, n_jobs=-1
)
clf_final.fit(X_scaled, y_all)

importances = clf_final.feature_importances_
indices = np.argsort(importances)[::-1]

print(f"{'Rank':<5} {'Feature':<30} {'Importance':>10}")
print("-"*50)
for rank, idx in enumerate(indices[:25]):
    print(f"{rank+1:<5} {feat_cols[idx]:<30} {importances[idx]:>10.4f}")

# ─── Category-level importance ───

print("\nCategory-level importance:")
categories = {
    'F0': [c for c in feat_cols if c.startswith('f0_')],
    'RMS/Energy': [c for c in feat_cols if c.startswith('rms_')],
    'Pause/Duration': [c for c in feat_cols if c.startswith('pause_') or c.startswith('word_')],
    'MFCC': [c for c in feat_cols if c.startswith('mfcc_')],
    'Spectral': [c for c in feat_cols if c.startswith('spectral_')],
    'ZCR': [c for c in feat_cols if c.startswith('zcr_')],
    'HNR': [c for c in feat_cols if c.startswith('hnr_')],
}

for cat, cols in categories.items():
    cat_indices = [feat_cols.index(c) for c in cols if c in feat_cols]
    cat_importance = sum(importances[i] for i in cat_indices)
    print(f"  {cat:<15}: {cat_importance:.4f} ({len(cols)} features)")

print("\n✅ Done!")