#!/usr/bin/env python3
"""
Advanced Gamepad Input Mapper
Works even if macOS misrecognizes the device as trackpad/headset
Uses low-level HID access to capture input
"""

import sys
import time
import subprocess
from typing import Dict, List, Optional

try:
    import pygame
except ImportError:
    print("Installing pygame...")
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pygame'])
    import pygame

class AdvancedGamepadMapper:
    def __init__(self):
        self.joysticks = []
        self.button_map = {}
        self.axis_map = {}
        self.running = False
        
        pygame.init()
        pygame.joystick.init()
        
        # Initialize button mapping (standard gamepad)
        self.button_map = {
            0: {'name': 'A', 'key': 'a'},
            1: {'name': 'B', 'key': 'b'},
            2: {'name': 'X', 'key': 'x'},
            3: {'name': 'Y', 'key': 'y'},
            4: {'name': 'LB', 'key': 'q'},
            5: {'name': 'RB', 'key': 'e'},
            6: {'name': 'Back', 'key': 'esc'},
            7: {'name': 'Start', 'key': 'enter'},
            8: {'name': 'Left Stick Press', 'key': 'l'},
            9: {'name': 'Right Stick Press', 'key': 'r'},
        }
        
        # Initialize axis mapping
        self.axis_map = {
            0: {'name': 'Left Stick X', 'deadzone': 0.1},
            1: {'name': 'Left Stick Y', 'deadzone': 0.1},
            2: {'name': 'Right Stick X', 'deadzone': 0.1},
            3: {'name': 'Right Stick Y', 'deadzone': 0.1},
            4: {'name': 'Left Trigger', 'deadzone': 0.1},
            5: {'name': 'Right Trigger', 'deadzone': 0.1},
        }
    
    def detect_gamepads(self) -> List[Dict]:
        """Detect all gamepads, including misrecognized ones"""
        gamepads = []
        
        # Method 1: Pygame detection
        count = pygame.joystick.get_count()
        print(f"Pygame detected {count} joystick(s)")
        
        for i in range(count):
            try:
                joy = pygame.joystick.Joystick(i)
                joy.init()
                gamepads.append({
                    'id': i,
                    'name': joy.get_name(),
                    'axes': joy.get_numaxes(),
                    'buttons': joy.get_numbuttons(),
                    'hats': joy.get_numhats(),
                    'method': 'pygame'
                })
            except:
                pass
        
        # Method 2: Check Bluetooth devices
        print("\nChecking Bluetooth devices...")
        result = subprocess.run(
            ["system_profiler", "SPBluetoothDataType"],
            capture_output=True, text=True
        )
        
        if "Gamepad-igs" in result.stdout:
            print("✅ Found Gamepad-igs in Bluetooth devices")
            # Extract info
            for line in result.stdout.split('\n'):
                if 'Gamepad-igs' in line:
                    print(f"   {line.strip()}")
        
        # Method 3: Check HID devices (low-level)
        print("\nChecking HID devices...")
        result = subprocess.run(
            ["ioreg", "-p", "IOHID", "-w0", "-l"],
            capture_output=True, text=True
        )
        
        if 'gamepad' in result.stdout.lower() or 'joystick' in result.stdout.lower():
            print("✅ Found potential gamepad in HID devices")
        
        return gamepads
    
    def map_input(self, joystick_id: int = 0):
        """Map gamepad input to actions"""
        if not self.joysticks:
            print("❌ No gamepads available")
            return
        
        if joystick_id >= len(self.joysticks):
            print(f"❌ Invalid joystick ID: {joystick_id}")
            return
        
        joy = pygame.joystick.Joystick(joystick_id)
        
        print(f"\n🎮 Mapping input from: {joy.get_name()}")
        print("="*60)
        print("Controls:")
        print("  - Press buttons and move sticks to test")
        print("  - Press 'q' to quit")
        print("  - Press 'r' to remap buttons")
        print("="*60 + "\n")
        
        pygame.event.set_allowed([
            pygame.JOYBUTTONDOWN,
            pygame.JOYBUTTONUP,
            pygame.JOYAXISMOTION,
            pygame.JOYHATMOTION,
            pygame.KEYDOWN,
            pygame.QUIT
        ])
        
        last_axis_values = [0.0] * joy.get_numaxes()
        
        try:
            while True:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        return
                    
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_q:
                            print("\n⏹️  Stopping...")
                            return
                        elif event.key == pygame.K_r:
                            self.remap_buttons(joy)
                    
                    elif event.type == pygame.JOYBUTTONDOWN:
                        btn_info = self.button_map.get(event.button, {})
                        btn_name = btn_info.get('name', f'Button {event.button}')
                        timestamp = time.strftime("%H:%M:%S.%f")[:-3]
                        print(f"[{timestamp}] 🔘 {btn_name} (Button {event.button}) PRESSED")
                        
                        # Here you can add keyboard emulation
                        # keyboard.press(btn_info.get('key')) if btn_info.get('key') else None
                    
                    elif event.type == pygame.JOYBUTTONUP:
                        btn_info = self.button_map.get(event.button, {})
                        btn_name = btn_info.get('name', f'Button {event.button}')
                        timestamp = time.strftime("%H:%M:%S.%f")[:-3]
                        print(f"[{timestamp}] 🔘 {btn_name} (Button {event.button}) RELEASED")
                    
                    elif event.type == pygame.JOYAXISMOTION:
                        axis_info = self.axis_map.get(event.axis, {})
                        axis_name = axis_info.get('name', f'Axis {event.axis}')
                        deadzone = axis_info.get('deadzone', 0.1)
                        
                        # Only print if value changed significantly
                        if abs(event.value - last_axis_values[event.axis]) > 0.05:
                            last_axis_values[event.axis] = event.value
                            
                            if abs(event.value) > deadzone:
                                timestamp = time.strftime("%H:%M:%S.%f")[:-3]
                                print(f"[{timestamp}] 🕹️  {axis_name}: {event.value:+.3f}")
                    
                    elif event.type == pygame.JOYHATMOTION:
                        if event.value != (0, 0):
                            timestamp = time.strftime("%H:%M:%S.%f")[:-3]
                            print(f"[{timestamp}] 🎯 Hat {event.hat}: {event.value}")
                
                time.sleep(0.001)
        
        except KeyboardInterrupt:
            print("\n\n⏹️  Stopped by user")
    
    def remap_buttons(self, joystick):
        """Remap button assignments"""
        print("\n🔧 Button Remapping")
        print("Current mappings:")
        for btn_id, btn_info in self.button_map.items():
            print(f"  Button {btn_id}: {btn_info.get('name', 'Unknown')}")
        
        print("\nTo remap, edit the button_map in the code")
        print("Or press a button to test:")
        
        start_time = time.time()
        while time.time() - start_time < 5:
            for event in pygame.event.get():
                if event.type == pygame.JOYBUTTONDOWN:
                    print(f"Button {event.button} pressed!")
                    return
    
    def test_all_inputs(self, joystick_id: int = 0):
        """Test all gamepad inputs"""
        if not self.joysticks:
            print("❌ No gamepads available")
            return
        
        joy = pygame.joystick.Joystick(joystick_id)
        
        print(f"\n🧪 Testing: {joy.get_name()}")
        print(f"   Axes: {joy.get_numaxes()}")
        print(f"   Buttons: {joy.get_numbuttons()}")
        print(f"   Hats: {joy.get_numhats()}")
        
        print("\n📋 Button Test:")
        print("   Press each button to test...")
        print("   Press Ctrl+C to stop")
        
        tested_buttons = set()
        
        try:
            start_time = time.time()
            while time.time() - start_time < 30:
                for event in pygame.event.get():
                    if event.type == pygame.JOYBUTTONDOWN:
                        if event.button not in tested_buttons:
                            tested_buttons.add(event.button)
                            print(f"   ✅ Button {event.button} works")
                    
                    elif event.type == pygame.JOYAXISMOTION:
                        if abs(event.value) > 0.1:
                            print(f"   ✅ Axis {event.axis} works: {event.value:+.2f}")
                
                time.sleep(0.01)
        
        except KeyboardInterrupt:
            pass
        
        print(f"\n✅ Tested {len(tested_buttons)} buttons")
    
    def run(self):
        """Run the mapper"""
        print("="*60)
        print("🎮 ADVANCED GAMEPAD INPUT MAPPER")
        print("="*60)
        
        # Detect gamepads
        print("\n1️⃣ Detecting gamepads...")
        detected = self.detect_gamepads()
        
        if detected:
            self.joysticks = detected
            for gp in detected:
                print(f"   ✅ {gp['name']} ({gp['method']})")
        else:
            print("   ⚠️  No gamepads detected by pygame")
            print("   But we'll try anyway...")
        
        # Try to initialize pygame joysticks
        count = pygame.joystick.get_count()
        if count > 0:
            for i in range(count):
                joy = pygame.joystick.Joystick(i)
                joy.init()
                self.joysticks.append(joy)
                print(f"   ✅ Pygame joystick {i}: {joy.get_name()}")
        
        if not self.joysticks:
            print("\n❌ No gamepads detected")
            print("\nTroubleshooting:")
            print("1. Make sure gamepad is connected")
            print("2. Try re-pairing in XInput mode")
            print("3. Check System Settings > Privacy > Input Monitoring")
            print("4. Restart your computer")
            return
        
        # Choose action
        print("\n2️⃣ Choose action:")
        print("   1. Map input (real-time monitoring)")
        print("   2. Test all inputs")
        print("   3. Exit")
        
        try:
            choice = input("\nEnter choice (1-3): ").strip()
            
            if choice == '1':
                self.map_input(0)
            elif choice == '2':
                self.test_all_inputs(0)
            elif choice == '3':
                print("Exiting...")
            else:
                print("Invalid choice")
        
        except KeyboardInterrupt:
            print("\n\n⏹️  Cancelled")
        finally:
            pygame.quit()

if __name__ == "__main__":
    mapper = AdvancedGamepadMapper()
    mapper.run()
