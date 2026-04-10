#!/usr/bin/env python3
"""
Simple Telegram Scraper - Direct Connection
"""

import time
import json
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    logger.info("🚀 SIMPLE TELEGRAM SCRAPER")
    logger.info("=" * 40)

    try:
        # Connect to existing Brave debugging session
        logger.info("🔌 Connecting to Brave debugging session...")
        chrome_options = Options()
        chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

        driver = webdriver.Chrome(options=chrome_options)
        logger.info("✅ Connected to Brave successfully!")

        # Navigate to Telegram channel
        channel_url = "https://web.telegram.org/k/#-2127259353"
        logger.info(f"🔗 Navigating to channel: {channel_url}")
        driver.get(channel_url)
        time.sleep(5)

        logger.info("✅ Successfully navigated to Telegram channel")
        logger.info(f"📍 Current URL: {driver.current_url}")

        # Look for messages
        logger.info("📨 Looking for messages...")

        # Try different selectors to find message elements
        selectors = [
            ".message-content",
            ".bubbles-text",
            ".message",
            "[class*='message']",
            "[class*='bubble']",
            "div[class*='message']"
        ]

        messages_found = 0
        for selector in selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    logger.info(f"✅ Found {len(elements)} elements with selector: {selector}")
                    messages_found = len(elements)

                    # Extract and display first few messages
                    for i, element in enumerate(elements[:3]):
                        try:
                            text = element.text.strip()
                            if text and len(text) > 10:
                                logger.info(f"📝 Message {i+1}: {text[:100]}...")
                        except:
                            continue
                    break
            except Exception as e:
                logger.debug(f"Selector {selector} failed: {e}")
                continue

        if messages_found == 0:
            logger.warning("⚠️  No messages found with any selector")
            logger.info("🔍 Let's check what's actually on the page...")

            # Get page source length
            page_source_length = len(driver.page_source)
            logger.info(f"📄 Page source length: {page_source_length} characters")

            # Look for any text content
            body_text = driver.find_element(By.TAG_NAME, "body").text
            logger.info(f"📄 Body text length: {len(body_text)} characters")
            if body_text:
                logger.info(f"📄 First 200 chars of body: {body_text[:200]}...")

        # Look for images
        logger.info("🖼️  Looking for images...")
        images = driver.find_elements(By.TAG_NAME, "img")
        logger.info(f"✅ Found {len(images)} images on the page")

        # Save a simple summary
        summary = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "url": driver.current_url,
            "messages_found": messages_found,
            "images_found": len(images),
            "success": True
        }

        with open("telegram_scraping_summary.json", "w") as f:
            json.dump(summary, f, indent=2)

        logger.info("💾 Summary saved to telegram_scraping_summary.json")
        logger.info("🎉 Scraping completed successfully!")

        # Keep browser open
        logger.info("🌐 Keeping Brave browser open for your use")

    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()