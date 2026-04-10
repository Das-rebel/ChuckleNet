#!/bin/bash

echo "🔧 FORCE GAMEPAD FIX - BLUETOOTH RESET"
echo "======================================="
echo ""
echo "⚠️  This will reset your Bluetooth connection."
echo "    All Bluetooth devices will disconnect temporarily."
echo ""
echo "Press Enter to continue (or Ctrl+C to cancel)..."
read -p ""

echo ""
echo "🔄 Step 1: Resetting Bluetooth module..."
echo "   (You may be prompted for your password)"
echo ""

# Reset Bluetooth
sudo pkill bluetoothd 2>/dev/null
sleep 2
sudo kextunload -b com.apple.iokit.BroadcomBluetoothHostControllerUSBTransport 2>/dev/null || true
sleep 2
sudo kextload -b com.apple.iokit.BroadcomBluetoothHostControllerUSBTransport 2>/dev/null || true
sleep 2

echo "✅ Bluetooth reset complete!"
echo ""
echo "⏳ Waiting 10 seconds for Bluetooth to restart..."
sleep 10

echo ""
echo "✅ Bluetooth has been reset!"
echo ""
echo "📋 NEXT STEPS - Please follow these carefully:"
echo ""
echo "1. Go to System Settings > Bluetooth"
echo ""
echo "2. Find 'Newgamepad N1' in the list"
echo "   Click the 'i' (info) button next to it"
echo "   Click 'Forget This Device' or 'Remove'"
echo ""
echo "3. Put your gamepad in XInput mode (if available):"
echo "   - Look for a mode switch on the gamepad (X/D/S/M)"
echo "   - Set it to 'X' (XInput mode)"
echo "   - This is best for Mac compatibility"
echo ""
echo "4. Put gamepad in pairing mode:"
echo "   - Hold Power button for 5-10 seconds"
echo "   - OR hold Power + Home/Share button together"
echo "   - Look for blinking LED indicating pairing mode"
echo ""
echo "5. In System Settings > Bluetooth:"
echo "   - Click the '+' button or 'Set Up New Device'"
echo "   - Wait for 'Newgamepad N1' to appear"
echo "   - Click on it to pair"
echo "   - Wait for pairing to complete"
echo ""
echo "6. After pairing, click the 'i' (info) button again"
echo "   - Check the 'Type' or 'Minor Type' field"
echo "   - It should say 'Game Controller' (not 'AppleTrackpad' or 'Headset')"
echo ""
echo "7. After re-pairing, run this command to verify:"
echo "   python3 check_newgamepad_status.py"
echo ""
echo "Press Enter when you've completed these steps..."
read -p ""

echo ""
echo "Checking status..."
python3 check_newgamepad_status.py