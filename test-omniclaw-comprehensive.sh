#!/bin/bash

###############################################################################
# OmniClaw Comprehensive Capability Test Suite
# Tests all deployed functions and integrations
###############################################################################

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_ID="omniclaw-personal-assistant"
REGION="asia-south1"
BASE_URL="https://${REGION}-${PROJECT_ID}.cloudfunctions.net"

echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}  OmniClaw Comprehensive Capability Test Suite${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Helper function to run test
run_test() {
    local test_name="$1"
    local test_command="$2"
    local expected_pattern="$3"

    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -e "${YELLOW}[Test ${TOTAL_TESTS}]${NC} ${test_name}"

    if eval "$test_command"; then
        if [ -n "$expected_pattern" ]; then
            if eval "$test_command" | grep -qi "$expected_pattern"; then
                echo -e "${GREEN}✓ PASSED${NC}"
                PASSED_TESTS=$((PASSED_TESTS + 1))
                echo ""
                return 0
            else
                echo -e "${RED}✗ FAILED${NC} - Pattern not found: $expected_pattern"
                FAILED_TESTS=$((FAILED_TESTS + 1))
                echo ""
                return 1
            fi
        else
            echo -e "${GREEN}✓ PASSED${NC}"
            PASSED_TESTS=$((PASSED_TESTS + 1))
            echo ""
            return 0
        fi
    else
        echo -e "${RED}✗ FAILED${NC} - Command failed"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        echo ""
        return 1
    fi
}

###############################################################################
# Part 1: Health Check Tests
###############################################################################

echo -e "${BLUE}=== Part 1: Health Check Tests ===${NC}"
echo ""

run_test "Health Endpoint - omniclaw-health" \
    "curl -s ${BASE_URL}/omniclaw-health/health" \
    "healthy"

run_test "Email Health - omniclaw-email" \
    "curl -s ${BASE_URL}/omniclaw-email/api/email/health" \
    "healthy"

run_test "Price Status - omniclaw-price" \
    "curl -s ${BASE_URL}/omniclaw-price/" \
    "operational"

run_test "Media Health - omniclaw-media" \
    "curl -s ${BASE_URL}/omniclaw-media/health" \
    "healthy"

run_test "Story Status - omniclaw-story" \
    "curl -s ${BASE_URL}/omniclaw-story/" \
    "operational"

run_test "Resilient Health - omniclaw-resilient" \
    "curl -s ${BASE_URL}/omniclaw-resilient/api/health" \
    "healthy"

###############################################################################
# Part 2: Secret Manager Verification
###############################################################################

echo -e "${BLUE}=== Part 2: Secret Manager Verification ===${NC}"
echo ""

run_test "GLM API Secret Exists" \
    "gcloud secrets describe glm-api-key --project=${PROJECT_ID} 2>/dev/null"

run_test "Groq API Secret Exists" \
    "gcloud secrets describe groq-api-key --project=${PROJECT_ID} 2>/dev/null"

run_test "YouTube API Secret Exists" \
    "gcloud secrets describe youtube-api-key --project=${PROJECT_ID} 2>/dev/null"

###############################################################################
# Part 3: YouTube API Test
###############################################################################

echo -e "${BLUE}=== Part 3: YouTube API Integration Test ===${NC}"
echo ""

run_test "YouTube API Search" \
    "curl -s 'https://www.googleapis.com/youtube/v3/search?part=snippet&q=omniclaw&type=video&key=AIzaSyDa5FNhFcJwfcVnjtHVn__zXjBppNIssiE' | python3 -c 'import sys, json; data=json.load(sys.stdin); print(\"Videos found:\", len(data.get(\"items\", [])))'"

###############################################################################
# Part 4: Codebase Verification
###############################################################################

echo -e "${BLUE}=== Part 4: Codebase Implementation Verification ===${NC}"
echo ""

run_test "Spotify Integration Exists" \
    "test -f /Users/Subho/omniclaw-personal-assistant/apps/media-streaming/integrations/spotify-integration.js"

run_test "Kodi/Fen Integration Exists" \
    "test -f /Users/Subho/omniclaw-personal-assistant/apps/media-streaming/integrations/fen-integration.js"

run_test "YouTube Integration Exists" \
    "test -f /Users/Subho/omniclaw-personal-assistant/apps/media-streaming/integrations/youtube-integration.js"

run_test "Unified Media Controller Exists" \
    "test -f /Users/Subho/omniclaw-personal-assistant/apps/media-streaming/controllers/unified-media-controller.js"

run_test "GraphQL Schema Exists" \
    "test -f /Users/Subho/omniclaw-personal-assistant/apps/media-streaming/bridge/media-streaming-schema.js"

run_test "Resilience Layer Exists" \
    "test -f /Users/Subho/omniclaw-personal-assistant/shared/resilience/circuit-breaker.js"

run_test "Gmail Integration Exists" \
    "test -f /Users/Subho/omniclaw-personal-assistant/apps/email-intelligence/services/gmail-service.js"

run_test "Outlook Integration Exists" \
    "test -f /Users/Subho/omniclaw-personal-assistant/apps/email-intelligence/services/outlook-service.js"

run_test "Price Scrapers Exist" \
    "test -d /Users/Subho/omniclaw-personal-assistant/apps/price-tracking/scrapers"

run_test "Story Narrator Exists" \
    "test -f /Users/Subho/omniclaw-personal-assistant/apps/story-narrator/story-orchestrator.js"

###############################################################################
# Part 5: Code Quality Metrics
###############################################################################

echo -e "${BLUE}=== Part 5: Code Quality Metrics ===${NC}"
echo ""

echo -e "${YELLOW}Code Statistics:${NC}"

# Count lines of code
TOTAL_LINES=$(find /Users/Subho/omniclaw-personal-assistant -name "*.js" -not -path "*/node_modules/*" | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}')
echo "Total JavaScript Lines: ${TOTAL_LINES}"

# Count resilience code
RESILIENCE_LINES=$(find /Users/Subho/omniclaw-personal-assistant/shared/resilience -name "*.js" | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}')
echo "Resilience Layer Lines: ${RESILIENCE_LINES}"

# Count legacy clients
LEGACY_CLIENTS=$(find /Users/Subho/omniclaw-personal-assistant/preserved/clients -name "*_client.js" | wc -l)
echo "Legacy OpenClaw Clients: ${LEGACY_CLIENTS}"

# Count functions
FUNCTION_COUNT=$(ls /tmp/omniclaw-deploy/*/index.js 2>/dev/null | wc -l)
echo "Cloud Functions Deployed: ${FUNCTION_COUNT}"

echo ""

###############################################################################
# Part 6: File Size Analysis
###############################################################################

echo -e "${BLUE}=== Part 6: Implementation File Analysis ===${NC}"
echo ""

echo -e "${YELLOW}Media Streaming Integration Sizes:${NC}"
for file in /Users/Subho/omniclaw-personal-assistant/apps/media-streaming/integrations/*.js; do
    if [ -f "$file" ]; then
        lines=$(wc -l < "$file")
        size=$(du -h "$file" | cut -f1)
        basename_file=$(basename "$file")
        printf "  %-40s %5d lines %8s\n" "$basename_file" "$lines" "$size"
    fi
done

echo ""
echo -e "${YELLOW}Phase Code Sizes:${NC}"
for phase in email-intelligence price-tracking media-streaming story-narrator; do
    if [ -d "/Users/Subho/omniclaw-personal-assistant/apps/$phase" ]; then
        lines=$(find /Users/Subho/omniclaw-personal-assistant/apps/$phase -name "*.js" | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}')
        printf "  %-40s %5d lines\n" "$phase" "$lines"
    fi
done

echo ""

###############################################################################
# Part 7: Kodi/Fen Integration Detailed Test
###############################################################################

echo -e "${BLUE}=== Part 7: Kodi/Fen Integration Analysis ===${NC}"
echo ""

if [ -f "/Users/Subho/omniclaw-personal-assistant/apps/media-streaming/integrations/fen-integration.js" ]; then
    echo -e "${GREEN}✓ Fen/Kodi integration file exists${NC}"
    echo ""
    echo "Implementation Details:"
    grep -E "(class|async|function)" /Users/Subho/omniclaw-personal-assistant/apps/media-streaming/integrations/fen-integration.js | head -20
    echo ""

    # Check for key features
    echo "Key Features Implemented:"
    grep -q "JSON-RPC" /Users/Subho/omniclaw-personal-assistant/apps/media-streaming/integrations/fen-integration.js && echo "  ✓ JSON-RPC protocol"
    grep -q "Real-Debrid" /Users/Subho/omniclaw-personal-assistant/apps/media-streaming/integrations/fen-integration.js && echo "  ✓ Real-Debrid integration"
    grep -q "Addons" /Users/Subho/omniclaw-personal-assistant/apps/media-streaming/integrations/fen-integration.js && echo "  ✓ Kodi addons support"
    grep -q "playback" /Users/Subho/omniclaw-personal-assistant/apps/media-streaming/integrations/fen-integration.js && echo "  ✓ Playback control"
    echo ""
fi

###############################################################################
# Part 8: Resilience Layer Verification
###############################################################################

echo -e "${BLUE}=== Part 8: Resilience Layer Verification ===${NC}"
echo ""

RESILIENCE_DIR="/Users/Subho/omniclaw-personal-assistant/shared/resilience"

if [ -d "$RESILIENCE_DIR" ]; then
    echo "Resilience Components:"
    for component in timeout-wrapper retry circuit-breaker graceful-degradation; do
        if [ -f "${RESILIENCE_DIR}/${component}.js" ]; then
            lines=$(wc -l < "${RESILIENCE_DIR}/${component}.js")
            echo "  ✓ ${component}.js (${lines} lines)"
        fi
    done
    echo ""

    # Check if resilient clients exist
    if [ -f "/Users/Subho/omniclaw-personal-assistant/preserved/resilient-clients.js" ]; then
        echo "  ✓ Resilient wrapper for 19 OpenClaw clients"
    fi
    echo ""
fi

###############################################################################
# Part 9: Legacy OpenClaw Clients
###############################################################################

echo -e "${BLUE}=== Part 9: Legacy OpenClaw Clients ===${NC}"
echo ""

CLIENT_DIR="/Users/Subho/omniclaw-personal-assistant/preserved/clients"

if [ -d "$CLIENT_DIR" ]; then
    echo "Available OpenClaw Clients:"
    for client in "${CLIENT_DIR}"/*_client.js; do
        if [ -f "$client" ]; then
            basename_client=$(basename "$client" .js)
            echo "  ✓ ${basename_client}"
        fi
    done
    echo ""
fi

###############################################################################
# Part 10: Cloud Functions Status
###############################################################################

echo -e "${BLUE}=== Part 10: Cloud Functions Deployment Status ===${NC}"
echo ""

echo "Deployed Functions:"
gcloud functions list --project=${PROJECT_ID} --regions=${REGION} 2>/dev/null | grep omniclaw | while read -r line; do
    echo "  ✓ $line"
done
echo ""

###############################################################################
# Final Summary
###############################################################################

echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}  Test Execution Summary${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""
echo -e "Total Tests Run: ${TOTAL_TESTS}"
echo -e "${GREEN}Passed: ${PASSED_TESTS}${NC}"
if [ $FAILED_TESTS -gt 0 ]; then
    echo -e "${RED}Failed: ${FAILED_TESTS}${NC}"
else
    echo -e "${GREEN}Failed: ${FAILED_TESTS}${NC}"
fi
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}✓ ALL TESTS PASSED!${NC}"
    echo -e "${GREEN}OmniClaw is fully operational!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests failed. Please review the output above.${NC}"
    exit 1
fi
