#!/usr/bin/env python3
"""
Enhanced Trading Bot Monitor
Uses your existing bot to monitor for trading signals
"""

import os
import json
import logging
import requests
import time
from datetime import datetime, timedelta
from telegram.ext import Updater, CommandHandler, MessageHandler, filters

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedTradingBot:
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN', '8279702044:AAEMfTZBZmRKjazkGjiSeLhWwEU9eTdjw-Q')
        self.trading_signals = []
        self.results_dir = "enhanced_bot_results"
        os.makedirs(self.results_dir, exist_ok=True)

        # Track bot activity
        self.start_time = datetime.now()
        self.messages_received = []

    def setup_bot_handlers(self):
        """Set up bot command handlers"""
        try:
            updater = Updater(token=self.bot_token, use_context=True)
            dispatcher = updater.dispatcher

            # Command handlers
            dispatcher.add_handler(CommandHandler("start", self.start_command))
            dispatcher.add_handler(CommandHandler("help", self.help_command))
            dispatcher.add_handler(CommandHandler("status", self.status_command))
            dispatcher.add_handler(CommandHandler("analyze", self.analyze_command))
            dispatcher.add_handler(CommandHandler("report", self.report_command))

            # Message handler for all text messages
            dispatcher.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

            logger.info("✅ Bot handlers configured successfully")
            return updater

        except Exception as e:
            logger.error(f"❌ Error setting up bot handlers: {e}")
            return None

    def start_command(self, update, context):
        """Handle /start command"""
        welcome_message = """
🚀 **Trading Signal Monitor Bot**

I'm here to help you analyze trading signals!

**Commands:**
/help - Show all commands
/status - Show bot status and recent activity
/analyze - Analyze all received messages for trading signals
/report - Generate comprehensive trading report

**How to use:**
1. Forward trading signals to me
2. I'll analyze them for trading opportunities
3. Use /report to get detailed analysis
        """
        update.message.reply_text(welcome_message, parse_mode='Markdown')

    def help_command(self, update, context):
        """Handle /help command"""
        help_text = """
📊 **Trading Bot Commands**

/start - Start using the bot
/help - Show this help message
/status - Show bot statistics and activity
/analyze - Analyze messages for trading signals
/report - Generate detailed trading report

**Signal Analysis Features:**
• Detects trading symbols (BTC, ETH, SOL, etc.)
• Identifies actions (BUY, SELL, LONG, SHORT)
• Extracts price levels and targets
• Calculates confidence scores
• Tracks timestamp data

**Usage:**
Forward any trading signals to this bot, then use /report to get analysis!
        """
        update.message.reply_text(help_text, parse_mode='Markdown')

    def status_command(self, update, context):
        """Handle /status command"""
        runtime = datetime.now() - self.start_time
        status_text = f"""
📈 **Bot Status Report**

**Runtime:** {runtime}
**Messages Received:** {len(self.messages_received)}
**Trading Signals Found:** {len(self.trading_signals)}
**Bot Token:** Active ✅

**Last 5 Messages:**
"""

        for i, msg in enumerate(self.messages_received[-5:], 1):
            status_text += f"{i}. {msg['text'][:50]}...\n"

        update.message.reply_text(status_text, parse_mode='Markdown')

    def analyze_command(self, update, context):
        """Handle /analyze command"""
        self.analyze_all_messages()

        if self.trading_signals:
            response = f"""
🔍 **Analysis Complete**

**Trading Signals Found:** {len(self.trading_signals)}

**Top Signals:**
"""
            for i, signal in enumerate(self.trading_signals[:3], 1):
                symbols = signal.get('symbols_mentioned', [])
                actions = signal.get('actions_found', [])
                confidence = signal.get('confidence_score', 0)

                response += f"\n{i}. Symbols: {', '.join(symbols)} | Actions: {', '.join(actions)} | Confidence: {confidence:.1%}"

            response += "\n\nUse /report for detailed analysis!"
        else:
            response = "❌ No trading signals found yet. Forward some trading messages first!"

        update.message.reply_text(response, parse_mode='Markdown')

    def report_command(self, update, context):
        """Handle /report command"""
        report = self.generate_comprehensive_report()

        # Save report to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = os.path.join(self.results_dir, f"trading_report_{timestamp}.txt")

        with open(report_file, 'w') as f:
            f.write(report)

        # Send summary to user
        summary = f"""
📊 **Comprehensive Report Generated**

**Total Messages:** {len(self.messages_received)}
**Trading Signals:** {len(self.trading_signals)}
**Report Saved:** trading_report_{timestamp}.txt

**Key Findings:**
{self.get_key_findings()}
        """

        update.message.reply_text(summary, parse_mode='Markdown')

    def handle_message(self, update, context):
        """Handle incoming text messages"""
        message_data = {
            'message_id': update.message.message_id,
            'text': update.message.text,
            'date': update.message.date.isoformat(),
            'from_user': update.message.from_user.username if update.message.from_user else 'Unknown'
        }

        self.messages_received.append(message_data)

        # Analyze for trading content
        if self.contains_trading_content(update.message.text):
            trading_analysis = self.analyze_trading_text(update.message.text, update.message.date)
            trading_analysis.update(message_data)
            self.trading_signals.append(trading_analysis)

            # Send quick analysis
            symbols = trading_analysis.get('symbols_mentioned', [])
            if symbols:
                quick_response = f"🎯 **Trading Signal Detected**\nSymbols: {', '.join(symbols)}\nAnalyzing... use /report for details!"
                update.message.reply_text(quick_response, parse_mode='Markdown')

        logger.info(f"📨 Message received: {update.message.text[:50]}...")

    def contains_trading_content(self, text):
        """Check if text contains trading-related content"""
        if not text:
            return False

        text_lower = text.lower()
        trading_keywords = [
            'buy', 'sell', 'long', 'short', 'hold', 'trade',
            'btc', 'eth', 'bitcoin', 'ethereum', 'sol', 'bnb',
            'price', 'target', 'stop', 'entry', 'exit',
            'bullish', 'bearish', 'signal', 'analysis',
            'leverage', 'position', 'portfolio'
        ]

        return any(keyword in text_lower for keyword in trading_keywords)

    def analyze_trading_text(self, message_text, message_date):
        """Extract trading signals from message text"""
        import re

        text_lower = message_text.lower()

        trading_analysis = {
            "original_text": message_text,
            "date": message_date.isoformat(),
            "symbols_mentioned": [],
            "actions_found": [],
            "price_levels": [],
            "timeframes": [],
            "confidence_score": 0.0
        }

        # Extract crypto symbols
        crypto_symbols = re.findall(r'\b(btc|eth|sol|bnb|ada|dot|avax|matic|link|uni|atom|xrp)\b', text_lower)
        trading_analysis["symbols_mentioned"] = list(set([sym.upper() for sym in crypto_symbols]))

        # Extract trading actions
        actions = re.findall(r'\b(buy|sell|long|short|hold|entry|exit|target|stop)\b', text_lower)
        trading_analysis["actions_found"] = list(set([action.upper() for action in actions]))

        # Extract price levels
        prices = re.findall(r'\$?\d{1,5}[.,]?\d{0,4}', text_lower)
        trading_analysis["price_levels"] = list(set(prices))

        # Extract timeframes
        timeframes = re.findall(r'\b(1m|5m|15m|30m|1h|4h|1d|1w)\b', text_lower)
        trading_analysis["timeframes"] = list(set(timeframes))

        # Calculate confidence score
        if trading_analysis["actions_found"]:
            trading_analysis["confidence_score"] += 0.3
        if trading_analysis["symbols_mentioned"]:
            trading_analysis["confidence_score"] += 0.3
        if trading_analysis["price_levels"]:
            trading_analysis["confidence_score"] += 0.2
        if len(message_text.split()) > 20:
            trading_analysis["confidence_score"] += 0.2

        trading_analysis["confidence_score"] = min(trading_analysis["confidence_score"], 1.0)

        return trading_analysis

    def analyze_all_messages(self):
        """Analyze all messages for trading signals"""
        for message in self.messages_received:
            if self.contains_trading_content(message['text']):
                # Check if already analyzed
                if not any(signal.get('message_id') == message['message_id'] for signal in self.trading_signals):
                    trading_analysis = self.analyze_trading_text(message['text'], datetime.fromisoformat(message['date'].replace('Z', '+00:00')))
                    trading_analysis['message_id'] = message['message_id']
                    trading_analysis['from_user'] = message['from_user']
                    self.trading_signals.append(trading_analysis)

    def generate_comprehensive_report(self):
        """Generate comprehensive trading report"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        report = f"""
🚀 ENHANCED TRADING BOT REPORT
============================

Generated: {timestamp}
Bot: @Das_ts_bot
Runtime: {datetime.now() - self.start_time}

📊 SUMMARY:
------------
• Total Messages Received: {len(self.messages_received)}
• Trading Signals Identified: {len(self.trading_signals)}
• Signal Success Rate: {len(self.trading_signals)/max(len(self.messages_received), 1):.1%}

💰 TRADING SIGNALS ANALYSIS:
-----------------------------
"""

        if self.trading_signals:
            # Most common symbols
            all_symbols = []
            for signal in self.trading_signals:
                all_symbols.extend(signal.get('symbols_mentioned', []))

            symbol_counts = {}
            for symbol in all_symbols:
                symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1

            if symbol_counts:
                report += "\nMost Mentioned Symbols:\n"
                for symbol, count in sorted(symbol_counts.items(), key=lambda x: x[1], reverse=True):
                    report += f"  • {symbol}: {count} times\n"

            # Trading actions
            all_actions = []
            for signal in self.trading_signals:
                all_actions.extend(signal.get('actions_found', []))

            action_counts = {}
            for action in all_actions:
                action_counts[action] = action_counts.get(action, 0) + 1

            if action_counts:
                report += "\nTrading Actions Distribution:\n"
                for action, count in sorted(action_counts.items(), key=lambda x: x[1], reverse=True):
                    report += f"  • {action}: {count} signals\n"

            # High confidence signals
            high_confidence = [s for s in self.trading_signals if s.get('confidence_score', 0) > 0.7]

            report += f"\nHigh Confidence Signals: {len(high_confidence)}/{len(self.trading_signals)}\n\n"

            # Detailed signals
            report += "📈 DETAILED SIGNALS:\n"
            report += "-" * 30 + "\n"

            for i, signal in enumerate(self.trading_signals, 1):
                report += f"\n🎯 SIGNAL #{i}:\n"
                report += f"   Date: {signal.get('date', 'Unknown')}\n"
                report += f"   From: {signal.get('from_user', 'Unknown')}\n"

                if signal.get('symbols_mentioned'):
                    report += f"   Symbols: {', '.join(signal['symbols_mentioned'])}\n"
                if signal.get('actions_found'):
                    report += f"   Actions: {', '.join(signal['actions_found'])}\n"
                if signal.get('price_levels'):
                    report += f"   Price Levels: {', '.join(signal['price_levels'][:3])}\n"

                report += f"   Confidence: {signal.get('confidence_score', 0):.1%}\n"
                report += f"   Message: {signal.get('original_text', 'No text')[:100]}...\n"
        else:
            report += "\n❌ No trading signals found in any messages.\n"
            report += "💡 Forward some trading signals to the bot to get started!\n"

        report += f"\n📋 ALL MESSAGES:\n"
        report += "-" * 20 + "\n"

        for i, msg in enumerate(self.messages_received[-10:], 1):  # Last 10 messages
            report += f"\n{i}. [{msg.get('date', 'Unknown')}] {msg.get('text', 'No text')[:80]}...\n"

        return report

    def get_key_findings(self):
        """Get key findings summary"""
        if not self.trading_signals:
            return "No trading signals detected yet"

        # Get top symbols
        all_symbols = []
        for signal in self.trading_signals:
            all_symbols.extend(signal.get('symbols_mentioned', []))

        if all_symbols:
            from collections import Counter
            symbol_counts = Counter(all_symbols)
            top_symbol = symbol_counts.most_common(1)[0]

            high_confidence = len([s for s in self.trading_signals if s.get('confidence_score', 0) > 0.7])

            return f"Top symbol: {top_symbol[0]} ({top_symbol[1]} mentions) | High confidence signals: {high_confidence}"

        return f"Found {len(self.trading_signals)} trading signals"

    def start_bot(self):
        """Start the bot"""
        try:
            updater = self.setup_bot_handlers()
            if updater:
                logger.info("🚀 Starting Enhanced Trading Bot...")
                logger.info(f"🤖 Bot Name: @Das_ts_bot")
                logger.info("📊 Commands: /start, /help, /status, /analyze, /report")
                logger.info("💡 Forward trading signals to the bot for analysis!")

                # Start the bot
                updater.start_polling()
                updater.idle()
            else:
                logger.error("❌ Failed to initialize bot handlers")

        except Exception as e:
            logger.error(f"❌ Error starting bot: {e}")

def main():
    """Main function"""
    print("🚀 ENHANCED TRADING BOT MONITOR")
    print("=" * 40)
    print("🤖 Bot: @Das_ts_bot")
    print("📊 Features: Trading signal analysis, confidence scoring")
    print("💡 Forward trading signals to the bot for automatic analysis!")
    print("=" * 40)

    bot = EnhancedTradingBot()
    bot.start_bot()

if __name__ == "__main__":
    main()