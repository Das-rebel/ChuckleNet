#!/usr/bin/env python3
"""
Simple TV Remote for Mac using AppleScript
Controls Android TV by sending keyboard commands via Bluetooth
"""

import sys
import subprocess
import time
from Cocoa import NSAppleScript

class SimpleTVRemote:
    def __init__(self):
        self.tv_name = "dasi"
        print("🎬 Simple TV Remote Controller")
        print("================================")

    def send_key_to_tv(self, key_name: str):
        """Send key command to TV via AppleScript"""
        script = f'''
        tell application "System Events"
            {key_name}
        end tell
        '''

        try:
            applescript = NSAppleScript.alloc().initWithSource_(script)
            result, error = applescript.executeAndReturnError_(None)

            if error:
                print(f"❌ Error sending command: {error}")
                return False
            else:
                print(f"✅ Sent: {key_name}")
                return True
        except Exception as e:
            print(f"❌ Command failed: {e}")
            return False

    def send_multiple_keys(self, commands: list):
        """Send sequence of commands with delays"""
        print(f"🎯 Sending sequence: {commands}")
        for cmd in commands:
            self.send_key_to_tv(cmd)
            time.sleep(0.5)  # Wait for TV to respond

    def connect_to_tv(self):
        """Connect to TV using Bluetooth preferences"""
        print(f"🔗 Connecting to {self.tv_name}...")

        script = f'''
        tell application "System Events"
            activate
        end tell

        tell application "System Preferences"
            activate
            set current pane to pane "com.apple.preference.bluetooth"
            delay 2
        end tell

        tell application "System Events"
            tell process "System Preferences"
                tell window "Bluetooth"
                    try
                        tell outline 1
                            select row "{self.tv_name}"
                        end tell
                        delay 1
                        click button "Connect"
                        delay 2
                    on error errMsg
                        log "Could not connect: " & errMsg
                    end try
                end tell
            end tell
        end tell
        '''

        applescript = NSAppleScript.alloc().initWithSource_(script)
        result, error = applescript.executeAndReturnError_(None)

        if error:
            print(f"❌ Connection attempt failed: {error}")
            print("💡 Try connecting manually in Bluetooth preferences first")
            return False
        else:
            print("✅ Connection attempt initiated")
            return True

    def navigate_to_bluetooth_settings(self):
        """Navigate TV to Bluetooth settings using key sequence"""
        print("🧭 Navigating to TV Bluetooth settings...")

        # Typical Android TV navigation sequence
        navigation_commands = [
            'key code 98 using command down, command up',  # Home
            'key code 124 using command down, command up',  # Right
            'key code 36 using command down, command up',   # Enter (select Settings)
            'key code 125 using command down, command up',  # Down
            'key code 125 using command down, command up',  # Down (to Connected Devices)
            'key code 36 using command down, command up',   # Enter
        ]

        for cmd in navigation_commands:
            self.send_key_to_tv(cmd)
            time.sleep(0.8)  # Longer delay for TV processing

        print("✅ Should now be in Bluetooth/Connected Devices settings")

    def start_pairing_mode(self):
        """Start TV pairing mode for phone"""
        print("🔄 Starting TV pairing mode...")

        pairing_commands = [
            'key code 125 using command down, command up',  # Down
            'key code 125 using command down, command up',  # Down (to "Add new device")
            'key code 36 using command down, command up',   # Enter
        ]

        for cmd in pairing_commands:
            self.send_key_to_tv(cmd)
            time.sleep(0.8)

        print("✅ TV should now be in pairing mode")
        print("📱 Now scan for devices on your iQoo phone!")

    def manual_remote_mode(self):
        """Interactive remote control mode"""
        print("\n🎮 Manual Remote Mode")
        print("======================")
        print("Press these keys to control TV:")
        print("  h = Home")
        print("  b = Back")
        print("  ↑/↓/←/→ = Arrow keys")
        print("  Enter = Select")
        print("  m = Menu")
        print("  + = Volume Up")
        print("  - = Volume Down")
        print("  c = Connect to TV")
        print("  t = Go to Bluetooth settings")
        print("  p = Start pairing mode")
        print("  q = Quit")
        print("\n💡 Make sure TV window is active for commands to work!")

        while True:
            try:
                # Get single character input
                import tty
                import termios
                fd = sys.stdin.fileno()
                old_settings = termios.tcgetattr(fd)
                try:
                    tty.setraw(sys.stdin.fileno())
                    char = sys.stdin.read(1)
                finally:
                    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

                if char == 'q':
                    break
                elif char == 'h':
                    self.send_key_to_tv('key code 98 using command down, command up')  # Home
                elif char == 'b':
                    self.send_key_to_tv('key code 98 using command down, command up')  # Back
                elif char == '\x1b':  # Escape sequence for arrow keys
                    char2 = sys.stdin.read(2)
                    if char2 == '[A':
                        self.send_key_to_tv('key code 126 using command down, command up')  # Up
                    elif char2 == '[B':
                        self.send_key_to_tv('key code 125 using command down, command up')  # Down
                    elif char2 == '[C':
                        self.send_key_to_tv('key code 124 using command down, command up')  # Right
                    elif char2 == '[D':
                        self.send_key_to_tv('key code 123 using command down, command up')  # Left
                elif char == '\r':  # Enter key
                    self.send_key_to_tv('key code 36 using command down, command up')  # Select
                elif char == 'm':
                    self.send_key_to_tv('key code 82 using command down, command up')  # Menu
                elif char == '+':
                    self.send_key_to_tv('key code 82 using command down, command up')  # Volume Up
                elif char == '-':
                    self.send_key_to_tv('key code 81 using command down, command up')  # Volume Down
                elif char == 'c':
                    self.connect_to_tv()
                elif char == 't':
                    self.navigate_to_bluetooth_settings()
                elif char == 'p':
                    self.start_pairing_mode()

            except KeyboardInterrupt:
                break

        print("\n👋 Remote mode ended")

def main():
    remote = SimpleTVRemote()

    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == "connect":
            remote.connect_to_tv()
        elif command == "bluetooth":
            remote.navigate_to_bluetooth_settings()
        elif command == "pair":
            remote.start_pairing_mode()
        elif command == "manual":
            remote.manual_remote_mode()
        else:
            print("Usage:")
            print("  python3 tv_remote_simple.py connect     - Connect to TV")
            print("  python3 tv_remote_simple.py bluetooth  - Navigate to Bluetooth settings")
            print("  python3 tv_remote_simple.py pair       - Start pairing mode")
            print("  python3 tv_remote_simple.py manual     - Interactive remote mode")
    else:
        print("Quick Start:")
        print("1. python3 tv_remote_simple.py connect")
        print("2. python3 tv_remote_simple.py bluetooth")
        print("3. python3 tv_remote_simple.py pair")
        print("4. Then scan on your phone!")
        print("\nOr use: python3 tv_remote_simple.py manual for interactive control")

if __name__ == "__main__":
    main()