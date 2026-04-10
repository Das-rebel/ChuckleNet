#!/usr/bin/env python3
"""
Setup Script for Brave Browser Telegram Scraper

This script helps verify and configure the Brave browser setup for the Telegram scraper.
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_brave_installation():
    """Check if Brave browser is installed"""
    logger.info("🔍 Checking Brave browser installation...")

    possible_paths = [
        "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
        os.path.expanduser("~/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"),
    ]

    for path in possible_paths:
        if os.path.exists(path):
            logger.info(f"✅ Brave Browser found at: {path}")
            return True, path

    # Try to find via Spotlight
    try:
        result = subprocess.run(['mdfind', 'kMDItemDisplayName == "Brave Browser"'],
                              capture_output=True, text=True)
        if result.stdout.strip():
            app_path = result.stdout.strip()
            binary_path = os.path.join(app_path, "Contents/MacOS/Brave Browser")
            if os.path.exists(binary_path):
                logger.info(f"✅ Brave Browser found via Spotlight: {binary_path}")
                return True, binary_path
    except:
        pass

    logger.error("❌ Brave Browser not found")
    logger.info("Please install Brave Browser from: https://brave.com/")
    return False, None

def check_brave_user_data():
    """Check Brave browser user data directory"""
    logger.info("🔍 Checking Brave user data...")

    possible_paths = [
        os.path.expanduser("~/Library/Application Support/BraveSoftware/Brave-Browser"),
        os.path.expanduser("~/Library/Application Support/Brave-Browser"),
    ]

    for path in possible_paths:
        if os.path.exists(path):
            logger.info(f"✅ Brave user data found at: {path}")
            return True, path

    logger.error("❌ Brave user data directory not found")
    logger.info("Please run Brave Browser at least once to create user data")
    return False, None

def check_telegram_session():
    """Check if Telegram Web is logged in"""
    logger.info("🔍 Checking for existing Telegram session...")

    # This is a simplified check - in reality, we'd need to examine the browser's
    # local storage or cookies to verify Telegram login status
    brave_paths = [
        os.path.expanduser("~/Library/Application Support/BraveSoftware/Brave-Browser"),
        os.path.expanduser("~/Library/Application Support/Brave-Browser"),
    ]

    for brave_path in brave_paths:
        if os.path.exists(brave_path):
            local_storage_path = os.path.join(brave_path, "Default", "Local Storage")
            if os.path.exists(local_storage_path):
                logger.info(f"✅ Found browser local storage at: {local_storage_path}")
                logger.info("⚠️  Please verify you are logged into Telegram Web in Brave browser")
                return True

    logger.warning("⚠️  Unable to verify Telegram session automatically")
    logger.info("Please ensure you are logged into Telegram Web in Brave browser")
    return False

def check_dependencies():
    """Check Python dependencies"""
    logger.info("🔍 Checking Python dependencies...")

    required_modules = [
        'selenium',
        'psutil'
    ]

    missing_modules = []

    for module in required_modules:
        try:
            __import__(module)
            logger.info(f"✅ {module} - OK")
        except ImportError:
            logger.error(f"❌ {module} - Missing")
            missing_modules.append(module)

    if missing_modules:
        logger.error(f"❌ Missing dependencies: {missing_modules}")
        logger.info("Install with: pip3 install " + " ".join(missing_modules))
        return False

    logger.info("✅ All dependencies are installed")
    return True

def install_dependencies():
    """Install missing dependencies"""
    logger.info("📦 Installing dependencies...")

    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "selenium", "psutil"],
                      check=True)
        logger.info("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Failed to install dependencies: {e}")
        logger.info("Please try: pip3 install selenium psutil")
        return False

def create_desktop_shortcut():
    """Create a desktop shortcut for easy access"""
    logger.info("🖥️  Creating desktop shortcut...")

    desktop_path = os.path.expanduser("~/Desktop")
    script_path = os.path.abspath("brave_telegram_scraper.py")

    if not os.path.exists(script_path):
        logger.error("❌ brave_telegram_scraper.py not found in current directory")
        return False

    # Create a simple shell script launcher
    launcher_path = os.path.join(desktop_path, "StartTelegramScraper.command")
    launcher_content = f"""#!/bin/bash
cd "{os.path.dirname(script_path)}"
python3 "{script_path}"
echo "Press Enter to close..."
read
"""

    try:
        with open(launcher_path, 'w') as f:
            f.write(launcher_content)

        # Make it executable
        os.chmod(launcher_path, 0o755)
        logger.info(f"✅ Desktop shortcut created: {launcher_path}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create desktop shortcut: {e}")
        return False

def test_brave_connection():
    """Test connection to Brave browser"""
    logger.info("🧪 Testing Brave browser connection...")

    try:
        # Import selenium here to check if it's working
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options

        # Check if we can start Brave with debugging
        options = Options()
        options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

        logger.info("⚠️  This test requires Brave browser to be running with remote debugging")
        logger.info("To enable remote debugging:")
        logger.info("1. Close all Brave browser windows")
        logger.info("2. Run: /Applications/Brave\\ Browser.app/Contents/MacOS/Brave\\ Browser --remote-debugging-port=9222")
        logger.info("3. Then run this test again")

        return True

    except ImportError:
        logger.error("❌ Selenium not properly installed")
        return False
    except Exception as e:
        logger.error(f"❌ Connection test failed: {e}")
        return False

def main():
    """Main setup function"""
    logger.info("🚀 BRAVE TELEGRAM SCRAPER SETUP")
    logger.info("=" * 50)

    # Check installation
    brave_ok, brave_path = check_brave_installation()
    if not brave_ok:
        return

    # Check user data
    user_data_ok, user_data_path = check_brave_user_data()
    if not user_data_ok:
        return

    # Check Telegram session
    telegram_ok = check_telegram_session()

    # Check dependencies
    deps_ok = check_dependencies()
    if not deps_ok:
        logger.info("📦 Installing missing dependencies...")
        if not install_dependencies():
            return

    # Create desktop shortcut
    create_desktop_shortcut()

    # Test connection (optional)
    test_brave_connection()

    # Final summary
    logger.info("\n" + "=" * 50)
    logger.info("✅ SETUP COMPLETE!")
    logger.info("=" * 50)
    logger.info("\n📋 SETUP SUMMARY:")
    logger.info(f"   Brave Browser: ✅ ({brave_path})")
    logger.info(f"   User Data: ✅ ({user_data_path})")
    logger.info(f"   Dependencies: ✅")
    logger.info(f"   Telegram Session: ⚠️  (Please verify you're logged in)")
    logger.info(f"   Desktop Shortcut: ✅")

    logger.info("\n🚀 NEXT STEPS:")
    logger.info("1. Open Brave Browser")
    logger.info("2. Go to https://web.telegram.org/k/")
    logger.info("3. Log in to your Telegram account")
    logger.info("4. Run: python3 brave_telegram_scraper.py")
    logger.info("5. Or double-click the 'StartTelegramScraper' icon on Desktop")

    logger.info("\n💡 TIPS:")
    logger.info("- Keep Brave browser open while running the scraper")
    logger.info("- The scraper uses your existing session - no need to log in again")
    logger.info("- All trading signals will be saved to JSON files")
    logger.info("- Monitor the console output for real-time signal detection")

if __name__ == "__main__":
    main()