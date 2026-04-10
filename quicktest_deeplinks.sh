#!/bin/bash

# Quick Deep Link Test Commands

echo "🚀 Quick Deep Link Test Commands"
echo "================================"
echo

# Quick test functions
test_design_tokens() {
    echo "🎨 Testing Design Tokens..."
    adb shell am start -W -a android.intent.action.VIEW -d "secondbrain://design/tokens" com.secondbrain.app/.MainActivity
    echo "✅ Command executed"
}

test_design_tokens_colors() {
    echo "🎨 Testing Design Tokens (Colors)..."
    adb shell am start -W -a android.intent.action.VIEW -d "secondbrain://design/tokens?category=colors" com.secondbrain.app/.MainActivity
    echo "✅ Command executed"
}

test_qa() {
    echo "🧪 Testing QA..."
    adb shell am start -W -a android.intent.action.VIEW -d "secondbrain://design/qa" com.secondbrain.app/.MainActivity
    echo "✅ Command executed"
}

test_qa_accessibility() {
    echo "🧪 Testing QA (Accessibility)..."
    adb shell am start -W -a android.intent.action.VIEW -d "secondbrain://design/qa?testId=accessibility" com.secondbrain.app/.MainActivity
    echo "✅ Command executed"
}

# Check current app
check_app() {
    echo "📱 Current App Status:"
    adb shell dumpsys activity activities | grep -E "mResumedActivity|mFocusedActivity" | head -2
}

# Monitor logs briefly
quick_monitor() {
    echo "📝 Quick Log Monitor (10 seconds)..."
    adb logcat -c
    timeout 10 adb logcat | grep -E "(secondbrain|MainActivity|Intent|DeepLink)" || echo "No relevant logs found"
}

# Main menu
while true; do
    echo
    echo "Quick Test Options:"
    echo "1. Test Design Tokens (basic)"
    echo "2. Test Design Tokens (colors)"
    echo "3. Test QA (basic)"
    echo "4. Test QA (accessibility)"
    echo "5. Check current app"
    echo "6. Quick log monitor"
    echo "7. Exit"
    echo

    read -p "Choose option (1-7): " choice

    case $choice in
        1) test_design_tokens ;;
        2) test_design_tokens_colors ;;
        3) test_qa ;;
        4) test_qa_accessibility ;;
        5) check_app ;;
        6) quick_monitor ;;
        7) echo "👋 Goodbye!"; exit 0 ;;
        *) echo "❌ Invalid choice" ;;
    esac

    sleep 1
done