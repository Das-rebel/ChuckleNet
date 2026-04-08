"""
SCRIPTS Stand-Up Comedy Benchmark - Standalone Implementation

Agent 7: SCRIPTS Benchmark Implementation
Text-only stand-up humor detection from comedy scripts.

This standalone version avoids torchaudio dependency issues.
"""

import os
import json
import random
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from collections import defaultdict
from datetime import datetime

import torch
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, BertForSequenceClassification
from torch.optim import AdamW
from sklearn.metrics import accuracy_score, precision_recall_fscore_support


@dataclass
class ComedyScriptSample:
    """Sample from comedy script with setup/punchline structure"""
    setup: str
    punchline: str
    context: str  # Preceding text for context
    label: int  # 1 if laughter follows, 0 otherwise
    comedian_id: str
    script_id: str
    metadata: Dict[str, Any]


@dataclass
class DataSample:
    """Unified data sample format"""
    text: str
    label: int
    speaker_id: str  # Comedian ID
    show_id: str  # Script ID
    metadata: Dict[str, Any]


class SCRIPTSStandUpDataset:
    """
    SCRIPTS Stand-Up Comedy Dataset

    Converts comedy transcripts into text-only SCRIPTS format
    for humor detection benchmark evaluation.
    """

    def __init__(self,
                 data_path: str,
                 split: str = 'train',
                 context_window: int = 3,
                 random_seed: int = 42):
        """
        Initialize SCRIPTS Stand-Up dataset

        Args:
            data_path: Path to raw comedy transcripts
            split: train/val/test split
            context_window: Number of previous lines to include as context
            random_seed: Random seed for reproducibility
        """
        self.data_path = Path(data_path)
        self.split = split
        self.context_window = context_window
        self.random_seed = random_seed
        self.samples = []

        # Set random seed
        random.seed(random_seed)
        np.random.seed(random_seed)

        # Load data
        self._load_data()

    def _load_data(self):
        """Load and process comedy transcripts into SCRIPTS format"""
        data_path = self.data_path

        # Find all comedy transcript files
        transcript_files = list(data_path.glob("comedy_transcript_*.txt"))
        # Filter out laughter annotation files
        transcript_files = [f for f in transcript_files if "laughter" not in f.name]
        transcript_files.sort()

        print(f"Found {len(transcript_files)} comedy transcript files")

        if len(transcript_files) == 0:
            print("WARNING: No transcript files found!")
            return

        # Process each transcript into setup/punchline format
        all_samples = []

        for transcript_file in transcript_files:
            try:
                # Load transcript and laughter annotations
                laughter_file = transcript_file.parent / f"{transcript_file.stem}_laughter.json"

                if not laughter_file.exists():
                    continue

                # Read transcript
                with open(transcript_file, 'r', encoding='utf-8') as f:
                    transcript_lines = f.readlines()

                # Read laughter annotations
                with open(laughter_file, 'r', encoding='utf-8') as f:
                    laughter_data = json.load(f)

                # Extract comedian info from filename
                script_id = transcript_file.stem
                comedian_id = f"comedian_{script_id.split('_')[-1]}"

                # Process into setup/punchline format
                script_samples = self._process_script_to_samples(
                    transcript_lines,
                    laughter_data,
                    comedian_id,
                    script_id
                )

                all_samples.extend(script_samples)

            except Exception as e:
                print(f"Warning: Failed to process {transcript_file}: {e}")
                continue

        print(f"Processed {len(all_samples)} setup/punchline samples from {len(transcript_files)} scripts")

        # Create comedian-independent splits
        self.samples = self._create_comedian_independent_splits(all_samples)

        print(f"Loaded {len(self.samples)} samples for {self.split} split")

    def _process_script_to_samples(self,
                                   transcript_lines: List[str],
                                   laughter_data: Dict,
                                   comedian_id: str,
                                   script_id: str) -> List[ComedyScriptSample]:
        """
        Process transcript into setup/punchline samples

        Args:
            transcript_lines: Lines from transcript
            laughter_data: Laughter annotation data
            comedian_id: Comedian identifier
            script_id: Script identifier

        Returns:
            List of ComedyScriptSample objects
        """
        samples = []

        # Parse transcript into structured format
        parsed_lines = []
        laugh_indicators = set()

        for line in transcript_lines:
            line = line.strip()
            if not line:
                continue

            # Check if this is a laughter indicator
            if line.startswith('[') and line.endswith(']'):
                laugh_type = line[1:-1].lower()
                if 'laugh' in laugh_type or 'chuckle' in laugh_type:
                    laugh_indicators.add(len(parsed_lines))
                continue

            # Regular dialogue line
            parsed_lines.append(line)

        # Create setup/punchline pairs
        for i in range(len(parsed_lines)):
            # Current line is potential punchline
            punchline = parsed_lines[i]

            # Get context (previous lines)
            context_start = max(0, i - self.context_window)
            context_lines = parsed_lines[context_start:i]
            setup = ' '.join(context_lines) if context_lines else ""
            context = ' '.join(context_lines[-self.context_window:]) if context_lines else ""

            # Determine label based on laughter after this line
            # Check if laughter indicator follows this line
            label = 1 if i in laugh_indicators else 0

            # Create sample
            sample = ComedyScriptSample(
                setup=setup,
                punchline=punchline,
                context=context,
                label=label,
                comedian_id=comedian_id,
                script_id=script_id,
                metadata={
                    'line_number': i,
                    'total_lines': len(parsed_lines),
                    'dataset': 'SCRIPTS_StandUp',
                    'has_context': len(context_lines) > 0
                }
            )

            samples.append(sample)

        return samples

    def _create_comedian_independent_splits(self,
                                           all_samples: List[ComedyScriptSample]) -> List[DataSample]:
        """
        Create comedian-independent train/val/test splits

        Ensures no comedian appears in multiple splits to test true generalization.

        Args:
            all_samples: All samples from all comedians

        Returns:
            Filtered samples for the current split
        """
        # Group samples by comedian
        comedian_samples = defaultdict(list)
        for sample in all_samples:
            comedian_samples[sample.comedian_id].append(sample)

        # Get unique comedians
        comedian_ids = list(comedian_samples.keys())
        random.shuffle(comedian_ids)

        # Split comedians (not samples) into train/val/test
        # 70% train, 15% val, 15% test
        n_comedians = len(comedian_ids)

        # Ensure at least 1 comedian per split
        if n_comedians < 3:
            # If we have very few comedians, adjust split ratios
            n_train = max(1, n_comedians - 2)
            n_val = 1 if n_comedians >= 2 else 0
            # Test gets the rest
        else:
            n_train = int(0.7 * n_comedians)
            n_val = int(0.15 * n_comedians)
            n_val = max(1, n_val)  # Ensure at least 1

        train_comedians = set(comedian_ids[:n_train])
        val_comedians = set(comedian_ids[n_train:n_train + n_val])
        test_comedians = set(comedian_ids[n_train + n_val:])

        # Select samples based on split
        if self.split == 'train':
            selected_comedians = train_comedians
        elif self.split == 'val':
            selected_comedians = val_comedians
        elif self.split == 'test':
            selected_comedians = test_comedians
        else:
            raise ValueError(f"Unknown split: {self.split}")

        # Filter and convert to DataSample format
        split_samples = []
        for sample in all_samples:
            if sample.comedian_id in selected_comedians:
                # Create combined text (setup + punchline)
                combined_text = f"{sample.context} {sample.punchline}".strip()

                data_sample = DataSample(
                    text=combined_text,
                    label=sample.label,
                    speaker_id=sample.comedian_id,
                    show_id=sample.script_id,
                    metadata={
                        **sample.metadata,
                        'setup': sample.setup,
                        'punchline': sample.punchline,
                        'context': sample.context
                    }
                )
                split_samples.append(data_sample)

        print(f"Created {self.split} split with {len(selected_comedians)} comedians, {len(split_samples)} samples")

        return split_samples

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        return self.samples[idx]


class SCRIPTSDatasetWrapper(Dataset):
    """PyTorch Dataset wrapper for SCRIPTS data"""

    def __init__(self, scripts_dataset, tokenizer, max_length=512):
        self.dataset = scripts_dataset
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.dataset.samples)

    def __getitem__(self, idx):
        sample = self.dataset.samples[idx]

        # Get setup and punchline from metadata
        setup = sample.metadata.get('setup', '')
        punchline = sample.metadata.get('punchline', sample.text)

        # Format as setup/punchline pair
        if setup:
            text = f"Setup: {setup} Punchline: {punchline}"
        else:
            text = punchline

        # Tokenize
        encoding = self.tokenizer(
            text,
            max_length=self.max_length,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )

        return {
            'input_ids': encoding['input_ids'].squeeze(0),
            'attention_mask': encoding['attention_mask'].squeeze(0),
            'label': torch.tensor(sample.label, dtype=torch.long)
        }


class SCRIPTSEvaluator:
    """
    Evaluator for SCRIPTS Stand-Up benchmark

    Handles model training, evaluation, and comparison to baseline.
    """

    def __init__(self,
                 model_name: str = 'bert-base-uncased',
                 device: str = 'cuda' if torch.cuda.is_available() else 'cpu'):
        """
        Initialize SCRIPTS evaluator

        Args:
            model_name: Pretrained model to use
            device: Device to run on
        """
        self.device = device
        self.model_name = model_name
        print(f"Loading model: {model_name}")

        self.model = BertForSequenceClassification.from_pretrained(
            model_name,
            num_labels=2
        ).to(device)

        self.tokenizer = AutoTokenizer.from_pretrained(model_name)

    def create_dataloader(self,
                         dataset: SCRIPTSStandUpDataset,
                         batch_size: int = 16,
                         shuffle: bool = True) -> DataLoader:
        """Create DataLoader for SCRIPTS dataset"""
        wrapped_dataset = SCRIPTSDatasetWrapper(
            dataset, self.tokenizer, max_length=512
        )

        return DataLoader(
            wrapped_dataset,
            batch_size=batch_size,
            shuffle=shuffle,
            num_workers=0
        )

    def train(self,
             train_dataset: SCRIPTSStandUpDataset,
             val_dataset: SCRIPTSStandUpDataset,
             num_epochs: int = 1,  # Reduce to 1 for faster testing
             learning_rate: float = 2e-5,
             batch_size: int = 16):
        """
        Train model on SCRIPTS data

        Args:
            train_dataset: Training dataset
            val_dataset: Validation dataset
            num_epochs: Number of training epochs
            learning_rate: Learning rate
            batch_size: Batch size
        """
        # Create dataloaders
        train_loader = self.create_dataloader(
            train_dataset, batch_size=batch_size, shuffle=True
        )
        val_loader = self.create_dataloader(
            val_dataset, batch_size=batch_size, shuffle=False
        )

        # Setup optimizer
        optimizer = AdamW(self.model.parameters(), lr=learning_rate)

        # Training loop
        best_val_acc = 0.0

        for epoch in range(num_epochs):
            # Training
            self.model.train()
            train_loss = 0.0

            for batch_idx, batch in enumerate(train_loader):
                # Move to device
                input_ids = batch['input_ids'].to(self.device)
                attention_mask = batch['attention_mask'].to(self.device)
                labels = batch['label'].to(self.device)

                # Forward pass
                outputs = self.model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    labels=labels
                )

                loss = outputs.loss
                train_loss += loss.item()

                # Backward pass
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

                # Print progress every 10 batches
                if (batch_idx + 1) % 10 == 0:
                    print(f"  Batch {batch_idx + 1}/{len(train_loader)}, Loss: {loss.item():.4f}")

            avg_train_loss = train_loss / len(train_loader)

            # Validation
            val_acc, val_f1 = self.evaluate(val_loader)

            print(f"Epoch {epoch + 1}/{num_epochs}")
            print(f"  Train Loss: {avg_train_loss:.4f}")
            print(f"  Val Acc: {val_acc:.4f}")
            print(f"  Val F1: {val_f1:.4f}")

            # Save best model
            if val_acc > best_val_acc:
                best_val_acc = val_acc
                print(f"  New best validation accuracy: {best_val_acc:.4f}")

        print(f"Training complete. Best val acc: {best_val_acc:.4f}")

    def evaluate(self, dataloader: DataLoader) -> Tuple[float, float, float, float]:
        """
        Evaluate model on dataset

        Args:
            dataloader: DataLoader to evaluate on

        Returns:
            Tuple of (accuracy, precision, recall, f1)
        """
        self.model.eval()

        all_preds = []
        all_labels = []

        with torch.no_grad():
            for batch in dataloader:
                # Move to device
                input_ids = batch['input_ids'].to(self.device)
                attention_mask = batch['attention_mask'].to(self.device)
                labels = batch['label'].to(self.device)

                # Forward pass
                outputs = self.model(
                    input_ids=input_ids,
                    attention_mask=attention_mask
                )

                # Get predictions
                preds = torch.argmax(outputs.logits, dim=1)

                all_preds.extend(preds.cpu().numpy())
                all_labels.extend(labels.cpu().numpy())

        # Calculate metrics
        accuracy = accuracy_score(all_labels, all_preds)
        precision, recall, f1, _ = precision_recall_fscore_support(
            all_labels, all_preds, average='binary'
        )

        return accuracy, precision, recall, f1

    def evaluate_benchmark(self,
                          train_dataset: SCRIPTSStandUpDataset,
                          val_dataset: SCRIPTSStandUpDataset,
                          test_dataset: SCRIPTSStandUpDataset) -> Dict[str, Any]:
        """
        Full benchmark evaluation

        Args:
            train_dataset: Training dataset
            val_dataset: Validation dataset
            test_dataset: Test dataset

        Returns:
            Dictionary with evaluation results
        """
        print("=" * 60)
        print("SCRIPTS Stand-Up Comedy Benchmark Evaluation")
        print("=" * 60)

        # Train model
        print("\nTraining model (1 epoch for faster evaluation)...")
        self.train(train_dataset, val_dataset, num_epochs=1)

        # Evaluate on test set
        print("\nEvaluating on test set...")
        test_loader = self.create_dataloader(
            test_dataset, batch_size=16, shuffle=False
        )

        accuracy, precision, recall, f1 = self.evaluate(test_loader)

        # Compare to baseline
        baseline_accuracy = 0.684  # ~68.4% from literature

        print("\n" + "=" * 60)
        print("Test Results:")
        print("=" * 60)
        print(f"Accuracy: {accuracy:.4f} ({accuracy*100:.2f}%)")
        print(f"Precision: {precision:.4f}")
        print(f"Recall: {recall:.4f}")
        print(f"F1 Score: {f1:.4f}")
        print(f"\nBaseline: {baseline_accuracy:.4f} ({baseline_accuracy*100:.2f}%)")
        print(f"Improvement: {accuracy - baseline_accuracy:+.4f} ({(accuracy - baseline_accuracy)*100:+.2f}%)")
        print("=" * 60)

        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'baseline_accuracy': baseline_accuracy,
            'improvement': accuracy - baseline_accuracy
        }


def create_scripts_benchmark(data_path: str) -> Tuple[SCRIPTSStandUpDataset, SCRIPTSStandUpDataset, SCRIPTSStandUpDataset]:
    """
    Create SCRIPTS benchmark datasets

    Args:
        data_path: Path to raw comedy transcripts

    Returns:
        Tuple of (train_dataset, val_dataset, test_dataset)
    """
    print("Creating SCRIPTS Stand-Up Comedy Benchmark...")
    print(f"Data path: {data_path}")

    # Create datasets with comedian-independent splits
    train_dataset = SCRIPTSStandUpDataset(
        data_path=data_path,
        split='train',
        context_window=3
    )

    val_dataset = SCRIPTSStandUpDataset(
        data_path=data_path,
        split='val',
        context_window=3
    )

    test_dataset = SCRIPTSStandUpDataset(
        data_path=data_path,
        split='test',
        context_window=3
    )

    print("\nDataset statistics:")
    print(f"Train: {len(train_dataset.samples)} samples")
    print(f"Val: {len(val_dataset.samples)} samples")
    print(f"Test: {len(test_dataset.samples)} samples")

    # Get comedian statistics
    train_comedians = set(s.speaker_id for s in train_dataset.samples)
    val_comedians = set(s.speaker_id for s in val_dataset.samples)
    test_comedians = set(s.speaker_id for s in test_dataset.samples)

    print(f"\nComedian-independent splits:")
    print(f"Train comedians: {len(train_comedians)}")
    print(f"Val comedians: {len(val_comedians)}")
    print(f"Test comedians: {len(test_comedians)}")

    # Verify no overlap
    overlap_train_val = train_comedians & val_comedians
    overlap_train_test = train_comedians & test_comedians
    overlap_val_test = val_comedians & test_comedians

    if overlap_train_val or overlap_train_test or overlap_val_test:
        print("WARNING: Comedian overlap detected between splits!")
        print(f"Train-Val overlap: {len(overlap_train_val)}")
        print(f"Train-Test overlap: {len(overlap_train_test)}")
        print(f"Val-Test overlap: {len(overlap_val_test)}")
    else:
        print("✓ Comedian-independent splits verified")

    return train_dataset, val_dataset, test_dataset


def main():
    """Main execution function for SCRIPTS benchmark"""

    print("=" * 80)
    print("SCRIPTS STAND-UP COMEDY BENCHMARK - AGENT 7")
    print("=" * 80)
    print("Text-only stand-up humor detection from comedy scripts")
    print("Objective: Compare against ~68.4% baseline accuracy")
    print("=" * 80)

    # Configuration
    data_path = "/Users/Subho/autonomous_laughter_prediction/data/raw"
    results_dir = "/Users/Subho/autonomous_laughter_prediction/benchmarks/results"
    model_name = 'bert-base-uncased'

    # Create results directory
    Path(results_dir).mkdir(parents=True, exist_ok=True)

    # Set random seeds for reproducibility
    torch.manual_seed(42)
    np.random.seed(42)

    try:
        # Step 1: Create SCRIPTS benchmark datasets
        print("\n[Step 1/4] Creating SCRIPTS benchmark datasets...")
        train_dataset, val_dataset, test_dataset = create_scripts_benchmark(data_path)

        if len(train_dataset.samples) == 0:
            print("ERROR: No training samples loaded!")
            return None

        # Step 2: Analyze dataset statistics
        print("\n[Step 2/4] Analyzing dataset statistics...")

        # Label distribution
        train_labels = [s.label for s in train_dataset.samples]
        val_labels = [s.label for s in val_dataset.samples]
        test_labels = [s.label for s in test_dataset.samples]

        print("\nLabel Distribution:")
        print(f"Train - Positive: {sum(train_labels)}/{len(train_labels)} ({sum(train_labels)/len(train_labels)*100:.1f}%)")
        if len(val_labels) > 0:
            print(f"Val - Positive: {sum(val_labels)}/{len(val_labels)} ({sum(val_labels)/len(val_labels)*100:.1f}%)")
        else:
            print(f"Val - No samples available")
        print(f"Test - Positive: {sum(test_labels)}/{len(test_labels)} ({sum(test_labels)/len(test_labels)*100:.1f}%)")

        # Sample analysis
        print("\nSample Analysis:")
        print(f"Average text length (train): {np.mean([len(s.text.split()) for s in train_dataset.samples]):.1f} words")
        print(f"Max text length (train): {max([len(s.text.split()) for s in train_dataset.samples])} words")

        # Show example samples
        print("\nExample samples from training set:")
        for i, sample in enumerate(train_dataset.samples[:3]):
            print(f"\nSample {i+1} (Label: {sample.label}):")
            print(f"  Setup: {sample.metadata.get('setup', 'N/A')[:100]}...")
            print(f"  Punchline: {sample.metadata.get('punchline', 'N/A')[:100]}...")

        # Step 3: Initialize evaluator
        print("\n[Step 3/4] Initializing SCRIPTS evaluator...")
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print(f"Using device: {device}")

        evaluator = SCRIPTSEvaluator(
            model_name=model_name,
            device=device
        )

        # Step 4: Run benchmark evaluation
        print("\n[Step 4/4] Running benchmark evaluation...")

        # Use training set for validation if val set is empty
        val_set = val_dataset if len(val_dataset.samples) > 0 else train_dataset
        if len(val_dataset.samples) == 0:
            print("Note: Using training set for validation (no dedicated validation set)")

        results = evaluator.evaluate_benchmark(
            train_dataset,
            val_set,
            test_dataset
        )

        # Generate comprehensive report
        print("\n" + "=" * 80)
        print("BENCHMARK RESULTS SUMMARY")
        print("=" * 80)

        # Format results
        test_comedians = set(s.speaker_id for s in test_dataset.samples)

        report = {
            'benchmark': 'SCRIPTS Stand-Up Comedy',
            'task': 'Text-only humor detection from comedy scripts',
            'timestamp': datetime.now().isoformat(),
            'model': model_name,
            'device': device,
            'dataset_stats': {
                'train_samples': len(train_dataset.samples),
                'val_samples': len(val_dataset.samples),
                'test_samples': len(test_dataset.samples),
                'total_comedians': len(set(s.speaker_id for s in train_dataset.samples +
                                         val_dataset.samples +
                                         test_dataset.samples)),
                'train_comedians': len(set(s.speaker_id for s in train_dataset.samples)),
                'test_comedians': len(test_comedians)
            },
            'label_distribution': {
                'train_positive_ratio': sum(train_labels)/len(train_labels),
                'test_positive_ratio': sum(test_labels)/len(test_labels)
            },
            'results': {
                'test_accuracy': float(results['accuracy']),
                'test_precision': float(results['precision']),
                'test_recall': float(results['recall']),
                'test_f1': float(results['f1']),
                'baseline_accuracy': results['baseline_accuracy'],
                'improvement': float(results['improvement'])
            },
            'comparison': {
                'meets_baseline': results['accuracy'] >= results['baseline_accuracy'],
                'improvement_percentage': float(results['improvement'] * 100),
                'performance_category': categorize_performance(results['accuracy'])
            },
            'cross_comedian_analysis': {
                'num_test_comedians': len(test_comedians),
                'unseen_comedians': len(test_comedians),
                'generalization_type': 'comedian-independent'
            }
        }

        # Save results
        results_file = Path(results_dir) / f"scripts_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\nResults saved to: {results_file}")

        # Print formatted summary
        print("\n" + "=" * 80)
        print("FINAL RESULTS")
        print("=" * 80)
        print(f"Benchmark: {report['benchmark']}")
        print(f"Task: {report['task']}")
        print(f"\nDataset Statistics:")
        print(f"  Total Samples: {report['dataset_stats']['train_samples'] + report['dataset_stats']['test_samples']}")
        print(f"  Train Samples: {report['dataset_stats']['train_samples']}")
        print(f"  Test Samples: {report['dataset_stats']['test_samples']}")
        print(f"  Total Comedians: {report['dataset_stats']['total_comedians']}")
        print(f"  Test Comedians (Unseen): {report['dataset_stats']['test_comedians']}")
        print(f"\nTest Performance:")
        print(f"  Accuracy: {report['results']['test_accuracy']:.4f} ({report['results']['test_accuracy']*100:.2f}%)")
        print(f"  Precision: {report['results']['test_precision']:.4f}")
        print(f"  Recall: {report['results']['test_recall']:.4f}")
        print(f"  F1 Score: {report['results']['test_f1']:.4f}")
        print(f"\nBaseline Comparison:")
        print(f"  Baseline Accuracy: {report['results']['baseline_accuracy']*100:.2f}%")
        print(f"  Our Accuracy: {report['results']['test_accuracy']*100:.2f}%")
        print(f"  Improvement: {report['results']['improvement']*100:+.2f}%")
        print(f"  Meets Baseline: {report['comparison']['meets_baseline']}")
        print(f"  Performance Category: {report['comparison']['performance_category']}")
        print(f"\nCross-Comedian Generalization:")
        print(f"  Generalization Type: {report['cross_comedian_analysis']['generalization_type']}")
        print(f"  Test Comedians: {report['cross_comedian_analysis']['num_test_comedians']}")
        print("=" * 80)

        print("\n✓ SCRIPTS benchmark evaluation complete!")

        return report

    except Exception as e:
        print(f"\nERROR during benchmark execution: {e}")
        import traceback
        traceback.print_exc()
        return None


def categorize_performance(accuracy: float) -> str:
    """Categorize performance level"""
    if accuracy >= 0.75:
        return "Excellent"
    elif accuracy >= 0.70:
        return "Good"
    elif accuracy >= 0.68:
        return "Acceptable (meets baseline)"
    elif accuracy >= 0.65:
        return "Below baseline"
    else:
        return "Poor"


if __name__ == "__main__":
    report = main()

    if report:
        print("\n🎉 SCRIPTS benchmark completed successfully!")
        print(f"Final accuracy: {report['results']['test_accuracy']*100:.2f}%")
        if report['comparison']['meets_baseline']:
            print("✓ Meets or exceeds baseline performance!")
        else:
            print("⚠ Below baseline - further optimization needed")
    else:
        print("\n❌ Benchmark execution failed")