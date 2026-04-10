#!/usr/bin/env python3
"""
Android TV Remote GUI for Mac
Inspired by Unified Remote - Complete GUI application for Android TV control
"""

import sys
import os
import time
import subprocess
import threading
from datetime import datetime
from tkinter import *
from tkinter import ttk, messagebox
from PIL import Image, ImageTk, ImageDraw
import json

class AndroidTVRemoteGUI:
    def __init__(self):
        self.root = Tk()
        self.setup_main_window()
        self.setup_variables()
        self.create_interface()
        self.setup_bluetooth_connection()

    def setup_main_window(self):
        """Setup main application window"""
        self.root.title("🎬 Android TV Remote - dasi TV")
        self.root.geometry("500x700")
        self.root.configure(bg='#1a1a1a')
        self.root.resizable(False, False)

        # Set window icon and style
        self.setup_styles()

    def setup_variables(self):
        """Initialize variables"""
        self.tv_mac_address = "F0:35:75:78:2B:BE"
        self.tv_name = "dasi"
        self.connected = False
        self.command_history = []
        self.app_running = True

        # Android TV keycodes
        self.keycodes = {
            'POWER': 98,
            'HOME': 98,
            'BACK': 98,
            'UP': 126,
            'DOWN': 125,
            'LEFT': 123,
            'RIGHT': 124,
            'SELECT': 36,
            'MENU': 82,
            'VOL_UP': 82,
            'VOL_DOWN': 81,
            'MUTE': 75,
            'CHANNEL_UP': 69,
            'CHANNEL_DOWN': 78,
            '0': 29, '1': 18, '2': 19, '3': 20, '4': 21,
            '5': 23, '6': 22, '7': 26, '8': 28, '9': 25,
        }

    def setup_styles(self):
        """Setup application styles"""
        style = ttk.Style()
        style.theme_use('clam')

        # Custom colors
        self.colors = {
            'bg': '#1a1a1a',
            'button': '#2a2a2a',
            'button_active': '#4a4a4a',
            'accent': '#007AFF',
            'text': '#ffffff',
            'text_secondary': '#cccccc'
        }

    def create_interface(self):
        """Create the main GUI interface"""
        self.create_header()
        self.create_status_panel()
        self.create_navigation_pad()
        self.create_control_buttons()
        self.create_number_pad()
        self.create_advanced_controls()
        self.create_action_buttons()

    def create_header(self):
        """Create header section"""
        header_frame = Frame(self.root, bg=self.colors['bg'], height=60)
        header_frame.pack(fill=X, padx=10, pady=5)

        # Title
        title_label = Label(header_frame, text="🎬 ANDROID TV REMOTE",
                           font=('Arial', 16, 'bold'),
                           fg=self.colors['text'], bg=self.colors['bg'])
        title_label.pack(side=LEFT)

        # Connection status
        self.status_label = Label(header_frame, text="🔴 NOT CONNECTED",
                                font=('Arial', 12),
                                fg='#ff4444', bg=self.colors['bg'])
        self.status_label.pack(side=RIGHT)

    def create_status_panel(self):
        """Create status information panel"""
        status_frame = Frame(self.root, bg='#2a2a2a', relief=RAISED, bd=1)
        status_frame.pack(fill=X, padx=10, pady=5)

        # TV info
        info_text = f"Device: {self.tv_name} ({self.tv_mac_address})"
        self.info_label = Label(status_frame, text=info_text,
                               font=('Courier', 9),
                               fg=self.colors['text_secondary'],
                               bg='#2a2a2a')
        self.info_label.pack(pady=5)

    def create_navigation_pad(self):
        """Create directional navigation pad"""
        nav_frame = Frame(self.root, bg=self.colors['bg'])
        nav_frame.pack(pady=10)

        # Create D-pad layout
        pad_frame = Frame(nav_frame, bg=self.colors['button'],
                         relief=RAISED, bd=2)
        pad_frame.pack()

        # Navigation buttons
        Button(pad_frame, text="▲", font=('Arial', 20, 'bold'), width=3, height=1,
               bg=self.colors['button'], fg=self.colors['text'],
               command=lambda: self.send_key('UP')).grid(row=0, column=1, padx=2, pady=2)

        Button(pad_frame, text="◀", font=('Arial', 20, 'bold'), width=3, height=1,
               bg=self.colors['button'], fg=self.colors['text'],
               command=lambda: self.send_key('LEFT')).grid(row=1, column=0, padx=2, pady=2)

        Button(pad_frame, text="●", font=('Arial', 24, 'bold'), width=3, height=1,
               bg=self.colors['accent'], fg='white',
               command=lambda: self.send_key('SELECT')).grid(row=1, column=1, padx=2, pady=2)

        Button(pad_frame, text="▶", font=('Arial', 20, 'bold'), width=3, height=1,
               bg=self.colors['button'], fg=self.colors['text'],
               command=lambda: self.send_key('RIGHT')).grid(row=1, column=2, padx=2, pady=2)

        Button(pad_frame, text="▼", font=('Arial', 20, 'bold'), width=3, height=1,
               bg=self.colors['button'], fg=self.colors['text'],
               command=lambda: self.send_key('DOWN')).grid(row=2, column=1, padx=2, pady=2)

    def create_control_buttons(self):
        """Create main control buttons"""
        control_frame = Frame(self.root, bg=self.colors['bg'])
        control_frame.pack(pady=10)

        # First row - Home, Back, Menu
        row1 = Frame(control_frame, bg=self.colors['bg'])
        row1.pack(pady=2)

        Button(row1, text="🏠 HOME", font=('Arial', 10, 'bold'), width=8,
               bg=self.colors['button'], fg=self.colors['text'],
               command=lambda: self.send_key('HOME')).pack(side=LEFT, padx=2)

        Button(row1, text="⬅ BACK", font=('Arial', 10, 'bold'), width=8,
               bg=self.colors['button'], fg=self.colors['text'],
               command=lambda: self.send_key('BACK')).pack(side=LEFT, padx=2)

        Button(row1, text="☰ MENU", font=('Arial', 10, 'bold'), width=8,
               bg=self.colors['button'], fg=self.colors['text'],
               command=lambda: self.send_key('MENU')).pack(side=LEFT, padx=2)

        # Second row - Power
        Button(control_frame, text="🔌 POWER", font=('Arial', 10, 'bold'), width=26,
               bg='#ff4444', fg='white',
               command=lambda: self.send_key('POWER')).pack(pady=5)

    def create_number_pad(self):
        """Create number pad for channels/input"""
        number_frame = Frame(self.root, bg=self.colors['bg'])
        number_frame.pack(pady=10)

        Label(number_frame, text="CHANNEL/INPUT", font=('Arial', 10),
              fg=self.colors['text_secondary'], bg=self.colors['bg']).pack()

        # Create 3x3 grid for numbers 1-9
        for row in range(3):
            row_frame = Frame(number_frame, bg=self.colors['bg'])
            row_frame.pack()

            for col in range(3):
                num = row * 3 + col + 1
                Button(row_frame, text=str(num), font=('Arial', 12, 'bold'),
                       width=3, height=1,
                       bg=self.colors['button'], fg=self.colors['text'],
                       command=lambda n=num: self.send_key(str(n))).pack(side=LEFT, padx=1)

        # Bottom row with 0 and channel buttons
        bottom_frame = Frame(number_frame, bg=self.colors['bg'])
        bottom_frame.pack(pady=2)

        Button(bottom_frame, text="0", font=('Arial', 12, 'bold'), width=3, height=1,
               bg=self.colors['button'], fg=self.colors['text'],
               command=lambda: self.send_key('0')).pack(side=LEFT, padx=1)

        Button(bottom_frame, text="CH+", font=('Arial', 10, 'bold'), width=4,
               bg=self.colors['button'], fg=self.colors['text'],
               command=lambda: self.send_key('CHANNEL_UP')).pack(side=LEFT, padx=1)

        Button(bottom_frame, text="CH-", font=('Arial', 10, 'bold'), width=4,
               bg=self.colors['button'], fg=self.colors['text'],
               command=lambda: self.send_key('CHANNEL_DOWN')).pack(side=LEFT, padx=1)

    def create_advanced_controls(self):
        """Create volume and other controls"""
        advanced_frame = Frame(self.root, bg=self.colors['bg'])
        advanced_frame.pack(pady=10)

        # Volume controls
        volume_frame = Frame(advanced_frame, bg=self.colors['bg'])
        volume_frame.pack()

        Label(volume_frame, text="VOLUME", font=('Arial', 10),
              fg=self.colors['text_secondary'], bg=self.colors['bg']).pack()

        vol_buttons = Frame(volume_frame, bg=self.colors['bg'])
        vol_buttons.pack(pady=2)

        Button(vol_buttons, text="🔉 VOL+", font=('Arial', 10, 'bold'), width=8,
               bg=self.colors['button'], fg=self.colors['text'],
               command=lambda: self.send_key('VOL_UP')).pack(side=LEFT, padx=2)

        Button(vol_buttons, text="🔇 MUTE", font=('Arial', 10, 'bold'), width=8,
               bg=self.colors['button'], fg=self.colors['text'],
               command=lambda: self.send_key('MUTE')).pack(side=LEFT, padx=2)

        Button(vol_buttons, text="🔊 VOL-", font=('Arial', 10, 'bold'), width=8,
               bg=self.colors['button'], fg=self.colors['text'],
               command=lambda: self.send_key('VOL_DOWN')).pack(side=LEFT, padx=2)

    def create_action_buttons(self):
        """Create action buttons for special functions"""
        action_frame = Frame(self.root, bg=self.colors['bg'])
        action_frame.pack(pady=10, fill=X, padx=10)

        # Navigation to Bluetooth settings
        Button(action_frame, text="📱 GO TO BLUETOOTH SETTINGS",
               font=('Arial', 10, 'bold'), width=25,
               bg=self.colors['accent'], fg='white',
               command=self.navigate_to_bluetooth).pack(pady=2)

        # Start pairing mode
        Button(action_frame, text="🔄 START PAIRING MODE",
               font=('Arial', 10, 'bold'), width=25,
               bg='#28a745', fg='white',
               command=self.start_pairing_mode).pack(pady=2)

        # Connection toggle
        self.connect_btn = Button(action_frame, text="🔗 CONNECT TO TV",
                                font=('Arial', 10, 'bold'), width=25,
                               bg='#ffc107', fg='black',
                               command=self.toggle_connection)
        self.connect_btn.pack(pady=2)

        # Command log
        log_frame = Frame(self.root, bg=self.colors['bg'])
        log_frame.pack(pady=5, fill=X, padx=10)

        Label(log_frame, text="COMMAND LOG:", font=('Arial', 9),
              fg=self.colors['text_secondary'], bg=self.colors['bg']).pack(anchor=W)

        self.log_text = Text(log_frame, height=4, width=50,
                            bg='#0a0a0a', fg=self.colors['text_secondary'],
                            font=('Courier', 8))
        self.log_text.pack()

    def setup_bluetooth_connection(self):
        """Setup Bluetooth connection to TV"""
        try:
            # Check if TV is already connected
            result = subprocess.run(['system_profiler', 'SPBluetoothDataType'],
                                  capture_output=True, text=True)

            if self.tv_name in result.stdout and 'Connected' in result.stdout:
                self.connected = True
                self.update_connection_status(True)
                self.log("✅ TV found connected to Mac")
            else:
                self.log("ℹ️ TV not connected - will attempt connection")
                self.attempt_connection()

        except Exception as e:
            self.log(f"❌ Error checking connection: {e}")

    def attempt_connection(self):
        """Attempt to connect to TV via Bluetooth"""
        self.log("🔗 Attempting to connect to TV...")

        try:
            # Try to connect using system Bluetooth
            script = f'''
            tell application "System Events"
                tell application "System Preferences"
                    activate
                    set current pane to pane id "com.apple.preference.bluetooth"
                    delay 2
                end tell

                tell application "System Events"
                    tell process "System Preferences"
                        tell window "Bluetooth"
                            try
                                tell outline 1
                                    select row "{self.tv_name}"
                                end tell
                                delay 1
                                click button "Connect"
                                delay 2
                            on error
                                log "Could not connect via UI"
                            end try
                        end tell
                    end tell
                end tell
            end tell
            '''

            from Cocoa import NSAppleScript
            applescript = NSAppleScript.alloc().initWithSource_(script)
            result, error = applescript.executeAndReturnError_(None)

            if not error:
                self.connected = True
                self.update_connection_status(True)
                self.log("✅ Connection attempt initiated")
            else:
                self.log(f"⚠️ Connection attempt: {error}")

        except Exception as e:
            self.log(f"❌ Connection failed: {e}")

    def send_key(self, key_name):
        """Send key command to TV"""
        if not self.connected:
            self.log("❌ Not connected to TV")
            return

        keycode = self.keycodes.get(key_name.upper())
        if not keycode:
            self.log(f"❌ Unknown key: {key_name}")
            return

        try:
            # Send key using AppleScript
            script = f'''
            tell application "System Events"
                key code {keycode}
            end tell
            '''

            from Cocoa import NSAppleScript
            applescript = NSAppleScript.alloc().initWithSource_(script)
            result, error = applescript.executeAndReturnError_(None)

            timestamp = datetime.now().strftime("%H:%M:%S")

            if not error:
                self.log(f"✅ [{timestamp}] Sent: {key_name} (code {keycode})")
                self.highlight_key(key_name)
            else:
                self.log(f"❌ [{timestamp}] Failed: {key_name} - {error}")

        except Exception as e:
            self.log(f"❌ [{timestamp}] Error sending {key_name}: {e}")

    def navigate_to_bluetooth(self):
        """Navigate TV to Bluetooth settings"""
        self.log("🧭 Navigating to Bluetooth settings...")

        sequence = ['HOME', 'RIGHT', 'RIGHT', 'SELECT', 'DOWN', 'DOWN', 'SELECT', 'DOWN', 'SELECT']

        def send_sequence():
            for key in sequence:
                time.sleep(1)
                self.send_key(key)

        threading.Thread(target=send_sequence, daemon=True).start()

    def start_pairing_mode(self):
        """Start TV pairing mode"""
        self.log("🔄 Starting pairing mode...")

        sequence = ['DOWN', 'DOWN', 'DOWN', 'SELECT']

        def send_pairing_sequence():
            time.sleep(1)
            for key in sequence:
                time.sleep(1)
                self.send_key(key)

        threading.Thread(target=send_pairing_sequence, daemon=True).start()

    def toggle_connection(self):
        """Toggle TV connection"""
        if self.connected:
            self.disconnect_tv()
        else:
            self.attempt_connection()

    def disconnect_tv(self):
        """Disconnect from TV"""
        self.log("🔌 Disconnecting from TV...")
        self.connected = False
        self.update_connection_status(False)

    def update_connection_status(self, connected):
        """Update connection status display"""
        if connected:
            self.status_label.config(text="🟢 CONNECTED", fg='#44ff44')
            self.connect_btn.config(text="🔌 DISCONNECT", bg='#dc3545')
        else:
            self.status_label.config(text="🔴 NOT CONNECTED", fg='#ff4444')
            self.connect_btn.config(text="🔗 CONNECT TO TV", bg='#ffc107')

        self.connected = connected

    def highlight_key(self, key_name):
        """Visual feedback for key press"""
        # This would highlight the pressed button temporarily
        pass

    def log(self, message):
        """Add message to command log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"

        self.log_text.insert(END, log_entry)
        self.log_text.see(END)

        # Keep log size manageable
        lines = self.log_text.get(1.0, END).split('\n')
        if len(lines) > 100:
            self.log_text.delete(1.0, 2.0)

    def run(self):
        """Start the GUI application"""
        self.log("🎬 Android TV Remote Started")
        self.log("📱 Target: dasi TV ({self.tv_mac_address})")

        # Handle window closing
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Start main loop
        self.root.mainloop()

    def on_closing(self):
        """Handle window closing"""
        self.log("👋 Shutting down remote...")
        self.app_running = False
        if self.connected:
            self.disconnect_tv()
        self.root.destroy()

def main():
    """Main entry point"""
    # Check for required dependencies
    try:
        from PIL import Image, ImageTk
    except ImportError:
        print("❌ PIL/Pillow not installed. Install with: pip3 install Pillow")
        sys.exit(1)

    try:
        from Cocoa import NSAppleScript
    except ImportError:
        print("❌ PyObjC not installed. Install with: pip3 install pyobjc-framework-Cocoa")
        sys.exit(1)

    # Create and run the GUI
    app = AndroidTVRemoteGUI()
    app.run()

if __name__ == "__main__":
    main()