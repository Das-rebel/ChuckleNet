#!/usr/bin/env python3
"""
Theory of Mind Component Training Script
Trains the ToM layer for improved humor prediction
"""

import torch
import torch.nn as nn
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.tom.theory_of_mind import TheoryOfMindLayer

class ToMTrainer:
    def __init__(self):
        # Model configuration
        self.embedding_dim = 256
        self.num_heads = 4
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        # Initialize model
        self.model = TheoryOfMindLayer(
            embedding_dim=self.embedding_dim,
            num_heads=self.num_heads
        ).to(self.device)

        # Training configuration
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=1e-4)
        self.criterion = nn.MSELoss()

        # Checkpoint configuration
        self.checkpoint_dir = project_root / "checkpoints" / "tom"
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        print(f"🧠 Theory of Mind Trainer Initialized")
        print(f"Device: {self.device}")
        print(f"Checkpoint Dir: {self.checkpoint_dir}")

    def create_mock_data(self, batch_size=16, seq_len=32):
        """Create mock training data for testing"""
        embeddings = torch.randn(batch_size, seq_len, self.embedding_dim).to(self.device)
        attention_mask = torch.ones(batch_size, seq_len).to(self.device)
        humor_labels = torch.rand(batch_size, 1).to(self.device)

        return embeddings, attention_mask, humor_labels

    def train_epoch(self, epoch_num, num_batches=10):
        """Train for one epoch"""
        self.model.train()
        total_loss = 0.0

        for batch_idx in range(num_batches):
            # Get batch data
            embeddings, attention_mask, humor_labels = self.create_mock_data()

            # Forward pass
            self.optimizer.zero_grad()
            outputs = self.model(embeddings, attention_mask)

            # Calculate loss
            humor_prediction = outputs['humor_prediction']
            loss = self.criterion(humor_prediction, humor_labels)

            # Backward pass
            loss.backward()
            self.optimizer.step()

            total_loss += loss.item()

            if batch_idx % 5 == 0:
                print(f"  Epoch {epoch_num} | Batch {batch_idx}/{num_batches} | Loss: {loss.item():.4f}")

        avg_loss = total_loss / num_batches
        return avg_loss

    def validate(self):
        """Validate model performance"""
        self.model.eval()
        with torch.no_grad():
            embeddings, attention_mask, humor_labels = self.create_mock_data(batch_size=32)
            outputs = self.model(embeddings, attention_mask)

            humor_score = outputs['humor_prediction'].mean().item()
            misalignment = outputs['causal_reasoning']['misalignment_score'].mean().item()

        return humor_score, misalignment

    def save_checkpoint(self, epoch, loss, metrics):
        """Save model checkpoint"""
        checkpoint_path = self.checkpoint_dir / f"tom_epoch_{epoch}.pt"

        checkpoint = {
            'epoch': epoch,
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'loss': loss,
            'metrics': metrics
        }

        torch.save(checkpoint, checkpoint_path)
        print(f"💾 Checkpoint saved: {checkpoint_path}")

        # Keep only last 3 checkpoints to manage space
        self.cleanup_checkpoints(keep_last=3)

    def cleanup_checkpoints(self, keep_last=3):
        """Remove old checkpoints to manage disk space"""
        checkpoints = sorted(self.checkpoint_dir.glob("tom_epoch_*.pt"))
        if len(checkpoints) > keep_last:
            for old_checkpoint in checkpoints[:-keep_last]:
                old_checkpoint.unlink()
                print(f"🗑️  Removed old checkpoint: {old_checkpoint}")

    def train(self, num_epochs=10, validate_every=2, checkpoint_every=5):
        """Main training loop"""
        print(f"🚀 Starting Theory of Mind Training")
        print(f"Epochs: {num_epochs}")
        print(f"Validate Every: {validate_every} epochs")
        print(f"Checkpoint Every: {checkpoint_every} epochs")
        print("=" * 60)

        best_loss = float('inf')

        for epoch in range(1, num_epochs + 1):
            print(f"\n📚 Epoch {epoch}/{num_epochs}")

            # Train
            avg_loss = self.train_epoch(epoch)

            # Validate
            if epoch % validate_every == 0:
                humor_score, misalignment = self.validate()
                print(f"✅ Validation | Humor Score: {humor_score:.4f} | Misalignment: {misalignment:.4f}")

                metrics = {
                    'humor_score': humor_score,
                    'misalignment': misalignment
                }

                # Save checkpoint
                if epoch % checkpoint_every == 0:
                    self.save_checkpoint(epoch, avg_loss, metrics)

                # Save best model
                if avg_loss < best_loss:
                    best_loss = avg_loss
                    best_model_path = self.checkpoint_dir / "tom_best.pt"
                    torch.save(self.model.state_dict(), best_model_path)
                    print(f"🏆 Best model saved with loss: {best_loss:.4f}")

        print("\n🎉 Training completed!")
        return best_loss

def main():
    """Main training function"""
    print("🎭 THEORY OF MIND COMPONENT TRAINING")
    print("=" * 60)

    trainer = ToMTrainer()

    # Train model
    best_loss = trainer.train(
        num_epochs=10,
        validate_every=2,
        checkpoint_every=5
    )

    print(f"\n🎯 Training Summary:")
    print(f"Best Loss: {best_loss:.4f}")
    print(f"Model saved to: {trainer.checkpoint_dir}")

    return trainer

if __name__ == "__main__":
    trainer = main()