#!/usr/bin/env python3
"""
Force gamepad recognition fix - tries multiple approaches
"""

import subprocess
import sys

def reset_bluetooth():
    """Reset Bluetooth module"""
    print("🔄 Resetting Bluetooth...")
    commands = [
        "sudo pkill bluetoothd",
        "sleep 2",
        "sudo kextunload -b com.apple.iokit.BroadcomBluetoothHostControllerUSBTransport 2>/dev/null || true",
        "sleep 2",
        "sudo kextload -b com.apple.iokit.BroadcomBluetoothHostControllerUSBTransport 2>/dev/null || true",
        "sleep 2",
    ]
    
    for cmd in commands:
        if cmd.startswith("sleep"):
            import time
            time.sleep(2)
        else:
            result = subprocess.run(cmd, shell=True, capture_output=True)
    
    print("✅ Bluetooth reset complete")
    print("⏳ Wait 10 seconds for Bluetooth to restart...")
    import time
    time.sleep(10)

def check_device_type():
    """Check current device type"""
    result = subprocess.run(
        ["system_profiler", "SPBluetoothDataType"],
        capture_output=True, text=True
    )
    
    if "Newgamepad N1" not in result.stdout:
        return None
    
    lines = result.stdout.split('\n')
    for line in lines:
        if "Newgamepad N1:" in line:
            idx = lines.index(line)
            for i in range(idx, min(idx+20, len(lines))):
                if "Minor Type:" in lines[i]:
                    return lines[i].split("Minor Type:")[1].strip()
    return None

def main():
    print("="*60)
    print("🔧 FORCE GAMEPAD FIX")
    print("="*60)
    
    print("\n⚠️  This will reset your Bluetooth connection.")
    print("    All Bluetooth devices will disconnect temporarily.")
    
    response = input("\nProceed? (y/n): ").lower()
    if response != 'y':
        print("Cancelled.")
        return
    
    # Reset Bluetooth
    reset_bluetooth()
    
    # Check device type
    print("\n📋 Checking device status...")
    device_type = check_device_type()
    
    if device_type:
        print(f"Current device type: {device_type}")
        if "Game Controller" in device_type:
            print("🎉 SUCCESS! Device is now recognized correctly!")
        else:
            print(f"❌ Still misrecognized as: {device_type}")
            print("\n💡 Next steps:")
            print("   1. Go to System Settings > Bluetooth")
            print("   2. Find 'Newgamepad N1' and click 'Forget This Device'")
            print("   3. Put gamepad in XInput mode (if available)")
            print("   4. Put gamepad in pairing mode")
            print("   5. Re-pair it")
            print("   6. Check device type again")
    else:
        print("⚠️  Device not found - may need to re-pair")
    
    print("\n✅ Bluetooth reset complete!")
    print("   Now try re-pairing your gamepad in System Settings > Bluetooth")

if __name__ == "__main__":
    main()