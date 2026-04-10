#!/bin/bash

# Brand Jobs Auto-Discovery Setup Script
# This script sets up the complete automation system

set -e

echo "🚀 Setting up Brand Jobs Auto-Discovery System..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if .env file exists and has required variables
check_env() {
    print_status "Checking environment configuration..."
    
    if [ ! -f ".env" ]; then
        print_error ".env file not found!"
        exit 1
    fi
    
    # Check for required variables
    if grep -q "your_serpapi_key_here" .env; then
        print_warning "Please update SERPAPI_KEY in .env file"
        echo "Get your free API key from: https://serpapi.com"
        read -p "Enter your SerpAPI key: " serpapi_key
        sed -i.bak "s/your_serpapi_key_here/$serpapi_key/" .env
        print_success "SerpAPI key updated"
    fi
    
    if grep -q "your_google_sheet_id_here" .env; then
        print_warning "Please update GOOGLE_SHEET_ID in .env file"
        echo "Create a Google Sheet and copy the ID from the URL"
        echo "Example: https://docs.google.com/spreadsheets/d/1A2B3C.../edit"
        read -p "Enter your Google Sheet ID: " sheet_id
        sed -i.bak "s/your_google_sheet_id_here/$sheet_id/" .env
        print_success "Google Sheet ID updated"
    fi
    
    if grep -q "you@example.com" .env; then
        print_warning "Please update DIGEST_EMAIL in .env file (optional)"
        read -p "Enter your email for daily digest (or press Enter to skip): " email
        if [ ! -z "$email" ]; then
            sed -i.bak "s/you@example.com/$email/" .env
            print_success "Email updated"
        fi
    fi
}

# Create Google Sheet template
create_google_sheet_template() {
    print_status "Creating Google Sheet template..."
    
    if [ ! -d "sheet" ]; then
        mkdir -p sheet
    fi
    
    # The CSV files are already created, just verify they exist
    if [ -f "sheet/jobs_sheet_template.csv" ] && [ -f "sheet/companies.csv" ]; then
        print_success "Google Sheet templates ready"
        echo "📋 Next steps for Google Sheets:"
        echo "1. Create a new Google Sheet"
        echo "2. Import sheet/jobs_sheet_template.csv as 'jobs' tab"
        echo "3. Import sheet/companies.csv as 'companies' tab (optional)"
        echo "4. Copy the Sheet ID from the URL and update .env file"
    else
        print_error "Sheet templates not found!"
        exit 1
    fi
}

# Start N8N server
start_n8n() {
    print_status "Starting N8N server..."
    
    # Load environment variables
    export $(cat .env | grep -v '^#' | xargs)
    
    # Start N8N in background
    nohup n8n start > n8n.log 2>&1 &
    N8N_PID=$!
    echo $N8N_PID > n8n.pid
    
    # Wait a moment for N8N to start
    sleep 5
    
    # Check if N8N is running
    if ps -p $N8N_PID > /dev/null; then
        print_success "N8N server started (PID: $N8N_PID)"
        echo "🌐 N8N Web Interface: http://localhost:5678"
        echo "👤 Username: admin"
        echo "🔑 Password: brandjobs2024"
    else
        print_error "Failed to start N8N server"
        exit 1
    fi
}

# Import N8N workflow
import_workflow() {
    print_status "Workflow import instructions..."
    echo "📥 To import the workflow:"
    echo "1. Open N8N at http://localhost:5678"
    echo "2. Login with admin/brandjobs2024"
    echo "3. Click 'Import from File'"
    echo "4. Select n8n/daily_brand_jobs_over_40lpa.json"
    echo "5. Configure Google Sheets credentials"
    echo "6. Test the workflow"
    echo "7. Activate the workflow"
}

# Create monitoring script
create_monitoring_script() {
    print_status "Creating monitoring script..."
    
    cat > monitor_brand_jobs.sh << 'EOF'
#!/bin/bash

# Brand Jobs Automation Monitor
echo "🔍 Brand Jobs Automation Status"
echo "================================"

# Check N8N process
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

# Check N8N web interface
if curl -s http://localhost:5678 > /dev/null; then
    echo "✅ N8N Web Interface: Accessible"
else
    echo "❌ N8N Web Interface: Not accessible"
fi

# Check log file
if [ -f "n8n.log" ]; then
    echo "📋 Recent N8N logs:"
    tail -5 n8n.log
fi

echo ""
echo "🔧 To restart N8N: ./restart_n8n.sh"
echo "🛑 To stop N8N: ./stop_n8n.sh"
EOF

    chmod +x monitor_brand_jobs.sh
    print_success "Monitoring script created"
}

# Create restart script
create_restart_script() {
    cat > restart_n8n.sh << 'EOF'
#!/bin/bash

echo "🔄 Restarting N8N server..."

# Stop existing N8N
if [ -f "n8n.pid" ]; then
    PID=$(cat n8n.pid)
    if ps -p $PID > /dev/null; then
        kill $PID
        echo "Stopped N8N (PID: $PID)"
    fi
    rm n8n.pid
fi

# Start N8N
export $(cat .env | grep -v '^#' | xargs)
nohup n8n start > n8n.log 2>&1 &
N8N_PID=$!
echo $N8N_PID > n8n.pid

sleep 3
if ps -p $N8N_PID > /dev/null; then
    echo "✅ N8N restarted successfully (PID: $N8N_PID)"
    echo "🌐 Web Interface: http://localhost:5678"
else
    echo "❌ Failed to restart N8N"
fi
EOF

    chmod +x restart_n8n.sh
}

# Create stop script
create_stop_script() {
    cat > stop_n8n.sh << 'EOF'
#!/bin/bash

echo "🛑 Stopping N8N server..."

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

    chmod +x stop_n8n.sh
}

# Main execution
main() {
    echo "🎯 Brand Jobs Auto-Discovery Setup"
    echo "=================================="
    echo ""
    
    check_env
    create_google_sheet_template
    create_monitoring_script
    create_restart_script
    create_stop_script
    
    echo ""
    print_success "Setup completed successfully!"
    echo ""
    echo "📋 Next Steps:"
    echo "1. Create Google Sheet and import templates"
    echo "2. Update .env with your Google Sheet ID"
    echo "3. Run: ./start_n8n.sh (or start N8N manually)"
    echo "4. Import workflow in N8N interface"
    echo "5. Configure Google Sheets credentials"
    echo "6. Test and activate workflow"
    echo ""
    echo "🔧 Management Commands:"
    echo "• Monitor: ./monitor_brand_jobs.sh"
    echo "• Restart: ./restart_n8n.sh"
    echo "• Stop: ./stop_n8n.sh"
    echo ""
    echo "📚 Documentation: docs/QUICKSTART.md"
}

# Run main function
main "$@"