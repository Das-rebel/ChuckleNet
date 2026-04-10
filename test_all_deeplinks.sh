#!/bin/bash

# Comprehensive Second Brain Deep Link Testing Suite

echo "=========================================="
echo "Second Brain Deep Link Testing Suite"
echo "=========================================="
echo

# Function to test deep link with logging
test_deeplink() {
    local url="$1"
    local package="$2"
    local description="$3"

    echo "🔍 Test: $description"
    echo "📱 URL: $url"
    echo "📦 Package: $package"
    echo "⏰ Timestamp: $(date)"

    # Clear logcat
    adb logcat -c

    # Start activity with intent
    echo "🚀 Launching deep link..."
    adb shell am start -W -a android.intent.action.VIEW -d "$url" "$package" 2>&1
    local result=$?

    echo "📊 Result Code: $result"

    # Capture logcat for 3 seconds
    echo "📝 Capturing logs..."
    timeout 3 adb logcat | grep -E "(secondbrain|MainActivity|Intent|deep|link)" || true

    echo "✅ Test completed"
    echo "----------------------------------------"
    echo
}

# Get connected devices
echo "📱 Connected Devices:"
adb devices
echo

# List available packages
echo "📦 Available Second Brain Packages:"
adb shell pm list packages | grep -i "secondbrain\|brainspark" | sort
echo

# Main package to test
MAIN_PACKAGE="com.secondbrain.app/.MainActivity"

echo "🎯 Starting Deep Link Tests with $MAIN_PACKAGE"
echo

# Test Design Tokens Deep Links
echo "🎨 === DESIGN TOKENS TESTS ==="
test_deeplink "secondbrain://design/tokens" "$MAIN_PACKAGE" "Basic Design Tokens"
test_deeplink "secondbrain://design/tokens?category=colors" "$MAIN_PACKAGE" "Design Tokens - Colors"
test_deeplink "secondbrain://design/tokens?category=typography" "$MAIN_PACKAGE" "Design Tokens - Typography"
test_deeplink "secondbrain://design/tokens?category=spacing&theme=dark" "$MAIN_PACKAGE" "Design Tokens - Spacing (Dark)"

# Test QA Deep Links
echo "🧪 === QA TESTS ==="
test_deeplink "secondbrain://design/qa" "$MAIN_PACKAGE" "Basic QA"
test_deeplink "secondbrain://design/qa?testId=accessibility" "$MAIN_PACKAGE" "QA - Accessibility Test"
test_deeplink "secondbrain://design/qa?component=button" "$MAIN_PACKAGE" "QA - Button Component"
test_deeplink "secondbrain://design/qa?suite=regression&priority=high" "$MAIN_PACKAGE" "QA - High Priority Regression"

# Test other installed packages
echo "🔄 === TESTING OTHER PACKAGES ==="
OTHER_PACKAGES=("com.secondbrain.app/.MainActivity" "com.secondbrain/.MainActivity")

for pkg in "${OTHER_PACKAGES[@]}"; do
    echo "📦 Testing package: $pkg"
    test_deeplink "secondbrain://design/tokens" "$pkg" "Design Tokens - $pkg"
    test_deeplink "secondbrain://design/qa" "$pkg" "QA - $pkg"
done

# Validation commands
echo "🔍 === VALIDATION COMMANDS ==="
echo "Current activity:"
adb shell dumpsys activity activities | grep -E "mResumedActivity|mFocusedActivity" || true
echo

echo "Recent intents:"
adb shell dumpsys activity intents | head -20 || true
echo

echo "🎉 === ALL TESTS COMPLETED ==="
echo "📅 Completed at: $(date)"
echo "=========================================="