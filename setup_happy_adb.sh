#!/bin/bash
# Happy Mobile Setup with ADB

echo "📱 Happy Mobile Setup via ADB"
echo "=============================="

DEVICE_ID="adb-10BEAG2THF003DD-Z0kION._adb-tls-connect._tcp"

echo "Device ID: $DEVICE_ID"
echo ""

# Check device connection
echo "Checking device connection..."
adb -s $DEVICE_ID get-state
echo ""

# Check Happy app status
echo "Checking Happy app status..."
adb -s $DEVICE_ID shell pm list packages | grep happy
echo ""

# Set up port forwarding
echo "Setting up port forwarding..."
adb -s $DEVICE_ID forward tcp:8080 tcp:8080
adb -s $DEVICE_ID forward tcp:60150 tcp:60150
echo ""

# Try to extract authentication data
echo "Attempting to extract authentication data..."
adb -s $DEVICE_ID shell am force-stop com.ex3ndr.happy

# Clear app data to start fresh
echo "Clearing Happy app data..."
adb -s $DEVICE_ID shell pm clear com.ex3ndr.happy
echo ""

# Launch Happy app
echo "Launching Happy app..."
adb -s $DEVICE_ID shell am start -n com.ex3ndr.happy/.MainActivity
echo ""

echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Use the Happy mobile app to authenticate"
echo "2. Once authenticated, run: happy --settings ~/.happy/zai_settings.json"
echo "3. Your device should appear in the mobile app for connection"
echo ""
echo "Port forwarding is active:"
echo "- Local port 8080 -> Device port 8080"
echo "- Local port 60150 -> Device port 60150"