#!/bin/bash

# Create Security_Camera_2.4GHz WiFi Hotspot
echo "Setting up Security Camera 2.4GHz WiFi Network..."

# Network Configuration
NETWORK_NAME="Security_Camera_2.4G"
PASSWORD="Cam1234Secure!"
SUBNET="192.168.200"
DHCP_RANGE_START="192.168.200.100"
DHCP_RANGE_END="192.168.200.150"

# Enable IP forwarding
echo "Enabling IP forwarding..."
sudo sysctl -w net.inet.ip.forwarding=1

# Configure WiFi interface for 2.4GHz hotspot
echo "Configuring WiFi interface..."
sudo networksetup -setairportpower en0 on

# Create NAT configuration
echo "Setting up NAT..."
cat << EOF | sudo tee /etc/pf.anchors/security_camera
nat on en0 from 192.168.200.0/24 to any -> (en0)
pass in on bridge100 quick
pass out quick on en0
EOF

# Load NAT rules
sudo pfctl -f /etc/pf.conf -f /etc/pf.anchors/security_camera
sudo pfctl -e

# Configure DHCP server for security camera network
echo "Setting up DHCP server..."
sudo brew services stop dnsmasq 2>/dev/null
cat << EOF | sudo tee /usr/local/etc/dnsmasq.conf
interface=bridge100
dhcp-range=$DHCP_RANGE_START,$DHCP_RANGE_END,255.255.255.0,24h
dhcp-option=3,$SUBNET.1
dhcp-option=6,8.8.8.8,8.8.4.4
server=8.8.8.8
server=8.8.4.4
no-resolv
bind-interfaces
EOF

# Start DHCP server
sudo brew services start dnsmasq

# Create internet sharing configuration
echo "Configuring internet sharing..."
sudo sysctl -w net.inet.ip.forwarding=1

echo "=========================================================="
echo "✅ Security Camera 2.4GHz Network Setup Complete!"
echo "=========================================================="
echo "Network Name: $NETWORK_NAME"
echo "Password: $PASSWORD"
echo "Subnet: $SUBNET.0/24"
echo "DHCP Range: $DHCP_RANGE_START - $DHCP_RANGE_END"
echo "Gateway: $SUBNET.1"
echo "DNS: 8.8.8.8, 8.8.4.4"
echo "=========================================================="
echo "📹 Connect your security camera to this network"
echo "🔒 This network is isolated and secure for cameras only"
echo "=========================================================="

# Save configuration for easy management
cat << EOF > /Users/Subho/security_camera_network_config.txt
Security Camera Network Configuration
=====================================
Network Name: $NETWORK_NAME
Password: $PASSWORD
Subnet: $SUBNET.0/24
Gateway: $SUBNET.1
DNS: 8.8.8.8, 8.8.4.4
DHCP Range: $DHCP_RANGE_START - $DHCP_RANGE_END
Created: $(date)
EOF

echo "Configuration saved to: /Users/Subho/security_camera_network_config.txt"