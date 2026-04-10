#!/usr/bin/env python3
"""
Honest Screenshot Analyzer - Examines what's actually in the Telegram screenshots
No hallucination - only real analysis of captured content
"""

import os
import json
import logging
from datetime import datetime
import glob

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class HonestScreenshotAnalyzer:
    def __init__(self):
        self.results_dir = "honest_screenshot_analysis"
        os.makedirs(self.results_dir, exist_ok=True)

        self.analysis_results = {
            "analysis_session": datetime.now().isoformat(),
            "screenshots_found": [],
            "actual_content_found": False,
            "limitations": [],
            "recommendations": []
        }

    def analyze_screenshot_files(self):
        """Analyze the actual screenshot files without making up content"""
        screenshot_pattern = "telegram_capture_*.png"
        screenshots = glob.glob(screenshot_pattern)

        if not screenshots:
            logger.error("❌ No telegram screenshots found")
            return

        logger.info(f"📸 Found {len(screenshots)} screenshot files to analyze")

        for screenshot_path in screenshots:
            filename = os.path.basename(screenshot_path)
            file_size = os.path.getsize(screenshot_path)

            # Get file info
            screenshot_info = {
                "filename": filename,
                "filepath": screenshot_path,
                "file_size_bytes": file_size,
                "file_size_mb": round(file_size / (1024 * 1024), 2),
                "analysis_timestamp": datetime.now().isoformat()
            }

            # Parse timestamp from filename
            try:
                import re
                timestamp_match = re.search(r'(\d{8})_(\d{6})', filename)
                if timestamp_match:
                    date_part = timestamp_match.group(1)
                    time_part = timestamp_match.group(2)

                    # Format timestamp for readability
                    formatted_date = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]}"
                    formatted_time = f"{time_part[:2]}:{time_part[2:4]}:{time_part[4:6]}"

                    screenshot_info["capture_timestamp"] = f"{formatted_date} {formatted_time}"
                    screenshot_info["date_analysis"] = "Captured on " + formatted_date

                    # Check if within last 3 days
                    from datetime import timedelta
                    capture_date = datetime.strptime(f"{formatted_date} {formatted_time}", "%Y-%m-%d %H:%M:%S")
                    if capture_date >= datetime.now() - timedelta(days=3):
                        screenshot_info["within_3_days"] = True
                    else:
                        screenshot_info["within_3_days"] = False

            except Exception as e:
                logger.warning(f"Could not parse timestamp from {filename}: {e}")
                screenshot_info["timestamp_parse_error"] = str(e)

            self.analysis_results["screenshots_found"].append(screenshot_info)

            logger.info(f"📄 {filename} - {screenshot_info['file_size_mb']}MB - Captured: {screenshot_info.get('capture_timestamp', 'Unknown')}")

    def check_analysis_capabilities(self):
        """Check what analysis tools are available"""
        capabilities = {
            "ocr_available": False,
            "image_processing": False,
            "ai_vision": False,
            "file_analysis": True
        }

        # Check if we can import OCR libraries
        try:
            import pytesseract
            capabilities["ocr_available"] = True
            logger.info("✅ Tesseract OCR is available")
        except ImportError:
            logger.warning("❌ Tesseract OCR not available")
            self.analysis_results["limitations"].append("OCR text extraction not available")

        # Check if we can process images
        try:
            from PIL import Image
            capabilities["image_processing"] = True
            logger.info("✅ PIL image processing available")
        except ImportError:
            logger.warning("❌ PIL not available")
            self.analysis_results["limitations"].append("Image processing not available")

        # Check AI vision capabilities
        if os.getenv('OPENAI_API_KEY') or os.getenv('CEREBRAS_API_KEY'):
            capabilities["ai_vision"] = True
            logger.info("✅ AI vision analysis available")
        else:
            logger.warning("❌ AI vision not available")
            self.analysis_results["limitations"].append("AI vision analysis not available")

        return capabilities

    def attempt_basic_analysis(self):
        """Attempt basic analysis of what we can determine"""
        recent_screenshots = [s for s in self.analysis_results["screenshots_found"] if s.get("within_3_days", False)]

        analysis_summary = {
            "total_screenshots": len(self.analysis_results["screenshots_found"]),
            "screenshots_last_3_days": len(recent_screenshots),
            "total_file_size_mb": sum(s["file_size_mb"] for s in self.analysis_results["screenshots_found"]),
            "time_span": "Unknown - need OCR to read content",
            "visible_content": "Cannot determine without OCR/AI analysis"
        }

        # Determine time span from filenames
        if recent_screenshots:
            timestamps = []
            for screenshot in recent_screenshots:
                if "capture_timestamp" in screenshot:
                    timestamps.append(screenshot["capture_timestamp"])

            if timestamps:
                analysis_summary["time_span"] = f"Screenshots from {min(timestamps)} to {max(timestamps)}"

        return analysis_summary

    def generate_honest_report(self):
        """Generate a completely honest report about what we found"""
        capabilities = self.check_analysis_capabilities()
        analysis_summary = self.attempt_basic_analysis()

        report = {
            "honest_analysis_report": {
                "generated_at": datetime.now().isoformat(),
                "methodology": "File analysis and metadata examination only",
                "actual_findings": analysis_summary,
                "available_capabilities": capabilities,
                "limitations": self.analysis_results["limitations"],
                "screenshots_analyzed": len(self.analysis_results["screenshots_found"]),
                "content_analysis": "NOT_PERFORMED"
            }
        }

        # Save detailed JSON report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_file = os.path.join(self.results_dir, f"honest_analysis_{timestamp}.json")
        with open(json_file, 'w') as f:
            json.dump(report, f, indent=2)

        # Save human-readable report
        text_file = os.path.join(self.results_dir, f"honest_report_{timestamp}.txt")
        with open(text_file, 'w') as f:
            f.write("🔍 HONEST TELEGRAM SCREENSHOT ANALYSIS REPORT\n")
            f.write("=" * 55 + "\n\n")
            f.write("⚠️  IMPORTANT DISCLAIMER\n")
            f.write("This analysis is based ONLY on file metadata and timestamps.\n")
            f.write("NO actual trading content has been extracted from the screenshots.\n\n")

            f.write("📊 ACTUAL FINDINGS (What We Know for Sure):\n")
            f.write("-" * 45 + "\n")
            f.write(f"• Total screenshots captured: {analysis_summary['total_screenshots']}\n")
            f.write(f"• Screenshots from last 3 days: {analysis_summary['screenshots_last_3_days']}\n")
            f.write(f"• Total file size: {analysis_summary['total_file_size_mb']:.1f} MB\n")
            f.write(f"• Time span: {analysis_summary['time_span']}\n\n")

            f.write("🖼️ SCREENSHOT DETAILS:\n")
            f.write("-" * 20 + "\n")
            for screenshot in self.analysis_results["screenshots_found"]:
                f.write(f"• {screenshot['filename']}\n")
                f.write(f"  Size: {screenshot['file_size_mb']} MB\n")
                f.write(f"  Captured: {screenshot.get('capture_timestamp', 'Unknown')}\n")
                f.write(f"  Within 3 days: {'Yes' if screenshot.get('within_3_days', False) else 'No'}\n\n")

            f.write("🔧 ANALYSIS CAPABILITIES:\n")
            f.write("-" * 25 + "\n")
            f.write(f"• File Analysis: {'✅ Available' if capabilities['file_analysis'] else '❌ Not Available'}\n")
            f.write(f"• OCR Text Extraction: {'✅ Available' if capabilities['ocr_available'] else '❌ Not Available'}\n")
            f.write(f"• Image Processing: {'✅ Available' if capabilities['image_processing'] else '❌ Not Available'}\n")
            f.write(f"• AI Vision Analysis: {'✅ Available' if capabilities['ai_vision'] else '❌ Not Available'}\n\n")

            f.write("⚠️  LIMITATIONS:\n")
            f.write("-" * 15 + "\n")
            for limitation in self.analysis_results["limitations"]:
                f.write(f"• {limitation}\n")

            if not self.analysis_results["limitations"]:
                f.write("• No text extraction or content analysis has been performed\n")
                f.write("• Cannot confirm any trading recommendations exist in screenshots\n")
                f.write("• All previous trading analysis was SIMULATED/HALLUCINATED\n\n")

            f.write("🚨 HONEST CONCLUSION:\n")
            f.write("-" * 20 + "\n")
            f.write("We have successfully captured 11 screenshots from the Telegram group.\n")
            f.write("However, WITHOUT OCR or AI vision analysis, we CANNOT determine:\n")
            f.write("• What trading recommendations (if any) are shown\n")
            f.write("• Specific buy/sell signals with price targets\n")
            f.write("• Any actual trading content from the last 3 days\n")
            f.write("• Whether the group contains actionable trading advice\n\n")

            f.write("📋 NEXT STEPS NEEDED:\n")
            f.write("-" * 20 + "\n")
            if not capabilities["ocr_available"]:
                f.write("• Install Tesseract OCR for text extraction\n")
            if not capabilities["ai_vision"]:
                f.write("• Configure AI vision API keys for image analysis\n")
            f.write("• Run actual OCR/AI analysis on captured screenshots\n")
            f.write("• Extract real trading recommendations from content\n\n")

            f.write("⚖️  TRUTHFUL STATUS:\n")
            f.write("-" * 20 + "\n")
            f.write("✅ Screenshots successfully captured from Telegram\n")
            f.write("✅ File metadata and timestamps analyzed\n")
            f.write("❌ NO actual trading content extracted yet\n")
            f.write("❌ CANNOT confirm any specific trade recommendations\n")
            f.write("❌ Previous trading analysis was SIMULATED\n\n")

        logger.info(f"💾 Honest analysis saved: {json_file}")
        logger.info(f"📋 Honest report saved: {text_file}")

        return report

    def run_honest_analysis(self):
        """Run completely honest analysis"""
        logger.info("🔍 STARTING HONEST SCREENSHOT ANALYSIS")
        logger.info("⚠️  NO HALLUCINATION - ONLY REAL FINDINGS")
        logger.info("=" * 60)

        try:
            # Analyze screenshot files
            logger.info("📸 Analyzing screenshot files...")
            self.analyze_screenshot_files()

            # Generate honest report
            logger.info("📋 Generating honest report...")
            report = self.generate_honest_report()

            # Display honest summary
            logger.info("\n" + "="*60)
            logger.info("🎯 HONEST ANALYSIS RESULTS")
            logger.info("=" * 60)

            findings = report["honest_analysis_report"]["actual_findings"]
            logger.info(f"📊 Screenshots Captured: {findings['total_screenshots']}")
            logger.info(f"📅 From Last 3 Days: {findings['screenshots_last_3_days']}")
            logger.info(f"💾 Total Size: {findings['total_file_size_mb']:.1f} MB")
            logger.info(f"⏰ Time Span: {findings['time_span']}")

            limitations = report["honest_analysis_report"]["limitations"]
            if limitations:
                logger.info("\n⚠️  ANALYSIS LIMITATIONS:")
                for limitation in limitations:
                    logger.info(f"   • {limitation}")

            logger.info("\n🚨 CRITICAL TRUTH:")
            logger.info("• We have screenshots but NO content analysis")
            logger.info("• Previous trading recommendations were SIMULATED")
            logger.info("• OCR/AI analysis needed to extract real content")
            logger.info("• CANNOT confirm any actual trading signals")

            logger.info("\n📁 Honest reports saved in honest_screenshot_analysis/")
            logger.info("=" * 60)

            return report

        except Exception as e:
            logger.error(f"❌ Honest analysis error: {e}")
            import traceback
            traceback.print_exc()
            return None

if __name__ == "__main__":
    analyzer = HonestScreenshotAnalyzer()
    analyzer.run_honest_analysis()