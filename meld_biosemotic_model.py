#!/usr/bin/env python3
"""
MELD Biosemotic Laughter Detection Model
Complete training and testing pipeline for MELD dataset validation
"""

import pandas as pd
import numpy as np
import re
import json
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, classification_report, confusion_matrix
from sklearn.preprocessing import StandardScaler
import joblib
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class MELDBiosemoticModel:
    """Biosemotic laughter detection model for MELD dataset"""

    def __init__(self, meld_path):
        self.meld_path = Path(meld_path)
        self.data_path = self.meld_path / "data" / "MELD"
        self.model = None
        self.vectorizer = None
        self.scaler = None
        self.feature_names = []

        print(f"🎯 MELD Biosemotic Model Initialized")
        print(f"📁 Data Path: {self.data_path}")

    def load_data(self):
        """Load MELD dataset"""
        print("\n📊 Loading MELD Dataset...")

        self.train_df = pd.read_csv(self.data_path / "train_sent_emo.csv")
        self.dev_df = pd.read_csv(self.data_path / "dev_sent_emo.csv")
        self.test_df = pd.read_csv(self.data_path / "test_sent_emo.csv")

        # Combine train and dev for training
        self.train_combined = pd.concat([self.train_df, self.dev_df], ignore_index=True)

        print(f"  ✅ Training Combined: {len(self.train_combined)} samples")
        print(f"  ✅ Test: {len(self.test_df)} samples")

        return True

    def create_biosemotic_features(self, df):
        """Create biosemotic features from MELD data"""
        print("\n🧬 Creating Biosemotic Features...")

        features = pd.DataFrame()

        # 1. LINGUISTIC FEATURES
        print("  📝 Creating linguistic features...")

        # Dialogue length features
        features['dialogue_length'] = df['Utterance'].str.len()
        features['word_count'] = df['Utterance'].str.split().str.len()
        features['avg_word_length'] = df['Utterance'].apply(lambda x: np.mean([len(word) for word in x.split()]) if x.split() else 0)

        # Punctuation features
        features['exclamation_count'] = df['Utterance'].str.count('!')
        features['question_count'] = df['Utterance'].str.count('\\?')
        features['ellipsis_count'] = df['Utterance'].str.count('\\.\\.\\.')

        # Laughter pattern features
        laughter_patterns = ['haha', 'ha ha', 'hahaha', 'lol', 'lmao', 'hee hee', 'chuckle', 'giggle']
        features['laughter_words'] = df['Utterance'].str.lower().apply(lambda x: sum(1 for pattern in laughter_patterns if pattern in x))

        # Positive sentiment words
        positive_words = ['great', 'good', 'love', 'happy', 'excited', 'awesome', 'wonderful', 'fantastic', 'amazing']
        features['positive_words'] = df['Utterance'].str.lower().apply(lambda x: sum(1 for word in positive_words if word in x.split()))

        # 2. CONTEXTUAL FEATURES
        print("  👥 Creating contextual features...")

        # Speaker encoding (frequency-based)
        speaker_freq = df['Speaker'].value_counts().to_dict()
        features['speaker_frequency'] = df['Speaker'].map(speaker_freq)

        # Episode features
        features['season'] = df['Season']
        features['episode'] = df['Episode']

        # 3. SEMANTIC FEATURES
        print("  💭 Creating semantic features...")

        # TF-IDF vectorization for semantic content
        if self.vectorizer is None:
            self.vectorizer = TfidfVectorizer(max_features=100, stop_words='english')
            tfidf_features = self.vectorizer.fit_transform(df['Utterance'])
        else:
            tfidf_features = self.vectorizer.transform(df['Utterance'])

        tfidf_df = pd.DataFrame(tfidf_features.toarray(), columns=[f'tfidf_{i}' for i in range(tfidf_features.shape[1])])
        features = pd.concat([features.reset_index(drop=True), tfidf_df], axis=1)

        # 4. PRAGMATIC FEATURES
        print("  🎯 Creating pragmatic features...")

        # Emotion distribution in dataset
        emotion_freq = df['Emotion'].value_counts().to_dict()
        features['emotion_frequency'] = df['Emotion'].map(emotion_freq)

        # Sentiment encoding
        sentiment_map = {'positive': 1, 'neutral': 0, 'negative': -1}
        features['sentiment_encoding'] = df['Sentiment'].map(sentiment_map).fillna(0)

        self.feature_names = features.columns.tolist()

        print(f"  ✅ Total Features: {len(self.feature_names)}")

        return features

    def prepare_labels(self, df):
        """Prepare binary laughter detection labels (joy vs non-joy)"""
        return (df['Emotion'] == 'joy').astype(int)

    def train_model(self, model_type='random_forest'):
        """Train biosemotic model on MELD data"""
        print(f"\n🚀 Training Biosemotic Model ({model_type})...")

        # Prepare features and labels
        X_train = self.create_biosemotic_features(self.train_combined)
        y_train = self.prepare_labels(self.train_combined)

        print(f"  📊 Training Data: {X_train.shape[0]} samples, {X_train.shape[1]} features")
        print(f"  😊 Joy Samples: {y_train.sum()} ({y_train.mean()*100:.1f}%)")

        # Scale features
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)

        # Initialize model
        if model_type == 'random_forest':
            self.model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
        elif model_type == 'gradient_boosting':
            self.model = GradientBoostingClassifier(n_estimators=100, max_depth=5, random_state=42)
        elif model_type == 'logistic_regression':
            self.model = LogisticRegression(max_iter=1000, random_state=42)
        else:
            raise ValueError(f"Unknown model type: {model_type}")

        # Train model
        print(f"  ⚡ Training {model_type.replace('_', ' ').title()}...")
        self.model.fit(X_train_scaled, y_train)

        # Training performance
        train_pred = self.model.predict(X_train_scaled)
        train_acc = accuracy_score(y_train, train_pred)

        print(f"  ✅ Training Accuracy: {train_acc*100:.2f}%")

        return train_acc

    def evaluate_model(self, dataset_name='test'):
        """Evaluate model on test data"""
        print(f"\n📈 Evaluating Model on {dataset_name.capitalize()} Set...")

        # Select dataset
        if dataset_name == 'test':
            df = self.test_df
        elif dataset_name == 'dev':
            df = self.dev_df
        else:
            raise ValueError(f"Unknown dataset: {dataset_name}")

        # Prepare features and labels
        X_test = self.create_biosemotic_features(df)
        y_test = self.prepare_labels(df)

        print(f"  📊 Test Data: {X_test.shape[0]} samples, {X_test.shape[1]} features")
        print(f"  😊 Joy Samples: {y_test.sum()} ({y_test.mean()*100:.1f}%)")

        # Scale features
        X_test_scaled = self.scaler.transform(X_test)

        # Predict
        y_pred = self.model.predict(X_test_scaled)
        y_pred_proba = self.model.predict_proba(X_test_scaled)[:, 1]

        # Calculate metrics
        accuracy = accuracy_score(y_test, y_pred)
        precision, recall, f1, _ = precision_recall_fscore_support(y_test, y_pred, average='binary')

        print(f"  ✅ Test Accuracy: {accuracy*100:.2f}%")
        print(f"  🎯 Precision: {precision*100:.2f}%")
        print(f"  🔄 Recall: {recall*100:.2f}%")
        print(f"  📊 F1-Score: {f1*100:.2f}%")

        # Detailed classification report
        print(f"\n  📋 Detailed Classification Report:")
        print(classification_report(y_test, y_pred, target_names=['Non-Joy', 'Joy']))

        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        print(f"  📊 Confusion Matrix:")
        print(f"    True Negatives: {cm[0,0]}, False Positives: {cm[0,1]}")
        print(f"    False Negatives: {cm[1,0]}, True Positives: {cm[1,1]}")

        results = {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'confusion_matrix': cm.tolist(),
            'predictions': y_pred.tolist(),
            'probabilities': y_pred_proba.tolist()
        }

        return results

    def run_ablation_study(self):
        """Run ablation study to understand feature contributions"""
        print("\n🔬 Running Ablation Study...")

        # Prepare data
        X_train = self.create_biosemotic_features(self.train_combined)
        y_train = self.prepare_labels(self.train_combined)
        X_test = self.create_biosemotic_features(self.test_df)
        y_test = self.prepare_labels(self.test_df)

        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # Feature group analysis
        feature_groups = {
            'linguistic': [col for col in self.feature_names if any(word in col for word in ['dialogue_length', 'word_count', 'avg_word_length', 'exclamation', 'question', 'ellipsis', 'laughter', 'positive'])],
            'contextual': [col for col in self.feature_names if any(word in col for word in ['speaker_frequency', 'season', 'episode'])],
            'tfidf': [col for col in self.feature_names if 'tfidf' in col],
            'pragmatic': [col for col in self.feature_names if any(word in col for word in ['emotion_frequency', 'sentiment_encoding'])]
        }

        ablation_results = {}

        for group_name, features in feature_groups.items():
            if not features:
                continue

            print(f"\n  🎯 Testing {group_name.upper()} Features Only...")

            # Get feature indices
            feature_indices = [self.feature_names.index(f) for f in features]

            # Train and evaluate with only this feature group
            model_subset = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
            model_subset.fit(X_train_scaled[:, feature_indices], y_train)
            y_pred = model_subset.predict(X_test_scaled[:, feature_indices])
            accuracy = accuracy_score(y_test, y_pred)

            ablation_results[group_name] = {
                'features': len(features),
                'accuracy': accuracy
            }

            print(f"    ✅ {group_name.capitalize()} Only: {accuracy*100:.2f}%")

        return ablation_results

    def save_model(self, output_dir):
        """Save trained model and components"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        print(f"\n💾 Saving Model to: {output_path}")

        # Save model
        model_file = output_path / "biosemotic_model.joblib"
        joblib.dump(self.model, model_file)
        print(f"  ✅ Saved: {model_file}")

        # Save vectorizer
        vectorizer_file = output_path / "vectorizer.joblib"
        joblib.dump(self.vectorizer, vectorizer_file)
        print(f"  ✅ Saved: {vectorizer_file}")

        # Save scaler
        scaler_file = output_path / "scaler.joblib"
        joblib.dump(self.scaler, scaler_file)
        print(f"  ✅ Saved: {scaler_file}")

        return True

def main():
    """Main execution function"""
    print("🎯 MELD Biosemotic Model Training and Testing")
    print("=" * 60)

    # Initialize model
    meld_path = "~/datasets/MELD"
    model = MELDBiosemoticModel(meld_path)

    # Load data
    model.load_data()

    # Test multiple model types
    model_types = ['random_forest', 'gradient_boosting', 'logistic_regression']
    results_summary = {}

    for model_type in model_types:
        print(f"\n{'='*60}")
        print(f"🚀 TESTING: {model_type.upper().replace('_', ' ')}")
        print('='*60)

        # Create new model instance for each type
        model = MELDBiosemoticModel(meld_path)
        model.load_data()

        # Train model
        train_acc = model.train_model(model_type)

        # Evaluate on test set
        test_results = model.evaluate_model('test')
        results_summary[model_type] = {
            'train_accuracy': train_acc,
            'test_accuracy': test_results['accuracy'],
            'precision': test_results['precision'],
            'recall': test_results['recall'],
            'f1': test_results['f1']
        }

        # Run ablation study for best model
        if model_type == 'random_forest':
            ablation_results = model.run_ablation_study()

        # Save model
        output_dir = f"/Users/Subho/autonomous_laughter_prediction/meld_models/{model_type}"
        model.save_model(output_dir)

    # Print summary
    print(f"\n{'='*60}")
    print("📊 FINAL RESULTS SUMMARY")
    print('='*60)

    for model_type, results in results_summary.items():
        print(f"\n  {model_type.upper().replace('_', ' ')}:")
        print(f"    Train Accuracy: {results['train_accuracy']*100:.2f}%")
        print(f"    Test Accuracy: {results['test_accuracy']*100:.2f}%")
        print(f"    Precision: {results['precision']*100:.2f}%")
        print(f"    Recall: {results['recall']*100:.2f}%")
        print(f"    F1-Score: {results['f1']*100:.2f}%")

    print(f"\n🎯 MELD Validation Complete!")
    print(f"📅 Timeline: Ready for AAAI 2027 paper with real experimental results")
    print(f"🏆 Goal: 3 publications (ACL/EMNLP + COLING + AAAI)")

if __name__ == "__main__":
    main()