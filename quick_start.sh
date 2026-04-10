#!/bin/bash

# Quick Start Script for Brand Jobs Automation
echo "🚀 Brand Jobs Automation - Quick Start"
echo "======================================"

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    exit 1
fi

echo "✅ Environment file found"
echo "📋 Please update the following in .env:"
echo "   - SERPAPI_KEY: Get from https://serpapi.com"
echo "   - GOOGLE_SHEET_ID: Create a Google Sheet and copy ID from URL"
echo "   - DIGEST_EMAIL: Your email for notifications (optional)"
echo ""

# Create management scripts
echo "🔧 Creating management scripts..."

# Monitor script
cat > monitor_brand_jobs.sh << 'EOF'
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
EOF

# Restart script
cat > restart_n8n.sh << 'EOF'
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
EOF

# Stop script
cat > stop_n8n.sh << 'EOF'
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
EOF

chmod +x monitor_brand_jobs.sh restart_n8n.sh stop_n8n.sh

echo "✅ Management scripts created"
echo ""
echo "🎯 Next Steps:"
echo "1. Update .env with your API keys"
echo "2. Create Google Sheet and import templates from sheet/ folder"
echo "3. Run: ./start_n8n.sh"
echo "4. Open http://localhost:5678 (admin/brandjobs2024)"
echo "5. Import n8n/enhanced_brand_jobs_workflow.json"
echo "6. Configure Google Sheets credentials"
echo "7. Test and activate workflow"
echo ""
echo "🔧 Management Commands:"
echo "• Monitor: ./monitor_brand_jobs.sh"
echo "• Restart: ./restart_n8n.sh"
echo "• Stop: ./stop_n8n.sh"
echo ""
echo "📚 Documentation: README_BRAND_JOBS_AUTOMATION.md"