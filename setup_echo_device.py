#!/usr/bin/env python3
"""
Navigate to Test tab and find Device Setup for Echo registration
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time

try:
    print("🔌 Connecting to Brave...")
    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    driver = webdriver.Chrome(options=chrome_options)

    # Navigate to Alexa console if needed
    current_url = driver.current_url
    print(f"📍 Current URL: {current_url}")

    if 'alexa/console/ask' not in current_url:
        print("📍 Navigating to Alexa Console...")
        driver.get("https://developer.amazon.com/alexa/console/ask")
        time.sleep(8)

    # Find and click the skill
    print("\n🔍 Looking for 'Personal Assistant' skill...")
    skill_selectors = [
        "//div[contains(text(), 'Personal Assistant')]",
        "//span[contains(text(), 'Personal Assistant')]",
    ]

    for selector in skill_selectors:
        try:
            elements = driver.find_elements(By.XPATH, selector)
            if elements:
                driver.execute_script("arguments[0].click();", elements[0])
                print("✅ Clicked 'Personal Assistant' skill")
                time.sleep(5)
                break
        except:
            continue

    # Click Test tab
    print("\n🧪 Clicking Test tab...")
    test_selectors = [
        "//span[contains(text(), 'Test')]",
        "//button[contains(text(), 'Test')]",
        "//a[contains(text(), 'Test')]",
    ]

    clicked = False
    for selector in test_selectors:
        try:
            elements = driver.find_elements(By.XPATH, selector)
            if elements:
                driver.execute_script("arguments[0].click();", elements[0])
                print("✅ Clicked Test tab")
                time.sleep(5)
                clicked = True
                break
        except:
            continue

    if not clicked:
        print("⚠️  Could not click Test tab")

    # Screenshot current view
    screenshot = f"/Users/Subho/alexa_test_tab_{int(time.time())}.png"
    driver.save_screenshot(screenshot)
    print(f"\n📸 Screenshot 1: {screenshot}")

    # Look for Device Setup section
    print("\n🔍 Looking for Device Setup section...")

    # Try scrolling down to find Device Setup
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)

    # Screenshot after scroll
    screenshot2 = f"/Users/Subho/alexa_test_tab_scrolled_{int(time.time())}.png"
    driver.save_screenshot(screenshot2)
    print(f"📸 Screenshot 2 (scrolled): {screenshot2}")

    # Search for device-related text
    page_text = driver.find_element(By.TAG_NAME, "body").text

    print("\n📋 Searching for device-related content...")
    device_keywords_found = []
    for line in page_text.split('\n'):
        line_lower = line.lower()
        if any(keyword in line_lower for keyword in ['device', 'echo', 'alexa', 'register', 'setup']):
            if len(line.strip()) > 3 and len(line.strip()) < 100:
                device_keywords_found.append(line.strip())

    if device_keywords_found:
        print("\n✅ Found device-related content:")
        for item in device_keywords_found[:15]:
            print(f"   • {item}")

    # Look for specific Device Setup elements
    print("\n🔍 Looking for Device Setup elements...")

    # Try to find device-related buttons or links
    device_button_selectors = [
        "//button[contains(text(), 'Device')]",
        "//button[contains(text(), 'Add Device')]",
        "//a[contains(text(), 'Device')]",
        "//div[contains(text(), 'Device Setup')]",
        "//button[contains(text(), 'Register')]",
    ]

    for selector in device_button_selectors:
        try:
            elements = driver.find_elements(By.XPATH, selector)
            if elements:
                for elem in elements[:3]:
                    try:
                        text = elem.text
                        if text and len(text.strip()) > 0:
                            print(f"   📌 Found: '{text.strip()}'")

                            # If it's a button, take a screenshot of it
                            if 'button' in selector:
                                driver.execute_script("arguments[0].scrollIntoView();", elem)
                                time.sleep(1)
                                screenshot_btn = f"/Users/Subho/alexa_device_button_{int(time.time())}.png"
                                driver.save_screenshot(screenshot_btn)
                                print(f"   📸 Screenshot: {screenshot_btn}")
                    except:
                        pass
        except:
            continue

    # Check for Simulator section
    print("\n🎮 Checking for Simulator...")
    simulator_found = False
    if 'simulator' in page_text.lower():
        print("✅ Simulator found on page")
        simulator_found = True

        # Look for simulator input
        input_selectors = [
            "//input[@type='text']",
            "//textarea",
            "//input[contains(@placeholder, 'try')]",
        ]

        for selector in input_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if elements:
                    for elem in elements[:3]:
                        placeholder = elem.get_attribute('placeholder')
                        if placeholder:
                            print(f"   📝 Input found: '{placeholder}'")
            except:
                continue

    # Final screenshot
    screenshot_final = f"/Users/Subho/alexa_device_setup_final_{int(time.time())}.png"
    driver.save_screenshot(screenshot_final)
    print(f"\n📸 Final screenshot: {screenshot_final}")

    print("\n" + "="*60)
    print("📋 DEVICE SETUP CHECK COMPLETE")
    print("="*60)
    print("\n📁 Screenshots saved to:")
    print(f"   • {screenshot}")
    print(f"   • {screenshot2}")
    print(f"   • {screenshot_final}")

    if not device_keywords_found:
        print("\n⚠️  Device Setup section not found")
        print("   This might mean:")
        print("   • Device Setup is in a different location")
        print("   • Your device is already registered")
        print("   • The interface has changed")
    else:
        print("\n✅ Device-related content found")

    print("\n💡 Next steps:")
    print("   1. Check the screenshots above")
    print("   2. Look for 'Device Setup' or 'Your Devices' section")
    print("   3. If found, click 'Add Device' button")
    print("   4. Select your Echo from the list")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
