#!/bin/bash

# Comprehensive Deep Link Debug Script

echo "=============================================="
echo "Second Brain Deep Link Debug & Validation Suite"
echo "=============================================="
echo

# Function to check device connectivity
check_device() {
    echo "📱 Checking device connectivity..."
    devices=$(adb devices | grep -v "List of devices" | grep "device" | wc -l)
    if [ $devices -eq 0 ]; then
        echo "❌ No devices connected!"
        echo "Please connect a device and enable USB debugging"
        exit 1
    fi
    echo "✅ Device connected ($devices device(s))"
    echo
}

# Function to validate package installation
validate_packages() {
    echo "📦 Validating Second Brain packages..."

    packages=$(adb shell pm list packages | grep -i "secondbrain\|brainspark")
    if [ -z "$packages" ]; then
        echo "❌ No Second Brain packages found!"
        echo "Please install the app first"
        exit 1
    fi

    echo "✅ Found packages:"
    echo "$packages"
    echo
}

# Function to check intent filters
check_intent_filters() {
    echo "🔍 Checking intent filters..."

    echo "Intent filters for app.secondbrain.v6:"
    adb shell dumpsys package app.secondbrain.v6 | grep -A 20 "Activity filter" | grep -E "(android.intent.action.VIEW|secondbrain)" || echo "No VIEW intent filters found"
    echo

    echo "Intent filters for com.secondbrain.app:"
    adb shell dumpsys package com.secondbrain.app | grep -A 20 "Activity filter" | grep -E "(android.intent.action.VIEW|secondbrain)" 2>/dev/null || echo "Package not found or no VIEW intent filters"
    echo
}

# Function to test basic connectivity
test_basic_intent() {
    echo "🧪 Testing basic intent handling..."

    # Test basic app launch
    echo "Testing basic app launch:"
    adb shell am start -W -n app.secondbrain.v6/.MainActivity
    sleep 2
    echo "✅ Basic launch completed"
    echo
}

# Function to capture detailed logs
capture_logs() {
    local test_name="$1"
    local url="$2"
    local duration="${3:-5}"

    echo "📝 Capturing logs for: $test_name"
    echo "URL: $url"

    # Clear logs
    adb logcat -c

    # Start logging in background
    adb logcat -v time | grep -E "(secondbrain|MainActivity|Intent|DeepLink|ReactNative)" > "/tmp/deeplink_${test_name}_$(date +%s).log" &
    local logcat_pid=$!

    # Trigger deep link
    echo "🚀 Triggering deep link..."
    adb shell am start -W -a android.intent.action.VIEW -d "$url" app.secondbrain.v6/.MainActivity

    # Wait and capture
    echo "⏳ Waiting ${duration} seconds for logs..."
    sleep $duration

    # Stop logging
    kill $logcat_pid 2>/dev/null

    echo "✅ Logs captured"
    echo
}

# Function to validate app state
validate_app_state() {
    echo "🔍 Validating current app state..."

    echo "Current activity:"
    current_activity=$(adb shell dumpsys activity activities | grep -E "mResumedActivity|mFocusedActivity")
    echo "$current_activity"
    echo

    echo "Recent tasks:"
    adb shell dumpsys activity recents | head -10
    echo

    echo "Memory usage:"
    adb shell dumpsys meminfo app.secondbrain.v6 | head -10 2>/dev/null || echo "Package not found in memory"
    echo
}

# Function to run comprehensive tests
run_comprehensive_tests() {
    echo "🚀 Running comprehensive deep link tests..."
    echo

    # Test cases
    declare -a test_cases=(
        "design_tokens_basic:secondbrain://design/tokens"
        "design_tokens_colors:secondbrain://design/tokens?category=colors"
        "design_tokens_typography:secondbrain://design/tokens?category=typography&theme=dark"
        "qa_basic:secondbrain://design/qa"
        "qa_accessibility:secondbrain://design/qa?testId=accessibility"
        "qa_component:secondbrain://design/qa?component=button&test=visual"
        "qa_regression:secondbrain://design/qa?suite=regression&priority=high&automated=true"
    )

    for test_case in "${test_cases[@]}"; do
        IFS=':' read -r name url <<< "$test_case"
        echo "===================="
        echo "Test: $name"
        echo "===================="
        capture_logs "$name" "$url"

        # Wait between tests
        sleep 2
    done
}

# Function to generate report
generate_report() {
    echo "📊 Generating test report..."

    report_file="/tmp/deeplink_test_report_$(date +%Y%m%d_%H%M%S).txt"

    {
        echo "Second Brain Deep Link Test Report"
        echo "Generated: $(date)"
        echo "========================================"
        echo

        echo "Device Information:"
        adb shell getprop ro.product.model
        adb shell getprop ro.build.version.release
        echo

        echo "Installed Packages:"
        adb shell pm list packages | grep -i "secondbrain\|brainspark"
        echo

        echo "Intent Filter Check:"
        adb shell dumpsys package app.secondbrain.v6 | grep -A 5 "secondbrain" || echo "No secondbrain scheme found"
        echo

        echo "Test Results:"
        echo "All logs are available in /tmp/deeplink_*.log"

    } > "$report_file"

    echo "✅ Report generated: $report_file"
    echo
}

# Main execution
main() {
    check_device
    validate_packages
    check_intent_filters
    test_basic_intent
    validate_app_state

    echo "🤔 Do you want to run comprehensive tests? (y/n)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        run_comprehensive_tests
    fi

    generate_report

    echo "🎉 Debug session completed!"
    echo "Check /tmp/deeplink_*.log for detailed logs"
}

# Run main function
main