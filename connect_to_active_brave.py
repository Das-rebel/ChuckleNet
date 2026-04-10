#!/usr/bin/env python3
"""
Connect to Active Brave Browser Session

This script attempts to connect to your currently running Brave browser
that already has Telegram logged in, without needing remote debugging setup.
"""

import os
import time
import json
import logging
import psutil
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def find_brave_processes():
    """Find all running Brave browser processes"""
    brave_processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if 'brave' in proc.info['name'].lower():
                cmdline = proc.info.get('cmdline', [])
                if cmdline and any('Brave Browser' in str(cmd) for cmd in cmdline):
                    brave_processes.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return brave_processes

def check_brave_debugging_ports():
    """Check if Brave is running on any debugging port"""
    common_ports = [9222, 9223, 9224, 9225]
    for port in common_ports:
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            if result == 0:
                return port
        except:
            continue
    return None

def launch_brave_with_debugging():
    """Try to launch Brave with debugging"""
    try:
        # Kill any existing Brave processes (gracefully)
        logger.info("🔄 Attempting to restart Brave with debugging...")
        subprocess.run(['pkill', '-f', 'Brave Browser'], check=False)
        time.sleep(3)

        # Get Brave path
        brave_path = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"
        if not os.path.exists(brave_path):
            logger.error("❌ Brave Browser not found")
            return False

        # Launch Brave with remote debugging
        subprocess.Popen([
            brave_path,
            '--remote-debugging-port=9222',
            '--user-data-dir=/Users/Subho/Library/Application Support/BraveSoftware/Brave-Browser',
            '--no-first-run',
            '--no-default-browser-check',
            '--disable-web-security',
            '--allow-running-insecure-content',
            '--disable-features=TranslateUI',
            '--disable-ipc-flooding-protection'
        ])

        logger.info("⏳ Waiting for Brave to start with debugging...")
        time.sleep(8)

        # Check if debugging is now available
        if check_brave_debugging_ports() == 9222:
            logger.info("✅ Brave is now running with remote debugging")
            return True
        else:
            logger.error("❌ Brave did not start with debugging enabled")
            return False

    except Exception as e:
        logger.error(f"❌ Error launching Brave: {e}")
        return False

def connect_to_brave():
    """Connect to Brave browser with debugging"""
    debug_port = check_brave_debugging_ports()

    if not debug_port:
        logger.info("🔄 Brave debugging not found, attempting to enable...")
        if not launch_brave_with_debugging():
            logger.error("❌ Failed to enable Brave debugging")
            return None
        debug_port = 9222

    try:
        logger.info(f"🔌 Connecting to Brave on port {debug_port}...")

        chrome_options = Options()
        chrome_options.add_experimental_option("debuggerAddress", f"127.0.0.1:{debug_port}")
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')

        driver = webdriver.Chrome(options=chrome_options)

        # Test connection
        current_url = driver.current_url
        logger.info(f"✅ Connected to Brave. Current URL: {current_url}")

        return driver

    except Exception as e:
        logger.error(f"❌ Failed to connect to Brave: {e}")
        return None

def check_telegram_session(driver):
    """Check if Telegram is logged in"""
    try:
        logger.info("🔍 Checking Telegram session...")

        # Navigate to Telegram Web
        driver.get("https://web.telegram.org/k/")
        time.sleep(5)

        # Look for signs of being logged in
        login_indicators = [
            "//div[contains(@class, 'chat-list')]",
            "//div[contains(@class, 'sidebar')]",
            "//div[contains(@class, 'chat')]",
            "//button[contains(text(), 'New chat')]",
            "//div[contains(@class, 'message')]"
        ]

        logged_in = False
        for indicator in login_indicators:
            try:
                elements = driver.find_elements(By.XPATH, indicator)
                if elements and len(elements) > 0:
                    logged_in = True
                    logger.info("✅ Telegram session found - already logged in!")
                    break
            except:
                continue

        if not logged_in:
            logger.warning("⚠️  Could not confirm Telegram login status")
            logger.info("   Please ensure you are logged into Telegram Web")
            logger.info("   The scraper will proceed anyway...")

        return True

    except Exception as e:
        logger.error(f"❌ Error checking Telegram session: {e}")
        return False

def navigate_to_channel(driver, channel_url="https://web.telegram.org/k/#-2127259353"):
    """Navigate to the specific Telegram channel"""
    try:
        logger.info(f"🔗 Navigating to channel: {channel_url}")
        driver.get(channel_url)
        time.sleep(5)

        # Wait for channel to load
        try:
            WebDriverWait(driver, 15).until(
                lambda driver: driver.current_url.startswith("https://web.telegram.org/k/#-")
            )
            logger.info("✅ Successfully navigated to Telegram channel")
            return True
        except TimeoutException:
            logger.warning("⚠️  Channel loading timed out, but continuing...")
            return True

    except Exception as e:
        logger.error(f"❌ Error navigating to channel: {e}")
        return False

def extract_messages(driver, max_scrolls=20):
    """Extract messages from the Telegram channel"""
    messages = []
    seen_texts = set()

    try:
        logger.info(f"📨 Extracting messages... (max {max_scrolls} scrolls)")

        # Scroll up to load more messages
        for i in range(max_scrolls):
            logger.info(f"📜 Scrolling... ({i+1}/{max_scrolls})")

            # Scroll to top
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)

            # Look for message elements
            message_selectors = [
                ".message-content",
                ".bubbles-text",
                ".message",
                "[class*='message']",
                "[class*='bubble']",
                ".chat-bubble",
                ".text-content",
                "div[class*='message']"
            ]

            all_elements = []
            for selector in message_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        all_elements.extend(elements)
                        break
                except:
                    continue

            # Extract text from elements
            new_messages = 0
            for element in all_elements:
                try:
                    text = element.text.strip()
                    if (text and len(text) > 10 and
                        text not in seen_texts and
                        not text.startswith('[') and
                        not text.startswith('Media')):

                        seen_texts.add(text)
                        messages.append({
                            'timestamp': datetime.now().isoformat(),
                            'content': text,
                            'length': len(text),
                            'has_trading_keywords': any(keyword in text.lower() for keyword in
                                ['buy', 'sell', 'trade', 'price', 'signal', 'btc', 'eth', 'aapl', 'tsla', 'gold', 'eur/usd'])
                        })
                        new_messages += 1
                except:
                    continue

            if new_messages == 0:
                logger.info("📄 No new messages found, stopping scroll")
                break

        logger.info(f"✅ Extracted {len(messages)} messages total")
        trading_messages = len([m for m in messages if m['has_trading_keywords']])
        logger.info(f"📊 Found {trading_messages} trading-related messages")

        return messages

    except Exception as e:
        logger.error(f"❌ Error extracting messages: {e}")
        return []

def extract_images(driver, max_images=50):
    """Extract and download images from the channel"""
    image_paths = []

    try:
        logger.info(f"🖼️  Extracting images... (max {max_images} images)")

        # Scroll up more to ensure we get images
        for i in range(10):
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)

        # Look for image elements
        image_selectors = [
            "img",
            "[class*='photo']",
            "[class*='image']",
            ".photo-image",
            ".media-photo",
            "a[href*='photo']"
        ]

        image_elements = []
        for selector in image_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    logger.info(f"✅ Found {len(elements)} potential images with selector: {selector}")
                    image_elements.extend(elements)
                    break
            except:
                continue

        # Download images
        import base64
        import requests
        from urllib.parse import urlparse

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        image_dir = "trading_images"
        os.makedirs(image_dir, exist_ok=True)

        downloaded = 0
        for i, element in enumerate(image_elements[:max_images]):
            try:
                # Get image URL
                img_url = None
                if element.tag_name == 'img':
                    img_url = element.get_attribute('src')
                else:
                    # Try to find image within the element
                    img_elements_nested = element.find_elements(By.TAG_NAME, 'img')
                    if img_elements_nested:
                        img_url = img_elements_nested[0].get_attribute('src')

                if img_url and img_url.startswith(('http', 'data:image')):
                    img_filename = f"trading_image_{timestamp}_{downloaded+1}.jpg"
                    img_path = os.path.join(image_dir, img_filename)

                    if img_url.startswith('data:image'):
                        # Handle base64 images
                        img_data = base64.b64decode(img_url.split(',')[1])
                        with open(img_path, 'wb') as f:
                            f.write(img_data)
                    else:
                        # Download from URL
                        response = requests.get(img_url, timeout=10)
                        if response.status_code == 200:
                            with open(img_path, 'wb') as f:
                                f.write(response.content)

                    image_paths.append(img_path)
                    downloaded += 1
                    logger.info(f"💾 Downloaded image {downloaded}/{max_images}: {img_filename}")

            except Exception as e:
                logger.debug(f"Error downloading image {i}: {e}")
                continue

        logger.info(f"✅ Downloaded {len(image_paths)} images")
        return image_paths

    except Exception as e:
        logger.error(f"❌ Error extracting images: {e}")
        return []

def save_results(messages, image_paths):
    """Save the extracted results"""
    try:
        # Create results directory
        results_dir = "scraping_results"
        os.makedirs(results_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save messages
        messages_file = os.path.join(results_dir, f"messages_{timestamp}.json")
        with open(messages_file, 'w') as f:
            json.dump(messages, f, indent=2)
        logger.info(f"💾 Saved {len(messages)} messages to {messages_file}")

        # Save image list
        images_file = os.path.join(results_dir, f"images_{timestamp}.json")
        image_data = []
        for img_path in image_paths:
            image_data.append({
                'filename': os.path.basename(img_path),
                'path': img_path,
                'size': os.path.getsize(img_path),
                'timestamp': datetime.now().isoformat()
            })

        with open(images_file, 'w') as f:
            json.dump(image_data, f, indent=2)
        logger.info(f"💾 Saved {len(image_paths)} image references to {images_file}")

        # Create summary
        summary = {
            'extraction_date': datetime.now().isoformat(),
            'total_messages': len(messages),
            'trading_messages': len([m for m in messages if m['has_trading_keywords']]),
            'total_images': len(image_paths),
            'results_directory': results_dir,
            'messages_file': messages_file,
            'images_file': images_file
        }

        summary_file = os.path.join(results_dir, f"summary_{timestamp}.json")
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)

        logger.info(f"📋 Extraction summary:")
        logger.info(f"   Total Messages: {len(messages)}")
        logger.info(f"   Trading Messages: {summary['trading_messages']}")
        logger.info(f"   Images: {len(image_paths)}")
        logger.info(f"   Results saved to: {results_dir}")

        return summary

    except Exception as e:
        logger.error(f"❌ Error saving results: {e}")
        return None

def main():
    """Main execution function"""
    logger.info("🚀 CONNECTING TO ACTIVE BRAVE SESSION")
    logger.info("=" * 50)

    driver = None
    try:
        # Check existing Brave processes
        brave_processes = find_brave_processes()
        if brave_processes:
            logger.info(f"✅ Found {len(brave_processes)} Brave browser process(es)")
        else:
            logger.info("🔄 No Brave processes found, will launch new instance")

        # Connect to Brave
        driver = connect_to_brave()
        if not driver:
            logger.error("❌ Failed to connect to Brave browser")
            return

        # Check Telegram session
        if not check_telegram_session(driver):
            logger.error("❌ Could not access Telegram properly")
            return

        # Navigate to channel
        if not navigate_to_channel(driver):
            logger.error("❌ Failed to navigate to channel")
            return

        # Extract data
        logger.info("\n" + "=" * 50)
        logger.info("📊 STARTING DATA EXTRACTION")
        logger.info("=" * 50)

        messages = extract_messages(driver, max_scrolls=30)
        images = extract_images(driver, max_images=50)

        # Save results
        summary = save_results(messages, images)

        if summary:
            logger.info("\n" + "=" * 50)
            logger.info("🎉 EXTRACTION COMPLETED SUCCESSFULLY!")
            logger.info("=" * 50)
            logger.info(f"📈 Trading Messages Found: {summary['trading_messages']}")
            logger.info(f"🖼️  Images Downloaded: {summary['total_images']}")
            logger.info(f"📁 All Data Saved To: {summary['results_directory']}")
            logger.info("\n💡 Next Steps:")
            logger.info("   1. Review the saved JSON files")
            logger.info("   2. Run AI analysis on the collected data")
            logger.info("   3. Use the trading insights for decision making")

    except KeyboardInterrupt:
        logger.info("⏹️  Extraction stopped by user")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
    finally:
        if driver:
            logger.info("🌐 Keeping Brave browser open for your continued use")

if __name__ == "__main__":
    main()