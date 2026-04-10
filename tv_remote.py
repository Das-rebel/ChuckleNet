#!/usr/bin/env python3
"""
Bluetooth TV Remote for Mac
Controls Android TV via Bluetooth connection
"""

import sys
import os
import subprocess
import time
import json
from typing import Dict, Optional, Any
import threading
from Cocoa import NSObject, NSAppleScript

class TVBluetoothRemote:
    def __init__(self):
        self.tv_mac_address = "F0:35:75:78:2B:BE"  # Your Dasi TV's MAC address
        self.tv_name = "dasi"
        self.connected = False

        # Android TV Bluetooth control codes and corresponding AppleScript commands
        self.commands = {
            'power': 'simulate key code 98 using {command down, command up}',
            'home': 'simulate key code 98 using {command down, command up}',
            'back': 'simulate key code 98 using {command down, command up}',
            'up': 'simulate key code 126 using {command down, command up}',
            'down': 'simulate key code 125 using {command down, command up}',
            'left': 'simulate key code 123 using {command down, command up}',
            'right': 'simulate key code 124 using {command down, command up}',
            'select': 'simulate key code 36 using {command down, command up}',
            'volume_up': 'simulate key code 82 using {command down, command up}',
            'volume_down': 'simulate key code 81 using {command down, command up}',
            'mute': 'simulate key code 75 using {command down, command up}',
            'menu': 'simulate key code 82 using {command down, command up}'
        }

    def connect_to_tv(self) -> bool:
        """Connect to TV via macOS Bluetooth"""
        try:
            print(f"Connecting to {self.tv_name} ({self.tv_mac_address})...")

            # Use system command to connect via Bluetooth
            script = f'''
            tell application "System Events"
                activate
                delay 1
            end tell

            tell application "System Preferences"
                activate
                set the current pane to pane id "com.apple.preference.bluetooth"
                delay 2
            end tell

            tell application "System Events"
                tell process "System Preferences"
                    try
                        click button "{self.tv_name}" of scroll area 1 of window "Bluetooth"
                        delay 1
                        click button "Connect" of sheet 1 of window "Bluetooth"
                        delay 2
                    on error
                        click menu item "{self.tv_name}" of menu "View" of menu bar 1
                        delay 1
                    end try
                end tell
            end tell
            '''

            applescript = NSAppleScript.alloc().initWithSource_(script)
            result, error = applescript.executeAndReturnError_(None)

            if error:
                print(f"❌ Connection failed: {error}")
                return False

            # Alternative method using command line
            try:
                subprocess.run(['blueutil', '--connect', self.tv_mac_address],
                             capture_output=True, check=True, timeout=10)
                self.connected = True
                print("✅ Successfully connected to TV!")
                return True
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("❌ blueutil not found. Install with: brew install blueutil")
                return False

        except Exception as e:
            print(f"❌ Failed to connect: {e}")
            return False

    def send_command(self, command: str) -> bool:
        """Send command to TV via AppleScript or alternative methods"""
        try:
            if command in self.commands:
                # Try AppleScript method first
                script = f'''
                tell application "System Events"
                    {self.commands[command]}
                end tell
                '''

                applescript = NSAppleScript.alloc().initWithSource_(script)
                result, error = applescript.executeAndReturnError_(None)

                if not error:
                    print(f"✅ Sent command: {command}")
                    return True

                # Fallback: try to use blueutil to send commands
                if command in ['volume_up', 'volume_down']:
                    volume_cmd = 'increase' if command == 'volume_up' else 'decrease'
                    subprocess.run(['blueutil', '--volume', volume_cmd],
                                 capture_output=True)
                elif command in ['mute']:
                    subprocess.run(['blueutil', '--volume', 'toggle'],
                                 capture_output=True)

                print(f"✅ Sent command: {command} (via alternative method)")
                return True
            else:
                print(f"❌ Unknown command: {command}")
                return False

        except Exception as e:
            print(f"❌ Failed to send command: {e}")
            return False

    def navigate_to_bluetooth_settings(self) -> bool:
        """Navigate to TV Bluetooth settings using keyboard commands"""
        navigation_sequence = [
            'home',      # Go to home screen
            'right',     # Navigate to settings
            'right',
            'select',    # Enter settings
            'down',      # Navigate to connected devices
            'down',
            'select'     # Enter Bluetooth settings
        ]

        print("🧭 Navigating to Bluetooth settings...")

        for command in navigation_sequence:
            time.sleep(0.5)  # Wait for TV to respond
            if not self.send_command(command):
                print(f"❌ Failed to execute: {command}")
                return False

        print("✅ Navigated to Bluetooth settings")
        return True

    def start_pairing_mode(self) -> bool:
        """Start TV pairing mode for phone"""
        navigation_sequence = [
            'down',      # Navigate to "Add new device"
            'down',
            'select'     # Start pairing
        ]

        print("🔄 Starting TV pairing mode...")

        for command in navigation_sequence:
            time.sleep(0.5)
            if not self.send_command(command):
                print(f"❌ Failed to execute: {command}")
                return False

        print("✅ TV is now in pairing mode")
        return True

    def disconnect(self):
        """Disconnect from TV"""
        if self.socket:
            self.socket.close()
        self.connected = False
        print("🔌 Disconnected from TV")

class RemoteGUI:
    def __init__(self, remote: TVBluetoothRemote):
        self.remote = remote
        self.setup_gui()

    def setup_gui(self):
        """Setup simple GUI using tkinter"""
        try:
            import tkinter as tk
            from tkinter import ttk

            self.root = tk.Tk()
            self.root.title("TV Bluetooth Remote")
            self.root.geometry("400x500")

            # Connection status
            self.status_label = ttk.Label(self.root, text="❌ Not Connected",
                                         font=('Arial', 12, 'bold'))
            self.status_label.pack(pady=10)

            # Connect button
            self.connect_btn = ttk.Button(self.root, text="Connect to TV",
                                        command=self.toggle_connection)
            self.connect_btn.pack(pady=5)

            # Navigation controls
            nav_frame = ttk.Frame(self.root)
            nav_frame.pack(pady=20)

            # Directional pad
            self.up_btn = ttk.Button(nav_frame, text="↑", width=5,
                                   command=lambda: self.send_cmd('up'))
            self.up_btn.grid(row=0, column=1, padx=2, pady=2)

            self.left_btn = ttk.Button(nav_frame, text="←", width=5,
                                     command=lambda: self.send_cmd('left'))
            self.left_btn.grid(row=1, column=0, padx=2, pady=2)

            self.select_btn = ttk.Button(nav_frame, text="SELECT", width=5,
                                        command=lambda: self.send_cmd('select'))
            self.select_btn.grid(row=1, column=1, padx=2, pady=2)

            self.right_btn = ttk.Button(nav_frame, text="→", width=5,
                                      command=lambda: self.send_cmd('right'))
            self.right_btn.grid(row=1, column=2, padx=2, pady=2)

            self.down_btn = ttk.Button(nav_frame, text="↓", width=5,
                                     command=lambda: self.send_cmd('down'))
            self.down_btn.grid(row=2, column=1, padx=2, pady=2)

            # Control buttons
            control_frame = ttk.Frame(self.root)
            control_frame.pack(pady=20)

            self.home_btn = ttk.Button(control_frame, text="HOME",
                                     command=lambda: self.send_cmd('home'))
            self.home_btn.grid(row=0, column=0, padx=5, pady=5)

            self.back_btn = ttk.Button(control_frame, text="BACK",
                                     command=lambda: self.send_cmd('back'))
            self.back_btn.grid(row=0, column=1, padx=5, pady=5)

            self.menu_btn = ttk.Button(control_frame, text="MENU",
                                     command=lambda: self.send_cmd('menu'))
            self.menu_btn.grid(row=0, column=2, padx=5, pady=5)

            # Special actions
            action_frame = ttk.Frame(self.root)
            action_frame.pack(pady=20)

            self.bluetooth_btn = ttk.Button(action_frame, text="Navigate to Bluetooth Settings",
                                          command=self.navigate_bluetooth)
            self.bluetooth_btn.pack(pady=5)

            self.pairing_btn = ttk.Button(action_frame, text="Start Phone Pairing Mode",
                                        command=self.start_pairing)
            self.pairing_btn.pack(pady=5)

            # Volume controls
            volume_frame = ttk.Frame(self.root)
            volume_frame.pack(pady=10)

            self.vol_up_btn = ttk.Button(volume_frame, text="VOL +",
                                        command=lambda: self.send_cmd('volume_up'))
            self.vol_up_btn.grid(row=0, column=0, padx=5, pady=5)

            self.vol_down_btn = ttk.Button(volume_frame, text="VOL -",
                                          command=lambda: self.send_cmd('volume_down'))
            self.vol_down_btn.grid(row=0, column=1, padx=5, pady=5)

            self.mute_btn = ttk.Button(volume_frame, text="MUTE",
                                      command=lambda: self.send_cmd('mute'))
            self.mute_btn.grid(row=0, column=2, padx=5, pady=5)

            # Instructions
            instructions = ttk.Label(self.root, text="Keyboard Controls:\n" +
                                   "Arrow Keys: Navigate | Enter: Select | " +
                                   "Esc: Back | Space: Home",
                                   font=('Arial', 10))
            instructions.pack(pady=10)

            # Bind keyboard shortcuts
            self.root.bind('<Up>', lambda e: self.send_cmd('up'))
            self.root.bind('<Down>', lambda e: self.send_cmd('down'))
            self.root.bind('<Left>', lambda e: self.send_cmd('left'))
            self.root.bind('<Right>', lambda e: self.send_cmd('right'))
            self.root.bind('<Return>', lambda e: self.send_cmd('select'))
            self.root.bind('<Escape>', lambda e: self.send_cmd('back'))
            self.root.bind('<space>', lambda e: self.send_cmd('home'))

            print("✅ GUI Remote Control Ready!")

        except ImportError:
            print("❌ tkinter not available. Install with: brew install python-tk")

    def toggle_connection(self):
        """Toggle TV connection"""
        if self.remote.connected:
            self.remote.disconnect()
            self.status_label.config(text="❌ Not Connected")
            self.connect_btn.config(text="Connect to TV")
        else:
            if self.remote.connect_to_tv():
                self.status_label.config(text="✅ Connected to dasi TV")
                self.connect_btn.config(text="Disconnect")
            else:
                self.status_label.config(text="❌ Connection Failed")

    def send_cmd(self, command: str):
        """Send command to TV"""
        self.remote.send_command(command)

    def navigate_bluetooth(self):
        """Navigate to Bluetooth settings"""
        if self.remote.connected:
            self.remote.navigate_to_bluetooth_settings()
        else:
            print("❌ Connect to TV first")

    def start_pairing(self):
        """Start phone pairing mode"""
        if self.remote.connected:
            self.remote.start_pairing_mode()
        else:
            print("❌ Connect to TV first")

    def run(self):
        """Start the GUI"""
        try:
            self.root.mainloop()
        except:
            pass

def main():
    print("🎬 TV Bluetooth Remote Controller")
    print("================================")

    # Create remote instance
    remote = TVBluetoothRemote()

    # Check if GUI is available
    if len(sys.argv) > 1 and sys.argv[1] == '--gui':
        gui = RemoteGUI(remote)
        gui.run()
    else:
        print("📱 Command Line Mode")
        print("Type 'help' for commands, 'quit' to exit")
        print("Run with --gui for graphical interface")
        print()

        while True:
            try:
                cmd = input("TV Remote> ").strip().lower()

                if cmd == 'quit' or cmd == 'exit':
                    break
                elif cmd == 'help':
                    print("Available commands:")
                    print("  connect - Connect to TV")
                    print("  disconnect - Disconnect from TV")
                    print("  home - Press home button")
                    print("  back - Press back button")
                    print("  up, down, left, right - Navigate")
                    print("  select - Press select button")
                    print("  menu - Press menu button")
                    print("  vol_up, vol_down - Volume control")
                    print("  mute - Mute/Unmute")
                    print("  bluetooth - Navigate to Bluetooth settings")
                    print("  pair - Start phone pairing mode")
                    print("  gui - Launch graphical interface")
                    print("  quit - Exit")
                elif cmd == 'connect':
                    remote.connect_to_tv()
                elif cmd == 'disconnect':
                    remote.disconnect()
                elif cmd == 'bluetooth':
                    remote.navigate_to_bluetooth_settings()
                elif cmd == 'pair':
                    remote.start_pairing_mode()
                elif cmd == 'gui':
                    gui = RemoteGUI(remote)
                    gui.run()
                    break
                elif cmd in remote.keycodes:
                    remote.send_command(cmd)
                else:
                    print(f"Unknown command: {cmd}")
                    print("Type 'help' for available commands")

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")

        # Cleanup
        remote.disconnect()
        print("\n👋 Goodbye!")

if __name__ == "__main__":
    main()