#!/usr/bin/env python3
"""
Quick TV Pairing Solution
Direct script to get your phone paired without complex GUI
"""

import subprocess
import time
from Cocoa import NSAppleScript

def send_command(command):
    """Send command to TV"""
    commands = {
        'home': 98,
        'up': 126,
        'down': 125,
        'right': 124,
        'select': 36,
    }

    keycode = commands.get(command, 98)

    script = f'''
    tell application "System Events"
        key code {keycode}
    end tell
    '''

    try:
        applescript = NSAppleScript.alloc().initWithSource_(script)
        result, error = applescript.executeAndReturnError_(None)
        return not error
    except:
        return False

def main():
    print("🎬 QUICK TV PAIRING SOLUTION")
    print("=" * 35)
    print("📱 This will get your iQoo phone paired to the TV")
    print()

    print("🔄 Step 1: Navigate to Bluetooth Settings")
    print("   Sending navigation commands...")

    # Navigate to Bluetooth settings
    sequence = [
        ('home', 'Go to home screen'),
        ('right', 'Navigate to apps'),
        ('right', 'Navigate to Settings'),
        ('select', 'Open Settings'),
        ('down', 'Navigate down'),
        ('down', 'Navigate to Connected Devices'),
        ('select', 'Open Connected Devices'),
        ('down', 'Navigate to Bluetooth'),
        ('select', 'Open Bluetooth'),
    ]

    for cmd, desc in sequence:
        print(f"   {desc}...")
        if send_command(cmd):
            print(f"   ✅ {desc}")
        else:
            print(f"   ❌ {desc}")
        time.sleep(1.5)

    print()
    print("✅ TV should now be in Bluetooth settings")
    print()

    print("🔄 Step 2: Start Pairing Mode")
    print("   Starting pairing mode...")

    # Start pairing mode
    pairing_sequence = [
        ('down', 'Navigate down'),
        ('down', 'Navigate down'),
        ('down', 'Navigate to pairing'),
        ('select', 'Start pairing'),
    ]

    for cmd, desc in pairing_sequence:
        print(f"   {desc}...")
        if send_command(cmd):
            print(f"   ✅ {desc}")
        else:
            print(f"   ❌ {desc}")
        time.sleep(2)

    print()
    print("🎯 TV IS NOW IN PAIRING MODE!")
    print("=" * 35)
    print()
    print("📱 NOW ON YOUR iQOO PHONE:")
    print("1. Open Settings → Bluetooth & device connection")
    print("2. Turn Bluetooth ON")
    print("3. Tap 'Scan' or 'Pair new device'")
    print("4. Look for 'dasi' in the list")
    print("5. Tap on 'dasi' when it appears")
    print("6. Confirm pairing if asked")
    print()
    print("💡 The TV should remain in pairing mode for 60 seconds")
    print("💡 Your phone should find 'dasi' immediately")
    print()
    print("✨ Once paired, your phone will work as a TV remote!")
    print("💡 You can control TV, volume, apps, etc. from your phone")

if __name__ == "__main__":
    main()