#!/usr/bin/env python3
"""
Interactive Gamepad Recognition Fix
Automated fix for gamepad recognition issues
"""

import subprocess
import sys
import time

def run_cmd(cmd, description=""):
    """Run command and return result"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def check_current_status():
    """Check current gamepad status"""
    print("\n" + "="*60)
    print("🔍 CURRENT STATUS")
    print("="*60)
    
    success, output, _ = run_cmd("system_profiler SPBluetoothDataType | grep -A 15 'Gamepad-igs'")
    
    if success and output:
        print(output)
        
        # Check device type
        if "Game Controller" in output:
            print("\n✅ Device is recognized as Game Controller!")
            return True
        elif "Headset" in output or "AppleTrackpad" in output:
            print("\n❌ Device is NOT recognized as Game Controller")
            print("   Current type: Headset/AppleTrackpad (incorrect)")
            return False
    else:
        print("⚠️  Could not find gamepad in Bluetooth devices")
        return False
    
    return False

def reset_bluetooth():
    """Reset Bluetooth module"""
    print("\n" + "="*60)
    print("🔄 RESETTING BLUETOOTH")
    print("="*60)
    
    print("\n⚠️  This will reset your Bluetooth connection.")
    print("   All Bluetooth devices will disconnect temporarily.")
    
    # Reset via System Preferences method (safer)
    print("\n📋 Manual Bluetooth Reset Instructions:")
    print("   1. Hold Shift + Option keys")
    print("   2. Click the Bluetooth icon in the menu bar")
    print("   3. Select 'Debug' > 'Reset the Bluetooth module'")
    print("   4. Wait for Bluetooth to restart (about 10 seconds)")
    
    print("\n💡 Alternative: Use System Settings")
    print("   1. Open System Settings > Bluetooth")
    print("   2. Turn Bluetooth Off")
    print("   3. Wait 5 seconds")
    print("   4. Turn Bluetooth On")
    
    print("\n⏳ Waiting 15 seconds for you to reset Bluetooth...")
    print("   (If you've already reset it, you can continue)")
    time.sleep(15)

def forget_device_instructions():
    """Provide instructions to forget device"""
    print("\n" + "="*60)
    print("📱 FORGET DEVICE - MANUAL STEP")
    print("="*60)
    
    print("\nFollow these steps to forget the gamepad:")
    print("\n1. Open System Settings (or System Preferences)")
    print("2. Go to Bluetooth")
    print("3. Find 'Gamepad-igs' in the device list")
    print("4. Click the 'i' (info) button next to it")
    print("   OR right-click and select 'Remove'")
    print("   OR click the 'X' button if available")
    print("5. Confirm removal/forgetting the device")
    
    input("\n⏸️  Press Enter when you've forgotten the device...")

def pair_device_instructions():
    """Provide instructions to re-pair device"""
    print("\n" + "="*60)
    print("🎮 RE-PAIR DEVICE - MANUAL STEP")
    print("="*60)
    
    print("\nFollow these steps to re-pair your gamepad:")
    print("\n1. Put your gamepad in pairing mode:")
    print("   - Usually: Hold Power + another button (check manual)")
    print("   - Some gamepads: Hold a specific button for 3-5 seconds")
    print("   - Look for blinking LED indicating pairing mode")
    print("   - Try XInput mode if your gamepad has mode switching")
    print("\n2. In System Settings > Bluetooth:")
    print("   - Click '+' or 'Set Up New Device'")
    print("   - Wait for 'Gamepad-igs' to appear")
    print("   - Click on it to connect")
    print("   - Complete pairing process")
    print("\n3. IMPORTANT: After pairing, check:")
    print("   - Device shows as 'Connected'")
    print("   - Device type should be 'Game Controller' (not Headset/Trackpad)")
    
    input("\n⏸️  Press Enter when you've re-paired the device...")

def test_pygame():
    """Test pygame detection"""
    print("\n" + "="*60)
    print("🧪 TESTING PYGAME DETECTION")
    print("="*60)
    
    try:
        import pygame
    except ImportError:
        print("Installing pygame...")
        success, _, _ = run_cmd(f"{sys.executable} -m pip install pygame")
        if not success:
            print("❌ Failed to install pygame")
            return False
        import pygame
    
    pygame.init()
    pygame.joystick.init()
    
    count = pygame.joystick.get_count()
    print(f"\nPygame detected {count} joystick(s)")
    
    if count == 0:
        print("❌ No gamepads detected by pygame")
        return False
    
    for i in range(count):
        joystick = pygame.joystick.Joystick(i)
        joystick.init()
        print(f"\n✅ Joystick {i}: {joystick.get_name()}")
        print(f"   - Axes: {joystick.get_numaxes()}")
        print(f"   - Buttons: {joystick.get_numbuttons()}")
        print(f"   - Hats: {joystick.get_numhats()}")
    
    pygame.quit()
    return True

def main():
    print("="*60)
    print("🎮 GAMEPAD RECOGNITION FIX")
    print("="*60)
    
    # Check current status
    is_recognized = check_current_status()
    
    if is_recognized:
        print("\n✅ Your gamepad is already properly recognized!")
        if test_pygame():
            print("\n🎉 Everything is working correctly!")
            return
        else:
            print("\n⚠️  Device is recognized but pygame can't detect it")
            print("   This might be a pygame/driver issue")
    
    print("\n🔧 Starting fix process...")
    
    # Step 1: Reset Bluetooth
    reset_bluetooth()
    
    # Step 2: Forget device
    forget_device_instructions()
    
    # Step 3: Re-pair device
    pair_device_instructions()
    
    # Step 4: Verify
    print("\n" + "="*60)
    print("✅ VERIFICATION")
    print("="*60)
    
    is_recognized = check_current_status()
    
    if is_recognized:
        print("\n✅ Device recognition fixed!")
    else:
        print("\n⚠️  Device may still need adjustment")
        print("   Try different gamepad modes (XInput, DInput, etc.)")
    
    # Test pygame
    if test_pygame():
        print("\n🎉 SUCCESS! Gamepad is working correctly!")
        print("\nYou can now test input with:")
        print("   python3 quick_gamepad_test.py")
        print("   python3 gamepad_firmware_and_input_manager.py")
    else:
        print("\n⚠️  Pygame still can't detect the gamepad")
        print("\nTroubleshooting:")
        print("1. Make sure gamepad is in XInput mode")
        print("2. Try disconnecting and reconnecting")
        print("3. Check System Settings > Privacy > Input Monitoring")
        print("4. Restart your computer if needed")

if __name__ == "__main__":
    main()
