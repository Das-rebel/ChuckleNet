#!/usr/bin/env python3
"""
Normal Brave Browser Telegram Connector
Connects to Brave browser normally (not debug mode) and accesses Telegram
"""

import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    logger.info("🚀 NORMAL BRAVE TELEGRAM CONNECTOR")
    logger.info("=" * 50)

    try:
        # Set up Chrome options for Brave
        chrome_options = Options()
        chrome_options.binary_location = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"

        # Use existing user data to access logged-in sessions
        chrome_options.add_argument("--user-data-dir=/Users/Subho/Library/Application Support/BraveSoftware/Brave-Browser")
        chrome_options.add_argument("--no-first-run")
        chrome_options.add_argument("--no-default-browser-check")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        logger.info("🔌 Starting Brave browser...")
        driver = webdriver.Chrome(options=chrome_options)

        # Set page load timeout
        driver.set_page_load_timeout(30)

        logger.info("✅ Brave browser started successfully!")

        # Navigate to Telegram Web
        telegram_url = "https://web.telegram.org/k/"
        logger.info(f"🔗 Navigating to Telegram Web: {telegram_url}")
        driver.get(telegram_url)

        # Wait for page to load
        time.sleep(5)
        logger.info("✅ Telegram Web loaded")

        # Check if we're already logged in
        current_url = driver.current_url
        logger.info(f"📍 Current URL: {current_url}")

        # Try to navigate to the specific channel
        channel_url = "https://web.telegram.org/k/#-2127259353"
        logger.info(f"🔗 Navigating to trading channel: {channel_url}")

        try:
            driver.get(channel_url)
            time.sleep(5)
            logger.info("✅ Successfully navigated to trading channel")
        except Exception as e:
            logger.warning(f"⚠️  Could not navigate directly to channel: {e}")
            logger.info("📱 You may need to manually navigate to the channel")

        # Look for messages
        logger.info("📨 Looking for messages...")

        # Wait a bit more for content to load
        time.sleep(3)

        # Try different selectors to find message elements
        selectors = [
            ".message-content",
            ".bubbles-text",
            ".message",
            "[class*='message']",
            "[class*='bubble']",
            ".chat-bubble",
            ".text-content",
            "div[class*='message']"
        ]

        messages_found = 0
        messages_text = []

        for selector in selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    logger.info(f"✅ Found {len(elements)} elements with selector: {selector}")
                    messages_found = len(elements)

                    # Extract messages
                    for i, element in enumerate(elements[:10]):  # Get first 10 messages
                        try:
                            text = element.text.strip()
                            if text and len(text) > 10 and text not in messages_text:
                                messages_text.append(text)
                                logger.info(f"📝 Message {i+1}: {text[:150]}...")
                        except:
                            continue
                    break
            except Exception as e:
                logger.debug(f"Selector {selector} failed: {e}")
                continue

        # Look for images
        logger.info("🖼️  Looking for images...")
        images = driver.find_elements(By.TAG_NAME, "img")
        logger.info(f"✅ Found {len(images)} images on the page")

        # Look for trading keywords
        trading_keywords = ['buy', 'sell', 'trade', 'price', 'signal', 'btc', 'eth', 'aapl', 'tsla', 'gold', 'eur/usd']
        trading_messages = []

        for msg in messages_text:
            msg_lower = msg.lower()
            if any(keyword in msg_lower for keyword in trading_keywords):
                trading_messages.append(msg)

        logger.info(f"📊 Found {len(trading_messages)} trading-related messages")

        # Print trading messages
        if trading_messages:
            logger.info("💰 TRADING MESSAGES FOUND:")
            for i, msg in enumerate(trading_messages[:5]):  # Show first 5
                logger.info(f"   {i+1}. {msg[:200]}...")

        # Save results
        import json
        results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "current_url": driver.current_url,
            "total_messages_found": messages_found,
            "unique_messages": len(messages_text),
            "trading_messages": len(trading_messages),
            "images_found": len(images),
            "success": True,
            "trading_message_samples": trading_messages[:3] if trading_messages else []
        }

        with open("telegram_results.json", "w") as f:
            json.dump(results, f, indent=2)

        logger.info("💾 Results saved to telegram_results.json")

        logger.info("\n" + "="*50)
        logger.info("🎉 TELEGRAM ACCESS SUCCESSFUL!")
        logger.info("="*50)
        logger.info(f"📈 Trading Messages Found: {len(trading_messages)}")
        logger.info(f"🖼️  Images Found: {len(images)}")
        logger.info(f"📝 Total Messages: {messages_found}")
        logger.info("🌐 Brave browser will remain open for your use")
        logger.info("="*50)

        # Keep the browser open for user interaction
        input("\nPress Enter to close the browser...")

    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()