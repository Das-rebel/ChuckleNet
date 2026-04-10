#!/usr/bin/env python3
"""
Force gamepad recognition fix - automated version
"""

import subprocess
import sys
import time
import os

def reset_bluetooth():
    """Reset Bluetooth module"""
    print("🔄 Resetting Bluetooth module...")
    print("   This will temporarily disconnect all Bluetooth devices.")
    print("   ⏳ Please wait...")
    
    commands = [
        ("sudo pkill bluetoothd", "Stopping Bluetooth daemon"),
        ("sleep 2", None),
        ("sudo kextunload -b com.apple.iokit.BroadcomBluetoothHostControllerUSBTransport 2>/dev/null || true", "Unloading Bluetooth extension"),
        ("sleep 2", None),
        ("sudo kextload -b com.apple.iokit.BroadcomBluetoothHostControllerUSBTransport 2>/dev/null || true", "Loading Bluetooth extension"),
        ("sleep 2", None),
    ]
    
    for cmd, desc in commands:
        if desc:
            print(f"   {desc}...")
        if not cmd.startswith("sleep"):
            result = subprocess.run(cmd, shell=True, capture_output=True)
        else:
            time.sleep(2)
    
    print("   ⏳ Waiting for Bluetooth to restart...")
    time.sleep(10)
    print("✅ Bluetooth reset complete!")

def check_device_type():
    """Check current device type"""
    result = subprocess.run(
        ["system_profiler", "SPBluetoothDataType"],
        capture_output=True, text=True
    )
    
    if "Newgamepad N1" not in result.stdout:
        return None, "Device not found"
    
    lines = result.stdout.split('\n')
    for line in lines:
        if "Newgamepad N1:" in line:
            idx = lines.index(line)
            for i in range(idx, min(idx+20, len(lines))):
                if "Minor Type:" in lines[i]:
                    device_type = lines[i].split("Minor Type:")[1].strip()
                    return device_type, "Device found"
    return None, "Device found but type unknown"

def main():
    print("="*60)
    print("🔧 FORCE GAMEPAD FIX (AUTOMATED)")
    print("="*60)
    
    # Check if running as root/sudo
    if os.geteuid() != 0:
        print("\n⚠️  This script requires sudo privileges.")
        print("   Running with sudo...")
        print("\n   Please enter your password when prompted:")
        print("   (This is needed to reset Bluetooth)")
        
        # Re-run with sudo
        result = subprocess.run(
            ["sudo", sys.executable, __file__],
            stdin=sys.stdin
        )
        sys.exit(result.returncode)
    
    # Reset Bluetooth
    reset_bluetooth()
    
    # Check device type
    print("\n📋 Checking device status...")
    device_type, status = check_device_type()
    
    if device_type:
        print(f"\n📱 Device Type: {device_type}")
        if "Game Controller" in device_type:
            print("\n🎉🎉🎉 SUCCESS! Device is now recognized correctly! 🎉🎉🎉")
            print("   Your gamepad should now work with games and pygame!")
        else:
            print(f"\n❌ Still misrecognized as: {device_type}")
            print("\n💡 Next Steps:")
            print("   1. Go to System Settings > Bluetooth")
            print("   2. Find 'Newgamepad N1' and click 'Forget This Device'")
            print("   3. Put gamepad in XInput mode (if available - look for X/D/S/M switch)")
            print("   4. Put gamepad in pairing mode:")
            print("      - Hold Power button for 5-10 seconds")
            print("      - Or Power + Home/Share button")
            print("      - Look for blinking LED")
            print("   5. In System Settings > Bluetooth, click '+' to add device")
            print("   6. Select 'Newgamepad N1' when it appears")
            print("   7. After pairing, click 'i' button and verify it shows 'Game Controller'")
            print("\n   Then run: python3 check_newgamepad_status.py")
    else:
        print(f"\n⚠️  {status}")
        print("   Device may need to be re-paired.")
        print("   Follow the steps above to re-pair your gamepad.")
    
    print("\n" + "="*60)
    print("✅ Bluetooth reset complete!")
    print("   Now proceed with re-pairing your gamepad.")
    print("="*60)

if __name__ == "__main__":
    main()