#!/bin/bash
echo "🔄 Restarting N8N..."

if [ -f "n8n.pid" ]; then
    PID=$(cat n8n.pid)
    if ps -p $PID > /dev/null; then
        kill $PID
        echo "Stopped N8N (PID: $PID)"
    fi
    rm n8n.pid
fi

export $(cat .env | grep -v '^#' | xargs)
nohup n8n start > n8n.log 2>&1 &
N8N_PID=$!
echo $N8N_PID > n8n.pid

sleep 3
if ps -p $N8N_PID > /dev/null; then
    echo "✅ N8N restarted (PID: $N8N_PID)"
    echo "🌐 Web Interface: http://localhost:5678"
else
    echo "❌ Failed to restart N8N"
fi
