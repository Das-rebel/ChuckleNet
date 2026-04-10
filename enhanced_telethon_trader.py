#!/usr/bin/env python3
"""
ENHANCED TELETHON TRADING MONITOR
Based on best GitHub solutions - Informer & Telethon approaches
Advanced trading signal analysis with real-time monitoring
"""

import asyncio
import logging
import re
import json
import os
from datetime import datetime, timedelta
from collections import Counter
from typing import List, Dict, Any

# Import Telethon (install with: pip install telethon)
try:
    from telethon import TelegramClient, events
    from telethon.errors import (
        ApiIdInvalidError,
        PhoneNumberInvalidError,
        UserPrivacyRestrictionError,
        ChannelPrivateError
    )
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("❌ Telethon or python-dotenv not installed. Run: pip install telethon python-dotenv")
    exit(1)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EnhancedTelethonTrader:
    """Advanced Telegram trading monitor with analysis capabilities"""

    def __init__(self, api_id: int = None, api_hash: str = None, phone: str = None):
        self.api_id = api_id or int(os.getenv('TELEGRAM_API_ID', 0))
        self.api_hash = api_hash or os.getenv('TELEGRAM_API_HASH', '')
        self.phone = phone or os.getenv('TELEGRAM_PHONE', '')

        self.target_group = -2127259353
        self.client = None
        self.trading_signals = []
        self.messages_processed = 0
        self.monitoring_active = False

        # Trading analysis settings
        self.crypto_symbols = {
            'BTC', 'ETH', 'SOL', 'BNB', 'ADA', 'DOT', 'AVAX',
            'MATIC', 'LINK', 'UNI', 'ATOM', 'XRP', 'DOGE', 'SHIB',
            'LTC', 'CRO', 'FTM', 'SAND', 'MANA', 'AXS'
        }

        self.trading_actions = {
            'BUY', 'SELL', 'LONG', 'SHORT', 'HOLD', 'ENTRY',
            'EXIT', 'TARGET', 'STOP', 'TAKEPROFIT', 'TP', 'SL'
        }

        self.timeframes = {
            '1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w',
            'DAILY', 'WEEKLY', 'HOURLY', 'MINUTES'
        }

    async def setup_client(self):
        """Initialize and authenticate Telethon client"""
        try:
            self.client = TelegramClient('trading_monitor_session', self.api_id, self.api_hash)

            logger.info("🔧 Initializing Telethon client...")
            await self.client.start(phone=self.phone)

            me = await self.client.get_me()
            logger.info(f"✅ Successfully logged in as: {me.first_name} {me.last_name or ''}")

            return True

        except ApiIdInvalidError:
            logger.error("❌ Invalid API ID/Hash. Please check your credentials")
            return False
        except PhoneNumberInvalidError:
            logger.error("❌ Invalid phone number")
            return False
        except Exception as e:
            logger.error(f"❌ Error setting up client: {e}")
            return False

    def analyze_trading_message(self, message_text: str) -> Dict[str, Any]:
        """Advanced trading signal analysis"""
        text_upper = message_text.upper()
        text_lower = message_text.lower()

        analysis = {
            "original_text": message_text,
            "symbols_mentioned": [],
            "actions_found": [],
            "price_levels": [],
            "timeframes": [],
            "confidence_score": 0.0,
            "sentiment": "neutral",
            "risk_level": "unknown",
            "trade_type": "unknown",
            "extracted_patterns": []
        }

        # Extract crypto symbols with advanced patterns
        symbol_patterns = [
            r'\b(' + '|'.join(self.crypto_symbols) + r')(?:/USDT|/USD|/BUSD)?\b',
            r'\$(' + '|'.join(self.crypto_symbols) + r')\b',
        ]

        for pattern in symbol_patterns:
            matches = re.findall(pattern, text_upper)
            analysis["symbols_mentioned"].extend(matches)

        analysis["symbols_mentioned"] = list(set(analysis["symbols_mentioned"]))

        # Extract trading actions
        action_pattern = r'\b(' + '|'.join(self.trading_actions) + r')\b'
        actions = re.findall(action_pattern, text_upper)
        analysis["actions_found"] = list(set(actions))

        # Extract price levels with various formats
        price_patterns = [
            r'\$\d{1,5}[.,]?\d{0,4}',
            r'\d{1,5}[.,]?\d{0,4}\s*(?:USD|USDT)',
            r'PRICE[:\s]*\$\d{1,5}[.,]?\d{0,4}',
            r'TARGET[:\s]*\$\d{1,5}[.,]?\d{0,4}',
            r'STOP(?:LOSS)?:\s*\$\d{1,5}[.,]?\d{0,4}'
        ]

        for pattern in price_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            analysis["price_levels"].extend(matches)

        analysis["price_levels"] = list(set(analysis["price_levels"]))

        # Extract timeframes
        timeframe_pattern = r'\b(' + '|'.join(self.timeframes) + r')\b'
        timeframes = re.findall(timeframe_pattern, text_upper)
        analysis["timeframes"] = list(set(timeframes))

        # Advanced sentiment analysis
        bullish_indicators = [
            '🚀', '📈', 'BULLISH', 'MOON', 'PUMP', 'BUY', 'LONG',
            'BREAKOUT', 'ABOVE', 'HIGHER', 'UP', 'ROCKET', 'BULL'
        ]

        bearish_indicators = [
            '📉', '🔻', 'BEARISH', 'DUMP', 'SELL', 'SHORT',
            'CRASH', 'FALL', 'BELOW', 'LOWER', 'DOWN', 'BEAR'
        ]

        bullish_count = sum(1 for indicator in bullish_indicators if indicator in text_upper)
        bearish_count = sum(1 for indicator in bearish_indicators if indicator in text_upper)

        if bullish_count > bearish_count:
            analysis["sentiment"] = "bullish"
        elif bearish_count > bullish_count:
            analysis["sentiment"] = "bearish"

        # Risk level assessment
        if any(word in text_lower for word in ['high risk', 'risky', 'dangerous']):
            analysis["risk_level"] = "high"
        elif any(word in text_lower for word in ['low risk', 'safe', 'conservative']):
            analysis["risk_level"] = "low"
        else:
            analysis["risk_level"] = "medium"

        # Trade type classification
        if 'scalp' in text_lower:
            analysis["trade_type"] = "scalping"
        elif 'swing' in text_lower:
            analysis["trade_type"] = "swing"
        elif 'long' in text_lower or 'invest' in text_lower:
            analysis["trade_type"] = "position"
        else:
            analysis["trade_type"] = "day"

        # Extract trading patterns
        patterns = []

        # Pattern 1: Symbol + Action + Price
        for symbol in analysis["symbols_mentioned"]:
            for action in analysis["actions_found"]:
                pattern = f"{symbol} {action}"
                if pattern in message_text.upper():
                    patterns.append(pattern)

        # Pattern 2: Price targets
        if analysis["price_levels"]:
            for price in analysis["price_levels"][:3]:  # Limit to first 3
                patterns.append(f"PRICE: {price}")

        analysis["extracted_patterns"] = patterns

        # Calculate confidence score
        score = 0.0
        if analysis["symbols_mentioned"]:
            score += 0.3
        if analysis["actions_found"]:
            score += 0.25
        if analysis["price_levels"]:
            score += 0.2
        if analysis["timeframes"]:
            score += 0.1
        if analysis["sentiment"] != "neutral":
            score += 0.1
        if len(message_text.split()) > 15:
            score += 0.05

        analysis["confidence_score"] = min(score, 1.0)

        return analysis

    async def process_message(self, message):
        """Process incoming message for trading signals"""
        try:
            if not message.text:
                return

            text = message.text.strip()
            if len(text) < 10:  # Skip very short messages
                return

            # Quick check for trading keywords
            trading_keywords = {
                'buy', 'sell', 'btc', 'eth', 'sol', 'trade', 'target',
                'stop', 'entry', 'exit', 'long', 'short', 'signal'
            }

            if not any(keyword in text.lower() for keyword in trading_keywords):
                return

            # Analyze the message
            analysis = self.analyze_trading_message(text)

            # Add metadata
            analysis.update({
                "message_id": message.id,
                "sender_id": message.sender_id,
                "date": message.date.isoformat(),
                "group_id": self.target_group,
                "processed_at": datetime.now().isoformat()
            })

            # Only save high-confidence signals
            if analysis["confidence_score"] > 0.4:
                self.trading_signals.append(analysis)
                self.messages_processed += 1

                logger.info(f"🎯 Trading Signal #{len(self.trading_signals)}")
                logger.info(f"   📊 Symbols: {analysis['symbols_mentioned']}")
                logger.info(f"   🎯 Actions: {analysis['actions_found']}")
                logger.info(f"   📈 Confidence: {analysis['confidence_score']:.1%}")
                logger.info(f"   😊 Sentiment: {analysis['sentiment']}")

        except Exception as e:
            logger.error(f"❌ Error processing message: {e}")

    async def monitor_group(self, duration_minutes: int = 30):
        """Monitor group for specified duration"""
        try:
            # Try to access the group
            try:
                entity = await self.client.get_entity(self.target_group)
                logger.info(f"✅ Accessing group: {entity.title}")
            except (ChannelPrivateError, UserPrivacyRestrictionError) as e:
                logger.error(f"❌ Cannot access group {self.target_group}: {e}")
                logger.info("💡 This group requires membership or has privacy restrictions")
                return False
            except ValueError as e:
                logger.error(f"❌ Group not found: {e}")
                return False

            self.monitoring_active = True
            logger.info(f"🔍 Starting monitoring for {duration_minutes} minutes...")

            @self.client.on(events.NewMessage(chats=self.target_group))
            async def message_handler(event):
                if self.monitoring_active:
                    await self.process_message(event.message)

            # Keep monitoring for specified duration
            await asyncio.sleep(duration_minutes * 60)

            logger.info(f"⏹️ Monitoring complete. Processed {self.messages_processed} messages")
            return True

        except Exception as e:
            logger.error(f"❌ Error during monitoring: {e}")
            return False

    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate detailed trading analysis report"""
        if not self.trading_signals:
            return {
                "summary": "No trading signals found during monitoring period",
                "total_signals": 0,
                "signals": []
            }

        # Analyze symbol frequency
        all_symbols = []
        for signal in self.trading_signals:
            all_symbols.extend(signal.get('symbols_mentioned', []))

        symbol_counts = Counter(all_symbols)

        # Analyze action frequency
        all_actions = []
        for signal in self.trading_signals:
            all_actions.extend(signal.get('actions_found', []))

        action_counts = Counter(all_actions)

        # Analyze sentiment distribution
        sentiments = [s.get('sentiment', 'neutral') for s in self.trading_signals]
        sentiment_counts = Counter(sentiments)

        # High confidence signals
        high_confidence = [s for s in self.trading_signals if s.get('confidence_score', 0) > 0.7]

        report = {
            "monitoring_summary": {
                "total_signals": len(self.trading_signals),
                "high_confidence_signals": len(high_confidence),
                "average_confidence": sum(s.get('confidence_score', 0) for s in self.trading_signals) / len(self.trading_signals),
                "monitoring_period": f"{datetime.now().isoformat()}",
                "messages_processed": self.messages_processed
            },
            "symbol_analysis": {
                "most_mentioned": dict(symbol_counts.most_common(5)),
                "total_unique_symbols": len(symbol_counts)
            },
            "action_analysis": dict(action_counts.most_common()),
            "sentiment_analysis": dict(sentiment_counts.most_common()),
            "signals": self.trading_signals
        }

        return report

    def save_results(self, report: Dict[str, Any]):
        """Save results to files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_dir = "enhanced_telethon_monitoring"
        os.makedirs(results_dir, exist_ok=True)

        # Save detailed JSON report
        json_file = os.path.join(results_dir, f"trading_report_{timestamp}.json")
        with open(json_file, 'w') as f:
            json.dump(report, f, indent=2)

        # Save readable summary
        summary_file = os.path.join(results_dir, f"trading_summary_{timestamp}.txt")
        with open(summary_file, 'w') as f:
            f.write(self.generate_readable_report(report))

        logger.info(f"💾 Results saved: {json_file}")
        logger.info(f"📋 Summary saved: {summary_file}")

        return json_file, summary_file

    def generate_readable_report(self, report: Dict[str, Any]) -> str:
        """Generate human-readable report"""
        summary = report.get("monitoring_summary", {})
        symbols = report.get("symbol_analysis", {})
        actions = report.get("action_analysis", {})
        sentiments = report.get("sentiment_analysis", {})

        readable = f"""
🚀 ENHANCED TELETHON TRADING MONITORING REPORT
===============================================

📅 Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
🎯 Target Group: {self.target_group}

📊 SUMMARY:
-----------
• Total Trading Signals: {summary.get('total_signals', 0)}
• High Confidence Signals: {summary.get('high_confidence_signals', 0)}
• Average Confidence: {summary.get('average_confidence', 0):.1%}
• Messages Processed: {summary.get('messages_processed', 0)}

"""

        if symbols.get("most_mentioned"):
            readable += "📈 MOST MENTIONED SYMBOLS:\n"
            for symbol, count in symbols["most_mentioned"].items():
                readable += f"   • {symbol}: {count} times\n"
            readable += "\n"

        if actions:
            readable += "🎯 TRADING ACTIONS:\n"
            for action, count in actions.items():
                readable += f"   • {action}: {count} signals\n"
            readable += "\n"

        if sentiments:
            readable += "😊 SENTIMENT ANALYSIS:\n"
            for sentiment, count in sentiments.items():
                readable += f"   • {sentiment.title()}: {count} signals\n"
            readable += "\n"

        if report.get("signals"):
            readable += "📋 DETAILED SIGNALS:\n"
            readable += "-" * 40 + "\n"

            for i, signal in enumerate(report["signals"][-5:], 1):  # Last 5 signals
                readable += f"\n{i}. SIGNAL ANALYSIS\n"
                readable += f"   📅 Time: {signal.get('date', 'Unknown')}\n"
                readable += f"   📊 Symbols: {', '.join(signal.get('symbols_mentioned', []))}\n"
                readable += f"   🎯 Actions: {', '.join(signal.get('actions_found', []))}\n"
                readable += f"   💰 Prices: {', '.join(signal.get('price_levels', [])[:3])}\n"
                readable += f"   📈 Confidence: {signal.get('confidence_score', 0):.1%}\n"
                readable += f"   😊 Sentiment: {signal.get('sentiment', 'neutral').title()}\n"
                readable += f"   🔧 Type: {signal.get('trade_type', 'unknown').title()}\n"
                readable += f"   ⚠️ Risk: {signal.get('risk_level', 'unknown').title()}\n"
                readable += f"   📝 Message: {signal.get('original_text', '')[:150]}...\n"

        return readable

async def main():
    """Main execution function"""
    print("🚀 ENHANCED TELETHON TRADING MONITOR")
    print("=" * 50)
    print("📊 Advanced trading signal analysis")
    print("🎯 Real-time group monitoring")
    print("⚡ High-confidence signal detection")
    print("=" * 50)

    # Check credentials
    if not os.getenv('TELEGRAM_API_ID') or not os.getenv('TELEGRAM_API_HASH'):
        print("❌ Missing Telegram API credentials!")
        print("💡 Set environment variables:")
        print("   export TELEGRAM_API_ID=your_api_id")
        print("   export TELEGRAM_API_HASH=your_api_hash")
        print("   export TELEGRAM_PHONE=your_phone_number")
        print()
        print("🔧 Or run: python3 setup_telethon_credentials.py")
        return

    # Initialize monitor
    monitor = EnhancedTelethonTrader()

    try:
        # Setup client
        if not await monitor.setup_client():
            return

        # Start monitoring for 30 minutes (adjust as needed)
        success = await monitor.monitor_group(duration_minutes=30)

        if success:
            # Generate and save report
            report = monitor.generate_comprehensive_report()
            json_file, summary_file = monitor.save_results(report)

            print("\n" + "=" * 60)
            print("🎯 MONITORING COMPLETE!")
            print("=" * 60)
            print(f"📊 Trading Signals Found: {len(monitor.trading_signals)}")
            print(f"📈 High Confidence: {len([s for s in monitor.trading_signals if s.get('confidence_score', 0) > 0.7])}")
            print(f"💾 Report Saved: {summary_file}")
            print("=" * 60)
        else:
            print("❌ Monitoring failed - check group access permissions")

    except KeyboardInterrupt:
        print("\n⏹️ Monitoring stopped by user")
        if monitor.trading_signals:
            report = monitor.generate_comprehensive_report()
            monitor.save_results(report)
            print(f"💾 Saved {len(monitor.trading_signals)} collected signals")

    finally:
        if monitor.client:
            await monitor.client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())