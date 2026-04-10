#!/bin/bash

# Second Brain QA Deep Link Testing Script

echo "=== Second Brain QA Deep Link Test ==="
echo

# Test 1: Basic secondbrain://design/qa
echo "Test 1: Testing secondbrain://design/qa"
adb shell am start -W -a android.intent.action.VIEW -d "secondbrain://design/qa" com.secondbrain.app/.MainActivity
echo "Result: $?"
echo

# Test 2: With test ID
echo "Test 2: Testing secondbrain://design/qa?testId=accessibility"
adb shell am start -W -a android.intent.action.VIEW -d "secondbrain://design/qa?testId=accessibility" app.secondbrain.v6/.MainActivity
echo "Result: $?"
echo

# Test 3: With component parameter
echo "Test 3: Testing secondbrain://design/qa?component=button&test=visual"
adb shell am start -W -a android.intent.action.VIEW -d "secondbrain://design/qa?component=button&test=visual" app.secondbrain.v6/.MainActivity
echo "Result: $?"
echo

# Test 4: With comprehensive parameters
echo "Test 4: Testing secondbrain://design/qa?suite=regression&priority=high&automated=true"
adb shell am start -W -a android.intent.action.VIEW -d "secondbrain://design/qa?suite=regression&priority=high&automated=true" app.secondbrain.v6/.MainActivity
echo "Result: $?"
echo

# Test 5: Test all installed packages
echo "Test 5: Testing with different package names"
echo "Available Second Brain packages:"
adb shell pm list packages | grep -i "secondbrain\|brainspark"
echo

echo "Testing com.secondbrain.app:"
adb shell am start -W -a android.intent.action.VIEW -d "secondbrain://design/qa" com.secondbrain.app/.MainActivity 2>/dev/null
echo "Result: $?"

echo "Testing com.secondbrain:"
adb shell am start -W -a android.intent.action.VIEW -d "secondbrain://design/qa" com.secondbrain/.MainActivity 2>/dev/null
echo "Result: $?"

echo "=== Test Complete ==="