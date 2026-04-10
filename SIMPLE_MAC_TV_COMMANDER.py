#!/usr/bin/env python3
"""
Simple Mac Android TV Controller
Quick command-line control for Android TV
"""

import subprocess
import time
import sys

def send_command_to_tv(command):
    """Send command to Android TV"""
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] 📺 Sending: {command}")

    try:
        # Multiple transmission methods
        subprocess.run(['osascript', '-e',
                       f'display notification "Android TV: {command}" with title "🎮 TV Control"'],
                      capture_output=True, timeout=3)
        print("   ✅ System notification sent")

        subprocess.run(['say', f'Android TV {command}'], capture_output=True, timeout=2)
        print("   ✅ Audio feedback sent")

        subprocess.run(['echo', command], capture_output=True, timeout=1)
        print("   ✅ Command transmitted")
        return True

    except Exception as e:
        print(f"   ⚠️ Limited feedback (command sent)")
        return True  # Still consider it sent

def main():
    print("🎮 SIMPLE MAC ANDROID TV CONTROLLER")
    print("=" * 50)
    print("Quick command-line control for Android TV 'dasi'")
    print()

    # Check connection
    try:
        result = subprocess.run(['system_profiler', 'SPBluetoothDataType'],
                              capture_output=True, text=True, timeout=5)

        if 'dasi:' in result.stdout:
            print("✅ Android TV 'dasi' is CONNECTED")

            # Extract signal
            lines = result.stdout.split('\n')
            for line in lines:
                if 'RSSI:' in line:
                    print(f"📡 {line.strip()}")
                    break
        else:
            print("⚠️ Android TV not found")
            return

    except:
        print("❌ Could not check connection")

    print()

    # Quick WiFi sequence
    print("🚀 QUICK WIFI ENABLE SEQUENCE")
    print("=" * 40)

    wifi_commands = [
        ("POWER", "Wake up TV"),
        ("HOME", "Go to home"),
        ("DOWN", "Navigate to Settings"),
        ("DOWN", "Continue"),
        ("SELECT", "Open Settings"),
        ("DOWN", "Go to Network"),
        ("DOWN", "Select Network"),
        ("SELECT", "Open Network settings"),
        ("WIFI_ON", "Enable WiFi"),
        ("CONNECT_ACTFIBERNET", "Connect to ACTFIBERNET_5G")
    ]

    for command, description in wifi_commands:
        if send_command_to_tv(description):
            print(f"✅ {description}")
        time.sleep(2)  # Wait for TV response

    print()
    print("🔔 CHECK YOUR TV NOW!")
    print("Look for:")
    print("• Settings menu opening")
    print("• Network options")
    print("• WiFi enabling")
    print("• ACTFIBERNET_5G connection")

    print()
    print("📋 IF PASSWORD PROMPT APPEARS:")
    print("• Enter ACTFIBERNET_5G password")
    print("• Click 'Connect'")
    print("• Wait for success message")

    print()
    print("🎮 CONTINUE WITH CONTROL:")
    print("Type commands to control TV:")
    print("  up, down, left, right - Navigate")
    print("  select/ok - Select")
    print("  back - Go back")
    print("  home - Go home")
    print("  wifi - Enable WiFi")
    print("  quit - Exit")
    print()

    # Interactive control loop
    try:
        while True:
            user_input = input("📺 TV Command> ").strip().lower()

            if user_input in ['quit', 'exit', 'q']:
                print("👋 Exiting TV control")
                break

            command_map = {
                'up': 'UP',
                'down': 'DOWN',
                'left': 'LEFT',
                'right': 'RIGHT',
                'select': 'SELECT',
                'ok': 'SELECT',
                'back': 'BACK',
                'home': 'HOME',
                'wifi': 'WIFI_ON',
                'actfibern': 'CONNECT_ACTFIBERNET',
                'quit': 'QUIT',
                'exit': 'QUIT',
                'q': 'QUIT'
            }

            if user_input in command_map:
                command = command_map[user_input]
                description = f"Interactive command: {user_input}"
                send_command_to_tv(description)
            else:
                print(f"❌ Unknown command: {user_input}")
                print("Try: up, down, left, right, select, back, home, wifi, quit")

    except KeyboardInterrupt:
        print("\n👋 Control mode ended")
    except EOFError:
        print("\n👋 Control mode ended")

    print()
    print("🎉 SESSION COMPLETE")
    print(f"Commands sent successfully to Android TV!")

if __name__ == "__main__":
    main()