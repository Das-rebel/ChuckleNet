#!/bin/bash
# Complete Happy Claude-GLM Mobile Setup

echo "🚀 Happy Claude-GLM Mobile Setup"
echo "================================"

DEVICE_ID="adb-10BEAG2THF003DD-Z0kION._adb-tls-connect._tcp"

# Function to check if Happy is authenticated
check_happy_auth() {
    happy auth status 2>/dev/null | grep -q "✓ Authenticated"
    return $?
}

# Function to start Happy with Claude-GLM
start_happy_glm() {
    echo "Starting Happy with Claude-GLM..."
    happy --settings ~/.happy/zai_settings.json "Ready for mobile connection with Claude-GLM" &
    HAPPY_PID=$!
    echo "Happy started with PID: $HAPPY_PID"
    
    # Wait a moment for Happy to initialize
    sleep 3
    
    # Check if Happy is running
    if happy daemon status | grep -q "Daemon is running"; then
        echo "✅ Happy daemon is running"
        return 0
    else
        echo "❌ Happy daemon failed to start"
        return 1
    fi
}

# Main setup process
echo "Step 1: Device Setup"
echo "-------------------"
# Ensure port forwarding is active
adb -s $DEVICE_ID forward tcp:8080 tcp:8080 2>/dev/null
adb -s $DEVICE_ID forward tcp:60150 tcp:60150 2>/dev/null

echo "✅ Port forwarding configured"
echo ""

echo "Step 2: Authentication Check"
echo "----------------------------"
if check_happy_auth; then
    echo "✅ Happy is already authenticated"
    happy auth show-backup
    echo ""
else
    echo "❌ Happy needs authentication"
    echo "Please authenticate Happy in a terminal:"
    echo "  happy auth login --force"
    echo ""
    echo "Choose 'Mobile App' option when prompted"
    echo ""
    
    # Try to authenticate anyway
    echo "Attempting authentication..."
    if happy auth login --force 2>/dev/null; then
        echo "✅ Authentication successful"
    else
        echo "⚠️  Interactive authentication failed"
        echo "Please authenticate manually in a terminal"
    fi
fi

echo "Step 3: Start Happy with Claude-GLM"
echo "-----------------------------------"
if start_happy_glm; then
    echo "✅ Happy with Claude-GLM is running"
    echo ""
    
    echo "Step 4: Mobile Connection"
    echo "--------------------------"
    echo "1. Open Happy mobile app on your device"
    echo "2. Get backup key: happy auth show-backup"
    echo "3. Link device using backup key in mobile app"
    echo "4. Your computer should appear for connection"
    echo ""
    
    echo "📡 Connection Information:"
    echo "- Device ID: $DEVICE_ID"
    echo "- Local Port: 60150"
    echo "- Settings: ~/.happy/zai_settings.json"
    echo "- Model: Claude-GLM (glm-4.5)"
    echo ""
    
    echo "🔧 Useful Commands:"
    echo "- Check status: happy daemon status"
    echo "- View sessions: happy daemon list"
    echo "- Stop Happy: pkill -f happy"
    echo "- Restart: happy --settings ~/.happy/zai_settings.json"
    
else
    echo "❌ Failed to start Happy with Claude-GLM"
    echo "Please check your settings and try again"
fi