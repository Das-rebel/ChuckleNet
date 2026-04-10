#!/usr/bin/env python3
"""
Simple Brave Monitor - Uses AppleScript to interact with your existing Brave session
Manual but effective approach for reading messages
"""

import os
import json
import logging
import subprocess
import time
from datetime import datetime, timedelta
from PIL import ImageGrab
import pytesseract

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleBraveMonitor:
    def __init__(self):
        self.results_dir = "simple_brave_monitoring"
        os.makedirs(self.results_dir, exist_ok=True)

        # Monitoring data
        self.captured_images = []
        self.trading_signals = []

    def activate_brave(self):
        """Activate Brave browser"""
        try:
            applescript = '''
            tell application "Brave Browser"
                activate
                delay 2
            end tell
            '''
            subprocess.run(['osascript', '-e', applescript], check=True)
            logger.info("✅ Brave browser activated")
            return True
        except Exception as e:
            logger.error(f"❌ Error activating Brave: {e}")
            return False

    def navigate_to_telegram(self):
        """Navigate to the Telegram group using AppleScript"""
        try:
            applescript = f'''
            tell application "Brave Browser"
                activate
                delay 1
                set URL of front document to "https://web.telegram.org/k/#-2127259353"
                delay 5
            end tell
            '''
            subprocess.run(['osascript', '-e', applescript], check=True)
            logger.info("✅ Navigated to Telegram group")
            return True
        except Exception as e:
            logger.error(f"❌ Error navigating to Telegram: {e}")
            return False

    def capture_screenshot_with_delay(self, description="", delay=2):
        """Capture screenshot with description and delay"""
        try:
            # Wait for page to load
            time.sleep(delay)

            # Capture screenshot
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"brave_telegram_{timestamp}_{description}.png"
            filepath = os.path.join(self.results_dir, filename)

            # Take screenshot
            screenshot = ImageGrab.grab()
            screenshot.save(filepath)

            # Extract text using OCR
            text = pytesseract.image_to_string(screenshot)

            self.captured_images.append({
                "filename": filename,
                "filepath": filepath,
                "text": text,
                "timestamp": timestamp,
                "description": description
            })

            logger.info(f"📸 Captured screenshot: {filename}")
            return filepath, text

        except Exception as e:
            logger.error(f"❌ Error capturing screenshot: {e}")
            return None, ""

    def scroll_and_capture_multiple(self, num_screenshots=5):
        """Scroll through the page and capture multiple screenshots"""
        logger.info(f"📱 Capturing {num_screenshots} screenshots with scrolling...")

        for i in range(num_screenshots):
            logger.info(f"📸 Capturing screenshot {i+1}/{num_screenshots}")
            self.capture_screenshot_with_delay(f"scroll_{i+1}", delay=2)

            if i < num_screenshots - 1:
                # Scroll down
                try:
                    applescript = '''
                    tell application "System Events"
                        tell process "Brave Browser"
                            keystroke space
                            delay 1
                        end tell
                    end tell
                    '''
                    subprocess.run(['osascript', '-e', applescript], check=False)
                except Exception as e:
                    logger.warning(f"⚠️ Could not scroll: {e}")

    def analyze_captured_text_for_trading(self):
        """Analyze all captured text for trading signals"""
        logger.info("🔍 Analyzing captured text for trading signals...")

        trading_signals = []
        trading_keywords = [
            'buy', 'sell', 'long', 'short', 'hold', 'trade',
            'btc', 'eth', 'bitcoin', 'ethereum', 'sol', 'bnb',
            'price', 'target', 'stop', 'entry', 'exit',
            'bullish', 'bearish', 'signal', 'analysis',
            'leverage', 'position', 'portfolio', 'moon', 'dump',
            'pump', 'breakout', 'resistance', 'support', 'chart'
        ]

        for image_data in self.captured_images:
            text = image_data['text']
            if not text.strip():
                continue

            # Check for trading content
            text_lower = text.lower()
            has_trading_content = any(keyword in text_lower for keyword in trading_keywords)

            if has_trading_content:
                # Analyze the text
                trading_analysis = self.analyze_trading_text(text, datetime.now())
                trading_analysis.update({
                    "source_screenshot": image_data['filename'],
                    "capture_timestamp": image_data['timestamp'],
                    "method": "screenshot_ocr"
                })

                trading_signals.append(trading_analysis)
                logger.info(f"🎯 Trading signal found in {image_data['filename']}")

        self.trading_signals = trading_signals
        return trading_signals

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
        json_file = os.path.join(self.results_dir, f"brave_monitoring_results_{timestamp}.json")
        results = {
            "monitoring_session": datetime.now().isoformat(),
            "method": "Simple Brave Monitor + OCR",
            "screenshots_captured": len(self.captured_images),
            "trading_signals_found": len(self.trading_signals),
            "signals": self.trading_signals,
            "images": self.captured_images
        }

        with open(json_file, 'w') as f:
            json.dump(results, f, indent=2)

        # Save readable report
        report_file = os.path.join(self.results_dir, f"trading_report_{timestamp}.txt")
        with open(report_file, 'w') as f:
            f.write(self.generate_report())

        logger.info(f"💾 Results saved: {json_file}")
        logger.info(f"📋 Report saved: {report_file}")

        return json_file, report_file

    def generate_report(self):
        """Generate comprehensive report"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        report = f"""
🚀 SIMPLE BRAVE MONITORING REPORT
================================

📅 Generated: {timestamp}
🌐 Method: Brave Browser + OCR Screenshots
📊 Screenshots Captured: {len(self.captured_images)}

📈 SUMMARY:
-----------
• Screenshots Analyzed: {len(self.captured_images)}
• Trading Signals Found: {len(self.trading_signals)}

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
            report += f"\n🔥 High Confidence Signals: {len(high_confidence)}/{len(self.trading_signals)}\n\n"

            # Detailed signals
            report += "📋 DETAILED TRADING SIGNALS:\n"
            report += "-" * 35 + "\n"

            for i, signal in enumerate(self.trading_signals, 1):
                report += f"\n{i}. **Signal**\n"
                report += f"   📅 Date: {signal.get('date', 'Unknown')}\n"
                report += f"   📊 Source: {signal.get('source_screenshot', 'Unknown')}\n"
                report += f"   📈 Symbols: {', '.join(signal.get('symbols_mentioned', []))}\n"
                report += f"   🎯 Actions: {', '.join(signal.get('actions_found', []))}\n"
                if signal.get('price_levels'):
                    report += f"   💰 Price Levels: {', '.join(signal['price_levels'][:3])}\n"
                report += f"   📈 Confidence: {signal.get('confidence_score', 0):.1%}\n"
                report += f"   😊 Sentiment: {signal.get('sentiment', 'neutral').title()}\n"
                report += f"   📝 Text Preview: {signal.get('original_text', '')[:200]}...\n"

        else:
            report += "\n❌ No trading signals found in the screenshots.\n"
            report += "💡 This could mean:\n"
            report += "   • The group messages don't contain trading content\n"
            report += "   • OCR couldn't read the text properly\n"
            report += "   • Need to try different scrolling/capturing approach\n"

        return report

    def print_summary(self):
        """Print monitoring summary"""
        print("\n" + "="*50)
        print("🎯 BRAVE MONITORING COMPLETE!")
        print("="*50)
        print(f"📸 Screenshots Captured: {len(self.captured_images)}")
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

        print("="*50)

    def run_monitoring(self):
        """Main monitoring function"""
        print("🚀 SIMPLE BRAVE MONITOR")
        print("="*40)
        print("🌐 Using your existing Brave browser")
        print("📸 Method: Screenshot + OCR")
        print("="*40)

        try:
            # Activate Brave
            if not self.activate_brave():
                return

            # Navigate to Telegram
            if not self.navigate_to_telegram():
                return

            # Wait for page to load
            print("⏳ Waiting for Telegram to load (10 seconds)...")
            time.sleep(10)

            # Scroll and capture screenshots
            self.scroll_and_capture_multiple(num_screenshots=8)

            # Analyze captured text
            trading_signals = self.analyze_captured_text_for_trading()

            if trading_signals:
                print(f"\n✅ Found {len(trading_signals)} trading signals!")

                # Save results
                json_file, report_file = self.save_results()

                # Print summary
                self.print_summary()

                print(f"\n💾 Results saved:")
                print(f"   📊 JSON: {json_file}")
                print(f"   📋 Report: {report_file}")

            else:
                print("❌ No trading signals found in the captured screenshots")
                print("💡 The OCR might not have captured readable text from the messages")

        except Exception as e:
            logger.error(f"❌ Monitoring error: {e}")
            print(f"\n❌ Error: {e}")

def main():
    """Main function"""
    monitor = SimpleBraveMonitor()
    monitor.run_monitoring()

if __name__ == "__main__":
    main()