#!/usr/bin/env python3
"""
TELEGRAM LITE/TRADING DESKTOP TRADING EXTRACTOR
Uses existing Telegram Desktop session to extract trading signals from target group
"""

import os
import json
import logging
import asyncio
from datetime import datetime, timedelta
from collections import Counter
import re

# Try to import OpenTele
try:
    from opentele import Telethon
    from opentele.td import TDesktop
    from opentele.td.types import AccountAuthorization
except ImportError:
    print("❌ OpenTele not installed. Run: pip3 install opentele")
    exit(1)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TelegramLiteTradingExtractor:
    """Trading signal extractor using existing Telegram Desktop session"""

    def __init__(self):
        self.target_group = -2127259353
        self.session_path = "/Users/Subho/Library/Application Support/Telegram Desktop/tdata"
        self.results_dir = "telegram_lite_trading_analysis"
        os.makedirs(self.results_dir, exist_ok=True)

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

    async def extract_trading_signals(self):
        """Extract trading signals from target group using existing session"""
        print("🚀 TELEGRAM LITE/TRADING DESKTOP EXTRACTOR")
        print("=" * 60)
        print(f"🎯 Target Group: {self.target_group}")
        print(f"📁 Session Path: {self.session_path}")
        print("=" * 60)

        try:
            # Step 1: Convert TDesktop session to Telethon
            print("\n📋 Step 1: Converting existing session...")

            if not os.path.exists(self.session_path):
                print(f"❌ Session not found at: {self.session_path}")
                return None

            # Load TDesktop session
            tdesk = TDesktop.from_telegram_desktop(self.session_path)
            print("✅ Successfully loaded Telegram Desktop session")

            # Convert to Telethon session
            telethon_session = os.path.join(self.results_dir, "trading_session")
            client = await tdesk.to_telethon_session(telethon_session)
            print("✅ Successfully converted to Telethon session")

            # Step 2: Connect and extract messages
            print("\n📋 Step 2: Extracting trading messages...")

            # Connect to Telegram
            await client.start()
            print("✅ Connected to Telegram")

            # Get target entity
            try:
                target_entity = await client.get_entity(self.target_group)
                print(f"✅ Found target group: {target_entity.title}")
            except Exception as e:
                print(f"❌ Cannot access group {self.target_group}: {e}")
                print("💡 Make sure you're a member of this group")
                return None

            # Get messages from last 7 days
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)

            print(f"📅 Extracting messages from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")

            # Iterate through messages
            trading_messages = []
            message_count = 0

            async for message in client.iter_messages(
                target_entity,
                offset_date=end_date,
                reverse=True  # Get older messages first
            ):
                if message.date < start_date:
                    break

                message_count += 1

                # Analyze message content
                if message.text:
                    trading_signal = self.analyze_message_for_trading(
                        message.text,
                        message.id,
                        message.date
                    )

                    if trading_signal:
                        trading_signal['group_name'] = target_entity.title
                        trading_signal['message_id'] = message.id
                        trading_messages.append(trading_signal)
                        print(f"🎯 Found trading signal in message {message.id}")

            print(f"\n📊 Analysis Complete:")
            print(f"   • Total messages analyzed: {message_count}")
            print(f"   • Trading signals found: {len(trading_messages)}")

            # Step 3: Generate comprehensive report
            if trading_messages:
                await self.generate_comprehensive_report(trading_messages)
            else:
                print("⚠️ No trading signals found in the specified time period")

            await client.disconnect()
            return trading_messages

        except Exception as e:
            logger.error(f"❌ Error during extraction: {e}")
            print(f"❌ Error: {e}")
            return None

    def analyze_message_for_trading(self, text, message_id, date):
        """Analyze message text for trading signals"""
        if not text or len(text.strip()) < 10:
            return None

        text_upper = text.upper()
        text_lower = text.lower()

        # Quick check for trading keywords
        trading_keywords = {
            'buy', 'sell', 'btc', 'eth', 'sol', 'trade', 'target',
            'stop', 'entry', 'exit', 'long', 'short', 'signal',
            'moon', 'pump', 'dump', 'bullish', 'bearish', 'price',
            'usdt', 'usd', '$', 'leverage', 'futures', 'spot'
        }

        if not any(keyword in text_lower for keyword in trading_keywords):
            return None

        # Extract trading information
        analysis = {
            "original_text": text,
            "message_id": message_id,
            "date": date.isoformat(),
            "symbols_mentioned": [],
            "actions_found": [],
            "price_levels": [],
            "confidence_score": 0.0,
            "sentiment": "neutral",
            "risk_level": "unknown"
        }

        # Extract crypto symbols
        symbol_pattern = r'\b(' + '|'.join(self.crypto_symbols) + r')(?:/USDT|/USD)?\b'
        symbols = re.findall(symbol_pattern, text_upper)
        analysis["symbols_mentioned"] = list(set(symbols))

        # Extract trading actions
        actions = re.findall(r'\b(' + '|'.join(self.trading_actions) + r')\b', text_upper)
        analysis["actions_found"] = list(set(actions))

        # Extract price levels
        price_patterns = [
            r'\$\d{1,5}[.,]?\d{0,4}',  # $42,150
            r'\d{1,5}[.,]?\d{0,4}\s*USDT',  # 42150 USDT
            r'\d{1,5}[.,]?\d{0,4}\s*USD'   # 42150 USD
        ]

        prices = []
        for pattern in price_patterns:
            prices.extend(re.findall(pattern, text_upper))
        analysis["price_levels"] = list(set(prices))

        # Sentiment analysis
        bullish_words = ['🚀', '📈', 'BULLISH', 'MOON', 'PUMP', 'BUY', 'LONG', 'BREAKOUT', 'GAINS']
        bearish_words = ['📉', '🔻', 'BEARISH', 'DUMP', 'SELL', 'SHORT', 'CRASH', 'LOSS', 'STOP']

        bullish_count = sum(1 for word in bullish_words if word in text_upper)
        bearish_count = sum(1 for word in bearish_words if word in text_upper)

        if bullish_count > bearish_count:
            analysis["sentiment"] = "bullish"
        elif bearish_count > bullish_count:
            analysis["sentiment"] = "bearish"

        # Risk assessment
        high_risk_words = ['HIGH', 'RISKY', 'DANGEROUS', 'CAUTION', '⚠️', '❌']
        medium_risk_words = ['MEDIUM', 'MODERATE', 'CAUTIOUS']
        low_risk_words = ['SAFE', 'LOW RISK', 'CONSERVATIVE', '✅']

        if any(word in text_upper for word in high_risk_words):
            analysis["risk_level"] = "high"
        elif any(word in text_upper for word in medium_risk_words):
            analysis["risk_level"] = "medium"
        elif any(word in text_upper for word in low_risk_words):
            analysis["risk_level"] = "low"

        # Calculate confidence score
        score = 0.0
        if analysis["symbols_mentioned"]:
            score += 0.3
        if analysis["actions_found"]:
            score += 0.25
        if analysis["price_levels"]:
            score += 0.2
        if len(text.split()) > 10:
            score += 0.15
        if analysis["sentiment"] != "neutral":
            score += 0.1

        analysis["confidence_score"] = min(score, 1.0)

        # Only return if substantial trading content
        if analysis["confidence_score"] > 0.3:
            return analysis

        return None

    async def generate_comprehensive_report(self, signals):
        """Generate comprehensive trading analysis report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Analyze data
        all_symbols = []
        all_sentiments = []
        all_confidences = []
        all_risks = []

        for signal in signals:
            all_symbols.extend(signal.get('symbols_mentioned', []))
            all_sentiments.append(signal.get('sentiment', 'neutral'))
            all_confidences.append(signal.get('confidence_score', 0))
            all_risks.append(signal.get('risk_level', 'unknown'))

        symbol_counts = Counter(all_symbols)
        sentiment_counts = Counter(all_sentiments)
        risk_counts = Counter(all_risks)
        avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0

        # Time analysis
        dates = [datetime.fromisoformat(signal['date'].replace('Z', '+00:00')) for signal in signals]
        if dates:
            latest_signal = max(dates)
            earliest_signal = min(dates)
            time_span = latest_signal - earliest_signal
        else:
            time_span = timedelta(0)

        # Save JSON report
        json_file = os.path.join(self.results_dir, f"telegram_lite_trading_report_{timestamp}.json")
        report = {
            "extraction_summary": {
                "target_group": self.target_group,
                "total_signals": len(signals),
                "average_confidence": avg_confidence,
                "time_span_hours": time_span.total_seconds() / 3600,
                "extraction_date": datetime.now().isoformat(),
                "method": "Telegram Lite/Desktop Session Extraction"
            },
            "symbol_analysis": dict(symbol_counts.most_common(10)),
            "sentiment_analysis": dict(sentiment_counts.most_common()),
            "risk_analysis": dict(risk_counts.most_common()),
            "signals": signals
        }

        with open(json_file, 'w') as f:
            json.dump(report, f, indent=2)

        # Generate readable report
        readable_file = os.path.join(self.results_dir, f"telegram_lite_trading_summary_{timestamp}.txt")
        readable_report = f"""
🚀 TELEGRAM LITE/TRADING DESKTOP TRADING ANALYSIS REPORT
========================================================

📅 Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
🎯 Target Group: {self.target_group}
💻 Method: Existing Telegram Session Extraction
📊 Trading Signals Found: {len(signals)}
📈 Average Confidence: {avg_confidence:.1%}
⏱️  Time Span: {time_span.days} days, {time_span.seconds // 3600} hours

📊 TOP SYMBOLS MENTIONED:
------------------------
"""

        if symbol_counts:
            for symbol, count in symbol_counts.most_common(10):
                readable_report += f"   • {symbol}: {count} signals\n"

        readable_report += f"""
😊 SENTIMENT ANALYSIS:
--------------------
"""

        if sentiment_counts:
            for sentiment, count in sentiment_counts.most_common():
                readable_report += f"   • {sentiment.title()}: {count} signals\n"

        readable_report += f"""
⚠️ RISK ANALYSIS:
----------------
"""

        if risk_counts:
            for risk, count in risk_counts.most_common():
                readable_report += f"   • {risk.title()} Risk: {count} signals\n"

        readable_report += f"""
📋 RECENT TRADING SIGNALS:
-------------------------
"""

        # Show last 5 signals
        sorted_signals = sorted(signals, key=lambda x: x['date'], reverse=True)[:5]
        for i, signal in enumerate(sorted_signals, 1):
            signal_date = datetime.fromisoformat(signal['date'].replace('Z', '+00:00'))
            readable_report += f"\n{i}. Signal from {signal_date.strftime('%Y-%m-%d %H:%M')} (Confidence: {signal['confidence_score']:.1%})\n"
            readable_report += f"   📊 Symbols: {', '.join(signal['symbols_mentioned'])}\n"
            readable_report += f"   🎯 Actions: {', '.join(signal['actions_found'])}\n"
            readable_report += f"   💰 Prices: {', '.join(signal['price_levels'][:3])}\n"
            readable_report += f"   😊 Sentiment: {signal['sentiment'].title()}\n"
            readable_report += f"   ⚠️  Risk: {signal['risk_level'].title()}\n"
            readable_report += f"   📝 Text: {signal['original_text'][:150]}...\n"

        with open(readable_file, 'w') as f:
            f.write(readable_report)

        # Display results
        print("\n" + "=" * 70)
        print("🎉 TELEGRAM LITE TRADING EXTRACTION COMPLETE!")
        print("=" * 70)
        print(f"📊 Trading Signals Found: {len(signals)}")
        print(f"📈 Average Confidence: {avg_confidence:.1%}")
        if symbol_counts:
            top_symbol = symbol_counts.most_common(1)[0]
            print(f"📈 Top Symbol: {top_symbol[0]} ({top_symbol[1]} mentions)")
        print(f"⏱️  Time Span: {time_span.days} days")
        print(f"💾 JSON Report: {json_file}")
        print(f"📋 Summary: {readable_file}")
        print("=" * 70)

async def main():
    """Main execution function"""
    extractor = TelegramLiteTradingExtractor()
    await extractor.extract_trading_signals()

if __name__ == "__main__":
    asyncio.run(main())