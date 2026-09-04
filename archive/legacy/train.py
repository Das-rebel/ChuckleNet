#!/usr/bin/env python3
"""
Main Training Script for Autonomous Laughter Prediction Framework
Integrates all cognitive architectures with memory optimization for 8GB constraint
"""

import os
import sys
import json
import logging
import argparse
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np
from tqdm import tqdm

# Import our cognitive architectures
from core.tom.theory_of_mind import TheoryOfMindLayer
from core.clost.clost import CLoSTLayer
from core.gcacu.gcacu import GCACUNetwork
from core.sevade.sevade import SEVADEEvaluator
from core.integrated_model import IntegratedLaughterModel

# Import memory optimization systems
from memory.engram.engram import EngramMemorySystem, EngramConfig, create_engram_system
from memory.mhc.mhc import ManifoldConstrainedHyperConnections, MHCConfig, create_mhc_system

# Import memory profiling
from training.memory_profiler import MemoryProfiler, memory_monitoring, optimize_for_8gb_mac_m2

# Import knowledge base
from knowledge_base.comedy_knowledge import create_comprehensive_knowledge_base

# Import data pipeline
from data.harvesters.subtitle_harvester import SubtitleHarvester
from data.processors.wesr_bench import WESRBenchEvaluator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('training.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class MemoryMonitor:
    """Monitor memory usage to ensure we stay under 8GB constraint"""
    
    def __init__(self, max_memory_gb: float = 5.0):
        self.max_memory_gb = max_memory_gb
        self.max_allocated = 0.0
        
    def check_memory(self) -> float:
        """Check current memory usage in GB"""
        if torch.cuda.is_available():
            allocated = torch.cuda.memory_allocated() / (1024**3)
            cached = torch.cuda.memory_reserved() / (1024**3)
        else:
            # For CPU/MPS, use psutil if available
            try:
                import psutil
                process = psutil.Process()
                allocated = process.memory_info().rss / (1024**3)
                cached = allocated
            except ImportError:
                allocated = 0.0
                cached = 0.0
        
        self.max_allocated = max(self.max_allocated, allocated)
        return allocated
    
    def is_safe(self) -> bool:
        """Check if memory usage is safe"""
        current = self.check_memory()
        return current < self.max_memory_gb
    
    def get_stats(self) -> Dict[str, float]:
        """Get memory statistics"""
        current = self.check_memory()
        return {
            'current_gb': current,
            'max_gb': self.max_allocated,
            'safety_margin_gb': self.max_memory_gb - current,
            'percentage': (current / self.max_memory_gb) * 100
        }


class ComedyDataset(Dataset):
    """Dataset for comedy transcript analysis"""
    
    def __init__(self, transcripts: List[Dict], max_length: int = 512, embedding_dim: int = 64):
        self.transcripts = transcripts
        self.max_length = max_length
        self.embedding_dim = embedding_dim
        
    def __len__(self):
        return len(self.transcripts)
    
    def __getitem__(self, idx: torch.Tensor) -> Dict[str, torch.Tensor]:
        transcript = self.transcripts[idx]
        
        # Create mock embeddings (in real system, use actual tokenizer)
        text = transcript.get('clean_content', '')
        words = text.split()[:self.max_length]
        
        # Mock word embeddings aligned with the compact integrated model config.
        embeddings = torch.randn(len(words), self.embedding_dim)
        
        # Create attention mask
        attention_mask = torch.ones(len(words))
        
        # Create labels (0 = no laughter, 1 = laughter)
        labels = torch.tensor([1 if transcript.get('has_laughter_tags', False) else 0])
        
        return {
            'embeddings': embeddings,
            'attention_mask': attention_mask,
            'labels': labels,
            'text': text
        }


class AdaptiveFocalLoss(nn.Module):
    """
    Adaptive Focal Loss for handling imbalanced laughter data
    Focuses on hard examples and adapts to class imbalance
    """
    
    def __init__(self, alpha: float = 0.25, gamma: float = 2.0, smoothing: float = 0.1):
        super().__init__()
        self.alpha = alpha
        self.gamma = gamma
        self.smoothing = smoothing
        
    def forward(self, predictions: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        """
        Compute adaptive focal loss
        
        Args:
            predictions: Predicted probabilities (batch, 1)
            targets: Ground truth labels (batch, 1)
        
        Returns:
            Computed loss
        """
        # Label smoothing
        targets_smooth = targets * (1 - self.smoothing) + self.smoothing / 2
        
        # Binary cross entropy with logits
        bce_loss = nn.functional.binary_cross_entropy(
            predictions, targets_smooth, reduction='none'
        )
        
        # Focal term: (1 - p_t)^gamma
        p_t = predictions * targets + (1 - predictions) * (1 - targets)
        focal_term = (1 - p_t) ** self.gamma
        
        # Adaptive focal loss
        loss = self.alpha * focal_term * bce_loss
        
        return loss.mean()


class TrainingPipeline:
    """Main training pipeline for laughter prediction"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        # Use advanced memory profiler
        self.memory_profiler = MemoryProfiler(max_memory_gb=config.get('MAX_MEMORY_GB', 5.0))
        self.memory_monitor = MemoryMonitor(max_memory_gb=config.get('MAX_MEMORY_GB', 5.0))

        # Setup directories
        self.checkpoint_dir = Path(config.get('CHECKPOINTS_DIR', 'checkpoints'))
        self.models_dir = Path(config.get('MODELS_DIR', 'models'))
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.models_dir.mkdir(parents=True, exist_ok=True)

        # Initialize model with memory optimization
        with memory_monitoring(self.memory_profiler, "Model initialization"):
            self.model = self._build_model()
            self.model.to(self.device)

            # Apply Mac M2 optimizations
            optimization_results = optimize_for_8gb_mac_m2(self.model)
            logger.info(f"Model optimizations applied: {optimization_results['optimizations_applied']}")

        # Initialize knowledge base for Engram
        if config.get('USE_ENGRAM', True):
            with memory_monitoring(self.memory_profiler, "Knowledge base initialization"):
                knowledge_base = create_comprehensive_knowledge_base()
                knowledge_data = knowledge_base.create_engram_data()
                self.model.initialize_knowledge_base(knowledge_data)
                logger.info(f"Knowledge base initialized with {len(knowledge_data)} entries")

        # Initialize loss and optimizer
        self.criterion = AdaptiveFocalLoss()
        self.optimizer = self._create_optimizer()

        # Training state
        self.epoch = 0
        self.best_f1 = 0.0
        self.training_history = []

        # Start memory monitoring
        self.memory_profiler.start_monitoring(interval_seconds=2.0)
        
    def _build_model(self) -> nn.Module:
        """Build integrated model with all cognitive architectures"""
        logger.info("Building integrated model with all cognitive architectures...")

        model = IntegratedLaughterModel(
            embedding_dim=self.config.get('EMBEDDING_DIM', 64),
            num_heads=self.config.get('NUM_HEADS', 4),
            hidden_dim=self.config.get('HIDDEN_DIM', 64),
            turboquant_heads=self.config.get('NUM_HEADS', 4),
            memory_budget_gb=self.config.get('MAX_MEMORY_GB', 5.0),
            use_engram=self.config.get('USE_ENGRAM', True),
            use_mhc=self.config.get('USE_MHC', True)
        )

        logger.info(f"Model built with {sum(p.numel() for p in model.parameters())} parameters")

        # Get memory stats
        memory_stats = model.get_memory_stats()
        logger.info(f"Model memory usage: {memory_stats['model_memory_mb']:.2f}MB")

        return model
    
    def _create_optimizer(self) -> optim.Optimizer:
        """Create optimizer with weight decay"""
        return optim.AdamW(
            self.model.parameters(),
            lr=self.config.get('LEARNING_RATE', 2e-5),
            weight_decay=self.config.get('WEIGHT_DECAY', 0.01),
            betas=(0.9, 0.999)
        )
    
    def load_data(self) -> Tuple[DataLoader, DataLoader]:
        """Load training and validation data"""
        logger.info("Loading data...")
        
        # Mock data loading - replace with actual data pipeline
        train_transcripts = [
            {
                'clean_content': 'This is a sample comedy transcript about everyday life situations',
                'has_laughter_tags': True
            }
        ] * 100
        
        val_transcripts = [
            {
                'clean_content': 'This is a validation transcript for testing',
                'has_laughter_tags': False
            }
        ] * 20
        
        train_dataset = ComedyDataset(
            train_transcripts,
            embedding_dim=self.config.get('EMBEDDING_DIM', 64),
        )
        val_dataset = ComedyDataset(
            val_transcripts,
            embedding_dim=self.config.get('EMBEDDING_DIM', 64),
        )
        
        train_loader = DataLoader(
            train_dataset,
            batch_size=self.config.get('BATCH_SIZE', 4),
            shuffle=True,
            num_workers=0  # Use 0 for memory efficiency
        )
        
        val_loader = DataLoader(
            val_dataset,
            batch_size=self.config.get('BATCH_SIZE', 4),
            shuffle=False,
            num_workers=0
        )
        
        logger.info(f"Data loaded: {len(train_dataset)} train, {len(val_dataset)} val samples")
        return train_loader, val_loader
    
    def train_epoch(self, train_loader: DataLoader) -> Dict[str, float]:
        """Train for one epoch"""
        self.model.train()
        total_loss = 0.0
        correct = 0
        total = 0
        
        progress_bar = tqdm(train_loader, desc=f"Epoch {self.epoch}")
        
        for batch_idx, batch in enumerate(progress_bar):
            # Check memory safety
            if not self.memory_monitor.is_safe():
                logger.warning("Memory limit approaching, clearing cache")
                torch.cuda.empty_cache() if torch.cuda.is_available() else None
                
            # Move data to device
            embeddings = batch['embeddings'].to(self.device)
            attention_mask = batch['attention_mask'].to(self.device)
            labels = batch['labels'].to(self.device)
            
            # Forward pass
            self.optimizer.zero_grad()
            
            # Get model predictions
            outputs = self.model({
                'embeddings': embeddings,
                'attention_mask': attention_mask,
            })
            predictions = outputs['probabilities']
            
            # Compute loss
            loss = self.criterion(predictions, labels)
            
            # Backward pass
            loss.backward()
            
            # Gradient clipping for stability
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
            
            self.optimizer.step()
            
            # Statistics
            total_loss += loss.item()
            predicted_labels = (predictions > 0.5).float()
            correct += (predicted_labels == labels).sum().item()
            total += labels.size(0)
            
            # Update progress bar
            progress_bar.set_postfix({
                'loss': f'{loss.item():.4f}',
                'acc': f'{100 * correct / total:.2f}%',
                'mem': f"{self.memory_monitor.get_stats()['current_gb']:.2f}GB"
            })
        
        return {
            'loss': total_loss / len(train_loader),
            'accuracy': correct / total
        }
    
    def validate(self, val_loader: DataLoader) -> Dict[str, float]:
        """Validate the model"""
        self.model.eval()
        total_loss = 0.0
        all_predictions = []
        all_labels = []
        
        with torch.no_grad():
            for batch in tqdm(val_loader, desc="Validation"):
                embeddings = batch['embeddings'].to(self.device)
                attention_mask = batch['attention_mask'].to(self.device)
                labels = batch['labels'].to(self.device)
                
                # Forward pass
                outputs = self.model({
                    'embeddings': embeddings,
                    'attention_mask': attention_mask,
                })
                predictions = outputs['probabilities']
                
                # Compute loss
                loss = self.criterion(predictions, labels)
                total_loss += loss.item()
                
                # Store predictions and labels
                all_predictions.extend(predictions.cpu().numpy())
                all_labels.extend(labels.cpu().numpy())
        
        # Compute metrics
        all_predictions = np.array(all_predictions)
        all_labels = np.array(all_labels)
        
        # Convert to binary predictions
        binary_preds = (all_predictions > 0.5).astype(int)
        
        # Calculate metrics
        from sklearn.metrics import f1_score, precision_score, recall_score
        
        f1 = f1_score(all_labels, binary_preds, average='binary', zero_division=0)
        precision = precision_score(all_labels, binary_preds, average='binary', zero_division=0)
        recall = recall_score(all_labels, binary_preds, average='binary', zero_division=0)
        
        return {
            'loss': total_loss / len(val_loader),
            'f1': f1,
            'precision': precision,
            'recall': recall
        }
    
    def train(self, train_loader: DataLoader, val_loader: DataLoader):
        """Main training loop"""
        logger.info("Starting training loop...")
        logger.info(f"Device: {self.device}")
        logger.info(f"Memory limit: {self.config.get('MAX_MEMORY_GB', 5.0)}GB")
        
        max_epochs = self.config.get('MAX_EPOCHS', 10)
        patience = self.config.get('EARLY_STOPPING_PATIENCE', 3)
        best_val_loss = float('inf')
        patience_counter = 0
        
        for epoch in range(max_epochs):
            self.epoch = epoch
            logger.info(f"\n{'='*60}")
            logger.info(f"Epoch {epoch + 1}/{max_epochs}")
            logger.info(f"{'='*60}")
            
            # Training
            train_metrics = self.train_epoch(train_loader)
            
            # Validation
            val_metrics = self.validate(val_loader)
            
            # Log metrics
            logger.info(f"Train Loss: {train_metrics['loss']:.4f}, Train Acc: {train_metrics['accuracy']:.4f}")
            logger.info(f"Val Loss: {val_metrics['loss']:.4f}, Val F1: {val_metrics['f1']:.4f}")
            logger.info(f"Memory: {self.memory_monitor.get_stats()}")
            
            # Save history
            self.training_history.append({
                'epoch': epoch,
                'train_metrics': train_metrics,
                'val_metrics': val_metrics,
                'memory_stats': self.memory_monitor.get_stats()
            })
            
            # Save best model
            if val_metrics['f1'] > self.best_f1:
                self.best_f1 = val_metrics['f1']
                self.save_checkpoint('best_model.pth')
                logger.info(f"🎉 New best F1: {self.best_f1:.4f}")
            
            # Early stopping
            if val_metrics['loss'] < best_val_loss:
                best_val_loss = val_metrics['loss']
                patience_counter = 0
            else:
                patience_counter += 1
                
            if patience_counter >= patience:
                logger.info(f"Early stopping triggered after {epoch + 1} epochs")
                break
        
        logger.info(f"\n🎉 Training completed! Best F1: {self.best_f1:.4f}")
    
    def save_checkpoint(self, filename: str):
        """Save model checkpoint"""
        checkpoint = {
            'epoch': self.epoch,
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'best_f1': self.best_f1,
            'training_history': self.training_history,
            'config': self.config
        }
        
        checkpoint_path = self.checkpoint_dir / filename
        torch.save(checkpoint, checkpoint_path)
        logger.info(f"Checkpoint saved: {checkpoint_path}")
    
    def load_checkpoint(self, filename: str):
        """Load model checkpoint"""
        checkpoint_path = self.checkpoint_dir / filename
        
        if not checkpoint_path.exists():
            logger.warning(f"Checkpoint not found: {checkpoint_path}")
            return
        
        checkpoint = torch.load(checkpoint_path, map_location=self.device)
        
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.epoch = checkpoint['epoch']
        self.best_f1 = checkpoint['best_f1']
        self.training_history = checkpoint['training_history']
        
        logger.info(f"Checkpoint loaded: {checkpoint_path}")


def main():
    """Main training function"""
    parser = argparse.ArgumentParser(description='Train Laughter Prediction Model')
    parser.add_argument('--config', type=str, default='config.json', help='Path to config file')
    parser.add_argument('--resume', type=str, help='Resume from checkpoint')
    parser.add_argument('--epochs', type=int, default=10, help='Number of epochs')
    parser.add_argument('--batch-size', type=int, default=4, help='Batch size')
    parser.add_argument('--lr', type=float, default=2e-5, help='Learning rate')
    parser.add_argument('--max-memory', type=float, default=5.0, help='Max memory in GB')
    
    args = parser.parse_args()
    
    # Configuration
    config = {
        'MAX_EPOCHS': args.epochs,
        'BATCH_SIZE': args.batch_size,
        'LEARNING_RATE': args.lr,
        'MAX_MEMORY_GB': args.max_memory,
        'WEIGHT_DECAY': 0.01,
        'EARLY_STOPPING_PATIENCE': 3,
        'CHECKPOINTS_DIR': 'checkpoints',
        'MODELS_DIR': 'models',
        'EMBEDDING_DIM': 64,
        'HIDDEN_DIM': 64,
        'NUM_HEADS': 4,
    }
    
    # Load additional config from file if exists
    if os.path.exists(args.config):
        with open(args.config, 'r') as f:
            file_config = json.load(f)
            config.update(file_config)
    
    logger.info("🚀 Starting Autonomous Laughter Prediction Training")
    logger.info(f"Configuration: {json.dumps(config, indent=2)}")
    
    # Create training pipeline
    pipeline = TrainingPipeline(config)
    
    # Resume from checkpoint if specified
    if args.resume:
        pipeline.load_checkpoint(args.resume)
    
    # Load data
    train_loader, val_loader = pipeline.load_data()
    
    # Train model
    pipeline.train(train_loader, val_loader)
    
    logger.info("✅ Training completed successfully!")


if __name__ == "__main__":
    main()
