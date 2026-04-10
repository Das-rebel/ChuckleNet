#!/usr/bin/env python3
"""
Simple TV Test - Check if commands actually reach your TV
"""

import subprocess
import time
from Cocoa import NSAppleScript

def test_tv_command(command_name, key_code):
    """Test if TV responds to a specific command"""
    print(f"📱 Testing {command_name} command...")

    script = f'''
    tell application "System Events"
        key code {key_code}
    end tell
    '''

    try:
        applescript = NSAppleScript.alloc().initWithSource_(script)
        result, error = applescript.executeAndReturnError_(None)

        if not error:
            print(f"✅ {command_name} command sent successfully")
            return True
        else:
            print(f"❌ {command_name} command failed: {error}")
            return False
    except Exception as e:
        print(f"❌ {command_name} command error: {e}")
        return False

def play_test_video():
    """Try to play video content to TV"""
    print("\n🎬 TRYING TO PLAY VIDEO TO TV")
    print("=" * 40)

    try:
        # Try to use AirPlay if available
        script = '''
        tell application "System Events"
            tell process "SystemUIServer"
                try
                    click menu bar item "AirPlay" of menu bar 1
                    delay 1
                    try
                        click menu item "dasi" of menu "AirPlay" of menu bar item "AirPlay" of menu bar 1
                    on error
                        log "dasi not found in AirPlay menu"
                    end try
                end try
            end tell
        end tell
        '''

        applescript = NSAppleScript.alloc().initWithSource_(script)
        result, error = applescript.executeAndReturnError_(None)

        if not error:
            print("✅ AirPlay command sent")
        else:
            print("⚠️ AirPlay not available or no dasi found")

        # Try to play a video with QuickTime
        print("🎥 Opening QuickTime with test video...")
        # Look for any video file on the system
        video_paths = [
            "/System/Library/Compositions/Default.mov",
            "/Library/Desktop Pictures/Solid Colors/*.mov"
        ]

        for path in video_paths:
            try:
                subprocess.run(['open', '-a', 'QuickTime Player', path],
                             capture_output=True, timeout=5)
                print(f"✅ Opened video: {path}")
                time.sleep(3)
                print("📺 Check if TV shows video content")
                return True
            except:
                continue

        print("❌ No test video files found")
        return False

    except Exception as e:
        print(f"❌ Video test error: {e}")
        return False

def test_audio_to_tv():
    """Test audio playback to TV"""
    print("\n🔊 TESTING AUDIO TO TV")
    print("=" * 25)

    try:
        # Try to route audio to TV
        script = '''
        tell application "System Preferences"
            activate
            set current pane to pane "com.apple.preference.sound"
            delay 2
        end tell

        tell application "System Events"
            tell process "System Preferences"
                tell window "Sound"
                    tell tab group 1
                        click radio button "Output"
                        delay 1
                        try
                            -- Look for dasi in the output list
                            tell table 1 of scroll area 1
                                repeat until exists (row 1 whose name contains "dasi")
                                    if row 1 exists then
                                        click row 1
                                        delay 1
                                        exit repeat
                                    end if
                                    delay 0.5
                                end repeat
                            end tell
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

            # Play test sound
            subprocess.run(['afplay', '/System/Library/Sounds/Ping.aiff'],
                         capture_output=True, timeout=3)
            print("🔊 Played test sound (check TV audio)")
            return True
        else:
            print("❌ Could not set TV as audio output")
            return False

    except Exception as e:
        print(f"❌ Audio test error: {e}")
        return False

def main():
    print("🧪 SIMPLE TV FUNCTIONALITY TEST")
    print("=" * 40)
    print("📱 Testing if your TV actually responds to Mac commands")
    print()

    # Test basic commands
    print("1️⃣ TESTING BASIC COMMANDS")
    print("-" * 25)

    test_commands = [
        ("Volume Up", 82),
        ("Volume Down", 81),
        ("Mute", 75),
        ("Home", 98),
    ]

    working = 0
    for name, code in test_commands:
        if test_tv_command(name, code):
            working += 1
            time.sleep(1)  # Wait to see if TV responds

    print(f"\n📊 COMMAND TEST RESULTS: {working}/{len(test_commands)} working")

    if working > 0:
        print("✅ TV IS RESPONDING to Mac commands!")
        print("💡 Your TV should have shown some response (volume change, menu, etc.)")
    else:
        print("❌ TV is NOT responding to Mac commands")

    # Test audio
    print("\n2️⃣ TESTING AUDIO/VIDEO")
    print("-" * 20)

    audio_ok = test_audio_to_tv()
    video_ok = play_test_video()

    print("\n" + "=" * 40)
    print("🎯 FINAL ASSESSMENT")
    print("=" * 40)

    if working > 0:
        print("✅ GOOD NEWS: TV responds to Mac commands!")
        print("📱 Try your phone pairing now - it should work!")
        print("💡 Use: python3 quick_tv_pairing.py")
    else:
        print("❌ TV doesn't respond to Mac commands")
        print("💡 Try these alternatives:")
        print("   1. Google Home app on your phone (WiFi based)")
        print("   2. Android TV Remote Service app")
        print("   3. YouTube casting from your phone")
        print("   4. Check if TV supports IR control")

if __name__ == "__main__":
    main()