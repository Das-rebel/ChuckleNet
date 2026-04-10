#!/bin/bash

###############################################################################
# OmniClaw Deployment Testing Script
# Tests all deployed Cloud Functions endpoints
###############################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-omniclaw-personal-assistant}"
REGION="${GOOGLE_CLOUD_REGION:-asia-south1}"

# Function URLs (will be retrieved dynamically)
OMNICLAW_URL=""
EMAIL_URL=""
PRICE_URL=""
MEDIA_URL=""
STORY_URL=""

echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}  OmniClaw Deployment Testing${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""

# Function to get function URL
get_function_url() {
    local name=$1
    gcloud functions describe "$name" \
        --region="$REGION" \
        --format="value(serviceConfig.uri)" \
        --project="$PROJECT_ID" 2>/dev/null || echo ""
}

# Function to test endpoint
test_endpoint() {
    local name=$1
    local url=$2
    local path=$3

    echo -e "${YELLOW}Testing $name...${NC}"

    if [ -z "$url" ]; then
        echo -e "${RED}✗ $name: No URL found (not deployed)${NC}"
        return 1
    fi

    local full_url="${url}${path}"

    if curl -s -f "$full_url" > /dev/null 2>&1; then
        local response=$(curl -s "$full_url")
        echo -e "${GREEN}✓ $name: Healthy${NC}"
        echo -e "${BLUE}  URL: $full_url${NC}"

        # Pretty print JSON if response is JSON
        if echo "$response" | jq -e . > /dev/null 2>&1; then
            echo -e "${BLUE}  Response:${NC}"
            echo "$response" | jq -r 'to_entries | .[] | "    \(.key): \(.value)"' 2>/dev/null || echo "    $response"
        fi
        echo ""
        return 0
    else
        echo -e "${RED}✗ $name: Failed${NC}"
        echo -e "${BLUE}  URL: $full_url${NC}"
        echo ""
        return 1
    fi
}

# Get all function URLs
echo -e "${YELLOW}Retrieving deployed function URLs...${NC}"
echo ""

OMNICLAW_URL=$(get_function_url "omniclaw-resilient")
EMAIL_URL=$(get_function_url "omniclaw-email")
PRICE_URL=$(get_function_url "omniclaw-price")
MEDIA_URL=$(get_function_url "omniclaw-media")
STORY_URL=$(get_function_url "omniclaw-story")

# Count deployments
DEPLOYED_COUNT=0
[ -n "$OMNICLAW_URL" ] && ((DEPLOYED_COUNT++)) || true
[ -n "$EMAIL_URL" ] && ((DEPLOYED_COUNT++)) || true
[ -n "$PRICE_URL" ] && ((DEPLOYED_COUNT++)) || true
[ -n "$MEDIA_URL" ] && ((DEPLOYED_COUNT++)) || true
[ -n "$STORY_URL" ] && ((DEPLOYED_COUNT++)) || true

echo -e "${GREEN}Found $DEPLOYED_COUNT/5 deployed functions${NC}"
echo ""

# Test each endpoint
echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}  Testing Health Endpoints${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""

PASS_COUNT=0
FAIL_COUNT=0

# Test Base OpenClaw
if test_endpoint "Base OpenClaw" "$OMNICLAW_URL" "/api/health"; then
    ((PASS_COUNT++))
else
    ((FAIL_COUNT++))
fi

# Test Email Intelligence
if test_endpoint "Email Intelligence" "$EMAIL_URL" "/api/email/health"; then
    ((PASS_COUNT++))
else
    ((FAIL_COUNT++))
fi

# Test Price Tracking
if test_endpoint "Price Tracking" "$PRICE_URL" "/"; then
    ((PASS_COUNT++))
else
    ((FAIL_COUNT++))
fi

# Test Media Streaming
if test_endpoint "Media Streaming" "$MEDIA_URL" "/health"; then
    ((PASS_COUNT++))
else
    ((FAIL_COUNT++))
fi

# Test Story Narrator
if test_endpoint "Story Narrator" "$STORY_URL" "/"; then
    ((PASS_COUNT++))
else
    ((FAIL_COUNT++))
fi

# ============================================================================
# Test Summary
# ============================================================================
echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}  Test Summary${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""
echo -e "Deployed Functions: ${GREEN}$DEPLOYED_COUNT${NC}/5"
echo -e "Health Checks:      ${GREEN}$PASS_COUNT${NC}/5 passed"

if [ $FAIL_COUNT -gt 0 ]; then
    echo -e "                   ${RED}$FAIL_COUNT${NC}/5 failed"
fi

echo ""

if [ $DEPLOYED_COUNT -eq 5 ] && [ $PASS_COUNT -eq 5 ]; then
    echo -e "${GREEN}✓ All systems operational!${NC}"
    echo ""
    echo -e "${YELLOW}Next Steps:${NC}"
    echo -e "  1. Configure API keys in Secret Manager"
    echo -e "  2. Test actual functionality with API calls"
    echo -e "  3. Update Alexa skill endpoints"
    echo -e "  4. Monitor circuit breaker states"
    exit 0
elif [ $DEPLOYED_COUNT -eq 0 ]; then
    echo -e "${RED}✗ No functions deployed. Run deployment script first.${NC}"
    exit 1
else
    echo -e "${YELLOW}⚠ Some functions not ready${NC}"
    echo ""
    echo -e "${YELLOW}Recommendations:${NC}"
    if [ $FAIL_COUNT -gt 0 ]; then
        echo -e "  - Check Cloud Functions logs for errors"
        echo -e "  - Verify deployment completed successfully"
        echo -e "  - Ensure all dependencies are installed"
    fi
    if [ $DEPLOYED_COUNT -lt 5 ]; then
        echo -e "  - Run deployment script to deploy missing functions"
    fi
    exit 1
fi
