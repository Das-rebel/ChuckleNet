#!/bin/bash
# MCP Integration Verification Script
# Tests all components of the MCP integration

echo "🔍 MCP Integration Verification"
echo "================================="
echo ""

PASS=0
FAIL=0

# Test 1: MCP Server Process
echo "Test 1: MCP Server Process"
if ps aux | grep -q "[m]cp-server"; then
    echo "✅ PASS: MCP Server is running"
    ((PASS++))
else
    echo "❌ FAIL: MCP Server not running"
    ((FAIL++))
fi
echo ""

# Test 2: MCP Server Port
echo "Test 2: MCP Server Port (18790)"
if lsof -i :18790 > /dev/null 2>&1; then
    echo "✅ PASS: MCP Server listening on port 18790"
    ((PASS++))
else
    echo "❌ FAIL: MCP Server not listening on port 18790"
    ((FAIL++))
fi
echo ""

# Test 3: MCP Server Files
echo "Test 3: MCP Server Files"
MCP_FILES=(
    "$HOME/.npm-global/lib/node_modules/openclaw/dist/mcp-server/index.js"
    "$HOME/.npm-global/lib/node_modules/openclaw/dist/mcp-server/server.js"
    "$HOME/.npm-global/lib/node_modules/openclaw/dist/mcp-server/bridge.js"
    "$HOME/.npm-global/lib/node_modules/openclaw/dist/mcp-server/tools/whatsapp.js"
    "$HOME/.npm-global/lib/node_modules/openclaw/dist/mcp-server/tools/telegram.js"
    "$HOME/.npm-global/lib/node_modules/openclaw/dist/mcp-server/tools/status.js"
)

ALL_FILES=true
for file in "${MCP_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $(basename $file)"
    else
        echo "  ❌ $(basename $file) - MISSING"
        ALL_FILES=false
    fi
done

if $ALL_FILES; then
    echo "✅ PASS: All MCP Server files present"
    ((PASS++))
else
    echo "❌ FAIL: Some MCP Server files missing"
    ((FAIL++))
fi
echo ""

# Test 4: Voice Server Files
echo "Test 4: Voice Server Integration Files"
VOICE_FILES=(
    "$HOME/projects/openclaw-voice-chat/server/mcp_client.py"
    "$HOME/projects/openclaw-voice-chat/server/tool_orchestrator.py"
)

ALL_VOICE_FILES=true
for file in "${VOICE_FILES[@]}"; do
    if [ -f "$file" ]; then
        SIZE=$(wc -l < "$file")
        echo "  ✅ $(basename $file) ($SIZE lines)"
    else
        echo "  ❌ $(basename $file) - MISSING"
        ALL_VOICE_FILES=false
    fi
done

if $ALL_VOICE_FILES; then
    echo "✅ PASS: All Voice Server integration files present"
    ((PASS++))
else
    echo "❌ FAIL: Some Voice Server files missing"
    ((FAIL++))
fi
echo ""

# Test 5: Voice Server Integration
echo "Test 5: Voice Server MCP Integration"
if grep -q "from tool_orchestrator import ToolOrchestrator" "$HOME/projects/openclaw-voice-chat/server/voice_server.py"; then
    echo "✅ PASS: Voice Server has MCP integration"
    ((PASS++))
else
    echo "❌ FAIL: Voice Server missing MCP integration"
    ((FAIL++))
fi
echo ""

# Test 6: MCP Server HTTP Endpoint
echo "Test 6: MCP Server HTTP Endpoint"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:18790/mcp || echo "000")
if [ "$HTTP_CODE" != "000" ]; then
    echo "✅ PASS: MCP Server HTTP endpoint responding (HTTP $HTTP_CODE)"
    ((PASS++))
else
    echo "❌ FAIL: MCP Server HTTP endpoint not responding"
    ((FAIL++))
fi
echo ""

# Test 7: Documentation
echo "Test 7: Documentation Files"
DOCS=(
    "$HOME/MCP_INTEGRATION_COMPLETE.md"
    "$HOME/.claude/plans/sleepy-sparking-sonnet.md"
    "$HOME/.openclaw/canvas/README.md"
)

DOCS_PRESENT=true
for doc in "${DOCS[@]}"; do
    if [ -f "$doc" ]; then
        echo "  ✅ $(basename $doc)"
    else
        echo "  ❌ $(basename $doc) - MISSING"
        DOCS_PRESENT=false
    fi
done

if $DOCS_PRESENT; then
    echo "✅ PASS: All documentation files present"
    ((PASS++))
else
    echo "❌ FAIL: Some documentation files missing"
    ((FAIL++))
fi
echo ""

# Summary
echo "================================="
echo "📊 Verification Summary"
echo "================================="
echo "✅ Passed: $PASS"
echo "❌ Failed: $FAIL"
echo "Total: $((PASS + FAIL)) tests"
echo ""

if [ $FAIL -eq 0 ]; then
    echo "🎉 All tests passed! MCP Integration is ready."
    echo ""
    echo "Next steps:"
    echo "  1. Start the voice server: ~/start-mcp-voice-system.sh"
    echo "  2. Open voice UI: http://127.0.0.1:18789/__openclaw__/canvas/voice.html"
    echo "  3. Try voice commands:"
    echo "     - 'Check channel status'"
    echo "     - 'Send WhatsApp message to +1234567890 saying hello'"
    echo "     - 'Send Telegram message to @username with test message'"
    exit 0
else
    echo "⚠️  Some tests failed. Please review and fix issues."
    exit 1
fi
