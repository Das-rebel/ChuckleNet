#!/usr/bin/env python3
"""
Comprehensive Telegram Data Extractor with OCR and AI Analysis
Extracts text and screenshots from Telegram group, then performs OCR and AI analysis
"""

import time
import json
import logging
import subprocess
import base64
import requests
from datetime import datetime, timedelta
from PIL import Image
import pytesseract
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TelegramExtractor:
    def __init__(self):
        self.results_dir = "telegram_extraction_results"
        self.screenshots_dir = os.path.join(self.results_dir, "screenshots")
        self.analysis_dir = os.path.join(self.results_dir, "analysis")

        # Create directories
        os.makedirs(self.screenshots_dir, exist_ok=True)
        os.makedirs(self.analysis_dir, exist_ok=True)

        self.extracted_data = {
            "extraction_session": datetime.now().isoformat(),
            "screenshots": [],
            "text_messages": [],
            "ocr_results": [],
            "ai_analysis": []
        }

    def execute_applescript(self, script):
        """Execute AppleScript command"""
        try:
            result = subprocess.run(['osascript', '-e', script],
                                 capture_output=True, text=True, timeout=30)
            return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
        except Exception as e:
            return False, "", str(e)

    def activate_brave(self):
        """Activate Brave browser"""
        script = '''tell application "Brave Browser" to activate'''
        success, output, error = self.execute_applescript(script)
        if success:
            logger.info("✅ Brave activated")
            return True
        else:
            logger.error(f"❌ Failed to activate Brave: {error}")
            return False

    def take_screenshot(self, description=""):
        """Take a screenshot and save with timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"telegram_screenshot_{timestamp}.png"
        filepath = os.path.join(self.screenshots_dir, filename)

        script = f'''
        tell application "System Events"
            do shell script "screencapture -x {filepath}"
        end tell
        '''

        success, output, error = self.execute_applescript(script)
        if success and os.path.exists(filepath):
            screenshot_data = {
                "filename": filename,
                "filepath": filepath,
                "timestamp": datetime.now().isoformat(),
                "description": description,
                "file_size": os.path.getsize(filepath)
            }
            self.extracted_data["screenshots"].append(screenshot_data)
            logger.info(f"📸 Screenshot saved: {filename} ({screenshot_data['file_size']} bytes)")
            return filepath
        else:
            logger.error(f"❌ Screenshot failed: {error}")
            return None

    def scroll_and_capture(self, scroll_count=10):
        """Scroll through messages and capture screenshots"""
        logger.info("📜 Starting scroll and capture process...")

        for i in range(scroll_count):
            logger.info(f"📸 Capturing screen {i+1}/{scroll_count}")

            # Take screenshot
            self.take_screenshot(f"Screen {i+1}")

            # Scroll up to see older messages
            if i < scroll_count - 1:  # Don't scroll after last screenshot
                scroll_script = '''
                tell application "System Events"
                    tell process "Brave Browser"
                        keystroke "page up"
                        delay 1
                    end tell
                end tell
                '''
                success, output, error = self.execute_applescript(scroll_script)
                if not success:
                    logger.warning(f"⚠️  Scroll failed: {error}")

                time.sleep(2)  # Wait for content to load

    def extract_text_from_screenshots(self):
        """Extract text from screenshots using OCR"""
        logger.info("🔍 Performing OCR on screenshots...")

        for screenshot in self.extracted_data["screenshots"]:
            filepath = screenshot["filepath"]
            logger.info(f"🔍 OCR processing: {screenshot['filename']}")

            try:
                # Open image
                image = Image.open(filepath)

                # Extract text using Tesseract OCR
                extracted_text = pytesseract.image_to_string(image, config='--psm 6')

                # Clean up the text
                cleaned_text = extracted_text.strip().replace('\n', ' ')

                if cleaned_text and len(cleaned_text) > 10:
                    ocr_result = {
                        "screenshot_filename": screenshot["filename"],
                        "extracted_text": cleaned_text,
                        "word_count": len(cleaned_text.split()),
                        "timestamp": datetime.now().isoformat()
                    }
                    self.extracted_data["ocr_results"].append(ocr_result)
                    logger.info(f"✅ OCR extracted {ocr_result['word_count']} words")
                else:
                    logger.info("ℹ️  No significant text found in screenshot")

            except Exception as e:
                logger.error(f"❌ OCR failed for {screenshot['filename']}: {e}")

    def analyze_with_cerebras(self, text):
        """Analyze text with Cerebras AI"""
        cerebras_api_key = os.getenv('CEREBRAS_API_KEY')
        if not cerebras_api_key:
            logger.warning("⚠️  CEREBRAS_API_KEY not found, skipping AI analysis")
            return None

        try:
            headers = {
                "Authorization": f"Bearer {cerebras_api_key}",
                "Content-Type": "application/json"
            }

            prompt = f"""
            Analyze this trading signal text and extract:
            1. Trading recommendations (BUY/SELL/HOLD)
            2. Assets mentioned (BTC, ETH, stocks, forex pairs, etc.)
            3. Price levels (entry, targets, stop losses)
            4. Confidence score (0-1)
            5. Risk level (LOW/MEDIUM/HIGH)
            6. Timeframe mentioned
            7. Key insights or warnings

            Text: {text}

            Respond with JSON format.
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
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                analysis = result["choices"][0]["message"]["content"]
                return analysis
            else:
                logger.error(f"❌ Cerebras API error: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"❌ Cerebras analysis failed: {e}")
            return None

    def perform_ai_analysis(self):
        """Perform AI analysis on extracted text"""
        logger.info("🤖 Performing AI analysis on extracted text...")

        # Combine all OCR text for analysis
        all_text = " ".join([result["extracted_text"] for result in self.extracted_data["ocr_results"]])

        if not all_text or len(all_text) < 50:
            logger.warning("⚠️  Not enough text for AI analysis")
            return

        logger.info(f"🤖 Analyzing {len(all_text)} characters of text...")

        # Analyze with Cerebras
        ai_result = self.analyze_with_cerebras(all_text)

        if ai_result:
            analysis_data = {
                "model_used": "cerebras_llama-3.3-70b",
                "text_length": len(all_text),
                "analysis": ai_result,
                "timestamp": datetime.now().isoformat()
            }
            self.extracted_data["ai_analysis"].append(analysis_data)
            logger.info("✅ AI analysis completed")
        else:
            logger.warning("⚠️  AI analysis failed")

    def identify_trading_signals(self):
        """Identify trading signals from OCR text"""
        logger.info("💰 Identifying trading signals...")

        trading_keywords = ['buy', 'sell', 'long', 'short', 'hold', 'trade', 'price', 'signal',
                          'btc', 'eth', 'bitcoin', 'ethereum', 'aapl', 'tsla', 'gold', 'eur/usd']

        signals_found = []

        for ocr_result in self.extracted_data["ocr_results"]:
            text = ocr_result["extracted_text"].lower()

            if any(keyword in text for keyword in trading_keywords):
                signal_data = {
                    "screenshot": ocr_result["screenshot_filename"],
                    "text_snippet": ocr_result["extracted_text"][:200],
                    "found_keywords": [kw for kw in trading_keywords if kw in text],
                    "timestamp": ocr_result["timestamp"]
                }
                signals_found.append(signal_data)
                logger.info(f"💰 Trading signal found in {ocr_result['screenshot_filename']}")

        self.extracted_data["trading_signals"] = signals_found
        logger.info(f"📊 Total trading signals found: {len(signals_found)}")

    def save_results(self):
        """Save all extraction results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = os.path.join(self.results_dir, f"telegram_extraction_{timestamp}.json")

        # Add summary statistics
        self.extracted_data["summary"] = {
            "total_screenshots": len(self.extracted_data["screenshots"]),
            "ocr_results_count": len(self.extracted_data["ocr_results"]),
            "trading_signals_found": len(self.extracted_data.get("trading_signals", [])),
            "ai_analysis_performed": len(self.extracted_data["ai_analysis"]) > 0,
            "extraction_completed": datetime.now().isoformat()
        }

        with open(results_file, 'w') as f:
            json.dump(self.extracted_data, f, indent=2)

        logger.info(f"💾 Results saved: {results_file}")

        # Also save a readable summary
        summary_file = os.path.join(self.results_dir, f"extraction_summary_{timestamp}.txt")
        with open(summary_file, 'w') as f:
            f.write("TELEGRAM EXTRACTION SUMMARY\n")
            f.write("=" * 40 + "\n\n")
            f.write(f"Extraction Date: {self.extracted_data['extraction_session']}\n")
            f.write(f"Total Screenshots: {self.extracted_data['summary']['total_screenshots']}\n")
            f.write(f"OCR Results: {self.extracted_data['summary']['ocr_results_count']}\n")
            f.write(f"Trading Signals: {self.extracted_data['summary']['trading_signals_found']}\n")
            f.write(f"AI Analysis: {'Completed' if self.extracted_data['summary']['ai_analysis_performed'] else 'Failed'}\n\n")

            if self.extracted_data.get("trading_signals"):
                f.write("TRADING SIGNALS FOUND:\n")
                f.write("-" * 20 + "\n")
                for i, signal in enumerate(self.extracted_data["trading_signals"][:5]):
                    f.write(f"{i+1}. {signal['text_snippet']}\n")
                    f.write(f"   Keywords: {', '.join(signal['found_keywords'])}\n\n")

        logger.info(f"📋 Summary saved: {summary_file}")

    def run_complete_extraction(self):
        """Run the complete extraction process"""
        logger.info("🚀 STARTING COMPREHENSIVE TELEGRAM EXTRACTION")
        logger.info("=" * 60)

        try:
            # Step 1: Activate Brave
            if not self.activate_brave():
                return

            time.sleep(2)

            # Step 2: Take initial screenshot
            logger.info("📸 Taking initial screenshot...")
            self.take_screenshot("Initial State")

            # Step 3: Scroll and capture multiple screenshots
            self.scroll_and_capture(scroll_count=8)

            # Step 4: Extract text using OCR
            self.extract_text_from_screenshots()

            # Step 5: Identify trading signals
            self.identify_trading_signals()

            # Step 6: Perform AI analysis
            self.perform_ai_analysis()

            # Step 7: Save all results
            self.save_results()

            logger.info("\n" + "="*60)
            logger.info("🎉 EXTRACTION COMPLETED SUCCESSFULLY!")
            logger.info("="*60)
            logger.info(f"📸 Screenshots: {self.extracted_data['summary']['total_screenshots']}")
            logger.info(f"🔍 OCR Results: {self.extracted_data['summary']['ocr_results_count']}")
            logger.info(f"💰 Trading Signals: {self.extracted_data['summary']['trading_signals_found']}")
            logger.info(f"🤖 AI Analysis: {'Completed' if self.extracted_data['summary']['ai_analysis_performed'] else 'Failed'}")
            logger.info(f"📁 Results Directory: {self.results_dir}")
            logger.info("="*60)

        except Exception as e:
            logger.error(f"❌ Extraction error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    extractor = TelegramExtractor()
    extractor.run_complete_extraction()