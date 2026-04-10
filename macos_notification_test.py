#!/usr/bin/env python3
"""Test macOS-specific notification functionality"""

import subprocess
import time

def test_macos_notification():
    """Test macOS notification using osascript"""
    try:
        script = '''
        display notification "Smart AI notification system is working!" with title "Smart AI Test" sound name "Glass"
        '''
        result = subprocess.run(['osascript', '-e', script], 
                              check=True, capture_output=True, text=True)
        print("✅ macOS notification sent successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ macOS notification failed: {e}")
        return False
    except FileNotFoundError:
        print("❌ osascript not found (not running on macOS)")
        return False

def main():
    print("🍎 macOS Notification Test")
    print("=" * 30)
    
    print("Testing macOS system notification...")
    success = test_macos_notification()
    
    if success:
        print("\n🎉 System notifications are working on macOS!")
        print("The notification system will use osascript fallback for system notifications.")
    else:
        print("\n⚠️  System notifications may not work, but terminal notifications will work fine.")
    
    print("\nNote: The plyer library requires additional dependencies for macOS.")
    print("Terminal notifications will always work and provide rich visual feedback.")

if __name__ == "__main__":
    main()