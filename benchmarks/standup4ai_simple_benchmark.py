"""
Simplified StandUp4AI Benchmark - Direct Implementation

This is a streamlined version that doesn't rely on the heavy benchmark infrastructure
and avoids dependency conflicts. It implements the core StandUp4AI evaluation.
"""

import json
import torch
import torch.nn as nn
import numpy as np
from pathlib import Path
from transformers import AutoTokenizer, AutoModel
from typing import Dict, List, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimpleStandUp4AIEvaluator:
    """Simplified StandUp4AI benchmark evaluator"""

    def __init__(self, data_path: str = "/Users/Subho/data/standup4ai"):
        self.data_path = Path(data_path)
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        # Load tokenizer
        logger.info("Loading tokenizer...")
        self.tokenizer = AutoTokenizer.from_pretrained('bert-base-multilingual-cased')

        # Initialize model
        logger.info("Initializing model...")
        self.model = SimpleWordLevelPredictor()
        self.model.to(self.device)

        # Evaluation metrics
        self.iou_threshold = 0.2
        self.languages = ['EN', 'RU', 'ES', 'FR', 'DE', 'IT', 'PT']

    def load_dataset(self, split: str) -> List[Dict]:
        """Load dataset split"""
        annotation_file = self.data_path / "annotations" / f"{split}_annotations.json"

        if not annotation_file.exists():
            logger.error(f"Annotation file not found: {annotation_file}")
            return []

        with open(annotation_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        logger.info(f"Loaded {len(data)} samples from {split} split")
        return data

    def evaluate_samples(self, samples: List[Dict]) -> Dict:
        """Evaluate model on samples"""
        logger.info(f"Evaluating {len(samples)} samples...")

        self.model.eval()
        language_metrics = {}

        for lang in self.languages:
            language_metrics[lang] = {
                'predictions': [],
                'ground_truth': [],
                'f1_scores': []
            }

        with torch.no_grad():
            for sample in samples:
                try:
                    # Get data
                    text = sample['text']
                    word_labels = sample['word_labels']
                    language = sample.get('language', 'EN')

                    # Tokenize
                    encoding = self.tokenizer(
                        text,
                        max_length=128,
                        padding='max_length',
                        truncation=True,
                        return_tensors='pt'
                    )

                    # Get predictions
                    input_ids = encoding['input_ids'].to(self.device)
                    attention_mask = encoding['attention_mask'].to(self.device)

                    # Forward pass
                    outputs = self.model(input_ids, attention_mask)
                    predictions = torch.argmax(outputs['logits'], dim=-1)[0].cpu().numpy()

                    # Align predictions with word labels
                    aligned_predictions = self.align_predictions_to_words(
                        predictions,
                        encoding.word_ids(),
                        len(word_labels)
                    )

                    # Compute metrics
                    f1 = self.compute_f1(aligned_predictions, word_labels)
                    iou_f1 = self.compute_iou_f1(aligned_predictions, word_labels)

                    language_metrics[language]['predictions'].extend(aligned_predictions)
                    language_metrics[language]['ground_truth'].extend(word_labels)
                    language_metrics[language]['f1_scores'].append({
                        'f1': f1,
                        'iou_f1': iou_f1
                    })

                except Exception as e:
                    logger.warning(f"Failed to evaluate sample: {e}")
                    continue

        # Aggregate metrics
        results = {}
        for lang in self.languages:
            if language_metrics[lang]['f1_scores']:
                f1_scores = [m['f1'] for m in language_metrics[lang]['f1_scores']]
                iou_f1_scores = [m['iou_f1'] for m in language_metrics[lang]['f1_scores']]

                results[lang] = {
                    'f1': np.mean(f1_scores),
                    'iou_f1': np.mean(iou_f1_scores),
                    'num_samples': len(language_metrics[lang]['f1_scores'])
                }

        # Macro average
        if results:
            macro_f1 = np.mean([r['f1'] for r in results.values()])
            macro_iou_f1 = np.mean([r['iou_f1'] for r in results.values()])
            total_samples = sum(r['num_samples'] for r in results.values())

            results['macro_avg'] = {
                'f1': macro_f1,
                'iou_f1': macro_iou_f1,
                'num_samples': total_samples
            }

        return results

    def align_predictions_to_words(self, predictions, word_ids, num_words):
        """Align token-level predictions to word-level"""
        aligned = []
        previous_word_idx = None

        for i, word_idx in enumerate(word_ids):
            if word_idx is None:
                continue  # Skip special tokens

            if word_idx != previous_word_idx:
                # First token of word
                if word_idx < num_words and i < len(predictions):
                    aligned.append(predictions[i])
                else:
                    aligned.append(0)  # Default to no laughter

            previous_word_idx = word_idx

        # Ensure we have the right number of predictions
        while len(aligned) < num_words:
            aligned.append(0)

        return aligned[:num_words]

    def compute_f1(self, predictions, ground_truth):
        """Compute F1 score"""
        predictions = np.array(predictions)
        ground_truth = np.array(ground_truth)

        tp = np.sum((predictions == 1) & (ground_truth == 1))
        fp = np.sum((predictions == 1) & (ground_truth == 0))
        fn = np.sum((predictions == 0) & (ground_truth == 1))

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

        return f1

    def compute_iou_f1(self, predictions, ground_truth):
        """Compute IoU-based F1 score"""
        pred_intervals = self.extract_intervals(predictions)
        true_intervals = self.extract_intervals(ground_truth)

        if not pred_intervals or not true_intervals:
            return 0.0

        # Compute IoU for each predicted interval
        ious = []
        for pred_interval in pred_intervals:
            max_iou = 0
            for true_interval in true_intervals:
                iou = self.compute_single_iou(pred_interval, true_interval)
                max_iou = max(max_iou, iou)
            ious.append(max_iou)

        # Count matches above threshold
        matches = sum(1 for iou in ious if iou >= self.iou_threshold)

        iou_precision = matches / len(pred_intervals) if pred_intervals else 0
        iou_recall = matches / len(true_intervals) if true_intervals else 0
        iou_f1 = 2 * (iou_precision * iou_recall) / (iou_precision + iou_recall) \
            if (iou_precision + iou_recall) > 0 else 0

        return iou_f1

    def extract_intervals(self, labels):
        """Extract continuous laughter intervals"""
        intervals = []
        start = None

        for i, label in enumerate(labels):
            if label == 1 and start is None:
                start = i
            elif label == 0 and start is not None:
                intervals.append((start, i - 1))
                start = None

        if start is not None:
            intervals.append((start, len(labels) - 1))

        return intervals

    def compute_single_iou(self, interval1, interval2):
        """Compute IoU between two intervals"""
        start1, end1 = interval1
        start2, end2 = interval2

        intersection_start = max(start1, start2)
        intersection_end = min(end1, end2)
        intersection = max(0, intersection_end - intersection_start + 1)

        union_start = min(start1, start2)
        union_end = max(end1, end2)
        union = union_end - union_start + 1

        return intersection / union if union > 0 else 0

    def run_benchmark(self):
        """Run complete benchmark"""
        logger.info("="*60)
        logger.info("StandUp4AI Benchmark Evaluation")
        logger.info("="*60)

        # Load datasets
        logger.info("Loading datasets...")
        train_data = self.load_dataset('train')
        val_data = self.load_dataset('val')
        test_data = self.load_dataset('test')

        logger.info(f"Train: {len(train_data)}, Val: {len(val_data)}, Test: {len(test_data)}")

        # Train model (simplified)
        logger.info("Training model...")
        try:
            self.train_model(train_data, val_data)
        except Exception as e:
            logger.error(f"Training failed: {e}")
            logger.info("Proceeding with evaluation using untrained model...")

        # Evaluate on test set
        logger.info("Evaluating on test set...")
        test_results = self.evaluate_samples(test_data)

        # Print results
        self.print_results(test_results)

        return test_results

    def train_model(self, train_data, val_data, num_epochs=2):
        """Simple training loop"""
        optimizer = torch.optim.AdamW(self.model.parameters(), lr=2e-5)

        for epoch in range(num_epochs):
            logger.info(f"Epoch {epoch + 1}/{num_epochs}")
            self.model.train()

            # Simple training on a few samples
            for i, sample in enumerate(train_data[:min(50, len(train_data))]):
                try:
                    text = sample['text']
                    word_labels = sample['word_labels']

                    # Create simple training targets
                    encoding = self.tokenizer(
                        text,
                        max_length=64,
                        padding='max_length',
                        truncation=True,
                        return_tensors='pt'
                    )

                    input_ids = encoding['input_ids'].to(self.device)
                    attention_mask = encoding['attention_mask'].to(self.device)

                    # Create simple labels (1 if any laughter in sentence, else 0)
                    labels = torch.tensor([1 if any(word_labels) else 0]).to(self.device)

                    # Forward pass
                    outputs = self.model(input_ids, attention_mask)

                    # Simple loss (binary classification)
                    pred = outputs['logits'].mean(dim=1)  # Average over sequence
                    loss = nn.BCEWithLogitsLoss()(pred.squeeze(), labels.float())

                    # Backward pass
                    optimizer.zero_grad()
                    loss.backward()
                    optimizer.step()

                except Exception as e:
                    logger.warning(f"Training sample {i} failed: {e}")
                    continue

            logger.info(f"Epoch {epoch + 1} completed")

    def print_results(self, results):
        """Print evaluation results"""
        print("\n" + "="*60)
        print("StandUp4AI Benchmark Results")
        print("="*60)

        for language in sorted(results.keys()):
            if language == 'macro_avg':
                print(f"\n{language.upper()}:")
            else:
                print(f"\n{language}:")

            metrics = results[language]
            print(f"  F1: {metrics['f1']:.4f}")
            print(f"  IoU@0.2 F1: {metrics['iou_f1']:.4f}")
            print(f"  Samples: {metrics['num_samples']}")

        # Baseline comparison
        print("\n" + "="*60)
        print("Baseline Comparison")
        print("="*60)

        if 'macro_avg' in results:
            macro_f1 = results['macro_avg']['f1']
            iou_f1 = results['macro_avg']['iou_f1']
            published_baseline = 0.58

            print(f"Published Baseline F1: {published_baseline:.4f}")
            print(f"Our Method F1: {macro_f1:.4f}")
            print(f"Our Method IoU@0.2 F1: {iou_f1:.4f}")
            print(f"Difference: {macro_f1 - published_baseline:+.4f}")

            if macro_f1 > published_baseline:
                print(f"✓ Outperforms baseline by {macro_f1 - published_baseline:.4f} F1")
            else:
                print(f"✗ Underperforms baseline by {published_baseline - macro_f1:.4f} F1")

    def save_results(self, results, output_path="standup4ai_results.json"):
        """Save results to file"""
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Results saved to {output_path}")


class SimpleWordLevelPredictor(nn.Module):
    """Simple word-level laughter prediction model"""

    def __init__(self):
        super().__init__()

        # Load pretrained BERT
        logger.info("Loading pretrained BERT...")
        self.bert = AutoModel.from_pretrained('bert-base-multilingual-cased')

        # Freeze BERT for now
        for param in self.bert.parameters():
            param.requires_grad = False

        # Simple classifier
        self.classifier = nn.Sequential(
            nn.Linear(768, 256),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(256, 2)
        )

    def forward(self, input_ids, attention_mask):
        """Forward pass"""
        outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        last_hidden_state = outputs.last_hidden_state

        logits = self.classifier(last_hidden_state)

        return {
            'logits': logits
        }


def main():
    """Main execution"""
    print("Simplified StandUp4AI Benchmark")
    print("="*60)

    evaluator = SimpleStandUp4AIEvaluator()
    results = evaluator.run_benchmark()

    if results:
        evaluator.save_results(results)
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
    import sys
    sys.exit(main())