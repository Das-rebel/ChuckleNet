#!/usr/bin/env python3
"""
Force Gamepad Recognition Script
This script attempts to force macOS to recognize the gamepad as a proper HID device
without requiring reconnection.
"""

import subprocess
import sys
import time
import os

def run_command(cmd, description, timeout=30):
    """Run a command and return the result"""
    print(f"Running: {description}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        if result.returncode == 0:
            print(f"✓ {description} - Success")
            if result.stdout.strip():
                print(f"  Output: {result.stdout.strip()}")
            return result
        else:
            print(f"✗ {description} - Failed")
            if result.stderr.strip():
                print(f"  Error: {result.stderr.strip()}")
            return result
    except subprocess.TimeoutExpired:
        print(f"✗ {description} - Timeout")
        return None
    except Exception as e:
        print(f"✗ {description} - Exception: {e}")
        return None

def check_current_hid_devices():
    """Check all HID devices currently registered"""
    print("\n" + "="*60)
    print("CHECKING CURRENT HID DEVICES")
    print("="*60)
    
    # Get all HID devices
    result = run_command("ioreg -p IOHID -w0", "Getting all HID devices")
    
    if result and result.stdout:
        # Look for gamepad-related devices
        lines = result.stdout.split('\n')
        gamepad_devices = []
        
        for i, line in enumerate(lines):
            if any(keyword in line.lower() for keyword in ['game', 'controller', 'joystick', 'button', 'axis']):
                # Get context around this line
                start = max(0, i-3)
                end = min(len(lines), i+8)
                context = '\n'.join(lines[start:end])
                gamepad_devices.append(context)
        
        if gamepad_devices:
            print("Found potential gamepad-related HID devices:")
            for i, device in enumerate(gamepad_devices):
                print(f"\n--- Device {i+1} ---")
                print(device)
        else:
            print("No gamepad-related HID devices found")
    
    return result

def check_bluetooth_hid_services():
    """Check Bluetooth HID services"""
    print("\n" + "="*60)
    print("CHECKING BLUETOOTH HID SERVICES")
    print("="*60)
    
    result = run_command("system_profiler SPBluetoothDataType | grep -A 20 -B 5 'HID'", 
                        "Checking Bluetooth HID services")
    
    if result and result.stdout:
        print("Bluetooth HID services found:")
        print(result.stdout)
    else:
        print("No Bluetooth HID services found")

def try_force_hid_recognition():
    """Try to force HID recognition of the gamepad"""
    print("\n" + "="*60)
    print("ATTEMPTING TO FORCE HID RECOGNITION")
    print("="*60)
    
    # Method 1: Reset HID manager
    print("Method 1: Resetting HID Manager...")
    run_command("sudo kextunload -b com.apple.iokit.IOHIDFamily", 
                "Unloading HID family kernel extension")
    time.sleep(2)
    run_command("sudo kextload -b com.apple.iokit.IOHIDFamily", 
                "Reloading HID family kernel extension")
    time.sleep(3)
    
    # Method 2: Reset Bluetooth HID profile
    print("\nMethod 2: Resetting Bluetooth HID profile...")
    run_command("sudo pkill -f bluetoothd", "Killing Bluetooth daemon")
    time.sleep(2)
    run_command("sudo launchctl load /System/Library/LaunchDaemons/com.apple.bluetoothd.plist", 
                "Restarting Bluetooth daemon")
    time.sleep(3)
    
    # Method 3: Force HID device rescan
    print("\nMethod 3: Forcing HID device rescan...")
    run_command("sudo kextunload -b com.apple.iokit.BroadcomBluetoothHostControllerUSBTransport", 
                "Unloading Bluetooth transport")
    time.sleep(2)
    run_command("sudo kextload -b com.apple.iokit.BroadcomBluetoothHostControllerUSBTransport", 
                "Reloading Bluetooth transport")
    time.sleep(3)

def check_gamepad_after_force():
    """Check if gamepad is now recognized after forcing recognition"""
    print("\n" + "="*60)
    print("CHECKING GAMEPAD AFTER FORCE RECOGNITION")
    print("="*60)
    
    # Check Bluetooth status
    result = run_command("system_profiler SPBluetoothDataType | grep -A 10 'Gamepad-igs'", 
                        "Checking gamepad Bluetooth status")
    
    if result and result.stdout:
        print("Gamepad Bluetooth status:")
        print(result.stdout)
        
        # Check if type changed
        if "Game Controller" in result.stdout:
            print("✓ SUCCESS: Gamepad now recognized as Game Controller!")
        elif "AppleTrackpad" in result.stdout:
            print("✗ Still recognized as AppleTrackpad")
        else:
            print("? Unknown recognition status")
    
    # Check HID devices
    check_current_hid_devices()
    
    # Test with pygame
    test_pygame_detection()

def test_pygame_detection():
    """Test gamepad detection with pygame"""
    print("\n" + "="*60)
    print("TESTING PYGAME DETECTION")
    print("="*60)
    
    try:
        import pygame
        pygame.init()
        pygame.joystick.init()
        
        joystick_count = pygame.joystick.get_count()
        print(f"Pygame detected {joystick_count} joystick(s)")
        
        if joystick_count > 0:
            for i in range(joystick_count):
                joystick = pygame.joystick.Joystick(i)
                print(f"Joystick {i}: {joystick.get_name()}")
                print(f"  - Axes: {joystick.get_numaxes()}")
                print(f"  - Buttons: {joystick.get_numbuttons()}")
                print(f"  - Hats: {joystick.get_numhats()}")
                print(f"  - GUID: {joystick.get_guid()}")
            
            print("\n✓ SUCCESS: Gamepad is now detected by pygame!")
            return True
        else:
            print("✗ No gamepads detected by pygame")
            return False
        
        pygame.quit()
        
    except ImportError:
        print("Pygame not available for testing")
        return False
    except Exception as e:
        print(f"Error testing pygame detection: {e}")
        return False

def try_alternative_detection_methods():
    """Try alternative methods to detect the gamepad"""
    print("\n" + "="*60)
    print("TRYING ALTERNATIVE DETECTION METHODS")
    print("="*60)
    
    # Method 1: Check using different system tools
    print("Method 1: Using hidutil...")
    result = run_command("hidutil list", "Listing HID devices with hidutil")
    
    # Method 2: Check using system_profiler with different options
    print("\nMethod 2: Using system_profiler with different options...")
    result = run_command("system_profiler SPUSBDataType SPBluetoothDataType | grep -i 'game\\|controller\\|joystick' -A 5 -B 5", 
                        "Checking all device types for gamepad")
    
    # Method 3: Check using ioreg with different parameters
    print("\nMethod 3: Using ioreg with different parameters...")
    result = run_command("ioreg -p IOHID -w0 -l | grep -i 'game\\|controller\\|joystick\\|button\\|axis' -A 3 -B 3", 
                        "Searching ioreg for gamepad-related terms")
    
    # Method 4: Check using lsusb equivalent
    print("\nMethod 4: Checking USB devices...")
    result = run_command("system_profiler SPUSBDataType | grep -A 10 -B 5 '1949\\|0402'", 
                        "Looking for gamepad in USB devices")

def create_hid_override():
    """Create a HID override to force gamepad recognition"""
    print("\n" + "="*60)
    print("CREATING HID OVERRIDE")
    print("="*60)
    
    # Create a HID override file
    override_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>VendorID</key>
    <integer>6473</integer>
    <key>ProductID</key>
    <integer>1026</integer>
    <key>HIDDefaultBehavior</key>
    <string>GameController</string>
    <key>HIDDefaultBehaviorName</key>
    <string>Game Controller</string>
</dict>
</plist>"""
    
    # Write override file
    override_path = "/tmp/gamepad_override.plist"
    try:
        with open(override_path, 'w') as f:
            f.write(override_content)
        print(f"Created HID override file: {override_path}")
        
        # Try to apply the override
        result = run_command(f"sudo cp {override_path} /Library/Preferences/SystemConfiguration/com.apple.iokit.IOHIDManager.plist", 
                            "Applying HID override")
        
        if result and result.returncode == 0:
            print("✓ HID override applied successfully")
            print("You may need to restart for changes to take effect")
        else:
            print("✗ Failed to apply HID override")
            
    except Exception as e:
        print(f"Error creating HID override: {e}")

def main():
    print("Force Gamepad Recognition Tool")
    print("="*40)
    print("This tool attempts to force macOS to recognize your gamepad")
    print("as a proper HID device without requiring reconnection.")
    print()
    
    # Check current status
    print("Current gamepad status:")
    result = run_command("system_profiler SPBluetoothDataType | grep -A 5 'Gamepad-igs'", 
                        "Checking current gamepad status")
    
    if result and result.stdout:
        print(result.stdout)
        if "AppleTrackpad" in result.stdout:
            print("\n❌ Problem: Gamepad is recognized as AppleTrackpad")
        elif "Game Controller" in result.stdout:
            print("\n✅ Good: Gamepad is recognized as Game Controller")
    
    print("\nChoose an approach:")
    print("1. Force HID recognition (reset HID manager)")
    print("2. Try alternative detection methods")
    print("3. Create HID override file")
    print("4. Check current HID devices")
    print("5. All of the above")
    
    try:
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == "1":
            try_force_hid_recognition()
            check_gamepad_after_force()
        
        elif choice == "2":
            try_alternative_detection_methods()
        
        elif choice == "3":
            create_hid_override()
        
        elif choice == "4":
            check_current_hid_devices()
            check_bluetooth_hid_services()
        
        elif choice == "5":
            check_current_hid_devices()
            check_bluetooth_hid_services()
            try_force_hid_recognition()
            try_alternative_detection_methods()
            create_hid_override()
            check_gamepad_after_force()
        
        else:
            print("Invalid choice. Exiting...")
    
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()