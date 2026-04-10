#!/bin/bash
cd /Users/Subho/CascadeProjects/windsurf-project/whatsapp-mcp/whatsapp-bridge
nohup go run main.go > /tmp/whatsapp-bridge.log 2>&1 &
echo "WhatsApp Bridge started - PID: $!"
