#!/usr/bin/env python3
"""
FULLY AUTOMATED MONITOR - Uses browser automation to read your existing Telegram session
Complete hands-off solution for automatic group monitoring
"""

import os
import json
import logging
import time
import subprocess
import asyncio
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FullyAutomatedMonitor:
    def __init__(self):
        self.target_group_id = -2127259353
        self.results_dir = "fully_automated_monitoring"
        os.makedirs(self.results_dir, exist_ok=True)

        # Monitoring data
        self.trading_signals = []
        self.messages_captured = []

    def setup_chrome_driver(self):
        """Set up Chrome driver with Brave profile"""
        try:
            chrome_options = Options()

            # Set up Brave-specific options
            brave_path = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"
            if os.path.exists(brave_path):
                chrome_options.binary_location = brave_path
                logger.info("✅ Using Brave Browser binary")

            # Use Brave user data directory
            brave_user_data = "/Users/Subho/Library/Application Support/Brave Browser"
            if os.path.exists(brave_user_data):
                chrome_options.add_argument(f"--user-data-dir={brave_user_data}")
                chrome_options.add_argument("--profile-directory=Default")
                logger.info("✅ Using Brave user data directory")

            # Additional options
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--allow-running-insecure-content")
            chrome_options.add_argument("--disable-features=VizDisplayCompositor")

            # Try to create driver
            driver = webdriver.Chrome(options=chrome_options)
            logger.info("✅ Chrome driver initialized")
            return driver

        except Exception as e:
            logger.error(f"❌ Failed to setup Chrome driver: {e}")
            return None

    def navigate_to_telegram_group(self, driver):
        """Navigate to the Telegram group"""
        try:
            logger.info(f"🌐 Navigating to Telegram group: {self.target_group_id}")

            # First try direct navigation
            telegram_url = f"https://web.telegram.org/k/#{self.target_group_id}"
            driver.get(telegram_url)

            # Wait for page to load
            time.sleep(3)

            # Check if we're on the right page
            current_url = driver.current_url
            if str(self.target_group_id) in current_url:
                logger.info("✅ Successfully navigated to Telegram group")
                return True
            else:
                # Try alternative URL format
                alt_url = f"https://web.telegram.org/#/{self.target_group_id}"
                driver.get(alt_url)
                time.sleep(3)
                current_url = driver.current_url
                if str(self.target_group_id) in current_url:
                    logger.info("✅ Successfully navigated to Telegram group (alternative URL)")
                    return True

                logger.warning(f"⚠️ May not be on the correct group. Current URL: {current_url}")
                return True  # Assume it's working and continue

        except Exception as e:
            logger.error(f"❌ Error navigating to Telegram: {e}")
            return False

    def wait_for_messages_to_load(self, driver):
        """Wait for messages to load in the group"""
        try:
            logger.info("⏳ Waiting for messages to load...")
            time.sleep(5)  # Give messages time to load

            # Try to scroll to trigger message loading
            try:
                # Find scrollable area and scroll down
                body = driver.find_element(By.TAG_NAME, "body")
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(2)
                logger.info("✅ Scrolled to trigger message loading")
            except Exception as e:
                logger.warning(f"⚠️ Could not scroll: {e}")

            return True

        except Exception as e:
            logger.error(f"❌ Error waiting for messages: {e}")
            return False

    def extract_messages_from_page(self, driver):
        """Extract messages from the loaded Telegram page"""
        try:
            logger.info("📥 Extracting messages from page...")

            all_text = driver.page_source

            # Look for message content in various formats
            message_patterns = [
                r'<div[^>]*class="[^"]*message[^"]*"[^>]*>([^<]+)</div>',
                r'<span[^>]*class="[^"]*text[^"]*"[^>]*>([^<]+)</span>',
                r'<div[^>]*data-testid="[^"]*message[^"]*"[^>]*>([^<]+)</div>',
                r'"message":"([^"]+)"',  # JSON format
                r'text":"([^"]+)"',      # Text content
            ]

            extracted_messages = []
            trading_keywords = [
                'buy', 'sell', 'long', 'short', 'hold', 'trade',
                'btc', 'eth', 'bitcoin', 'ethereum', 'sol', 'bnb',
                'price', 'target', 'stop', 'entry', 'exit',
                'bullish', 'bearish', 'signal', 'analysis',
                'leverage', 'position', 'portfolio', 'moon', 'dump',
                'pump', 'breakout', 'resistance', 'support', 'chart',
                '🚀', '📈', '📉', '🎯', '💰', '📊'
            ]

            for pattern in message_patterns:
                try:
                    matches = re.findall(pattern, all_text)
                    for match in matches:
                        text = match.strip()
                        if len(text) > 10:  # Only keep substantial messages
                            # Check if it contains trading content
                            text_lower = text.lower()
                            has_trading = any(keyword in text_lower for keyword in trading_keywords)

                            if has_trading:
                                message_data = {
                                    "id": len(extracted_messages),
                                    "text": text,
                                    "date": datetime.now().isoformat(),
                                    "source": "automated_extraction",
                                    "has_trading_content": True
                                }
                                extracted_messages.append(message_data)

                                # Analyze for trading signals
                                trading_analysis = self.analyze_trading_text(text, datetime.now())
                                trading_analysis.update(message_data)
                                self.trading_signals.append(trading_analysis)

                except Exception as e:
                    continue

            logger.info(f"📊 Extracted {len(extracted_messages)} messages with trading content")
            logger.info(f"🎯 Found {len(self.trading_signals)} trading signals")

            self.messages_captured = extracted_messages
            return extracted_messages

        except Exception as e:
            logger.error(f"❌ Error extracting messages: {e}")
            return []

    def analyze_trading_text(self, message_text, message_date):
        """Analyze text for trading signals"""
        text_lower = message_text.lower()

        analysis = {
            "original_text": message_text,
            "date": message_date.isoformat(),
            "symbols_mentioned": [],
            "actions_found": [],
            "price_levels": [],
            "timeframes": [],
            "confidence_score": 0.0,
            "sentiment": "neutral"
        }

        # Extract crypto symbols
        crypto_symbols = re.findall(r'\b(btc|eth|sol|bnb|ada|dot|avax|matic|link|uni|atom|xrp|doge|shib|ltc|cro|avax)\b', text_lower)
        analysis["symbols_mentioned"] = list(set([sym.upper() for sym in crypto_symbols]))

        # Extract trading actions
        actions = re.findall(r'\b(buy|sell|long|short|hold|entry|exit|target|stop|takeprofit|tp|sl|short|long|position)\b', text_lower)
        analysis["actions_found"] = list(set([action.upper() for action in actions]))

        # Extract price levels
        prices = re.findall(r'\$?\d{1,5}[.,]?\d{0,4}', text_lower)
        analysis["price_levels"] = list(set(prices))

        # Extract timeframes
        timeframes = re.findall(r'\b(1m|5m|15m|30m|1h|4h|1d|1w|daily|weekly)\b', text_lower)
        analysis["timeframes"] = list(set(timeframes))

        # Sentiment analysis
        bullish_words = ['moon', 'pump', 'bullish', 'buy', 'long', 'rocket', '🚀', '📈', 'breakout', 'above', 'higher', 'up']
        bearish_words = ['dump', 'bearish', 'sell', 'short', 'crash', '📉', '🔻', 'fall', 'below', 'lower', 'down']

        bullish_count = sum(1 for word in bullish_words if word in text_lower)
        bearish_count = sum(1 for word in bearish_words if word in text_lower)

        if bullish_count > bearish_count:
            analysis["sentiment"] = "bullish"
        elif bearish_count > bullish_count:
            analysis["sentiment"] = "bearish"

        # Calculate confidence score
        if analysis["symbols_mentioned"]:
            analysis["confidence_score"] += 0.3
        if analysis["actions_found"]:
            analysis["confidence_score"] += 0.3
        if analysis["price_levels"]:
            analysis["confidence_score"] += 0.2
        if len(message_text.split()) > 20:
            analysis["confidence_score"] += 0.1
        if analysis["sentiment"] != "neutral":
            analysis["confidence_score"] += 0.1

        analysis["confidence_score"] = min(analysis["confidence_score"], 1.0)

        return analysis

    def save_results(self):
        """Save monitoring results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save JSON data
        json_file = os.path.join(self.results_dir, f"automated_monitoring_{timestamp}.json")
        results = {
            "monitoring_session": datetime.now().isoformat(),
            "method": "Fully Automated Browser Monitor",
            "target_group": self.target_group_id,
            "messages_captured": len(self.messages_captured),
            "trading_signals_found": len(self.trading_signals),
            "signals": self.trading_signals,
            "messages": self.messages_captured
        }

        with open(json_file, 'w') as f:
            json.dump(results, f, indent=2)

        # Save readable report
        report_file = os.path.join(self.results_dir, f"trading_report_{timestamp}.txt")
        with open(report_file, 'w') as f:
            f.write(self.generate_comprehensive_report())

        logger.info(f"💾 Results saved: {json_file}")
        logger.info(f"📋 Report saved: {report_file}")

        return json_file, report_file

    def generate_comprehensive_report(self):
        """Generate comprehensive report"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        report = f"""
🚀 FULLY AUTOMATED MONITORING REPORT
=====================================

📅 Generated: {timestamp}
🤖 Method: Browser Automation
🎯 Target Group: {self.target_group_id}

📊 SUMMARY:
-----------
• Messages Captured: {len(self.messages_captured)}
• Trading Signals Found: {len(self.trading_signals)}
• Signal Success Rate: {len(self.trading_signals)/max(len(self.messages_captured), 1):.1%}

"""

        if self.trading_signals:
            # Symbol analysis
            all_symbols = []
            for signal in self.trading_signals:
                all_symbols.extend(signal.get('symbols_mentioned', []))

            if all_symbols:
                from collections import Counter
                symbol_counts = Counter(all_symbols)
                report += "📈 Most Mentioned Symbols:\n"
                for symbol, count in symbol_counts.most_common(5):
                    report += f"   • {symbol}: {count} times\n"

            # Action analysis
            all_actions = []
            for signal in self.trading_signals:
                all_actions.extend(signal.get('actions_found', []))

            if all_actions:
                action_counts = Counter(all_actions)
                report += "\n🎯 Trading Actions:\n"
                for action, count in action_counts.most_common():
                    report += f"   • {action}: {count} signals\n"

            # Sentiment analysis
            sentiments = [s.get('sentiment', 'neutral') for s in self.trading_signals]
            if sentiments:
                sentiment_counts = Counter(sentiments)
                report += "\n😊 Market Sentiment:\n"
                for sentiment, count in sentiment_counts.most_common():
                    report += f"   • {sentiment.title()}: {count} signals\n"

            # High confidence signals
            high_confidence = [s for s in self.trading_signals if s.get('confidence_score', 0) > 0.7]
            report += f"\n🔥 High Confidence Signals: {len(high_confidence)}/{len(self.trading_signals)} ({len(high_confidence)/len(self.trading_signals):.1%})\n\n"

            # Detailed signals
            report += "📋 DETAILED TRADING SIGNALS:\n"
            report += "-" * 35 + "\n"

            for i, signal in enumerate(self.trading_signals, 1):
                report += f"\n{i}. **Signal**\n"
                report += f"   📅 Date: {signal.get('date', 'Unknown')}\n"
                report += f"   📊 Symbols: {', '.join(signal.get('symbols_mentioned', []))}\n"
                report += f"   🎯 Actions: {', '.join(signal.get('actions_found', []))}\n"
                if signal.get('price_levels'):
                    report += f"   💰 Price Levels: {', '.join(signal['price_levels'][:3])}\n"
                report += f"   📈 Confidence: {signal.get('confidence_score', 0):.1%}\n"
                report += f"   😊 Sentiment: {signal.get('sentiment', 'neutral').title()}\n"
                report += f"   📝 Message: {signal.get('original_text', '')[:200]}...\n"

        else:
            report += "\n❌ No trading signals found in the captured messages.\n"
            report += "💡 This could mean:\n"
            report += "   • The group might not have recent trading activity\n"
            report += "   • Messages are still loading or not accessible\n"
            report += "   • Need to try different extraction methods\n"

        return report

    def print_summary(self):
        """Print monitoring summary"""
        print("\n" + "="*60)
        print("🎯 FULLY AUTOMATED MONITORING COMPLETE!")
        print("="*60)
        print(f"📊 Messages Captured: {len(self.messages_captured)}")
        print(f"🎯 Trading Signals Found: {len(self.trading_signals)}")

        if self.trading_signals:
            # Top symbols
            all_symbols = []
            for signal in self.trading_signals:
                all_symbols.extend(signal.get('symbols_mentioned', []))

            if all_symbols:
                from collections import Counter
                symbol_counts = Counter(all_symbols)
                top_symbol = symbol_counts.most_common(1)[0]
                print(f"📈 Top Symbol: {top_symbol[0]} ({top_symbol[1]} mentions)")

            avg_confidence = sum(s.get('confidence_score', 0) for s in self.trading_signals) / len(self.trading_signals)
            print(f"📊 Average Confidence: {avg_confidence:.1%}")

        print("="*60)

    def run_automated_monitoring(self):
        """Main monitoring function"""
        print("🚀 FULLY AUTOMATED GROUP MONITOR")
        print("=" * 50)
        print("🎯 Target Group: -2127259353")
        print("🤖 Method: Browser Automation (Your Session)")
        print("⚡ Status: Reading your existing Telegram login")
        print("=" * 50)

        driver = None
        try:
            # Setup Chrome driver
            print("🔧 Setting up browser automation...")
            driver = self.setup_chrome_driver()
            if not driver:
                print("❌ Failed to setup browser driver")
                return

            # Navigate to Telegram
            print("🌐 Navigating to Telegram group...")
            if not self.navigate_to_telegram_group(driver):
                print("❌ Failed to navigate to Telegram")
                return

            # Wait for messages to load
            print("⏳ Waiting for messages to load...")
            if not self.wait_for_messages_to_load(driver):
                print("❌ Error waiting for messages")
                return

            # Extract messages
            print("📥 Extracting trading messages...")
            messages = self.extract_messages_from_page(driver)

            if messages:
                print(f"\n✅ Successfully captured {len(messages)} trading messages")
                print(f"🎯 Found {len(self.trading_signals)} trading signals")

                # Save results
                json_file, report_file = self.save_results()

                # Print summary
                self.print_summary()

                print(f"\n💾 Results saved:")
                print(f"   📊 JSON: {json_file}")
                print(f"   📋 Report: {report_file}")

            else:
                print("❌ No trading messages found or extracted")

        except Exception as e:
            logger.error(f"❌ Monitoring error: {e}")
            print(f"\n❌ Error: {e}")

        finally:
            if driver:
                try:
                    driver.quit()
                    logger.info("✅ Browser session closed")
                except:
                    pass

def main():
    """Main function"""
    monitor = FullyAutomatedMonitor()
    monitor.run_automated_monitoring()

if __name__ == "__main__":
    main()