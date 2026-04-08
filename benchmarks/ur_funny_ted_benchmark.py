"""
UR-FUNNY TED Benchmark Evaluation Script

This script implements the complete evaluation pipeline for the UR-FUNNY TED benchmark,
including dataset loading, model training, evaluation, and comparison to published baselines.

Target: Beat or match 65.23% accuracy (C-MFN baseline)
"""

import os
import json
import torch
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Any
from datetime import datetime
import argparse

# Import our UR-FUNNY TED dataset and model
from benchmarks.datasets.ur_funny_ted import (
    URFunnyTEDDataset,
    create_ur_funny_ted_dataloaders
)
from models.multimodal_humor_detector import (
    URFunnyTEDModel,
    create_ur_funny_model
)
from benchmarks.external_benchmark_evaluator import ExternalBenchmarkEvaluator


class URFunnyTEDEvaluator:
    """
    Evaluator for UR-FUNNY TED benchmark.

    Handles complete evaluation pipeline:
    1. Dataset loading and preprocessing
    2. Model training and evaluation
    3. Comparison to published baselines
    4. Results generation and reporting
    """

    def __init__(self,
                 data_path: str,
                 output_dir: str = './ur_funny_ted_results',
                 model_type: str = 'early_fusion',
                 device: str = 'cuda'):
        """
        Initialize UR-FUNNY TED evaluator.

        Args:
            data_path: Path to UR-FUNNY TED dataset
            output_dir: Directory to save results
            model_type: Model architecture type
            device: Device to run evaluation on
        """
        self.data_path = Path(data_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.model_type = model_type
        self.device = device if torch.cuda.is_available() else 'cpu'

        # Benchmark constants
        self.BASELINE_ACCURACY = 65.23  # C-MFN published baseline
        self.HUMAN_PERFORMANCE = 82.5   # Human upper bound

        print(f"UR-FUNNY TED Evaluator initialized")
        print(f"Model type: {model_type}")
        print(f"Device: {self.device}")
        print(f"Target baseline: {self.BASELINE_ACCURACY}%")

    def load_dataset(self) -> Dict[str, torch.utils.data.DataLoader]:
        """
        Load UR-FUNNY TED dataset and create dataloaders.

        Returns:
            Dictionary with train, val, test dataloaders
        """
        print("\n" + "="*50)
        print("Loading UR-FUNNY TED Dataset")
        print("="*50)

        try:
            dataloaders = create_ur_funny_ted_dataloaders(
                data_path=str(self.data_path),
                batch_size=32,
                num_workers=4
            )

            # Print dataset statistics
            for split, dataloader in dataloaders.items():
                print(f"{split.capitalize()} split: {len(dataloader.dataset)} samples")

                # Get label distribution
                dataset = dataloader.dataset
                if hasattr(dataset, 'get_statistics'):
                    stats = dataset.get_statistics()
                    print(f"  Statistics: {stats}")

            return dataloaders

        except Exception as e:
            print(f"Error loading dataset: {e}")
            print("Please ensure UR-FUNNY TED dataset is properly set up at:", self.data_path)
            raise

    def create_model(self) -> URFunnyTEDModel:
        """Create and initialize the multimodal humor detection model"""
        print("\n" + "="*50)
        print("Creating Multimodal Humor Detection Model")
        print("="*50)

        model = create_ur_funny_model(
            model_type=self.model_type,
            device=self.device
        )

        print(f"Model architecture: {self.model_type}")
        print(f"Number of parameters: {sum(p.numel() for p in model.model.parameters()):,}")

        return model

    def train_model(self,
                   model: URFunnyTEDModel,
                   dataloaders: Dict[str, torch.utils.data.DataLoader],
                   num_epochs: int = 20) -> Dict[str, List[float]]:
        """
        Train the multimodal humor detection model.

        Args:
            model: Model to train
            dataloaders: Dictionary with train/val dataloaders
            num_epochs: Maximum number of training epochs

        Returns:
            Training history
        """
        print("\n" + "="*50)
        print("Training Model")
        print("="*50)

        train_loader = dataloaders['train']
        val_loader = dataloaders['val']

        # Train model
        best_val_acc = model.train(
            train_loader=train_loader,
            val_loader=val_loader,
            num_epochs=num_epochs,
            early_stopping_patience=5
        )

        print(f"\nTraining complete. Best validation accuracy: {best_val_acc:.2f}%")

        return model.history

    def evaluate_model(self,
                      model: URFunnyTEDModel,
                      test_loader: torch.utils.data.DataLoader) -> Dict[str, float]:
        """
        Evaluate model on test set and compare to baseline.

        Args:
            model: Trained model
            test_loader: Test dataloader

        Returns:
            Evaluation metrics and comparison to baseline
        """
        print("\n" + "="*50)
        print("Evaluating Model on Test Set")
        print("="*50)

        # Evaluate on test set
        test_loss, test_acc = model.evaluate(test_loader)

        print(f"\nTest Results:")
        print(f"  Test Accuracy: {test_acc:.2f}%")
        print(f"  Test Loss: {test_loss:.4f}")

        # Compare to baseline
        comparison = model.compare_to_baseline(test_acc)

        print(f"\nBaseline Comparison:")
        print(f"  C-MFN Baseline: {comparison['baseline_accuracy']:.2f}%")
        print(f"  Human Performance: {comparison['human_performance']:.2f}%")
        print(f"  Improvement: {comparison['improvement_over_baseline']:+.2f}%")
        print(f"  Gap to Human: {comparison['gap_to_human_performance']:.2f}%")
        print(f"  % of Human Performance: {comparison['percentage_of_human_performance']:.1f}%")

        # Determine if we beat the baseline
        if test_acc >= self.BASELINE_ACCURACY:
            print(f"\n✅ SUCCESS: Model beat the C-MFN baseline!")
        else:
            gap = self.BASELINE_ACCURACY - test_acc
            print(f"\n❌ BELOW BASELINE: Model is {gap:.2f}% below C-MFN baseline")

        return {
            'test_accuracy': test_acc,
            'test_loss': test_loss,
            'baseline_comparison': comparison
        }

    def generate_detailed_report(self,
                                model: URFunnyTEDModel,
                                evaluation_results: Dict[str, float],
                                training_history: Dict[str, List[float]]) -> str:
        """
        Generate detailed evaluation report.

        Args:
            model: Trained model
            evaluation_results: Test evaluation results
            training_history: Training history

        Returns:
            Path to generated report
        """
        print("\n" + "="*50)
        print("Generating Evaluation Report")
        print("="*50)

        # Create report
        report = {
            'benchmark': 'UR-FUNNY-TED',
            'evaluation_date': datetime.now().isoformat(),
            'model_type': self.model_type,
            'device': self.device,

            'dataset_info': {
                'name': 'UR-FUNNY-TED',
                'total_videos': 1866,
                'total_instances': 16514,
                'task': 'Multimodal humor detection (binary classification)',
                'features': ['text', 'audio', 'visual']
            },

            'baseline_info': {
                'published_baseline': 'C-MFN',
                'baseline_accuracy': self.BASELINE_ACCURACY,
                'human_performance': self.HUMAN_PERFORMANCE,
                'paper': 'UR-FUNNY: A Large-Scale Dataset for Humor Detection in TED Talks'
            },

            'training_info': {
                'num_epochs': len(training_history['train_loss']),
                'final_train_loss': training_history['train_loss'][-1],
                'final_train_acc': training_history['train_acc'][-1],
                'final_val_loss': training_history['val_loss'][-1],
                'final_val_acc': training_history['val_acc'][-1],
                'best_val_acc': max(training_history['val_acc'])
            },

            'test_results': {
                'test_accuracy': evaluation_results['test_accuracy'],
                'test_loss': evaluation_results['test_loss']
            },

            'comparison': evaluation_results['baseline_comparison'],

            'success_criteria': {
                'target_baseline': self.BASELINE_ACCURACY,
                'achieved': evaluation_results['test_accuracy'] >= self.BASELINE_ACCURACY,
                'improvement': evaluation_results['test_accuracy'] - self.BASELINE_ACCURACY
            }
        }

        # Save report
        report_path = self.output_dir / 'ur_funny_ted_report.json'
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)

        # Create human-readable summary
        summary_path = self.output_dir / 'ur_funny_ted_summary.txt'
        with open(summary_path, 'w') as f:
            f.write("="*70 + "\n")
            f.write("UR-FUNNY TED BENCHMARK EVALUATION SUMMARY\n")
            f.write("="*70 + "\n\n")

            f.write(f"Evaluation Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Model Architecture: {self.model_type}\n")
            f.write(f"Device: {self.device}\n\n")

            f.write("DATASET INFORMATION\n")
            f.write("-" * 70 + "\n")
            f.write(f"Dataset: UR-FUNNY-TED\n")
            f.write(f"Total Videos: 1,866\n")
            f.write(f"Total Instances: 16,514\n")
            f.write(f"Task: Multimodal humor detection (binary classification)\n")
            f.write(f"Features: Text + Audio + Visual\n\n")

            f.write("BASELINE COMPARISON\n")
            f.write("-" * 70 + "\n")
            f.write(f"C-MFN Baseline: {self.BASELINE_ACCURACY:.2f}%\n")
            f.write(f"Human Performance: {self.HUMAN_PERFORMANCE:.2f}%\n")
            f.write(f"Target: Beat or match {self.BASELINE_ACCURACY:.2f}%\n\n")

            f.write("TRAINING RESULTS\n")
            f.write("-" * 70 + "\n")
            f.write(f"Final Train Accuracy: {training_history['train_acc'][-1]:.2f}%\n")
            f.write(f"Final Val Accuracy: {training_history['val_acc'][-1]:.2f}%\n")
            f.write(f"Best Val Accuracy: {max(training_history['val_acc']):.2f}%\n\n")

            f.write("TEST RESULTS\n")
            f.write("-" * 70 + "\n")
            test_acc = evaluation_results['test_accuracy']
            f.write(f"Test Accuracy: {test_acc:.2f}%\n")
            f.write(f"Test Loss: {evaluation_results['test_loss']:.4f}\n\n")

            f.write("PERFORMANCE COMPARISON\n")
            f.write("-" * 70 + "\n")
            improvement = test_acc - self.BASELINE_ACCURACY
            f.write(f"Improvement over C-MFN: {improvement:+.2f}%\n")
            f.write(f"Gap to Human Performance: {self.HUMAN_PERFORMANCE - test_acc:.2f}%\n")
            f.write(f"% of Human Performance: {(test_acc / self.HUMAN_PERFORMANCE) * 100:.1f}%\n\n")

            f.write("SUCCESS CRITERIA\n")
            f.write("-" * 70 + "\n")
            if test_acc >= self.BASELINE_ACCURACY:
                f.write(f"✅ SUCCESS: Model beat the C-MFN baseline!\n")
                f.write(f"   Target: {self.BASELINE_ACCURACY:.2f}%\n")
                f.write(f"   Achieved: {test_acc:.2f}%\n")
                f.write(f"   Improvement: {improvement:+.2f}%\n")
            else:
                f.write(f"❌ BELOW BASELINE: Model is {self.BASELINE_ACCURACY - test_acc:.2f}% below C-MFN baseline\n")
                f.write(f"   Target: {self.BASELINE_ACCURACY:.2f}%\n")
                f.write(f"   Achieved: {test_acc:.2f}%\n")
                f.write(f"   Gap: {self.BASELINE_ACCURACY - test_acc:.2f}%\n")

            f.write("\n" + "="*70 + "\n")

        print(f"\nReports saved to:")
        print(f"  JSON: {report_path}")
        print(f"  Summary: {summary_path}")

        return str(summary_path)

    def run_full_evaluation(self, num_epochs: int = 20) -> Dict[str, Any]:
        """
        Run complete UR-FUNNY TED evaluation pipeline.

        Args:
            num_epochs: Maximum number of training epochs

        Returns:
            Complete evaluation results
        """
        print("\n" + "="*70)
        print("UR-FUNNY TED BENCHMARK EVALUATION")
        print("="*70)
        print(f"Target: Beat or match {self.BASELINE_ACCURACY}% C-MFN baseline")
        print(f"Model: {self.model_type}")
        print(f"Device: {self.device}")
        print("="*70)

        try:
            # 1. Load dataset
            dataloaders = self.load_dataset()

            # 2. Create model
            model = self.create_model()

            # 3. Train model
            training_history = self.train_model(model, dataloaders, num_epochs)

            # 4. Evaluate on test set
            evaluation_results = self.evaluate_model(model, dataloaders['test'])

            # 5. Generate report
            report_path = self.generate_detailed_report(
                model, evaluation_results, training_history
            )

            print("\n" + "="*70)
            print("EVALUATION COMPLETE")
            print("="*70)
            print(f"Report saved to: {report_path}")

            return {
                'model': model,
                'training_history': training_history,
                'evaluation_results': evaluation_results,
                'report_path': report_path
            }

        except Exception as e:
            print(f"\n❌ Evaluation failed with error: {e}")
            raise


def main():
    """Main function to run UR-FUNNY TED benchmark evaluation"""
    parser = argparse.ArgumentParser(description='UR-FUNNY TED Benchmark Evaluation')
    parser.add_argument('--data_path', type=str, required=True,
                       help='Path to UR-FUNNY TED dataset')
    parser.add_argument('--output_dir', type=str, default='./ur_funny_ted_results',
                       help='Directory to save results')
    parser.add_argument('--model_type', type=str, default='early_fusion',
                       choices=['early_fusion', 'late_fusion', 'attention'],
                       help='Model architecture type')
    parser.add_argument('--num_epochs', type=int, default=20,
                       help='Maximum number of training epochs')
    parser.add_argument('--device', type=str, default='cuda',
                       help='Device to run evaluation on')

    args = parser.parse_args()

    # Create evaluator
    evaluator = URFunnyTEDEvaluator(
        data_path=args.data_path,
        output_dir=args.output_dir,
        model_type=args.model_type,
        device=args.device
    )

    # Run evaluation
    results = evaluator.run_full_evaluation(num_epochs=args.num_epochs)

    print("\n✅ UR-FUNNY TED benchmark evaluation completed successfully!")
    print(f"Results saved to: {args.output_dir}")


if __name__ == "__main__":
    main()