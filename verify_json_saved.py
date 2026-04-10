#!/usr/bin/env python3
"""Check and fix JSON in editor"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import json

try:
    print("🔌 Connecting to Brave...")
    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    driver = webdriver.Chrome(options=chrome_options)

    # Click JSON Editor
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

    # Get content
    print("\n📄 Checking JSON content...")
    try:
        textarea = driver.find_element(By.TAG_NAME, "textarea")
        content = textarea.get_attribute('value')

        if not content or content.strip() == "":
            print("❌ JSON Editor is EMPTY! Fix didn't save!")
            print("🔧 Re-applying fix...")

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

            # Apply fix
            driver.execute_script("""
                arguments[0].value = '';
                arguments[0].innerHTML = '';
                arguments[0].value = arguments[1];
                arguments[0].innerHTML = arguments[1];
                arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
                arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
            """, textarea, correct_json)

            print("✅ JSON re-applied!")
            time.sleep(2)

            # Save
            print("\n💾 Saving...")
            for selector in ["//button[contains(text(), 'Save Model')]"]:
                try:
                    elements = driver.find_elements(By.XPATH, selector)
                    if elements:
                        driver.execute_script("arguments[0].click();", elements[0])
                        print("✅ Saved")
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
                        driver.execute_script("arguments[0].click();", elements[0])
                        print("✅ Building...")
                        time.sleep(5)
                        break
                except:
                    continue

        else:
            print(f"✅ JSON has content ({len(content)} chars)")

            # Try to parse
            try:
                data = json.loads(content)
                invocation = data.get('interactionModel', {}).get('languageModel', {}).get('invocationName', '')
                print(f"\n📌 Invocation: '{invocation}'")

                intents = data.get('interactionModel', {}).get('languageModel', {}).get('intents', [])
                chat_intent = next((i for i in intents if i.get('name') == 'ChatIntent'), None)

                if chat_intent:
                    samples = chat_intent.get('samples', [])
                    print(f"📋 ChatIntent samples: {samples}")

                    has_carrier = any('ask' in s.lower() or 'tell' in s.lower() or 'what' in s.lower()
                                    for s in samples)
                    if has_carrier:
                        print("✅ Has carrier phrases - JSON is correct!")
                    else:
                        print("❌ Missing carrier phrases!")

            except json.JSONDecodeError as e:
                print(f"❌ JSON Parse Error: {e}")
                print("JSON content:")
                print(content[:500])

    except Exception as e:
        print(f"❌ Error: {e}")

    # Screenshot
    screenshot = f"/Users/Subho/alexa_json_check_{int(time.time())}.png"
    driver.save_screenshot(screenshot)
    print(f"\n📸 Screenshot: {screenshot}")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
