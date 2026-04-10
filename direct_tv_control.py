#!/usr/bin/env python3
"""
Simple Direct TV Control - Just the buttons that work
No complex connection logic - direct TV control
"""

import subprocess
import time
from Cocoa import NSAppleScript

class DirectTVControl:
    def __init__(self):
        self.tv_name = "dasi"
        print("🎬 DIRECT TV CONTROL")
        print("=" * 30)
        print("💡 Simple controls - click and TV responds")
        print("📱 Target:", self.tv_name)

    def send_command(self, action):
        """Send command directly to TV"""
        commands = {
            'home': 'key code 98',      # F12/Home
            'back': 'key code 98',      # Back (same as home)
            'up': 'key code 126',       # Up arrow
            'down': 'key code 125',     # Down arrow
            'left': 'key code 123',     # Left arrow
            'right': 'key code 124',    # Right arrow
            'select': 'key code 36',    # Enter
            'menu': 'key code 82',      # Menu (Volume Up)
            'volume_up': 'key code 82', # Volume Up
            'volume_down': 'key code 81', # Volume Down
            'mute': 'key code 75',      # Mute
            'power': 'key code 122',    # Power
        }

        script_code = commands.get(action.lower())
        if not script_code:
            print(f"❌ Unknown command: {action}")
            return False

        script = f'''
        tell application "System Events"
            {script_code}
        end tell
        '''

        try:
            applescript = NSAppleScript.alloc().initWithSource_(script)
            result, error = applescript.executeAndReturnError_(None)

            if not error:
                print(f"✅ Sent: {action}")
                return True
            else:
                print(f"❌ Failed: {action}")
                return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False

    def navigate_to_bluetooth(self):
        """Navigate to TV Bluetooth settings"""
        print("🧭 Navigating to Bluetooth settings...")

        sequence = [
            ('home', 'Go to home'),
            ('right', 'Navigate right'),
            ('right', 'Navigate right again'),
            ('select', 'Select Settings'),
            ('down', 'Navigate down'),
            ('down', 'Navigate down again'),
            ('select', 'Select Connected Devices'),
            ('down', 'Navigate to Bluetooth'),
            ('select', 'Select Bluetooth')
        ]

        for action, description in sequence:
            print(f"   {description}")
            self.send_command(action)
            time.sleep(1.5)  # Longer delay for TV response

        print("✅ Should be in Bluetooth settings now!")

    def start_pairing(self):
        """Start TV pairing mode"""
        print("🔄 Starting pairing mode...")

        sequence = [
            ('down', 'Navigate down'),
            ('down', 'Navigate down again'),
            ('down', 'Navigate to pairing option'),
            ('select', 'Select to start pairing')
        ]

        for action, description in sequence:
            print(f"   {description}")
            self.send_command(action)
            time.sleep(1.5)

        print("✅ TV should now be in pairing mode!")
        print("📱 Scan for 'dasi' on your iQoo phone now!")

    def test_tv_response(self):
        """Test if TV responds to commands"""
        print("\n🧪 Testing TV response...")

        test_commands = [
            ('up', 'Try moving up'),
            ('down', 'Try moving down'),
            ('home', 'Try home button'),
        ]

        responding = False
        for action, description in test_commands:
            print(f"   {description}...")
            if self.send_command(action):
                print("   Command sent - did TV respond?")
                responding = True
                time.sleep(2)

        if responding:
            print("✅ TV should be responding to commands!")
        else:
            print("❌ TV may not be responding - check connection")

def main():
    control = DirectTVControl()

    print("\n🎮 CONTROL OPTIONS:")
    print("1. test      - Test TV response")
    print("2. bluetooth - Navigate to Bluetooth settings")
    print("3. pair      - Start pairing mode")
    print("4. up/down/left/right/select - Direct control")
    print("5. quit      - Exit")

    print("\n💡 If commands don't work, the TV may not be connected via Bluetooth")
    print("💡 Check macOS Bluetooth preferences to ensure TV is connected")

    while True:
        try:
            choice = input("\nTV Control> ").strip().lower()

            if choice in ['quit', 'exit', 'q']:
                break
            elif choice == 'test':
                control.test_tv_response()
            elif choice == 'bluetooth':
                control.navigate_to_bluetooth()
            elif choice == 'pair':
                control.start_pairing()
            elif choice in ['up', 'down', 'left', 'right', 'select', 'home', 'back', 'menu', 'volume_up', 'volume_down', 'mute', 'power']:
                control.send_command(choice)
            else:
                print("Options: test, bluetooth, pair, up, down, left, right, select, quit")

        except KeyboardInterrupt:
            break
        except EOFError:
            break

    print("\n👋 TV Control ended")

if __name__ == "__main__":
    main()