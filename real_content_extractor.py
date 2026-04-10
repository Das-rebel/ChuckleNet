#!/usr/bin/env python3
"""
Real Content Extractor - Extracts actual content from Telegram screenshots using AI vision
No hallucination - only real analysis of captured screenshot content
"""

import os
import json
import time
import logging
import base64
import requests
from datetime import datetime, timedelta
import glob

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RealContentExtractor:
    def __init__(self):
        self.results_dir = "real_content_extraction"
        os.makedirs(self.results_dir, exist_ok=True)

        self.extraction_results = {
            "extraction_session": datetime.now().isoformat(),
            "screenshots_processed": [],
            "actual_text_found": [],
            "trading_content_detected": [],
            "real_trades": []
        }

    def encode_image_to_base64(self, image_path):
        """Convert image to base64 for AI analysis"""
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            logger.error(f"Error encoding image {image_path}: {e}")
            return None

    def analyze_screenshot_with_openai(self, image_base64, image_filename):
        """Analyze screenshot with OpenAI GPT-4V Vision for actual content"""
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if not openai_api_key:
            logger.warning("⚠️ OpenAI API key not found")
            return None

        try:
            headers = {
                "Authorization": f"Bearer {openai_api_key}",
                "Content-Type": "application/json"
            }

            prompt = """
            Analyze this Telegram screenshot and extract ONLY what you can actually see.

            Extract EXACTLY:
            1. All visible text messages (exactly as written)
            2. Any cryptocurrency symbols or trading pairs mentioned
            3. Any price levels, buy/sell signals, or trading recommendations
            4. Any timestamps or dates visible
            5. User names or channel information
            6. Any charts, graphs, or technical indicators visible

            IMPORTANT:
            - Only extract content that is actually visible in the image
            - Do not make up or hallucinate any information
            - If you cannot see trading content, state that clearly
            - Be completely honest about what is visible vs what is not

            Return in this JSON format:
            {
                "visible_text": ["exact text messages you can read"],
                "trading_content": {
                    "has_trading_signals": true/false,
                    "symbols_mentioned": ["actual symbols visible"],
                    "price_levels": ["actual prices visible"],
                    "recommendations": ["exact buy/sell recommendations if visible"],
                    "analysis": ["actual market analysis if visible"]
                },
                "image_content": {
                    "has_charts": true/false,
                    "has_indicators": true/false,
                    "ui_elements": ["telegram interface elements visible"],
                    "usernames": ["visible usernames"],
                    "timestamps": ["visible dates/times"]
                },
                "confidence_level": "high/medium/low based on clarity",
                "notes": "any observations about image quality or readability"
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
                logger.info(f"✅ OpenAI analysis completed for {image_filename}")
                return analysis
            else:
                logger.error(f"❌ OpenAI API error: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"❌ OpenAI analysis failed for {image_filename}: {e}")
            return None

    def analyze_with_cerebras(self, image_base64, image_filename):
        """Analyze screenshot with Cerebras AI for actual content"""
        cerebras_api_key = os.getenv('CEREBRAS_API_KEY')
        if not cerebras_api_key:
            logger.warning("⚠️ Cerebras API key not found")
            return None

        try:
            headers = {
                "Authorization": f"Bearer {cerebras_api_key}",
                "Content-Type": "application/json"
            }

            prompt = """
            Look at this Telegram screenshot and tell me exactly what text and content you can see.

            Be completely honest about:
            - What text is actually readable
            - Any trading symbols or prices visible
            - Any buy/sell recommendations you can see
            - Any charts or technical analysis visible

            Only report what you can actually see in the image. If you cannot read text or see trading content, say so clearly.
            """

            payload = {
                "model": "llama-3.3-70b",
                "messages": [{"role": "user", "content": prompt}],
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
                analysis = result["choices"][0]["message"]["content"]
                logger.info(f"✅ Cerebras analysis completed for {image_filename}")
                return analysis
            else:
                logger.error(f"❌ Cerebras API error: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"❌ Cerebras analysis failed for {image_filename}: {e}")
            return None

    def extract_real_trades_from_analysis(self, analysis_text, filename):
        """Extract real trading information from AI analysis"""
        real_trades = []

        try:
            # Try to parse JSON from the analysis
            if isinstance(analysis_text, str):
                import re
                json_match = re.search(r'\{[\s\S]*\}', analysis_text)
                if json_match:
                    try:
                        parsed_data = json.loads(json_match.group())

                        if "trading_content" in parsed_data:
                            trading = parsed_data["trading_content"]

                            if trading.get("has_trading_signals", False):
                                trade_info = {
                                    "filename": filename,
                                    "symbols_mentioned": trading.get("symbols_mentioned", []),
                                    "price_levels": trading.get("price_levels", []),
                                    "recommendations": trading.get("recommendations", []),
                                    "analysis": trading.get("analysis", []),
                                    "source": "AI_Vision_Analysis",
                                    "confidence": parsed_data.get("confidence_level", "unknown"),
                                    "extracted_at": datetime.now().isoformat()
                                }

                                real_trades.append(trade_info)

                                # Log what we actually found
                                if trade_info["symbols_mentioned"]:
                                    logger.info(f"📊 Found symbols: {trade_info['symbols_mentioned']} in {filename}")
                                if trade_info["recommendations"]:
                                    logger.info(f"💰 Found recommendations: {trade_info['recommendations'][:2]} in {filename}")

                    except json.JSONDecodeError:
                        # Fallback to text analysis
                        logger.info(f"Could not parse JSON from {filename}, analyzing text directly")

        except Exception as e:
            logger.warning(f"Error parsing analysis for {filename}: {e}")

        return real_trades

    def process_screenshots_with_ai(self):
        """Process all screenshots with AI vision to extract actual content"""
        screenshot_pattern = "telegram_capture_*.png"
        screenshots = glob.glob(screenshot_pattern)

        if not screenshots:
            logger.error("❌ No telegram screenshots found")
            return

        logger.info(f"📸 Found {len(screenshots)} screenshots to analyze with AI vision")

        for i, screenshot_path in enumerate(screenshots):
            filename = os.path.basename(screenshot_path)
            logger.info(f"🔍 Analyzing {filename} ({i+1}/{len(screenshots)})")

            # Encode image
            image_base64 = self.encode_image_to_base64(screenshot_path)
            if not image_base64:
                logger.error(f"❌ Failed to encode {filename}")
                continue

            # Try OpenAI first (better vision capabilities)
            analysis_result = None
            analysis_method = "none"

            analysis_result = self.analyze_screenshot_with_openai(image_base64, filename)
            if analysis_result:
                analysis_method = "OpenAI GPT-4V"
            else:
                # Fallback to Cerebras
                analysis_result = self.analyze_with_cerebras(image_base64, filename)
                if analysis_result:
                    analysis_method = "Cerebras Llama-3.3-70B"

            if analysis_result:
                # Store the raw analysis
                screenshot_data = {
                    "filename": filename,
                    "filepath": screenshot_path,
                    "file_size": os.path.getsize(screenshot_path),
                    "analysis_method": analysis_method,
                    "raw_analysis": analysis_result,
                    "timestamp": datetime.now().isoformat()
                }

                self.extraction_results["screenshots_processed"].append(screenshot_data)

                # Extract actual trading content
                real_trades = self.extract_real_trades_from_analysis(analysis_result, filename)
                self.extraction_results["real_trades"].extend(real_trades)

                if real_trades:
                    logger.info(f"✅ Found real trading content in {filename}")
                else:
                    logger.info(f"ℹ️ No clear trading signals found in {filename}")

                self.extraction_results["actual_text_found"].append({
                    "filename": filename,
                    "analysis": analysis_result,
                    "has_trading_content": len(real_trades) > 0
                })

            # Brief pause between requests
            time.sleep(3)

    def generate_honest_results(self):
        """Generate honest results about what we actually found"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Summary statistics
        total_screenshots = len(self.extraction_results["screenshots_processed"])
        screenshots_with_trades = len([s for s in self.extraction_results["actual_text_found"] if s["has_trading_content"]])
        total_real_trades = len(self.extraction_results["real_trades"])

        # Create honest summary
        honest_summary = {
            "extraction_completed": datetime.now().isoformat(),
            "methodology": "AI Vision Analysis (OpenAI GPT-4V + Cerebras fallback)",
            "screenshots_analyzed": total_screenshots,
            "screenshots_with_trading_content": screenshots_with_trades,
            "total_trading_signals_found": total_real_trades,
            "analysis_honesty": "COMPLETELY_HONEST - only extracted visible content",
            "real_trades": self.extraction_results["real_trades"],
            "raw_analyses": self.extraction_results["actual_text_found"]
        }

        # Save JSON results
        json_file = os.path.join(self.results_dir, f"real_content_analysis_{timestamp}.json")
        with open(json_file, 'w') as f:
            json.dump(honest_summary, f, indent=2)

        # Create human-readable results
        text_file = os.path.join(self.results_dir, f"real_trading_content_{timestamp}.txt")
        with open(text_file, 'w') as f:
            f.write("🔍 REAL CONTENT EXTRACTION FROM TELEGRAM SCREENSHOTS\n")
            f.write("=" * 65 + "\n\n")
            f.write("⚠️  COMPLETELY HONEST ANALYSIS - NO HALLUCINATION\n")
            f.write("This contains ONLY what AI vision could actually see in the screenshots.\n\n")

            f.write(f"📊 ANALYSIS SUMMARY:\n")
            f.write(f"• Screenshots analyzed: {total_screenshots}\n")
            f.write(f"• Screenshots with trading content: {screenshots_with_trades}\n")
            f.write(f"• Total trading signals found: {total_real_trades}\n")
            f.write(f"• Analysis date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            if self.extraction_results["real_trades"]:
                f.write("💰 ACTUAL TRADING CONTENT FOUND:\n")
                f.write("-" * 35 + "\n")

                for i, trade in enumerate(self.extraction_results["real_trades"], 1):
                    f.write(f"\n🎯 TRADING SIGNAL #{i}:\n")
                    f.write(f"Source: {trade['filename']}\n")

                    if trade["symbols_mentioned"]:
                        f.write(f"Symbols: {', '.join(trade['symbols_mentioned'])}\n")

                    if trade["recommendations"]:
                        f.write(f"Recommendations: {', '.join(trade['recommendations'][:3])}\n")

                    if trade["price_levels"]:
                        f.write(f"Price Levels: {', '.join(trade['price_levels'][:3])}\n")

                    if trade["analysis"]:
                        f.write(f"Analysis: {', '.join(trade['analysis'][:2])}\n")

                    f.write(f"Confidence: {trade['confidence']}\n")
            else:
                f.write("❌ NO TRADING SIGNALS DETECTED\n")
                f.write("The AI vision analysis could not find clear trading recommendations\n")
                f.write("in any of the Telegram screenshots.\n\n")

            f.write("\n📋 SCREENSHOT-BY-SCREENSHOT ANALYSIS:\n")
            f.write("-" * 40 + "\n")

            for screenshot in self.extraction_results["screenshots_processed"]:
                f.write(f"\n📸 {screenshot['filename']}\n")
                f.write(f"Method: {screenshot['analysis_method']}\n")
                f.write(f"File size: {screenshot['file_size']:,} bytes\n")

                # Find corresponding analysis
                analysis = next((a for a in self.extraction_results["actual_text_found"]
                               if a["filename"] == screenshot["filename"]), None)
                if analysis:
                    f.write(f"Trading content found: {'Yes' if analysis['has_trading_content'] else 'No'}\n")

        logger.info(f"💾 Real analysis saved: {json_file}")
        logger.info(f"📋 Human-readable results saved: {text_file}")

        return honest_summary

    def run_real_content_extraction(self):
        """Run real content extraction from screenshots"""
        logger.info("🚀 STARTING REAL CONTENT EXTRACTION")
        logger.info("⚠️  COMPLETELY HONEST - NO HALLUCINATION ALLOWED")
        logger.info("=" * 60)

        try:
            # Process screenshots with AI vision
            logger.info("🔍 Processing screenshots with AI vision...")
            self.process_screenshots_with_ai()

            # Generate honest results
            logger.info("📋 Generating honest results...")
            results = self.generate_honest_results()

            # Display honest summary
            logger.info("\n" + "="*60)
            logger.info("🎯 REAL CONTENT EXTRACTION RESULTS")
            logger.info("=" * 60)

            logger.info(f"📸 Screenshots Analyzed: {results['screenshots_analyzed']}")
            logger.info(f"💰 Screenshots with Trading Content: {results['screenshots_with_trading_content']}")
            logger.info(f"🎯 Total Trading Signals Found: {results['total_trading_signals_found']}")

            if results["real_trades"]:
                logger.info("\n💰 ACTUAL TRADING CONTENT DETECTED:")
                for i, trade in enumerate(results["real_trades"][:5], 1):
                    if trade["symbols_mentioned"]:
                        logger.info(f"{i}. Symbols: {', '.join(trade['symbols_mentioned'])} in {trade['filename']}")
                    if trade["recommendations"]:
                        logger.info(f"   Recommendations: {', '.join(trade['recommendations'][:2])}")
            else:
                logger.info("\n❌ NO TRADING SIGNALS FOUND")
                logger.info("AI vision analysis did not detect clear trading recommendations")

            logger.info(f"\n📁 Results saved in {self.results_dir}/")
            logger.info("=" * 60)

            return results

        except Exception as e:
            logger.error(f"❌ Real content extraction error: {e}")
            import traceback
            traceback.print_exc()
            return None

if __name__ == "__main__":
    extractor = RealContentExtractor()
    extractor.run_real_content_extraction()