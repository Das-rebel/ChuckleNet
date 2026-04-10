#!/usr/bin/env python3
"""
Automatic Group Monitor Bot
Joins and monitors a specific Telegram group for trading signals
"""

import os
import json
import logging
import asyncio
from datetime import datetime, timedelta
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AutoGroupMonitor:
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN', '8279702044:AAEMfTZBZmRKjazkGjiSeLhWwEU9eTdjw-Q')
        self.target_group_id = -2127259353  # Your target group
        self.trading_signals = []
        self.messages_captured = []
        self.results_dir = "auto_group_monitoring"
        os.makedirs(self.results_dir, exist_ok=True)

        # Monitoring status
        self.monitoring_active = False
        self.start_time = datetime.now()

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        start_text = f"""
🚀 **Automatic Group Monitor Bot**

I'm configured to automatically monitor the trading group!
**Target Group:** ID {self.target_group_id}
**Status:** {'✅ Active' if self.monitoring_active else '⏳ Standby'}

**Commands:**
/start - Show this message
/help - Show help
/status - Show monitoring status
/join - Try to join target group
/monitor - Start/stop automatic monitoring
/report - Generate comprehensive analysis
/history - Show captured messages

**How it works:**
• I automatically read all messages from the target group
• Trading signals are analyzed in real-time
• Use /report to get trading insights
        """
        await update.message.reply_text(start_text, parse_mode='Markdown')

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = f"""
📊 **Group Monitor Help**

**Target Group:** {self.target_group_id}

**Automatic Features:**
✅ Reads all messages from the group
✅ Detects trading signals automatically
✅ Analyzes symbols and actions
✅ Calculates confidence scores
✅ Builds real-time database
✅ Generates detailed reports

**Commands:**
/join - Join the target group
/monitor - Toggle automatic monitoring
/status - Current monitoring status
/report - Full trading analysis
/history - Show recent captured messages

**Note:** The bot needs to be a member of the target group to read messages. Use /join to attempt joining!
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        runtime = datetime.now() - self.start_time
        signal_rate = len(self.trading_signals) / max(len(self.messages_captured), 1)

        status_text = f"""
📈 **Group Monitor Status**

🎯 **Target Group:** {self.target_group_id}
🤖 **Bot Status:** {'✅ Monitoring' if self.monitoring_active else '⏳ Standby'}
⏱️ **Runtime:** {runtime}
📨 **Messages Captured:** {len(self.messages_captured)}
🎯 **Trading Signals:** {len(self.trading_signals)}
📊 **Signal Rate:** {signal_rate:.1%}

**Recent Activity:**
"""
        for i, msg in enumerate(self.messages_captured[-5:], 1):
            status_text += f"{i}. {msg['text'][:40]}...\n"

        if self.monitoring_active:
            status_text += "\n🔄 **Automatic monitoring is ACTIVE**"
        else:
            status_text += "\n⏸️ **Monitoring is PAUSED** - use /monitor to start"

        await update.message.reply_text(status_text, parse_mode='Markdown')

    async def join_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /join command - try to join target group"""
        try:
            # Get the bot instance
            bot = context.bot

            # Try to get chat info (this works if bot is already member)
            try:
                chat = await bot.get_chat(self.target_group_id)
                await update.message.reply_text(
                    f"✅ **Bot is already a member of the group!**\n\n"
                    f"📛 Group Name: {chat.title}\n"
                    f"👥 Members: {getattr(chat, 'member_count', 'Unknown')}\n"
                    f"🎯 Monitoring ready!",
                    parse_mode='Markdown'
                )
                self.monitoring_active = True
                return

            except Exception as e:
                await update.message.reply_text(
                    f"❌ **Cannot access the group**\n\n"
                    f"🔍 Error: {str(e)}\n\n"
                    f"💡 **Solutions:**\n"
                    f"1. Add the bot manually to the group\n"
                    f"2. Make the bot an admin in the group\n"
                    f"3. Check if the group ID is correct\n\n"
                    f"📝 **Group ID:** {self.target_group_id}",
                    parse_mode='Markdown'
                )

        except Exception as e:
            logger.error(f"Join command error: {e}")
            await update.message.reply_text(f"❌ Error: {e}")

    async def monitor_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /monitor command - toggle monitoring"""
        self.monitoring_active = not self.monitoring_active

        if self.monitoring_active:
            await update.message.reply_text(
                "🟢 **Automatic Monitoring STARTED**\n\n"
                "📡 Now reading messages from the target group\n"
                "🎯 Trading signals will be detected automatically\n"
                "📊 Use /status and /report for insights",
                parse_mode='Markdown'
            )
            logger.info("🟢 Automatic monitoring STARTED")
        else:
            await update.message.reply_text(
                "🔴 **Automatic Monitoring PAUSED**\n\n"
                "⏸️ No longer reading new messages\n"
                "📈 Existing data is preserved\n"
                "▶️ Use /monitor to resume",
                parse_mode='Markdown'
            )
            logger.info("🔴 Automatic monitoring PAUSED")

    async def history_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /history command - show recent messages"""
        if not self.messages_captured:
            await update.message.reply_text("📭 No messages captured yet.\n💡 Use /monitor to start automatic reading!")
            return

        history_text = f"""
📋 **Recent Messages History**

Total captured: {len(self.messages_captured)}
Trading signals: {len(self.trading_signals)}

**Last 10 messages:**
"""
        for i, msg in enumerate(self.messages_captured[-10:], 1):
            timestamp = msg.get('date', 'Unknown')
            text_preview = msg.get('text', 'No text')[:60]
            is_signal = any(signal.get('message_id') == msg['message_id'] for signal in self.trading_signals)
            signal_indicator = "🎯" if is_signal else "📨"

            history_text += f"\n{signal_indicator} {i}. [{timestamp}] {text_preview}..."

        await update.message.reply_text(history_text, parse_mode='Markdown')

    async def report_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /report command - generate comprehensive analysis"""
        report = self.generate_comprehensive_report()

        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = os.path.join(self.results_dir, f"auto_group_report_{timestamp}.txt")

        with open(report_file, 'w') as f:
            f.write(report)

        # Send summary
        summary = f"""
📊 **Automatic Group Report Generated**

🎯 **Group Monitored:** {self.target_group_id}
📈 **Messages Analyzed:** {len(self.messages_captured)}
🎪 **Trading Signals Found:** {len(self.trading_signals)}
📁 **Report Saved:** auto_group_report_{timestamp}.txt

**Key Insights:**
{self.get_key_insights()}

**Monitoring Status:** {'✅ Active' if self.monitoring_active else '⏸️ Paused'}
        """
        await update.message.reply_text(summary, parse_mode='Markdown')

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle messages from monitored group"""
        # Check if message is from our target group
        if update.effective_chat and update.effective_chat.id == self.target_group_id:
            if not self.monitoring_active:
                return  # Skip if monitoring is paused

            message_data = {
                'message_id': update.message.message_id,
                'text': update.message.text,
                'date': update.message.date.isoformat(),
                'from_user': update.message.from_user.username if update.message.from_user else 'Unknown',
                'chat_title': update.effective_chat.title,
                'chat_id': update.effective_chat.id
            }

            self.messages_captured.append(message_data)
            logger.info(f"📨 Captured from group: {update.message.text[:50]}...")

            # Analyze for trading content
            if self.contains_trading_content(update.message.text):
                trading_analysis = self.analyze_trading_text(update.message.text, update.message.date)
                trading_analysis.update(message_data)
                self.trading_signals.append(trading_analysis)

                logger.info(f"🎯 Trading signal detected: {trading_analysis.get('symbols_mentioned', [])}")

    async def handle_private_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle private messages to bot"""
        # Only respond to commands in private chats
        if update.effective_chat.type == 'private':
            # Let the command handlers deal with this
            return

    def contains_trading_content(self, text):
        """Check if text contains trading content"""
        if not text:
            return False

        trading_keywords = [
            'buy', 'sell', 'long', 'short', 'hold', 'trade',
            'btc', 'eth', 'bitcoin', 'ethereum', 'sol', 'bnb',
            'price', 'target', 'stop', 'entry', 'exit',
            'bullish', 'bearish', 'signal', 'analysis',
            'leverage', 'position', 'portfolio', 'moon', 'dump'
        ]

        return any(keyword.lower() in text.lower() for keyword in trading_keywords)

    def analyze_trading_text(self, message_text, message_date):
        """Extract trading signals from message text"""
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
        crypto_symbols = re.findall(r'\b(btc|eth|sol|bnb|ada|dot|avax|matic|link|uni|atom|xrp|doge|shib)\b', text_lower)
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
        bullish_words = ['moon', 'pump', 'bullish', 'buy', 'long', 'rocket', '🚀', '📈']
        bearish_words = ['dump', 'bearish', 'sell', 'short', 'crash', '📉', '🔻']

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

    def generate_comprehensive_report(self):
        """Generate comprehensive report from monitored group"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        report = f"""
🚀 AUTOMATIC GROUP MONITORING REPORT
====================================

📅 Generated: {timestamp}
🎯 Target Group: {self.target_group_id}
🤖 Bot: @Das_ts_bot
⏱️ Monitoring Period: {datetime.now() - self.start_time}

📊 SUMMARY:
------------
• Total Messages Captured: {len(self.messages_captured)}
• Trading Signals Identified: {len(self.trading_signals)}
• Signal Success Rate: {len(self.trading_signals)/max(len(self.messages_captured), 1):.1%}
• Average Confidence: {self.get_average_confidence():.1%}

"""

        if self.trading_signals:
            # Most mentioned symbols
            all_symbols = []
            for signal in self.trading_signals:
                all_symbols.extend(signal.get('symbols_mentioned', []))

            if all_symbols:
                from collections import Counter
                symbol_counts = Counter(all_symbols)
                report += "📈 Most Mentioned Symbols:\n"
                for symbol, count in symbol_counts.most_common(5):
                    report += f"   • {symbol}: {count} times ({count/len(self.trading_signals):.1%})\n"

            # Trading actions analysis
            all_actions = []
            for signal in self.trading_signals:
                all_actions.extend(signal.get('actions_found', []))

            if all_actions:
                action_counts = Counter(all_actions)
                report += "\n🎯 Trading Actions Distribution:\n"
                for action, count in action_counts.most_common():
                    report += f"   • {action}: {count} signals ({count/len(self.trading_signals):.1%})\n"

            # Sentiment analysis
            sentiments = [s.get('sentiment', 'neutral') for s in self.trading_signals]
            if sentiments:
                from collections import Counter
                sentiment_counts = Counter(sentiments)
                report += "\n📊 Market Sentiment Analysis:\n"
                for sentiment, count in sentiment_counts.most_common():
                    report += f"   • {sentiment.title()}: {count} signals ({count/len(sentiments):.1%})\n"

            # High confidence signals
            high_confidence = [s for s in self.trading_signals if s.get('confidence_score', 0) > 0.7]
            report += f"\n🔥 High Confidence Signals: {len(high_confidence)}/{len(self.trading_signals)} ({len(high_confidence)/len(self.trading_signals):.1%})\n\n"

            # Detailed signals
            report += "📋 DETAILED TRADING SIGNALS:\n"
            report += "-" * 35 + "\n"

            for i, signal in enumerate(self.trading_signals, 1):
                report += f"\n{i}. **Trading Signal**\n"
                report += f"   📅 Date: {signal.get('date', 'Unknown')}\n"
                report += f"   👤 From: {signal.get('from_user', 'Unknown')}\n"

                if signal.get('symbols_mentioned'):
                    report += f"   📊 Symbols: {', '.join(signal['symbols_mentioned'])}\n"
                if signal.get('actions_found'):
                    report += f"   🎯 Actions: {', '.join(signal['actions_found'])}\n"
                if signal.get('price_levels'):
                    report += f"   💰 Price Levels: {', '.join(signal['price_levels'][:3])}\n"
                if signal.get('timeframes'):
                    report += f"   ⏰ Timeframes: {', '.join(signal['timeframes'])}\n"

                report += f"   📈 Confidence: {signal.get('confidence_score', 0):.1%}\n"
                report += f"   😊 Sentiment: {signal.get('sentiment', 'neutral').title()}\n"
                report += f"   📝 Message: {signal.get('original_text', '')[:120]}...\n"

        else:
            report += "\n❌ No trading signals detected in the monitored group.\n"
            report += "💡 Ensure the bot is a member of the group and monitoring is active.\n"

        return report

    def get_key_insights(self):
        """Get key insights summary"""
        if not self.trading_signals:
            return "No trading signals found yet"

        # Most active symbol
        all_symbols = []
        for signal in self.trading_signals:
            all_symbols.extend(signal.get('symbols_mentioned', []))

        if all_symbols:
            from collections import Counter
            symbol_counts = Counter(all_symbols)
            top_symbol = symbol_counts.most_common(1)[0]

            avg_confidence = self.get_average_confidence()
            high_conf_rate = len([s for s in self.trading_signals if s.get('confidence_score', 0) > 0.7]) / len(self.trading_signals)

            return f"Top symbol: {top_symbol[0]} ({top_symbol[1]}×) | Avg confidence: {avg_confidence:.1%} | High confidence: {high_conf_rate:.1%}"

        return f"Found {len(self.trading_signals)} trading signals"

    def get_average_confidence(self):
        """Calculate average confidence score"""
        if not self.trading_signals:
            return 0
        return sum(s.get('confidence_score', 0) for s in self.trading_signals) / len(self.trading_signals)

    def run_bot(self):
        """Start the automatic group monitor"""
        try:
            # Create application
            application = Application.builder().token(self.bot_token).build()

            # Add command handlers (only in private chat)
            application.add_handler(CommandHandler("start", self.start_command))
            application.add_handler(CommandHandler("help", self.help_command))
            application.add_handler(CommandHandler("status", self.status_command))
            application.add_handler(CommandHandler("join", self.join_command))
            application.add_handler(CommandHandler("monitor", self.monitor_command))
            application.add_handler(CommandHandler("report", self.report_command))
            application.add_handler(CommandHandler("history", self.history_command))

            # Add message handler for the target group (all messages)
            application.add_handler(MessageHandler(
                filters.Chat(chat_id=self.target_group_id) & filters.TEXT,
                self.handle_message
            ))

            # Add message handler for private chats (commands only) - removed problematic filter
            # application.add_handler(MessageHandler(
            #     filters.PRIVATE & filters.TEXT & ~filters.COMMAND,
            #     self.handle_private_message
            # ))

            logger.info("🚀 Starting Automatic Group Monitor...")
            logger.info(f"🎯 Target Group: {self.target_group_id}")
            logger.info("📊 Ready to automatically monitor trading signals!")
            logger.info("💡 Bot must be added to the target group as a member")

            # Start bot
            application.run_polling()

        except Exception as e:
            logger.error(f"❌ Bot error: {e}")
            print(f"Error starting bot: {e}")

def main():
    """Main function"""
    print("🚀 AUTOMATIC GROUP MONITOR BOT")
    print("=" * 50)
    print("🎯 Target Group: -2127259353")
    print("🤖 Bot: @Das_ts_bot")
    print("📊 Features: Automatic group message monitoring")
    print("💡 Bot needs to be added as group member to work")
    print("=" * 50)

    monitor = AutoGroupMonitor()
    monitor.run_bot()

if __name__ == "__main__":
    main()