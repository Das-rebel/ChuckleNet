#!/usr/bin/env python3
"""
Force HID Profile Connection with TV
Try to establish proper Human Interface Device connection
"""

import subprocess
import time
from Cocoa import NSAppleScript

class HIDConnectionForcer:
    def __init__(self):
        self.tv_mac = "F0:35:75:78:2B:BE"
        self.tv_name = "dasi"
        print("🔧 FORCING HID CONNECTION TO TV")
        print("=" * 40)
        print(f"📱 Target: {self.tv_name}")
        print(f"📡 MAC: {self.tv_mac}")
        print()

    def open_bluetooth_preferences(self):
        """Open Bluetooth preferences for manual setup"""
        print("🔧 METHOD 1: Manual HID Profile Setup")
        print("-" * 35)

        print("Opening Bluetooth preferences...")
        subprocess.run(['open', 'x-apple.systempreferences:com.apple.BluetoothSettings'],
                      capture_output=True)

        instructions = """
        📱 MANUAL STEPS TO ENABLE HID CONTROL:

        1. In Bluetooth Preferences, find "dasi"
        2. Click "Options" or "Configure" next to dasi
        3. Look for "Use as keyboard/mouse" or "HID device"
        4. Enable "Human Interface Device" profile
        5. Click "Apply" or "Done"

        🔍 What to look for:
        - "Service Type" or "Device Type" options
        - "Keyboard", "Mouse", or "HID" checkboxes
        - "Remote Control" or "Input Device" options
        - "Allow Control" or "Input Device Access"

        ✅ If you see these options:
        - Enable Keyboard/Mouse/HID options
        - Click "Connect" if prompted
        - TV might show confirmation code

        ❌ If no HID options:
        - TV may not support HID control via Mac
        - Try alternative methods below
        """

        print(instructions)

    def disconnect_and_reconnect(self):
        """Try disconnecting and reconnecting with different profile"""
        print("\n🔄 METHOD 2: Disconnect and Reconnect")
        print("-" * 35)

        try:
            print("Step 1: Disconnect from TV...")
            script = f'''
            tell application "System Events"
                tell application "System Preferences"
                    activate
                    set current pane to pane id "com.apple.preference.bluetooth"
                    delay 1
                end tell

                tell application "System Events"
                    tell process "System Preferences"
                        tell window "Bluetooth"
                            try
                                tell outline 1
                                    select first row whose name contains "{self.tv_name}"
                                end tell
                                delay 1
                                click button "Disconnect" or button "Remove"
                                delay 2
                            on error
                                log "Could not disconnect automatically"
                            end try
                        end tell
                    end tell
                end tell
            end tell
            '''

            applescript = NSAppleScript.alloc().initWithSource_(script)
            result, error = applescript.executeAndReturnError_(None)
            print("   Disconnect command sent")

            time.sleep(3)

            print("Step 2: Wait 5 seconds...")
            time.sleep(5)

            print("Step 3: Reconnect with HID focus...")
            script2 = f'''
            tell application "System Events"
                tell application "System Preferences"
                    activate
                    set current pane to pane id "com.apple.preference.bluetooth"
                    delay 1
                end tell

                tell application "System Events"
                    tell process "System Preferences"
                        tell window "Bluetooth"
                            try
                                tell outline 1
                                    select first row whose name contains "{self.tv_name}"
                                end tell
                                delay 1
                                -- Try to access options or connect button
                                try
                                    click button "Options" or button "Configure"
                                    delay 1
                                    -- Look for HID/Keyboard options
                                end try
                                click button "Connect"
                                delay 2
                            on error errMsg
                                log "Could not connect: " & errMsg
                            end try
                        end tell
                    end tell
                end tell
            end tell
            '''

            applescript = NSAppleScript.alloc().initWithSource_(script2)
            result, error = applescript.executeAndReturnError_(None)
            print("   Reconnect command sent")

            time.sleep(3)
            print("✅ Attempt completed - check TV response")

        except Exception as e:
            print(f"❌ Error: {e}")

    def try_alternative_connection(self):
        """Try alternative connection methods"""
        print("\n🔧 METHOD 3: Alternative Connection Attempts")
        print("-" * 40)

        attempts = [
            ("AppleScript Control", '''
            tell application "System Events"
                key code 125  -- Down arrow
            end tell
            '''),
            ("Mouse Click Simulation", '''
            tell application "System Events"
                click at {{100, 100}}
            end tell
            '''),
            ("Multiple Key Press", '''
            tell application "System Events"
                key code 125 using {{shift down}}
                key code 124 using {{control down}}
            end tell
            '''),
        ]

        for name, script in attempts:
            print(f"   Trying {name}...")
            try:
                applescript = NSAppleScript.alloc().initWithSource_(script)
                result, error = applescript.executeAndReturnError_(None)

                if not error:
                    print(f"   ✅ {name} sent")
                else:
                    print(f"   ❌ {name} failed")
            except:
                print(f"   ❌ {name} error")

    def check_current_status(self):
        """Check current connection status"""
        print("\n📊 CURRENT CONNECTION STATUS")
        print("-" * 30)

        try:
            result = subprocess.run(['system_profiler', 'SPBluetoothDataType'],
                                  capture_output=True, text=True)

            if self.tv_name in result.stdout:
                print(f"✅ {self.tv_name} found in Bluetooth devices")

                # Extract services info
                tv_section = result.stdout.split(self.tv_name)[1].split("iQOO")[0]
                print(f"📋 Device info: {tv_section.strip()}")

                if "GATT ACL" in tv_section:
                    print("   📡 Connected via GATT ACL (basic connection)")
                    print("   ❌ HID/Keyboard/Mouse profile NOT connected")
                    print("   ❌ Audio/AVRCP profile NOT connected")

                return True
            else:
                print(f"❌ {self.tv_name} NOT found")
                return False

        except Exception as e:
            print(f"❌ Error checking status: {e}")
            return False

    def show_alternatives(self):
        """Show alternative solutions"""
        print("\n💡 ALTERNATIVE SOLUTIONS")
        print("-" * 25)

        alternatives = """
        📱 PHONE-BASED SOLUTIONS (RECOMMENDED):
        =====================================
        1. Google Home App:
           - Install on iQoo phone
           - Auto-discovers TV via WiFi
           - Full remote control via WiFi
           - No Bluetooth needed

        2. YouTube Casting:
           - Open YouTube on phone
           - Tap Cast icon
           - Select your TV
           - Immediate control

        3. Android TV Remote Service:
           - Official Google app
           - Works via WiFi

        🔌 HARDWARE SOLUTIONS:
        =================
        1. USB Mouse:
           - Plug any USB mouse into TV
           - Works immediately for TV navigation
           - Navigate to Bluetooth settings
           - Pair your iQoo phone

        2. Universal Remote:
           - Buy cheap universal remote
           - Program for Android TV
           - Immediate solution

        📡 NETWORK SOLUTIONS:
        =================
        1. Connect TV to Ethernet
        2. Use WiFi-based remote apps
        3. No Bluetooth dependency
        """

        print(alternatives)

    def main(self):
        """Run all HID connection attempts"""
        print("🚀 Starting HID connection attempts...\n")

        # Check current status
        self.check_current_status()

        # Try different methods
        self.disconnect_and_reconnect()
        self.try_alternative_connection()

        # Open Bluetooth preferences for manual setup
        self.open_bluetooth_preferences()

        # Show alternatives
        self.show_alternatives()

        print("\n" + "=" * 50)
        print("🎯 RECOMMENDED ACTION:")
        print("=" * 50)
        print()
        print("1️⃣ Check Bluetooth Preferences window (should be open)")
        print("2️⃣ Look for 'Options' or 'Configure' next to 'dasi'")
        print("3️⃣ Enable Keyboard/Mouse/HID options if available")
        print("4️⃣ If no HID options: Use phone solutions (Google Home app)")
        print()
        print("💡 Your TV shows as 'connected' but only basic GATT profile")
        print("💡 For full control, need HID profile or use WiFi solutions")

if __name__ == "__main__":
    forcer = HIDConnectionForcer()
    forcer.main()