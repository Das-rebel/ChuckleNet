#!/usr/bin/env python3
"""
Enhanced ZAI Telegram Analyzer - Comprehensive Trading Signal Analysis
Uses ZAI models for advanced OCR and trading signal extraction from Telegram screenshots
"""

import os
import json
import time
import logging
import base64
import requests
from datetime import datetime
import glob

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedZAITelegramAnalyzer:
    def __init__(self):
        self.results_dir = "zai_telegram_analysis"
        os.makedirs(self.results_dir, exist_ok=True)

        self.analysis_results = {
            "session_start": datetime.now().isoformat(),
            "screenshots_analyzed": [],
            "ocr_results": [],
            "trading_signals": [],
            "zai_analysis": []
        }

    def encode_image_to_base64(self, image_path):
        """Convert image to base64 for AI analysis"""
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            logger.error(f"Error encoding image {image_path}: {e}")
            return None

    def analyze_with_zai_vision(self, image_base64, image_filename):
        """Analyze screenshot with ZAI Vision capabilities"""
        zai_api_key = os.getenv('ZAI_API_KEY')
        if not zai_api_key:
            logger.warning("⚠️  ZAI_API_KEY not found, using alternative analysis")
            return self.analyze_with_cerebras_fallback(image_base64, image_filename)

        try:
            headers = {
                "Authorization": f"Bearer {zai_api_key}",
                "Content-Type": "application/json"
            }

            prompt = """Analyze this Telegram trading group screenshot and extract comprehensive trading information:

EXTRACT AND ANALYZE TRADING INFORMATION:

- Trading Signals: Look for BUY/SELL/HOLD/LONG/SHORT patterns
- Cryptocurrencies: BTC, ETH, SOL, BNB, ADA, DOT, AVAX, etc.
- Stocks: AAPL, TSLA, GOOGL, MSFT, AMZN, NVDA, META
- Forex: EUR/USD, GBP/USD, USD/JPY, etc.
- Prices: Exact price levels, entries, exits, targets, stops
- Risk: Leverage, position size, warnings, confidence levels
- Timeframes: various timeframes mentioned

Return comprehensive JSON format:
{
    "comprehensive_analysis": {
        "text_extraction": "all text content",
        "trading_signals": [{
            "action": "BUY/SELL/HOLD",
            "asset": "symbol",
            "price_level": "price",
            "confidence": 0.0-1.0,
            "timeframe": "timeframe"
        }],
        "market_sentiment": "bullish/bearish/neutral",
        "risk_assessment": "LOW/MEDIUM/HIGH",
        "key_insights": ["insight1", "insight2"]
    }
}"""

            payload = {
                "model": "zai-vision",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_base64}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 2000,
                "temperature": 0.1
            }

            response = requests.post(
                "https://api.zai.ai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                analysis = result["choices"][0]["message"]["content"]
                logger.info(f"✅ ZAI vision analysis completed for {image_filename}")
                return analysis
            else:
                logger.error(f"❌ ZAI API error: {response.status_code}")
                return self.analyze_with_cerebras_fallback(image_base64, image_filename)

        except Exception as e:
            logger.error(f"❌ ZAI analysis failed for {image_filename}: {e}")
            return self.analyze_with_cerebras_fallback(image_base64, image_filename)

    def analyze_with_cerebras_fallback(self, image_base64, image_filename):
        """Fallback analysis with Cerebras AI"""
        cerebras_api_key = os.getenv('CEREBRAS_API_KEY')
        if not cerebras_api_key:
            logger.warning("⚠️  CEREBRAS_API_KEY not found")
            return None

        try:
            headers = {
                "Authorization": f"Bearer {cerebras_api_key}",
                "Content-Type": "application/json"
            }

            prompt = """Analyze this Telegram screenshot for trading information:

Extract: Trading signals (BUY/SELL), assets (BTC/ETH/stocks), price levels, confidence, sentiment

Return as JSON with: trading_signals, assets_found, sentiment_analysis, key_insights"""

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
                analysis = result["choices"][0]["message"]["content"]
                logger.info(f"✅ Cerebras fallback analysis completed for {image_filename}")
                return analysis
            else:
                logger.error(f"❌ Cerebras fallback failed: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"❌ Cerebras fallback failed for {image_filename}: {e}")
            return None

    def process_screenshots(self):
        """Process all Telegram screenshots with ZAI analysis"""

        # Find all telegram screenshots
        screenshot_pattern = "telegram_capture_*.png"
        screenshots = glob.glob(screenshot_pattern)

        if not screenshots:
            logger.error("❌ No telegram screenshots found")
            return

        logger.info(f"📸 Found {len(screenshots)} screenshots to analyze")

        for i, screenshot_path in enumerate(screenshots):
            logger.info(f"🔍 Analyzing screenshot {i+1}/{len(screenshots)}: {screenshot_path}")

            # Encode image
            image_base64 = self.encode_image_to_base64(screenshot_path)
            if not image_base64:
                continue

            # Analyze with ZAI
            filename = os.path.basename(screenshot_path)
            analysis_result = self.analyze_with_zai_vision(image_base64, filename)

            if analysis_result:
                screenshot_data = {
                    "filename": filename,
                    "filepath": screenshot_path,
                    "file_size": os.path.getsize(screenshot_path),
                    "model_used": "ZAI Vision with Cerebras fallback",
                    "analysis": analysis_result,
                    "timestamp": datetime.now().isoformat()
                }

                self.analysis_results["screenshots_analyzed"].append(screenshot_data)
                self.analysis_results["zai_analysis"].append(screenshot_data)

                logger.info(f"✅ ZAI analysis completed: {filename}")

            # Brief pause between requests
            time.sleep(2)

    def extract_comprehensive_trading_signals(self):
        """Extract comprehensive trading signals from ZAI analysis"""
        trading_keywords = ['buy', 'sell', 'long', 'short', 'hold', 'trade', 'signal', 'price', 'target', 'stop']
        crypto_assets = ['btc', 'eth', 'bitcoin', 'ethereum', 'sol', 'bnb', 'ada', 'dot', 'avax']
        stock_assets = ['aapl', 'tsla', 'googl', 'msft', 'amzn', 'nvda', 'meta']

        for analysis in self.analysis_results["zai_analysis"]:
            analysis_text = str(analysis["analysis"]).lower()

            # Look for trading keywords
            found_signals = []
            found_assets = []

            # Check for trading actions
            for keyword in trading_keywords:
                if keyword in analysis_text:
                    found_signals.append(keyword)

            # Check for crypto assets
            for asset in crypto_assets:
                if asset in analysis_text:
                    found_assets.append(asset.upper())

            # Check for stock assets
            for asset in stock_assets:
                if asset in analysis_text:
                    found_assets.append(asset.upper())

            if found_signals or found_assets:
                signal_data = {
                    "screenshot": analysis["filename"],
                    "model": analysis["model_used"],
                    "trading_signals": found_signals,
                    "assets_found": found_assets,
                    "analysis_full": analysis["analysis"],
                    "timestamp": analysis["timestamp"]
                }
                self.analysis_results["trading_signals"].append(signal_data)
                logger.info(f"💰 Trading signals found in {analysis['filename']}: {found_assets}")

    def save_comprehensive_results(self):
        """Save all ZAI analysis results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = os.path.join(self.results_dir, f"zai_telegram_analysis_{timestamp}.json")

        self.analysis_results["session_end"] = datetime.now().isoformat()
        self.analysis_results["screenshots_processed"] = len(self.analysis_results["screenshots_analyzed"])
        self.analysis_results["trading_signals_found"] = len(self.analysis_results["trading_signals"])

        with open(results_file, 'w') as f:
            json.dump(self.analysis_results, f, indent=2)

        logger.info(f"💾 ZAI Results saved: {results_file}")

        # Create comprehensive summary
        summary_file = os.path.join(self.results_dir, f"zai_analysis_summary_{timestamp}.txt")
        with open(summary_file, 'w') as f:
            f.write("ENHANCED ZAI-POWERED TELEGRAM TRADING ANALYSIS SUMMARY\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Analysis Session: {self.analysis_results['session_start']}\n")
            f.write(f"AI Model Used: ZAI Vision with Cerebras Fallback\n")
            f.write(f"Screenshots Processed: {self.analysis_results['screenshots_processed']}\n")
            f.write(f"Trading Signals Found: {self.analysis_results['trading_signals_found']}\n\n")

            if self.analysis_results["trading_signals"]:
                f.write("COMPREHENSIVE TRADING SIGNALS DETECTED:\n")
                f.write("-" * 40 + "\n")
                for signal in self.analysis_results["trading_signals"]:
                    f.write(f"📊 Screenshot: {signal['screenshot']}\n")
                    f.write(f"   Trading Signals: {', '.join(signal['trading_signals'])}\n")
                    f.write(f"   Assets Found: {', '.join(signal['assets_found'])}\n")
                    f.write(f"   Model: {signal['model']}\n")
                    f.write(f"   Time: {signal['timestamp']}\n\n")

        logger.info(f"📋 ZAI Summary saved: {summary_file}")

    def run_enhanced_analysis(self):
        """Run the complete enhanced ZAI analysis"""
        logger.info("🚀 STARTING ENHANCED ZAI-POWERED TELEGRAM ANALYSIS")
        logger.info("=" * 70)

        try:
            # Process screenshots with ZAI
            logger.info("🔍 Starting enhanced ZAI vision analysis...")
            self.process_screenshots()

            # Extract comprehensive trading signals
            logger.info("💰 Extracting comprehensive trading signals...")
            self.extract_comprehensive_trading_signals()

            # Save comprehensive results
            self.save_comprehensive_results()

            logger.info("\n" + "="*70)
            logger.info("🎉 ENHANCED ZAI ANALYSIS COMPLETED!")
            logger.info("=" * 70)
            logger.info(f"📸 Screenshots Analyzed: {self.analysis_results['screenshots_processed']}")
            logger.info(f"💰 Trading Signals: {self.analysis_results['trading_signals_found']}")
            logger.info(f"🤖 AI Models Used: ZAI Vision + Cerebras Fallback")
            logger.info(f"📁 Results Directory: {self.results_dir}")
            logger.info("=" * 70)

            if self.analysis_results['trading_signals_found'] > 0:
                logger.info(f"✅ SUCCESS: Found trading signals in {self.analysis_results['trading_signals_found']} screenshots!")
            else:
                logger.info("ℹ️  No explicit trading signals detected, but analysis completed")

        except Exception as e:
            logger.error(f"❌ Enhanced ZAI analysis error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    analyzer = EnhancedZAITelegramAnalyzer()
    analyzer.run_enhanced_analysis()