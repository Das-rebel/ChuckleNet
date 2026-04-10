#!/bin/bash

# Second Brain V6 Android App - Automated UI Screenshot Testing Suite
# This script captures screenshots of all main screens for UI validation and comparison

set -e

# Configuration
APP_PACKAGE="com.secondbrain.app"
SCREENSHOT_DIR="$(pwd)/second_brain_screenshots"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
TEST_SESSION_DIR="${SCREENSHOT_DIR}/test_session_${TIMESTAMP}"
DEVICE_ID=""
WAIT_TIME=3

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

wait_for_ui() {
    log_info "Waiting ${WAIT_TIME} seconds for UI to stabilize..."
    sleep $WAIT_TIME
}

# Check if device is connected
check_device() {
    log_info "Checking for connected devices..."

    DEVICES=$(adb devices | grep -v "List of devices" | grep "device$" | wc -l)

    if [ $DEVICES -eq 0 ]; then
        log_error "No Android devices connected. Please connect a device or start an emulator."
        exit 1
    elif [ $DEVICES -gt 1 ]; then
        log_warning "Multiple devices detected. Please specify device ID:"
        adb devices
        read -p "Enter device ID: " DEVICE_ID
        DEVICE_FLAG="-s $DEVICE_ID"
    else
        DEVICE_FLAG=""
        DEVICE_ID=$(adb devices | grep "device$" | cut -f1)
        log_success "Connected to device: $DEVICE_ID"
    fi
}

# Create screenshot directory
setup_directories() {
    log_info "Setting up screenshot directories..."
    mkdir -p "$TEST_SESSION_DIR"
    mkdir -p "$TEST_SESSION_DIR/portrait"
    mkdir -p "$TEST_SESSION_DIR/landscape"
    mkdir -p "$TEST_SESSION_DIR/comparisons"
    log_success "Directories created at: $TEST_SESSION_DIR"
}

# Get device info
get_device_info() {
    log_info "Gathering device information..."

    DEVICE_MODEL=$(adb $DEVICE_FLAG shell getprop ro.product.model)
    ANDROID_VERSION=$(adb $DEVICE_FLAG shell getprop ro.build.version.release)
    SCREEN_SIZE=$(adb $DEVICE_FLAG shell wm size | cut -d: -f2 | xargs)
    SCREEN_DENSITY=$(adb $DEVICE_FLAG shell wm density | cut -d: -f2 | xargs)

    cat > "$TEST_SESSION_DIR/device_info.txt" << EOF
Device Information
==================
Model: $DEVICE_MODEL
Android Version: $ANDROID_VERSION
Screen Size: $SCREEN_SIZE
Screen Density: $SCREEN_DENSITY
Package: $APP_PACKAGE
Test Timestamp: $TIMESTAMP
EOF

    log_success "Device info saved to device_info.txt"
}

# Take screenshot with metadata
take_screenshot() {
    local screen_name=$1
    local orientation=${2:-"portrait"}
    local description=${3:-""}

    local filename="${orientation}_${screen_name}_${TIMESTAMP}.png"
    local filepath="$TEST_SESSION_DIR/$orientation/$filename"

    log_info "Capturing screenshot: $screen_name ($orientation)"

    # Take screenshot
    adb $DEVICE_FLAG shell screencap -p > "$filepath"

    if [ -f "$filepath" ]; then
        log_success "Screenshot saved: $filename"

        # Create metadata file
        cat > "$TEST_SESSION_DIR/$orientation/${screen_name}_metadata.json" << EOF
{
    "screen_name": "$screen_name",
    "orientation": "$orientation",
    "description": "$description",
    "filename": "$filename",
    "timestamp": "$TIMESTAMP",
    "device_model": "$DEVICE_MODEL",
    "android_version": "$ANDROID_VERSION",
    "screen_size": "$SCREEN_SIZE",
    "app_package": "$APP_PACKAGE"
}
EOF
    else
        log_error "Failed to capture screenshot for $screen_name"
        return 1
    fi
}

# App interaction functions
launch_app() {
    log_info "Launching Second Brain app..."
    adb $DEVICE_FLAG shell monkey -p $APP_PACKAGE -c android.intent.category.LAUNCHER 1
    wait_for_ui
    log_success "App launched successfully"
}

force_stop_app() {
    log_info "Force stopping app..."
    adb $DEVICE_FLAG shell am force-stop $APP_PACKAGE
    sleep 2
    log_success "App stopped"
}

# Navigation functions
navigate_to_screen() {
    local screen=$1

    case $screen in
        "dashboard"|"home"|"knowledgehub")
            log_info "Navigating to Dashboard/Knowledge Hub..."
            # Tap on Knowledge Hub tab (bottom navigation)
            adb $DEVICE_FLAG shell input tap 100 700  # Adjust coordinates based on your UI
            ;;
        "search")
            log_info "Navigating to Search..."
            # Tap on Search tab
            adb $DEVICE_FLAG shell input tap 200 700
            ;;
        "twitter")
            log_info "Navigating to Twitter..."
            # Tap on Twitter tab
            adb $DEVICE_FLAG shell input tap 300 700
            ;;
        "profile"|"settings")
            log_info "Navigating to Profile/Settings..."
            # Tap on Profile tab
            adb $DEVICE_FLAG shell input tap 400 700
            ;;
        "collections")
            log_info "Navigating to Collections..."
            # This might require additional navigation from main screen
            navigate_to_screen "dashboard"
            wait_for_ui
            # Tap on collections button/menu item
            adb $DEVICE_FLAG shell input tap 360 200  # Adjust based on UI
            ;;
    esac

    wait_for_ui
}

# Deep link navigation
open_deep_link() {
    local deep_link=$1
    log_info "Opening deep link: $deep_link"
    adb $DEVICE_FLAG shell am start -W -a android.intent.action.VIEW -d "$deep_link" $APP_PACKAGE
    wait_for_ui
}

# Screen orientation functions
set_orientation() {
    local orientation=$1

    case $orientation in
        "portrait")
            log_info "Setting orientation to portrait..."
            adb $DEVICE_FLAG shell settings put system user_rotation 0
            adb $DEVICE_FLAG shell settings put system accelerometer_rotation 0
            ;;
        "landscape")
            log_info "Setting orientation to landscape..."
            adb $DEVICE_FLAG shell settings put system user_rotation 1
            adb $DEVICE_FLAG shell settings put system accelerometer_rotation 0
            ;;
    esac

    sleep 2  # Wait for orientation change
}

# Reset orientation to auto
reset_orientation() {
    log_info "Resetting orientation to auto-rotate..."
    adb $DEVICE_FLAG shell settings put system accelerometer_rotation 1
}

# Main screenshot capture functions
capture_main_screens_portrait() {
    log_info "=== Capturing Main Screens in Portrait ==="

    set_orientation "portrait"

    # Launch app fresh
    force_stop_app
    launch_app

    # 1. Dashboard/Knowledge Hub Screen
    navigate_to_screen "dashboard"
    take_screenshot "01_dashboard" "portrait" "Main dashboard/knowledge hub with bookmarks and collections"

    # 2. Search Screen
    navigate_to_screen "search"
    take_screenshot "02_search" "portrait" "Search interface for finding bookmarks and content"

    # 3. Twitter Screen
    navigate_to_screen "twitter"
    take_screenshot "03_twitter" "portrait" "Twitter integration screen"

    # 4. Profile/Settings Screen
    navigate_to_screen "profile"
    take_screenshot "04_profile" "portrait" "User profile and settings screen"

    # 5. Collections Screen (if accessible)
    navigate_to_screen "collections"
    take_screenshot "05_collections" "portrait" "Collections management screen"

    log_success "Portrait screenshots completed"
}

capture_main_screens_landscape() {
    log_info "=== Capturing Main Screens in Landscape ==="

    set_orientation "landscape"

    # Launch app fresh
    force_stop_app
    launch_app

    # Capture same screens in landscape
    navigate_to_screen "dashboard"
    take_screenshot "01_dashboard" "landscape" "Main dashboard in landscape orientation"

    navigate_to_screen "search"
    take_screenshot "02_search" "landscape" "Search screen in landscape orientation"

    navigate_to_screen "twitter"
    take_screenshot "03_twitter" "landscape" "Twitter screen in landscape orientation"

    navigate_to_screen "profile"
    take_screenshot "04_profile" "landscape" "Profile screen in landscape orientation"

    log_success "Landscape screenshots completed"
}

# Deep link testing
test_deep_links() {
    log_info "=== Testing Deep Link Navigation ==="

    set_orientation "portrait"

    # Test design tokens deep link
    open_deep_link "secondbrain://design-tokens"
    take_screenshot "06_design_tokens" "portrait" "Design tokens screen via deep link"

    # Test other deep links if available
    open_deep_link "secondbrain://collections"
    take_screenshot "07_collections_deeplink" "portrait" "Collections via deep link"

    log_success "Deep link testing completed"
}

# Navigation flow testing
test_navigation_flows() {
    log_info "=== Testing Navigation Flows ==="

    set_orientation "portrait"
    force_stop_app
    launch_app

    # Test bottom tab navigation
    log_info "Testing bottom tab navigation flow..."

    # Start from dashboard
    navigate_to_screen "dashboard"
    take_screenshot "nav_01_dashboard_start" "portrait" "Navigation test - Dashboard start"

    # Navigate through all tabs
    navigate_to_screen "search"
    take_screenshot "nav_02_search_tab" "portrait" "Navigation test - Search tab"

    navigate_to_screen "twitter"
    take_screenshot "nav_03_twitter_tab" "portrait" "Navigation test - Twitter tab"

    navigate_to_screen "profile"
    take_screenshot "nav_04_profile_tab" "portrait" "Navigation test - Profile tab"

    # Back to dashboard
    navigate_to_screen "dashboard"
    take_screenshot "nav_05_dashboard_return" "portrait" "Navigation test - Return to dashboard"

    log_success "Navigation flow testing completed"
}

# Interaction testing
test_interactions() {
    log_info "=== Testing UI Interactions ==="

    set_orientation "portrait"
    navigate_to_screen "dashboard"

    # Test scroll interactions
    log_info "Testing scroll interactions..."
    take_screenshot "interaction_01_before_scroll" "portrait" "Before scrolling"

    # Scroll down
    adb $DEVICE_FLAG shell input swipe 360 600 360 300 500
    wait_for_ui
    take_screenshot "interaction_02_after_scroll" "portrait" "After scrolling down"

    # Scroll back up
    adb $DEVICE_FLAG shell input swipe 360 300 360 600 500
    wait_for_ui
    take_screenshot "interaction_03_scroll_up" "portrait" "After scrolling up"

    # Test search functionality if available
    navigate_to_screen "search"
    # Tap on search input
    adb $DEVICE_FLAG shell input tap 360 200
    wait_for_ui
    take_screenshot "interaction_04_search_focus" "portrait" "Search input focused"

    log_success "Interaction testing completed"
}

# Generate comparison report
generate_comparison_report() {
    log_info "Generating comparison report..."

    cat > "$TEST_SESSION_DIR/test_report.html" << EOF
<!DOCTYPE html>
<html>
<head>
    <title>Second Brain V6 UI Test Report - $TIMESTAMP</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background-color: #f5f5f5; padding: 15px; border-radius: 5px; }
        .screen-section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
        .screenshot { max-width: 300px; margin: 10px; border: 1px solid #ccc; }
        .comparison-grid { display: flex; flex-wrap: wrap; gap: 20px; }
        .device-info { background-color: #e8f4f8; padding: 10px; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Second Brain V6 Android App UI Test Report</h1>
        <p>Test Session: $TIMESTAMP</p>
        <p>Device: $DEVICE_MODEL (Android $ANDROID_VERSION)</p>
    </div>

    <div class="device-info">
        <h3>Device Information</h3>
        <ul>
            <li>Model: $DEVICE_MODEL</li>
            <li>Android Version: $ANDROID_VERSION</li>
            <li>Screen Size: $SCREEN_SIZE</li>
            <li>Screen Density: $SCREEN_DENSITY</li>
            <li>App Package: $APP_PACKAGE</li>
        </ul>
    </div>

    <div class="screen-section">
        <h2>Portrait Screenshots</h2>
        <div class="comparison-grid">
EOF

    # Add portrait screenshots to report
    for img in "$TEST_SESSION_DIR/portrait"/*.png; do
        if [ -f "$img" ]; then
            basename_img=$(basename "$img")
            echo "            <div><img src='portrait/$basename_img' class='screenshot' alt='$basename_img'><br>$basename_img</div>" >> "$TEST_SESSION_DIR/test_report.html"
        fi
    done

    cat >> "$TEST_SESSION_DIR/test_report.html" << EOF
        </div>
    </div>

    <div class="screen-section">
        <h2>Landscape Screenshots</h2>
        <div class="comparison-grid">
EOF

    # Add landscape screenshots to report
    for img in "$TEST_SESSION_DIR/landscape"/*.png; do
        if [ -f "$img" ]; then
            basename_img=$(basename "$img")
            echo "            <div><img src='landscape/$basename_img' class='screenshot' alt='$basename_img'><br>$basename_img</div>" >> "$TEST_SESSION_DIR/test_report.html"
        fi
    done

    cat >> "$TEST_SESSION_DIR/test_report.html" << EOF
        </div>
    </div>

    <div class="screen-section">
        <h2>Test Summary</h2>
        <ul>
            <li>Total Screenshots: $(find "$TEST_SESSION_DIR" -name "*.png" | wc -l)</li>
            <li>Portrait Screenshots: $(find "$TEST_SESSION_DIR/portrait" -name "*.png" | wc -l)</li>
            <li>Landscape Screenshots: $(find "$TEST_SESSION_DIR/landscape" -name "*.png" | wc -l)</li>
            <li>Test Duration: Completed at $(date)</li>
        </ul>
    </div>
</body>
</html>
EOF

    log_success "Test report generated: test_report.html"
}

# Cleanup function
cleanup() {
    log_info "Cleaning up..."
    reset_orientation
    force_stop_app
    log_success "Cleanup completed"
}

# Main execution function
run_full_test_suite() {
    log_info "Starting Second Brain V6 UI Test Suite..."

    check_device
    setup_directories
    get_device_info

    # Run all test phases
    capture_main_screens_portrait
    capture_main_screens_landscape
    test_deep_links
    test_navigation_flows
    test_interactions

    generate_comparison_report
    cleanup

    log_success "=== UI Test Suite Completed ==="
    log_info "Results saved to: $TEST_SESSION_DIR"
    log_info "Open test_report.html in your browser to view results"
}

# Command line argument handling
case "${1:-full}" in
    "full")
        run_full_test_suite
        ;;
    "portrait")
        check_device
        setup_directories
        get_device_info
        capture_main_screens_portrait
        cleanup
        ;;
    "landscape")
        check_device
        setup_directories
        get_device_info
        capture_main_screens_landscape
        cleanup
        ;;
    "deeplinks")
        check_device
        setup_directories
        get_device_info
        test_deep_links
        cleanup
        ;;
    "navigation")
        check_device
        setup_directories
        get_device_info
        test_navigation_flows
        cleanup
        ;;
    "interactions")
        check_device
        setup_directories
        get_device_info
        test_interactions
        cleanup
        ;;
    "help"|"-h"|"--help")
        cat << EOF
Second Brain V6 Android App UI Testing Suite

Usage: $0 [command]

Commands:
    full         Run complete test suite (default)
    portrait     Capture main screens in portrait only
    landscape    Capture main screens in landscape only
    deeplinks    Test deep link navigation
    navigation   Test navigation flows
    interactions Test UI interactions
    help         Show this help message

Examples:
    $0              # Run full test suite
    $0 portrait     # Capture portrait screenshots only
    $0 navigation   # Test navigation flows only

Output:
    Screenshots and reports are saved to: ./second_brain_screenshots/test_session_[timestamp]/
EOF
        ;;
    *)
        log_error "Unknown command: $1"
        log_info "Use '$0 help' to see available commands"
        exit 1
        ;;
esac