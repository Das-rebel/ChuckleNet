#!/bin/bash
echo "🛑 Stopping N8N..."

if [ -f "n8n.pid" ]; then
    PID=$(cat n8n.pid)
    if ps -p $PID > /dev/null; then
        kill $PID
        echo "✅ N8N stopped (PID: $PID)"
    else
        echo "❌ N8N process not found"
    fi
    rm n8n.pid
else
    echo "❌ No PID file found"
fi
