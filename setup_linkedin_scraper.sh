#!/bin/bash

echo "🚀 Setting up LinkedIn Scraper"
echo "================================"

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Install Playwright
echo ""
echo "📦 Installing Playwright..."
pip3 install playwright>=1.40.0

# Install Playwright browsers
echo ""
echo "🌐 Installing Playwright browsers..."
python3 -m playwright install chromium

# Install other dependencies
echo ""
echo "📚 Installing other dependencies..."
pip3 install -r requirements_linkedin_scraper.txt

echo ""
echo "✅ Setup complete!"
echo ""
echo "To run the scraper:"
echo "  python3 linkedin_post_scraper.py"
echo ""
echo "Make sure you have:"
echo "  - Stable internet connection"
echo "  - LinkedIn credentials ready"
echo "  - At least 30 minutes for full scraping"
