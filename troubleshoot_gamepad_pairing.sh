#!/bin/bash

echo "🔧 GAMEPAD PAIRING TROUBLESHOOTING"
echo "===================================="
echo ""

# Check Bluetooth status
echo "1. Checking Bluetooth status..."
if system_profiler SPBluetoothDataType | grep -q "State: On"; then
    echo "   ✅ Bluetooth is ON"
else
    echo "   ❌ Bluetooth is OFF - Turn it on in System Settings"
    exit 1
fi

echo ""
echo "2. Checking for gamepad devices..."
GAMEPAD_FOUND=$(system_profiler SPBluetoothDataType | grep -i "gamepad\|controller" | head -5)
if [ -z "$GAMEPAD_FOUND" ]; then
    echo "   ⚠️  No gamepad found in Bluetooth devices"
    echo ""
    echo "   Possible issues:"
    echo "   - Gamepad might not be in pairing mode"
    echo "   - Gamepad might use a different name"
    echo "   - Bluetooth might need a reset"
else
    echo "   Found: $GAMEPAD_FOUND"
fi

echo ""
echo "3. Checking all discoverable devices..."
echo "   Look in System Settings > Bluetooth for any new/unpaired devices"
echo "   The gamepad might appear with a different name or under 'Other Devices'"

echo ""
echo "4. Troubleshooting steps:"
echo ""
echo "   A. Make sure gamepad is REALLY in pairing mode:"
echo "      - LED should be blinking rapidly"
echo "      - Some gamepads need to be held in pairing mode longer"
echo "      - Try holding Power + another button for 10+ seconds"
echo ""
echo "   B. Reset Bluetooth (if needed):"
echo "      - Hold Shift + Option"
echo "      - Click Bluetooth icon in menu bar"
echo "      - Select 'Debug' > 'Reset the Bluetooth module'"
echo "      - Wait 10-15 seconds"
echo ""
echo "   C. Check if gamepad has a mode switch:"
echo "      - Look for X/D/S/M mode switch on gamepad"
echo "      - Try XInput mode (X) for best Mac compatibility"
echo "      - Some gamepads need to be in specific mode for pairing"
echo ""
echo "   D. Try USB connection first:"
echo "      - Connect gamepad via USB cable"
echo "      - Pair it while connected via USB"
echo "      - Then try Bluetooth"
echo ""
echo "   E. Check gamepad manual:"
echo "      - Look for specific pairing instructions"
echo "      - Some gamepads have unique pairing button combinations"
echo ""
echo "5. After putting gamepad in pairing mode, wait 30 seconds"
echo "   then check System Settings > Bluetooth again"
echo ""
echo "6. If you see it in System Settings but can't pair:"
echo "   - Click on it to try pairing"
echo "   - If it fails, try forgetting and re-pairing"
echo "   - Check if it requires a PIN (usually 0000 or 1234)"
echo ""
echo "Press Enter when you've tried these steps..."
read -p ""

echo ""
echo "Checking again..."
python3 check_fix_progress.py