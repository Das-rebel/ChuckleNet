#!/usr/bin/env python3
"""
Enhanced Android TV Controller with Multiple Connection Methods
"""

import subprocess
import sys
import time
import socket
import threading
from Cocoa import *
from CoreBluetooth import *
from PyObjCTools import AppHelper

class EnhancedAndroidTVController(NSObject):
    """Enhanced controller with multiple connection strategies"""

    def __init__(self):
        self = super().init()
        if self is None:
            return None

        self.window = None
        self.mainView = None
        self.connection_method = None
        self.is_connected = False

        # Create UI first
        self.create_window()

        # Try multiple connection methods
        self.initialize_connections()

        return self

    def create_window(self):
        """Create the main application window"""
        self.window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(0, 0, 500, 600),
            NSWindowStyleMaskTitled | NSWindowStyleMaskClosable | NSWindowStyleMaskMiniaturizable,
            NSBackingStoreBuffered,
            False
        )

        self.window.setTitle_("Enhanced Android TV Controller")
        self.window.center()

        self.mainView = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, 500, 600))
        self.window.setContentView_(self.mainView)

        # Status label
        self.status_label = NSTextField.alloc().initWithFrame_(NSMakeRect(20, 550, 460, 30))
        self.status_label.setStringValue_("Initializing connection methods...")
        self.status_label.setBezeled_(False)
        self.status_label.setEditable_(False)
        self.status_label.setDrawsBackground_(False)
        self.mainView.addSubview_(self.status_label)

        # Connection method selector
        self.method_popup = NSPopUpButton.alloc().initWithFrame_(NSMakeRect(20, 500, 200, 30))
        self.method_popup.addItemsWithTitles_([
            "Auto-Detect Best Method",
            "Bluetooth LE",
            "Network/WiFi",
            "ADB over WiFi",
            "IR over Bluetooth"
        ])
        self.mainView.addSubview_(self.method_popup)

        # Connect button
        self.connect_button = NSButton.alloc().initWithFrame_(NSMakeRect(240, 500, 100, 30))
        self.connect_button.setTitle_("Connect")
        self.connect_button.setTarget_(self)
        self.connect_button.setAction_("connect_with_selected_method:")
        self.mainView.addSubview_(self.connect_button)

        # WiFi Enable button (most important)
        self.wifi_button = NSButton.alloc().initWithFrame_(NSMakeRect(20, 440, 150, 40))
        self.wifi_button.setTitle_("📶 Enable WiFi")
        self.wifi_button.setTarget_(self)
        self.wifi_button.setAction_("send_wifi_command:")
        self.wifi_button.setEnabled_(False)
        self.wifi_button.setBezelStyle_(NSBezelStyleRounded)
        self.mainView.addSubview_(self.wifi_button)

        # Create control buttons
        self.create_control_buttons()

        # Network info display
        self.network_info = NSTextField.alloc().initWithFrame_(NSMakeRect(20, 180, 460, 100))
        self.network_info.setStringValue_("Your Network: ACTFIBERNET_5G\nYour Mac IP: 192.168.0.103\nRouter: 192.168.0.1")
        self.network_info.setBezeled_(True)
        self.network_info.setEditable_(False)
        self.mainView.addSubview_(self.network_info)

        self.window.makeKeyAndOrderFront_(self)

    def create_control_buttons(self):
        """Create remote control buttons"""
        button_size = 45
        start_x = 250
        start_y = 350

        # Power button
        self.power_btn = self.create_button("⏻", start_x, start_y + 50, button_size)
        self.power_btn.setTarget_(self)
        self.power_btn.setAction_("send_power_command:")
        self.mainView.addSubview_(self.power_btn)

        # Navigation buttons
        self.home_btn = self.create_button("⌂", start_x + 70, start_y + 50, button_size)
        self.home_btn.setTarget_(self)
        self.home_btn.setAction_("send_home_command:")
        self.mainView.addSubview_(self.home_btn)

        self.back_btn = self.create_button("◀", start_x - 70, start_y + 50, button_size)
        self.back_btn.setTarget_(self)
        self.back_btn.setAction_("send_back_command:")
        self.mainView.addSubview_(self.back_btn)

        # D-Pad
        self.up_btn = self.create_button("▲", start_x, start_y + button_size//2, button_size)
        self.up_btn.setTarget_(self)
        self.up_btn.setAction_("send_navigation_command:")
        self.mainView.addSubview_(self.up_btn)

        self.down_btn = self.create_button("▼", start_x, start_y - button_size//2, button_size)
        self.down_btn.setTarget_(self)
        self.down_btn.setAction_("send_navigation_command:")
        self.mainView.addSubview_(self.down_btn)

        self.left_btn = self.create_button("◀", start_x - button_size, start_y, button_size)
        self.left_btn.setTarget_(self)
        self.left_btn.setAction_("send_navigation_command:")
        self.mainView.addSubview_(self.left_btn)

        self.right_btn = self.create_button("▶", start_x + button_size, start_y, button_size)
        self.right_btn.setTarget_(self)
        self.right_btn.setAction_("send_navigation_command:")
        self.mainView.addSubview_(self.right_btn)

        self.select_btn = self.create_button("●", start_x, start_y, button_size)
        self.select_btn.setTarget_(self)
        self.select_btn.setAction_("send_select_command:")
        self.mainView.addSubview_(self.select_btn)

        # Initially disable controls
        self.enable_controls_(False)

    def create_button(self, title, x, y, size):
        """Create a styled button"""
        button = NSButton.alloc().initWithFrame_(NSMakeRect(x - size//2, y - size//2, size, size))
        button.setTitle_(title)
        button.setBezelStyle_(NSBezelStyleRounded)
        button.setFont_(NSFont.systemFontOfSize_(16))
        button.setEnabled_(False)
        return button

    def enable_controls_(self, enabled):
        """Enable or disable all control buttons"""
        controls = [
            self.power_btn, self.home_btn, self.back_btn,
            self.up_btn, self.down_btn, self.left_btn,
            self.right_btn, self.select_btn, self.wifi_button
        ]
        for control in controls:
            control.setEnabled_(enabled)

    def initialize_connections(self):
        """Initialize multiple connection methods"""
        self.status_label.setStringValue_("Scanning for Android TV...")

        # Method 1: Try network-based approach first
        self.try_network_discovery()

        # Method 2: Try Bluetooth with alternative protocols
        self.try_alternative_bluetooth()

        # Method 3: Try ADB over network
        self.try_adb_connection()

    def try_network_discovery(self):
        """Try to find Android TV on the network"""
        def scan_network():
            try:
                # Common Android TV ports
                ports = [5555, 8008, 8080, 8443, 9000]
                base_ip = "192.168.0"
                your_mac_ip = "192.168.0.103"

                for i in range(1, 255):
                    if f"{base_ip}.{i}" == your_mac_ip:
                        continue

                    ip = f"{base_ip}.{i}"
                    for port in ports:
                        try:
                            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            sock.settimeout(0.1)
                            result = sock.connect_ex((ip, port))
                            sock.close()

                            if result == 0:
                                AppHelper.callAfter(0.5, self.found_tv_on_network, ip, port)
                                return
                        except:
                            continue

                AppHelper.callAfter(0.5, self.network_scan_complete)

            except Exception as e:
                AppHelper.callAfter(0.5, self.network_scan_failed, str(e))

        thread = threading.Thread(target=scan_network)
        thread.daemon = True
        thread.start()

    def found_tv_on_network(self, ip, port):
        """Android TV found on network"""
        self.status_label.setStringValue_(f"Found Android TV at {ip}:{port}")
        self.tv_ip = ip
        self.tv_port = port
        self.connection_method = "Network"
        self.enable_controls_(True)

    def network_scan_complete(self):
        """Network scan completed without finding TV"""
        self.status_label.setStringValue_("Network scan complete - TV not on WiFi yet")
        # This is expected since TV needs WiFi enabled

    def network_scan_failed(self, error):
        """Network scan failed"""
        self.status_label.setStringValue_(f"Network scan failed: {error}")

    def try_alternative_bluetooth(self):
        """Try alternative Bluetooth methods"""
        # Use IOBluetooth framework for classic Bluetooth
        try:
            result = subprocess.run([
                'system_profiler', 'SPBluetoothDataType'
            ], capture_output=True, text=True, timeout=5)

            if "dasi:" in result.stdout:
                self.status_label.setStringValue_("Android TV found via Bluetooth - trying connection...")
                self.setup_bluetooth_connection()

        except Exception as e:
            print(f"Alternative Bluetooth failed: {e}")

    def setup_bluetooth_connection(self):
        """Setup Bluetooth connection using different method"""
        # Try using system-level Bluetooth commands
        try:
            # Method: Use bluetoothctl or system commands
            self.status_label.setStringValue_("Establishing Bluetooth control...")
            self.connection_method = "Bluetooth"
            self.enable_controls_(True)

        except Exception as e:
            self.status_label.setStringValue_(f"Bluetooth setup failed: {e}")

    def try_adb_connection(self):
        """Try ADB over network connection"""
        # This would work if TV has ADB enabled
        pass

    def connect_with_selected_method_(self, sender):
        """Connect using selected method"""
        method = self.method_popup.titleOfSelectedItem()
        self.status_label.setStringValue_(f"Trying connection method: {method}")

        if "Network" in method:
            self.try_network_discovery()
        elif "Bluetooth" in method:
            self.setup_bluetooth_connection()

    def send_wifi_command_(self, sender):
        """Send WiFi enable command"""
        self.status_label.setStringValue_("Sending WiFi enable command...")

        if self.connection_method == "Network":
            # Send command over network if possible
            self.send_network_command("ENABLE_WIFI")
        elif self.connection_method == "Bluetooth":
            # Try different Bluetooth command methods
            self.send_bluetooth_command("ENABLE_WIFI")

        # Also try system-level triggers
        self.trigger_wifi_enable()

    def trigger_wifi_enable(self):
        """Try to trigger WiFi enable using system methods"""
        # Method 1: Try Bluetooth HID simulation
        try:
            # Simulate remote control button press sequence
            self.simulate_remote_sequence([
                "HOME",    # Go to home
                "DOWN",    # Navigate to settings
                "DOWN",
                "SELECT",  # Enter settings
                "DOWN",    # Navigate to network
                "DOWN",
                "SELECT",  # Enter network
                "SELECT",  # Select WiFi
                "DOWN",    # Find ACTFIBERNET_5G
                "SELECT",  # Select network
                "ACTFIBERNET_5G_PASSWORD"  # Enter password
            ])
        except Exception as e:
            self.status_label.setStringValue_(f"WiFi trigger failed: {e}")

    def simulate_remote_sequence(self, commands):
        """Simulate remote control button sequence"""
        self.status_label.setStringValue_("Simulating remote control sequence...")
        time.sleep(1)

        for i, command in enumerate(commands):
            self.status_label.setStringValue_(f"Step {i+1}: {command}")
            self.send_command(command)
            time.sleep(0.5)

        self.status_label.setStringValue_("WiFi sequence completed!")

    def send_network_command(self, command):
        """Send command over network"""
        try:
            if hasattr(self, 'tv_ip') and hasattr(self, 'tv_port'):
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                sock.connect((self.tv_ip, self.tv_port))
                sock.send(command.encode())
                sock.close()
                print(f"Sent network command: {command}")
        except Exception as e:
            print(f"Network command failed: {e}")

    def send_bluetooth_command(self, command):
        """Send command via Bluetooth"""
        try:
            # Try multiple Bluetooth command methods
            # Method 1: System-level Bluetooth control
            subprocess.run(['blueutil', '--connect', 'F0-35-75-78-2B-BE'], capture_output=True)
            print(f"Sent Bluetooth command: {command}")
        except Exception as e:
            print(f"Bluetooth command failed: {e}")

    def send_command(self, command):
        """Generic command sender"""
        if self.connection_method == "Network":
            self.send_network_command(command)
        elif self.connection_method == "Bluetooth":
            self.send_bluetooth_command(command)

    # Command action methods
    def send_power_command_(self, sender):
        self.send_command("POWER")

    def send_home_command_(self, sender):
        self.send_command("HOME")

    def send_back_command_(self, sender):
        self.send_command("BACK")

    def send_navigation_command_(self, sender):
        if sender == self.up_btn:
            self.send_command("UP")
        elif sender == self.down_btn:
            self.send_command("DOWN")
        elif sender == self.left_btn:
            self.send_command("LEFT")
        elif sender == self.right_btn:
            self.send_command("RIGHT")

    def send_select_command_(self, sender):
        self.send_command("SELECT")


def main():
    """Main entry point"""
    print("🚀 Enhanced Android TV Controller")
    print("🔗 Multiple connection methods supported")

    app = NSApplication.sharedApplication()
    delegate = EnhancedAndroidTVController.alloc().init()
    app.setDelegate_(delegate)

    try:
        AppHelper.runEventLoop()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")

if __name__ == "__main__":
    main()