#!/usr/bin/env python3
"""
Telegram Bot API Scraper
Uses public Bot API to analyze telegram groups when available
"""

import os
import json
import logging
import requests
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TelegramBotScraper:
    def __init__(self):
        self.results_dir = "telegram_bot_scraping"
        os.makedirs(self.results_dir, exist_ok=True)

        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.results = {
            "scraping_session": datetime.now().isoformat(),
            "method": "Bot API",
            "results": []
        }

    def get_bot_info(self):
        """Get bot information"""
        if not self.bot_token:
            logger.error("❌ No bot token provided")
            return None

        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/getMe"
            response = requests.get(url)

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"❌ Bot API error: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"❌ Error getting bot info: {e}")
            return None

    def get_updates(self):
        """Get recent updates"""
        if not self.bot_token:
            return None

        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/getUpdates"
            response = requests.get(url)

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"❌ Bot API error: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"❌ Error getting updates: {e}")
            return None

    def analyze_updates_for_trading(self, updates):
        """Analyze updates for trading content"""
        trading_signals = []

        if not updates or 'result' not in updates:
            return trading_signals

        for update in updates['result']:
            if 'message' in update and 'text' in update['message']:
                message = update['message']['text']
                message_data = {
                    'message_id': update['message']['message_id'],
                    'text': message,
                    'date': datetime.fromtimestamp(update['message']['date']).isoformat(),
                    'chat_title': update['message']['chat'].get('title', 'Unknown'),
                    'chat_id': update['message']['chat']['id']
                }

                # Check for trading content
                if self.contains_trading_content(message):
                    trading_analysis = self.analyze_trading_text(message)
                    trading_analysis.update(message_data)
                    trading_signals.append(trading_analysis)

        return trading_signals

    def contains_trading_content(self, text):
        """Check if text contains trading content"""
        if not text:
            return False

        trading_keywords = [
            'buy', 'sell', 'long', 'short', 'hold', 'trade',
            'btc', 'eth', 'bitcoin', 'ethereum', 'sol', 'bnb',
            'price', 'target', 'stop', 'entry', 'exit'
        ]

        return any(keyword.lower() in text.lower() for keyword in trading_keywords)

    def analyze_trading_text(self, text):
        """Analyze text for trading signals"""
        analysis = {
            'original_text': text,
            'symbols_found': [],
            'actions_found': [],
            'confidence': 0.0
        }

        text_lower = text.lower()

        # Find symbols
        symbols = re.findall(r'\b(btc|eth|sol|bnb|ada|dot|avax|matic|link|uni)\b', text_lower)
        analysis['symbols_found'] = list(set([s.upper() for s in symbols]))

        # Find actions
        actions = re.findall(r'\b(buy|sell|long|short|hold)\b', text_lower)
        analysis['actions_found'] = list(set([a.upper() for a in actions]))

        # Calculate confidence
        if analysis['symbols_found']:
            analysis['confidence'] += 0.5
        if analysis['actions_found']:
            analysis['confidence'] += 0.5

        return analysis

    def save_results(self):
        """Save scraping results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save JSON
        json_file = os.path.join(self.results_dir, f"bot_scraping_results_{timestamp}.json")
        with open(json_file, 'w') as f:
            json.dump(self.results, f, indent=2)

        # Save report
        report_file = os.path.join(self.results_dir, f"bot_scraping_report_{timestamp}.txt")
        with open(report_file, 'w') as f:
            f.write("🤖 TELEGRAM BOT API SCRAPING RESULTS\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Method: Bot API\n")
            f.write(f"Status: {'Success' if self.results else 'Failed'}\n\n")

            trading_signals = []
            for result in self.results.get('results', []):
                if result.get('trading_signals'):
                    trading_signals.extend(result['trading_signals'])

            if trading_signals:
                f.write(f"💰 Trading Signals Found: {len(trading_signals)}\n\n")
                for signal in trading_signals:
                    f.write(f"📊 Signal:\n")
                    f.write(f"   Text: {signal['original_text'][:100]}...\n")
                    f.write(f"   Symbols: {signal.get('symbols_found', [])}\n")
                    f.write(f"   Actions: {signal.get('actions_found', [])}\n")
                    f.write(f"   Date: {signal['date']}\n\n")
            else:
                f.write("❌ No trading signals found\n")

        logger.info(f"💾 Results saved: {json_file}")
        logger.info(f"📋 Report saved: {report_file}")

    def run_scraper(self):
        """Run the bot scraper"""
        logger.info("🚀 STARTING TELEGRAM BOT API SCRAPING")
        logger.info("=" * 50)

        # Get bot info
        logger.info("🤖 Getting bot information...")
        bot_info = self.get_bot_info()

        if not bot_info:
            logger.error("❌ Could not get bot info")
            return

        logger.info(f"✅ Bot: {bot_info['result']['username']}")

        # Try to get updates
        logger.info("📥 Getting recent updates...")
        updates = self.get_updates()

        if not updates:
            logger.error("❌ Could not get updates")
            return

        logger.info(f"📊 Found {len(updates.get('result', []))} updates")

        # Analyze for trading content
        trading_signals = self.analyze_updates_for_trading(updates)

        if trading_signals:
            self.results['results'] = [{
                'trading_signals': trading_signals,
                'total_updates': len(updates.get('result', []))
            }]
            logger.info(f"💰 Found {len(trading_signals)} trading signals")
        else:
            logger.info("ℹ️ No trading signals found in updates")

        # Save results
        self.save_results()

        logger.info("\n" + "="*50)
        logger.info("🎯 BOT API SCRAPING COMPLETED")
        logger.info("=" * 50)

if __name__ == "__main__":
    scraper = TelegramBotScraper()
    scraper.run_scraper()