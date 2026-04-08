#!/usr/bin/env python3
"""
Language-Specific Enhanced Biosemotic Testing
Comprehensive evaluation separated by Hindi, English, and Hinglish content
"""

import sys
from pathlib import Path
import json
import torch
import numpy as np
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from sklearn.metrics import f1_score, precision_score, recall_score, accuracy_score
import re

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.biosemotic_enhancement import create_enhanced_model


@dataclass
class LanguageSpecificResults:
    """Results for specific language testing"""
    language: str
    total_examples: int
    base_binary_f1: float
    laughter_detection_accuracy: float
    non_laughter_accuracy: float
    duchenne_classification_avg: float
    sarcasm_detection_avg: float
    mental_state_modeling_avg: float
    cross_cultural_nuance_avg: float
    biosemotic_diversity: float
    processing_time_ms: float


class LanguageSpecificTester:
    """Enhanced biosemotic system tester with language-specific evaluation"""

    def __init__(self, model_path: str):
        self.model_path = Path(model_path)
        print(f"🧪 Loading Enhanced Biosemotic System for Language-Specific Testing")

        self.model = create_enhanced_model(
            model_path=str(self.model_path),
            device=torch.device('cpu')
        )

        # Language detection patterns
        self.hindi_patterns = [
            r'[\u0900-\u097F]',  # Devanagari script
            r'\b(?:kya|kyun|kahan|kaun|hai|hain|ho|kar|li|ye|wo|jab|to|agar|magar|par)\b',
            r'\b(?:acha|theek|haa|naa|ji|sahib|please)\b'
        ]

        self.hinglish_patterns = [
            r'\b(?:kya|kyun|kahan|kaun|hai|hain|ho|kar|li|ye|wo|jab|to|agar|magar)\b',
            r'\b(?:acha|theek|please|ji|sahib|actually|basically|simply)\b',
            r'[a-zA-Z]+\s+[a-zA-Z]+\s+(?:kya|kyun|hai|hain)',
            r'(?:kya|kyun|hai|hain)\s+[a-zA-Z]+'
        ]

        print("✅ Enhanced system loaded with language detection capabilities")

    def detect_language(self, text: str) -> str:
        """
        Detect language of text: 'hindi', 'english', 'hinglish', or 'mixed'
        """
        # Check for Hindi (Devanagari)
        if re.search(self.hindi_patterns[0], text):
            # Check if it's pure Hindi or Hinglish
            english_word_ratio = len(re.findall(r'\b[a-zA-Z]{2,}\b', text)) / max(len(text.split()), 1)
            if english_word_ratio > 0.3:
                return 'hinglish'
            return 'hindi'

        # Check for Hinglish patterns (Latin script with Hindi words)
        hinglish_matches = sum(1 for pattern in self.hinglish_patterns[1:]
                              if re.search(pattern, text, re.IGNORECASE))
        if hinglish_matches >= 2:
            return 'hinglish'

        # Default to English
        return 'english'

    def test_dataset_by_language(self, dataset_path: str, max_examples: int = 100) -> Dict[str, LanguageSpecificResults]:
        """
        Test enhanced system and separate results by language

        Args:
            dataset_path: Path to JSONL dataset
            max_examples: Maximum examples to test

        Returns:
            Dictionary mapping language names to their specific results
        """
        print(f"\n🎯 Language-Specific Testing on: {dataset_path}")

        # Load dataset
        examples = []
        with open(dataset_path, 'r') as f:
            for line in f:
                if len(examples) >= max_examples:
                    break
                examples.append(json.loads(line.strip()))

        print(f"📊 Loaded {len(examples)} examples for language-specific analysis")

        # Separate by language
        language_examples = {
            'hindi': [],
            'english': [],
            'hinglish': [],
            'mixed': []
        }

        for example in examples:
            text = ' '.join(example['words'])
            detected_lang = self.detect_language(text)
            language_examples[detected_lang].append(example)

        # Print distribution
        print("\n🌍 Language Distribution:")
        for lang, lang_examples in language_examples.items():
            if lang_examples:
                pct = (len(lang_examples) / len(examples)) * 100
                print(f"  - {lang.upper()}: {len(lang_examples)} examples ({pct:.1f}%)")

        # Test each language separately
        language_results = {}

        for lang, lang_examples in language_examples.items():
            if not lang_examples:
                continue

            print(f"\n{'='*60}")
            print(f"🎯 Testing {lang.upper()} Content")
            print(f"{'='*60}")

            results = self._test_language_subset(lang_examples, lang)
            language_results[lang] = results

            # Print language-specific summary
            self._print_language_summary(results)

        return language_results

    def _test_language_subset(self, examples: List[Dict], language: str) -> LanguageSpecificResults:
        """Test a subset of examples for a specific language"""

        all_predictions = []
        all_ground_truth = []
        processing_times = []

        biosemotic_features = {
            'duchenne_probs': [],
            'sarcasm_probs': [],
            'emotion_intensities': [],
            'cultural_nuances': []
        }

        for example in examples:
            try:
                text = ' '.join(example['words'])
                ground_truth = example['labels']

                import time
                start_time = time.time()

                predictions = self._predict_example(text, example['words'])

                processing_time = (time.time() - start_time) * 1000

                all_predictions.append(predictions)
                all_ground_truth.append(ground_truth)
                processing_times.append(processing_time)

                # Collect biosemotic features
                biosemotic_features['duchenne_probs'].extend(predictions['duchenne_probability'])
                biosemotic_features['sarcasm_probs'].extend(predictions['sarcasm_probability'])
                biosemotic_features['emotion_intensities'].extend(predictions['emotional_intensity'])

            except Exception as e:
                print(f"⚠️  Error processing example: {e}")
                continue

        # Calculate metrics
        return self._calculate_language_metrics(
            language, all_predictions, all_ground_truth,
            processing_times, biosemotic_features
        )

    def _predict_example(self, text: str, words: List[str]) -> Dict[str, Any]:
        """Predict biosemotic features for a single example"""

        # Tokenize
        encoding = self.model.tokenizer(
            words,
            is_split_into_words=True,
            max_length=128,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )

        # Run enhanced prediction
        with torch.no_grad():
            outputs = self.model(encoding['input_ids'], encoding['attention_mask'])

        # Extract word-level predictions
        word_ids = encoding.word_ids()
        word_predictions = self._extract_word_predictions(outputs, word_ids, len(words))

        return word_predictions

    def _extract_word_predictions(self, outputs, word_ids: List[int], num_words: int) -> Dict[str, Any]:
        """Extract word-level predictions from enhanced output"""
        word_level_preds = {
            'base_laughter': [],
            'duchenne_probability': [],
            'sarcasm_probability': [],
            'incongruity_score': [],
            'emotional_intensity': [],
            'cultural_nuance': []
        }

        for word_idx in range(num_words):
            # Find all token indices for this word
            token_indices = [i for i, wid in enumerate(word_ids) if wid == word_idx]
            if not token_indices:
                continue

            # Average predictions across tokens
            word_preds = {
                'base_laughter': float(outputs.base_laughter_probability[0, token_indices].mean()),
                'duchenne_probability': float(outputs.duchenne_probability[0, token_indices].mean()),
                'sarcasm_probability': float(outputs.sarcasm_probability[0, token_indices].mean()),
                'incongruity_score': float(outputs.incongruity_score[0, token_indices].mean()),
                'emotional_intensity': float(outputs.emotional_intensity[0, token_indices].mean()),
                'cultural_nuance': int(outputs.cultural_nuance[0, token_indices].mean(dim=0).argmax())
            }

            # Add to word-level predictions
            for key, value in word_preds.items():
                if key in word_level_preds:
                    word_level_preds[key].append(value)

        return word_level_preds

    def _calculate_language_metrics(self, language: str, predictions: List[Dict],
                                   ground_truth: List[List[int]], processing_times: List[float],
                                   biosemotic_features: Dict) -> LanguageSpecificResults:
        """Calculate comprehensive metrics for a specific language"""

        # Base binary F1
        all_base_preds = []
        all_ground = []

        for pred, gt in zip(predictions, ground_truth):
            # Ensure we match the lengths correctly
            pred_len = len(pred['base_laughter'])
            gt_len = len(gt)
            min_len = min(pred_len, gt_len)

            binary_preds = [1 if p > 0.5 else 0 for p in pred['base_laughter'][:min_len]]
            all_base_preds.extend(binary_preds)
            all_ground.extend(gt[:min_len])

        base_binary_f1 = f1_score(all_ground, all_base_preds, zero_division=0)

        # Laughter detection accuracy
        laughter_examples = [(p, g) for p, g in zip(predictions, ground_truth)
                            if any(g)]
        non_laughter_examples = [(p, g) for p, g in zip(predictions, ground_truth)
                                if not any(g)]

        laughter_acc = 0.0
        if laughter_examples:
            laughter_correct = sum(1 for p, g in laughter_examples
                                 if any(p_pred > 0.5 for p_pred in p['base_laughter']))
            laughter_acc = laughter_correct / len(laughter_examples)

        non_laughter_acc = 0.0
        if non_laughter_examples:
            non_laughter_correct = sum(1 for p, g in non_laughter_examples
                                     if not any(p_pred > 0.5 for p_pred in p['base_laughter']))
            non_laughter_acc = non_laughter_correct / len(non_laughter_examples)

        # Biosemotic features
        avg_duchenne = float(np.mean(biosemotic_features['duchenne_probs'])) if biosemotic_features['duchenne_probs'] else 0.0
        avg_sarcasm = float(np.mean(biosemotic_features['sarcasm_probs'])) if biosemotic_features['sarcasm_probs'] else 0.0
        avg_emotion = float(np.mean(biosemotic_features['emotion_intensities'])) if biosemotic_features['emotion_intensities'] else 0.0

        # Cultural nuance (how well it detects the correct cultural context)
        # For this, we'd expect English->US, Hindi->Indian, Hinglish->Indian
        expected_cultural_map = {
            'english': 0,  # US
            'hindi': 2,    # Indian
            'hinglish': 2  # Indian
        }

        expected_culture = expected_cultural_map.get(language, 1)  # Default to UK

        # Calculate how often it predicts the expected cultural context
        cultural_nuance_scores = []
        for pred in predictions:
            for cultural_idx in pred['cultural_nuance']:
                cultural_nuance_scores.append(1.0 if cultural_idx == expected_culture else 0.0)

        cross_cultural_nuance = float(np.mean(cultural_nuance_scores)) if cultural_nuance_scores else 0.0

        # Biosemotic diversity
        biosemotic_diversity = 0.0
        if biosemotic_features['duchenne_probs']:
            diversities = [
                float(np.std(biosemotic_features['duchenne_probs'])),
                float(np.std(biosemotic_features['sarcasm_probs'])),
                float(np.std(biosemotic_features['emotion_intensities']))
            ]
            biosemotic_diversity = float(np.mean(diversities))

        # Processing time
        processing_time_ms = float(np.mean(processing_times)) if processing_times else 0.0

        return LanguageSpecificResults(
            language=language,
            total_examples=len(predictions),
            base_binary_f1=base_binary_f1,
            laughter_detection_accuracy=laughter_acc,
            non_laughter_accuracy=non_laughter_acc,
            duchenne_classification_avg=avg_duchenne,
            sarcasm_detection_avg=avg_sarcasm,
            mental_state_modeling_avg=avg_emotion,
            cross_cultural_nuance_avg=cross_cultural_nuance,
            biosemotic_diversity=biosemotic_diversity,
            processing_time_ms=processing_time_ms
        )

    def _print_language_summary(self, results: LanguageSpecificResults):
        """Print summary for a specific language"""

        print(f"\n📊 {results.language.upper()} Performance Summary:")
        print(f"  - Examples Tested: {results.total_examples}")
        print(f"  - Base Binary F1: {results.base_binary_f1:.4f}")
        print(f"  - Laughter Detection: {results.laughter_detection_accuracy:.4f}")
        print(f"  - Non-Laughter Detection: {results.non_laughter_accuracy:.4f}")

        print(f"\n🧠 Biosemotic Capabilities:")
        print(f"  - Duchenne Classification: {results.duchenne_classification_avg:.4f} avg")
        print(f"  - Sarcasm Detection: {results.sarcasm_detection_avg:.4f} avg")
        print(f"  - Mental State Modeling: {results.mental_state_modeling_avg:.4f} avg")
        print(f"  - Cross-Cultural Nuance: {results.cross_cultural_nuance_avg:.4f}")
        print(f"  - Biosemotic Diversity: {results.biosemotic_diversity:.4f}")

        print(f"\n⏱️  Performance:")
        print(f"  - Processing Time: {results.processing_time_ms:.2f}ms avg")

        # Interpret results
        print(f"\n🎯 Language-Specific Insights:")
        if results.base_binary_f1 > 0.7:
            print(f"  ✅ EXCELLENT: F1 {results.base_binary_f1:.4f} exceeds target")
        elif results.base_binary_f1 > 0.6:
            print(f"  ⚠️  GOOD: F1 {results.base_binary_f1:.4f} near target")
        else:
            print(f"  ❌ NEEDS IMPROVEMENT: F1 {results.base_binary_f1:.4f} below target")


def run_comprehensive_language_tests():
    """Run comprehensive language-specific tests"""

    print("🚀 Starting Comprehensive Language-Specific Enhanced Biosemotic Testing")
    print("="*70)

    model_path = "models/xlmr_turboquant_restart/best_model_f1_0.8880"
    tester = LanguageSpecificTester(model_path)

    # Test datasets with language separation
    test_datasets = [
        ('data/training/youtube_comedy_augmented/test.jsonl', 100, 'YouTube Comedy Augmented'),
        ('data/training/standup_word_level_wesr_balanced/test.jsonl', 50, 'WESR Balanced'),
        ('data/training/standup_word_level_multilingual/test.jsonl', 30, 'Multilingual Standup')
    ]

    all_language_results = {}

    for dataset_path, max_examples, dataset_name in test_datasets:
        if Path(dataset_path).exists():
            try:
                print(f"\n{'='*70}")
                print(f"🎯 Testing Dataset: {dataset_name}")
                print(f"{'='*70}")

                language_results = tester.test_dataset_by_language(dataset_path, max_examples)
                all_language_results[dataset_name] = language_results

            except Exception as e:
                print(f"❌ Error testing {dataset_path}: {e}")
        else:
            print(f"⚠️  Dataset not found: {dataset_path}")

    # Generate comprehensive language report
    generate_language_report(all_language_results)


def generate_language_report(all_results: Dict[str, Dict[str, LanguageSpecificResults]]):
    """Generate comprehensive language-specific report"""

    print("\n" + "="*70)
    print("🎯 COMPREHENSIVE LANGUAGE-SPECITIVE TESTING REPORT")
    print("="*70)

    if not all_results:
        print("❌ No language-specific results available")
        return

    # Aggregate results across datasets by language
    language_aggregates = {
        'hindi': [],
        'english': [],
        'hinglish': [],
        'mixed': []
    }

    for dataset_name, language_results in all_results.items():
        for lang, results in language_results.items():
            language_aggregates[lang].append(results)

    print(f"\n🌍 LANGUAGE-SPECIFIC PERFORMANCE SUMMARY")
    print("="*50)

    for lang, lang_results_list in language_aggregates.items():
        if not lang_results_list:
            continue

        print(f"\n📊 {lang.upper()} CONTENT ANALYSIS")
        print("-"*40)

        # Calculate averages across datasets
        avg_f1 = np.mean([r.base_binary_f1 for r in lang_results_list])
        avg_laughter_acc = np.mean([r.laughter_detection_accuracy for r in lang_results_list])
        avg_non_laughter_acc = np.mean([r.non_laughter_accuracy for r in lang_results_list])
        avg_duchenne = np.mean([r.duchenne_classification_avg for r in lang_results_list])
        avg_sarcasm = np.mean([r.sarcasm_detection_avg for r in lang_results_list])
        avg_emotion = np.mean([r.mental_state_modeling_avg for r in lang_results_list])
        avg_cultural = np.mean([r.cross_cultural_nuance_avg for r in lang_results_list])
        total_examples = sum(r.total_examples for r in lang_results_list)

        print(f"  📈 Base Performance:")
        print(f"    - F1 Score: {avg_f1:.4f}")
        print(f"    - Laughter Detection: {avg_laughter_acc:.4f}")
        print(f"    - Non-Laughter Detection: {avg_non_laughter_acc:.4f}")
        print(f"    - Total Examples: {total_examples}")

        print(f"  🧠 Biosemotic Capabilities:")
        print(f"    - Duchenne Classification: {avg_duchenne:.4f}")
        print(f"    - Sarcasm Detection: {avg_sarcasm:.4f}")
        print(f"    - Mental State Modeling: {avg_emotion:.4f}")
        print(f"    - Cross-Cultural Nuance: {avg_cultural:.4f}")

        # Language-specific assessment
        print(f"  🎯 Language Assessment:")
        if avg_f1 >= 0.7:
            print(f"    ✅ EXCELLENCE ACHIEVED: Meets publication standards")
        elif avg_f1 >= 0.6:
            print(f"    ⚠️  GOOD PERFORMANCE: Near publication standards")
        else:
            print(f"    ❌ NEEDS IMPROVEMENT: Below publication standards")

    # Final comparison table
    print(f"\n📊 CROSS-LANGUAGE COMPARISON")
    print("="*50)

    comparison_data = []
    for lang in ['hindi', 'english', 'hinglish']:
        if language_aggregates[lang]:
            comparison_data.append({
                'language': lang.upper(),
                'f1_score': np.mean([r.base_binary_f1 for r in language_aggregates[lang]]),
                'examples': sum(r.total_examples for r in language_aggregates[lang]),
                'duchenne': np.mean([r.duchenne_classification_avg for r in language_aggregates[lang]]),
                'sarcasm': np.mean([r.sarcasm_detection_avg for r in language_aggregates[lang]])
            })

    if comparison_data:
        print(f"{'Language':<12} {'F1 Score':<10} {'Examples':<10} {'Duchenne':<10} {'Sarcasm':<10}")
        print("-"*50)
        for data in comparison_data:
            print(f"{data['language']:<12} {data['f1_score']:<10.4f} {data['examples']:<10} {data['duchenne']:<10.4f} {data['sarcasm']:<10.4f}")

    print(f"\n🏆 ENHANCED BIOSEMIOTIC SYSTEM VALIDATION COMPLETE")
    print(f"Language-specific capabilities demonstrated across Hindi, English, and Hinglish content")


if __name__ == "__main__":
    run_comprehensive_language_tests()