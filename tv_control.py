#!/usr/bin/env python3
"""
Simple TV Control Script for Mac
Uses AppleScript to send commands to connected TV via Bluetooth
"""

import sys
import time
from Cocoa import NSAppleScript

class TVController:
    def __init__(self):
        print("🎬 TV Controller - Connected to dasi TV")
        print("========================================")

    def send_command(self, command_name, key_code):
        """Send command to TV"""
        script = f'''
        tell application "System Events"
            key code {key_code}
        end tell
        '''

        try:
            applescript = NSAppleScript.alloc().initWithSource_(script)
            result, error = applescript.executeAndReturnError_(None)

            if error:
                print(f"❌ Error: {error.get('NSAppleScriptErrorMessage', 'Unknown error')}")
                return False
            else:
                print(f"✅ Sent: {command_name}")
                return True
        except Exception as e:
            print(f"❌ Command failed: {e}")
            return False

    def navigate_to_bluetooth_settings(self):
        """Navigate to TV Bluetooth settings"""
        print("🧭 Navigating to TV Bluetooth Settings...")

        commands = [
            ("Home", 98),
            ("Right", 124),
            ("Right", 124),
            ("Enter", 36),  # Select Settings
            ("Down", 125),
            ("Down", 125),
            ("Enter", 36),  # Enter Connected Devices
            ("Down", 125),
            ("Enter", 36),  # Enter Bluetooth
        ]

        for name, code in commands:
            time.sleep(1)
            if not self.send_command(name, code):
                print(f"❌ Failed to send {name}")
                return False

        print("✅ Should be in Bluetooth Settings now!")
        return True

    def start_pairing_mode(self):
        """Start TV pairing mode"""
        print("🔄 Starting TV Pairing Mode...")

        commands = [
            ("Down", 125),
            ("Down", 125),
            ("Down", 125),
            ("Enter", 36),  # Select "Add new device" or "Pair new device"
        ]

        for name, code in commands:
            time.sleep(1)
            self.send_command(name, code)

        print("✅ TV should now be in pairing mode!")
        print("📱 Now scan for 'dasi' on your iQoo phone!")

    def send_home(self):
        """Send Home command"""
        self.send_command("Home", 98)

    def send_back(self):
        """Send Back command"""
        self.send_command("Back", 98)

    def send_volume_up(self):
        """Send Volume Up"""
        self.send_command("Volume Up", 82)

    def send_volume_down(self):
        """Send Volume Down"""
        self.send_command("Volume Down", 81)

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 tv_control.py home          - Send Home button")
        print("  python3 tv_control.py back          - Send Back button")
        print("  python3 tv_control.py volume_up     - Volume up")
        print("  python3 tv_control.py volume_down   - Volume down")
        print("  python3 tv_control.py bluetooth     - Navigate to Bluetooth settings")
        print("  python3 tv_control.py pair          - Start pairing mode")
        print("  python3 tv_control.py sequence      - Run full pairing sequence")
        return

    controller = TVController()
    command = sys.argv[1].lower()

    if command == "home":
        controller.send_home()
    elif command == "back":
        controller.send_back()
    elif command == "volume_up":
        controller.send_volume_up()
    elif command == "volume_down":
        controller.send_volume_down()
    elif command == "bluetooth":
        controller.navigate_to_bluetooth_settings()
    elif command == "pair":
        controller.start_pairing_mode()
    elif command == "sequence":
        print("🚀 Running full TV pairing sequence...")
        controller.navigate_to_bluetooth_settings()
        time.sleep(2)
        controller.start_pairing_mode()
    else:
        print(f"❌ Unknown command: {command}")

if __name__ == "__main__":
    main()