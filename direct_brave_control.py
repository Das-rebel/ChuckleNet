#!/usr/bin/env python3
"""
Direct Brave Browser Control using AppleScript and screenshots
"""

import time
import json
import logging
import subprocess
import os
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def execute_applescript(script):
    """Execute AppleScript command"""
    try:
        result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return False, "", str(e)

def activate_brave():
    """Activate Brave browser"""
    script = '''tell application "Brave Browser" to activate'''
    success, output, error = execute_applescript(script)
    return success

def open_telegram():
    """Open Telegram Web in Brave"""
    script = '''
    tell application "Brave Browser"
        activate
        delay 1
        set URL of front document to "https://web.telegram.org/k/#-2127259353"
        delay 3
    end tell
    '''
    success, output, error = execute_applescript(script)
    return success

def take_screenshot():
    """Take a screenshot of the current screen"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"brave_screenshot_{timestamp}.png"

    script = f'''
    tell application "System Events"
        set screenshotPath to "/Users/Subho/{filename}" as string
        do shell script "screencapture -x " & quoted form of screenshotPath
    end tell
    '''

    success, output, error = execute_applescript(script)
    if success:
        return filename
    else:
        logger.error(f"Screenshot failed: {error}")
        return None

def get_page_source_attempt():
    """Try to get page source using JavaScript"""
    script = '''
    tell application "Brave Browser"
        activate
        delay 1
        tell front document
            try
                set pageSource to execute javascript "document.documentElement.outerHTML"
                return pageSource
            on error
                return "Error getting page source"
            end try
        end tell
    end tell
    '''

    success, output, error = execute_applescript(script)
    if success and output != "Error getting page source":
        return output
    else:
        logger.warning(f"Could not get page source: {error}")
        return None

def main():
    logger.info("🚀 DIRECT BRAVE CONTROL")
    logger.info("=" * 30)

    try:
        # Step 1: Activate Brave
        logger.info("🔌 Activating Brave browser...")
        if not activate_brave():
            logger.error("❌ Failed to activate Brave")
            return
        logger.info("✅ Brave activated")

        # Step 2: Open Telegram
        logger.info("📱 Opening Telegram channel...")
        if not open_telegram():
            logger.error("❌ Failed to open Telegram")
            return
        logger.info("✅ Telegram channel opened")

        # Step 3: Wait for page to load
        logger.info("⏳ Waiting for page to load...")
        time.sleep(5)

        # Step 4: Take screenshot
        logger.info("📸 Taking screenshot...")
        screenshot_file = take_screenshot()
        if screenshot_file:
            logger.info(f"✅ Screenshot saved: {screenshot_file}")
        else:
            logger.error("❌ Screenshot failed")

        # Step 5: Try to get page source
        logger.info("📄 Attempting to get page source...")
        page_source = get_page_source_attempt()
        if page_source:
            # Save page source to file
            source_file = f"telegram_page_source_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            with open(source_file, 'w', encoding='utf-8') as f:
                f.write(page_source)
            logger.info(f"✅ Page source saved: {source_file}")

            # Look for message patterns in HTML
            if "message" in page_source.lower():
                logger.info("✅ Found message elements in page source")
            if "buy" in page_source.lower() or "sell" in page_source.lower():
                logger.info("💰 Found potential trading signals in page source")

        # Step 6: Save summary
        summary = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "brave_activated": True,
            "telegram_opened": True,
            "screenshot_file": screenshot_file if screenshot_file else None,
            "page_source_saved": page_source is not None,
            "success": True
        }

        with open("brave_control_summary.json", "w") as f:
            json.dump(summary, f, indent=2)

        logger.info("\n" + "="*30)
        logger.info("🎉 BRAVE CONTROL COMPLETE!")
        logger.info("="*30)
        logger.info(f"📸 Screenshot: {screenshot_file}")
        logger.info(f"📄 Page Source: {'Saved' if page_source else 'Not available'}")
        logger.info(f"💾 Summary: brave_control_summary.json")
        logger.info("\n📱 Check the screenshot and page source files!")
        logger.info("="*30)

        # Keep Brave open for user
        logger.info("🌐 Brave browser is open and ready for your use")

    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()