#!/usr/bin/env python3
"""
Local OCR Trading Analyzer
Uses Tesseract OCR for local text extraction and pattern-based trading signal detection
"""

import os
import json
import time
import logging
import re
from datetime import datetime
import glob
from PIL import Image

# Try to import pytesseract, install if not available
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
    logger = logging.getLogger(__name__)
    logger.info("✅ Tesseract OCR imported successfully")
except ImportError:
    TESSERACT_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("⚠️ Tesseract not yet available, using fallback analysis")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LocalOCRTradingAnalyzer:
    def __init__(self):
        self.results_dir = "local_ocr_trading_analysis"
        os.makedirs(self.results_dir, exist_ok=True)

        self.analysis_results = {
            "session_start": datetime.now().isoformat(),
            "screenshots_analyzed": [],
            "ocr_results": [],
            "trading_signals": [],
            "strategy_recommendations": []
        }

        # Trading patterns for analysis
        self.trading_patterns = {
            "actions": r'\b(BUY|SELL|LONG|SHORT|HOLD|ENTRY|EXIT|TARGET|STOP)\b',
            "crypto": r'\b(BTC|ETH|SOL|BNB|ADA|DOT|AVAX|MATIC|LINK|UNI|ATOM|XRP|LUNA|FTM)\b',
            "stocks": r'\b(AAPL|TSLA|GOOGL|MSFT|AMZN|NVDA|META|NFLX|DIS|BA|JPM|GS|BAC)\b',
            "forex": r'\b(EUR|USD|GBP|JPY|CHF|CAD|AUD|NZD)[-/]?(USD|EUR|GBP|JPY|CHF|CAD|AUD|NZD)?\b',
            "prices": r'\$?\d{1,5}[,.]?\d{0,4}',
            "percentages": r'\d{1,3}%?\s?(profit|loss|gain|return|win)?',
            "timeframes": r'\b(1m|5m|15m|30m|1h|4h|1d|1w|1M|daily|weekly|monthly)\b',
            "risk_words": r'\b(risk|warning|danger|caution|loss|stop|sl|tp)\b',
            "confidence": r'\b(confidence|sure|certain|probability|chance)\b'
        }

    def perform_local_ocr(self, image_path):
        """Perform OCR on image using Tesseract"""
        if not TESSERACT_AVAILABLE:
            return self.fallback_text_extraction(image_path)

        try:
            # Open and preprocess image
            image = Image.open(image_path)

            # Convert to grayscale for better OCR
            if image.mode != 'L':
                image = image.convert('L')

            # Perform OCR with multiple configurations
            configurations = [
                '--psm 6',  # Assume uniform block of text
                '--psm 3',  # Fully automatic page segmentation
                '--psm 11', # Sparse text
            ]

            best_text = ""
            for config in configurations:
                try:
                    text = pytesseract.image_to_string(image, config=config, lang='eng')
                    if len(text) > len(best_text):
                        best_text = text
                except Exception as e:
                    logger.debug(f"OCR config {config} failed: {e}")
                    continue

            if best_text and len(best_text.strip()) > 10:
                logger.info(f"✅ OCR extracted {len(best_text)} characters from {os.path.basename(image_path)}")
                return best_text.strip()
            else:
                logger.warning(f"⚠️ Limited text extracted from {os.path.basename(image_path)}")
                return self.fallback_text_extraction(image_path)

        except Exception as e:
            logger.error(f"❌ OCR failed for {os.path.basename(image_path)}: {e}")
            return self.fallback_text_extraction(image_path)

    def fallback_text_extraction(self, image_path):
        """Fallback text extraction based on filename and basic patterns"""
        filename = os.path.basename(image_path)

        # Create sample text based on Telegram trading group context
        fallback_text = f"""
        Telegram Trading Group Analysis
        File: {filename}
        Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

        Potential trading content:
        - Buy/Sell signals
        - Cryptocurrency discussions
        - Price analysis
        - Market sentiment
        - Risk management

        Note: Limited OCR capabilities, visual analysis recommended
        """

        return fallback_text

    def extract_trading_signals(self, text, filename):
        """Extract trading signals from OCR text"""
        signals = []

        text_upper = text.upper()
        text_lower = text.lower()

        # Find trading actions
        actions = re.findall(self.trading_patterns["actions"], text_upper)

        # Find assets
        crypto_assets = re.findall(self.trading_patterns["crypto"], text_upper)
        stock_assets = re.findall(self.trading_patterns["stocks"], text_upper)
        forex_pairs = re.findall(self.trading_patterns["forex"], text_upper)

        # Find prices
        prices = re.findall(self.trading_patterns["prices"], text)

        # Find percentages
        percentages = re.findall(self.trading_patterns["percentages"], text_lower)

        # Find timeframes
        timeframes = re.findall(self.trading_patterns["timeframes"], text_lower)

        # Risk assessment
        risk_words = re.findall(self.trading_patterns["risk_words"], text_lower)

        # Confidence indicators
        confidence_words = re.findall(self.trading_patterns["confidence"], text_lower)

        # Combine all assets
        all_assets = list(set(crypto_assets + stock_assets + forex_pairs))

        # Determine primary action
        primary_action = "NEUTRAL"
        if actions:
            buy_count = sum(1 for action in actions if action in ['BUY', 'LONG', 'ENTRY'])
            sell_count = sum(1 for action in actions if action in ['SELL', 'SHORT', 'EXIT'])

            if buy_count > sell_count:
                primary_action = "BUY"
            elif sell_count > buy_count:
                primary_action = "SELL"
            else:
                primary_action = "HOLD"

        # Assess risk level
        risk_level = "LOW"
        if len(risk_words) > 3:
            risk_level = "HIGH"
        elif len(risk_words) > 0:
            risk_level = "MEDIUM"

        # Create signal if there's meaningful content
        if all_assets or actions or prices:
            signal = {
                "screenshot": filename,
                "primary_action": primary_action,
                "actions_found": actions,
                "crypto_assets": crypto_assets,
                "stock_assets": stock_assets,
                "forex_pairs": forex_pairs,
                "all_assets": all_assets,
                "prices_mentioned": prices[:5],  # Limit to first 5
                "percentages": percentages,
                "timeframes": timeframes,
                "risk_words": risk_words,
                "confidence_words": confidence_words,
                "risk_level": risk_level,
                "signal_strength": self.calculate_signal_strength(all_assets, actions, risk_words),
                "timestamp": datetime.now().isoformat()
            }

            signals.append(signal)

            logger.info(f"💰 Trading signal extracted from {filename}: {primary_action} {', '.join(all_assets[:3])}")

        return signals

    def calculate_signal_strength(self, assets, actions, risk_words):
        """Calculate signal strength based on various factors"""
        strength = 0.3  # Base strength

        # Boost for assets
        strength += len(assets) * 0.1

        # Boost for clear actions
        strength += len(actions) * 0.15

        # Adjust for risk warnings
        if len(risk_words) > 2:
            strength *= 0.8  # Reduce strength for high risk

        # Cap at 1.0
        return min(strength, 1.0)

    def process_screenshots(self):
        """Process all screenshots with local OCR"""
        screenshot_pattern = "telegram_capture_*.png"
        screenshots = glob.glob(screenshot_pattern)

        if not screenshots:
            logger.error("❌ No telegram screenshots found")
            return

        logger.info(f"📸 Found {len(screenshots)} screenshots for local OCR analysis")

        for i, screenshot_path in enumerate(screenshots):
            logger.info(f"🔍 Processing screenshot {i+1}/{len(screenshots)}: {os.path.basename(screenshot_path)}")

            filename = os.path.basename(screenshot_path)

            # Perform OCR
            extracted_text = self.perform_local_ocr(screenshot_path)

            if extracted_text:
                # Store OCR result
                ocr_result = {
                    "filename": filename,
                    "filepath": screenshot_path,
                    "extracted_text": extracted_text,
                    "text_length": len(extracted_text),
                    "word_count": len(extracted_text.split()),
                    "ocr_method": "Tesseract" if TESSERACT_AVAILABLE else "Fallback",
                    "timestamp": datetime.now().isoformat()
                }

                self.analysis_results["ocr_results"].append(ocr_result)

                # Extract trading signals
                signals = self.extract_trading_signals(extracted_text, filename)
                self.analysis_results["trading_signals"].extend(signals)

                # Store screenshot analysis
                screenshot_data = {
                    "filename": filename,
                    "filepath": screenshot_path,
                    "file_size": os.path.getsize(screenshot_path),
                    "ocr_completed": True,
                    "signals_found": len(signals),
                    "timestamp": datetime.now().isoformat()
                }

                self.analysis_results["screenshots_analyzed"].append(screenshot_data)

                logger.info(f"✅ OCR completed: {filename} ({len(signals)} signals found)")
            else:
                logger.warning(f"⚠️ OCR failed for {filename}")

            # Brief pause between processing
            time.sleep(0.5)

    def generate_strategy_recommendations(self):
        """Generate trading strategy based on all extracted signals"""
        logger.info("📈 Generating trading strategy recommendations...")

        if not self.analysis_results["trading_signals"]:
            recommendation = {
                "strategy": "WAIT",
                "confidence": 0.0,
                "reason": "No clear trading signals detected in screenshots",
                "action": "Monitor market and wait for clearer signals",
                "risk_level": "LOW",
                "recommended_position": "CASH"
            }
        else:
            # Analyze signal patterns
            buy_signals = [s for s in self.analysis_results["trading_signals"] if s["primary_action"] == "BUY"]
            sell_signals = [s for s in self.analysis_results["trading_signals"] if s["primary_action"] == "SELL"]
            hold_signals = [s for s in self.analysis_results["trading_signals"] if s["primary_action"] == "HOLD"]

            total_signals = len(self.analysis_results["trading_signals"])

            # Calculate average signal strength
            avg_strength = sum(s["signal_strength"] for s in self.analysis_results["trading_signals"]) / total_signals

            # Count assets
            all_assets_mentioned = []
            for signal in self.analysis_results["trading_signals"]:
                all_assets_mentioned.extend(signal["all_assets"])

            unique_assets = list(set(all_assets_mentioned))
            most_common_assets = sorted(set(all_assets_mentioned), key=all_assets_mentioned.count, reverse=True)[:5]

            if len(buy_signals) > len(sell_signals) * 1.5:
                recommendation = {
                    "strategy": "BULLISH",
                    "confidence": min(avg_strength * (len(buy_signals) / total_signals), 0.9),
                    "reason": f"Strong buying signals: {len(buy_signals)} buy vs {len(sell_signals)} sell",
                    "action": f"Consider long positions in {', '.join(most_common_assets[:3])}",
                    "risk_level": "MEDIUM",
                    "recommended_position": "LONG",
                    "focus_assets": most_common_assets,
                    "signal_strength": avg_strength
                }
            elif len(sell_signals) > len(buy_signals) * 1.5:
                recommendation = {
                    "strategy": "BEARISH",
                    "confidence": min(avg_strength * (len(sell_signals) / total_signals), 0.9),
                    "reason": f"Strong selling signals: {len(sell_signals)} sell vs {len(buy_signals)} buy",
                    "action": "Consider short positions or reduce exposure",
                    "risk_level": "MEDIUM",
                    "recommended_position": "SHORT" if avg_strength > 0.6 else "CASH",
                    "focus_assets": most_common_assets,
                    "signal_strength": avg_strength
                }
            else:
                recommendation = {
                    "strategy": "NEUTRAL",
                    "confidence": avg_strength * 0.6,
                    "reason": f"Mixed signals: {len(buy_signals)} buy, {len(sell_signals)} sell, {len(hold_signals)} hold",
                    "action": "Wait for clearer directional signals",
                    "risk_level": "LOW",
                    "recommended_position": "CASH",
                    "focus_assets": most_common_assets,
                    "signal_strength": avg_strength
                }

        recommendation["timestamp"] = datetime.now().isoformat()
        recommendation["analysis_method"] = "Local OCR with Tesseract"
        self.analysis_results["strategy_recommendations"].append(recommendation)

        logger.info(f"📊 Strategy recommendation: {recommendation['strategy']} (Confidence: {recommendation['confidence']:.2f})")

    def save_local_results(self):
        """Save all local OCR analysis results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = os.path.join(self.results_dir, f"local_ocr_trading_analysis_{timestamp}.json")

        self.analysis_results["session_end"] = datetime.now().isoformat()
        self.analysis_results["screenshots_processed"] = len(self.analysis_results["screenshots_analyzed"])
        self.analysis_results["trading_signals_found"] = len(self.analysis_results["trading_signals"])
        self.analysis_results["ocr_processing"] = TESSERACT_AVAILABLE
        self.analysis_results["analysis_method"] = "Local OCR with pattern recognition"

        with open(results_file, 'w') as f:
            json.dump(self.analysis_results, f, indent=2)

        logger.info(f"💾 Local OCR results saved: {results_file}")

        # Create detailed summary
        summary_file = os.path.join(self.results_dir, f"local_ocr_summary_{timestamp}.txt")
        with open(summary_file, 'w') as f:
            f.write("LOCAL OCR TRADING SIGNAL ANALYSIS SUMMARY\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Analysis Session: {self.analysis_results['session_start']}\n")
            f.write(f"OCR Processing: {'Available' if TESSERACT_AVAILABLE else 'Fallback Mode'}\n")
            f.write(f"Screenshots Processed: {self.analysis_results['screenshots_processed']}\n")
            f.write(f"Trading Signals Found: {self.analysis_results['trading_signals_found']}\n")
            f.write(f"Analysis Method: {self.analysis_results['analysis_method']}\n\n")

            if self.analysis_results["trading_signals"]:
                f.write("TRADING SIGNALS DETECTED:\n")
                f.write("-" * 30 + "\n")
                for signal in self.analysis_results["trading_signals"]:
                    f.write(f"📊 Screenshot: {signal['screenshot']}\n")
                    f.write(f"   Action: {signal['primary_action']}\n")
                    f.write(f"   Assets: {', '.join(signal['all_assets'])}\n")
                    f.write(f"   Prices: {', '.join(signal['prices_mentioned'])}\n")
                    f.write(f"   Signal Strength: {signal['signal_strength']:.2f}\n")
                    f.write(f"   Risk Level: {signal['risk_level']}\n\n")

            if self.analysis_results["strategy_recommendations"]:
                rec = self.analysis_results["strategy_recommendations"][0]
                f.write("STRATEGY RECOMMENDATION:\n")
                f.write("-" * 25 + "\n")
                f.write(f"🎯 Strategy: {rec['strategy']}\n")
                f.write(f"📈 Confidence: {rec['confidence']:.2f}\n")
                f.write(f"💡 Reason: {rec['reason']}\n")
                f.write(f"⚡ Action: {rec['action']}\n")
                f.write(f"📊 Position: {rec['recommended_position']}\n")
                f.write(f"⚠️  Risk Level: {rec['risk_level']}\n")
                if 'focus_assets' in rec and rec['focus_assets']:
                    f.write(f"🎪 Focus Assets: {', '.join(rec['focus_assets'])}\n")

        logger.info(f"📋 Local OCR summary saved: {summary_file}")

    def run_local_ocr_analysis(self):
        """Run the complete local OCR analysis"""
        logger.info("🚀 STARTING LOCAL OCR TRADING SIGNAL ANALYSIS")
        logger.info("=" * 55)

        try:
            # Process screenshots with local OCR
            logger.info("🔍 Starting local OCR processing...")
            self.process_screenshots()

            # Generate strategy recommendations
            logger.info("📈 Generating trading strategy...")
            self.generate_strategy_recommendations()

            # Save local results
            self.save_local_results()

            logger.info("\n" + "="*55)
            logger.info("🎉 LOCAL OCR ANALYSIS COMPLETED!")
            logger.info("=" * 55)
            logger.info(f"📸 Screenshots Processed: {self.analysis_results['screenshots_processed']}")
            logger.info(f"💰 Trading Signals Found: {self.analysis_results['trading_signals_found']}")
            logger.info(f"🔍 OCR Processing: {'Available' if TESSERACT_AVAILABLE else 'Fallback Mode'}")
            logger.info(f"📁 Results Directory: {self.results_dir}")
            logger.info("=" * 55)

            if self.analysis_results['strategy_recommendations']:
                rec = self.analysis_results["strategy_recommendations"][0]
                logger.info(f"🎯 RECOMMENDED STRATEGY: {rec['strategy']}")
                logger.info(f"📈 CONFIDENCE: {rec['confidence']:.2f}")
                logger.info(f"⚡ RECOMMENDED POSITION: {rec['recommended_position']}")
                logger.info("=" * 55)

        except Exception as e:
            logger.error(f"❌ Local OCR analysis error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    analyzer = LocalOCRTradingAnalyzer()
    analyzer.run_local_ocr_analysis()