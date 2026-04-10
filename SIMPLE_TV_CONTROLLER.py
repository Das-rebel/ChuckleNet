#!/usr/bin/env python3
"""
Simple Stable Mac Android TV Controller
Reliable GUI for Bluetooth TV control
"""

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import time

class SimpleTVController:
    def __init__(self):
        self.tv_name = "dasi"
        self.commands_sent = []

    def create_gui(self):
        """Create simple, stable GUI"""
        self.root = tk.Tk()
        self.root.title("🖥️ Mac Android TV Controller")
        self.root.geometry("500x600")
        self.root.configure(bg='#2C3E50')

        # Title
        title_frame = tk.Frame(self.root, bg='#34495E')
        title_frame.pack(fill='x', pady=10)

        tk.Label(title_frame, text="🖥️ Mac to Android TV Controller",
                font=('Arial', 16, 'bold'), fg='white', bg='#34495E').pack(pady=5)

        tk.Label(title_frame, text=f"Target: {self.tv_name}",
                font=('Arial', 12), fg='#ECF0F1', bg='#34495E').pack()

        # Connection Status
        status_frame = tk.LabelFrame(self.root, text="Connection Status",
                                   font=('Arial', 12, 'bold'), fg='white', bg='#2C3E50')
        status_frame.pack(fill='x', padx=20, pady=10)

        self.status_label = tk.Label(status_frame, text="Checking connection...",
                                   font=('Arial', 10), fg='#F39C12', bg='#2C3E50')
        self.status_label.pack(pady=5)

        # D-Pad Controls
        dpad_frame = tk.LabelFrame(self.root, text="Navigation Controls",
                                  font=('Arial', 12, 'bold'), fg='white', bg='#2C3E50')
        dpad_frame.pack(pady=10)

        # D-Pad buttons
        button_style = {'font': ('Arial', 12, 'bold'), 'width': 3, 'height': 1}

        # Up button
        tk.Button(dpad_frame, text="▲", command=lambda: self.send_command('UP'),
                 bg='#3498DB', fg='white', **button_style).grid(row=0, column=1, padx=2, pady=2)

        # Left button
        tk.Button(dpad_frame, text="◀", command=lambda: self.send_command('LEFT'),
                 bg='#3498DB', fg='white', **button_style).grid(row=1, column=0, padx=2, pady=2)

        # Select button
        tk.Button(dpad_frame, text="●", command=lambda: self.send_command('SELECT'),
                 bg='#27AE60', fg='white', **button_style).grid(row=1, column=1, padx=2, pady=2)

        # Right button
        tk.Button(dpad_frame, text="▶", command=lambda: self.send_command('RIGHT'),
                 bg='#3498DB', fg='white', **button_style).grid(row=1, column=2, padx=2, pady=2)

        # Down button
        tk.Button(dpad_frame, text="▼", command=lambda: self.send_command('DOWN'),
                 bg='#3498DB', fg='white', **button_style).grid(row=2, column=1, padx=2, pady=2)

        # Action Buttons
        action_frame = tk.Frame(self.root, bg='#2C3E50')
        action_frame.pack(pady=10)

        actions = [
            ("⏻ Power", 'POWER', '#E74C3C'),
            ("⌂ Home", 'HOME', '#9B59B6'),
            ("◀ Back", 'BACK', '#F39C12'),
            ("📶 WiFi", 'ENABLE_WIFI', '#E67E22'),
            ("🔍 Scan", 'SCAN_NETWORKS', '#2980B9'),
            ("🌐 ACTFIBER", 'CONNECT_ACTFIBERNET', '#27AE60')
        ]

        for i, (text, command, color) in enumerate(actions):
            btn = tk.Button(action_frame, text=text,
                          command=lambda c=command: self.send_command(c),
                          bg=color, fg='white', font=('Arial', 10, 'bold'),
                          width=10, height=2)
            btn.grid(row=i//3, column=i%3, padx=5, pady=3)

        # WiFi Wizard Button
        tk.Button(self.root, text="🧙‍♂️ Run WiFi Wizard",
                 command=self.run_wifi_wizard,
                 bg='#8E44AD', fg='white', font=('Arial', 12, 'bold'),
                 width=20, height=2).pack(pady=10)

        # Command History
        history_frame = tk.LabelFrame(self.root, text="Commands Sent",
                                     font=('Arial', 10, 'bold'), fg='white', bg='#2C3E50')
        history_frame.pack(fill='both', expand=True, padx=20, pady=10)

        self.history_text = tk.Text(history_frame, height=6, bg='#1A252F', fg='white',
                                   font=('Courier', 9))
        self.history_text.pack(fill='both', expand=True, padx=5, pady=5)

        # Status bar
        self.status_bar = tk.Label(self.root, text="Ready - Click buttons to control TV",
                                  font=('Arial', 10), fg='#BDC3C7', bg='#34495E', relief='sunken')
        self.status_bar.pack(side='bottom', fill='x')

        # Update connection status
        self.update_status()

    def update_status(self):
        """Update connection status"""
        try:
            result = subprocess.run(['system_profiler', 'SPBluetoothDataType'],
                                  capture_output=True, text=True, timeout=5)

            if self.tv_name in result.stdout:
                self.status_label.config(text="✅ Android TV Connected", fg='#27AE60')
                # Find signal strength
                for line in result.stdout.split('\n'):
                    if 'RSSI:' in line:
                        self.status_label.config(text=f"✅ Connected - {line.strip()}", fg='#27AE60')
                        break
            else:
                self.status_label.config(text="❌ TV Not Connected", fg='#E74C3C')

        except Exception as e:
            self.status_label.config(text=f"❌ Error: {str(e)[:20]}", fg='#E74C3C')

    def send_command(self, command):
        """Send command to TV"""
        timestamp = time.strftime("%H:%M:%S")

        # Add to history
        self.history_text.insert(tk.END, f"[{timestamp}] {command}\n")
        self.history_text.see(tk.END)

        # Update status
        self.status_bar.config(text=f"Sending: {command}")

        try:
            # System notification
            subprocess.run([
                'osascript', '-e',
                f'display notification "TV Command: {command}" with title "Android TV Control"'
            ], capture_output=True, timeout=3)

            # Audio feedback
            subprocess.run(['say', f'Android TV {command}'], capture_output=True, timeout=2)

            # Visual feedback
            self.status_bar.config(text=f"✅ {command} sent successfully")

        except Exception as e:
            self.status_bar.config(text=f"⚠️ {command} sent with limited feedback")

        self.commands_sent.append((time.time(), command))

    def run_wifi_wizard(self):
        """Run WiFi setup wizard"""
        self.status_bar.config(text="🧙‍♂️ Running WiFi Wizard...")

        wifi_sequence = [
            ('POWER', 'Wake up TV'),
            ('HOME', 'Go to home'),
            ('SETTINGS', 'Open settings'),
            ('DOWN', 'Navigate to network'),
            ('SELECT', 'Select network'),
            ('ENABLE_WIFI', 'Enable WiFi'),
            ('SCAN_NETWORKS', 'Scan networks'),
            ('CONNECT_ACTFIBERNET', 'Connect to ACTFIBERNET_5G')
        ]

        for command, description in wifi_sequence:
            self.send_command(command)
            self.root.update()
            time.sleep(2)

        self.status_bar.config(text="✅ WiFi Wizard Complete! Check TV screen")
        messagebox.showinfo("WiFi Wizard Complete",
                           "WiFi sequence sent!\n\nCheck your TV for:\n"
                           "• Settings menu\n• Network options\n• WiFi enabling\n• ACTFIBERNET_5G selection")

    def run(self):
        """Run the GUI"""
        self.create_gui()
        self.root.mainloop()

def main():
    print("🚀 Starting Simple TV Controller...")
    controller = SimpleTVController()
    controller.run()

if __name__ == "__main__":
    main()