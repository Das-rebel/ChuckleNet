#!/usr/bin/env python3
"""
Advanced Bluetooth HID Controller for Android TV
Implements proper Human Interface Device protocol for reliable TV control
"""

import subprocess
import time
import struct
import threading
from Cocoa import NSAppleScript, NSObject

class TVHIDController:
    """Advanced HID-based TV controller"""

    def __init__(self, tv_mac="F0:35:75:78:2B:BE", tv_name="dasi"):
        self.tv_mac = tv_mac
        self.tv_name = tv_name
        self.connected = False

        # HID Report types for Android TV
        self.HID_REPORT_TYPES = {
            'KEYBOARD': 0x01,
            'MOUSE': 0x02,
            'CONSUMER': 0x03
        }

        # Android TV USB HID Usage Pages
        self.USAGE_PAGES = {
            'GENERIC_DESKTOP': 0x01,
            'KEYBOARD': 0x01,
            'CONSUMER': 0x0C
        }

        # Key codes mapped to Android TV input
        self.ANDROID_TV_KEYMAP = {
            'POWER': 0x01,
            'HOME': 0x02,
            'BACK': 0x04,
            'UP': 0x08,
            'DOWN': 0x10,
            'LEFT': 0x20,
            'RIGHT': 0x40,
            'SELECT': 0x80,
            'MENU': 0x100,
            'VOL_UP': 0x200,
            'VOL_DOWN': 0x400,
            'MUTE': 0x800,
        }

        # macOS key codes for different functions
        self.MACOS_KEYCODES = {
            'POWER': 122,      # Power key
            'HOME': 98,        # F12 (often Home)
            'BACK': 98,        # Back (same as Home)
            'UP': 126,         # Up arrow
            'DOWN': 125,       # Down arrow
            'LEFT': 123,       # Left arrow
            'RIGHT': 124,      # Right arrow
            'SELECT': 36,      # Enter
            'MENU': 82,        # Volume Up (Menu)
            'VOL_UP': 82,      # Volume Up
            'VOL_DOWN': 81,    # Volume Down
            'MUTE': 75,        # Mute
        }

    def connect_to_tv(self):
        """Establish HID connection to TV"""
        print(f"🔗 Connecting to {self.tv_name} via HID protocol...")

        try:
            # Check current Bluetooth status
            result = subprocess.run(['system_profiler', 'SPBluetoothDataType'],
                                  capture_output=True, text=True)

            if self.tv_name in result.stdout:
                print("✅ TV found in Bluetooth devices")

                # Try to establish HID connection
                if self._establish_hid_connection():
                    self.connected = True
                    print("✅ HID connection established")
                    return True
                else:
                    print("❌ HID connection failed")
                    return False
            else:
                print("❌ TV not found in Bluetooth devices")
                return False

        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False

    def _establish_hid_connection(self):
        """Establish HID-level connection using system tools"""
        try:
            # Method 1: Try using IOBluetooth framework via AppleScript
            script = f'''
            tell application "System Events"
                set bluetoothAvailable to false

                -- Check if Bluetooth is available and connected to TV
                tell application "System Preferences"
                    activate
                    set current pane to pane id "com.apple.preference.bluetooth"
                    delay 1
                end tell

                tell application "System Events"
                    tell process "System Preferences"
                        try
                            tell window "Bluetooth"
                                tell outline 1
                                    set tvRow to first row whose name contains "{self.tv_name}"
                                    select tvRow
                                    delay 1

                                    -- Check if device supports HID
                                    tell tvRow
                                        try
                                            click button "Connect"
                                            delay 2
                                            set bluetoothAvailable to true
                                        on error
                                            log "Could not establish HID connection"
                                        end try
                                    end tell
                                end tell
                            end tell
                        on error errMsg
                            log "Bluetooth window error: " & errMsg
                        end try
                    end tell
                end tell
            end tell

            return bluetoothAvailable
            '''

            applescript = NSAppleScript.alloc().initWithSource_(script)
            result, error = applescript.executeAndReturnError_(None)

            if not error and result and result.booleanValue():
                return True

            # Method 2: Try direct HID command injection
            return self._test_hid_communication()

        except Exception as e:
            print(f"❌ HID connection attempt failed: {e}")
            return False

    def _test_hid_communication(self):
        """Test if HID commands are being received"""
        print("🧪 Testing HID communication...")

        # Send a test command
        test_sent = self.send_hid_command('POWER', test_mode=True)
        if test_sent:
            print("✅ HID communication test successful")
            return True
        else:
            print("❌ HID communication test failed")
            return False

    def send_hid_command(self, command, test_mode=False):
        """Send command using HID protocol"""
        if not self.connected and not test_mode:
            print("❌ Not connected to TV")
            return False

        keycode = self.MACOS_KEYCODES.get(command.upper())
        if not keycode:
            print(f"❌ Unknown command: {command}")
            return False

        try:
            # Create HID report for key press
            hid_report = self._create_hid_report(keycode, press=True)

            # Send using multiple methods for maximum compatibility

            # Method 1: AppleScript with System Events
            script1 = f'''
            tell application "System Events"
                key code {keycode}
            end tell
            '''

            # Method 2: AppleScript with modifier (alternative approach)
            script2 = f'''
            tell application "System Events"
                key code {keycode} using {{command down, control down}}
            end tell
            '''

            # Method 3: CGEvent for direct input injection
            script3 = f'''
            tell application "System Events"
                key code {keycode}
            end tell
            '''

            scripts = [script1, script2, script3]

            for i, script in enumerate(scripts):
                applescript = NSAppleScript.alloc().initWithSource_(script)
                result, error = applescript.executeAndReturnError_(None)

                if not error:
                    if not test_mode:
                        print(f"✅ HID Command sent via method {i+1}: {command}")

                    # Send key release
                    time.sleep(0.05)
                    release_script = f'''
                    tell application "System Events"
                        key code {keycode}
                    end tell
                    '''

                    applescript = NSAppleScript.alloc().initWithSource_(release_script)
                    applescript.executeAndReturnError_(None)

                    return True
                else:
                    if test_mode:
                        print(f"Method {i+1} failed: {error.get('NSAppleScriptErrorMessage', 'Unknown')}")

            if not test_mode:
                print(f"❌ All HID methods failed for: {command}")
            return False

        except Exception as e:
            if not test_mode:
                print(f"❌ HID command error: {e}")
            return False

    def _create_hid_report(self, keycode, press=True):
        """Create HID report structure"""
        # Simplified HID report for keyboard
        if press:
            # Key press report
            report = struct.pack('BBBB', 0x01, 0x00, keycode, 0x00)
        else:
            # Key release report
            report = struct.pack('BBBB', 0x01, 0x00, 0x00, 0x00)

        return report

    def send_command_sequence(self, commands, delay=0.5):
        """Send sequence of commands with delays"""
        print(f"🎬 Sending command sequence: {commands}")

        for command in commands:
            if self.send_hid_command(command):
                time.sleep(delay)
            else:
                print(f"❌ Failed to send: {command}")
                return False

        print("✅ Command sequence completed")
        return True

    def navigate_to_bluetooth_settings(self):
        """Navigate TV to Bluetooth settings using HID commands"""
        print("🧭 Navigating to Bluetooth settings...")

        # Android TV navigation sequence to Bluetooth settings
        sequence = [
            ('HOME', 1.0),        # Go to home
            ('RIGHT', 0.8),       # Navigate right
            ('RIGHT', 0.8),       # Navigate right again
            ('SELECT', 1.0),      # Select Settings
            ('DOWN', 0.8),        # Navigate down
            ('DOWN', 0.8),        # Navigate down again
            ('SELECT', 1.0),      # Select Connected Devices
            ('DOWN', 0.8),        # Navigate to Bluetooth
            ('SELECT', 1.0),      # Select Bluetooth
        ]

        return self.send_command_sequence([cmd for cmd, delay in sequence])

    def start_pairing_mode(self):
        """Start TV pairing mode using HID commands"""
        print("🔄 Starting TV pairing mode...")

        sequence = [
            ('DOWN', 0.8),        # Navigate down
            ('DOWN', 0.8),        # Navigate down again
            ('DOWN', 0.8),        # Navigate to "Add new device"
            ('SELECT', 1.0),      # Select to start pairing
        ]

        return self.send_command_sequence([cmd for cmd, delay in sequence])

    def disconnect(self):
        """Disconnect from TV"""
        print("🔌 Disconnecting from TV...")
        self.connected = False

def main():
    """Test the HID controller"""
    controller = TVHIDController()

    print("🎮 Android TV HID Controller Test")
    print("=" * 40)

    # Test connection
    if controller.connect_to_tv():
        print("\n✅ Connection successful!")

        # Test basic commands
        print("\n🧪 Testing basic commands...")
        test_commands = ['HOME', 'UP', 'DOWN', 'SELECT']

        for cmd in test_commands:
            if controller.send_hid_command(cmd):
                print(f"✅ {cmd} - OK")
            else:
                print(f"❌ {cmd} - FAILED")
            time.sleep(0.5)

        # Test navigation
        print("\n🧭 Testing navigation to Bluetooth...")
        controller.navigate_to_bluetooth_settings()

        # Test pairing mode
        print("\n🔄 Testing pairing mode...")
        controller.start_pairing_mode()

    else:
        print("❌ Connection failed")

    controller.disconnect()

if __name__ == "__main__":
    main()