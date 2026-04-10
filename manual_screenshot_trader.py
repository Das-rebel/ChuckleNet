#!/usr/bin/env python3
"""
MANUAL SCREENSHOT TRADING ANALYZER
For Option 4 - Manual Browser + OCR Approach
"""

import os
import json
import logging
import time
from datetime import datetime, timedelta
from PIL import ImageGrab
import pytesseract
from collections import Counter

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ManualScreenshotTrader:
    """Manual screenshot-based trading signal analyzer"""

    def __init__(self):
        self.results_dir = "manual_trading_analysis"
        os.makedirs(self.results_dir, exist_ok=True)
        self.trading_signals = []

        # Trading analysis parameters
        self.crypto_symbols = {
            'BTC', 'ETH', 'SOL', 'BNB', 'ADA', 'DOT', 'AVAX',
            'MATIC', 'LINK', 'UNI', 'ATOM', 'XRP', 'DOGE', 'SHIB',
            'LTC', 'CRO', 'FTM', 'SAND', 'MANA', 'AXS'
        }

        self.trading_actions = {
            'BUY', 'SELL', 'LONG', 'SHORT', 'HOLD', 'ENTRY',
            'EXIT', 'TARGET', 'STOP', 'TAKEPROFIT', 'TP', 'SL'
        }

    def capture_screenshot(self, description=""):
        """Capture a screenshot of the current screen"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"trading_screenshot_{timestamp}_{description}.png"
            filepath = os.path.join(self.results_dir, filename)

            # Capture screenshot
            screenshot = ImageGrab.grab()
            screenshot.save(filepath)

            logger.info(f"📸 Screenshot captured: {filename}")
            return filepath

        except Exception as e:
            logger.error(f"❌ Error capturing screenshot: {e}")
            return None

    def analyze_screenshot_text(self, image_path):
        """Analyze text from a screenshot using OCR"""
        try:
            # Open image
            image = Image.open(image_path)

            # Extract text using Tesseract OCR
            text = pytesseract.image_to_string(image)

            logger.info(f"📝 Extracted {len(text)} characters from screenshot")
            return text.strip()

        except Exception as e:
            logger.error(f"❌ Error analyzing screenshot: {e}")
            return ""

    def analyze_trading_text(self, text, screenshot_filename):
        """Analyze extracted text for trading signals"""
        if not text.strip():
            return None

        text_upper = text.upper()
        text_lower = text.lower()

        # Quick check for trading keywords
        trading_keywords = {
            'buy', 'sell', 'btc', 'eth', 'sol', 'trade', 'target',
            'stop', 'entry', 'exit', 'long', 'short', 'signal',
            'moon', 'pump', 'dump', 'bullish', 'bearish'
        }

        if not any(keyword in text_lower for keyword in trading_keywords):
            return None

        # Analyze for trading signals
        analysis = {
            "screenshot_filename": screenshot_filename,
            "extracted_text": text,
            "date": datetime.now().isoformat(),
            "symbols_mentioned": [],
            "actions_found": [],
            "price_levels": [],
            "confidence_score": 0.0,
            "sentiment": "neutral"
        }

        # Extract crypto symbols
        import re
        symbol_pattern = r'\b(' + '|'.join(self.crypto_symbols) + r')(?:/USDT|/USD)?\b'
        symbols = re.findall(symbol_pattern, text_upper)
        analysis["symbols_mentioned"] = list(set(symbols))

        # Extract trading actions
        actions = re.findall(r'\b(' + '|'.join(self.trading_actions) + r')\b', text_upper)
        analysis["actions_found"] = list(set(actions))

        # Extract price levels
        prices = re.findall(r'\$\d{1,5}[.,]?\d{0,4}', text)
        analysis["price_levels"] = list(set(prices))

        # Sentiment analysis
        bullish_words = ['🚀', '📈', 'BULLISH', 'MOON', 'PUMP', 'BUY', 'LONG', 'BREAKOUT']
        bearish_words = ['📉', '🔻', 'BEARISH', 'DUMP', 'SELL', 'SHORT', 'CRASH']

        bullish_count = sum(1 for word in bullish_words if word in text_upper)
        bearish_count = sum(1 for word in bearish_words if word in text_upper)

        if bullish_count > bearish_count:
            analysis["sentiment"] = "bullish"
        elif bearish_count > bullish_count:
            analysis["sentiment"] = "bearish"

        # Calculate confidence score
        score = 0.0
        if analysis["symbols_mentioned"]:
            score += 0.4
        if analysis["actions_found"]:
            score += 0.3
        if analysis["price_levels"]:
            score += 0.2
        if len(text.split()) > 15:
            score += 0.1

        analysis["confidence_score"] = min(score, 1.0)

        # Only return if we found something substantial
        if score > 0.2:
            return analysis

        return None

    def run_manual_capture_session(self):
        """Run a manual capture session with user guidance"""
        print("🚀 MANUAL SCREENSHOT TRADING ANALYZER")
        print("=" * 50)
        print("💡 This captures screenshots and analyzes them for trading signals")
        print()

        # Check if Tesseract is available
        try:
            pytesseract.get_tesseract_version()
            print("✅ Tesseract OCR is ready")
        except:
            print("❌ Tesseract not found")
            print("💡 Make sure it's installed: brew install tesseract")
            return

        print("\n📋 INSTRUCTIONS:")
        print("=" * 30)
        print("1. Open Brave browser and go to your Telegram group")
        print("2. Scroll to trading messages you want to analyze")
        print("3. Press ENTER here to capture a screenshot")
        print("4. Type 'done' when you're finished")
        print("5. Type 'quit' to exit")
        print()

        captured_signals = []
        screenshot_count = 0

        while True:
            try:
                user_input = input(f"\n📸 Screenshot #{screenshot_count + 1} - Press ENTER to capture, 'done' to analyze, 'quit' to exit: ").strip().lower()

                if user_input == 'quit':
                    break
                elif user_input == 'done':
                    if captured_signals:
                        self.generate_final_report(captured_signals)
                    else:
                        print("❌ No trading signals found in captured screenshots")
                    break

                # Capture screenshot
                print("📸 Capturing screenshot in 3 seconds...")
                print("💡 Make sure your trading messages are visible on screen!")
                time.sleep(3)

                image_path = self.capture_screenshot(f"capture_{screenshot_count + 1}")
                if image_path:
                    # Analyze screenshot
                    print("🔍 Analyzing screenshot for trading signals...")
                    extracted_text = self.analyze_screenshot_text(image_path)

                    if extracted_text:
                        analysis = self.analyze_trading_text(extracted_text, os.path.basename(image_path))

                        if analysis:
                            captured_signals.append(analysis)
                            print(f"✅ Trading signal found!")
                            print(f"   📊 Symbols: {analysis['symbols_mentioned']}")
                            print(f"   🎯 Actions: {analysis['actions_found']}")
                            print(f"   💰 Prices: {analysis['price_levels']}")
                            print(f"   📈 Confidence: {analysis['confidence_score']:.1%}")
                            print(f"   😊 Sentiment: {analysis['sentiment']}")
                        else:
                            print("⚠️ No trading signals found in this screenshot")
                            print(f"📝 Extracted text preview: {extracted_text[:200]}...")
                    else:
                        print("❌ No text extracted from screenshot")

                    screenshot_count += 1

            except KeyboardInterrupt:
                print("\n⏹️ Capture session stopped by user")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

    def generate_final_report(self, signals):
        """Generate final trading analysis report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Analyze symbol frequency
        all_symbols = []
        for signal in signals:
            all_symbols.extend(signal.get('symbols_mentioned', []))

        symbol_counts = Counter(all_symbols)

        # Analyze sentiment
        sentiments = [s.get('sentiment', 'neutral') for s in signals]
        sentiment_counts = Counter(sentiments)

        # Calculate average confidence
        avg_confidence = sum(s.get('confidence_score', 0) for s in signals) / len(signals)

        # Save JSON report
        json_file = os.path.join(self.results_dir, f"manual_trading_report_{timestamp}.json")
        report = {
            "capture_summary": {
                "total_screenshots": len(signals),
                "average_confidence": avg_confidence,
                "capture_date": datetime.now().isoformat(),
                "method": "Manual Screenshot + OCR"
            },
            "symbol_analysis": dict(symbol_counts.most_common()),
            "sentiment_analysis": dict(sentiment_counts.most_common()),
            "signals": signals
        }

        with open(json_file, 'w') as f:
            json.dump(report, f, indent=2)

        # Generate readable report
        readable_file = os.path.join(self.results_dir, f"manual_trading_summary_{timestamp}.txt")
        readable_report = f"""
🚀 MANUAL SCREENSHOT TRADING ANALYSIS REPORT
=============================================

📅 Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
💻 Method: Manual Screenshot + OCR Analysis
🎯 Screenshots Analyzed: {len(signals)}
📈 Average Confidence: {avg_confidence:.1%}

📊 SYMBOL ANALYSIS:
-----------------
"""

        if symbol_counts:
            for symbol, count in symbol_counts.most_common():
                readable_report += f"   • {symbol}: {count} mentions\n"

        readable_report += f"""
😊 SENTIMENT ANALYSIS:
--------------------
"""

        if sentiments:
            for sentiment, count in sentiment_counts.most_common():
                readable_report += f"   • {sentiment.title()}: {count} signals\n"

        readable_report += f"""
📋 DETAILED SIGNALS:
-------------------
"""

        for i, signal in enumerate(signals, 1):
            readable_report += f"\n{i}. SIGNAL FROM {signal['screenshot_filename']}\n"
            readable_report += f"   📅 Time: {signal['date']}\n"
            readable_report += f"   📊 Symbols: {', '.join(signal['symbols_mentioned'])}\n"
            readable_report += f"   🎯 Actions: {', '.join(signal['actions_found'])}\n"
            readable_report += f"   💰 Prices: {', '.join(signal['price_levels'])}\n"
            readable_report += f"   📈 Confidence: {signal['confidence_score']:.1%}\n"
            readable_report += f"   😊 Sentiment: {signal['sentiment'].title()}\n"
            readable_report += f"   📝 Text: {signal['extracted_text'][:150]}...\n"

        with open(readable_file, 'w') as f:
            f.write(readable_report)

        print("\n" + "=" * 60)
        print("🎉 MANUAL TRADING ANALYSIS COMPLETE!")
        print("=" * 60)
        print(f"📊 Trading Signals Found: {len(signals)}")
        print(f"📈 Average Confidence: {avg_confidence:.1%}")
        if symbol_counts:
            top_symbol = symbol_counts.most_common(1)[0]
            print(f"📈 Top Symbol: {top_symbol[0]} ({top_symbol[1]} mentions)")
        print(f"💾 JSON Report: {json_file}")
        print(f"📋 Summary: {readable_file}")
        print("=" * 60)

def main():
    """Main execution function"""
    analyzer = ManualScreenshotTrader()
    analyzer.run_manual_capture_session()

if __name__ == "__main__":
    main()