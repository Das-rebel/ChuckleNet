#!/usr/bin/env python3
"""
Comprehensive Sarvam API Key Validation Script
Tests API key validity, permissions, rate limits, and translation capabilities
"""

import os
import sys
import time
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class SarvamAPIValidator:
    def __init__(self):
        self.api_key = os.getenv('SARVAM_API_KEY')
        self.base_url = "https://api.sarvam.ai"
        self.results = {
            'api_key_valid': False,
            'api_key_info': {},
            'language_permissions': {},
            'translation_permissions': {},
            'rate_limits': {},
            'api_health': {},
            'end_to_end_tests': {},
            'errors': []
        }

    def validate_api_key_format(self):
        """Basic validation of API key format"""
        if not self.api_key:
            self.results['errors'].append("SARVAM_API_KEY not found in environment")
            return False

        if not self.api_key.startswith('sk_'):
            self.results['errors'].append("API key doesn't start with 'sk_'")
            return False

        if len(self.api_key) < 20:
            self.results['errors'].append("API key too short")
            return False

        print(f"✅ API Key Format Valid")
        print(f"   Length: {len(self.api_key)} characters")
        print(f"   Prefix: {self.api_key[:8]}***")
        return True

    def test_api_health(self):
        """Test if Sarvam API is accessible"""
        print("\n🔍 Testing API Health...")

        try:
            # Try to reach the API (even without authentication)
            response = requests.get(
                f"{self.base_url}/health",
                timeout=10
            )

            if response.status_code == 200:
                self.results['api_health']['status'] = 'healthy'
                self.results['api_health']['response_time'] = response.elapsed.total_seconds()
                print(f"✅ API is healthy - Response time: {response.elapsed.total_seconds():.2f}s")
                return True
            else:
                self.results['api_health']['status'] = f'error_{response.status_code}'
                self.results['errors'].append(f"API health check failed: {response.status_code}")
                return False

        except requests.exceptions.RequestException as e:
            self.results['api_health']['status'] = 'unreachable'
            self.results['errors'].append(f"API unreachable: {str(e)}")
            print(f"❌ API unreachable: {str(e)}")
            return False

    def test_api_key_authentication(self):
        """Test if API key provides valid authentication"""
        print("\n🔐 Testing API Key Authentication...")

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        try:
            # Try to get API key info or list available services
            response = requests.get(
                f"{self.base_url}/v1/models",
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                self.results['api_key_valid'] = True
                self.results['api_key_info']['status'] = 'valid'
                print(f"✅ API Key is valid and authenticated")
                return True
            elif response.status_code == 401:
                self.results['api_key_info']['status'] = 'invalid'
                self.results['errors'].append("API key authentication failed - invalid key")
                print(f"❌ API Key authentication failed - Invalid key")
                return False
            else:
                self.results['api_key_info']['status'] = f'error_{response.status_code}'
                self.results['errors'].append(f"Authentication check failed: {response.status_code}")
                print(f"❌ Authentication check failed: {response.status_code}")
                return False

        except requests.exceptions.RequestException as e:
            self.results['errors'].append(f"Authentication request failed: {str(e)}")
            print(f"❌ Authentication request failed: {str(e)}")
            return False

    def test_translation_permissions(self):
        """Test permissions for different language translations"""
        print("\n🌍 Testing Translation Permissions...")

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        # Test cases for different language pairs
        test_cases = [
            {'source': 'en-IN', 'target': 'hi-IN', 'text': 'Hello', 'direction': 'English to Hindi'},
            {'source': 'hi-IN', 'target': 'en-IN', 'text': 'नमस्ते', 'direction': 'Hindi to English'},
            {'source': 'en-IN', 'target': 'bn-IN', 'text': 'Hello', 'direction': 'English to Bengali'},
            {'source': 'bn-IN', 'target': 'en-IN', 'text': 'হ্যালো', 'direction': 'Bengali to English'},
        ]

        for test in test_cases:
            test_key = f"{test['source']} -> {test['target']}"

            try:
                payload = {
                    'source_language_code': test['source'],
                    'target_language_code': test['target'],
                    'text': test['text']
                }

                response = requests.post(
                    f"{self.base_url}/v1/translation",
                    headers=headers,
                    json=payload,
                    timeout=10
                )

                if response.status_code == 200:
                    result = response.json()
                    self.results['translation_permissions'][test_key] = {
                        'status': 'allowed',
                        'response_time': response.elapsed.total_seconds(),
                        'translated_text': result.get('translated_text', 'N/A')
                    }
                    print(f"✅ {test['direction']}: Allowed - {result.get('translated_text', 'N/A')}")
                else:
                    self.results['translation_permissions'][test_key] = {
                        'status': 'denied',
                        'error': response.status_code
                    }
                    print(f"❌ {test['direction']}: Denied (Status: {response.status_code})")

            except requests.exceptions.RequestException as e:
                self.results['translation_permissions'][test_key] = {
                    'status': 'error',
                    'error': str(e)
                }
                print(f"❌ {test['direction']}: Error - {str(e)}")

        # Check if all language pairs are allowed
        all_allowed = all(
            perm.get('status') == 'allowed'
            for perm in self.results['translation_permissions'].values()
        )
        return all_allowed

    def test_rate_limits(self):
        """Test API rate limits by making multiple requests"""
        print("\n⚡ Testing Rate Limits...")

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        success_count = 0
        error_count = 0
        rate_limit_hit = False

        # Make 10 rapid requests to test rate limiting
        for i in range(10):
            try:
                payload = {
                    'source_language_code': 'en-IN',
                    'target_language_code': 'hi-IN',
                    'text': f'Test message {i}'
                }

                response = requests.post(
                    f"{self.base_url}/v1/translation",
                    headers=headers,
                    json=payload,
                    timeout=10
                )

                if response.status_code == 200:
                    success_count += 1
                elif response.status_code == 429:
                    rate_limit_hit = True
                    print(f"⚠️ Rate limit hit after {i + 1} requests")
                    break
                else:
                    error_count += 1

                # Small delay to avoid immediate rate limiting
                time.sleep(0.1)

            except requests.exceptions.RequestException as e:
                error_count += 1

        self.results['rate_limits'] = {
            'success_count': success_count,
            'error_count': error_count,
            'rate_limit_hit': rate_limit_hit,
            'test_requests': 10
        }

        print(f"✅ Rate Limit Test Results:")
        print(f"   Successful requests: {success_count}/10")
        print(f"   Failed requests: {error_count}/10")
        print(f"   Rate limit hit: {rate_limit_hit}")

        return not rate_limit_hit and success_count >= 5

    def test_end_to_end_translation(self):
        """Comprehensive end-to-end translation test"""
        print("\n🔄 Testing End-to-End Translation...")

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        # Test real-world translation scenarios
        test_scenarios = [
            {
                'name': 'Simple greeting (English -> Hindi)',
                'source': 'en-IN', 'target': 'hi-IN',
                'text': 'Hello, how are you?'
            },
            {
                'name': 'Simple greeting (English -> Bengali)',
                'source': 'en-IN', 'target': 'bn-IN',
                'text': 'Hello, how are you?'
            },
            {
                'name': 'Hindi phrase (Hindi -> English)',
                'source': 'hi-IN', 'target': 'en-IN',
                'text': 'नमस्ते, आप कैसे हैं?'
            },
            {
                'name': 'Bengali phrase (Bengali -> English)',
                'source': 'bn-IN', 'target': 'en-IN',
                'text': 'নমস্কার, আপনি কেমন আছেন?'
            }
        ]

        all_passed = True

        for scenario in test_scenarios:
            try:
                payload = {
                    'source_language_code': scenario['source'],
                    'target_language_code': scenario['target'],
                    'text': scenario['text']
                }

                response = requests.post(
                    f"{self.base_url}/v1/translation",
                    headers=headers,
                    json=payload,
                    timeout=10
                )

                if response.status_code == 200:
                    result = response.json()
                    translated_text = result.get('translated_text', 'N/A')
                    self.results['end_to_end_tests'][scenario['name']] = {
                        'status': 'passed',
                        'original': scenario['text'],
                        'translated': translated_text,
                        'response_time': response.elapsed.total_seconds()
                    }
                    print(f"✅ {scenario['name']}:")
                    print(f"   Original: {scenario['text']}")
                    print(f"   Translated: {translated_text}")
                    print(f"   Response time: {response.elapsed.total_seconds():.2f}s")
                else:
                    self.results['end_to_end_tests'][scenario['name']] = {
                        'status': 'failed',
                        'error': response.status_code
                    }
                    print(f"❌ {scenario['name']}: Failed (Status: {response.status_code})")
                    all_passed = False

            except requests.exceptions.RequestException as e:
                self.results['end_to_end_tests'][scenario['name']] = {
                    'status': 'error',
                    'error': str(e)
                }
                print(f"❌ {scenario['name']}: Error - {str(e)}")
                all_passed = False

        return all_passed

    def generate_report(self):
        """Generate comprehensive validation report"""
        print("\n" + "="*60)
        print("📊 SARVAM API VALIDATION REPORT")
        print("="*60)

        # Summary section
        print("\n📋 SUMMARY:")
        api_key_valid = self.results['api_key_valid']
        languages_supported = all(
            perm.get('status') == 'allowed'
            for perm in self.results['translation_permissions'].values()
        )
        end_to_end_passed = all(
            test.get('status') == 'passed'
            for test in self.results['end_to_end_tests'].values()
        )

        print(f"   API Key Valid: {'✅ YES' if api_key_valid else '❌ NO'}")
        print(f"   Language Support: {'✅ ALL' if languages_supported else '❌ PARTIAL'}")
        print(f"   End-to-End Tests: {'✅ PASSED' if end_to_end_passed else '❌ FAILED'}")

        # API Key Information
        print("\n🔑 API KEY INFORMATION:")
        print(f"   Valid: {'✅ YES' if api_key_valid else '❌ NO'}")
        if self.api_key:
            print(f"   Format: {'✅ Valid' if self.api_key.startswith('sk_') else '❌ Invalid'}")
            print(f"   Length: {len(self.api_key)} characters")

        # API Health
        print("\n🏥 API HEALTH:")
        if self.results['api_health']:
            status = self.results['api_health'].get('status', 'unknown')
            print(f"   Status: {'✅ Healthy' if status == 'healthy' else '❌ Unhealthy'}")
            if 'response_time' in self.results['api_health']:
                print(f"   Response Time: {self.results['api_health']['response_time']:.2f}s")

        # Language Permissions
        print("\n🌍 LANGUAGE PERMISSIONS:")
        for direction, perm in self.results['translation_permissions'].items():
            status_icon = "✅" if perm.get('status') == 'allowed' else "❌"
            print(f"   {status_icon} {direction}: {perm.get('status', 'unknown').upper()}")

        # Rate Limits
        print("\n⚡ RATE LIMITS:")
        rate_limits = self.results['rate_limits']
        if rate_limits:
            print(f"   Test Requests: {rate_limits.get('test_requests', 'N/A')}")
            print(f"   Successful: {rate_limits.get('success_count', 'N/A')}")
            print(f"   Failed: {rate_limits.get('error_count', 'N/A')}")
            print(f"   Rate Limit Hit: {'⚠️ YES' if rate_limits.get('rate_limit_hit') else '✅ NO'}")

        # End-to-End Tests
        print("\n🔄 END-TO-END TESTS:")
        for test_name, test_result in self.results['end_to_end_tests'].items():
            status_icon = "✅" if test_result.get('status') == 'passed' else "❌"
            print(f"   {status_icon} {test_name}: {test_result.get('status', 'unknown').upper()}")

        # Errors
        if self.results['errors']:
            print("\n❌ ERRORS:")
            for error in self.results['errors']:
                print(f"   • {error}")

        # Overall Status
        print("\n" + "="*60)
        overall_status = api_key_valid and languages_supported and end_to_end_passed
        status_text = "✅ VALIDATION PASSED" if overall_status else "❌ VALIDATION FAILED"
        print(f"OVERALL STATUS: {status_text}")
        print("="*60)

        # Generate JSON report
        report_file = '/Users/Subho/sarvam_api_validation_report.json'
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)

        print(f"\n📄 Detailed report saved to: {report_file}")

        return overall_status

def main():
    """Main execution function"""
    print("🚀 Starting Sarvam API Key Validation...")
    print("="*60)

    validator = SarvamAPIValidator()

    # Run all validation tests
    tests = [
        ("API Key Format Validation", validator.validate_api_key_format),
        ("API Health Check", validator.test_api_health),
        ("API Key Authentication", validator.test_api_key_authentication),
        ("Translation Permissions", validator.test_translation_permissions),
        ("Rate Limits", validator.test_rate_limits),
        ("End-to-End Translation", validator.test_end_to_end_translation),
    ]

    for test_name, test_func in tests:
        try:
            test_func()
        except Exception as e:
            print(f"❌ {test_name} failed with error: {str(e)}")
            validator.results['errors'].append(f"{test_name}: {str(e)}")

    # Generate and display report
    overall_success = validator.generate_report()

    return 0 if overall_success else 1

if __name__ == "__main__":
    sys.exit(main())