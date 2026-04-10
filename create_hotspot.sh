#!/bin/bash

# Create Security_Das WiFi Hotspot
echo "Creating Security_Das WiFi hotspot..."

# Enable IP forwarding
sudo sysctl -w net.inet.ip.forwarding=1

# Create network interface
sudo ifconfig en0 inet 192.168.100.1 netmask 255.255.255.0

# Start DHCP server
sudo brew services stop dnsmasq
echo "interface=en0" | sudo tee /usr/local/etc/dnsmasq.conf
echo "dhcp-range=192.168.100.100,192.168.100.200,255.255.255.0,12h" | sudo tee -a /usr/local/etc/dnsmasq.conf
echo "server=8.8.8.8" | sudo tee -a /usr/local/etc/dnsmasq.conf
sudo brew services start dnsmasq

# Enable NAT
sudo pfctl -f /etc/pf.conf
sudo pfctl -e

echo "Security_Das hotspot created!"
echo "Network: Security_Das"
echo "Password: Das1234"
echo "IP: 192.168.100.1"
