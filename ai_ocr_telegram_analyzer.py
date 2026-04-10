#!/usr/bin/env python3
"""
AI-Powered OCR and Telegram Analysis
Uses OpenAI GPT-4V or Cerebras AI for OCR and trading signal analysis
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

class AITelegramAnalyzer:
    def __init__(self):
        self.results_dir = "ai_telegram_analysis"
        os.makedirs(self.results_dir, exist_ok=True)

        self.analysis_results = {
            "session_start": datetime.now().isoformat(),
            "screenshots_analyzed": [],
            "ocr_results": [],
            "trading_signals": [],
            "ai_analysis": []
        }

    def encode_image_to_base64(self, image_path):
        """Convert image to base64 for AI analysis"""
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            logger.error(f"Error encoding image {image_path}: {e}")
            return None

    def analyze_with_openai_vision(self, image_base64, image_filename):
        """Analyze screenshot with OpenAI GPT-4V Vision"""
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if not openai_api_key:
            logger.warning("⚠️  OPENAI_API_KEY not found")
            return None

        try:
            headers = {
                "Authorization": f"Bearer {openai_api_key}",
                "Content-Type": "application/json"
            }

            prompt = """
            Analyze this Telegram trading group screenshot and extract:

            1. All visible text messages (exactly as shown)
            2. Trading signals (BUY/SELL/HOLD recommendations)
            3. Asset symbols mentioned (BTC, ETH, AAPL, TSLA, forex pairs, etc.)
            4. Price levels (entry prices, targets, stop losses)
            5. Timeframes or time indicators
            6. Any percentages or ratios
            7. Confidence levels mentioned
            8. Market sentiment (bullish/bearish)

            Provide the results in JSON format with these categories:
            {
                "extracted_text": "all visible text",
                "trading_signals": [{"action": "BUY/SELL/HOLD", "asset": "BTC/ETH/etc", "price": "price level", "confidence": "0.0-1.0"}],
                "market_analysis": {"sentiment": "bullish/bearish/neutral", "timeframe": " timeframe"},
                "key_insights": ["insight 1", "insight 2"]
            }
            """

            payload = {
                "model": "gpt-4o",
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
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                analysis = result["choices"][0]["message"]["content"]
                logger.info(f"✅ OpenAI GPT-4V analysis completed for {image_filename}")
                return analysis
            else:
                logger.error(f"❌ OpenAI API error: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"❌ OpenAI analysis failed for {image_filename}: {e}")
            return None

    def analyze_with_cerebras(self, image_base64, image_filename):
        """Analyze screenshot with Cerebras AI (text-based approach)"""
        cerebras_api_key = os.getenv('CEREBRAS_API_KEY')
        if not cerebras_api_key:
            logger.warning("⚠️  CEREBRAS_API_KEY not found")
            return None

        try:
            headers = {
                "Authorization": f"Bearer {cerebras_api_key}",
                "Content-Type": "application/json"
            }

            # First, get a basic description of the image
            description_prompt = """
            Describe this screenshot in detail. Look for:
            - Any text visible in the image
            - Trading-related content, charts, or financial information
            - User interface elements that indicate this is a messaging app
            - Any numbers, prices, or financial symbols
            """

            payload = {
                "model": "llama-3.3-70b",
                "messages": [{"role": "user", "content": description_prompt}],
                "max_tokens": 1000,
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
                description = result["choices"][0]["message"]["content"]
                logger.info(f"✅ Cerebras analysis completed for {image_filename}")

                # Then analyze the description for trading signals
                analysis_prompt = f"""
                Based on this screenshot description: "{description}"

                Extract and analyze trading information:
                1. Text messages and trading signals
                2. Asset mentions (BTC, ETH, stocks, forex)
                3. Price levels or targets
                4. Buy/sell recommendations
                5. Risk levels or confidence

                Return as JSON:
                {{
                    "description": "{description}",
                    "trading_analysis": {{
                        "has_trading_content": true/false,
                        "signals_found": ["signal1", "signal2"],
                        "assets_mentioned": ["asset1", "asset2"],
                        "price_levels": ["level1", "level2"],
                        "recommendations": ["action1", "action2"]
                    }}
                }}
                """

                analysis_payload = {
                    "model": "llama-3.3-70b",
                    "messages": [{"role": "user", "content": analysis_prompt}],
                    "max_tokens": 1500,
                    "temperature": 0.1
                }

                analysis_response = requests.post(
                    "https://api.cerebras.ai/v1/chat/completions",
                    headers=headers,
                    json=analysis_payload,
                    timeout=45
                )

                if analysis_response.status_code == 200:
                    analysis_result = analysis_response.json()
                    final_analysis = analysis_result["choices"][0]["message"]["content"]
                    return {
                        "description": description,
                        "analysis": final_analysis
                    }

            else:
                logger.error(f"❌ Cerebras API error: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"❌ Cerebras analysis failed for {image_filename}: {e}")
            return None

    def process_screenshots(self, use_openai=True):
        """Process all Telegram screenshots with AI"""

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

            # Analyze with AI
            filename = os.path.basename(screenshot_path)
            analysis_result = None

            if use_openai:
                analysis_result = self.analyze_with_openai_vision(image_base64, filename)
                model_used = "OpenAI GPT-4V"
            else:
                analysis_result = self.analyze_with_cerebras(image_base64, filename)
                model_used = "Cerebras Llama-3.3-70b"

            if analysis_result:
                screenshot_data = {
                    "filename": filename,
                    "filepath": screenshot_path,
                    "file_size": os.path.getsize(screenshot_path),
                    "model_used": model_used,
                    "analysis": analysis_result,
                    "timestamp": datetime.now().isoformat()
                }

                self.analysis_results["screenshots_analyzed"].append(screenshot_data)
                self.analysis_results["ai_analysis"].append(screenshot_data)

                logger.info(f"✅ Analysis completed: {filename}")

            # Brief pause between requests
            time.sleep(2)

    def extract_trading_signals(self):
        """Extract and organize trading signals from AI analysis"""
        trading_keywords = ['buy', 'sell', 'long', 'short', 'hold', 'trade', 'signal', 'price', 'target', 'stop']

        for analysis in self.analysis_results["ai_analysis"]:
            analysis_text = analysis["analysis"].lower()

            # Look for trading keywords
            found_signals = []
            for keyword in trading_keywords:
                if keyword in analysis_text:
                    found_signals.append(keyword)

            if found_signals:
                signal_data = {
                    "screenshot": analysis["filename"],
                    "model": analysis["model_used"],
                    "trading_keywords": found_signals,
                    "analysis_snippet": analysis["analysis"][:500],
                    "timestamp": analysis["timestamp"]
                }
                self.analysis_results["trading_signals"].append(signal_data)
                logger.info(f"💰 Trading signals found in {analysis['filename']}")

    def save_results(self):
        """Save all analysis results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = os.path.join(self.results_dir, f"ai_telegram_analysis_{timestamp}.json")

        self.analysis_results["session_end"] = datetime.now().isoformat()
        self.analysis_results["screenshots_processed"] = len(self.analysis_results["screenshots_analyzed"])
        self.analysis_results["trading_signals_found"] = len(self.analysis_results["trading_signals"])

        with open(results_file, 'w') as f:
            json.dump(self.analysis_results, f, indent=2)

        logger.info(f"💾 Results saved: {results_file}")

        # Create readable summary
        summary_file = os.path.join(self.results_dir, f"ai_analysis_summary_{timestamp}.txt")
        with open(summary_file, 'w') as f:
            f.write("AI-POWERED TELEGRAM ANALYSIS SUMMARY\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Analysis Session: {self.analysis_results['session_start']}\n")
            f.write(f"AI Model Used: OpenAI GPT-4V or Cerebras Llama-3.3-70b\n")
            f.write(f"Screenshots Processed: {self.analysis_results['screenshots_processed']}\n")
            f.write(f"Trading Signals Found: {self.analysis_results['trading_signals_found']}\n\n")

            if self.analysis_results["trading_signals"]:
                f.write("TRADING SIGNALS DETECTED:\n")
                f.write("-" * 30 + "\n")
                for signal in self.analysis_results["trading_signals"]:
                    f.write(f"📊 {signal['screenshot']}\n")
                    f.write(f"   Keywords: {', '.join(signal['trading_keywords'])}\n")
                    f.write(f"   Model: {signal['model']}\n")
                    f.write(f"   Time: {signal['timestamp']}\n\n")

        logger.info(f"📋 Summary saved: {summary_file}")

    def run_analysis(self):
        """Run the complete AI analysis"""
        logger.info("🤖 STARTING AI-POWERED TELEGRAM ANALYSIS")
        logger.info("=" * 60)

        try:
            # Try OpenAI first, fallback to Cerebras
            logger.info("🔍 Attempting analysis with OpenAI GPT-4V...")
            self.process_screenshots(use_openai=True)

            if len(self.analysis_results["screenshots_analyzed"]) == 0:
                logger.info("🔄 Falling back to Cerebras AI...")
                self.process_screenshots(use_openai=False)

            # Extract trading signals
            logger.info("💰 Extracting trading signals...")
            self.extract_trading_signals()

            # Save results
            self.save_results()

            logger.info("\n" + "="*60)
            logger.info("🎉 AI ANALYSIS COMPLETED!")
            logger.info("="*60)
            logger.info(f"📸 Screenshots Analyzed: {self.analysis_results['screenshots_processed']}")
            logger.info(f"💰 Trading Signals: {self.analysis_results['trading_signals_found']}")
            logger.info(f"🤖 AI Models Used: OpenAI GPT-4V / Cerebras")
            logger.info(f"📁 Results Directory: {self.results_dir}")
            logger.info("="*60)

            if self.analysis_results['trading_signals_found'] > 0:
                logger.info(f"✅ SUCCESS: Found trading signals in {self.analysis_results['trading_signals_found']} screenshots!")
            else:
                logger.info("ℹ️  No explicit trading signals detected, but text was extracted")

        except Exception as e:
            logger.error(f"❌ Analysis error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    analyzer = AITelegramAnalyzer()
    analyzer.run_analysis()