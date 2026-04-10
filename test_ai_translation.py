#!/usr/bin/env python3
"""
Test AI Providers for Translation Capabilities
Tests Cerebras, OpenAI, Groq, Mistral, and other AI models for Hindi/Bengali translation
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_provider_translation(provider_name, api_key, api_endpoint, model, test_cases):
    """Test a specific AI provider's translation capabilities"""
    print(f"\n{'='*60}")
    print(f"Testing {provider_name} ({model})")
    print(f"{'='*60}")

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }

    results = []

    for test_case in test_cases:
        prompt = f"Translate the following text from {test_case['source_lang']} to {test_case['target_lang']}: '{test_case['text']}'"

        try:
            payload = {
                'model': model,
                'messages': [
                    {'role': 'user', 'content': prompt}
                ],
                'temperature': 0.3,
                'max_tokens': 200
            }

            response = requests.post(
                api_endpoint,
                headers=headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                # Extract translated text from response
                if 'choices' in result and len(result['choices']) > 0:
                    translated_text = result['choices'][0]['message']['content']
                    results.append({
                        'provider': provider_name,
                        'model': model,
                        'test_case': test_case['name'],
                        'source': test_case['text'],
                        'translation': translated_text,
                        'status': 'success',
                        'response_time': response.elapsed.total_seconds()
                    })
                    print(f"✅ {test_case['name']}")
                    print(f"   Original: {test_case['text']}")
                    print(f"   Translation: {translated_text}")
                    print(f"   Response time: {response.elapsed.total_seconds():.2f}s")
                else:
                    results.append({
                        'provider': provider_name,
                        'model': model,
                        'test_case': test_case['name'],
                        'error': 'Invalid response format',
                        'status': 'failed'
                    })
                    print(f"❌ {test_case['name']}: Invalid response format")
            else:
                results.append({
                    'provider': provider_name,
                    'model': model,
                    'test_case': test_case['name'],
                    'error': f"HTTP {response.status_code}",
                    'status': 'failed'
                })
                print(f"❌ {test_case['name']}: HTTP {response.status_code}")

        except requests.exceptions.RequestException as e:
            results.append({
                'provider': provider_name,
                'model': model,
                'test_case': test_case['name'],
                'error': str(e),
                'status': 'error'
            })
            print(f"❌ {test_case['name']}: {str(e)}")

    return results

def main():
    """Main function to test all AI providers"""
    print("🌍 AI Provider Translation Capabilities Test")
    print("="*60)

    # Test cases for Hindi and Bengali translation
    test_cases = [
        {'name': 'English to Hindi', 'source_lang': 'English', 'target_lang': 'Hindi', 'text': 'Hello, how are you?'},
        {'name': 'Hindi to English', 'source_lang': 'Hindi', 'target_lang': 'English', 'text': 'नमस्ते, आप कैसे हैं?'},
        {'name': 'English to Bengali', 'source_lang': 'English', 'target_lang': 'Bengali', 'text': 'Hello, how are you?'},
        {'name': 'Bengali to English', 'source_lang': 'Bengali', 'target_lang': 'English', 'text': 'নমস্কার, আপনি কেমন আছেন?'},
        {'name': 'Technical EN to HI', 'source_lang': 'English', 'target_lang': 'Hindi', 'text': 'What is machine learning?'},
        {'name': 'Technical EN to BN', 'source_lang': 'English', 'target_lang': 'Bengali', 'text': 'What is machine learning?'}
    ]

    all_results = []

    # Test Cerebras
    cerebras_key = os.getenv('CEREBRAS_API_KEY')
    if cerebras_key:
        cerebras_results = test_provider_translation(
            'Cerebras',
            cerebras_key,
            'https://api.cerebras.ai/v1/chat/completions',
            'llama-3.3-70b',
            test_cases
        )
        all_results.extend(cerebras_results)

    # Test Groq
    groq_key = os.getenv('GROQ_API_KEY')
    if groq_key:
        groq_results = test_provider_translation(
            'Groq',
            groq_key,
            'https://api.groq.com/openai/v1/chat/completions',
            'llama-3.3-70b-versatile',
            test_cases
        )
        all_results.extend(groq_results)

    # Test Mistral
    mistral_key = os.getenv('MISTRAL_API_KEY')
    if mistral_key:
        mistral_results = test_provider_translation(
            'Mistral',
            mistral_key,
            'https://api.mistral.ai/v1/chat/completions',
            'mistral-small-latest',
            test_cases
        )
        all_results.extend(mistral_results)

    # Test OpenAI (though quota exceeded, let's try)
    openai_key = os.getenv('OPENAI_API_KEY')
    if openai_key:
        openai_results = test_provider_translation(
            'OpenAI',
            openai_key,
            'https://api.openai.com/v1/chat/completions',
            'gpt-4o-mini-2024-07-18',
            test_cases
        )
        all_results.extend(openai_results)

    # Generate summary report
    print("\n" + "="*60)
    print("📊 TRANSLATION CAPABILITIES SUMMARY")
    print("="*60)

    # Group results by provider
    provider_stats = {}
    for result in all_results:
        provider = result['provider']
        if provider not in provider_stats:
            provider_stats[provider] = {'success': 0, 'failed': 0, 'error': 0, 'total': 0}

        if result['status'] == 'success':
            provider_stats[provider]['success'] += 1
        elif result['status'] == 'failed':
            provider_stats[provider]['failed'] += 1
        else:
            provider_stats[provider]['error'] += 1

        provider_stats[provider]['total'] += 1

    # Display provider statistics
    print("\n📈 Provider Performance:")
    for provider, stats in provider_stats.items():
        success_rate = (stats['success'] / stats['total'] * 100) if stats['total'] > 0 else 0
        print(f"\n   {provider}:")
        print(f"   ✅ Success: {stats['success']}/{stats['total']} ({success_rate:.1f}%)")
        print(f"   ❌ Failed: {stats['failed']}")
        print(f"   ⚠️  Error: {stats['error']}")

    # Language support analysis
    print("\n🌍 Language Support Analysis:")
    language_support = {
        'English to Hindi': {'success': 0, 'total': 0},
        'Hindi to English': {'success': 0, 'total': 0},
        'English to Bengali': {'success': 0, 'total': 0},
        'Bengali to English': {'success': 0, 'total': 0},
    }

    for result in all_results:
        test_name = result['test_case']
        if test_name in language_support:
            language_support[test_name]['total'] += 1
            if result['status'] == 'success':
                language_support[test_name]['success'] += 1

    for direction, stats in language_support.items():
        success_rate = (stats['success'] / stats['total'] * 100) if stats['total'] > 0 else 0
        status_icon = "✅" if success_rate > 75 else "⚠️" if success_rate > 50 else "❌"
        print(f"   {status_icon} {direction}: {stats['success']}/{stats['total']} ({success_rate:.1f}%)")

    # Save detailed results
    report_file = '/Users/Subho/ai_translation_capabilities_report.json'
    with open(report_file, 'w') as f:
        json.dump(all_results, f, indent=2)

    print(f"\n📄 Detailed report saved to: {report_file}")

    # Overall assessment
    total_success = sum(stats['success'] for stats in provider_stats.values())
    total_tests = sum(stats['total'] for stats in provider_stats.values())
    overall_success_rate = (total_success / total_tests * 100) if total_tests > 0 else 0

    print("\n" + "="*60)
    print(f"OVERALL SUCCESS RATE: {total_success}/{total_tests} ({overall_success_rate:.1f}%)")
    print("="*60)

    if overall_success_rate > 80:
        print("✅ EXCELLENT - Translation capabilities are working well")
    elif overall_success_rate > 60:
        print("⚠️  MODERATE - Translation capabilities are working but could be improved")
    else:
        print("❌ WEAK - Translation capabilities need significant improvement")

    return 0

if __name__ == "__main__":
    sys.exit(main())