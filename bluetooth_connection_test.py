#!/usr/bin/env python3
"""
Comprehensive Bluetooth Connection Test
Check if Mac can actually communicate with TV at all
"""

import subprocess
import time
import os
import sys
from Cocoa import NSAppleScript

class BluetoothTester:
    def __init__(self):
        self.tv_mac = "F0:35:75:78:2B:BE"
        self.tv_name = "dasi"
        print("🔍 COMPREHENSIVE BLUETOOTH CONNECTION TEST")
        print("=" * 50)
        print(f"📱 Target: {self.tv_name} ({self.tv_mac})")
        print()

    def test_bluetooth_status(self):
        """Test basic Bluetooth status"""
        print("1️⃣ CHECKING BLUETOOTH STATUS")
        print("-" * 30)

        try:
            # Check if Bluetooth is on
            result = subprocess.run(['system_profiler', 'SPBluetoothDataType'],
                                  capture_output=True, text=True)

            if "Bluetooth Power" in result.stdout and "On" in result.stdout:
                print("✅ Bluetooth is ON")
            else:
                print("❌ Bluetooth is OFF or not available")
                return False

            # Check for TV in devices
            if self.tv_name in result.stdout:
                print(f"✅ {self.tv_name} found in Bluetooth devices")

                # Check connection status
                tv_section = result.stdout.split(self.tv_name)[1].split("Gamepad")[0]
                if "Connected" in tv_section:
                    print("✅ TV shows as Connected")
                else:
                    print("❌ TV found but NOT connected")
                    print("   TV section:", tv_section[:100] + "...")
                return False
            else:
                print(f"❌ {self.tv_name} NOT found in Bluetooth devices")
                return False

        except Exception as e:
            print(f"❌ Error checking Bluetooth: {e}")
            return False

        return True

    def test_audio_streaming(self):
        """Test audio streaming to TV"""
        print("\n2️⃣ TESTING AUDIO STREAMING")
        print("-" * 30)

        try:
            # Check if TV is available as audio output
            result = subprocess.run(['system_profiler', 'SPAudioDataType'],
                                  capture_output=True, text=True)

            if self.tv_name in result.stdout:
                print("✅ TV found as audio device")
                print("💡 Trying to set TV as audio output...")

                # Try to set TV as audio output
                script = '''
                tell application "System Preferences"
                    activate
                    set current pane to pane "com.apple.preference.sound"
                    delay 1
                end tell

                tell application "System Events"
                    tell process "System Preferences"
                        tell window "Sound"
                            tell tab group 1
                                click radio button "Output"
                                delay 1
                                try
                                    select row 1 of table 1 of scroll area 1 whose name contains "dasi"
                                    delay 1
                                end try
                            end tell
                        end tell
                    end tell
                end tell
                '''

                applescript = NSAppleScript.alloc().initWithSource_(script)
                result, error = applescript.executeAndReturnError_(None)

                if not error:
                    print("✅ Attempted to set TV as audio output")
                    return True
                else:
                    print("⚠️ Could not set TV as audio output:", error.get('NSAppleScriptErrorMessage', ''))
            else:
                print("❌ TV not found as audio device")

        except Exception as e:
            print(f"❌ Audio test error: {e}")

        return False

    def play_test_sound(self):
        """Play a test sound"""
        print("\n3️⃣ PLAYING TEST SOUND")
        print("-" * 30)

        try:
            # Try to play a system sound
            sound_file = "/System/Library/Sounds/Glass.aiff"
            if os.path.exists(sound_file):
                subprocess.run(['afplay', sound_file], capture_output=True, timeout=3)
                print("✅ Played test sound (check if TV plays it)")
                return True
            else:
                print("❌ Test sound file not found")
                return False

        except Exception as e:
            print(f"❌ Could not play test sound: {e}")
            return False

    def test_hid_communication(self):
        """Test HID communication"""
        print("\n4️⃣ TESTING HID COMMUNICATION")
        print("-" * 30)

        # Try different HID commands
        test_commands = [
            ('Power', 122),
            ('Up', 126),
            ('Down', 125),
            ('Select', 36),
        ]

        working_commands = []

        for name, code in test_commands:
            script = f'''
            tell application "System Events"
                key code {code}
            end tell
            '''

            try:
                applescript = NSAppleScript.alloc().initWithSource_(script)
                result, error = applescript.executeAndReturnError_(None)

                if not error:
                    print(f"✅ {name} command sent successfully")
                    working_commands.append(name)
                else:
                    print(f"❌ {name} command failed")
            except:
                print(f"❌ {name} command error")

        if working_commands:
            print(f"✅ {len(working_commands)} commands working: {', '.join(working_commands)}")
            return True
        else:
            print("❌ No HID commands working")
            return False

    def test_alternative_connection(self):
        """Test alternative connection methods"""
        print("\n5️⃣ TESTING ALTERNATIVE CONNECTIONS")
        print("-" * 30)

        # Try using hcitool if available (Linux style)
        try:
            result = subprocess.run(['hcitool', 'scan'], capture_output=True, text=True)
            if self.tv_mac in result.stdout:
                print("✅ TV found via hcitool scan")
            else:
                print("❌ TV not found via hcitool")
        except FileNotFoundError:
            print("⚠️ hcitool not available on macOS")
        except Exception as e:
            print(f"❌ hcitool error: {e}")

        # Try using bluetoothctl style commands
        try:
            result = subprocess.run(['bluetoothctl', 'devices'], capture_output=True, text=True)
            if self.tv_mac in result.stdout:
                print("✅ TV found via bluetoothctl")
            else:
                print("❌ TV not found via bluetoothctl")
        except FileNotFoundError:
            print("⚠️ bluetoothctl not available")
        except Exception as e:
            print(f"❌ bluetoothctl error: {e}")

    def test_wifi_connection(self):
        """Test if TV is accessible via WiFi"""
        print("\n6️⃣ TESTING WI-FI CONNECTION")
        print("-" * 30)

        try:
            import socket

            # Common TV ports to check
            ports = [8080, 80, 443, 5555, 22]
            common_ips = [
                "192.168.1.100", "192.168.1.101", "192.168.1.102",
                "192.168.0.100", "192.168.0.101", "192.168.0.102"
            ]

            found = False
            for ip in common_ips:
                for port in ports:
                    try:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(1)
                        result = sock.connect_ex((ip, port))
                        if result == 0:
                            print(f"✅ Found device at {ip}:{port}")
                            found = True
                        sock.close()
                    except:
                        continue

            if not found:
                print("❌ No TV found via WiFi scan")

        except Exception as e:
            print(f"❌ WiFi test error: {e}")

    def generate_report(self):
        """Generate comprehensive report"""
        print("\n" + "=" * 50)
        print("📊 CONNECTION TEST RESULTS")
        print("=" * 50)

        print("\n💡 WHAT THIS MEANS:")

        print("\n🔵 If Bluetooth shows TV as Connected but commands fail:")
        print("   - TV might need to be paired for HID (control) profile")
        print("   - Try connecting TV as keyboard/mouse in Bluetooth settings")
        print("   - Some TVs need manual confirmation for HID pairing")

        print("\n🟢 If TV responds to commands:")
        print("   - Great! Your remote should work")
        print("   - Use the simple TV remote or GUI")

        print("\n🔴 If nothing works:")
        print("   - TV might not support HID control via Mac")
        print("   - Try phone pairing via WiFi instead")
        print("   - Consider IR blaster solution")

        print("\n📱 RECOMMENDATIONS:")
        print("1. Try Google Home app on phone (uses WiFi, not Bluetooth)")
        print("2. Try Android TV Remote Service app")
        print("3. Use YouTube casting as alternative")
        print("4. Consider USB mouse as temporary solution")

    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting comprehensive connection tests...")
        print()

        # Run all tests
        bluetooth_ok = self.test_bluetooth_status()
        audio_ok = self.test_audio_streaming() if bluetooth_ok else False
        sound_ok = self.play_test_sound() if audio_ok else False
        hid_ok = self.test_hid_communication() if bluetooth_ok else False

        self.test_alternative_connection()
        self.test_wifi_connection()

        self.generate_report()

        # Summary
        print(f"\n🎯 SUMMARY:")
        print(f"Bluetooth Status: {'✅' if bluetooth_ok else '❌'}")
        print(f"Audio Device: {'✅' if audio_ok else '❌'}")
        print(f"Sound Playback: {'✅' if sound_ok else '❌'}")
        print(f"HID Commands: {'✅' if hid_ok else '❌'}")

        if hid_ok:
            print(f"\n🎉 TV CONTROL SHOULD WORK!")
            print(f"Try: python3 simple_tv_remote.py")
        else:
            print(f"\n❌ TV CONTROL LIKELY WON'T WORK VIA BLUETOOTH")
            print(f"Try WiFi-based solutions instead")

def main():
    tester = BluetoothTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()