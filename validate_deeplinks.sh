#!/bin/bash

# Deep Link Validation and Monitoring Script

echo "======================================="
echo "Deep Link Validation & Monitoring Tool"
echo "======================================="
echo

# Real-time monitoring function
monitor_deeplinks() {
    echo "📊 Starting real-time deep link monitoring..."
    echo "Press Ctrl+C to stop monitoring"
    echo

    # Clear logcat
    adb logcat -c

    # Start monitoring with enhanced filtering
    adb logcat -v time | while read line; do
        # Check for deep link related logs
        if echo "$line" | grep -E "(secondbrain|MainActivity|Intent|ACTION_VIEW|DeepLink)" >/dev/null; then
            timestamp=$(echo "$line" | awk '{print $1, $2}')
            message=$(echo "$line" | cut -d' ' -f3-)

            # Color coding based on log type
            if echo "$line" | grep -E "(ERROR|FATAL)" >/dev/null; then
                echo -e "🔴 [$timestamp] $message"
            elif echo "$line" | grep -E "(WARN)" >/dev/null; then
                echo -e "🟡 [$timestamp] $message"
            elif echo "$line" | grep -E "(secondbrain://)" >/dev/null; then
                echo -e "🟢 [$timestamp] 🔗 $message"
            else
                echo -e "ℹ️  [$timestamp] $message"
            fi
        fi
    done
}

# Validation function for specific URL
validate_url() {
    local url="$1"
    echo "🔍 Validating URL: $url"

    # Parse URL components
    if [[ "$url" =~ ^secondbrain:// ]]; then
        echo "✅ Valid scheme: secondbrain://"

        # Extract path
        path=$(echo "$url" | sed 's|secondbrain://[^/]*||')
        echo "📁 Path: $path"

        # Check for supported paths
        if [[ "$path" =~ ^/design/(tokens|qa) ]]; then
            echo "✅ Valid path: $path"
        else
            echo "❌ Invalid path: $path (should be /design/tokens or /design/qa)"
        fi

        # Extract query parameters
        if [[ "$url" =~ \? ]]; then
            query=$(echo "$url" | cut -d'?' -f2)
            echo "📋 Query parameters: $query"

            # Validate common parameters
            IFS='&' read -ra params <<< "$query"
            for param in "${params[@]}"; do
                IFS='=' read -ra kv <<< "$param"
                key="${kv[0]}"
                value="${kv[1]}"
                echo "  - $key: $value"

                # Validate parameter names
                case "$key" in
                    category|theme|testId|component|suite|priority|automated)
                        echo "    ✅ Valid parameter: $key"
                        ;;
                    *)
                        echo "    ⚠️  Unknown parameter: $key"
                        ;;
                esac
            done
        fi
    else
        echo "❌ Invalid scheme: Expected secondbrain://"
    fi
    echo
}

# Test URL with validation
test_with_validation() {
    local url="$1"
    local description="$2"

    echo "===================="
    echo "Test: $description"
    echo "===================="

    # Validate URL format
    validate_url "$url"

    # Test the deep link
    echo "🚀 Testing deep link..."

    # Start background monitoring
    adb logcat -c
    timeout 10 adb logcat | grep -E "(secondbrain|MainActivity|Intent)" > "/tmp/test_$(date +%s).log" &
    local monitor_pid=$!

    # Execute deep link
    adb shell am start -W -a android.intent.action.VIEW -d "$url" app.secondbrain.v6/.MainActivity
    local result=$?

    # Wait for logs
    sleep 3
    kill $monitor_pid 2>/dev/null

    if [ $result -eq 0 ]; then
        echo "✅ Deep link executed successfully"
    else
        echo "❌ Deep link execution failed (code: $result)"
    fi

    # Check app state
    echo "📱 Checking app state..."
    current_activity=$(adb shell dumpsys activity activities | grep -E "mResumedActivity" | head -1)
    if echo "$current_activity" | grep -q "secondbrain"; then
        echo "✅ Second Brain app is active"
    else
        echo "⚠️  App state unclear: $current_activity"
    fi

    echo
}

# Interactive testing mode
interactive_mode() {
    echo "🎮 Entering interactive testing mode..."
    echo

    while true; do
        echo "Available commands:"
        echo "1. Test design tokens (basic)"
        echo "2. Test design tokens (with parameters)"
        echo "3. Test QA (basic)"
        echo "4. Test QA (with parameters)"
        echo "5. Custom URL"
        echo "6. Monitor real-time"
        echo "7. Exit"
        echo

        read -p "Choose an option (1-7): " choice

        case $choice in
            1)
                test_with_validation "secondbrain://design/tokens" "Design Tokens - Basic"
                ;;
            2)
                test_with_validation "secondbrain://design/tokens?category=colors&theme=dark" "Design Tokens - With Parameters"
                ;;
            3)
                test_with_validation "secondbrain://design/qa" "QA - Basic"
                ;;
            4)
                test_with_validation "secondbrain://design/qa?testId=accessibility&priority=high" "QA - With Parameters"
                ;;
            5)
                read -p "Enter custom URL: " custom_url
                test_with_validation "$custom_url" "Custom URL Test"
                ;;
            6)
                monitor_deeplinks
                ;;
            7)
                echo "👋 Exiting interactive mode"
                break
                ;;
            *)
                echo "❌ Invalid choice. Please select 1-7."
                ;;
        esac

        echo
        read -p "Press Enter to continue..."
        echo
    done
}

# Command-line argument handling
if [ "$#" -eq 0 ]; then
    echo "Usage: $0 [monitor|test <url>|interactive]"
    echo
    echo "Examples:"
    echo "  $0 monitor                                    # Start real-time monitoring"
    echo "  $0 test 'secondbrain://design/tokens'        # Test specific URL"
    echo "  $0 interactive                                # Interactive testing mode"
    echo
    exit 1
fi

case "$1" in
    monitor)
        monitor_deeplinks
        ;;
    test)
        if [ -z "$2" ]; then
            echo "❌ Please provide a URL to test"
            exit 1
        fi
        test_with_validation "$2" "Command Line Test"
        ;;
    interactive)
        interactive_mode
        ;;
    *)
        echo "❌ Unknown command: $1"
        echo "Available commands: monitor, test, interactive"
        exit 1
        ;;
esac