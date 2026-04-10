#!/bin/bash

# Start Docker for OpenClaw Alexa Bridge using Colima
# Colima provides a Linux VM with Docker support for macOS

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                                                               ║${NC}"
echo -e "${GREEN}║   🚀 OpenClaw Bridge - Colima Docker Startup              ║${NC}"
echo -e "${GREEN}║                                                               ║${NC}"
echo -e "${GREEN}╚═════════════════════════════════════════════╝${NC}"
echo ""

# Check prerequisites
echo -e "${YELLOW}📋 Checking prerequisites...${NC}"

if ! command -v colima &> /dev/null; then
    echo -e "${RED}❌ Colima not installed${NC}"
    echo -e "${YELLOW}Install with: brew install colima${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Colima: installed${NC}"
echo ""

# Check if Docker daemon is running
if docker info > /dev/null 2>&1 | grep -q "Server Version: 29"; then
    echo -e "${GREEN}✅ Docker daemon running${NC}"
else
    echo -e "${YELLOW}⚠️  Docker daemon not running${NC}"
fi
echo ""

# Start or restart Colima VM
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Step 1: Start Colima VM${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if docker info 2>&1 | grep -q "Server Version: 29"; then
    echo -e "${YELLOW}Docker daemon already running, restarting Colima...${NC}"
    colima restart 2>/dev/null
else
    echo -e "${YELLOW}Starting Colima VM with Docker...${NC}"
    colima start --cpu 2 --memory 4 --docker-runtime 2>/dev/null
fi

# Wait for Colima to be ready
echo ""
echo -e "${YELLOW}Waiting for Colima VM to be ready...${NC}"
sleep 10

# Verify Docker is running
if docker ps 2>&1 | grep -q "openclaw-bridge"; then
    echo -e "${GREEN}✅ OpenClaw bridge container is running!${NC}"
else
    echo -e "${YELLOW}Waiting for container...${NC}"
    sleep 5
    if docker ps 2>&1 | grep -q "openclaw-bridge"; then
        echo -e "${GREEN}✅ OpenClaw bridge container is running!${NC}"
    else
        echo -e "${RED}❌ Container failed to start${NC}"
        echo -e "${YELLOW}Check logs: docker logs openclaw-bridge${NC}"
        exit 1
    fi
fi

echo ""
echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                               ║${NC}"
echo -e "${BLUE}║   🎉 Colima Docker Startup Complete!                ║${NC}"
echo -e "${BLUE}║                                                               ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════╝${NC}"
echo ""

echo -e "${GREEN}✅ Ready to deploy!${NC}"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 Next Steps:"
echo ""
echo "1. Build and push Docker image to Google Cloud"
echo "   cd /Users/Subho/openclaw-alexa-bridge"
echo "   docker build -t openclaw-bridge:latest ."
echo "   docker tag openclaw-bridge:latest us-central1-docker.pkg.dev/dauntless-glow-487412-s7/openclaw-bridge:latest"
echo "   docker push us-central1-docker.pkg.dev/dauntless-glow-487412-s7/openclaw-bridge:latest"
echo ""
echo "2. Deploy to Cloud Run"
echo "   gcloud run deploy openclaw-bridge \\"
echo "       --image=us-central1-docker.pkg.dev/dauntless-glow-487412-s7/openclaw-bridge:latest \\"
echo "       --platform=managed \\"
echo "       --region=us-central1 \\"
echo "       --allow-unauthenticated \\"
echo "       --port=3000 \\"
echo "       --memory=512Mi \\"
echo "       --cpu=1 \\"
echo "       --min-instances=0 \\"
echo "       --max-instances=1000 \\"
echo "       --timeout=3600 \\"
echo "       --set-env-vars=\"OPENCLAW_GATEWAY_URL=ws://localhost:18789\" \\"
echo "       --set-env-vars=\"LOG_VERBOSE=true\" \\"
echo "       --set-env-vars=\"BRIDGE_PORT=3000\""
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "💡 Alternative: Use Google Cloud Console"
echo "   https://console.cloud.google.com/run"
echo "   Upload Dockerfile or use the web UI"
echo ""
echo "📚 Management Commands:"
echo ""
echo "  Stop Colima:"
echo "  ./start-docker-with-colima.sh stop"
echo ""
echo "  Restart Colima:"
echo "  ./start-docker-with-colima.sh start"
echo ""
echo "  Check container status:"
echo "  docker ps | grep openclaw"
echo ""
echo "  View logs:"
echo "  docker logs -f openclaw-bridge"
echo ""
echo "  Delete container (if needed):"
echo "  docker rm -f openclaw-bridge"
echo ""
echo -e "${GREEN}✅ Script complete!${NC}"
