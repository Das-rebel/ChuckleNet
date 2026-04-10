#!/bin/bash

###############################################################################
# OmniClaw Deployment Monitor
# Real-time deployment status monitoring
###############################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

PROJECT_ID="omniclaw-personal-assistant"
REGION="asia-south1"

echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}  OmniClaw Deployment Monitor${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""

# Function list
FUNCTIONS=(
  "omniclaw-health"
  "omniclaw-resilient"
  "omniclaw-email"
  "omniclaw-price"
  "omniclaw-media"
  "omniclaw-story"
)

# Function to get function status
get_function_status() {
    local name=$1
    local status=$(gcloud functions describe "$name" \
        --region="$REGION" \
        --format="value(state)" \
        --project="$PROJECT_ID" 2>/dev/null || echo "NOT_DEPLOYED")

    echo "$status"
}

# Function to get function URL
get_function_url() {
    local name=$1
    local url=$(gcloud functions describe "$name" \
        --region="$REGION" \
        --format="value(serviceConfig.uri)" \
        --project="$PROJECT_ID" 2>/dev/null || echo "")

    echo "$url"
}

# Function to test health endpoint
test_health() {
    local name=$1
    local url=$2
    local path=$3

    if [ -z "$url" ]; then
        echo -e "${RED}✗${NC} No URL"
        return 1
    fi

    local full_url="${url}${path}"
    if curl -s -f "$full_url" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Healthy"
        return 0
    else
        echo -e "${YELLOW}⚠${NC} Not responding"
        return 1
    fi
}

# Monitor loop
iteration=0
max_iterations=60  # 10 minutes (60 * 10 seconds)

while [ $iteration -lt $max_iterations ]; do
    clear

    echo -e "${BLUE}============================================================================${NC}"
    echo -e "${BLUE}  Deployment Status - Check $((iteration + 1))/$max_iterations${NC}"
    echo -e "${BLUE}============================================================================${NC}"
    echo ""
    echo -e "${CYAN}Time: $(date '+%Y-%m-%d %H:%M:%S')${NC}"
    echo ""

    deployed_count=0
    active_count=0

    for func in "${FUNCTIONS[@]}"; do
        status=$(get_function_status "$func")
        url=$(get_function_url "$func")

        # Determine color and symbol
        case "$status" in
            "ACTIVE")
                color=$GREEN
                symbol="✓"
                ((active_count++))
                ((deployed_count++))
                ;;
            "DEPLOYING"|"DEPLOY_IN_PROGRESS")
                color=$YELLOW
                symbol="⏳"
                ((deployed_count++))
                ;;
            "FAILED")
                color=$RED
                symbol="✗"
                ;;
            "NOT_DEPLOYED")
                color=$YELLOW
                symbol="○"
                ;;
            *)
                color=$YELLOW
                symbol="?"
                ;;
        esac

        echo -e "${color}${symbol} ${func}${NC}"
        echo -e "   Status: ${color}${status}${NC}"

        if [ -n "$url" ]; then
            echo -e "   URL: ${url}"

            # Test health endpoint if active
            if [ "$status" = "ACTIVE" ]; then
                case "$func" in
                    omniclaw-health)
                        health=$(test_health "$func" "$url" "/health")
                        echo -e "   Health: $health"
                        ;;
                    omniclaw-resilient)
                        health=$(test_health "$func" "$url" "/api/health")
                        echo -e "   Health: $health"
                        ;;
                    omniclaw-email)
                        health=$(test_health "$func" "$url" "/api/email/health")
                        echo -e "   Health: $health"
                        ;;
                    omniclaw-media)
                        health=$(test_health "$func" "$url" "/health")
                        echo -e "   Health: $health"
                        ;;
                    *)
                        echo -e "   Health: ${GREEN}✓${NC} (endpoint active)"
                        ;;
                esac
            fi
        fi

        echo ""
    done

    # Summary
    echo -e "${BLUE}------------------------------------------------------------------------${NC}"
    echo -e "Deployed: ${GREEN}${deployed_count}${NC}/6"
    echo -e "Active:   ${GREEN}${active_count}${NC}/6"
    echo ""

    # Check if all done
    if [ $active_count -eq 6 ]; then
        echo -e "${GREEN}============================================================================${NC}"
        echo -e "${GREEN}  ✓ All Functions Deployed Successfully!${NC}"
        echo -e "${GREEN}============================================================================${NC}"
        echo ""

        # Show URLs
        echo -e "${CYAN}Function URLs:${NC}"
        for func in "${FUNCTIONS[@]}"; do
            url=$(get_function_url "$func")
            echo -e "  ${func}: ${url}"
        done
        echo ""

        echo -e "${GREEN}Deployment complete at: $(date)${NC}"
        exit 0
    fi

    # Wait before next check
    echo -e "${YELLOW}Waiting 10 seconds...${NC}"
    sleep 10
    ((iteration++))
done

# Timeout
echo -e "${RED}============================================================================${NC}"
echo -e "${RED}  Deployment Timeout${NC}"
echo -e "${RED}============================================================================${NC}"
echo ""
echo -e "Some functions did not deploy within the expected time."
echo -e "Check the Google Cloud Console for more details."
echo ""

exit 1
