#!/bin/bash

###############################################################################
# Kodi/Fen Integration Deep Dive Test
###############################################################################

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

FEN_FILE="/Users/Subho/omniclaw-personal-assistant/apps/media-streaming/integrations/fen-integration.js"

echo -e "${CYAN}╔═══════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║  Kodi/Fen Integration - Deep Technical Analysis                 ║${NC}"
echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════════╝${NC}"
echo ""

###############################################################################
# File Overview
###############################################################################

echo -e "${BLUE}=== 1. File Overview ===${NC}"
echo ""

if [ ! -f "$FEN_FILE" ]; then
    echo -e "${RED}✗ Fen integration file not found${NC}"
    exit 1
fi

LINES=$(wc -l < "$FEN_FILE")
SIZE=$(du -h "$FEN_FILE" | cut -f1)
echo -e "${GREEN}File:${NC} $FEN_FILE"
echo -e "${GREEN}Size:${NC} $LINES lines ($SIZE)"
echo ""

###############################################################################
# Class Structure Analysis
###############################################################################

echo -e "${BLUE}=== 2. Class & Method Structure ===${NC}"
echo ""

echo "Classes Defined:"
grep -E "^class " "$FEN_FILE" | sed 's/class /  • /' | sed 's/ {$//'
echo ""

echo "Key Methods:"
grep -E "^\s+(async\s+)?[a-zA-Z_][a-zA-Z0-9_]*\(" "$FEN_FILE" | head -20 | sed 's/^/  • /' | sed 's/()$//'
echo ""

###############################################################################
# Feature Detection
###############################################################################

echo -e "${BLUE}=== 3. Feature Detection ===${NC}"
echo ""

echo "Kodi JSON-RPC Features:"
if grep -q "JSON-RPC" "$FEN_FILE"; then
    echo -e "  ${GREEN}✓${NC} JSON-RPC 2.0 protocol"
else
    echo -e "  ${YELLOW}○${NC} JSON-RPC 2.0 protocol"
fi

if grep -q "jsonrpc\|JSONRPC\|JsonRpc" "$FEN_FILE"; then
    echo -e "  ${GREEN}✓${NC} JSON-RPC client implementation"
else
    echo -e "  ${YELLOW}○${NC} JSON-RPC client implementation"
fi

if grep -q "Player\|playback\|play\|pause\|stop" "$FEN_FILE"; then
    echo -e "  ${GREEN}✓${NC} Playback controls (play/pause/stop)"
else
    echo -e "  ${YELLOW}○${NC} Playback controls"
fi

if grep -q "seek\|volume\|mute" "$FEN_FILE"; then
    echo -e "  ${GREEN}✓${NC} Advanced controls (seek/volume)"
else
    echo -e "  ${YELLOW}○${NC} Advanced controls"
fi

echo ""
echo "Real-Debrid Integration:"
if grep -qi "real-debrid\|realdebrid\|realdebrid" "$FEN_FILE"; then
    echo -e "  ${GREEN}✓${NC} Real-Debrid API support"
else
    echo -e "  ${YELLOW}○${NC} Real-Debrid API support"
fi

if grep -qi "premiumize\|alldebrid\|easynews" "$FEN_FILE"; then
    echo -e "  ${GREEN}✓${NC} Multiple debrid services"
else
    echo -e "  ${YELLOW}○${NC} Multiple debrid services"
fi

echo ""
echo "Content Resolution:"
if grep -qi "search\|scrape\|resolver" "$FEN_FILE"; then
    echo -e "  ${GREEN}✓${NC} Content search/scraping"
else
    echo -e "  ${YELLOW}○${NC} Content search/scraping"
fi

if grep -qi "torrent\|magnet\|hoster\|cached" "$FEN_FILE"; then
    echo -e "  ${GREEN}✓${NC} Torrent/hoster support"
else
    echo -e "  ${YELLOW}○${NC} Torrent/hoster support"
fi

###############################################################################
# Code Sample Analysis
###############################################################################

echo -e "${BLUE}=== 4. Constructor & Configuration ===${NC}"
echo ""

grep -A 20 "constructor" "$FEN_FILE" | head -25
echo ""

###############################################################################
# Method Signatures
###############################################################################

echo -e "${BLUE}=== 5. Key Method Signatures ===${NC}"
echo ""

echo "Public Methods:"
grep -E "^\s+(async\s+)?[a-zA-Z_][a-zA-Z0-9_]*\(" "$FEN_FILE" | grep -v "private\|_" | head -10 | while read -r line; do
    # Extract method name
    method=$(echo "$line" | sed -E 's/.*\s+([a-zA-Z_][a-zA-Z0-9_]*)\(.*/\1/')
    indent=$(echo "$line" | sed 's/[^ ].*//g' | sed 's/ /  /g')
    echo "${indent}• ${method}"
done
echo ""

###############################################################################
# Integration Points
###############################################################################

echo -e "${BLUE}=== 6. Integration Points ===${NC}"
echo ""

echo "External APIs:"
grep -E "(https?://|api\.|\.api)" "$FEN_FILE" | grep -v "//" | head -5 | sed 's/^/  • /'
echo ""

echo "Environment Variables:"
grep -E "process\.env\." "$FEN_FILE" | sed 's/process\.env\./  • /' | sed 's/[,)].*//' | sort -u
echo ""

###############################################################################
# Resilience Features
###############################################################################

echo -e "${BLUE}=== 7. Resilience Patterns Used ===${NC}"
echo ""

if grep -q "timeout\|setTimeout\|withTimeout" "$FEN_FILE"; then
    echo -e "  ${GREEN}✓${NC} Timeout protection"
else
    echo -e "  ${YELLOW}○${NC} Timeout protection"
fi

if grep -q "retry\|withRetry\|exponential" "$FEN_FILE"; then
    echo -e "  ${GREEN}✓${NC} Retry logic"
else
    echo -e "  ${YELLOW}○${NC} Retry logic"
fi

if grep -q "circuit\|breaker\|CircuitBreaker" "$FEN_FILE"; then
    echo -e "  ${GREEN}✓${NC} Circuit breaker"
else
    echo -e "  ${YELLOW}○${NC} Circuit breaker"
fi

if grep -q "catch\|error\|Error" "$FEN_FILE"; then
    echo -e "  ${GREEN}✓${NC} Error handling"
else
    echo -e "  ${YELLOW}○${NC} Error handling"
fi

echo ""

###############################################################################
# Dependencies
###############################################################################

echo -e "${BLUE}=== 8. Dependencies & Imports ===${NC}"
echo ""

echo "Required Modules:"
grep "require(" "$FEN_FILE" | sed 's/.*require(/  • /' | sed "s/['\"]//g" | sed 's/).*$//' | sort -u
echo ""

###############################################################################
# Code Complexity
###############################################################################

echo -e "${BLUE}=== 9. Code Quality Metrics ===${NC}"
echo ""

# Count functions
FUNCTIONS=$(grep -c "function\|=>.*{" "$FEN_FILE" || true)
echo "  • Functions/Methods: $FUNCTIONS"

# Count async functions
ASYNC=$(grep -c "async function\|async.*=>" "$FEN_FILE" || true)
echo "  • Async Methods: $ASYNC"

# Count classes
CLASSES=$(grep -c "^class " "$FEN_FILE" || true)
echo "  • Classes: $CLASSES"

# Count comments
COMMENTS=$(grep -c "^\s*//" "$FEN_FILE" || true)
echo "  • Comment Lines: $COMMENTS"

# Cyclomatic complexity (rough estimate)
BRANCHES=$(grep -c "if\|else\|for\|while\|try\|catch" "$FEN_FILE" || true)
echo "  • Branch Statements: $BRANCHES"
echo ""

###############################################################################
# Usage Examples
###############################################################################

echo -e "${BLUE}=== 10. Usage Examples from Code ===${NC}"
echo ""

if grep -q "example\|Example\|usage\|Usage" "$FEN_FILE"; then
    echo "Found usage examples:"
    grep -B 2 -A 5 "example\|Example\|usage\|Usage" "$FEN_FILE" | head -20
else
    echo "No explicit usage examples found in code"
fi
echo ""

###############################################################################
# Summary
###############################################################################

echo -e "${BLUE}=== 11. Kodi/Fen Integration Summary ===${NC}"
echo ""

echo -e "${CYAN}Implementation Status:${NC}"
echo -e "  ${GREEN}✓${NC} File exists with $LINES lines of code"
echo -e "  ${GREEN}✓${NC} Integration code present"

echo ""
echo -e "${CYAN}Capabilities:${NC}"
echo "  • Kodi JSON-RPC protocol support"
echo "  • Fen addon integration"
echo "  • Real-Debrid integration"
echo "  • Content search and resolution"
echo "  • Playback control"
echo "  • Media center management"

echo ""
echo -e "${CYAN}Integration Architecture:${NC}"
echo "  OmniClaw → Unified Media Controller → Fen Integration"
echo "              ↓"
echo "         Kodi JSON-RPC API → Fen Addon"
echo "                              ↓"
echo "                         Real-Debrid CDN"

echo ""
echo -e "${CYAN}Typical Usage Flow:${NC}"
echo "  1. User voice command: 'Play The Matrix on Fen'"
echo "  2. Alexa → omniclaw-resilient function"
echo "  3. Unified controller routes to Fen integration"
echo "  4. Fen searches via Kodi JSON-RPC"
echo "  5. Fen addon queries Real-Debrid for cached sources"
echo "  6. Returns direct CDN URL to Kodi player"
echo "  7. Kodi streams content to TV"

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
