#!/bin/bash

# OpenClaw Alexa Bridge - Ngrok Tunnel Manager

set -e

NGROK_PORT="${BRIDGE_PORT:-3000}"
LOG_FILE="/tmp/ngrok-bridge.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

case "${1:-}" in
    start)
        echo -e "${GREEN}🚀 Starting ngrok tunnel...${NC}"

        # Check if ngrok is already running
        if pgrep -f "ngrok.*${NGROK_PORT}" > /dev/null; then
            echo -e "${YELLOW}⚠️  Ngrok is already running on port ${NGROK_PORT}${NC}"
            echo -e "${YELLOW}Get status: curl -s http://localhost:4040/api/tunnels | jq '.'${NC}"
            exit 0
        fi

        # Start ngrok
        ngrok http ${NGROK_PORT} --log=stdout > ${LOG_FILE} 2>&1 &

        # Wait for ngrok to start
        echo -e "${YELLOW}Waiting for ngrok to initialize...${NC}"
        sleep 3

        # Get the public URL
        PUBLIC_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | jq -r '.tunnels[0].public_url' 2>/dev/null)

        if [ -z "${PUBLIC_URL}" ]; then
            echo -e "${RED}❌ Failed to get ngrok public URL${NC}"
            echo "Check logs: tail -f ${LOG_FILE}"
            exit 1
        fi

        echo -e "${GREEN}✅ Ngrok tunnel started successfully!${NC}"
        echo ""
        echo "════════════════════════════════════════════════"
        echo -e "${GREEN}📡 PUBLIC URL: ${PUBLIC_URL}${NC}"
        echo "════════════════════════════════════════════════"
        echo ""
        echo "Available endpoints:"
        echo "  Health:   ${PUBLIC_URL}/health"
        echo "  Alexa:    ${PUBLIC_URL}/alexa"
        echo "  Stats:    ${PUBLIC_URL}/stats"
        echo "  Dashboard: ${PUBLIC_URL}/dashboard"
        echo ""
        echo "📝 Logs: tail -f ${LOG_FILE}"
        echo "📊 Status: curl -s http://localhost:4040/api/tunnels | jq '.'"
        echo ""
        echo "📌 Update Alexa Skill Endpoint to:"
        echo -e "${GREEN}${PUBLIC_URL}/alexa${NC}"
        ;;

    stop)
        echo -e "${YELLOW}🛑 Stopping ngrok tunnel...${NC}"

        # Kill ngrok processes
        pkill -f "ngrok.*${NGROK_PORT}" 2>/dev/null || true

        if pgrep -f "ngrok" > /dev/null; then
            echo -e "${RED}⚠️  Some ngrok processes still running${NC}"
            echo "Run: pkill -f ngrok"
        else
            echo -e "${GREEN}✅ Ngrok tunnel stopped${NC}"
        fi
        ;;

    status)
        echo -e "${GREEN}📊 Ngrok Tunnel Status${NC}"
        echo ""

        # Check if ngrok is running
        if pgrep -f "ngrok.*${NGROK_PORT}" > /dev/null; then
            echo -e "${GREEN}● Status: RUNNING${NC}"

            # Get tunnel info
            PUBLIC_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | jq -r '.tunnels[0].public_url' 2>/dev/null)

            if [ -n "${PUBLIC_URL}" ]; then
                echo ""
                echo "📡 Public URL: ${PUBLIC_URL}"
                echo "📡 Local:      http://localhost:${NGROK_PORT}"
                echo ""
                echo "Endpoints:"
                echo "  Health:   ${PUBLIC_URL}/health"
                echo "  Alexa:    ${PUBLIC_URL}/alexa"
                echo "  Stats:    ${PUBLIC_URL}/stats"
                echo "  Dashboard: ${PUBLIC_URL}/dashboard"
            fi
        else
            echo -e "${RED}● Status: STOPPED${NC}"
        fi
        ;;

    restart)
        echo -e "${YELLOW}🔄 Restarting ngrok tunnel...${NC}"
        "$0" stop
        sleep 2
        "$0" start
        ;;

    logs)
        echo -e "${GREEN}📝 Ngrok Logs${NC}"
        echo ""
        if [ -f "${LOG_FILE}" ]; then
            tail -f ${LOG_FILE}
        else
            echo -e "${RED}No log file found${NC}"
        fi
        ;;

    *)
        echo "OpenClaw Alexa Bridge - Ngrok Tunnel Manager"
        echo ""
        echo "Usage: $0 {start|stop|status|restart|logs}"
        echo ""
        echo "Commands:"
        echo "  start    Start ngrok tunnel and show public URL"
        echo "  stop     Stop ngrok tunnel"
        echo "  status   Show tunnel status and public URL"
        echo "  restart  Restart tunnel (stop + start)"
        echo "  logs     Show ngrok logs (tail -f)"
        echo ""
        echo "Environment Variables:"
        echo "  BRIDGE_PORT   Port to tunnel (default: 3000)"
        echo ""
        echo "Examples:"
        echo "  $0 start     # Start tunnel on port 3000"
        echo "  BRIDGE_PORT=8080 $0 start  # Start tunnel on port 8080"
        echo "  $0 status    # Show current status"
        echo "  $0 stop      # Stop tunnel"
        echo "  $0 logs      # View logs"
        exit 1
        ;;
esac
