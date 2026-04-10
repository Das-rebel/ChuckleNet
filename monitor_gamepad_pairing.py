#!/usr/bin/env python3
"""
Monitor gamepad pairing status - checks periodically until device is properly paired
"""

import subprocess
import time
import sys

def check_device_status():
    """Check if gamepad is paired and properly recognized"""
    result = subprocess.run(
        ["system_profiler", "SPBluetoothDataType"],
        capture_output=True, text=True
    )
    
    if "Gamepad-igs" not in result.stdout:
        return None, "Device not found in Bluetooth"
    
    # Extract device type
    lines = result.stdout.split('\n')
    in_section = False
    device_type = None
    
    for line in lines:
        if "Gamepad-igs:" in line:
            in_section = True
            continue
        
        if in_section:
            if line.strip() and not line.startswith(' ') and ':' not in line:
                break
            
            if "Minor Type:" in line:
                device_type = line.split("Minor Type:")[1].strip()
                break
    
    if device_type:
        if 'Game Controller' in device_type:
            return True, f"✅ SUCCESS! Recognized as: {device_type}"
        else:
            return False, f"❌ Still misrecognized as: {device_type}"
    
    return None, "Device found but type unknown"

def check_pygame():
    """Check if pygame can detect the gamepad"""
    try:
        import pygame
        pygame.init()
        pygame.joystick.init()
        
        count = pygame.joystick.get_count()
        
        if count > 0:
            names = []
            for i in range(count):
                joy = pygame.joystick.Joystick(i)
                joy.init()
                names.append(joy.get_name())
            pygame.quit()
            return True, f"Pygame detected {count} gamepad(s): {', '.join(names)}"
        else:
            pygame.quit()
            return False, "Pygame can't detect gamepad yet"
    except ImportError:
        return None, "Pygame not installed"
    except Exception as e:
        return None, f"Pygame error: {e}"

def main():
    print("="*60)
    print("🎮 GAMEPAD PAIRING MONITOR")
    print("="*60)
    print("\nThis script will monitor for gamepad pairing.")
    print("Put your gamepad in pairing mode and pair it in System Settings > Bluetooth.")
    print("\nPress Ctrl+C to stop monitoring.\n")
    
    check_count = 0
    last_status = None
    
    try:
        while True:
            check_count += 1
            status, message = check_device_status()
            pygame_status, pygame_msg = check_pygame()
            
            # Only print if status changed
            if status != last_status:
                print(f"\n[{time.strftime('%H:%M:%S')}] Check #{check_count}")
                print(f"Bluetooth: {message}")
                print(f"Pygame: {pygame_msg}")
                
                if status is True:
                    print("\n🎉🎉🎉 GAMEPAD IS PROPERLY RECOGNIZED! 🎉🎉🎉")
                    if pygame_status:
                        print("✅ Everything is working correctly!")
                        print("\nYou can now use your gamepad!")
                        break
                    else:
                        print("⚠️  Device recognized but pygame can't detect it yet.")
                        print("   Try: python3 gamepad_input_mapper_advanced.py")
                elif status is False:
                    print("\n⚠️  Device is paired but still misrecognized.")
                    print("   Try putting gamepad in XInput mode and re-pairing.")
                elif status is None:
                    print("\n⏳ Waiting for device to pair...")
                    print("   Make sure gamepad is in pairing mode.")
                
                last_status = status
            
            time.sleep(3)  # Check every 3 seconds
            
    except KeyboardInterrupt:
        print("\n\n⏸️  Monitoring stopped.")
        final_status, final_msg = check_device_status()
        print(f"\nFinal Status: {final_msg}")
        sys.exit(0)

if __name__ == "__main__":
    main()