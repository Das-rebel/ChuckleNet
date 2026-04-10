#!/usr/bin/env python3
"""Quick screenshot of current build status"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

try:
    print("🔌 Connecting to Brave...")
    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    driver = webdriver.Chrome(options=chrome_options)

    print("📸 Taking screenshot...")
    screenshot = f"/Users/Subho/alexa_build_status_now_{int(time.time())}.png"
    driver.save_screenshot(screenshot)
    print(f"✅ Screenshot: {screenshot}")

    # Get page text
    page_text = driver.find_element("tag name", "body").text

    # Look for build status
    print("\n🔨 Build Status:")
    for line in page_text.split('\n'):
        line_lower = line.lower()
        if any(keyword in line_lower for keyword in ['build', 'error', 'success', 'fail', 'complete']):
            if len(line.strip()) > 3:
                print(f"   {line.strip()}")

    print(f"\n🌐 Browser URL: {driver.current_url}")

except Exception as e:
    print(f"❌ Error: {e}")
