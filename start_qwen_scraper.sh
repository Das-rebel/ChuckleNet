#!/bin/bash

# Brave Telegram Scraper with Qwen OCR Launcher
echo "🚀 Starting Brave Telegram Scraper with Qwen OCR..."
echo "=================================================="

# Check if API key is set
if [ -z "$QWEN_API_KEY" ]; then
    echo "❌ QWEN_API_KEY not set"
    echo "Please set your API key:"
    echo "export QWEN_API_KEY='your-qwen-api-key-here'"
    echo ""
    echo "Or create a .env file with your API key:"
    echo "echo 'QWEN_API_KEY=your-key-here' > .env"
    exit 1
fi

# Check if Python dependencies are available
python3 -c "import selenium, psutil, requests, PIL" 2>/dev/null
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
    /Applications/Brave\ Browser.app/Contents/MacOS/Brave\ Browser \
        --remote-debugging-port=9222 \
        --user-data-dir="$HOME/Library/Application Support/BraveSoftware/Brave-Browser" &
    echo "Waiting for Brave to start..."
    sleep 5
fi

echo "✅ All checks passed. Starting scraper..."
echo "📊 Monitoring will run for 60 minutes by default"
echo "🖼️  Images will be processed with Qwen OCR"
echo "📋 Results will be saved to JSON files"
echo ""
echo "Press Ctrl+C to stop monitoring"
echo "=================================================="

# Start the scraper
python3 brave_telegram_scraper_with_qwen_ocr.py