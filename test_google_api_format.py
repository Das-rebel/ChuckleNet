#!/usr/bin/env python3
"""
Test Google Translate API response format to understand detection capabilities
"""

import requests
import json

def test_google_api():
    """Test Google Translate API to understand the response format"""

    test_texts = [
        "Hello, how are you?",  # English
        "नमस्ते, आप कैसे हैं?",  # Hindi
        "নমস্কার, আপনি কেমন আছেন?",  # Bengali
        "Weather kaisa hai aaj?",  # Hinglish
        "Weather kemon ache aaj?",  # Benglish
    ]

    url = "https://translate.googleapis.com/translate_a/single"

    print("Testing Google Translate API Response Format")
    print("="*80)

    for text in test_texts:
        print(f"\n📝 Testing: '{text}'")

        try:
            params = {
                'client': 'gtx',
                'sl': 'auto',  # Auto-detect source language
                'tl': 'en',    # Translate to English
                'dt': 't',     # Translation
                'q': text
            }

            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                result_data = response.json()

                print(f"✅ Response successful (HTTP {response.status_code})")
                print(f"🔍 Full response structure:")
                print(json.dumps(result_data, indent=2)[:500] + "...")

                # Try to extract detection information
                if len(result_data) > 2:
                    detection_info = result_data[2]
                    print(f"\n📊 Detection info found: {detection_info}")

                    if detection_info and len(detection_info) > 0:
                        detected_lang = detection_info[0][0] if len(detection_info[0]) > 0 else 'unknown'
                        print(f"🌍 Detected Language: {detected_lang}")

                # Try to extract translation
                if result_data[0]:
                    translation = result_data[0][0][0] if result_data[0][0] else 'N/A'
                    print(f"📝 Translation: {translation}")

            else:
                print(f"❌ Request failed: HTTP {response.status_code}")

        except Exception as e:
            print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_google_api()