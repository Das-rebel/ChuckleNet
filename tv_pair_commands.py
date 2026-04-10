#!/usr/bin/env python3
"""
Send various pairing confirmation commands to TV
"""

from Cocoa import NSAppleScript
import time

print("🔗 Trying multiple pairing confirmation commands...")

# Different commands that might work as "Select" or "Pair"
commands = [
    ("Enter", 36),
    ("Space", 49),
    ("Tab", 48),
    ("Return", 36),
]

for name, keycode in commands:
    print(f"\n📱 Trying {name} command...")

    script = f'''
    tell application "System Events"
        key code {keycode}
    end tell
    '''

    applescript = NSAppleScript.alloc().initWithSource_(script)
    result, error = applescript.executeAndReturnError_(None)

    if error:
        print(f"❌ {name} failed: {error.get('NSAppleScriptErrorMessage', 'Unknown error')}")
    else:
        print(f"✅ {name} sent successfully!")

    time.sleep(1)  # Wait between commands

print("\n🎯 Also trying arrow keys to navigate to Pair button...")

# Try navigation to Pair button if it's not selected
navigation_keys = [
    ("Right", 124),
    ("Left", 123),
    ("Up", 126),
    ("Down", 125),
]

for name, keycode in navigation_keys:
    print(f"🧭 Trying {name} arrow...")

    script = f'''
    tell application "System Events"
        key code {keycode}
    end tell
    '''

    applescript = NSAppleScript.alloc().initWithSource_(script)
    result, error = applescript.executeAndReturnError_(None)

    if error:
        print(f"❌ {name} failed")
    else:
        print(f"✅ {name} sent!")

    time.sleep(0.5)

# Final Enter attempt
print("\n✨ Final Enter attempt...")
script = '''
tell application "System Events"
    key code 36
end tell
'''

applescript = NSAppleScript.alloc().initWithSource_(script)
result, error = applescript.executeAndReturnError_(None)

if error:
    print(f"❌ Final Enter failed")
else:
    print("✅ Final Enter sent!")

print("\n🏁 Command sequence complete!")