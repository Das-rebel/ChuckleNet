#!/bin/bash

# Second Brain Design Tokens Deep Link Testing Script

echo "=== Second Brain Design Tokens Deep Link Test ==="
echo

# Test 1: Basic secondbrain://design/tokens
echo "Test 1: Testing secondbrain://design/tokens"
adb shell am start -W -a android.intent.action.VIEW -d "secondbrain://design/tokens" com.secondbrain.app/.MainActivity
echo "Result: $?"
echo

# Test 2: With additional parameters
echo "Test 2: Testing secondbrain://design/tokens?category=colors"
adb shell am start -W -a android.intent.action.VIEW -d "secondbrain://design/tokens?category=colors" app.secondbrain.v6/.MainActivity
echo "Result: $?"
echo

# Test 3: With multiple parameters
echo "Test 3: Testing secondbrain://design/tokens?category=typography&theme=dark"
adb shell am start -W -a android.intent.action.VIEW -d "secondbrain://design/tokens?category=typography&theme=dark" app.secondbrain.v6/.MainActivity
echo "Result: $?"
echo

# Test 4: Test all installed packages
echo "Test 4: Testing with different package names"
echo "Available Second Brain packages:"
adb shell pm list packages | grep -i "secondbrain\|brainspark"
echo

echo "Testing com.secondbrain.app:"
adb shell am start -W -a android.intent.action.VIEW -d "secondbrain://design/tokens" com.secondbrain.app/.MainActivity 2>/dev/null
echo "Result: $?"

echo "Testing com.secondbrain:"
adb shell am start -W -a android.intent.action.VIEW -d "secondbrain://design/tokens" com.secondbrain/.MainActivity 2>/dev/null
echo "Result: $?"

echo "=== Test Complete ==="