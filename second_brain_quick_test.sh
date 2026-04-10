#!/bin/bash

# Quick Second Brain V6 Deep Link Test
# Simplified version for immediate testing

echo "🔗 Quick Deep Link Test for Second Brain V6"
echo "=========================================="

# Package name
PACKAGE_NAME="com.secondbrain.app"

# Function to test deep link quickly
quick_test() {
    local link=$1
    local name=$2

    echo "Testing: $link"

    # Clear logcat
    adb logcat -c

    # Start deep link
    adb shell am start -a android.intent.action.VIEW -d "$link"

    # Wait and capture
    sleep 3
    adb shell screencap -p /sdcard/test_$name.png
    adb pull /sdcard/test_$name.png ~/second_brain_quick_$name.png

    echo "Screenshot saved: ~/second_brain_quick_$name.png"
    echo ""
}

echo "📱 Checking device connection..."
adb devices

echo ""
echo "🔍 Checking app installation..."
if adb shell pm list packages | grep -q $PACKAGE_NAME; then
    echo "✅ Second Brain app found"
else
    echo "❌ App not found. Available apps:"
    adb shell pm list packages | grep -i "brain\|second"
    exit 1
fi

echo ""
echo "🚀 Testing deep links..."

# Test both deep links
quick_test "secondbrain://design/tokens" "tokens"
quick_test "secondbrain://design/qa" "qa"

echo "✅ Quick test complete!"
echo ""
echo "🐛 To monitor logs, run:"
echo "adb logcat | grep -i 'secondbrain\|deeplink\|intent'"