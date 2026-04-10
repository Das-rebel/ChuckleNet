#!/bin/bash
# Simplified Happy Claude-GLM Setup

echo "🚀 Simplified Happy Claude-GLM Setup"
echo "==================================="

DEVICE_ID="adb-10BEAG2THF003DD-Z0kION._adb-tls-connect._tcp"

# Setup port forwarding
echo "Setting up ADB connection..."
adb -s $DEVICE_ID forward tcp:8080 tcp:8080
adb -s $DEVICE_ID forward tcp:60150 tcp:60150

# Launch Happy app on device
echo "Launching Happy app..."
adb -s $DEVICE_ID shell am start -n com.ex3ndr.happy/.MainActivity

echo ""
echo "📋 ONE-STEP SETUP:"
echo "=================="
echo ""
echo "1. Open Happy mobile app on your device"
echo "2. Look for 'Computer Connection' or 'Link Device' option"
echo "3. Your computer should automatically appear"
echo "4. Tap to connect - no QR code needed!"
echo ""
echo "🔧 QUICK COMMANDS:"
echo "------------------"
echo "Start Happy: happy --settings ~/.happy/zai_settings.json"
echo "Status: happy daemon status"
echo "Stop: pkill -f happy"
echo ""
echo "📡 CONNECTION INFO:"
echo "- Device: $DEVICE_ID"
echo "- Port: 60150"
echo "- Model: Claude-GLM (glm-4.5)"
echo ""
echo "✅ Setup complete - just connect from mobile app!"