#!/bin/bash

# Comprehensive Deep Link Testing Script for Second Brain Android App
# Tests all defined deep links and validates their behavior

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Deep links to test
DEEPLINKS=(
    "secondbrain://dashboard"
    "secondbrain://bookmarks"
    "secondbrain://collections"
    "secondbrain://search"
    "secondbrain://settings"
    "secondbrain://add?url=https://example.com"
    "secondbrain://analytics"
    "secondbrain://ai-assistant"
)

# App package names to try
PACKAGES=(
    "com.secondbrain.app"
    "com.secondbrain.app.debug"
    "com.secondbrain"
    "com.brainspark.app"
    "com.brainspark.platform.debug"
)

# Test results
RESULTS=()

echo -e "${BLUE}=== SECOND BRAIN DEEP LINK TESTING ===${NC}"
echo

# Function to test a deep link
test_deeplink() {
    local deeplink=$1
    local package=$2
    local result

    echo -e "${YELLOW}Testing: $deeplink with package $package${NC}"

    # Clear logcat
    adb logcat -c

    # Test the deep link
    result=$(adb shell am start -W -a android.intent.action.VIEW -d "$deeplink" "$package" 2>&1)

    # Check result
    if echo "$result" | grep -q "Activity not started"; then
        echo -e "${RED}✗ FAILED: Activity not started${NC}"
        RESULTS+=("$deeplink|$package|FAILED|Activity not started")
        return 1
    elif echo "$result" | grep -q "Status: ok"; then
        echo -e "${GREEN}✓ SUCCESS: Deep link handled${NC}"
        RESULTS+=("$deeplink|$package|SUCCESS|Deep link handled")
        return 0
    else
        echo -e "${YELLOW}? UNKNOWN: $result${NC}"
        RESULTS+=("$deeplink|$package|UNKNOWN|$result")
        return 2
    fi
}

# Function to check logcat for errors
check_logcat_errors() {
    local deeplink=$1
    echo -e "${YELLOW}Checking logcat for errors...${NC}"

    # Check for crashes or errors
    errors=$(adb logcat -d | grep -i "error\|crash\|exception" | tail -10)

    if [ -n "$errors" ]; then
        echo -e "${RED}Errors found in logcat:${NC}"
        echo "$errors"
        return 1
    else
        echo -e "${GREEN}No errors found in logcat${NC}"
        return 0
    fi
}

# Main testing loop
echo "Testing deep links..."
echo

for package in "${PACKAGES[@]}"; do
    echo -e "${BLUE}Testing package: $package${NC}"
    echo "----------------------------------------"

    # First, try to start the app directly to see if it's installed
    direct_start=$(adb shell am start -n "$package/.MainActivity" 2>&1)
    if echo "$direct_start" | grep -q "does not exist"; then
        echo -e "${RED}Package $package not found or app not installed${NC}"
        continue
    fi

    # Test each deep link
    for deeplink in "${DEEPLINKS[@]}"; do
        test_deeplink "$deeplink" "$package"
        check_logcat_errors "$deeplink"
        echo

        # Small delay between tests
        sleep 2
    done
done

# Generate report
echo -e "${BLUE}=== TEST RESULTS SUMMARY ===${NC}"
echo

echo -e "${BLUE}Detailed Results:${NC}"
echo "----------------------------------------"
for result in "${RESULTS[@]}"; do
    IFS='|' read -r deeplink package status message <<< "$result"
    if [ "$status" = "SUCCESS" ]; then
        echo -e "${GREEN}✓ $deeplink ($package) - $message${NC}"
    elif [ "$status" = "FAILED" ]; then
        echo -e "${RED}✗ $deeplink ($package) - $message${NC}"
    else
        echo -e "${YELLOW}? $deeplink ($package) - $message${NC}"
    fi
done

echo
echo -e "${BLUE}Recommendations:${NC}"
echo "----------------------------------------"

# Count successes
success_count=$(echo "${RESULTS[@]}" | grep -o "SUCCESS" | wc -l)
total_count=${#RESULTS[@]}

if [ $success_count -eq 0 ]; then
    echo -e "${RED}• No deep links are working. Possible issues:${NC}"
    echo "  - Deep links not properly configured in AndroidManifest.xml"
    echo "  - App not built with deep link support"
    echo "  - Wrong package name"
    echo "  - Intent filters not properly set up"
    echo "  - Deep link handling code not implemented"

    echo -e "${YELLOW}• Recommendations:${NC}"
    echo "  - Check AndroidManifest.xml intent filter configuration"
    echo "  - Verify package name is correct"
    echo "  - Ensure deep link handling is implemented in the app"
    echo "  - Test with different URL schemes (exp+second-brain, etc.)"
elif [ $success_count -lt $total_count ]; then
    echo -e "${YELLOW}• Some deep links are working. Review configuration for failed ones.${NC}"
    echo "  - Check if all deep link routes are properly handled"
    echo "  - Verify parameter parsing for dynamic deep links"
    echo "  - Test fallback behavior"
else
    echo -e "${GREEN}• All deep links are working properly!${NC}"
fi

echo
echo -e "${BLUE}Next Steps:${NC}"
echo "----------------------------------------"
echo "1. Review AndroidManifest.xml configuration"
echo "2. Check deep link handling implementation in app code"
echo "3. Verify all routes are properly mapped"
echo "4. Test parameter handling for dynamic deep links"
echo "5. Implement proper error handling and fallback behavior"

echo
echo -e "${BLUE}=== TEST COMPLETE ===${NC}"