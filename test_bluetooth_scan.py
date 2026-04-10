#!/usr/bin/env python3
"""
Quick test to verify Bluetooth scanning works
"""

import sys
try:
    from CoreBluetooth import *
    from PyObjCTools import AppHelper
    from Cocoa import NSObject
    print("✅ All frameworks imported successfully")
except Exception as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

class BluetoothTester(NSObject):
    def init(self):
        self = super().init()
        if self is None:
            return None

        self.centralManager = CBCentralManager.alloc().initWithDelegate_queue_(self, None)
        print("🔵 Bluetooth manager initialized")
        return self

    def centralManagerDidUpdateState_(self, central):
        state = central.state()
        if state == CBCentralManagerStatePoweredOn:
            print("✅ Bluetooth is ON and ready")
            print("🔍 Starting scan for Android TV devices...")

            # Scan for common Android TV service UUIDs
            tv_uuids = [
                CBUUID.UUIDWithString_("0000110E-0000-1000-8000-00805F9B34FB"),  # A2DP
                CBUUID.UUIDWithString_("0000110A-0000-1000-8000-00805F9B34FB"),  # Audio Sink
                CBUUID.UUIDWithString_("00001108-0000-1000-8000-00805F9B34FB")   # HID
            ]

            central.scanForPeripheralsWithServices_options_(tv_uuids, None)
            print("📡 Scanning started...")

        elif state == CBCentralManagerStatePoweredOff:
            print("❌ Bluetooth is turned off")
        elif state == CBCentralManagerStateUnauthorized:
            print("❌ Bluetooth access denied - grant permissions")
        else:
            print(f"⚠️  Bluetooth state: {state}")

    def centralManager_didDiscoverPeripheral_advertisementData_RSSI_(self, central, peripheral, data, rssi):
        name = peripheral.name() or "Unknown Device"
        print(f"📱 Found device: {name} (RSSI: {rssi})")

        # Check if it looks like an Android TV
        tv_keywords = ["android", "tv", "shield", "nvidia", "xiaomi", "mi", "samsung", "lg", "sony"]
        name_lower = name.lower()

        if any(keyword in name_lower for keyword in tv_keywords):
            print(f"🎯 ANDROID TV DETECTED: {name}")
            print(f"   - Address: {peripheral.identifier()}")
            print(f"   - RSSI: {rssi}")
            print(f"   - Connectable: {peripheral.isConnectable() if hasattr(peripheral, 'isConnectable') else 'Unknown'}")

def main():
    print("🚀 Testing Android TV Bluetooth Scanner")
    print("="*50)

    tester = BluetoothTester.alloc().init()

    try:
        # Run for 15 seconds to scan
        import time
        print("⏱️  Scanning for 15 seconds...")
        time.sleep(15)
        print("✅ Scan completed")
    except KeyboardInterrupt:
        print("\n⏹️  Scan stopped by user")
    except Exception as e:
        print(f"❌ Error during scan: {e}")

if __name__ == "__main__":
    main()