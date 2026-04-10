#!/usr/bin/env python3
"""
OPENTELE TRADING MONITOR
Uses existing Telegram Desktop sessions without API credentials
Multiple approaches to find and access Telegram sessions
"""

import os
import json
import asyncio
import logging
from datetime import datetime, timedelta
from collections import Counter
from typing import List, Dict, Any, Optional

# Import OpenTele
try:
    from opentele import TelegramDesktop
    from opentele.td import TdLib
except ImportError as e:
    print(f"❌ OpenTele not found: {e}")
    print("💡 Install with: pip3 install opentele")
    exit(1)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OpenTeleTradingMonitor:
    """Trading monitor using OpenTele with existing Telegram Desktop session"""

    def __init__(self, target_group: int = -2127259353):
        self.target_group = target_group
        self.tdesk = None
        self.trading_signals = []
        self.monitoring_active = False

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

    def find_telegram_sessions(self) -> List[str]:
        """Find possible Telegram Desktop session paths"""
        possible_paths = []

        # macOS Telegram Desktop paths
        macos_paths = [
            os.path.expanduser("~/Library/Application Support/Telegram Desktop"),
            os.path.expanduser("~/Library/Application Support/TelegramDesktop"),
            os.path.expanduser("~/Library/Application Support/Telegram"),
            os.path.expanduser("~/Library/Telegram Desktop"),
            os.path.expanduser("~/Telegram Desktop"),
            "/Applications/Telegram Desktop.app/Contents/Resources",
        ]

        # Check each path
        for path in macos_paths:
            if os.path.exists(path):
                # Look for tdata directory
                tdata_path = os.path.join(path, "tdata")
                if os.path.exists(tdata_path):
                    possible_paths.append(tdata_path)
                    logger.info(f"✅ Found Telegram session at: {tdata_path}")
                else:
                    # Check if the path itself is the tdata
                    if any(f in os.listdir(path) for f in ["D877F783D5D3EF8C", "maps", "user_data"]):
                        possible_paths.append(path)
                        logger.info(f"✅ Found Telegram session at: {path}")

        return possible_paths

    async def setup_opentele(self, session_path: Optional[str] = None) -> bool:
        """Setup OpenTele connection to Telegram Desktop"""
        try:
            logger.info("🔧 Setting up OpenTele connection...")

            if session_path:
                # Use provided session path
                logger.info(f"📁 Using session path: {session_path}")
                self.tdesk = TelegramDesktop(session_path)
            else:
                # Try auto-detection
                logger.info("🔍 Auto-detecting Telegram sessions...")
                sessions = self.find_telegram_sessions()

                if not sessions:
                    logger.error("❌ No Telegram Desktop sessions found")
                    logger.info("💡 Please install Telegram Desktop or provide session path")
                    return False

                # Use first found session
                session_path = sessions[0]
                logger.info(f"📁 Using session: {session_path}")
                self.tdesk = TelegramDesktop(session_path)

            # Connect to the session
            logger.info("🔗 Connecting to Telegram Desktop session...")
            self.tdesk.Connect()

            # Check if connected
            if self.tdesk.IsConnected():
                logger.info("✅ Successfully connected to Telegram Desktop!")
                return True
            else:
                logger.error("❌ Failed to connect to Telegram Desktop")
                return False

        except Exception as e:
            logger.error(f"❌ Error setting up OpenTele: {e}")
            return False

    def analyze_trading_message(self, message_text: str, message_date: datetime) -> Dict[str, Any]:
        """Analyze message for trading signals"""
        text_upper = message_text.upper()
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
        import re
        symbol_pattern = r'\b(' + '|'.join(self.crypto_symbols) + r')(?:/USDT|/USD)?\b'
        symbols = re.findall(symbol_pattern, text_upper)
        analysis["symbols_mentioned"] = list(set(symbols))

        # Extract trading actions
        action_pattern = r'\b(' + '|'.join(self.trading_actions) + r')\b'
        actions = re.findall(action_pattern, text_upper)
        analysis["actions_found"] = list(set(actions))

        # Extract price levels
        price_pattern = r'\$\d{1,5}[.,]?\d{0,4}'
        prices = re.findall(price_pattern, message_text)
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
        if len(message_text.split()) > 10:
            score += 0.1

        analysis["confidence_score"] = min(score, 1.0)

        return analysis

    async def get_group_messages(self, limit: int = 100) -> List[Dict]:
        """Get messages from the target group"""
        try:
            logger.info(f"📥 Getting messages from group {self.target_group}...")

            # Try to get messages
            messages = []

            # Different methods to get messages
            try:
                # Method 1: Get by group ID
                messages = self.tdesk.GetMessages(self.target_group, limit=limit)
                logger.info(f"✅ Retrieved {len(messages)} messages via group ID")
            except:
                try:
                    # Method 2: Search for group
                    # This would require knowing the group name or having a search function
                    logger.warning("⚠️ Cannot access group by ID, trying alternative methods...")

                    # For now, we'll create a demo message structure
                    # In real implementation, you'd need to navigate to the group
                    return []

                except Exception as e:
                    logger.error(f"❌ Error getting messages: {e}")
                    return []

            # Analyze messages for trading signals
            trading_signals = []
            for msg in messages:
                if hasattr(msg, 'text') and msg.text:
                    analysis = self.analyze_trading_message(msg.text, msg.date)
                    if analysis["confidence_score"] > 0.3:
                        analysis.update({
                            "message_id": getattr(msg, 'id', None),
                            "sender_id": getattr(msg, 'sender_id', None),
                            "group_id": self.target_group,
                            "method": "opentele"
                        })
                        trading_signals.append(analysis)

            logger.info(f"🎯 Found {len(trading_signals)} trading signals")
            return trading_signals

        except Exception as e:
            logger.error(f"❌ Error getting group messages: {e}")
            return []

    def generate_report(self, signals: List[Dict]) -> Dict[str, Any]:
        """Generate comprehensive trading report"""
        if not signals:
            return {
                "summary": "No trading signals found",
                "total_signals": 0,
                "signals": []
            }

        # Analyze symbol frequency
        all_symbols = []
        for signal in signals:
            all_symbols.extend(signal.get('symbols_mentioned', []))

        symbol_counts = Counter(all_symbols)

        # Analyze sentiment
        sentiments = [s.get('sentiment', 'neutral') for s in signals]
        sentiment_counts = Counter(sentiments)

        report = {
            "monitoring_summary": {
                "total_signals": len(signals),
                "monitoring_method": "OpenTele Desktop",
                "target_group": self.target_group,
                "timestamp": datetime.now().isoformat()
            },
            "symbol_analysis": dict(symbol_counts.most_common(5)),
            "sentiment_analysis": dict(sentiment_counts.most_common()),
            "signals": signals
        }

        return report

    def save_results(self, report: Dict[str, Any]):
        """Save monitoring results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_dir = "opentele_monitoring_results"
        os.makedirs(results_dir, exist_ok=True)

        # Save JSON report
        json_file = os.path.join(results_dir, f"opentele_trading_report_{timestamp}.json")
        with open(json_file, 'w') as f:
            json.dump(report, f, indent=2)

        # Save readable summary
        summary_file = os.path.join(results_dir, f"opentele_summary_{timestamp}.txt")
        with open(summary_file, 'w') as f:
            f.write(self.generate_readable_report(report))

        logger.info(f"💾 Results saved: {json_file}")
        logger.info(f"📋 Summary saved: {summary_file}")

        return json_file, summary_file

    def generate_readable_report(self, report: Dict[str, Any]) -> str:
        """Generate human-readable report"""
        summary = report.get("monitoring_summary", {})
        symbols = report.get("symbol_analysis", {})
        sentiments = report.get("sentiment_analysis", {})

        readable = f"""
🚀 OPENTELE TRADING MONITORING REPORT
======================================

📅 Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
🎯 Target Group: {summary.get('target_group', 'Unknown')}
💻 Method: {summary.get('monitoring_method', 'Unknown')}

📊 SUMMARY:
-----------
• Total Trading Signals: {summary.get('total_signals', 0)}
• Monitoring Date: {summary.get('timestamp', 'Unknown')}

"""

        if symbols:
            readable += "📈 SYMBOLS MENTIONED:\n"
            for symbol, count in symbols.items():
                readable += f"   • {symbol}: {count} times\n"
            readable += "\n"

        if sentiments:
            readable += "😊 SENTIMENT ANALYSIS:\n"
            for sentiment, count in sentiments.items():
                readable += f"   • {sentiment.title()}: {count} signals\n"
            readable += "\n"

        if report.get("signals"):
            readable += "📋 DETAILED SIGNALS:\n"
            readable += "-" * 40 + "\n"

            for i, signal in enumerate(report["signals"][:5], 1):  # First 5 signals
                readable += f"\n{i}. SIGNAL\n"
                readable += f"   📅 Time: {signal.get('date', 'Unknown')}\n"
                readable += f"   📊 Symbols: {', '.join(signal.get('symbols_mentioned', []))}\n"
                readable += f"   🎯 Actions: {', '.join(signal.get('actions_found', []))}\n"
                readable += f"   💰 Prices: {', '.join(signal.get('price_levels', []))}\n"
                readable += f"   📈 Confidence: {signal.get('confidence_score', 0):.1%}\n"
                readable += f"   😊 Sentiment: {signal.get('sentiment', 'neutral').title()}\n"
                readable += f"   📝 Message: {signal.get('original_text', '')[:100]}...\n"

        return readable

async def main():
    """Main execution function"""
    print("🚀 OPENTELE TRADING MONITOR")
    print("=" * 50)
    print("💻 Using existing Telegram Desktop session")
    print("🎯 No API credentials required")
    print("=" * 50)

    monitor = OpenTeleTradingMonitor()

    try:
        # Find and setup Telegram session
        sessions = monitor.find_telegram_sessions()

        if not sessions:
            print("\n❌ NO TELEGRAM DESKTOP SESSIONS FOUND")
            print("=" * 50)
            print("💡 Solutions:")
            print("1. Install Telegram Desktop from https://telegram.org/")
            print("2. Login to Telegram Desktop")
            print("3. Run this script again")
            print("4. Or use your bot @Das_ts_bot for manual forwarding")
            print("=" * 50)
            return

        print(f"\n✅ Found {len(sessions)} Telegram Desktop session(s)")
        for i, session in enumerate(sessions, 1):
            print(f"   {i}. {session}")

        # Use first session
        session_path = sessions[0]
        print(f"\n🔗 Using session: {session_path}")

        # Setup OpenTele connection
        if not await monitor.setup_opentele(session_path):
            return

        # Get trading messages
        print("\n📥 Analyzing trading messages...")
        signals = await monitor.get_group_messages(limit=200)

        if signals:
            # Generate report
            report = monitor.generate_report(signals)
            json_file, summary_file = monitor.save_results(report)

            print("\n" + "=" * 60)
            print("🎯 MONITORING COMPLETE!")
            print("=" * 60)
            print(f"📊 Trading Signals Found: {len(signals)}")
            print(f"📈 Top Symbols: {list(report['symbol_analysis'].keys())[:3]}")
            print(f"💾 Report Saved: {summary_file}")
            print("=" * 60)
        else:
            print("\n⚠️ No trading signals found")
            print("💡 This could mean:")
            print("   • Group has no recent trading activity")
            print("   • Session access limitations")
            print("   • Need different message access method")

    except KeyboardInterrupt:
        print("\n⏹️ Monitoring stopped by user")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
    finally:
        if monitor.tdesk:
            try:
                monitor.tdesk.Disconnect()
                logger.info("✅ Disconnected from Telegram Desktop")
            except:
                pass

if __name__ == "__main__":
    asyncio.run(main())