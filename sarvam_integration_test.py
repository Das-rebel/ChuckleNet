#!/usr/bin/env python3
"""
Sarvam Translation Pipeline Integration Test
Tests how well Google Translate detection works with Sarvam translation
"""

import requests
import json
import time
from typing import Dict, List, Optional

class SarvamTranslationService:
    """Sarvam Translation API Client"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.api_url = "https://api.sarvam.ai/translate"

    def translate(self, text: str, source_lang: str, target_lang: str) -> Dict:
        """
        Translate text using Sarvam API
        Returns: {'translation': str, 'status': str, 'response_time': float}
        """
        start_time = time.time()

        if not self.api_key:
            return {
                'translation': None,
                'status': 'error',
                'error': 'No API key provided',
                'response_time': time.time() - start_time
            }

        try:
            headers = {
                'Content-Type': 'application/json',
                'api-subscription-key': self.api_key
            }

            # Map language codes to Sarvam format
            lang_mapping = {
                'hi': 'hi-IN',
                'en': 'en-IN',
                'bn': 'bn-IN'
            }

            sarvam_source = lang_mapping.get(source_lang, source_lang)
            sarvam_target = lang_mapping.get(target_lang, target_lang)

            payload = {
                'input': text,
                'source_language_code': sarvam_source,
                'target_language_code': sarvam_target,
                'gender': 'female'  # Default gender
            }

            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                translation = result.get('translated_text', '')

                return {
                    'translation': translation,
                    'status': 'success',
                    'response_time': time.time() - start_time,
                    'error': None
                }
            else:
                return {
                    'translation': None,
                    'status': 'failed',
                    'error': f"HTTP {response.status_code}",
                    'response_time': time.time() - start_time
                }

        except Exception as e:
            return {
                'translation': None,
                'status': 'error',
                'error': str(e),
                'response_time': time.time() - start_time
            }

class GoogleLanguageDetector:
    """Google Translate API Client for Language Detection"""

    def __init__(self):
        self.api_url = "https://translate.googleapis.com/translate_a/single"

    def detect_language(self, text: str) -> Dict:
        """Detect language using Google Translate API"""
        start_time = time.time()

        try:
            params = {
                'client': 'gtx',
                'sl': 'auto',
                'tl': 'en',
                'dt': 't',
                'q': text
            }

            response = requests.get(self.api_url, params=params, timeout=10)

            if response.status_code == 200:
                result_data = response.json()

                if len(result_data) > 2 and result_data[2]:
                    detected_language = result_data[2]
                    confidence = 0.95
                else:
                    detected_language = 'unknown'
                    confidence = 0.0

                return {
                    'detected_language': detected_language,
                    'confidence': confidence,
                    'response_time': time.time() - start_time,
                    'success': True,
                    'error': None
                }
            else:
                return {
                    'detected_language': 'unknown',
                    'confidence': 0.0,
                    'response_time': time.time() - start_time,
                    'success': False,
                    'error': f"HTTP {response.status_code}"
                }

        except Exception as e:
            return {
                'detected_language': 'unknown',
                'confidence': 0.0,
                'response_time': time.time() - start_time,
                'success': False,
                'error': str(e)
            }

class IntegratedTranslationPipeline:
    """Integrated pipeline combining Google detection with Sarvam translation"""

    def __init__(self, sarvam_api_key: Optional[str] = None):
        self.google_detector = GoogleLanguageDetector()
        self.sarvam_translator = SarvamTranslationService(sarvam_api_key)

    def translate_with_detection(self, text: str, target_language: str = 'en') -> Dict:
        """
        Detect language and translate using the integrated pipeline
        Returns: {'detection': Dict, 'translation': Dict, 'total_time': float}
        """
        pipeline_start = time.time()

        # Step 1: Detect language
        detection_result = self.google_detector.detect_language(text)

        if not detection_result['success']:
            return {
                'detection': detection_result,
                'translation': {
                    'translation': None,
                    'status': 'skipped',
                    'error': 'Language detection failed'
                },
                'total_time': time.time() - pipeline_start
            }

        detected_language = detection_result['detected_language']

        # Skip translation if already in target language
        if detected_language == target_language:
            return {
                'detection': detection_result,
                'translation': {
                    'translation': text,  # Return original text
                    'status': 'skipped_no_translation_needed',
                    'error': None
                },
                'total_time': time.time() - pipeline_start
            }

        # Step 2: Translate using Sarvam
        translation_result = self.sarvam_translator.translate(
            text,
            detected_language,
            target_language
        )

        return {
            'detection': detection_result,
            'translation': translation_result,
            'total_time': time.time() - pipeline_start
        }

def run_integration_tests(sarvam_api_key: Optional[str] = None):
    """Run integration tests for the translation pipeline"""

    print("🌍 SARVAM TRANSLATION PIPELINE INTEGRATION TEST")
    print("="*80)

    pipeline = IntegratedTranslationPipeline(sarvam_api_key)

    # Test cases covering various scenarios
    test_cases = [
        # Pure language tests
        {'text': 'नमस्ते, आप कैसे हैं?', 'expected_detection': 'hi', 'name': 'Pure Hindi'},
        {'text': 'নমস্কার, আপনি কেমন আছেন?', 'expected_detection': 'bn', 'name': 'Pure Bengali'},
        {'text': 'Hello, how are you?', 'expected_detection': 'en', 'name': 'Pure English'},

        # Hinglish tests
        {'text': 'Weather kaisa hai aaj?', 'expected_detection': 'hi', 'name': 'Hinglish Weather'},
        {'text': 'Mujhe Python code likhna hai', 'expected_detection': 'hi', 'name': 'Hinglish Technical'},
        {'text': 'Please mujhe help karo', 'expected_detection': 'hi', 'name': 'Hinglish Request'},

        # Benglish tests
        {'text': 'Weather kemon ache aaj?', 'expected_detection': 'bn', 'name': 'Benglish Weather'},
        {'text': 'Amake Python code likhte hobe', 'expected_detection': 'bn', 'name': 'Benglish Technical'},
        {'text': 'Please amake help koro', 'expected_detection': 'bn', 'name': 'Benglish Request'},

        # Mixed script tests
        {'text': 'আজ code explain করো please', 'expected_detection': 'bn', 'name': 'Mixed Script Bengali'},
        {'text': 'आज code explain करो please', 'expected_detection': 'hi', 'name': 'Mixed Script Hindi'},

        # Complex scenarios
        {'text': 'Hey bhai, aaj weather kaisa hai? Please batao', 'expected_detection': 'hi', 'name': 'Complex Hinglish'},
        {'text': 'Hey bhai, aaj weather kemon ache? Please bolo', 'expected_detection': 'bn', 'name': 'Complex Benglish'}
    ]

    results = []

    for test in test_cases:
        print(f"\n📋 Test: {test['name']}")
        print(f"   Input: '{test['text']}'")
        print(f"   Expected Detection: {test['expected_detection']}")

        # Run pipeline test
        result = pipeline.translate_with_detection(test['text'], 'en')

        detection = result['detection']
        translation = result['translation']

        # Analyze results
        detection_correct = detection['detected_language'] == test['expected_detection']

        print(f"   🔍 Detection: {detection['detected_language']} "
              f"{'✅' if detection_correct else '❌'} "
              f"({detection['response_time']:.3f}s)")
        print(f"   📝 Translation Status: {translation['status']}")

        if translation['translation']:
            print(f"   🌐 Translation: {translation['translation']}")
            if 'response_time' in translation and translation['response_time']:
                print(f"   ⏱️  Translation Time: {translation['response_time']:.3f}s")

        if translation['error']:
            print(f"   ⚠️  Translation Error: {translation['error']}")

        print(f"   ⏱️  Total Pipeline Time: {result['total_time']:.3f}s")

        test_result = {
            'test_name': test['name'],
            'input_text': test['text'],
            'expected_detection': test['expected_detection'],
            'detection_result': detection,
            'detection_correct': detection_correct,
            'translation_result': translation,
            'pipeline_time': result['total_time'],
            'timestamp': time.time()
        }

        results.append(test_result)

    return results

def generate_integration_report(results: List[Dict]) -> Dict:
    """Generate comprehensive integration report"""

    print("\n" + "="*80)
    print("📊 INTEGRATION TEST REPORT GENERATION")
    print("="*80)

    report = {
        'timestamp': time.time(),
        'total_tests': len(results),
        'summary': {},
        'detailed_results': results,
        'recommendations': []
    }

    # Detection accuracy
    detection_correct = sum(1 for r in results if r['detection_correct'])
    detection_accuracy = (detection_correct / len(results) * 100) if results else 0

    # Translation success rate
    translation_success = sum(1 for r in results if r['translation_result']['status'] == 'success')
    translation_rate = (translation_success / len(results) * 100) if results else 0

    # Pipeline performance
    pipeline_times = [r['pipeline_time'] for r in results]
    avg_pipeline_time = sum(pipeline_times) / len(pipeline_times) if pipeline_times else 0

    report['summary'] = {
        'detection_accuracy': detection_accuracy,
        'translation_success_rate': translation_rate,
        'avg_pipeline_time': avg_pipeline_time,
        'total_successful_translations': translation_success,
        'total_correct_detections': detection_correct
    }

    # Language-specific analysis
    language_performance = {}

    for result in results:
        expected_lang = result['expected_detection']
        if expected_lang not in language_performance:
            language_performance[expected_lang] = {'detection_correct': 0, 'total': 0}

        language_performance[expected_lang]['total'] += 1
        if result['detection_correct']:
            language_performance[expected_lang]['detection_correct'] += 1

    report['summary']['language_performance'] = {}

    for lang, stats in language_performance.items():
        accuracy = (stats['detection_correct'] / stats['total'] * 100) if stats['total'] > 0 else 0
        report['summary']['language_performance'][lang] = {
            'accuracy': accuracy,
            'correct': stats['detection_correct'],
            'total': stats['total']
        }

    # Production readiness assessment
    production_ready = detection_accuracy >= 85 and translation_rate >= 80

    report['summary']['production_readiness'] = {
        'target_detection_accuracy': 85,
        'detection_meets_target': detection_accuracy >= 85,
        'target_translation_success': 80,
        'translation_meets_target': translation_rate >= 80,
        'production_ready': production_ready
    }

    # Recommendations
    recommendations = []

    if production_ready:
        recommendations.append("✅ System meets production readiness criteria")
        recommendations.append("✅ Detection accuracy and translation success rates are acceptable")
        recommendations.append("✅ Ready for deployment with Google + Sarvam pipeline")
    else:
        if detection_accuracy < 85:
            recommendations.append(f"⚠️ Detection accuracy ({detection_accuracy:.1f}%) below 85% target")
            recommendations.append("💡 Consider adding fallback detection mechanisms")
        if translation_rate < 80:
            recommendations.append(f"⚠️ Translation success rate ({translation_rate:.1f}%) below 80% target")
            recommendations.append("💡 Check Sarvam API availability and rate limits")

    # Performance recommendations
    if avg_pipeline_time > 2.0:
        recommendations.append(f"⚠️ Average pipeline time ({avg_pipeline_time:.1f}s) exceeds 2s target")
        recommendations.append("💡 Consider caching frequent translations")
    else:
        recommendations.append(f"✅ Excellent pipeline performance: {avg_pipeline_time:.1f}s average")

    report['recommendations'] = recommendations

    return report

def print_integration_summary(report: Dict):
    """Print formatted integration summary"""

    print("\n" + "="*80)
    print("📊 INTEGRATION TEST SUMMARY")
    print("="*80)

    summary = report['summary']

    # Overall performance
    print("\n🎯 OVERALL PIPELINE PERFORMANCE:")
    print(f"   Detection Accuracy: {summary['detection_accuracy']:.1f}% "
          f"({summary['total_correct_detections']}/{report['total_tests']})")
    print(f"   Translation Success Rate: {summary['translation_success_rate']:.1f}% "
          f"({summary['total_successful_translations']}/{report['total_tests']})")
    print(f"   Average Pipeline Time: {summary['avg_pipeline_time']:.3f}s")

    # Language-specific performance
    print("\n🌍 LANGUAGE-SPECIFIC DETECTION:")
    for lang, stats in summary['language_performance'].items():
        accuracy = stats['accuracy']
        status = "✅" if accuracy >= 85 else "⚠️" if accuracy >= 70 else "❌"
        print(f"   {status} {lang.upper()}: {accuracy:.1f}% "
              f"({stats['correct']}/{stats['total']})")

    # Production readiness
    print("\n🚀 PRODUCTION READINESS:")
    prod = summary['production_readiness']
    detection_status = "✅ YES" if prod['detection_meets_target'] else "❌ NO"
    translation_status = "✅ YES" if prod['translation_meets_target'] else "❌ NO"
    overall_status = "✅ YES" if prod['production_ready'] else "❌ NO"

    print(f"   Detection meets 85% target: {detection_status}")
    print(f"   Translation meets 80% target: {translation_status}")
    print(f"   Overall production ready: {overall_status}")

    # Recommendations
    print("\n💡 RECOMMENDATIONS:")
    for recommendation in report['recommendations']:
        print(f"   {recommendation}")

    # Final verdict
    print("\n" + "="*80)
    if prod['production_ready']:
        print("✅ INTEGRATION READY - Google + Sarvam pipeline ready for production")
    else:
        print("⚠️  NEEDS IMPROVEMENT - Address performance gaps before production")
    print("="*80)

def main():
    """Main execution function"""

    # Check for Sarvam API key
    import os
    from dotenv import load_dotenv
    load_dotenv()

    sarvam_api_key = os.getenv('SARVAM_API_KEY')

    if sarvam_api_key:
        print("✅ Sarvam API key found - will test full translation pipeline")
    else:
        print("⚠️  Sarvam API key not found - testing detection pipeline only")
        print("   Set SARVAM_API_KEY environment variable to test full pipeline")

    # Run integration tests
    results = run_integration_tests(sarvam_api_key)

    # Generate and print report
    report = generate_integration_report(results)
    print_integration_summary(report)

    # Save report
    report_file = '/Users/Subho/sarvam_integration_test_report.json'
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\n📄 Integration report saved to: {report_file}")

    return 0 if report['summary']['production_readiness']['production_ready'] else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())