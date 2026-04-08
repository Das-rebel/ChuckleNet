#!/usr/bin/env python3
"""
Fast Advanced Ensemble - Focused on Performance
Quick training with proven ensemble techniques
"""

import pandas as pd
import numpy as np
import json
import time
from datetime import datetime
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix
from sklearn.preprocessing import StandardScaler
from imblearn.over_sampling import SMOTE
import warnings
warnings.filterwarnings('ignore')

print("⚡ FAST ADVANCED ENSEMBLE")
print("=" * 40)

class FastAdvancedEnsemble:
    """Fast but advanced ensemble methods"""

    def __init__(self):
        print("🚀 Fast Advanced Ensemble")
        self.ensemble = None
        self.feature_extractors = {}
        self.optimized_thresholds = {}
        self.performance_log = []

    def train_advanced_ensemble(self):
        """Train advanced ensemble quickly"""
        print("\n🎯 TRAINING ADVANCED ENSEMBLE...")

        # Load MELD
        meld_path = Path("~/datasets/MELD").expanduser()
        data_path = meld_path / "data" / "MELD"

        train_df = pd.read_csv(data_path / "train_sent_emo.csv")
        test_df = pd.read_csv(data_path / "test_sent_emo.csv")

        # Enhanced features
        print("  🧠 Creating enhanced features...")
        self.tfidf = TfidfVectorizer(max_features=25, stop_words='english')
        X_train = self.tfidf.fit_transform(train_df['Utterance']).toarray()
        X_test = self.tfidf.transform(test_df['Utterance']).toarray()

        y_train = (train_df['Emotion'] == 'joy').astype(int)
        y_test = (test_df['Emotion'] == 'joy').astype(int)

        # Add text length feature
        train_lengths = train_df['Utterance'].str.len().values.reshape(-1, 1)
        test_lengths = test_df['Utterance'].str.len().values.reshape(-1, 1)

        # Add exclamation count
        train_excl = train_df['Utterance'].str.count('!').values.reshape(-1, 1)
        test_excl = test_df['Utterance'].str.count('!').values.reshape(-1, 1)

        # Combine features
        X_train_enhanced = np.concatenate([X_train, train_lengths, train_excl], axis=1)
        X_test_enhanced = np.concatenate([X_test, test_lengths, test_excl], axis=1)

        # Scale
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train_enhanced)
        X_test_scaled = self.scaler.transform(X_test_enhanced)

        # Split
        X_tr, X_val, y_tr, y_val = train_test_split(X_train_scaled, y_train, test_size=0.2, stratify=y_train, random_state=42)

        # SMOTE
        print("  ⚖️ Applying SMOTE...")
        smote = SMOTE(random_state=42, k_neighbors=3)
        X_smote, y_smote = smote.fit_resample(X_tr, y_tr)
        print(f"    Training: {y_smote.sum()} joy samples")

        # Train individual models
        print("  🤖 Training ensemble models...")

        # Model 1: Logistic Regression
        print("    📊 Logistic Regression...")
        lr = LogisticRegression(max_iter=1000, random_state=42, class_weight='balanced')
        lr.fit(X_smote, y_smote)

        # Model 2: Random Forest (small)
        print("    🌲 Random Forest...")
        rf = RandomForestClassifier(n_estimators=50, max_depth=10, random_state=42, class_weight='balanced', n_jobs=1)
        rf.fit(X_smote, y_smote)

        # Model 3: Gradient Boosting (small)
        print("    📈 Gradient Boosting...")
        gb = GradientBoostingClassifier(n_estimators=50, max_depth=6, random_state=42)
        gb.fit(X_smote, y_smote)

        # Create voting ensemble
        print("    🗳️ Creating Voting Ensemble...")
        self.ensemble = VotingClassifier(
            estimators=[
                ('lr', lr),
                ('rf', rf),
                ('gb', gb)
            ],
            voting='soft'
        )

        self.ensemble.fit(X_smote, y_smote)

        # Validate individual models
        print("\n  📈 VALIDATION RESULTS:")
        for name, model in [('Logistic', lr), ('RandomForest', rf), ('GradientBoosting', gb)]:
            y_pred = model.predict(X_val)
            acc = accuracy_score(y_val, y_pred)
            prec, rec, f1, _ = precision_recall_fscore_support(y_val, y_pred, average='binary', zero_division=0)
            print(f"    {name:15s}: F1={f1*100:.1f}%, Prec={prec*100:.1f}%, Rec={rec*100:.1f}%")

        # Optimize threshold
        print("\n  🎯 OPTIMIZING ENSEMBLE THRESHOLD...")
        y_probs_val = self.ensemble.predict_proba(X_val)[:, 1]

        best_thresh = 0.5
        best_f1 = 0

        for thresh in np.arange(0.3, 0.7, 0.05):
            y_pred_t = (y_probs_val >= thresh).astype(int)
            _, _, f1, _ = precision_recall_fscore_support(y_val, y_pred_t, average='binary', zero_division=0)

            if f1 > best_f1:
                best_f1 = f1
                best_thresh = thresh

        self.optimized_thresholds['ensemble'] = best_thresh
        print(f"    Optimal threshold: {best_thresh:.2f} (F1: {best_f1:.3f})")

        return True

    def predict_ensemble(self, texts, threshold=None):
        """Ensemble prediction with optimization"""
        if threshold is None:
            threshold = self.optimized_thresholds.get('ensemble', 0.5)

        start_time = time.time()

        if isinstance(texts, str):
            texts = [texts]

        # Prepare features
        tfidf_features = self.tfidf.transform(texts).toarray()
        lengths = np.array([[len(t)] for t in texts])
        exclamations = np.array([[t.count('!')] for t in texts])

        X_input = np.concatenate([tfidf_features, lengths, exclamations], axis=1)
        X_scaled = self.scaler.transform(X_input)

        # Ensemble prediction
        y_probs = self.ensemble.predict_proba(X_scaled)[:, 1]
        y_preds = (y_probs >= threshold).astype(int)

        # Build results
        results = []
        latency = (time.time() - start_time) * 1000

        for i, text in enumerate(texts):
            results.append({
                'text': text,
                'prediction': int(y_preds[i]),
                'confidence': float(y_probs[i]),
                'threshold': threshold,
                'latency_ms': latency,
                'timestamp': datetime.now().isoformat()
            })

        return results

    def compare_with_baseline(self):
        """Compare ensemble vs baseline"""
        print("\n📊 COMPARING ENSEMBLE VS BASELINE")

        # Load MELD test data
        meld_path = Path("~/datasets/MELD").expanduser()
        data_path = meld_path / "data" / "MELD"

        test_df = pd.read_csv(data_path / "test_sent_emo.csv")
        y_test = (test_df['Emotion'] == 'joy').astype(int)

        # Prepare features
        X_test = self.tfidf.transform(test_df['Utterance']).toarray()
        test_lengths = test_df['Utterance'].str.len().values.reshape(-1, 1)
        test_excl = test_df['Utterance'].str.count('!').values.reshape(-1, 1)

        X_test_enhanced = np.concatenate([X_test, test_lengths, test_excl], axis=1)
        X_test_scaled = self.scaler.transform(X_test_enhanced)

        # Baseline (single model) - use just LR
        baseline_model = self.ensemble.estimators_[0]  # Logistic Regression
        baseline_pred = baseline_model.predict(X_test_scaled)
        baseline_acc = accuracy_score(y_test, baseline_pred)
        baseline_prec, baseline_rec, baseline_f1, _ = precision_recall_fscore_support(y_test, baseline_pred, average='binary', zero_division=0)

        # Ensemble prediction
        ensemble_probs = self.ensemble.predict_proba(X_test_scaled)[:, 1]
        ensemble_pred = (ensemble_probs >= 0.5).astype(int)
        ensemble_acc = accuracy_score(y_test, ensemble_pred)
        ensemble_prec, ensemble_rec, ensemble_f1, _ = precision_recall_fscore_support(y_test, ensemble_pred, average='binary', zero_division=0)

        # Optimized ensemble
        opt_thresh = self.optimized_thresholds['ensemble']
        opt_ensemble_pred = (ensemble_probs >= opt_thresh).astype(int)
        opt_ensemble_acc = accuracy_score(y_test, opt_ensemble_pred)
        opt_ensemble_prec, opt_ensemble_rec, opt_ensemble_f1, _ = precision_recall_fscore_support(y_test, opt_ensemble_pred, average='binary', zero_division=0)

        print(f"  📊 COMPARISON RESULTS:")
        print(f"    Baseline (LR):      Acc={baseline_acc*100:.1f}%, Prec={baseline_prec*100:.1f}%, Rec={baseline_rec*100:.1f}%, F1={baseline_f1*100:.1f}%")
        print(f"    Ensemble (0.5):     Acc={ensemble_acc*100:.1f}%, Prec={ensemble_prec*100:.1f}%, Rec={ensemble_rec*100:.1f}%, F1={ensemble_f1*100:.1f}%")
        print(f"    Ensemble ({opt_thresh:.2f}): Acc={opt_ensemble_acc*100:.1f}%, Prec={opt_ensemble_prec*100:.1f}%, Rec={opt_ensemble_rec*100:.1f}%, F1={opt_ensemble_f1*100:.1f}%")

        print(f"\n  🚀 IMPROVEMENTS:")
        print(f"    Accuracy:  {baseline_acc*100:.1f}% → {opt_ensemble_acc*100:.1f}% ({(opt_ensemble_acc-baseline_acc)*100:+.1f}%)")
        print(f"    Precision: {baseline_prec*100:.1f}% → {opt_ensemble_prec*100:.1f}% ({(opt_ensemble_prec-baseline_prec)*100:+.1f}%)")
        print(f"    Recall:    {baseline_rec*100:.1f}% → {opt_ensemble_rec*100:.1f}% ({(opt_ensemble_rec-baseline_rec)*100:+.1f}%)")
        print(f"    F1-Score:  {baseline_f1*100:.1f}% → {opt_ensemble_f1*100:.1f}% ({(opt_ensemble_f1-baseline_f1)*100:+.1f}%)")

        return {
            'baseline': {'f1': baseline_f1, 'acc': baseline_acc},
            'ensemble': {'f1': opt_ensemble_f1, 'acc': opt_ensemble_acc},
            'improvement': opt_ensemble_f1 - baseline_f1
        }


def demo_advanced_ensemble():
    """Demonstrate advanced ensemble"""
    print("\n🎯 FAST ADVANCED ENSEMBLE DEMO")

    ensemble = FastAdvancedEnsemble()
    ensemble.train_advanced_ensemble()

    # Test predictions
    print("\n📝 TESTING ENSEMBLE PREDICTIONS:")

    test_texts = [
        "This is hilarious 😂",
        "I need help with calculus",
        "LMAO so funny",
        "Looking for recommendations",
        "This tweet is weak 💀"
    ]

    results = ensemble.predict_ensemble(test_texts)

    for result in results:
        prediction = "😂 HUMOR" if result['prediction'] == 1 else "😐 SERIOUS"
        print(f"  '{result['text'][:35]}...' → {prediction} ({result['confidence']:.3f})")

    # Compare performance
    comparison = ensemble.compare_with_baseline()

    # Save results
    print("\n💾 SAVING ADVANCED ENSEMBLE RESULTS...")
    results_dir = Path("/Users/Subho/autonomous_laughter_prediction/advanced_ensemble_results")
    results_dir.mkdir(exist_ok=True)

    ensemble_data = {
        'deployment_time': datetime.now().isoformat(),
        'ensemble_type': 'voting_classifier_3_models',
        'optimized_threshold': ensemble.optimized_thresholds['ensemble'],
        'baseline_vs_ensemble': comparison,
        'test_predictions': results
    }

    with open(results_dir / "fast_ensemble_results.json", 'w') as f:
        json.dump(ensemble_data, f, indent=2, default=float)

    print(f"  ✅ Results saved to: {results_dir}")

    print("\n🎯 ADVANCED ENSEMBLE DEPLOYED!")
    print("📈 Enhanced Features:")
    print("  ✅ Voting ensemble (3 models)")
    print("  ✅ Enhanced feature engineering")
    print("  ✅ Optimized thresholds")
    print("  ✅ Performance comparison")
    print("  ✅ Baseline improvement tracking")

    return ensemble


# Deploy advanced ensemble
if __name__ == "__main__":
    advanced_ensemble = demo_advanced_ensemble()