#!/usr/bin/env python3
"""
Quick status checker - run after each step to verify progress
"""

import subprocess
import sys

def check_status():
    """Check current gamepad status"""
    print("\n" + "="*60)
    print("🔍 CHECKING GAMEPAD STATUS")
    print("="*60)
    
    # Check Bluetooth
    result = subprocess.run(
        ["system_profiler", "SPBluetoothDataType"],
        capture_output=True, text=True
    )
    
    if "Gamepad-igs" in result.stdout:
        print("\n✅ Device Found in Bluetooth")
        
        # Extract details
        lines = result.stdout.split('\n')
        in_section = False
        details = {}
        
        for line in lines:
            if "Gamepad-igs:" in line:
                in_section = True
                continue
            
            if in_section:
                if line.strip() and not line.startswith(' '):
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
                    details['type'] = line.split("Minor Type:")[1].strip()
        
        print(f"\n📱 Device Details:")
        for key, value in details.items():
            print(f"   {key.replace('_', ' ').title()}: {value}")
        
        # Check device type
        device_type = details.get('type', '')
        if 'Game Controller' in device_type:
            print("\n🎉 SUCCESS! Device is recognized as 'Game Controller'!")
            return True
        elif 'AppleTrackpad' in device_type or 'Headset' in device_type:
            print(f"\n❌ Still recognized as '{device_type}'")
            print("   Continue with next steps...")
            return False
    else:
        print("\n⚠️  Device not found in Bluetooth")
        print("   This is normal if you just forgot the device")
        print("   Continue with pairing steps...")
        return None
    
    return False

def check_pygame():
    """Check if pygame can detect the gamepad"""
    print("\n" + "="*60)
    print("🎮 CHECKING PYGAME DETECTION")
    print("="*60)
    
    try:
        import pygame
        pygame.init()
        pygame.joystick.init()
        
        count = pygame.joystick.get_count()
        
        if count > 0:
            print(f"\n✅ Pygame detected {count} gamepad(s):")
            for i in range(count):
                joy = pygame.joystick.Joystick(i)
                joy.init()
                print(f"   - {joy.get_name()}")
                print(f"     Axes: {joy.get_numaxes()}, Buttons: {joy.get_numbuttons()}")
            pygame.quit()
            return True
        else:
            print("\n⚠️  Pygame can't detect gamepad yet")
            print("   This is normal if device is misrecognized")
            pygame.quit()
            return False
    except ImportError:
        print("\n⚠️  Pygame not installed")
        return False
    except Exception as e:
        print(f"\n⚠️  Error: {e}")
        return False

if __name__ == "__main__":
    print("="*60)
    print("📊 GAMEPAD FIX PROGRESS CHECKER")
    print("="*60)
    
    # Check Bluetooth status
    bluetooth_ok = check_status()
    
    # Check pygame detection
    pygame_ok = check_pygame()
    
    # Summary
    print("\n" + "="*60)
    print("📋 SUMMARY")
    print("="*60)
    
    if bluetooth_ok:
        print("✅ Bluetooth Recognition: FIXED!")
    elif bluetooth_ok is None:
        print("⏳ Bluetooth Recognition: Device not paired (this is OK if you forgot it)")
    else:
        print("❌ Bluetooth Recognition: Still needs fixing")
    
    if pygame_ok:
        print("✅ Pygame Detection: WORKING!")
    else:
        print("⚠️  Pygame Detection: Not working yet")
    
    print("\n💡 Next Steps:")
    if not bluetooth_ok and bluetooth_ok is not None:
        print("   1. Re-pair the device in XInput mode")
        print("   2. Check device type after pairing")
    elif bluetooth_ok is None:
        print("   1. Put gamepad in pairing mode")
        print("   2. Re-pair in System Settings > Bluetooth")
    elif bluetooth_ok and not pygame_ok:
        print("   1. Try: python3 gamepad_input_mapper_advanced.py")
        print("   2. Check System Settings > Privacy > Input Monitoring")
    else:
        print("   🎉 Everything looks good!")
