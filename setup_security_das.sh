#!/bin/bash

echo "Setting up Security_Das WiFi network..."
echo "====================================="

# Step 1: Enable IP forwarding (requires sudo)
echo "Enabling IP forwarding..."
sudo sysctl -w net.inet.ip.forwarding=1

# Step 2: Configure NAT
echo "Configuring NAT..."
sudo sysctl -w net.inet.ip.scopedroute=0

# Step 3: Configure Internet Sharing
echo "Configuring Internet Sharing..."
sudo defaults write /Library/Preferences/SystemConfiguration/com.apple.nat NAT -dict-add Enabled -bool true
sudo defaults write /Library/Preferences/SystemConfiguration/com.apple.nat NAT -dict-add InterfaceName -string "en0"

# Step 4: Configure WiFi hotspot settings
echo "Configuring WiFi hotspot settings..."
sudo defaults write /Library/Preferences/SystemConfiguration/com.apple.airport.preferences SSID -string "Security_Das"
sudo defaults write /Library/Preferences/SystemConfiguration/com.apple.airport.preferences Password -string "Das1234"
sudo defaults write /Library/Preferences/SystemConfiguration/com.apple.airport.preferences Channel -integer 6

# Step 5: Enable Internet Sharing service
echo "Enabling Internet Sharing service..."
sudo launchctl load -w /System/Library/LaunchDaemons/com.apple.InternetSharing.plist

echo "Setup complete! Security_Das network should now be active."
echo "Network Name: Security_Das"
echo "Password: Das1234"
echo "Frequency: 2.4 GHz (Channel 6)"
