#!/usr/bin/env python3
"""
Production Laughter Detection API
Real-time inference service with ensemble methods, confidence scoring, and monitoring
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
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix
from sklearn.preprocessing import StandardScaler
from imblearn.over_sampling import SMOTE
import warnings
warnings.filterwarnings('ignore')

class ProductionLaughterDetector:
    """Production-ready laughter detection with ensemble methods"""

    def __init__(self):
        print("🚀 Production Laughter Detection API")
        self.models = {}
        self.vectorizer = None
        self.scaler = None
        self.performance_metrics = {}
        self.confidence_thresholds = {
            'conservative': 0.8,  # High precision
            'balanced': 0.5,      # Current optimized
            'discovery': 0.3      # High recall
        }

    def load_and_train_ensemble(self):
        """Load training data and train ensemble models"""
        print("\n🎯 TRAINING PRODUCTION ENSEMBLE...")

        # Load MELD training data
        meld_path = Path("~/datasets/MELD").expanduser()
        data_path = meld_path / "data" / "MELD"

        train_df = pd.read_csv(data_path / "train_sent_emo.csv")
        test_df = pd.read_csv(data_path / "test_sent_emo.csv")

        # Create features
        print("  🧬 Creating production features...")
        self.vectorizer = TfidfVectorizer(max_features=30, stop_words='english')
        X_train = self.vectorizer.fit_transform(train_df['Utterance']).toarray()
        X_test = self.vectorizer.transform(test_df['Utterance']).toarray()

        y_train = (train_df['Emotion'] == 'joy').astype(int)
        y_test = (test_df['Emotion'] == 'joy').astype(int)

        # Scale features
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # Split for validation
        X_tr, X_val, y_tr, y_val = train_test_split(X_train_scaled, y_train, test_size=0.2, stratify=y_train, random_state=42)

        # Apply SMOTE
        print("  ⚖️ Applying SMOTE...")
        smote = SMOTE(random_state=42, k_neighbors=3)
        X_smote, y_smote = smote.fit_resample(X_tr, y_tr)

        # Train ensemble models
        print("  🤖 Training ensemble models...")

        # Model 1: Logistic Regression (fast, interpretable)
        print("    📊 Training Logistic Regression...")
        lr = LogisticRegression(max_iter=500, random_state=42, class_weight='balanced')
        lr.fit(X_smote, y_smote)
        self.models['logistic_regression'] = lr

        # Model 2: Random Forest (robust, handles noise)
        print("    🌲 Training Random Forest...")
        rf = RandomForestClassifier(n_estimators=50, max_depth=8, random_state=42, class_weight='balanced')
        rf.fit(X_smote, y_smote)
        self.models['random_forest'] = rf

        # Model 3: Gradient Boosting (optimized performance)
        print("    📈 Training Gradient Boosting...")
        gb = GradientBoostingClassifier(n_estimators=50, max_depth=5, random_state=42)
        gb.fit(X_smote, y_smote)
        self.models['gradient_boosting'] = gb

        # Validate ensemble performance
        print("\n  📈 VALIDATING ENSEMBLE PERFORMANCE:")
        self.validate_ensemble(X_val, y_val, X_test, y_test)

        return True

    def validate_ensemble(self, X_val, y_val, X_test, y_test):
        """Validate ensemble models on validation and test sets"""
        validation_results = {}

        for model_name, model in self.models.items():
            # Test predictions
            y_pred = model.predict(X_test)
            y_pred_val = model.predict(X_val)

            # Metrics
            acc = accuracy_score(y_test, y_pred)
            prec, rec, f1, _ = precision_recall_fscore_support(y_test, y_pred, average='binary', zero_division=0)
            cm = confusion_matrix(y_test, y_pred)

            # Validation metrics
            val_acc = accuracy_score(y_val, y_pred_val)
            val_prec, val_rec, val_f1, _ = precision_recall_fscore_support(y_val, y_pred_val, average='binary', zero_division=0)

            validation_results[model_name] = {
                'test': {'accuracy': acc, 'precision': prec, 'recall': rec, 'f1': f1, 'confusion_matrix': cm.tolist()},
                'validation': {'accuracy': val_acc, 'precision': val_prec, 'recall': val_rec, 'f1': val_f1}
            }

            print(f"    {model_name:20s}: Test F1={f1*100:.1f}%, Val F1={val_f1*100:.1f}%")

        self.performance_metrics = validation_results
        return validation_results

    def predict_ensemble(self, texts, mode='balanced'):
        """Make ensemble predictions with confidence scoring"""
        """Production prediction method with ensemble and confidence scoring"""
        start_time = time.time()

        # Transform input
        if isinstance(texts, str):
            texts = [texts]

        X_input = self.vectorizer.transform(texts).toarray()
        X_input_scaled = self.scaler.transform(X_input)

        # Get predictions from all models
        ensemble_predictions = []
        ensemble_confidences = []

        for model_name, model in self.models.items():
            # Get prediction probabilities
            if hasattr(model, 'predict_proba'):
                probs = model.predict_proba(X_input_scaled)[:, 1]
                preds = (probs >= self.confidence_thresholds[mode]).astype(int)
            else:
                preds = model.predict(X_input_scaled)
                probs = preds.astype(float)  # Binary confidence

            ensemble_predictions.append(preds)
            ensemble_confidences.append(probs)

        # Average ensemble predictions
        avg_confidence = np.mean(ensemble_confidences, axis=0)
        final_predictions = (avg_confidence >= self.confidence_thresholds[mode]).astype(int)

        # Calculate prediction metadata
        prediction_time = time.time() - start_time

        results = []
        for i, text in enumerate(texts):
            result = {
                'text': text,
                'prediction': int(final_predictions[i]),
                'confidence': float(avg_confidence[i]),
                'mode': mode,
                'timestamp': datetime.now().isoformat(),
                'prediction_time_ms': prediction_time * 1000,
                'model_agreement': self.calculate_agreement([pred[i] for pred in ensemble_predictions]),
                'individual_predictions': {
                    model_name: int(pred[i]) for model_name, pred in zip(self.models.keys(), ensemble_predictions)
                }
            }
            results.append(result)

        return results

    def calculate_agreement(self, predictions):
        """Calculate model agreement percentage"""
        if len(predictions) <= 1:
            return 1.0
        agreements = sum(1 for i in range(len(predictions)-1) if predictions[i] == predictions[i+1])
        return agreements / (len(predictions) - 1)

    def batch_predict(self, texts, mode='balanced'):
        """Efficient batch prediction for large datasets"""
        return self.predict_ensemble(texts, mode)

    def get_model_info(self):
        """Get model information and performance metrics"""
        return {
            'model_type': 'Biosemotic Laughter Detection Ensemble',
            'n_models': len(self.models),
            'model_names': list(self.models.keys()),
            'features': self.vectorizer.get_feature_names_out().tolist() if hasattr(self.vectorizer, 'get_feature_names_out') else [],
            'performance_metrics': self.performance_metrics,
            'confidence_thresholds': self.confidence_thresholds,
            'last_updated': datetime.now().isoformat()
        }

    def monitor_performance(self, recent_predictions, ground_truth=None):
        """Monitor model performance and detect degradation"""
        monitoring_data = {
            'timestamp': datetime.now().isoformat(),
            'total_predictions': len(recent_predictions),
            'positive_predictions': sum(1 for p in recent_predictions if p['prediction'] == 1),
            'average_confidence': np.mean([p['confidence'] for p in recent_predictions]),
            'average_agreement': np.mean([p['model_agreement'] for p in recent_predictions]),
            'average_prediction_time_ms': np.mean([p['prediction_time_ms'] for p in recent_predictions])
        }

        if ground_truth is not None:
            # Calculate accuracy if ground truth provided
            correct = sum(1 for i, p in enumerate(recent_predictions) if p['prediction'] == ground_truth[i])
            monitoring_data['accuracy'] = correct / len(recent_predictions)

        return monitoring_data


class ProductionAPIServer:
    """Mock API server for production deployment"""

    def __init__(self, detector):
        self.detector = detector
        self.request_count = 0
        self.start_time = time.time()

    def handle_request(self, text_data, mode='balanced'):
        """Handle incoming prediction requests"""
        self.request_count += 1

        if isinstance(text_data, str):
            texts = [text_data]
        elif isinstance(text_data, list):
            texts = text_data
        else:
            texts = [str(text_data)]

        # Make predictions
        results = self.detector.predict_ensemble(texts, mode)

        # Add request metadata
        for result in results:
            result['request_id'] = f"req_{self.request_count}_{int(time.time()*1000)}"

        return {
            'status': 'success',
            'request_id': f"req_{self.request_count}",
            'predictions': results,
            'server_info': {
                'uptime_seconds': time.time() - self.start_time,
                'total_requests': self.request_count,
                'average_latency_ms': np.mean([r['prediction_time_ms'] for r in results])
            }
        }

    def get_server_status(self):
        """Get server status and health metrics"""
        uptime = time.time() - self.start_time
        return {
            'status': 'healthy',
            'uptime_seconds': uptime,
            'total_requests': self.request_count,
            'requests_per_second': self.request_count / uptime if uptime > 0 else 0,
            'model_info': self.detector.get_model_info()
        }


def test_production_system():
    """Test the production system with various scenarios"""
    print("\n" + "="*60)
    print("🚀 TESTING PRODUCTION LAUGHTER DETECTION SYSTEM")
    print("="*60)

    # Initialize detector
    detector = ProductionLaughterDetector()

    # Train ensemble
    print("\n🎯 PHASE 1: ENSEMBLE TRAINING")
    detector.load_and_train_ensemble()

    # Test individual prediction
    print("\n🎯 PHASE 2: SINGLE PREDICTION TEST")
    test_texts = [
        "This is hilarious! I can't stop laughing 😂",
        "I need help with my homework",
        "This meme has me dying 💀",
        "Looking for laptop recommendations",
        "Twitter is undefeated today lol"
    ]

    print("  📝 Testing individual predictions:")
    for text in test_texts:
        result = detector.predict_ensemble(text, mode='balanced')
        print(f"    Text: '{text[:50]}...'")
        print(f"    Prediction: {'😂 HUMOR' if result[0]['prediction'] == 1 else '😐 SERIOUS'}")
        print(f"    Confidence: {result[0]['confidence']:.3f}")
        print(f"    Agreement: {result[0]['model_agreement']*100:.0f}%")

    # Test batch prediction
    print("\n🎯 PHASE 3: BATCH PREDICTION TEST")
    batch_results = detector.batch_predict(test_texts, mode='discovery')
    print(f"  ✅ Batch processed: {len(batch_results)} predictions")
    print(f"  😂 Humor detected: {sum(1 for r in batch_results if r['prediction'] == 1)}")
    print(f"  😐 Serious: {sum(1 for r in batch_results if r['prediction'] == 0)}")

    # Test different modes
    print("\n🎯 PHASE 4: MODE COMPARISON TEST")
    humor_text = "This is so funny I'm crying 😂"

    for mode in ['conservative', 'balanced', 'discovery']:
        result = detector.predict_ensemble(humor_text, mode=mode)
        prediction = '😂 HUMOR' if result[0]['prediction'] == 1 else '😐 SERIOUS'
        print(f"  {mode:12s}: {prediction} (confidence: {result[0]['confidence']:.3f})")

    # Test API server
    print("\n🎯 PHASE 5: API SERVER SIMULATION")
    api_server = ProductionAPIServer(detector)

    # Simulate requests
    print("  📡 Simulating API requests:")
    for i, text in enumerate(test_texts[:3], 1):
        response = api_server.handle_request(text, mode='balanced')
        print(f"    Request {i}: {response['predictions'][0]['prediction']} ({response['predictions'][0]['prediction_time_ms']:.1f}ms)")

    # Get server status
    status = api_server.get_server_status()
    print(f"\n  📊 Server Status:")
    print(f"    Uptime: {status['uptime_seconds']:.1f}s")
    print(f"    Requests: {status['total_requests']}")
    print(f"    Rate: {status['requests_per_second']:.2f} req/s")

    # Performance monitoring
    print("\n🎯 PHASE 6: PERFORMANCE MONITORING")
    monitoring_data = detector.monitor_performance(batch_results)
    print(f"  📈 Performance Metrics:")
    print(f"    Total predictions: {monitoring_data['total_predictions']}")
    print(f"    Positive rate: {monitoring_data['positive_predictions']}/{monitoring_data['total_predictions']}")
    print(f"    Avg confidence: {monitoring_data['average_confidence']:.3f}")
    print(f"    Model agreement: {monitoring_data['average_agreement']*100:.1f}%")
    print(f"    Avg latency: {monitoring_data['average_prediction_time_ms']:.1f}ms")

    # Save production artifacts
    print("\n💾 SAVING PRODUCTION ARTIFACTS...")
    production_dir = Path("/Users/Subho/autonomous_laughter_prediction/production_deployment")
    production_dir.mkdir(exist_ok=True)

    # Save model metadata
    model_info = detector.get_model_info()
    with open(production_dir / "model_metadata.json", 'w') as f:
        json.dump(model_info, f, indent=2, default=float)

    # Save test results
    test_results = {
        'test_timestamp': datetime.now().isoformat(),
        'ensemble_results': batch_results,
        'performance_monitoring': monitoring_data,
        'server_status': status
    }

    with open(production_dir / "production_test_results.json", 'w') as f:
        json.dump(test_results, f, indent=2, default=float)

    print(f"  ✅ Production artifacts saved to: {production_dir}")

    return detector, api_server


def main():
    """Main production deployment"""
    print("🚀 PRODUCTION LAUGHTER DETECTION SYSTEM")
    print("=" * 60)

    detector, api_server = test_production_system()

    print("\n🎯 PRODUCTION SYSTEM READY!")
    print("📈 Capabilities:")
    print("  ✅ Ensemble prediction (3 models)")
    print("  ✅ Confidence scoring")
    print("  ✅ Multiple prediction modes")
    print("  ✅ Real-time inference")
    print("  ✅ Performance monitoring")
    print("  ✅ Batch processing")
    print("  ✅ API server simulation")

    print("\n🌟 PRODUCTION DEPLOYMENT READY!")

if __name__ == "__main__":
    main()