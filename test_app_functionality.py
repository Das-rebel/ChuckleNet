#!/usr/bin/env python3
"""
Test the Android TV Controller app functionality
"""

import subprocess
import time
import sys

def test_app_launch():
    """Test if the app launches properly"""
    print("🚀 Testing App Launch...")

    # Check if app is already running
    result = subprocess.run(['pgrep', '-f', 'AndroidTVController'], capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ App is running (PID: {})".format(result.stdout.strip()))
        return True
    else:
        print("❌ App is not running")
        return False

def test_bluetooth_status():
    """Test Bluetooth status and connected devices"""
    print("\n🔵 Testing Bluetooth Status...")

    try:
        result = subprocess.run(['system_profiler', 'SPBluetoothDataType'], capture_output=True, text=True)
        if "State: On" in result.stdout:
            print("✅ Bluetooth is ON")
        else:
            print("❌ Bluetooth is OFF")
            return False

        if "dasi:" in result.stdout:
            print("✅ Android TV device 'dasi' is connected via Bluetooth")
            return True
        else:
            print("⚠️  Android TV device not detected in system profiler")
            return False

    except Exception as e:
        print(f"❌ Error checking Bluetooth: {e}")
        return False

def test_app_permissions():
    """Test if app has necessary permissions"""
    print("\n📋 Testing App Permissions...")

    # Check if app can access Bluetooth by checking its Info.plist
    try:
        with open('/Users/Subho/Desktop/AndroidTVController.app/Contents/Info.plist', 'r') as f:
            content = f.read()
            if 'NSBluetoothAlwaysUsageDescription' in content:
                print("✅ App has Bluetooth usage description in Info.plist")
                return True
            else:
                print("⚠️  App may not have proper Bluetooth permissions")
                return False
    except Exception as e:
        print(f"❌ Error checking Info.plist: {e}")
        return False

def test_ui_elements():
    """Test if app UI is accessible"""
    print("\n🖥️  Testing UI Accessibility...")

    try:
        result = subprocess.run([
            'osascript', '-e',
            '''
            tell application "System Events"
                tell process "AndroidTVController"
                    if exists window 1 then
                        return "Window exists"
                    else
                        return "No window found"
                    end if
                end tell
            end tell
            '''
        ], capture_output=True, text=True)

        if "Window exists" in result.stdout:
            print("✅ App window is accessible")
            return True
        else:
            print("❌ App window not found")
            return False

    except Exception as e:
        print(f"⚠️  Could not verify UI: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Android TV Controller App")
    print("=" * 50)

    tests = [
        ("App Launch", test_app_launch),
        ("Bluetooth Status", test_bluetooth_status),
        ("App Permissions", test_app_permissions),
        ("UI Elements", test_ui_elements)
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test failed: {e}")
            results.append((test_name, False))

    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print("=" * 50)

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:20} {status}")
        if result:
            passed += 1

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! App should work correctly.")
    elif passed >= total // 2:
        print("⚠️  Some tests failed, but app may still work.")
    else:
        print("❌ Many tests failed. App may need fixes.")

    # Recommendations
    print("\n💡 Recommendations:")
    if passed >= 3:
        print("- App should work for controlling Android TV")
        print("- Try clicking 'Connect' in the app")
        print("- Make sure TV is discoverable via Bluetooth")
    else:
        print("- Check if Bluetooth is enabled on your Mac")
        print("- Restart the app if needed")
        print("- Use Python backup solution if needed")

if __name__ == "__main__":
    main()