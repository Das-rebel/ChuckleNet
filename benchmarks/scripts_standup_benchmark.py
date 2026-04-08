"""
SCRIPTS Stand-Up Comedy Benchmark Implementation

Agent 7: SCRIPTS Benchmark Implementation
Text-only stand-up humor detection from comedy scripts.

This implementation converts our 102 comedy transcripts into a SCRIPTS-format dataset
for text-only humor detection, simulating the published SCRIPTS benchmark with:
- 90+ comedy scripts from various comedians
- Setup/punchline format parsing
- Comedian-independent splits
- Context+punchline prediction
- Comparison to ~68.4% baseline
"""

import os
import json
import random
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from collections import defaultdict
import re

import torch
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, BertForSequenceClassification
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_recall_fscore_support

from benchmarks.utils.base_dataset import BaseBenchmarkDataset, DataSample


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


class SCRIPTSStandUpDataset(BaseBenchmarkDataset):
    """
    SCRIPTS Stand-Up Comedy Dataset

    Converts our 102 comedy transcripts into text-only SCRIPTS format
    for humor detection benchmark evaluation.
    """

    def __init__(self,
                 data_path: str,
                 split: str = 'train',
                 context_window: int = 3,
                 **kwargs):
        """
        Initialize SCRIPTS Stand-Up dataset

        Args:
            data_path: Path to raw comedy transcripts
            split: train/val/test split
            context_window: Number of previous lines to include as context
        """
        self.context_window = context_window
        super().__init__(data_path, split, **kwargs)

    def _load_data(self):
        """Load and process comedy transcripts into SCRIPTS format"""
        data_path = Path(self.data_path)

        # Find all comedy transcript files
        transcript_files = list(data_path.glob("comedy_*_transcript_*.txt"))
        transcript_files.sort()

        print(f"Found {len(transcript_files)} comedy transcript files")

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
        n_train = int(0.7 * n_comedians)
        n_val = int(0.15 * n_comedians)

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
                    audio_path=None,
                    video_path=None,
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


class SCRIPTSProcessor:
    """
    Processor for SCRIPTS Stand-Up benchmark evaluation

    Handles text preprocessing, tokenization, and model evaluation.
    """

    def __init__(self, model_name: str = 'bert-base-uncased'):
        """
        Initialize SCRIPTS processor

        Args:
            model_name: Pretrained model to use
        """
        self.model_name = model_name
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)

    def preprocess_sample(self, sample: DataSample, max_length: int = 512) -> Dict[str, torch.Tensor]:
        """
        Preprocess a single sample for model input

        Args:
            sample: DataSample to preprocess
            max_length: Maximum sequence length

        Returns:
            Dictionary with tokenized inputs
        """
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
            max_length=max_length,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )

        return {
            'input_ids': encoding['input_ids'].squeeze(0),
            'attention_mask': encoding['attention_mask'].squeeze(0),
            'label': torch.tensor(sample.label, dtype=torch.long)
        }

    def create_dataloader(self,
                         dataset: SCRIPTSStandUpDataset,
                         batch_size: int = 16,
                         shuffle: bool = True) -> DataLoader:
        """
        Create DataLoader for SCRIPTS dataset

        Args:
            dataset: SCRIPTS dataset
            batch_size: Batch size
            shuffle: Whether to shuffle data

        Returns:
            DataLoader instance
        """
        class SCRIPTSDatasetWrapper(Dataset):
            def __init__(self, scripts_dataset, processor):
                self.dataset = scripts_dataset
                self.processor = processor

            def __len__(self):
                return len(self.dataset.samples)

            def __getitem__(self, idx):
                sample = self.dataset.samples[idx]
                return self.processor.preprocess_sample(sample)

        wrapped_dataset = SCRIPTSDatasetWrapper(dataset, self)

        return DataLoader(
            wrapped_dataset,
            batch_size=batch_size,
            shuffle=shuffle,
            num_workers=0
        )


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
        self.model = BertForSequenceClassification.from_pretrained(
            model_name,
            num_labels=2
        ).to(device)
        self.processor = SCRIPTSProcessor(model_name)

    def train(self,
             train_dataset: SCRIPTSStandUpDataset,
             val_dataset: SCRIPTSStandUpDataset,
             num_epochs: int = 3,
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
        train_loader = self.processor.create_dataloader(
            train_dataset, batch_size=batch_size, shuffle=True
        )
        val_loader = self.processor.create_dataloader(
            val_dataset, batch_size=batch_size, shuffle=False
        )

        # Setup optimizer
        optimizer = torch.optim.AdamW(self.model.parameters(), lr=learning_rate)

        # Training loop
        best_val_acc = 0.0

        for epoch in range(num_epochs):
            # Training
            self.model.train()
            train_loss = 0.0

            for batch in train_loader:
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
        print("\nTraining model...")
        self.train(train_dataset, val_dataset)

        # Evaluate on test set
        print("\nEvaluating on test set...")
        test_loader = self.processor.create_dataloader(
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


if __name__ == "__main__":
    # Example usage
    data_path = "/Users/Subho/autonomous_laughter_prediction/data/raw"

    # Create benchmark datasets
    train_dataset, val_dataset, test_dataset = create_scripts_benchmark(data_path)

    # Run evaluation
    evaluator = SCRIPTSEvaluator()
    results = evaluator.evaluate_benchmark(train_dataset, val_dataset, test_dataset)

    print("\n✓ SCRIPTS Stand-Up Comedy Benchmark evaluation complete!")
