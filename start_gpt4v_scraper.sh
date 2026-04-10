#!/bin/bash

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
    /Applications/Brave\ Browser.app/Contents/MacOS/Brave\ Browser \
        --remote-debugging-port=9222 \
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
