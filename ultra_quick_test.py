#!/usr/bin/env python3
"""
Ultra-quick SMOTE test - minimal features, fast models
"""

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix
from sklearn.preprocessing import StandardScaler
from imblearn.over_sampling import SMOTE
import warnings
warnings.filterwarnings('ignore')

print("🚀 ULTRA-QUICK SMOTE TEST")

# Load data
print("📊 Loading MELD...")
meld_path = Path("~/datasets/MELD").expanduser()
data_path = meld_path / "data" / "MELD"

train_df = pd.read_csv(data_path / "train_sent_emo.csv")
test_df = pd.read_csv(data_path / "test_sent_emo.csv")

# Ultra-simple features
print("🧬 Creating minimal features...")
tfidf = TfidfVectorizer(max_features=10, stop_words='english')
X_train = tfidf.fit_transform(train_df['Utterance']).toarray()
X_test = tfidf.transform(test_df['Utterance']).toarray()

y_train = (train_df['Emotion'] == 'joy').astype(int)
y_test = (test_df['Emotion'] == 'joy').astype(int)

print(f"  Train: {X_train.shape[0]} samples, {y_train.sum()} joy ({y_train.mean()*100:.1f}%)")
print(f"  Test: {X_test.shape[0]} samples, {y_test.sum()} joy ({y_test.mean()*100:.1f}%)")

# Scale
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Split
X_tr, X_val, y_tr, y_val = train_test_split(X_train_scaled, y_train, test_size=0.2, stratify=y_train, random_state=42)

# Apply SMOTE
print("⚖️ Applying SMOTE...")
print(f"  Before: {y_tr.sum()} joy samples")

smote = SMOTE(random_state=42, k_neighbors=3)
X_smote, y_smote = smote.fit_resample(X_tr, y_tr)

print(f"  After: {y_smote.sum()} joy samples")

# Train Logistic Regression (very fast)
print("🤖 Training Logistic Regression...")
lr = LogisticRegression(max_iter=500, random_state=42)
lr.fit(X_smote, y_smote)

# Test on validation
y_pred_val = lr.predict(X_val)
val_acc = accuracy_score(y_val, y_pred_val)
val_prec, val_rec, val_f1, _ = precision_recall_fscore_support(y_val, y_pred_val, average='binary', zero_division=0)
val_cm = confusion_matrix(y_val, y_pred_val)

print(f"\n📈 VALIDATION: Acc={val_acc*100:.1f}%, Prec={val_prec*100:.1f}%, Rec={val_rec*100:.1f}%, F1={val_f1*100:.1f}%")
print(f"  TP={val_cm[1,1]}, FP={val_cm[0,1]}, FN={val_cm[1,0]}, TN={val_cm[0,0]}")

# Test on test set
y_pred_test = lr.predict(X_test_scaled)
test_acc = accuracy_score(y_test, y_pred_test)
test_prec, test_rec, test_f1, _ = precision_recall_fscore_support(y_test, y_pred_test, average='binary', zero_division=0)
test_cm = confusion_matrix(y_test, y_pred_test)

print(f"\n🎯 TEST: Acc={test_acc*100:.1f}%, Prec={test_prec*100:.1f}%, Rec={test_rec*100:.1f}%, F1={test_f1*100:.1f}%")
print(f"  TP={test_cm[1,1]}, FP={test_cm[0,1]}, FN={test_cm[1,0]}, TN={test_cm[0,0]}")

# Compare to baseline
lr_base = LogisticRegression(max_iter=500, random_state=42)
lr_base.fit(X_tr, y_tr)
y_pred_base = lr_base.predict(X_test_scaled)
base_acc = accuracy_score(y_test, y_pred_base)
base_prec, base_rec, base_f1, _ = precision_recall_fscore_support(y_test, y_pred_base, average='binary', zero_division=0)
base_cm = confusion_matrix(y_test, y_pred_base)

print(f"\n📊 BASELINE (no SMOTE): Acc={base_acc*100:.1f}%, Prec={base_prec*100:.1f}%, Rec={base_rec*100:.1f}%, F1={base_f1*100:.1f}%")
print(f"  TP={base_cm[1,1]}, FP={base_cm[0,1]}, FN={base_cm[1,0]}, TN={base_cm[0,0]}")

print(f"\n🚀 SMOTE IMPACT:")
print(f"  F1-Score: {base_f1*100:.1f}% → {test_f1*100:.1f}% ({test_f1-base_f1:+.1f}%)")
print(f"  Joy Detection: {base_cm[1,1]} → {test_cm[1,1]} ({test_cm[1,1]-base_cm[1,1]:+d} samples)")

# Try threshold optimization
y_probs = lr.predict_proba(X_test_scaled)[:, 1]
best_thresh = 0.5
best_f1 = 0

print(f"\n🎯 THRESHOLD OPTIMIZATION:")
for thresh in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]:
    y_pred_t = (y_probs >= thresh).astype(int)
    _, _, f1, _ = precision_recall_fscore_support(y_test, y_pred_t, average='binary', zero_division=0)
    n_pred = y_pred_t.sum()
    print(f"  Thresh {thresh}: F1={f1:.3f}, Predictions={n_pred}")

    if f1 > best_f1:
        best_f1 = f1
        best_thresh = thresh

print(f"\n✅ Best threshold: {best_thresh} (F1: {best_f1:.3f})")
print("🎯 ULTRA-QUICK TEST COMPLETE!")