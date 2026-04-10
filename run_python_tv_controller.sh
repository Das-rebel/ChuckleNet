#!/bin/bash

echo "📱 Starting Android TV Bluetooth Controller (Python)..."
echo "🔵 Make sure your Android TV is in Bluetooth pairing mode"

# Check if PyObjC is installed
if ! python3 -c "import PyObjC" 2>/dev/null; then
    echo "❌ PyObjC not found. Installing..."
    pip3 install PyObjC
fi

# Run the Python app
echo "🚀 Launching Android TV Controller..."
python3 /Users/Subho/android_tv_bluetooth_controller.py

echo ""
echo "📖 If the app doesn't find your TV:"
echo "1. Make sure your TV is discoverable via Bluetooth"
echo "2. Check that your TV supports Bluetooth remote control"
echo "3. Try putting your TV in pairing mode"
echo "4. Move closer to improve Bluetooth signal"