#!/usr/bin/env python3
"""Get exact error message from build"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time

try:
    print("🔌 Connecting to Brave...")
    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    driver = webdriver.Chrome(options=chrome_options)

    # Look for error sections
    print("\n⚠️  Looking for error details...")

    # Try clicking on Errors and Warnings
    for selector in [
        "//button[contains(text(), 'Errors and Warnings')]",
        "//div[contains(text(), 'Errors and Warnings')]",
        "//span[contains(text(), 'Errors and Warnings')]",
    ]:
        try:
            elements = driver.find_elements(By.XPATH, selector)
            if elements:
                print(f"Found 'Errors and Warnings' element")
                driver.execute_script("arguments[0].click();", elements[0])
                print("✅ Clicked it")
                time.sleep(2)
                break
        except:
            continue

    # Get page text and look for specific error
    page_text = driver.find_element("tag name", "body").text

    print("\n🔍 Searching for error messages...")
    for line in page_text.split('\n'):
        line_lower = line.lower()
        if any(keyword in line_lower for keyword in ['error:', 'carrier phrase', 'required', 'invalid', 'failed']):
            if len(line.strip()) > 5:
                print(f"   📌 {line.strip()}")

    # Screenshot
    screenshot = f"/Users/Subho/alexa_error_detail_{int(time.time())}.png"
    driver.save_screenshot(screenshot)
    print(f"\n📸 Screenshot: {screenshot}")

    # Also check if there's an error panel visible
    error_panels = driver.find_elements(By.XPATH, "//div[contains(@class, 'error') or contains(@class, 'warning')]")
    if error_panels:
        print(f"\n📋 Found {len(error_panels)} error/warning panels")
        for i, panel in enumerate(error_panels[:3]):
            try:
                text = panel.text
                if text and len(text.strip()) > 10:
                    print(f"\n   Panel {i+1}:")
                    print(f"   {text.strip()[:200]}")
            except:
                pass

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
