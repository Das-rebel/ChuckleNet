#!/usr/bin/env python3
"""
Brave Browser Controller using AppleScript
Controls existing Brave browser and extracts Telegram data
"""

import time
import json
import logging
import subprocess
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def bring_brave_to_front():
    """Bring Brave browser to front using AppleScript"""
    try:
        applescript = '''
        tell application "Brave Browser"
            activate
            delay 2
        end tell
        '''
        subprocess.run(['osascript', '-e', applescript], check=True)
        logger.info("✅ Brave browser brought to front")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to bring Brave to front: {e}")
        return False

def check_debugging_port():
    """Check if Brave has debugging enabled"""
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(('127.0.0.1', 9222))
        sock.close()
        return result == 0
    except:
        return False

def connect_to_brave():
    """Try to connect to Brave via debugging"""
    try:
        chrome_options = Options()
        chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        driver = webdriver.Chrome(options=chrome_options)
        logger.info("✅ Connected to Brave via debugging")
        return driver
    except Exception as e:
        logger.error(f"❌ Failed to connect via debugging: {e}")
        return None

def main():
    logger.info("🚀 BRAVE TELEGRAM CONTROLLER")
    logger.info("=" * 40)

    # Step 1: Check if Brave is running with debugging
    if check_debugging_port():
        logger.info("✅ Brave debugging port is open")
        driver = connect_to_brave()
        if driver:
            logger.info("✅ Successfully connected to Brave!")
        else:
            logger.error("❌ Could not connect to Brave debugging")
            return
    else:
        logger.info("🔄 Brave debugging not available, enabling it...")

        # Try to restart Brave with debugging
        try:
            # Close Brave first
            subprocess.run(['pkill', '-f', 'Brave Browser'], check=False)
            time.sleep(2)

            # Start Brave with debugging
            brave_path = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"
            user_data = "/Users/Subho/Library/Application Support/BraveSoftware/Brave-Browser"

            subprocess.Popen([
                brave_path,
                '--remote-debugging-port=9222',
                f'--user-data-dir={user_data}',
                '--no-first-run',
                '--no-default-browser-check'
            ])

            logger.info("⏳ Waiting for Brave to start with debugging...")
            time.sleep(8)

            # Try to connect
            driver = connect_to_brave()
            if not driver:
                logger.error("❌ Failed to connect to Brave after restart")
                return

        except Exception as e:
            logger.error(f"❌ Failed to restart Brave: {e}")
            return

    try:
        # Step 2: Navigate to Telegram
        logger.info("🔗 Navigating to Telegram...")

        # First try Telegram main
        driver.get("https://web.telegram.org/k/")
        time.sleep(5)
        logger.info(f"📍 Current URL: {driver.current_url}")

        # Then try the specific channel
        channel_url = "https://web.telegram.org/k/#-2127259353"
        logger.info(f"🔗 Navigating to trading channel: {channel_url}")
        driver.get(channel_url)
        time.sleep(5)

        logger.info(f"📍 Final URL: {driver.current_url}")

        # Step 3: Extract messages
        logger.info("📨 Extracting messages...")

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
        messages = []

        for selector in selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    logger.info(f"✅ Found {len(elements)} messages with selector: {selector}")
                    messages_found = len(elements)

                    for i, element in enumerate(elements[:5]):
                        try:
                            text = element.text.strip()
                            if text and len(text) > 10:
                                messages.append({
                                    'index': i,
                                    'content': text,
                                    'length': len(text)
                                })
                                logger.info(f"📝 Message {i+1}: {text[:100]}...")
                        except:
                            continue
                    break
            except Exception as e:
                logger.debug(f"Selector {selector} failed: {e}")
                continue

        # Step 4: Look for images
        logger.info("🖼️  Looking for images...")
        images = driver.find_elements(By.TAG_NAME, "img")
        logger.info(f"✅ Found {len(images)} images")

        # Step 5: Analyze for trading content
        trading_keywords = ['buy', 'sell', 'trade', 'price', 'signal', 'btc', 'eth', 'aapl', 'tsla', 'gold']
        trading_messages = []

        for msg in messages:
            msg_lower = msg['content'].lower()
            if any(keyword in msg_lower for keyword in trading_keywords):
                trading_messages.append(msg)

        logger.info(f"📊 Found {len(trading_messages)} trading-related messages")

        # Step 6: Save results
        results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "current_url": driver.current_url,
            "messages_found": messages_found,
            "trading_messages": len(trading_messages),
            "images_found": len(images),
            "success": True,
            "messages": messages[:10],  # Save first 10 messages
            "trading_message_samples": [msg['content'][:200] for msg in trading_messages[:3]]
        }

        with open("brave_telegram_results.json", "w") as f:
            json.dump(results, f, indent=2)

        logger.info("\n" + "="*50)
        logger.info("🎉 TELEGRAM DATA EXTRACTION COMPLETE!")
        logger.info("="*50)
        logger.info(f"📈 Trading Messages: {len(trading_messages)}")
        logger.info(f"🖼️  Images: {len(images)}")
        logger.info(f"📝 Total Messages: {messages_found}")
        logger.info(f"💾 Results saved to: brave_telegram_results.json")
        logger.info("🌐 Brave browser will remain open")
        logger.info("="*50)

        # Keep browser open
        input("Press Enter to continue...")

    except Exception as e:
        logger.error(f"❌ Error during extraction: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()