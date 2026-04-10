#!/usr/bin/env python3
"""
Check status of Newgamepad N1 specifically
"""

import subprocess
import sys

def check_device():
    """Check Newgamepad N1 status"""
    result = subprocess.run(
        ["system_profiler", "SPBluetoothDataType"],
        capture_output=True, text=True
    )
    
    if "Newgamepad N1" not in result.stdout:
        print("❌ Newgamepad N1 not found in Bluetooth")
        return False
    
    print("✅ Device found: Newgamepad N1")
    print("\n📋 Device Details:")
    
    lines = result.stdout.split('\n')
    in_section = False
    details = {}
    
    for line in lines:
        if "Newgamepad N1:" in line:
            in_section = True
            continue
        
        if in_section:
            if line.strip() and not line.startswith(' ') and ':' not in line:
                break
            
            if "Address:" in line:
                details['address'] = line.split("Address:")[1].strip()
            elif "Vendor ID:" in line:
                details['vendor_id'] = line.split("Vendor ID:")[1].strip()
            elif "Product ID:" in line:
                details['product_id'] = line.split("Product ID:")[1].strip()
            elif "Firmware Version:" in line:
                details['firmware'] = line.split("Firmware Version:")[1].strip()
            elif "Minor Type:" in line:
                details['device_type'] = line.split("Minor Type:")[1].strip()
            elif "Major Type:" in line:
                details['major_type'] = line.split("Major Type:")[1].strip()
            elif "Services:" in line:
                details['services'] = line.split("Services:")[1].strip()
    
    for key, value in details.items():
        print(f"   {key.replace('_', ' ').title()}: {value}")
    
    # Check device type
    device_type = details.get('device_type', 'Unknown')
    print(f"\n🎯 Device Recognition Status:")
    
    if 'Game Controller' in device_type:
        print("   ✅ SUCCESS! Recognized as Game Controller!")
        return True
    elif 'AppleTrackpad' in device_type or 'Headset' in device_type:
        print(f"   ❌ Still misrecognized as: {device_type}")
        print("   ⚠️  This is the problem - device needs to be recognized as Game Controller")
        return False
    else:
        print(f"   ⚠️  Device type: {device_type}")
        print("   (Unknown if this is correct)")
        return None

def check_pygame():
    """Check pygame detection"""
    print("\n🎮 Pygame Detection:")
    try:
        import pygame
        pygame.init()
        pygame.joystick.init()
        
        count = pygame.joystick.get_count()
        
        if count > 0:
            print(f"   ✅ Pygame detected {count} gamepad(s):")
            for i in range(count):
                joy = pygame.joystick.Joystick(i)
                joy.init()
                print(f"      [{i}] {joy.get_name()}")
                print(f"          Axes: {joy.get_numaxes()}, Buttons: {joy.get_numbuttons()}")
            pygame.quit()
            return True
        else:
            print("   ❌ Pygame can't detect gamepad (0 joysticks found)")
            print("   This is likely because device is misrecognized")
            pygame.quit()
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("="*60)
    print("🔍 CHECKING NEWGAMEPAD N1 STATUS")
    print("="*60)
    
    device_ok = check_device()
    pygame_ok = check_pygame()
    
    print("\n" + "="*60)
    print("📋 SUMMARY")
    print("="*60)
    
    if device_ok:
        if pygame_ok:
            print("🎉🎉🎉 SUCCESS! Everything is working! 🎉🎉🎉")
        else:
            print("✅ Device recognized correctly, but pygame can't detect it")
            print("   Try: python3 gamepad_input_mapper_advanced.py")
    elif device_ok is False:
        print("❌ Device is still misrecognized")
        print("   Next steps:")
        print("   1. Disconnect and re-pair in XInput mode")
        print("   2. Or use: python3 gamepad_input_mapper_advanced.py")
    else:
        print("⚠️  Device status unclear - check device type above")