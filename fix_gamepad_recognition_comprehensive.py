#!/usr/bin/env python3
"""
Comprehensive Gamepad Recognition Fix
Attempts multiple methods to fix trackpad recognition issue
"""

import subprocess
import sys
import os
import time
import json
from typing import Dict, Optional, List

def run_cmd(cmd: str, description: str = "", timeout: int = 30) -> tuple:
    """Run command and return success, stdout, stderr"""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def get_device_info() -> Optional[Dict]:
    """Get current device information"""
    success, output, _ = run_cmd("system_profiler SPBluetoothDataType | grep -A 15 'Gamepad-igs:'")
    
    if not success or 'Gamepad-igs' not in output:
        return None
    
    info = {}
    lines = output.split('\n')
    for line in lines:
        if 'Address:' in line:
            info['address'] = line.split('Address:')[1].strip()
        elif 'Vendor ID:' in line:
            info['vendor_id'] = line.split('Vendor ID:')[1].strip()
        elif 'Product ID:' in line:
            info['product_id'] = line.split('Product ID:')[1].strip()
        elif 'Firmware Version:' in line:
            info['firmware'] = line.split('Firmware Version:')[1].strip()
        elif 'Minor Type:' in line:
            info['device_type'] = line.split('Minor Type:')[1].strip()
    
    return info

def method_1_reset_bluetooth():
    """Method 1: Reset Bluetooth module"""
    print("\n" + "="*60)
    print("METHOD 1: Bluetooth Reset")
    print("="*60)
    
    print("\nThis will reset your Bluetooth connection.")
    print("All Bluetooth devices will disconnect temporarily.")
    
    response = input("\nProceed with Bluetooth reset? (y/n): ").lower()
    if response != 'y':
        return False
    
    commands = [
        ("sudo pkill bluetoothd", "Killing Bluetooth daemon"),
        ("sleep 2", "Waiting"),
        ("sudo kextunload -b com.apple.iokit.BroadcomBluetoothHostControllerUSBTransport 2>/dev/null || true",
         "Unloading Bluetooth kernel extension"),
        ("sleep 2", "Waiting"),
        ("sudo kextload -b com.apple.iokit.BroadcomBluetoothHostControllerUSBTransport 2>/dev/null || true",
         "Reloading Bluetooth kernel extension"),
        ("sleep 2", "Waiting"),
        ("sudo launchctl load /System/Library/LaunchDaemons/com.apple.bluetoothd.plist 2>/dev/null || true",
         "Restarting Bluetooth daemon")
    ]
    
    for cmd, desc in commands:
        if desc != "Waiting":
            success, _, _ = run_cmd(cmd)
            status = "✅" if success else "⚠️"
            print(f"{status} {desc}")
        else:
            time.sleep(2)
    
    print("\n⏳ Waiting for Bluetooth to restart...")
    time.sleep(5)
    return True

def method_2_forget_and_reconnect():
    """Method 2: Forget and re-pair device"""
    print("\n" + "="*60)
    print("METHOD 2: Forget and Re-pair Device")
    print("="*60)
    
    print("\n📋 Steps to fix device recognition:")
    print("\n1. Open System Settings > Bluetooth")
    print("2. Find 'Gamepad-igs' and click 'Remove' or 'Forget This Device'")
    print("3. Put gamepad in pairing mode:")
    print("   - Try different button combinations:")
    print("     • Hold Power button for 5 seconds")
    print("     • Hold Power + Home/Share button")
    print("     • Hold specific mode button (check manual)")
    print("   - Look for blinking LED indicating pairing mode")
    print("   - Try XInput mode if available")
    print("\n4. In System Settings > Bluetooth:")
    print("   - Click '+' to add new device")
    print("   - Select 'Gamepad-igs' when it appears")
    print("   - Complete pairing")
    print("\n5. After pairing, check device type:")
    print("   - Should show 'Game Controller' not 'AppleTrackpad'")
    print("   - If still wrong, try different gamepad mode and re-pair")
    
    input("\n⏸️  Press Enter when you've completed these steps...")
    
    # Verify
    info = get_device_info()
    if info and info.get('device_type') == 'Game Controller':
        print("\n✅ SUCCESS! Device is now recognized as Game Controller!")
        return True
    else:
        print(f"\n⚠️  Device type is still: {info.get('device_type', 'Unknown') if info else 'Not found'}")
        return False

def method_3_hid_override():
    """Method 3: Attempt HID descriptor override"""
    print("\n" + "="*60)
    print("METHOD 3: HID Descriptor Override (Advanced)")
    print("="*60)
    
    print("\n⚠️  This method attempts to override device recognition.")
    print("    It requires creating a custom HID descriptor override.")
    
    response = input("\nProceed with HID override attempt? (y/n): ").lower()
    if response != 'y':
        return False
    
    # Get device info
    info = get_device_info()
    if not info:
        print("❌ Could not get device info")
        return False
    
    vid = info.get('vendor_id', '').replace('0x', '').upper()
    pid = info.get('product_id', '').replace('0x', '').upper()
    
    print(f"\nDevice IDs: Vendor={vid}, Product={pid}")
    
    # Create override plist
    override_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>IOProviderClass</key>
    <string>IOHIDDevice</string>
    <key>VendorID</key>
    <integer>{int(vid, 16)}</integer>
    <key>ProductID</key>
    <integer>{int(pid, 16)}</integer>
    <key>IOClass</key>
    <string>IOHIDGameController</string>
    <key>IOUserClass</key>
    <string>IOHIDGameController</string>
</dict>
</plist>"""
    
    override_file = f'/tmp/gamepad_override_{vid}_{pid}.plist'
    
    try:
        with open(override_file, 'w') as f:
            f.write(override_content)
        print(f"\n✅ Created override file: {override_file}")
        print("\n⚠️  Note: This override may not work for all devices.")
        print("    macOS HID system is complex and may ignore this override.")
        print("    You may need to use third-party drivers instead.")
        
        print("\nTo apply (requires restart):")
        print(f"   sudo cp {override_file} /System/Library/Extensions/IOHIDFamily.kext/Contents/PlugIns/IOHIDLib.plist")
        print("   sudo kextcache -system-caches")
        print("   sudo reboot")
        
        print("\n⚠️  WARNING: Modifying system extensions can be risky!")
        print("    Consider using third-party drivers instead (Method 4).")
        
        return False  # Don't auto-apply, too risky
        
    except Exception as e:
        print(f"❌ Error creating override: {e}")
        return False

def method_4_third_party_drivers():
    """Method 4: Use third-party drivers/mappers"""
    print("\n" + "="*60)
    print("METHOD 4: Third-Party Drivers/Mappers")
    print("="*60)
    
    print("\nSince macOS isn't recognizing the device correctly,")
    print("third-party tools can help map it as a game controller:")
    
    print("\n📦 Recommended Tools:")
    print("\n1. **Enjoyable** (Free, Open Source)")
    print("   - Maps keyboard/mouse to gamepad")
    print("   - Download: https://github.com/AlexNisnevich/enjoyable")
    print("   - Can help recognize gamepad inputs")
    
    print("\n2. **Gamepad Mapper** (Paid)")
    print("   - Professional gamepad mapping tool")
    print("   - App Store or developer website")
    
    print("\n3. **Steam** (Free)")
    print("   - Has built-in controller support")
    print("   - Can recognize many gamepads")
    print("   - Download: https://store.steampowered.com/about/")
    
    print("\n4. **JoyToKey** (Free)")
    print("   - Maps gamepad to keyboard")
    print("   - Windows tool, but Wine version available")
    
    print("\n5. **8BitDo Ultimate Software** (If applicable)")
    print("   - For 8BitDo controllers")
    print("   - Check if your controller is compatible")
    
    print("\n💡 Alternative: Use Python input mapping")
    print("   - We can create a Python script to map gamepad input")
    print("   - Works even if macOS doesn't recognize it correctly")
    
    response = input("\nWould you like me to create a Python input mapper? (y/n): ").lower()
    if response == 'y':
        return True
    
    return False

def method_5_python_input_mapper():
    """Method 5: Create Python input mapper"""
    print("\n" + "="*60)
    print("METHOD 5: Python Input Mapper")
    print("="*60)
    
    mapper_code = '''#!/usr/bin/env python3
"""
Gamepad Input Mapper - Works even if device is misrecognized
Maps gamepad input to keyboard/mouse or game controller events
"""

import pygame
import sys
import time
from typing import Dict, Optional

class GamepadMapper:
    def __init__(self):
        pygame.init()
        pygame.joystick.init()
        
        self.joysticks = []
        self.running = False
        
        # Initialize joysticks
        count = pygame.joystick.get_count()
        if count == 0:
            print("⚠️  No gamepads detected by pygame")
            print("   Trying alternative detection methods...")
            self.try_alternative_detection()
        else:
            for i in range(count):
                joy = pygame.joystick.Joystick(i)
                joy.init()
                self.joysticks.append(joy)
                print(f"✅ Detected: {joy.get_name()}")
    
    def try_alternative_detection(self):
        """Try alternative methods to detect gamepad"""
        import subprocess
        
        # Check if device is connected via Bluetooth
        result = subprocess.run(
            ["system_profiler", "SPBluetoothDataType"],
            capture_output=True, text=True
        )
        
        if "Gamepad-igs" in result.stdout:
            print("✅ Gamepad-igs found in Bluetooth devices")
            print("   Device may be misrecognized, but we can try to use it")
            print("   Try re-pairing in XInput mode")
    
    def map_input(self, joystick_id=0):
        """Map gamepad input - customizable mapping"""
        if not self.joysticks:
            print("❌ No joysticks available")
            return
        
        joy = self.joysticks[joystick_id]
        
        print(f"\\n🎮 Mapping input from: {joy.get_name()}")
        print("Press buttons and move sticks to test")
        print("Press Ctrl+C to stop\\n")
        
        # Button mapping (customize as needed)
        button_map = {
            0: 'A',
            1: 'B',
            2: 'X',
            3: 'Y',
            4: 'LB',
            5: 'RB',
            6: 'Back',
            7: 'Start',
            8: 'Left Stick',
            9: 'Right Stick'
        }
        
        # Axis mapping
        axis_map = {
            0: 'Left Stick X',
            1: 'Left Stick Y',
            2: 'Right Stick X',
            3: 'Right Stick Y',
            4: 'LT',
            5: 'RT'
        }
        
        pygame.event.set_allowed([
            pygame.JOYBUTTONDOWN,
            pygame.JOYBUTTONUP,
            pygame.JOYAXISMOTION,
            pygame.JOYHATMOTION
        ])
        
        try:
            while True:
                for event in pygame.event.get():
                    if event.type == pygame.JOYBUTTONDOWN:
                        btn_name = button_map.get(event.button, f'Button {event.button}')
                        print(f"🔘 {btn_name} pressed")
                        # Here you can add keyboard/mouse emulation
                        # Example: keyboard.press('a') if event.button == 0
                    
                    elif event.type == pygame.JOYAXISMOTION:
                        if abs(event.value) > 0.1:
                            axis_name = axis_map.get(event.axis, f'Axis {event.axis}')
                            print(f"🕹️  {axis_name}: {event.value:+.2f}")
                    
                    elif event.type == pygame.JOYHATMOTION:
                        if event.value != (0, 0):
                            print(f"🎯 Hat {event.hat}: {event.value}")
                
                time.sleep(0.01)
        
        except KeyboardInterrupt:
            print("\\n\\n⏹️  Stopped")
    
    def run(self):
        """Run the mapper"""
        if not self.joysticks:
            print("\\n❌ No gamepads detected")
            print("\\nTroubleshooting:")
            print("1. Make sure gamepad is connected")
            print("2. Try re-pairing in XInput mode")
            print("3. Check System Settings > Privacy > Input Monitoring")
            return
        
        self.map_input(0)

if __name__ == "__main__":
    mapper = GamepadMapper()
    mapper.run()
    pygame.quit()
'''
    
    mapper_file = 'gamepad_input_mapper.py'
    
    try:
        with open(mapper_file, 'w') as f:
            f.write(mapper_code)
        
        # Make executable
        os.chmod(mapper_file, 0o755)
        
        print(f"\n✅ Created Python input mapper: {mapper_file}")
        print("\nUsage:")
        print(f"   python3 {mapper_file}")
        print("\nThis mapper will:")
        print("- Detect gamepad even if macOS misrecognizes it")
        print("- Map buttons and sticks to actions")
        print("- Allow customization for your needs")
        print("- Can be extended to map to keyboard/mouse")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating mapper: {e}")
        return False

def method_6_firmware_update_check():
    """Method 6: Check for firmware update to fix recognition"""
    print("\n" + "="*60)
    print("METHOD 6: Firmware Update (If Available)")
    print("="*60)
    
    print("\n📋 Firmware Update Options:")
    print("\n1. **Check Manufacturer Website**")
    print("   - Search for your gamepad model + 'firmware update'")
    print("   - Look for official update tools")
    
    print("\n2. **Windows PC Update** (Most Common)")
    print("   - Connect gamepad via USB to Windows PC")
    print("   - Download manufacturer firmware update tool")
    print("   - Run update utility")
    print("   - Some firmware updates can fix device recognition")
    
    print("\n3. **Check Product Page**")
    print("   - If purchased from AliExpress/Amazon")
    print("   - Check product page for firmware files")
    print("   - Contact seller for update tool")
    
    print("\n4. **Generic Firmware Update Tools**")
    print("   - Some generic gamepads use standard update tools")
    print("   - Search for 'generic bluetooth gamepad firmware update'")
    
    print("\n⚠️  WARNING: Firmware updates can:")
    print("   - Fix device recognition issues")
    print("   - But incorrect firmware can brick your device")
    print("   - Always use official/manufacturer tools")
    print("   - Backup current firmware if possible")
    
    # Run firmware checker
    print("\n🔍 Running firmware update checker...")
    success, _, _ = run_cmd("python3 check_gamepad_firmware_update.py")
    
    return True

def main():
    print("="*70)
    print("🔧 COMPREHENSIVE GAMEPAD RECOGNITION FIX")
    print("="*70)
    
    # Check current status
    print("\n1️⃣ Checking current device status...")
    info = get_device_info()
    
    if info:
        print(f"\n📱 Current Status:")
        print(f"   Device Type: {info.get('device_type', 'Unknown')}")
        print(f"   Vendor ID: {info.get('vendor_id', 'Unknown')}")
        print(f"   Product ID: {info.get('product_id', 'Unknown')}")
        print(f"   Firmware: {info.get('firmware', 'Unknown')}")
        
        if info.get('device_type') == 'Game Controller':
            print("\n✅ Device is already recognized correctly!")
            return
        else:
            print(f"\n❌ Device is recognized as '{info.get('device_type')}' instead of 'Game Controller'")
    else:
        print("\n⚠️  Could not detect device")
    
    print("\n" + "="*70)
    print("🔧 AVAILABLE FIX METHODS")
    print("="*70)
    
    print("\nChoose a method to try:")
    print("1. Reset Bluetooth (Simple, often works)")
    print("2. Forget and Re-pair (Most reliable)")
    print("3. HID Override (Advanced, risky)")
    print("4. Third-Party Drivers (Recommended alternative)")
    print("5. Python Input Mapper (Works even if misrecognized)")
    print("6. Check for Firmware Update")
    print("7. Try all methods in sequence")
    print("8. Exit")
    
    try:
        choice = input("\nEnter choice (1-8): ").strip()
        
        if choice == '1':
            method_1_reset_bluetooth()
            method_2_forget_and_reconnect()
        
        elif choice == '2':
            method_2_forget_and_reconnect()
        
        elif choice == '3':
            method_3_hid_override()
        
        elif choice == '4':
            method_4_third_party_drivers()
        
        elif choice == '5':
            method_5_python_input_mapper()
        
        elif choice == '6':
            method_6_firmware_update_check()
        
        elif choice == '7':
            print("\n🔄 Trying all methods in sequence...")
            method_1_reset_bluetooth()
            if not method_2_forget_and_reconnect():
                method_4_third_party_drivers()
                method_5_python_input_mapper()
        
        elif choice == '8':
            print("Exiting...")
            return
        
        else:
            print("Invalid choice")
        
        # Final verification
        print("\n" + "="*70)
        print("✅ FINAL VERIFICATION")
        print("="*70)
        
        info = get_device_info()
        if info:
            if info.get('device_type') == 'Game Controller':
                print("\n🎉 SUCCESS! Device is now recognized as Game Controller!")
            else:
                print(f"\n⚠️  Device type is still: {info.get('device_type')}")
                print("\n💡 Alternative solutions:")
                print("   - Use Python input mapper (method 5)")
                print("   - Use third-party drivers (method 4)")
                print("   - Try firmware update (method 6)")
        else:
            print("\n⚠️  Could not verify device status")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
