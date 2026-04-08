#!/usr/bin/env python3
"""
Simple Real Data Training Script
Trains cognitive architectures on real comedy transcript data
"""

import json
import torch
import torch.nn as nn
from pathlib import Path
import sys
import os

# Add project to path
project_dir = Path("~/autonomous_laughter_prediction").expanduser()
sys.path.insert(0, str(project_dir))
os.chdir(str(project_dir))

# Import the core cognitive architecture components
exec(open(project_dir / 'core' / 'tom' / 'theory_of_mind.py').read())
exec(open(project_dir / 'core' / 'gcacu' / 'gcacu.py').read())

class SimpleRealTrainer:
    def __init__(self):
        self.data_dir = project_dir / "data" / "raw"
        self.training_data_file = self.data_dir / "real_training_dataset.json"

        # Load training data
        with open(self.training_data_file, 'r') as f:
            self.training_data = json.load(f)

        print("🎯 SIMPLE REAL TRAINER")
        print(f"📊 Training samples: {len(self.training_data)}")

    def create_training_samples(self):
        """Create training samples from real transcript data"""
        print("📋 Creating training samples...")

        training_samples = []

        for transcript_data in self.training_data:
            # Read transcript file
            transcript_file = self.data_dir / f"{transcript_data['source']}_1.txt"
            if not transcript_file.exists():
                continue

            with open(transcript_file, 'r') as f:
                transcript_text = f.read()

            # Create simple embedding from text
            words = transcript_text.lower().split()
            feature_dim = 128
            text_embedding = torch.zeros(feature_dim)

            for i, word in enumerate(words[:feature_dim]):
                hash_val = hash(word) % feature_dim
                text_embedding[hash_val] += 1.0

            # Normalize
            text_embedding = text_embedding / (text_embedding.norm() + 1e-8)

            # Create label
            laughter_count = transcript_data['total_laughter_count']
            laughter_label = min(laughter_count / 10.0, 1.0)

            sample = {
                'embedding': text_embedding,
                'laughter_probability': laughter_label,
                'title': transcript_data['title']
            }

            training_samples.append(sample)
            print(f"✅ {transcript_data['title']}: {laughter_label:.2f} laughter prob")

        return training_samples

    def train_on_real_data(self, training_samples):
        """Train both components on real data"""
        print("🧠 TRAINING ON REAL COMEDY DATA")
        print("=" * 50)

        # Initialize models
        tom_config = ToMConfig(input_dim=128, hidden_dim=64, num_belief_states=4, attention_heads=2)
        tom_model = TheoryOfMindLayer(tom_config)

        gcacu_config = GCACUConfig(input_dim=128, hidden_dim=64, num_context_patterns=8)
        gcacu_model = GCACUNetwork(gcacu_config)

        optimizers = {
            'tom': torch.optim.Adam(tom_model.parameters(), lr=0.001),
            'gcacu': torch.optim.Adam(gcacu_model.parameters(), lr=0.001)
        }

        print("🚀 Starting real data training...")

        # Training loop
        for epoch in range(15):
            total_loss = 0.0

            for sample in training_samples:
                embedding = sample['embedding'].unsqueeze(0)
                attention_mask = torch.ones(1, 128)
                target = sample['laughter_probability']

                # Train ToM
                tom_outputs = tom_model(embedding, attention_mask)
                tom_pred = tom_outputs['humor_prediction']
                tom_loss = nn.MSELoss()(tom_pred, torch.tensor([target]))

                optimizers['tom'].zero_grad()
                tom_loss.backward()
                optimizers['tom'].step()

                # Train GCACU
                gcacu_outputs = gcacu_model(embedding, attention_mask)
                gcacu_pred = gcacu_outputs['incongruity_score']
                gcacu_loss = nn.MSELoss()(gcacu_pred, torch.tensor([target]))

                optimizers['gcacu'].zero_grad()
                gcacu_loss.backward()
                optimizers['gcacu'].step()

                total_loss += (tom_loss.item() + gcacu_loss.item())

            avg_loss = total_loss / (2 * len(training_samples))

            if (epoch + 1) % 5 == 0:
                print(f"Epoch {epoch+1}/15 - Loss: {avg_loss:.4f}")

        print("✅ Training complete!")

        # Save models
        models_dir = project_dir / "models"
        models_dir.mkdir(parents=True, exist_ok=True)

        torch.save(tom_model.state_dict(), models_dir / "tom_real_trained.pth")
        torch.save(gcacu_model.state_dict(), models_dir / "gcacu_real_trained.pth")

        print(f"💾 Models saved to {models_dir}")

        return tom_model, gcacu_model

    def test_predictions(self, tom_model, gcacu_model, training_samples):
        """Test predictions on real data"""
        print("🔮 TESTING PREDICTIONS ON REAL DATA")
        print("=" * 50)

        tom_model.eval()
        gcacu_model.eval()

        with torch.no_grad():
            for sample in training_samples:
                embedding = sample['embedding'].unsqueeze(0)
                attention_mask = torch.ones(1, 128)

                tom_outputs = tom_model(embedding, attention_mask)
                gcacu_outputs = gcacu_model(embedding, attention_mask)

                tom_pred = tom_outputs['humor_prediction'].item()
                gcacu_pred = gcacu_outputs['incongruity_score'].item()
                ensemble_pred = 0.6 * tom_pred + 0.4 * gcacu_pred
                actual = sample['laughter_probability']

                print(f"📊 {sample['title']}:")
                print(f"   ToM: {tom_pred:.3f}, GCACU: {gcacu_pred:.3f}, Ensemble: {ensemble_pred:.3f}")
                print(f"   Actual: {actual:.3f}, Error: {abs(ensemble_pred - actual):.3f}")

def main():
    """Main function"""
    import os
    os.chdir(str(project_dir))

    trainer = SimpleRealTrainer()
    training_samples = trainer.create_training_samples()

    if len(training_samples) == 0:
        print("❌ No training samples!")
        return

    # Train on real data
    tom_model, gcacu_model = trainer.train_on_real_data(training_samples)

    # Test predictions
    trainer.test_predictions(tom_model, gcacu_model, training_samples)

    # Check disk usage
    project_size = sum(f.stat().st_size for f in project_dir.rglob('*') if f.is_file()) / (1024**3)
    print(f"\n💾 Current project size: {project_size:.2f} GB / 10.0 GB limit")

    if project_size < 10.0:
        print("✅ Within 10GB limit!")
    else:
        print("⚠️ Approaching limit!")

    print("\n🎯 REAL DATA TRAINING SUCCESSFUL!")

if __name__ == "__main__":
    import os
    main()