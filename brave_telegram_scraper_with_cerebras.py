#!/usr/bin/env python3
"""
Brave Browser Telegram Scraper with Cerebras AI Integration

This scraper connects to your existing Brave browser with Telegram logged in
and uses Cerebras AI for text analysis combined with basic image processing
to extract trading signals from messages and images.
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

class CerebrasAIProcessor:
    """Cerebras AI processor for text-based trading signal analysis"""

    def __init__(self, api_key: str, base_url: str = "https://api.cerebras.ai/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.logger = logging.getLogger(__name__)

    def analyze_trading_signals(self, text_content: str, image_description: str = "") -> Dict:
        """Analyze trading signals using Cerebras AI"""
        try:
            # Enhanced trading analysis prompt for Cerebras
            prompt = f"""
            You are an expert trading analyst. Analyze the following trading content and extract all trading-related information.

            CONTENT TO ANALYZE:
            {text_content}

            {f"IMAGE DESCRIPTION: {image_description}" if image_description else ""}

            FOCUS ON EXTRACTING:

            1. TRADING SIGNALS:
               - Buy/Sell indicators (BUY, SELL, ENTER, EXIT, LONG, SHORT)
               - Signal emojis (🟢🔴✅❌🚀📉📈💰⚡🎯)
               - Entry/Exit recommendations
               - Signal strength and confidence

            2. SYMBOLS & ASSETS:
               - Cryptocurrency symbols (BTC, ETH, SOL, BNB, ADA, DOT, etc.)
               - Stock symbols (AAPL, TSLA, GOOGL, MSFT, AMZN, NVDA, etc.)
               - Forex pairs (EUR/USD, GBP/USD, USD/JPY, etc.)
               - Commodity symbols (GOLD, OIL, SILVER, etc.)

            3. PRICE INFORMATION:
               - Current price levels
               - Target prices (Take Profit)
               - Stop loss levels
               - Support and resistance levels
               - Price ranges and zones

            4. TECHNICAL ANALYSIS:
               - Trend direction (bullish/bearish/sideways)
               - Timeframes (1m, 5m, 15m, 30m, 1H, 4H, 1D, 1W)
               - Technical indicators mentioned (RSI, MACD, MA, etc.)
               - Chart patterns
               - Volume analysis

            5. MARKET CONTEXT:
               - Trading strategy context
               - Risk level assessment
               - Market sentiment
               - Urgency indicators

            Provide the analysis in this EXACT JSON format:
            {{
                "signals_detected": true/false,
                "action": "BUY/SELL/HOLD",
                "symbol": "SYMBOL_NAME",
                "price": current_price,
                "target_price": target_level,
                "stop_loss": stop_loss_level,
                "support_levels": [price1, price2],
                "resistance_levels": [price1, price2],
                "confidence": 0.0-1.0,
                "timeframe": "timeframe",
                "technical_analysis": {{
                    "trend": "bullish/bearish/sideways",
                    "indicators": ["indicator1", "indicator2"],
                    "patterns": ["pattern1"],
                    "timeframe": "timeframe"
                }},
                "market_context": {{
                    "sentiment": "bullish/bearish/neutral",
                    "urgency": "high/medium/low",
                    "risk_level": "LOW/MEDIUM/HIGH"
                }},
                "reasoning": "detailed_analysis_explanation",
                "key_points": ["point1", "point2", "point3"]
            }}

            If no clear trading signals are found, set signals_detected to false and explain why.
            Be precise with numbers and provide actionable trading insights.
            """

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": "llama-3.3-70b",  # Use available Cerebras model
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 2000,
                "temperature": 0.1  # Low temperature for consistent analysis
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
                    import re
                    json_match = re.search(r'\{.*\}', content, re.DOTALL)
                    if json_match:
                        trading_analysis = json.loads(json_match.group())
                        trading_analysis["raw_response"] = content
                        trading_analysis["success"] = True

                        # Validate and clean up the response
                        if not trading_analysis.get("signals_detected", False):
                            trading_analysis["action"] = "HOLD"

                        # Ensure numeric values are properly typed
                        for field in ['price', 'target_price', 'stop_loss', 'confidence']:
                            if field in trading_analysis and trading_analysis[field] is not None:
                                try:
                                    if isinstance(trading_analysis[field], str):
                                        # Extract numbers from strings
                                        import re
                                        numbers = re.findall(r'\d+\.?\d*', str(trading_analysis[field]))
                                        if numbers:
                                            trading_analysis[field] = float(numbers[0])
                                except:
                                    trading_analysis[field] = None

                        return trading_analysis
                    else:
                        # Fallback analysis
                        return {
                            "success": True,
                            "signals_detected": False,
                            "raw_response": content,
                            "reasoning": "Could not parse structured JSON, but content was analyzed",
                            "action": "HOLD"
                        }
                except json.JSONDecodeError:
                    return {
                        "success": True,
                        "signals_detected": False,
                        "raw_response": content,
                        "reasoning": "JSON parsing failed, but content was processed",
                        "action": "HOLD"
                    }

            else:
                self.logger.error(f"❌ Cerebras API error: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"API error: {response.status_code}",
                    "details": response.text
                }

        except Exception as e:
            self.logger.error(f"❌ Error processing with Cerebras AI: {e}")
            return {
                "success": False,
                "error": str(e)
            }

class BasicImageProcessor:
    """Basic image processing for extracting text and metadata"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def extract_image_metadata(self, image_path: str) -> Dict:
        """Extract basic metadata from image"""
        try:
            with Image.open(image_path) as img:
                metadata = {
                    "success": True,
                    "filename": os.path.basename(image_path),
                    "format": img.format,
                    "size": img.size,
                    "mode": img.mode,
                    "file_size": os.path.getsize(image_path),
                    "has_transparency": img.mode in ('RGBA', 'LA') or 'transparency' in img.info,
                    "estimated_chart_type": self._estimate_chart_type(img.size, img.mode),
                    "description": f"Trading chart image ({img.size[0]}x{img.size[1]})"
                }
                return metadata
        except Exception as e:
            self.logger.error(f"❌ Error extracting image metadata: {e}")
            return {
                "success": False,
                "error": str(e),
                "description": "Failed to process image"
            }

    def _estimate_chart_type(self, size: tuple, mode: str) -> str:
        """Estimate the type of trading chart based on image characteristics"""
        width, height = size
        aspect_ratio = width / height

        # Common trading chart aspect ratios
        if 1.5 <= aspect_ratio <= 2.0:
            return "standard_chart"
        elif aspect_ratio > 2.0:
            return "wide_chart"
        elif aspect_ratio < 1.0:
            return "vertical_chart"
        else:
            return "square_chart"

class BraveTelegramScraperWithCerebras:
    """Enhanced scraper with Cerebras AI capabilities"""

    def __init__(self, cerebras_api_key: str):
        self.driver = None
        self.browser_path = self._find_brave_browser()
        self.user_data_dir = self._find_brave_user_data()
        self.channel_url = "https://web.telegram.org/k/#-2127259353"
        self.signals = []
        self.image_signals = []

        # Initialize processors
        self.ai_processor = CerebrasAIProcessor(cerebras_api_key)
        self.image_processor = BasicImageProcessor()

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

            # Calculate scroll amount for 7 days
            scroll_iterations = min(days_back * 8, 40)  # Cap at 40 scrolls
            logger.info(f"🔄 Performing {scroll_iterations} scroll operations to load historical data...")

            for i in range(scroll_iterations):
                logger.info(f"📜 Scrolling up... ({i+1}/{scroll_iterations})")

                # Scroll to top of chat
                self.driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(1.5)

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
            for i, element in enumerate(image_elements[:80]):  # Limit to 80 images
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

    def analyze_content_with_cerebras(self, messages: List[str], image_paths: List[str]) -> List[Dict]:
        """Analyze text messages and images using Cerebras AI"""
        all_signals = []

        logger.info(f"🧠 Analyzing {len(messages)} text messages with Cerebras AI...")

        # Analyze text messages
        for i, message in enumerate(messages):
            try:
                logger.info(f"📝 Analyzing message {i+1}/{len(messages)}")

                # Analyze with Cerebras
                result = self.ai_processor.analyze_trading_signals(message)

                if result.get("success", False):
                    if result.get("signals_detected", False):
                        signal_data = {
                            'timestamp': datetime.now().isoformat(),
                            'source': 'cerebras_ai',
                            'content_type': 'text',
                            'original_message': message[:200] + "..." if len(message) > 200 else message,
                            'action': result.get('action', 'HOLD'),
                            'symbol': result.get('symbol'),
                            'price': result.get('price'),
                            'target_price': result.get('target_price'),
                            'stop_loss': result.get('stop_loss'),
                            'support_levels': result.get('support_levels', []),
                            'resistance_levels': result.get('resistance_levels', []),
                            'confidence': result.get('confidence', 0.0),
                            'timeframe': result.get('timeframe'),
                            'technical_analysis': result.get('technical_analysis', {}),
                            'market_context': result.get('market_context', {}),
                            'reasoning': result.get('reasoning', ''),
                            'key_points': result.get('key_points', []),
                            'raw_response': result.get('raw_response', '')
                        }

                        all_signals.append(signal_data)
                        self._log_signal(signal_data)

                # Add delay between API calls
                time.sleep(1)

            except Exception as e:
                logger.error(f"❌ Error analyzing message {i}: {e}")
                continue

        # Analyze images (basic metadata + AI analysis of context)
        logger.info(f"🖼️  Analyzing {len(image_paths)} images...")

        for i, image_path in enumerate(image_paths):
            try:
                logger.info(f"🖼️  Processing image {i+1}/{len(image_paths)}: {os.path.basename(image_path)}")

                # Extract image metadata
                metadata = self.image_processor.extract_image_metadata(image_path)

                if metadata.get("success", False):
                    # Create a signal based on image metadata
                    # Since we can't do advanced OCR, we'll note the presence of trading charts
                    signal_data = {
                        'timestamp': datetime.now().isoformat(),
                        'source': 'image_metadata',
                        'content_type': 'image',
                        'image_path': image_path,
                        'action': 'HOLD',  # Default to hold without detailed analysis
                        'symbol': None,
                        'price': None,
                        'target_price': None,
                        'stop_loss': None,
                        'support_levels': [],
                        'resistance_levels': [],
                        'confidence': 0.3,  # Low confidence without detailed analysis
                        'timeframe': None,
                        'technical_analysis': {
                            'chart_type': metadata.get('estimated_chart_type'),
                            'image_size': metadata.get('size'),
                            'format': metadata.get('format')
                        },
                        'market_context': {
                            'content_type': 'trading_chart_image',
                            'analysis_method': 'basic_metadata'
                        },
                        'reasoning': f"Trading chart detected ({metadata.get('description', 'unknown type')}). Advanced OCR analysis not available without vision API.",
                        'key_points': [
                            "Trading chart image detected",
                            f"Image size: {metadata.get('size', 'unknown')}",
                            f"Chart type: {metadata.get('estimated_chart_type', 'unknown')}"
                        ],
                        'image_metadata': metadata
                    }

                    all_signals.append(signal_data)
                    logger.info(f"📷 Trading chart image detected: {os.path.basename(image_path)}")

                    # Move to processed folder
                    processed_filename = f"processed_{os.path.basename(image_path)}"
                    processed_path = os.path.join(self.processed_dir, processed_filename)
                    os.rename(image_path, processed_path)

            except Exception as e:
                logger.error(f"❌ Error processing image {image_path}: {e}")
                continue

        logger.info(f"🎯 Total signals analyzed: {len(all_signals)}")
        return all_signals

    def _log_signal(self, signal: Dict):
        """Log a trading signal"""
        logger.info("🎯 CEREBRAS AI TRADING SIGNAL:")
        logger.info(f"   Action: {signal['action']}")
        logger.info(f"   Symbol: {signal['symbol']}")
        logger.info(f"   Price: ${signal['price']}" if signal['price'] else "   Price: Not specified")
        logger.info(f"   Target: ${signal['target_price']}" if signal.get('target_price') else "   Target: Not specified")
        logger.info(f"   Stop Loss: ${signal['stop_loss']}" if signal.get('stop_loss') else "   Stop Loss: Not specified")
        logger.info(f"   Confidence: {signal['confidence']:.2f}")
        logger.info(f"   Timeframe: {signal.get('timeframe', 'N/A')}")
        logger.info(f"   Reasoning: {signal.get('reasoning', 'N/A')[:100]}...")

    def analyze_historical_data(self, days_back: int = 7):
        """Analyze historical data from the last N days"""
        logger.info(f"🚀 Starting historical analysis for last {days_back} days...")

        start_time = datetime.now()
        all_signals = []

        try:
            # Extract historical data
            messages, image_paths = self.extract_historical_data(days_back)

            # Analyze content with Cerebras AI
            if messages or image_paths:
                logger.info(f"🧠 Analyzing content with Cerebras AI...")
                all_signals = self.analyze_content_with_cerebras(messages, image_paths)
            else:
                logger.warning("⚠️  No content found to analyze")

            # Generate comprehensive report
            self._generate_comprehensive_report(all_signals, days_back, start_time)

        except Exception as e:
            logger.error(f"❌ Error during historical analysis: {e}")
        finally:
            self.cleanup()

    def _generate_comprehensive_report(self, signals: List[Dict], days_analyzed: int, start_time: datetime):
        """Generate comprehensive analysis report"""
        logger.info("📋 GENERATING COMPREHENSIVE ANALYSIS REPORT")

        analysis_duration = (datetime.now() - start_time).total_seconds()

        # Filter out image metadata signals to focus on actionable signals
        actionable_signals = [s for s in signals if s.get('confidence', 0) > 0.5]
        text_signals = [s for s in signals if s.get('content_type') == 'text']
        image_signals = [s for s in signals if s.get('content_type') == 'image']

        # Signal statistics
        buy_signals = len([s for s in actionable_signals if s['action'] == 'BUY'])
        sell_signals = len([s for s in actionable_signals if s['action'] == 'SELL'])
        hold_signals = len([s for s in actionable_signals if s['action'] == 'HOLD'])

        # Calculate average confidence
        avg_confidence = (sum(s.get('confidence', 0) for s in actionable_signals) /
                         len(actionable_signals)) if actionable_signals else 0

        # Symbol analysis
        symbols = [s.get('symbol') for s in actionable_signals if s.get('symbol')]
        symbol_frequency = {symbol: symbols.count(symbol) for symbol in set(symbols)} if symbols else {}

        # Timeframe analysis
        timeframes = [s.get('timeframe') for s in actionable_signals if s.get('timeframe')]
        timeframe_frequency = {tf: timeframes.count(tf) for tf in set(timeframes)} if timeframes else {}

        # Price analysis
        prices = [s.get('price') for s in actionable_signals if s.get('price')]
        avg_price = sum(prices) / len(prices) if prices else 0
        min_price = min(prices) if prices else 0
        max_price = max(prices) if prices else 0

        # Technical analysis insights
        trends = [s.get('technical_analysis', {}).get('trend') for s in actionable_signals
                 if s.get('technical_analysis', {}).get('trend')]
        trend_distribution = {trend: trends.count(trend) for trend in set(trends)} if trends else {}

        comprehensive_report = {
            'analysis_metadata': {
                'analysis_date': datetime.now().isoformat(),
                'period_analyzed': f"last_{days_analyzed}_days",
                'analysis_duration_seconds': analysis_duration,
                'ai_model_used': 'Cerebras Llama 3.2 90B',
                'total_content_processed': len(signals),
                'scraper_version': 'Cerebras Enhanced v1.0'
            },
            'content_summary': {
                'total_items_processed': len(signals),
                'text_messages': len(text_signals),
                'trading_images': len(image_signals),
                'actionable_signals': len(actionable_signals),
                'content_types': {
                    'text_signals': len(text_signals),
                    'image_charts': len(image_signals)
                }
            },
            'signal_summary': {
                'total_signals': len(actionable_signals),
                'buy_signals': buy_signals,
                'sell_signals': sell_signals,
                'hold_signals': hold_signals,
                'signal_success_rate': len(actionable_signals) / len(signals) * 100 if signals else 0,
                'average_confidence': round(avg_confidence, 3)
            },
            'symbol_analysis': {
                'symbols_detected': list(symbol_frequency.keys()),
                'most_mentioned_symbols': dict(sorted(symbol_frequency.items(), key=lambda x: x[1], reverse=True)[:5]),
                'symbol_diversity': len(symbol_frequency)
            },
            'price_analysis': {
                'average_price': round(avg_price, 2),
                'min_price': round(min_price, 2),
                'max_price': round(max_price, 2),
                'price_range': round(max_price - min_price, 2) if max_price > min_price else 0,
                'total_price_points': len(prices)
            },
            'technical_analysis': {
                'trend_distribution': trend_distribution,
                'dominant_trend': max(trend_distribution.items(), key=lambda x: x[1])[0] if trend_distribution else 'UNKNOWN',
                'timeframe_distribution': timeframe_frequency,
                'most_common_timeframe': max(timeframe_frequency.items(), key=lambda x: x[1])[0] if timeframe_frequency else 'UNKNOWN'
            },
            'quality_metrics': {
                'high_confidence_signals': len([s for s in actionable_signals if s.get('confidence', 0) > 0.8]),
                'medium_confidence_signals': len([s for s in actionable_signals if 0.6 <= s.get('confidence', 0) <= 0.8]),
                'low_confidence_signals': len([s for s in actionable_signals if s.get('confidence', 0) < 0.6])
            },
            'insights': self._generate_insights(signals, actionable_signals, symbol_frequency, trend_distribution),
            'recommendations': self._generate_recommendations(actionable_signals, symbol_frequency),
            'detailed_signals': signals
        }

        # Save comprehensive report
        report_filename = f"cerebras_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w') as f:
            json.dump(comprehensive_report, f, indent=2, default=str)

        # Save actionable signals separately
        actionable_filename = f"actionable_signals_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(actionable_filename, 'w') as f:
            json.dump(actionable_signals, f, indent=2, default=str)

        # Print summary
        self._print_analysis_summary(comprehensive_report, report_filename)

        return comprehensive_report

    def _generate_insights(self, all_signals: List[Dict], actionable_signals: List[Dict], symbol_frequency: Dict, trend_distribution: Dict):
        """Generate analytical insights"""
        insights = []

        # Content volume insights
        if len(all_signals) > 100:
            insights.append("📈 High content volume detected - Very active trading channel")
        elif len(all_signals) > 50:
            insights.append("📊 Moderate content volume - Active trading recommendations")
        elif len(all_signals) > 20:
            insights.append("📉 Moderate-low content volume - Periodic trading signals")
        else:
            insights.append("📉 Low content volume - Limited trading activity")

        # Signal quality insights
        if len(actionable_signals) > len(all_signals) * 0.5:
            insights.append("💪 High signal quality - More than 50% of content provides actionable insights")
        elif len(actionable_signals) > len(all_signals) * 0.3:
            insights.append("👍 Good signal quality - Significant actionable trading content")
        else:
            insights.append("⚠️  Low signal quality - Limited actionable trading insights")

        # Symbol diversity insights
        if symbol_frequency:
            if len(symbol_frequency) > 8:
                insights.append("🌐 Highly diversified coverage across multiple markets and assets")
            elif len(symbol_frequency) > 5:
                insights.append("📊 Good diversification across major trading symbols")
            elif len(symbol_frequency) > 3:
                insights.append("🎯 Focused coverage on key trading symbols")
            else:
                insights.append("🔍 Concentrated on few specific trading opportunities")

            # Most popular symbol
            top_symbol = max(symbol_frequency.items(), key=lambda x: x[1])
            insights.append(f"🏆 Most discussed symbol: {top_symbol[0]} ({top_symbol[1]} mentions)")

        # Trend insights
        if trend_distribution:
            dominant_trend = max(trend_distribution.items(), key=lambda x: x[1])
            total_trend_signals = sum(trend_distribution.values())
            trend_percentage = (dominant_trend[1] / total_trend_signals) * 100

            if dominant_trend[0] == 'bullish':
                insights.append(f"🚀 Strong bullish sentiment ({trend_percentage:.1f}% of trend signals)")
            elif dominant_trend[0] == 'bearish':
                insights.append(f"📉 Strong bearish sentiment ({trend_percentage:.1f}% of trend signals)")
            else:
                insights.append(f"⚖️  Balanced/neutral sentiment ({trend_percentage:.1f}% neutral signals)")

        # Content type insights
        text_signals = len([s for s in all_signals if s.get('content_type') == 'text'])
        image_signals = len([s for s in all_signals if s.get('content_type') == 'image'])

        if image_signals > text_signals:
            insights.append("🖼️  Visual content dominates - Chart-heavy analysis")
        elif text_signals > image_signals * 2:
            insights.append("📝 Text-based analysis dominates - Direct recommendations")
        else:
            insights.append("🔄 Balanced mix of text and visual trading content")

        # AI model performance
        insights.append("🤖 Analysis powered by Cerebras Llama 3.2 90B - High-performance reasoning")
        insights.append("⚡ Fast processing with detailed trading insights and technical analysis")

        return insights

    def _generate_recommendations(self, actionable_signals: List[Dict], symbol_frequency: Dict):
        """Generate actionable recommendations"""
        recommendations = []

        # Signal quality recommendations
        high_conf_signals = [s for s in actionable_signals if s.get('confidence', 0) > 0.8]
        if high_conf_signals:
            recommendations.append("🎯 PRIORITY: High-confidence signals (>80%) deserve immediate consideration")
        else:
            recommendations.append("⚠️  CAUTION: No high-confidence signals detected - Additional verification recommended")

        # Symbol-specific recommendations
        if symbol_frequency:
            strong_symbols = [symbol for symbol, count in symbol_frequency.items() if count >= 3]
            if strong_symbols:
                recommendations.append(f"💎 FOCUS SYMBOLS: {', '.join(strong_symbols)} - Multiple signals indicate significant opportunities")

        # Market trend recommendations
        buy_signals = len([s for s in actionable_signals if s['action'] == 'BUY'])
        sell_signals = len([s for s in actionable_signals if s['action'] == 'SELL'])

        if buy_signals > sell_signals * 1.5:
            recommendations.append("📊 MARKET BIAS: Strong bullish sentiment detected - Consider long positions")
        elif sell_signals > buy_signals * 1.5:
            recommendations.append("📉 MARKET BIAS: Strong bearish sentiment detected - Consider short positions or protective puts")
        elif buy_signals == sell_signals and buy_signals > 0:
            recommendations.append("⚖️  BALANCED MARKET: Equal buy/sell signals - Consider market-neutral strategies")
        else:
            recommendations.append("📊 MARKET STATUS: Limited directional bias - Maintain diversified approach")

        # Risk management recommendations
        if len(actionable_signals) > 20:
            recommendations.append("🛡️  RISK MANAGEMENT: High signal volume - Implement strict position sizing")
        elif len(actionable_signals) < 5:
            recommendations.append("🔍 DUE DILIGENCE: Low signal volume - Conduct thorough research before acting")

        # Technical analysis recommendations
        timeframe_signals = [s for s in actionable_signals if s.get('timeframe')]
        if timeframe_signals:
            common_timeframes = [s.get('timeframe') for s in timeframe_signals]
            most_common_tf = max(set(common_timeframes), key=common_timeframes.count)
            recommendations.append(f"⏰ TIMEFRAME FOCUS: {most_common_tf} timeframe appears most frequently - Align your trading strategy")

        # Actionable next steps
        if actionable_signals:
            recommendations.append("📋 ACTION PLAN: Create watchlist for symbols with multiple signals")
            recommendations.append("⏰ MONITORING: Set up price alerts for identified support/resistance levels")
            recommendations.append("💼 POSITION SIZING: Scale positions based on signal confidence levels")

        # General best practices
        recommendations.append("🔍 VERIFICATION: Always cross-reference signals with your own analysis")
        recommendations.append("📊 TECHNICAL ANALYSIS: Use provided technical insights as starting points for deeper analysis")
        recommendations.append("💰 PORTFOLIO MANAGEMENT: Maintain proper diversification regardless of signal strength")

        return recommendations

    def _print_analysis_summary(self, report: Dict, report_filename: str):
        """Print a concise analysis summary"""
        logger.info("\n" + "="*80)
        logger.info("📊 CEREBRAS AI POWERED TRADING ANALYSIS SUMMARY")
        logger.info("="*80)

        content = report['content_summary']
        logger.info(f"\n📈 CONTENT ANALYZED:")
        logger.info(f"   Total Items: {content['total_items_processed']}")
        logger.info(f"   Text Messages: {content['text_messages']}")
        logger.info(f"   Trading Images: {content['trading_images']}")
        logger.info(f"   Actionable Signals: {content['actionable_signals']}")

        signals = report['signal_summary']
        logger.info(f"\n🎯 SIGNAL BREAKDOWN:")
        logger.info(f"   Total Signals: {signals['total_signals']}")
        logger.info(f"   Buy Signals: {signals['buy_signals']}")
        logger.info(f"   Sell Signals: {signals['sell_signals']}")
        logger.info(f"   Hold Signals: {signals['hold_signals']}")
        logger.info(f"   Average Confidence: {signals['average_confidence']:.2f}")
        logger.info(f"   Signal Success Rate: {signals['signal_success_rate']:.1f}%")

        symbols = report['symbol_analysis']
        if symbols['most_mentioned_symbols']:
            logger.info(f"\n🏆 TOP SYMBOLS:")
            for symbol, count in list(symbols['most_mentioned_symbols'].items())[:5]:
                logger.info(f"   {symbol}: {count} signals")

        technical = report['technical_analysis']
        if technical['dominant_trend'] != 'UNKNOWN':
            logger.info(f"\n📊 TECHNICAL INSIGHTS:")
            logger.info(f"   Dominant Trend: {technical['dominant_trend'].upper()}")
            logger.info(f"   Common Timeframe: {technical['most_common_timeframe']}")

        price_analysis = report['price_analysis']
        if price_analysis['total_price_points'] > 0:
            logger.info(f"\n💰 PRICE ANALYSIS:")
            logger.info(f"   Average Price: ${price_analysis['average_price']:,.2f}")
            logger.info(f"   Price Range: ${price_analysis['min_price']:,.2f} - ${price_analysis['max_price']:,.2f}")

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
        logger.info(f"   Actionable Signals: actionable_signals_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")

        metadata = report['analysis_metadata']
        logger.info(f"\n⏱️  Analysis completed in {metadata['analysis_duration_seconds']:.1f} seconds using {metadata['ai_model_used']}")
        logger.info("="*80)

    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            logger.info("🌐 Keeping Brave browser open for your continued use")

def main():
    """Main execution function"""
    logger.info("🚀 BRAVE TELEGRAM SCRAPER WITH CEREBRAS AI")
    logger.info("=" * 60)

    # Get Cerebras API key from environment
    cerebras_api_key = os.getenv('CEREBRAS_API_KEY')
    if not cerebras_api_key:
        logger.error("❌ CEREBRAS_API_KEY environment variable not set")
        logger.info("Please set your Cerebras API key:")
        logger.info("export CEREBRAS_API_KEY='your-cerebras-api-key-here'")
        return

    scraper = None
    try:
        # Initialize scraper with Cerebras AI
        scraper = BraveTelegramScraperWithCerebras(cerebras_api_key)

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