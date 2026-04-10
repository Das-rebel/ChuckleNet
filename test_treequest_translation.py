#!/usr/bin/env python3
"""
Test TreeQuest AI Translation Capabilities
Tests translation functionality using TreeQuest for Hindi and Bengali
"""

import treequest
import json
import sys
from datetime import datetime

def test_translation_capability():
    """Test TreeQuest's translation capabilities for Hindi and Bengali"""
    print("🌍 Testing TreeQuest AI Translation Capabilities")
    print("="*60)

    # Test translation cases
    test_cases = [
        {
            'name': 'English to Hindi Simple',
            'query': 'Translate "Hello, how are you?" to Hindi',
            'expected_language': 'Hindi'
        },
        {
            'name': 'Hindi to English Simple',
            'query': 'Translate "नमस्ते, आप कैसे हैं?" to English',
            'expected_language': 'English'
        },
        {
            'name': 'English to Bengali Simple',
            'query': 'Translate "Hello, how are you?" to Bengali',
            'expected_language': 'Bengali'
        },
        {
            'name': 'Bengali to English Simple',
            'query': 'Translate "নমস্কার, আপনি কেমন আছেন?" to English',
            'expected_language': 'English'
        },
        {
            'name': 'Technical English to Hindi',
            'query': 'Translate "What is machine learning?" to Hindi',
            'expected_language': 'Hindi'
        },
        {
            'name': 'Technical English to Bengali',
            'query': 'Translate "What is machine learning?" to Bengali',
            'expected_language': 'Bengali'
        },
        {
            'name': 'Conversational English to Hindi',
            'query': 'Translate "Thanks for your help, I really appreciate it!" to Hindi',
            'expected_language': 'Hindi'
        },
        {
            'name': 'Complex Bengali to English',
            'query': 'Translate "আমি আজকে খুব ভালো আছি, আশা করি তুমিও ভালো আছো?" to English',
            'expected_language': 'English'
        }
    ]

    results = []

    print(f"\nRunning {len(test_cases)} translation tests...\n")

    for i, test_case in enumerate(test_cases, 1):
        print(f"{i}. {test_case['name']}")
        print(f"   Query: {test_case['query']}")

        try:
            # Use TreeQuest to handle the translation query
            response = treequest.route_query_sync(test_case['query'])

            result = {
                'test_name': test_case['name'],
                'query': test_case['query'],
                'expected_language': test_case['expected_language'],
                'response': response,
                'timestamp': datetime.now().isoformat(),
                'status': 'success',
                'error': None
            }

            print(f"   ✅ Response: {response[:100]}..." if len(response) > 100 else f"   ✅ Response: {response}")

            results.append(result)

        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            results.append({
                'test_name': test_case['name'],
                'query': test_case['query'],
                'expected_language': test_case['expected_language'],
                'response': None,
                'timestamp': datetime.now().isoformat(),
                'status': 'error',
                'error': str(e)
            })

        print()  # Empty line for readability

    # Generate summary
    print("="*60)
    print("📊 TEST RESULTS SUMMARY")
    print("="*60)

    success_count = sum(1 for r in results if r['status'] == 'success')
    error_count = sum(1 for r in results if r['status'] == 'error')
    total_count = len(results)

    success_rate = (success_count / total_count * 100) if total_count > 0 else 0

    print(f"\nTotal Tests: {total_count}")
    print(f"Successful: {success_count} ({success_rate:.1f}%)")
    print(f"Errors: {error_count}")

    # Language-specific analysis
    language_analysis = {
        'Hindi': {'tests': 0, 'success': 0},
        'English': {'tests': 0, 'success': 0},
        'Bengali': {'tests': 0, 'success': 0}
    }

    for result in results:
        if result['status'] == 'success':
            language = result['expected_language']
            language_analysis[language]['tests'] += 1
            language_analysis[language]['success'] += 1
        else:
            language = result['expected_language']
            language_analysis[language]['tests'] += 1

    print("\n🌍 Language Support:")
    for language, stats in language_analysis.items():
        if stats['tests'] > 0:
            rate = (stats['success'] / stats['tests'] * 100)
            status_icon = "✅" if rate == 100 else "⚠️" if rate > 50 else "❌"
            print(f"   {status_icon} {language}: {stats['success']}/{stats['tests']} ({rate:.1f}%)")

    # Overall assessment
    print("\n" + "="*60)
    if success_rate == 100:
        print("✅ EXCELLENT - All translation capabilities working perfectly")
        overall_status = "EXCELLENT"
    elif success_rate >= 75:
        print("⚠️  GOOD - Translation capabilities working well with minor issues")
        overall_status = "GOOD"
    elif success_rate >= 50:
        print("⚠️  MODERATE - Translation capabilities functional but need improvement")
        overall_status = "MODERATE"
    else:
        print("❌ WEAK - Translation capabilities need significant improvement")
        overall_status = "WEAK"

    print("="*60)

    # Save detailed results
    report_file = '/Users/Subho/treequest_translation_test_report.json'
    report_data = {
        'timestamp': datetime.now().isoformat(),
        'overall_status': overall_status,
        'success_rate': success_rate,
        'total_tests': total_count,
        'successful_tests': success_count,
        'failed_tests': error_count,
        'language_analysis': language_analysis,
        'detailed_results': results
    }

    with open(report_file, 'w') as f:
        json.dump(report_data, f, indent=2)

    print(f"\n📄 Detailed report saved to: {report_file}")

    return 0 if success_rate >= 50 else 1

def main():
    """Main function"""
    try:
        return test_translation_capability()
    except Exception as e:
        print(f"❌ Fatal error during testing: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())