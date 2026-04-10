#!/bin/bash
#
# WhatsApp Auto-Reply + TMLPD: VPS Deployment Script
# Usage: ./deploy-whatsapp-to-vps.sh <vps-ip> [root]
#

set -e

# Configuration
VPS_IP="${1:-}"
VPS_USER="${2:-root}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Functions
log() { echo -e "${BLUE}[$(date +%H:%M:%S)]${NC} $1"; }
success() { echo -e "${GREEN}✓${NC} $1"; }
warn() { echo -e "${YELLOW}⚠${NC} $1"; }
error() { echo -e "${RED}✗${NC} $1"; }

# Check arguments
if [ -z "$VPS_IP" ]; then
    error "Usage: $0 <vps-ip> [user]"
    echo ""
    echo "Example:"
    echo "  $0 123.45.67.89           # Uses root user"
    echo "  $0 123.45.67.89 ubuntu    # Uses ubuntu user"
    exit 1
fi

log "🚀 Deploying WhatsApp Auto-Reply with TMLPD to VPS"
log "   Target: ${VPS_USER}@${VPS_IP}"
echo ""

# Test SSH connection
log "Testing SSH connection..."
if ! ssh -o ConnectTimeout=5 "${VPS_USER}@${VPS_IP}" "echo 'Connected'" > /dev/null 2>&1; then
    error "Cannot connect to ${VPS_USER}@${VPS_IP}"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Check VPS IP is correct"
    echo "  2. Ensure SSH key is added: ssh-copy-id ${VPS_USER}@${VPS_IP}"
    echo "  3. Verify VPS is running"
    exit 1
fi
success "SSH connection verified"

# Check if main script exists
if [ ! -f "$SCRIPT_DIR/whatsapp_auto_reply_tmlpd.py" ]; then
    error "whatsapp_auto_reply_tmlpd.py not found in current directory"
    exit 1
fi

# Copy files to VPS
log "📦 Copying files to VPS..."
scp "$SCRIPT_DIR/whatsapp_auto_reply_tmlpd.py" "${VPS_USER}@${VPS_IP}:/root/"
if [ -f "$SCRIPT_DIR/Desktop/TMLPD_TRIGGER_MESSAGES.md" ]; then
    scp "$SCRIPT_DIR/Desktop/TMLPD_TRIGGER_MESSAGES.md" "${VPS_USER}@${VPS_IP}:/root/"
fi
success "Files copied"

# Install dependencies and setup service
log "🔧 Setting up VPS environment..."
ssh "${VPS_USER}@${VPS_IP}" << 'ENDSSH'
set -e

echo "📋 System info:"
echo "  OS: $(lsb_release -d | cut -f2-)"
echo "  Python: $(python3 --version 2>&1 || echo 'Not installed')"
echo ""

# Update and install dependencies
echo "📦 Installing system dependencies..."
apt-get update -qq
apt-get install -y -qq python3-pip python3-venv > /dev/null 2>&1

# Install Python packages
echo "🐍 Installing Python packages..."
pip3 install --quiet --upgrade \
    asyncio \
    aiohttp \
    websockets \
    python-dotenv 2>/dev/null || true

# Install Node.js and OpenClaw
if ! command -v openclaw &> /dev/null; then
    echo "📦 Installing Node.js and OpenClaw..."
    curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - > /dev/null 2>&1
    apt-get install -y -qq nodejs > /dev/null 2>&1
    npm install -g --silent openclaw 2>/dev/null || true
    echo "   OpenClaw installed: $(openclaw --version 2>&1 || echo 'Version unknown')"
else
    echo "   OpenClaw already installed: $(openclaw --version 2>&1 || echo 'Version unknown')"
fi

# Create log directory
mkdir -p /tmp/logs

# Create systemd service
echo "⚙️  Creating systemd service..."
cat > /etc/systemd/system/whatsapp-auto-reply.service << 'EOF'
[Unit]
Description=WhatsApp Auto-Reply with TMLPD Integration
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=/root
ExecStart=/usr/bin/python3 /root/whatsapp_auto_reply_tmlpd.py
Restart=always
RestartSec=10
StandardOutput=append:/tmp/whatsapp-auto-reply.log
StandardError=append:/tmp/whatsapp-auto-reply-error.log

# Environment variables
Environment="TMLPD_ENABLED=true"
Environment="TMLPD_THRESHOLD=40"
Environment="AGENT_TIMEOUT=65000"
Environment="LOG_FILE=/tmp/whatsapp-auto-reply-live.log"

[Install]
WantedBy=multi-user.target
EOF

# Create logrotate config
echo "📝 Setting up log rotation..."
cat > /etc/logrotate.d/whatsapp-auto-reply << 'EOF'
/tmp/whatsapp-auto-reply*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0640 root root
}
EOF

# Reload systemd and enable service
echo "🔄 Reloading systemd..."
systemctl daemon-reload
systemctl enable whatsapp-auto-reply.service

# Show status
echo ""
echo "✅ Setup complete!"
echo ""
ENDSSH

success "VPS environment configured"

# Start the service
log "🚀 Starting WhatsApp auto-reply service..."
ssh "${VPS_USER}@${VPS_IP}" << 'ENDSSH'
systemctl restart whatsapp-auto-reply
sleep 3
systemctl status whatsapp-auto-reply --no-pager
ENDSSH

success "Service started"

# Create monitoring script on VPS
log "📊 Creating monitoring helpers..."
ssh "${VPS_USER}@${VPS_IP}" << 'ENDSSH'
cat > /usr/local/bin/whatsapp-status << 'EOF'
#!/bin/bash
echo "=== WhatsApp Auto-Reply Status ==="
echo ""
systemctl status whatsapp-auto-reply --no-pager -l
echo ""
echo "=== Recent Logs (last 20 lines) ==="
journalctl -u whatsapp-auto-reply -n 20 --no-pager
EOF
chmod +x /usr/local/bin/whatsapp-status

cat > /usr/local/bin/whatsapp-logs << 'EOF'
#!/bin/bash
tail -f /tmp/whatsapp-auto-reply-live.log
EOF
chmod +x /usr/local/bin/whatsapp-logs

cat > /usr/local/bin/whatsapp-restart << 'EOF'
#!/bin/bash
systemctl restart whatsapp-auto-reply
echo "Service restarted. Use 'whatsapp-status' to check."
EOF
chmod +x /usr/local/bin/whatsapp-restart
ENDSSH

success "Monitoring commands created"

# Final summary
echo ""
success "Deployment complete!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🎉 WhatsApp Auto-Reply with TMLPD is now running on your VPS!"
echo ""
echo "📊 Monitoring commands (run from VPS):"
echo "   ssh ${VPS_USER}@${VPS_IP}"
echo "   whatsapp-status    # Show service status and logs"
echo "   whatsapp-logs      # Follow live logs"
echo "   whatsapp-restart   # Restart service"
echo ""
echo "📱 Test by sending a WhatsApp message to: +919003349852"
echo ""
echo "🔍 Quick test messages (from Desktop/TMLPD_TRIGGER_MESSAGES.md):"
echo "   - Simple: 'What is 2+2?'"
echo "   - TMLPD:  'Design a scalable REST API with JWT authentication'"
echo ""
echo "⚠️  Important notes:"
echo "   - Service auto-starts on VPS reboot"
echo "   - Logs rotate daily (7 days retained)"
echo "   - Monitor: journalctl -u whatsapp-auto-reply -f"
echo ""
echo "🛠️  Troubleshooting:"
echo "   - Check logs: ssh ${VPS_USER}@${VPS_IP} 'journalctl -u whatsapp-auto-reply -n 50'"
echo "   - Restart:    ssh ${VPS_USER}@${VPS_IP} 'systemctl restart whatsapp-auto-reply'"
echo "   - Stop:       ssh ${VPS_USER}@${VPS_IP} 'systemctl stop whatsapp-auto-reply'"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
