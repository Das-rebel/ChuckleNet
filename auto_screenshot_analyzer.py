#!/usr/bin/env python3
"""
AUTOMATIC SCREENSHOT ANALYZER
Takes screenshots and analyzes them for trading signals automatically
"""

import os
import json
import logging
import time
from datetime import datetime
from PIL import ImageGrab
import pytesseract

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AutoScreenshotAnalyzer:
    """Automatic screenshot trading analyzer"""

    def __init__(self):
        self.results_dir = "auto_screenshot_analysis"
        os.makedirs(self.results_dir, exist_ok=True)
        self.screenshots_taken = 0

    def take_and_analyze_screenshot(self):
        """Take a screenshot and analyze it"""
        try:
            self.screenshots_taken += 1
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"auto_screenshot_{timestamp}.png"
            filepath = os.path.join(self.results_dir, filename)

            # Take screenshot
            logger.info(f"📸 Taking screenshot {self.screenshots_taken}...")
            screenshot = ImageGrab.grab()
            screenshot.save(filepath)
            logger.info(f"✅ Screenshot saved: {filename}")

            # Analyze with OCR
            logger.info("🔍 Analyzing text with OCR...")
            text = pytesseract.image_to_string(screenshot)

            # Analyze for trading signals
            signals = self.analyze_text_for_trading(text, filename)

            if signals:
                logger.info(f"🎯 Found {len(signals)} trading signals!")
                for signal in signals:
                    logger.info(f"   • {signal['summary']}")
            else:
                logger.info("⚠️ No trading signals found")

            return {
                "filename": filename,
                "text_length": len(text),
                "signals": signals,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"❌ Error: {e}")
            return None

    def analyze_text_for_trading(self, text, filename):
        """Analyze extracted text for trading signals"""
        if not text.strip():
            return []

        text_lower = text.lower()
        signals = []

        # Trading keywords
        trading_keywords = {
            'buy', 'sell', 'long', 'short', 'hold', 'trade',
            'btc', 'eth', 'sol', 'bnb', 'price', 'target',
            'stop', 'entry', 'exit', 'bullish', 'bearish'
        }

        # Look for lines with trading content
        lines = text.split('\n')
        for line_num, line in enumerate(lines):
            line = line.strip()
            if len(line) < 10:
                continue

            if any(keyword in line_lower for keyword in trading_keywords):
                # Analyze this line
                signal = self.extract_signal_info(line, line_num, filename)
                if signal:
                    signals.append(signal)

        return signals

    def extract_signal_info(self, text, line_num, filename):
        """Extract signal information from a line of text"""
        try:
            # Extract crypto symbols
            import re
            crypto_pattern = r'\b(btc|eth|sol|bnb|ada|dot|avax|matic|link|uni|atom|xrp|doge|shib|ltc|cro)\b'
            symbols = re.findall(crypto_pattern, text.lower())
            symbols = list(set([s.upper() for s in symbols]))

            # Extract prices
            price_pattern = r'\$\d{1,5}[.,]?\d{0,4}'
            prices = re.findall(price_pattern, text)

            # Extract actions
            actions = re.findall(r'\b(buy|sell|long|short|hold|entry|exit|target|stop|takeprofit|tp|sl)\b', text.lower())
            actions = list(set([a.upper() for a in actions]))

            # Sentiment analysis
            bullish_words = ['🚀', '📈', 'bullish', 'moon', 'pump', 'buy', 'long', 'breakout']
            bearish_words = ['📉', '🔻', 'bearish', 'dump', 'sell', 'short', 'crash']

            bullish_count = sum(1 for word in bullish_words if word in text.lower())
            bearish_count = sum(1 for word in bearish_words if word in text.lower())

            sentiment = "neutral"
            if bullish_count > bearish_count:
                sentiment = "bullish"
            elif bearish_count > bullish_count:
                sentiment = "bearish"

            # Calculate confidence
            confidence = 0.0
            if symbols:
                confidence += 0.4
            if actions:
                confidence += 0.3
            if prices:
                confidence += 0.2
            if len(text.split()) > 15:
                confidence += 0.1

            if confidence > 0.2:
                return {
                    "line_number": line_num,
                    "filename": filename,
                    "text": text,
                    "symbols": symbols,
                    "actions": actions,
                    "prices": prices,
                    "sentiment": sentiment,
                    "confidence": min(confidence, 1.0),
                    "summary": f"{', '.join(symbols)} {', '.join(actions)} @ {', '.join(prices[:2])}"
                }

        except Exception as e:
            logger.error(f"❌ Error extracting signal: {e}")

        return None

    def run_auto_session(self, num_screenshots=5, delay=3):
        """Run automatic screenshot session"""
        print("🚀 AUTOMATIC SCREENSHOT ANALYZER")
        print("=" * 40)
        print(f"📸 Will take {num_screenshots} screenshots")
        print(f"⏱️  {delay} seconds delay between captures")
        print("💡 Make sure your trading messages are visible!")
        print("=" * 40)

        all_results = []
        total_signals = 0

        try:
            for i in range(num_screenshots):
                print(f"\n📸 Screenshot {i+1}/{num_screenshots}")

                result = self.take_and_analyze_screenshot()
                if result:
                    all_results.append(result)
                    total_signals += len(result['signals'])

                    # Display findings
                    if result['signals']:
                        print(f"✅ Found {len(result['signals'])} trading signals:")
                        for signal in result['signals']:
                            print(f"   • {signal['summary']} (confidence: {signal['confidence']:.1%})")

                if i < num_screenshots - 1:
                    print(f"⏳ Waiting {delay} seconds...")
                    time.sleep(delay)

        except KeyboardInterrupt:
            print("\n⏹️ Session stopped by user")

        # Generate report
        if all_results:
            self.generate_report(all_results, total_signals)

        print(f"\n🎉 ANALYSIS COMPLETE!")
        print(f"📸 Screenshots: {len(all_results)}")
        print(f"🎯 Total Signals: {total_signals}")
        print(f"📁 Results saved to: {self.results_dir}")

    def generate_report(self, results, total_signals):
        """Generate analysis report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Aggregate data
        all_symbols = []
        all_sentiments = []
        all_confidences = []

        for result in results:
            for signal in result['signals']:
                all_symbols.extend(signal['symbols'])
                all_sentiments.append(signal['sentiment'])
                all_confidences.append(signal['confidence'])

        from collections import Counter
        symbol_counts = Counter(all_symbols)
        sentiment_counts = Counter(all_sentiments)
        avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0

        # Save JSON report
        json_file = os.path.join(self.results_dir, f"auto_analysis_report_{timestamp}.json")
        report = {
            "session_summary": {
                "screenshots_taken": len(results),
                "total_signals": total_signals,
                "average_confidence": avg_confidence,
                "timestamp": datetime.now().isoformat()
            },
            "symbol_analysis": dict(symbol_counts.most_common(10)),
            "sentiment_analysis": dict(sentiment_counts.most_common()),
            "results": results
        }

        with open(json_file, 'w') as f:
            json.dump(report, f, indent=2)

        # Generate readable report
        readable_file = os.path.join(self.results_dir, f"auto_analysis_summary_{timestamp}.txt")
        readable = f"""
🚀 AUTOMATIC SCREENSHOT ANALYSIS REPORT
=======================================

📅 Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
📸 Screenshots Analyzed: {len(results)}
🎯 Trading Signals Found: {total_signals}
📈 Average Confidence: {avg_confidence:.1%}

📊 SYMBOL ANALYSIS:
-----------------
"""
        if symbol_counts:
            for symbol, count in symbol_counts.most_common():
                readable += f"   • {symbol}: {count} mentions\n"

        readable += f"""
😊 SENTIMENT ANALYSIS:
--------------------
"""
        if sentiment_counts:
            for sentiment, count in sentiment_counts.most_common():
                readable += f"   • {sentiment.title()}: {count} signals\n"

        readable += f"""
📋 DETAILED FINDINGS:
--------------------
"""

        for i, result in enumerate(results, 1):
            if result['signals']:
                readable += f"\n{i}. From {result['filename']}:\n"
                for signal in result['signals'][:3]:  # First 3 signals
                    readable += f"   • {signal['summary']} (confidence: {signal['confidence']:.1%})\n"

        with open(readable_file, 'w') as f:
            f.write(readable)

        logger.info(f"💾 JSON report: {json_file}")
        logger.info(f"📋 Summary: {readable_file}")

def main():
    """Main execution function"""
    analyzer = AutoScreenshotAnalyzer()

    print("🎯 OPTION 4: Automatic Screenshot Analysis")
    print("=" * 50)
    print("💡 This will automatically capture and analyze screenshots")
    print("🖥️  Make sure your Telegram group is visible on screen!")
    print()

    # Let user choose parameters
    try:
        num_screenshots = int(input("How many screenshots to take? (default 3): ") or "3")
        delay = int(input("Delay between captures in seconds? (default 5): ") or "5")

        analyzer.run_auto_session(num_screenshots=num_screenshots, delay=delay)

    except KeyboardInterrupt:
        print("\n⏹️ Setup cancelled")
    except ValueError:
        print("❌ Invalid input. Using defaults...")
        analyzer.run_auto_session()

if __name__ == "__main__":
    main()