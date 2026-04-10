#!/bin/bash

echo "🔄 Starting Brave with Remote Debugging..."
echo

# Kill existing Brave processes gracefully
echo "⏹️  Stopping existing Brave processes..."
pkill -f "Brave Browser" 2>/dev/null
sleep 3

# Check if processes stopped
if pgrep -f "Brave Browser" > /dev/null; then
    echo "⚠️  Some Brave processes still running, forcing stop..."
    pkill -9 -f "Brave Browser" 2>/dev/null
    sleep 2
fi

echo "✅ Brave stopped"
echo

# Launch Brave with remote debugging
echo "🚀 Launching Brave with remote debugging on port 9222..."
nohup /Applications/Brave\ Browser.app/Contents/MacOS/Brave\ Browser \
    --remote-debugging-port=9222 \
    --user-data-dir=/Users/Subho/Library/Application\ Support/BraveSoftware/Brave-Browser \
    --no-first-run \
    --no-default-browser-check \
    > /dev/null 2>&1 &

BRAVE_PID=$!
echo "✅ Brave started with PID: $BRAVE_PID"
echo

# Wait for Brave to start
echo "⏳ Waiting for Brave to start..."
sleep 8

# Check if debugging port is open
if lsof -i :9222 > /dev/null 2>&1; then
    echo "✅ Remote debugging is active on port 9222"
    echo
    echo "📝 Debugging URL: http://localhost:9222"
    echo "🌐 Brave is ready for automation!"
else
    echo "⚠️  Remote debugging port not detected"
    echo "   Brave may still be starting..."
fi

echo
echo "✅ Ready! You can now run: python3 /Users/Subho/alexa_skill_fixer.py"
