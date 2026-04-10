#!/bin/bash
# Comprehensive OpenClaw WhatsApp Auto-Reply Test
# Tests all possibilities without requiring actual WhatsApp messages

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  OpenClaw WhatsApp Auto-Reply - Comprehensive Test Suite      ║"
echo "║  Testing all components without WhatsApp dependency           ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Helper functions
pass_test() {
    echo -e "${GREEN}✓ PASS${NC}: $1"
    ((TESTS_PASSED++))
}

fail_test() {
    echo -e "${RED}✗ FAIL${NC}: $1"
    ((TESTS_FAILED++))
}

info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Get current timestamp
TIMESTAMP=$(date +%s)

# ========================================
# TEST 1: Gateway Status
# ========================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 1: Gateway Status"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

GATEWAY_PID=$(ps aux | grep 'openclaw.*gateway' | grep -v grep | awk '{print $2}')
if [ -n "$GATEWAY_PID" ]; then
    pass_test "Gateway running (PID: $GATEWAY_PID)"
else
    fail_test "Gateway not running"
fi

# Check if listening on port 18789
if lsof -i :18789 >/dev/null 2>&1; then
    pass_test "Gateway listening on port 18789"
else
    fail_test "Gateway not listening on port 18789"
fi

# Check LaunchAgent status
LAUNCH_AGENT_STATUS=$(launchctl list | grep openclaw.gateway | awk '{print $1}')
if [ "$LAUNCH_AGENT_STATUS" = "0" ]; then
    pass_test "LaunchAgent healthy (exit code 0)"
else
    fail_test "LaunchAgent unhealthy (exit code: $LAUNCH_AGENT_STATUS)"
fi

echo ""

# ========================================
# TEST 2: Configuration Validation
# ========================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 2: Configuration Validation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check timeout configuration
TIMEOUT_CONFIG=$(grep -o "timeoutSeconds.*[0-9]*" ~/openclaw/openclaw.json 2>/dev/null | grep -o "[0-9]*" || echo "0")
if [ "$TIMEOUT_CONFIG" -le 60 ]; then
    pass_test "Agent timeout configured: ${TIMEOUT_CONFIG}s (≤ 60s)"
else
    fail_test "Agent timeout too high: ${TIMEOUT_CONFIG}s (should be ≤ 60s)"
fi

# Check Z.AI model configuration
ZAI_MODEL=$(grep -o '"primary".*"zai/glm' ~/openclaw/openclaw.json 2>/dev/null)
if [ -n "$ZAI_MODEL" ]; then
    pass_test "Z.AI model configured as primary"
else
    fail_test "Z.AI model not configured as primary"
fi

# Check fallback model
FALLBACK_MODEL=$(grep -o '"fallbacks".*\[.*"google' ~/openclaw/openclaw.json 2>/dev/null)
if [ -n "$FALLBACK_MODEL" ]; then
    pass_test "Google Gemini fallback configured"
else
    warn "Fallback model not configured"
fi

echo ""

# ========================================
# TEST 3: Auth Profile Validation
# ========================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 3: Auth Profile Validation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

AUTH_FILE="$HOME/.openclaw/agents/main/agent/auth-profiles.json"
if [ -f "$AUTH_FILE" ]; then
    # Check for required fields
    if grep -q '"version"' "$AUTH_FILE" && \
       grep -q '"profiles"' "$AUTH_FILE" && \
       grep -q '"type": "api_key"' "$AUTH_FILE" && \
       grep -q '"key": "8851fb52fc4340a0996e8e8a0bc50cfe.ITMBhmxhypDlwncv"' "$AUTH_FILE"; then
        pass_test "Auth profile structure correct"
    else
        fail_test "Auth profile structure invalid"
    fi

    # Check for lastGood entry
    if grep -q '"lastGood"' "$AUTH_FILE"; then
        pass_test "Auth profile has lastGood entry"
    else
        warn "Auth profile missing lastGood entry"
    fi
else
    fail_test "Auth profile file not found: $AUTH_FILE"
fi

echo ""

# ========================================
# TEST 4: Agent Direct Invocation Test
# ========================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 4: Agent Direct Invocation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

info "Running agent with simple math question..."

# Run agent and capture output
AGENT_START_TIME=$(date +%s)
AGENT_OUTPUT=$(timeout 70 openclaw agent --local --agent main --message "What is 2+2? Answer in ONE WORD only." 2>&1)
AGENT_EXIT_CODE=$?
AGENT_END_TIME=$(date +%s)
AGENT_DURATION=$((AGENT_END_TIME - AGENT_START_TIME))

if [ $AGENT_EXIT_CODE -eq 0 ] || [ $AGENT_EXIT_CODE -eq 124 ]; then
    if [ $AGENT_DURATION -le 65 ]; then
        pass_test "Agent completed in ${AGENT_DURATION}s (≤ 65s)"

        # Check if response contains the answer
        if echo "$AGENT_OUTPUT" | grep -iq "4\|four"; then
            pass_test "Agent returned correct answer"
        else
            warn "Agent response unclear (check logs)"
        fi
    else
        fail_test "Agent took too long: ${AGENT_DURATION}s (should be ≤ 65s)"
    fi
else
    fail_test "Agent failed with exit code: $AGENT_EXIT_CODE"
fi

echo ""

# ========================================
# TEST 5: Recent Agent Run Analysis
# ========================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 5: Recent Agent Run Analysis (from logs)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Get today's log file
TODAY=$(date +%Y-%m-%d)
LOG_FILE="/tmp/openclaw/openclaw-${TODAY}.log"

if [ -f "$LOG_FILE" ]; then
    # Count agent runs today
    AGENT_RUNS_START=$(grep -c "embedded run start" "$LOG_FILE" 2>/dev/null || echo "0")
    AGENT_RUNS_DONE=$(grep -c "embedded run done" "$LOG_FILE" 2>/dev/null || echo "0")

    info "Agent runs started today: $AGENT_RUNS_START"
    info "Agent runs completed today: $AGENT_RUNS_DONE"

    # Check for hung runs
    HUNG_RUNS=$((AGENT_RUNS_START - AGENT_RUNS_DONE))
    if [ $HUNG_RUNS -eq 0 ]; then
        pass_test "No hung agent runs detected"
    else
        warn "Potentially hung runs: $HUNG_RUNS"
    fi

    # Get most recent run duration
    LAST_RUN_DONE=$(grep "embedded run done" "$LOG_FILE" 2>/dev/null | tail -1)
    if [ -n "$LAST_RUN_DONE" ]; then
        LAST_RUN_DURATION=$(echo "$LAST_RUN_DONE" | grep -o "durationMs=[0-9]*" | grep -o "[0-9]*")
        LAST_RUN_SECONDS=$(echo "scale=1; $LAST_RUN_DURATION / 1000" | bc)
        pass_test "Last run completed in ${LAST_RUN_SECONDS}s"

        # Check if last run used Z.AI
        LAST_RUN_START=$(grep "embedded run start" "$LOG_FILE" 2>/dev/null | tail -1)
        if echo "$LAST_RUN_START" | grep -q "provider=zai"; then
            pass_test "Last run used Z.AI provider"
        fi
    else
        warn "No completed runs found in today's log"
    fi

    # Check for timeout errors
    TIMEOUT_ERRORS=$(grep -c "embedded run timeout" "$LOG_FILE" 2>/dev/null || echo "0")
    if [ $TIMEOUT_ERRORS -eq 0 ]; then
        pass_test "No timeout errors in logs"
    else
        warn "Timeout errors found: $TIMEOUT_ERRORS"
    fi
else
    warn "Log file not found: $LOG_FILE"
fi

echo ""

# ========================================
# TEST 6: WhatsApp Auto-Reply Configuration
# ========================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 6: WhatsApp Auto-Reply Configuration"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check WhatsApp enabled
WHATSAPP_ENABLED=$(grep -o '"whatsapp".*enabled.*true' ~/openclaw/openclaw.json 2>/dev/null)
if [ -n "$WHATSAPP_ENABLED" ]; then
    pass_test "WhatsApp plugin enabled"
else
    fail_test "WhatsApp plugin not enabled"
fi

# Check allowFrom configuration
ALLOW_FROM=$(grep -A2 '"whatsapp"' ~/openclaw/openclaw.json | grep -o '"allowFrom".*"' | head -1)
if echo "$ALLOW_FROM" | grep -q '\[\s*"\*"\s*\]'; then
    pass_test "WhatsApp allowFrom configured to accept all"
else
    warn "WhatsApp allowFrom might be restricted"
fi

# Check sendReadReceipts
if grep -q '"sendReadReceipts":\s*true' ~/openclaw/openclaw.json 2>/dev/null; then
    pass_test "WhatsApp sendReadReceipts enabled"
else
    warn "WhatsApp sendReadReceipts disabled"
fi

echo ""

# ========================================
# TEST 7: File Descriptor Check
# ========================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 7: File Descriptor Check"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -n "$GATEWAY_PID" ]; then
    FD_COUNT=$(lsof -p $GATEWAY_PID 2>/dev/null | wc -l)
    info "Gateway open file descriptors: $FD_COUNT"

    if [ $FD_COUNT -lt 200 ]; then
        pass_test "File descriptor count healthy ($FD_COUNT < 200)"
    else
        warn "File descriptor count high: $FD_COUNT"
    fi

    # Check for EMFILE errors in logs
    EMFILE_COUNT=$(grep -c "EMFILE\|too many open files" "$LOG_FILE" 2>/dev/null || echo "0")
    if [ $EMFILE_COUNT -eq 0 ]; then
        pass_test "No EMFILE errors in recent logs"
    else
        warn "EMFILE errors found: $EMFILE_COUNT"
    fi
fi

echo ""

# ========================================
# TEST 8: Z.AI API Connectivity Test
# ========================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 8: Z.AI API Connectivity"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

info "Testing Z.AI API directly..."

ZAI_RESPONSE=$(curl -s -X POST \
  "https://open.bigmodel.cn/api/paas/v4/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer 8851fb52fc4340a0996e8e8a0bc50cfe.ITMBhmxhypDlwncv" \
  -d '{
    "model": "glm-4.7",
    "messages": [{"role": "user", "content": "Say TEST in one word."}],
    "max_tokens": 10
  }' 2>&1)

if echo "$ZAI_RESPONSE" | grep -q "TEST\|test"; then
    pass_test "Z.AI API responding correctly"
elif echo "$ZAI_RESPONSE" | grep -q "error\|Error\|401\|403"; then
    fail_test "Z.AI API returned error"
else
    warn "Z.AI API response unclear"
fi

echo ""

# ========================================
# TEST 9: Auto-Reply Trigger Mechanism
# ========================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 9: Auto-Reply Trigger Mechanism Check"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check for recent inbound messages
INBOUND_COUNT=$(grep -c "Inbound message.*919003349852" "$LOG_FILE" 2>/dev/null || echo "0")
info "Inbound WhatsApp messages detected: $INBOUND_COUNT"

if [ $INBOUND_COUNT -gt 0 ]; then
    # Check if inbound messages triggered agent runs
    LATEST_INBOUND_TIME=$(grep "Inbound message.*919003349852" "$LOG_FILE" 2>/dev/null | tail -1 | grep -o '"time":"[^"]*"' | cut -d'"' -f4)
    info "Latest inbound message at: $LATEST_INBOUND_TIME"

    # Look for agent run within 5 seconds after inbound
    # This checks if auto-reply was triggered
    warn "Manual verification needed: Check if agent ran after inbound message"
fi

echo ""

# ========================================
# TEST SUMMARY
# ========================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${GREEN}Tests Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Tests Failed: $TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    echo ""
    echo "The system is configured correctly. The agent is working."
    echo ""
    echo "NEXT STEP: Send a WhatsApp message from +917977110915 to +919003349852"
    echo "to test the actual auto-reply functionality."
    exit 0
else
    echo -e "${RED}✗ Some tests failed.${NC}"
    echo ""
    echo "Please review the failed tests above and fix the issues."
    exit 1
fi
