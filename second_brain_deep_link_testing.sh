#!/bin/bash

# Second Brain V6 Deep Link Testing Suite
# Tests deep links, app launch, navigation, and validates AndroidManifest intent filters

echo "=== Second Brain V6 Deep Link Testing Suite ==="
echo "Testing deep links: secondbrain://design/tokens and secondbrain://design/qa"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Package name (update if different)
PACKAGE_NAME="com.secondbrain.app"
ACTIVITY_NAME=".MainActivity"

# Function to capture screenshot
capture_screenshot() {
    local filename=$1
    local description=$2
    echo -e "${BLUE}📸 Capturing screenshot: $description${NC}"
    adb shell screencap -p /sdcard/screenshot_$filename.png
    adb pull /sdcard/screenshot_$filename.png ~/second_brain_$filename.png
    echo -e "${GREEN}✅ Screenshot saved: ~/second_brain_$filename.png${NC}"
}

# Function to check if app is installed
check_app_installed() {
    echo -e "${BLUE}🔍 Checking if Second Brain V6 is installed...${NC}"
    if adb shell pm list packages | grep -q $PACKAGE_NAME; then
        echo -e "${GREEN}✅ Second Brain V6 app found${NC}"
        return 0
    else
        echo -e "${RED}❌ Second Brain V6 app not found${NC}"
        echo "Available packages with 'second' or 'brain':"
        adb shell pm list packages | grep -i "second\|brain"
        return 1
    fi
}

# Function to get app info
get_app_info() {
    echo -e "${BLUE}📱 Getting app information...${NC}"
    adb shell dumpsys package $PACKAGE_NAME | head -20
    echo ""
    echo -e "${BLUE}🎯 Intent filters:${NC}"
    adb shell dumpsys package $PACKAGE_NAME | grep -A 10 -B 2 "android.intent.action.VIEW"
}

# Function to clear app data (optional)
clear_app_data() {
    echo -e "${YELLOW}🧹 Clearing app data for fresh test...${NC}"
    adb shell pm clear $PACKAGE_NAME
    sleep 2
}

# Function to force stop app
force_stop_app() {
    echo -e "${YELLOW}🛑 Force stopping app...${NC}"
    adb shell am force-stop $PACKAGE_NAME
    sleep 1
}

# Function to launch app normally
launch_app_normal() {
    echo -e "${BLUE}🚀 Launching Second Brain V6 normally...${NC}"
    adb shell monkey -p $PACKAGE_NAME -c android.intent.category.LAUNCHER 1
    sleep 3
    capture_screenshot "normal_launch" "Normal app launch"
}

# Function to test deep link
test_deep_link() {
    local deep_link=$1
    local test_name=$2

    echo -e "${BLUE}🔗 Testing deep link: $deep_link${NC}"

    # Method 1: Using am start with VIEW intent
    echo "Method 1: Using VIEW intent"
    adb shell am start -a android.intent.action.VIEW -d "$deep_link"
    sleep 3
    capture_screenshot "deeplink_${test_name}_method1" "Deep link $test_name - Method 1"

    # Wait a bit
    sleep 2

    # Method 2: Using specific component
    echo "Method 2: Using specific component"
    adb shell am start -n $PACKAGE_NAME/$ACTIVITY_NAME -a android.intent.action.VIEW -d "$deep_link"
    sleep 3
    capture_screenshot "deeplink_${test_name}_method2" "Deep link $test_name - Method 2"
}

# Function to test navigation flow
test_navigation_flow() {
    echo -e "${BLUE}🧭 Testing navigation flow...${NC}"

    # Launch app first
    launch_app_normal

    # Navigate through different screens (simulate taps)
    echo "Testing navigation to different sections..."

    # Tap on different areas to test navigation
    adb shell input tap 200 400  # Example coordinates
    sleep 2
    capture_screenshot "navigation_1" "Navigation test 1"

    adb shell input tap 200 500
    sleep 2
    capture_screenshot "navigation_2" "Navigation test 2"

    # Test back navigation
    adb shell input keyevent KEYCODE_BACK
    sleep 2
    capture_screenshot "navigation_back" "Back navigation test"
}

# Function to check logcat for deep link activity
monitor_logcat() {
    echo -e "${BLUE}📝 Starting logcat monitoring (will run for 30 seconds)...${NC}"
    echo "Look for deep link related logs..."

    # Clear logcat first
    adb logcat -c

    # Monitor logcat for 30 seconds
    timeout 30 adb logcat | grep -i "secondbrain\|deeplink\|intent\|MainActivity" &
    LOGCAT_PID=$!

    return $LOGCAT_PID
}

# Function to validate intent filters in AndroidManifest
validate_intent_filters() {
    echo -e "${BLUE}🔍 Validating AndroidManifest intent filters...${NC}"

    # Get the APK path
    APK_PATH=$(adb shell pm path $PACKAGE_NAME | cut -d: -f2)
    echo "APK Path: $APK_PATH"

    # Pull APK for analysis
    adb pull $APK_PATH ~/temp_secondbrain.apk

    # Use aapt to dump AndroidManifest (if available)
    echo "Checking for aapt tool..."
    if command -v aapt &> /dev/null; then
        echo "Using aapt to analyze AndroidManifest:"
        aapt dump xmltree ~/temp_secondbrain.apk AndroidManifest.xml | grep -A 20 -B 5 "secondbrain"
    else
        echo "aapt not found. Using dumpsys instead:"
        adb shell dumpsys package $PACKAGE_NAME | grep -A 15 -B 5 "android.intent.action.VIEW"
    fi

    # Clean up
    rm -f ~/temp_secondbrain.apk
}

# Function to run comprehensive tests
run_all_tests() {
    echo -e "${YELLOW}🏁 Running comprehensive deep link tests...${NC}"
    echo ""

    # Start logcat monitoring in background
    monitor_logcat
    LOGCAT_PID=$!

    # Test 1: Check if app is installed
    if ! check_app_installed; then
        echo -e "${RED}❌ Cannot proceed without app installed${NC}"
        exit 1
    fi

    # Test 2: Get app info and intent filters
    get_app_info
    echo ""

    # Test 3: Validate AndroidManifest
    validate_intent_filters
    echo ""

    # Test 4: Clear app data for fresh test
    clear_app_data

    # Test 5: Test normal app launch
    launch_app_normal
    sleep 2

    # Test 6: Test first deep link - design tokens
    force_stop_app
    test_deep_link "secondbrain://design/tokens" "tokens"
    sleep 3

    # Test 7: Test second deep link - design QA
    force_stop_app
    test_deep_link "secondbrain://design/qa" "qa"
    sleep 3

    # Test 8: Test navigation flow
    test_navigation_flow

    # Test 9: Test deep links when app is already running
    echo -e "${BLUE}🔄 Testing deep links with app already running...${NC}"
    launch_app_normal
    sleep 2
    test_deep_link "secondbrain://design/tokens" "tokens_running"
    sleep 3
    test_deep_link "secondbrain://design/qa" "qa_running"

    # Stop logcat monitoring
    kill $LOGCAT_PID 2>/dev/null

    echo ""
    echo -e "${GREEN}✅ All tests completed!${NC}"
    echo -e "${BLUE}📁 Screenshots saved to: ~/second_brain_*.png${NC}"
}

# Function to show debugging commands
show_debugging_commands() {
    cat << 'EOF'

=== DEBUGGING COMMANDS ===

1. Check installed packages:
   adb shell pm list packages | grep -i brain

2. Get detailed package info:
   adb shell dumpsys package com.secondbrain.app

3. Check intent filters specifically:
   adb shell dumpsys package com.secondbrain.app | grep -A 10 "android.intent.action.VIEW"

4. Monitor logcat for deep link activity:
   adb logcat | grep -i "secondbrain\|deeplink\|intent"

5. Test deep link manually:
   adb shell am start -a android.intent.action.VIEW -d "secondbrain://design/tokens"

6. Check current activity:
   adb shell dumpsys activity activities | grep mResumedActivity

7. Force stop app:
   adb shell am force-stop com.secondbrain.app

8. Clear app data:
   adb shell pm clear com.secondbrain.app

9. Get app version info:
   adb shell dumpsys package com.secondbrain.app | grep versionName

10. Check if app can handle custom schemes:
    adb shell pm query-intent-activities -a android.intent.action.VIEW -d "secondbrain://test"

11. Test with browser fallback:
    adb shell am start -a android.intent.action.VIEW -d "https://secondbrain.app/design/tokens"

12. Capture current screen:
    adb shell screencap -p /sdcard/test.png && adb pull /sdcard/test.png

EOF
}

# Main execution
case "${1:-run}" in
    "run")
        run_all_tests
        ;;
    "debug")
        show_debugging_commands
        ;;
    "check")
        check_app_installed
        get_app_info
        ;;
    "tokens")
        test_deep_link "secondbrain://design/tokens" "tokens"
        ;;
    "qa")
        test_deep_link "secondbrain://design/qa" "qa"
        ;;
    "launch")
        launch_app_normal
        ;;
    "clear")
        clear_app_data
        ;;
    "manifest")
        validate_intent_filters
        ;;
    "logcat")
        echo "Monitoring logcat for deep link activity (Ctrl+C to stop)..."
        adb logcat | grep -i "secondbrain\|deeplink\|intent\|MainActivity"
        ;;
    *)
        echo "Usage: $0 [run|debug|check|tokens|qa|launch|clear|manifest|logcat]"
        echo ""
        echo "Commands:"
        echo "  run      - Run all tests (default)"
        echo "  debug    - Show debugging commands"
        echo "  check    - Check app installation and info"
        echo "  tokens   - Test secondbrain://design/tokens deep link"
        echo "  qa       - Test secondbrain://design/qa deep link"
        echo "  launch   - Launch app normally"
        echo "  clear    - Clear app data"
        echo "  manifest - Validate AndroidManifest intent filters"
        echo "  logcat   - Monitor logcat for deep link activity"
        ;;
esac