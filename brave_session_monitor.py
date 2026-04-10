#!/usr/bin/env python3
"""
Brave Session Monitor - Uses your existing logged-in Brave browser
Reads messages directly from your active Telegram session
"""

import os
import json
import logging
import time
import asyncio
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BraveSessionMonitor:
    def __init__(self):
        self.target_url = "https://web.telegram.org/k/#-2127259353"
        self.results_dir = "brave_session_monitoring"
        os.makedirs(self.results_dir, exist_ok=True)

        # Monitoring data
        self.trading_signals = []
        self.messages_captured = []
        self.monitoring_active = True

    def setup_brave_driver(self):
        """Set up Chrome driver to connect to existing Brave session"""
        try:
            # Chrome options to connect to existing Brave
            chrome_options = Options()

            # Connect to existing Brave browser
            chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

            # Additional options
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")

            # Try to connect to existing Brave
            try:
                driver = webdriver.Chrome(options=chrome_options)
                logger.info("✅ Connected to existing Brave browser")
                return driver
            except Exception as e:
                logger.info(f"⚠️ Could not connect to existing session: {e}")

                # Start new Brave session if needed
                chrome_options.add_argument("--user-data-dir=/Users/Subho/Library/Application Support/Google/Chrome")
                chrome_options.add_argument("--profile-directory=Default")

                driver = webdriver.Chrome(options=chrome_options)
                logger.info("✅ Started new Brave session")
                return driver

        except Exception as e:
            logger.error(f"❌ Failed to setup Brave driver: {e}")
            return None

    def navigate_to_telegram(self, driver):
        """Navigate to the target Telegram group"""
        try:
            logger.info(f"🌐 Navigating to: {self.target_url}")
            driver.get(self.target_url)

            # Wait for page to load
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            # Additional wait for Telegram to load
            time.sleep(3)

            logger.info("✅ Navigated to Telegram group")
            return True

        except TimeoutException:
            logger.error("❌ Timeout loading Telegram page")
            return False
        except Exception as e:
            logger.error(f"❌ Error navigating to Telegram: {e}")
            return False

    def capture_messages_from_page(self, driver):
        """Capture messages from the loaded page"""
        try:
            logger.info("📥 Capturing messages from page...")

            # Scroll to load more messages
            for _ in range(5):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)

            # Find message elements
            message_selectors = [
                ".message",
                "[class*='message']",
                "[class*='bubble']",
                ".chat-message"
            ]

            messages_text = []
            for selector in message_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        text = element.text.strip()
                        if text and len(text) > 10:  # Filter out very short texts
                            messages_text.append(text)
                    if messages_text:
                        break
                except:
                    continue

            logger.info(f"📊 Found {len(messages_text)} potential messages")

            # Analyze for trading content
            trading_signals = []
            for i, text in enumerate(messages_text):
                message_data = {
                    "message_id": i,
                    "text": text,
                    "date": datetime.now().isoformat(),
                    "source": "brave_session"
                }

                self.messages_captured.append(message_data)

                if self.contains_trading_content(text):
                    trading_analysis = self.analyze_trading_text(text, datetime.now())
                    trading_analysis.update(message_data)
                    trading_signals.append(trading_analysis)
                    self.trading_signals.append(trading_analysis)
                    logger.info(f"🎯 Trading signal found: {trading_analysis.get('symbols_mentioned', [])}")

            logger.info(f"✅ Processed {len(messages_text)} messages, found {len(trading_signals)} trading signals")
            return trading_signals

        except Exception as e:
            logger.error(f"❌ Error capturing messages: {e}")
            return []

    def contains_trading_content(self, text):
        """Check if text contains trading content"""
        if not text:
            return False

        trading_keywords = [
            'buy', 'sell', 'long', 'short', 'hold', 'trade',
            'btc', 'eth', 'bitcoin', 'ethereum', 'sol', 'bnb',
            'price', 'target', 'stop', 'entry', 'exit',
            'bullish', 'bearish', 'signal', 'analysis',
            'leverage', 'position', 'portfolio', 'moon', 'dump',
            'pump', 'breakout', 'resistance', 'support', 'chart'
        ]

        text_lower = text.lower()
        return any(keyword in text_lower for keyword in trading_keywords)

    def analyze_trading_text(self, message_text, message_date):
        """Analyze text for trading signals"""
        import re

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
        crypto_symbols = re.findall(r'\b(btc|eth|sol|bnb|ada|dot|avax|matic|link|uni|atom|xrp|doge|shib|ltc)\b', text_lower)
        analysis["symbols_mentioned"] = list(set([sym.upper() for sym in crypto_symbols]))

        # Extract trading actions
        actions = re.findall(r'\b(buy|sell|long|short|hold|entry|exit|target|stop|takeprofit|tp|sl)\b', text_lower)
        analysis["actions_found"] = list(set([action.upper() for action in actions]))

        # Extract price levels
        prices = re.findall(r'\$?\d{1,5}[.,]?\d{0,4}', text_lower)
        analysis["price_levels"] = list(set(prices))

        # Extract timeframes
        timeframes = re.findall(r'\b(1m|5m|15m|30m|1h|4h|1d|1w)\b', text_lower)
        analysis["timeframes"] = list(set(timeframes))

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
        json_file = os.path.join(self.results_dir, f"brave_session_results_{timestamp}.json")
        results = {
            "monitoring_session": datetime.now().isoformat(),
            "method": "Brave Browser Session",
            "target_url": self.target_url,
            "messages_captured": len(self.messages_captured),
            "trading_signals_found": len(self.trading_signals),
            "signals": self.trading_signals,
            "messages": self.messages_captured
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
🚀 BRAVE SESSION MONITORING REPORT
=================================

📅 Generated: {timestamp}
🌐 Method: Brave Browser Session
🎯 Target: {self.target_url}

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
                    report += f"   • {symbol}: {count} times ({count/len(self.trading_signals):.1%})\n"

            # Action analysis
            all_actions = []
            for signal in self.trading_signals:
                all_actions.extend(signal.get('actions_found', []))

            if all_actions:
                action_counts = Counter(all_actions)
                report += "\n🎯 Trading Actions:\n"
                for action, count in action_counts.most_common():
                    report += f"   • {action}: {count} signals ({count/len(self.trading_signals):.1%})\n"

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
            report += "\n❌ No trading signals found in the captured messages.\n"
            report += "💡 The group might not have recent trading activity or messages weren't captured properly.\n"

        return report

    def print_summary(self):
        """Print monitoring summary"""
        print("\n" + "="*50)
        print("🎯 BRAVE SESSION MONITORING COMPLETE!")
        print("="*50)
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

            print(f"\n🎪 High-Confidence Signals: {len([s for s in self.trading_signals if s.get('confidence_score', 0) > 0.7])}")

        print("="*50)

    def run_monitoring(self):
        """Main monitoring function"""
        print("🚀 BRAVE SESSION MONITOR")
        print("="*40)
        print(f"🎯 Target: {self.target_url}")
        print(f"🌐 Method: Your existing Brave browser")
        print("="*40)

        driver = None
        try:
            # Setup Brave driver
            driver = self.setup_brave_driver()
            if not driver:
                print("❌ Failed to connect to Brave browser")
                return

            # Navigate to Telegram
            if not self.navigate_to_telegram(driver):
                print("❌ Failed to navigate to Telegram")
                return

            # Wait for page to fully load
            print("⏳ Waiting for Telegram to load...")
            time.sleep(5)

            # Capture messages from page
            trading_signals = self.capture_messages_from_page(driver)

            if trading_signals:
                print(f"\n✅ Successfully captured and analyzed {len(self.messages_captured)} messages")
                print(f"🎯 Found {len(trading_signals)} trading signals")

                # Save results
                json_file, report_file = self.save_results()

                # Print summary
                self.print_summary()

                print(f"\n💾 Results saved:")
                print(f"   📊 JSON: {json_file}")
                print(f"   📋 Report: {report_file}")

            else:
                print("❌ No trading signals found or messages couldn't be captured")

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
    monitor = BraveSessionMonitor()
    monitor.run_monitoring()

if __name__ == "__main__":
    main()