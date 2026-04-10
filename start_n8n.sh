#!/bin/bash

# Start N8N Server for Brand Jobs Automation
echo "🚀 Starting N8N Server..."

# Load environment variables (skip comments and empty lines)
export $(cat .env | grep -v '^#' | grep -v '^$' | xargs)

# Check if N8N is already running
if [ -f "n8n.pid" ]; then
    PID=$(cat n8n.pid)
    if ps -p $PID > /dev/null; then
        echo "⚠️  N8N is already running (PID: $PID)"
        echo "🌐 Web Interface: http://localhost:5678"
        echo "👤 Username: admin"
        echo "🔑 Password: brandjobs2024"
        exit 0
    else
        rm n8n.pid
    fi
fi

# Start N8N in background
echo "Starting N8N server..."
nohup n8n start > n8n.log 2>&1 &
N8N_PID=$!
echo $N8N_PID > n8n.pid

# Wait for N8N to start
echo "Waiting for N8N to start..."
sleep 5

# Check if N8N started successfully
if ps -p $N8N_PID > /dev/null; then
    echo "✅ N8N server started successfully!"
    echo "🌐 Web Interface: http://localhost:5678"
    echo "👤 Username: admin"
    echo "🔑 Password: brandjobs2024"
    echo "📋 Logs: tail -f n8n.log"
    echo ""
    echo "📥 Next steps:"
    echo "1. Open http://localhost:5678 in your browser"
    echo "2. Login with admin/brandjobs2024"
    echo "3. Import n8n/daily_brand_jobs_over_40lpa.json"
    echo "4. Configure Google Sheets credentials"
    echo "5. Test and activate the workflow"
else
    echo "❌ Failed to start N8N server"
    echo "📋 Check logs: cat n8n.log"
    exit 1
fi