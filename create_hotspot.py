#!/usr/bin/env python3
import subprocess
import sys
import time

def create_hotspot():
    print("Creating Security_Das WiFi hotspot...")
    
    # Enable IP forwarding
    try:
        subprocess.run(['sudo', 'sysctl', '-w', 'net.inet.ip.forwarding=1'], check=True)
    except:
        print("Failed to enable IP forwarding")
    
    # Configure network interface
    try:
        subprocess.run(['sudo', 'ifconfig', 'en0', 'inet', '192.168.100.1', 'netmask', '255.255.255.0'], check=True)
    except:
        print("Failed to configure network interface")
    
    print("Security_Das hotspot setup attempted")
    print("Network: Security_Das")
    print("Password: Das1234")

if __name__ == "__main__":
    create_hotspot()
