#!/usr/bin/env python3
"""
Final OpenDia WiFi Setup - Direct Browser Control
"""

import json
import requests
import time

def send_opendia_command(action, params=None):
    """Send command to OpenDia"""
    url = "http://localhost:5556/sse"
    command = {"action": action, "params": params or {}}

    try:
        response = requests.post(url, json=command, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {response.status_code}")
            return None
    except Exception as e:
        print(f"Connection error: {e}")
        return None

def main():
    print("🚀 OpenDia Security Camera WiFi Setup")
    print("=" * 50)

    # Step 1: Open System Preferences
    print("1️⃣ Opening System Preferences...")
    result = send_opendia_command("navigate", {
        "url": "x-apple.systempreferences:com.apple.preference.sharing"
    })

    if result:
        print("✅ System Preferences opened")
    else:
        print("❌ Failed to open System Preferences")
        return

    time.sleep(3)

    # Step 2: Look for any clickable elements related to Internet Sharing
    print("2️⃣ Looking for Internet Sharing controls...")

    # Try different selectors to find the right element
    selectors_to_try = [
        "text=Internet Sharing",
        "[aria-label*='Internet Sharing']",
        "[title*='Internet Sharing']",
        "a:contains('Internet Sharing')",
        "button:contains('Internet Sharing')",
        "input:contains('Internet Sharing')"
    ]

    for selector in selectors_to_try:
        print(f"   Trying selector: {selector}")
        result = send_opendia_command("find_element", {
            "selector": selector
        })

        if result and result.get("success"):
            print(f"✅ Found element with selector: {selector}")

            # Click the element
            click_result = send_opendia_command("click", {
                "element_id": result.get("element_id")
            })

            if click_result:
                print("✅ Clicked Internet Sharing")
                break
        else:
            print(f"   ❌ No match for selector: {selector}")

    time.sleep(2)

    # Step 3: Try to find and interact with form elements
    print("3️⃣ Looking for form controls...")

    # Look for select elements
    form_actions = [
        ("select_option", "select", "Wi-Fi"),
        ("click", "input[type='checkbox']", None),
        ("click", "button[aria-label*='Wi-Fi Options']", None),
    ]

    for action_type, selector, value in form_actions:
        print(f"   Trying to {action_type} on {selector}")

        if action_type == "select_option":
            result = send_opendia_command("select_option", {
                "selector": selector,
                "value": value
            })
        else:
            result = send_opendia_command("find_element", {
                "selector": selector
            })

            if result and result.get("success"):
                result = send_opendia_command("click", {
                    "element_id": result.get("element_id")
                })

        if result:
            print(f"   ✅ {action_type} successful")
        else:
            print(f"   ❌ {action_type} failed")

        time.sleep(1)

    print("🎯 OpenDia automation attempt completed!")
    print("Please check System Preferences to see if the setup worked.")

if __name__ == "__main__":
    main()