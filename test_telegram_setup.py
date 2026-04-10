#!/usr/bin/env python3
"""
Test script for Telegram Trading Scraper Setup
"""

import sys
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def test_chrome_driver():
    """Test if Chrome driver is working"""
    print("🔧 Testing Chrome driver setup...")

    try:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')

        driver = webdriver.Chrome(options=chrome_options)

        # Test navigation
        driver.get("https://www.google.com")
        title = driver.title

        if "Google" in title:
            print("✅ Chrome driver is working correctly!")
            driver.quit()
            return True
        else:
            print("❌ Chrome driver navigation test failed")
            driver.quit()
            return False

    except Exception as e:
        print(f"❌ Chrome driver test failed: {str(e)}")
        return False

def test_dependencies():
    """Test if all dependencies are installed"""
    print("📦 Testing dependencies...")

    required_modules = [
        'selenium', 'pandas', 'numpy', 'json', 'logging',
        'datetime', 're', 'argparse', 'os', 'sys', 'time'
    ]

    missing_modules = []

    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module} - OK")
        except ImportError:
            print(f"❌ {module} - Missing")
            missing_modules.append(module)

    if missing_modules:
        print(f"\n⚠️  Missing modules: {missing_modules}")
        print("Install with: pip3 install " + " ".join(missing_modules))
        return False
    else:
        print("\n✅ All dependencies are installed!")
        return True

def test_telegram_access():
    """Test if Telegram Web is accessible"""
    print("🌐 Testing Telegram Web access...")

    try:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')

        driver = webdriver.Chrome(options=chrome_options)

        # Test Telegram Web access
        driver.get("https://web.telegram.org/k/")
        time.sleep(5)

        title = driver.title
        current_url = driver.current_url

        if "telegram" in title.lower() or "telegram" in current_url.lower():
            print("✅ Telegram Web is accessible!")
            driver.quit()
            return True
        else:
            print(f"⚠️  Telegram Web may have issues. Title: {title}, URL: {current_url}")
            driver.quit()
            return False

    except Exception as e:
        print(f"❌ Telegram Web access test failed: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🚀 Telegram Trading Scraper Setup Test")
    print("=" * 50)

    tests = [
        ("Dependencies", test_dependencies),
        ("Chrome Driver", test_chrome_driver),
        ("Telegram Access", test_telegram_access)
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} Test...")
        print("-" * 30)

        result = test_func()
        results.append((test_name, result))

    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:20} : {status}")
        if result:
            passed += 1

    print(f"\nOverall Result: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! You're ready to use the Telegram Trading Scraper.")
        print("\nNext steps:")
        print("1. Run: python telegram_scraper_enhanced.py")
        print("2. Manually authenticate when prompted")
        print("3. Monitor the trading signals")
    else:
        print("\n⚠️  Some tests failed. Please fix the issues before running the scraper.")

    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)