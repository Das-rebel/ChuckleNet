#!/usr/bin/env python3
"""
Train a simple MLP on prosody features for laughter prediction.
Works on CPU - uses only prosody features (21-dim).
"""

import json
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import f1_score, classification_report
import joblib
import os
from datetime import datetime
from sklearn.utils.class_weight import compute_sample_weight

# ============================================================================
# CONFIG
# ============================================================================

DATA_FILE = '/Users/Subho/data/chuckle-net-youtube/combined_dataset.jsonl'
OUTPUT_DIR = '/Users/Subho/data/chuckle-net-youtube/prosody_mlp'
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("=== Prosody MLP Training (CPU) ===")
print(f"Started: {datetime.now()}")

# ============================================================================
# LOAD DATA
# ============================================================================

print("\nLoading data...")
X = []
y = []
sources = []
video_ids = []

with open(DATA_FILE) as f:
    for line in f:
        data = json.loads(line)
        X.append(data['prosody'])
        y.append(data['label_any'])
        sources.append(data['source'])
        video_ids.append(data['video_id'])

X = np.array(X)
y = np.array(y)
sources = np.array(sources)
video_ids = np.array(video_ids)

print(f"Total samples: {len(X)}")
print(f"Positive: {y.sum()} ({y.mean()*100:.1f}%)")
print(f"YouTube: {(sources == 'youtube').sum()}")
print(f"Original: {(sources == 'original').sum()}")

# ============================================================================
# SPLIT BY VIDEO (to avoid leakage)
# ============================================================================

print("\nSplitting by video...")

unique_videos = list(set(video_ids))
np.random.seed(42)
np.random.shuffle(unique_videos)

# 70% train, 15% val, 15% test
n_train = int(len(unique_videos) * 0.70)
n_val = int(len(unique_videos) * 0.15)

train_videos = set(unique_videos[:n_train])
val_videos = set(unique_videos[n_train:n_train+n_val])
test_videos = set(unique_videos[n_train+n_val:])

train_mask = np.array([v in train_videos for v in video_ids])
val_mask = np.array([v in val_videos for v in video_ids])
test_mask = np.array([v in test_videos for v in video_ids])

X_train, y_train = X[train_mask], y[train_mask]
X_val, y_val = X[val_mask], y[val_mask]
X_test, y_test = X[test_mask], y[test_mask]

print(f"Train: {len(X_train)} ({y_train.sum()} positive, {y_train.mean()*100:.1f}%)")
print(f"Val: {len(X_val)} ({y_val.sum()} positive, {y_val.mean()*100:.1f}%)")
print(f"Test: {len(X_test)} ({y_test.sum()} positive, {y_test.mean()*100:.1f}%)")

# ============================================================================
# SCALE FEATURES
# ============================================================================

print("\nScaling features...")
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_val_scaled = scaler.transform(X_val)
X_test_scaled = scaler.transform(X_test)

# ============================================================================
# TRAIN MLP
# ============================================================================

print("\nTraining MLP...")

# Handle class imbalance with class_weight
from sklearn.utils.class_weight import compute_class_weight
classes = np.unique(y_train)
weights = compute_class_weight('balanced', classes=classes, y=y_train)
class_weight = {c: w for c, w in zip(classes, weights)}
print(f"Class weights: {class_weight}")

mlp = MLPClassifier(
    hidden_layer_sizes=(128, 64, 32),
    activation='relu',
    solver='adam',
    alpha=0.001,  # L2 regularization
    batch_size=256,
    learning_rate='adaptive',
    learning_rate_init=0.001,
    max_iter=200,
    early_stopping=True,
    validation_fraction=0.1,
    n_iter_no_change=20,
    random_state=42,
    verbose=True,
)

# Use sample weights to handle imbalance
sample_weights = compute_sample_weight('balanced', y_train)
mlp.fit(X_train_scaled, y_train, sample_weight=sample_weights)

print(f"\nTraining stopped at iteration: {mlp.n_iter_}")

# ============================================================================
# EVALUATE
# ============================================================================

print("\n=== RESULTS ===")

for name, X_s, y_s in [('Train', X_train_scaled, y_train), 
                         ('Val', X_val_scaled, y_val),
                         ('Test', X_test_scaled, y_test)]:
    y_pred = mlp.predict(X_s)
    f1 = f1_score(y_s, y_pred, average='binary')
    f1_macro = f1_score(y_s, y_pred, average='macro')
    print(f"{name}: F1={f1:.4f}, F1-macro={f1_macro:.4f}")

# Detailed report on test
print("\n=== TEST CLASSIFICATION REPORT ===")
y_test_pred = mlp.predict(X_test_scaled)
print(classification_report(y_test, y_test_pred, digits=4))

# ============================================================================
# SAVE MODEL
# ============================================================================

timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
model_file = f'{OUTPUT_DIR}/prosody_mlp_{timestamp}.pkl'
scaler_file = f'{OUTPUT_DIR}/scaler_{timestamp}.pkl'

joblib.dump(mlp, model_file)
joblib.dump(scaler, scaler_file)

print(f"\nModel saved: {model_file}")
print(f"Scaler saved: {scaler_file}")

# ============================================================================
# SAVE RESULTS
# ============================================================================

results = {
    'model': 'MLP (128, 64, 32)',
    'features': 'prosody_21dim',
    'train_samples': int(len(X_train)),
    'val_samples': int(len(X_val)),
    'test_samples': int(len(X_test)),
    'positive_rate_train': float(y_train.mean()),
    'positive_rate_val': float(y_val.mean()),
    'positive_rate_test': float(y_test.mean()),
    'n_iter': int(mlp.n_iter_),
    'train_f1': float(f1_score(y_train, mlp.predict(X_train_scaled))),
    'val_f1': float(f1_score(y_val, mlp.predict(X_val_scaled))),
    'test_f1': float(f1_score(y_test, y_test_pred)),
    'test_f1_macro': float(f1_score(y_test, y_test_pred, average='macro')),
    'timestamp': timestamp,
    'model_file': model_file,
}

results_file = f'{OUTPUT_DIR}/results_{timestamp}.json'
with open(results_file, 'w') as f:
    json.dump(results, f, indent=2)

print(f"Results: {results_file}")
print(f"\nFinished: {datetime.now()}")
