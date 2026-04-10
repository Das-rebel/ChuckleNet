#!/usr/bin/env python3
"""
Quick Gamepad Input Test
Simple script to quickly test if gamepad input is working
"""

import sys
import time
from datetime import datetime

def test_gamepad():
    """Quick gamepad input test"""
    try:
        import pygame
    except ImportError:
        print("Installing pygame...")
        import subprocess
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pygame'])
        import pygame
    
    pygame.init()
    pygame.joystick.init()
    
    count = pygame.joystick.get_count()
    
    if count == 0:
        print("❌ No gamepads detected")
        print("\nTroubleshooting:")
        print("1. Make sure gamepad is connected via Bluetooth or USB")
        print("2. Check System Settings > Bluetooth")
        print("3. Try running: python3 gamepad_firmware_and_input_manager.py")
        return
    
    print(f"✅ Found {count} gamepad(s)")
    
    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    
    print(f"\nGamepad: {joystick.get_name()}")
    print(f"Axes: {joystick.get_numaxes()}")
    print(f"Buttons: {joystick.get_numbuttons()}")
    print(f"Hats: {joystick.get_numhats()}")
    
    print("\n" + "="*50)
    print("Testing input for 15 seconds...")
    print("Move sticks, press buttons!")
    print("Press Ctrl+C to stop early")
    print("="*50 + "\n")
    
    start = time.time()
    events_captured = 0
    
    pygame.event.set_allowed([
        pygame.JOYBUTTONDOWN,
        pygame.JOYBUTTONUP,
        pygame.JOYAXISMOTION,
        pygame.JOYHATMOTION
    ])
    
    try:
        while time.time() - start < 15:
            for event in pygame.event.get():
                events_captured += 1
                
                if event.type == pygame.JOYBUTTONDOWN:
                    print(f"🔘 Button {event.button} pressed")
                
                elif event.type == pygame.JOYAXISMOTION:
                    if abs(event.value) > 0.1:
                        axis_name = f"Axis {event.axis}"
                        if event.axis < 2:
                            axis_name = f"Left {'X' if event.axis == 0 else 'Y'}"
                        elif event.axis < 4:
                            axis_name = f"Right {'X' if event.axis == 2 else 'Y'}"
                        print(f"🕹️  {axis_name}: {event.value:+.2f}")
                
                elif event.type == pygame.JOYHATMOTION:
                    if event.value != (0, 0):
                        print(f"🎯 Hat {event.hat}: {event.value}")
            
            time.sleep(0.01)
    
    except KeyboardInterrupt:
        print("\n\nStopped by user")
    
    print("\n" + "="*50)
    print(f"✅ Test complete! Captured {events_captured} events")
    if events_captured == 0:
        print("⚠️  No input detected. Make sure to move sticks/press buttons")
    
    pygame.quit()

if __name__ == "__main__":
    test_gamepad()
