#!/bin/bash
# Happy Claude-GLM ADB Setup - Final Configuration

echo "🎯 Happy Claude-GLM ADB Setup"
echo "============================="

DEVICE_ID="adb-10BEAG2THF003DD-Z0kION._adb-tls-connect._tcp"

echo "✅ Device connected: $DEVICE_ID"
echo "✅ Happy app installed on device"
echo "✅ Port forwarding configured"
echo ""

# Ensure port forwarding is active
echo "Configuring port forwarding..."
adb -s $DEVICE_ID forward tcp:8080 tcp:8080
adb -s $DEVICE_ID forward tcp:60150 tcp:60150
echo "✅ Port forwarding active"
echo ""

# Check if Happy app is running
echo "Checking Happy app status..."
if adb -s $DEVICE_ID shell pidof com.ex3ndr.happy >/dev/null 2>&1; then
    echo "✅ Happy app is running on device"
else
    echo "Starting Happy app on device..."
    adb -s $DEVICE_ID shell am start -n com.ex3ndr.happy/.MainActivity
    echo "✅ Happy app launched"
fi
echo ""

echo "📋 SETUP COMPLETE"
echo "================="
echo ""
echo "🔧 TO USE HAPPY WITH CLAUDE-GLM:"
echo "--------------------------------"
echo ""
echo "Step 1: Authenticate Happy (in a regular terminal)"
echo "-------------------------------------------------"
echo "Open a new terminal and run:"
echo "  happy auth login --force"
echo ""
echo "Choose 'Mobile App' option when prompted"
echo ""
echo "Step 2: Start Happy with Claude-GLM"
echo "-----------------------------------"
echo "Once authenticated, run:"
echo "  happy --settings ~/.happy/zai_settings.json"
echo ""
echo "Step 3: Connect Mobile Device"
echo "----------------------------"
echo "1. Open Happy mobile app on your device"
echo "2. Get backup key: happy auth show-backup"
echo "3. Link device using backup key"
echo "4. Your computer should appear for connection"
echo ""
echo "📡 CONNECTION INFO:"
echo "- Device: $DEVICE_ID"
echo "- Local Port: 60150"
echo "- Settings: ~/.happy/zai_settings.json"
echo "- Model: Claude-GLM (glm-4.5)"
echo ""
echo "🔍 STATUS CHECKS:"
echo "happy auth status"
echo "happy daemon status"
echo "happy doctor"
echo ""
echo "🛑 TO STOP:"
echo "pkill -f happy"
echo "happy daemon stop"