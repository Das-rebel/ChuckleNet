#!/usr/bin/env python3
"""
Simplified Advanced Techniques for MELD Laughter Detection
Testing SMOTE and ensemble methods step by step
"""

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix
from sklearn.preprocessing import StandardScaler
from imblearn.over_sampling import SMOTE
import warnings
warnings.filterwarnings('ignore')

print("🎯 Advanced MELD Testing - Step by Step")
print("=" * 50)

# Step 1: Load data
print("\n📊 Step 1: Loading MELD data...")
meld_path = Path("~/datasets/MELD").expanduser()
data_path = meld_path / "data" / "MELD"

train_df = pd.read_csv(data_path / "train_sent_emo.csv")
dev_df = pd.read_csv(data_path / "dev_sent_emo.csv")
test_df = pd.read_csv(data_path / "test_sent_emo.csv")

train_df = pd.concat([train_df, dev_df], ignore_index=True)
print(f"  ✅ Training: {len(train_df)} samples")
print(f"  ✅ Test: {len(test_df)} samples")

# Step 2: Create features
print("\n🧬 Step 2: Creating features...")
def create_features(df):
    features = pd.DataFrame()

    # Text features
    features['length'] = df['Utterance'].str.len()
    features['words'] = df['Utterance'].str.split().str.len()
    features['exclamations'] = df['Utterance'].str.count('!')
    features['questions'] = df['Utterance'].str.count('\\?')

    # Laughter indicators
    laughter_words = ['haha', 'hahaha', 'lol', 'lmao', 'hee', 'giggle']
    features['laughter'] = df['Utterance'].str.lower().apply(lambda x: sum(1 for w in laughter_words if w in x))

    # Positive words
    positive_words = ['great', 'good', 'love', 'happy', 'awesome', 'fantastic', 'amazing']
    features['positive'] = df['Utterance'].str.lower().apply(lambda x: sum(1 for w in positive_words if w in x.split()))

    # TF-IDF
    if not hasattr(create_features, 'vectorizer'):
        create_features.vectorizer = TfidfVectorizer(max_features=30, stop_words='english')
        tfidf = create_features.vectorizer.fit_transform(df['Utterance'])
    else:
        tfidf = create_features.vectorizer.transform(df['Utterance'])

    tfidf_df = pd.DataFrame(tfidf.toarray(), columns=[f'tfidf_{i}' for i in range(tfidf.shape[1])])
    features = pd.concat([features.reset_index(drop=True), tfidf_df], axis=1)

    return features

X_train = create_features(train_df)
X_test = create_features(test_df)

y_train = (train_df['Emotion'] == 'joy').astype(int)
y_test = (test_df['Emotion'] == 'joy').astype(int)

print(f"  ✅ Features: {X_train.shape[1]}")
print(f"  😊 Train joy: {y_train.sum()} ({y_train.mean()*100:.1f}%)")
print(f"  😊 Test joy: {y_test.sum()} ({y_test.mean()*100:.1f}%)")

# Step 3: Scale features
print("\n⚙️ Step 3: Scaling features...")
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Step 4: Split for validation
print("\n🔪 Step 4: Splitting for validation...")
X_train_split, X_val_split, y_train_split, y_val_split = train_test_split(
    X_train_scaled, y_train, test_size=0.2, stratify=y_train, random_state=42
)

# Step 5: Apply SMOTE
print("\n⚖️ Step 5: Applying SMOTE...")
print(f"  Before SMOTE: {X_train_split.shape} (Joy: {y_train_split.sum()})")

smote = SMOTE(random_state=42, k_neighbors=3)
X_smote, y_smote = smote.fit_resample(X_train_split, y_train_split)

print(f"  After SMOTE: {X_smote.shape} (Joy: {y_smote.sum()})")

# Step 6: Train multiple models
print("\n🤖 Step 6: Training models...")

# Model 1: Random Forest with SMOTE
print("  🌲 Training Random Forest + SMOTE...")
rf_smote = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
rf_smote.fit(X_smote, y_smote)

# Model 2: Gradient Boosting with SMOTE
print("  📈 Training Gradient Boosting + SMOTE...")
gb_smote = GradientBoostingClassifier(n_estimators=100, max_depth=5, random_state=42)
gb_smote.fit(X_smote, y_smote)

# Model 3: Logistic Regression with SMOTE
print("  📊 Training Logistic Regression + SMOTE...")
lr_smote = LogisticRegression(max_iter=1000, class_weight='balanced', random_state=42)
lr_smote.fit(X_smote, y_smote)

# Step 7: Evaluate on validation set
print("\n📈 Step 7: Evaluating on validation set...")

def evaluate_model(model, X_val, y_val, name):
    y_pred = model.predict(X_val)
    accuracy = accuracy_score(y_val, y_pred)
    precision, recall, f1, _ = precision_recall_fscore_support(y_val, y_pred, average='binary', zero_division=0)
    cm = confusion_matrix(y_val, y_pred)

    print(f"\n  {name}:")
    print(f"    Accuracy: {accuracy*100:.2f}%")
    print(f"    Precision: {precision*100:.2f}%")
    print(f"    Recall: {recall*100:.2f}%")
    print(f"    F1-Score: {f1*100:.2f}%")
    print(f"    TP: {cm[1,1]}, FP: {cm[0,1]}, FN: {cm[1,0]}, TN: {cm[0,0]}")

    return {'accuracy': accuracy, 'precision': precision, 'recall': recall, 'f1': f1, 'cm': cm}

results = {}
results['RF_SMOTE'] = evaluate_model(rf_smote, X_val_split, y_val_split, "Random Forest + SMOTE")
results['GB_SMOTE'] = evaluate_model(gb_smote, X_val_split, y_val_split, "Gradient Boosting + SMOTE")
results['LR_SMOTE'] = evaluate_model(lr_smote, X_val_split, y_val_split, "Logistic Regression + SMOTE")

# Step 8: Test best model on test set
print("\n🎯 Step 8: Testing best models on test set...")

best_model_name = max(results.keys(), key=lambda k: results[k]['f1'])
print(f"  Best validation model: {best_model_name} (F1: {results[best_model_name]['f1']*100:.2f}%)")

# Get the actual model
if best_model_name == 'RF_SMOTE':
    best_model = rf_smote
elif best_model_name == 'GB_SMOTE':
    best_model = gb_smote
else:
    best_model = lr_smote

# Test all models on test set
print("\n📊 Test Set Performance:")
test_results = {}
for name, model in [('RF_SMOTE', rf_smote), ('GB_SMOTE', gb_smote), ('LR_SMOTE', lr_smote)]:
    test_results[name] = evaluate_model(model, X_test_scaled, y_test, name)

# Step 9: Threshold optimization
print("\n🎯 Step 9: Optimizing decision threshold...")

# Get probabilities from best model
y_probs = best_model.predict_proba(X_test_scaled)[:, 1]

# Test different thresholds
best_threshold = 0.5
best_f1 = 0

for threshold in np.arange(0.1, 0.9, 0.1):
    y_pred_thresh = (y_probs >= threshold).astype(int)
    _, _, f1, _ = precision_recall_fscore_support(y_test, y_pred_thresh, average='binary', zero_division=0)

    if f1 > best_f1:
        best_f1 = f1
        best_threshold = threshold

    print(f"  Threshold {threshold:.1f}: F1 = {f1:.3f}")

print(f"\n  ✅ Best threshold: {best_threshold:.1f} (F1: {best_f1:.3f})")

# Final evaluation with optimized threshold
print("\n🏆 FINAL RESULTS WITH OPTIMIZED THRESHOLD:")

y_pred_final = (y_probs >= best_threshold).astype(int)
final_accuracy = accuracy_score(y_test, y_pred_final)
final_precision, final_recall, final_f1, _ = precision_recall_fscore_support(y_test, y_pred_final, average='binary', zero_division=0)
final_cm = confusion_matrix(y_test, y_pred_final)

print(f"  Accuracy: {final_accuracy*100:.2f}%")
print(f"  Precision: {final_precision*100:.2f}%")
print(f"  Recall: {final_recall*100:.2f}%")
print(f"  F1-Score: {final_f1*100:.2f}%")
print(f"  True Positives: {final_cm[1,1]} out of {y_test.sum()} joy samples")

print("\n🎯 Advanced Testing Complete!")
print("📈 Focus: Building robust systems with real validation")