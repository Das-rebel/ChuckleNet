#!/bin/bash
# Quick check after pairing - run this immediately after you pair the gamepad

echo "🔍 Quick Pairing Status Check"
echo "=============================="
echo ""

# Check if device is paired
if system_profiler SPBluetoothDataType | grep -q "Gamepad-igs"; then
    echo "✅ Device is paired!"
    echo ""
    
    # Get device type
    DEVICE_TYPE=$(system_profiler SPBluetoothDataType | grep -A 10 "Gamepad-igs" | grep "Minor Type:" | awk -F': ' '{print $2}')
    
    if echo "$DEVICE_TYPE" | grep -q "Game Controller"; then
        echo "🎉 SUCCESS! Device is recognized as: $DEVICE_TYPE"
        echo ""
        echo "Testing pygame detection..."
        python3 -c "
import pygame
pygame.init()
pygame.joystick.init()
count = pygame.joystick.get_count()
if count > 0:
    print(f'✅ Pygame detected {count} gamepad(s)!')
    for i in range(count):
        j = pygame.joystick.Joystick(i)
        j.init()
        print(f'   - {j.get_name()}')
else:
    print('⚠️  Pygame can\\'t detect gamepad yet')
pygame.quit()
"
    else
        echo "❌ Device is still misrecognized as: $DEVICE_TYPE"
        echo ""
        echo "⚠️  Next steps:"
        echo "   1. Disconnect the gamepad"
        echo "   2. Put it in XInput mode (if available)"
        echo "   3. Re-pair it"
        echo ""
        echo "Or use the input mapper:"
        echo "   python3 gamepad_input_mapper_advanced.py"
    fi
else
    echo "⚠️  Device not found in Bluetooth"
    echo "   Make sure you've completed pairing in System Settings"
fi