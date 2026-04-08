#!/usr/bin/env python3
"""
Comprehensive Adaptive Threshold System Testing
Validates the improved approach to address conservative calibration issue
"""

import sys
from pathlib import Path
import json
import time

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.adaptive_threshold_predictor import create_adaptive_predictor


def test_adaptive_threshold_system():
    """Test the adaptive threshold system on our language-specific examples"""

    print("🎯 Adaptive Threshold System - Comprehensive Validation")
    print("=" * 70)

    # Load adaptive predictor
    model_path = "models/xlmr_turboquant_restart/best_model_f1_0.8880"
    predictor = create_adaptive_predictor(model_path)
    print("✅ Adaptive threshold predictor initialized")

    # Our original test examples
    test_examples = {
        'hindi': [
            {
                'text': 'अरे वाह बहुत अच्छा [हास्य]',
                'description': 'Pure Hindi with laughter marker',
                'expected_laughter': True
            },
            {
                'text': 'क्या बात है यार बहुत मज़ेदार है',
                'description': 'Hindi comedy expression',
                'expected_laughter': True
            },
            {
                'text': 'आज का दिन बहुत अच्छा रहा',
                'description': 'Hindi normal statement',
                'expected_laughter': False
            }
        ],
        'english': [
            {
                'text': 'why did the chicken cross the road to get to the other side [laughter]',
                'description': 'Classic English joke with laughter',
                'expected_laughter': True
            },
            {
                'text': 'thank you so much for being here tonight you\'ve been a great audience',
                'description': 'English show closing',
                'expected_laughter': False
            },
            {
                'text': 'so I walked into a bank and the teller asked for my ID [audience laughing]',
                'description': 'English comedy setup with audience reaction',
                'expected_laughter': True
            }
        ],
        'hinglish': [
            {
                'text': 'yaar kya baat hai bahut mast hai [laughter]',
                'description': 'Hinglish with Latin script Hindi words',
                'expected_laughter': True
            },
            {
                'text': 'actually very funny hai bilkul sahi',
                'description': 'Hinglish code-mixed comedy',
                'expected_laughter': True
            },
            {
                'text': 'so basically what happened was very theek hai',
                'description': 'Hinglish normal conversation',
                'expected_laughter': False
            }
        ]
    }

    print("\n" + "=" * 70)
    print("🧪 ADAPTIVE THRESHOLD SYSTEM VALIDATION")
    print("=" * 70)

    # Test each language
    all_results = {}
    overall_improvements = {}

    for language, examples in test_examples.items():
        print(f"\n{'='*70}")
        print(f"🎯 Testing {language.upper()} with Adaptive Thresholds")
        print(f"{'='*70}")

        language_results = []
        improvements = []

        for i, example in enumerate(examples):
            print(f"\n📝 Example {i+1}: {example['description']}")
            print(f"🔤 Text: \"{example['text']}\"")
            print(f"🎯 Expected: {'✅ LAUGHTER' if example['expected_laughter'] else '❌ NO LAUGHTER'}")

            # Get adaptive prediction
            result = predictor.predict_with_adaptive_threshold(example['text'])

            # Display adaptive analysis
            print(f"\n🔬 Adaptive Threshold Analysis:")
            print(f"  - Language Detected: {result.language}")
            print(f"  - Base Probability: {result.base_probability:.4f}")
            print(f"  - Biosemotic Enhancement: +{result.biosemotic_enhancement:.4f}")
            print(f"  - Adjusted Probability: {result.adjusted_probability:.4f}")
            print(f"  - Adaptive Threshold: {result.threshold_used:.4f}")
            print(f"  - Final Prediction: {'✅ LAUGHTER' if result.predicted_laughter else '❌ NO LAUGHTER'}")
            print(f"  - Confidence Score: {result.confidence_score:.4f}")
            print(f"  - Cultural Context: {result.cultural_context}")

            # Compare with original 0.5 threshold
            original_prediction = result.base_probability > 0.5
            adaptive_prediction = result.predicted_laughter

            print(f"\n📊 Comparison:")
            print(f"  - Original (0.5 threshold): {'✅' if original_prediction == example['expected_laughter'] else '❌'}")
            print(f"  - Adaptive ({result.threshold_used:.4f} threshold): {'✅' if adaptive_prediction == example['expected_laughter'] else '❌'}")

            # Track improvement
            improvement = "NO_CHANGE"
            if original_prediction != example['expected_laughter'] and adaptive_prediction == example['expected_laughter']:
                improvement = "FIXED"
                improvements.append(1)
                print(f"  - ✅ IMPROVEMENT: Adaptive threshold fixed the error!")
            elif original_prediction == example['expected_laughter'] and adaptive_prediction != example['expected_laughter']:
                improvement = "REGRESSED"
                improvements.append(-1)
                print(f"  - ⚠️  REGRESSION: Adaptive threshold introduced error")
            else:
                improvements.append(0)
                print(f"  - ➡️  NO CHANGE: Both methods agree")

            result_dict = {
                'text': example['text'],
                'description': example['description'],
                'expected': example['expected_laughter'],
                'base_prob': result.base_probability,
                'adjusted_prob': result.adjusted_probability,
                'threshold': result.threshold_used,
                'biosemotic_boost': result.biosemotic_enhancement,
                'original_correct': original_prediction == example['expected_laughter'],
                'adaptive_correct': adaptive_prediction == example['expected_laughter'],
                'improvement': improvement
            }

            language_results.append(result_dict)

        all_results[language] = language_results
        overall_improvements[language] = improvements

    # Generate comprehensive improvement report
    generate_improvement_report(all_results, overall_improvements)


def generate_improvement_report(all_results, overall_improvements):
    """Generate comprehensive improvement analysis"""

    print("\n" + "=" * 70)
    print("🎯 ADAPTIVE THRESHOLD IMPROVEMENT ANALYSIS")
    print("=" * 70)

    # Calculate metrics by language
    for language, results in all_results.items():
        improvements = overall_improvements[language]

        original_correct = sum(1 for r in results if r['original_correct'])
        adaptive_correct = sum(1 for r in results if r['adaptive_correct'])

        fixed = sum(1 for i in improvements if i == 1)
        regressed = sum(1 for i in improvements if i == -1)
        unchanged = sum(1 for i in improvements if i == 0)

        total = len(results)

        print(f"\n📊 {language.upper()} PERFORMANCE ANALYSIS")
        print("-" * 50)
        print(f"  Original Accuracy: {original_correct}/{total} ({original_correct/total*100:.1f}%)")
        print(f"  Adaptive Accuracy: {adaptive_correct}/{total} ({adaptive_correct/total*100:.1f}%)")
        print(f"\n  Improvements:")
        print(f"    - Fixed Errors: {fixed}")
        print(f"    - Regressions: {regressed}")
        print(f"    - Unchanged: {unchanged}")

        if adaptive_correct > original_correct:
            improvement_pct = ((adaptive_correct - original_correct) / total) * 100
            print(f"  ✅ NET IMPROVEMENT: +{improvement_pct:.1f}%")
        elif adaptive_correct < original_correct:
            regression_pct = ((original_correct - adaptive_correct) / total) * 100
            print(f"  ⚠️  NET REGRESSION: -{regression_pct:.1f}%")
        else:
            print(f"  ➡️  NO CHANGE: Accuracy maintained")

    # Overall analysis
    print("\n" + "=" * 70)
    print("🏆 OVERALL SYSTEM PERFORMANCE")
    print("=" * 70)

    total_original = sum(sum(1 for r in results if r['original_correct']) for results in all_results.values())
    total_adaptive = sum(sum(1 for r in results if r['adaptive_correct']) for results in all_results.values())
    total_examples = sum(len(results) for results in all_results.values())

    all_improvements = [i for improvements in overall_improvements.values() for i in improvements]
    total_fixed = sum(1 for i in all_improvements if i == 1)
    total_regressed = sum(1 for i in all_improvements if i == -1)
    total_unchanged = sum(1 for i in all_improvements if i == 0)

    print(f"\n  Total Examples: {total_examples}")
    print(f"  Original Correct: {total_original}/{total_examples} ({total_original/total_examples*100:.1f}%)")
    print(f"  Adaptive Correct: {total_adaptive}/{total_examples} ({total_adaptive/total_examples*100:.1f}%)")
    print(f"\n  System-Wide Changes:")
    print(f"    - Errors Fixed: {total_fixed}")
    print(f"    - Regressions: {total_regressed}")
    print(f"    - Unchanged: {total_unchanged}")

    if total_adaptive > total_original:
        improvement_pct = ((total_adaptive - total_original) / total_examples) * 100
        print(f"\n  ✅ OVERALL IMPROVEMENT: +{improvement_pct:.1f}%")
        print(f"  🎯 SUCCESS: Adaptive threshold system enhanced performance!")
    elif total_adaptive < total_original:
        regression_pct = ((total_original - total_adaptive) / total_examples) * 100
        print(f"\n  ⚠️  OVERALL REGRESSION: -{regression_pct:.1f}%")
        print(f"  📉 ISSUE: Adaptive system needs refinement")
    else:
        print(f"\n  ➡️  NO OVERALL CHANGE: Performance maintained")

    # Biosemotic enhancement analysis
    print(f"\n🧠 BIOSEMIOTIC ENHANCEMENT ANALYSIS")
    print("=" * 50)

    all_results_list = [r for results in all_results.values() for r in results]

    avg_base_prob = sum(r['base_prob'] for r in all_results_list) / len(all_results_list)
    avg_adjusted_prob = sum(r['adjusted_prob'] for r in all_results_list) / len(all_results_list)
    avg_threshold = sum(r['threshold'] for r in all_results_list) / len(all_results_list)
    avg_boost = sum(r['biosemotic_boost'] for r in all_results_list) / len(all_results_list)

    print(f"  Average Base Probability: {avg_base_prob:.4f}")
    print(f"  Average Adjusted Probability: {avg_adjusted_prob:.4f}")
    print(f"  Average Enhancement: +{avg_boost:.4f}")
    print(f"  Average Threshold Used: {avg_threshold:.4f}")

    print(f"\n🎯 ADAPTIVE THRESHOLD SYSTEM VALIDATION COMPLETE")
    print(f"Biosemotic enhancements successfully integrated into base prediction")
    print(f"Language-specific and content-aware thresholds operational")


if __name__ == "__main__":
    test_adaptive_threshold_system()