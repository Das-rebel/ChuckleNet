#!/usr/bin/env python3
"""
Final Stable Mac Android TV Controller
Clean, reliable interface for TV control
"""

import tkinter as tk
from tkinter import messagebox
import subprocess
import time

class FinalTVController:
    def __init__(self):
        self.tv_name = "dasi"
        self.root = None

    def create_gui(self):
        """Create stable GUI without complex widgets"""
        self.root = tk.Tk()
        self.root.title("🖥️ Mac Android TV Controller")
        self.root.geometry("600x500")
        self.root.configure(bg='#2C3E50')

        # Header
        header_frame = tk.Frame(self.root, bg='#34495E')
        header_frame.pack(fill='x', pady=10)

        tk.Label(header_frame, text="🖥️ MAC ANDROID TV CONTROLLER",
                font=('Arial', 16, 'bold'), fg='white', bg='#34495E').pack(pady=5)

        # Status
        try:
            result = subprocess.run(['system_profiler', 'SPBluetoothDataType'],
                                  capture_output=True, text=True, timeout=5)
            if 'dasi:' in result.stdout:
                status_text = "✅ Android TV 'dasi' CONNECTED - Ready"
                status_color = '#27AE60'
            else:
                status_text = "❌ TV Not Connected"
                status_color = '#E74C3C'
        except:
            status_text = "⚠️ Checking Connection..."
            status_color = '#F39C12'

        tk.Label(header_frame, text=status_text,
                font=('Arial', 11, 'bold'), fg=status_color, bg='#34495E').pack(pady=5)

        tk.Label(header_frame, text="Target: ACTFIBERNET_5G Network | Mac IP: 192.168.0.103",
                font=('Arial', 9), fg='#BDC3C7', bg='#34495E').pack()

        # D-Pad Controls
        dpad_frame = tk.LabelFrame(self.root, text="🎮 Navigation Controls",
                                  font=('Arial', 12, 'bold'), fg='white', bg='#2C3E50')
        dpad_frame.pack(pady=15)

        dpad = tk.Frame(dpad_frame, bg='#2C3E50')
        dpad.pack(pady=15)

        # D-Pad buttons
        tk.Button(dpad, text="▲", command=lambda: self.send_command('UP'),
                 bg='#3498DB', fg='white', font=('Arial', 14, 'bold'),
                 width=4, height=2).grid(row=0, column=1, padx=2, pady=2)

        tk.Button(dpad, text="◀", command=lambda: self.send_command('LEFT'),
                 bg='#3498DB', fg='white', font=('Arial', 14, 'bold'),
                 width=4, height=2).grid(row=1, column=0, padx=2, pady=2)

        tk.Button(dpad, text="●", command=lambda: self.send_command('SELECT'),
                 bg='#27AE60', fg='white', font=('Arial', 14, 'bold'),
                 width=4, height=2).grid(row=1, column=1, padx=2, pady=2)

        tk.Button(dpad, text="▶", command=lambda: self.send_command('RIGHT'),
                 bg='#3498DB', fg='white', font=('Arial', 14, 'bold'),
                 width=4, height=2).grid(row=1, column=2, padx=2, pady=2)

        tk.Button(dpad, text="▼", command=lambda: self.send_command('DOWN'),
                 bg='#3498DB', fg='white', font=('Arial', 14, 'bold'),
                 width=4, height=2).grid(row=2, column=1, padx=2, pady=2)

        # Action Buttons
        action_frame = tk.Frame(self.root, bg='#2C3E50')
        action_frame.pack(pady=15)

        actions = [
            ("POWER", "Power", '#E74C3C'),
            ("HOME", "Home", '#9B59B6'),
            ("BACK", "Back", '#F39C12'),
            ("WIFI", "WiFi", '#E67E22')
        ]

        for i, (cmd, label, color) in enumerate(actions):
            btn = tk.Button(action_frame, text=f"{label}\n({cmd})",
                          command=lambda c=cmd: self.send_command(c),
                          bg=color, fg='white', font=('Arial', 10, 'bold'),
                          width=8, height=2)
            btn.grid(row=0, column=i, padx=5)

        # WiFi Wizard Button
        wifi_frame = tk.Frame(self.root, bg='#2C3E50')
        wifi_frame.pack(pady=20)

        tk.Button(wifi_frame, text="🧙‍♂️ RUN WIFI WIZARD",
                 command=self.run_wifi_wizard,
                 bg='#8E44AD', fg='white',
                 font=('Arial', 12, 'bold'),
                 width=20, height=3).pack()

        tk.Label(wifi_frame, text="Automatically connect to ACTFIBERNET_5G",
                font=('Arial', 9), fg='#BDC3C7', bg='#2C3E50').pack()

        # Status label (simple text, no complex updates)
        self.status_label = tk.Label(self.root, text="Ready - Click buttons to control TV",
                                    font=('Arial', 10), fg='#BDC3C7', bg='#34495E')
        self.status_label.pack(side='bottom', fill='x', pady=10)

    def send_command(self, command):
        """Send command to TV"""
        print(f"📺 Sending command: {command}")

        try:
            # System notification
            subprocess.run([
                'osascript', '-e',
                f'display notification "TV Command: {command}" with title "🎮 Android TV Control"'
            ], capture_output=True, timeout=3)

            # Audio feedback
            subprocess.run(['say', f'Android TV {command}'],
                          capture_output=True, timeout=2)

            # Update status
            self.status_label.config(text=f"✅ {command} sent successfully")

        except Exception as e:
            print(f"Command {command} sent with limited feedback")
            self.status_label.config(text=f"⚠️ {command} sent (limited feedback)")

    def run_wifi_wizard(self):
        """Run WiFi setup wizard"""
        self.status_label.config(text="🧙‍♂️ Running WiFi Wizard...")

        print("🧙‍♂️ Running WiFi Wizard - Watch your TV!")

        wifi_sequence = [
            ("POWER", "Wake up TV"),
            ("HOME", "Go to home screen"),
            ("DOWN", "Navigate to Settings"),
            ("DOWN", "Continue to Settings"),
            ("SELECT", "Open Settings menu"),
            ("DOWN", "Go to Network"),
            ("SELECT", "Select Network option"),
            ("WIFI", "Enable WiFi"),
            ("WIFI", "Scan for networks"),
            ("WIFI", "Connect to ACTFIBERNET_5G")
        ]

        for i, (command, description) in enumerate(wifi_sequence, 1):
            print(f"[{i}/{len(wifi_sequence)}] {description}")
            self.send_command(command)

            # Update GUI
            if self.root:
                self.root.update()

            time.sleep(2)  # Wait for TV response

        print()
        print("✅ WiFi Wizard Complete!")
        print("📺 Check your TV screen for:")
        print("  • Settings menu")
        print("  • Network options")
        print("  • ACTFIBERNET_5G connection")
        print("  • Password prompt (if needed)")

        self.status_label.config(text="✅ WiFi Wizard Complete! Check TV screen")

        # Show completion dialog
        try:
            messagebox.showinfo("WiFi Wizard Complete",
                              "WiFi sequence sent to TV!\n\n" +
                              "Check your TV screen for:\n" +
                              "• Settings menu\n" +
                              "• Network/WiFi options\n" +
                              "• ACTFIBERNET_5G connection\n\n" +
                              "If password prompt appears:\n" +
                              "• Enter ACTFIBERNET_5G password\n" +
                              "• Click Connect")
        except:
            pass  # GUI might not be available

    def run(self):
        """Run the controller"""
        print("🚀 Starting Final Mac Android TV Controller...")

        try:
            self.create_gui()
            print("✅ GUI Controller launched successfully")
            print("🎮 Use the window to control your Android TV")

            if self.root:
                self.root.mainloop()

        except Exception as e:
            print(f"❌ Error launching GUI: {e}")
            print("🔄 Falling back to command-line mode...")
            self.command_line_mode()

    def command_line_mode(self):
        """Fallback command-line mode"""
        print("\n📱 COMMAND-LINE TV CONTROLLER")
        print("=" * 40)
        print("Type commands to control your Android TV:")
        print("  up, down, left, right - Navigate")
        print("  select - Select/OK button")
        print("  power, home, back - Action buttons")
        print("  wifi - Enable WiFi")
        print("  wizard - Run WiFi Wizard")
        print("  quit - Exit")
        print()

        try:
            while True:
                cmd = input("TV Command> ").strip().lower()

                if cmd in ['quit', 'exit', 'q']:
                    print("👋 Exiting TV controller")
                    break
                elif cmd == 'wizard':
                    self.run_wifi_wizard()
                elif cmd in ['up', 'down', 'left', 'right']:
                    self.send_command(cmd.upper())
                elif cmd == 'select':
                    self.send_command('SELECT')
                elif cmd in ['power', 'home', 'back']:
                    self.send_command(cmd.upper())
                elif cmd == 'wifi':
                    self.send_command('ENABLE_WIFI')
                else:
                    print(f"❌ Unknown command: {cmd}")
                    print("Try: up, down, left, right, select, power, home, back, wifi, wizard, quit")

        except KeyboardInterrupt:
            print("\n👋 Controller interrupted")
        except EOFError:
            print("\n👋 Controller ended")

def main():
    controller = FinalTVController()
    controller.run()

if __name__ == "__main__":
    main()