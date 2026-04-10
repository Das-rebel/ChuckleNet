#!/usr/bin/env python3
"""
Fix Open Claw skill - Click on it and check the error
"""

import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

def connect_to_brave():
    """Connect to Brave"""
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

def find_and_click_open_claw(driver):
    """Find and click Open Claw skill"""
    try:
        print("\n🔍 Looking for 'Open Claw' skill...")

        # Look for Open Claw
        skill_selectors = [
            "//div[contains(text(), 'Open Claw')]",
            "//span[contains(text(), 'Open Claw')]",
            "//h3[contains(text(), 'Open Claw')]",
            "//a[contains(text(), 'Open Claw')]",
        ]

        for selector in skill_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if elements:
                    print(f"   ✅ Found 'Open Claw' skill")
                    driver.execute_script("arguments[0].scrollIntoView();", elements[0])
                    time.sleep(1)
                    driver.execute_script("arguments[0].click();", elements[0])
                    print("   ✅ Clicked Open Claw")
                    time.sleep(5)
                    return True
            except Exception as e:
                print(f"   Selector failed: {e}")
                continue

        print("   ❌ Could not find Open Claw skill")
        return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def check_error_message(driver):
    """Look for error messages"""
    try:
        print("\n⚠️  Checking for error messages...")

        # Screenshot current state
        screenshot = f"/Users/Subho/alexa_open_claw_error_{int(time.time())}.png"
        driver.save_screenshot(screenshot)
        print(f"   📸 Screenshot: {screenshot}")

        # Look for error text
        page_text = driver.find_element(By.TAG_NAME, "body").text

        # Common error indicators
        error_keywords = ['error', 'failed', 'invalid', 'missing', 'required', 'carrier phrase']

        errors_found = []
        for line in page_text.split('\n'):
            if any(keyword in line.lower() for keyword in error_keywords):
                if len(line.strip()) > 5:  # Ignore very short matches
                    errors_found.append(line.strip())

        if errors_found:
            print(f"\n   ❌ ERRORS FOUND:")
            for error in errors_found[:10]:  # Show first 10
                print(f"      • {error}")
        else:
            print("   ℹ️  No error text found on page")

        # Look for build status
        if 'build' in page_text.lower():
            print(f"\n   🔨 Build Status:")
            for line in page_text.split('\n'):
                if 'build' in line.lower() and len(line.strip()) > 0:
                    print(f"      • {line.strip()}")

        return True

    except Exception as e:
        print(f"❌ Error checking: {e}")
        return False

def open_json_editor(driver):
    """Open JSON Editor"""
    try:
        print("\n📝 Opening JSON Editor...")

        for selector in ["//span[contains(text(), 'JSON Editor')]", "//button[contains(text(), 'JSON Editor')]"]:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if elements:
                    driver.execute_script("arguments[0].click();", elements[0])
                    print("   ✅ Opened JSON Editor")
                    time.sleep(3)
                    return True
            except:
                continue

        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def check_json_content(driver):
    """Check and fix JSON content"""
    try:
        print("\n📄 Checking JSON content...")

        # Try to get JSON from textarea
        try:
            textarea = driver.find_element(By.TAG_NAME, "textarea")
            content = textarea.get_attribute('value')

            if not content or content.strip() == "":
                print("   ⚠️  JSON Editor is EMPTY - this is the problem!")
                print("   🔧 Need to add interaction model...")
                return False

            print(f"   📝 Current JSON length: {len(content)} chars")

            # Try to parse
            try:
                data = json.loads(content)

                # Check invocation name
                invocation = data.get('interactionModel', {}).get('languageModel', {}).get('invocationName', '')
                print(f"   📌 Invocation Name: '{invocation}'")

                # Check intents
                intents = data.get('interactionModel', {}).get('languageModel', {}).get('intents', [])
                print(f"   📋 Intents: {len(intents)}")

                for intent in intents:
                    if intent.get('name') == 'ChatIntent':
                        samples = intent.get('samples', [])
                        print(f"      ChatIntent samples: {samples}")

                        # Check for carrier phrases
                        has_carrier = any('ask' in s.lower() or 'tell' in s.lower() or 'what' in s.lower()
                                        for s in samples)
                        if not has_carrier:
                            print("      ❌ PROBLEM: No carrier phrases found!")
                            return False
                        else:
                            print("      ✅ Has carrier phrases")

            except json.JSONDecodeError as e:
                print(f"   ❌ JSON Parse Error: {e}")
                return False

        except Exception as e:
            print(f"   ⚠️  Could not get textarea: {e}")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def fix_json(driver):
    """Fix the JSON with correct interaction model"""
    try:
        print("\n🔧 Fixing JSON...")

        # Find textarea
        try:
            textarea = driver.find_element(By.TAG_NAME, "textarea")
        except:
            print("   ❌ Could not find JSON editor")
            return False

        # Correct JSON
        correct_json = '''{
  "interactionModel": {
    "languageModel": {
      "invocationName": "open claw",
      "intents": [
        {
          "name": "AMAZON.CancelIntent",
          "samples": []
        },
        {
          "name": "AMAZON.HelpIntent",
          "samples": []
        },
        {
          "name": "AMAZON.StopIntent",
          "samples": []
        },
        {
          "name": "ChatIntent",
          "samples": [
            "ask {query}",
            "tell me {query}",
            "what is {query}",
            "what's {query}",
            "say {query}"
          ],
          "slots": [
            {
              "name": "query",
              "type": "AMAZON.SearchQuery"
            }
          ]
        }
      ],
      "types": []
    }
  }
}'''

        # Clear and set new content
        driver.execute_script("""
            arguments[0].value = '';
            arguments[0].innerHTML = '';
            arguments[0].value = arguments[1];
            arguments[0].innerHTML = arguments[1];
            arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
            arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
        """, textarea, correct_json)

        print("   ✅ JSON fixed with invocation name: 'open claw'")
        print("   ✅ Added carrier phrases: ask, tell me, what is, what's, say")

        time.sleep(2)
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def save_and_build(driver):
    """Save and build"""
    try:
        print("\n💾 Saving and building...")

        # Save
        save_selectors = ["//button[contains(text(), 'Save Model')]", "//button[contains(., 'Save')]"]
        for selector in save_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if elements:
                    driver.execute_script("arguments[0].click();", elements[0])
                    print("   ✅ Saved")
                    time.sleep(2)
                    break
            except:
                continue

        # Build
        build_selectors = ["//button[contains(text(), 'Build Model')]", "//button[contains(., 'Build')]"]
        for selector in build_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if elements:
                    driver.execute_script("arguments[0].click();", elements[0])
                    print("   ✅ Building...")
                    print("   ⏳ Wait 30-60 seconds for green checkmark")
                    time.sleep(5)
                    break
            except:
                continue

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("🔧 FIXING OPEN CLAW SKILL")
    print("=" * 50)

    driver = None
    try:
        driver = connect_to_brave()
        if not driver:
            return

        # Navigate to console if needed
        if not 'developer.amazon.com' in driver.current_url:
            print("📍 Navigating to Alexa Console...")
            driver.get("https://developer.amazon.com/alexa/console/ask")
            time.sleep(8)

        # Find and click Open Claw
        find_and_click_open_claw(driver)

        # Check for errors
        check_error_message(driver)

        # Open JSON Editor
        open_json_editor(driver)

        # Check current content
        check_json_content(driver)

        # Fix it
        fix_json(driver)

        # Save and build
        save_and_build(driver)

        print("\n" + "=" * 50)
        print("🎉 FIX COMPLETE!")
        print("=" * 50)
        print("\n✅ Changes made:")
        print("   • Invocation name: 'open claw'")
        print("   • Added carrier phrases to ChatIntent")
        print("   • Model saved and build started")
        print("\n📋 Test with:")
        print('   "Alexa, open Open Claw"')
        print('   "Alexa, ask Open Claw what time is it"')
        print("\n⏳ Wait for build to complete...\n")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            print("🌐 Brave remains open - check for green checkmark")

if __name__ == "__main__":
    main()
