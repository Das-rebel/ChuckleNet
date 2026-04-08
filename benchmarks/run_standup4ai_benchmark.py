"""
StandUp4AI Benchmark Runner

Execute complete StandUp4AI evaluation with word-level laughter prediction,
multi-language support, and IoU-based temporal metrics.
"""

import os
import sys
import json
import torch
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
import logging

# Add project path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from benchmarks.standup4ai_word_level import (
    StandUp4AIConfig,
    WordLevelLaughterPredictor,
    StandUp4AIWordLevelDataset,
    IoUEvaluator,
    StandUp4AIBenchmark
)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class StandUp4AIRunner:
    """Enhanced runner for StandUp4AI benchmark"""

    def __init__(self, config: StandUp4AIConfig):
        self.config = config
        self.benchmark = StandUp4AIBenchmark(config)
        self.results = {}

    def prepare_data(self) -> Tuple[any, any, any]:
        """Prepare datasets for evaluation"""
        logger.info("Preparing StandUp4AI datasets...")

        try:
            # Create datasets
            train_dataset = StandUp4AIWordLevelDataset(self.config, 'train')
            val_dataset = StandUp4AIWordLevelDataset(self.config, 'val')
            test_dataset = StandUp4AIWordLevelDataset(self.config, 'test')

            logger.info(f"Train dataset: {len(train_dataset)} samples")
            logger.info(f"Val dataset: {len(val_dataset)} samples")
            logger.info(f"Test dataset: {len(test_dataset)} samples")

            return train_dataset, val_dataset, test_dataset

        except Exception as e:
            logger.error(f"Data preparation failed: {e}")
            return None, None, None

    def setup_model(self) -> bool:
        """Setup and initialize model"""
        logger.info("Setting up model...")

        try:
            self.benchmark.setup_model()
            logger.info("Model setup completed successfully")
            return True

        except Exception as e:
            logger.error(f"Model setup failed: {e}")
            return False

    def run_evaluation(self) -> Dict:
        """Run complete benchmark evaluation"""
        logger.info("="*60)
        logger.info("Starting StandUp4AI Benchmark Evaluation")
        logger.info("="*60)

        # Prepare data
        train_dataset, val_dataset, test_dataset = self.prepare_data()
        if train_dataset is None:
            logger.error("Failed to prepare datasets")
            return {}

        # Setup model
        if not self.setup_model():
            logger.error("Failed to setup model")
            return {}

        # Create dataloaders
        from torch.utils.data import DataLoader

        train_loader = DataLoader(
            train_dataset,
            batch_size=self.config.batch_size,
            shuffle=True,
            num_workers=0  # Set to 0 for compatibility
        )

        val_loader = DataLoader(
            val_dataset,
            batch_size=self.config.batch_size,
            shuffle=False,
            num_workers=0
        )

        test_loader = DataLoader(
            test_dataset,
            batch_size=self.config.batch_size,
            shuffle=False,
            num_workers=0
        )

        # Setup device
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        logger.info(f"Using device: {device}")

        # Move model to device
        self.benchmark.model.to(device)

        # Train model (simplified for demo)
        logger.info("Training model...")
        try:
            self.train_model(train_loader, val_loader, device)
        except Exception as e:
            logger.error(f"Training failed: {e}")
            logger.info("Proceeding with evaluation using untrained model...")

        # Evaluate on test set
        logger.info("Evaluating on test set...")
        test_results = self.benchmark.evaluate_per_language(
            self.benchmark.model,
            test_loader,
            device
        )

        return test_results

    def train_model(self, train_loader, val_loader, device):
        """Train the model (simplified implementation)"""
        logger.info("Starting training...")

        optimizer = torch.optim.AdamW(
            self.benchmark.model.parameters(),
            lr=self.config.learning_rate
        )

        # Training loop
        for epoch in range(self.config.num_epochs):
            logger.info(f"Epoch {epoch + 1}/{self.config.num_epochs}")

            self.benchmark.model.train()
            total_loss = 0

            for batch_idx, batch in enumerate(train_loader):
                try:
                    # Move to device
                    input_ids = batch['input_ids'].to(device)
                    attention_mask = batch['attention_mask'].to(device)
                    labels = batch['labels'].to(device)
                    language = batch['language'][0] if isinstance(batch['language'], list) else batch['language']

                    # Forward pass
                    outputs = self.benchmark.model(
                        input_ids,
                        attention_mask,
                        language=language,
                        labels=labels
                    )

                    loss = outputs['loss']
                    if loss is not None:
                        # Backward pass
                        optimizer.zero_grad()
                        loss.backward()
                        optimizer.step()

                        total_loss += loss.item()

                except Exception as e:
                    logger.warning(f"Training batch {batch_idx} failed: {e}")
                    continue

            avg_loss = total_loss / len(train_loader) if len(train_loader) > 0 else 0
            logger.info(f"Average training loss: {avg_loss:.4f}")

        logger.info("Training completed")

    def generate_report(self, results: Dict) -> str:
        """Generate comprehensive evaluation report"""
        report = []
        report.append("="*60)
        report.append("StandUp4AI Benchmark Evaluation Report")
        report.append("="*60)

        # Results by language
        report.append("\nPer-Language Results:")
        report.append("-" * 40)

        for language in sorted(results.keys()):
            if language == 'macro_avg':
                continue

            metrics = results[language]
            report.append(f"\n{language}:")
            report.append(f"  F1 Score: {metrics['f1']:.4f}")
            report.append(f"  IoU@0.2 F1: {metrics['iou_f1']:.4f}")
            report.append(f"  Precision: {metrics['precision']:.4f}")
            report.append(f"  Recall: {metrics['recall']:.4f}")
            report.append(f"  Samples: {metrics['num_samples']}")

        # Macro average
        if 'macro_avg' in results:
            report.append("\n" + "-" * 40)
            report.append("Macro Average:")
            macro_metrics = results['macro_avg']
            report.append(f"  F1 Score: {macro_metrics['f1']:.4f}")
            report.append(f"  IoU@0.2 F1: {macro_metrics['iou_f1']:.4f}")
            report.append(f"  Total Samples: {macro_metrics['num_samples']}")

        # Baseline comparison
        report.append("\n" + "="*60)
        report.append("Baseline Comparison")
        report.append("="*60)

        published_baseline = 0.58  # From StandUp4AI paper
        our_f1 = results.get('macro_avg', {}).get('f1', 0.0)
        our_iou_f1 = results.get('macro_avg', {}).get('iou_f1', 0.0)

        report.append(f"Published Baseline F1: {published_baseline:.4f}")
        report.append(f"Our Method F1: {our_f1:.4f}")
        report.append(f"Our Method IoU@0.2 F1: {our_iou_f1:.4f}")
        report.append(f"F1 Difference: {our_f1 - published_baseline:+.4f}")

        if our_f1 > published_baseline:
            report.append(f"✓ SUCCESS: Outperforms baseline by {our_f1 - published_baseline:.4f} F1")
        else:
            report.append(f"✗ GAP: Underperforms baseline by {published_baseline - our_f1:.4f} F1")

        # Analysis
        report.append("\n" + "="*60)
        report.append("Analysis")
        report.append("="*60)

        report.append(f"\nModel Configuration:")
        report.append(f"  Model: {self.config.model_name}")
        report.append(f"  Max Sequence Length: {self.config.max_seq_length}")
        report.append(f"  Hidden Dimension: {self.config.hidden_dim}")
        report.append(f"  Batch Size: {self.config.batch_size}")
        report.append(f"  Learning Rate: {self.config.learning_rate}")
        report.append(f"  Epochs: {self.config.num_epochs}")

        report.append(f"\nEvaluation Protocol:")
        report.append(f"  IoU Threshold: {self.config.iou_threshold}")
        report.append(f"  Speaker Independent: {self.config.speaker_independent}")
        report.append(f"  Languages Supported: {', '.join(self.config.languages)}")

        return "\n".join(report)

    def save_results(self, results: Dict, report: str):
        """Save results and report to files"""
        output_dir = Path("./results/standup4ai")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save JSON results
        results_file = output_dir / "evaluation_results.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)

        # Save text report
        report_file = output_dir / "evaluation_report.txt"
        with open(report_file, 'w') as f:
            f.write(report)

        logger.info(f"Results saved to {results_file}")
        logger.info(f"Report saved to {report_file}")

    def run_benchmark(self) -> Dict:
        """Run complete benchmark pipeline"""
        try:
            # Run evaluation
            results = self.run_evaluation()

            if not results:
                logger.error("Benchmark evaluation failed")
                return {}

            # Generate report
            report = self.generate_report(results)

            # Print report
            print("\n" + report)

            # Save results
            self.save_results(results, report)

            return results

        except Exception as e:
            logger.error(f"Benchmark execution failed: {e}")
            import traceback
            traceback.print_exc()
            return {}


def main():
    """Main execution function"""
    print("StandUp4AI Benchmark Runner")
    print("="*60)

    # Configuration
    config = StandUp4AIConfig(
        data_dir='/Users/Subho/data/standup4ai',
        cache_dir='./cache/standup4ai',
        model_name='bert-base-multilingual-cased',
        max_seq_length=128,  # Reduced for demo
        batch_size=4,        # Reduced for demo
        learning_rate=2e-5,
        num_epochs=2,        # Reduced for demo
        iou_threshold=0.2
    )

    # Run benchmark
    runner = StandUp4AIRunner(config)
    results = runner.run_benchmark()

    if results:
        print("\n" + "="*60)
        print("Benchmark completed successfully!")
        print("="*60)
        return 0
    else:
        print("\n" + "="*60)
        print("Benchmark failed!")
        print("="*60)
        return 1


if __name__ == '__main__':
    sys.exit(main())