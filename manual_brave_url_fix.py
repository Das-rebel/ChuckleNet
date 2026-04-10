#!/usr/bin/env python3
"""
Manual Brave URL Fix using AppleScript
Uses AppleScript to control Brave and navigate to Telegram
"""

import time
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

def open_new_tab():
    """Open a new tab in Brave"""
    script = '''
    tell application "System Events"
        tell process "Brave Browser"
            keystroke "t" using command down
            delay 1
        end tell
    end tell
    '''
    success, output, error = execute_applescript(script)
    if success:
        logger.info("✅ New tab opened")
        return True
    else:
        logger.warning(f"⚠️  Could not open new tab: {error}")
        return False

def navigate_to_url(url):
    """Navigate to a specific URL in Brave"""
    # Focus on address bar
    address_bar_script = '''
    tell application "System Events"
        tell process "Brave Browser"
            keystroke "l" using command down
            delay 0.5
        end tell
    end tell
    '''

    # Type the URL
    url_script = f'''
    tell application "System Events"
        tell process "Brave Browser"
            keystroke "{url}"
            delay 0.5
            keystroke return
        end tell
    end tell
    '''

    logger.info(f"🔗 Navigating to: {url}")

    # Execute the navigation
    success1, output1, error1 = execute_applescript(address_bar_script)
    if not success1:
        logger.warning(f"⚠️  Could not focus address bar: {error1}")

    time.sleep(1)

    success2, output2, error2 = execute_applescript(url_script)
    if success2:
        logger.info("✅ URL entered and navigating")
        return True
    else:
        logger.error(f"❌ Failed to enter URL: {error2}")
        return False

def wait_for_page_load():
    """Wait for page to load"""
    logger.info("⏳ Waiting for page to load...")
    time.sleep(8)

def take_screenshot():
    """Take a screenshot for verification"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"telegram_step_{timestamp}.png"

    script = f'''
    tell application "System Events"
        do shell script "screencapture -x /Users/Subho/{filename}"
    end tell
    '''

    success, output, error = execute_applescript(script)
    if success:
        logger.info(f"📸 Screenshot saved: {filename}")
        return filename
    else:
        logger.error(f"❌ Screenshot failed: {error}")
        return None

def main():
    logger.info("🚀 MANUAL BRAVE URL FIX")
    logger.info("=" * 30)

    try:
        # Step 1: Activate Brave
        if not activate_brave():
            return

        time.sleep(2)

        # Step 2: Open new tab (optional)
        open_new_tab()
        time.sleep(1)

        # Step 3: Navigate to Telegram Web
        logger.info("📱 Step 1: Opening Telegram Web...")
        if not navigate_to_url("https://web.telegram.org/k/"):
            return

        wait_for_page_load()
        screenshot1 = take_screenshot()

        # Step 4: Navigate to the specific channel
        logger.info("📈 Step 2: Opening trading channel...")
        if not navigate_to_url("https://web.telegram.org/k/#-2127259353"):
            return

        wait_for_page_load()
        screenshot2 = take_screenshot()

        logger.info("\n" + "="*30)
        logger.info("🎉 BRAVE URL FIX COMPLETE!")
        logger.info("="*30)
        logger.info("✅ Telegram Web opened")
        logger.info("✅ Trading channel opened")
        logger.info(f"📸 Screenshots: {screenshot1} and {screenshot2}")
        logger.info("🌐 Brave is ready with Telegram channel!")
        logger.info("="*30)
        logger.info("\n💡 Check the screenshots to verify:")
        logger.info("   1. Telegram Web loaded")
        logger.info("   2. Trading channel visible")
        logger.info("   3. Messages are accessible")
        logger.info("="*30)

        # Success message
        logger.info("\n✅ SUCCESS: Brave browser now has the Telegram channel open!")
        logger.info("🚀 Ready for message extraction!")

    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()