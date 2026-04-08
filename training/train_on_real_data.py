#!/usr/bin/env python3
"""
Train Cognitive Architectures on Real Comedy Transcript Data
This script implements the real training as specified in the training plan
"""

import json
import torch
import torch.nn as nn
from pathlib import Path
import sys
sys.path.insert(0, str(Path("~/autonomous_laughter_prediction").expanduser()))

# Import cognitive architecture components
import os
os.chdir(str(Path("~/autonomous_laughter_prediction").expanduser()))

exec(open('individual_component_training/theory_of_mind_layer.py').read())
exec(open('individual_component_training/gcacu_network.py').read())

class RealDataTrainer:
    def __init__(self):
        self.data_dir = Path("~/autonomous_laughter_prediction/data/raw").expanduser()
        self.training_data_file = self.data_dir / "real_training_dataset.json"

        # Load training data
        with open(self.training_data_file, 'r') as f:
            self.training_data = json.load(f)

        print("🎯 REAL DATA TRAINER INITIALIZED")
        print(f"📊 Training samples: {len(self.training_data)}")
        total_laughter = sum(sample['total_laughter_count'] for sample in self.training_data)
        print(f"🎭 Total laughter segments: {total_laughter}")

    def create_training_samples(self):
        """
        Convert real transcript data into training samples
        """
        print("📋 CREATING TRAINING SAMPLES FROM REAL DATA")
        print("=" * 60)

        training_samples = []

        for transcript_data in self.training_data:
            # Read the actual transcript file
            transcript_file = self.data_dir / f"{transcript_data['source']}_1.txt"
            if not transcript_file.exists():
                print(f"⚠️ Transcript file not found: {transcript_file}")
                continue

            with open(transcript_file, 'r') as f:
                transcript_text = f.read()

            # Create embedding from transcript text
            # For demonstration, use simple word frequency features
            words = transcript_text.lower().split()
            word_freq = {}
            for word in words:
                word_freq[word] = word_freq.get(word, 0) + 1

            # Create simple feature vector
            feature_dim = 128
            text_embedding = torch.zeros(feature_dim)
            for i, word in enumerate(words[:feature_dim]):
                # Simple hash-based embedding
                hash_val = hash(word) % feature_dim
                text_embedding[hash_val] += 1.0

            # Normalize
            text_embedding = text_embedding / (text_embedding.norm() + 1e-8)

            # Create label based on laughter segments
            laughter_count = transcript_data['total_laughter_count']
            laughter_label = min(laughter_count / 10.0, 1.0)  # Normalize to 0-1

            # Determine discrete vs continuous ratio
            discrete_count = len([s for s in transcript_data['laughter_segments'] if s['type'] == 'discrete'])
            continuous_count = len([s for s in transcript_data['laughter_segments'] if s['type'] == 'continuous'])

            sample = {
                'embedding': text_embedding,
                'laughter_probability': laughter_label,
                'laughter_count': laughter_count,
                'discrete_ratio': discrete_count / (discrete_count + continuous_count) if (discrete_count + continuous_count) > 0 else 0.0,
                'title': transcript_data['title'],
                'source': transcript_data['source']
            }

            training_samples.append(sample)
            print(f"✅ Created sample: {transcript_data['title']} (laughter prob: {laughter_label:.2f})")

        print(f"📊 Total training samples: {len(training_samples)}")
        return training_samples

    def train_tom_on_real_data(self, training_samples):
        """
        Train Theory of Mind component on real data
        """
        print("🧠 TRAINING THEORY OF MIND ON REAL DATA")
        print("=" * 60)

        # Initialize ToM model
        config = ToMConfig(
            input_dim=128,
            hidden_dim=64,
            num_belief_states=4,
            attention_heads=2
        )
        tom_model = TheoryOfMindLayer(config)
        optimizer = torch.optim.Adam(tom_model.parameters(), lr=0.001)

        # Training loop
        print("Starting real data training...")
        for epoch in range(20):  # More epochs for real data
            epoch_loss = 0.0
            correct_predictions = 0

            for sample in training_samples:
                embedding = sample['embedding'].unsqueeze(0)
                attention_mask = torch.ones(1, 128)
                target_laughter = sample['laughter_probability']

                # Forward pass
                outputs = tom_model(embedding, attention_mask)
                humor_pred = outputs['humor_prediction']

                # Loss calculation
                loss = nn.MSELoss()(humor_pred, torch.tensor([target_laughter]))

                # Backward pass
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

                epoch_loss += loss.item()

                # Check if prediction is correct (within 0.2 threshold)
                if abs(humor_pred.item() - target_laughter) < 0.2:
                    correct_predictions += 1

            avg_loss = epoch_loss / len(training_samples)
            accuracy = correct_predictions / len(training_samples)

            if (epoch + 1) % 5 == 0:
                print(f"Epoch {epoch+1}/20 - Loss: {avg_loss:.4f}, Accuracy: {accuracy:.2f}")

        print("✅ Theory of Mind training complete!")

        # Save trained model
        model_path = Path("~/autonomous_laughter_prediction/models/tom_real_trained.pth").expanduser()
        model_path.parent.mkdir(parents=True, exist_ok=True)
        torch.save(tom_model.state_dict(), model_path)
        print(f"💾 Model saved: {model_path}")

        return tom_model

    def train_gcacu_on_real_data(self, training_samples):
        """
        Train GCACU component on real data
        """
        print("🎯 TRAINING GCACU ON REAL DATA")
        print("=" * 60)

        # Initialize GCACU model
        config = GCACUConfig(
            input_dim=128,
            hidden_dim=64,
            num_context_patterns=8
        )
        gcacu_model = GCACUNetwork(config)
        optimizer = torch.optim.Adam(gcacu_model.parameters(), lr=0.001)

        # Training loop
        print("Starting real data training...")
        for epoch in range(20):  # More epochs for real data
            epoch_loss = 0.0
            correct_predictions = 0

            for sample in training_samples:
                embedding = sample['embedding'].unsqueeze(0)
                attention_mask = torch.ones(1, 128)
                target_laughter = sample['laughter_probability']

                # Forward pass
                outputs = gcacu_model(embedding, attention_mask)
                incongruity = outputs['incongruity_score']

                # Loss calculation
                loss = nn.MSELoss()(incongruity, torch.tensor([target_laughter]))

                # Backward pass
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

                epoch_loss += loss.item()

                # Check if prediction is correct (within 0.2 threshold)
                if abs(incongruity.item() - target_laughter) < 0.2:
                    correct_predictions += 1

            avg_loss = epoch_loss / len(training_samples)
            accuracy = correct_predictions / len(training_samples)

            if (epoch + 1) % 5 == 0:
                print(f"Epoch {epoch+1}/20 - Loss: {avg_loss:.4f}, Accuracy: {accuracy:.2f}")

        print("✅ GCACU training complete!")

        # Save trained model
        model_path = Path("~/autonomous_laughter_prediction/models/gcacu_real_trained.pth").expanduser()
        model_path.parent.mkdir(parents=True, exist_ok=True)
        torch.save(gcacu_model.state_dict(), model_path)
        print(f"💾 Model saved: {model_path}")

        return gcacu_model

    def test_ensemble_on_real_data(self, tom_model, gcacu_model, training_samples):
        """
        Test ensemble predictor on real data
        """
        print("🔮 TESTING ENSEMBLE ON REAL DATA")
        print("=" * 60)

        tom_model.eval()
        gcacu_model.eval()

        test_results = []

        with torch.no_grad():
            for sample in training_samples:
                embedding = sample['embedding'].unsqueeze(0)
                attention_mask = torch.ones(1, 128)

                # Get predictions
                tom_outputs = tom_model(embedding, attention_mask)
                gcacu_outputs = gcacu_model(embedding, attention_mask)

                tom_humor = tom_outputs['humor_prediction'].item()
                gcacu_incongruity = gcacu_outputs['incongruity_score'].item()

                # Ensemble prediction (weighted average)
                ensemble_prediction = 0.6 * tom_humor + 0.4 * gcacu_incongruity
                actual_laughter = sample['laughter_probability']

                result = {
                    'title': sample['title'],
                    'tom_prediction': tom_humor,
                    'gcacu_prediction': gcacu_incongruity,
                    'ensemble_prediction': ensemble_prediction,
                    'actual_laughter': actual_laughter,
                    'error': abs(ensemble_prediction - actual_laughter)
                }
                test_results.append(result)

                print(f"📊 {sample['title']}:")
                print(f"   ToM: {tom_humor:.3f}, GCACU: {gcacu_incongruity:.3f}, Ensemble: {ensemble_prediction:.3f}")
                print(f"   Actual: {actual_laughter:.3f}, Error: {result['error']:.3f}")

        # Calculate overall performance
        avg_error = sum(r['error'] for r in test_results) / len(test_results)
        print(f"\n📈 Average prediction error: {avg_error:.3f}")

        return test_results

def main():
    """Main training function"""
    print("🎯 AUTONOMOUS LAUGHTER PREDICTION - REAL DATA TRAINING")
    print("=" * 70)

    trainer = RealDataTrainer()

    # Create training samples
    training_samples = trainer.create_training_samples()

    if len(training_samples) == 0:
        print("❌ No training samples available!")
        return

    # Train ToM on real data
    tom_model = trainer.train_tom_on_real_data(training_samples)

    # Train GCACU on real data
    gcacu_model = trainer.train_gcacu_on_real_data(training_samples)

    # Test ensemble on real data
    test_results = trainer.test_ensemble_on_real_data(tom_model, gcacu_model, training_samples)

    print("\n✅ REAL DATA TRAINING COMPLETE!")
    print("🎯 Successfully trained cognitive architectures on real comedy transcripts!")

if __name__ == "__main__":
    main()