#!/usr/bin/env python3
"""
Fixed Android TV Remote GUI for Mac
Enhanced with improved Bluetooth connection methods
"""

import sys
import os
import time
import subprocess
import threading
from datetime import datetime
from tkinter import *
from tkinter import ttk, messagebox
from improved_tv_connector import ImprovedTVConnector

class AndroidTVRemoteGUIFixed:
    def __init__(self):
        self.root = Tk()
        self.setup_main_window()
        self.setup_variables()
        self.create_interface()
        self.setup_bluetooth_connection()

    def setup_main_window(self):
        """Setup main application window"""
        self.root.title("🎬 Android TV Remote - dasi TV (FIXED)")
        self.root.geometry("520x750")
        self.root.configure(bg='#1a1a1a')
        self.root.resizable(False, False)

        # Center window on screen
        self.center_window()

    def center_window(self):
        """Center the window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def setup_variables(self):
        """Initialize variables"""
        self.tv_mac_address = "F0:35:75:78:2B:BE"
        self.tv_name = "dasi"
        self.connected = False
        self.command_history = []
        self.app_running = True
        self.connector = ImprovedTVConnector(self.tv_mac_address, self.tv_name)

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

        # Colors
        self.colors = {
            'bg': '#1a1a1a',
            'button': '#2a2a2a',
            'button_active': '#4a4a4a',
            'accent': '#007AFF',
            'success': '#28a745',
            'warning': '#ffc107',
            'danger': '#dc3545',
            'text': '#ffffff',
            'text_secondary': '#cccccc'
        }

    def create_interface(self):
        """Create the main GUI interface"""
        self.create_header()
        self.create_connection_panel()
        self.create_navigation_pad()
        self.create_control_buttons()
        self.create_number_pad()
        self.create_volume_controls()
        self.create_action_buttons()
        self.create_log_panel()

    def create_header(self):
        """Create header section"""
        header_frame = Frame(self.root, bg=self.colors['bg'], height=60)
        header_frame.pack(fill=X, padx=10, pady=5)

        # Title
        title_label = Label(header_frame, text="🎬 ANDROID TV REMOTE (FIXED)",
                           font=('Arial', 16, 'bold'),
                           fg=self.colors['text'], bg=self.colors['bg'])
        title_label.pack(side=LEFT)

        # Connection status with more detail
        self.status_label = Label(header_frame, text="🔴 NOT CONNECTED",
                                font=('Arial', 12, 'bold'),
                                fg=self.colors['danger'], bg=self.colors['bg'])
        self.status_label.pack(side=RIGHT)

    def create_connection_panel(self):
        """Create connection status panel"""
        conn_frame = Frame(self.root, bg='#2a2a2a', relief=RAISED, bd=1)
        conn_frame.pack(fill=X, padx=10, pady=5)

        # TV info
        self.info_label = Label(conn_frame, text=f"Device: {self.tv_name} ({self.tv_mac_address})",
                               font=('Courier', 9),
                               fg=self.colors['text_secondary'],
                               bg='#2a2a2a')
        self.info_label.pack(pady=5)

        # Connection method display
        self.method_label = Label(conn_frame, text="Method: None",
                                font=('Courier', 8),
                                fg=self.colors['text_secondary'],
                                bg='#2a2a2a')
        self.method_label.pack(pady=2)

    def create_navigation_pad(self):
        """Create directional navigation pad"""
        nav_frame = Frame(self.root, bg=self.colors['bg'])
        nav_frame.pack(pady=10)

        # Create D-pad layout
        pad_frame = Frame(nav_frame, bg=self.colors['button'],
                         relief=RAISED, bd=3)
        pad_frame.pack()

        # Navigation buttons with better visual feedback
        buttons_config = [
            ('▲', 0, 1, 'UP'),
            ('◀', 1, 0, 'LEFT'),
            ('●', 1, 1, 'SELECT'),
            ('▶', 1, 2, 'RIGHT'),
            ('▼', 2, 1, 'DOWN'),
        ]

        for text, row, col, command in buttons_config:
            btn_color = self.colors['accent'] if command == 'SELECT' else self.colors['button']
            Button(pad_frame, text=text, font=('Arial', 24, 'bold'), width=4, height=2,
                   bg=btn_color, fg='white' if command == 'SELECT' else self.colors['text'],
                   relief=RAISED, bd=2,
                   command=lambda cmd=command: self.send_key(cmd)).grid(row=row, column=col, padx=3, pady=3)

    def create_control_buttons(self):
        """Create main control buttons"""
        control_frame = Frame(self.root, bg=self.colors['bg'])
        control_frame.pack(pady=10)

        # Main navigation buttons
        row1 = Frame(control_frame, bg=self.colors['bg'])
        row1.pack(pady=3)

        Button(row1, text="🏠 HOME", font=('Arial', 10, 'bold'), width=10,
               bg=self.colors['button'], fg=self.colors['text'],
               command=lambda: self.send_key('HOME')).pack(side=LEFT, padx=3)

        Button(row1, text="⬅ BACK", font=('Arial', 10, 'bold'), width=10,
               bg=self.colors['button'], fg=self.colors['text'],
               command=lambda: self.send_key('BACK')).pack(side=LEFT, padx=3)

        Button(row1, text="☰ MENU", font=('Arial', 10, 'bold'), width=10,
               bg=self.colors['button'], fg=self.colors['text'],
               command=lambda: self.send_key('MENU')).pack(side=LEFT, padx=3)

        # Power button (more prominent)
        Button(control_frame, text="🔌 POWER OFF/ON", font=('Arial', 12, 'bold'), width=32,
               bg=self.colors['danger'], fg='white',
               command=lambda: self.send_key('POWER')).pack(pady=8)

    def create_number_pad(self):
        """Create number pad for channels/input"""
        number_frame = Frame(self.root, bg=self.colors['bg'])
        number_frame.pack(pady=10)

        Label(number_frame, text="CHANNEL & INPUT CONTROL", font=('Arial', 10, 'bold'),
              fg=self.colors['text_secondary'], bg=self.colors['bg']).pack()

        # Create number grid
        grid_frame = Frame(number_frame, bg=self.colors['bg'])
        grid_frame.pack(pady=5)

        for row in range(3):
            row_frame = Frame(grid_frame, bg=self.colors['bg'])
            row_frame.pack()

            for col in range(3):
                num = row * 3 + col + 1
                Button(row_frame, text=str(num), font=('Arial', 14, 'bold'),
                       width=4, height=1,
                       bg=self.colors['button'], fg=self.colors['text'],
                       command=lambda n=num: self.send_key(str(n))).pack(side=LEFT, padx=2)

        # Bottom row with 0 and channel controls
        bottom_frame = Frame(number_frame, bg=self.colors['bg'])
        bottom_frame.pack(pady=3)

        Button(bottom_frame, text="0", font=('Arial', 14, 'bold'), width=4, height=1,
               bg=self.colors['button'], fg=self.colors['text'],
               command=lambda: self.send_key('0')).pack(side=LEFT, padx=2)

        Button(bottom_frame, text="CH+", font=('Arial', 10, 'bold'), width=6,
               bg=self.colors['button'], fg=self.colors['text'],
               command=lambda: self.send_key('CHANNEL_UP')).pack(side=LEFT, padx=2)

        Button(bottom_frame, text="CH-", font=('Arial', 10, 'bold'), width=6,
               bg=self.colors['button'], fg=self.colors['text'],
               command=lambda: self.send_key('CHANNEL_DOWN')).pack(side=LEFT, padx=2)

    def create_volume_controls(self):
        """Create volume controls"""
        volume_frame = Frame(self.root, bg=self.colors['bg'])
        volume_frame.pack(pady=10)

        Label(volume_frame, text="🔊 VOLUME CONTROL", font=('Arial', 10, 'bold'),
              fg=self.colors['text_secondary'], bg=self.colors['bg']).pack()

        vol_buttons = Frame(volume_frame, bg=self.colors['bg'])
        vol_buttons.pack(pady=5)

        Button(vol_buttons, text="🔉 VOL+", font=('Arial', 11, 'bold'), width=10,
               bg=self.colors['success'], fg='white',
               command=lambda: self.send_key('VOL_UP')).pack(side=LEFT, padx=3)

        Button(vol_buttons, text="🔇 MUTE", font=('Arial', 11, 'bold'), width=10,
               bg=self.colors['warning'], fg='black',
               command=lambda: self.send_key('MUTE')).pack(side=LEFT, padx=3)

        Button(vol_buttons, text="🔊 VOL-", font=('Arial', 11, 'bold'), width=10,
               bg=self.colors['button'], fg=self.colors['text'],
               command=lambda: self.send_key('VOL_DOWN')).pack(side=LEFT, padx=3)

    def create_action_buttons(self):
        """Create action buttons for special functions"""
        action_frame = Frame(self.root, bg=self.colors['bg'])
        action_frame.pack(pady=10, fill=X, padx=10)

        # Connection management
        self.connect_btn = Button(action_frame, text="🔗 CONNECT TO TV",
                                font=('Arial', 11, 'bold'), width=28,
                                bg=self.colors['success'], fg='white',
                                command=self.attempt_connection)
        self.connect_btn.pack(pady=3)

        # TV functions
        Button(action_frame, text="📱 GO TO BLUETOOTH SETTINGS",
               font=('Arial', 10, 'bold'), width=28,
               bg=self.colors['accent'], fg='white',
               command=self.navigate_to_bluetooth).pack(pady=2)

        Button(action_frame, text="🔄 START PAIRING MODE",
               font=('Arial', 10, 'bold'), width=28,
               bg=self.colors['warning'], fg='black',
               command=self.start_pairing_mode).pack(pady=2)

        Button(action_frame, text="🔧 DIAGNOSE CONNECTION",
               font=('Arial', 10, 'bold'), width=28,
               bg=self.colors['button'], fg=self.colors['text'],
               command=self.diagnose_connection).pack(pady=2)

    def create_log_panel(self):
        """Create command log panel"""
        log_frame = Frame(self.root, bg=self.colors['bg'])
        log_frame.pack(pady=5, fill=X, padx=10)

        Label(log_frame, text="📋 ACTIVITY LOG:", font=('Arial', 9, 'bold'),
              fg=self.colors['text_secondary'], bg=self.colors['bg']).pack(anchor=W)

        self.log_text = Text(log_frame, height=6, width=60,
                            bg='#0a0a0a', fg=self.colors['text_secondary'],
                            font=('Courier', 8), wrap=WORD)
        self.log_text.pack(fill=X)

    def setup_bluetooth_connection(self):
        """Setup Bluetooth connection to TV"""
        self.log("🎬 Android TV Remote Started (Enhanced Version)")
        self.log(f"📱 Target: {self.tv_name} ({self.tv_mac_address})")
        self.log("🔧 Using improved connection methods...")

        # Auto-connect on startup
        threading.Thread(target=self.auto_connect, daemon=True).start()

    def auto_connect(self):
        """Attempt to auto-connect on startup"""
        time.sleep(2)  # Wait for GUI to load
        self.attempt_connection()

    def attempt_connection(self):
        """Attempt to connect using improved methods"""
        self.log("🔗 Attempting connection...")

        # Update UI to show connecting state
        self.status_label.config(text="🟡 CONNECTING...", fg=self.colors['warning'])
        self.root.update()

        # Run connection attempt in background
        def connect_bg():
            result = self.connector.connect_with_fallbacks()

            # Update UI based on result
            self.root.after(0, lambda: self.connection_result(result))

        threading.Thread(target=connect_bg, daemon=True).start()

    def connection_result(self, result):
        """Handle connection result"""
        if result is True:
            self.connected = True
            self.update_connection_status(True)
            info = self.connector.get_connection_info()
            self.method_label.config(text=f"Method: {info['method']}")
            self.log(f"✅ Connected successfully via {info['method']}")
        elif result == "manual":
            self.log("💡 Manual connection required - see instructions above")
            self.status_label.config(text="🟡 MANUAL SETUP", fg=self.colors['warning'])
        else:
            self.connected = False
            self.update_connection_status(False)
            self.log("❌ All connection methods failed - try diagnosis")

    def diagnose_connection(self):
        """Run connection diagnosis"""
        self.log("🔍 Running connection diagnosis...")
        status = self.connector.diagnose_connection()

        diagnosis_messages = {
            "connected": "✅ TV shows as connected but may not be responsive",
            "not_connected": "❌ TV found but not connected",
            "not_found": "❌ TV not found in Bluetooth devices",
            "error": "❌ Error during diagnosis"
        }

        self.log(f"Diagnosis: {diagnosis_messages.get(status, status)}")

        if status == "not_connected":
            self.log("💡 Try clicking 'CONNECT TO TV' to establish connection")
        elif status == "not_found":
            self.log("💡 Make sure TV is on and Bluetooth is enabled")

    def send_key(self, key_name):
        """Send key command to TV with enhanced feedback"""
        if not self.connected:
            self.log("❌ Not connected to TV - click CONNECT first")
            return

        keycode = self.keycodes.get(key_name.upper())
        if not keycode:
            self.log(f"❌ Unknown command: {key_name}")
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
                self.log(f"✅ [{timestamp}] Sent: {key_name}")
                self.flash_button_feedback(key_name)
            else:
                self.log(f"❌ [{timestamp}] Failed: {key_name} - {error}")

        except Exception as e:
            self.log(f"❌ [{timestamp}] Error: {key_name} - {e}")

    def flash_button_feedback(self, key_name):
        """Provide visual feedback for button press"""
        # This would temporarily change button color to show feedback
        pass

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
        self.log("🔄 Starting pairing mode for phone...")

        sequence = ['DOWN', 'DOWN', 'DOWN', 'SELECT']

        def send_pairing_sequence():
            time.sleep(1)
            for key in sequence:
                time.sleep(1)
                self.send_key(key)

        threading.Thread(target=send_pairing_sequence, daemon=True).start()

    def update_connection_status(self, connected):
        """Update connection status display"""
        if connected:
            self.status_label.config(text="🟢 CONNECTED & ACTIVE", fg=self.colors['success'])
            self.connect_btn.config(text="🔌 DISCONNECT", bg=self.colors['danger'])
        else:
            self.status_label.config(text="🔴 NOT CONNECTED", fg=self.colors['danger'])
            self.connect_btn.config(text="🔗 CONNECT TO TV", bg=self.colors['success'])
            self.method_label.config(text="Method: None")

        self.connected = connected

    def log(self, message):
        """Add message to activity log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"

        self.log_text.insert(END, log_entry)
        self.log_text.see(END)

        # Keep log size manageable
        lines = self.log_text.get(1.0, END).split('\n')
        if len(lines) > 50:
            self.log_text.delete(1.0, 2.0)

    def run(self):
        """Start the GUI application"""
        self.log("🚀 GUI ready - Click 'CONNECT TO TV' to begin")

        # Handle window closing
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Start main loop
        self.root.mainloop()

    def on_closing(self):
        """Handle window closing"""
        self.log("👋 Shutting down remote...")
        self.app_running = False
        if self.connected:
            self.connector.connected = False
        self.root.destroy()

def main():
    """Main entry point"""
    try:
        app = AndroidTVRemoteGUIFixed()
        app.run()
    except Exception as e:
        print(f"❌ Application error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()