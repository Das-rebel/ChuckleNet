#!/usr/bin/env python3
"""
Demonstration of Working Translation Solution
Tests various translation methods that actually work
"""

import requests
import json
from typing import Dict, List, Optional

def test_google_translate_public_api():
    """Test Google Translate's public (unofficial) API"""
    print("\n" + "="*60)
    print("Testing Google Translate Public API")
    print("="*60)

    # Note: This is Google's public translate endpoint (not officially documented)
    url = "https://translate.googleapis.com/translate_a/single"

    test_cases = [
        {"name": "English to Hindi", "text": "Hello, how are you?", "target": "hi"},
        {"name": "Hindi to English", "text": "नमस्ते, आप कैसे हैं?", "target": "en"},
        {"name": "English to Bengali", "text": "Hello, how are you?", "target": "bn"},
        {"name": "Bengali to English", "text": "নমস্কার, আপনি কেমন আছেন?", "target": "en"},
    ]

    results = []

    for test_case in test_cases:
        print(f"\n{test_case['name']}:")
        print(f"Original: {test_case['text']}")

        try:
            params = {
                'client': 'gtx',
                'sl': 'auto',
                'tl': test_case['target'],
                'dt': 't',
                'q': test_case['text']
            }

            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                # Parse the response
                result_data = response.json()
                translated_text = result_data[0][0][0]

                results.append({
                    'test_name': test_case['name'],
                    'original': test_case['text'],
                    'translated': translated_text,
                    'target_language': test_case['target'],
                    'status': 'success'
                })

                print(f"✅ Translation: {translated_text}")

            else:
                results.append({
                    'test_name': test_case['name'],
                    'original': test_case['text'],
                    'error': f"HTTP {response.status_code}",
                    'status': 'failed'
                })
                print(f"❌ Failed: HTTP {response.status_code}")

        except Exception as e:
            results.append({
                'test_name': test_case['name'],
                'original': test_case['text'],
                'error': str(e),
                'status': 'error'
            })
            print(f"❌ Error: {str(e)}")

    return results

def test_mymemory_translation_api():
    """Test MyMemory Translation API (free, no API key required)"""
    print("\n" + "="*60)
    print("Testing MyMemory Translation API")
    print("="*60)

    url = "https://api.mymemory.translated.net/get"

    test_cases = [
        {"name": "English to Hindi", "text": "Hello, how are you?", "langpair": "en|hi"},
        {"name": "Hindi to English", "text": "नमस्ते, आप कैसे हैं?", "langpair": "hi|en"},
        {"name": "English to Bengali", "text": "Hello, how are you?", "langpair": "en|bn"},
    ]

    results = []

    for test_case in test_cases:
        print(f"\n{test_case['name']}:")
        print(f"Original: {test_case['text']}")

        try:
            params = {
                'q': test_case['text'],
                'langpair': test_case['langpair']
            }

            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                result_data = response.json()
                translated_text = result_data.get('responseData', {}).get('translatedText', 'N/A')

                results.append({
                    'test_name': test_case['name'],
                    'original': test_case['text'],
                    'translated': translated_text,
                    'langpair': test_case['langpair'],
                    'status': 'success'
                })

                print(f"✅ Translation: {translated_text}")

            else:
                results.append({
                    'test_name': test_case['name'],
                    'original': test_case['text'],
                    'error': f"HTTP {response.status_code}",
                    'status': 'failed'
                })
                print(f"❌ Failed: HTTP {response.status_code}")

        except Exception as e:
            results.append({
                'test_name': test_case['name'],
                'original': test_case['text'],
                'error': str(e),
                'status': 'error'
            })
            print(f"❌ Error: {str(e)}")

    return results

def test_libretranslate_public():
    """Test LibreTranslate public instances"""
    print("\n" + "="*60)
    print("Testing LibreTranslate Public Instance")
    print("="*60)

    # Using a public LibreTranslate instance
    url = "https://libretranslate.de/translate"

    test_cases = [
        {"name": "English to Hindi", "text": "Hello", "source": "en", "target": "hi"},
        {"name": "English to Bengali", "text": "Hello", "source": "en", "target": "bn"},
    ]

    results = []

    for test_case in test_cases:
        print(f"\n{test_case['name']}:")
        print(f"Original: {test_case['text']}")

        try:
            payload = {
                'q': test_case['text'],
                'source': test_case['source'],
                'target': test_case['target'],
                'format': 'text'
            }

            response = requests.post(url, json=payload, timeout=10)

            if response.status_code == 200:
                result_data = response.json()
                translated_text = result_data.get('translatedText', 'N/A')

                results.append({
                    'test_name': test_case['name'],
                    'original': test_case['text'],
                    'translated': translated_text,
                    'source_lang': test_case['source'],
                    'target_lang': test_case['target'],
                    'status': 'success'
                })

                print(f"✅ Translation: {translated_text}")

            else:
                results.append({
                    'test_name': test_case['name'],
                    'original': test_case['text'],
                    'error': f"HTTP {response.status_code}",
                    'status': 'failed'
                })
                print(f"❌ Failed: HTTP {response.status_code}")

        except Exception as e:
            results.append({
                'test_name': test_case['name'],
                'original': test_case['text'],
                'error': str(e),
                'status': 'error'
            })
            print(f"❌ Error: {str(e)}")

    return results

def main():
    """Main function to test all working translation APIs"""
    print("🌍 Testing Working Translation Solutions")
    print("="*60)

    all_results = []

    # Test Google Translate Public API
    try:
        google_results = test_google_translate_public_api()
        all_results.extend(google_results)
    except Exception as e:
        print(f"\n❌ Google Translate API test failed: {str(e)}")

    # Test MyMemory Translation API
    try:
        memory_results = test_mymemory_translation_api()
        all_results.extend(memory_results)
    except Exception as e:
        print(f"\n❌ MyMemory API test failed: {str(e)}")

    # Test LibreTranslate
    try:
        libre_results = test_libretranslate_public()
        all_results.extend(libre_results)
    except Exception as e:
        print(f"\n❌ LibreTranslate test failed: {str(e)}")

    # Generate Summary
    print("\n" + "="*60)
    print("📊 WORKING TRANSLATION SOLUTIONS SUMMARY")
    print("="*60)

    total_tests = len(all_results)
    success_count = sum(1 for r in all_results if r['status'] == 'success')
    error_count = sum(1 for r in all_results if r['status'] == 'error')
    failed_count = sum(1 for r in all_results if r['status'] == 'failed')

    success_rate = (success_count / total_tests * 100) if total_tests > 0 else 0

    print(f"\nTotal Tests: {total_tests}")
    print(f"✅ Successful: {success_count} ({success_rate:.1f}%)")
    print(f"❌ Failed: {failed_count}")
    print(f"⚠️  Errors: {error_count}")

    # Language-specific success
    language_success = {
        'Hindi': {'tests': 0, 'success': 0},
        'Bengali': {'tests': 0, 'success': 0},
        'English': {'tests': 0, 'success': 0}
    }

    for result in all_results:
        if result['status'] == 'success':
            test_name = result['test_name']
            if 'Hindi' in test_name:
                language_success['Hindi']['tests'] += 1
                language_success['Hindi']['success'] += 1
            elif 'Bengali' in test_name:
                language_success['Bengali']['tests'] += 1
                language_success['Bengali']['success'] += 1
            elif 'English' in test_name:
                language_success['English']['tests'] += 1
                language_success['English']['success'] += 1
        else:
            test_name = result['test_name']
            if 'Hindi' in test_name:
                language_success['Hindi']['tests'] += 1
            elif 'Bengali' in test_name:
                language_success['Bengali']['tests'] += 1
            elif 'English' in test_name:
                language_success['English']['tests'] += 1

    print("\n🌍 Language Support:")
    for language, stats in language_success.items():
        if stats['tests'] > 0:
            rate = (stats['success'] / stats['tests'] * 100)
            status_icon = "✅" if rate == 100 else "⚠️" if rate > 50 else "❌"
            print(f"   {status_icon} {language}: {stats['success']}/{stats['tests']} ({rate:.1f}%)")

    # Save results
    report_file = '/Users/Subho/working_translation_solutions_report.json'
    with open(report_file, 'w') as f:
        json.dump(all_results, f, indent=2)

    print(f"\n📄 Detailed report saved to: {report_file}")

    # Recommendations
    print("\n" + "="*60)
    print("💡 RECOMMENDATIONS")
    print("="*60)

    if success_rate >= 80:
        print("✅ Excellent! These translation APIs are working well.")
        print("Recommendation: Use Google Translate Public API as primary solution.")
    elif success_rate >= 50:
        print("⚠️  Good progress! Most translations are working.")
        print("Recommendation: Combine multiple APIs for better coverage.")
    else:
        print("❌ Limited success. Consider implementing alternative solutions.")
        print("Recommendation: Set up paid APIs (Google Cloud Translation, DeepL).")

    return 0 if success_rate >= 50 else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())