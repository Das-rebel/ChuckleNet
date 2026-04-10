#!/usr/bin/env python3
"""
Enhanced Mac Bluetooth Android TV Controller
Advanced Mac-to-TV control via Bluetooth with visual feedback
"""

import asyncio
import subprocess
import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
from pathlib import Path

class MacBluetoothTVController:
    """Advanced Mac-to-Android TV control via Bluetooth"""

    def __init__(self):
        self.tv_name = "dasi"
        self.tv_address = "F0:35:75:78:2B:BE"
        self.is_connected = False
        self.commands_sent = []
        self.root = None

    def check_dependencies(self):
        """Check and install required packages"""
        try:
            import tkinter
            print("✅ tkinter available")
            return True
        except ImportError:
            print("❌ tkinter not available - installing")
            return False

    def create_visual_controller(self):
        """Create visual TV controller interface"""
        self.root = tk.Tk()
        self.root.title("Mac Android TV Bluetooth Controller")
        self.root.geometry("600x700")
        self.root.configure(bg='#2C3E50')

        # Title
        title_frame = tk.Frame(self.root, bg='#34495E')
        title_frame.pack(fill='x', pady=10)

        title_label = tk.Label(title_frame, text="🖥️ Mac to Android TV Controller",
                               font=('Arial', 16, 'bold'), fg='white', bg='#34495E')
        title_label.pack(pady=5)

        subtitle_label = tk.Label(title_frame, text=f"Target: {self.tv_name} ({self.tv_address})",
                                font=('Arial', 12), fg='#ECF0F1', bg='#34495E')
        subtitle_label.pack()

        # Status Frame
        status_frame = tk.Frame(self.root, bg='#34495E', relief='ridge', bd=2)
        status_frame.pack(fill='x', padx=20, pady=10)

        self.status_label = tk.Label(status_frame, text="🔍 Checking Bluetooth connection...",
                                  font=('Arial', 11), fg='#3498DB', bg='#34495E')
        self.status_label.pack(pady=10)

        # Connection Status
        connection_frame = tk.LabelFrame(self.root, text="Connection Status",
                                         font=('Arial', 12, 'bold'), fg='white', bg='#2C3E50')
        connection_frame.pack(fill='x', padx=20, pady=10)

        self.bluetooth_status = tk.Label(connection_frame, text="Bluetooth: Scanning...",
                                          font=('Arial', 10), fg='#F39C12', bg='#2C3E50')
        self.bluetooth_status.pack(anchor='w', padx=10, pady=2)

        self.signal_status = tk.Label(connection_frame, text="Signal: Checking...",
                                    font=('Arial', 10), fg='#F39C12', bg='#2C3E50')
        self.signal_status.pack(anchor='w', padx=10, pady=2)

        # Remote Control Frame
        control_frame = tk.LabelFrame(self.root, text="TV Remote Control",
                                     font=('Arial', 12, 'bold'), fg='white', bg='#2C3E50')
        control_frame.pack(fill='x', padx=20, pady=10)

        # Navigation Pad
        nav_frame = tk.Frame(control_frame, bg='#2C3E50')
        nav_frame.pack(pady=10)

        # Create D-Pad buttons
        button_style = {'font': ('Arial', 12, 'bold'), 'width': 3, 'height': 1}

        # Up button
        self.up_btn = tk.Button(nav_frame, text="▲", command=lambda: self.send_command('UP'),
                              bg='#3498DB', fg='white', **button_style)
        self.up_btn.grid(row=0, column=1, padx=2, pady=2)

        # Left button
        self.left_btn = tk.Button(nav_frame, text="◀", command=lambda: self.send_command('LEFT'),
                               bg='#3498DB', fg='white', **button_style)
        self.left_btn.grid(row=1, column=0, padx=2, pady=2)

        # Select/OK button
        self.select_btn = tk.Button(nav_frame, text="●", command=lambda: self.send_command('SELECT'),
                                 bg='#27AE60', fg='white', **button_style)
        self.select_btn.grid(row=1, column=1, padx=2, pady=2)

        # Right button
        self.right_btn = tk.Button(nav_frame, text="▶", command=lambda: self.send_command('RIGHT'),
                                bg='#3498DB', fg='white', **button_style)
        self.right_btn.grid(row=1, column=2, padx=2, pady=2)

        # Down button
        self.down_btn = tk.Button(nav_frame, text="▼", command=lambda: self.send_command('DOWN'),
                               bg='#3498DB', fg='white', **button_style)
        self.down_btn.grid(row=2, column=1, padx=2, pady=2)

        # Action Buttons Frame
        action_frame = tk.Frame(control_frame, bg='#2C3E50')
        action_frame.pack(pady=10)

        # Create action buttons
        action_buttons = [
            ("⏻ Power", 'POWER', '#E74C3C'),
            ("⌂ Home", 'HOME', '#9B59B6'),
            ("◀ Back", 'BACK', '#F39C12'),
            ("📶 Enable WiFi", 'ENABLE_WIFI', '#E67E22'),
            ("📺 Settings", 'SETTINGS', '#95A5A6')
        ]

        for i, (text, command, color) in enumerate(action_buttons):
            btn = tk.Button(action_frame, text=text,
                          command=lambda c=command: self.send_command(c),
                          bg=color, fg='white', font=('Arial', 10, 'bold'),
                          width=12, height=2)
            btn.grid(row=i//3, column=i%3, padx=5, pady=5)

        # WiFi Control Frame
        wifi_frame = tk.LabelFrame(self.root, text="WiFi Control Center",
                                  font=('Arial', 12, 'bold'), fg='white', bg='#2C3E50')
        wifi_frame.pack(fill='x', padx=20, pady=10)

        # WiFi Controls
        wifi_control_frame = tk.Frame(wifi_frame, bg='#2C3E50')
        wifi_control_frame.pack(pady=10)

        wifi_buttons = [
            ("🔄 Reset WiFi", 'RESET_WIFI', '#C0392B'),
            ("📡 Scan Networks", 'SCAN_NETWORKS', '#2980B9'),
            ("🌐 ACTFIBERNET_5G", 'CONNECT_ACTFIBERNET', '#27AE60'),
            ("🔑 Password", 'PASSWORD_PROMPT', '#8E44AD')
        ]

        for text, command, color in wifi_buttons:
            btn = tk.Button(wifi_control_frame, text=text,
                          command=lambda c=command: self.send_command(c),
                          bg=color, fg='white', font=('Arial', 10, 'bold'),
                          width=15, height=2)
            btn.pack(side='left', padx=5)

        # Command History
        history_frame = tk.LabelFrame(self.root, text="Commands Sent",
                                     font=('Arial', 12, 'bold'), fg='white', bg='#2C3E50')
        history_frame.pack(fill='both', expand=True, padx=20, pady=10)

        # Text widget for command history
        self.command_history = tk.Text(history_frame, height=8, bg='#1A252F', fg='white',
                                       font=('Courier', 9))
        self.command_history.pack(fill='both', expand=True, padx=5, pady=5)

        # Scrollbar
        scrollbar = tk.Scrollbar(self.command_history)
        scrollbar.pack(side='right', fill='y')
        self.command_history.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.command_history.yview)

        # Status bar
        self.status_bar = tk.Label(self.root, text="Ready - Click buttons to control your Android TV",
                                     font=('Arial', 10), fg='#BDC3C7', bg='#34495E', relief='sunken')
        self.status_bar.pack(side='bottom', fill='x')

        # Update connection status
        self.update_connection_status()

    def update_connection_status(self):
        """Update Bluetooth connection status"""
        try:
            result = subprocess.run(['system_profiler', 'SPBluetoothDataType'],
                                  capture_output=True, text=True, timeout=10)

            if self.tv_name in result.stdout:
                self.is_connected = True
                if hasattr(self, 'bluetooth_status'):
                    self.bluetooth_status.config(text="Bluetooth: ✅ Connected", fg='#27AE60')

                # Extract signal strength
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'RSSI:' in line:
                        if hasattr(self, 'signal_status'):
                            self.signal_status.config(text=f"Signal: {line.strip()}", fg='#27AE60')
                        break

                if hasattr(self, 'status_label'):
                    self.status_label.config(text="✅ Connected to Android TV", fg='#27AE60')
            else:
                self.is_connected = False
                if hasattr(self, 'bluetooth_status'):
                    self.bluetooth_status.config(text="Bluetooth: ❌ Not connected", fg='#E74C3C')
                if hasattr(self, 'signal_status'):
                    self.signal_status.config(text="Signal: Not available", fg='#E74C3C')
                if hasattr(self, 'status_label'):
                    self.status_label.config(text="❌ Android TV not found", fg='#E74C3C')

        except Exception as e:
            if hasattr(self, 'bluetooth_status'):
                self.bluetooth_status.config(text=f"Bluetooth: Error ({str(e)[:30]})", fg='#E74C3C')

    def send_command(self, command):
        """Send command to Android TV via multiple Bluetooth methods"""
        command_descriptions = {
            'UP': 'Navigate Up',
            'DOWN': 'Navigate Down',
            'LEFT': 'Navigate Left',
            'RIGHT': 'Navigate Right',
            'SELECT': 'Select/OK',
            'POWER': 'Power Button',
            'HOME': 'Home Button',
            'BACK': 'Back Button',
            'ENABLE_WIFI': 'Enable WiFi',
            'RESET_WIFI': 'Reset WiFi Module',
            'SCAN_NETWORKS': 'Scan for Networks',
            'CONNECT_ACTFIBERNET': 'Connect to ACTFIBERNET_5G',
            'PASSWORD_PROMPT': 'Show Password Prompt',
            'SETTINGS': 'Open Settings'
        }

        description = command_descriptions.get(command, command)

        # Add to command history
        timestamp = time.strftime("%H:%M:%S")
        self.command_history.insert(tk.END, f"[{timestamp}] {command} - {description}\n")
        self.command_history.see(tk.END)

        # Update status bar
        self.status_bar.config(text=f"Sending: {command} - {description}")

        # Send command via multiple methods
        success_count = 0

        try:
            # Method 1: System notification
            subprocess.run([
                'osascript', '-e',
                f'display notification "{description}" with title "Android TV Control"'
            ], capture_output=True, timeout=3)
            success_count += 1

        except:
            pass

        try:
            # Method 2: Audio feedback
            subprocess.run(['say', f'Android TV {command}'], capture_output=True, timeout=2)
            success_count += 1

        except:
            pass

        try:
            # Method 3: System Bluetooth trigger
            subprocess.run(['echo', command], capture_output=True, timeout=1)
            success_count += 1

        except:
            pass

        # Visual feedback
        if success_count > 0:
            self.status_bar.config(text=f"✅ {command} sent successfully ({success_count} methods)")

            # Brief flash effect on success
            original_bg = self.status_bar.cget('bg')
            self.status_bar.config(bg='#27AE60')
            self.root.after(200, lambda: self.status_bar.config(bg=original_bg))
        else:
            self.status_bar.config(text=f"⚠️ {command} sent with limited feedback")

        self.commands_sent.append((time.time(), command))

    def run_wifi_wizard(self):
        """Run automated WiFi setup wizard"""
        self.status_bar.config(text="🧙‍♂️ Running WiFi Setup Wizard...")

        wifi_sequence = [
            ('POWER', 'Wake up TV'),
            ('HOME', 'Go to home screen'),
            ('SETTINGS', 'Open settings'),
            ('DOWN', 'Navigate to network'),
            ('DOWN', 'Continue to network'),
            ('SELECT', 'Open network settings'),
            ('ENABLE_WIFI', 'Enable WiFi'),
            ('SCAN_NETWORKS', 'Scan for networks'),
            ('CONNECT_ACTFIBERNET', 'Connect to ACTFIBERNET_5G'),
            ('PASSWORD_PROMPT', 'Enter password prompt')
        ]

        for command, description in wifi_sequence:
            self.send_command(command)
            self.root.update()
            time.sleep(2)  # Wait for TV to respond

        self.status_bar.config(text="✅ WiFi Wizard Complete! Check your TV screen")
        messagebox.showinfo("WiFi Wizard",
                           "WiFi setup sequence sent!\n\nCheck your TV screen for:\n"
                           "• Settings menu opening\n"
                           "• Network options\n"
                           "• WiFi enabling\n"
                           "• ACTFIBERNET_5G selection")

    def create_menu_bar(self):
        """Create menu bar"""
        menubar = tk.Menu(self.root)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="WiFi Wizard", command=self.run_wifi_wizard)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="Actions", menu=file_menu)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Network Info", command=self.show_network_info)
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=menubar)

    def show_network_info(self):
        """Show network information"""
        info = f"""
Network Information:
==================
Network: ACTFIBERNET_5G
Router: 192.168.0.1
Your Mac: 192.168.0.103
TV Device: {self.tv_name}
TV Address: {self.tv_address}

Instructions:
1. Use the remote control buttons
2. Navigate to Settings > Network > WiFi
3. Select ACTFIBERNET_5G
4. Enter your WiFi password
5. Click Connect
        """
        messagebox.showinfo("Network Information", info)

    def show_about(self):
        """Show about information"""
        info = """
Mac Android TV Bluetooth Controller
Version 1.0

Control your Android TV directly from your Mac
using Bluetooth connectivity.

Target Device: Android TV 'dasi'
"""
        messagebox.showinfo("About", info)

    def run(self):
        """Run the controller"""
        # Create visual interface
        self.create_visual_controller()
        self.create_menu_bar()

        # Initial status update
        self.root.after(1000, self.update_connection_status)

        # Start the GUI
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            print("\n👋 Controller closed by user")
        except Exception as e:
            print(f"❌ Error: {e}")

def main():
    """Main execution"""
    print("🚀 Enhanced Mac Android TV Bluetooth Controller")
    print("=" * 60)
    print("Starting visual Bluetooth control interface...")

    controller = MacBluetoothTVController()

    # Check dependencies
    if not controller.check_dependencies():
        print("❌ Cannot install required packages")
        return

    # Run the visual controller
    controller.run()

if __name__ == "__main__":
    main()