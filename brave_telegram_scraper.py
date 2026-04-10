#!/usr/bin/env python3
"""
Brave Browser Telegram Scraper - Uses Existing Logged-in Session

This script connects to your existing Brave browser with Telegram already logged in,
eliminating the need for manual authentication each time.
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
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BraveTelegramScraper:
    """Scraper that uses existing Brave browser session"""

    def __init__(self):
        self.driver = None
        self.browser_path = self._find_brave_browser()
        self.user_data_dir = self._find_brave_user_data()
        self.channel_url = "https://web.telegram.org/k/#-2127259353"
        self.signals = []

    def _find_brave_browser(self) -> Optional[str]:
        """Find Brave browser executable path"""
        possible_paths = [
            "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
            "/usr/bin/brave-browser",
            "/usr/local/bin/brave-browser",
            os.path.expanduser("~/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"),
        ]

        for path in possible_paths:
            if os.path.exists(path):
                logger.info(f"✅ Found Brave Browser at: {path}")
                return path

        # Try to find via system command
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

        logger.error("❌ Brave Browser not found. Please install Brave Browser.")
        return None

    def _find_brave_user_data(self) -> Optional[str]:
        """Find Brave browser user data directory"""
        possible_paths = [
            os.path.expanduser("~/Library/Application Support/BraveSoftware/Brave-Browser"),
            os.path.expanduser("~/Library/Application Support/Brave-Browser"),
            os.path.expanduser("~/.config/brave"),
        ]

        for path in possible_paths:
            if os.path.exists(path):
                logger.info(f"✅ Found Brave user data at: {path}")
                return path

        logger.error("❌ Brave user data directory not found")
        return None

    def _is_brave_running(self) -> bool:
        """Check if Brave browser is currently running"""
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if 'brave' in proc.info['name'].lower():
                    logger.info(f"✅ Found Brave browser running (PID: {proc.info['pid']})")
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False

    def _launch_brave_with_debugging(self):
        """Launch Brave browser with remote debugging enabled"""
        if self._is_brave_running():
            logger.info("🌐 Brave browser is already running")
            return

        logger.info("🚀 Launching Brave browser with remote debugging...")

        # Kill any existing Brave processes to ensure clean start
        try:
            subprocess.run(['pkill', '-f', 'Brave Browser'], check=False)
            time.sleep(2)
        except:
            pass

        # Launch Brave with remote debugging
        try:
            subprocess.Popen([
                self.browser_path,
                '--remote-debugging-port=9222',
                '--user-data-dir=' + self.user_data_dir,
                '--no-first-run',
                '--no-default-browser-check'
            ])

            # Wait for browser to start
            time.sleep(5)
            logger.info("✅ Brave browser launched successfully")
        except Exception as e:
            logger.error(f"❌ Failed to launch Brave browser: {e}")
            raise

    def connect_to_brave(self) -> bool:
        """Connect to existing Brave browser session"""
        try:
            # Launch Brave with debugging if not running
            self._launch_brave_with_debugging()

            # Connect to existing Brave browser
            chrome_options = Options()
            chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

            # Don't set any user data dir - we want to use existing session
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')

            self.driver = webdriver.Chrome(options=chrome_options)

            # Verify we're connected
            current_url = self.driver.current_url
            logger.info(f"✅ Connected to Brave browser. Current URL: {current_url}")

            return True

        except Exception as e:
            logger.error(f"❌ Failed to connect to Brave browser: {e}")
            return False

    def check_telegram_session(self) -> bool:
        """Check if Telegram is already logged in"""
        try:
            # Navigate to Telegram Web
            self.driver.get("https://web.telegram.org/k/")
            time.sleep(3)

            # Check if we're logged in by looking for chat list or auth elements
            try:
                # Look for chat list (indicates logged in)
                chat_list = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR,
                        ".chat-list, .chats-container, [class*='chat']"))
                )
                logger.info("✅ Telegram session found - already logged in!")
                return True
            except TimeoutException:
                # Check if login page is shown
                try:
                    login_element = self.driver.find_element(By.CSS_SELECTOR,
                        ".auth-form, .login-form, [class*='auth']")
                    logger.warning("⚠️  Telegram login page detected - please log in manually")
                    input("Press Enter after you've logged in to Telegram...")
                    return self.check_telegram_session()  # Recheck after manual login
                except NoSuchElementException:
                    logger.warning("⚠️  Unable to determine Telegram login status")
                    return False

        except Exception as e:
            logger.error(f"❌ Error checking Telegram session: {e}")
            return False

    def navigate_to_channel(self) -> bool:
        """Navigate to the specific Telegram channel"""
        try:
            logger.info(f"🔗 Navigating to channel: {self.channel_url}")
            self.driver.get(self.channel_url)
            time.sleep(3)

            # Wait for channel to load
            try:
                WebDriverWait(self.driver, 10).until(
                    lambda driver: driver.current_url.startswith("https://web.telegram.org/k/#-")
                )
                logger.info("✅ Successfully navigated to Telegram channel")
                return True
            except TimeoutException:
                logger.error("❌ Failed to navigate to channel")
                return False

        except Exception as e:
            logger.error(f"❌ Error navigating to channel: {e}")
            return False

    def extract_messages(self, scroll_count: int = 3) -> List[str]:
        """Extract messages from the Telegram channel"""
        messages = []

        try:
            logger.info("📨 Extracting messages from channel...")

            # Scroll up to load more messages
            for i in range(scroll_count):
                logger.info(f"📜 Scrolling up... ({i+1}/{scroll_count})")
                self.driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(2)

            # Try multiple selectors to find messages
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
                        break  # Use the first successful selector
                except:
                    continue

            # Extract text from elements
            seen_messages = set()
            for element in all_elements:
                try:
                    text = element.text.strip()
                    if (text and len(text) > 10 and
                        text not in seen_messages and
                        not text.startswith('[') and  # Skip system messages
                        'message' in text.lower() or
                        any(keyword in text.lower() for keyword in ['buy', 'sell', 'trade', 'price', 'signal'])):

                        seen_messages.add(text)
                        messages.append(text)
                except Exception as e:
                    logger.debug(f"Error extracting message text: {e}")
                    continue

            logger.info(f"✅ Extracted {len(messages)} relevant messages")
            return messages

        except Exception as e:
            logger.error(f"❌ Error extracting messages: {e}")
            return []

    def analyze_trading_signals(self, messages: List[str]) -> List[Dict]:
        """Analyze messages for trading signals"""
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

        # Price patterns
        price_patterns = [
            r'\$?(\d+\.?\d*)\s*(usd)?',  # Price with optional USD
            r'(price|at|@)\s*[$]?(\d+\.?\d*)',  # Price indicators
            r'(\d+\.?\d*)\s*[$]?'  # Number followed by optional $
        ]

        trading_symbols = ['BTC', 'ETH', 'AAPL', 'TSLA', 'EUR/USD', 'GOLD', 'SPY']

        for message in messages:
            signal_data = {
                'timestamp': datetime.now().isoformat(),
                'message': message[:200] + "..." if len(message) > 200 else message,
                'action': 'HOLD',
                'symbol': None,
                'price': None,
                'confidence': 0.0
            }

            # Calculate confidence
            confidence = self._calculate_signal_confidence(message)
            signal_data['confidence'] = confidence

            if confidence < 0.6:  # Skip low confidence signals
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
            for pattern in price_patterns:
                match = self._pattern_match(message, pattern)
                if match:
                    try:
                        # Extract the numeric value
                        import re
                        numbers = re.findall(r'\d+\.?\d*', match.group(0))
                        if numbers:
                            signal_data['price'] = float(numbers[0])
                            break
                    except:
                        pass

            # Only keep actionable signals
            if signal_data['action'] != 'HOLD' and signal_data['symbol']:
                signals.append(signal_data)

        logger.info(f"🎯 Found {len(signals)} trading signals")
        return signals

    def _calculate_signal_confidence(self, message: str) -> float:
        """Calculate confidence score for a trading signal"""
        confidence = 0.0

        # Trading emojis (strong indicators)
        trading_emojis = ['🟢', '🔴', '✅', '❌', '🚀', '📉', '📈', '💰', '⚡', '🎯']
        emoji_count = sum(1 for emoji in trading_emojis if emoji in message)
        confidence += min(emoji_count * 0.2, 0.4)

        # Trading keywords
        trading_keywords = [
            'buy', 'sell', 'trade', 'signal', 'entry', 'exit', 'long', 'short',
            'bullish', 'bearish', 'breakout', 'support', 'resistance', 'target',
            'stop loss', 'take profit', 'technical', 'analysis'
        ]
        keyword_count = sum(1 for keyword in trading_keywords if keyword.lower() in message.lower())
        confidence += min(keyword_count * 0.1, 0.3)

        # Price/volume information
        if '$' in message or any(char.isdigit() for char in message):
            confidence += 0.2

        # Urgency indicators
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
        """Monitor the Telegram channel for trading signals"""
        logger.info(f"🚀 Starting channel monitoring for {duration_minutes} minutes...")
        logger.info(f"📊 Checking for signals every {check_interval} seconds")

        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=duration_minutes)

        all_signals = []

        try:
            while datetime.now() < end_time:
                logger.info(f"🔍 Checking for new signals... ({datetime.now().strftime('%H:%M:%S')})")

                # Extract messages
                messages = self.extract_messages()

                # Analyze for signals
                current_signals = self.analyze_trading_signals(messages)

                # Process new signals
                for signal in current_signals:
                    if signal not in all_signals:
                        all_signals.append(signal)
                        self._log_signal(signal)

                        # Save signal to file
                        self._save_signal_to_file(signal)

                # Wait for next check
                logger.info(f"⏳ Waiting {check_interval} seconds for next check...")
                time.sleep(check_interval)

        except KeyboardInterrupt:
            logger.info("⏹️  Monitoring stopped by user")
        except Exception as e:
            logger.error(f"❌ Error during monitoring: {e}")
        finally:
            self._generate_final_report(all_signals)

    def _log_signal(self, signal: Dict):
        """Log a trading signal"""
        logger.info("🎯 TRADING SIGNAL DETECTED:")
        logger.info(f"   Action: {signal['action']}")
        logger.info(f"   Symbol: {signal['symbol']}")
        logger.info(f"   Price: ${signal['price']}" if signal['price'] else "   Price: Not specified")
        logger.info(f"   Confidence: {signal['confidence']:.2f}")
        logger.info(f"   Time: {signal['timestamp']}")
        logger.info(f"   Message: {signal['message'][:100]}...")

    def _save_signal_to_file(self, signal: Dict):
        """Save signal to JSON file"""
        filename = f"telegram_signals_{datetime.now().strftime('%Y%m%d')}.json"

        try:
            # Load existing signals
            existing_signals = []
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    existing_signals = json.load(f)

            # Add new signal
            existing_signals.append(signal)

            # Save updated signals
            with open(filename, 'w') as f:
                json.dump(existing_signals, f, indent=2)

        except Exception as e:
            logger.error(f"❌ Error saving signal to file: {e}")

    def _generate_final_report(self, all_signals: List[Dict]):
        """Generate final monitoring report"""
        logger.info("📋 GENERATING FINAL REPORT")

        if not all_signals:
            logger.info("   No trading signals found during monitoring period")
            return

        # Calculate statistics
        buy_signals = len([s for s in all_signals if s['action'] == 'BUY'])
        sell_signals = len([s for s in all_signals if s['action'] == 'SELL'])
        avg_confidence = sum(s['confidence'] for s in all_signals) / len(all_signals)
        symbols = list(set(s['symbol'] for s in all_signals if s['symbol']))

        report = {
            'monitoring_summary': {
                'total_signals': len(all_signals),
                'buy_signals': buy_signals,
                'sell_signals': sell_signals,
                'avg_confidence': round(avg_confidence, 3),
                'symbols_detected': symbols,
                'monitoring_period': f"{(datetime.now() - all_signals[0]['timestamp']).total_seconds() / 60:.1f} minutes" if all_signals else "N/A"
            },
            'signals': all_signals,
            'generated_at': datetime.now().isoformat()
        }

        # Save report
        report_filename = f"telegram_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w') as f:
            json.dump(report, f, indent=2)

        logger.info(f"   📊 Total Signals: {len(all_signals)}")
        logger.info(f"   📈 Buy Signals: {buy_signals}")
        logger.info(f"   📉 Sell Signals: {sell_signals}")
        logger.info(f"   🎯 Avg Confidence: {avg_confidence:.2f}")
        logger.info(f"   💰 Symbols: {', '.join(symbols)}")
        logger.info(f"   💾 Report saved: {report_filename}")

    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            # Don't quit the browser - keep the user's session intact
            logger.info("🌐 Keeping Brave browser open for your continued use")

def main():
    """Main execution function"""
    logger.info("🚀 BRAVE TELEGRAM TRADING SCRAPER")
    logger.info("=" * 50)

    scraper = None
    try:
        # Initialize scraper
        scraper = BraveTelegramScraper()

        # Connect to Brave browser
        if not scraper.connect_to_brave():
            logger.error("❌ Failed to connect to Brave browser")
            return

        # Check Telegram session
        if not scraper.check_telegram_session():
            logger.error("❌ No valid Telegram session found")
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
        logger.info("🏁 Scraper finished")

if __name__ == "__main__":
    main()