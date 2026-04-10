#!/usr/bin/env python3
"""
Brave Browser Telegram Scraper with OpenAI GPT-4V Vision Integration

This enhanced scraper connects to your existing Brave browser with Telegram logged in
and uses OpenAI's GPT-4V model to perform OCR on trading images, extracting detailed
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

class OpenAIVisionProcessor:
    """OpenAI GPT-4V processor for trading image analysis"""

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
        """Extract trading signals from image using OpenAI GPT-4V with trading-specific prompts"""
        try:
            base64_image = self.encode_image_to_base64(image_path)
            if not base64_image:
                return {"success": False, "error": "Failed to encode image"}

            # Enhanced trading-specific prompt for GPT-4V
            prompt = """
            You are an expert trading analyst. Analyze this trading screenshot and extract all trading-related information with high precision.

            FOCUS ON EXTRACTING:

            1. TRADING SIGNALS (Priority: High):
               - Buy/Sell indicators (arrows, text like "BUY", "SELL", "ENTER", "EXIT", "LONG", "SHORT")
               - Signal emojis (🟢🔴✅❌🚀📉📈💰⚡🎯)
               - Chart patterns and technical analysis formations
               - Entry/Exit recommendations

            2. PRICE INFORMATION (Priority: High):
               - Current price levels (exact numbers)
               - Support and resistance levels
               - Target prices (Take Profit)
               - Stop loss levels
               - Price action zones

            3. TRADING SYMBOLS (Priority: High):
               - Cryptocurrency symbols (BTC, ETH, SOL, BNB, ADA, DOT, etc.)
               - Stock symbols (AAPL, TSLA, GOOGL, MSFT, AMZN, NVDA, etc.)
               - Forex pairs (EUR/USD, GBP/USD, USD/JPY, etc.)
               - Commodity symbols (GOLD, OIL, SILVER, etc.)

            4. TECHNICAL INDICATORS (Priority: Medium):
               - RSI values and overbought/oversold conditions
               - MACD signals and crossovers
               - Moving Average values and golden/death crosses
               - Volume indicators and volume analysis
               - Bollinger Bands positions
               - Stochastic indicators

            5. CHART ANALYSIS (Priority: Medium):
               - Trend direction (bullish/bearish/sideways)
               - Timeframes (1m, 5m, 15m, 30m, 1H, 4H, 1D, 1W)
               - Chart patterns (head & shoulders, triangles, flags, wedges)
               - Support and resistance zones
               - Breakout/breakdown levels

            6. TRADING CONTEXT (Priority: Low):
               - Market sentiment indicators
               - Risk management suggestions
               - Position sizing recommendations
               - Trading strategy context

            CRITICAL INSTRUCTIONS:
            - Extract ALL numbers, prices, and percentages accurately
            - Identify the exact trading symbol(s) mentioned
            - Determine clear BUY/SELL/HOLD signals
            - Be precise with price levels to 2 decimal places
            - Assign confidence scores based on signal clarity

            Provide the analysis in this EXACT JSON format:
            {
                "signals_detected": true/false,
                "action": "BUY/SELL/HOLD",
                "symbol": "EXACT_SYMBOL",
                "price": exact_current_price,
                "target_price": target_level,
                "stop_loss": stop_loss_level,
                "support_levels": [price1, price2, price3],
                "resistance_levels": [price1, price2, price3],
                "confidence": 0.0-1.0,
                "timeframe": "timeframe_detected",
                "technical_analysis": {
                    "trend": "bullish/bearish/sideways",
                    "indicators": ["indicator1", "indicator2"],
                    "patterns": ["pattern1", "pattern2"],
                    "rsi": rsi_value,
                    "macd": "macd_signal"
                },
                "market_context": {
                    "sentiment": "bullish/bearish/neutral",
                    "volume_analysis": "volume_description",
                    "key_events": "relevant_events"
                },
                "extracted_text": "all_readable_text_from_image",
                "analysis_summary": "brief_trading_opportunity_summary",
                "risk_level": "LOW/MEDIUM/HIGH"
            }

            If no clear trading signals are found, set signals_detected to false and explain why.
            """

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": "gpt-4o",  # GPT-4V with vision capabilities
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
                                    "url": f"data:image/jpeg;base64,{base64_image}",
                                    "detail": "high"  # High detail for better analysis
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 2000,
                "temperature": 0.1  # Low temperature for consistent analysis
            }

            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=45  # Longer timeout for image processing
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

                        # Validate required fields
                        if not trading_analysis.get("signals_detected", False):
                            trading_analysis["action"] = "HOLD"

                        return trading_analysis
                    else:
                        # Fallback: extract key information manually
                        return {
                            "success": True,
                            "signals_detected": False,
                            "extracted_text": content,
                            "analysis_summary": "Could not parse structured trading data from image",
                            "action": "HOLD"
                        }
                except json.JSONDecodeError:
                    return {
                        "success": True,
                        "signals_detected": False,
                        "extracted_text": content,
                        "analysis_summary": "Could not parse JSON response from GPT-4V",
                        "action": "HOLD"
                    }

            else:
                self.logger.error(f"❌ OpenAI API error: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"API error: {response.status_code}",
                    "details": response.text
                }

        except Exception as e:
            self.logger.error(f"❌ Error processing image with GPT-4V: {e}")
            return {
                "success": False,
                "error": str(e)
            }

class BraveTelegramScraperWithGPT4V:
    """Enhanced scraper with OpenAI GPT-4V capabilities"""

    def __init__(self, openai_api_key: str):
        self.driver = None
        self.browser_path = self._find_brave_browser()
        self.user_data_dir = self._find_brave_user_data()
        self.channel_url = "https://web.telegram.org/k/#-2127259353"
        self.signals = []
        self.image_signals = []

        # Initialize OpenAI Vision processor
        self.vision_processor = OpenAIVisionProcessor(openai_api_key)

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

    def extract_historical_data(self, days_back: int = 7) -> Tuple[List[str], List[str]]:
        """Extract messages and images from the last N days"""
        messages = []
        image_paths = []

        try:
            logger.info(f"📜 Extracting historical data from last {days_back} days...")

            # Calculate scroll amount for 7 days (approximate)
            scroll_iterations = min(days_back * 10, 50)  # Cap at 50 scrolls
            logger.info(f"🔄 Performing {scroll_iterations} scroll operations to load historical data...")

            for i in range(scroll_iterations):
                logger.info(f"📜 Scrolling up... ({i+1}/{scroll_iterations})")

                # Scroll to top of chat
                self.driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(1.5)

                # Also try to click "Load more" if it appears
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
                    if (text and len(text) > 10 and
                        text not in seen_messages and
                        not text.startswith('[') and
                        any(keyword in text.lower() for keyword in ['buy', 'sell', 'trade', 'price', 'signal', 'btc', 'eth'])):

                        seen_messages.add(text)
                        messages.append(text)
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

            logger.info(f"✅ Extraction complete: {len(messages)} messages, {len(image_paths)} images")
            return messages, image_paths

        except Exception as e:
            logger.error(f"❌ Error extracting historical data: {e}")
            return [], []

    def process_images_with_gpt4v(self, image_paths: List[str]) -> List[Dict]:
        """Process downloaded images with OpenAI GPT-4V"""
        image_signals = []

        logger.info(f"🔍 Processing {len(image_paths)} images with GPT-4V...")

        for i, image_path in enumerate(image_paths):
            try:
                logger.info(f"🖼️  Processing image {i+1}/{len(image_paths)}: {os.path.basename(image_path)}")

                # Process with GPT-4V
                vision_result = self.vision_processor.extract_trading_signals_from_image(image_path)

                if vision_result.get("success", False):
                    if vision_result.get("signals_detected", False):
                        # Extract trading signal
                        signal_data = {
                            'timestamp': datetime.now().isoformat(),
                            'source': 'gpt4v_vision',
                            'image_path': image_path,
                            'action': vision_result.get('action', 'HOLD'),
                            'symbol': vision_result.get('symbol'),
                            'price': vision_result.get('price'),
                            'target_price': vision_result.get('target_price'),
                            'stop_loss': vision_result.get('stop_loss'),
                            'support_levels': vision_result.get('support_levels', []),
                            'resistance_levels': vision_result.get('resistance_levels', []),
                            'confidence': vision_result.get('confidence', 0.0),
                            'timeframe': vision_result.get('timeframe'),
                            'technical_analysis': vision_result.get('technical_analysis', {}),
                            'market_context': vision_result.get('market_context', {}),
                            'risk_level': vision_result.get('risk_level', 'UNKNOWN'),
                            'extracted_text': vision_result.get('extracted_text', ''),
                            'analysis_summary': vision_result.get('analysis_summary', ''),
                            'raw_response': vision_result.get('raw_response', '')
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
                    logger.error(f"❌ GPT-4V failed for image: {os.path.basename(image_path)}")
                    logger.error(f"   Error: {vision_result.get('error', 'Unknown error')}")

                # Add delay between API calls to respect rate limits
                time.sleep(2)

            except Exception as e:
                logger.error(f"❌ Error processing image {image_path}: {e}")
                continue

        logger.info(f"🎯 Found {len(image_signals)} trading signals from images")
        return image_signals

    def _log_image_signal(self, signal: Dict):
        """Log an image-based trading signal"""
        logger.info("🎯 GPT-4V TRADING SIGNAL DETECTED:")
        logger.info(f"   Action: {signal['action']}")
        logger.info(f"   Symbol: {signal['symbol']}")
        logger.info(f"   Price: ${signal['price']}" if signal['price'] else "   Price: Not specified")
        logger.info(f"   Target: ${signal['target_price']}" if signal.get('target_price') else "   Target: Not specified")
        logger.info(f"   Stop Loss: ${signal['stop_loss']}" if signal.get('stop_loss') else "   Stop Loss: Not specified")
        logger.info(f"   Confidence: {signal['confidence']:.2f}")
        logger.info(f"   Timeframe: {signal.get('timeframe', 'N/A')}")
        logger.info(f"   Risk Level: {signal.get('risk_level', 'N/A')}")
        logger.info(f"   Analysis: {signal.get('analysis_summary', 'N/A')[:100]}...")

    def analyze_text_signals(self, messages: List[str]) -> List[Dict]:
        """Analyze text messages for trading signals"""
        signals = []

        # Trading signal patterns
        buy_patterns = [
            r'(?i)(buy|long|enter).*?(btc|eth|aapl|tsla|eur/usd|gold|spy|sol|bnb)',
            r'(?i)(buy signal|entry point|go long|long position)',
            r'(?i)(🟢|✅|🚀|📈).*?(buy|enter|long)',
            r'(?i)(bullish|uptrend|breakout).*?(buy|enter)'
        ]

        sell_patterns = [
            r'(?i)(sell|short|exit).*?(btc|eth|aapl|tsla|eur/usd|gold|spy|sol|bnb)',
            r'(?i)(sell signal|exit point|go short|short position)',
            r'(?i)(🔴|❌|📉).*?(sell|exit|short)',
            r'(?i)(bearish|downtrend|breakdown).*?(sell|exit)'
        ]

        trading_symbols = ['BTC', 'ETH', 'AAPL', 'TSLA', 'EUR/USD', 'GOLD', 'SPY', 'SOL', 'BNB', 'ADA', 'DOT']

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

    def analyze_historical_data(self, days_back: int = 7):
        """Analyze historical data from the last N days"""
        logger.info(f"🚀 Starting historical analysis for last {days_back} days...")

        start_time = datetime.now()
        all_text_signals = []
        all_image_signals = []

        try:
            # Extract historical data
            messages, image_paths = self.extract_historical_data(days_back)

            # Analyze text signals
            if messages:
                logger.info("📊 Analyzing text messages...")
                all_text_signals = self.analyze_text_signals(messages)

            # Analyze images with GPT-4V
            if image_paths:
                logger.info("🖼️  Analyzing images with GPT-4V...")
                all_image_signals = self.process_images_with_gpt4v(image_paths)

            # Generate comprehensive report
            self._generate_comprehensive_report(all_text_signals, all_image_signals, days_back, start_time)

        except Exception as e:
            logger.error(f"❌ Error during historical analysis: {e}")
        finally:
            self.cleanup()

    def _generate_comprehensive_report(self, text_signals: List[Dict], image_signals: List[Dict], days_analyzed: int, start_time: datetime):
        """Generate comprehensive analysis report"""
        logger.info("📋 GENERATING COMPREHENSIVE ANALYSIS REPORT")

        analysis_duration = (datetime.now() - start_time).total_seconds()

        # Text signal statistics
        text_buy = len([s for s in text_signals if s['action'] == 'BUY'])
        text_sell = len([s for s in text_signals if s['action'] == 'SELL'])
        text_avg_confidence = sum(s['confidence'] for s in text_signals) / len(text_signals) if text_signals else 0

        # Image signal statistics
        image_buy = len([s for s in image_signals if s['action'] == 'BUY'])
        image_sell = len([s for s in image_signals if s['action'] == 'SELL'])
        image_avg_confidence = sum(s['confidence'] for s in image_signals) / len(image_signals) if image_signals else 0

        # Symbol analysis
        all_symbols = []
        for signal in text_signals + image_signals:
            if signal.get('symbol'):
                all_symbols.append(signal['symbol'])
        symbol_frequency = {symbol: all_symbols.count(symbol) for symbol in set(all_symbols)}

        # Timeframe analysis
        timeframes = []
        for signal in image_signals:
            if signal.get('timeframe'):
                timeframes.append(signal['timeframe'])
        timeframe_frequency = {tf: timeframes.count(tf) for tf in set(timeframes)}

        # Risk analysis
        risk_levels = []
        for signal in image_signals:
            if signal.get('risk_level'):
                risk_levels.append(signal['risk_level'])
        risk_distribution = {risk: risk_levels.count(risk) for risk in set(risk_levels)}

        # Price level analysis
        all_prices = []
        for signal in text_signals + image_signals:
            if signal.get('price'):
                all_prices.append(signal['price'])

        avg_price = sum(all_prices) / len(all_prices) if all_prices else 0
        min_price = min(all_prices) if all_prices else 0
        max_price = max(all_prices) if all_prices else 0

        # Trend analysis
        trends = []
        for signal in image_signals:
            if signal.get('technical_analysis', {}).get('trend'):
                trends.append(signal['technical_analysis']['trend'])
        trend_distribution = {trend: trends.count(trend) for trend in set(trends)}

        comprehensive_report = {
            'analysis_metadata': {
                'analysis_date': datetime.now().isoformat(),
                'period_analyzed': f"last_{days_analyzed}_days",
                'analysis_duration_seconds': analysis_duration,
                'total_messages_processed': len(text_signals) + len(image_signals),
                'scraper_version': 'GPT-4V Enhanced v1.0'
            },
            'signal_summary': {
                'total_signals': len(text_signals) + len(image_signals),
                'text_signals': {
                    'total': len(text_signals),
                    'buy_signals': text_buy,
                    'sell_signals': text_sell,
                    'avg_confidence': round(text_avg_confidence, 3)
                },
                'image_signals': {
                    'total': len(image_signals),
                    'buy_signals': image_buy,
                    'sell_signals': image_sell,
                    'avg_confidence': round(image_avg_confidence, 3)
                }
            },
            'symbol_analysis': {
                'most_traded_symbols': dict(sorted(symbol_frequency.items(), key=lambda x: x[1], reverse=True)[:10]),
                'symbol_count': len(symbol_frequency),
                'diverse_symbols': len(symbol_frequency) > 5
            },
            'price_analysis': {
                'average_price': round(avg_price, 2),
                'min_price': round(min_price, 2),
                'max_price': round(max_price, 2),
                'price_volatility': round((max_price - min_price) / avg_price * 100, 2) if avg_price > 0 else 0,
                'total_price_points': len(all_prices)
            },
            'technical_analysis': {
                'trend_distribution': trend_distribution,
                'dominant_trend': max(trend_distribution.items(), key=lambda x: x[1])[0] if trend_distribution else 'UNKNOWN',
                'timeframe_distribution': timeframe_frequency,
                'most_common_timeframe': max(timeframe_distribution.items(), key=lambda x: x[1])[0] if timeframe_frequency else 'UNKNOWN'
            },
            'risk_analysis': {
                'risk_distribution': risk_distribution,
                'dominant_risk_level': max(risk_distribution.items(), key=lambda x: x[1])[0] if risk_distribution else 'UNKNOWN',
                'high_risk_signals': risk_distribution.get('HIGH', 0),
                'low_risk_signals': risk_distribution.get('LOW', 0)
            },
            'quality_metrics': {
                'high_confidence_signals': len([s for s in (text_signals + image_signals) if s.get('confidence', 0) > 0.8]),
                'medium_confidence_signals': len([s for s in (text_signals + image_signals) if 0.6 <= s.get('confidence', 0) <= 0.8]),
                'overall_signal_quality': 'HIGH' if (text_avg_confidence + image_avg_confidence) / 2 > 0.75 else 'MEDIUM' if (text_avg_confidence + image_avg_confidence) / 2 > 0.6 else 'LOW'
            },
            'insights': self._generate_insights(text_signals, image_signals, symbol_frequency, trend_distribution),
            'recommendations': self._generate_recommendations(text_signals, image_signals),
            'detailed_signals': {
                'text_signals': text_signals,
                'image_signals': image_signals
            }
        }

        # Save comprehensive report
        report_filename = f"comprehensive_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w') as f:
            json.dump(comprehensive_report, f, indent=2, default=str)

        # Save individual signal files
        text_signals_filename = f"text_signals_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(text_signals_filename, 'w') as f:
            json.dump(text_signals, f, indent=2, default=str)

        image_signals_filename = f"image_signals_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(image_signals_filename, 'w') as f:
            json.dump(image_signals, f, indent=2, default=str)

        # Print summary
        self._print_analysis_summary(comprehensive_report, report_filename)

        return comprehensive_report

    def _generate_insights(self, text_signals: List[Dict], image_signals: List[Dict], symbol_frequency: Dict, trend_distribution: Dict):
        """Generate analytical insights"""
        insights = []

        # Signal volume insights
        total_signals = len(text_signals) + len(image_signals)
        if total_signals > 50:
            insights.append("📈 High signal volume detected - Active trading community")
        elif total_signals > 20:
            insights.append("📊 Moderate signal volume - Steady trading recommendations")
        else:
            insights.append("📉 Low signal volume - Limited trading activity")

        # Symbol insights
        if symbol_frequency:
            top_symbol = max(symbol_frequency.items(), key=lambda x: x[1])
            insights.append(f"🎯 Most traded symbol: {top_symbol[0]} ({top_symbol[1]} signals)")

            if len(symbol_frequency) > 10:
                insights.append("🌐 Highly diversified symbol coverage across multiple markets")
            elif len(symbol_frequency) > 5:
                insights.append("📊 Moderate diversification across key trading symbols")
            else:
                insights.append("🔍 Focused on few high-priority trading symbols")

        # Trend insights
        if trend_distribution:
            dominant_trend = max(trend_distribution.items(), key=lambda x: x[1])
            if dominant_trend[0] == 'bullish':
                insights.append(f"🚀 Dominant bullish sentiment detected ({dominant_trend[1]} bullish signals)")
            elif dominant_trend[0] == 'bearish':
                insights.append(f"📉 Dominant bearish sentiment detected ({dominant_trend[1]} bearish signals)")
            else:
                insights.append(f"⚖️  Mixed/Neutral market sentiment ({dominant_trend[1]} neutral signals)")

        # Source insights
        if len(image_signals) > len(text_signals):
            insights.append("🖼️  Image-based signals dominate - Visual chart analysis is primary")
        elif len(text_signals) > len(image_signals):
            insights.append("📝 Text-based signals dominate - Direct recommendations are primary")
        else:
            insights.append("🔄 Balanced mix of text and image-based signals")

        # Confidence insights
        avg_confidence = (sum(s.get('confidence', 0) for s in text_signals + image_signals) /
                         len(text_signals + image_signals)) if (text_signals + image_signals) else 0

        if avg_confidence > 0.8:
            insights.append("💪 High confidence signals - Strong technical analysis quality")
        elif avg_confidence > 0.7:
            insights.append("👍 Good confidence levels - Reliable trading recommendations")
        else:
            insights.append("⚠️  Moderate confidence levels - Additional verification recommended")

        return insights

    def _generate_recommendations(self, text_signals: List[Dict], image_signals: List[Dict]):
        """Generate actionable recommendations"""
        recommendations = []

        # Signal quality recommendations
        high_conf_signals = [s for s in (text_signals + image_signals) if s.get('confidence', 0) > 0.8]
        if high_conf_signals:
            recommendations.append("🎯 PRIORITIZE: High-confidence signals (>80%) for immediate consideration")

        # Symbol-specific recommendations
        symbol_signals = {}
        for signal in text_signals + image_signals:
            symbol = signal.get('symbol')
            if symbol:
                if symbol not in symbol_signals:
                    symbol_signals[symbol] = []
                symbol_signals[symbol].append(signal)

        # Find symbols with strong signals
        strong_symbols = []
        for symbol, signals in symbol_signals.items():
            if len(signals) >= 3:  # Multiple signals for same symbol
                avg_confidence = sum(s.get('confidence', 0) for s in signals) / len(signals)
                if avg_confidence > 0.7:
                    strong_symbols.append(symbol)

        if strong_symbols:
            recommendations.append(f"💎 FOCUS SYMBOLS: {', '.join(strong_symbols)} - Multiple high-quality signals")

        # Risk management recommendations
        buy_signals = len([s for s in (text_signals + image_signals) if s.get('action') == 'BUY'])
        sell_signals = len([s for s in (text_signals + image_signals) if s.get('action') == 'SELL'])

        if buy_signals > sell_signals * 1.5:
            recommendations.append("📊 MARKET SENTIMENT: Strong bullish bias - Consider long positions")
        elif sell_signals > buy_signals * 1.5:
            recommendations.append("📉 MARKET SENTIMENT: Strong bearish bias - Consider short positions or cash")
        else:
            recommendations.append("⚖️  MARKET SENTIMENT: Balanced signals - Maintain diversified portfolio")

        # Technical analysis recommendations
        image_ta_signals = [s for s in image_signals if s.get('technical_analysis')]
        if image_ta_signals:
            recommendations.append("📈 TECHNICAL ANALYSIS: Image-based signals provide detailed TA - Use for entry/exit timing")

        # Monitoring recommendations
        if len(text_signals + image_signals) > 0:
            recommendations.append("🔍 MONITORING: Set up alerts for these symbols to catch future signals")
            recommendations.append("⏰ TIMING: Consider the timeframes mentioned in signals for optimal entry")

        # Risk management
        recommendations.append("🛡️  RISK MANAGEMENT: Always verify signals with multiple sources before trading")
        recommendations.append("💰 POSITION SIZING: Use appropriate position sizing based on signal confidence")

        return recommendations

    def _print_analysis_summary(self, report: Dict, report_filename: str):
        """Print a concise analysis summary"""
        logger.info("\n" + "="*80)
        logger.info("📊 COMPREHENSIVE TRADING ANALYSIS SUMMARY")
        logger.info("="*80)

        summary = report['signal_summary']
        logger.info(f"\n📈 SIGNAL OVERVIEW:")
        logger.info(f"   Total Signals: {summary['total_signals']}")
        logger.info(f"   Text Signals: {summary['text_signals']['total']} (Buy: {summary['text_signals']['buy_signals']}, Sell: {summary['text_signals']['sell_signals']})")
        logger.info(f"   Image Signals: {summary['image_signals']['total']} (Buy: {summary['image_signals']['buy_signals']}, Sell: {summary['image_signals']['sell_signals']})")

        symbol_analysis = report['symbol_analysis']
        if symbol_analysis['most_traded_symbols']:
            logger.info(f"\n🎯 TOP TRADED SYMBOLS:")
            for symbol, count in list(symbol_analysis['most_traded_symbols'].items())[:5]:
                logger.info(f"   {symbol}: {count} signals")

        technical = report['technical_analysis']
        if technical['dominant_trend'] != 'UNKNOWN':
            logger.info(f"\n📊 MARKET TRENDS:")
            logger.info(f"   Dominant Trend: {technical['dominant_trend'].upper()}")
            logger.info(f"   Common Timeframe: {technical['most_common_timeframe']}")

        price_analysis = report['price_analysis']
        if price_analysis['total_price_points'] > 0:
            logger.info(f"\n💰 PRICE ANALYSIS:")
            logger.info(f"   Average Price: ${price_analysis['average_price']:,.2f}")
            logger.info(f"   Price Range: ${price_analysis['min_price']:,.2f} - ${price_analysis['max_price']:,.2f}")
            logger.info(f"   Volatility: {price_analysis['price_volatility']:.1f}%")

        quality = report['quality_metrics']
        logger.info(f"\n📊 SIGNAL QUALITY:")
        logger.info(f"   High Confidence: {quality['high_confidence_signals']} signals")
        logger.info(f"   Medium Confidence: {quality['medium_confidence_signals']} signals")
        logger.info(f"   Overall Quality: {quality['overall_signal_quality']}")

        # Top insights
        logger.info(f"\n💡 KEY INSIGHTS:")
        for insight in report['insights'][:5]:
            logger.info(f"   {insight}")

        # Top recommendations
        logger.info(f"\n🎯 KEY RECOMMENDATIONS:")
        for recommendation in report['recommendations'][:5]:
            logger.info(f"   {recommendation}")

        logger.info(f"\n📁 DETAILED REPORTS:")
        logger.info(f"   Main Report: {report_filename}")
        logger.info(f"   Text Signals: text_signals_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        logger.info(f"   Image Signals: image_signals_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")

        logger.info(f"\n⏱️  Analysis completed in {report['analysis_metadata']['analysis_duration_seconds']:.1f} seconds")
        logger.info("="*80)

    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            logger.info("🌐 Keeping Brave browser open for your continued use")

def main():
    """Main execution function"""
    logger.info("🚀 BRAVE TELEGRAM SCRAPER WITH OPENAI GPT-4V VISION")
    logger.info("=" * 70)

    # Get OpenAI API key from environment
    openai_api_key = os.getenv('OPENAI_API_KEY')
    if not openai_api_key:
        logger.error("❌ OPENAI_API_KEY environment variable not set")
        logger.info("Please set your OpenAI API key:")
        logger.info("export OPENAI_API_KEY='your-openai-api-key-here'")
        return

    scraper = None
    try:
        # Initialize scraper with OpenAI GPT-4V
        scraper = BraveTelegramScraperWithGPT4V(openai_api_key)

        # Connect to Brave browser
        if not scraper.connect_to_brave():
            logger.error("❌ Failed to connect to Brave browser")
            return

        # Navigate to channel
        if not scraper.navigate_to_channel():
            logger.error("❌ Failed to navigate to channel")
            return

        # Analyze historical data (last 7 days)
        scraper.analyze_historical_data(days_back=7)

    except KeyboardInterrupt:
        logger.info("⏹️  Analysis stopped by user")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
    finally:
        if scraper:
            scraper.cleanup()
        logger.info("🏁 Historical analysis completed")

if __name__ == "__main__":
    main()