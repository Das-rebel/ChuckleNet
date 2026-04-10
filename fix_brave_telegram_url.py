#!/usr/bin/env python3
"""
Fix Brave Telegram URL Navigation
Ensures Brave opens with the correct Telegram channel URL
"""

import time
import logging
import subprocess
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    logger.info("🚀 FIXING BRAVE TELEGRAM URL NAVIGATION")
    logger.info("=" * 50)

    try:
        # Close any existing Brave instances to start fresh
        logger.info("🔄 Closing any existing Brave instances...")
        subprocess.run(['pkill', '-f', 'Brave Browser'], check=False)
        time.sleep(3)

        # Set up Chrome options for Brave
        chrome_options = Options()
        chrome_options.binary_location = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"

        # Use existing user data to access logged-in sessions
        user_data_dir = "/Users/Subho/Library/Application Support/BraveSoftware/Brave-Browser"
        chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
        chrome_options.add_argument("--no-first-run")
        chrome_options.add_argument("--no-default-browser-check")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        logger.info("🔌 Starting fresh Brave browser instance...")
        driver = webdriver.Chrome(options=chrome_options)

        # Set timeouts
        driver.set_page_load_timeout(60)
        driver.implicitly_wait(10)

        logger.info("✅ Brave browser started successfully!")

        # Step 1: Navigate to Telegram Web first
        logger.info("📱 Step 1: Navigating to Telegram Web...")
        telegram_web_url = "https://web.telegram.org/k/"
        logger.info(f"🔗 URL: {telegram_web_url}")

        try:
            driver.get(telegram_web_url)
            logger.info("✅ Telegram Web loaded")
        except Exception as e:
            logger.warning(f"⚠️  Telegram Web load issue: {e}")

        # Wait for Telegram to load
        time.sleep(5)

        # Check current state
        current_url = driver.current_url
        logger.info(f"📍 Current URL after Telegram Web: {current_url}")

        # Step 2: Wait a bit more for full load
        logger.info("⏳ Waiting for Telegram to fully load...")
        time.sleep(5)

        # Step 3: Navigate to the specific channel
        logger.info("📈 Step 2: Navigating to trading channel...")
        channel_url = "https://web.telegram.org/k/#-2127259353"
        logger.info(f"🔗 Channel URL: {channel_url}")

        try:
            driver.get(channel_url)
            logger.info("✅ Channel URL loaded")
        except Exception as e:
            logger.warning(f"⚠️  Channel URL load issue: {e}")

        # Wait for channel to load
        time.sleep(8)

        # Final URL check
        final_url = driver.current_url
        logger.info(f"📍 Final URL: {final_url}")

        # Check if we're in the right place
        if "web.telegram.org" in final_url:
            logger.info("✅ Successfully loaded Telegram!")
            if "-2127259353" in final_url or final_url.endswith("#"):
                logger.info("✅ Channel navigation appears successful!")
            else:
                logger.info("ℹ️  Telegram loaded, but channel may need manual navigation")
        else:
            logger.warning("⚠️  Not on Telegram - check if login is needed")

        # Try to find some elements to verify the page
        try:
            # Look for any message-like elements
            message_elements = driver.find_elements(By.CSS_SELECTOR, "[class*='message'], [class*='chat'], [class*='bubble']")
            logger.info(f"📨 Found {len(message_elements)} potential message elements")

            # Look for input field (indicates Telegram is loaded)
            input_elements = driver.find_elements(By.CSS_SELECTOR, "input[type='text'], textarea, [contenteditable='true']")
            logger.info(f"⌨️  Found {len(input_elements)} input elements")

        except Exception as e:
            logger.debug(f"Element search failed: {e}")

        # Take a screenshot for verification
        try:
            screenshot_path = f"/Users/Subho/telegram_verification_{int(time.time())}.png"
            driver.save_screenshot(screenshot_path)
            logger.info(f"📸 Screenshot saved: {screenshot_path}")
        except Exception as e:
            logger.warning(f"Screenshot failed: {e}")

        logger.info("\n" + "="*50)
        logger.info("🎉 BRAVE TELEGRAM URL FIX COMPLETE!")
        logger.info("="*50)
        logger.info(f"📍 Final URL: {final_url}")
        logger.info("📱 Browser is ready for message extraction")
        logger.info("🌐 Brave will remain open for your use")
        logger.info("="*50)
        logger.info("\n💡 Next steps:")
        logger.info("   1. Check if the Telegram channel loaded properly")
        logger.info("   2. If login is needed, log in manually")
        logger.info("   3. Run the message extraction script")
        logger.info("="*50)

        # Keep browser open
        input("\nPress Enter to close the browser...")

    except Exception as e:
        logger.error(f"❌ Error during Brave setup: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()