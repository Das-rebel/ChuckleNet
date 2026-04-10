#!/bin/bash

echo "🚀 ENABLING BRAVE DEBUGGING FOR AUTOMATIC MONITORING"
echo "======================================================="

# Kill any existing Brave instances
echo "🔄 Closing existing Brave instances..."
pkill -f "Brave Browser" 2>/dev/null || true
sleep 2

# Start Brave with remote debugging enabled
echo "🌐 Starting Brave with remote debugging..."
open -a "Brave Browser" --args --remote-debugging-port=9222 --user-data-dir="/tmp/brave_debug"

echo "⏳ Waiting for Brave to start..."
sleep 5

echo "✅ Brave is starting with remote debugging enabled"
echo "📊 You can now run: python3 brave_session_monitor.py"
echo ""
echo "💡 Make sure you're logged into Telegram in Brave when it opens!"
echo "🎯 The monitor will automatically connect to your session."