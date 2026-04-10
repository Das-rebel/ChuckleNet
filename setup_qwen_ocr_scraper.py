#!/usr/bin/env python3
"""
Setup Script for Brave Browser Telegram Scraper with Qwen OCR

This script helps verify and configure the enhanced scraper with Qwen OCR capabilities.
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_qwen_api_key():
    """Check if Qwen API key is configured"""
    logger.info("🔑 Checking Qwen API key configuration...")

    api_key = os.getenv('QWEN_API_KEY')
    if api_key:
        logger.info("✅ QWEN_API_KEY environment variable is set")
        logger.info(f"   API Key: {api_key[:10]}...{api_key[-4:]}")
        return True
    else:
        logger.error("❌ QWEN_API_KEY environment variable not set")
        logger.info("Please set your Qwen API key:")
        logger.info("export QWEN_API_KEY='your-qwen-api-key-here'")
        logger.info("")
        logger.info("You can get Qwen API keys from:")
        logger.info("- Alibaba Cloud (Dashscope)")
        logger.info("- OpenAI-compatible endpoints that host Qwen models")
        logger.info("- ModelScope")
        return False

def create_env_file():
    """Create .env file for API key configuration"""
    env_file = ".env"

    if os.path.exists(env_file):
        logger.info("⚠️  .env file already exists")
        return False

    logger.info("📝 Creating .env file for API key configuration...")

    env_content = """# Qwen OCR API Configuration
# Get your API key from Alibaba Cloud, OpenAI-compatible endpoints, or ModelScope

# Option 1: Direct API key
QWEN_API_KEY=your-qwen-api-key-here

# Option 2: If using custom endpoint
# QWEN_API_KEY=your-api-key
# QWEN_BASE_URL=https://your-custom-endpoint.com/v1

# Option 3: For Alibaba Cloud Dashscope
# DASHSCOPE_API_KEY=your-dashscope-api-key
"""

    try:
        with open(env_file, 'w') as f:
            f.write(env_content)

        logger.info(f"✅ Created {env_file}")
        logger.info("Please edit the file and add your Qwen API key")
        logger.info("Then run: source .env")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create .env file: {e}")
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

def test_qwen_connection(api_key: str):
    """Test connection to Qwen OCR API"""
    logger.info("🧪 Testing Qwen OCR connection...")

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
            "model": "qwen-vl-plus",
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
                                "url": f"data:image/gif;base64,{test_image_data}"
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
            timeout=10
        )

        if response.status_code == 200:
            logger.info("✅ Qwen OCR API connection successful")
            return True
        else:
            logger.error(f"❌ Qwen API error: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False

    except Exception as e:
        logger.error(f"❌ Connection test failed: {e}")
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
    """Create a launch script"""
    logger.info("🚀 Creating launch script...")

    script_content = """#!/bin/bash

# Brave Telegram Scraper with Qwen OCR Launcher
echo "🚀 Starting Brave Telegram Scraper with Qwen OCR..."
echo "=================================================="

# Check if API key is set
if [ -z "$QWEN_API_KEY" ]; then
    echo "❌ QWEN_API_KEY not set"
    echo "Please set your API key:"
    echo "export QWEN_API_KEY='your-qwen-api-key-here'"
    exit 1
fi

# Start the scraper
python3 brave_telegram_scraper_with_qwen_ocr.py
"""

    script_path = "start_qwen_scraper.sh"
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
    logger.info("🚀 QWEN OCR ENHANCED TELEGRAM SCRAPER SETUP")
    logger.info("=" * 60)

    # Check API key
    if not check_qwen_api_key():
        create_env_file()
        logger.info("\n⚠️  Please set your Qwen API key before running the scraper")
        logger.info("Edit the .env file or set the environment variable")
        return

    api_key = os.getenv('QWEN_API_KEY')

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

    # Test Qwen connection
    logger.info("\n🧪 Testing Qwen OCR API connection...")
    qwen_ok = test_qwen_connection(api_key)

    # Create directories
    create_directories()

    # Create launch script
    create_launch_script()

    # Final summary
    logger.info("\n" + "=" * 60)
    logger.info("✅ SETUP COMPLETE!")
    logger.info("=" * 60)
    logger.info("\n📋 SETUP SUMMARY:")
    logger.info(f"   Qwen API Key: ✅")
    logger.info(f"   Dependencies: ✅")
    logger.info(f"   Brave Browser: ✅")
    logger.info(f"   Directories: ✅")
    logger.info(f"   Launch Script: ✅")
    logger.info(f"   API Connection: {'✅' if qwen_ok else '⚠️  (Check API key/endpoint)'}")

    logger.info("\n🚀 NEXT STEPS:")
    logger.info("1. Open Brave Browser")
    logger.info("2. Go to https://web.telegram.org/k/")
    logger.info("3. Log in to your Telegram account")
    logger.info("4. Navigate to your trading channel")
    logger.info("5. Run: ./start_qwen_scraper.sh")
    logger.info("   OR: python3 brave_telegram_scraper_with_qwen_ocr.py")

    logger.info("\n🆕 NEW OCR FEATURES:")
    logger.info("🖼️  Automatic image downloading from Telegram")
    logger.info("🔍 Qwen OCR analysis of trading screenshots")
    logger.info("📊 Extraction of price levels, indicators, patterns")
    logger.info("🎯 Structured trading signal generation from images")
    logger.info("📈 Support/resistance level detection")
    logger.info("⏰ Timeframe analysis")

    logger.info("\n💡 TIPS:")
    logger.info("- The scraper now processes both text AND images")
    logger.info("- Images are saved to 'telegram_images/' folder")
    logger.info("- Processed images move to 'processed_images/'")
    logger.info("- All signals saved to JSON files with timestamps")
    logger.info("- Check the console for real-time signal detection")

if __name__ == "__main__":
    main()