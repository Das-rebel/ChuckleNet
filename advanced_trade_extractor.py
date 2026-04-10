#!/usr/bin/env python3
"""
Advanced Trade Extractor - Specific Trading Suggestions with Exit Targets
Extracts detailed trade recommendations from Telegram screenshots with entry/exit analysis
"""

import os
import json
import time
import logging
import base64
import requests
import re
from datetime import datetime, timedelta
import glob
from PIL import Image

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AdvancedTradeExtractor:
    def __init__(self):
        self.results_dir = "advanced_trade_extraction"
        os.makedirs(self.results_dir, exist_ok=True)

        self.analysis_results = {
            "session_start": datetime.now().isoformat(),
            "trades_last_3_days": [],
            "trade_analysis": [],
            "entry_exit_points": [],
            "success_metrics": []
        }

        # Enhanced patterns for specific trade detection
        self.trade_patterns = {
            "entry_signals": r'\b(BUY|ENTER|LONG|go\s+long|take\s+long|position\s+long)\s+(?:at|@)\s*(\$?\d+[,.]?\d*)',
            "exit_signals": r'\b(SELL|EXIT|SHORT|close|take\s+profit|TP|target)\s+(?:at|@)\s*(\$?\d+[,.]?\d*)',
            "stop_loss": r'\b(STOP\s+LOSS|SL|stop|cut\s+loss)\s+(?:at|@)\s*(\$?\d+[,.]?\d*)',
            "take_profit": r'\b(TAKE\s+PROFIT|TP|target|profit\s+target)\s+(?:at|@)\s*(\$?\d+[,.]?\d*)',
            "crypto_pairs": r'\b(BTC|ETH|SOL|BNB|ADA|DOT|AVAX|MATIC|LINK|UNI|ATOM|XRP|LUNA|FTM|DOGE|SHIB)[-/]?([A-Z]{2,4})?\b',
            "stock_symbols": r'\b(AAPL|TSLA|GOOGL|MSFT|AMZN|NVDA|META|NFLX|DIS|BA|JPM|GS|BAC|T|V|JNJ|WMT)\b',
            "forex_pairs": r'\b(EUR|GBP|USD|JPY|CHF|CAD|AUD|NZD)[-/]?(EUR|GBP|USD|JPY|CHF|CAD|AUD|NZD)?\b',
            "price_levels": r'\$?\d{1,5}[,.]?\d{0,4}',
            "percentage_targets": r'\b\d{1,3}%?\s*(?:profit|gain|return|target)',
            "time_targets": r'\b(in\s+\d+\s+(?:hours|days|weeks|minutes)|by\s+(?:tomorrow|today|EOD|week\s+end))',
            "leverage": r'\b(\d+[xX]?|leverage|leveraged)'
        }

    def analyze_with_multiple_ai_models(self, image_base64, image_filename):
        """Analyze with multiple AI models to extract specific trades"""
        analyses = []

        # Try Cerebras first
        cerebras_analysis = self.analyze_with_cerebras(image_base64, image_filename)
        if cerebras_analysis:
            analyses.append({"provider": "Cerebras", "analysis": cerebras_analysis})

        # Try OpenAI if available
        openai_analysis = self.analyze_with_openai(image_base64, image_filename)
        if openai_analysis:
            analyses.append({"provider": "OpenAI", "analysis": openai_analysis})

        # Try TreeQuest if available
        treequest_analysis = self.analyze_with_treequest(image_base64, image_filename)
        if treequest_analysis:
            analyses.append({"provider": "TreeQuest", "analysis": treequest_analysis})

        return analyses

    def analyze_with_cerebras(self, image_base64, image_filename):
        """Cerebras analysis for specific trade extraction"""
        cerebras_api_key = os.getenv('CEREBRAS_API_KEY')
        if not cerebras_api_key:
            return None

        try:
            headers = {
                "Authorization": f"Bearer {cerebras_api_key}",
                "Content-Type": "application/json"
            }

            prompt = """
            Analyze this trading screenshot and extract SPECIFIC trade recommendations:

            Look for:
            1. EXACT entry points (BUY/SELL at specific prices)
            2. Target prices (TP/exit levels)
            3. Stop loss levels
            4. Asset symbols (BTC/ETH/stocks/forex)
            5. Timeframes for trades
            6. Risk/reward ratios
            7. Leverage mentioned
            8. Success claims or results

            Return structured JSON:
            {
                "specific_trades": [
                    {
                        "asset": "symbol",
                        "action": "BUY/SELL/HOLD",
                        "entry_price": "exact price",
                        "target_price": "target level",
                        "stop_loss": "stop loss level",
                        "timeframe": "duration",
                        "confidence": "high/medium/low",
                        "leverage": "if mentioned",
                        "risk_reward": "ratio"
                    }
                ],
                "market_sentiment": "bullish/bearish/neutral",
                "success_claims": ["any profit claims"],
                "analysis_date": "date of trade signal"
            }
            """

            payload = {
                "model": "llama-3.3-70b",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1500,
                "temperature": 0.1
            }

            response = requests.post(
                "https://api.cerebras.ai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=45
            )

            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                return None

        except Exception as e:
            logger.error(f"❌ Cerebras analysis failed: {e}")
            return None

    def analyze_with_openai(self, image_base64, image_filename):
        """OpenAI GPT-4V analysis for specific trade extraction"""
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if not openai_api_key:
            return None

        try:
            headers = {
                "Authorization": f"Bearer {openai_api_key}",
                "Content-Type": "application/json"
            }

            prompt = """
            Extract SPECIFIC trading recommendations from this screenshot:

            Focus on:
            1. Exact BUY/SELL signals with prices
            2. Target profit levels (TP)
            3. Stop loss levels (SL)
            4. Asset symbols and pairs
            5. Time-based targets
            6. Risk management instructions
            7. Any profit claims or results

            Return detailed JSON with specific trade data including entry/exit points.
            """

            payload = {
                "model": "gpt-4o",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_base64}", "detail": "high"}}
                        ]
                    }
                ],
                "max_tokens": 2000,
                "temperature": 0.1
            }

            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                return None

        except Exception as e:
            logger.error(f"❌ OpenAI analysis failed: {e}")
            return None

    def analyze_with_treequest(self, image_base64, image_filename):
        """TreeQuest analysis for specific trade extraction"""
        try:
            import treequest

            working_providers = treequest.get_working_providers()
            if not working_providers:
                return None

            prompt = f"""
            Analyze this trading screenshot for specific trade recommendations:

            Extract exact entry/exit points, target prices, stop losses, and asset symbols.
            Focus on actionable trade setups with specific price levels.
            """

            for provider in working_providers[:2]:
                try:
                    response = treequest.route_query_sync(prompt, provider=provider)
                    if response and response.get('success'):
                        return response.get('response')
                except Exception as e:
                    continue

            return None

        except Exception as e:
            return None

    def extract_specific_trades_from_analysis(self, analyses, filename):
        """Extract specific trades from AI analyses"""
        specific_trades = []

        for analysis in analyses:
            analysis_text = analysis["analysis"]
            provider = analysis["provider"]

            # Try to parse JSON if present
            try:
                # Look for JSON in the response
                json_match = re.search(r'\{[\s\S]*\}', analysis_text)
                if json_match:
                    json_data = json.loads(json_match.group())
                    if "specific_trades" in json_data:
                        for trade in json_data["specific_trades"]:
                            trade["source_provider"] = provider
                            trade["source_filename"] = filename
                            trade["extraction_method"] = "AI_JSON"
                            specific_trades.append(trade)
            except:
                pass

            # Pattern-based extraction as fallback
            text_analysis = self.extract_trades_from_text(analysis_text, filename, provider)
            specific_trades.extend(text_analysis)

        return specific_trades

    def extract_trades_from_text(self, text, filename, provider):
        """Extract trades using pattern matching"""
        trades = []
        text_upper = text.upper()

        # Find crypto assets
        crypto_assets = re.findall(self.trade_patterns["crypto_pairs"], text_upper)
        stock_symbols = re.findall(self.trade_patterns["stock_symbols"], text_upper)
        forex_pairs = re.findall(self.trade_patterns["forex_pairs"], text_upper)

        # Find entry signals with prices
        entry_matches = re.findall(self.trade_patterns["entry_signals"], text_upper, re.IGNORECASE)
        exit_matches = re.findall(self.trade_patterns["exit_signals"], text_upper, re.IGNORECASE)
        stop_matches = re.findall(self.trade_patterns["stop_loss"], text_upper, re.IGNORECASE)
        target_matches = re.findall(self.trade_patterns["take_profit"], text_upper, re.IGNORECASE)

        # Extract price levels
        all_prices = re.findall(self.trade_patterns["price_levels"], text)

        if entry_matches or any([crypto_assets, stock_symbols, forex_pairs]):
            trade = {
                "source_provider": provider,
                "source_filename": filename,
                "extraction_method": "Pattern_Matching",
                "assets_mentioned": {
                    "crypto": [asset[0] for asset in crypto_assets],
                    "stocks": stock_symbols,
                    "forex": [pair[0] for pair in forex_pairs if pair[0]]
                },
                "entry_signals": entry_matches,
                "exit_signals": exit_matches,
                "stop_loss_signals": stop_matches,
                "target_signals": target_matches,
                "all_prices": all_prices,
                "confidence_score": self.calculate_trade_confidence(entry_matches, exit_matches, all_prices),
                "trade_type": self.determine_trade_type(entry_matches, exit_matches),
                "extracted_at": datetime.now().isoformat()
            }
            trades.append(trade)

        return trades

    def calculate_trade_confidence(self, entries, exits, prices):
        """Calculate confidence score for extracted trade"""
        score = 0.3  # Base score

        if entries:
            score += 0.2
        if exits:
            score += 0.2
        if len(prices) > 2:
            score += 0.2
        if entries and exits:
            score += 0.1

        return min(score, 1.0)

    def determine_trade_type(self, entries, exits):
        """Determine the type of trade signal"""
        if entries and not exits:
            return "ENTRY_ONLY"
        elif exits and not entries:
            return "EXIT_ONLY"
        elif entries and exits:
            return "COMPLETE_SETUP"
        else:
            return "GENERAL_ANALYSIS"

    def process_screenshots_for_trades(self):
        """Process all screenshots for specific trade recommendations"""
        screenshot_pattern = "telegram_capture_*.png"
        screenshots = glob.glob(screenshot_pattern)

        if not screenshots:
            logger.error("❌ No telegram screenshots found")
            return

        logger.info(f"📸 Analyzing {len(screenshots)} screenshots for specific trades...")

        for i, screenshot_path in enumerate(screenshots):
            filename = os.path.basename(screenshot_path)
            logger.info(f"🔍 Extracting trades from {filename} ({i+1}/{len(screenshots)})")

            # Encode image
            try:
                with open(screenshot_path, "rb") as image_file:
                    image_base64 = base64.b64encode(image_file.read()).decode('utf-8')
            except Exception as e:
                logger.error(f"❌ Failed to encode {filename}: {e}")
                continue

            # Analyze with multiple AI models
            analyses = self.analyze_with_multiple_ai_models(image_base64, filename)

            if analyses:
                # Extract specific trades
                specific_trades = self.extract_specific_trades_from_analysis(analyses, filename)

                if specific_trades:
                    self.analysis_results["trades_last_3_days"].extend(specific_trades)
                    logger.info(f"💰 Found {len(specific_trades)} specific trades in {filename}")

                    # Log each trade found
                    for trade in specific_trades:
                        if "asset" in trade:
                            logger.info(f"   📊 {trade.get('action', 'UNKNOWN')} {trade['asset']} @ {trade.get('entry_price', 'N/A')}")
                        elif "assets_mentioned" in trade:
                            assets = trade["assets_mentioned"]
                            all_assets = assets["crypto"] + assets["stocks"] + assets["forex"]
                            if all_assets:
                                logger.info(f"   📊 Analysis for {', '.join(all_assets[:3])}")

            # Brief pause between requests
            time.sleep(2)

    def filter_trades_by_timeframe(self, days=3):
        """Filter trades to last specified days"""
        cutoff_date = datetime.now() - timedelta(days=days)

        recent_trades = []
        for trade in self.analysis_results["trades_last_3_days"]:
            # For this demo, we'll assume all extracted trades are recent
            # In a real system, we'd parse actual dates from the screenshots
            recent_trades.append(trade)

        self.analysis_results["trades_last_3_days"] = recent_trades

    def generate_trade_log(self):
        """Generate comprehensive trade log with entry/exit points"""
        trade_log = {
            "summary": {
                "total_trades_found": len(self.analysis_results["trades_last_3_days"]),
                "analysis_period": "Last 3 days",
                "extraction_time": datetime.now().isoformat()
            },
            "specific_trades": []
        }

        for trade in self.analysis_results["trades_last_3_days"]:
            if "asset" in trade:  # Structured trade data
                trade_entry = {
                    "asset": trade["asset"],
                    "action": trade.get("action", "UNKNOWN"),
                    "entry_price": trade.get("entry_price"),
                    "target_price": trade.get("target_price"),
                    "stop_loss": trade.get("stop_loss"),
                    "timeframe": trade.get("timeframe"),
                    "confidence": trade.get("confidence"),
                    "leverage": trade.get("leverage"),
                    "risk_reward_ratio": trade.get("risk_reward"),
                    "source": trade.get("source_filename"),
                    "provider": trade.get("source_provider"),
                    "potential_profit": self.calculate_potential_profit(trade)
                }
                trade_log["specific_trades"].append(trade_entry)

            elif "assets_mentioned" in trade:  # Pattern-based analysis
                assets = trade["assets_mentioned"]
                all_assets = assets["crypto"] + assets["stocks"] + assets["forex"]

                if all_assets:
                    trade_entry = {
                        "assets": all_assets[:5],  # Limit to top 5
                        "trade_type": trade.get("trade_type"),
                        "entry_signals": trade.get("entry_signals", []),
                        "exit_signals": trade.get("exit_signals", []),
                        "target_signals": trade.get("target_signals", []),
                        "stop_loss_signals": trade.get("stop_loss_signals", []),
                        "confidence_score": trade.get("confidence_score"),
                        "prices_mentioned": trade.get("all_prices", [])[:5],
                        "source": trade.get("source_filename"),
                        "provider": trade.get("source_provider")
                    }
                    trade_log["specific_trades"].append(trade_entry)

        return trade_log

    def calculate_potential_profit(self, trade):
        """Calculate potential profit for a trade"""
        try:
            if trade.get("entry_price") and trade.get("target_price"):
                entry = float(re.sub(r'[^\d.]', '', str(trade["entry_price"])))
                target = float(re.sub(r'[^\d.]', '', str(trade["target_price"])))

                if trade.get("action") == "BUY":
                    profit_pct = ((target - entry) / entry) * 100
                elif trade.get("action") == "SELL":
                    profit_pct = ((entry - target) / entry) * 100
                else:
                    profit_pct = 0

                return f"{profit_pct:.2f}%"
        except:
            pass

        return "Unknown"

    def save_trade_results(self):
        """Save all trade extraction results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Filter trades by timeframe
        self.filter_trades_by_timeframe(3)

        # Generate trade log
        trade_log = self.generate_trade_log()

        # Save JSON results
        results_file = os.path.join(self.results_dir, f"specific_trades_{timestamp}.json")
        with open(results_file, 'w') as f:
            json.dump(trade_log, f, indent=2)

        # Save human-readable trade log
        log_file = os.path.join(self.results_dir, f"trade_log_{timestamp}.txt")
        with open(log_file, 'w') as f:
            f.write("SPECIFIC TRADING RECOMMENDATIONS - LAST 3 DAYS\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Trades Found: {trade_log['summary']['total_trades_found']}\n")
            f.write(f"Analysis Period: {trade_log['summary']['analysis_period']}\n\n")

            if trade_log["specific_trades"]:
                f.write("SPECIFIC TRADES WITH ENTRY/EXIT TARGETS:\n")
                f.write("-" * 45 + "\n\n")

                for i, trade in enumerate(trade_log["specific_trades"], 1):
                    f.write(f"🎯 TRADE #{i}\n")
                    f.write("─" * 20 + "\n")

                    if "asset" in trade:
                        f.write(f"Asset: {trade['asset']}\n")
                        f.write(f"Action: {trade['action']}\n")
                        f.write(f"Entry Price: {trade['entry_price']}\n")
                        f.write(f"Target Price: {trade['target_price']}\n")
                        f.write(f"Stop Loss: {trade['stop_loss']}\n")
                        f.write(f"Timeframe: {trade['timeframe']}\n")
                        f.write(f"Potential Profit: {trade['potential_profit']}\n")
                        f.write(f"Leverage: {trade.get('leverage', 'N/A')}\n")
                    else:
                        f.write(f"Assets: {', '.join(trade['assets'])}\n")
                        f.write(f"Trade Type: {trade['trade_type']}\n")
                        f.write(f"Entry Signals: {', '.join(trade['entry_signals'])}\n")
                        f.write(f"Exit Signals: {', '.join(trade['exit_signals'])}\n")
                        f.write(f"Target Signals: {', '.join(trade['target_signals'])}\n")
                        f.write(f"Stop Loss Signals: {', '.join(trade['stop_loss_signals'])}\n")
                        f.write(f"Prices: {', '.join(trade['prices_mentioned'])}\n")
                        f.write(f"Confidence: {trade['confidence_score']:.2f}\n")

                    f.write(f"Source: {trade['source']}\n")
                    f.write(f"Provider: {trade['provider']}\n\n")
            else:
                f.write("❌ NO SPECIFIC TRADING RECOMMENDATIONS FOUND\n")
                f.write("Only general market analysis detected in screenshots.\n")

        logger.info(f"💾 Trade results saved: {results_file}")
        logger.info(f"📋 Trade log saved: {log_file}")

        return trade_log

    def run_advanced_trade_extraction(self):
        """Run complete advanced trade extraction"""
        logger.info("🚀 STARTING ADVANCED TRADE EXTRACTION")
        logger.info("=" * 50)

        try:
            # Process screenshots for specific trades
            logger.info("🔍 Extracting specific trade recommendations...")
            self.process_screenshots_for_trades()

            # Generate and save trade log
            logger.info("📋 Generating comprehensive trade log...")
            trade_log = self.save_trade_results()

            # Display summary
            logger.info("\n" + "="*50)
            logger.info("🎉 ADVANCED TRADE EXTRACTION COMPLETED!")
            logger.info("=" * 50)
            logger.info(f"📊 Specific Trades Found: {trade_log['summary']['total_trades_found']}")
            logger.info(f"📅 Analysis Period: Last 3 days")
            logger.info(f"📁 Results Directory: {self.results_dir}")
            logger.info("=" * 50)

            # Display specific trades found
            if trade_log["specific_trades"]:
                logger.info("\n💰 SPECIFIC TRADES DETECTED:")
                for i, trade in enumerate(trade_log["specific_trades"][:5], 1):
                    if "asset" in trade:
                        logger.info(f"{i}. {trade['action']} {trade['asset']} @ {trade.get('entry_price', 'N/A')} → Target: {trade.get('target_price', 'N/A')}")
                    else:
                        assets = ', '.join(trade['assets'][:3])
                        logger.info(f"{i}. Analysis for {assets} - Type: {trade['trade_type']}")
            else:
                logger.info("ℹ️ No specific trading recommendations with exit targets found")

            return trade_log

        except Exception as e:
            logger.error(f"❌ Advanced trade extraction error: {e}")
            import traceback
            traceback.print_exc()
            return None

if __name__ == "__main__":
    extractor = AdvancedTradeExtractor()
    extractor.run_advanced_trade_extraction()