#!/usr/bin/env python3
"""
ALTERNATIVE TELEGRAM SETUP
Multiple methods to get API credentials
"""

import asyncio
import os
from telethon.sync import TelegramClient

async def check_existing_session():
    """Check if we have an existing session we can use"""
    print("🔍 CHECKING FOR EXISTING SESSIONS...")

    session_files = [
        'trading_monitor_session.session',
        'telethon_session.session',
        'default.session'
    ]

    for session_file in session_files:
        if os.path.exists(session_file):
            print(f"✅ Found existing session: {session_file}")
            try:
                # Try to use existing session (might need API keys anyway)
                print("💡 Existing sessions still require API credentials")
                return False
            except:
                continue

    print("❌ No existing sessions found")
    return False

def manual_setup_guide():
    """Provide detailed manual setup instructions"""
    print("""
🎯 MANUAL SETUP GUIDE - STEP BY STEP
=====================================

IF WEBSITE IS NOT WORKING:

METHOD 1: DIFFERENT BROWSER
----------------------------
• Try Safari instead of Chrome/Brave
• Try incognito/private mode
• Clear browser cookies first
• Use: https://my.telegram.org/apps

METHOD 2: DIFFERENT APP NAME
---------------------------
If "Trading Monitor" doesn't work, try:
• App title: "My Telegram App"
• Short name: "myapp"
• Platform: Desktop
• Description: "Personal application"

METHOD 3: MINIMAL INFO
----------------------
• App title: "Test"
• Short name: "test"
• Platform: Desktop
• Description: "Testing"

COMMON ERRORS & FIXES:
----------------------
• Error: "Incorrect app name!" → Use shorter name, no special characters
• Error: "App not found" → Wait 10 minutes and try again
• Error: "Invalid phone" → Use country code: +1234567890

QUICK TEMPLATE FOR .ENV FILE:
----------------------------
TELEGRAM_API_ID=28451523  (example - replace with yours)
TELEGRAM_API_HASH=abcdef123456789abcdef123456789  (example - replace)
TELEGRAM_PHONE=+1234567890  (replace with your number)

ONCE YOU HAVE CREDENTIALS:
--------------------------
1. Edit /Users/Subho/.env
2. Replace the YOUR_* values
3. Run: python3 enhanced_telethon_trader.py
""")

def troubleshoot_website_issues():
    """Help troubleshoot my.telegram.org issues"""
    print("""
🔧 WEBSITE TROUBLESHOOTING
==========================

IF MY.TELEGRAM.ORG IS NOT WORKING:

1. CHECK NETWORK:
   • Try: ping my.telegram.org
   • Check if you can reach the site

2. ALTERNATIVE APPROACH:
   • The site might be temporarily down
   • Try again in 10-15 minutes
   • Use a VPN if needed

3. BROWSER ISSUES:
   • Clear cache and cookies
   • Try a different browser
   • Disable browser extensions

4. ACCOUNT ISSUES:
   • Make sure your phone number is active
   • Check if you have 2FA enabled
   • Ensure Telegram account is not restricted

IF ALL ELSE FAILS:
------------------
We can try other approaches:
• Browser automation (use your existing Brave session)
• Your bot @Das_ts_bot for manual message forwarding
• Screenshot + OCR analysis
""")

async def main():
    """Main troubleshooting function"""
    print("🚀 ALTERNATIVE TELEGRAM SETUP TROUBLESHOOTER")
    print("=" * 60)

    # Check for existing sessions
    await check_existing_session()

    # Provide manual setup guide
    manual_setup_guide()

    # Troubleshoot website issues
    troubleshoot_website_issues()

    print("\n🎯 RECOMMENDED NEXT STEPS:")
    print("1. Try the website with a different browser")
    print("2. If that fails, we can use alternative methods")
    print("3. Your bot @Das_ts_bot is ready as backup")

    choice = input("\n❓ Do you want to try the website again? (y/n): ").strip().lower()

    if choice == 'y':
        print("🌐 Opening website in Safari...")
        os.system('open -a Safari https://my.telegram.org/')
        print("📱 Try the steps from the manual guide above")
    else:
        print("🔄 Let's try alternative methods...")
        print("💡 Your bot @Das_ts_bot is ready for message forwarding")
        print("📸 Or we can use screenshot + OCR approach")

if __name__ == "__main__":
    asyncio.run(main())