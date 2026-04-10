#!/usr/bin/env python3
"""
Simple Brave Check - Just activate and screenshot
"""

import time
import json
import logging
import subprocess
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def execute_applescript(script):
    """Execute AppleScript command"""
    try:
        result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True, timeout=30)
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return False, "", str(e)

def activate_and_screenshot():
    """Activate Brave and take screenshot"""

    # First activate Brave
    logger.info("🔌 Activating Brave browser...")
    script = '''tell application "Brave Browser" to activate'''
    success, output, error = execute_applescript(script)

    if not success:
        logger.error(f"❌ Failed to activate Brave: {error}")
        return False

    logger.info("✅ Brave activated")

    # Wait a moment
    time.sleep(2)

    # Take screenshot
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_file = f"/Users/Subho/brave_current_state_{timestamp}.png"

    logger.info("📸 Taking screenshot...")
    screenshot_script = f'''
    tell application "System Events"
        do shell script "screencapture -x {screenshot_file}"
    end tell
    '''

    success, output, error = execute_applescript(screenshot_script)

    if success:
        logger.info(f"✅ Screenshot saved: brave_current_state_{timestamp}.png")

        # Check if file was created
        if os.path.exists(screenshot_file):
            file_size = os.path.getsize(screenshot_file)
            logger.info(f"📊 Screenshot file size: {file_size} bytes")
            return True, screenshot_file
        else:
            logger.error("❌ Screenshot file not found")
            return False, None
    else:
        logger.error(f"❌ Screenshot failed: {error}")
        return False, None

def get_current_url():
    """Try to get current URL from Brave"""
    script = '''
    tell application "Brave Browser"
        try
            set currentURL to URL of front document
            return currentURL
        on error
            return "Could not get URL"
        end try
    end tell
    '''

    success, output, error = execute_applescript(script)
    if success and output != "Could not get URL":
        return output
    else:
        return None

def main():
    logger.info("🚀 SIMPLE BRAVE CHECK")
    logger.info("=" * 25)

    try:
        # Step 1: Activate Brave and screenshot
        success, screenshot_file = activate_and_screenshot()
        if not success:
            logger.error("❌ Failed to get screenshot")
            return

        # Step 2: Try to get current URL
        logger.info("📍 Getting current URL...")
        current_url = get_current_url()
        if current_url:
            logger.info(f"✅ Current URL: {current_url}")
        else:
            logger.info("⚠️  Could not determine current URL")

        # Step 3: Save summary
        summary = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "brave_activated": True,
            "screenshot_taken": success,
            "current_url": current_url,
            "success": True
        }

        with open("brave_check_summary.json", "w") as f:
            json.dump(summary, f, indent=2)

        logger.info("\n" + "="*25)
        logger.info("🎉 BRAVE CHECK COMPLETE!")
        logger.info("="*25)
        logger.info(f"📸 Screenshot: Available")
        logger.info(f"📍 URL: {current_url if current_url else 'Unknown'}")
        logger.info("="*25)

        # Manual instructions
        if "telegram.org" in str(current_url or "").lower():
            logger.info("✅ Brave is showing Telegram!")
            logger.info("📱 The screenshot should show the trading channel")
        else:
            logger.info("📋 Manual steps needed:")
            logger.info("   1. In Brave, go to https://web.telegram.org/k/")
            logger.info("   2. Log in if needed")
            logger.info("   3. Navigate to channel: https://web.telegram.org/k/#-2127259353")
            logger.info("   4. Then run a scraping script")

    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import os
    main()