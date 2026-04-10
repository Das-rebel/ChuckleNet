#!/usr/bin/env python3
"""
macOS Gamepad Configuration Tool (joy.cpl equivalent)
Helps configure and test gamepad connections on macOS
"""

import subprocess
import sys
import time
import json
import os
from typing import Dict, List, Optional, Tuple

try:
    import pygame
    HAS_PYGAME = True
except ImportError:
    HAS_PYGAME = False
    print("⚠️  pygame not installed - some features will be limited")
    print("   Install with: pip3 install pygame")

class GamepadConfigTool:
    """macOS Gamepad Configuration Tool - equivalent to Windows joy.cpl"""
    
    def __init__(self):
        self.gamepad_info = {}
        self.bluetooth_devices = []
        self.pygame_joysticks = []
        
    def get_bluetooth_devices(self) -> List[Dict]:
        """Get all Bluetooth devices"""
        result = subprocess.run(
            ["system_profiler", "SPBluetoothDataType"],
            capture_output=True, text=True
        )
        
        devices = []
        current_device = None
        
        for line in result.stdout.split('\n'):
            line = line.strip()
            if not line or line.startswith('Bluetooth'):
                continue
            
            # Device name
            if ':' in line and not line.startswith(' '):
                if current_device:
                    devices.append(current_device)
                current_device = {
                    'name': line.split(':')[0].strip(),
                    'details': {}
                }
            elif current_device and ':' in line:
                key = line.split(':')[0].strip()
                value = ':'.join(line.split(':')[1:]).strip()
                current_device['details'][key] = value
        
        if current_device:
            devices.append(current_device)
        
        self.bluetooth_devices = devices
        return devices
    
    def find_gamepad_devices(self) -> List[Dict]:
        """Find potential gamepad devices"""
        gamepads = []
        
        for device in self.bluetooth_devices:
            name_lower = device['name'].lower()
            details_str = ' '.join(device['details'].values()).lower()
            
            # Check for gamepad-related keywords
            keywords = ['gamepad', 'controller', 'joystick', 'xbox', 'playstation', 'ps', 'nintendo', 'switch']
            if any(keyword in name_lower or keyword in details_str for keyword in keywords):
                device_type = device['details'].get('Minor Type', 'Unknown')
                gamepads.append({
                    'name': device['name'],
                    'type': device_type,
                    'details': device['details'],
                    'connected': 'Connected: Yes' in str(device['details']),
                    'is_game_controller': 'Game Controller' in device_type
                })
        
        return gamepads
    
    def check_pygame_detection(self) -> List[Dict]:
        """Check if pygame can detect gamepads"""
        if not HAS_PYGAME:
            return []
        
        pygame.init()
        pygame.joystick.init()
        
        joysticks = []
        count = pygame.joystick.get_count()
        
        for i in range(count):
            try:
                joy = pygame.joystick.Joystick(i)
                joy.init()
                joysticks.append({
                    'id': i,
                    'name': joy.get_name(),
                    'axes': joy.get_numaxes(),
                    'buttons': joy.get_numbuttons(),
                    'hats': joy.get_numhats(),
                    'guid': joy.get_guid() if hasattr(joy, 'get_guid') else 'N/A'
                })
            except Exception as e:
                print(f"   Error initializing joystick {i}: {e}")
        
        self.pygame_joysticks = joysticks
        return joysticks
    
    def get_hid_devices(self) -> List[Dict]:
        """Get HID devices using ioreg"""
        result = subprocess.run(
            ["ioreg", "-p", "IOHID", "-w0", "-l"],
            capture_output=True, text=True
        )
        
        devices = []
        current_device = {}
        
        for line in result.stdout.split('\n'):
            if '+-o' in line and 'IOHID' in line:
                if current_device:
                    devices.append(current_device)
                current_device = {'name': line.split('+-o')[1].strip()}
            elif 'Product' in line and '=' in line:
                current_device['product'] = line.split('=')[1].strip().strip('"')
            elif 'VendorID' in line:
                current_device['vendor_id'] = line.split('=')[1].strip()
            elif 'ProductID' in line:
                current_device['product_id'] = line.split('=')[1].strip()
        
        if current_device:
            devices.append(current_device)
        
        return devices
    
    def test_gamepad_input(self, joystick_id: int = 0, duration: int = 30):
        """Test gamepad input (like joy.cpl test)"""
        if not HAS_PYGAME:
            print("❌ pygame required for input testing")
            print("   Install with: pip3 install pygame")
            return False
        
        pygame.init()
        pygame.joystick.init()
        
        count = pygame.joystick.get_count()
        if count == 0:
            print("❌ No gamepads detected by pygame")
            return False
        
        if joystick_id >= count:
            print(f"❌ Invalid joystick ID: {joystick_id} (only {count} available)")
            return False
        
        joy = pygame.joystick.Joystick(joystick_id)
        joy.init()
        
        print(f"\n{'='*60}")
        print(f"🎮 TESTING GAMEPAD: {joy.get_name()}")
        print(f"{'='*60}")
        print(f"   Buttons: {joy.get_numbuttons()}")
        print(f"   Axes: {joy.get_numaxes()}")
        print(f"   Hats: {joy.get_numhats()}")
        print(f"\n📋 Test will run for {duration} seconds")
        print("   - Press buttons and move sticks")
        print("   - Press Ctrl+C to stop early")
        print(f"{'='*60}\n")
        
        pygame.event.set_allowed([
            pygame.JOYBUTTONDOWN,
            pygame.JOYBUTTONUP,
            pygame.JOYAXISMOTION,
            pygame.JOYHATMOTION,
            pygame.QUIT
        ])
        
        button_states = [False] * joy.get_numbuttons()
        axis_values = [0.0] * joy.get_numaxes()
        hat_states = [(0, 0)] * joy.get_numhats()
        
        start_time = time.time()
        events_count = 0
        
        try:
            while time.time() - start_time < duration:
                for event in pygame.event.get():
                    events_count += 1
                    
                    if event.type == pygame.JOYBUTTONDOWN:
                        button_states[event.button] = True
                        print(f"🔘 Button {event.button} PRESSED")
                    
                    elif event.type == pygame.JOYBUTTONUP:
                        button_states[event.button] = False
                        print(f"🔘 Button {event.button} RELEASED")
                    
                    elif event.type == pygame.JOYAXISMOTION:
                        old_value = axis_values[event.axis]
                        axis_values[event.axis] = event.value
                        if abs(event.value - old_value) > 0.05:
                            axis_name = ['X', 'Y', 'Z', 'RX', 'RY', 'RZ'][event.axis] if event.axis < 6 else f'Axis{event.axis}'
                            print(f"🕹️  {axis_name}: {event.value:+.3f}")
                    
                    elif event.type == pygame.JOYHATMOTION:
                        hat_states[event.hat] = event.value
                        if event.value != (0, 0):
                            print(f"🎯 Hat {event.hat}: {event.value}")
                
                time.sleep(0.01)
            
            print(f"\n✅ Test completed!")
            print(f"   Events captured: {events_count}")
            print(f"\n📊 Final State:")
            print(f"   Buttons pressed: {sum(button_states)}")
            print(f"   Active axes: {sum(1 for v in axis_values if abs(v) > 0.1)}")
            
            return True
            
        except KeyboardInterrupt:
            print("\n\n⏹️  Test stopped by user")
            return True
        finally:
            pygame.quit()
    
    def show_device_properties(self, device_name: str):
        """Show detailed properties of a device (like joy.cpl properties)"""
        print(f"\n{'='*60}")
        print(f"📋 DEVICE PROPERTIES: {device_name}")
        print(f"{'='*60}\n")
        
        # Find device in Bluetooth
        for device in self.bluetooth_devices:
            if device['name'] == device_name:
                print("📡 Bluetooth Information:")
                for key, value in device['details'].items():
                    print(f"   {key}: {value}")
                print()
        
        # Check HID devices
        hid_devices = self.get_hid_devices()
        for hid in hid_devices:
            if device_name.lower() in str(hid.get('product', '')).lower():
                print("🔌 HID Information:")
                for key, value in hid.items():
                    print(f"   {key}: {value}")
                print()
        
        # Check pygame detection
        if HAS_PYGAME:
            pygame.init()
            pygame.joystick.init()
            for i in range(pygame.joystick.get_count()):
                joy = pygame.joystick.Joystick(i)
                if device_name.lower() in joy.get_name().lower():
                    joy.init()
                    print("🎮 Pygame Detection:")
                    print(f"   Name: {joy.get_name()}")
                    print(f"   GUID: {joy.get_guid() if hasattr(joy, 'get_guid') else 'N/A'}")
                    print(f"   Axes: {joy.get_numaxes()}")
                    print(f"   Buttons: {joy.get_numbuttons()}")
                    print(f"   Hats: {joy.get_numhats()}")
                    print()
                    pygame.quit()
                    break
    
    def show_main_menu(self):
        """Show main menu (like joy.cpl interface)"""
        print("\n" + "="*60)
        print("🎮 GAMEPAD CONFIGURATION TOOL (macOS)")
        print("   (Equivalent to Windows joy.cpl)")
        print("="*60)
        
        # Refresh device info
        print("\n1️⃣ Scanning for devices...")
        self.get_bluetooth_devices()
        gamepads = self.find_gamepad_devices()
        
        if gamepads:
            print(f"   ✅ Found {len(gamepads)} potential gamepad device(s):")
            for i, gp in enumerate(gamepads):
                status = "✅ Connected" if gp['connected'] else "❌ Disconnected"
                recognition = "✅ Game Controller" if gp['is_game_controller'] else "❌ Misrecognized"
                print(f"      [{i+1}] {gp['name']}")
                print(f"          Status: {status}")
                print(f"          Type: {gp['type']} ({recognition})")
        else:
            print("   ⚠️  No gamepad devices found in Bluetooth")
        
        # Check pygame detection
        if HAS_PYGAME:
            joysticks = self.check_pygame_detection()
            if joysticks:
                print(f"\n   ✅ Pygame detected {len(joysticks)} gamepad(s):")
                for js in joysticks:
                    print(f"      - {js['name']} (ID: {js['id']})")
            else:
                print("\n   ❌ Pygame cannot detect any gamepads")
        
        # Menu options
        print("\n" + "="*60)
        print("📋 MENU OPTIONS:")
        print("="*60)
        print("   1. Test Gamepad Input (like joy.cpl test)")
        print("   2. Show Device Properties")
        print("   3. Scan for Gamepads")
        print("   4. Troubleshooting Guide")
        print("   5. Exit")
        print("="*60)
    
    def show_troubleshooting(self):
        """Show troubleshooting guide"""
        print("\n" + "="*60)
        print("🔧 TROUBLESHOOTING GUIDE")
        print("="*60)
        
        gamepads = self.find_gamepad_devices()
        
        if not gamepads:
            print("\n❌ PROBLEM: No gamepad found")
            print("\n📋 SOLUTIONS:")
            print("   1. Make sure gamepad is powered on")
            print("   2. Put gamepad in pairing mode:")
            print("      - Usually: Hold Power + Home/Share buttons")
            print("      - Check your gamepad manual")
            print("   3. Open System Settings > Bluetooth")
            print("   4. Look for your gamepad in the list")
            print("   5. Click 'Connect' if it appears")
            return
        
        for gp in gamepads:
            print(f"\n📱 Device: {gp['name']}")
            
            if not gp['connected']:
                print("   ❌ PROBLEM: Device not connected")
                print("\n   📋 SOLUTIONS:")
                print("      1. Open System Settings > Bluetooth")
                print(f"      2. Find '{gp['name']}' and click 'Connect'")
                print("      3. If not visible, put gamepad in pairing mode")
                continue
            
            if not gp['is_game_controller']:
                print(f"   ❌ PROBLEM: Misrecognized as '{gp['type']}' instead of 'Game Controller'")
                print("\n   📋 SOLUTIONS:")
                print("      1. DISCONNECT in System Settings > Bluetooth")
                print("      2. FORGET the device (click 'X' or 'Remove')")
                print("      3. Check if gamepad has mode switch (X/D/S/M)")
                print("         - Put it in XInput mode (X) if available")
                print("      4. Put gamepad in pairing mode")
                print("      5. RE-PAIR as new device")
                print("      6. Check device type - should show 'Game Controller'")
                print("\n   💡 Alternative: Use input mapper even if misrecognized:")
                print("      python3 gamepad_input_mapper_advanced.py")
                continue
            
            if gp['is_game_controller'] and gp['connected']:
                print("   ✅ Device is connected and recognized correctly!")
                
                # Check pygame detection
                if HAS_PYGAME:
                    joysticks = self.check_pygame_detection()
                    if not joysticks:
                        print("   ⚠️  But pygame cannot detect it")
                        print("\n   📋 SOLUTIONS:")
                        print("      1. Check System Settings > Privacy > Input Monitoring")
                        print("         - Make sure Terminal/Python has access")
                        print("      2. Restart your computer")
                        print("      3. Try USB connection if available")
                        print("      4. Use: python3 gamepad_input_mapper_advanced.py")
    
    def run(self):
        """Run the configuration tool"""
        while True:
            self.show_main_menu()
            
            try:
                choice = input("\nEnter choice (1-5): ").strip()
                
                if choice == '1':
                    if not HAS_PYGAME:
                        print("\n❌ pygame required for testing")
                        print("   Install with: pip3 install pygame")
                        input("\nPress Enter to continue...")
                        continue
                    
                    joysticks = self.check_pygame_detection()
                    if not joysticks:
                        print("\n❌ No gamepads detected by pygame")
                        print("   Try troubleshooting first (option 4)")
                        input("\nPress Enter to continue...")
                        continue
                    
                    print(f"\nAvailable gamepads:")
                    for js in joysticks:
                        print(f"   [{js['id']}] {js['name']}")
                    
                    try:
                        joy_id = int(input("\nEnter gamepad ID to test (0): ") or "0")
                        duration = int(input("Test duration in seconds (30): ") or "30")
                        self.test_gamepad_input(joy_id, duration)
                    except ValueError:
                        print("❌ Invalid input")
                    except KeyboardInterrupt:
                        print("\n⏹️  Cancelled")
                    
                    input("\nPress Enter to continue...")
                
                elif choice == '2':
                    gamepads = self.find_gamepad_devices()
                    if not gamepads:
                        print("\n❌ No gamepad devices found")
                        input("\nPress Enter to continue...")
                        continue
                    
                    print("\nAvailable devices:")
                    for i, gp in enumerate(gamepads):
                        print(f"   [{i+1}] {gp['name']}")
                    
                    try:
                        idx = int(input("\nEnter device number: ")) - 1
                        if 0 <= idx < len(gamepads):
                            self.show_device_properties(gamepads[idx]['name'])
                        else:
                            print("❌ Invalid device number")
                    except ValueError:
                        print("❌ Invalid input")
                    
                    input("\nPress Enter to continue...")
                
                elif choice == '3':
                    print("\n🔄 Scanning for gamepads...")
                    self.get_bluetooth_devices()
                    gamepads = self.find_gamepad_devices()
                    if gamepads:
                        print(f"\n✅ Found {len(gamepads)} gamepad(s):")
                        for gp in gamepads:
                            status = "✅" if gp['connected'] else "❌"
                            print(f"   {status} {gp['name']} - {gp['type']}")
                    else:
                        print("\n❌ No gamepads found")
                    
                    input("\nPress Enter to continue...")
                
                elif choice == '4':
                    self.show_troubleshooting()
                    input("\nPress Enter to continue...")
                
                elif choice == '5':
                    print("\n👋 Goodbye!")
                    break
                
                else:
                    print("❌ Invalid choice")
                    input("\nPress Enter to continue...")
            
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                import traceback
                traceback.print_exc()
                input("\nPress Enter to continue...")

if __name__ == "__main__":
    tool = GamepadConfigTool()
    tool.run()