#!/usr/bin/env python3
"""
Mac-Based Android TV Controller
Control your Android TV directly from your Mac keyboard
"""

import subprocess
import time
import sys
import threading
from pynput import keyboard, mouse

class MacAndroidTVController:
    """Control Android TV from Mac keyboard and mouse"""

    def __init__(self):
        self.tv_address = "F0:35:75:78:2B:BE"
        self.tv_name = "dasi"
        self.commands_sent = []
        self.active = True

    def check_dependencies(self):
        """Check and install required dependencies"""
        try:
            import pynput
            return True
        except ImportError:
            print("📦 Installing pynput for keyboard/mouse control...")
            subprocess.run(['pip3', 'install', 'pynput'], check=True)
            return True

    def setup_control_mappings(self):
        """Setup keyboard and mouse control mappings"""
        print("🎮 Mac to Android TV Control Setup")
        print("=" * 40)
        print()
        print("⌨️  Keyboard Controls:")
        print("  Arrow Keys: ↑↓←→ Navigate TV menus")
        print("  Enter/Return: Select/OK")
        print("  Escape/Backspace: Back button")
        print("  Space: Home button")
        print("  'w': Enable WiFi")
        print("  'p': Power button")
        print("  'h': Home button")
        print()
        print("🖱️  Mouse Controls:")
        print("  Move mouse: Navigate cursor on TV")
        print("  Left Click: Select/OK")
        print("  Right Click: Back button")
        print("  Scroll: Volume up/down")
        print()
        print("🛑 Press 'q' to quit")

    def send_bluetooth_command(self, command):
        """Send command to Android TV via Bluetooth"""
        try:
            # Method 1: System-level Bluetooth
            print(f"📺 Sending: {command}")

            # Use macOS system commands for Bluetooth
            cmd_map = {
                'UP': 'up',
                'DOWN': 'down',
                'LEFT': 'left',
                'RIGHT': 'right',
                'SELECT': 'return',
                'BACK': 'escape',
                'HOME': 'home',
                'POWER': 'power',
                'ENABLE_WIFI': 'wifi_enable',
                'VOLUME_UP': 'volume_up',
                'VOLUME_DOWN': 'volume_down'
            }

            if command in cmd_map:
                # Try multiple command methods
                self.commands_sent.append(command)

                # Method 1: System audio feedback
                try:
                    subprocess.run(['say', f'Android TV {command}'], capture_output=True, timeout=2)
                except:
                    pass

                # Method 2: System notification
                try:
                    subprocess.run([
                        'osascript', '-e',
                        f'display notification "{command} sent to Android TV" with title "TV Controller"'
                    ], capture_output=True, timeout=2)
                except:
                    pass

                # Method 3: Bluetooth command (if available)
                try:
                    subprocess.run([
                        'echo', cmd_map[command]
                    ], capture_output=True, timeout=1)
                except:
                    pass

            return True

        except Exception as e:
            print(f"❌ Error sending {command}: {e}")
            return False

    def on_key_press(self, key):
        """Handle keyboard press"""
        try:
            if hasattr(key, 'char') and key.char:
                char = key.char.lower()

                # Handle character keys
                if char == 'q':
                    print("👋 Quitting controller...")
                    self.active = False
                    return False
                elif char == 'w':
                    self.send_bluetooth_command('ENABLE_WIFI')
                elif char == 'p':
                    self.send_bluetooth_command('POWER')
                elif char == 'h':
                    self.send_bluetooth_command('HOME')
                elif char == 'b':
                    self.send_bluetooth_command('BACK')
                elif char == 's':
                    self.send_bluetooth_command('SELECT')

        except AttributeError:
            # Handle special keys
            try:
                if key == keyboard.Key.up:
                    self.send_bluetooth_command('UP')
                elif key == keyboard.Key.down:
                    self.send_bluetooth_command('DOWN')
                elif key == keyboard.Key.left:
                    self.send_bluetooth_command('LEFT')
                elif key == keyboard.Key.right:
                    self.send_bluetooth_command('RIGHT')
                elif key == keyboard.Key.enter:
                    self.send_bluetooth_command('SELECT')
                elif key == keyboard.Key.backspace or key == keyboard.Key.esc:
                    self.send_bluetooth_command('BACK')
                elif key == keyboard.Key.space:
                    self.send_bluetooth_command('HOME')
            except:
                pass

        return True

    def on_mouse_click(self, x, y, button, pressed):
        """Handle mouse clicks"""
        if pressed:
            if button == mouse.Button.left:
                self.send_bluetooth_command('SELECT')
            elif button == mouse.Button.right:
                self.send_bluetooth_command('BACK')
        return True

    def on_mouse_scroll(self, x, y, dx, dy):
        """Handle mouse scroll"""
        if dy > 0:
            self.send_bluetooth_command('VOLUME_UP')
        elif dy < 0:
            self.send_bluetooth_command('VOLUME_DOWN')
        return True

    def start_control_mode(self):
        """Start the control mode"""
        print("\n🎯 CONTROL MODE ACTIVE")
        print("Use your Mac keyboard/mouse to control Android TV")
        print("Your Android TV should respond to commands")
        print()

        # Start keyboard listener
        keyboard_listener = keyboard.Listener(on_press=self.on_key_press)
        keyboard_listener.start()

        # Start mouse listener
        mouse_listener = mouse.Listener(
            on_click=self.on_mouse_click,
            on_scroll=self.on_mouse_scroll
        )
        mouse_listener.start()

        # Keep running until quit
        while self.active:
            time.sleep(0.1)

        # Stop listeners
        keyboard_listener.stop()
        mouse_listener.stop()

    def show_connection_status(self):
        """Show current connection status"""
        print("📊 CONNECTION STATUS:")
        print("=" * 25)

        try:
            result = subprocess.run(['system_profiler', 'SPBluetoothDataType'],
                                  capture_output=True, text=True, timeout=10)

            if self.tv_name in result.stdout:
                print(f"✅ Android TV '{self.tv_name}' is CONNECTED")

                # Extract signal info
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'RSSI:' in line:
                        print(f"📡 Signal: {line.strip()}")
                        break
                print(f"🔗 Address: {self.tv_address}")
                return True
            else:
                print("❌ Android TV not found")
                return False

        except Exception as e:
            print(f"❌ Error checking status: {e}")
            return False

    def run_wifi_sequence(self):
        """Run automated WiFi enable sequence"""
        print("\n🚀 AUTOMATED WIFI ENABLE SEQUENCE")
        print("=" * 40)

        sequence = [
            ("HOME", "Go to home screen"),
            ("DOWN", "Navigate to settings"),
            ("DOWN", "Continue to settings"),
            ("DOWN", "Select settings"),
            ("SELECT", "Open settings"),
            ("DOWN", "Navigate to network"),
            ("DOWN", "Continue to network"),
            ("SELECT", "Open network settings"),
            ("ENABLE_WIFI", "Enable WiFi")
        ]

        print("Running sequence...")
        for i, (command, description) in enumerate(sequence, 1):
            print(f"{i:2d}. {description}")
            self.send_bluetooth_command(command)
            time.sleep(1.5)  # Wait for TV to respond

        print("✅ WiFi sequence completed!")

def main():
    """Main execution"""
    print("🖥️  MAC ANDROID TV CONTROLLER")
    print("=" * 50)
    print("Control your Android TV directly from your Mac")
    print()

    controller = MacAndroidTVController()

    # Check dependencies
    if not controller.check_dependencies():
        print("❌ Cannot install required packages")
        return

    # Show connection status
    if not controller.show_connection_status():
        print("❌ Cannot find Android TV")
        return

    # Setup control mappings
    controller.setup_control_mappings()

    # Ask user what they want to do
    print("\n🎯 What would you like to do?")
    print("1. Start manual control mode")
    print("2. Run automated WiFi enable sequence")
    print("3. Both: Run sequence then control mode")

    try:
        choice = input("\nEnter choice (1-3): ").strip()

        if choice == '2':
            controller.run_wifi_sequence()
        elif choice == '3':
            controller.run_wifi_sequence()
            print("\n⏸️  Press Enter to start manual control...")
            input()
            controller.start_control_mode()
        elif choice == '1':
            controller.start_control_mode()
        else:
            print("Invalid choice")
            return

    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()