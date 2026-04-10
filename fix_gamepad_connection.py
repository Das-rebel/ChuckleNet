#!/usr/bin/env python3
"""
Gamepad Connection Fix Script for macOS
This script helps fix the issue where gamepads are recognized as AppleTrackpad instead of Game Controller
"""

import subprocess
import sys
import time
import os

def run_command(cmd, description):
    """Run a command and return the result"""
    print(f"\n🔧 {description}")
    print(f"Running: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(f"✅ Success: {description}")
            if result.stdout.strip():
                print(f"Output: {result.stdout.strip()}")
        else:
            print(f"❌ Failed: {description}")
            if result.stderr.strip():
                print(f"Error: {result.stderr.strip()}")
        return result
    except subprocess.TimeoutExpired:
        print(f"⏰ Timeout: {description}")
        return None
    except Exception as e:
        print(f"💥 Exception: {description} - {e}")
        return None

def check_gamepad_status():
    """Check current gamepad status"""
    print("🔍 Checking current gamepad status...")
    
    # Check Bluetooth devices
    result = run_command("system_profiler SPBluetoothDataType | grep -A 10 -B 2 'Gamepad'", "Check Bluetooth gamepad status")
    
    # Check pygame detection
    pygame_test = '''
import pygame
pygame.init()
pygame.joystick.init()
print(f'Joysticks detected: {pygame.joystick.get_count()}')
for i in range(pygame.joystick.get_count()):
    j = pygame.joystick.Joystick(i)
    print(f'Joystick {i}: {j.get_name()}')
pygame.quit()
'''
    
    result = run_command(f"python3 -c \"{pygame_test}\"", "Check pygame gamepad detection")
    
    return result

def reset_bluetooth():
    """Reset Bluetooth module"""
    print("\n🔄 Resetting Bluetooth module...")
    
    commands = [
        ("sudo pkill bluetoothd", "Kill Bluetooth daemon"),
        ("sudo kextunload -b com.apple.iokit.BroadcomBluetoothHostControllerUSBTransport", "Unload Bluetooth kernel extension"),
        ("sudo kextload -b com.apple.iokit.BroadcomBluetoothHostControllerUSBTransport", "Reload Bluetooth kernel extension"),
        ("sudo launchctl load /System/Library/LaunchDaemons/com.apple.bluetoothd.plist", "Restart Bluetooth daemon")
    ]
    
    for cmd, desc in commands:
        result = run_command(cmd, desc)
        if result and result.returncode != 0:
            print(f"⚠️  Warning: {desc} failed, but continuing...")
        time.sleep(2)
    
    print("⏳ Waiting for Bluetooth to restart...")
    time.sleep(5)

def forget_gamepad_device():
    """Instructions to forget the gamepad device"""
    print("\n📱 MANUAL STEP REQUIRED:")
    print("1. Open System Preferences > Bluetooth")
    print("2. Find 'Gamepad-igs' in the list")
    print("3. Click the 'X' next to it to remove/forget the device")
    print("4. Confirm the removal")
    print("\nPress Enter when you've completed this step...")
    input()

def reconnect_gamepad():
    """Instructions to reconnect the gamepad"""
    print("\n🎮 MANUAL STEP REQUIRED:")
    print("1. Put your gamepad in pairing mode (usually hold a specific button combination)")
    print("2. In System Preferences > Bluetooth, click '+' to add a new device")
    print("3. Select your gamepad when it appears")
    print("4. Follow the pairing process")
    print("5. Make sure it shows as 'Connected' and the device type is correct")
    print("\nPress Enter when you've completed this step...")
    input()

def test_gamepad():
    """Test gamepad functionality"""
    print("\n🧪 Testing gamepad functionality...")
    
    # Check device type
    result = run_command("system_profiler SPBluetoothDataType | grep -A 10 'Gamepad-igs'", "Check device type")
    
    # Test pygame detection
    pygame_test = '''
import pygame
pygame.init()
pygame.joystick.init()
print(f'Joysticks detected: {pygame.joystick.get_count()}')
if pygame.joystick.get_count() > 0:
    for i in range(pygame.joystick.get_count()):
        j = pygame.joystick.Joystick(i)
        print(f'Joystick {i}: {j.get_name()}')
        print(f'  - Axes: {j.get_numaxes()}')
        print(f'  - Buttons: {j.get_numbuttons()}')
        print(f'  - Hats: {j.get_numhats()}')
else:
    print('No gamepads detected by pygame')
pygame.quit()
'''
    
    result = run_command(f"python3 -c \"{pygame_test}\"", "Test pygame gamepad detection")

def main():
    """Main fix process"""
    print("🎮 Gamepad Connection Fix Script")
    print("=" * 50)
    
    # Check current status
    print("\n1️⃣ Checking current status...")
    check_gamepad_status()
    
    # Reset Bluetooth
    print("\n2️⃣ Resetting Bluetooth module...")
    reset_bluetooth()
    
    # Forget device
    print("\n3️⃣ Forgetting the gamepad device...")
    forget_gamepad_device()
    
    # Reconnect device
    print("\n4️⃣ Reconnecting the gamepad...")
    reconnect_gamepad()
    
    # Test the fix
    print("\n5️⃣ Testing the fix...")
    test_gamepad()
    
    print("\n" + "=" * 50)
    print("🎯 Fix process completed!")
    print("\nIf the gamepad is still not working:")
    print("- Check if your gamepad has different modes (XInput, DInput, etc.)")
    print("- Try connecting via USB cable if available")
    print("- Check the manufacturer's website for Mac-specific drivers")
    print("- Verify the gamepad is compatible with macOS")

if __name__ == "__main__":
    main()