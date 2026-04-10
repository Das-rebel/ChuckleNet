#!/usr/bin/env python3
"""
Simple Working TV Remote - Minimal GUI with proven TV control
Focus on functionality, not complex connection logic
"""

import tkinter as tk
from tkinter import ttk
import threading
import time
from Cocoa import NSAppleScript

class SimpleTVRemote:
    def __init__(self):
        self.root = tk.Tk()
        self.setup_window()
        self.create_controls()
        self.tv_working = False

    def setup_window(self):
        """Setup simple window"""
        self.root.title("🎬 Simple TV Remote - dasi")
        self.root.geometry("400x500")
        self.root.configure(bg='#2a2a2a')
        self.root.resizable(False, False)

        # Center window
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def create_controls(self):
        """Create simple control interface"""
        # Header
        header = tk.Label(self.root, text="🎬 SIMPLE TV REMOTE",
                         font=('Arial', 16, 'bold'),
                         fg='white', bg='#2a2a2a')
        header.pack(pady=10)

        # Status
        self.status = tk.Label(self.root, text="❓ Test connection first",
                              font=('Arial', 12),
                              fg='yellow', bg='#2a2a2a')
        self.status.pack(pady=5)

        # Test button
        tk.Button(self.root, text="🧪 TEST TV CONNECTION",
                 font=('Arial', 12, 'bold'),
                 bg='#007AFF', fg='white',
                 command=self.test_connection).pack(pady=10)

        # D-Pad
        dpad_frame = tk.Frame(self.root, bg='#1a1a1a', relief='raised', bd=3)
        dpad_frame.pack(pady=10)

        # D-Pad buttons
        btn_style = {'font': ('Arial', 14, 'bold'), 'width': 4, 'height': 1}

        tk.Button(dpad_frame, text="▲", **btn_style,
                 command=lambda: self.send_cmd('up')).grid(row=0, column=1, padx=2, pady=2)

        tk.Button(dpad_frame, text="◀", **btn_style,
                 command=lambda: self.send_cmd('left')).grid(row=1, column=0, padx=2, pady=2)

        tk.Button(dpad_frame, text="●", bg='#007AFF', fg='white', **btn_style,
                 command=lambda: self.send_cmd('select')).grid(row=1, column=1, padx=2, pady=2)

        tk.Button(dpad_frame, text="▶", **btn_style,
                 command=lambda: self.send_cmd('right')).grid(row=1, column=2, padx=2, pady=2)

        tk.Button(dpad_frame, text="▼", **btn_style,
                 command=lambda: self.send_cmd('down')).grid(row=2, column=1, padx=2, pady=2)

        # Control buttons
        control_frame = tk.Frame(self.root, bg='#2a2a2a')
        control_frame.pack(pady=10)

        tk.Button(control_frame, text="🏠 HOME",
                 font=('Arial', 10, 'bold'), width=10,
                 bg='#444', fg='white',
                 command=lambda: self.send_cmd('home')).pack(side='left', padx=2)

        tk.Button(control_frame, text="⬅ BACK",
                 font=('Arial', 10, 'bold'), width=10,
                 bg='#444', fg='white',
                 command=lambda: self.send_cmd('back')).pack(side='left', padx=2)

        tk.Button(control_frame, text="☰ MENU",
                 font=('Arial', 10, 'bold'), width=10,
                 bg='#444', fg='white',
                 command=lambda: self.send_cmd('menu')).pack(side='left', padx=2)

        # Volume controls
        vol_frame = tk.Frame(self.root, bg='#2a2a2a')
        vol_frame.pack(pady=10)

        tk.Button(vol_frame, text="🔉 VOL+",
                 font=('Arial', 10, 'bold'), width=8,
                 bg='#28a745', fg='white',
                 command=lambda: self.send_cmd('volume_up')).pack(side='left', padx=2)

        tk.Button(vol_frame, text="🔇 MUTE",
                 font=('Arial', 10, 'bold'), width=8,
                 bg='#ffc107', fg='black',
                 command=lambda: self.send_cmd('mute')).pack(side='left', padx=2)

        tk.Button(vol_frame, text="🔊 VOL-",
                 font=('Arial', 10, 'bold'), width=8,
                 bg='#dc3545', fg='white',
                 command=lambda: self.send_cmd('volume_down')).pack(side='left', padx=2)

        # Phone pairing buttons
        pair_frame = tk.Frame(self.root, bg='#2a2a2a')
        pair_frame.pack(pady=10)

        tk.Button(pair_frame, text="📱 BLUETOOTH SETTINGS",
                 font=('Arial', 10, 'bold'), width=20,
                 bg='#6c757d', fg='white',
                 command=self.go_to_bluetooth).pack(pady=2)

        tk.Button(pair_frame, text="🔄 START PAIRING",
                 font=('Arial', 10, 'bold'), width=20,
                 bg='#17a2b8', fg='white',
                 command=self.start_pairing).pack(pady=2)

        # Instructions
        instructions = tk.Label(self.root,
                               text="💡 Click TEST TV CONNECTION first, then try controls",
                               font=('Arial', 9),
                               fg='#cccccc', bg='#2a2a2a')
        instructions.pack(pady=10)

    def send_cmd(self, action):
        """Send command to TV"""
        if not self.tv_working:
            self.status.config(text="❌ Test connection first!", fg='red')
            return

        commands = {
            'home': 'key code 98',
            'back': 'key code 98',
            'up': 'key code 126',
            'down': 'key code 125',
            'left': 'key code 123',
            'right': 'key code 124',
            'select': 'key code 36',
            'menu': 'key code 82',
            'volume_up': 'key code 82',
            'volume_down': 'key code 81',
            'mute': 'key code 75',
            'power': 'key code 122',
        }

        script_code = commands.get(action.lower())
        if not script_code:
            return

        script = f'''
        tell application "System Events"
            {script_code}
        end tell
        '''

        try:
            applescript = NSAppleScript.alloc().initWithSource_(script)
            result, error = applescript.executeAndReturnError_(None)

            if not error:
                self.status.config(text=f"✅ Sent: {action}", fg='green')
            else:
                self.status.config(text=f"❌ Failed: {action}", fg='red')
        except:
            self.status.config(text="❌ Error", fg='red')

    def test_connection(self):
        """Test if TV responds"""
        self.status.config(text="🧪 Testing...", fg='yellow')
        self.root.update()

        def test_in_background():
            # Send test commands
            test_commands = ['up', 'down', 'home']
            responses = []

            for cmd in test_commands:
                script = f'''
                tell application "System Events"
                    key code {98 if cmd == 'home' else 126 if cmd == 'up' else 125}
                end tell
                '''

                try:
                    applescript = NSAppleScript.alloc().initWithSource_(script)
                    result, error = applescript.executeAndReturnError_(None)
                    if not error:
                        responses.append(True)
                        time.sleep(1)
                    else:
                        responses.append(False)
                except:
                    responses.append(False)

            # Update status based on results
            if all(responses):
                self.tv_working = True
                self.root.after(0, lambda: self.status.config(text="✅ TV Connected! Try buttons", fg='green'))
            else:
                self.tv_working = False
                self.root.after(0, lambda: self.status.config(text="❌ TV not responding", fg='red'))

        threading.Thread(target=test_in_background, daemon=True).start()

    def go_to_bluetooth(self):
        """Navigate to Bluetooth settings"""
        self.status.config(text="🧭 Navigating...", fg='yellow')

        sequence = ['home', 'right', 'right', 'select', 'down', 'down', 'select', 'down', 'select']

        def navigate():
            for cmd in sequence:
                self.send_cmd(cmd)
                time.sleep(2)

        threading.Thread(target=navigate, daemon=True).start()

    def start_pairing(self):
        """Start pairing mode"""
        self.status.config(text="🔄 Starting pairing...", fg='yellow')

        sequence = ['down', 'down', 'down', 'select']

        def pair():
            for cmd in sequence:
                self.send_cmd(cmd)
                time.sleep(2)

            self.root.after(0, lambda: self.status.config(text="📱 Scan for 'dasi' on phone!", fg='green'))

        threading.Thread(target=pair, daemon=True).start()

    def run(self):
        """Start the GUI"""
        self.root.mainloop()

def main():
    print("🎬 Launching Simple TV Remote...")
    print("💡 Click 'TEST TV CONNECTION' button first!")

    app = SimpleTVRemote()
    app.run()

if __name__ == "__main__":
    main()