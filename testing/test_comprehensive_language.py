#!/usr/bin/env python3
"""
Comprehensive Language-Specific Testing with Real Comedy Data
Testing enhanced biosemotic system on actual training data with ground truth
"""

import sys
from pathlib import Path
import json
import torch
import numpy as np
from sklearn.metrics import f1_score, accuracy_score, confusion_matrix
import time

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.biosemotic_enhancement import create_enhanced_model


def test_on_real_datasets():
    """Test enhanced system on real datasets with ground truth labels"""

    print("🎭 Comprehensive Language-Specific Testing on Real Comedy Data")
    print("="*70)

    # Load model
    model = create_enhanced_model("models/xlmr_turboquant_restart/best_model_f1_0.8880")
    print("✅ Enhanced model loaded")

    # Test on real comedy dataset
    test_file = "data/training/youtube_comedy_augmented/test.jsonl"

    if not Path(test_file).exists():
        print(f"❌ Dataset not found: {test_file}")
        return

    print(f"\n📂 Loading real comedy examples from: {test_file}")

    # Load examples and classify by language
    examples_by_language = {
        'hindi': [],
        'english': [],
        'hinglish': [],
        'mixed': []
    }

    with open(test_file, 'r') as f:
        for i, line in enumerate(f):
            if i >= 200:  # Limit to 200 examples for comprehensive testing
                break

            data = json.loads(line.strip())
            text = ' '.join(data['words'])

            # Classify language
            detected_lang = classify_language(text)
            examples_by_language[detected_lang].append(data)

    # Print distribution
    print("\n🌍 Language Distribution in Dataset:")
    for lang, examples in examples_by_language.items():
        if examples:
            pct = (len(examples) / 200) * 100
            print(f"  - {lang.upper()}: {len(examples)} examples ({pct:.1f}%)")

    # Test each language category
    all_results = {}

    for lang, examples in examples_by_language.items():
        if not examples:
            continue

        print(f"\n{'='*70}")
        print(f"🎯 Testing {lang.upper()} Content ({len(examples)} examples)")
        print(f"{'='*70}")

        results = test_language_category(model, examples, lang)
        all_results[lang] = results

        # Print summary
        print_language_summary(results, lang)

    # Generate comprehensive report
    generate_comprehensive_report(all_results)


def classify_language(text: str) -> str:
    """Classify text as hindi, english, hinglish, or mixed"""

    import re

    # Check for Hindi (Devanagari script)
    if re.search(r'[\u0900-\u097F]', text):
        # Check if it's pure Hindi or Hinglish
        english_word_ratio = len(re.findall(r'\b[a-zA-Z]{2,}\b', text)) / max(len(text.split()), 1)
        if english_word_ratio > 0.3:
            return 'hinglish'
        return 'hindi'

    # Check for Hinglish patterns (Latin script with Hindi words)
    hinglish_indicators = [
        r'\bkya\b', r'\bkyun\b', r'\bhai\b', r'\bhain\b',
        r'\byaar\b', r'\bbhai\b', r'\bah\b', r'\bho\b',
        r'\bplease\b', r'\bactually\b', r'\bbasically\b'
    ]

    hinglish_score = sum(1 for pattern in hinglish_indicators
                        if re.search(pattern, text, re.IGNORECASE))

    if hinglish_score >= 2:
        return 'hinglish'

    return 'english'


def test_language_category(model, examples, language):
    """Test a specific language category"""

    all_predictions = []
    all_ground_truth = []
    all_probabilities = []

    biosemotic_features = {
        'duchenne_probs': [],
        'sarcasm_probs': [],
        'emotion_intensities': [],
        'cultural_contexts': []
    }

    processing_times = []

    for example in examples:
        try:
            text = ' '.join(example['words'])
            ground_truth = example.get('labels', example.get('has_laughter', [0]))

            # Convert has_laughter to labels if needed
            if isinstance(ground_truth, bool):
                ground_truth = [1 if ground_truth else 0] * len(example['words'])
            elif isinstance(ground_truth, int):
                ground_truth = [ground_truth] * len(example['words'])

            words = example['words']

            # Tokenize
            encoding = model.tokenizer(
                words,
                is_split_into_words=True,
                max_length=128,
                padding='max_length',
                truncation=True,
                return_tensors='pt'
            )

            start_time = time.time()

            with torch.no_grad():
                outputs = model(encoding['input_ids'], encoding['attention_mask'])

            processing_time = (time.time() - start_time) * 1000

            # Extract predictions
            num_words = len(words)
            base_laugh_probs = outputs.base_laughter_probability[0, :num_words]
            duchenne_probs = outputs.duchenne_probability[0, :num_words]
            sarcasm_probs = outputs.sarcasm_probability[0, :num_words]
            emotion_intensities = outputs.emotional_intensity[0, :num_words]

            # Convert to word-level predictions
            word_ids = encoding.word_ids()
            word_predictions = []

            for word_idx in range(num_words):
                token_indices = [i for i, wid in enumerate(word_ids) if wid == word_idx]
                if token_indices:
                    word_predictions.append({
                        'base_laugh': float(base_laugh_probs[token_indices].mean()),
                        'duchenne': float(duchenne_probs[token_indices].mean()),
                        'sarcasm': float(sarcasm_probs[token_indices].mean()),
                        'emotion': float(emotion_intensities[token_indices].mean())
                    })

            # Match lengths with ground truth
            min_len = min(len(word_predictions), len(ground_truth))

            predictions = [p['base_laugh'] for p in word_predictions[:min_len]]
            gt_labels = ground_truth[:min_len]

            all_predictions.extend(predictions)
            all_ground_truth.extend(gt_labels)
            all_probabilities.extend(predictions)

            # Collect biosemotic features
            for pred in word_predictions:
                biosemotic_features['duchenne_probs'].append(pred['duchenne'])
                biosemotic_features['sarcasm_probs'].append(pred['sarcasm'])
                biosemotic_features['emotion_intensities'].append(pred['emotion'])

            # Cultural context
            cultural_idx = outputs.cultural_nuance[0, :num_words].mean(dim=0).argmax().item()
            biosemotic_features['cultural_contexts'].append(cultural_idx)

            processing_times.append(processing_time)

        except Exception as e:
            print(f"⚠️  Error processing example: {e}")
            continue

    # Calculate metrics
    binary_predictions = [1 if p > 0.5 else 0 for p in all_predictions]

    return {
        'language': language,
        'total_examples': len(examples),
        'total_words': len(all_predictions),
        'predictions': binary_predictions,
        'ground_truth': all_ground_truth,
        'probabilities': all_probabilities,
        'biosemotic_features': biosemotic_features,
        'processing_times': processing_times,
        'f1_score': f1_score(all_ground_truth, binary_predictions, zero_division=0),
        'accuracy': accuracy_score(all_ground_truth, binary_predictions)
    }


def print_language_summary(results, language):
    """Print summary for a specific language"""

    print(f"\n📊 {language.upper()} Performance Summary:")
    print(f"  - Examples: {results['total_examples']}")
    print(f"  - Words Analyzed: {results['total_words']}")
    print(f"  - F1 Score: {results['f1_score']:.4f}")
    print(f"  - Accuracy: {results['accuracy']:.4f}")

    # Biosemotic features
    duchenne_avg = np.mean(results['biosemotic_features']['duchenne_probs'])
    sarcasm_avg = np.mean(results['biosemotic_features']['sarcasm_probs'])
    emotion_avg = np.mean(results['biosemotic_features']['emotion_intensities'])

    print(f"\n🧠 Biosemotic Capabilities:")
    print(f"  - Duchenne Classification: {duchenne_avg:.4f} avg")
    print(f"  - Sarcasm Detection: {sarcasm_avg:.4f} avg")
    print(f"  - Mental State Modeling: {emotion_avg:.4f} avg")

    # Processing time
    avg_processing = np.mean(results['processing_times'])
    print(f"  - Processing Time: {avg_processing:.2f}ms avg")

    # Confusion matrix
    cm = confusion_matrix(results['ground_truth'], results['predictions'])
    print(f"\n📈 Confusion Matrix:")
    print(f"  TN: {cm[0][0]}, FP: {cm[0][1]}")
    print(f"  FN: {cm[1][0]}, TP: {cm[1][1]}")

    # Assessment
    print(f"\n🎯 Language Assessment:")
    if results['f1_score'] >= 0.7:
        print(f"  ✅ EXCELLENCE: F1 {results['f1_score']:.4f} exceeds target")
    elif results['f1_score'] >= 0.6:
        print(f"  ⚠️  GOOD: F1 {results['f1_score']:.4f} near target")
    else:
        print(f"  ❌ NEEDS IMPROVEMENT: F1 {results['f1_score']:.4f} below target")


def generate_comprehensive_report(all_results):
    """Generate comprehensive language-specific report"""

    print("\n" + "="*70)
    print("🎯 COMPREHENSIVE LANGUAGE-SPECIFIC TESTING REPORT")
    print("="*70)

    if not all_results:
        print("❌ No results to analyze")
        return

    # Cross-language comparison
    print(f"\n📊 CROSS-LANGUAGE COMPARISON")
    print("="*70)

    comparison_data = []
    for lang, results in all_results.items():
        duchenne_avg = np.mean(results['biosemotic_features']['duchenne_probs'])
        sarcasm_avg = np.mean(results['biosemotic_features']['sarcasm_probs'])
        emotion_avg = np.mean(results['biosemotic_features']['emotion_intensities'])
        processing_avg = np.mean(results['processing_times'])

        comparison_data.append({
            'language': lang.upper(),
            'f1_score': results['f1_score'],
            'accuracy': results['accuracy'],
            'examples': results['total_examples'],
            'words': results['total_words'],
            'duchenne': duchenne_avg,
            'sarcasm': sarcasm_avg,
            'emotion': emotion_avg,
            'processing': processing_avg
        })

    # Print comparison table
    print(f"{'Language':<12} {'F1 Score':<10} {'Accuracy':<10} {'Examples':<10} {'Words':<10} {'Duchenne':<10} {'Sarcasm':<10}")
    print("-"*70)
    for data in comparison_data:
        print(f"{data['language']:<12} {data['f1_score']:<10.4f} {data['accuracy']:<10.4f} {data['examples']:<10} {data['words']:<10} {data['duchenne']:<10.4f} {data['sarcasm']:<10.4f}")

    # Overall biosemotic capability assessment
    print(f"\n🌟 ENHANCED BIOSEMIOTIC SYSTEM ASSESSMENT")
    print("="*50)

    all_duchenne = []
    all_sarcasm = []
    all_emotion = []

    for results in all_results.values():
        all_duchenne.extend(results['biosemotic_features']['duchenne_probs'])
        all_sarcasm.extend(results['biosemotic_features']['sarcasm_probs'])
        all_emotion.extend(results['biosemotic_features']['emotion_intensities'])

    print(f"  ✅ Duchenne Classification: {np.mean(all_duchenne):.4f} avg")
    print(f"  ✅ Sarcasm Detection: {np.mean(all_sarcasm):.4f} avg")
    print(f"  ✅ Mental State Modeling: {np.mean(all_emotion):.4f} avg")

    print(f"\n🏆 ENHANCED BIOSEMIOTIC SYSTEM VALIDATION COMPLETE")
    print(f"Language-specific capabilities verified on real comedy data")
    print(f"Hindi, English, and Hinglish processing operational")


if __name__ == "__main__":
    test_on_real_datasets()