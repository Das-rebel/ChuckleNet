#!/bin/bash
# Quick script to help connect gamepad on macOS

echo "============================================================"
echo "🎮 GAMEPAD CONNECTION HELPER"
echo "============================================================"
echo ""

# Check if gamepad is already connected
echo "1️⃣ Checking current Bluetooth status..."
if system_profiler SPBluetoothDataType | grep -q "Gamepad-igs.*Connected: Yes"; then
    echo "   ✅ Gamepad-igs is already connected!"
    
    # Check device type
    DEVICE_TYPE=$(system_profiler SPBluetoothDataType | grep -A 10 "Gamepad-igs" | grep "Minor Type:" | awk -F': ' '{print $2}')
    
    if echo "$DEVICE_TYPE" | grep -q "Game Controller"; then
        echo "   ✅ Recognized as: $DEVICE_TYPE (CORRECT!)"
        echo ""
        echo "🎉 Your gamepad is properly configured!"
        echo ""
        echo "Test it with:"
        echo "   python3 gamepad_config_tool.py"
        exit 0
    else
        echo "   ❌ Recognized as: $DEVICE_TYPE (INCORRECT)"
        echo ""
        echo "⚠️  Gamepad is connected but misrecognized."
        echo ""
        echo "📋 Next steps:"
        echo "   1. Open System Settings > Bluetooth"
        echo "   2. Disconnect Gamepad-igs (click 'X' or 'Disconnect')"
        echo "   3. Forget the device (remove it)"
        echo "   4. Put gamepad in pairing mode (Power + Home/Share)"
        echo "   5. Make sure it's in XInput mode (X) if available"
        echo "   6. Re-pair in System Settings > Bluetooth"
        echo ""
        echo "Or use the workaround:"
        echo "   python3 gamepad_input_mapper_advanced.py"
        exit 1
    fi
else
    echo "   ❌ Gamepad-igs is NOT connected"
    echo ""
fi

echo ""
echo "2️⃣ Device found in Bluetooth list:"
system_profiler SPBluetoothDataType | grep -A 5 "Gamepad-igs" | head -10

echo ""
echo "============================================================"
echo "📋 CONNECTION INSTRUCTIONS"
echo "============================================================"
echo ""
echo "1. Put your gamepad in pairing mode:"
echo "   - Hold Power + Home/Share buttons for 3-5 seconds"
echo "   - LED should blink rapidly"
echo ""
echo "2. Check gamepad mode (if available):"
echo "   - Look for X/D/S/M switch"
echo "   - Set to X (XInput) mode"
echo ""
echo "3. Open System Settings > Bluetooth"
echo ""
echo "4. Wait for 'Gamepad-igs' to appear"
echo ""
echo "5. Click 'Connect' next to it"
echo ""
echo "6. After connecting, run:"
echo "   python3 gamepad_config_tool.py"
echo ""
echo "============================================================"
echo ""

# Offer to open Bluetooth settings
read -p "Open System Settings > Bluetooth now? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    open "x-apple.systempreferences:com.apple.preference.Bluetooth"
    echo "✅ Opening Bluetooth settings..."
fi

echo ""
echo "After connecting, verify with:"
echo "   python3 check_newgamepad_status.py"
echo ""
