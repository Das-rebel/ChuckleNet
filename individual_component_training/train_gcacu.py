#!/usr/bin/env python3
"""
GCACU Network Component Training Script
Trains the GCACU network for improved incongruity detection
"""

import torch
import torch.nn as nn
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.gcacu.gcacu import GCACUNetwork

class GCACUTrainer:
    def __init__(self):
        # Model configuration
        self.embedding_dim = 256
        self.num_heads = 4
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        # Initialize model
        self.model = GCACUNetwork(
            embedding_dim=self.embedding_dim,
            num_heads=self.num_heads
        ).to(self.device)

        # Training configuration
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=1e-4)
        self.criterion = nn.MSELoss()

        # Checkpoint configuration
        self.checkpoint_dir = project_root / "checkpoints" / "gcacu"
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        print(f"⚡ GCACU Network Trainer Initialized")
        print(f"Device: {self.device}")
        print(f"Checkpoint Dir: {self.checkpoint_dir}")

    def create_mock_data(self, batch_size=16, seq_len=32):
        """Create mock training data for testing"""
        embeddings = torch.randn(batch_size, seq_len, self.embedding_dim).to(self.device)
        attention_mask = torch.ones(batch_size, seq_len).to(self.device)
        incongruity_labels = torch.rand(batch_size, 1).to(self.device)

        return embeddings, attention_mask, incongruity_labels

    def train_epoch(self, epoch_num, num_batches=10):
        """Train for one epoch"""
        self.model.train()
        total_loss = 0.0

        for batch_idx in range(num_batches):
            # Get batch data
            embeddings, attention_mask, incongruity_labels = self.create_mock_data()

            # Forward pass
            self.optimizer.zero_grad()
            outputs = self.model(embeddings, attention_mask)

            # Calculate loss
            incongruity_score = outputs['incongruity_score']
            loss = self.criterion(incongruity_score, incongruity_labels)

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
            embeddings, attention_mask, incongruity_labels = self.create_mock_data(batch_size=32)
            outputs = self.model(embeddings, attention_mask)

            incongruity_score = outputs['incongruity_score'].mean().item()
            importance_score = outputs['importance_scores'].mean().item()

        return incongruity_score, importance_score

    def save_checkpoint(self, epoch, loss, metrics):
        """Save model checkpoint"""
        checkpoint_path = self.checkpoint_dir / f"gcacu_epoch_{epoch}.pt"

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
        checkpoints = sorted(self.checkpoint_dir.glob("gcacu_epoch_*.pt"))
        if len(checkpoints) > keep_last:
            for old_checkpoint in checkpoints[:-keep_last]:
                old_checkpoint.unlink()
                print(f"🗑️  Removed old checkpoint: {old_checkpoint}")

    def train(self, num_epochs=10, validate_every=2, checkpoint_every=5):
        """Main training loop"""
        print(f"🚀 Starting GCACU Network Training")
        print(f"Epochs: {num_epochs}")
        print(f"Validate Every: {validate_every} epochs")
        print(f"Checkpoint Every: {checkpoint_every} epochs")
        print("=" * 60)

        best_loss = float('inf')

        for epoch in range(1, num_epochs + 1):
            print(f"\n⚡ Epoch {epoch}/{num_epochs}")

            # Train
            avg_loss = self.train_epoch(epoch)

            # Validate
            if epoch % validate_every == 0:
                incongruity_score, importance_score = self.validate()
                print(f"✅ Validation | Incongruity: {incongruity_score:.4f} | Importance: {importance_score:.4f}")

                metrics = {
                    'incongruity_score': incongruity_score,
                    'importance_score': importance_score
                }

                # Save checkpoint
                if epoch % checkpoint_every == 0:
                    self.save_checkpoint(epoch, avg_loss, metrics)

                # Save best model
                if avg_loss < best_loss:
                    best_loss = avg_loss
                    best_model_path = self.checkpoint_dir / "gcacu_best.pt"
                    torch.save(self.model.state_dict(), best_model_path)
                    print(f"🏆 Best model saved with loss: {best_loss:.4f}")

        print("\n🎉 Training completed!")
        return best_loss

def main():
    """Main training function"""
    print("⚡ GCACU NETWORK COMPONENT TRAINING")
    print("=" * 60)

    trainer = GCACUTrainer()

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