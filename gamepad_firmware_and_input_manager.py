#!/usr/bin/env python3
"""
Comprehensive Gamepad Firmware Update and Input Detection Manager
Handles firmware updates, device recognition, and real-time input monitoring
"""

import subprocess
import sys
import time
import json
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime

def run_command(cmd: str, description: str = "", timeout: int = 30) -> Tuple[bool, str, str]:
    """Run a command and return success, stdout, stderr"""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", f"Command timed out after {timeout}s"
    except Exception as e:
        return False, "", str(e)

def get_gamepad_info() -> Optional[Dict]:
    """Get detailed gamepad information from system"""
    success, output, _ = run_command(
        "system_profiler SPBluetoothDataType | grep -A 15 'Gamepad-igs'"
    )
    
    if not success or not output:
        return None
    
    info = {
        'name': 'Gamepad-igs',
        'address': None,
        'vendor_id': None,
        'product_id': None,
        'firmware_version': None,
        'device_type': None,
        'rssi': None,
        'connected': False
    }
    
    lines = output.split('\n')
    for line in lines:
        if 'Address:' in line:
            info['address'] = line.split('Address:')[1].strip()
        elif 'Vendor ID:' in line:
            vid = line.split('Vendor ID:')[1].strip()
            info['vendor_id'] = vid
        elif 'Product ID:' in line:
            pid = line.split('Product ID:')[1].strip()
            info['product_id'] = pid
        elif 'Firmware Version:' in line:
            info['firmware_version'] = line.split('Firmware Version:')[1].strip()
        elif 'Minor Type:' in line:
            info['device_type'] = line.split('Minor Type:')[1].strip()
        elif 'RSSI:' in line:
            info['rssi'] = line.split('RSSI:')[1].strip()
        elif 'Connected:' in line:
            info['connected'] = True
    
    return info

def check_firmware_update_availability(info: Dict) -> Dict:
    """Check if firmware update is available and provide instructions"""
    result = {
        'current_version': info.get('firmware_version'),
        'update_available': False,
        'update_method': None,
        'instructions': []
    }
    
    if not info.get('firmware_version'):
        result['instructions'].append("Firmware version not detected")
        return result
    
    # Check for manufacturer-specific update tools
    vendor_id = info.get('vendor_id', '').upper()
    
    # Vendor ID 0x1949 might be a generic gamepad
    # Most gamepads don't have macOS firmware update tools
    # But we can provide general guidance
    
    result['instructions'].extend([
        "Most gamepad firmware updates require:",
        "1. Windows PC with manufacturer software",
        "2. Manufacturer's mobile app",
        "3. USB connection (more reliable for updates)",
        "",
        "To check for updates:",
        f"- Current firmware: {info.get('firmware_version', 'Unknown')}",
        "- Search for your gamepad model + 'firmware update'",
        "- Check manufacturer's website or support page",
        "- Use manufacturer's official update tool if available"
    ])
    
    return result

def reset_bluetooth_connection():
    """Reset Bluetooth to fix device recognition"""
    print("\n🔄 Resetting Bluetooth connection...")
    
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
        success, stdout, stderr = run_command(cmd)
        if desc != "Waiting":
            status = "✅" if success else "⚠️"
            print(f"{status} {desc}")
    
    print("⏳ Waiting for Bluetooth to restart...")
    time.sleep(5)
    print("✅ Bluetooth reset complete")

def fix_device_recognition():
    """Guide user through fixing device recognition"""
    print("\n" + "="*60)
    print("🔧 FIXING DEVICE RECOGNITION")
    print("="*60)
    
    print("\nThe gamepad is being recognized as 'AppleTrackpad' instead of")
    print("'Game Controller'. This needs to be fixed for proper functionality.")
    
    print("\n📋 Manual Steps Required:")
    print("1. Open System Settings > Bluetooth")
    print("2. Find 'Gamepad-igs' in the device list")
    print("3. Click the 'info' (i) button or right-click the device")
    print("4. Click 'Remove' or 'Forget This Device'")
    print("5. Put your gamepad in pairing mode:")
    print("   - Usually involves holding a button combination")
    print("   - Check your gamepad manual")
    print("   - Some gamepads need to be in XInput mode")
    print("6. In System Settings > Bluetooth, click '+' to add device")
    print("7. Select your gamepad when it appears")
    print("8. Complete the pairing process")
    
    input("\n⏸️  Press Enter when you've completed these steps...")
    
    # Verify the fix
    print("\n🔍 Verifying device recognition...")
    info = get_gamepad_info()
    if info:
        if info.get('device_type') == 'Game Controller':
            print("✅ SUCCESS: Device is now recognized as Game Controller!")
            return True
        else:
            print(f"⚠️  Device type is still: {info.get('device_type')}")
            print("   You may need to try a different gamepad mode")
            return False
    else:
        print("❌ Could not detect gamepad. Make sure it's connected.")
        return False

def test_pygame_detection():
    """Test gamepad detection with pygame"""
    print("\n🎮 Testing pygame gamepad detection...")
    
    # Check if pygame is installed
    try:
        import pygame
    except ImportError:
        print("📦 Installing pygame...")
        success, _, _ = run_command(f"{sys.executable} -m pip install pygame")
        if not success:
            print("❌ Failed to install pygame")
            return None
        import pygame
    
    pygame.init()
    pygame.joystick.init()
    
    count = pygame.joystick.get_count()
    print(f"Found {count} joystick(s)")
    
    if count == 0:
        return None
    
    joysticks = []
    for i in range(count):
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
        
        print(f"\n  Joystick {i}: {joystick_info['name']}")
        print(f"    - Axes: {joystick_info['axes']}")
        print(f"    - Buttons: {joystick_info['buttons']}")
        print(f"    - Hats: {joystick_info['hats']}")
        print(f"    - GUID: {joystick_info['guid']}")
    
    return joysticks

def monitor_gamepad_input(joystick_id: int = 0, duration: int = 30):
    """Real-time gamepad input monitoring with enhanced detection"""
    try:
        import pygame
    except ImportError:
        print("❌ Pygame not available. Install with: pip install pygame")
        return
    
    pygame.init()
    pygame.joystick.init()
    
    if pygame.joystick.get_count() == 0:
        print("❌ No gamepads detected")
        return
    
    joystick = pygame.joystick.Joystick(joystick_id)
    joystick.init()
    
    print(f"\n🎮 Real-time Input Monitoring")
    print(f"Gamepad: {joystick.get_name()}")
    print(f"Duration: {duration} seconds")
    print("Press buttons and move sticks. Press Ctrl+C to stop early.")
    print("="*60)
    
    # Initialize state tracking
    axis_states = [0.0] * joystick.get_numaxes()
    button_states = [False] * joystick.get_numbuttons()
    hat_states = [(0, 0)] * joystick.get_numhats()
    
    # Dead zones for analog sticks
    dead_zone = 0.1
    
    start_time = time.time()
    event_count = {'buttons': 0, 'axes': 0, 'hats': 0}
    
    pygame.event.set_allowed([
        pygame.JOYBUTTONDOWN, 
        pygame.JOYBUTTONUP, 
        pygame.JOYAXISMOTION, 
        pygame.JOYHATMOTION,
        pygame.QUIT
    ])
    
    try:
        while time.time() - start_time < duration:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    break
                
                elif event.type == pygame.JOYBUTTONDOWN:
                    button_states[event.button] = True
                    event_count['buttons'] += 1
                    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                    print(f"[{timestamp}] 🔘 Button {event.button} PRESSED")
                
                elif event.type == pygame.JOYBUTTONUP:
                    button_states[event.button] = False
                    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                    print(f"[{timestamp}] 🔘 Button {event.button} RELEASED")
                
                elif event.type == pygame.JOYAXISMOTION:
                    axis_id = event.axis
                    value = event.value
                    
                    # Only report if value changed significantly
                    if abs(value - axis_states[axis_id]) > 0.05:
                        axis_states[axis_id] = value
                        if abs(value) > dead_zone:
                            event_count['axes'] += 1
                            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                            axis_name = f"Axis {axis_id}"
                            if axis_id < 2:
                                axis_name = f"Left Stick {'X' if axis_id == 0 else 'Y'}"
                            elif axis_id < 4:
                                axis_name = f"Right Stick {'X' if axis_id == 2 else 'Y'}"
                            print(f"[{timestamp}] 🕹️  {axis_name}: {value:+.3f}")
                
                elif event.type == pygame.JOYHATMOTION:
                    hat_id = event.hat
                    value = event.value
                    
                    if value != hat_states[hat_id]:
                        hat_states[hat_id] = value
                        if value != (0, 0):
                            event_count['hats'] += 1
                            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                            print(f"[{timestamp}] 🎯 Hat {hat_id}: {value}")
            
            time.sleep(0.001)  # Small delay to prevent CPU spinning
        
        print("\n" + "="*60)
        print("📊 Input Summary:")
        print(f"  Button events: {event_count['buttons']}")
        print(f"  Axis events: {event_count['axes']}")
        print(f"  Hat events: {event_count['hats']}")
        print(f"  Total events: {sum(event_count.values())}")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Monitoring stopped by user")
    
    pygame.quit()

def save_gamepad_config(info: Dict, joysticks: List[Dict]):
    """Save gamepad configuration for future reference"""
    config = {
        'timestamp': datetime.now().isoformat(),
        'device_info': info,
        'joystick_info': joysticks
    }
    
    config_file = 'gamepad_config.json'
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"\n💾 Configuration saved to {config_file}")

def main():
    """Main gamepad management interface"""
    print("="*60)
    print("🎮 GAMEPAD FIRMWARE & INPUT DETECTION MANAGER")
    print("="*60)
    
    # Get current gamepad info
    print("\n1️⃣ Checking gamepad status...")
    info = get_gamepad_info()
    
    if not info:
        print("❌ No gamepad detected. Please connect your gamepad.")
        return
    
    print(f"\n📱 Device Information:")
    print(f"  Name: {info.get('name', 'Unknown')}")
    print(f"  Address: {info.get('address', 'Unknown')}")
    print(f"  Vendor ID: {info.get('vendor_id', 'Unknown')}")
    print(f"  Product ID: {info.get('product_id', 'Unknown')}")
    print(f"  Firmware Version: {info.get('firmware_version', 'Unknown')}")
    print(f"  Device Type: {info.get('device_type', 'Unknown')}")
    print(f"  Connected: {'✅' if info.get('connected') else '❌'}")
    
    # Check firmware update availability
    print("\n2️⃣ Checking firmware update information...")
    firmware_info = check_firmware_update_availability(info)
    print(f"\n  Current Firmware: {firmware_info['current_version']}")
    print("\n  Firmware Update Instructions:")
    for instruction in firmware_info['instructions']:
        print(f"    {instruction}")
    
    # Check device recognition
    device_type_ok = info.get('device_type') == 'Game Controller'
    
    if not device_type_ok:
        print("\n⚠️  Device recognition issue detected!")
        print("   The gamepad is recognized as 'AppleTrackpad' instead of 'Game Controller'")
        
        response = input("\nWould you like to fix device recognition? (y/n): ").lower()
        if response == 'y':
            # Option to reset Bluetooth
            reset_bt = input("Reset Bluetooth first? (y/n): ").lower()
            if reset_bt == 'y':
                reset_bluetooth_connection()
            
            # Fix device recognition
            if fix_device_recognition():
                # Re-check info
                info = get_gamepad_info()
                device_type_ok = info.get('device_type') == 'Game Controller'
    
    # Test pygame detection
    print("\n3️⃣ Testing gamepad detection...")
    joysticks = test_pygame_detection()
    
    if not joysticks:
        print("\n❌ Gamepad not detected by pygame")
        print("   This usually means:")
        print("   - Device recognition issue (fix above)")
        print("   - Gamepad needs to be in correct mode")
        print("   - Driver issues")
        return
    
    # Save configuration
    save_gamepad_config(info, joysticks)
    
    # Real-time input monitoring
    print("\n4️⃣ Real-time Input Monitoring")
    response = input("Would you like to test gamepad input? (y/n): ").lower()
    if response == 'y':
        joystick_id = 0
        if len(joysticks) > 1:
            try:
                joystick_id = int(input(f"Which joystick? (0-{len(joysticks)-1}): ") or "0")
            except ValueError:
                joystick_id = 0
        
        duration = 30
        try:
            duration = int(input("Test duration in seconds (default 30): ") or "30")
        except ValueError:
            duration = 30
        
        monitor_gamepad_input(joystick_id, duration)
    
    print("\n" + "="*60)
    print("✅ Gamepad management complete!")
    print("="*60)

if __name__ == "__main__":
    main()
