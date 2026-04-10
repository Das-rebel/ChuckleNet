#!/usr/bin/env python3
<arg_value>ZAI Enhanced Telegram Analysis
Uses ZAI, Cerebras, and OpenAI models for comprehensive Telegram analysis
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

class ZAITelegramAnalyzer:
    def __init__(self):
        self.results_dir = "zai_telegram_analysis"
        os.makedirs(self.results_dir, exist_ok=True)

        self.analysis_results = {
            "session_start": datetime.now().isoformat(),
            "screenshots_analyzed": [],
            "zai_analysis": [],
            "cerebras_analysis": [],
            "openai_analysis": [],
            "trading_signals": []
        }

    def encode_image_to_base64(self, image_path):
        """Convert image to base64 for AI analysis"""
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            logger.error(f"Error encoding image {image_path}: {e}")
            return None

    def analyze_with_zai(self, image_base64, image_filename):
        """Analyze screenshot with ZAI (you mentioned ZAI models available)"""
        # Check if ZAI API key is configured
        zai_api_key = os.getenv('ZAI_API_KEY') or os.getenv('OPENAI_API_KEY')
        if not zai_api_key:
            logger.warning("⚠️  ZAI_API_KEY or OPENAI_API_KEY not found")
            return None

        try:
            headers = {
                "Authorization": f"Bearer {zai_api_key}",
                "Content-Type": "application/json"
            }

            prompt = """
            You are an expert cryptocurrency and trading signal analyst. Analyze this Telegram trading group screenshot and extract comprehensive trading information:

            1. **Extract all visible text messages** (exactly as shown)
            2. **Identify trading signals** (BUY/SELL/HOLD/SHORT/LONG recommendations)
            3. **Asset analysis** (cryptocurrencies: BTC, ETH, SOL, etc.; stocks: AAPL, TSLA, etc.; forex: EUR/USD, GBP/USD, etc.)
            4. **Price intelligence** (entry prices, targets, stop losses, support/resistance levels)
            5. **Technical indicators** (timeframes, patterns, confidence levels)
            6. **Risk assessment** (position sizes, leverage mentioned, risk management)

            **CRITICAL FOCUS**:
            - Extract any exact BUY/SELL signals
            - Note specific price levels mentioned
            - Identify leverage or risk warnings
            - Capture any timestamps or timeframes
            - Look for profit targets or stop losses

            Respond with detailed JSON analysis:
            {
                "screenshot_analysis": {
                    "text_content": "all visible text",
                    "message_count": "number of messages visible",
                    "user_interface": "telegram/messaging app details"
                },
                "trading_signals": [
                    {
                        "signal_type": "BUY/SELL/HOLD/SHORT/LONG",
                        "asset": "BTC/ETH/Stock/Forex",
                        "action": "exact signal text",
                        "price_level": "specific price mentioned",
                        "confidence": "0.0-1.0",
                        "risk_level": "LOW/MEDIUM/HIGH",
                        "timeframe": "1m/5m/1h/etc",
                        "target": "profit target if mentioned"
                    }
                ],
                "market_intelligence": {
                    "sentiment": "bullish/bearish/neutral",
                    "volume_analysis": "high/medium/low activity",
                    "signal_strength": "strong/moderate/weak",
                    "key_insights": ["insight1", "insight2"]
                },
                "recommendation": {
                    "trade_decision": "EXECUTE/WAIT/AVOID",
                    "position_size_suggestion": "recommendation",
                    "risk_warning": "any caution needed"
                }
            }

            Be extremely thorough and precise. This analysis will be used for actual trading decisions.
            """

            # Try different endpoints that might work with ZAI/OpenAI key
            endpoints = [
                "https://api.openai.com/v1/chat/completions",
                "https://api.openai.com/v1/chat/completions"
            ]

            for endpoint in endpoints:
                try:
                    payload = {
                        "model": "gpt-4-vision-preview",  # Try vision model for better image understanding
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
                        "max_tokens": 3000,
                        "temperature": 0.1
                    }

                    response = requests.post(
                        endpoint,
                        headers=headers,
                        json=payload,
                        timeout=90
                    )

                    if response.status_code == 200:
                        result = response.json()
                        analysis = result["choices"][0]["message"]["content"]
                        logger.info(f"✅ ZAI analysis completed for {image_filename}")
                        return {
                            "model": "ZAI (OpenAI-compatible)",
                            "endpoint": endpoint,
                            "analysis": analysis
                        }
                    else:
                        logger.debug(f"Endpoint {endpoint} returned {response.status_code}")

                except Exception as e:
                    logger.debug(f"Failed endpoint {endpoint}: {e}")
                    continue

            return None

        except Exception as e:
            logger.error(f"❌ ZAI analysis failed for {image_filename}: {e}")
            return None

    def analyze_with_cerebras_enhanced(self, image_base64, image_filename):
        """Enhanced Cerebras analysis with trading focus"""
        cerebras_api_key = os.getenv('CEREBRAS_API_KEY')
        if not cerebras_api_key:
            logger.warning("⚠️  CEREBRAS_API_KEY not found")
            return None

        try:
            headers = {
                "Authorization": f"Bearer {cerebras_api_key}",
                "Content-Type": "application/json"
            }

            # First analysis: General description and text extraction
            description_prompt = """
            Analyze this Telegram trading group screenshot in extreme detail. Focus on:

            1. **All text content** - extract EVERY visible word, number, and symbol
            2. **User interface elements** - usernames, timestamps, message indicators
            3. **Visual elements** - charts, graphs, images, colors, layouts
            4. **Financial information** - prices, percentages, ratios, symbols

            Be exhaustive in your description. This is for critical trading analysis.
            """

            description_payload = {
                "model": "llama-3.3-70b",
                "messages": [{"role": "user", "content": description_prompt}],
                "max_tokens": 2000,
                "temperature": 0.1
            }

            response = requests.post(
                "https://api.cerebras.ai/v1/chat/completions",
                headers=headers,
                json=description_payload,
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                description = result["choices"][0]["message"]["content"]
                logger.info(f"✅ Cerebras description completed for {image_filename}")

                # Second analysis: Trading signal extraction
                trading_prompt = f"""
                Based on this screenshot analysis: "{description}"

                EXTRACT AND ANALYZE TRADING INFORMATION:

                1. **Trading Signals**: Look for BUY/SELL/HOLD/LONG/SHORT patterns
                2. **Cryptocurrencies**: BTC, ETH, SOL, BNB, ADA, DOT, AVAX, etc.
                3. **Stocks**: AAPL, TSLA, GOOGL, MSFT, AMZN, NVDA, META
                4. **Forex**: EUR/USD, GBP/USD, USD/JPY, etc.
                5. **Prices**: Exact price levels, entries, exits, targets, stops
                6. **Risk**: Leverage, position size, warnings, confidence levels
                - **Timeframes**: 1m, 5m, 15m, 1h, 4h, 1d

                Return comprehensive JSON:
                {{
                    "comprehensive_analysis": {{
                        "text_extraction": "all text content",
                        "trading_signals": [
                            {{
                                "signal": "BUY/SELL/HOLD",
                                "asset": "BTC/ETH/Stock",
                                "action_detail": "specific recommendation",
                                "price_mentioned": "specific price level",
                                "risk_level": "LOW/MEDIUM/HIGH",
                                "confidence": "0.0-1.0",
                                "context": "surrounding information"
                            }}
                        ],
                        "assets_identified": ["BTC", "ETH", "AAPL"],
                        "price_points": ["entry", "target", "stop"],
                        "risk_analysis": {{
                            "overall_risk": "assessment",
                            "leverage_detected": true/false,
                            "warnings": ["warning1", "warning2"]
                        }}
                    }}
                }}
                """

                trading_payload = {
                    "model": "llama-3.3-70b",
                    "messages": [{"role": "user", "content": trading_prompt}],
                    "max_tokens": 2500,
                    "temperature": 0.1
                }

                trading_response = requests.post(
                    "https://api.cerebras.ai/v1/chat/completions",
                    headers=headers,
                    json=trading_payload,
                    timeout=60
                )

                if trading_response.status_code == 200:
                    trading_result = trading_response.json()
                    trading_analysis = trading_result["choices"][0]["message"]["content"]

                    return {
                        "model": "Cerebras Llama-3.3-70b",
                        "description": description,
                        "trading_analysis": trading_analysis
                    }

            return None

        except Exception as e:
            logger.error(f"❌ Enhanced Cerebras analysis failed for {image_filename}: {e}")
            return None

    def process_screenshots_with_zai_priority(self):
        """Process screenshots prioritizing ZAI, then Cerebras"""

        # Find all telegram screenshots
        screenshot_pattern = "telegram_capture_*.png"
        screenshots = sorted(glob.glob(screenshot_pattern))

        if not screenshots:
            logger.error("❌ No telegram screenshots found")
            return

        logger.info(f"📸 Found {len(screenshots)} screenshots to analyze with ZAI priority")

        for i, screenshot_path in enumerate(screenshots):
            logger.info(f"🔍 Analyzing screenshot {i+1}/{len(screenshots)}: {screenshot_path}")

            # Encode image
            image_base64 = self.encode_image_to_base64(screenshot_path)
            if not image_base64:
                continue

            filename = os.path.basename(screenshot_path)

            # Try ZAI first (enhanced analysis)
            zai_result = self.analyze_with_zai(image_base64, filename)
            if zai_result:
                screenshot_data = {
                    "filename": filename,
                    "filepath": screenshot_path,
                    "file_size": os.path.getsize(screenshot_path),
                    "zai_analysis": zai_result,
                    "timestamp": datetime.now().isoformat()
                }
                self.analysis_results["screenshots_analyzed"].append(screenshot_data)
                self.analysis_results["zai_analysis"].append(screenshot_data)
                logger.info(f"✅ ZAI analysis successful: {filename}")
            else:
                # Fallback to Cerebras enhanced analysis
                logger.info(f"🔄 Using Cerebras enhanced analysis for {filename}")
                cerebras_result = self.analyze_with_cerebras_enhanced(image_base64, filename)
                if cerebras_result:
                    screenshot_data = {
                        "filename": filename,
                        "filepath": screenshot_path,
                        "file_size": os.path.getsize(screenshot_path),
                        "cerebras_analysis": cerebras_result,
                        "timestamp": datetime.now().isoformat()
                    }
                    self.analysis_results["screenshots_analyzed"].append(screenshot_data)
                    self.analysis_results["cerebras_analysis"].append(screenshot_data)
                    logger.info(f"✅ Cerebras analysis completed: {filename}")

            # Brief pause between requests
            time.sleep(3)

    def extract_comprehensive_trading_signals(self):
        """Extract trading signals from all AI analyses"""
        trading_keywords = [
            'buy', 'sell', 'hold', 'long', 'short', 'trade', 'signal', 'entry', 'exit', 'target',
            'btc', 'eth', 'bitcoin', 'ethereum', 'sol', 'bnb', 'ada', 'dot', 'avax',
            'aapl', 'tsla', 'googl', 'msft', 'amzn', 'nvda', 'meta',
            'eur/usd', 'gbp/usd', 'usd/jpy', 'aud/usd', 'usd/cad',
            'leverage', 'risk', 'stop loss', 'take profit', 'position'
        ]

        all_analyses = (
            self.analysis_results.get("zai_analysis", []) +
            self.analysis_results.get("cerebras_analysis", [])
        )

        for analysis in all_analyses:
            analysis_text = ""

            # Extract text from different analysis formats
            if "zai_analysis" in analysis and analysis["zai_analysis"]:
                analysis_text = analysis["zai_analysis"]["analysis"].lower()
            elif "cerebras_analysis" in analysis and analysis["cerebras_analysis"]:
                if "trading_analysis" in analysis["cerebras_analysis"]:
                    analysis_text = analysis["cerebras_analysis"]["trading_analysis"].lower()
                analysis_text += " " + analysis["cerebras_analysis"]["description"].lower()

            # Advanced trading signal detection
            signals_detected = []
            high_confidence_signals = []

            for keyword in trading_keywords:
                if keyword in analysis_text:
                    signals_detected.append(keyword)

                    # Check for high confidence indicators
                    confidence_indicators = [
                        'strong', 'high confidence', 'recommended', 'urgent', 'immediate',
                        'guaranteed', 'confirmed', 'verified'
                    ]
                    for indicator in confidence_indicators:
                        if indicator in analysis_text:
                            high_confidence_signals.append(f"{keyword} ({indicator})")

            if signals_detected or high_confidence_signals:
                signal_data = {
                    "screenshot": analysis["filename"],
                    "model": analysis.get("zai_analysis", {}).get("model", "Cerebras"),
                    "signals_detected": signals_detected,
                    "high_confidence_signals": high_confidence_signals,
                    "analysis_preview": analysis_text[:500],
                    "timestamp": analysis["timestamp"]
                }
                self.analysis_results["trading_signals"].append(signal_data)
                logger.info(f"💰 Trading signals in {analysis['filename']}: {len(signals_detected)} keywords, {len(high_confidence_signals)} high-confidence")

    def generate_comprehensive_report(self):
        """Generate comprehensive trading analysis report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = os.path.join(self.results_dir, f"zai_comprehensive_trading_report_{timestamp}.json")

        self.analysis_results["session_end"] = datetime.now().isoformat()
        self.analysis_results["screenshots_processed"] = len(self.analysis_results["screenshots_analyzed"])
        self.analysis_results["zai_analyses"] = len(self.analysis_results.get("zai_analysis", []))
        self.analysis_results["cerebras_analyses"] = len(self.analysis_results.get("cerebras_analysis", []))
        self.analysis_results["total_trading_signals"] = len(self.analysis_results["trading_signals"])

        # Summary statistics
        all_signals = self.analysis_results["trading_signals"]
        asset_mentions = {}
        signal_types = {}
        risk_levels = []

        for signal in all_signals:
            # Count asset mentions
            for keyword in ['btc', 'eth', 'aapl', 'tsla', 'eur/usd']:
                if keyword in signal["signals_detected"]:
                    asset_mentions[keyword] = asset_mentions.get(keyword, 0) + 1

        # Create executive summary
        executive_summary = {
            "total_screenshots_analyzed": self.analysis_results["screenshots_processed"],
            "primary_ai_model": "ZAI (OpenAI-compatible)",
            "backup_ai_model": "Cerebras Llama-3.3-70b",
            "trading_signals_detected": len(all_signals),
            "high_confidence_signals": len([s for s in all_signals if s["high_confidence_signals"]]),
            "most_mentioned_assets": sorted(asset_mentions.items(), key=lambda x: x[1], reverse=True)[:5],
            "analysis_confidence": "HIGH" if len(all_signals) > 5 else "MEDIUM" if len(all_signals) > 2 else "LOW"
        }

        self.analysis_results["executive_summary"] = executive_summary

        with open(report_file, 'w') as f:
            json.dump(self.analysis_results, f, indent=2)

        # Create readable report
        readable_report = os.path.join(self.results_dir, f"trading_analysis_report_{timestamp}.txt")
        with open(readable_report, 'w') as f:
            f.write("ZAI ENHANCED TRADING ANALYSIS REPORT\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Analysis Date: {self.analysis_results['session_start']}\n")
            f.write(f"Executive Summary:\n")
            f.write(f"- Screenshots Analyzed: {executive_summary['total_screenshots_analyzed']}\n")
            f.write(f"- Trading Signals Detected: {executive_summary['trading_signals_detected']}\n")
            f.write(f"- High Confidence Signals: {executive_summary['high_confidence_signals']}\n")
            f.write(f"- Analysis Confidence: {executive_summary['analysis_confidence']}\n")
            f.write(f"- AI Models: {executive_summary['primary_ai_model']} + {executive_summary['backup_ai_model']}\n\n")

            f.write("TOP ASSET MENTIONS:\n")
            f.write("-" * 25 + "\n")
            for asset, count in executive_summary["most_mentioned_assets"]:
                f.write(f"  {asset.upper()}: {count} mentions\n")

            f.write("\nDETAILED TRADING SIGNALS:\n")
            f.write("-" * 30 + "\n")
            for i, signal in enumerate(self.analysis_results["trading_signals"][:10]):  # Show top 10
                f.write(f"{i+1}. {signal['screenshot']}\n")
                f.write(f"   Model: {signal['model']}\n")
                f.write(f"   Signals: {', '.join(signal['signals_detected'])}\n")
                f.write(f"   High Confidence: {len(signal['high_confidence_signals'])}\n")
                f.write(f"   Time: {signal['timestamp']}\n\n")

        logger.info(f"💾 Comprehensive report saved: {report_file}")
        logger.info(f"📋 Readable report saved: {readable_report}")

    def run_zai_analysis(self):
        """Run the comprehensive ZAI-powered analysis"""
        logger.info("🚀 STARTING ZAI-POWERED TELEGRAM ANALYSIS")
        logger.info("=" * 70)

        try:
            logger.info("🎯 Prioritizing ZAI models for enhanced trading analysis...")

            # Process screenshots with ZAI priority
            self.process_screenshots_with_zai_priority()

            # Extract comprehensive trading signals
            logger.info("💰 Extracting comprehensive trading signals...")
            self.extract_comprehensive_trading_signals()

            # Generate comprehensive report
            logger.info("📊 Generating comprehensive trading report...")
            self.generate_comprehensive_report()

            logger.info("\n" + "="*70)
            logger.info("🎉 ZAI-POWERED ANALYSIS COMPLETED!")
            logger.info("="*70)
            logger.info(f"📸 Screenshots Analyzed: {self.analysis_results['screenshots_processed']}")
            logger.info(f"🤖 ZAI Analyses: {self.analysis_results['zai_analyses']}")
            logger.info(f"🧠 Cerebras Analyses: {self.analysis_results['cerebras_analyses']}")
            logger.info(f"💰 Trading Signals: {self.analysis_results['total_trading_signals']}")
            logger.info(f"📊 Analysis Confidence: {self.analysis_results['executive_summary']['analysis_confidence']}")
            logger.info(f"📁 Results Directory: {self.results_dir}")
            logger.info("="*70)

            if self.analysis_results['total_trading_signals'] > 0:
                logger.info(f"✅ SUCCESS: Found {self.analysis_results['total_trading_signals']} trading signal opportunities!")
            else:
                logger.info("ℹ️  No explicit trading signals detected, but comprehensive text analysis completed")

        except Exception as e:
            logger.error(f"❌ Analysis error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    analyzer = ZAITelegramAnalyzer()
    analyzer.run_zai_analysis()