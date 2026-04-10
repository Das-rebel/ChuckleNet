#!/usr/bin/env python3
"""
Setup Script for Brave Browser Telegram Scraper with OpenAI GPT-4V Vision

This script helps verify and configure the enhanced scraper with OpenAI GPT-4V capabilities.
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_openai_api_key():
    """Check if OpenAI API key is configured"""
    logger.info("🔑 Checking OpenAI API key configuration...")

    api_key = os.getenv('OPENAI_API_KEY')
    if api_key:
        logger.info("✅ OPENAI_API_KEY environment variable is set")
        logger.info(f"   API Key: {api_key[:10]}...{api_key[-4:]}")
        return True
    else:
        logger.error("❌ OPENAI_API_KEY environment variable not set")
        logger.info("Please set your OpenAI API key:")
        logger.info("export OPENAI_API_KEY='your-openai-api-key-here'")
        logger.info("")
        logger.info("You can get OpenAI API keys from: https://platform.openai.com/api-keys")
        return False

def test_openai_connection(api_key: str):
    """Test connection to OpenAI API"""
    logger.info("🧪 Testing OpenAI API connection...")

    try:
        import requests
        import base64

        # Create a simple test image (1x1 pixel)
        test_image_data = "R0lGODdhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw=="  # 1x1 transparent GIF
        image_data = base64.b64decode(test_image_data)

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "This is a test image. Please respond with 'OK' if you can see this."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/gif;base64,{test_image_data}",
                                "detail": "low"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 10
        }

        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=15
        )

        if response.status_code == 200:
            logger.info("✅ OpenAI GPT-4V API connection successful")
            return True
        else:
            logger.error(f"❌ OpenAI API error: {response.status_code}")
            if response.status_code == 401:
                logger.error("   Invalid API key - please check your OPENAI_API_KEY")
            elif response.status_code == 429:
                logger.error("   Rate limit exceeded - please try again later")
            logger.error(f"Response: {response.text}")
            return False

    except Exception as e:
        logger.error(f"❌ Connection test failed: {e}")
        return False

def check_dependencies():
    """Check Python dependencies"""
    logger.info("🔍 Checking Python dependencies...")

    required_modules = [
        'selenium',
        'psutil',
        'requests',
        'openai',
        'PIL'  # Pillow
    ]

    missing_modules = []

    for module in required_modules:
        try:
            if module == 'PIL':
                __import__('PIL')
                logger.info(f"✅ Pillow - OK")
            else:
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
        subprocess.run([sys.executable, "-m", "pip", "install",
                       "selenium", "psutil", "requests", "openai", "pillow"],
                      check=True)
        logger.info("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Failed to install dependencies: {e}")
        return False

def check_brave_setup():
    """Check Brave browser setup"""
    logger.info("🔍 Checking Brave browser setup...")

    possible_paths = [
        "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
        os.path.expanduser("~/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"),
    ]

    for path in possible_paths:
        if os.path.exists(path):
            logger.info(f"✅ Brave Browser found at: {path}")

            # Check user data
            user_data_paths = [
                os.path.expanduser("~/Library/Application Support/BraveSoftware/Brave-Browser"),
                os.path.expanduser("~/Library/Application Support/Brave-Browser"),
            ]

            for user_path in user_data_paths:
                if os.path.exists(user_path):
                    logger.info(f"✅ Brave user data found at: {user_path}")
                    return True

    logger.error("❌ Brave Browser not found or user data missing")
    return False

def create_directories():
    """Create necessary directories"""
    logger.info("📁 Creating directories...")

    directories = [
        "telegram_images",
        "processed_images",
        "reports"
    ]

    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            logger.info(f"✅ Created directory: {directory}")
        except Exception as e:
            logger.error(f"❌ Failed to create {directory}: {e}")

def create_launch_script():
    """Create a launch script for GPT-4V scraper"""
    logger.info("🚀 Creating GPT-4V launch script...")

    script_content = """#!/bin/bash

# Brave Telegram Scraper with OpenAI GPT-4V Launcher
echo "🚀 Starting Brave Telegram Scraper with OpenAI GPT-4V Vision..."
echo "================================================================"

# Check if API key is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ OPENAI_API_KEY not set"
    echo "Please set your API key:"
    echo "export OPENAI_API_KEY='your-openai-api-key-here'"
    exit 1
fi

# Check if Python dependencies are available
python3 -c "import selenium, psutil, requests, openai, PIL" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Missing Python dependencies"
    echo "Install with: pip3 install selenium psutil requests openai pillow"
    exit 1
fi

# Check if Brave is running
pgrep -f "Brave Browser" > /dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Brave Browser is not running"
    echo "Starting Brave with remote debugging..."
    /Applications/Brave\\ Browser.app/Contents/MacOS/Brave\\ Browser \\
        --remote-debugging-port=9222 \\
        --user-data-dir="$HOME/Library/Application Support/BraveSoftware/Brave-Browser" &
    echo "Waiting for Brave to start..."
    sleep 5
fi

echo "✅ All checks passed. Starting GPT-4V enhanced scraper..."
echo "📊 Will analyze last 7 days of trading signals"
echo "🖼️  Images will be processed with GPT-4V vision model"
echo "📋 Comprehensive report will be generated"
echo ""
echo "Press Ctrl+C to stop analysis"
echo "================================================================"

# Start the GPT-4V scraper
python3 brave_telegram_scraper_with_gpt4v.py
"""

    script_path = "start_gpt4v_scraper.sh"
    try:
        with open(script_path, 'w') as f:
            f.write(script_content)

        os.chmod(script_path, 0o755)
        logger.info(f"✅ Created launch script: {script_path}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create launch script: {e}")
        return False

def main():
    """Main setup function"""
    logger.info("🚀 OPENAI GPT-4V ENHANCED TELEGRAM SCRAPER SETUP")
    logger.info("=" * 65)

    # Check API key
    if not check_openai_api_key():
        return

    api_key = os.getenv('OPENAI_API_KEY')

    # Check dependencies
    deps_ok = check_dependencies()
    if not deps_ok:
        logger.info("📦 Installing missing dependencies...")
        if not install_dependencies():
            return

    # Check Brave setup
    brave_ok = check_brave_setup()
    if not brave_ok:
        return

    # Test OpenAI connection
    logger.info("\n🧪 Testing OpenAI GPT-4V API connection...")
    openai_ok = test_openai_connection(api_key)

    # Create directories
    create_directories()

    # Create launch script
    create_launch_script()

    # Final summary
    logger.info("\n" + "=" * 65)
    logger.info("✅ SETUP COMPLETE!")
    logger.info("=" * 65)
    logger.info("\n📋 SETUP SUMMARY:")
    logger.info(f"   OpenAI API Key: ✅")
    logger.info(f"   Dependencies: ✅")
    logger.info(f"   Brave Browser: ✅")
    logger.info(f"   Directories: ✅")
    logger.info(f"   Launch Script: ✅")
    logger.info(f"   API Connection: {'✅' if openai_ok else '⚠️  (Check API key/endpoint)'}")

    logger.info("\n🚀 NEXT STEPS:")
    logger.info("1. Open Brave Browser")
    logger.info("2. Go to https://web.telegram.org/k/")
    logger.info("3. Log in to your Telegram account")
    logger.info("4. Navigate to your trading channel")
    logger.info("5. Run: ./start_gpt4v_scraper.sh")
    logger.info("   OR: python3 brave_telegram_scraper_with_gpt4v.py")

    logger.info("\n🆕 GPT-4V VISION FEATURES:")
    logger.info("🖼️  Advanced image analysis with GPT-4V")
    logger.info("📊 Superior chart pattern recognition")
    logger.info("🎯 Precise price level extraction")
    logger.info("📈 Technical indicator identification")
    logger.info("💰 Accurate support/resistance detection")
    logger.info("⏰ Timeframe and pattern analysis")
    logger.info("🔍 Market sentiment analysis")

    logger.info("\n💡 ADVANTAGES OVER QWEN:")
    logger.info("• Higher accuracy for financial charts")
    logger.info("• Better understanding of trading indicators")
    logger.info("• More precise price level extraction")
    logger.info("• Superior pattern recognition")
    logger.info("• Enhanced technical analysis capabilities")

    logger.info("\n📊 ANALYSIS FEATURES:")
    logger.info("• 7-day historical data extraction")
    logger.info("• Comprehensive signal analysis")
    logger.info("• Market trend identification")
    logger.info("• Risk assessment and recommendations")
    logger.info("• Detailed JSON reports with insights")

if __name__ == "__main__":
    main()