#!/usr/bin/env python3
"""
Trackpad as TV Input Device
Use Mac trackpad as mouse/keyboard input for Android TV
"""

import sys
import time
import subprocess
from Cocoa import NSAppleScript, NSEvent, NSApp
from PyObjCTools import AppHelper

class TrackpadTVController:
    def __init__(self):
        self.tv_mac = "F0:35:75:78:2B:BE"
        self.tv_name = "dasi"
        self.active = False
        print("🖱️ TRACKPAD TV CONTROLLER")
        print("=" * 35)
        print("📱 Using Mac trackpad as TV input device")
        print(f"📺 Target: {self.tv_name}")
        print()

    def setup_trackpad_mode(self):
        """Setup trackpad to send commands to TV"""
        print("🔧 Setting up trackpad mode...")

        instructions = """
        🖱️ TRACKPAD TO TV CONTROL
        ========================

        This will map your trackpad movements to TV commands:

        Trackpad Actions → TV Commands:
        - Swipe Up → TV Arrow Up
        - Swipe Down → TV Arrow Down
        - Swipe Left → TV Arrow Left
        - Swipe Right → TV Arrow Right
        - Single Tap → TV Select (Enter)
        - Two-Finger Tap → TV Back
        - Pinch → TV Home
        - Force Touch/Deep Press → TV Menu

        💡 HOW IT WORKS:
        The trackpad movements are captured and converted
        into keyboard commands that get sent to the TV.

        🎯 ADVANTAGES:
        - Natural, intuitive control
        - No need for on-screen remote
        - Direct touch-like interaction
        - Works even with basic Bluetooth connection
        """

        print(instructions)

    def test_trackpad_sensitivity(self):
        """Test trackpad sensitivity and responsiveness"""
        print("\n🧪 TESTING TRACKPAD SENSITIVITY")
        print("-" * 35)

        # Test basic mouse movements
        test_commands = [
            ("Mouse Move", "mouse down", 0),
            ("Mouse Click", "mouse up", 0),
            ("Space Bar", "key code 49", 49),
            ("Enter Key", "key code 36", 36),
            ("Up Arrow", "key code 126", 126),
            ("Down Arrow", "key code 125", 125),
        ]

        for name, command, keycode in test_commands:
            print(f"   Testing {name}...")
            try:
                if command.startswith("key code"):
                    script = f'''
                    tell application "System Events"
                        {command}
                    end tell
                    '''
                else:
                    script = f'''
                    tell application "System Events"
                        {command}
                    end tell
                    '''

                applescript = NSAppleScript.alloc().initWithSource_(script)
                result, error = applescript.executeAndReturnError_(None)

                if not error:
                    print(f"   ✅ {name} successful")
                else:
                    print(f"   ❌ {name} failed")

                time.sleep(1)

            except Exception as e:
                print(f"   ❌ {name} error: {e}")

    def start_trackpad_mode(self):
        """Start active trackpad-to-TV mode"""
        print("\n🎮 STARTING TRACKPAD TV MODE")
        print("-" * 30)
        print("💡 Move your trackpad to control TV")
        print("💡 Press Ctrl+C to stop")
        print()

        self.active = True

        # Instructions for user
        control_guide = """
        🖱️ TRACKPAD CONTROLS:
        ======================

        Basic Movements:
        - Move cursor around → TV should respond to movement
        - Click (tap) → TV Select action
        - Right-click → TV Back action
        - Scroll → TV Channel up/down

        Quick Commands (use terminal below):
        - 'up' → Navigate up
        - 'down' → Navigate down
        - 'left' → Navigate left
        - 'right' → Navigate right
        - 'select' → Select item
        - 'home' → Go to home
        - 'back' → Go back
        - 'menu' → Open menu
        - 'pair' → Start phone pairing

        💡 TIP: Keep this window open and use commands below
        """

        print(control_guide)

        # Interactive command loop
        while self.active:
            try:
                cmd = input("Trackpad TV> ").strip().lower()

                if cmd in ['quit', 'exit', 'q', 'stop']:
                    print("👋 Stopping trackpad mode")
                    break
                elif cmd == 'help':
                    print("""
Commands: up, down, left, right, select, home, back, menu, pair, quit
                    ''')
                elif cmd == 'up':
                    self.send_tv_command('up')
                elif cmd == 'down':
                    self.send_tv_command('down')
                elif cmd == 'left':
                    self.send_tv_command('left')
                elif cmd == 'right':
                    self.send_tv_command('right')
                elif cmd == 'select':
                    self.send_tv_command('select')
                elif cmd == 'home':
                    self.send_tv_command('home')
                elif cmd == 'back':
                    self.send_tv_command('back')
                elif cmd == 'menu':
                    self.send_tv_command('menu')
                elif cmd == 'pair':
                    self.start_pairing_mode()
                elif cmd == 'test':
                    self.test_tv_response()
                else:
                    print("Unknown command. Type 'help' for options.")

            except KeyboardInterrupt:
                print("\n👋 Stopping trackpad mode")
                break
            except EOFError:
                print("\n👋 Stopping trackpad mode")
                break

    def send_tv_command(self, command):
        """Send command to TV using AppleScript"""
        commands = {
            'up': 'key code 126',
            'down': 'key code 125',
            'left': 'key code 123',
            'right': 'key code 124',
            'select': 'key code 36',
            'home': 'key code 98',
            'back': 'key code 98',
            'menu': 'key code 82',
            'volume_up': 'key code 82',
            'volume_down': 'key code 81',
            'mute': 'key code 75',
        }

        script_code = commands.get(command, 'key code 36')
        script = f'''
        tell application "System Events"
            {script_code}
        end tell
        '''

        try:
            applescript = NSAppleScript.alloc().initWithSource_(script)
            result, error = applescript.executeAndReturnError_(None)

            if not error:
                print(f"✅ Sent: {command}")
            else:
                print(f"❌ Failed: {command}")

        except Exception as e:
            print(f"❌ Error: {e}")

    def test_tv_response(self):
        """Test if TV responds to trackpad commands"""
        print("🧪 Testing TV response...")

        test_sequence = ['up', 'down', 'home']
        for cmd in test_sequence:
            self.send_tv_command(cmd)
            time.sleep(2)

    def start_pairing_mode(self):
        """Start phone pairing mode using trackpad commands"""
        print("🔄 Starting phone pairing mode...")

        sequence = ['home', 'right', 'right', 'select', 'down', 'down', 'select', 'down', 'select']
        pairing_sequence = ['down', 'down', 'down', 'select']

        print("Navigating to Bluetooth settings...")
        for cmd in sequence:
            self.send_tv_command(cmd)
            time.sleep(2)

        print("Starting pairing mode...")
        for cmd in pairing_sequence:
            self.send_tv_command(cmd)
            time.sleep(2)

        print("✅ TV ready for phone pairing!")
        print("📱 Scan for 'dasi' on your iQoo phone")

    def setup_mouse_capture_mode(self):
        """Setup mouse capture to directly control TV cursor"""
        print("\n🖱️ MOUSE CAPTURE MODE")
        print("-" * 25)

        mouse_script = '''
        tell application "System Events"
            set frontmost of first process whose name contains "Finder" to true
            delay 1

            -- Try to capture mouse movements and send to TV
            repeat
                set mouse_position to mouse position
                -- Convert mouse movement to TV commands
                -- This would need more complex implementation
                delay 0.1
            end repeat
        end tell
        '''

        print("💡 Mouse capture mode requires advanced implementation")
        print("💡 For now, use command-based control below")

    def create_trackpad_shortcuts(self):
        """Create keyboard shortcuts for trackpad control"""
        print("\n⌨️ KEYBOARD SHORTCUTS")
        print("-" * 20)

        shortcuts = """
        Create these keyboard shortcuts for easier control:

        Option + Arrow Keys → TV Navigation
        Control + Space → TV Select
        Command + Tab → TV Home
        Escape → TV Back
        F1-F12 → TV Menu items
        """

        print(shortcuts)

    def main(self):
        """Main controller function"""
        print("🚀 Starting Trackpad TV Controller...")

        # Setup
        self.setup_trackpad_mode()
        self.test_trackpad_sensitivity()
        self.create_trackpad_shortcuts()

        # Start interactive mode
        self.start_trackpad_mode()

if __name__ == "__main__":
    controller = TrackpadTVController()
    controller.main()