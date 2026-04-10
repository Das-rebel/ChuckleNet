#!/usr/bin/env python3
"""
Gamepad Firmware Update/Rewrite Tool
Attempts to find and apply firmware updates for generic gamepads
"""

import subprocess
import sys
import os
import json
import re
from typing import Dict, Optional, List

def run_cmd(cmd: str, timeout: int = 30) -> tuple:
    """Run command and return success, stdout, stderr"""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def get_device_info() -> Optional[Dict]:
    """Get device information"""
    success, output, _ = run_cmd("system_profiler SPBluetoothDataType | grep -A 15 'Gamepad-igs:'")
    
    if not success or 'Gamepad-igs' not in output:
        return None
    
    info = {}
    for line in output.split('\n'):
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

def search_firmware_online(info: Dict) -> Dict:
    """Search for firmware updates online"""
    print("\n🔍 Searching for firmware updates...")
    
    vid = info.get('vendor_id', '').replace('0x', '').upper()
    pid = info.get('product_id', '').replace('0x', '').upper()
    
    search_queries = [
        f"0x{vid} 0x{pid} gamepad firmware update",
        f"Vendor ID {vid} Product ID {pid} firmware",
        "IGS gamepad firmware update",
        "Gamepad-igs firmware update",
        f"generic bluetooth gamepad {vid} {pid} firmware"
    ]
    
    results = {
        'queries': search_queries,
        'found': False,
        'sources': [],
        'warnings': []
    }
    
    print("\n📋 Recommended Search Queries:")
    for i, query in enumerate(search_queries, 1):
        print(f"   {i}. {query}")
    
    print("\n💡 Where to Search:")
    print("   1. Google: Search the queries above")
    print("   2. GitHub: Search for 'gamepad firmware' or 'HID firmware'")
    print("   3. AliExpress/Amazon: Check product page")
    print("   4. Contact seller for firmware update tool")
    print("   5. USB ID Database: Check device compatibility")
    
    return results

def check_firmware_tools():
    """Check for available firmware update tools"""
    print("\n🔧 Checking for Firmware Update Tools...")
    
    tools = []
    
    # Check for common tools
    common_tools = [
        ('dfu-util', 'DFU (Device Firmware Update) utility'),
        ('dfu-programmer', 'DFU programmer tool'),
        ('avrdude', 'AVR device programmer'),
        ('stm32flash', 'STM32 flash tool'),
    ]
    
    for tool, desc in common_tools:
        success, _, _ = run_cmd(f"which {tool}")
        if success:
            tools.append((tool, desc, True))
        else:
            tools.append((tool, desc, False))
    
    print("\n📦 Available Tools:")
    for tool, desc, available in tools:
        status = "✅ Installed" if available else "❌ Not installed"
        print(f"   {status}: {tool} - {desc}")
    
    if not any(available for _, _, available in tools):
        print("\n⚠️  No firmware update tools found")
        print("   Most generic gamepads require manufacturer-specific tools")
    
    return tools

def create_firmware_update_guide(info: Dict):
    """Create a comprehensive firmware update guide"""
    print("\n" + "="*70)
    print("📘 FIRMWARE UPDATE GUIDE")
    print("="*70)
    
    vid = info.get('vendor_id', '').replace('0x', '').upper()
    pid = info.get('product_id', '').replace('0x', '').upper()
    
    guide = f"""
# Firmware Update Guide for Gamepad-igs

## Device Information
- Vendor ID: {info.get('vendor_id', 'Unknown')}
- Product ID: {info.get('product_id', 'Unknown')}
- Current Firmware: {info.get('firmware', 'Unknown')}
- Device Type: {info.get('device_type', 'Unknown')}

## Method 1: Manufacturer Update Tool (Recommended)

### Windows PC Method (Most Common)
1. Connect gamepad via USB to Windows PC
2. Download manufacturer firmware update tool from:
   - Manufacturer website
   - Product page (AliExpress/Amazon)
   - Contact seller
3. Run the update utility
4. Follow on-screen instructions
5. **DO NOT disconnect during update**

### Finding Update Tool
- Search: "IGS gamepad firmware update tool"
- Search: "0x{vid} 0x{pid} firmware update"
- Check USB ID database: https://devicehunt.com/all?vid={vid}&pid={pid}
- Contact seller for firmware files

## Method 2: Generic Firmware Update Tools

### DFU (Device Firmware Update)
If your gamepad supports DFU mode:
1. Put gamepad in DFU mode (check manual)
2. Install dfu-util: `brew install dfu-util`
3. Flash firmware: `dfu-util -a 0 -s 0x08000000 -D firmware.bin`

### Custom Firmware (Advanced)
⚠️  WARNING: Custom firmware can brick your device!
- Only use if you understand the risks
- Requires firmware binary file
- May need to reverse engineer HID descriptors
- Not recommended for beginners

## Method 3: HID Descriptor Modification

If firmware update isn't available, you can try modifying HID descriptors:

### macOS HID Override
1. Create override plist (see HID override guide)
2. Place in system extensions
3. Requires system modification (risky)

### Alternative: Use Input Mapper
- Use Python input mapper (gamepad_input_mapper.py)
- Works even if device is misrecognized
- Maps gamepad to keyboard/mouse/game controller

## Method 4: Third-Party Drivers

### Steam Controller Support
- Steam has built-in gamepad support
- Can recognize many generic gamepads
- Download Steam and enable controller support

### Other Tools
- Enjoyable: Maps gamepad to keyboard
- Gamepad Mapper: Professional mapping tool
- 8BitDo Ultimate Software: If compatible

## Safety Warnings

⚠️  CRITICAL WARNINGS:
1. **Never use firmware from untrusted sources**
2. **Incorrect firmware can permanently brick your device**
3. **Always backup current firmware if possible**
4. **Use official manufacturer tools when available**
5. **Do not disconnect device during firmware update**
6. **Test firmware on Windows PC if possible (more stable)**

## Troubleshooting

### Firmware Update Fails
- Try different USB cable
- Try different USB port
- Try on Windows PC instead of Mac
- Check if gamepad is in correct mode (DFU/update mode)
- Contact manufacturer support

### Device Still Misrecognized After Update
- Try different gamepad modes (XInput, DInput)
- Use input mapper instead
- Contact manufacturer for support
- May need custom HID descriptor

## Alternative Solutions

If firmware update isn't possible:
1. Use Python input mapper (works with misrecognized devices)
2. Use third-party drivers/mappers
3. Try different gamepad modes
4. Consider purchasing a compatible gamepad

## Resources

- USB ID Database: https://devicehunt.com/all?vid={vid}&pid={pid}
- HID Descriptor Guide: Check online HID documentation
- Gamepad Firmware Community: Search GitHub for projects
"""
    
    guide_file = 'FIRMWARE_UPDATE_GUIDE.md'
    with open(guide_file, 'w') as f:
        f.write(guide)
    
    print(f"\n✅ Guide saved to: {guide_file}")
    print("\n" + guide)
    
    return guide_file

def attempt_firmware_rewrite():
    """Attempt to rewrite firmware (if possible)"""
    print("\n" + "="*70)
    print("⚠️  FIRMWARE REWRITE ATTEMPT")
    print("="*70)
    
    print("\n⚠️  WARNING: Firmware rewriting is RISKY!")
    print("   - Can permanently brick your device")
    print("   - Requires firmware binary file")
    print("   - Requires update tool")
    print("   - Not recommended without manufacturer support")
    
    response = input("\nDo you have a firmware binary file? (y/n): ").lower()
    if response != 'y':
        print("\n❌ Cannot proceed without firmware file")
        print("\n💡 Options:")
        print("   1. Search for firmware online (see guide above)")
        print("   2. Contact manufacturer/seller")
        print("   3. Use input mapper instead (safer)")
        return False
    
    firmware_file = input("Enter path to firmware file: ").strip()
    
    if not os.path.exists(firmware_file):
        print(f"❌ Firmware file not found: {firmware_file}")
        return False
    
    print(f"\n✅ Found firmware file: {firmware_file}")
    
    # Check for update tool
    print("\n🔍 Checking for update tools...")
    tools = check_firmware_tools()
    
    if not any(available for _, _, available in tools):
        print("\n❌ No firmware update tools found")
        print("   You need manufacturer-specific update tool")
        return False
    
    print("\n⚠️  Proceeding with firmware update...")
    print("   This will attempt to flash the firmware")
    print("   Make sure:")
    print("   1. Gamepad is connected via USB")
    print("   2. Gamepad is in update/DFU mode")
    print("   3. You have the correct firmware for your device")
    print("   4. You have a backup if something goes wrong")
    
    confirm = input("\n⚠️  Proceed with firmware update? (yes/no): ").lower()
    if confirm != 'yes':
        print("Cancelled")
        return False
    
    # Here you would run the actual firmware update
    # This is device-specific and requires the correct tool
    print("\n⚠️  Firmware update requires device-specific tool")
    print("   Please use manufacturer's update utility")
    print("   This script cannot safely flash firmware without the tool")
    
    return False

def main():
    print("="*70)
    print("🔧 GAMEPAD FIRMWARE UPDATE/REWRITE TOOL")
    print("="*70)
    
    # Get device info
    print("\n1️⃣ Detecting device...")
    info = get_device_info()
    
    if not info:
        print("❌ Could not detect gamepad")
        return
    
    print(f"✅ Device detected:")
    print(f"   Vendor ID: {info.get('vendor_id')}")
    print(f"   Product ID: {info.get('product_id')}")
    print(f"   Firmware: {info.get('firmware')}")
    print(f"   Type: {info.get('device_type')}")
    
    # Search for firmware
    print("\n2️⃣ Searching for firmware updates...")
    search_results = search_firmware_online(info)
    
    # Check tools
    print("\n3️⃣ Checking update tools...")
    tools = check_firmware_tools()
    
    # Create guide
    print("\n4️⃣ Creating update guide...")
    guide_file = create_firmware_update_guide(info)
    
    # Options
    print("\n" + "="*70)
    print("📋 OPTIONS")
    print("="*70)
    
    print("\nChoose an option:")
    print("1. View firmware update guide")
    print("2. Search for firmware online (opens browser)")
    print("3. Attempt firmware rewrite (if you have firmware file)")
    print("4. Check USB connection (for firmware update)")
    print("5. Exit")
    
    try:
        choice = input("\nEnter choice (1-5): ").strip()
        
        if choice == '1':
            print(f"\n📘 Guide saved to: {guide_file}")
            print("   Open it to view complete instructions")
        
        elif choice == '2':
            vid = info.get('vendor_id', '').replace('0x', '').upper()
            pid = info.get('product_id', '').replace('0x', '').upper()
            url = f"https://www.google.com/search?q=0x{vid}+0x{pid}+gamepad+firmware+update"
            print(f"\n🌐 Opening search in browser...")
            run_cmd(f"open '{url}'")
        
        elif choice == '3':
            attempt_firmware_rewrite()
        
        elif choice == '4':
            print("\n🔌 USB Connection Check:")
            success, output, _ = run_cmd("system_profiler SPUSBDataType | grep -i 'gamepad\\|joystick\\|controller'")
            if success and output:
                print("✅ USB gamepad detected:")
                print(output)
            else:
                print("❌ No USB gamepad detected")
                print("   Connect gamepad via USB for firmware update")
        
        elif choice == '5':
            print("Exiting...")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Cancelled")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
