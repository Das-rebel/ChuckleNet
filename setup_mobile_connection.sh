#!/bin/bash
# Mobile Connection Setup Script for Happy with Claude-GLM

echo "📱 Happy Mobile Connection Setup"
echo "=================================="

# Check if we have the backup key
if [ -f ~/.happy/backup_key.txt ]; then
    echo "Found backup key:"
    cat ~/.happy/backup_key.txt
    echo ""
fi

echo "Step 1: Authentication Setup"
echo "---------------------------"
echo "You need to authenticate Happy first."
echo ""
echo "In a terminal that supports interactive mode, run:"
echo "  happy auth login --force"
echo ""
echo "Choose 'Mobile App' option and follow the prompts"
echo ""

echo "Step 2: Start Happy with Claude-GLM"
echo "-----------------------------------"
echo "Once authenticated, start Happy with:"
echo "  happy --settings ~/.happy/zai_settings.json"
echo ""

echo "Step 3: Connect Mobile Device"
echo "----------------------------"
echo "1. Open Happy mobile app"
echo "2. Choose 'Link Device' or 'Restore from Backup'"
echo "3. Enter the backup key shown above"
echo "4. Your computer should appear in the device list"
echo ""

echo "Current Status:"
happy auth status
echo ""

echo "Backup Key (if available):"
happy auth show-backup 2>/dev/null || echo "Not available - please authenticate first"

echo ""
echo "If you're having trouble with interactive authentication,"
echo "try running this script in a regular terminal window."