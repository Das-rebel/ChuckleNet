#!/usr/bin/env python3
"""
Set up Wi-Fi based TV control as Bluetooth alternative
"""

import subprocess
import socket
import time

def check_tv_network_presence():
    """Check if TV is on same network"""
    print("🌐 Checking if TV is accessible via network...")

    # Try to connect to TV's common ports
    tv_ips = [
        "192.168.1.100", "192.168.1.101", "192.168.1.102",  # Common TV IPs
        "192.168.0.100", "192.168.0.101", "192.168.0.102",
        "10.0.0.100", "10.0.0.101"
    ]

    common_ports = [8080, 5555, 80, 443, 22]

    for ip in tv_ips:
        for port in common_ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex((ip, port))
                if result == 0:
                    print(f"✅ Found device at {ip}:{port}")
                    sock.close()
                    return ip, port
                sock.close()
            except:
                continue

    return None, None

def setup_phone_as_remote():
    """Guide for setting up phone as remote via Wi-Fi"""
    print("\n📱 Setting up Wi-Fi Remote Control...")
    print("=" * 50)

    instructions = """
    STEP 1: Connect Both Devices to Same Wi-Fi
    ========================================
    - Make sure your Mac is connected to Wi-Fi
    - Connect your iQoo phone to SAME Wi-Fi network

    STEP 2: Install Remote Apps on Your Phone
    =========================================
    Try these apps in order:

    1. Google Home App (Primary)
       - Install from Play Store
       - Should auto-discover your "dasi" TV
       - Use built-in remote control

    2. Android TV Remote Service
       - Official Google app
       - Auto-connects via Wi-Fi
       - Full remote control

    3. AnyMote Universal Remote
       - Install and add device
       - Select "Android TV" type
       - Manual IP setup if needed

    4. VLC Remote (Alternative)
       - Can control some TV functions
       - Good backup option

    STEP 3: Alternative Phone Features
    ==================================
    Try these built-in features:

    1. Quick Connect (Samsung)
    2. Cast Screen (Android)
    3. Mi Remote (Xiaomi phones)
    4. Peel Smart Remote

    STEP 4: Manual IP Connection
    ===========================
    If auto-discovery doesn't work:
    1. Find TV's IP address in TV settings
    2. Use remote app with manual IP input
    3. Common TV IPs: 192.168.1.x or 192.168.0.x
    """

    print(instructions)

def network_scan():
    """Scan local network for devices"""
    print("\n🔍 Scanning local network for devices...")

    try:
        # Get local network range
        result = subprocess.run(['ifconfig'], capture_output=True, text=True)
        lines = result.stdout.split('\n')

        network_ips = []
        for line in lines:
            if 'inet ' in line and '127.0.0.1' not in line:
                # Extract IP
                parts = line.strip().split()
                for part in parts:
                    if '.' in part and len(part.split('.')) == 4:
                        ip = part
                        network_base = '.'.join(ip.split('.')[:3])
                        network_ips.append(f"{network_base}.1")
                        break

        # Check common TV IPs in the network
        for base in set(network_ips):
            for suffix in range(100, 110):
                ip = f"{base.rsplit('.', 1)[0]}.{suffix}"
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1)
                    result = sock.connect_ex((ip, 80))
                    if result == 0:
                        print(f"✅ Device found: {ip}")
                    sock.close()
                except:
                    continue

    except Exception as e:
        print(f"❌ Network scan failed: {e}")

def main():
    print("🌐 Wi-Fi TV Control Setup")
    print("=" * 30)

    # Check if TV is accessible via network
    ip, port = check_tv_network_presence()

    if ip:
        print(f"✅ Found potential TV device at {ip}:{port}")
    else:
        print("❌ No TV device found via network scan")

    # Scan local network
    network_scan()

    # Setup instructions
    setup_phone_as_remote()

    print("\n" + "=" * 50)
    print("💡 KEY ADVANTAGE: Wi-Fi control bypasses Bluetooth issues!")
    print("💡 Once connected via Wi-Fi, you have full remote control!")

if __name__ == "__main__":
    main()