#!/bin/bash

# Claude-Qwen: EXTREME SPEED MODE for 8GB M1 Mac
# Using Qwen 2.5 Coder 7B + TurboQuant + Flash Attention + Memory Purge

# Configuration
PROXY_PORT=8001
PROXY_PID=""
WORKSPACE="$HOME/.claude-qwen-workspace"

# --- SPEED HACKS ---
# 1. Force Flash Attention for faster prompt processing
export OLLAMA_FLASH_ATTENTION=1
# 2. Force TurboQuant (4-bit KV cache) to save ~1.5GB RAM
export OLLAMA_KV_CACHE_TYPE=q4_0
# 3. Memory Purge (requires password) to free up system cache for the LLM
echo "🧹 Purging system memory for maximum AI performance..."
sudo purge

# Function to clean up background processes
cleanup() {
    echo ""
    echo "Shutting down Claude-Qwen proxy..."
    if [ -n "$PROXY_PID" ]; then
        kill "$PROXY_PID" 2>/dev/null
    fi
    exit
}

trap cleanup EXIT INT TERM

echo "🚀 Starting Claude-Qwen Local Workspace..."

# Sync current CLAUDE.md from home to workspace
if [ -f "$HOME/CLAUDE.md" ]; then
    cp "$HOME/CLAUDE.md" "$WORKSPACE/CLAUDE.md"
fi

# Start the Node.js proxy in the background
cd "$HOME"
node claude-qwen-proxy.js &
PROXY_PID=$!

# Wait for proxy to be ready
echo "⌛ Warming up Qwen 2.5 Coder 7B (Extreme Speed Mode)..."
max_retries=30
count=0
while ! curl -s "http://localhost:$PROXY_PORT/health" > /dev/null; do
    sleep 1
    ((count++))
    if [ $count -ge $max_retries ]; then
        echo "❌ Proxy failed to start. Check if Ollama is running."
        exit 1
    fi
done

echo "✅ Claude-Qwen is ready! Speed optimization: ACTIVE."
echo "----------------------------------------------------"

# Enter the workspace and launch Claude Code
cd "$WORKSPACE"
export ANTHROPIC_BASE_URL="http://localhost:$PROXY_PORT"
export ANTHROPIC_API_KEY="local-qwen-key"

# Run claude with all passed arguments
claude "$@"
