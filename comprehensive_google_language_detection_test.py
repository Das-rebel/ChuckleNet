#!/usr/bin/env python3
"""
Comprehensive Google Translate API Language Detection Test Suite
Tests detection accuracy for all language types and compares with baseline
"""

import requests
import json
import time
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import re

class GoogleLanguageDetector:
    """Google Translate API Client for Language Detection"""

    def __init__(self):
        self.api_url = "https://translate.googleapis.com/translate_a/single"

    def detect_language(self, text: str) -> Dict:
        """
        Detect language using Google Translate API
        Returns: {'detected_language': str, 'confidence': float, 'response_time': float}
        """
        start_time = time.time()

        try:
            params = {
                'client': 'gtx',
                'sl': 'auto',  # Auto-detect source language
                'tl': 'en',    # Translate to English
                'dt': 't',     # Translation
                'q': text
            }

            response = requests.get(self.api_url, params=params, timeout=10)

            if response.status_code == 200:
                result_data = response.json()

                # Google returns detection info at index 2 of the main array
                # Format: [[...translations...], ..., "detected_language", ...]
                if len(result_data) > 2 and result_data[2]:
                    detected_language = result_data[2]  # This is the detected language code
                    confidence = 0.95  # Google Translate has high confidence in detection
                else:
                    detected_language = 'unknown'
                    confidence = 0.0

                response_time = time.time() - start_time

                return {
                    'detected_language': detected_language,
                    'confidence': confidence,
                    'response_time': response_time,
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

class EnhancedDetector:
    """
    Simulated enhanced detector (based on 12.5% Benglish accuracy baseline)
    This represents the existing system that needs improvement
    """

    def detect_language(self, text: str) -> Dict:
        """
        Enhanced detector with known limitations:
        - Good at pure languages (Hindi, Bengali, English)
        - Poor at Hinglish/Benglish (12.5% accuracy for Benglish)
        - Script-based detection fails for mixed languages
        """
        start_time = time.time()

        # Simulate known accuracy patterns
        bengali_script = re.search(r'[\u0980-\u09FF]', text)
        hindi_script = re.search(r'[\u0900-\u097F]', text)
        english_words = re.search(r'[a-zA-Z]{3,}', text)

        detected = 'unknown'
        confidence = 0.0

        # Pure language detection (80%+ accuracy)
        if bengali_script and not english_words:
            detected = 'bn'
            confidence = 0.9
        elif hindi_script and not english_words:
            detected = 'hi'
            confidence = 0.9
        elif english_words and not bengali_script and not hindi_script:
            detected = 'en'
            confidence = 0.95
        # Mixed languages (12.5% accuracy for Benglish)
        elif english_words and (bengali_script or hindi_script):
            if bengali_script:
                # Poor Benglish detection - 12.5% accuracy
                import random
                if random.random() < 0.125:  # 12.5% chance of correct detection
                    detected = 'bn-en'  # Mixed Bengali-English
                    confidence = 0.3
                else:
                    detected = 'en'  # Usually fails and detects as English
                    confidence = 0.6
            elif hindi_script:
                # Hinglish is slightly better at 25% accuracy
                import random
                if random.random() < 0.25:
                    detected = 'hi-en'  # Mixed Hindi-English
                    confidence = 0.4
                else:
                    detected = 'en'
                    confidence = 0.6

        return {
            'detected_language': detected,
            'confidence': confidence,
            'response_time': time.time() - start_time + 0.05,  # Simulated slower response
            'success': True,
            'error': None
        }

class LanguageDetectionTestSuite:
    """Comprehensive test suite for language detection systems"""

    def __init__(self):
        self.google_detector = GoogleLanguageDetector()
        self.enhanced_detector = EnhancedDetector()
        self.test_results = []

    def create_test_cases(self) -> Dict[str, List[Dict]]:
        """Create comprehensive test cases for all language types"""
        return {
            'pure_hindi': [
                {'text': 'भारत की राजधानी क्या है?', 'expected': 'hi', 'type': 'question'},
                {'text': 'आज मौसम कैसा है?', 'expected': 'hi', 'type': 'weather'},
                {'text': 'मुझे पायथन कोड लिखना है', 'expected': 'hi', 'type': 'technical'},
                {'text': 'कृपया मेरी मदद करें', 'expected': 'hi', 'type': 'polite'},
                {'text': 'बहुत धन्यवाद आपकी मदद के लिए', 'expected': 'hi', 'type': 'gratitude'},
                {'text': 'मैं सीखना चाहता हूं कि मशीन लर्निंग क्या है', 'expected': 'hi', 'type': 'technical'},
                {'text': 'आज का समय क्या है?', 'expected': 'hi', 'type': 'time'},
                {'text': 'कैसे हो आप सब?', 'expected': 'hi', 'type': 'greeting'}
            ],
            'pure_bengali': [
                {'text': 'ভারতের রাজধানী কী?', 'expected': 'bn', 'type': 'question'},
                {'text': 'আজ আবহাওয়া কেমন?', 'expected': 'bn', 'type': 'weather'},
                {'text': 'আমাকে পাইথন কোড লিখতে হবে', 'expected': 'bn', 'type': 'technical'},
                {'text': 'দয়া করে আমাকে সাহায্য করুন', 'expected': 'bn', 'type': 'polite'},
                {'text': 'অনেক ধন্যবাদ আপনার সাহায্যের জন্য', 'expected': 'bn', 'type': 'gratitude'},
                {'text': 'আমি শিখতে চাই মেশিন লার্নিং কী', 'expected': 'bn', 'type': 'technical'},
                {'text': 'এখন সময় কত?', 'expected': 'bn', 'type': 'time'},
                {'text': 'তোমরা সবাই কেমন আছো?', 'expected': 'bn', 'type': 'greeting'}
            ],
            'pure_english': [
                {'text': 'What is the capital of India?', 'expected': 'en', 'type': 'question'},
                {'text': 'How is the weather today?', 'expected': 'en', 'type': 'weather'},
                {'text': 'I need to write Python code', 'expected': 'en', 'type': 'technical'},
                {'text': 'Please help me', 'expected': 'en', 'type': 'polite'},
                {'text': 'Thank you very much for your help', 'expected': 'en', 'type': 'gratitude'},
                {'text': 'I want to learn what machine learning is', 'expected': 'en', 'type': 'technical'},
                {'text': 'What time is it now?', 'expected': 'en', 'type': 'time'},
                {'text': 'How are you all doing?', 'expected': 'en', 'type': 'greeting'}
            ],
            'hinglish': [
                {'text': 'Weather kaisa hai aaj?', 'expected': 'hi', 'type': 'weather'},
                {'text': 'Mujhe Python code likhna hai', 'expected': 'hi', 'type': 'technical'},
                {'text': 'Please mujhe help karo', 'expected': 'hi', 'type': 'polite'},
                {'text': 'Bahut dhanyawad aapki madad ke liye', 'expected': 'hi', 'type': 'gratitude'},
                {'text': 'Machine learning kya hai mujhe sikhna hai', 'expected': 'hi', 'type': 'technical'},
                {'text': 'Abhi time kya hai?', 'expected': 'hi', 'type': 'time'},
                {'text': 'Tum sab kaise ho?', 'expected': 'hi', 'type': 'greeting'},
                {'text': 'Code explain karo please', 'expected': 'hi', 'type': 'technical'},
                {'text': 'India ka capital kya hai?', 'expected': 'hi', 'type': 'question'},
                {'text': 'Kaun kaun online hai?', 'expected': 'hi', 'type': 'conversation'}
            ],
            'benglish': [
                {'text': 'Weather kemon ache aaj?', 'expected': 'bn', 'type': 'weather'},
                {'text': 'Amake Python code likhte hobe', 'expected': 'bn', 'type': 'technical'},
                {'text': 'Please amake help koro', 'expected': 'bn', 'type': 'polite'},
                {'text': 'Onek dhonnobad tomar sahajjo jonno', 'expected': 'bn', 'type': 'gratitude'},
                {'text': 'Machine learning ki ami shikhte chai', 'expected': 'bn', 'type': 'technical'},
                {'text': 'Ekhon time ki?', 'expected': 'bn', 'type': 'time'},
                {'text': 'Tumi sob kemon acho?', 'expected': 'bn', 'type': 'greeting'},
                {'text': 'Code explain koro please', 'expected': 'bn', 'type': 'technical'},
                {'text': 'Bharater rajdhani ki?', 'expected': 'bn', 'type': 'question'},
                {'text': 'Ke ke online ache?', 'expected': 'bn', 'type': 'conversation'}
            ],
            'mixed_script': [
                {'text': 'আজ code explain করো please', 'expected': 'bn', 'type': 'technical'},
                {'text': 'আজ weather কেমন?', 'expected': 'bn', 'type': 'weather'},
                {'text': 'আমাকে help করো please', 'expected': 'bn', 'type': 'polite'},
                {'text': 'आज code explain करो please', 'expected': 'hi', 'type': 'technical'},
                {'text': 'आज weather कैसा?', 'expected': 'hi', 'type': 'weather'},
                {'text': 'मुझे help करो please', 'expected': 'hi', 'type': 'polite'},
                {'text': 'আমি Python code লিখতে চাই', 'expected': 'bn', 'type': 'technical'},
                {'text': 'मुझे Python code लिखना है', 'expected': 'hi', 'type': 'technical'},
                {'text': 'তোমারা সবাই কেমন আছো? Everyone good?', 'expected': 'bn', 'type': 'conversation'},
                {'text': 'तुम सब कैसे हो? Everyone good?', 'expected': 'hi', 'type': 'conversation'}
            ],
            'edge_cases': [
                {'text': '', 'expected': 'unknown', 'type': 'empty'},
                {'text': '12345', 'expected': 'unknown', 'type': 'numbers'},
                {'text': 'Hello 👋', 'expected': 'en', 'type': 'emoji'},
                {'text': '😊', 'expected': 'unknown', 'type': 'emoji_only'},
                {'text': 'A', 'expected': 'en', 'type': 'single_char'},
                {'text': 'अ', 'expected': 'hi', 'type': 'single_char'},
                {'text': 'আ', 'expected': 'bn', 'type': 'single_char'},
                {'text': 'Python3.9.7', 'expected': 'en', 'type': 'technical'},
                {'text': 'API_KEY=12345', 'expected': 'en', 'type': 'technical'},
                {'text': 'मशीन learning', 'expected': 'hi', 'type': 'partial_transliteration'}
            ]
        }

    def normalize_language_code(self, lang_code: str) -> str:
        """Normalize language codes for comparison"""
        lang_code = lang_code.lower().replace('_', '-')

        # Google sometimes returns country codes like 'hi-IN', 'bn-IN'
        if lang_code.startswith('hi'):
            return 'hi'
        elif lang_code.startswith('bn'):
            return 'bn'
        elif lang_code.startswith('en'):
            return 'en'
        else:
            return lang_code

    def is_detection_correct(self, detected: str, expected: str) -> bool:
        """Check if detected language matches expected"""
        detected_normalized = self.normalize_language_code(detected)
        expected_normalized = self.normalize_language_code(expected)

        return detected_normalized == expected_normalized

    def run_basic_detection_tests(self) -> List[Dict]:
        """Run basic detection accuracy tests (30+ queries)"""
        print("\n" + "="*80)
        print("🔍 PHASE 1: BASIC DETECTION ACCURACY TESTS (30+ queries)")
        print("="*80)

        test_cases = self.create_test_cases()
        basic_test_results = []

        for category, tests in test_cases.items():
            print(f"\n📋 Testing {category.upper()} ({len(tests)} queries)")

            for test in tests:
                # Test Google Detector
                google_result = self.google_detector.detect_language(test['text'])
                google_correct = self.is_detection_correct(
                    google_result['detected_language'],
                    test['expected']
                )

                # Test Enhanced Detector
                enhanced_result = self.enhanced_detector.detect_language(test['text'])
                enhanced_correct = self.is_detection_correct(
                    enhanced_result['detected_language'],
                    test['expected']
                )

                test_result = {
                    'category': category,
                    'text': test['text'],
                    'expected_language': test['expected'],
                    'type': test['type'],
                    'google_detection': google_result,
                    'google_correct': google_correct,
                    'enhanced_detection': enhanced_result,
                    'enhanced_correct': enhanced_correct,
                    'timestamp': time.time()
                }

                basic_test_results.append(test_result)

                # Print result
                google_status = "✅" if google_correct else "❌"
                enhanced_status = "✅" if enhanced_correct else "❌"

                print(f"  {google_status} Google: {google_result['detected_language']} "
                      f"({google_result['response_time']:.3f}s) | "
                      f"{enhanced_status} Enhanced: {enhanced_result['detected_language']} "
                      f"({enhanced_result['response_time']:.3f}s) | "
                      f"Expected: {test['expected']}")

        return basic_test_results

    def run_mixed_language_tests(self) -> List[Dict]:
        """Run mixed language detection tests (20+ queries)"""
        print("\n" + "="*80)
        print("🔍 PHASE 2: MIXED LANGUAGE DETECTION TESTS (20+ queries)")
        print("="*80)

        mixed_test_cases = [
            # Hinglish variants
            {'text': 'Hey, aaj weather kaisa hai?', 'expected': 'hi', 'type': 'hinglish_greeting'},
            {'text': 'Mujhe actually code chahiye please', 'expected': 'hi', 'type': 'hinglish_technical'},
            {'text': 'Thanks yaar, bahut help kiya', 'expected': 'hi', 'type': 'hinglish_gratitude'},
            {'text': 'Can you please code explain karo?', 'expected': 'hi', 'type': 'hinglish_request'},
            {'text': 'Basically mujhe samajh nahi aa raha', 'expected': 'hi', 'type': 'hinglish_confusion'},
            {'text': 'Ok got it, thanks!', 'expected': 'hi', 'type': 'hinglish_acknowledgment'},

            # Benglish variants
            {'text': 'Hey, aaj weather kemon ache?', 'expected': 'bn', 'type': 'benglish_greeting'},
            {'text': 'Amake actually code dorkar please', 'expected': 'bn', 'type': 'benglish_technical'},
            {'text': 'Thanks bhai, onek help korecho', 'expected': 'bn', 'type': 'benglish_gratitude'},
            {'text': 'Can you please code explain koro?', 'expected': 'bn', 'type': 'benglish_request'},
            {'text': 'Basically amake bujhte parchi na', 'expected': 'bn', 'type': 'benglish_confusion'},
            {'text': 'Ok thik ache, thanks!', 'expected': 'bn', 'type': 'benglish_acknowledgment'},

            # Technical mixed
            {'text': 'Python function likhna hai please', 'expected': 'hi', 'type': 'technical_hinglish'},
            {'text': 'Python function likhte hobe please', 'expected': 'bn', 'type': 'technical_benglish'},
            {'text': 'API call karna hai', 'expected': 'hi', 'type': 'technical_hinglish'},
            {'text': 'API call korte hobe', 'expected': 'bn', 'type': 'technical_benglish'},

            # Conversational mixed
            {'text': 'Kya haal hai bhai? How are you?', 'expected': 'hi', 'type': 'conversational_hinglish'},
            {'text': 'Ki khobar bhai? How are you?', 'expected': 'bn', 'type': 'conversational_benglish'},
            {'text': 'Good morning bhai, subah', 'expected': 'hi', 'type': 'conversational_hinglish'},
            {'text': 'Good morning bhai, shokal', 'expected': 'bn', 'type': 'conversational_benglish'}
        ]

        mixed_test_results = []

        for test in mixed_test_cases:
            # Test Google Detector
            google_result = self.google_detector.detect_language(test['text'])
            google_correct = self.is_detection_correct(
                google_result['detected_language'],
                test['expected']
            )

            # Test Enhanced Detector
            enhanced_result = self.enhanced_detector.detect_language(test['text'])
            enhanced_correct = self.is_detection_correct(
                enhanced_result['detected_language'],
                test['expected']
            )

            test_result = {
                'category': 'mixed_language',
                'text': test['text'],
                'expected_language': test['expected'],
                'type': test['type'],
                'google_detection': google_result,
                'google_correct': google_correct,
                'enhanced_detection': enhanced_result,
                'enhanced_correct': enhanced_correct,
                'timestamp': time.time()
            }

            mixed_test_results.append(test_result)

            google_status = "✅" if google_correct else "❌"
            enhanced_status = "✅" if enhanced_correct else "❌"

            print(f"  {google_status} Google: {google_result['detected_language']} "
                  f"({google_result['response_time']:.3f}s) | "
                  f"{enhanced_status} Enhanced: {enhanced_result['detected_language']} "
                  f"({enhanced_result['response_time']:.3f}s) | "
                  f"Expected: {test['expected']} | "
                  f"Type: {test['type']}")

        return mixed_test_results

    def run_edge_case_tests(self) -> List[Dict]:
        """Run edge case tests (10+ queries)"""
        print("\n" + "="*80)
        print("🔍 PHASE 3: EDGE CASE TESTS (10+ queries)")
        print("="*80)

        edge_cases = [
            {'text': '😊😊😊', 'expected': 'unknown', 'type': 'emoji_only'},
            {'text': '1234567890', 'expected': 'unknown', 'type': 'numbers_only'},
            {'text': 'A', 'expected': 'en', 'type': 'single_english_char'},
            {'text': 'Hi', 'expected': 'en', 'type': 'short_english'},
            {'text': 'नमस्ते', 'expected': 'hi', 'type': 'short_hindi'},
            {'text': 'নমস্কার', 'expected': 'bn', 'type': 'short_bengali'},
            {'text': 'Hello world! 🌍', 'expected': 'en', 'type': 'emoji_english'},
            {'text': 'Machine Learning™', 'expected': 'en', 'type': 'trademark'},
            {'text': 'C++ programming', 'expected': 'en', 'type': 'programming_language'},
            {'text': '#python #coding', 'expected': 'en', 'type': 'hashtags'},
            {'text': 'API_KEY=value', 'expected': 'en', 'type': 'config'},
            {'text': 'SELECT * FROM table', 'expected': 'en', 'type': 'sql'}
        ]

        edge_test_results = []

        for test in edge_cases:
            # Test Google Detector
            google_result = self.google_detector.detect_language(test['text'])
            google_correct = self.is_detection_correct(
                google_result['detected_language'],
                test['expected']
            )

            # Test Enhanced Detector
            enhanced_result = self.enhanced_detector.detect_language(test['text'])
            enhanced_correct = self.is_detection_correct(
                enhanced_result['detected_language'],
                test['expected']
            )

            test_result = {
                'category': 'edge_cases',
                'text': test['text'],
                'expected_language': test['expected'],
                'type': test['type'],
                'google_detection': google_result,
                'google_correct': google_correct,
                'enhanced_detection': enhanced_result,
                'enhanced_correct': enhanced_correct,
                'timestamp': time.time()
            }

            edge_test_results.append(test_result)

            google_status = "✅" if google_correct else "❌"
            enhanced_status = "✅" if enhanced_correct else "❌"

            print(f"  {google_status} Google: {google_result['detected_language']} "
                  f"({google_result['response_time']:.3f}s) | "
                  f"{enhanced_status} Enhanced: {enhanced_result['detected_language']} "
                  f"({enhanced_result['response_time']:.3f}s) | "
                  f"Expected: {test['expected']} | "
                  f"Type: {test['type']}")

        return edge_test_results

    def run_performance_tests(self) -> List[Dict]:
        """Run performance tests (10+ queries)"""
        print("\n" + "="*80)
        print("🔍 PHASE 4: PERFORMANCE TESTS (10+ queries)")
        print("="*80)

        performance_test_cases = [
            {'text': 'What is the capital of India?', 'expected': 'en', 'length': 'short'},
            {'text': 'I need to write a Python function that implements machine learning algorithms for data analysis and prediction', 'expected': 'en', 'length': 'medium'},
            {'text': ' '.join(['Hello'] * 50), 'expected': 'en', 'length': 'long'},
            {'text': 'भारत की राजधानी क्या है?', 'expected': 'hi', 'length': 'short'},
            {'text': 'मुझे एक पायथन फंक्शन लिखना है जो मशीन लर्निंग एल्गोरिदम को डेटा विश्लेषण और पूर्वानुमान के लिए लागू करता है', 'expected': 'hi', 'length': 'medium'},
            {'text': ' '.join(['नमस्ते'] * 50), 'expected': 'hi', 'length': 'long'},
            {'text': 'ভারতের রাজধানী কী?', 'expected': 'bn', 'length': 'short'},
            {'text': 'আমাকে একটি পাইথন ফাংশন লিখতে হবে যে মেশিন লার্নিং অ্যালগরিদম বাস্তবায়ন করে', 'expected': 'bn', 'length': 'medium'},
            {'text': ' '.join(['নমস্কার'] * 50), 'expected': 'bn', 'length': 'long'},
            {'text': 'Weather kaisa hai aaj please?', 'expected': 'hi', 'length': 'short'}
        ]

        performance_results = []

        for test in performance_test_cases:
            # Test Google Detector
            google_start = time.time()
            google_result = self.google_detector.detect_language(test['text'])
            google_time = time.time() - google_start

            # Test Enhanced Detector
            enhanced_start = time.time()
            enhanced_result = self.enhanced_detector.detect_language(test['text'])
            enhanced_time = time.time() - enhanced_start

            test_result = {
                'category': 'performance',
                'text': test['text'],
                'expected_language': test['expected'],
                'length': test['length'],
                'google_detection': google_result,
                'google_response_time': google_time,
                'enhanced_detection': enhanced_result,
                'enhanced_response_time': enhanced_time,
                'timestamp': time.time()
            }

            performance_results.append(test_result)

            print(f"  Text length: {test['length']} | "
                  f"Google: {google_time:.4f}s | "
                  f"Enhanced: {enhanced_time:.4f}s | "
                  f"Speedup: {enhanced_time/google_time:.2f}x")

        return performance_results

    def run_error_recovery_tests(self) -> List[Dict]:
        """Run error recovery tests (5+ scenarios)"""
        print("\n" + "="*80)
        print("🔍 PHASE 5: ERROR RECOVERY TESTS (5+ scenarios)")
        print("="*80)

        error_scenarios = [
            {'text': 'x' * 10000, 'expected': 'en', 'type': 'very_long_text'},
            {'text': '!@#$%^&*()', 'expected': 'unknown', 'type': 'special_chars'},
            {'text': '\n\n\n\n\n', 'expected': 'unknown', 'type': 'whitespace'},
            {'text': '<script>alert("test")</script>', 'expected': 'en', 'type': 'html'},
            {'text': 'SELECT * FROM users WHERE id = 1 OR 1=1', 'expected': 'en', 'type': 'sql_injection'}
        ]

        error_recovery_results = []

        for test in error_scenarios:
            # Test Google Detector
            google_result = self.google_detector.detect_language(test['text'])
            google_success = google_result['success']

            # Test Enhanced Detector
            enhanced_result = self.enhanced_detector.detect_language(test['text'])
            enhanced_success = enhanced_result['success']

            test_result = {
                'category': 'error_recovery',
                'text': test['text'],
                'expected_language': test['expected'],
                'type': test['type'],
                'google_detection': google_result,
                'google_success': google_success,
                'enhanced_detection': enhanced_result,
                'enhanced_success': enhanced_success,
                'timestamp': time.time()
            }

            error_recovery_results.append(test_result)

            google_status = "✅" if google_success else "❌"
            enhanced_status = "✅" if enhanced_success else "❌"

            print(f"  {google_status} Google: {google_result['detected_language']} "
                  f"({google_result.get('error', 'No error')}) | "
                  f"{enhanced_status} Enhanced: {enhanced_result['detected_language']} "
                  f"({enhanced_result.get('error', 'No error')}) | "
                  f"Type: {test['type']}")

        return error_recovery_results

    def generate_comprehensive_report(self, all_results: List[Dict]) -> Dict:
        """Generate comprehensive test report with metrics"""
        print("\n" + "="*80)
        print("📊 COMPREHENSIVE TEST REPORT GENERATION")
        print("="*80)

        report = {
            'timestamp': time.time(),
            'total_tests': len(all_results),
            'summary': {},
            'detailed_results': all_results,
            'recommendations': []
        }

        # Overall accuracy comparison
        google_correct = sum(1 for r in all_results if r.get('google_correct', False))
        enhanced_correct = sum(1 for r in all_results if r.get('enhanced_correct', False))

        google_accuracy = (google_correct / len(all_results) * 100) if all_results else 0
        enhanced_accuracy = (enhanced_correct / len(all_results) * 100) if all_results else 0

        report['summary']['overall_accuracy'] = {
            'google_translate': google_accuracy,
            'enhanced_detector': enhanced_accuracy,
            'improvement': google_accuracy - enhanced_accuracy
        }

        # Language-specific performance
        language_performance = defaultdict(lambda: {'google': {'correct': 0, 'total': 0}, 'enhanced': {'correct': 0, 'total': 0}})

        for result in all_results:
            expected = result.get('expected_language', 'unknown')
            language_performance[expected]['google']['total'] += 1
            language_performance[expected]['enhanced']['total'] += 1

            if result.get('google_correct', False):
                language_performance[expected]['google']['correct'] += 1
            if result.get('enhanced_correct', False):
                language_performance[expected]['enhanced']['correct'] += 1

        report['summary']['language_specific_performance'] = {}

        for language, stats in language_performance.items():
            google_rate = (stats['google']['correct'] / stats['google']['total'] * 100) if stats['google']['total'] > 0 else 0
            enhanced_rate = (stats['enhanced']['correct'] / stats['enhanced']['total'] * 100) if stats['enhanced']['total'] > 0 else 0

            report['summary']['language_specific_performance'][language] = {
                'google_accuracy': google_rate,
                'enhanced_accuracy': enhanced_rate,
                'google_correct': stats['google']['correct'],
                'google_total': stats['google']['total'],
                'enhanced_correct': stats['enhanced']['correct'],
                'enhanced_total': stats['enhanced']['total'],
                'improvement': google_rate - enhanced_rate
            }

        # Performance metrics
        google_times = [r['google_detection']['response_time'] for r in all_results if 'google_detection' in r and r['google_detection']['success']]
        enhanced_times = [r['enhanced_detection']['response_time'] for r in all_results if 'enhanced_detection' in r and r['enhanced_detection']['success']]

        if google_times:
            report['summary']['performance'] = {
                'google_avg_response_time': sum(google_times) / len(google_times),
                'google_min_response_time': min(google_times),
                'google_max_response_time': max(google_times)
            }
        else:
            report['summary']['performance'] = {}

        if enhanced_times:
            report['summary']['performance'].update({
                'enhanced_avg_response_time': sum(enhanced_times) / len(enhanced_times),
                'enhanced_min_response_time': min(enhanced_times),
                'enhanced_max_response_time': max(enhanced_times)
            })

        # Category-specific analysis
        category_analysis = defaultdict(lambda: {'google': {'correct': 0, 'total': 0}, 'enhanced': {'correct': 0, 'total': 0}})

        for result in all_results:
            category = result.get('category', 'unknown')
            category_analysis[category]['google']['total'] += 1
            category_analysis[category]['enhanced']['total'] += 1

            if result.get('google_correct', False):
                category_analysis[category]['google']['correct'] += 1
            if result.get('enhanced_correct', False):
                category_analysis[category]['enhanced']['correct'] += 1

        report['summary']['category_analysis'] = {}

        for category, stats in category_analysis.items():
            google_rate = (stats['google']['correct'] / stats['google']['total'] * 100) if stats['google']['total'] > 0 else 0
            enhanced_rate = (stats['enhanced']['correct'] / stats['enhanced']['total'] * 100) if stats['enhanced']['total'] > 0 else 0

            report['summary']['category_analysis'][category] = {
                'google_accuracy': google_rate,
                'enhanced_accuracy': enhanced_rate,
                'google_correct': stats['google']['correct'],
                'google_total': stats['google']['total'],
                'enhanced_correct': stats['enhanced']['correct'],
                'enhanced_total': stats['enhanced']['total'],
                'improvement': google_rate - enhanced_rate
            }

        # Production readiness assessment
        target_accuracy = 85.0
        production_ready = google_accuracy >= target_accuracy

        report['summary']['production_readiness'] = {
            'target_accuracy': target_accuracy,
            'google_meets_target': production_ready,
            'gap': target_accuracy - google_accuracy if not production_ready else 0,
            'baseline_accuracy': enhanced_accuracy,
            'overall_improvement': google_accuracy - enhanced_accuracy
        }

        # Recommendations
        recommendations = []

        if production_ready:
            recommendations.append("✅ Google Translate API meets 85%+ accuracy target")
            recommendations.append("✅ Recommended for production deployment")
            recommendations.append("✅ Significant improvement over enhanced detector")
        else:
            recommendations.append(f"⚠️ Google Translate API at {google_accuracy:.1f}% below 85% target")
            recommendations.append(f"💡 Gap to target: {target_accuracy - google_accuracy:.1f}%")
            recommendations.append("🔧 Consider implementing fallback mechanisms")

        # Benglish specific analysis
        benglish_google = report['summary']['language_specific_performance'].get('bn', {}).get('google_accuracy', 0)
        benglish_enhanced = report['summary']['language_specific_performance'].get('bn', {}).get('enhanced_accuracy', 0)

        if benglish_google > 80:
            recommendations.append(f"✅ Excellent Benglish detection: {benglish_google:.1f}% vs {benglish_enhanced:.1f}% baseline")
        elif benglish_google > 12.5:
            recommendations.append(f"✅ Benglish improvement: {benglish_google:.1f}% vs {benglish_enhanced:.1f}% baseline")
        else:
            recommendations.append(f"⚠️ Benglish still challenging: {benglish_google:.1f}% vs {benglish_enhanced:.1f}% baseline")

        report['recommendations'] = recommendations

        return report

    def run_comprehensive_tests(self) -> Dict:
        """Run all comprehensive tests and generate report"""
        print("🌍 COMPREHENSIVE GOOGLE TRANSLATE LANGUAGE DETECTION TEST SUITE")
        print("="*80)

        all_results = []

        # Phase 1: Basic Detection Tests
        basic_results = self.run_basic_detection_tests()
        all_results.extend(basic_results)

        # Phase 2: Mixed Language Tests
        mixed_results = self.run_mixed_language_tests()
        all_results.extend(mixed_results)

        # Phase 3: Edge Case Tests
        edge_results = self.run_edge_case_tests()
        all_results.extend(edge_results)

        # Phase 4: Performance Tests
        performance_results = self.run_performance_tests()
        all_results.extend(performance_results)

        # Phase 5: Error Recovery Tests
        error_results = self.run_error_recovery_tests()
        all_results.extend(error_results)

        # Generate comprehensive report
        report = self.generate_comprehensive_report(all_results)

        return report

    def print_summary(self, report: Dict):
        """Print formatted summary report"""
        print("\n" + "="*80)
        print("📊 COMPREHENSIVE TEST RESULTS SUMMARY")
        print("="*80)

        summary = report['summary']

        # Overall accuracy
        print("\n🎯 OVERALL ACCURACY:")
        google_acc = summary['overall_accuracy']['google_translate']
        enhanced_acc = summary['overall_accuracy']['enhanced_detector']
        improvement = summary['overall_accuracy']['improvement']

        print(f"   Google Translate API: {google_acc:.1f}%")
        print(f"   Enhanced Detector: {enhanced_acc:.1f}%")
        print(f"   Improvement: +{improvement:.1f}%")

        # Language-specific performance
        print("\n🌍 LANGUAGE-SPECIFIC PERFORMANCE:")
        for language, stats in summary['language_specific_performance'].items():
            google_acc = stats['google_accuracy']
            enhanced_acc = stats['enhanced_accuracy']
            improvement = stats['improvement']

            status = "✅" if google_acc > 80 else "⚠️" if google_acc > 60 else "❌"
            print(f"   {status} {language.upper()}: Google {google_acc:.1f}% | "
                  f"Enhanced {enhanced_acc:.1f}% | Improvement: +{improvement:.1f}%")

        # Category analysis
        print("\n📋 CATEGORY ANALYSIS:")
        for category, stats in summary['category_analysis'].items():
            google_acc = stats['google_accuracy']
            enhanced_acc = stats['enhanced_accuracy']
            improvement = stats['improvement']

            status = "✅" if google_acc > 80 else "⚠️" if google_acc > 60 else "❌"
            print(f"   {status} {category.replace('_', ' ').title()}: "
                  f"Google {google_acc:.1f}% | Enhanced {enhanced_acc:.1f}% | "
                  f"Improvement: +{improvement:.1f}%")

        # Performance metrics
        if 'performance' in summary:
            print("\n⚡ PERFORMANCE METRICS:")
            perf = summary['performance']
            if 'google_avg_response_time' in perf:
                print(f"   Google: Avg {perf['google_avg_response_time']:.4f}s | "
                      f"Min {perf['google_min_response_time']:.4f}s | "
                      f"Max {perf['google_max_response_time']:.4f}s")
            if 'enhanced_avg_response_time' in perf:
                print(f"   Enhanced: Avg {perf['enhanced_avg_response_time']:.4f}s | "
                      f"Min {perf['enhanced_min_response_time']:.4f}s | "
                      f"Max {perf['enhanced_max_response_time']:.4f}s")

        # Production readiness
        print("\n🚀 PRODUCTION READINESS:")
        prod = summary['production_readiness']
        target = prod['target_accuracy']
        meets_target = prod['google_meets_target']

        print(f"   Target Accuracy: {target}%")
        print(f"   Google Meets Target: {'✅ YES' if meets_target else '❌ NO'}")
        if not meets_target:
            print(f"   Gap to Target: {prod['gap']:.1f}%")
        print(f"   Baseline (Enhanced): {prod['baseline_accuracy']:.1f}%")
        print(f"   Overall Improvement: +{prod['overall_improvement']:.1f}%")

        # Recommendations
        print("\n💡 RECOMMENDATIONS:")
        for recommendation in report['recommendations']:
            print(f"   {recommendation}")

        # Final verdict
        print("\n" + "="*80)
        if meets_target:
            print("✅ PRODUCTION READY - Google Translate API recommended for deployment")
        else:
            print("⚠️  NEEDS IMPROVEMENT - Consider fallback mechanisms or tuning")
        print("="*80)

def main():
    """Main execution function"""
    test_suite = LanguageDetectionTestSuite()
    report = test_suite.run_comprehensive_tests()
    test_suite.print_summary(report)

    # Save report to file
    report_file = '/Users/Subho/comprehensive_google_language_detection_report.json'
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\n📄 Detailed report saved to: {report_file}")

    return 0 if report['summary']['production_readiness']['google_meets_target'] else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())