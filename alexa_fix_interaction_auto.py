#!/usr/bin/env python3
"""
Automatic Alexa Interaction Model Fix - No user input required
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
        print("✅ Connected to Brave")
        return driver
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return None

def update_interaction_model(driver):
    """Update the interaction model JSON"""
    try:
        print("\n📝 Updating Interaction Model...")
        time.sleep(2)

        # Click JSON Editor tab
        json_selectors = ["//span[contains(text(), 'JSON Editor')]", "//button[contains(text(), 'JSON Editor')]"]
        for selector in json_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if elements:
                    driver.execute_script("arguments[0].click();", elements[0])
                    print("   ✅ Clicked JSON Editor")
                    time.sleep(3)
                    break
            except:
                continue

        # Find and update JSON editor
        textarea = None
        try:
            textarea = driver.find_element(By.TAG_NAME, "textarea")
            print("   ✅ Found JSON editor")
        except:
            # Try contenteditable div
            try:
                textarea = driver.find_element(By.XPATH, "//div[@contenteditable='true']")
                print("   ✅ Found JSON editor (div)")
            except:
                print("   ⚠️  Could not find JSON editor")
                return False

        # New correct JSON
        new_json = '''{
  "interactionModel": {
    "languageModel": {
      "invocationName": "personal assistant",
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
              "type": "AMAZON.SearchQuery",
              "samples": ["the time", "a joke", "what's the weather"]
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
        """, textarea, new_json)

        time.sleep(2)
        print("   ✅ JSON updated with carrier phrases")

        # Screenshot
        screenshot = f"/Users/Subho/alexa_json_fixed_{int(time.time())}.png"
        driver.save_screenshot(screenshot)
        print(f"   📸 Screenshot: {screenshot}")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def save_and_build(driver):
    """Save and build"""
    try:
        print("\n💾 Saving and building...")

        # Save
        for selector in ["//button[contains(text(), 'Save Model')]", "//button[contains(., 'Save']]"]:
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
        for selector in ["//button[contains(text(), 'Build Model')]", "//button[contains(., 'Build')]"]:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if elements:
                    driver.execute_script("arguments[0].click();", elements[0])
                    print("   ✅ Building (may take 30-60s)")
                    time.sleep(3)
                    break
            except:
                continue
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("🚀 AUTOMATIC INTERACTION MODEL FIX")
    print("=" * 40)

    driver = connect_to_brave()
    if not driver:
        return

    if update_interaction_model(driver):
        save_and_build(driver)

        print("\n" + "=" * 40)
        print("🎉 FIXED!")
        print("=" * 40)
        print("\n✅ Sample utterances now include carrier phrases:")
        print("   • ask {query}")
        print("   • tell me {query}")
        print("   • what is {query}")
        print("   • what's {query}")
        print("\n📋 Test with:")
        print('   "Alexa, ask Personal Assistant what time is it"')
        print('   "Alexa, tell Personal Assistant to tell me a joke"')
        print("\n⏳ Wait for build to complete...\n")

if __name__ == "__main__":
    main()
