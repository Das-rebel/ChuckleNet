#!/usr/bin/env python3
"""
Simple Telegram Data Extractor - Focused on data collection only

This script extracts messages and images from Telegram without AI analysis,
saving the raw data for later processing.
"""

import os
import time
import json
import logging
import psutil
import subprocess
import base64
import requests
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

class TelegramDataExtractor:
    """Simple Telegram data extractor"""

    def __init__(self):
        self.driver = None
        self.browser_path = self._find_brave_browser()
        self.user_data_dir = self._find_brave_user_data()
        self.channel_url = "https://web.telegram.org/k/#-2127259353"

        # Create directories for data
        self.data_dir = "telegram_raw_data"
        self.image_dir = os.path.join(self.data_dir, "images")
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.image_dir, exist_ok=True)

    def _find_brave_browser(self) -> Optional[str]:
        """Find Brave browser executable path"""
        possible_paths = [
            "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
            os.path.expanduser("~/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"),
        ]

        for path in possible_paths:
            if os.path.exists(path):
                logger.info(f"✅ Found Brave Browser at: {path}")
                return path

        try:
            result = subprocess.run(['mdfind', 'kMDItemDisplayName == "Brave Browser"'],
                                  capture_output=True, text=True)
            if result.stdout.strip():
                brave_path = os.path.join(result.stdout.strip(),
                                         "Contents/MacOS/Brave Browser")
                if os.path.exists(brave_path):
                    logger.info(f"✅ Found Brave Browser via mdfind: {brave_path}")
                    return brave_path
        except:
            pass

        logger.error("❌ Brave Browser not found")
        return None

    def _find_brave_user_data(self) -> Optional[str]:
        """Find Brave browser user data directory"""
        possible_paths = [
            os.path.expanduser("~/Library/Application Support/BraveSoftware/Brave-Browser"),
            os.path.expanduser("~/Library/Application Support/Brave-Browser"),
        ]

        for path in possible_paths:
            if os.path.exists(path):
                logger.info(f"✅ Found Brave user data at: {path}")
                return path

        logger.error("❌ Brave user data directory not found")
        return None

    def connect_to_brave(self) -> bool:
        """Connect to existing Brave browser session"""
        try:
            # Check if Brave is running
            if not self._is_brave_running():
                logger.info("🚀 Launching Brave browser...")
                self._launch_brave_with_debugging()

            # Connect to existing Brave browser
            chrome_options = Options()
            chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')

            self.driver = webdriver.Chrome(options=chrome_options)
            logger.info("✅ Connected to Brave browser")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to connect to Brave browser: {e}")
            return False

    def _is_brave_running(self) -> bool:
        """Check if Brave browser is currently running"""
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if 'brave' in proc.info['name'].lower():
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False

    def _launch_brave_with_debugging(self):
        """Launch Brave browser with remote debugging enabled"""
        try:
            subprocess.run(['pkill', '-f', 'Brave Browser'], check=False)
            time.sleep(2)

            subprocess.Popen([
                self.browser_path,
                '--remote-debugging-port=9222',
                '--user-data-dir=' + self.user_data_dir,
                '--no-first-run',
                '--no-default-browser-check'
            ])

            time.sleep(5)
        except Exception as e:
            logger.error(f"❌ Failed to launch Brave browser: {e}")
            raise

    def navigate_to_channel(self) -> bool:
        """Navigate to the Telegram channel"""
        try:
            logger.info(f"🔗 Navigating to channel: {self.channel_url}")
            self.driver.get(self.channel_url)
            time.sleep(3)

            WebDriverWait(self.driver, 10).until(
                lambda driver: driver.current_url.startswith("https://web.telegram.org/k/#-")
            )
            logger.info("✅ Successfully navigated to Telegram channel")
            return True

        except Exception as e:
            logger.error(f"❌ Error navigating to channel: {e}")
            return False

    def extract_historical_data(self, days_back: int = 7) -> Tuple[List[Dict], List[str]]:
        """Extract messages and images from the last N days"""
        messages = []
        image_paths = []

        try:
            logger.info(f"📜 Extracting historical data from last {days_back} days...")

            # Calculate scroll amount for 7 days
            scroll_iterations = min(days_back * 10, 50)  # Cap at 50 scrolls
            logger.info(f"🔄 Performing {scroll_iterations} scroll operations to load historical data...")

            for i in range(scroll_iterations):
                logger.info(f"📜 Scrolling up... ({i+1}/{scroll_iterations})")

                # Scroll to top of chat
                self.driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(2)

                # Try to click "Load more" if it appears
                try:
                    load_more_buttons = self.driver.find_elements(By.XPATH,
                        "//button[contains(text(), 'Load more')] | //div[contains(text(), 'Load more')]")
                    for button in load_more_buttons:
                        if button.is_displayed():
                            self.driver.execute_script("arguments[0].click();", button)
                            time.sleep(1)
                except:
                    pass

            # Extract text messages
            logger.info("📨 Extracting text messages...")
            message_selectors = [
                ".message-content",
                ".bubbles-text",
                ".message",
                "[class*='message']",
                "[class*='bubble']",
                ".chat-bubble",
                ".text-content"
            ]

            all_elements = []
            for selector in message_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        logger.info(f"✅ Found {len(elements)} messages with selector: {selector}")
                        all_elements.extend(elements)
                        break
                except:
                    continue

            seen_messages = set()
            for element in all_elements:
                try:
                    text = element.text.strip()
                    if (text and len(text) > 5 and
                        text not in seen_messages):

                        message_data = {
                            'timestamp': datetime.now().isoformat(),
                            'content': text,
                            'length': len(text),
                            'has_trading_keywords': any(keyword in text.lower() for keyword in
                                ['buy', 'sell', 'trade', 'price', 'signal', 'btc', 'eth', 'aapl', 'tsla'])
                        }

                        seen_messages.add(text)
                        messages.append(message_data)
                except:
                    continue

            # Extract images
            logger.info("🖼️  Extracting images...")
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
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        logger.info(f"✅ Found {len(elements)} images with selector: {selector}")
                        image_elements.extend(elements)
                        break
                except:
                    continue

            # Download images
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            for i, element in enumerate(image_elements[:100]):  # Limit to 100 images
                try:
                    # Get image URL
                    img_url = None
                    if element.tag_name == 'img':
                        img_url = element.get_attribute('src')
                    else:
                        # Try to find image within the element
                        img = element.find_element(By.TAG_NAME, 'img')
                        img_url = img.get_attribute('src')

                    if img_url and img_url.startswith(('http', 'data:image')):
                        # Download image
                        img_filename = f"telegram_image_{timestamp}_{i}.jpg"
                        img_path = os.path.join(self.image_dir, img_filename)

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
                        logger.info(f"💾 Downloaded image: {img_filename}")

                except Exception as e:
                    logger.debug(f"Error downloading image {i}: {e}")
                    continue

            logger.info(f"✅ Extraction complete: {len(messages)} messages, {len(image_paths)} images")
            return messages, image_paths

        except Exception as e:
            logger.error(f"❌ Error extracting historical data: {e}")
            return [], []

    def save_data(self, messages: List[Dict], image_paths: List[str]):
        """Save extracted data to files"""
        try:
            # Save messages
            messages_file = os.path.join(self.data_dir, f"messages_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            with open(messages_file, 'w') as f:
                json.dump(messages, f, indent=2)
            logger.info(f"💾 Saved {len(messages)} messages to {messages_file}")

            # Save image list
            images_file = os.path.join(self.data_dir, f"images_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
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

            # Save summary
            summary = {
                'extraction_date': datetime.now().isoformat(),
                'total_messages': len(messages),
                'total_images': len(image_paths),
                'trading_messages': len([m for m in messages if m['has_trading_keywords']]),
                'data_directory': self.data_dir,
                'messages_file': messages_file,
                'images_file': images_file
            }

            summary_file = os.path.join(self.data_dir, f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2)
            logger.info(f"💾 Saved extraction summary to {summary_file}")

        except Exception as e:
            logger.error(f"❌ Error saving data: {e}")

    def extract_data(self, days_back: int = 7):
        """Main extraction function"""
        logger.info(f"🚀 Starting Telegram data extraction for last {days_back} days...")

        start_time = datetime.now()

        try:
            # Connect to Brave browser
            if not self.connect_to_brave():
                logger.error("❌ Failed to connect to Brave browser")
                return

            # Navigate to channel
            if not self.navigate_to_channel():
                logger.error("❌ Failed to navigate to channel")
                return

            # Extract historical data
            messages, image_paths = self.extract_historical_data(days_back)

            # Save data
            self.save_data(messages, image_paths)

            # Print summary
            duration = (datetime.now() - start_time).total_seconds()
            trading_messages = len([m for m in messages if m['has_trading_keywords']])

            logger.info("\n" + "="*60)
            logger.info("📊 DATA EXTRACTION SUMMARY")
            logger.info("="*60)
            logger.info(f"   Total Messages: {len(messages)}")
            logger.info(f"   Trading Messages: {trading_messages}")
            logger.info(f"   Images Downloaded: {len(image_paths)}")
            logger.info(f"   Data Directory: {self.data_dir}")
            logger.info(f"   Extraction Time: {duration:.1f} seconds")
            logger.info("="*60)

        except Exception as e:
            logger.error(f"❌ Error during extraction: {e}")
        finally:
            if self.driver:
                logger.info("🌐 Keeping Brave browser open for your use")

def main():
    """Main execution function"""
    logger.info("🚀 TELEGRAM DATA EXTRACTOR")
    logger.info("=" * 40)

    extractor = None
    try:
        extractor = TelegramDataExtractor()
        extractor.extract_data(days_back=7)

    except KeyboardInterrupt:
        logger.info("⏹️  Extraction stopped by user")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
    finally:
        logger.info("🏁 Data extraction completed")

if __name__ == "__main__":
    main()