#!/usr/bin/env python3
"""
Benchmark Integration System
Connects Agent 3's metrics framework with external academic datasets
"""

import numpy as np
import torch
from typing import Dict, List, Tuple, Any, Optional
from pathlib import Path
import json
import sys

# Import our metrics framework
from academic_metrics_framework import AcademicMetricsFramework, EvaluationResult

# Import dataset loaders
sys.path.insert(0, str(Path("~/autonomous_laughter_prediction").expanduser()))
from benchmarks.datasets.standup4ai import StandUp4AIDataset
from benchmarks.datasets.ur_funny import UrFunnyDataset
from benchmarks.datasets.ted_laughter import TedLaughterDataset
from benchmarks.datasets.humor_detection import HumorDetectionDataset


class BenchmarkIntegration:
    """
    Integration system for evaluating models against academic benchmarks.

    Coordinates between:
    - Agent 1: Data infrastructure and dataset loading
    - Agent 2: Model implementations and predictions
    - Agent 3: Metrics calculation and statistical validation
    """

    def __init__(self):
        """Initialize benchmark integration system"""
        self.metrics_framework = AcademicMetricsFramework()

        # Dataset configurations
        self.dataset_configs = {
            'standup4ai': {
                'name': 'StandUp4AI',
                'paper': 'EMNLP 2025',
                'task_type': 'word_level_iou',
                'primary_metric': 'f1_iou_20',
                'published_baseline': 0.58,  # From paper
                'evaluation_protocols': ['word_level', 'temporal_iou', 'classification']
            },
            'ur_funny': {
                'name': 'UR-FUNNY',
                'paper': 'EMNLP 2019',
                'task_type': 'multimodal_classification',
                'primary_metric': 'accuracy',
                'published_baseline': 65.23,  # Percentage from paper
                'evaluation_protocols': ['multimodal', 'text_only', 'audio_only']
            },
            'ted_laughter': {
                'name': 'TED Laughter',
                'paper': 'Various',
                'task_type': 'binary_classification',
                'primary_metric': 'f1',
                'published_baseline': 0.606,
                'evaluation_protocols': ['text_classification', 'speaker_independent']
            },
            'mhd': {
                'name': 'MHD',
                'paper': 'WACV 2021',
                'task_type': 'temporal_detection',
                'primary_metric': 'f1_iou_30',
                'published_baseline': 81.32,  # F1 score
                'evaluation_protocols': ['temporal_detection', 'laughter_classification']
            },
            'scripts': {
                'name': 'SCRIPTS',
                'paper': 'LREC 2022',
                'task_type': 'standup_classification',
                'primary_metric': 'accuracy',
                'published_baseline': 68.4,  # Percentage
                'evaluation_protocols': ['binary_classification', 'multi_class']
            }
        }

        print("🔗 BENCHMARK INTEGRATION SYSTEM")
        print("=" * 80)
        print(f"Datasets configured: {len(self.dataset_configs)}")
        for dataset_id, config in self.dataset_configs.items():
            print(f"  - {config['name']} ({config['paper']})")
        print("=" * 80)

    def evaluate_standup4ai_benchmark(self, model: Any, split: str = 'test') -> Dict[str, EvaluationResult]:
        """
        Evaluate model on StandUp4AI benchmark using exact paper protocols.

        StandUp4AI Evaluation:
        - Word-level laughter-after-word prediction
        - IoU-based temporal metrics (IoU@0.2, @0.3, @0.5)
        - Classification metrics for humor detection
        """
        print("\n🎯 Evaluating StandUp4AI Benchmark (EMNLP 2025)")
        print("-" * 80)

        try:
            # Load dataset
            dataset = StandUp4AIDataset()
            samples = dataset.get_split(split)

            # Extract ground truth and predictions
            word_predictions = []
            word_labels = []
            temporal_segments_gt = []
            temporal_segments_pred = []
            humor_labels = []
            humor_predictions = []

            for sample in samples:
                # Word-level predictions
                for word_data in sample.get('words', []):
                    word_labels.append(word_data.get('laughter_after_word', 0))

                    # TODO: Get model prediction for this word
                    # For now, use placeholder
                    word_pred = self._get_model_prediction(model, word_data, 'word_level')
                    word_predictions.append(word_pred)

                # Temporal segments
                if 'laughter_segments' in sample:
                    temporal_segments_gt.extend(sample['laughter_segments'])

                    # TODO: Get model predictions for temporal segments
                    predicted_segments = self._get_model_temporal_predictions(model, sample)
                    temporal_segments_pred.extend(predicted_segments)

                # Humor classification
                humor_labels.append(sample.get('is_humorous', 0))
                humor_pred = self._get_model_prediction(model, sample, 'humor_classification')
                humor_predictions.append(humor_pred)

            # Calculate metrics
            results = {}

            # 1. Word-level classification metrics
            if word_labels and word_predictions:
                word_labels_array = np.array(word_labels)
                word_predictions_array = np.array(word_predictions)

                word_metrics = self.metrics_framework.classification_metrics(
                    word_labels_array, word_predictions_array
                )

                # Add word-specific metrics
                for metric_name, result in word_metrics.items():
                    results[f'word_{metric_name}'] = result

                print(f"  Word-level F1: {word_metrics['f1'].value:.4f}")

            # 2. Temporal IoU metrics
            if temporal_segments_gt and temporal_segments_pred:
                iou_metrics = self.metrics_framework.iou_based_detection_metrics(
                    temporal_segments_gt, temporal_segments_pred
                )

                for metric_name, result in iou_metrics.items():
                    results[metric_name] = result

                print(f"  IoU@0.2 F1: {iou_metrics['f1_iou_20'].value:.4f}")
                print(f"  IoU@0.3 F1: {iou_metrics['f1_iou_30'].value:.4f}")

            # 3. Humor classification metrics
            if humor_labels and humor_predictions:
                humor_labels_array = np.array(humor_labels)
                humor_predictions_array = np.array(humor_predictions)

                humor_metrics = self.metrics_framework.classification_metrics(
                    humor_labels_array, humor_predictions_array
                )

                for metric_name, result in humor_metrics.items():
                    results[f'humor_{metric_name}'] = result

                print(f"  Humor Classification F1: {humor_metrics['f1'].value:.4f}")

            # Compare with published baseline
            primary_metric = results.get(self.dataset_configs['standup4ai']['primary_metric'])
            if primary_metric:
                baseline = self.dataset_configs['standup4ai']['published_baseline']
                improvement = ((primary_metric.value - baseline) / baseline) * 100

                print(f"\n  📊 Comparison with published baseline:")
                print(f"     Published: {baseline:.4f}")
                print(f"     Our Method: {primary_metric.value:.4f}")
                print(f"     Improvement: {improvement:+.2f}%")

                results['baseline_comparison'] = EvaluationResult(
                    metric_name='Baseline Comparison (%)',
                    value=float(improvement),
                    confidence_interval=(0.0, 0.0),
                    metadata={'baseline': baseline, 'our_method': primary_metric.value}
                )

            return results

        except Exception as e:
            print(f"❌ Error evaluating StandUp4AI: {str(e)}")
            return {}

    def evaluate_ur_funny_benchmark(self, model: Any, split: str = 'test') -> Dict[str, EvaluationResult]:
        """
        Evaluate model on UR-FUNNY benchmark using exact paper protocols.

        UR-FUNNY Evaluation:
        - Multimodal humor detection (text + audio)
        - Text-only baseline
        - Audio-only baseline
        """
        print("\n🎯 Evaluating UR-FUNNY Benchmark (EMNLP 2019)")
        print("-" * 80)

        try:
            # Load dataset
            dataset = UrFunnyDataset()
            samples = dataset.get_split(split)

            # Extract labels and predictions for different modalities
            multimodal_labels = []
            multimodal_predictions = []
            text_only_predictions = []
            audio_only_predictions = []

            for sample in samples:
                label = sample.get('is_funny', 0)
                multimodal_labels.append(label)

                # Get predictions for different modalities
                multimodal_pred = self._get_model_prediction(model, sample, 'multimodal')
                text_pred = self._get_model_prediction(model, sample, 'text_only')
                audio_pred = self._get_model_prediction(model, sample, 'audio_only')

                multimodal_predictions.append(multimodal_pred)
                text_only_predictions.append(text_pred)
                audio_only_predictions.append(audio_pred)

            # Convert to arrays
            labels_array = np.array(multimodal_labels)
            multimodal_preds_array = np.array(multimodal_predictions)
            text_preds_array = np.array(text_only_predictions)
            audio_preds_array = np.array(audio_only_predictions)

            results = {}

            # Calculate metrics for each modality
            for modality_name, predictions in [('multimodal', multimodal_preds_array),
                                              ('text_only', text_preds_array),
                                              ('audio_only', audio_preds_array)]:
                modality_metrics = self.metrics_framework.classification_metrics(
                    labels_array, predictions
                )

                for metric_name, result in modality_metrics.items():
                    results[f'{modality_name}_{metric_name}'] = result

                print(f"  {modality_name} Accuracy: {modality_metrics['accuracy'].value:.4f}")

            # Compare with published baseline
            primary_metric = results.get('multimodal_accuracy')
            if primary_metric:
                baseline = self.dataset_configs['ur_funny']['published_baseline'] / 100.0  # Convert percentage
                improvement = ((primary_metric.value - baseline) / baseline) * 100

                print(f"\n  📊 Comparison with published baseline:")
                print(f"     Published: {baseline:.4f}")
                print(f"     Our Method: {primary_metric.value:.4f}")
                print(f"     Improvement: {improvement:+.2f}%")

                results['baseline_comparison'] = EvaluationResult(
                    metric_name='Baseline Comparison (%)',
                    value=float(improvement),
                    confidence_interval=(0.0, 0.0),
                    metadata={'baseline': baseline, 'our_method': primary_metric.value}
                )

            return results

        except Exception as e:
            print(f"❌ Error evaluating UR-FUNNY: {str(e)}")
            return {}

    def evaluate_ted_laughter_benchmark(self, model: Any, split: str = 'test') -> Dict[str, EvaluationResult]:
        """
        Evaluate model on TED Laughter benchmark.

        TED Laughter Evaluation:
        - Binary laughter detection
        - Speaker-independent evaluation
        """
        print("\n🎯 Evaluating TED Laughter Benchmark")
        print("-" * 80)

        try:
            # Load dataset
            dataset = TedLaughterDataset()
            samples = dataset.get_split(split)

            # Extract labels and predictions
            labels = []
            predictions = []
            predictions_by_speaker = {}

            for sample in samples:
                label = sample.get('has_laughter', 0)
                labels.append(label)

                prediction = self._get_model_prediction(model, sample, 'binary_classification')
                predictions.append(prediction)

                # Speaker-independent evaluation
                speaker_id = sample.get('speaker_id', 'unknown')
                if speaker_id not in predictions_by_speaker:
                    predictions_by_speaker[speaker_id] = ([], [])
                predictions_by_speaker[speaker_id][0].append(label)
                predictions_by_speaker[speaker_id][1].append(prediction)

            # Convert to arrays
            labels_array = np.array(labels)
            predictions_array = np.array(predictions)

            results = {}

            # Overall classification metrics
            overall_metrics = self.metrics_framework.classification_metrics(
                labels_array, predictions_array
            )

            for metric_name, result in overall_metrics.items():
                results[metric_name] = result

            print(f"  Overall F1: {overall_metrics['f1'].value:.4f}")

            # Speaker-independent metrics
            if len(predictions_by_speaker) > 1:
                speaker_predictions = {
                    speaker: (np.array(labels), np.array(preds))
                    for speaker, (labels, preds) in predictions_by_speaker.items()
                }

                speaker_metrics = self.metrics_framework.speaker_independent_metrics(speaker_predictions)

                for metric_name, result in speaker_metrics.items():
                    results[metric_name] = result

                print(f"  Speaker-independent F1: {speaker_metrics['mean_speaker_f1'].value:.4f}")

            return results

        except Exception as e:
            print(f"❌ Error evaluating TED Laughter: {str(e)}")
            return {}

    def cross_domain_evaluation(self, model: Any, source_dataset: str, target_dataset: str) -> Dict[str, EvaluationResult]:
        """
        Evaluate cross-domain generalization.

        Tests model's ability to transfer knowledge across different domains.
        """
        print(f"\n🎯 Cross-Domain Evaluation: {source_dataset} → {target_dataset}")
        print("-" * 80)

        try:
            # Load source and target datasets
            source_results = self._evaluate_single_dataset(model, source_dataset, 'test')
            target_results = self._evaluate_single_dataset(model, target_dataset, 'test')

            # Get F1 scores for comparison
            source_f1 = source_results.get('f1', source_results.get('word_f1'))
            target_f1 = target_results.get('f1', target_results.get('word_f1'))

            if source_f1 and target_f1:
                cross_domain_metrics = self.metrics_framework.cross_domain_metrics(
                    (np.array([1, 0]), np.array([1, 0])),  # Placeholder - needs actual predictions
                    (np.array([1, 0]), np.array([1, 0]))
                )

                # Update with actual values
                cross_domain_metrics['source_f1'].value = source_f1.value
                cross_domain_metrics['target_f1'].value = target_f1.value

                performance_drop = source_f1.value - target_f1.value
                cross_domain_metrics['transfer_performance_drop'].value = performance_drop

                if source_f1.value > 0:
                    transfer_ratio = target_f1.value / source_f1.value
                    cross_domain_metrics['transfer_ratio'].value = transfer_ratio

                print(f"  Source F1: {source_f1.value:.4f}")
                print(f"  Target F1: {target_f1.value:.4f}")
                print(f"  Transfer Ratio: {cross_domain_metrics['transfer_ratio'].value:.4f}")

                return cross_domain_metrics

        except Exception as e:
            print(f"❌ Error in cross-domain evaluation: {str(e)}")
            return {}

    def _evaluate_single_dataset(self, model: Any, dataset_name: str, split: str) -> Dict[str, EvaluationResult]:
        """Helper method to evaluate a single dataset"""
        if dataset_name == 'standup4ai':
            return self.evaluate_standup4ai_benchmark(model, split)
        elif dataset_name == 'ur_funny':
            return self.evaluate_ur_funny_benchmark(model, split)
        elif dataset_name == 'ted_laughter':
            return self.evaluate_ted_laughter_benchmark(model, split)
        else:
            print(f"⚠️ Unknown dataset: {dataset_name}")
            return {}

    def _get_model_prediction(self, model: Any, input_data: Any, task_type: str) -> int:
        """
        Get prediction from model for specific task type.

        TODO: This is a placeholder that needs to be connected to actual model implementations.
        Should call Agent 2's model interface.
        """
        # Placeholder: Return random prediction
        # In production, this would call model.predict(input_data, task_type)
        return np.random.randint(0, 2)

    def _get_model_temporal_predictions(self, model: Any, input_data: Any) -> List[Dict]:
        """
        Get temporal segment predictions from model.

        TODO: This is a placeholder that needs to be connected to actual model implementations.
        """
        # Placeholder: Return empty segments
        # In production, this would call model.predict_temporal(input_data)
        return []

    def run_full_benchmark_suite(self, model: Any) -> Dict[str, Dict[str, EvaluationResult]]:
        """
        Run complete benchmark suite across all datasets.

        Returns comprehensive evaluation results for all academic benchmarks.
        """
        print("\n🏆 RUNNING FULL BENCHMARK SUITE")
        print("=" * 80)

        all_results = {}

        # Evaluate each benchmark
        benchmarks = [
            ('standup4ai', self.evaluate_standup4ai_benchmark),
            ('ur_funny', self.evaluate_ur_funny_benchmark),
            ('ted_laughter', self.evaluate_ted_laughter_benchmark)
        ]

        for benchmark_name, evaluator in benchmarks:
            print(f"\n{'='*80}")
            print(f"Evaluating: {self.dataset_configs[benchmark_name]['name']}")
            print(f"Paper: {self.dataset_configs[benchmark_name]['paper']}")
            print(f"{'='*80}")

            try:
                results = evaluator(model, 'test')
                all_results[benchmark_name] = results

                # Print summary
                if results:
                    primary_metric_name = self.dataset_configs[benchmark_name]['primary_metric']
                    if primary_metric_name in results:
                        primary_result = results[primary_metric_name]
                        print(f"\n✅ {benchmark_name.upper()} PRIMARY METRIC:")
                        print(f"   {primary_result.metric_name}: {primary_result.value:.4f}")
                        print(f"   95% CI: [{primary_result.confidence_interval[0]:.4f}, {primary_result.confidence_interval[1]:.4f}]")

            except Exception as e:
                print(f"❌ Failed to evaluate {benchmark_name}: {str(e)}")
                all_results[benchmark_name] = {}

        # Cross-domain evaluations
        print(f"\n{'='*80}")
        print("Cross-Domain Evaluation")
        print(f"{'='*80}")

        cross_domain_pairs = [
            ('standup4ai', 'ur_funny'),
            ('ted_laughter', 'standup4ai')
        ]

        for source, target in cross_domain_pairs:
            cross_domain_results = self.cross_domain_evaluation(model, source, target)
            all_results[f'{source}_to_{target}'] = cross_domain_results

        return all_results

    def generate_publication_table(self, all_results: Dict[str, Dict[str, EvaluationResult]]) -> str:
        """Generate publication-ready comparison table"""
        print("\n📊 PUBLICATION-READY RESULTS TABLE")
        print("=" * 80)

        table_format = "{:<20} | {:<25} | {:<12} | {:<12} | {:<10}"
        header = table_format.format("Dataset", "Task", "Published", "Our Method", "Improvement")
        print(header)
        print("-" * 100)

        rows = []
        for dataset_name, dataset_config in self.dataset_configs.items():
            if dataset_name not in all_results or not all_results[dataset_name]:
                continue

            results = all_results[dataset_name]
            primary_metric_name = dataset_config['primary_metric']

            if primary_metric_name not in results:
                continue

            our_result = results[primary_metric_name]
            published_baseline = dataset_config['published_baseline']

            # Calculate improvement
            if published_baseline > 0:
                improvement = ((our_result.value - published_baseline) / published_baseline) * 100
                improvement_str = f"{improvement:+.2f}%"
            else:
                improvement_str = "N/A"

            row = table_format.format(
                dataset_config['name'],
                dataset_config['task_type'].replace('_', ' ').title(),
                f"{published_baseline:.4f}",
                f"{our_result.value:.4f}",
                improvement_str
            )
            print(row)
            rows.append(row)

        print("=" * 80)
        return "\n".join([header, "-" * 100] + rows)

    def save_all_results(self, all_results: Dict[str, Dict[str, EvaluationResult]], output_dir: str):
        """Save all evaluation results to files"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Save individual dataset results
        for dataset_name, results in all_results.items():
            if results:
                filepath = output_path / f"{dataset_name}_results.json"
                self.metrics_framework.save_results(results, filepath)

        # Save publication table
        table = self.generate_publication_table(all_results)
        table_path = output_path / "publication_table.txt"
        with open(table_path, 'w') as f:
            f.write(table)

        print(f"\n✅ All results saved to {output_path}")


def main():
    """Demonstration of benchmark integration"""
    print("🔗 BENCHMARK INTEGRATION SYSTEM")
    print("=" * 80)
    print("Agent 3: Academic Evaluation Metrics Framework")
    print("=" * 80)

    # Initialize benchmark integration
    integration = BenchmarkIntegration()

    print("\n✅ BENCHMARK INTEGRATION READY")
    print("🎯 Ready to evaluate models against academic benchmarks")
    print("📊 Implementing exact metrics from published research papers")
    print("🔬 Statistical validation with bootstrap confidence intervals")
    print("📈 Cross-domain and speaker-independent evaluation")

    print("\n📋 CONFIGURED DATASETS:")
    for dataset_id, config in integration.dataset_configs.items():
        print(f"  • {config['name']} ({config['paper']})")
        print(f"    - Task: {config['task_type']}")
        print(f"    - Primary Metric: {config['primary_metric']}")
        print(f"    - Published Baseline: {config['published_baseline']}")

    print("\n🚀 NEXT STEPS:")
    print("  1. Connect with Agent 2's model implementations")
    print("  2. Run full benchmark suite evaluation")
    print("  3. Generate publication-ready results")
    print("  4. Compare against published baselines")


if __name__ == "__main__":
    main()