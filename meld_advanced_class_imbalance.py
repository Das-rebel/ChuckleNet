#!/usr/bin/env python3
"""
Advanced Class Imbalance Techniques for MELD Laughter Detection
Focus on building robust models with SMOTE, ensembles, and threshold optimization
"""

import pandas as pd
import numpy as np
import re
import json
from pathlib import Path
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier, BaggingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, classification_report, confusion_matrix
from sklearn.preprocessing import StandardScaler
from sklearn.utils.class_weight import compute_class_weight
from imblearn.over_sampling import SMOTE, ADASYN
from imblearn.ensemble import BalancedRandomForestClassifier, EasyEnsembleClassifier
import joblib
import warnings
warnings.filterwarnings('ignore')

class AdvancedMELDLaughterDetector:
    """Advanced laughter detection with multiple imbalance handling techniques"""

    def __init__(self, meld_path):
        self.meld_path = Path(meld_path).expanduser()
        self.data_path = self.meld_path / "data" / "MELD"
        self.models = {}
        self.results = {}

        print(f"🎯 Advanced MELD Laughter Detector Initialized")

    def load_data(self):
        """Load and prepare MELD dataset"""
        print("\n📊 Loading MELD Dataset...")

        train_df = pd.read_csv(self.data_path / "train_sent_emo.csv")
        dev_df = pd.read_csv(self.data_path / "dev_sent_emo.csv")
        test_df = pd.read_csv(self.data_path / "test_sent_emo.csv")

        # Combine train and dev
        self.train_df = pd.concat([train_df, dev_df], ignore_index=True)
        self.test_df = test_df

        print(f"  ✅ Training: {len(self.train_df)} samples")
        print(f"  ✅ Test: {len(self.test_df)} samples")

        return True

    def create_advanced_features(self, df):
        """Create comprehensive biosemotic features"""
        print("🧬 Creating Advanced Biosemotic Features...")

        features = pd.DataFrame()

        # Text-based features
        features['text_length'] = df['Utterance'].str.len()
        features['word_count'] = df['Utterance'].str.split().str.len()
        features['avg_word_len'] = df['Utterance'].apply(lambda x: np.mean([len(w) for w in x.split()]) if x.split() else 0)

        # Punctuation patterns
        features['exclamations'] = df['Utterance'].str.count('!')
        features['questions'] = df['Utterance'].str.count('\\?')
        features['dots'] = df['Utterance'].str.count('\\.')

        # Laughter indicators
        laughter_words = ['haha', 'hahaha', 'lol', 'lmao', 'hee', 'chuckle', 'giggle']
        features['laughter_count'] = df['Utterance'].str.lower().apply(lambda x: sum(1 for w in laughter_words if w in x))

        # Positive sentiment
        positive_words = ['great', 'good', 'love', 'happy', 'awesome', 'fantastic', 'amazing', 'wonderful']
        features['positive_count'] = df['Utterance'].str.lower().apply(lambda x: sum(1 for w in positive_words if w in x.split()))

        # Contextual features
        speaker_freq = df['Speaker'].value_counts().to_dict()
        features['speaker_freq'] = df['Speaker'].map(speaker_freq)

        # TF-IDF features
        if not hasattr(self, 'tfidf_vectorizer'):
            self.tfidf_vectorizer = TfidfVectorizer(max_features=50, stop_words='english')
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(df['Utterance'])
        else:
            tfidf_matrix = self.tfidf_vectorizer.transform(df['Utterance'])

        tfidf_df = pd.DataFrame(tfidf_matrix.toarray(), columns=[f'tfidf_{i}' for i in range(tfidf_matrix.shape[1])])
        features = pd.concat([features.reset_index(drop=True), tfidf_df], axis=1)

        return features

    def prepare_labels(self, df):
        """Create binary labels (joy=1, other=0)"""
        return (df['Emotion'] == 'joy').astype(int)

    def apply_smote(self, X_train, y_train):
        """Apply SMOTE oversampling"""
        print("  ⚖️ Applying SMOTE oversampling...")

        smote = SMOTE(random_state=42, k_neighbors=5)
        X_resampled, y_resampled = smote.fit_resample(X_train, y_train)

        print(f"    Before: {X_train.shape} samples (Joy: {y_train.sum()})")
        print(f"    After: {X_resampled.shape} samples (Joy: {y_resampled.sum()})")

        return X_resampled, y_resampled

    def apply_adasyn(self, X_train, y_train):
        """Apply ADASYN oversampling"""
        print("  ⚖️ Applying ADASYN oversampling...")

        adasyn = ADASYN(random_state=42, n_neighbors=5)
        X_resampled, y_resampled = adasyn.fit_resample(X_train, y_train)

        print(f"    Before: {X_train.shape} samples (Joy: {y_train.sum()})")
        print(f"    After: {X_resampled.shape} samples (Joy: {y_resampled.sum()})")

        return X_resampled, y_resampled

    def train_balanced_random_forest(self, X_train, y_train):
        """Train Balanced Random Forest"""
        print("🌲 Training Balanced Random Forest...")

        brf = BalancedRandomForestClassifier(
            n_estimators=200,
            max_depth=15,
            min_samples_split=5,
            random_state=42,
            sampling_strategy='auto'
        )

        brf.fit(X_train, y_train)
        return brf

    def train_easy_ensemble(self, X_train, y_train):
        """Train Easy Ensemble Classifier"""
        print("🎯 Training Easy Ensemble Classifier...")

        ee = EasyEnsembleClassifier(
            n_estimators=10,
            random_state=42,
            sampling_strategy='auto'
        )

        ee.fit(X_train, y_train)
        return ee

    def train_voting_ensemble(self, X_train, y_train):
        """Train Voting Ensemble with multiple algorithms"""
        print("🗳️ Training Voting Ensemble...")

        # Create individual models
        rf = RandomForestClassifier(n_estimators=100, max_depth=10, class_weight='balanced', random_state=42)
        gb = GradientBoostingClassifier(n_estimators=100, max_depth=5, random_state=42)
        lr = LogisticRegression(max_iter=1000, class_weight='balanced', random_state=42)

        # Create voting ensemble
        voting_clf = VotingClassifier(
            estimators=[('rf', rf), ('gb', gb), ('lr', lr)],
            voting='soft'
        )

        voting_clf.fit(X_train, y_train)
        return voting_clf

    def optimize_threshold(self, model, X_val, y_val):
        """Optimize decision threshold for better precision-recall balance"""
        print("🎯 Optimizing decision threshold...")

        # Get prediction probabilities
        if hasattr(model, 'predict_proba'):
            y_probs = model.predict_proba(X_val)[:, 1]
        else:
            # For models without predict_proba, use decision function
            y_probs = model.decision_function(X_val)
            y_probs = (y_probs - y_probs.min()) / (y_probs.max() - y_probs.min())

        # Test different thresholds
        best_threshold = 0.5
        best_f1 = 0

        for threshold in np.arange(0.1, 0.9, 0.05):
            y_pred = (y_probs >= threshold).astype(int)
            _, _, f1, _ = precision_recall_fscore_support(y_val, y_pred, average='binary', zero_division=0)

            if f1 > best_f1:
                best_f1 = f1
                best_threshold = threshold

        print(f"  ✅ Best threshold: {best_threshold:.2f} (F1: {best_f1:.3f})")
        return best_threshold

    def evaluate_model(self, model, X_test, y_test, threshold=0.5):
        """Evaluate model with optimized threshold"""
        print("\n📈 Evaluating Model Performance...")

        # Get predictions
        if hasattr(model, 'predict_proba'):
            y_probs = model.predict_proba(X_test)[:, 1]
            y_pred = (y_probs >= threshold).astype(int)
        else:
            y_pred = model.predict(X_test)

        # Calculate metrics
        accuracy = accuracy_score(y_test, y_pred)
        precision, recall, f1, _ = precision_recall_fscore_support(y_test, y_pred, average='binary', zero_division=0)

        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred)

        print(f"  ✅ Accuracy: {accuracy*100:.2f}%")
        print(f"  🎯 Precision: {precision*100:.2f}%")
        print(f"  🔄 Recall: {recall*100:.2f}%")
        print(f"  📊 F1-Score: {f1*100:.2f}%")
        print(f"  📊 TP: {cm[1,1]}, FP: {cm[0,1]}, FN: {cm[1,0]}, TN: {cm[0,0]}")

        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'confusion_matrix': cm.tolist(),
            'threshold': threshold
        }

    def run_comprehensive_tests(self):
        """Run comprehensive testing with multiple techniques"""
        print("\n" + "="*60)
        print("🚀 COMPREHENSIVE MELD LAUGHTER DETECTION TESTING")
        print("="*60)

        # Load data
        self.load_data()

        # Prepare features and labels
        print("\n🧬 Preparing Features...")
        X_train = self.create_advanced_features(self.train_df)
        y_train = self.prepare_labels(self.train_df)
        X_test = self.create_advanced_features(self.test_df)
        y_test = self.prepare_labels(self.test_df)

        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        # Split training data for validation
        X_train_split, X_val_split, y_train_split, y_val_split = train_test_split(
            X_train_scaled, y_train, test_size=0.2, stratify=y_train, random_state=42
        )

        print(f"\n📊 Dataset Info:")
        print(f"  Training: {X_train_scaled.shape[0]} samples (Joy: {y_train.sum()}, {y_train.mean()*100:.1f}%)")
        print(f"  Test: {X_test_scaled.shape[0]} samples (Joy: {y_test.sum()}, {y_test.mean()*100:.1f}%)")

        results_summary = {}

        # Technique 1: SMOTE + Random Forest
        print("\n" + "="*60)
        print("🎯 TECHNIQUE 1: SMOTE + Random Forest")
        print("="*60)

        X_smote, y_smote = self.apply_smote(X_train_split, y_train_split)
        rf_smote = RandomForestClassifier(n_estimators=200, max_depth=15, random_state=42)
        rf_smote.fit(X_smote, y_smote)

        threshold = self.optimize_threshold(rf_smote, X_val_split, y_val_split)
        results = self.evaluate_model(rf_smote, X_test_scaled, y_test, threshold)
        results_summary['SMOTE_RandomForest'] = results

        # Technique 2: ADASYN + Gradient Boosting
        print("\n" + "="*60)
        print("🎯 TECHNIQUE 2: ADASYN + Gradient Boosting")
        print("="*60)

        X_adasyn, y_adasyn = self.apply_adasyn(X_train_split, y_train_split)
        gb_adasyn = GradientBoostingClassifier(n_estimators=200, max_depth=7, random_state=42)
        gb_adasyn.fit(X_adasyn, y_adasyn)

        threshold = self.optimize_threshold(gb_adasyn, X_val_split, y_val_split)
        results = self.evaluate_model(gb_adasyn, X_test_scaled, y_test, threshold)
        results_summary['ADASYN_GradientBoosting'] = results

        # Technique 3: Balanced Random Forest
        print("\n" + "="*60)
        print("🎯 TECHNIQUE 3: Balanced Random Forest")
        print("="*60)

        brf = self.train_balanced_random_forest(X_train_scaled, y_train)
        threshold = self.optimize_threshold(brf, X_val_split, y_val_split)
        results = self.evaluate_model(brf, X_test_scaled, y_test, threshold)
        results_summary['BalancedRandomForest'] = results

        # Technique 4: Easy Ensemble
        print("\n" + "="*60)
        print("🎯 TECHNIQUE 4: Easy Ensemble Classifier")
        print("="*60)

        ee = self.train_easy_ensemble(X_train_scaled, y_train)
        threshold = self.optimize_threshold(ee, X_val_split, y_val_split)
        results = self.evaluate_model(ee, X_test_scaled, y_test, threshold)
        results_summary['EasyEnsemble'] = results

        # Technique 5: Voting Ensemble
        print("\n" + "="*60)
        print("🎯 TECHNIQUE 5: Voting Ensemble")
        print("="*60)

        voting = self.train_voting_ensemble(X_train_scaled, y_train)
        threshold = self.optimize_threshold(voting, X_val_split, y_val_split)
        results = self.evaluate_model(voting, X_test_scaled, y_test, threshold)
        results_summary['VotingEnsemble'] = results

        # Print summary
        print("\n" + "="*60)
        print("📊 FINAL RESULTS COMPARISON")
        print("="*60)

        for technique, results in results_summary.items():
            print(f"\n🎯 {technique}:")
            print(f"  Accuracy: {results['accuracy']*100:.2f}%")
            print(f"  Precision: {results['precision']*100:.2f}%")
            print(f"  Recall: {results['recall']*100:.2f}%")
            print(f"  F1-Score: {results['f1']*100:.2f}%")
            print(f"  True Positives: {results['confusion_matrix'][1][1]}")

        # Find best technique
        best_technique = max(results_summary.items(), key=lambda x: x[1]['f1'])
        print(f"\n🏆 BEST TECHNIQUE: {best_technique[0]}")
        print(f"   F1-Score: {best_technique[1]['f1']*100:.2f}%")
        print(f"   True Positives: {best_technique[1]['confusion_matrix'][1][1]}")

        # Save results
        self.save_results(results_summary)

        return results_summary

    def save_results(self, results):
        """Save experimental results"""
        output_dir = Path("/Users/Subho/autonomous_laughter_prediction/meld_advanced_results")
        output_dir.mkdir(exist_ok=True)

        results_file = output_dir / "advanced_imbalance_results.json"
        with open(results_file, 'w') as f:
            # Convert numpy types to Python types for JSON serialization
            results_serializable = {}
            for technique, metrics in results.items():
                results_serializable[technique] = {
                    k: v.tolist() if isinstance(v, np.ndarray) else float(v) if isinstance(v, (np.floating, np.integer)) else v
                    for k, v in metrics.items()
                }

            json.dump(results_serializable, f, indent=2)

        print(f"\n💾 Results saved to: {results_file}")

def main():
    """Main execution"""
    detector = AdvancedMELDLaughterDetector("~/datasets/MELD")
    results = detector.run_comprehensive_tests()

    print("\n🎯 Advanced Class Imbalance Testing Complete!")
    print("📈 Focus: Building robust laughter detection systems")
    print("🌟 Goal: Real-world deployment capabilities")

if __name__ == "__main__":
    main()