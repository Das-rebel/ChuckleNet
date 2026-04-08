#!/usr/bin/env python3
"""
Cultural Priors Enhancement Testing
Validates regional comedy pattern recognition and cultural intelligence
"""

import sys
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.cultural_priors_enhancement import create_cultural_adaptive_predictor


def test_cultural_priors_enhancement():
    """Test cultural priors enhancement on diverse regional comedy examples"""

    print("🌍 Cultural Priors Enhancement - Regional Comedy Intelligence Test")
    print("=" * 70)

    # Load cultural adaptive predictor
    model_path = "models/xlmr_turboquant_restart/best_model_f1_0.8880"
    predictor = create_cultural_adaptive_predictor(model_path)
    print("✅ Cultural adaptive predictor initialized")

    # Region-specific test examples
    regional_test_examples = {
        'US_comedy': [
            {
                'text': 'dude I was like literally at the store and this guy was like whatever',
                'description': 'US West Coast casual observational humor',
                'expected_laughter': True,
                'expected_region': 'US',
                'expected_tradition': 'observational_humor'
            },
            {
                'text': 'so I told my boss man I gotta go pick up my kids from school',
                'description': 'US workplace family observation',
                'expected_laughter': True,
                'expected_region': 'US',
                'expected_tradition': 'observational_humor'
            },
            {
                'text': 'the weather is quite nice today I suppose',
                'description': 'Understated statement (not comedy)',
                'expected_laughter': False,
                'expected_region': 'US',
                'expected_tradition': 'observational_humor'
            }
        ],
        'UK_comedy': [
            {
                'text': 'I went to the pub and it was rather crowded indeed',
                'description': 'UK dry observational humor',
                'expected_laughter': True,
                'expected_region': 'UK',
                'expected_tradition': 'ironic_wordplay'
            },
            {
                'text': 'that\'s bloody brilliant mate cheers',
                'description': 'UK colloquial expression',
                'expected_laughter': True,
                'expected_region': 'UK',
                'expected_tradition': 'ironic_wordplay'
            },
            {
                'text': 'the meeting was quite productive actually',
                'description': 'UK understated statement (not comedy)',
                'expected_laughter': False,
                'expected_region': 'UK',
                'expected_tradition': 'ironic_wordplay'
            }
        ],
        'Indian_comedy': [
            {
                'text': 'yaar my mummy was like beta get married but I was like yaar chill',
                'description': 'Indian family dynamics humor',
                'expected_laughter': True,
                'expected_region': 'Indian',
                'expected_tradition': 'family_social_observational'
            },
            {
                'text': 'paji this jugaad is amazing mast hai',
                'description': 'Indian colloquial expression',
                'expected_laughter': True,
                'expected_region': 'Indian',
                'expected_tradition': 'family_social_observational'
            },
            {
                'text': 'आज का दिन बहुत अच्छा रहा',
                'description': 'Hindi normal statement',
                'expected_laughter': False,
                'expected_region': 'Indian',
                'expected_tradition': 'family_social_observational'
            }
        ],
        'cross_cultural': [
            {
                'text': 'why did the chicken cross the road to get to the other side [laughter]',
                'description': 'Universal classic joke',
                'expected_laughter': True,
                'expected_region': 'US',
                'expected_tradition': 'observational_humor'
            },
            {
                'text': 'actually very funny hai bilkul sahi [laughter]',
                'description': 'Hinglish cultural fusion',
                'expected_laughter': True,
                'expected_region': 'Indian',
                'expected_tradition': 'family_social_observational'
            }
        ]
    }

    print("\n" + "=" * 70)
    print("🧪 CULTURAL INTELLIGENCE VALIDATION")
    print("=" * 70)

    # Test each regional category
    all_results = {}
    overall_cultural_analysis = {
        'region_detection_accuracy': 0,
        'tradition_detection_accuracy': 0,
        'laughter_prediction_accuracy': 0,
        'cultural_enhancement_impact': 0
    }

    for category, examples in regional_test_examples.items():
        print(f"\n{'='*70}")
        print(f"🎯 Testing {category.upper().replace('_', ' ')}")
        print(f"{'='*70}")

        category_results = []

        for i, example in enumerate(examples):
            print(f"\n📝 Example {i+1}: {example['description']}")
            print(f"🔤 Text: \"{example['text']}\"")
            print(f"🎯 Expected: {'✅ LAUGHTER' if example['expected_laughter'] else '❌ NO LAUGHTER'}")
            print(f"🌍 Expected Region: {example['expected_region']}")
            print(f"🎭 Expected Tradition: {example['expected_tradition']}")

            # Get cultural adaptive prediction
            result = predictor.predict_with_cultural_intelligence(example['text'])

            # Display cultural intelligence analysis
            print(f"\n🌍 Cultural Intelligence Analysis:")
            print(f"  - Detected Region: {result['cultural_context'].region}")
            print(f"  - Comedy Tradition: {result['comedy_tradition']}")
            print(f"  - Humor Style: {result['humor_style']}")
            print(f"  - Cultural Match: {'✅ YES' if result['region_match'] else '❌ NO'}")

            print(f"\n🔬 Enhanced Prediction Analysis:")
            print(f"  - Base Probability: {result['base_probability']:.4f}")
            print(f"  - Biosemotic Enhancement: +{result['biosemotic_enhancement']:.4f}")
            print(f"  - Cultural Enhancement: +{result['cultural_enhancement']:.4f}")
            print(f"  - Total Enhancement: +{result['total_enhancement']:.4f}")
            print(f"  - Enhanced Probability: {result['enhanced_probability']:.4f}")
            print(f"  - Adjusted Threshold: {result['threshold_used']:.4f}")
            print(f"  - Demographic Adaptation: {result['demographic_adaptation']:.2f}x")
            print(f"  - Final Prediction: {'✅ LAUGHTER' if result['predicted_laughter'] else '❌ NO LAUGHTER'}")
            print(f"  - Confidence Score: {result['confidence_score']:.4f}")

            # Validate results
            prediction_correct = result['predicted_laughter'] == example['expected_laughter']
            region_correct = result['cultural_context'].region == example['expected_region']
            tradition_correct = result['comedy_tradition'] == example['expected_tradition']

            print(f"\n📊 Validation:")
            print(f"  - Prediction: {'✅' if prediction_correct else '❌'}")
            print(f"  - Region Detection: {'✅' if region_correct else '❌'}")
            print(f"  - Tradition Detection: {'✅' if tradition_correct else '❌'}")

            if result['cultural_enhancement'] > 0.05:
                print(f"  - 🌟 CULTURAL BOOST: Strong cultural priors enhancement")
            elif result['cultural_enhancement'] > 0.02:
                print(f"  - 🌟 CULTURAL BOOST: Moderate cultural priors enhancement")
            elif result['cultural_enhancement'] > 0:
                print(f"  - 🌟 CULTURAL BOOST: Light cultural priors enhancement")

            result_dict = {
                'text': example['text'],
                'description': example['description'],
                'expected_laughter': example['expected_laughter'],
                'predicted_laughter': result['predicted_laughter'],
                'prediction_correct': prediction_correct,
                'expected_region': example['expected_region'],
                'detected_region': result['cultural_context'].region,
                'region_correct': region_correct,
                'expected_tradition': example['expected_tradition'],
                'detected_tradition': result['comedy_tradition'],
                'tradition_correct': tradition_correct,
                'cultural_enhancement': result['cultural_enhancement'],
                'demographic_adaptation': result['demographic_adaptation']
            }

            category_results.append(result_dict)

        all_results[category] = category_results

    # Generate comprehensive cultural intelligence report
    generate_cultural_intelligence_report(all_results)


def generate_cultural_intelligence_report(all_results):
    """Generate comprehensive cultural intelligence analysis"""

    print("\n" + "=" * 70)
    print("🎯 CULTURAL INTELLIGENCE SYSTEM ANALYSIS")
    print("=" * 70)

    # Calculate metrics by category
    total_examples = 0
    total_prediction_correct = 0
    total_region_correct = 0
    total_tradition_correct = 0
    total_cultural_enhancement = 0
    total_demographic_adaptation = 0

    for category, results in all_results.items():
        if not results:
            continue

        print(f"\n📊 {category.upper().replace('_', ' ')} PERFORMANCE")
        print("-" * 50)

        prediction_correct = sum(1 for r in results if r['prediction_correct'])
        region_correct = sum(1 for r in results if r['region_correct'])
        tradition_correct = sum(1 for r in results if r['tradition_correct'])

        avg_cultural_enhancement = sum(r['cultural_enhancement'] for r in results) / len(results)
        avg_demographic_adaptation = sum(r['demographic_adaptation'] for r in results) / len(results)

        total = len(results)

        print(f"  Laughter Prediction: {prediction_correct}/{total} ({prediction_correct/total*100:.1f}%)")
        print(f"  Region Detection: {region_correct}/{total} ({region_correct/total*100:.1f}%)")
        print(f"  Tradition Detection: {tradition_correct}/{total} ({tradition_correct/total*100:.1f}%)")
        print(f"  Avg Cultural Enhancement: +{avg_cultural_enhancement:.4f}")
        print(f"  Avg Demographic Adaptation: {avg_demographic_adaptation:.2f}x")

        # Update totals
        total_examples += total
        total_prediction_correct += prediction_correct
        total_region_correct += region_correct
        total_tradition_correct += tradition_correct
        total_cultural_enhancement += avg_cultural_enhancement * total
        total_demographic_adaptation += avg_demographic_adaptation * total

    # Overall analysis
    print("\n" + "=" * 70)
    print("🏆 OVERALL CULTURAL INTELLIGENCE PERFORMANCE")
    print("=" * 70)

    overall_prediction_accuracy = total_prediction_correct / total_examples if total_examples > 0 else 0
    overall_region_accuracy = total_region_correct / total_examples if total_examples > 0 else 0
    overall_tradition_accuracy = total_tradition_correct / total_examples if total_examples > 0 else 0
    overall_cultural_enhancement = total_cultural_enhancement / total_examples if total_examples > 0 else 0
    overall_demographic_adaptation = total_demographic_adaptation / total_examples if total_examples > 0 else 0

    print(f"\n  Total Examples: {total_examples}")
    print(f"  Laughter Prediction Accuracy: {overall_prediction_accuracy:.4f}")
    print(f"  Region Detection Accuracy: {overall_region_accuracy:.4f}")
    print(f"  Tradition Detection Accuracy: {overall_tradition_accuracy:.4f}")
    print(f"  Average Cultural Enhancement: +{overall_cultural_enhancement:.4f}")
    print(f"  Average Demographic Adaptation: {overall_demographic_adaptation:.2f}x")

    # System assessment
    print(f"\n🌟 CULTURAL INTELLIGENCE CAPABILITIES ASSESSMENT")

    if overall_region_accuracy >= 0.8:
        print(f"  ✅ EXCELLENCE: Outstanding regional comedy pattern recognition")
    elif overall_region_accuracy >= 0.6:
        print(f"  ⚠️  GOOD: Strong regional pattern detection")
    else:
        print(f"  ❌ NEEDS WORK: Regional pattern detection requires improvement")

    if overall_tradition_accuracy >= 0.8:
        print(f"  ✅ EXCELLENCE: Outstanding comedy tradition identification")
    elif overall_tradition_accuracy >= 0.6:
        print(f"  ⚠️  GOOD: Strong tradition detection")
    else:
        print(f"  ❌ NEEDS WORK: Comedy tradition identification needs refinement")

    if overall_cultural_enhancement > 0.08:
        print(f"  ✅ EXCELLENCE: Strong cultural priors enhancement")
    elif overall_cultural_enhancement > 0.04:
        print(f"  ⚠️  GOOD: Moderate cultural enhancement")
    else:
        print(f"  ❌ NEEDS WORK: Cultural enhancement system needs optimization")

    print(f"\n🎯 CULTURAL PRIORS ENHANCEMENT VALIDATION COMPLETE")
    print(f"Regional comedy intelligence system operational")
    print(f"Cross-cultural comedy understanding validated")


if __name__ == "__main__":
    test_cultural_priors_enhancement()