#!/bin/bash
# OpenClaw MCP Voice System - Startup Script
# Starts MCP server and Voice server with full integration

set -e

echo "🚀 OpenClaw MCP Voice System"
echo "======================================"
echo ""

# Check if MCP server is running
if ps aux | grep -q "[m]cp-server"; then
    echo "✅ MCP Server already running (PID $(pgrep -f 'mcp-server' | head -1))"
else
    echo "📍 Starting MCP Server..."
    node ~/.npm-global/lib/node_modules/openclaw/dist/mcp-server/index.js > /tmp/mcp-server.log 2>&1 &
    MCP_PID=$!
    echo "✅ MCP Server started (PID: $MCP_PID)"
    echo "   Logs: tail -f /tmp/mcp-server.log"
    sleep 2
fi

# Verify MCP server is listening
if lsof -i :18790 > /dev/null 2>&1; then
    echo "✅ MCP Server listening on port 18790"
else
    echo "❌ ERROR: MCP Server not listening on port 18790"
    echo "   Check logs: tail -20 /tmp/mcp-server.log"
    exit 1
fi

echo ""
echo "📍 Starting Voice Server with MCP integration..."
echo ""

# Change to voice server directory
cd ~/projects/openclaw-voice-chat

# Set environment variables
export MCP_TOOLS_ENABLED=true
export MCP_SERVER_URL=http://localhost:18790/mcp
export OPENCLAW_AUTH_TOKEN=local-dev-token-1769809384

# Show configuration
echo "Configuration:"
echo "  MCP_TOOLS_ENABLED: $MCP_TOOLS_ENABLED"
echo "  MCP_SERVER_URL: $MCP_SERVER_URL"
echo "  Voice Server: Port 5999"
echo ""

# Start voice server
python server/voice_server.py
