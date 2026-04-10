#!/usr/bin/env python3
"""
Brave Browser Telegram Scraper with Qwen OCR Integration

This enhanced scraper connects to your existing Brave browser with Telegram logged in
and uses Qwen AI models to perform OCR on trading images, extracting detailed
trading signals from screenshots, charts, and annotations.
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
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from PIL import Image
import io

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class QwenOCRProcessor:
    """Qwen OCR processor for trading image analysis"""

    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.logger = logging.getLogger(__name__)

    def encode_image_to_base64(self, image_path: str) -> str:
        """Encode image to base64 for API transmission"""
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            self.logger.error(f"❌ Failed to encode image {image_path}: {e}")
            return None

    def extract_trading_signals_from_image(self, image_path: str) -> Dict:
        """Extract trading signals from image using Qwen OCR with trading-specific prompts"""
        try:
            base64_image = self.encode_image_to_base64(image_path)
            if not base64_image:
                return {"success": False, "error": "Failed to encode image"}

            # Trading-specific OCR prompt for Qwen
            prompt = """
            Analyze this trading screenshot and extract all trading-related information.
            Look for:

            1. TRADING SIGNALS:
               - Buy/Sell indicators (arrows, text like "BUY", "SELL", "ENTER", "EXIT")
               - Signal emojis (🟢🔴✅❌🚀📉📈)
               - Chart patterns and technical analysis

            2. PRICE INFORMATION:
               - Current price levels
               - Support/resistance levels
               - Target prices
               - Stop loss levels

            3. TECHNICAL INDICATORS:
               - RSI, MACD, Moving Averages
               - Volume indicators
               - Trend lines and patterns

            4. SYMBOLS:
               - Cryptocurrency symbols (BTC, ETH, etc.)
               - Stock symbols (AAPL, TSLA, etc.)
               - Forex pairs (EUR/USD, etc.)

            5. TIMEFRAMES:
               - Chart timeframes (1m, 5m, 1h, 4h, 1D)
               - Entry/exit timing

            Please provide the analysis in this JSON format:
            {
                "signals_detected": true/false,
                "action": "BUY/SELL/HOLD",
                "symbol": "symbol_name",
                "price": current_price,
                "support_levels": [price1, price2],
                "resistance_levels": [price1, price2],
                "target_price": target,
                "stop_loss": stop_loss,
                "confidence": 0.0-1.0,
                "timeframe": "timeframe",
                "technical_analysis": {
                    "trend": "bullish/bearish/sideways",
                    "indicators": ["indicator1", "indicator2"],
                    "patterns": ["pattern1", "pattern2"]
                },
                "extracted_text": "all text from image",
                "analysis_summary": "brief summary of the trading opportunity"
            }

            If no clear trading signals are found, set signals_detected to false.
            """

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": "qwen-vl-plus",  # or "qwen-vl-max" for better quality
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 1500,
                "temperature": 0.1  # Lower temperature for more consistent analysis
            }

            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']

                # Try to parse JSON from the response
                try:
                    # Extract JSON from the content
                    import re
                    json_match = re.search(r'\{.*\}', content, re.DOTALL)
                    if json_match:
                        trading_analysis = json.loads(json_match.group())
                        trading_analysis["raw_response"] = content
                        trading_analysis["success"] = True
                        return trading_analysis
                    else:
                        # Fallback: return the raw text
                        return {
                            "success": True,
                            "signals_detected": False,
                            "extracted_text": content,
                            "analysis_summary": "Could not parse structured trading data from image"
                        }
                except json.JSONDecodeError:
                    return {
                        "success": True,
                        "signals_detected": False,
                        "extracted_text": content,
                        "analysis_summary": "Could not parse JSON response from Qwen"
                    }

            else:
                self.logger.error(f"❌ Qwen API error: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"API error: {response.status_code}",
                    "details": response.text
                }

        except Exception as e:
            self.logger.error(f"❌ Error processing image with Qwen OCR: {e}")
            return {
                "success": False,
                "error": str(e)
            }

class BraveTelegramScraperWithOCR:
    """Enhanced scraper with Qwen OCR capabilities"""

    def __init__(self, qwen_api_key: str):
        self.driver = None
        self.browser_path = self._find_brave_browser()
        self.user_data_dir = self._find_brave_user_data()
        self.channel_url = "https://web.telegram.org/k/#-2127259353"
        self.signals = []
        self.image_signals = []

        # Initialize Qwen OCR processor
        self.ocr_processor = QwenOCRProcessor(qwen_api_key)

        # Create directories for images
        self.image_dir = "telegram_images"
        self.processed_dir = "processed_images"
        os.makedirs(self.image_dir, exist_ok=True)
        os.makedirs(self.processed_dir, exist_ok=True)

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

    def extract_text_messages(self, scroll_count: int = 3) -> List[str]:
        """Extract text messages from the Telegram channel"""
        messages = []

        try:
            logger.info("📨 Extracting text messages...")

            # Scroll up to load more messages
            for i in range(scroll_count):
                logger.info(f"📜 Scrolling up... ({i+1}/{scroll_count})")
                self.driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(2)

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
                    if (text and len(text) > 10 and
                        text not in seen_messages and
                        not text.startswith('[') and
                        any(keyword in text.lower() for keyword in ['buy', 'sell', 'trade', 'price', 'signal'])):

                        seen_messages.add(text)
                        messages.append(text)
                except:
                    continue

            logger.info(f"✅ Extracted {len(messages)} text messages")
            return messages

        except Exception as e:
            logger.error(f"❌ Error extracting text messages: {e}")
            return []

    def extract_and_download_images(self, scroll_count: int = 3) -> List[str]:
        """Extract and download images from Telegram messages"""
        image_paths = []

        try:
            logger.info("🖼️  Extracting images from messages...")

            # Scroll up to load more messages
            for i in range(scroll_count):
                self.driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(2)

            # Find image elements
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
            for i, element in enumerate(image_elements):
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
                        if img_url.startswith('data:image'):
                            # Handle base64 images
                            img_data = base64.b64decode(img_url.split(',')[1])
                            img_filename = f"telegram_image_{timestamp}_{i}.jpg"
                            img_path = os.path.join(self.image_dir, img_filename)

                            with open(img_path, 'wb') as f:
                                f.write(img_data)
                        else:
                            # Download from URL
                            response = requests.get(img_url, timeout=10)
                            if response.status_code == 200:
                                img_filename = f"telegram_image_{timestamp}_{i}.jpg"
                                img_path = os.path.join(self.image_dir, img_filename)

                                with open(img_path, 'wb') as f:
                                    f.write(response.content)

                        image_paths.append(img_path)
                        logger.info(f"💾 Downloaded image: {img_filename}")

                except Exception as e:
                    logger.debug(f"Error downloading image {i}: {e}")
                    continue

            logger.info(f"✅ Downloaded {len(image_paths)} images")
            return image_paths

        except Exception as e:
            logger.error(f"❌ Error extracting images: {e}")
            return []

    def process_images_with_ocr(self, image_paths: List[str]) -> List[Dict]:
        """Process downloaded images with Qwen OCR"""
        image_signals = []

        for image_path in image_paths:
            try:
                logger.info(f"🔍 Processing image: {os.path.basename(image_path)}")

                # Process with Qwen OCR
                ocr_result = self.ocr_processor.extract_trading_signals_from_image(image_path)

                if ocr_result.get("success", False):
                    if ocr_result.get("signals_detected", False):
                        # Extract trading signal
                        signal_data = {
                            'timestamp': datetime.now().isoformat(),
                            'source': 'image_ocr',
                            'image_path': image_path,
                            'action': ocr_result.get('action', 'HOLD'),
                            'symbol': ocr_result.get('symbol'),
                            'price': ocr_result.get('price'),
                            'target_price': ocr_result.get('target_price'),
                            'stop_loss': ocr_result.get('stop_loss'),
                            'support_levels': ocr_result.get('support_levels', []),
                            'resistance_levels': ocr_result.get('resistance_levels', []),
                            'confidence': ocr_result.get('confidence', 0.0),
                            'timeframe': ocr_result.get('timeframe'),
                            'technical_analysis': ocr_result.get('technical_analysis', {}),
                            'extracted_text': ocr_result.get('extracted_text', ''),
                            'analysis_summary': ocr_result.get('analysis_summary', ''),
                            'raw_response': ocr_result.get('raw_response', '')
                        }

                        image_signals.append(signal_data)
                        self._log_image_signal(signal_data)

                        # Move to processed folder
                        processed_filename = f"processed_{os.path.basename(image_path)}"
                        processed_path = os.path.join(self.processed_dir, processed_filename)
                        os.rename(image_path, processed_path)

                    else:
                        logger.info(f"📷 No trading signals found in image: {os.path.basename(image_path)}")
                else:
                    logger.error(f"❌ OCR failed for image: {os.path.basename(image_path)}")
                    logger.error(f"   Error: {ocr_result.get('error', 'Unknown error')}")

            except Exception as e:
                logger.error(f"❌ Error processing image {image_path}: {e}")

        logger.info(f"🎯 Found {len(image_signals)} trading signals from images")
        return image_signals

    def _log_image_signal(self, signal: Dict):
        """Log an image-based trading signal"""
        logger.info("🎯 IMAGE-BASED TRADING SIGNAL DETECTED:")
        logger.info(f"   Action: {signal['action']}")
        logger.info(f"   Symbol: {signal['symbol']}")
        logger.info(f"   Price: ${signal['price']}" if signal['price'] else "   Price: Not specified")
        logger.info(f"   Target: ${signal['target_price']}" if signal.get('target_price') else "   Target: Not specified")
        logger.info(f"   Stop Loss: ${signal['stop_loss']}" if signal.get('stop_loss') else "   Stop Loss: Not specified")
        logger.info(f"   Confidence: {signal['confidence']:.2f}")
        logger.info(f"   Timeframe: {signal.get('timeframe', 'N/A')}")
        logger.info(f"   Analysis: {signal.get('analysis_summary', 'N/A')[:100]}...")

    def analyze_text_signals(self, messages: List[str]) -> List[Dict]:
        """Analyze text messages for trading signals"""
        signals = []

        # Trading signal patterns
        buy_patterns = [
            r'(?i)(buy|long|enter).*?(btc|eth|aapl|tsla|eur/usd|gold|spy)',
            r'(?i)(buy signal|entry point|go long|long position)',
            r'(?i)(🟢|✅|🚀|📈).*?(buy|enter|long)',
            r'(?i)(bullish|uptrend|breakout).*?(buy|enter)'
        ]

        sell_patterns = [
            r'(?i)(sell|short|exit).*?(btc|eth|aapl|tsla|eur/usd|gold|spy)',
            r'(?i)(sell signal|exit point|go short|short position)',
            r'(?i)(🔴|❌|📉).*?(sell|exit|short)',
            r'(?i)(bearish|downtrend|breakdown).*?(sell|exit)'
        ]

        trading_symbols = ['BTC', 'ETH', 'AAPL', 'TSLA', 'EUR/USD', 'GOLD', 'SPY']

        for message in messages:
            signal_data = {
                'timestamp': datetime.now().isoformat(),
                'source': 'text_analysis',
                'message': message[:200] + "..." if len(message) > 200 else message,
                'action': 'HOLD',
                'symbol': None,
                'price': None,
                'confidence': 0.0
            }

            confidence = self._calculate_signal_confidence(message)
            signal_data['confidence'] = confidence

            if confidence < 0.6:
                continue

            # Determine action
            for pattern in buy_patterns:
                if self._pattern_match(message, pattern):
                    signal_data['action'] = 'BUY'
                    break

            for pattern in sell_patterns:
                if self._pattern_match(message, pattern):
                    signal_data['action'] = 'SELL'
                    break

            # Extract symbol
            for symbol in trading_symbols:
                if symbol.lower() in message.lower():
                    signal_data['symbol'] = symbol
                    break

            # Extract price
            price_patterns = [
                r'\$?(\d+\.?\d*)\s*(usd)?',
                r'(price|at|@)\s*[$]?(\d+\.?\d*)',
                r'(\d+\.?\d*)\s*[$]?'
            ]

            for pattern in price_patterns:
                match = self._pattern_match(message, pattern)
                if match:
                    try:
                        import re
                        numbers = re.findall(r'\d+\.?\d*', match.group(0))
                        if numbers:
                            signal_data['price'] = float(numbers[0])
                            break
                    except:
                        pass

            if signal_data['action'] != 'HOLD' and signal_data['symbol']:
                signals.append(signal_data)

        logger.info(f"🎯 Found {len(signals)} trading signals from text")
        return signals

    def _calculate_signal_confidence(self, message: str) -> float:
        """Calculate confidence score for a trading signal"""
        confidence = 0.0

        trading_emojis = ['🟢', '🔴', '✅', '❌', '🚀', '📉', '📈', '💰', '⚡', '🎯']
        emoji_count = sum(1 for emoji in trading_emojis if emoji in message)
        confidence += min(emoji_count * 0.2, 0.4)

        trading_keywords = [
            'buy', 'sell', 'trade', 'signal', 'entry', 'exit', 'long', 'short',
            'bullish', 'bearish', 'breakout', 'support', 'resistance', 'target'
        ]
        keyword_count = sum(1 for keyword in trading_keywords if keyword.lower() in message.lower())
        confidence += min(keyword_count * 0.1, 0.3)

        if '$' in message or any(char.isdigit() for char in message):
            confidence += 0.2

        urgency_words = ['now', 'urgent', 'immediate', 'fast', 'quick']
        urgency_count = sum(1 for word in urgency_words if word.lower() in message.lower())
        confidence += min(urgency_count * 0.1, 0.1)

        return min(confidence, 1.0)

    def _pattern_match(self, text: str, pattern: str) -> Optional[any]:
        """Helper method for regex pattern matching"""
        try:
            import re
            return re.search(pattern, text)
        except:
            return None

    def monitor_channel(self, duration_minutes: int = 60, check_interval: int = 60):
        """Monitor the Telegram channel for text and image signals"""
        logger.info(f"🚀 Starting enhanced monitoring for {duration_minutes} minutes...")
        logger.info(f"📊 Checking text and image signals every {check_interval} seconds")

        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=duration_minutes)

        all_text_signals = []
        all_image_signals = []

        try:
            while datetime.now() < end_time:
                logger.info(f"🔍 Checking for new signals... ({datetime.now().strftime('%H:%M:%S')})")

                # Extract text messages and analyze
                messages = self.extract_text_messages()
                current_text_signals = self.analyze_text_signals(messages)

                # Extract and process images
                image_paths = self.extract_and_download_images()
                current_image_signals = self.process_images_with_ocr(image_paths)

                # Process new text signals
                for signal in current_text_signals:
                    if signal not in all_text_signals:
                        all_text_signals.append(signal)
                        self._log_text_signal(signal)
                        self._save_signal_to_file(signal, "text")

                # Process new image signals
                for signal in current_image_signals:
                    if signal not in all_image_signals:
                        all_image_signals.append(signal)
                        self._save_signal_to_file(signal, "image")

                # Wait for next check
                logger.info(f"⏳ Waiting {check_interval} seconds for next check...")
                time.sleep(check_interval)

        except KeyboardInterrupt:
            logger.info("⏹️  Monitoring stopped by user")
        except Exception as e:
            logger.error(f"❌ Error during monitoring: {e}")
        finally:
            self._generate_final_report(all_text_signals, all_image_signals)

    def _log_text_signal(self, signal: Dict):
        """Log a text-based trading signal"""
        logger.info("🎯 TEXT-BASED TRADING SIGNAL:")
        logger.info(f"   Action: {signal['action']}")
        logger.info(f"   Symbol: {signal['symbol']}")
        logger.info(f"   Price: ${signal['price']}" if signal['price'] else "   Price: Not specified")
        logger.info(f"   Confidence: {signal['confidence']:.2f}")
        logger.info(f"   Message: {signal['message'][:100]}...")

    def _save_signal_to_file(self, signal: Dict, signal_type: str):
        """Save signal to JSON file"""
        filename = f"telegram_{signal_type}_signals_{datetime.now().strftime('%Y%m%d')}.json"

        try:
            existing_signals = []
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    existing_signals = json.load(f)

            existing_signals.append(signal)

            with open(filename, 'w') as f:
                json.dump(existing_signals, f, indent=2)

        except Exception as e:
            logger.error(f"❌ Error saving signal to file: {e}")

    def _generate_final_report(self, text_signals: List[Dict], image_signals: List[Dict]):
        """Generate final monitoring report"""
        logger.info("📋 GENERATING FINAL REPORT")

        # Text signal statistics
        text_buy = len([s for s in text_signals if s['action'] == 'BUY'])
        text_sell = len([s for s in text_signals if s['action'] == 'SELL'])
        text_avg_confidence = sum(s['confidence'] for s in text_signals) / len(text_signals) if text_signals else 0

        # Image signal statistics
        image_buy = len([s for s in image_signals if s['action'] == 'BUY'])
        image_sell = len([s for s in image_signals if s['action'] == 'SELL'])
        image_avg_confidence = sum(s['confidence'] for s in image_signals) / len(image_signals) if image_signals else 0

        report = {
            'monitoring_summary': {
                'total_text_signals': len(text_signals),
                'total_image_signals': len(image_signals),
                'total_signals': len(text_signals) + len(image_signals),
                'text_signals': {
                    'buy': text_buy,
                    'sell': text_sell,
                    'avg_confidence': round(text_avg_confidence, 3)
                },
                'image_signals': {
                    'buy': image_buy,
                    'sell': image_sell,
                    'avg_confidence': round(image_avg_confidence, 3)
                }
            },
            'text_signals': text_signals,
            'image_signals': image_signals,
            'generated_at': datetime.now().isoformat()
        }

        report_filename = f"enhanced_telegram_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w') as f:
            json.dump(report, f, indent=2)

        logger.info(f"   📊 Text Signals: {len(text_signals)} (Buy: {text_buy}, Sell: {text_sell})")
        logger.info(f"   🖼️  Image Signals: {len(image_signals)} (Buy: {image_buy}, Sell: {image_sell})")
        logger.info(f"   🎯 Total Signals: {len(text_signals) + len(image_signals)}")
        logger.info(f"   💾 Report saved: {report_filename}")

    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            logger.info("🌐 Keeping Brave browser open for your continued use")

def main():
    """Main execution function"""
    logger.info("🚀 BRAVE TELEGRAM SCRAPER WITH QWEN OCR")
    logger.info("=" * 60)

    # Get Qwen API key
    qwen_api_key = os.getenv('QWEN_API_KEY')
    if not qwen_api_key:
        logger.error("❌ QWEN_API_KEY environment variable not set")
        logger.info("Please set your Qwen API key:")
        logger.info("export QWEN_API_KEY='your-qwen-api-key-here'")
        return

    scraper = None
    try:
        # Initialize scraper with Qwen OCR
        scraper = BraveTelegramScraperWithOCR(qwen_api_key)

        # Connect to Brave browser
        if not scraper.connect_to_brave():
            logger.error("❌ Failed to connect to Brave browser")
            return

        # Navigate to channel
        if not scraper.navigate_to_channel():
            logger.error("❌ Failed to navigate to channel")
            return

        # Start monitoring
        scraper.monitor_channel(duration_minutes=60, check_interval=60)

    except KeyboardInterrupt:
        logger.info("⏹️  Scraper stopped by user")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
    finally:
        if scraper:
            scraper.cleanup()
        logger.info("🏁 Enhanced scraper finished")

if __name__ == "__main__":
    main()