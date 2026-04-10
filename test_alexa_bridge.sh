#!/bin/bash

echo "========================================================================"
echo "           COMPREHENSIVE ALEXA BRIDGE TEST SUITE"
echo "========================================================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
PASSED=0
FAILED=0

# Test function
test_query() {
    local test_name="$1"
    local query="$2"
    local expected_pattern="$3"

    echo "Testing: $test_name"
    echo "Query: $query"

    response=$(curl -s -X POST http://localhost:3000/alexa \
        -H "Content-Type: application/json" \
        -d "{
            \"request\": {
                \"type\": \"IntentRequest\",
                \"intent\": {\"name\": \"QueryIntent\", \"slots\": {\"query\": {\"value\": \"$query\"}}, \"requestId\": \"test_$RANDOM\"}
            },
            \"session\": {\"user\": {\"userId\": \"test_user\"}, \"sessionId\": \"test_session\"}
        }" 2>/dev/null)

    # Check if response contains expected content
    if echo "$response" | grep -q "$expected_pattern"; then
        echo -e "${GREEN}✓ PASSED${NC}"
        ((PASSED++))
    else
        echo -e "${RED}✗ FAILED${NC}"
        echo "Response: $response" | head -100
        ((FAILED++))
    fi
    echo ""
}

echo "========================================================================"
echo "                    STARTING TESTS"
echo "========================================================================"
echo ""

# Test 1: Health Check
echo "1. Health Check"
health=$(curl -s http://localhost:3000/health 2>/dev/null)
if echo "$health" | grep -q "running"; then
    echo -e "${GREEN}✓ Bridge is running${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ Bridge health check failed${NC}"
    ((FAILED++))
fi
echo ""

# Test 2: Elon Musk Twitter
test_query "Elon Musk Tweets" "what did elon musk tweet" "Elon"

# Test 3: Trending topics
test_query "Trending Topics" "what is trending" "trending"

# Test 4: General question
test_query "General Question" "what is the capital of France" "Paris"

# Test 5: How question
test_query "How Question" "how does photosynthesis work" "photosynthesis"

# Test 6: Search query
test_query "Search Query" "search for python tutorials" "Python"

# Test 7: WhatsApp intent
echo "Testing: WhatsApp Messaging"
response=$(curl -s -X POST http://localhost:3000/alexa \
    -H "Content-Type: application/json" \
    -d '{
        "request": {"type": "IntentRequest", "intent": {"name": "WhatsAppIntent", "slots": {"message": {"value": "send to 9876543210 saying Test"}}, "requestId": "test_whatsapp"},
        "session": {"user": {"userId": "test_user"}, "sessionId": "test_session"}
    }' 2>/dev/null)

if echo "$response" | grep -q "WhatsApp"; then
    echo -e "${GREEN}✓ PASSED${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ FAILED${NC}"
    echo "Response: $response" | head -100
    ((FAILED++))
fi
echo ""

# Test 8: Reddit search
test_query "Reddit Search" "search reddit for artificial intelligence" "reddit"

# Test 9: Latest news
test_query "Latest News" "what is the latest news" "news"

# Test 10: Check session stays open
echo "Testing: Multi-turn Session (shouldEndSession should be false)"
response=$(curl -s -X POST http://localhost:3000/alexa \
    -H "Content-Type: application/json" \
    -d '{
        "request": {"type": "IntentRequest", "intent": {"name": "QueryIntent", "slots": {"query": {"value": "hello"}}, "requestId": "test_session"},
        "session": {"user": {"userId": "test_user"}, "sessionId": "test_session"}
    }' 2>/dev/null)

if echo "$response" | grep -q '"shouldEndSession": false'; then
    echo -e "${GREEN}✓ PASSED - Session stays open for follow-up questions${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ FAILED - Session closing prematurely${NC}"
    echo "Response: $response" | head -100
    ((FAILED++))
fi
echo ""

echo "========================================================================"
echo "                      TEST RESULTS"
echo "========================================================================"
echo -e "${GREEN}PASSED: $PASSED${NC}"
echo -e "${RED}FAILED: $FAILED${NC}"
echo "TOTAL: $((PASSED + FAILED))"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ ALL TESTS PASSED!${NC}"
    echo "The Alexa bridge is fully functional!"
    exit 0
else
    echo -e "${RED}✗ SOME TESTS FAILED${NC}"
    echo "Please check the logs: /tmp/bridge_final_test.log"
    exit 1
fi
