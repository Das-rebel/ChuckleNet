#!/usr/bin/env python3
"""
Simple Telegram Screenshot Capture with Timestamps
Captures screenshots from Telegram with timestamps for manual analysis
"""

import time
import json
import logging
import subprocess
from datetime import datetime
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def execute_applescript(script):
    """Execute AppleScript command"""
    try:
        result = subprocess.run(['osascript', '-e', script],
                             capture_output=True, text=True, timeout=30)
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return False, "", str(e)

def activate_brave():
    """Activate Brave browser"""
    script = '''tell application "Brave Browser" to activate'''
    success, output, error = execute_applescript(script)
    if success:
        logger.info("✅ Brave activated")
        return True
    else:
        logger.error(f"❌ Failed to activate Brave: {error}")
        return False

def take_screenshot_with_timestamp(description=""):
    """Take a screenshot with timestamp and description"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"telegram_capture_{timestamp}.png"
    filepath = os.path.join("/Users/Subho", filename)

    script = f'''
    tell application "System Events"
        do shell script "screencapture -x {filepath}"
    end tell
    '''

    success, output, error = execute_applescript(script)
    if success and os.path.exists(filepath):
        file_size = os.path.getsize(filepath)
        screenshot_info = {
            "filename": filename,
            "filepath": filepath,
            "timestamp": datetime.now().isoformat(),
            "description": description,
            "file_size": file_size,
            "capture_number": None  # Will be filled in by main function
        }
        logger.info(f"📸 Screenshot captured: {filename} ({file_size} bytes) - {description}")
        return screenshot_info
    else:
        logger.error(f"❌ Screenshot failed: {error}")
        return None

def scroll_up():
    """Scroll up in Brave to see older messages"""
    script = '''
    tell application "System Events"
        tell process "Brave Browser"
            delay 1
            repeat 3 times
                keystroke "page up"
                delay 0.5
            end repeat
        end tell
    end tell
    '''
    success, output, error = execute_applescript(script)
    if success:
        logger.info("📜 Scrolled up to see older messages")
        return True
    else:
        logger.warning(f"⚠️  Scroll failed: {error}")
        return False

def main():
    logger.info("🚀 SIMPLE TELEGRAM SCREENSHOT CAPTURE")
    logger.info("=" * 50)

    try:
        # Initialize data structure
        capture_session = {
            "session_start": datetime.now().isoformat(),
            "screenshots": [],
            "total_screenshots": 0,
            "success": True
        }

        # Step 1: Activate Brave
        if not activate_brave():
            return

        time.sleep(2)

        # Step 2: Take initial screenshot
        logger.info("📸 Taking initial screenshot...")
        initial_shot = take_screenshot_with_timestamp("Initial State - Current View")
        if initial_shot:
            initial_shot["capture_number"] = 1
            capture_session["screenshots"].append(initial_shot)
            capture_session["total_screenshots"] += 1

        # Step 3: Scroll and capture multiple screenshots
        logger.info("📜 Starting scroll and capture process...")
        capture_count = capture_session["total_screenshots"]

        for i in range(10):  # Capture 10 scroll positions
            logger.info(f"📸 Capturing position {i+2}/11...")

            # Scroll up to see older content
            if i < 9:  # Don't scroll after last capture
                scroll_up()
                time.sleep(2)  # Wait for content to load

            # Take screenshot
            screenshot_info = take_screenshot_with_timestamp(f"Scroll Position {i+2}")
            if screenshot_info:
                screenshot_info["capture_number"] = i + 2
                capture_session["screenshots"].append(screenshot_info)
                capture_session["total_screenshots"] += 1

            time.sleep(1)  # Brief pause between captures

        # Step 4: Save session data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_file = f"telegram_capture_session_{timestamp}.json"

        capture_session["session_end"] = datetime.now().isoformat()
        capture_session["duration_minutes"] = (datetime.now() - datetime.fromisoformat(capture_session["session_start"])).total_seconds() / 60

        with open(session_file, 'w') as f:
            json.dump(capture_session, f, indent=2)

        logger.info(f"💾 Session data saved: {session_file}")

        # Step 5: Create a summary
        summary_file = f"telegram_capture_summary_{timestamp}.txt"
        with open(summary_file, 'w') as f:
            f.write("TELEGRAM SCREENSHOT CAPTURE SUMMARY\n")
            f.write("=" * 40 + "\n\n")
            f.write(f"Session Start: {capture_session['session_start']}\n")
            f.write(f"Session End: {capture_session['session_end']}\n")
            f.write(f"Duration: {capture_session['duration_minutes']:.1f} minutes\n")
            f.write(f"Total Screenshots: {capture_session['total_screenshots']}\n\n")
            f.write("SCREENSHOTS CAPTURED:\n")
            f.write("-" * 25 + "\n")
            for shot in capture_session["screenshots"]:
                f.write(f"{shot['capture_number']:2d}. {shot['filename']}\n")
                f.write(f"     {shot['description']}\n")
                f.write(f"     Size: {shot['file_size']:,} bytes\n")
                f.write(f"     Time: {shot['timestamp']}\n\n")

        logger.info(f"📋 Summary saved: {summary_file}")

        logger.info("\n" + "="*50)
        logger.info("🎉 SCREENSHOT CAPTURE COMPLETED!")
        logger.info("="*50)
        logger.info(f"📸 Total Screenshots: {capture_session['total_screenshots']}")
        logger.info(f"⏱️  Duration: {capture_session['duration_minutes']:.1f} minutes")
        logger.info(f"📁 Session Data: {session_file}")
        logger.info(f"📋 Summary: {summary_file}")
        logger.info("🌐 Brave browser remains open with Telegram channel")
        logger.info("="*50)
        logger.info("\n💡 Next Steps:")
        logger.info("   1. Review the screenshots for trading content")
        logger.info("   2. Manual text extraction or run OCR analysis later")
        logger.info("   3. Trading signals should be visible in the screenshots")
        logger.info("="*50)

    except Exception as e:
        logger.error(f"❌ Capture error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()