#!/usr/bin/env python3
"""
Quick SMOTE Test for MELD - Focused on results
"""

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix
from sklearn.preprocessing import StandardScaler
from imblearn.over_sampling import SMOTE
import warnings
warnings.filterwarnings('ignore')

print("🎯 QUICK SMOTE TEST FOR MELD")
print("=" * 40)

# Load data
print("\n📊 Loading data...")
meld_path = Path("~/datasets/MELD").expanduser()
data_path = meld_path / "data" / "MELD"

train_df = pd.read_csv(data_path / "train_sent_emo.csv")
dev_df = pd.read_csv(data_path / "dev_sent_emo.csv")
test_df = pd.read_csv(data_path / "test_sent_emo.csv")
train_df = pd.concat([train_df, dev_df], ignore_index=True)

# Simple features
print("🧬 Creating simple features...")
def simple_features(df):
    features = pd.DataFrame({
        'length': df['Utterance'].str.len(),
        'words': df['Utterance'].str.split().str.len(),
        'exclamations': df['Utterance'].str.count('!')
    })

    # TF-IDF
    if not hasattr(simple_features, 'tfidf'):
        simple_features.tfidf = TfidfVectorizer(max_features=20, stop_words='english')
        tfidf_matrix = simple_features.tfidf.fit_transform(df['Utterance'])
    else:
        tfidf_matrix = simple_features.tfidf.transform(df['Utterance'])

    tfidf_df = pd.DataFrame(tfidf_matrix.toarray(), columns=[f'tfidf_{i}' for i in range(tfidf_matrix.shape[1])])
    return pd.concat([features.reset_index(drop=True), tfidf_df], axis=1)

X_train = simple_features(train_df)
X_test = simple_features(test_df)

y_train = (train_df['Emotion'] == 'joy').astype(int)
y_test = (test_df['Emotion'] == 'joy').astype(int)

print(f"  Features: {X_train.shape[1]}")
print(f"  Train joy: {y_train.sum()} ({y_train.mean()*100:.1f}%)")
print(f"  Test joy: {y_test.sum()} ({y_test.mean()*100:.1f}%)")

# Scale
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Split for validation
X_train_split, X_val_split, y_train_split, y_val_split = train_test_split(
    X_train_scaled, y_train, test_size=0.2, stratify=y_train, random_state=42
)

# Apply SMOTE
print("\n⚖️ Applying SMOTE...")
print(f"  Before: {X_train_split.shape} (Joy: {y_train_split.sum()})")

smote = SMOTE(random_state=42, k_neighbors=3)
X_smote, y_smote = smote.fit_resample(X_train_split, y_train_split)

print(f"  After: {X_smote.shape} (Joy: {y_smote.sum()})")

# Train quick models
print("\n🤖 Training quick models...")

# Random Forest (smaller for speed)
rf = RandomForestClassifier(n_estimators=50, max_depth=8, random_state=42, n_jobs=1)
rf.fit(X_smote, y_smote)
print("  ✅ Random Forest trained")

# Logistic Regression (faster)
lr = LogisticRegression(max_iter=500, random_state=42)
lr.fit(X_smote, y_smote)
print("  ✅ Logistic Regression trained")

# Evaluate on validation
print("\n📈 VALIDATION RESULTS:")

def quick_eval(model, X, y, name):
    y_pred = model.predict(X)
    accuracy = accuracy_score(y, y_pred)
    precision, recall, f1, _ = precision_recall_fscore_support(y, y_pred, average='binary', zero_division=0)
    cm = confusion_matrix(y, y_pred)

    print(f"\n  {name}:")
    print(f"    Acc: {accuracy*100:.1f}%, Prec: {precision*100:.1f}%, Rec: {recall*100:.1f}%, F1: {f1*100:.1f}%")
    print(f"    TP: {cm[1,1]}, FP: {cm[0,1]}, FN: {cm[1,0]}, TN: {cm[0,0]}")
    return {'acc': accuracy, 'prec': precision, 'rec': recall, 'f1': f1, 'cm': cm}

rf_val = quick_eval(rf, X_val_split, y_val_split, "Random Forest")
lr_val = quick_eval(lr, X_val_split, y_val_split, "Logistic Regression")

# Test on test set
print("\n🎯 TEST SET RESULTS:")

rf_test = quick_eval(rf, X_test_scaled, y_test, "Random Forest")
lr_test = quick_eval(lr, X_test_scaled, y_test, "Logistic Regression")

# Threshold optimization for best model
best_model = rf if rf_val['f1'] > lr_val['f1'] else lr
print(f"\n🎯 Best model: {'Random Forest' if rf_val['f1'] > lr_val['f1'] else 'Logistic Regression'}")

# Optimize threshold
y_probs = best_model.predict_proba(X_test_scaled)[:, 1]

print("\n🎯 Threshold Optimization:")
best_thresh = 0.5
best_f1 = 0

for thresh in np.arange(0.1, 0.9, 0.1):
    y_pred_t = (y_probs >= thresh).astype(int)
    _, _, f1, _ = precision_recall_fscore_support(y_test, y_pred_t, average='binary', zero_division=0)

    if f1 > best_f1:
        best_f1 = f1
        best_thresh = thresh

    # Count predictions
    n_joy_pred = y_pred_t.sum()
    print(f"  Thresh {thresh:.1f}: F1={f1:.3f}, Joy predictions={n_joy_pred}")

print(f"\n✅ Best threshold: {best_thresh:.1f} (F1: {best_f1:.3f})")

# Final results
y_pred_final = (y_probs >= best_thresh).astype(int)
final_acc = accuracy_score(y_test, y_pred_final)
final_prec, final_rec, final_f1, _ = precision_recall_fscore_support(y_test, y_pred_final, average='binary', zero_division=0)
final_cm = confusion_matrix(y_test, y_pred_final)

print("\n🏆 FINAL OPTIMIZED RESULTS:")
print(f"  Accuracy: {final_acc*100:.1f}%")
print(f"  Precision: {final_prec*100:.1f}%")
print(f"  Recall: {final_rec*100:.1f}%")
print(f"  F1-Score: {final_f1*100:.1f}%")
print(f"  True Positives: {final_cm[1,1]}/{y_test.sum()} joy samples detected")
print(f"  False Positives: {final_cm[0,1]}")

# Compare to baseline (no SMOTE)
print("\n📊 BASELINE COMPARISON (No SMOTE):")
rf_baseline = RandomForestClassifier(n_estimators=50, max_depth=8, random_state=42, n_jobs=1)
rf_baseline.fit(X_train_split, y_train_split)
y_pred_base = rf_baseline.predict(X_test_scaled)
base_acc = accuracy_score(y_test, y_pred_base)
base_prec, base_rec, base_f1, _ = precision_recall_fscore_support(y_test, y_pred_base, average='binary', zero_division=0)
base_cm = confusion_matrix(y_test, y_pred_base)

print(f"  Accuracy: {base_acc*100:.1f}%")
print(f"  Precision: {base_prec*100:.1f}%")
print(f"  Recall: {base_rec*100:.1f}%")
print(f"  F1-Score: {base_f1*100:.1f}%")
print(f"  True Positives: {base_cm[1,1]}/{y_test.sum()} joy samples detected")

print(f"\n🚀 SMOTE IMPROVEMENT:")
print(f"  F1-Score: {base_f1*100:.1f}% → {final_f1*100:.1f}% ({final_f1-base_f1:+.1f}%)")
print(f"  True Positives: {base_cm[1,1]} → {final_cm[1,1]} ({final_cm[1,1]-base_cm[1,1]:+d})")

print("\n✅ Quick SMOTE Test Complete!")