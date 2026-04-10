#!/usr/bin/env python3
"""
Extract Messages from Already Open Brave
Connects to the existing Brave session that has Telegram open
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
    logger.info("🚀 EXTRACTING FROM OPEN BRAVE SESSION")
    logger.info("=" * 45)

    try:
        # Connect to the existing Brave debugging session
        logger.info("🔌 Connecting to existing Brave debugging session...")
        chrome_options = Options()
        chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

        try:
            driver = webdriver.Chrome(options=chrome_options)
            logger.info("✅ Connected to Brave successfully!")
        except Exception as e:
            logger.error(f"❌ Failed to connect: {e}")
            logger.info("💡 Make sure Brave is running with --remote-debugging-port=9222")
            return

        # Check current URL
        current_url = driver.current_url
        logger.info(f"📍 Current URL: {current_url}")

        if "telegram.org" not in current_url:
            logger.warning("⚠️  Brave is not on Telegram. Please navigate manually first.")
            return

        # Wait a moment for any loading
        time.sleep(3)

        # Extract messages
        logger.info("📨 Extracting messages...")

        # Try multiple selectors for messages
        selectors = [
            ".message-content",
            ".bubbles-text",
            ".message",
            "[class*='message']",
            "[class*='bubble']",
            ".chat-bubble",
            ".text-content",
            "div[class*='message']",
            ".message-text",
            ".tgme_widget_message_text"
        ]

        messages_found = 0
        messages = []

        for selector in selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    logger.info(f"✅ Found {len(elements)} elements with selector: {selector}")
                    messages_found = len(elements)

                    # Extract messages
                    for i, element in enumerate(elements):
                        try:
                            text = element.text.strip()
                            if text and len(text) > 5 and text not in [m['content'] for m in messages]:
                                messages.append({
                                    'index': len(messages) + 1,
                                    'content': text,
                                    'length': len(text)
                                })
                                if len(messages) <= 5:  # Show first 5 in logs
                                    logger.info(f"📝 Message {len(messages)}: {text[:100]}...")
                        except:
                            continue
                    if messages_found > 5:  # Found good amount, stop trying other selectors
                        break
            except Exception as e:
                logger.debug(f"Selector {selector} failed: {e}")
                continue

        # Look for images
        logger.info("🖼️  Looking for images...")
        image_selectors = ["img", "[class*='photo']", "[class*='image']", ".photo-image"]
        images_found = 0

        for selector in image_selectors:
            try:
                images = driver.find_elements(By.CSS_SELECTOR, selector)
                if images:
                    logger.info(f"✅ Found {len(images)} images with selector: {selector}")
                    images_found = len(images)
                    break
            except:
                continue

        # Look for trading keywords
        trading_keywords = ['buy', 'sell', 'trade', 'price', 'signal', 'btc', 'eth', 'aapl', 'tsla', 'gold', 'eur/usd', 'long', 'short']
        trading_messages = []

        for msg in messages:
            msg_lower = msg['content'].lower()
            if any(keyword in msg_lower for keyword in trading_keywords):
                trading_messages.append(msg)

        logger.info(f"📊 Analysis Results:")
        logger.info(f"   Total Messages: {len(messages)}")
        logger.info(f"   Trading Messages: {len(trading_messages)}")
        logger.info(f"   Images Found: {images_found}")

        # Display trading messages
        if trading_messages:
            logger.info("💰 TRADING MESSAGES FOUND:")
            for i, msg in enumerate(trading_messages[:3]):  # Show first 3
                logger.info(f"   {i+1}. {msg['content'][:150]}...")

        # Save comprehensive results
        results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "current_url": current_url,
            "total_messages": len(messages),
            "trading_messages": len(trading_messages),
            "images_found": images_found,
            "success": True,
            "messages": messages[:10],  # Save first 10 messages
            "trading_message_samples": [msg['content'][:200] for msg in trading_messages[:5]]
        }

        # Save to JSON
        with open("brave_telegram_extraction.json", "w") as f:
            json.dump(results, f, indent=2)

        logger.info("\n" + "="*45)
        logger.info("🎉 EXTRACTION COMPLETE!")
        logger.info("="*45)
        logger.info(f"📈 Trading Messages: {len(trading_messages)}")
        logger.info(f"🖼️  Images: {images_found}")
        logger.info(f"📝 Total Messages: {len(messages)}")
        logger.info(f"💾 Results saved to: brave_telegram_extraction.json")
        logger.info("🌐 Brave browser remains open")
        logger.info("="*45)

        if len(trading_messages) > 0:
            logger.info(f"✅ SUCCESS: Found {len(trading_messages)} trading-related messages!")
        else:
            logger.info("ℹ️  No trading messages found in visible content")

    except Exception as e:
        logger.error(f"❌ Error during extraction: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()