#!/usr/bin/env python3
"""Fix with complete JSON including slot samples"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time

try:
    print("🔌 Connecting to Brave...")
    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    driver = webdriver.Chrome(options=chrome_options)

    # Open JSON Editor
    print("\n📝 Opening JSON Editor...")
    for selector in ["//span[contains(text(), 'JSON Editor')]", "//button[contains(text(), 'JSON Editor')]"]:
        try:
            elements = driver.find_elements(By.XPATH, selector)
            if elements:
                driver.execute_script("arguments[0].click();", elements[0])
                print("✅ Opened JSON Editor")
                time.sleep(3)
                break
        except:
            continue

    # COMPLETE JSON with slot samples
    complete_json = '''{
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
              "type": "AMAZON.SearchQuery",
              "samples": [
                "the time",
                "a joke",
                "three plus three"
              ]
            }
          ]
        }
      ],
      "types": []
    }
  }
}'''

    # Apply to textarea
    print("\n🔧 Applying COMPLETE JSON (with slot samples)...")
    try:
        textarea = driver.find_element(By.TAG_NAME, "textarea")

        # Clear and set
        driver.execute_script("""
            arguments[0].value = arguments[1];
            arguments[0].innerHTML = arguments[1];
            arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
            arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
            arguments[0].dispatchEvent(new Event('blur', { bubbles: true }));
            // Trigger all possible events
            var event = new Event('input', { bubbles: true });
            event.data = arguments[1];
            arguments[0].dispatchEvent(event);
        """, textarea, complete_json)

        print("✅ JSON applied with:")
        print("   • Invocation: 'open claw'")
        print("   • ChatIntent with 5 carrier phrases")
        print("   • Slot with 3 sample values")
        time.sleep(3)

    except Exception as e:
        print(f"❌ Error applying JSON: {e}")

    # Save multiple times to be sure
    print("\n💾 Saving...")
    for i in range(3):
        for selector in ["//button[contains(text(), 'Save Model')]"]:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if elements:
                    # Focus and click
                    driver.execute_script("arguments[0].focus();", elements[0])
                    time.sleep(0.5)
                    driver.execute_script("arguments[0].click();", elements[0])
                    print(f"   Save attempt {i+1}/3")
                    time.sleep(2)
                    break
            except:
                continue

    # Build
    print("\n🔨 Building...")
    for selector in ["//button[contains(text(), 'Build Model')]"]:
        try:
            elements = driver.find_elements(By.XPATH, selector)
            if elements:
                driver.execute_script("arguments[0].focus();", elements[0])
                time.sleep(0.5)
                driver.execute_script("arguments[0].click();", elements[0])
                print("✅ Build started")
                time.sleep(5)
                break
        except:
            continue

    # Screenshot
    screenshot = f"/Users/Subho/alexa_final_fix_{int(time.time())}.png"
    driver.save_screenshot(screenshot)
    print(f"\n📸 Screenshot: {screenshot}")

    print("\n✅ Fix applied!")
    print("⏳ Wait 30-60 seconds for build to complete")
    print("👀 Look for green checkmark ✅")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
