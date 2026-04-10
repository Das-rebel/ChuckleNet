#!/usr/bin/env python3
"""
Telethon Group Monitor - Uses your Telegram account to monitor groups
No admin permissions needed - just your account membership
"""

import os
import json
import logging
import asyncio
from datetime import datetime, timedelta
import re
from telethon import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TelethonGroupMonitor:
    def __init__(self):
        self.target_group_id = -2127259353
        self.results_dir = "telethon_monitoring"
        os.makedirs(self.results_dir, exist_ok=True)

        # Telegram API credentials (need to be set)
        self.api_id = None
        self.api_hash = None
        self.phone = None

        # Monitoring data
        self.trading_signals = []
        self.messages_analyzed = []
        self.monitoring_active = True

    async def initialize_client(self):
        """Initialize Telegram client with your account"""
        # Get API credentials from environment
        self.api_id = os.getenv('TELEGRAM_API_ID')
        self.api_hash = os.getenv('TELEGRAM_API_HASH')
        self.phone = os.getenv('TELEGRAM_PHONE')

        if not all([self.api_id, self.api_hash, self.phone]):
            print("❌ Missing Telegram API credentials")
            print("\n📋 How to set them:")
            print("export TELEGRAM_API_ID='your_api_id'")
            print("export TELEGRAM_API_HASH='your_api_hash'")
            print("export TELEGRAM_PHONE='+1234567890'")
            print("\n📖 Get API credentials: https://my.telegram.org/")
            return None

        try:
            # Convert api_id to integer
            self.api_id = int(self.api_id)
        except ValueError:
            print("❌ TELEGRAM_API_ID must be a number")
            return None

        # Create Telegram client
        client = TelegramClient('group_monitor_session', self.api_id, self.api_hash)

        try:
            await client.connect()
            logger.info("✅ Connected to Telegram")

            # Check if already authorized
            if not await client.is_user_authorized():
                logger.info("📱 Sending verification code...")
                await client.send_code_request(self.phone)
                code = input("🔢 Enter the verification code you received: ")
                await client.sign_in(self.phone, code)

            logger.info("✅ Successfully logged in!")
            return client

        except Exception as e:
            logger.error(f"❌ Failed to initialize client: {e}")
            return None

    async def access_target_group(self, client):
        """Access the target group"""
        try:
            logger.info(f"🔍 Accessing group ID: {self.target_group_id}")

            # Try to get the group by ID
            group = await client.get_entity(self.target_group_id)
            logger.info(f"✅ Found group: {group.title}")
            logger.info(f"👥 Members: {getattr(group, 'participants_count', 'Unknown')}")

            return group

        except Exception as e:
            logger.error(f"❌ Cannot access group: {e}")
            print(f"\n💡 Solutions:")
            print(f"1. Make sure you're a member of the group")
            print(f"2. Check if the group ID is correct: {self.target_group_id}")
            print(f"3. Some private groups require admin approval")
            return None

    async def get_recent_messages(self, client, group, limit=100, days_back=3):
        """Get recent messages from the group"""
        messages = []

        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        logger.info(f"📥 Extracting messages from {group.title}")
        logger.info(f"📅 Last {days_back} days, max {limit} messages")

        try:
            # Get message history
            history = await client(GetHistoryRequest(
                peer=group,
                limit=limit,
                offset_date=start_date,
                reverse=True
            ))

            logger.info(f"📊 Found {len(history.messages)} messages")

            for message in history.messages:
                if hasattr(message, 'message') and message.message:
                    message_data = {
                        "id": message.id,
                        "text": message.message,
                        "date": message.date.isoformat(),
                        "from_user": getattr(message, 'from_id', 'Unknown'),
                        "group_name": group.title,
                        "group_id": group.id
                    }

                    messages.append(message_data)

                    # Check for trading content
                    if self.contains_trading_content(message.message):
                        trading_analysis = self.analyze_trading_message(
                            message.message, message.date
                        )
                        trading_analysis.update(message_data)
                        self.trading_signals.append(trading_analysis)
                        logger.info(f"🎯 Trading signal found: {trading_analysis.get('symbols_mentioned', [])}")

            self.messages_analyzed = messages
            logger.info(f"✅ Processed {len(messages)} messages")
            logger.info(f"🎯 Found {len(self.trading_signals)} trading signals")

            return messages

        except Exception as e:
            logger.error(f"❌ Error getting messages: {e}")
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
            'pump', 'breakout', 'resistance', 'support'
        ]

        return any(keyword.lower() in text.lower() for keyword in trading_keywords)

    def analyze_trading_message(self, message_text, message_date):
        """Analyze message for trading signals"""
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
        actions = re.findall(r'\b(buy|sell|long|short|hold|entry|exit|target|stop|takeprofit|tp|sl|short|long)\b', text_lower)
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
        json_file = os.path.join(self.results_dir, f"telethon_results_{timestamp}.json")
        results = {
            "monitoring_session": datetime.now().isoformat(),
            "target_group": self.target_group_id,
            "messages_analyzed": len(self.messages_analyzed),
            "trading_signals_found": len(self.trading_signals),
            "signals": self.trading_signals,
            "messages": self.messages_analyzed
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
        """Generate comprehensive trading report"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        report = f"""
🚀 TELETHON GROUP MONITORING REPORT
===================================

📅 Generated: {timestamp}
🎯 Target Group: {self.target_group_id}
📊 Method: Telethon User API

📈 SUMMARY:
-----------
• Messages Analyzed: {len(self.messages_analyzed)}
• Trading Signals Found: {len(self.trading_signals)}
• Signal Success Rate: {len(self.trading_signals)/max(len(self.messages_analyzed), 1):.1%}

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

            # Sentiment analysis
            sentiments = [s.get('sentiment', 'neutral') for s in self.trading_signals]
            if sentiments:
                sentiment_counts = Counter(sentiments)
                report += "\n😊 Market Sentiment:\n"
                for sentiment, count in sentiment_counts.most_common():
                    report += f"   • {sentiment.title()}: {count} signals ({count/len(sentiments):.1%})\n"

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
            report += "\n❌ No trading signals found in the analyzed messages.\n"
            report += "💡 The group might not have recent trading activity.\n"

        return report

    def print_summary(self):
        """Print monitoring summary"""
        print("\n" + "="*50)
        print("🎯 TELETHON GROUP MONITORING COMPLETE!")
        print("="*50)
        print(f"📊 Messages Analyzed: {len(self.messages_analyzed)}")
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

    async def run_monitoring(self):
        """Main monitoring function"""
        print("🚀 TELETHON GROUP MONITOR")
        print("="*40)
        print(f"🎯 Target Group: {self.target_group_id}")
        print(f"📊 Method: Your Telegram Account")
        print("="*40)

        try:
            # Initialize client
            client = await self.initialize_client()
            if not client:
                return

            # Access target group
            group = await self.access_target_group(client)
            if not group:
                await client.disconnect()
                return

            # Get recent messages
            messages = await self.get_recent_messages(client, group, limit=200, days_back=7)

            if messages:
                print(f"\n✅ Successfully analyzed {len(messages)} messages")
                print(f"🎯 Found {len(self.trading_signals)} trading signals")

                # Save results
                json_file, report_file = self.save_results()

                # Print summary
                self.print_summary()

                print(f"\n💾 Results saved:")
                print(f"   📊 JSON: {json_file}")
                print(f"   📋 Report: {report_file}")

            else:
                print("❌ No messages found or couldn't access the group")

            await client.disconnect()

        except Exception as e:
            logger.error(f"❌ Monitoring error: {e}")
            print(f"\n❌ Error: {e}")

def main():
    """Main function"""
    monitor = TelethonGroupMonitor()

    try:
        asyncio.run(monitor.run_monitoring())
    except KeyboardInterrupt:
        print("\n⚠️ Monitoring cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()