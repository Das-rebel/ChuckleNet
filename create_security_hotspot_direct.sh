#!/bin/bash

echo "Creating Security Camera 2.4GHz WiFi Hotspot..."
echo "================================================"

# Network Configuration
NETWORK_NAME="Security_Camera_2.4G"
PASSWORD="Cam1234Secure!"
CHANNEL=6

# Create network configuration plist
echo "Creating network configuration..."
cat << EOF > /tmp/com.apple.internetsharing.plist
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>NetworkName</key>
    <string>${NETWORK_NAME}</string>
    <key>SecurityType</key>
    <string>WPA2</string>
    <key>Password</key>
    <string>${PASSWORD}</string>
    <key>Channel</key>
    <integer>${CHANNEL}</integer>
    <key>Band</key>
    <string>2.4GHz</string>
</dict>
</plist>
EOF

# Stop existing services
echo "Stopping existing services..."
sudo launchctl unload /System/Library/LaunchDaemons/com.apple.InternetSharing.plist 2>/dev/null
sudo killall bootpd 2>/dev/null
sudo killall InternetSharing 2>/dev/null

# Enable IP forwarding
echo "Enabling IP forwarding..."
sudo sysctl -w net.inet.ip.forwarding=1

# Create network interface
echo "Configuring network interface..."
sudo ifconfig bridge0 create 2>/dev/null
sudo ifconfig bridge0 up 2>/dev/null

# Configure NAT
echo "Setting up NAT..."
echo "nat on en0 from 192.168.2.0/24 to any -> (en0)" | sudo tee /etc/pf.anchors/security-camera
echo "pass in on bridge0 quick" | sudo tee -a /etc/pf.anchors/security-camera
echo "pass out quick on en0" | sudo tee -a /etc/pf.anchors/security-camera

sudo pfctl -f /etc/pf.conf -f /etc/pf.anchors/security-camera
sudo pfctl -e

# Start DHCP server
echo "Starting DHCP server..."
cat << EOF | sudo tee /etc/bootpd.plist
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Subnets</key>
    <array>
        <dict>
            <key>name</key>
            <string>192.168.2.0</string>
            <key>net_mask</key>
            <string>255.255.255.0</string>
            <key>allocate</key>
            <true/>
            <key>dhcp_range_start</key>
            <string>192.168.2.100</string>
            <key>dhcp_range_end</key>
            <string>192.168.2.200</string>
            <key>lease_min</key>
            <integer>3600</integer>
            <key>lease_max</key>
            <integer>86400</integer>
            <key>netmask</key>
            <string>255.255.255.0</string>
        </dict>
    </array>
    <key>bootp_enabled</key>
    <false/>
    <key>dhcp_enabled</key>
    <true/>
    <key>dhcp_option_4</key>
    <string>192.168.2.1</string>
    <key>dhcp_option_6</key>
    <string>8.8.8.8 8.8.4.4</string>
    <key>interface</key>
    <string>bridge0</string>
</dict>
</plist>
EOF

# Start bootpd
sudo launchctl load /System/Library/LaunchDaemons/com.apple.bootpd.plist
sudo launchctl start com.apple.bootpd

# Configure bridge interface IP
sudo ifconfig bridge0 192.168.2.1 netmask 255.255.255.0

# Start Internet Sharing service
echo "Starting Internet Sharing..."
sudo launchctl load /System/Library/LaunchDaemons/com.apple.InternetSharing.plist

echo "================================================"
echo "✅ Security Camera Hotspot Setup Attempted!"
echo "================================================"
echo "Network: ${NETWORK_NAME}"
echo "Password: ${PASSWORD}"
echo "Channel: ${CHANNEL} (2.4GHz)"
echo "Subnet: 192.168.2.0/24"
echo "Gateway: 192.168.2.1"
echo "DHCP Range: 192.168.2.100 - 192.168.2.200"
echo "================================================"
echo "📹 Connect your security camera to this network"
echo "================================================"

# Wait a moment for services to start
sleep 3

# Check if hotspot is broadcasting
echo "Checking if hotspot is active..."
/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -s | grep -i "${NETWORK_NAME}" || echo "Network not found in scan - manual setup may be needed"