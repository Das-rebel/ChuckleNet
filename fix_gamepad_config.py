#!/usr/bin/env python3
"""
Gamepad Configuration Fix Script
This script helps fix gamepad recognition issues on macOS.
"""

import subprocess
import sys
import time

def run_command(cmd, description):
    """Run a command and return the result"""
    print(f"Running: {description}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(f"✓ {description} - Success")
            if result.stdout.strip():
                print(f"  Output: {result.stdout.strip()}")
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

def reset_bluetooth():
    """Reset Bluetooth module"""
    print("\n" + "="*50)
    print("RESETTING BLUETOOTH MODULE")
    print("="*50)
    
    # Turn off Bluetooth
    run_command("sudo pkill bluetoothd", "Killing Bluetooth daemon")
    time.sleep(2)
    
    # Reset Bluetooth module
    run_command("sudo kextunload -b com.apple.iokit.BroadcomBluetoothHostControllerUSBTransport", 
                "Unloading Bluetooth kernel extension")
    time.sleep(2)
    
    run_command("sudo kextload -b com.apple.iokit.BroadcomBluetoothHostControllerUSBTransport", 
                "Reloading Bluetooth kernel extension")
    time.sleep(2)
    
    # Start Bluetooth daemon
    run_command("sudo launchctl load /System/Library/LaunchDaemons/com.apple.bluetoothd.plist", 
                "Starting Bluetooth daemon")
    time.sleep(3)
    
    print("Bluetooth reset completed. Please wait for Bluetooth to restart...")

def forget_and_reconnect_device():
    """Guide user through forgetting and reconnecting the device"""
    print("\n" + "="*50)
    print("DEVICE RECONNECTION GUIDE")
    print("="*50)
    
    print("1. Open System Preferences > Bluetooth")
    print("2. Find your 'Gamepad-igs' device in the list")
    print("3. Click the 'X' next to it to remove/forget the device")
    print("4. Put your gamepad in pairing mode:")
    print("   - Usually involves holding a specific button combination")
    print("   - Check your gamepad manual for pairing instructions")
    print("   - Some gamepads need to be in a specific mode (XInput, DInput, etc.)")
    print("5. Click 'Set Up New Device' or the '+' button in Bluetooth preferences")
    print("6. Select your gamepad when it appears")
    print("7. Follow the pairing process")
    print("\nPress Enter when you've completed the reconnection process...")
    input()

def check_hid_devices():
    """Check HID devices after reconnection"""
    print("\n" + "="*50)
    print("CHECKING HID DEVICES")
    print("="*50)
    
    # Check for HID devices
    result = run_command("ioreg -p IOHID -w0 | grep -i 'game\\|controller\\|joystick' -A 5 -B 5", 
                        "Checking for HID gamepad devices")
    
    if result and result.stdout.strip():
        print("Found HID gamepad devices:")
        print(result.stdout)
    else:
        print("No HID gamepad devices found")
    
    # Check Bluetooth devices again
    result = run_command("system_profiler SPBluetoothDataType | grep -A 10 -B 2 'Gamepad\\|Controller'", 
                        "Checking Bluetooth gamepad devices")
    
    if result and result.stdout.strip():
        print("Bluetooth gamepad devices:")
        print(result.stdout)

def test_gamepad_after_fix():
    """Test gamepad functionality after fix"""
    print("\n" + "="*50)
    print("TESTING GAMEPAD AFTER FIX")
    print("="*50)
    
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
            
            # Test input
            print("\nTesting gamepad input for 5 seconds...")
            print("Press buttons and move sticks!")
            
            joystick = pygame.joystick.Joystick(0)
            joystick.init()
            
            start_time = time.time()
            pygame.event.set_allowed([pygame.JOYBUTTONDOWN, pygame.JOYBUTTONUP, pygame.JOYAXISMOTION])
            
            while time.time() - start_time < 5:
                for event in pygame.event.get():
                    if event.type == pygame.JOYBUTTONDOWN:
                        print(f"Button {event.button} pressed")
                    elif event.type == pygame.JOYAXISMOTION:
                        if abs(event.value) > 0.1:
                            print(f"Axis {event.axis}: {event.value:.2f}")
                time.sleep(0.01)
            
            print("Gamepad test completed!")
        else:
            print("No gamepads detected by pygame")
        
        pygame.quit()
        
    except ImportError:
        print("Pygame not available for testing")
    except Exception as e:
        print(f"Error testing gamepad: {e}")

def provide_alternative_solutions():
    """Provide alternative solutions if the fix doesn't work"""
    print("\n" + "="*50)
    print("ALTERNATIVE SOLUTIONS")
    print("="*50)
    
    print("If the gamepad still doesn't work, try these alternatives:")
    print()
    print("1. USB Connection:")
    print("   - Try connecting via USB cable if available")
    print("   - Some gamepads work better with USB")
    print()
    print("2. Third-party Drivers:")
    print("   - Install Xbox 360 Controller Driver for Mac")
    print("   - Install DS4Windows equivalent for Mac")
    print("   - Check if your gamepad manufacturer has Mac drivers")
    print()
    print("3. Game-specific Solutions:")
    print("   - Some games have built-in gamepad support")
    print("   - Use Steam's controller configuration")
    print("   - Try using a different gamepad")
    print()
    print("4. System Updates:")
    print("   - Update macOS to the latest version")
    print("   - Check for gamepad compatibility updates")
    print()
    print("5. Check Gamepad Mode:")
    print("   - Some gamepads have multiple modes (XInput, DInput, etc.)")
    print("   - Try switching between different modes")
    print("   - Check the gamepad manual for mode switching")

def main():
    print("Gamepad Configuration Fix Tool")
    print("="*40)
    print("This tool will help fix gamepad recognition issues on macOS")
    print()
    
    # Check current status
    print("Current gamepad status:")
    run_command("system_profiler SPBluetoothDataType | grep -A 5 'Gamepad-igs'", 
                "Checking current gamepad status")
    
    print("\nThe issue is that your gamepad is being recognized as an 'AppleTrackpad'")
    print("instead of a game controller. This needs to be fixed.")
    print()
    
    # Ask user what they want to do
    print("Choose an option:")
    print("1. Reset Bluetooth and reconnect gamepad (Recommended)")
    print("2. Just check current status")
    print("3. Show alternative solutions")
    print("4. Exit")
    
    try:
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            print("\nThis will reset your Bluetooth module and guide you through reconnecting.")
            confirm = input("Are you sure you want to proceed? (y/n): ").lower()
            if confirm == 'y':
                reset_bluetooth()
                forget_and_reconnect_device()
                check_hid_devices()
                test_gamepad_after_fix()
            else:
                print("Operation cancelled.")
        
        elif choice == "2":
            check_hid_devices()
            test_gamepad_after_fix()
        
        elif choice == "3":
            provide_alternative_solutions()
        
        elif choice == "4":
            print("Exiting...")
        
        else:
            print("Invalid choice. Exiting...")
    
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()