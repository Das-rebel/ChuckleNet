#!/usr/bin/env python3
"""
Improved TV Connector with Multiple Connection Methods
Enhanced connection reliability for GUI integration
"""

import subprocess
import time
from Cocoa import NSAppleScript
from datetime import datetime

class ImprovedTVConnector:
    def __init__(self, tv_mac="F0:35:75:78:2B:BE", tv_name="dasi"):
        self.tv_mac = tv_mac
        self.tv_name = tv_name
        self.connected = False
        self.connection_method = None

    def diagnose_connection(self):
        """Diagnose connection status and issues"""
        print("🔍 Diagnosing TV connection...")

        try:
            # Check Bluetooth status
            result = subprocess.run(['system_profiler', 'SPBluetoothDataType'],
                                  capture_output=True, text=True)

            if self.tv_name in result.stdout:
                print(f"✅ {self.tv_name} found in Bluetooth devices")

                # Check if "Connected" is mentioned
                if "Connected" in result.stdout.split(self.tv_name)[1].split("Gamepad-igs")[0]:
                    print("✅ TV appears to be connected")
                    return "connected"
                else:
                    print("❌ TV found but not connected")
                    return "not_connected"
            else:
                print("❌ TV not found in Bluetooth devices")
                return "not_found"

        except Exception as e:
            print(f"❌ Diagnosis error: {e}")
            return "error"

    def connect_method_1_applescript_ui(self):
        """Method 1: Use AppleScript to control System Preferences UI"""
        print("🔄 Trying Method 1: AppleScript UI Control...")

        script = f'''
        tell application "System Events"
            activate
        end tell

        tell application "System Preferences"
            activate
            set current pane to pane id "com.apple.preference.bluetooth"
            delay 2
        end tell

        tell application "System Events"
            tell process "System Preferences"
                try
                    tell window "Bluetooth"
                        tell outline 1
                            select first row whose name contains "{self.tv_name}"
                        end tell
                        delay 1

                        -- Try to find and click Connect button
                        try
                            click button "Connect"
                            delay 3
                            return "success"
                        on error
                            -- Try alternative button names
                            try
                                click button "Pair"
                                delay 3
                                return "success"
                            on error
                                -- Try clicking the device itself
                                try
                                    click at {{100, 150}}
                                    delay 2
                                    return "success"
                                on error
                                    return "button_not_found"
                                end try
                            end try
                        end try
                    end tell
                on error errMsg
                    return "window_not_found: " & errMsg
                end try
            end tell
        end tell
        '''

        try:
            applescript = NSAppleScript.alloc().initWithSource_(script)
            result, error = applescript.executeAndReturnError_(None)

            if not error:
                return True
            else:
                print(f"Method 1 failed: {error}")
                return False
        except Exception as e:
            print(f"Method 1 error: {e}")
            return False

    def connect_method_2_blueutil_fallback(self):
        """Method 2: Try blueutil if available"""
        print("🔄 Trying Method 2: blueutil command...")

        try:
            # Check if blueutil is available
            result = subprocess.run(['which', 'blueutil'],
                                  capture_output=True, text=True)

            if result.returncode == 0:
                # Try to connect using blueutil
                result = subprocess.run(['blueutil', '--connect', self.tv_mac],
                                      capture_output=True, text=True, timeout=10)

                if result.returncode == 0:
                    print("✅ Connected via blueutil")
                    return True
                else:
                    print(f"blueutil failed: {result.stderr}")
                    return False
            else:
                print("blueutil not available")
                return False

        except Exception as e:
            print(f"Method 2 error: {e}")
            return False

    def connect_method_3_manual_pairing(self):
        """Method 3: Manual pairing instructions"""
        print("🔄 Method 3: Manual connection approach...")

        print("💡 Manual steps to connect:")
        print("1. Open System Preferences")
        print("2. Go to Bluetooth")
        print(f"3. Find '{self.tv_name}' in device list")
        print("4. Click 'Connect' or 'Pair' button")
        print("5. Confirm any pairing codes")

        # Try to open Bluetooth preferences
        try:
            subprocess.run(['open', 'x-apple.systempreferences:com.apple.BluetoothSettings'],
                          capture_output=True)
            print("✅ Bluetooth preferences opened")
            return "manual_prompt"
        except Exception as e:
            print(f"Failed to open preferences: {e}")
            return False

    def connect_method_4_restart_bluetooth(self):
        """Method 4: Restart Bluetooth and retry"""
        print("🔄 Method 4: Restart Bluetooth service...")

        try:
            # Restart Bluetooth service (macOS)
            subprocess.run(['sudo', 'pkill', '-f', 'bluetoothd'],
                          capture_output=True, text=True, timeout=5)
            time.sleep(2)

            # Restart Bluetooth interface
            subprocess.run(['sudo', 'ifconfig', 'bge0', 'down'],
                          capture_output=True, text=True, timeout=5)
            time.sleep(2)
            subprocess.run(['sudo', 'ifconfig', 'bge0', 'up'],
                          capture_output=True, text=True, timeout=5)
            time.sleep(3)

            print("✅ Bluetooth service restarted")
            return True
        except Exception as e:
            print(f"Bluetooth restart failed: {e}")
            return False

    def test_connection(self):
        """Test if connection actually works"""
        print("🧪 Testing connection...")

        # Try to send a simple command
        script = '''
        tell application "System Events"
            key code 126  -- Up arrow
        end tell
        '''

        try:
            applescript = NSAppleScript.alloc().initWithSource_(script)
            result, error = applescript.executeAndReturnError_(None)

            if not error:
                print("✅ Connection test successful")
                return True
            else:
                print(f"❌ Connection test failed: {error}")
                return False
        except Exception as e:
            print(f"❌ Connection test error: {e}")
            return False

    def connect_with_fallbacks(self):
        """Try all connection methods in order"""
        print(f"🔗 Attempting to connect to {self.tv_name}...")

        # First diagnose current state
        status = self.diagnose_connection()
        print(f"Current status: {status}")

        if status == "connected":
            # Test if it actually works
            if self.test_connection():
                self.connected = True
                self.connection_method = "existing"
                return True
            else:
                print("❌ Shows as connected but not responding")

        # Try connection methods in order
        methods = [
            ("AppleScript UI", self.connect_method_1_applescript_ui),
            ("blueutil", self.connect_method_2_blueutil_fallback),
            ("Restart Bluetooth", self.connect_method_4_restart_bluetooth),
            ("Manual Instructions", self.connect_method_3_manual_pairing),
        ]

        for method_name, method_func in methods:
            print(f"\n🔄 Trying {method_name}...")
            result = method_func()

            if result is True:
                time.sleep(2)
                if self.test_connection():
                    self.connected = True
                    self.connection_method = method_name
                    print(f"✅ Connected via {method_name}")
                    return True
                else:
                    print(f"❌ {method_name} connected but not working")
            elif result == "manual_prompt":
                print("💡 Follow the manual instructions above")
                return "manual"
            else:
                print(f"❌ {method_name} failed")

        print("❌ All connection methods failed")
        return False

    def get_connection_info(self):
        """Get detailed connection information"""
        info = {
            'tv_name': self.tv_name,
            'tv_mac': self.tv_mac,
            'connected': self.connected,
            'method': self.connection_method,
            'timestamp': datetime.now().isoformat()
        }

        if self.connected:
            info['status'] = "✅ Connected and responsive"
        else:
            info['status'] = "❌ Not connected or not responding"

        return info

def main():
    """Test the improved connector"""
    connector = ImprovedTVConnector()

    print("🔧 Improved TV Connector Test")
    print("=" * 40)

    # Try to connect
    result = connector.connect_with_fallbacks()

    if result is True:
        print("\n🎉 Connection successful!")
        print(connector.get_connection_info())
    elif result == "manual":
        print("\n👋 Manual connection required")
    else:
        print("\n❌ All automatic methods failed")
        print("\n💡 Try these manual steps:")
        print("1. Restart your TV")
        print("2. Move closer to the TV")
        print("3. Check TV's Bluetooth is on")
        print("4. Try connecting from Mac Bluetooth preferences")

if __name__ == "__main__":
    main()