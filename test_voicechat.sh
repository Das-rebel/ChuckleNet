#!/bin/bash

echo "🧪 Testing Alexa Bridge - Voice Chat Mode"
echo "=========================================="

# Test 1: Health check
echo ""
echo "Test 1: Health Check"
echo "--------------------"
curl -s http://localhost:3000/health | python3 -m json.tool

# Test 2: Stats endpoint
echo ""
echo "Test 2: Stats Endpoint"
echo "---------------------"
curl -s http://localhost:3000/stats | python3 -m json.tool

# Test 3: LaunchRequest
echo ""
echo "Test 3: LaunchRequest"
echo "--------------------"
curl -s -X POST http://localhost:3000/alexa \
  -H "Content-Type: application/json" \
  -d '{"request":{"type":"LaunchRequest"},"session":{"user":{"userId":"test-user"}}}' | python3 -m json.tool

# Test 4: IntentRequest - Simple question
echo ""
echo "Test 4: IntentRequest - What is OpenClaw?"
echo "-----------------------------------------"
curl -s -X POST http://localhost:3000/alexa \
  -H "Content-Type: application/json" \
  -d '{
    "request": {
      "type": "IntentRequest",
      "intent": {
        "name": "ChatIntent",
        "slots": {
          "query": {
            "value": "What is OpenClaw?"
          }
        }
      }
    },
    "session": {
      "user": {
        "userId": "test-user"
      }
    }
  }' | python3 -m json.tool

# Test 5: IntentRequest - Time query
echo ""
echo "Test 5: IntentRequest - What time is it?"
echo "----------------------------------------"
curl -s -X POST http://localhost:3000/alexa \
  -H "Content-Type: application/json" \
  -d '{
    "request": {
      "type": "IntentRequest",
      "intent": {
        "name": "ChatIntent",
        "slots": {
          "query": {
            "value": "What time is it?"
          }
        }
      }
    },
    "session": {
      "user": {
        "userId": "test-user"
      }
    }
  }' | python3 -m json.tool

# Test 6: StopIntent
echo ""
echo "Test 6: StopIntent"
echo "------------------"
curl -s -X POST http://localhost:3000/alexa \
  -H "Content-Type: application/json" \
  -d '{"request":{"type":"IntentRequest","intent":{"name":"AMAZON.StopIntent"}},"session":{"user":{"userId":"test-user"}}}' | python3 -m json.tool

echo ""
echo "✅ All tests completed!"
