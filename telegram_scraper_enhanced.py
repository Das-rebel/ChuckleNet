#!/usr/bin/env python3
"""
Enhanced Telegram Trading Scraper with Configuration Support

Usage:
    python telegram_scraper_enhanced.py [--config trading_config.json] [--headless]

Features:
- Configuration file support
- Enhanced error handling
- Better logging
- Trading signal analysis
- Risk management
- Report generation
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler
from typing import Dict, List, Optional, Tuple

import pandas as pd
from selenium import webdriver
from selenium.common.exceptions import (NoSuchElementException,
                                      StaleElementReferenceException,
                                      TimeoutException)
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options

class TradingConfig:
    """Configuration manager for trading scraper"""

    def __init__(self, config_file: str = "trading_config.json"):
        self.config = self._load_config(config_file)
        self._setup_logging()

    def _load_config(self, config_file: str) -> Dict:
        """Load configuration from JSON file"""
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    return json.load(f)
            else:
                print(f"⚠️  Config file {config_file} not found. Using defaults.")
                return self._get_default_config()
        except Exception as e:
            print(f"❌ Error loading config: {e}. Using defaults.")
            return self._get_default_config()

    def _get_default_config(self) -> Dict:
        """Get default configuration"""
        return {
            "telegram": {
                "channel_url": "https://web.telegram.org/k/#-2127259353",
                "monitoring_duration_minutes": 60,
                "check_interval_seconds": 60
            },
            "trading_strategy": {
                "min_confidence": 0.7,
                "max_trades_per_hour": 5,
                "risk_per_trade": 0.02,
                "symbols_to_track": ["BTC", "ETH", "AAPL", "TSLA", "EUR/USD"],
                "blacklist_symbols": [],
                "reward_risk_ratio": 2.0
            },
            "browser": {
                "headless": False,
                "page_load_timeout": 30,
                "implicit_wait": 10
            }
        }

    def _setup_logging(self):
        """Setup logging configuration"""
        log_config = self.config.get("logging", {})
        log_level = getattr(logging, log_config.get("level", "INFO"))
        log_file = log_config.get("file", "telegram_scraper.log")

        # Create logs directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # Setup rotating file handler
        handler = RotatingFileHandler(
            log_file,
            maxBytes=log_config.get("max_size_mb", 10) * 1024 * 1024,
            backupCount=log_config.get("backup_count", 5)
        )

        # Setup formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)

        # Setup root logger
        logger = logging.getLogger()
        logger.setLevel(log_level)
        logger.addHandler(handler)

        # Also add console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

class TradingSignal:
    """Trading signal data structure"""

    def __init__(self, symbol: str, action: str, confidence: float,
                 timestamp: datetime, message: str, price: float = None,
                 volume: float = None):
        self.symbol = symbol
        self.action = action
        self.confidence = confidence
        self.timestamp = timestamp
        self.message = message
        self.price = price
        self.volume = volume
        self.analysis_notes = ""

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'symbol': self.symbol,
            'action': self.action,
            'confidence': self.confidence,
            'timestamp': self.timestamp.isoformat(),
            'message': self.message,
            'price': self.price,
            'volume': self.volume,
            'analysis_notes': self.analysis_notes
        }

class TelegramTradingScraper:
    """Enhanced Telegram Trading Scraper"""

    def __init__(self, config: TradingConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.driver = None
        self.signals: List[TradingSignal] = []
        self.trades_executed = 0
        self.start_time = datetime.now()

    def setup_browser(self) -> bool:
        """Setup Chrome browser with enhanced options"""
        try:
            browser_config = self.config.config.get("browser", {})
            chrome_options = Options()

            # Basic options
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)

            # Headless mode if specified
            if browser_config.get("headless", False):
                chrome_options.add_argument('--headless=new')

            # Custom user agent if specified
            user_agent = browser_config.get("user_agent")
            if user_agent:
                chrome_options.add_argument(f'--user-agent={user_agent}')

            # Performance optimizations
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-plugins')
            chrome_options.add_argument('--disable-images')
            chrome_options.add_argument('--disable-javascript')

            # Create driver
            self.driver = webdriver.Chrome(options=chrome_options)

            # Set timeouts
            self.driver.set_page_load_timeout(browser_config.get("page_load_timeout", 30))
            self.driver.implicitly_wait(browser_config.get("implicit_wait", 10))

            # Anti-detection
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            self.logger.info("✅ Browser setup completed successfully")
            return True

        except Exception as e:
            self.logger.error(f"❌ Browser setup failed: {str(e)}")
            return False

    def navigate_to_telegram(self) -> bool:
        """Navigate to Telegram channel"""
        try:
            telegram_config = self.config.config.get("telegram", {})
            channel_url = telegram_config.get("channel_url")

            # Open Telegram Web
            self.driver.get("https://web.telegram.org/k/")
            self.logger.info("🌐 Navigated to Telegram Web")

            # Wait for manual authentication
            self.logger.warning("⚠️  Please manually authenticate with Telegram...")
            input("Press Enter after you've successfully logged in...")

            # Navigate to channel
            self.driver.get(channel_url)
            time.sleep(3)

            self.logger.info(f"✅ Navigated to channel: {channel_url}")
            return True

        except Exception as e:
            self.logger.error(f"❌ Navigation failed: {str(e)}")
            return False

    def extract_messages(self) -> List[str]:
        """Extract messages from Telegram channel"""
        messages = []
        try:
            # Scroll up to load more messages
            for _ in range(3):
                self.driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(1)

            # Try multiple selectors for message content
            selectors = [
                ".message-content",
                ".bubbles-text",
                ".message",
                "[class*='message']",
                "[class*='bubble']"
            ]

            message_elements = []
            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        message_elements = elements
                        break
                except:
                    continue

            # Extract text from elements
            for element in message_elements:
                try:
                    text = element.text.strip()
                    if text and len(text) > 10 and text not in messages:
                        messages.append(text)
                except StaleElementReferenceException:
                    continue
                except:
                    continue

            self.logger.info(f"📨 Extracted {len(messages)} messages")
            return messages

        except Exception as e:
            self.logger.error(f"❌ Message extraction failed: {str(e)}")
            return []

    def analyze_trading_signals(self, messages: List[str]) -> List[TradingSignal]:
        """Analyze messages for trading signals"""
        signals = []
        strategy_config = self.config.config.get("trading_strategy", {})

        # Trading patterns
        patterns = {
            'buy': [
                r'(?i)(buy|long|enter).*?(' + '|'.join(strategy_config.get("symbols_to_track", [])) + r')',
                r'(?i)(buy signal|entry point|go long)',
                r'(?i)(🟢|✅|🚀|📈).*?(buy|enter)'
            ],
            'sell': [
                r'(?i)(sell|short|exit).*?(' + '|'.join(strategy_config.get("symbols_to_track", [])) + r')',
                r'(?i)(sell signal|exit point|go short)',
                r'(?i)(🔴|❌|📉).*?(sell|exit)'
            ]
        }

        confidence_keywords = self.config.config.get("analysis", {}).get("confidence_keywords", [])

        for message in messages[-100:]:  # Analyze last 100 messages
            confidence = self._calculate_confidence(message, confidence_keywords)

            if confidence < strategy_config.get("min_confidence", 0.7):
                continue

            # Determine action and symbol
            action = "HOLD"
            symbol = None

            for action_type, action_patterns in patterns.items():
                for pattern in action_patterns:
                    if re.search(pattern, message):
                        action = action_type.upper()
                        # Extract symbol
                        for tracked_symbol in strategy_config.get("symbols_to_track", []):
                            if tracked_symbol.lower() in message.lower():
                                symbol = tracked_symbol
                                break
                        break
                if symbol:
                    break

            if symbol and action != "HOLD":
                signal = TradingSignal(
                    symbol=symbol,
                    action=action,
                    confidence=confidence,
                    timestamp=datetime.now(),
                    message=message[:200] + "..." if len(message) > 200 else message
                )
                signal.analysis_notes = f"Pattern matched for {action} signal"
                signals.append(signal)

        self.logger.info(f"🎯 Found {len(signals)} trading signals")
        return signals

    def _calculate_confidence(self, message: str, confidence_keywords: List[str]) -> float:
        """Calculate confidence score for a message"""
        confidence = 0.0

        # Check for confidence keywords
        for keyword in confidence_keywords:
            if keyword.lower() in message.lower():
                confidence += 0.15

        # Check for emojis
        if re.search(r'[🟢🔴✅❌🚀📉📈💰⚡🎯]', message):
            confidence += 0.1

        # Check for price/volume information
        if re.search(r'\$\d+\.?\d*', message):
            confidence += 0.2

        if re.search(r'(size|lot|amount).*?\d+\.?\d*', message, re.IGNORECASE):
            confidence += 0.1

        # Check for technical analysis terms
        ta_terms = ['support', 'resistance', 'trend', 'breakout', 'reversal']
        ta_count = sum(1 for term in ta_terms if term.lower() in message.lower())
        confidence += min(ta_count * 0.1, 0.3)

        return min(confidence, 1.0)

    def monitor_channel(self):
        """Monitor Telegram channel for trading signals"""
        telegram_config = self.config.config.get("telegram", {})
        duration = telegram_config.get("monitoring_duration_minutes", 60)
        interval = telegram_config.get("check_interval_seconds", 60)

        self.logger.info(f"🚀 Starting monitoring for {duration} minutes...")

        end_time = datetime.now() + timedelta(minutes=duration)

        try:
            while datetime.now() < end_time:
                self.logger.info("📊 Checking for new messages...")

                # Extract and analyze messages
                messages = self.extract_messages()
                new_signals = self.analyze_trading_signals(messages)

                # Process new signals
                for signal in new_signals:
                    if signal not in self.signals:
                        self.signals.append(signal)
                        self._process_signal(signal)

                # Wait for next check
                time.sleep(interval)

        except KeyboardInterrupt:
            self.logger.info("⏹️  Monitoring stopped by user")
        except Exception as e:
            self.logger.error(f"❌ Monitoring error: {str(e)}")
        finally:
            self._generate_report()

    def _process_signal(self, signal: TradingSignal):
        """Process a trading signal"""
        strategy_config = self.config.config.get("trading_strategy", {})

        # Check if we should execute this trade
        if signal.confidence < strategy_config.get("min_confidence", 0.7):
            return

        if self.trades_executed >= strategy_config.get("max_trades_per_hour", 5):
            return

        if signal.symbol in strategy_config.get("blacklist_symbols", []):
            return

        # Log the signal
        self.logger.info(f"📈 Trading Signal:")
        self.logger.info(f"   Symbol: {signal.symbol}")
        self.logger.info(f"   Action: {signal.action}")
        self.logger.info(f"   Confidence: {signal.confidence:.2f}")
        self.logger.info(f"   Message: {signal.message[:100]}...")

        self.trades_executed += 1

    def _generate_report(self):
        """Generate trading analysis report"""
        if not self.signals:
            self.logger.info("📋 No signals found during monitoring period")
            return

        # Create DataFrame
        df_data = [signal.to_dict() for signal in self.signals]
        df = pd.DataFrame(df_data)

        # Generate statistics
        stats = {
            'total_signals': len(self.signals),
            'buy_signals': len(df[df['action'] == 'BUY']),
            'sell_signals': len(df[df['action'] == 'SELL']),
            'avg_confidence': df['confidence'].mean(),
            'symbols_tracked': df['symbol'].unique().tolist(),
            'monitoring_duration': str(datetime.now() - self.start_time),
            'trades_executed': self.trades_executed,
            'timestamp': datetime.now().isoformat()
        }

        # Save reports
        output_config = self.config.config.get("output", {})
        if output_config.get("save_reports", True):
            report_dir = output_config.get("report_directory", "./reports")
            os.makedirs(report_dir, exist_ok=True)

            # Save JSON report
            json_file = os.path.join(report_dir, f'trading_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
            with open(json_file, 'w') as f:
                json.dump({**stats, 'signals': df_data}, f, indent=2, default=str)

            # Save CSV report
            if 'csv' in output_config.get("export_format", ["json"]):
                csv_file = os.path.join(report_dir, f'trading_signals_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
                df.to_csv(csv_file, index=False)

            self.logger.info(f"📋 Reports saved to {report_dir}")

        self.logger.info(f"📊 Final Report: {stats}")

    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            self.driver.quit()
            self.logger.info("🧹 Browser closed")

def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Enhanced Telegram Trading Scraper')
    parser.add_argument('--config', default='trading_config.json',
                       help='Configuration file path')
    parser.add_argument('--headless', action='store_true',
                       help='Run in headless mode')
    parser.add_argument('--duration', type=int, default=60,
                       help='Monitoring duration in minutes')

    args = parser.parse_args()

    try:
        # Load configuration
        config = TradingConfig(args.config)

        # Override config with command line arguments
        if args.headless:
            config.config['browser']['headless'] = True
        if args.duration:
            config.config['telegram']['monitoring_duration_minutes'] = args.duration

        # Initialize scraper
        scraper = TelegramTradingScraper(config)

        # Setup browser
        if not scraper.setup_browser():
            sys.exit(1)

        # Navigate to Telegram
        if not scraper.navigate_to_telegram():
            sys.exit(1)

        # Start monitoring
        scraper.monitor_channel()

    except Exception as e:
        logging.error(f"❌ Application error: {str(e)}")
        sys.exit(1)
    finally:
        if 'scraper' in locals():
            scraper.cleanup()

if __name__ == "__main__":
    main()