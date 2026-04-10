#!/usr/bin/env python3
"""
Send Enter/Select command to TV
"""

from Cocoa import NSAppleScript

print("📺 Sending Enter/Select to TV...")

script = '''
tell application "System Events"
    key code 36  -- Enter key
end tell
'''

applescript = NSAppleScript.alloc().initWithSource_(script)
result, error = applescript.executeAndReturnError_(None)

if error:
    print(f"❌ Error: {error.get('NSAppleScriptErrorMessage', 'Unknown error')}")
else:
    print("✅ Enter/Select sent to TV!")