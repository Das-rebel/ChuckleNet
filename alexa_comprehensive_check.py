#!/usr/bin/env python3
"""
Comprehensive Alexa Skill Configuration Check
Verifies all settings on Amazon Developer Console
"""

import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

def connect_to_brave():
    """Connect to Brave browser"""
    try:
        print("🔌 Connecting to Brave...")
        chrome_options = Options()
        chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        driver = webdriver.Chrome(options=chrome_options)
        print("✅ Connected")
        return driver
    except Exception as e:
        print(f"❌ Failed: {e}")
        return None

def navigate_to_console(driver):
    """Navigate to Alexa console"""
    try:
        print("\n📍 Navigating to Alexa Developer Console...")
        driver.get("https://developer.amazon.com/alexa/console/ask")
        time.sleep(8)
        print("✅ Alexa Console loaded")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def check_skill_list(driver):
    """Check and screenshot skill list"""
    try:
        print("\n🔍 Checking skill list...")
        time.sleep(3)

        screenshot = f"/Users/Subho/alexa_check_1_skill_list_{int(time.time())}.png"
        driver.save_screenshot(screenshot)
        print(f"   📸 Screenshot: {screenshot}")

        # Look for Personal Assistant skill
        skill_found = False
        for selector in ["//div[contains(text(), 'Personal Assistant')]", "//span[contains(text(), 'Personal Assistant')]"]:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if elements:
                    print(f"   ✅ Found 'Personal Assistant' skill")
                    skill_found = True
                    # Click it
                    driver.execute_script("arguments[0].click();", elements[0])
                    time.sleep(4)
                    break
            except:
                continue

        if not skill_found:
            print("   ⚠️  Personal Assistant skill not found in list")

        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def check_invocation_name(driver):
    """Check invocation name in JSON Editor"""
    try:
        print("\n🎯 Checking Invocation Name...")

        # Click JSON Editor
        for selector in ["//span[contains(text(), 'JSON Editor')]", "//button[contains(text(), 'JSON Editor')]"]:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if elements:
                    driver.execute_script("arguments[0].click();", elements[0])
                    print("   ✅ Opened JSON Editor")
                    time.sleep(3)
                    break
            except:
                continue

        # Screenshot JSON Editor
        screenshot = f"/Users/Subho/alexa_check_2_json_editor_{int(time.time())}.png"
        driver.save_screenshot(screenshot)
        print(f"   📸 Screenshot: {screenshot}")

        # Get JSON content
        try:
            textarea = driver.find_element(By.TAG_NAME, "textarea")
            json_content = textarea.get_attribute('value')

            # Parse JSON
            data = json.loads(json_content)
            invocation_name = data['interactionModel']['languageModel']['invocationName']

            print(f"   📝 Invocation Name: '{invocation_name}'")

            if invocation_name.lower() == "personal assistant":
                print("   ✅ CORRECT: Invocation name is 'personal assistant'")
            else:
                print(f"   ⚠️  WARNING: Should be 'personal assistant', found '{invocation_name}'")

            # Check intents
            intents = data['interactionModel']['languageModel']['intents']
            print(f"\n   📋 Intents found: {len(intents)}")

            for intent in intents:
                if intent['name'] == 'ChatIntent':
                    print(f"      • ChatIntent:")
                    print(f"        - Samples: {intent['samples'][:3]}...")  # Show first 3
                    has_carrier = any('ask' in s.lower() or 'tell' in s.lower() or 'what' in s.lower()
                                    for s in intent.get('samples', []))
                    if has_carrier:
                        print(f"        ✅ Has carrier phrases")
                    else:
                        print(f"        ❌ Missing carrier phrases!")

        except Exception as e:
            print(f"   ⚠️  Could not parse JSON: {e}")

        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def check_endpoints(driver):
    """Check endpoint configuration"""
    try:
        print("\n🔗 Checking Endpoints...")

        # Click Endpoints
        endpoint_selectors = [
            "//span[contains(text(), 'Endpoints')]",
            "//a[contains(text(), 'Endpoints')]",
        ]

        clicked = False
        for selector in endpoint_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if elements:
                    driver.execute_script("arguments[0].click();", elements[0])
                    print("   ✅ Opened Endpoints")
                    time.sleep(3)
                    clicked = True
                    break
            except:
                continue

        if not clicked:
            print("   ⚠️  Could not click Endpoints tab")
            return True

        # Screenshot
        screenshot = f"/Users/Subho/alexa_check_3_endpoints_{int(time.time())}.png"
        driver.save_screenshot(screenshot)
        print(f"   📸 Screenshot: {screenshot}")

        # Check endpoint input
        expected = "https://afad-2406-7400-9d-5689-8575-7c96-da58-d7d2.ngrok-free.app/alexa"

        for selector in ["//input[@name='default']", "//input[@type='url']", "//textarea"]:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if elements:
                    for elem in elements:
                        value = elem.get_attribute('value')
                        if value and ('ngrok' in value or 'http' in value):
                            print(f"   📝 Endpoint: {value}")
                            if value == expected:
                                print(f"   ✅ CORRECT: Endpoint matches ngrok URL")
                            elif 'ngrok-free.app' in value:
                                print(f"   ✅ OK: Has ngrok URL (may be different session)")
                            else:
                                print(f"   ⚠️  WARNING: Unexpected endpoint")
                            return True
            except:
                continue

        print("   ⚠️  Could not find endpoint field")
        return True

    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def check_test_tab(driver):
    """Check Test tab and device setup"""
    try:
        print("\n🧪 Checking Test Tab...")

        # Click Test
        test_selectors = [
            "//span[contains(text(), 'Test')]",
            "//button[contains(text(), 'Test')]",
        ]

        clicked = False
        for selector in test_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if elements:
                    driver.execute_script("arguments[0].click();", elements[0])
                    print("   ✅ Opened Test tab")
                    time.sleep(3)
                    clicked = True
                    break
            except:
                continue

        if not clicked:
            print("   ⚠️  Could not click Test tab")
            return True

        # Screenshot
        screenshot = f"/Users/Subho/alexa_check_4_test_tab_{int(time.time())}.png"
        driver.save_screenshot(screenshot)
        print(f"   📸 Screenshot: {screenshot}")

        # Look for device setup info
        page_text = driver.find_element(By.TAG_NAME, "body").text

        if 'device' in page_text.lower():
            print("   📱 Device section found")

            # Try to identify if device is registered
            device_indicators = ['your device', 'test device', 'enabled', 'registered']
            found_devices = [ind for ind in device_indicators if ind.lower() in page_text.lower()]

            if found_devices:
                print(f"   ℹ️  Found device indicators: {found_devices}")
            else:
                print("   ⚠️  Could not determine device status")

        # Check for simulator
        if 'simulator' in page_text.lower():
            print("   ✅ Simulator available")

        return True

    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def check_certificate_tab(driver):
    """Check distribution/certificate settings"""
    try:
        print("\n📜 Checking Distribution Tab...")

        # Click Distribution/Deployment
        dist_selectors = [
            "//span[contains(text(), 'Distribution')]",
            "//span[contains(text(), 'Deployment')]",
        ]

        clicked = False
        for selector in dist_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if elements:
                    driver.execute_script("arguments[0].click();", elements[0])
                    print("   ✅ Opened Distribution")
                    time.sleep(3)
                    clicked = True
                    break
            except:
                continue

        if not clicked:
            print("   ℹ️  Distribution tab not found (may be in different location)")
            return True

        # Screenshot
        screenshot = f"/Users/Subho/alexa_check_5_distribution_{int(time.time())}.png"
        driver.save_screenshot(screenshot)
        print(f"   📸 Screenshot: {screenshot}")

        # Check availability
        page_text = driver.find_element(By.TAG_NAME, "body").text

        if 'development' in page_text.lower():
            print("   ✅ Skill is in Development mode")

        if 'certification' in page_text.lower() or 'live' in page_text.lower():
            print("   ℹ️  Skill may be in Certification/Live")

        return True

    except Exception as e:
        print(f"   ℹ️  Could not check distribution: {e}")
        return True

def check_build_status(driver):
    """Check current build status"""
    try:
        print("\n🔨 Checking Build Status...")

        # Go back to interaction model
        for selector in ["//span[contains(text(), 'Interaction Model')]", "//a[contains(text(), 'Interaction Model')]"]:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if elements:
                    driver.execute_script("arguments[0].click();", elements[0])
                    time.sleep(2)
                    break
            except:
                continue

        # Look for build status indicators
        page_text = driver.find_element(By.TAG_NAME, "body").text

        if 'build' in page_text.lower():
            # Look for status indicators
            if 'success' in page_text.lower() or 'complete' in page_text.lower():
                print("   ✅ Build: Successful/Complete")
            elif 'in progress' in page_text.lower() or 'building' in page_text.lower():
                print("   ⏳ Build: In progress")
            elif 'error' in page_text.lower() or 'failed' in page_text.lower():
                print("   ❌ Build: Has errors")
            else:
                print("   ℹ️  Build status unclear")

        # Screenshot for visual verification
        screenshot = f"/Users/Subho/alexa_check_6_build_status_{int(time.time())}.png"
        driver.save_screenshot(screenshot)
        print(f"   📸 Screenshot: {screenshot}")

        return True

    except Exception as e:
        print(f"   ⚠️  Could not check build status: {e}")
        return False

def generate_report():
    """Generate final report"""
    print("\n" + "=" * 60)
    print("📊 COMPREHENSIVE CHECK COMPLETE")
    print("=" * 60)
    print("\n✅ Screenshots saved:")
    print("   • Skill list")
    print("   • JSON Editor (invocation name & intents)")
    print("   • Endpoints configuration")
    print("   • Test tab & device setup")
    print("   • Distribution settings")
    print("   • Build status")
    print("\n📋 Check the screenshots above to verify all settings.")
    print("📁 All screenshots saved to: /Users/Subho/alexa_check_*.png")
    print("\n" + "=" * 60)

def main():
    print("🔍 ALEXA SKILL COMPREHENSIVE CHECK")
    print("=" * 60)
    print("\nThis will check:")
    print("• Skill name and listing")
    print("• Invocation name (must be 'personal assistant')")
    print("• JSON interaction model")
    print("• Endpoint URL (must match ngrok)")
    print("• Test tab & device registration")
    print("• Distribution/Availability settings")
    print("• Build status")
    print()

    driver = None
    try:
        driver = connect_to_brave()
        if not driver:
            return

        navigate_to_console(driver)
        check_skill_list(driver)
        check_invocation_name(driver)
        check_endpoints(driver)
        check_test_tab(driver)
        check_certificate_tab(driver)
        check_build_status(driver)

        generate_report()

        # Final summary screenshot
        screenshot = f"/Users/Subho/alexa_check_FINAL_{int(time.time())}.png"
        driver.save_screenshot(screenshot)
        print(f"\n📸 Final screenshot: {screenshot}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            print("\n🌐 Brave browser remains open")
            print("📝 Check screenshots for detailed verification")

if __name__ == "__main__":
    main()
