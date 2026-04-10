#!/usr/bin/env python3
"""
Professional Telegram API Scraper
Uses Telethon to connect to Telegram API and extract actual messages from channels
"""

import os
import json
import logging
import asyncio
from datetime import datetime, timedelta
import re
from telethon import TelegramClient, events
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.types import InputPeerChannel

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TelegramAPIScraper:
    def __init__(self):
        self.results_dir = "telegram_api_scraping"
        os.makedirs(self.results_dir, exist_ok=True)

        self.scraping_results = {
            "scraping_session": datetime.now().isoformat(),
            "messages_extracted": [],
            "trading_signals": [],
            "channel_info": {},
            "api_method": "Telethon"
        }

        # Telegram API credentials (need to be set by user)
        self.api_id = None
        self.api_hash = None
        self.phone = None

    async def initialize_client(self):
        """Initialize Telegram client with API credentials"""
        # Get API credentials from environment variables
        self.api_id = os.getenv('TELEGRAM_API_ID')
        self.api_hash = os.getenv('TELEGRAM_API_HASH')
        self.phone = os.getenv('TELEGRAM_PHONE')

        if not all([self.api_id, self.api_hash]):
            logger.error("❌ Missing Telegram API credentials")
            logger.error("Please set environment variables:")
            logger.error("export TELEGRAM_API_ID='your_api_id'")
            logger.error("export TELEGRAM_API_HASH='your_api_hash'")
            logger.error("export TELEGRAM_PHONE='your_phone_number'")
            return None

        # Convert api_id to integer if it's a string
        try:
            self.api_id = int(self.api_id)
        except ValueError:
            logger.error("❌ TELEGRAM_API_ID must be a valid integer")
            return None

        # Create Telegram client
        client = TelegramClient('session_name', self.api_id, self.api_hash)

        try:
            await client.start(self.phone)
            logger.info("✅ Telegram client initialized successfully")
            return client
        except Exception as e:
            logger.error(f"❌ Failed to initialize Telegram client: {e}")
            return None

    async def get_channel_by_username(self, client, channel_username):
        """Get channel by username"""
        try:
            entity = await client.get_entity(channel_username)
            logger.info(f"✅ Found channel: {entity.title}")
            return entity
        except Exception as e:
            logger.error(f"❌ Could not find channel {channel_username}: {e}")
            return None

    async def get_channel_messages(self, client, channel_entity, limit=100, days_back=3):
        """Get messages from a channel"""
        messages = []

        # Calculate the date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        logger.info(f"📥 Extracting messages from {channel_entity.title}")
        logger.info(f"📅 Looking for messages from last {days_back} days")

        try:
            # Get message history
            history = await client(GetHistoryRequest(
                peer=channel_entity,
                limit=limit,
                offset_date=start_date,
                reverse=True
            ))

            for message in history.messages:
                if hasattr(message, 'message') and message.message:
                    message_data = {
                        "id": message.id,
                        "text": message.message,
                        "date": message.date.isoformat(),
                        "sender": getattr(message, 'sender_id', None),
                        "channel_id": channel_entity.id,
                        "channel_title": channel_entity.title
                    }

                    messages.append(message_data)

                    # Check for trading content
                    if self.contains_trading_content(message.message):
                        trading_analysis = self.analyze_trading_message(message.message, message.date)
                        trading_analysis["message_id"] = message.id
                        trading_analysis["channel"] = channel_entity.title
                        trading_analysis["date"] = message.date.isoformat()
                        self.scraping_results["trading_signals"].append(trading_analysis)

            logger.info(f"✅ Extracted {len(messages)} messages")
            return messages

        except Exception as e:
            logger.error(f"❌ Error getting messages: {e}")
            return []

    def contains_trading_content(self, text):
        """Check if message contains trading-related content"""
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

    def analyze_trading_message(self, message_text, message_date):
        """Extract trading signals from message text"""
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

    def save_results(self):
        """Save scraping results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save JSON results
        json_file = os.path.join(self.results_dir, f"telegram_api_results_{timestamp}.json")
        with open(json_file, 'w') as f:
            json.dump(self.scraping_results, f, indent=2)

        # Save readable report
        text_file = os.path.join(self.results_dir, f"telegram_trading_report_{timestamp}.txt")
        with open(text_file, 'w') as f:
            f.write("🚀 TELEGRAM API SCRAPING RESULTS\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Scraping Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Method: Telethon API\n")
            f.write(f"Channel: https://web.telegram.org/k/#-2127259353\n\n")

            messages = self.scraping_results["messages_extracted"]
            trading_signals = self.scraping_results["trading_signals"]

            f.write(f"📊 SUMMARY:\n")
            f.write(f"• Total Messages Extracted: {len(messages)}\n")
            f.write(f"• Trading Signals Found: {len(trading_signals)}\n")
            f.write(f"• Date Range: Last 3 days\n\n")

            if trading_signals:
                f.write("💰 TRADING SIGNALS FOUND:\n")
                f.write("-" * 30 + "\n")

                for i, signal in enumerate(trading_signals[:10], 1):
                    f.write(f"\n🎯 SIGNAL #{i}:\n")
                    f.write(f"   Date: {signal['date']}\n")
                    f.write(f"   Channel: {signal['channel']}\n")

                    if signal["symbols_mentioned"]:
                        f.write(f"   Symbols: {', '.join(signal['symbols_mentioned'])}\n")
                    if signal["actions_found"]:
                        f.write(f"   Actions: {', '.join(signal['actions_found'])}\n")
                    if signal["price_levels"]:
                        f.write(f"   Price Levels: {', '.join(signal['price_levels'][:3])}\n")

                    f.write(f"   Confidence: {signal['confidence_score']:.2f}\n")
                    f.write(f"   Message: {signal['original_text'][:200]}...\n")

            f.write(f"\n📋 ALL EXTRACTED MESSAGES:\n")
            f.write("-" * 30 + "\n")

            for i, msg in enumerate(messages[:20], 1):
                f.write(f"\n{i}. [{msg['date']}] {msg['text'][:100]}...\n")

        logger.info(f"💾 Results saved: {json_file}")
        logger.info(f"📋 Report saved: {text_file}")

    async def scrape_telegram_channel(self):
        """Main scraping function"""
        logger.info("🚀 STARTING TELEGRAM API SCRAPING")
        logger.info("=" * 50)

        try:
            # Initialize client
            logger.info("🔧 Initializing Telegram client...")
            client = await self.initialize_client()

            if not client:
                logger.error("❌ Failed to initialize Telegram client")
                return

            # Get channel entity
            channel_username = "cryptowarriorsofficial"  # Example - would need the actual channel
            logger.info(f"🔍 Looking for channel: {channel_username}")

            channel_entity = await self.get_channel_by_username(client, channel_username)

            if not channel_entity:
                # Try the actual channel from the URL
                # Extract channel ID from the URL: https://web.telegram.org/k/#-2127259353
                channel_id = -2127259353
                try:
                    logger.info(f"🔍 Trying channel ID: {channel_id}")
                    channel_entity = await client.get_entity(channel_id)
                    logger.info(f"✅ Found channel by ID: {channel_entity.title}")
                except:
                    logger.error("❌ Could not access the target channel")
                    await client.disconnect()
                    return

            # Extract messages
            logger.info("📥 Extracting messages from channel...")
            messages = await self.get_channel_messages(client, channel_entity, limit=100, days_back=3)

            if messages:
                self.scraping_results["messages_extracted"] = messages
                self.scraping_results["channel_info"] = {
                    "title": channel_entity.title,
                    "id": channel_entity.id,
                    "username": getattr(channel_entity, 'username', None)
                }

            # Disconnect
            await client.disconnect()

            # Save results
            logger.info("💾 Saving results...")
            self.save_results()

            # Display summary
            logger.info("\n" + "="*50)
            logger.info("🎯 TELEGRAM API SCRAPING COMPLETED!")
            logger.info("=" * 50)

            logger.info(f"📊 Messages Extracted: {len(messages)}")
            logger.info(f"💰 Trading Signals Found: {len(self.scraping_results['trading_signals'])}")
            logger.info(f"📁 Results saved in {self.results_dir}/")
            logger.info("=" * 50)

            if self.scraping_results["trading_signals"]:
                logger.info(f"\n💰 TRADING SIGNALS DETECTED:")
                for i, signal in enumerate(self.scraping_results["trading_signals"][:5], 1):
                    if signal["symbols_mentioned"]:
                        logger.info(f"{i}. {', '.join(signal['symbols_mentioned'])} - {', '.join(signal['actions_found'])}")
            else:
                logger.info("\nℹ️ No clear trading signals found in extracted messages")

        except Exception as e:
            logger.error(f"❌ Scraping error: {e}")
            import traceback
            traceback.print_exc()

    def run_scraper(self):
        """Run the scraper"""
        try:
            asyncio.run(self.scrape_telegram_channel())
        except Exception as e:
            logger.error(f"❌ Error running scraper: {e}")

if __name__ == "__main__":
    scraper = TelegramAPIScraper()
    scraper.run_scraper()