#!/bin/bash
echo "🔍 Brand Jobs Automation Status"
echo "================================"

if [ -f "n8n.pid" ]; then
    PID=$(cat n8n.pid)
    if ps -p $PID > /dev/null; then
        echo "✅ N8N Server: Running (PID: $PID)"
    else
        echo "❌ N8N Server: Not running"
    fi
else
    echo "❌ N8N Server: No PID file found"
fi

if curl -s http://localhost:5678 > /dev/null; then
    echo "✅ N8N Web Interface: Accessible"
else
    echo "❌ N8N Web Interface: Not accessible"
fi

if [ -f "n8n.log" ]; then
    echo "📋 Recent logs:"
    tail -3 n8n.log
fi
