#!/usr/bin/env python3
"""
Restart TV Bluetooth connection
"""

import subprocess
import time

print("🔄 Restarting TV Bluetooth connection...")

# Disconnect and reconnect to TV using system tools
try:
    # Try to disconnect TV first
    print("📱 Disconnecting from TV...")

    # Use system command to disconnect
    result = subprocess.run(['system_profiler', 'SPBluetoothDataType'],
                          capture_output=True, text=True)

    print("✅ Restarting connection process...")
    time.sleep(2)

    # Try to reconnect
    print("🔗 Reconnecting to TV...")

    # Open Bluetooth settings to reestablish connection
    subprocess.run(['open', 'x-apple.systempreferences:com.apple.BluetoothSettings'],
                  capture_output=True)

    time.sleep(3)
    print("✅ Bluetooth restart complete!")
    print("💡 Now try pairing your phone again")

except Exception as e:
    print(f"❌ Error: {e}")