#!/usr/bin/env python3
"""
Quick script to update Alexa Interaction Model with carrier phrases
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

        # Navigate to JSON Editor
        print("   Navigating to JSON Editor...")

        # Wait for page to be ready
        time.sleep(2)

        # Try to find and click JSON Editor tab
        json_editor_selectors = [
            "//span[contains(text(), 'JSON Editor')]",
            "//button[contains(text(), 'JSON Editor')]",
            "//a[contains(text(), 'JSON Editor')]",
        ]

        clicked = False
        for selector in json_editor_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if elements:
                    driver.execute_script("arguments[0].click();", elements[0])
                    print("   ✅ Clicked JSON Editor")
                    clicked = True
                    time.sleep(2)
                    break
            except:
                continue

        if not clicked:
            print("   ⚠️  Could not find JSON Editor button")
            print("   Please click 'JSON Editor' tab manually")
            input("   Press Enter when done...")
            time.sleep(2)

        # Find the JSON editor textarea
        print("   Looking for JSON editor...")

        textarea_selectors = [
            "//textarea",
            "//div[@contenteditable='true']",
            "//pre[@contenteditable='true']",
        ]

        textarea = None
        for selector in textarea_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if elements:
                    # Find the largest textarea (likely the JSON editor)
                    textarea = max(elements, key=lambda e: e.size['width'] * e.size['height'])
                    print("   ✅ Found JSON editor")
                    break
            except:
                continue

        if not textarea:
            print("   ⚠️  Could not find JSON editor textarea")
            return False

        # Clear existing content
        print("   Clearing existing content...")
        driver.execute_script("""
            arguments[0].value = '';
            arguments[0].innerHTML = '';
        """, textarea)

        time.sleep(1)

        # New correct JSON with carrier phrases
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
              "samples": [
                "the time",
                "a joke",
                "what's the weather"
              ]
            }
          ]
        }
      ],
      "types": []
    }
  }
}'''

        # Set new content
        print("   Inserting new JSON...")
        driver.execute_script("""
            arguments[0].value = arguments[1];
            arguments[0].innerHTML = arguments[1];
            // Trigger change events
            arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
            arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
        """, textarea, new_json)

        time.sleep(2)

        print("   ✅ JSON updated successfully!")

        # Take screenshot
        screenshot_path = f"/Users/Subho/alexa_json_updated_{int(time.time())}.png"
        driver.save_screenshot(screenshot_path)
        print(f"   📸 Screenshot saved: {screenshot_path}")

        return True

    except Exception as e:
        print(f"❌ Error updating JSON: {e}")
        import traceback
        traceback.print_exc()
        return False

def save_and_build(driver):
    """Save and build the model"""
    try:
        print("\n💾 Saving and building...")

        # Save
        save_selectors = [
            "//button[contains(text(), 'Save Model')]",
            "//button[contains(., 'Save')]",
        ]

        for selector in save_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if elements:
                    driver.execute_script("arguments[0].click();", elements[0])
                    print("   ✅ Saved model")
                    time.sleep(2)
                    break
            except:
                continue

        # Build
        build_selectors = [
            "//button[contains(text(), 'Build Model')]",
            "//button[contains(., 'Build')]",
        ]

        for selector in build_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if elements:
                    driver.execute_script("arguments[0].click();", elements[0])
                    print("   ✅ Building model...")
                    print("   ⏳ This may take 30-60 seconds...")
                    time.sleep(3)
                    break
            except:
                continue

        return True

    except Exception as e:
        print(f"❌ Error saving/building: {e}")
        return False

def main():
    print("🚀 ALEXA INTERACTION MODEL FIXER")
    print("=" * 50)
    print()
    print("This script will:")
    print("1. Connect to Brave browser")
    print("2. Navigate to JSON Editor")
    print("3. Update the interaction model with carrier phrases")
    print("4. Save and build the model")
    print()
    print("Make sure you're on the Alexa skill page in Brave!")
    print()

    input("Press Enter when ready...")

    driver = None
    try:
        driver = connect_to_brave()
        if not driver:
            return

        if update_interaction_model(driver):
            save_and_build(driver)

            print("\n" + "=" * 50)
            print("🎉 FIX COMPLETE!")
            print("=" * 50)
            print()
            print("✅ Interaction model updated with carrier phrases:")
            print("   • ask {query}")
            print("   • tell me {query}")
            print("   • what is {query}")
            print("   • what's {query}")
            print()
            print("📋 Now you can test with:")
            print('   "Alexa, ask Personal Assistant what time is it"')
            print('   "Alexa, tell Personal Assistant to tell me a joke"')
            print('   "Alexa, ask Personal Assistant what is 3 plus 3"')
            print()
            print("⏳ Wait for build to complete (green checkmark)")
            print()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            print("🌐 Brave browser remains open")

if __name__ == "__main__":
    main()
