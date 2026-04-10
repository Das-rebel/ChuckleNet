#!/usr/bin/env python3
"""
Force TV to use HID (Human Interface Device) profile for remote control
"""

import subprocess
import time
from Cocoa import NSAppleScript

print("🎮 Forcing TV HID Control Mode...")

# Try to make TV treat Mac as keyboard/mouse input
scripts = [
    # Attempt 1: Force system to send input as HID device
    '''
    tell application "System Events"
        set frontmost of first process whose name contains "System Preferences" to true
        delay 1
        key code 125 using {control down}  -- Control + Down arrow
    end tell
    ''',

    # Attempt 2: Alternative key codes
    '''
    tell application "System Events"
        key code 36 using {shift down}  -- Shift + Enter
    end tell
    ''',

    # Attempt 3: Simulate mouse click
    '''
    tell application "System Events"
        click at {100, 100}
    end tell
    '''
]

for i, script in enumerate(scripts):
    print(f"\n🎯 Attempt {i+1}...")

    applescript = NSAppleScript.alloc().initWithSource_(script)
    result, error = applescript.executeAndReturnError_(None)

    if error:
        print(f"❌ Attempt {i+1} failed: {error.get('NSAppleScriptErrorMessage', 'Unknown')}")
    else:
        print(f"✅ Attempt {i+1} sent!")

    time.sleep(1)

print("\n🔄 Alternative HID approach...")

# Try using system-level input that bypasses AppleScript
try:
    # Use osascript with different approach
    result = subprocess.run([
        'osascript', '-e',
        '''
        tell application "System Events"
            key code 36
        end tell
        '''
    ], capture_output=True, text=True)

    if result.returncode == 0:
        print("✅ Alternative Enter sent!")
    else:
        print(f"❌ Alternative failed: {result.stderr}")

except Exception as e:
    print(f"❌ System error: {e}")

print("🏁 HID control attempts complete!")