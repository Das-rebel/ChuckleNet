#!/usr/bin/env python3
"""
Gamepad Configuration and Testing Script
This script helps detect, configure, and test gamepad controllers on macOS.
"""

import sys
import time
import subprocess
import json
from typing import List, Dict, Any

def install_pygame():
    """Install pygame if not available"""
    try:
        import pygame
        return True
    except ImportError:
        print("Installing pygame...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pygame'], check=True)
        return True

def get_bluetooth_devices():
    """Get Bluetooth devices using system_profiler"""
    try:
        result = subprocess.run(['system_profiler', 'SPBluetoothDataType'], 
                              capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error getting Bluetooth devices: {e}")
        return ""

def find_gamepad_devices():
    """Find potential gamepad devices from Bluetooth output"""
    bluetooth_output = get_bluetooth_devices()
    gamepads = []
    
    lines = bluetooth_output.split('\n')
    for i, line in enumerate(lines):
        if any(keyword in line.lower() for keyword in ['gamepad', 'controller', 'joystick', 'xbox', 'playstation', 'nintendo']):
            # Look for device details in surrounding lines
            device_info = {}
            for j in range(max(0, i-5), min(len(lines), i+10)):
                if 'Address:' in lines[j]:
                    device_info['address'] = lines[j].split('Address:')[1].strip()
                elif 'Vendor ID:' in lines[j]:
                    device_info['vendor_id'] = lines[j].split('Vendor ID:')[1].strip()
                elif 'Product ID:' in lines[j]:
                    device_info['product_id'] = lines[j].split('Product ID:')[1].strip()
                elif 'Minor Type:' in lines[j]:
                    device_info['type'] = lines[j].split('Minor Type:')[1].strip()
            
            if device_info:
                device_info['name'] = line.strip()
                gamepads.append(device_info)
    
    return gamepads

def test_pygame_detection():
    """Test gamepad detection using pygame"""
    try:
        import pygame
        pygame.init()
        pygame.joystick.init()
        
        joystick_count = pygame.joystick.get_count()
        print(f"Pygame detected {joystick_count} joystick(s)")
        
        joysticks = []
        for i in range(joystick_count):
            joystick = pygame.joystick.Joystick(i)
            joystick.init()
            
            joystick_info = {
                'id': i,
                'name': joystick.get_name(),
                'axes': joystick.get_numaxes(),
                'buttons': joystick.get_numbuttons(),
                'hats': joystick.get_numhats(),
                'guid': joystick.get_guid()
            }
            joysticks.append(joystick_info)
            
            print(f"  Joystick {i}: {joystick_info['name']}")
            print(f"    - Axes: {joystick_info['axes']}")
            print(f"    - Buttons: {joystick_info['buttons']}")
            print(f"    - Hats: {joystick_info['hats']}")
            print(f"    - GUID: {joystick_info['guid']}")
        
        pygame.quit()
        return joysticks
    except Exception as e:
        print(f"Error testing pygame detection: {e}")
        return []

def test_gamepad_input(joystick_id=0, duration=10):
    """Test gamepad input for a specified duration"""
    try:
        import pygame
        pygame.init()
        pygame.joystick.init()
        
        if pygame.joystick.get_count() == 0:
            print("No joysticks detected by pygame")
            return
        
        joystick = pygame.joystick.Joystick(joystick_id)
        joystick.init()
        
        print(f"Testing gamepad input for {duration} seconds...")
        print("Press buttons and move sticks. Press Ctrl+C to stop early.")
        print("=" * 50)
        
        start_time = time.time()
        pygame.event.set_allowed([pygame.JOYBUTTONDOWN, pygame.JOYBUTTONUP, pygame.JOYAXISMOTION, pygame.JOYHATMOTION])
        
        while time.time() - start_time < duration:
            for event in pygame.event.get():
                if event.type == pygame.JOYBUTTONDOWN:
                    print(f"Button {event.button} pressed")
                elif event.type == pygame.JOYBUTTONUP:
                    print(f"Button {event.button} released")
                elif event.type == pygame.JOYAXISMOTION:
                    if abs(event.value) > 0.1:  # Only print significant movement
                        print(f"Axis {event.axis}: {event.value:.2f}")
                elif event.type == pygame.JOYHATMOTION:
                    if event.value != (0, 0):
                        print(f"Hat {event.hat}: {event.value}")
            
            time.sleep(0.01)
        
        pygame.quit()
        print("Gamepad test completed!")
        
    except KeyboardInterrupt:
        print("\nTest stopped by user")
        pygame.quit()
    except Exception as e:
        print(f"Error during gamepad test: {e}")

def check_macos_gamepad_support():
    """Check macOS gamepad support and configuration"""
    print("Checking macOS Gamepad Support...")
    print("=" * 40)
    
    # Check if Game Controller framework is available
    try:
        import objc
        from Foundation import NSBundle
        bundle = NSBundle.bundleWithPath_('/System/Library/Frameworks/GameController.framework')
        if bundle:
            print("✓ GameController framework available")
        else:
            print("✗ GameController framework not found")
    except ImportError:
        print("✗ PyObjC not available (needed for GameController framework)")
    
    # Check for gamepad-related processes
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        if 'GameController' in result.stdout:
            print("✓ GameController processes running")
        else:
            print("ℹ No GameController processes detected")
    except:
        pass

def provide_troubleshooting_tips():
    """Provide troubleshooting tips for gamepad issues"""
    print("\nTroubleshooting Tips:")
    print("=" * 20)
    print("1. Make sure your gamepad is properly paired via Bluetooth")
    print("2. Try disconnecting and reconnecting the gamepad")
    print("3. Check if the gamepad is in the correct mode (some have multiple modes)")
    print("4. Restart Bluetooth: System Preferences > Bluetooth > Turn Bluetooth Off/On")
    print("5. Reset Bluetooth module: Hold Shift+Option and click Bluetooth menu > Debug > Reset")
    print("6. Check if the gamepad is compatible with macOS")
    print("7. Try connecting via USB if available")
    print("8. Check System Preferences > Security & Privacy > Privacy > Input Monitoring")

def main():
    print("Gamepad Configuration and Testing Tool")
    print("=" * 40)
    
    # Install pygame if needed
    if not install_pygame():
        print("Failed to install pygame")
        return
    
    # Check macOS support
    check_macos_gamepad_support()
    
    # Find Bluetooth gamepad devices
    print("\nScanning for Bluetooth gamepad devices...")
    gamepads = find_gamepad_devices()
    
    if gamepads:
        print(f"Found {len(gamepads)} potential gamepad device(s):")
        for i, gamepad in enumerate(gamepads):
            print(f"  {i+1}. {gamepad.get('name', 'Unknown')}")
            print(f"     Address: {gamepad.get('address', 'Unknown')}")
            print(f"     Type: {gamepad.get('type', 'Unknown')}")
            print(f"     Vendor ID: {gamepad.get('vendor_id', 'Unknown')}")
            print(f"     Product ID: {gamepad.get('product_id', 'Unknown')}")
            print()
    else:
        print("No gamepad devices found in Bluetooth devices")
    
    # Test pygame detection
    print("Testing pygame gamepad detection...")
    joysticks = test_pygame_detection()
    
    if joysticks:
        print(f"\nPygame successfully detected {len(joysticks)} gamepad(s)")
        
        # Ask if user wants to test input
        try:
            response = input("\nWould you like to test gamepad input? (y/n): ").lower()
            if response == 'y':
                joystick_id = 0
                if len(joysticks) > 1:
                    try:
                        joystick_id = int(input(f"Which joystick to test? (0-{len(joysticks)-1}): "))
                    except ValueError:
                        joystick_id = 0
                
                duration = 10
                try:
                    duration = int(input("Test duration in seconds (default 10): ") or "10")
                except ValueError:
                    duration = 10
                
                test_gamepad_input(joystick_id, duration)
        except KeyboardInterrupt:
            print("\nSkipping input test")
    else:
        print("\nPygame did not detect any gamepads")
        print("This could mean:")
        print("- The gamepad is not properly connected")
        print("- The gamepad is not recognized as a HID device")
        print("- The gamepad needs to be in a specific mode")
    
    # Provide troubleshooting tips
    provide_troubleshooting_tips()

if __name__ == "__main__":
    main()