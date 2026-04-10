#!/bin/bash

echo "🎮 Gamepad Connection Fix Script"
echo "================================"
echo ""

echo "Step 1: Resetting Bluetooth module..."
echo "This will temporarily disconnect all Bluetooth devices."
echo ""

# Reset Bluetooth module
echo "Killing Bluetooth daemon..."
sudo pkill bluetoothd

echo "Unloading Bluetooth kernel extension..."
sudo kextunload -b com.apple.iokit.BroadcomBluetoothHostControllerUSBTransport

echo "Reloading Bluetooth kernel extension..."
sudo kextload -b com.apple.iokit.BroadcomBluetoothHostControllerUSBTransport

echo "Starting Bluetooth daemon..."
sudo launchctl load /System/Library/LaunchDaemons/com.apple.bluetoothd.plist

echo ""
echo "✅ Bluetooth module reset complete!"
echo ""
echo "Step 2: Manual steps required:"
echo "1. Open System Preferences > Bluetooth"
echo "2. Find 'Gamepad-igs' in the list"
echo "3. Click the 'X' next to it to forget/remove the device"
echo "4. Put your gamepad in pairing mode (check manual for instructions)"
echo "5. Click '+' or 'Set Up New Device' in Bluetooth preferences"
echo "6. Select your gamepad when it appears and complete pairing"
echo ""
echo "Step 3: After reconnecting, run this command to test:"
echo "python3 gamepad_config.py"
echo ""
echo "Press Enter when you've completed the manual steps..."
read -p ""

echo "Testing gamepad connection..."
python3 gamepad_config.py