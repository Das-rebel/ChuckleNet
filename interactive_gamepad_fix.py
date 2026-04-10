#!/usr/bin/env python3
"""
Interactive Gamepad Fix - Step-by-step guide with user input
"""

import subprocess
import sys
import time

def run_cmd(cmd, description=""):
    """Run command and return success, stdout, stderr"""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=30
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def check_current_status():
    """Check current gamepad status"""
    print("\n" + "="*70)
    print("📊 CURRENT STATUS CHECK")
    print("="*70)
    
    # Check Bluetooth
    success, output, _ = run_cmd("system_profiler SPBluetoothDataType | grep -A 10 'Gamepad-igs:'")
    
    if success and 'Gamepad-igs' in output:
        print("\n✅ Device Found in Bluetooth:")
        for line in output.split('\n'):
            if any(keyword in line for keyword in ['Gamepad-igs', 'Address', 'Vendor ID', 'Product ID', 'Firmware', 'Minor Type']):
                print(f"   {line.strip()}")
        
        if 'AppleTrackpad' in output or 'Headset' in output:
            print("\n❌ PROBLEM: Device is recognized as 'AppleTrackpad' or 'Headset'")
            print("   Should be: 'Game Controller'")
            return False, output
        elif 'Game Controller' in output:
            print("\n✅ Device is correctly recognized as 'Game Controller'!")
            return True, output
    else:
        print("\n⚠️  Device not found in Bluetooth devices")
        return None, None
    
    return False, output

def step_1_bluetooth_reset():
    """Step 1: Reset Bluetooth"""
    print("\n" + "="*70)
    print("STEP 1: Bluetooth Reset")
    print("="*70)
    
    print("\n⚠️  This will reset your Bluetooth connection.")
    print("   All Bluetooth devices will disconnect temporarily (about 10-15 seconds).")
    print("   They should reconnect automatically after.")
    
    response = input("\n❓ Do you want to proceed with Bluetooth reset? (yes/no): ").lower()
    
    if response != 'yes':
        print("\n⏭️  Skipping Bluetooth reset. You can do it manually:")
        print("   1. Hold Shift + Option keys")
        print("   2. Click Bluetooth icon in menu bar")
        print("   3. Select 'Debug' > 'Reset the Bluetooth module'")
        return False
    
    print("\n🔄 Resetting Bluetooth...")
    
    commands = [
        ("sudo pkill bluetoothd", "Stopping Bluetooth daemon"),
        ("sleep 2", None),
        ("sudo kextunload -b com.apple.iokit.BroadcomBluetoothHostControllerUSBTransport 2>/dev/null || true",
         "Unloading Bluetooth extension"),
        ("sleep 2", None),
        ("sudo kextload -b com.apple.iokit.BroadcomBluetoothHostControllerUSBTransport 2>/dev/null || true",
         "Reloading Bluetooth extension"),
        ("sleep 2", None),
        ("sudo launchctl load /System/Library/LaunchDaemons/com.apple.bluetoothd.plist 2>/dev/null || true",
         "Starting Bluetooth daemon")
    ]
    
    for cmd, desc in commands:
        if desc:
            success, _, _ = run_cmd(cmd)
            status = "✅" if success else "⚠️"
            print(f"   {status} {desc}")
        else:
            time.sleep(2)
    
    print("\n⏳ Waiting 10 seconds for Bluetooth to restart...")
    time.sleep(10)
    print("✅ Bluetooth reset complete!")
    
    return True

def step_2_forget_device():
    """Step 2: Forget the device - MANUAL STEP"""
    print("\n" + "="*70)
    print("STEP 2: Forget Device - REQUIRES YOUR ACTION")
    print("="*70)
    
    print("\n📋 MANUAL STEPS (I'll wait for you):")
    print("\n1. Open System Settings (or System Preferences)")
    print("   - Click the Apple menu > System Settings")
    print("   - Or click System Preferences in Dock")
    print("\n2. Go to Bluetooth")
    print("   - Click 'Bluetooth' in the sidebar")
    print("\n3. Find 'Gamepad-igs' in the device list")
    print("   - Look for your gamepad in the list")
    print("\n4. Remove/Forget the device:")
    print("   - Click the 'i' (info) button next to it")
    print("   - OR right-click and select 'Remove'")
    print("   - OR click the 'X' button if visible")
    print("   - Confirm removal")
    print("\n5. Verify it's removed:")
    print("   - 'Gamepad-igs' should no longer appear in the list")
    
    input("\n⏸️  Press Enter when you've completed these steps...")
    
    # Verify
    success, output, _ = run_cmd("system_profiler SPBluetoothDataType | grep 'Gamepad-igs'")
    if not success or 'Gamepad-igs' not in output:
        print("\n✅ Device has been forgotten/removed!")
        return True
    else:
        print("\n⚠️  Device still appears. Make sure you clicked 'Remove' or 'Forget This Device'")
        retry = input("   Try again? (yes/no): ").lower()
        if retry == 'yes':
            return step_2_forget_device()
        return False

def step_3_pair_device():
    """Step 3: Re-pair device - MANUAL STEP"""
    print("\n" + "="*70)
    print("STEP 3: Re-pair Device - REQUIRES YOUR ACTION")
    print("="*70)
    
    print("\n📋 MANUAL STEPS (I'll wait for you):")
    print("\n1. Put your gamepad in pairing mode:")
    print("   Try these methods (check your gamepad manual):")
    print("   • Hold Power button for 5 seconds")
    print("   • Hold Power + Home/Share button")
    print("   • Hold Power + another button (check manual)")
    print("   • Some gamepads have a dedicated pairing button")
    print("\n2. Look for pairing indicators:")
    print("   • LED should blink rapidly")
    print("   • Some gamepads show different LED pattern")
    print("\n3. In System Settings > Bluetooth:")
    print("   • Click '+' or 'Set Up New Device' button")
    print("   • Wait for 'Gamepad-igs' to appear in the list")
    print("   • Click on 'Gamepad-igs' when it appears")
    print("   • Wait for pairing to complete")
    print("\n4. IMPORTANT - Check device type after pairing:")
    print("   • Click the 'i' (info) button next to 'Gamepad-igs'")
    print("   • Look at the device type")
    print("   • Should say 'Game Controller' (not 'AppleTrackpad' or 'Headset')")
    print("\n5. If device type is still wrong:")
    print("   • Disconnect the gamepad")
    print("   • Put it in a different mode (XInput mode recommended)")
    print("   • Re-pair again")
    
    input("\n⏸️  Press Enter when you've completed pairing...")
    
    # Verify
    print("\n🔍 Verifying device recognition...")
    time.sleep(2)
    
    success, output, _ = run_cmd("system_profiler SPBluetoothDataType | grep -A 10 'Gamepad-igs:'")
    
    if success and 'Gamepad-igs' in output:
        print("\n✅ Device is paired!")
        
        if 'Game Controller' in output:
            print("🎉 SUCCESS! Device is now recognized as 'Game Controller'!")
            return True
        elif 'AppleTrackpad' in output or 'Headset' in output:
            print(f"\n⚠️  Device type is still incorrect: {output.split('Minor Type:')[1].split()[0] if 'Minor Type:' in output else 'Unknown'}")
            print("\n💡 Try these fixes:")
            print("   1. Disconnect and put gamepad in XInput mode")
            print("   2. Re-pair again")
            print("   3. Or use the input mapper (works even if misrecognized)")
            
            retry = input("\n   Try re-pairing in different mode? (yes/no): ").lower()
            if retry == 'yes':
                return step_3_pair_device()
            return False
    else:
        print("\n⚠️  Could not find device. Make sure it's paired.")
        return False

def step_4_test_input():
    """Step 4: Test input detection"""
    print("\n" + "="*70)
    print("STEP 4: Test Input Detection")
    print("="*70)
    
    print("\n🧪 Testing if pygame can detect the gamepad...")
    
    try:
        import pygame
    except ImportError:
        print("Installing pygame...")
        run_cmd(f"{sys.executable} -m pip install pygame")
        import pygame
    
    pygame.init()
    pygame.joystick.init()
    
    count = pygame.joystick.get_count()
    
    if count > 0:
        print(f"\n✅ SUCCESS! Pygame detected {count} gamepad(s):")
        for i in range(count):
            joy = pygame.joystick.Joystick(i)
            joy.init()
            print(f"   - {joy.get_name()}")
            print(f"     Axes: {joy.get_numaxes()}, Buttons: {joy.get_numbuttons()}")
        
        print("\n🎮 Would you like to test input now?")
        response = input("   Test input for 10 seconds? (yes/no): ").lower()
        
        if response == 'yes':
            print("\n📋 Press buttons and move sticks for 10 seconds...")
            print("   (Press Ctrl+C to stop early)")
            
            start_time = time.time()
            pygame.event.set_allowed([
                pygame.JOYBUTTONDOWN,
                pygame.JOYAXISMOTION,
                pygame.JOYHATMOTION
            ])
            
            try:
                while time.time() - start_time < 10:
                    for event in pygame.event.get():
                        if event.type == pygame.JOYBUTTONDOWN:
                            print(f"   🔘 Button {event.button} pressed")
                        elif event.type == pygame.JOYAXISMOTION:
                            if abs(event.value) > 0.1:
                                print(f"   🕹️  Axis {event.axis}: {event.value:+.2f}")
                        elif event.type == pygame.JOYHATMOTION:
                            if event.value != (0, 0):
                                print(f"   🎯 Hat {event.hat}: {event.value}")
                    time.sleep(0.01)
                
                print("\n✅ Input test complete!")
            except KeyboardInterrupt:
                print("\n\n⏹️  Test stopped")
        
        pygame.quit()
        return True
    else:
        print("\n⚠️  Pygame still can't detect the gamepad")
        print("\n💡 Options:")
        print("   1. Use the input mapper (works even if misrecognized)")
        print("   2. Try re-pairing in different mode")
        print("   3. Check System Settings > Privacy > Input Monitoring")
        
        pygame.quit()
        return False

def main():
    print("="*70)
    print("🎮 INTERACTIVE GAMEPAD FIX - STEP BY STEP")
    print("="*70)
    print("\nI'll guide you through fixing the gamepad recognition.")
    print("I'll ask for your permission/input at each step.")
    
    # Check current status
    is_ok, status_output = check_current_status()
    
    if is_ok:
        print("\n✅ Your gamepad is already working correctly!")
        step_4_test_input()
        return
    
    print("\n" + "="*70)
    print("🔧 STARTING FIX PROCESS")
    print("="*70)
    
    # Step 1: Bluetooth reset (optional)
    print("\n📋 Step 1: Bluetooth Reset (Optional but recommended)")
    do_reset = input("   Reset Bluetooth first? (yes/no): ").lower()
    
    if do_reset == 'yes':
        step_1_bluetooth_reset()
    else:
        print("⏭️  Skipping Bluetooth reset")
    
    # Step 2: Forget device
    print("\n📋 Step 2: Forget Device (Required)")
    if step_2_forget_device():
        print("✅ Device forgotten successfully!")
    else:
        print("⚠️  Device may still be connected. Continuing anyway...")
    
    # Step 3: Re-pair device
    print("\n📋 Step 3: Re-pair Device (Required)")
    if step_3_pair_device():
        print("✅ Device re-paired successfully!")
    else:
        print("⚠️  Device recognition may still need work")
    
    # Step 4: Test input
    print("\n📋 Step 4: Test Input Detection")
    if step_4_test_input():
        print("\n🎉 SUCCESS! Your gamepad is working!")
    else:
        print("\n💡 If input still doesn't work, try:")
        print("   python3 gamepad_input_mapper_advanced.py")
        print("   (This works even if device is misrecognized)")
    
    print("\n" + "="*70)
    print("✅ FIX PROCESS COMPLETE")
    print("="*70)

if __name__ == "__main__":
    main()
