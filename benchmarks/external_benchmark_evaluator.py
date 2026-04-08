#!/usr/bin/env python3
"""
External Academic Benchmark Evaluator
Proper evaluation against published research benchmarks
"""

import json
import torch
import numpy as np
from pathlib import Path
import sys
import os
from typing import Dict, List, Tuple, Any
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, f1_score

# Setup paths
project_dir = Path("~/autonomous_laughter_prediction").expanduser()
sys.path.insert(0, str(project_dir))
os.chdir(str(project_dir))

class ExternalBenchmarkEvaluator:
    """Proper external benchmark evaluation framework"""

    def __init__(self):
        self.project_dir = project_dir
        self.benchmarks_dir = self.project_dir / "benchmarks"
        self.benchmarks_dir.mkdir(parents=True, exist_ok=True)

        self.results = {}

        print("🔍 EXTERNAL BENCHMARK EVALUATOR")
        print("=" * 80)

    def calculate_standard_metrics(self, y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
        """Calculate standard academic metrics"""
        accuracy = accuracy_score(y_true, y_pred)
        precision, recall, f1, _ = precision_recall_fscore_support(
            y_true, y_pred, average='binary', zero_division=0
        )

        # Macro-average for class-imbalanced datasets
        precision_macro, recall_macro, f1_macro, _ = precision_recall_fscore_support(
            y_true, y_pred, average='macro', zero_division=0
        )

        return {
            'accuracy': float(accuracy),
            'precision': float(precision),
            'recall': float(recall),
            'f1': float(f1),
            'precision_macro': float(precision_macro),
            'recall_macro': float(recall_macro),
            'f1_macro': float(f1_macro)
        }

    def calculate_iou_metrics(self, y_true_segments: List[Dict], y_pred_segments: List[Dict],
                             iou_threshold: float = 0.2) -> Dict[str, float]:
        """Calculate IoU-based temporal detection metrics"""
        def calculate_iou(seg1: Dict, seg2: Dict) -> float:
            """Calculate Intersection over Union for temporal segments"""
            start1, end1 = seg1['start'], seg1['end']
            start2, end2 = seg2['start'], seg2['end']

            intersection = max(0, min(end1, end2) - max(start1, start2))
            union = max(end1, end2) - min(start1, start2)

            return intersection / union if union > 0 else 0.0

        # Match predictions to ground truth
        tp, fp, fn = 0, 0, 0
        matched_pred = set()

        for gt_seg in y_true_segments:
            best_iou = 0.0
            best_pred_idx = -1

            for pred_idx, pred_seg in enumerate(y_pred_segments):
                if pred_idx in matched_pred:
                    continue

                iou = calculate_iou(gt_seg, pred_seg)
                if iou > best_iou:
                    best_iou = iou
                    best_pred_idx = pred_idx

            if best_iou >= iou_threshold:
                tp += 1
                if best_pred_idx >= 0:
                    matched_pred.add(best_pred_idx)
            else:
                fn += 1

        fp = len(y_pred_segments) - len(matched_pred)

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        return {
            f'iou_tp_{int(iou_threshold*100)}': tp,
            f'iou_fp_{int(iou_threshold*100)}': fp,
            f'iou_fn_{int(iou_threshold*100)}': fn,
            f'iou_precision_{int(iou_threshold*100)}': float(precision),
            f'iou_recall_{int(iou_threshold*100)}': float(recall),
            f'iou_f1_{int(iou_threshold*100)}': float(f1)
        }

    def evaluate_ted_style_benchmark(self, samples: List[Dict]) -> Dict[str, float]:
        """Evaluate TED-style binary classification (sentence-level)"""
        print("🎯 Evaluating TED-style binary classification...")

        y_true = []
        y_pred = []

        for sample in samples:
            # Ground truth label
            label = sample.get('has_laughter', 0)
            y_true.append(label)

            # Our model prediction (placeholder - needs actual model)
            # For now, random prediction for demonstration
            prediction = np.random.randint(0, 2)  # TODO: Replace with actual model
            y_pred.append(prediction)

        metrics = self.calculate_standard_metrics(np.array(y_true), np.array(y_pred))

        print(f"   Accuracy: {metrics['accuracy']:.3f}")
        print(f"   F1: {metrics['f1']:.3f}")
        print(f"   Macro-F1: {metrics['f1_macro']:.3f}")

        return metrics

    def evaluate_word_level_benchmark(self, transcript: List[Dict]) -> Dict[str, float]:
        """Evaluate word-level laughter-after-word prediction"""
        print("🎯 Evaluating word-level laughter prediction...")

        word_predictions = []
        word_labels = []

        for word_data in transcript:
            # Ground truth: does laughter follow this word?
            label = word_data.get('laughter_after_word', 0)
            word_labels.append(label)

            # Our model prediction (placeholder)
            prediction = np.random.randint(0, 2)  # TODO: Replace with actual model
            word_predictions.append(prediction)

        metrics = self.calculate_standard_metrics(
            np.array(word_labels),
            np.array(word_predictions)
        )

        print(f"   Word-level Accuracy: {metrics['accuracy']:.3f}")
        print(f"   Word-level F1: {metrics['f1']:.3f}")

        return metrics

    def evaluate_temporal_detection_benchmark(self, laughter_segments: List[Dict],
                                            predicted_segments: List[Dict]) -> Dict[str, float]:
        """Evaluate temporal laughter detection with IoU metrics"""
        print("🎯 Evaluating temporal detection with IoU...")

        iou_metrics = self.calculate_iou_metrics(laughter_segments, predicted_segments)

        print(f"   IoU@0.2 Precision: {iou_metrics['iou_precision_20']:.3f}")
        print(f"   IoU@0.2 Recall: {iou_metrics['iou_recall_20']:.3f}")
        print(f"   IoU@0.2 F1: {iou_metrics['iou_f1_20']:.3f}")

        return iou_metrics

    def cross_domain_evaluation(self, source_data: List[Dict], target_data: List[Dict]) -> Dict[str, float]:
        """Evaluate cross-domain generalization"""
        print("🎯 Evaluating cross-domain generalization...")

        # Train on source domain, test on target domain
        # This is a zero-shot transfer evaluation

        source_metrics = self.evaluate_ted_style_benchmark(source_data)
        target_metrics = self.evaluate_ted_style_benchmark(target_data)

        # Calculate transfer performance degradation
        performance_drop = source_metrics['f1'] - target_metrics['f1']

        transfer_metrics = {
            'source_f1': source_metrics['f1'],
            'target_f1': target_metrics['f1'],
            'transfer_performance_drop': float(performance_drop),
            'transfer_ratio': float(target_metrics['f1'] / source_metrics['f1']) if source_metrics['f1'] > 0 else 0.0
        }

        print(f"   Source F1: {transfer_metrics['source_f1']:.3f}")
        print(f"   Target F1: {transfer_metrics['target_f1']:.3f}")
        print(f"   Transfer Ratio: {transfer_metrics['transfer_ratio']:.3f}")

        return transfer_metrics

    def speaker_independent_evaluation(self, samples: List[Dict], speaker_column: str = 'speaker_id') -> Dict[str, float]:
        """Evaluate speaker-independent generalization"""
        print("🎯 Evaluating speaker-independent generalization...")

        unique_speakers = list(set(sample.get(speaker_column, 'unknown') for sample in samples))

        if len(unique_speakers) < 2:
            print("   ⚠️ Need multiple speakers for speaker-independent evaluation")
            return {}

        # Leave-one-speaker-out cross-validation
        speaker_scores = []

        for held_out_speaker in unique_speakers:
            train_samples = [s for s in samples if s.get(speaker_column) != held_out_speaker]
            test_samples = [s for s in samples if s.get(speaker_column) == held_out_speaker]

            if len(test_samples) == 0:
                continue

            # Train on other speakers, test on held-out speaker
            # For demonstration, just evaluate test samples
            test_metrics = self.evaluate_ted_style_benchmark(test_samples)
            speaker_scores.append({
                'speaker': held_out_speaker,
                'f1': test_metrics['f1'],
                'num_samples': len(test_samples)
            })

        # Calculate statistics
        f1_scores = [s['f1'] for s in speaker_scores]
        speaker_independent_metrics = {
            'mean_speaker_f1': float(np.mean(f1_scores)) if f1_scores else 0.0,
            'std_speaker_f1': float(np.std(f1_scores)) if f1_scores else 0.0,
            'min_speaker_f1': float(np.min(f1_scores)) if f1_scores else 0.0,
            'max_speaker_f1': float(np.max(f1_scores)) if f1_scores else 0.0,
            'num_speakers': len(unique_speakers),
            'speaker_scores': speaker_scores
        }

        print(f"   Mean Speaker F1: {speaker_independent_metrics['mean_speaker_f1']:.3f} ± {speaker_independent_metrics['std_speaker_f1']:.3f}")

        return speaker_independent_metrics

    def generate_comparison_table(self, results: Dict[str, Dict]) -> str:
        """Generate publication-ready comparison table"""
        print("\n📊 ACADEMIC COMPARISON TABLE")
        print("=" * 80)

        # Format: Dataset | Task | Published Baseline | Our Method | Improvement
        table_format = "{:<25} | {:<25} | {:<15} | {:<12} | {:<10}"

        header = table_format.format("Dataset", "Task", "Published Best", "Our Method", "Improvement")
        print(header)
        print("-" * 100)

        # Known published baselines (from research)
        published_baselines = {
            'StandUp4AI': {'best': '0.58 F1', 'task': 'Word-level IoU F1'},
            'UR-FUNNY': {'best': '65.23%', 'task': 'Multimodal Accuracy'},
            'TED_Laughter': {'best': '0.606 F1', 'task': 'Text Classification'},
            'MHD': {'best': '81.32 F1', 'task': 'Humor-Class F1'},
            'SCRIPTS': {'best': '68.4%', 'task': 'Stand-up Accuracy'}
        }

        for dataset_name, dataset_results in results.items():
            baseline = published_baselines.get(dataset_name, {'best': 'N/A', 'task': 'N/A'})

            # Extract our best metric (simplified)
            our_metric = 'TBD'  # To be filled with actual results
            improvement = 'TBD'

            row = table_format.format(
                dataset_name,
                baseline['task'],
                baseline['best'],
                our_metric,
                improvement
            )
            print(row)

        return "\n".join([header, "-" * 100])  # Return header for saving

def main():
    """Main benchmark evaluation function"""
    evaluator = ExternalBenchmarkEvaluator()

    print("\n🚨 CRITICAL VALIDATION GAP ANALYSIS")
    print("=" * 80)
    print("Current status: Internal validation only")
    print("Required: External academic benchmark evaluation")
    print("\n📋 Benchmarks to implement:")
    print("   1. StandUp4AI (EMNLP 2025) - Most critical")
    print("   2. UR-FUNNY (EMNLP 2019) - Standard TED benchmark")
    print("   3. TED Laughter Corpus - Text classification")
    print("   4. MHD (WACV 2021) - Sitcom laugh tracks")
    print("   5. SCRIPTS (LREC 2022) - Stand-up scripts")
    print("   6. Cross-domain generalization tests")
    print("   7. Speaker-independent evaluation")

if __name__ == "__main__":
    main()