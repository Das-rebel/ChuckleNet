#!/usr/bin/env python3
"""
OpenDia WiFi Setup Script for Security Camera
Uses OpenDia to automate the 2.4GHz WiFi network configuration
"""

import json
import requests
import time
import subprocess

def send_to_opendia(action, params=None):
    """Send command to OpenDia via HTTP endpoint"""
    url = "http://localhost:5556/sse"

    command = {
        "action": action,
        "params": params or {}
    }

    try:
        response = requests.post(url, json=command, timeout=30)
        return response.json()
    except Exception as e:
        print(f"Error sending command to OpenDia: {e}")
        return None

def setup_wifi_with_opendia():
    """Setup WiFi using OpenDia browser automation"""

    print("🚀 Starting OpenDia WiFi Setup for Security Camera")
    print("=" * 50)

    # Step 1: Open System Preferences
    print("1️⃣ Opening System Preferences...")
    result = send_to_opendia("navigate", {"url": "x-apple.systempreferences:com.apple.preference.sharing"})
    if result:
        print("✅ System Preferences opened")
    else:
        print("❌ Failed to open System Preferences")
        return False

    time.sleep(2)

    # Step 2: Find and configure Internet Sharing
    print("2️⃣ Configuring Internet Sharing...")

    # Look for Internet Sharing in the sidebar
    result = send_to_opendia("find_element", {
        "selector": "text=Internet Sharing",
        "type": "link"
    })

    if result and "element_id" in result:
        print("✅ Found Internet Sharing option")

        # Click on Internet Sharing
        send_to_opendia("click", {"element_id": result["element_id"]})
        time.sleep(1)

        # Configure sharing options
        print("3️⃣ Setting up sharing options...")

        # Set "Share your connection from" to Wi-Fi
        send_to_opendia("select_option", {
            "selector": "select[aria-label*='Share your connection from']",
            "value": "Wi-Fi"
        })

        # Set "To computers using" to Wi-Fi
        send_to_opendia("click", {
            "selector": "input[type='checkbox'][value='Wi-Fi']"
        })

        # Click WiFi Options
        print("4️⃣ Opening WiFi Options...")
        send_to_opendia("click", {
            "selector": "button[aria-label*='Wi-Fi Options']"
        })

        time.sleep(2)

        # Fill in WiFi details
        print("5️⃣ Configuring WiFi network details...")

        # Network Name
        send_to_opendia("fill_input", {
            "selector": "input[placeholder*='Network Name' or placeholder*='Name']",
            "value": "Security_Camera_2.4G"
        })

        # Password
        send_to_opendia("fill_input", {
            "selector": "input[type='password']",
            "value": "Cam1234Secure!"
        })

        # Security
        send_to_opendia("select_option", {
            "selector": "select[aria-label*='Security']",
            "value": "WPA2 Personal"
        })

        # Channel
        send_to_opendia("select_option", {
            "selector": "select[aria-label*='Channel']",
            "value": "6"
        })

        # Band
        send_to_opendia("select_option", {
            "selector": "select[aria-label*='Band']",
            "value": "2.4 GHz"
        })

        # Save WiFi Options
        print("6️⃣ Saving WiFi configuration...")
        send_to_opendia("click", {
            "selector": "button[aria-label*='OK' or text='OK']"
        })

        time.sleep(1)

        # Enable Internet Sharing
        print("7️⃣ Enabling Internet Sharing...")
        send_to_opendia("click", {
            "selector": "input[type='checkbox'][aria-label*='Internet Sharing']"
        })

        # Confirm if prompted
        time.sleep(1)
        send_to_opendia("click", {
            "selector": "button[aria-label*='Start' or text='Start']"
        })

        print("✅ WiFi setup completed!")
        return True

    else:
        print("❌ Could not find Internet Sharing option")
        return False

def verify_setup():
    """Verify the WiFi network is active"""
    print("🔍 Verifying WiFi setup...")

    # Scan for networks
    result = subprocess.run([
        "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport",
        "-s"
    ], capture_output=True, text=True)

    if "Security_Camera_2.4G" in result.stdout:
        print("✅ Security_Camera_2.4G network is active!")
        return True
    else:
        print("⚠️  Network not found in scan (may take a moment to appear)")
        return False

if __name__ == "__main__":
    print("🎯 OpenDia Security Camera WiFi Setup")
    print("=" * 50)
    print("Make sure you have the OpenDia browser extension installed and running")
    print("Also ensure System Preferences is not already open")
    print()

    input("Press Enter to start the setup...")

    if setup_wifi_with_opendia():
        print("\n🎉 Setup completed successfully!")
        print("Network Name: Security_Camera_2.4G")
        print("Password: Cam1234Secure!")

        # Wait a moment and verify
        time.sleep(5)
        verify_setup()
    else:
        print("\n❌ Setup failed. Please check the OpenDia connection and try again.")