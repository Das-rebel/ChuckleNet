#!/usr/bin/env python3
"""
QUICK SCREENSHOT TEST
Non-interactive screenshot analysis for trading signals
"""

import os
import sys
from datetime import datetime
from PIL import ImageGrab
import pytesseract

def quick_test():
    """Quick screenshot test"""
    print("🚀 QUICK SCREENSHOT TEST")
    print("=" * 30)
    print("📸 Taking 3 screenshots...")
    print("💡 Make sure your Telegram group is visible!")
    print("⏳ 5 second delay between captures")
    print("=" * 30)

    results_dir = "quick_screenshot_test"
    os.makedirs(results_dir, exist_ok=True)

    for i in range(3):
        try:
            print(f"\n📸 Screenshot {i+1}/3...")

            # Take screenshot
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_screenshot_{timestamp}.png"
            filepath = os.path.join(results_dir, filename)

            screenshot = ImageGrab.grab()
            screenshot.save(filepath)
            print(f"✅ Screenshot saved: {filename}")

            # Analyze with OCR
            print("🔍 Analyzing with OCR...")
            text = pytesseract.image_to_string(screenshot)
            print(f"📝 Extracted {len(text)} characters")

            # Quick trading signal check
            trading_keywords = ['buy', 'sell', 'btc', 'eth', 'sol', 'price', 'target']
            has_trading = any(keyword in text.lower() for keyword in trading_keywords)

            if has_trading:
                print("🎯 TRADING CONTENT DETECTED!")
                print(f"📝 Preview: {text[:200]}...")
            else:
                print("⚠️ No trading content found")

            if i < 2:
                print("⏳ Waiting 5 seconds...")
                import time
                time.sleep(5)

        except Exception as e:
            print(f"❌ Error: {e}")
            break

    print(f"\n✅ Test complete! Check: {results_dir}")

if __name__ == "__main__":
    quick_test()