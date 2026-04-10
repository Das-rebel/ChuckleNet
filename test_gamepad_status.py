#!/usr/bin/env python3
"""
Simple Gamepad Status Test Script
Quickly check if your gamepad is properly connected and recognized
"""

import subprocess
import sys

def check_bluetooth_status():
    """Check Bluetooth gamepad status"""
    print("🔍 Checking Bluetooth gamepad status...")
    try:
        result = subprocess.run(
            "system_profiler SPBluetoothDataType | grep -A 10 -B 2 'Gamepad'",
            shell=True, capture_output=True, text=True, timeout=10
        )
        
        if result.returncode == 0 and result.stdout.strip():
            print("📱 Bluetooth Status:")
            print(result.stdout)
            
            # Check if it's recognized as Game Controller
            if "Game Controller" in result.stdout:
                print("✅ Device type: Game Controller (Correct!)")
                return True
            elif "AppleTrackpad" in result.stdout:
                print("❌ Device type: AppleTrackpad (Incorrect - needs fixing)")
                return False
            else:
                print("⚠️  Device type: Unknown")
                return False
        else:
            print("❌ No gamepad found in Bluetooth devices")
            return False
            
    except Exception as e:
        print(f"💥 Error checking Bluetooth: {e}")
        return False

def check_pygame_detection():
    """Check if pygame can detect the gamepad"""
    print("\n🎮 Checking pygame gamepad detection...")
    try:
        # Use a temporary Python file to avoid shell escaping issues
        import tempfile
        import os
        
        pygame_test = '''
import pygame
pygame.init()
pygame.joystick.init()
count = pygame.joystick.get_count()
print(f"Joysticks detected: {count}")
if count > 0:
    for i in range(count):
        j = pygame.joystick.Joystick(i)
        print(f"Joystick {i}: {j.get_name()}")
        print(f"  - Axes: {j.get_numaxes()}")
        print(f"  - Buttons: {j.get_numbuttons()}")
        print(f"  - Hats: {j.get_numhats()}")
pygame.quit()
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(pygame_test)
            temp_file = f.name
        
        try:
            result = subprocess.run(
                f"python3 {temp_file}",
                shell=True, capture_output=True, text=True, timeout=10
            )
        finally:
            os.unlink(temp_file)
        
        if result.returncode == 0:
            print("🎮 Pygame Status:")
            print(result.stdout)
            
            if "Joysticks detected: 0" in result.stdout:
                print("❌ Pygame cannot detect any gamepads")
                return False
            else:
                print("✅ Pygame can detect gamepad(s)")
                return True
        else:
            print(f"❌ Pygame test failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"💥 Error testing pygame: {e}")
        return False

def main():
    """Main test function"""
    print("🎮 Gamepad Status Test")
    print("=" * 30)
    
    bluetooth_ok = check_bluetooth_status()
    pygame_ok = check_pygame_detection()
    
    print("\n" + "=" * 30)
    print("📊 SUMMARY:")
    print(f"Bluetooth Recognition: {'✅ Working' if bluetooth_ok else '❌ Not Working'}")
    print(f"Pygame Detection: {'✅ Working' if pygame_ok else '❌ Not Working'}")
    
    if bluetooth_ok and pygame_ok:
        print("\n🎉 SUCCESS: Your gamepad is properly connected and working!")
    elif bluetooth_ok and not pygame_ok:
        print("\n⚠️  PARTIAL: Gamepad is connected but pygame can't detect it")
        print("   This might be a pygame or driver issue")
    elif not bluetooth_ok:
        print("\n❌ FAILED: Gamepad is not properly recognized by the system")
        print("   Run the fix script: python3 fix_gamepad_connection.py")
    else:
        print("\n❌ FAILED: Multiple issues detected")
        print("   Run the fix script: python3 fix_gamepad_connection.py")

if __name__ == "__main__":
    main()