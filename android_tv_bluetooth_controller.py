#!/usr/bin/env python3
"""
Android TV Bluetooth Controller for Mac
A macOS app to control Android TV via Bluetooth connection
"""

import sys
import time
import threading
from Cocoa import *
from CoreBluetooth import *
from PyObjCTools import AppHelper

class AndroidTVController(NSObject):
    """Main controller class for Android TV Bluetooth remote"""

    def init(self):
        """Initialize the controller"""
        self = super().init()
        if self is None:
            return None

        # Bluetooth properties
        self.centralManager = CBCentralManager.alloc().initWithDelegate_queue_(self, None)
        self.connectedPeripheral = None
        self.controlCharacteristic = None

        # UI elements
        self.statusLabel = None
        self.connectButton = None

        # Android TV identification
        self.tvServiceUUID = CBUUID.UUIDWithString_("0000110E-0000-1000-8000-00805F9B34FB")  # A2DP Profile
        self.controlUUID = CBUUID.UUIDWithString_("0000110C-0000-1000-8000-00805F9B34FB")    # Remote Control

        return self

    def createWindow(self):
        """Create the main application window"""
        # Create window
        self.window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(0, 0, 450, 500),
            NSWindowStyleMaskTitled | NSWindowStyleMaskClosable | NSWindowStyleMaskMiniaturizable,
            NSBackingStoreBuffered,
            False
        )

        self.window.setTitle_("Android TV Bluetooth Controller")
        self.window.center()

        # Create main view
        self.mainView = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, 450, 500))
        self.window.setContentView_(self.mainView)

        # Status label
        self.statusLabel = NSTextField.alloc().initWithFrame_(NSMakeRect(20, 440, 410, 30))
        self.statusLabel.setStringValue_("Searching for Android TV...")
        self.statusLabel.setBezeled_(False)
        self.statusLabel.setEditable_(False)
        self.statusLabel.setDrawsBackground_(False)
        self.statusLabel.setFont_(NSFont.systemFontOfSize_(14))
        self.statusLabel.setTextColor_(NSColor.secondaryLabelColor())
        self.mainView.addSubview_(self.statusLabel)

        # Connect button
        self.connectButton = NSButton.alloc().initWithFrame_(NSMakeRect(20, 400, 100, 30))
        self.connectButton.setTitle_("Connect")
        self.connectButton.setTarget_(self)
        self.connectButton.setAction_("connectToDevice:")
        self.connectButton.setEnabled_(False)
        self.mainView.addSubview_(self.connectButton)

        # Create remote control buttons
        self.createRemoteControls()

        # Show window
        self.window.makeKeyAndOrderFront_(self)

        return self.window

    def createRemoteControls(self):
        """Create the remote control button layout"""
        button_size = 50
        center_x = 225
        center_y = 200

        # Power button
        self.powerButton = self.createButton_("⏻", NSMakeRect(center_x - button_size//2, center_y + 200, button_size, button_size))
        self.powerButton.setTarget_(self)
        self.powerButton.setAction_("sendCommand:")
        self.mainView.addSubview_(self.powerButton)

        # Navigation buttons
        self.homeButton = self.createButton_("⌂", NSMakeRect(center_x + 80, center_y + 200, button_size, button_size))
        self.homeButton.setTarget_(self)
        self.homeButton.setAction_("sendCommand:")
        self.mainView.addSubview_(self.homeButton)

        self.backButton = self.createButton_("◀", NSMakeRect(center_x - 130, center_y + 200, button_size, button_size))
        self.backButton.setTarget_(self)
        self.backButton.setAction_("sendCommand:")
        self.mainView.addSubview_(self.backButton)

        # D-Pad
        self.upButton = self.createButton_("▲", NSMakeRect(center_x - button_size//2, center_y + button_size, button_size, button_size))
        self.upButton.setTarget_(self)
        self.upButton.setAction_("sendCommand:")
        self.mainView.addSubview_(self.upButton)

        self.downButton = self.createButton_("▼", NSMakeRect(center_x - button_size//2, center_y - button_size, button_size, button_size))
        self.downButton.setTarget_(self)
        self.downButton.setAction_("sendCommand:")
        self.mainView.addSubview_(self.downButton)

        self.leftButton = self.createButton_("◀", NSMakeRect(center_x - button_size * 1.5, center_y - button_size//2, button_size, button_size))
        self.leftButton.setTarget_(self)
        self.leftButton.setAction_("sendCommand:")
        self.mainView.addSubview_(self.leftButton)

        self.rightButton = self.createButton_("▶", NSMakeRect(center_x + button_size//2, center_y - button_size//2, button_size, button_size))
        self.rightButton.setTarget_(self)
        self.rightButton.setAction_("sendCommand:")
        self.mainView.addSubview_(self.rightButton)

        # Select button (center of D-Pad)
        self.selectButton = self.createButton_("●", NSMakeRect(center_x - button_size//2, center_y - button_size//2, button_size, button_size))
        self.selectButton.setTarget_(self)
        self.selectButton.setAction_("sendCommand:")
        self.mainView.addSubview_(self.selectButton)

        # Volume controls
        self.volumeUpButton = self.createButton_("🔊", NSMakeRect(350, center_y + 40, button_size, button_size))
        self.volumeUpButton.setTarget_(self)
        self.volumeUpButton.setAction_("sendCommand:")
        self.mainView.addSubview_(self.volumeUpButton)

        self.volumeDownButton = self.createButton_("🔉", NSMakeRect(350, center_y - 20, button_size, button_size))
        self.volumeDownButton.setTarget_(self)
        self.volumeDownButton.setAction_("sendCommand:")
        self.mainView.addSubview_(self.volumeDownButton)

        self.muteButton = self.createButton_("🔇", NSMakeRect(350, center_y + 10, button_size, button_size))
        self.muteButton.setTarget_(self)
        self.muteButton.setAction_("sendCommand:")
        self.mainView.addSubview_(self.muteButton)

        # WiFi enable button
        self.wifiButton = NSButton.alloc().initWithFrame_(NSMakeRect(20, 340, 150, 30))
        self.wifiButton.setTitle_("Enable WiFi")
        self.wifiButton.setTarget_(self)
        self.wifiButton.setAction_("sendWiFiCommand:")
        self.mainView.addSubview_(self.wifiButton)

        # Network status button
        self.networkStatusButton = NSButton.alloc().initWithFrame_(NSMakeRect(20, 300, 150, 30))
        self.networkStatusButton.setTitle_("Check Network")
        self.networkStatusButton.setTarget_(self)
        self.networkStatusButton.setAction_("checkNetworkStatus:")
        self.mainView.addSubview_(self.networkStatusButton)

        # Initially disable all control buttons
        self.enableControls_(False)

    def createButton_(self, title, frame):
        """Create a styled button"""
        button = NSButton.alloc().initWithFrame_(frame)
        button.setTitle_(title)
        button.setBezelStyle_(NSBezelStyleRounded)
        button.setFont_(NSFont.systemFontOfSize_(18))
        button.setEnabled_(False)
        return button

    def enableControls_(self, enabled):
        """Enable or disable all control buttons"""
        for button in [self.powerButton, self.homeButton, self.backButton,
                      self.upButton, self.downButton, self.leftButton,
                      self.rightButton, self.selectButton, self.volumeUpButton,
                      self.volumeDownButton, self.muteButton, self.wifiButton,
                      self.networkStatusButton]:
            button.setEnabled_(enabled)

    # Bluetooth Manager Delegate Methods
    def centralManagerDidUpdateState_(self, central):
        """Called when Bluetooth state changes"""
        if central.state() == CBCentralManagerStatePoweredOn:
            self.statusLabel.setStringValue_("Scanning for Android TV...")
            central.scanForPeripheralsWithServices_options_([self.tvServiceUUID], None)
        elif central.state() == CBCentralManagerStatePoweredOff:
            self.statusLabel.setStringValue_("Bluetooth is turned off")
        else:
            self.statusLabel.setStringValue_("Bluetooth unavailable")

    def centralManager_didDiscoverPeripheral_advertisementData_RSSI_(self, central, peripheral, data, rssi):
        """Called when a peripheral is discovered"""
        device_name = peripheral.name() or "Unknown Device"

        # Check if this looks like an Android TV
        tv_indicators = ["android", "tv", "shield", "nvidia", "xiaomi", "mi tv", "samsung", "lg", "sony"]
        device_name_lower = device_name.lower()

        if any(indicator in device_name_lower for indicator in tv_indicators):
            self.statusLabel.setStringValue_(f"Found Android TV: {device_name}")
            self.connectedPeripheral = peripheral
            peripheral.setDelegate_(self)
            self.connectButton.setEnabled_(True)
            central.stopScan()

    def centralManager_didConnectPeripheral_(self, central, peripheral):
        """Called when connected to peripheral"""
        self.statusLabel.setStringValue_(f"Connected to {peripheral.name() or 'Android TV'}")
        self.connectButton.setTitle_("Disconnect")
        peripheral.discoverServices_([self.tvServiceUUID])
        self.enableControls_(True)

    def centralManager_didDisconnectPeripheral_error_(self, central, peripheral, error):
        """Called when disconnected from peripheral"""
        self.statusLabel.setStringValue_("Disconnected from Android TV")
        self.connectButton.setTitle_("Connect")
        self.enableControls_(False)
        self.connectedPeripheral = None

    def peripheral_didDiscoverServices_(self, peripheral, error):
        """Called when services are discovered"""
        services = peripheral.services()
        if services:
            for service in services:
                if service.UUID().UUIDString() == self.tvServiceUUID.UUIDString():
                    peripheral.discoverCharacteristics_([self.controlUUID], forService_=service)

    def peripheral_didDiscoverCharacteristicsForService_error_(self, peripheral, service, error):
        """Called when characteristics are discovered"""
        characteristics = service.characteristics()
        if characteristics:
            for characteristic in characteristics:
                if characteristic.UUID().UUIDString() == self.controlUUID.UUIDString():
                    self.controlCharacteristic = characteristic
                    self.statusLabel.setStringValue_("Ready to control Android TV")

    # Button Actions
    def connectToDevice_(self, sender):
        """Connect or disconnect from Android TV"""
        if self.connectedPeripheral:
            if self.connectButton.title() == "Connect":
                self.centralManager.connectPeripheral_options_(self.connectedPeripheral, None)
            else:
                self.centralManager.cancelPeripheralConnection_(self.connectedPeripheral)

    def sendCommand_(self, sender):
        """Send a command based on which button was pressed"""
        command_map = {
            self.powerButton: "POWER",
            self.homeButton: "HOME",
            self.backButton: "BACK",
            self.upButton: "UP",
            self.downButton: "DOWN",
            self.leftButton: "LEFT",
            self.rightButton: "RIGHT",
            self.selectButton: "SELECT",
            self.volumeUpButton: "VOLUME_UP",
            self.volumeDownButton: "VOLUME_DOWN",
            self.muteButton: "MUTE"
        }

        command = command_map.get(sender)
        if command:
            self.sendCommandToTV_(command)
            self.statusLabel.setStringValue_(f"Sent: {command}")

    def sendWiFiCommand_(self, sender):
        """Send WiFi enable command"""
        self.sendCommandToTV_("ENABLE_WIFI")
        self.statusLabel.setStringValue_("Sent WiFi enable command")

    def checkNetworkStatus_(self, sender):
        """Check network status on TV"""
        self.sendCommandToTV_("NETWORK_STATUS")
        self.statusLabel.setStringValue_("Checking network status...")

    def sendCommandToTV_(self, command):
        """Send a command to the Android TV via Bluetooth"""
        if self.connectedPeripheral and self.controlCharacteristic:
            # Convert command to data
            command_bytes = command.encode('utf-8')
            command_data = NSData.dataWithBytes_length_(command_bytes, len(command_bytes))

            # Send the command
            self.connectedPeripheral.writeValue_forCharacteristic_type_(
                command_data, self.controlCharacteristic, CBCharacteristicWriteWithResponse
            )
        else:
            self.statusLabel.setStringValue_("Not connected to Android TV")


class AppDelegate(NSObject):
    """Application delegate"""

    def applicationDidFinishLaunching_(self, notification):
        """Called when app finishes launching"""
        self.controller = AndroidTVController.alloc().init()
        self.controller.createWindow()

    def applicationShouldTerminateAfterLastWindowClosed_(self, sender):
        """Return True to quit app when window closes"""
        return True


def main():
    """Main application entry point"""
    app = NSApplication.sharedApplication()
    delegate = AppDelegate.alloc().init()
    app.setDelegate_(delegate)

    # Run the application
    AppHelper.runEventLoop()


if __name__ == "__main__":
    main()