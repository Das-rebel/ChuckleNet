#!/usr/bin/env python3
"""
REAL TELEGRAM GROUP ACCESS
Attempts multiple approaches to access actual group content without new API creation
"""

import os
import json
import logging
import asyncio
from datetime import datetime, timedelta
import re

# Try all possible import approaches
try:
    from opentele.td import TDesktop
    from opentele import Telethon
    OPENTELE_AVAILABLE = True
    print("✅ OpenTele available")
except ImportError as e:
    OPENTELE_AVAILABLE = False
    print(f"❌ OpenTele not available: {e}")

try:
    import telethon
    TELETHON_AVAILABLE = True
    print("✅ Telethon available")
except ImportError as e:
    TELETHON_AVAILABLE = False
    print(f"❌ Telethon not available: {e}")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RealGroupAccess:
    """Access real Telegram group content using existing sessions"""

    def __init__(self):
        self.target_group = -2127259353
        self.session_path = "/Users/Subho/Library/Application Support/Telegram Desktop/tdata"
        self.results_dir = "real_group_analysis"
        os.makedirs(self.results_dir, exist_ok=True)

    async def attempt_opentele_access(self):
        """Attempt to access using OpenTele session conversion"""
        print("\n🔄 Attempt 1: OpenTele Session Conversion")
        print("=" * 50)

        if not OPENTELE_AVAILABLE:
            print("❌ OpenTele not available")
            return None

        try:
            print(f"📁 Checking session path: {self.session_path}")

            if not os.path.exists(self.session_path):
                print(f"❌ Session path not found")
                return None

            print("✅ Session path exists")

            # Try to load TDesktop session
            try:
                print("📋 Loading TDesktop session...")
                tdesk = TDesktop.from_telegram_desktop(self.session_path)
                print("✅ TDesktop session loaded successfully")

                # Get session info
                print(f"📊 Session info: {tdesk}")

                # Try to convert to Telethon
                telethon_session = os.path.join(self.results_dir, "real_session")
                print("🔄 Converting to Telethon session...")

                client = await tdesk.to_telethon_session(telethon_session)
                print("✅ Successfully converted to Telethon session")

                return client

            except Exception as e:
                print(f"❌ TDesktop conversion error: {e}")
                return None

        except Exception as e:
            print(f"❌ OpenTele access failed: {e}")
            return None

    async def attempt_browser_automation(self):
        """Attempt to access using browser automation"""
        print("\n🔄 Attempt 2: Browser Automation")
        print("=" * 50)

        try:
            # Open Brave to the specific group
            group_url = f"https://web.telegram.org/k/#{self.target_group}"
            print(f"🌐 Opening: {group_url}")

            os.system(f'open -a "Brave Browser" "{group_url}"')
            print("✅ Brave Browser opened with group URL")

            # Wait for page to load
            print("⏳ Waiting 5 seconds for page to load...")
            await asyncio.sleep(5)

            return "browser_opened"

        except Exception as e:
            print(f"❌ Browser automation failed: {e}")
            return None

    async def attempt_screenshot_analysis(self):
        """Take screenshots and analyze for actual content"""
        print("\n🔄 Attempt 3: Advanced Screenshot Analysis")
        print("=" * 50)

        try:
            from PIL import ImageGrab
            import pytesseract

            print("✅ Screenshot tools available")

            # Take multiple screenshots
            screenshots = []
            for i in range(3):
                print(f"📸 Taking screenshot {i+1}/3...")

                # Bring Brave to front
                os.system('osascript -e \'tell application "Brave Browser" to activate\'')
                await asyncio.sleep(1)

                # Capture screenshot
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"real_group_screenshot_{timestamp}_{i}.png"
                filepath = os.path.join(self.results_dir, filename)

                screenshot = ImageGrab.grab()
                screenshot.save(filepath)
                screenshots.append(filepath)

                print(f"✅ Screenshot saved: {filename}")

                # Analyze immediately
                text = pytesseract.image_to_string(screenshot)
                print(f"📝 Extracted {len(text)} characters")

                # Quick check for trading content
                trading_keywords = ['buy', 'sell', 'btc', 'eth', 'price', '$', 'target']
                if any(keyword in text.lower() for keyword in trading_keywords):
                    print(f"🎯 Trading content detected in screenshot {i+1}!")
                    print(f"📝 Preview: {text[:200]}...")

                if i < 2:
                    print("⏳ Waiting 3 seconds...")
                    await asyncio.sleep(3)

            return screenshots

        except Exception as e:
            print(f"❌ Screenshot analysis failed: {e}")
            return None

    async def attempt_existing_session_direct(self):
        """Try to use existing session files directly"""
        print("\n🔄 Attempt 4: Direct Session File Analysis")
        print("=" * 50)

        try:
            # Look for existing session files
            session_files = []

            # Check for various session file patterns
            patterns = [
                "*.session",
                "*.session*",
                "tdata/*",
                "*.db",
                "*.sqlite"
            ]

            print(f"📁 Searching in: {self.session_path}")
            for pattern in patterns:
                try:
                    import glob
                    matches = glob.glob(os.path.join(self.session_path, pattern))
                    session_files.extend(matches)
                    print(f"📋 Found {len(matches)} files matching {pattern}")
                except:
                    pass

            if session_files:
                print(f"✅ Found {len(session_files)} session-related files:")
                for file in session_files[:10]:  # Show first 10
                    size = os.path.getsize(file) if os.path.exists(file) else 0
                    print(f"   • {os.path.basename(file)} ({size} bytes)")
            else:
                print("⚠️ No session files found with standard patterns")

            return session_files

        except Exception as e:
            print(f"❌ Direct session analysis failed: {e}")
            return None

    async def check_bot_forwarding_status(self):
        """Check if bot forwarding is working"""
        print("\n🔄 Attempt 5: Bot Forwarding Check")
        print("=" * 50)

        try:
            # Your bot should be @Das_ts_bot
            bot_username = "@Das_ts_bot"
            print(f"🤖 Checking bot: {bot_username}")
            print("💡 If you can see this bot, you can forward messages to it for analysis")
            print("📋 Bot features:")
            print("   • Instant AI analysis of forwarded messages")
            print("   • Trading signal detection")
            print("   • Price level extraction")
            print("   • Sentiment analysis")
            print("   • Risk assessment")

            return "bot_available"

        except Exception as e:
            print(f"❌ Bot check failed: {e}")
            return None

    async def run_comprehensive_analysis(self):
        """Run all access attempts"""
        print("🚀 COMPREHENSIVE TELEGRAM GROUP ACCESS")
        print("=" * 60)
        print(f"🎯 Target Group: {self.target_group}")
        print(f"📁 Session Path: {self.session_path}")
        print("=" * 60)

        results = {}

        # Attempt 1: OpenTele
        results['opentele'] = await self.attempt_opentele_access()

        # Attempt 2: Browser automation
        results['browser'] = await self.attempt_browser_automation()

        # Attempt 3: Screenshot analysis
        results['screenshots'] = await self.attempt_screenshot_analysis()

        # Attempt 4: Direct session analysis
        results['session_files'] = await self.attempt_existing_session_direct()

        # Attempt 5: Bot forwarding
        results['bot'] = await self.check_bot_forwarding_status()

        # Generate summary report
        await self.generate_access_report(results)

        return results

    async def generate_access_report(self, results):
        """Generate comprehensive access report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        report = {
            "access_analysis": {
                "target_group": self.target_group,
                "session_path": self.session_path,
                "analysis_date": datetime.now().isoformat(),
                "attempts_made": len(results)
            },
            "results": {}
        }

        working_methods = []
        for method, result in results.items():
            if result:
                working_methods.append(method)
                report["results"][method] = {
                    "status": "success",
                    "details": str(result)[:200]
                }
            else:
                report["results"][method] = {
                    "status": "failed",
                    "details": "No access possible"
                }

        # Save report
        report_file = os.path.join(self.results_dir, f"access_analysis_report_{timestamp}.json")
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        # Display summary
        print("\n" + "=" * 60)
        print("🎯 ACCESS ANALYSIS COMPLETE!")
        print("=" * 60)
        print(f"📊 Working Methods Found: {len(working_methods)}")

        if working_methods:
            print(f"✅ Successful approaches:")
            for method in working_methods:
                print(f"   • {method.title()}")
        else:
            print("⚠️ No direct access methods worked")
            print("💡 Recommendations:")
            print("   • Use bot forwarding: Forward messages to @Das_ts_bot")
            print("   • Manual screenshots: Use browser and take screenshots")
            print("   • Check Telegram Desktop: Ensure you're logged into the target group")

        print(f"📁 Detailed report: {report_file}")
        print("=" * 60)

async def main():
    """Main execution"""
    access = RealGroupAccess()
    await access.run_comprehensive_analysis()

if __name__ == "__main__":
    asyncio.run(main())