#!/bin/bash

# Test script for OpenClaw Alexa Bridge
echo "=========================================="
echo "Testing OpenClaw Alexa Bridge Server"
echo "=========================================="
echo ""

cd /Users/Subho/openclaw-alexa-bridge

# Check if Node.js is available
echo "1. Checking Node.js..."
if command -v node &> /dev/null; then
    echo "   ✓ Node.js found: $(node --version)"
else
    echo "   ✗ Node.js not found"
    exit 1
fi

# Check for existing processes on port 3000
echo ""
echo "2. Checking port 3000..."
if lsof -ti:3000 &> /dev/null; then
    echo "   ⚠ Port 3000 is in use, killing process..."
    kill -9 $(lsof -ti:3000) 2>/dev/null
    sleep 1
else
    echo "   ✓ Port 3000 is free"
fi

# Check for gateway on port 18789
echo ""
echo "3. Checking OpenClaw Gateway (port 18789)..."
if lsof -ti:18789 &> /dev/null; then
    echo "   ✓ Gateway is running"
else
    echo "   ⚠ Gateway is NOT running"
    echo "   → Start with: cd ~/openclaw && npm start"
fi

# Start the bridge server
echo ""
echo "4. Starting bridge server..."
node index.js > /tmp/bridge-startup.log 2>&1 &
BRIDGE_PID=$!
echo "   ✓ Server started with PID: $BRIDGE_PID"

# Wait for server to initialize
echo "   → Waiting 5 seconds for startup..."
sleep 5

# Check if server is still running
if ps -p $BRIDGE_PID > /dev/null; then
    echo "   ✓ Server is running"
else
    echo "   ✗ Server failed to start"
    echo ""
    echo "=== Startup Logs ==="
    cat /tmp/bridge-startup.log
    exit 1
fi

# Show startup logs
echo ""
echo "5. Startup Logs:"
echo "=========================================="
cat /tmp/bridge-startup.log
echo "=========================================="

# Test health endpoint
echo ""
echo "6. Testing health endpoint..."
HEALTH_RESPONSE=$(curl -s http://localhost:3000/health 2>&1)
if [ $? -eq 0 ]; then
    echo "   ✓ Health check successful"
    echo "   Response: $HEALTH_RESPONSE"
else
    echo "   ✗ Health check failed"
fi

# Test Alexa endpoint with LaunchRequest
echo ""
echo "7. Testing Alexa endpoint (LaunchRequest)..."
ALEXA_RESPONSE=$(curl -s -X POST http://localhost:3000/alexa \
    -H "Content-Type: application/json" \
    -d '{"request":{"type":"LaunchRequest"},"session":{"user":{"userId":"test-user-123"}}}' 2>&1)

if [ $? -eq 0 ]; then
    echo "   ✓ Alexa request successful"
    echo "   Response: $ALEXA_RESPONSE"
else
    echo "   ✗ Alexa request failed"
fi

# Cleanup
echo ""
echo "8. Cleanup..."
kill $BRIDGE_PID 2>/dev/null
echo "   ✓ Server stopped"

echo ""
echo "=========================================="
echo "Test Complete"
echo "=========================================="
