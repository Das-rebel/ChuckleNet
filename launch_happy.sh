#!/bin/bash
# Direct Happy Claude-GLM Launch

echo "🎯 Direct Happy Claude-GLM Launch"
echo "================================="

# Start Happy with Claude-GLM directly
echo "Starting Happy with Claude-GLM..."
happy --settings ~/.happy/zai_settings.json "Ready for mobile connection" &

# Wait for Happy to start
sleep 3

# Check status
echo ""
echo "📊 Status:"
happy daemon status

echo ""
echo "📱 MOBILE CONNECTION:"
echo "====================="
echo "1. Open Happy mobile app"
echo "2. Your computer should appear automatically"
echo "3. Tap to connect - no QR codes needed!"
echo ""
echo "🔧 Commands:"
echo "- Stop: pkill -f happy"
echo "- Restart: ./happy_simple.sh"
echo "- Status: happy daemon status"