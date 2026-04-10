#!/usr/bin/env python3
"""
REFINED TRADING EXTRACTOR
Uses the best working methods to extract trading signals from actual group content
"""

import os
import json
import logging
import asyncio
from datetime import datetime, timedelta
from collections import Counter
import re

# Check what libraries are available
try:
    from PIL import ImageGrab
    import pytesseract
    SCREENSHOT_AVAILABLE = True
except ImportError:
    SCREENSHOT_AVAILABLE = False

try:
    import telethon
    TELETHON_AVAILABLE = True
except ImportError:
    TELETHON_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RefinedTradingExtractor:
    """Refined trading signal extractor using best available methods"""

    def __init__(self):
        self.target_group = -2127259353
        self.bot_username = "@Das_ts_bot"
        self.results_dir = "refined_trading_analysis"
        os.makedirs(self.results_dir, exist_ok=True)

        # Enhanced trading patterns based on real analysis
        self.crypto_symbols = {
            'BTC', 'ETH', 'SOL', 'BNB', 'ADA', 'DOT', 'AVAX',
            'MATIC', 'LINK', 'UNI', 'ATOM', 'XRP', 'DOGE', 'SHIB',
            'LTC', 'CRO', 'FTM', 'SAND', 'MANA', 'AXS', 'AVAX',
            'FTM', 'CRV', 'SUSHI', 'AAVE', 'COMP', 'MKR', 'YFI'
        }

        self.trading_actions = {
            'BUY', 'SELL', 'LONG', 'SHORT', 'HOLD', 'ENTRY',
            'EXIT', 'TARGET', 'STOP', 'TAKEPROFIT', 'TP', 'SL',
            'SCALP', 'SWING', 'POSITION', 'LEVERAGE', 'FUTURES',
            'SPOT', 'MARGIN', 'CALL', 'PUT'
        }

        # Trading indicators and patterns
        self.trading_patterns = {
            'breakout', 'resistance', 'support', 'trend', 'momentum',
            'bullish', 'bearish', 'consolidation', 'reversal', 'pullback',
            'dip', 'top', 'bottom', 'ATH', 'ATL', 'volume', 'RSI',
            'MACD', 'MA', 'EMA', 'SMA', 'BB', 'fibonacci', 'wick'
        }

    def navigate_to_group_and_capture(self):
        """Navigate to the specific group and capture actual trading content"""
        print("🎯 METHOD 1: Direct Group Navigation & Capture")
        print("=" * 60)

        try:
            # Open the specific group
            group_url = f"https://web.telegram.org/k/#{self.target_group}"
            print(f"🌐 Opening target group: {group_url}")

            os.system(f'open -a "Brave Browser" "{group_url}"')

            # Wait for page to load and navigate
            print("⏳ Waiting 8 seconds for group to load...")
            import time
            time.sleep(8)

            # Bring Brave to front
            print("📱 Bringing Brave to front...")
            os.system('osascript -e \'tell application "Brave Browser" to activate\'')
            time.sleep(2)

            # Take multiple screenshots of the actual group content
            screenshots = []
            for i in range(5):
                print(f"📸 Capturing group content screenshot {i+1}/5...")

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"trading_group_{timestamp}_{i}.png"
                filepath = os.path.join(self.results_dir, filename)

                if SCREENSHOT_AVAILABLE:
                    screenshot = ImageGrab.grab()
                    screenshot.save(filepath)
                    screenshots.append(filepath)

                    # Immediate analysis
                    text = pytesseract.image_to_string(screenshot)
                    print(f"📝 Extracted {len(text)} characters")

                    # Check for actual trading content
                    if self.has_trading_content(text):
                        print(f"🎯 TRADING CONTENT FOUND in screenshot {i+1}!")
                        self.save_trading_content(text, filename)
                    else:
                        print(f"⚠️ No clear trading content in screenshot {i+1}")

                if i < 4:
                    print("⏳ Waiting 2 seconds...")
                    time.sleep(2)

            return screenshots

        except Exception as e:
            print(f"❌ Navigation and capture failed: {e}")
            return None

    def has_trading_content(self, text):
        """Check if text contains actual trading signals"""
        if not text or len(text.strip()) < 20:
            return False

        text_lower = text.lower()

        # Look for multiple trading indicators
        trading_score = 0

        # Crypto symbols (weighted heavily)
        for symbol in self.crypto_symbols:
            if symbol.lower() in text_lower:
                trading_score += 3

        # Trading actions
        for action in self.trading_actions:
            if action.lower() in text_lower:
                trading_score += 2

        # Price levels
        price_matches = re.findall(r'\$\d{1,5}[.,]?\d{0,4}', text)
        trading_score += len(price_matches)

        # Trading patterns
        for pattern in self.trading_patterns:
            if pattern.lower() in text_lower:
                trading_score += 1

        # Emoji indicators
        bullish_emojis = ['🚀', '📈', '📊', '💰', '⭐', '✅']
        bearish_emojis = ['📉', '🔻', '⚠️', '❌', '🔴']

        for emoji in bullish_emojis + bearish_emojis:
            if emoji in text:
                trading_score += 1

        # Require a minimum score to consider it trading content
        return trading_score >= 5

    def save_trading_content(self, text, filename):
        """Save discovered trading content"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        content_file = os.path.join(self.results_dir, f"trading_content_{timestamp}.txt")

        with open(content_file, 'w') as f:
            f.write(f"Source: {filename}\n")
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            f.write("=" * 50 + "\n")
            f.write(text)

        print(f"💾 Trading content saved: {content_file}")

    def provide_manual_instructions(self):
        """Provide clear instructions for manual content access"""
        print("\n🎯 METHOD 2: Manual Content Access Instructions")
        print("=" * 60)

        instructions = """
📋 STEP-BY-STEP INSTRUCTIONS TO GET TRADING CONTENT:

1. 🌐 OPEN THE TARGET GROUP:
   • Open Brave Browser
   • Go to: https://web.telegram.org/k/#-2127259353
   • Make sure you're logged into your Telegram account

2. 📱 NAVIGATE TO TRADING MESSAGES:
   • Scroll through the group to find recent trading signals
   • Look for messages with crypto symbols (BTC, ETH, SOL, etc.)
   • Identify messages with price targets and entry/exit points

3. 🔄 USE YOUR BOT @Das_ts_bot:
   • Forward any trading message to @Das_ts_bot
   • Get instant AI analysis with:
     • Symbol detection
     • Price level extraction
     • Sentiment analysis
     • Risk assessment
     • Confidence scoring

4. 📸 ALTERNATIVE - SCREENSHOTS:
   • Take screenshots of trading messages
   • Run: python3 refined_trading_extractor.py
   • System will analyze screenshots for trading signals

5. 🎯 WHAT TO LOOK FOR:
   • Buy/Sell signals with specific prices
   • Target and stop-loss levels
   • Cryptocurrency symbols (BTC, ETH, SOL, etc.)
   • Time frames (short-term, long-term)
   • Risk levels and leverage information

💡 IMMEDIATE ACTION:
Since your bot @Das_ts_bot is already running, forward any trading
message from the group to it for instant analysis right now!
        """

        print(instructions)

        # Save instructions to file
        instructions_file = os.path.join(self.results_dir, "access_instructions.txt")
        with open(instructions_file, 'w') as f:
            f.write(instructions)

        print(f"\n💾 Instructions saved: {instructions_file}")

    def analyze_existing_content(self):
        """Analyze any existing trading content we've captured"""
        print("\n🎯 METHOD 3: Analyze Existing Content")
        print("=" * 40)

        # Look for existing trading content files
        content_files = []
        for file in os.listdir(self.results_dir):
            if file.startswith("trading_content_") and file.endswith(".txt"):
                content_files.append(os.path.join(self.results_dir, file))

        if content_files:
            print(f"📁 Found {len(content_files)} trading content files")

            all_signals = []
            for content_file in content_files:
                print(f"📋 Analyzing: {os.path.basename(content_file)}")

                with open(content_file, 'r') as f:
                    content = f.read()

                # Extract trading signals from content
                signals = self.extract_signals_from_text(content)
                all_signals.extend(signals)

                print(f"   📊 Found {len(signals)} signals")

            if all_signals:
                self.generate_comprehensive_analysis(all_signals)
                return all_signals
            else:
                print("⚠️ No trading signals found in existing content")
        else:
            print("📁 No existing trading content found")
            print("💡 Use the manual instructions to capture trading content")

        return []

    def extract_signals_from_text(self, text):
        """Extract trading signals from text content"""
        signals = []

        # Split text into potential messages
        lines = text.split('\n')
        current_message = []

        for line in lines:
            if len(line.strip()) > 0:
                current_message.append(line)
            elif current_message:
                # Analyze complete message
                message_text = ' '.join(current_message)
                signal = self.analyze_message_text(message_text)
                if signal:
                    signals.append(signal)
                current_message = []

        # Analyze last message if exists
        if current_message:
            message_text = ' '.join(current_message)
            signal = self.analyze_message_text(message_text)
            if signal:
                signals.append(signal)

        return signals

    def analyze_message_text(self, text):
        """Analyze a single message for trading signals"""
        if not text or len(text.strip()) < 10:
            return None

        text_upper = text.upper()
        text_lower = text.lower()

        # Quick check for trading keywords
        if not self.has_trading_content(text):
            return None

        # Extract trading information
        signal = {
            "original_text": text,
            "symbols_mentioned": [],
            "actions_found": [],
            "price_levels": [],
            "confidence_score": 0.0,
            "sentiment": "neutral",
            "risk_level": "unknown",
            "timeframe": "unknown",
            "extracted_date": datetime.now().isoformat()
        }

        # Extract crypto symbols
        for symbol in self.crypto_symbols:
            if symbol in text_upper or f"{symbol}/USDT" in text_upper or f"{symbol}/USD" in text_upper:
                signal["symbols_mentioned"].append(symbol)

        # Extract trading actions
        for action in self.trading_actions:
            if action in text_upper:
                signal["actions_found"].append(action)

        # Extract price levels
        price_patterns = [
            r'\$\d{1,5}[.,]?\d{0,4}',
            r'\d{1,5}[.,]?\d{0,4}\s*USDT',
            r'\d{1,5}[.,]?\d{0,4}\s*USD',
            r'Entry\s*[:\-]?\s*\$?\d+',
            r'Target\s*[:\-]?\s*\$?\d+',
            r'Stop\s*[:\-]?\s*\$?\d+',
            r'TP\s*[:\-]?\s*\$?\d+',
            r'SL\s*[:\-]?\s*\$?\d+'
        ]

        prices = []
        for pattern in price_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            prices.extend(matches)

        signal["price_levels"] = list(set(prices))

        # Sentiment analysis
        bullish_words = ['🚀', '📈', 'BULLISH', 'MOON', 'PUMP', 'BUY', 'LONG', 'BREAKOUT', 'GAINS', 'PROFIT']
        bearish_words = ['📉', '🔻', 'BEARISH', 'DUMP', 'SELL', 'SHORT', 'CRASH', 'LOSS', 'FALL']

        bullish_count = sum(1 for word in bullish_words if word in text_upper)
        bearish_count = sum(1 for word in bearish_words if word in text_upper)

        if bullish_count > bearish_count:
            signal["sentiment"] = "bullish"
        elif bearish_count > bullish_count:
            signal["sentiment"] = "bearish"

        # Risk assessment
        high_risk_words = ['HIGH', 'RISKY', 'DANGEROUS', 'LEVERAGE', 'FUTURES', '⚠️', 'CAUTION']
        low_risk_words = ['SAFE', 'LOW RISK', 'CONSERVATIVE', 'SPOT', '✅', 'SAFE']

        if any(word in text_upper for word in high_risk_words):
            signal["risk_level"] = "high"
        elif any(word in text_upper for word in low_risk_words):
            signal["risk_level"] = "low"
        else:
            signal["risk_level"] = "medium"

        # Timeframe detection
        timeframes = {
            '1m': '1-minute', '5m': '5-minute', '15m': '15-minute', '1h': '1-hour',
            '4h': '4-hour', '1d': '1-day', '1w': '1-week', 'scalp': 'scalping',
            'swing': 'swing trading', 'position': 'position trading', 'long': 'long-term'
        }

        for tf_key, tf_value in timeframes.items():
            if tf_key in text_lower:
                signal["timeframe"] = tf_value
                break

        # Calculate confidence score
        score = 0.0
        if signal["symbols_mentioned"]:
            score += 0.25
        if signal["actions_found"]:
            score += 0.25
        if signal["price_levels"]:
            score += 0.20
        if signal["sentiment"] != "neutral":
            score += 0.10
        if len(text.split()) > 15:
            score += 0.10
        if signal["timeframe"] != "unknown":
            score += 0.10

        signal["confidence_score"] = min(score, 1.0)

        # Only return substantial signals
        return signal if signal["confidence_score"] > 0.3 else None

    def generate_comprehensive_analysis(self, signals):
        """Generate comprehensive analysis of extracted signals"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Analyze data
        all_symbols = []
        all_sentiments = []
        all_confidences = []
        all_risks = []
        all_timeframes = []

        for signal in signals:
            all_symbols.extend(signal.get('symbols_mentioned', []))
            all_sentiments.append(signal.get('sentiment', 'neutral'))
            all_confidences.append(signal.get('confidence_score', 0))
            all_risks.append(signal.get('risk_level', 'unknown'))
            all_timeframes.append(signal.get('timeframe', 'unknown'))

        symbol_counts = Counter(all_symbols)
        sentiment_counts = Counter(all_sentiments)
        risk_counts = Counter(all_risks)
        timeframe_counts = Counter(all_timeframes)
        avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0

        # Save comprehensive report
        json_file = os.path.join(self.results_dir, f"comprehensive_analysis_{timestamp}.json")
        report = {
            "analysis_summary": {
                "total_signals": len(signals),
                "average_confidence": avg_confidence,
                "analysis_date": datetime.now().isoformat(),
                "source": "Refined Trading Extractor"
            },
            "symbol_analysis": dict(symbol_counts.most_common()),
            "sentiment_analysis": dict(sentiment_counts.most_common()),
            "risk_analysis": dict(risk_counts.most_common()),
            "timeframe_analysis": dict(timeframe_counts.most_common()),
            "signals": signals
        }

        with open(json_file, 'w') as f:
            json.dump(report, f, indent=2)

        # Generate readable summary
        readable_file = os.path.join(self.results_dir, f"analysis_summary_{timestamp}.txt")
        summary = f"""
🚀 COMPREHENSIVE TRADING ANALYSIS
=================================

📊 Summary:
• Total Signals: {len(signals)}
• Average Confidence: {avg_confidence:.1%}
• Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📈 Top Symbols:
"""

        if symbol_counts:
            for symbol, count in symbol_counts.most_common(5):
                summary += f"• {symbol}: {count} signals\n"

        summary += f"""
😊 Sentiment Breakdown:
"""

        if sentiment_counts:
            for sentiment, count in sentiment_counts.most_common():
                summary += f"• {sentiment.title()}: {count} signals\n"

        summary += f"""
⚠️ Risk Analysis:
"""

        if risk_counts:
            for risk, count in risk_counts.most_common():
                summary += f"• {risk.title()} Risk: {count} signals\n"

        with open(readable_file, 'w') as f:
            f.write(summary)

        # Display results
        print("\n" + "=" * 60)
        print("🎉 COMPREHENSIVE ANALYSIS COMPLETE!")
        print("=" * 60)
        print(f"📊 Trading Signals: {len(signals)}")
        print(f"📈 Average Confidence: {avg_confidence:.1%}")
        if symbol_counts:
            print(f"📈 Top Symbol: {symbol_counts.most_common(1)[0][0]}")
        print(f"💾 JSON Report: {json_file}")
        print(f"📋 Summary: {readable_file}")
        print("=" * 60)

    async def run_refined_extraction(self):
        """Run the refined extraction process"""
        print("🚀 REFINED TRADING EXTRACTOR")
        print("=" * 50)
        print(f"🎯 Target Group: {self.target_group}")
        print(f"🤖 Available Bot: {self.bot_username}")
        print("=" * 50)

        # Method 1: Direct navigation and capture
        screenshots = self.navigate_to_group_and_capture()

        # Method 2: Provide manual instructions
        self.provide_manual_instructions()

        # Method 3: Analyze existing content
        signals = self.analyze_existing_content()

        print(f"\n✅ Extraction complete! Check {self.results_dir} for results.")
        return signals

async def main():
    """Main execution"""
    extractor = RefinedTradingExtractor()
    await extractor.run_refined_extraction()

if __name__ == "__main__":
    asyncio.run(main())