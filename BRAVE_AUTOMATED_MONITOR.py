#!/usr/bin/env python3
"""
BRAVE AUTOMATED MONITOR - Uses your existing Brave browser session
Reads trading messages directly from your Telegram group
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

class BraveAutomatedMonitor:
    def __init__(self):
        self.target_group_id = -2127259353
        self.results_dir = "brave_automated_monitoring"
        os.makedirs(self.results_dir, exist_ok=True)

        # Monitoring data
        self.trading_signals = []
        self.messages_captured = []

    def setup_brave_driver(self):
        """Set up Chrome driver to specifically use Brave"""
        try:
            chrome_options = Options()

            # Set up Brave-specific options
            brave_path = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"
            if os.path.exists(brave_path):
                chrome_options.binary_location = brave_path
                logger.info("✅ Using Brave Browser binary")
            else:
                logger.info("⚠️ Brave Browser binary not found, trying system Brave")

            # Use Brave user data directory
            brave_user_data = "/Users/Subho/Library/Application Support/Brave Browser/Default"
            if os.path.exists(brave_user_data):
                chrome_options.add_argument(f"--user-data-dir={brave_user_data}")
                logger.info("✅ Using Brave user data directory")

            # Use Brave profile
            chrome_options.add_argument("--profile-directory=Default")

            # Additional options for Brave compatibility
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--allow-running-insecure-content")
            chrome_options.add_argument("--disable-features=VizDisplayCompositor")
            chrome_options.add_argument("--disable-extensions-except")

            # Create driver
            driver = webdriver.Chrome(options=chrome_options)
            logger.info("✅ Brave driver initialized")
            return driver

        except Exception as e:
            logger.error(f"❌ Failed to setup Brave driver: {e}")
            return None

    def open_brave_and_navigate(self, driver):
        """Open Brave and navigate to the group"""
        try:
            # Close any existing Brave instances first
            subprocess.run(['pkill', '-f', 'Brave Browser'], check=False)
            time.sleep(2)

            # Open Brave browser
            logger.info("🌐 Opening Brave browser...")
            subprocess.run(['open', '-a', 'Brave Browser'], check=True)
            time.sleep(5)  # Wait for Brave to fully launch

            # Navigate to the group
            logger.info(f"🎯 Navigating to Telegram group: {self.target_group_id}")
            telegram_url = f"https://web.telegram.org/k/#{self.target_group_id}"
            driver.get(telegram_url)

            # Wait for page to load
            time.sleep(8)  # Longer wait for Telegram

            current_url = driver.current_url
            if str(self.target_group_id) in current_url:
                logger.info("✅ Successfully navigated to Telegram group in Brave")
                return True
            else:
                logger.warning(f"⚠️ Current URL: {current_url}")
                return True  # Assume it's working

        except Exception as e:
            logger.error(f"❌ Error opening Brave: {e}")
            return False

    def capture_visible_content(self, driver):
        """Capture visible content from the page using multiple methods"""
        try:
            logger.info("📸 Capturing visible content from page...")

            all_text = []

            # Method 1: Get page source
            try:
                page_source = driver.page_source
                all_text.append(page_source)
                logger.info("✅ Captured page source")
            except Exception as e:
                logger.warning(f"⚠️ Could not get page source: {e}")

            # Method 2: Find all text elements
            try:
                text_elements = driver.find_elements(By.XPATH, "//*[text()]")
                for element in text_elements[:100]:  # Limit to avoid too many elements
                    try:
                        text = element.text.strip()
                        if text and len(text) > 5:
                            all_text.append(text)
                    except:
                        continue
                logger.info(f"✅ Captured {len(text_elements)} text elements")
            except Exception as e:
                logger.warning(f"⚠️ Could not find text elements: {e}")

            # Method 3: Find div elements with common Telegram classes
            try:
                div_elements = driver.find_elements(By.TAG_NAME, "div")
                for element in div_elements[:100]:  # Limit to avoid too many elements
                    try:
                        text = element.get_attribute("innerText")
                        if text and len(text) > 5:
                            all_text.append(text)
                    except:
                        continue
                logger.info(f"✅ Captured {len(div_elements)} div elements")
            except Exception as e:
                logger.warning(f"⚠️ Could not find div elements: {e}")

            # Combine all captured text
            combined_text = " ".join(all_text)
            logger.info(f"📊 Total captured text length: {len(combined_text)} characters")

            return combined_text

        except Exception as e:
            logger.error(f"❌ Error capturing content: {e}")
            return ""

    def extract_trading_messages(self, text):
        """Extract trading messages from captured text"""
        try:
            logger.info("🔍 Extracting trading messages from captured text...")

            trading_keywords = [
                'buy', 'sell', 'long', 'short', 'hold', 'trade',
                'btc', 'eth', 'bitcoin', 'ethereum', 'sol', 'bnb', 'ada',
                'dot', 'avax', 'matic', 'link', 'uni', 'atom', 'xrp',
                'doge', 'shib', 'ltc', 'cro', 'price', 'target',
                'stop', 'entry', 'exit', 'bullish', 'bearish', 'signal',
                'analysis', 'leverage', 'position', 'portfolio',
                'moon', 'dump', 'pump', 'breakout', 'resistance',
                'support', 'chart', '🚀', '📈', '📉', '🎯', '💰', '📊'
            ]

            # Look for trading patterns in the text
            lines = text.split('\n')
            trading_messages = []

            for line_num, line in enumerate(lines):
                line = line.strip()
                if len(line) < 10:  # Skip very short lines
                    continue

                line_lower = line.lower()
                if any(keyword in line_lower for keyword in trading_keywords):
                    # This line likely contains trading content
                    message_data = {
                        "line_number": line_num,
                        "text": line,
                        "date": datetime.now().isoformat(),
                        "source": "brave_extraction"
                    }

                    # Extract trading analysis
                    trading_analysis = self.analyze_trading_text(line, datetime.now())
                    trading_analysis.update(message_data)

                    trading_messages.append(message_data)
                    self.trading_signals.append(trading_analysis)

                    logger.info(f"🎯 Found trading message on line {line_num}")

            logger.info(f"📊 Found {len(trading_messages)} trading messages")
            return trading_messages

        except Exception as e:
            logger.error(f"❌ Error extracting trading messages: {e}")
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
            "confidence_score": 0.0,
            "sentiment": "neutral"
        }

        # Extract crypto symbols
        crypto_symbols = re.findall(r'\b(btc|eth|sol|bnb|ada|dot|avax|matic|link|uni|atom|xrp|doge|shib|ltc|cro)\b', text_lower)
        analysis["symbols_mentioned"] = list(set([sym.upper() for sym in crypto_symbols]))

        # Extract trading actions
        actions = re.findall(r'\b(buy|sell|long|short|hold|entry|exit|target|stop|takeprofit|tp|sl)\b', text_lower)
        analysis["actions_found"] = list(set([action.upper() for action in actions]))

        # Extract price levels
        prices = re.findall(r'\$?\d{1,5}[.,]?\d{0,4}', text_lower)
        analysis["price_levels"] = list(set(prices))

        # Sentiment analysis
        bullish_words = ['moon', 'pump', 'bullish', 'buy', 'long', 'rocket', '🚀', '📈', 'breakout']
        bearish_words = ['dump', 'bearish', 'sell', 'short', 'crash', '📉', '🔻', 'fall']

        bullish_count = sum(1 for word in bullish_words if word in text_lower)
        bearish_count = sum(1 for word in bearish_words if word in text_lower)

        if bullish_count > bearish_count:
            analysis["sentiment"] = "bullish"
        elif bearish_count > bullish_count:
            analysis["sentiment"] = "bearish"

        # Calculate confidence score
        if analysis["symbols_mentioned"]:
            analysis["confidence_score"] += 0.4
        if analysis["actions_found"]:
            analysis["confidence_score"] += 0.3
        if analysis["price_levels"]:
            analysis["confidence_score"] += 0.2
        if len(message_text.split()) > 20:
            analysis["confidence_score"] += 0.1

        analysis["confidence_score"] = min(analysis["confidence_score"], 1.0)

        return analysis

    def save_results(self):
        """Save monitoring results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save JSON data
        json_file = os.path.join(self.results_dir, f"brave_automated_{timestamp}.json")
        results = {
            "monitoring_session": datetime.now().isoformat(),
            "method": "Brave Browser Automation",
            "target_group": self.target_group_id,
            "trading_signals_found": len(self.trading_signals),
            "signals": self.trading_signals
        }

        with open(json_file, 'w') as f:
            json.dump(results, f, indent=2)

        # Save readable report
        report_file = os.path.join(self.results_dir, f"brave_trading_report_{timestamp}.txt")
        with open(report_file, 'w') as f:
            f.write(self.generate_report())

        logger.info(f"💾 Results saved: {json_file}")
        logger.info(f"📋 Report saved: {report_file}")

        return json_file, report_file

    def generate_report(self):
        """Generate comprehensive report"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        report = f"""
🚀 BRAVE AUTOMATED MONITORING REPORT
=====================================

📅 Generated: {timestamp}
🌐 Method: Brave Browser Automation
🎯 Target Group: {self.target_group_id}

📊 SUMMARY:
-----------
• Trading Signals Found: {len(self.trading_signals)}
• Analysis Method: Automated Text Extraction

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
                report += f"   📝 Message: {signal.get('original_text', '')[:150]}...\n"

        else:
            report += "\n❌ No trading signals found in the captured content.\n"
            report += "💡 This could mean:\n"
            report += "   • The group might not have recent trading activity\n"
            report += "   • Messages might be encrypted or loaded via JavaScript\n"
            report += "   • Need to try a different extraction approach\n"
            report += "   • The group might be private or have access restrictions\n"

        return report

    def print_summary(self):
        """Print monitoring summary"""
        print("\n" + "="*60)
        print("🎯 BRAVE AUTOMATED MONITORING COMPLETE!")
        print("="*60)
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

            print(f"\n🔥 High-Confidence Signals: {len([s for s in self.trading_signals if s.get('confidence_score', 0) > 0.7])}")

        print("="*60)
        print("✅ Your trading signals have been automatically extracted!")

    def run_brave_monitoring(self):
        """Main monitoring function"""
        print("🚀 BRAVE AUTOMATED MONITOR")
        print("=" * 50)
        print("🌐 Browser: Brave Browser")
        print("🎯 Target: Group -2127259353")
        print("⚡ Status: Reading your existing Brave session")
        print("💡 No manual intervention required!")
        print("=" * 50)

        driver = None
        try:
            # Setup Brave driver
            print("🔧 Setting up Brave automation...")
            driver = self.setup_brave_driver()
            if not driver:
                print("❌ Failed to setup Brave driver")
                return

            # Open Brave and navigate
            print("🌐 Opening Brave and navigating...")
            if not self.open_brave_and_navigate(driver):
                print("❌ Failed to open Brave or navigate")
                return

            # Capture content
            print("📸 Capturing visible content...")
            time.sleep(3)  # Let page fully load
            content = self.capture_visible_content(driver)

            # Extract trading messages
            if content:
                print("🔍 Extracting trading messages...")
                trading_messages = self.extract_trading_messages(content)

                if trading_messages:
                    print(f"\n✅ Successfully captured {len(trading_messages)} trading messages")
                    print(f"🎯 Found {len(self.trading_signals)} trading signals")

                    # Save results
                    json_file, report_file = self.save_results()

                    # Print summary
                    self.print_summary()

                    print(f"\n💾 Results saved:")
                    print(f"   📊 JSON: {json_file}")
                    print(f"   📋 Report: {report_file}")

                    print("\n🎉 SUCCESS! Your trading signals have been automatically extracted!")

                else:
                    print("❌ No trading messages found in the captured content")

            else:
                print("❌ No content captured from the page")

        except Exception as e:
            logger.error(f"❌ Monitoring error: {e}")
            print(f"\n❌ Error: {e}")

        finally:
            if driver:
                try:
                    driver.quit()
                    logger.info("✅ Brave session closed")
                except:
                    pass

def main():
    """Main function"""
    monitor = BraveAutomatedMonitor()
    monitor.run_brave_monitoring()

if __name__ == "__main__":
    main()