"""
SCRIPTS Stand-Up Comedy Benchmark - Fast Evaluation

Agent 7: Quick SCRIPTS benchmark evaluation without full training
"""

import os
import json
import random
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from collections import defaultdict
from datetime import datetime

import torch
from sklearn.metrics import accuracy_score, precision_recall_fscore_support


@dataclass
class DataSample:
    """Unified data sample format"""
    text: str
    label: int
    speaker_id: str  # Comedian ID
    show_id: str  # Script ID
    metadata: Dict[str, Any]


class SCRIPTSStandUpFast:
    """
    Fast SCRIPTS evaluation without model training
    Uses heuristics to establish baseline performance
    """

    def __init__(self, data_path: str, random_seed: int = 42):
        """Initialize fast SCRIPTS evaluator"""
        self.data_path = Path(data_path)
        self.random_seed = random_seed

        # Set random seeds
        random.seed(random_seed)
        np.random.seed(random_seed)

    def load_and_process_data(self) -> Tuple[List[DataSample], List[DataSample], List[DataSample]]:
        """Load and process comedy transcripts into SCRIPTS format"""
        data_path = self.data_path

        # Find all comedy transcript files
        transcript_files = list(data_path.glob("comedy_transcript_*.txt"))
        # Filter out laughter annotation files
        transcript_files = [f for f in transcript_files if "laughter" not in f.name]
        transcript_files.sort()

        print(f"Found {len(transcript_files)} comedy transcript files")

        if len(transcript_files) == 0:
            print("ERROR: No transcript files found!")
            return [], [], []

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
        train_samples, val_samples, test_samples = self._create_comedian_independent_splits(all_samples)

        return train_samples, val_samples, test_samples

    def _process_script_to_samples(self,
                                   transcript_lines: List[str],
                                   laughter_data: Dict,
                                   comedian_id: str,
                                   script_id: str) -> List[DataSample]:
        """Process transcript into setup/punchline samples"""
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
            punchline = parsed_lines[i]

            # Get context (previous lines)
            context_start = max(0, i - 3)
            context_lines = parsed_lines[context_start:i]
            setup = ' '.join(context_lines) if context_lines else ""
            context = ' '.join(context_lines[-3:]) if context_lines else ""

            # Determine label based on laughter after this line
            label = 1 if i in laugh_indicators else 0

            # Create combined text
            combined_text = f"{context} {punchline}".strip()

            data_sample = DataSample(
                text=combined_text,
                label=label,
                speaker_id=comedian_id,
                show_id=script_id,
                metadata={
                    'setup': setup,
                    'punchline': punchline,
                    'context': context,
                    'line_number': i,
                    'total_lines': len(parsed_lines),
                    'dataset': 'SCRIPTS_StandUp'
                }
            )

            samples.append(data_sample)

        return samples

    def _create_comedian_independent_splits(self, all_samples: List[DataSample]) -> Tuple[List[DataSample], List[DataSample], List[DataSample]]:
        """Create comedian-independent train/val/test splits"""
        # Group samples by comedian
        comedian_samples = defaultdict(list)
        for sample in all_samples:
            comedian_samples[sample.speaker_id].append(sample)

        # Get unique comedians
        comedian_ids = list(comedian_samples.keys())
        random.shuffle(comedian_ids)

        # Split comedians (not samples) into train/val/test
        n_comedians = len(comedian_ids)

        # Ensure at least 1 comedian per split
        if n_comedians < 3:
            n_train = max(1, n_comedians - 2)
            n_val = 1 if n_comedians >= 2 else 0
        else:
            n_train = int(0.7 * n_comedians)
            n_val = max(1, int(0.15 * n_comedians))

        train_comedians = set(comedian_ids[:n_train])
        val_comedians = set(comedian_ids[n_train:n_train + n_val])
        test_comedians = set(comedian_ids[n_train + n_val:])

        # Filter samples
        train_samples = [s for s in all_samples if s.speaker_id in train_comedians]
        val_samples = [s for s in all_samples if s.speaker_id in val_comedians]
        test_samples = [s for s in all_samples if s.speaker_id in test_comedians]

        print(f"Created comedian-independent splits:")
        print(f"  Train: {len(train_comedians)} comedians, {len(train_samples)} samples")
        print(f"  Val: {len(val_comedians)} comedians, {len(val_samples)} samples")
        print(f"  Test: {len(test_comedians)} comedians, {len(test_samples)} samples")

        return train_samples, val_samples, test_samples

    def heuristic_evaluation(self, test_samples: List[DataSample]) -> Dict[str, float]:
        """Run heuristic-based evaluation without model training"""
        print("\nRunning heuristic evaluation...")

        # Simple heuristic: predict based on text features
        predictions = []

        for sample in test_samples:
            text = sample.text.lower()

            # Simple heuristics for humor detection
            humor_indicators = [
                '!', '?', 'like', 'just', 'so', 'really', 'literally',
                'basically', 'actually', 'you know', 'i mean', 'wait',
                'but seriously', 'no but', 'i mean', 'okay so'
            ]

            setup_words = sample.metadata.get('setup', '').lower().split()
            punchline_words = sample.metadata.get('punchline', '').lower().split()

            # Heuristic 1: Punchline length vs setup
            setup_length = len(setup_words)
            punchline_length = len(punchline_words)

            # Heuristic 2: Presence of humor indicators
            humor_score = sum(1 for indicator in humor_indicators if indicator in text)

            # Heuristic 3: Question marks and exclamations
            humor_score += text.count('!') + text.count('?')

            # Make prediction
            if humor_score > 1 or punchline_length > setup_length:
                predictions.append(1)  # Predict humorous
            else:
                predictions.append(0)  # Predict not humorous

        # Calculate metrics
        true_labels = [s.label for s in test_samples]

        accuracy = accuracy_score(true_labels, predictions)
        precision, recall, f1, _ = precision_recall_fscore_support(
            true_labels, predictions, average='binary', zero_division=0
        )

        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1
        }

    def majority_baseline(self, test_samples: List[DataSample]) -> Dict[str, float]:
        """Calculate majority class baseline"""
        print("\nCalculating majority class baseline...")

        true_labels = [s.label for s in test_samples]
        majority_class = max(set(true_labels), key=true_labels.count)
        predictions = [majority_class] * len(true_labels)

        accuracy = accuracy_score(true_labels, predictions)
        precision, recall, f1, _ = precision_recall_fscore_support(
            true_labels, predictions, average='binary', zero_division=0
        )

        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'majority_class': majority_class
        }

    def run_evaluation(self) -> Dict[str, Any]:
        """Run complete SCRIPTS benchmark evaluation"""
        print("=" * 80)
        print("SCRIPTS STAND-UP COMEDY BENCHMARK - FAST EVALUATION")
        print("=" * 80)
        print("Text-only stand-up humor detection from comedy scripts")
        print("Objective: Establish baseline performance")
        print("=" * 80)

        # Load data
        print("\n[Step 1/3] Loading and processing data...")
        train_samples, val_samples, test_samples = self.load_and_process_data()

        if len(test_samples) == 0:
            print("ERROR: No test samples available!")
            return None

        # Analyze dataset statistics
        print("\n[Step 2/3] Analyzing dataset statistics...")

        train_labels = [s.label for s in train_samples]
        test_labels = [s.label for s in test_samples]

        print("\nLabel Distribution:")
        print(f"Train - Positive: {sum(train_labels)}/{len(train_labels)} ({sum(train_labels)/len(train_labels)*100:.1f}%)")
        print(f"Test - Positive: {sum(test_labels)}/{len(test_labels)} ({sum(test_labels)/len(test_labels)*100:.1f}%)")

        # Sample analysis
        print("\nSample Analysis:")
        print(f"Average text length (train): {np.mean([len(s.text.split()) for s in train_samples]):.1f} words")
        print(f"Max text length (train): {max([len(s.text.split()) for s in train_samples])} words")

        # Show example samples
        print("\nExample samples from test set:")
        for i, sample in enumerate(test_samples[:3]):
            print(f"\nSample {i+1} (Label: {sample.label}):")
            print(f"  Setup: {sample.metadata.get('setup', 'N/A')[:80]}...")
            print(f"  Punchline: {sample.metadata.get('punchline', 'N/A')[:80]}...")

        # Run evaluations
        print("\n[Step 3/3] Running evaluations...")

        # Majority baseline
        majority_results = self.majority_baseline(test_samples)

        # Heuristic evaluation
        heuristic_results = self.heuristic_evaluation(test_samples)

        # Compare to literature baseline
        baseline_accuracy = 0.684  # ~68.4% from literature

        # Generate report
        print("\n" + "=" * 80)
        print("BENCHMARK RESULTS SUMMARY")
        print("=" * 80)

        report = {
            'benchmark': 'SCRIPTS Stand-Up Comedy',
            'task': 'Text-only humor detection from comedy scripts',
            'timestamp': datetime.now().isoformat(),
            'evaluation_type': 'Fast heuristic evaluation',
            'dataset_stats': {
                'total_samples': len(train_samples) + len(test_samples),
                'train_samples': len(train_samples),
                'test_samples': len(test_samples),
                'total_comedians': len(set(s.speaker_id for s in train_samples + test_samples)),
                'test_comedians': len(set(s.speaker_id for s in test_samples))
            },
            'label_distribution': {
                'train_positive_ratio': sum(train_labels)/len(train_labels),
                'test_positive_ratio': sum(test_labels)/len(test_labels)
            },
            'results': {
                'majority_baseline': {
                    'accuracy': float(majority_results['accuracy']),
                    'precision': float(majority_results['precision']),
                    'recall': float(majority_results['recall']),
                    'f1': float(majority_results['f1'])
                },
                'heuristic_model': {
                    'accuracy': float(heuristic_results['accuracy']),
                    'precision': float(heuristic_results['precision']),
                    'recall': float(heuristic_results['recall']),
                    'f1': float(heuristic_results['f1'])
                },
                'literature_baseline': baseline_accuracy
            },
            'comparison': {
                'heuristic_vs_baseline': float(heuristic_results['accuracy'] - baseline_accuracy),
                'heuristic_vs_majority': float(heuristic_results['accuracy'] - majority_results['accuracy']),
                'meets_baseline': heuristic_results['accuracy'] >= baseline_accuracy
            }
        }

        # Save results
        results_dir = Path("/Users/Subho/autonomous_laughter_prediction/benchmarks/results")
        results_dir.mkdir(parents=True, exist_ok=True)

        results_file = results_dir / f"scripts_fast_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\nResults saved to: {results_file}")

        # Print formatted summary
        print("\n" + "=" * 80)
        print("FINAL RESULTS")
        print("=" * 80)
        print(f"Benchmark: {report['benchmark']}")
        print(f"Evaluation: {report['evaluation_type']}")
        print(f"\nDataset Statistics:")
        print(f"  Total Samples: {report['dataset_stats']['total_samples']}")
        print(f"  Train Samples: {report['dataset_stats']['train_samples']}")
        print(f"  Test Samples: {report['dataset_stats']['test_samples']}")
        print(f"  Total Comedians: {report['dataset_stats']['total_comedians']}")
        print(f"  Test Comedians (Unseen): {report['dataset_stats']['test_comedians']}")
        print(f"\nTest Performance:")
        print(f"  Majority Baseline:")
        print(f"    Accuracy: {report['results']['majority_baseline']['accuracy']:.4f} ({report['results']['majority_baseline']['accuracy']*100:.2f}%)")
        print(f"    F1 Score: {report['results']['majority_baseline']['f1']:.4f}")
        print(f"  Heuristic Model:")
        print(f"    Accuracy: {report['results']['heuristic_model']['accuracy']:.4f} ({report['results']['heuristic_model']['accuracy']*100:.2f}%)")
        print(f"    Precision: {report['results']['heuristic_model']['precision']:.4f}")
        print(f"    Recall: {report['results']['heuristic_model']['recall']:.4f}")
        print(f"    F1 Score: {report['results']['heuristic_model']['f1']:.4f}")
        print(f"  Literature Baseline:")
        print(f"    Accuracy: {report['results']['literature_baseline']:.4f} ({report['results']['literature_baseline']*100:.2f}%)")
        print(f"\nComparison:")
        print(f"  Heuristic vs Literature: {report['comparison']['heuristic_vs_baseline']:+.4f} ({report['comparison']['heuristic_vs_baseline']*100:+.2f}%)")
        print(f"  Heuristic vs Majority: {report['comparison']['heuristic_vs_majority']:+.4f} ({report['comparison']['heuristic_vs_majority']*100:+.2f}%)")
        print(f"  Meets Literature Baseline: {report['comparison']['meets_baseline']}")
        print("=" * 80)

        print("\n✓ SCRIPTS fast benchmark evaluation complete!")

        return report


def main():
    """Main execution function"""
    data_path = "/Users/Subho/autonomous_laughter_prediction/data/raw"

    evaluator = SCRIPTSStandUpFast(data_path)
    report = evaluator.run_evaluation()

    if report:
        print("\n🎉 SCRIPTS fast benchmark completed successfully!")
        print(f"Heuristic accuracy: {report['results']['heuristic_model']['accuracy']*100:.2f}%")
        print(f"Literature baseline: {report['results']['literature_baseline']*100:.2f}%")
        if report['comparison']['meets_baseline']:
            print("✓ Meets or exceeds literature baseline!")
        else:
            print("⚠ Below literature baseline - this demonstrates the need for ML models")
        print("\nNote: This was a fast heuristic evaluation. Full ML training would likely yield better results.")
    else:
        print("\n❌ Benchmark execution failed")

    return report


if __name__ == "__main__":
    main()