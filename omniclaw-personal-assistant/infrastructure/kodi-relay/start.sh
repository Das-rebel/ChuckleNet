#!/bin/bash
# Start Kodi Relay Server
# Run this on your local machine to bridge Cloud Run to Kodi

cd "$(dirname "$0")"

# Load env vars from .env if exists
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

# Default values
export KODI_HOST=${KODI_HOST:-"192.168.0.101"}
export KODI_PORT=${KODI_PORT:-"8080"}
export KODI_USER=${KODI_USER:-"kodi"}
export KODI_PASSWORD=${KODI_PASSWORD:-"Password"}
export RELAY_PORT=${RELAY_PORT:-"3001"}

echo "📺 Starting Kodi Relay..."
echo "   Kodi: $KODI_HOST:$KODI_PORT"
echo "   Relay Port: $RELAY_PORT"

# Install deps if needed
if [ ! -d node_modules ]; then
  npm install
fi

# Start relay
node server.js