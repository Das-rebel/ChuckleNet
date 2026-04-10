#!/usr/bin/env python3
"""
Simple Working Trading Bot
Uses current python-telegram-bot API
"""

import os
import json
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleTradingBot:
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN', '8279702044:AAEMfTZBZmRKjazkGjiSeLhWwEU9eTdjw-Q')
        self.trading_signals = []
        self.messages_received = []

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        welcome_text = """
🚀 **Trading Signal Monitor Bot**

I'm ready to analyze trading signals for you!

**Available Commands:**
/start - Start using the bot
/help - Show help
/status - Show bot statistics
/analyze - Analyze messages for trading signals
/report - Generate detailed report

**How to use:**
1. Forward trading signals to me
2. I'll automatically analyze them
3. Use /report to get comprehensive analysis

💡 Try forwarding a trading message now!
        """
        await update.message.reply_text(welcome_text, parse_mode='Markdown')

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
📊 **Trading Bot Help**

**Commands:**
/start - Welcome message
/help - This help message
/status - Bot statistics and activity
/analyze - Quick signal analysis
/report - Full trading report

**What I can analyze:**
• Trading symbols (BTC, ETH, SOL, etc.)
• Buy/Sell signals
• Price targets and levels
• Timeframes
• Confidence scoring

**Usage:**
Forward any trading signal to me, and I'll analyze it automatically!
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        status_text = f"""
📈 **Bot Status**

🤖 **Bot:** @Das_ts_bot ✅
📨 **Messages Received:** {len(self.messages_received)}
🎯 **Trading Signals Found:** {len(self.trading_signals)}
📊 **Analysis Rate:** {len(self.trading_signals)/max(len(self.messages_received), 1):.1%}

**Recent Activity:**
"""
        for i, msg in enumerate(self.messages_received[-3:], 1):
            status_text += f"{i}. {msg['text'][:40]}...\n"

        await update.message.reply_text(status_text, parse_mode='Markdown')

    async def analyze_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /analyze command"""
        if self.trading_signals:
            analysis_text = f"""
🔍 **Signal Analysis**

**Trading Signals Found:** {len(self.trading_signals)}

**Top Signals:**
"""
            for i, signal in enumerate(self.trading_signals[:3], 1):
                symbols = signal.get('symbols_mentioned', ['None'])
                actions = signal.get('actions_found', ['None'])
                confidence = signal.get('confidence_score', 0)

                analysis_text += f"\n{i}. {', '.join(symbols)} - {', '.join(actions)} ({confidence:.1%} confidence)"

            analysis_text += "\n\nUse /report for detailed analysis!"
        else:
            analysis_text = "❌ No trading signals found yet.\n💡 Forward some trading signals to get started!"

        await update.message.reply_text(analysis_text, parse_mode='Markdown')

    async def report_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /report command"""
        report = self.generate_report()

        # Save report to file
        results_dir = "enhanced_bot_results"
        os.makedirs(results_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = os.path.join(results_dir, f"trading_report_{timestamp}.txt")

        with open(report_file, 'w') as f:
            f.write(report)

        # Send summary
        summary = f"""
📊 **Trading Report Generated**

📈 **Messages Analyzed:** {len(self.messages_received)}
🎯 **Signals Found:** {len(self.trading_signals)}
📁 **Report Saved:** trading_report_{timestamp}.txt

**Key Findings:**
{self.get_key_findings()}

📋 Full report saved with detailed analysis!
        """
        await update.message.reply_text(summary, parse_mode='Markdown')

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming messages"""
        message_data = {
            'message_id': update.message.message_id,
            'text': update.message.text,
            'date': update.message.date.isoformat(),
            'from_user': update.message.from_user.username if update.message.from_user else 'Unknown'
        }

        self.messages_received.append(message_data)
        logger.info(f"📨 Message received: {update.message.text[:50]}...")

        # Analyze for trading content
        if self.contains_trading_content(update.message.text):
            trading_analysis = self.analyze_trading_text(update.message.text, update.message.date)
            trading_analysis.update(message_data)
            self.trading_signals.append(trading_analysis)

            # Send quick notification
            symbols = trading_analysis.get('symbols_mentioned', [])
            if symbols:
                quick_response = f"🎯 **Trading Signal Detected!**\n📊 Symbols: {', '.join(symbols)}\n📈 Confidence: {trading_analysis.get('confidence_score', 0):.1%}\n\n💡 Use /report for detailed analysis!"
                await update.message.reply_text(quick_response, parse_mode='Markdown')

    def contains_trading_content(self, text):
        """Check if text contains trading content"""
        if not text:
            return False

        trading_keywords = [
            'buy', 'sell', 'long', 'short', 'hold', 'trade',
            'btc', 'eth', 'bitcoin', 'ethereum', 'sol', 'bnb',
            'price', 'target', 'stop', 'entry', 'exit',
            'bullish', 'bearish', 'signal', 'analysis'
        ]

        return any(keyword.lower() in text.lower() for keyword in trading_keywords)

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
            "confidence_score": 0.0
        }

        # Extract symbols
        symbols = re.findall(r'\b(btc|eth|sol|bnb|ada|dot|avax|matic|link|uni|atom|xrp)\b', text_lower)
        analysis["symbols_mentioned"] = list(set([sym.upper() for sym in symbols]))

        # Extract actions
        actions = re.findall(r'\b(buy|sell|long|short|hold|entry|exit|target|stop)\b', text_lower)
        analysis["actions_found"] = list(set([action.upper() for action in actions]))

        # Extract prices
        prices = re.findall(r'\$?\d{1,5}[.,]?\d{0,4}', text_lower)
        analysis["price_levels"] = list(set(prices))

        # Calculate confidence
        if analysis["symbols_mentioned"]:
            analysis["confidence_score"] += 0.4
        if analysis["actions_found"]:
            analysis["confidence_score"] += 0.3
        if analysis["price_levels"]:
            analysis["confidence_score"] += 0.2
        if len(message_text.split()) > 15:
            analysis["confidence_score"] += 0.1

        analysis["confidence_score"] = min(analysis["confidence_score"], 1.0)

        return analysis

    def generate_report(self):
        """Generate comprehensive report"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        report = f"""
🚀 TRADING BOT ANALYSIS REPORT
============================

📅 Generated: {timestamp}
🤖 Bot: @Das_ts_bot
📊 Method: Message Analysis

📈 SUMMARY:
-----------
• Total Messages: {len(self.messages_received)}
• Trading Signals: {len(self.trading_signals)}
• Success Rate: {len(self.trading_signals)/max(len(self.messages_received), 1):.1%}

"""

        if self.trading_signals:
            # Symbol analysis
            all_symbols = []
            for signal in self.trading_signals:
                all_symbols.extend(signal.get('symbols_mentioned', []))

            if all_symbols:
                from collections import Counter
                symbol_counts = Counter(all_symbols)
                report += "📊 Most Mentioned Symbols:\n"
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
            high_conf = len([s for s in self.trading_signals if s.get('confidence_score', 0) > 0.7])
            report += f"\n🔥 High Confidence Signals: {high_conf}/{len(self.trading_signals)}\n\n"

            # Detailed signals
            report += "📋 DETAILED SIGNALS:\n"
            report += "-" * 25 + "\n"

            for i, signal in enumerate(self.trading_signals, 1):
                report += f"\n{i}. **Signal**\n"
                report += f"   Date: {signal.get('date', 'Unknown')}\n"
                report += f"   Symbols: {', '.join(signal.get('symbols_mentioned', []))}\n"
                report += f"   Actions: {', '.join(signal.get('actions_found', []))}\n"
                report += f"   Confidence: {signal.get('confidence_score', 0):.1%}\n"
                report += f"   Message: {signal.get('original_text', '')[:100]}...\n"
        else:
            report += "❌ No trading signals detected\n"
            report += "💡 Forward trading messages to the bot to start analysis!\n"

        return report

    def get_key_findings(self):
        """Get key findings summary"""
        if not self.trading_signals:
            return "No trading signals found yet"

        # Most common symbol
        all_symbols = []
        for signal in self.trading_signals:
            all_symbols.extend(signal.get('symbols_mentioned', []))

        if all_symbols:
            from collections import Counter
            symbol_counts = Counter(all_symbols)
            top_symbol = symbol_counts.most_common(1)[0]

            avg_confidence = sum(s.get('confidence_score', 0) for s in self.trading_signals) / len(self.trading_signals)

            return f"Top: {top_symbol[0]} ({top_symbol[1]}×) | Avg confidence: {avg_confidence:.1%}"

        return f"Found {len(self.trading_signals)} trading signals"

    def run_bot(self):
        """Start the bot"""
        try:
            # Create application
            application = Application.builder().token(self.bot_token).build()

            # Add handlers
            application.add_handler(CommandHandler("start", self.start_command))
            application.add_handler(CommandHandler("help", self.help_command))
            application.add_handler(CommandHandler("status", self.status_command))
            application.add_handler(CommandHandler("analyze", self.analyze_command))
            application.add_handler(CommandHandler("report", self.report_command))
            application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

            logger.info("🚀 Starting Simple Trading Bot...")
            logger.info(f"🤖 Bot: @Das_ts_bot")
            logger.info("📊 Ready to analyze trading signals!")

            # Start bot
            application.run_polling()

        except Exception as e:
            logger.error(f"❌ Bot error: {e}")

def main():
    """Main function"""
    print("🚀 SIMPLE WORKING TRADING BOT")
    print("=" * 40)
    print("🤖 Bot: @Das_ts_bot")
    print("📊 Features: Real-time trading signal analysis")
    print("💡 Forward trading signals to get started!")
    print("=" * 40)

    bot = SimpleTradingBot()
    bot.run_bot()

if __name__ == "__main__":
    main()