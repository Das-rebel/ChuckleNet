#!/bin/bash

echo "Testing different Alexa endpoints..."

echo "1. Testing the deployed enhanced service:"
curl -X POST https://helloworld-fqm3wms5ka-uc.a.run.app/alexa \
  -H "Content-Type: application/json" \
  -d '{
    "version": "1.0",
    "session": {
      "sessionId": "test-session-final",
      "application": {
        "applicationId": "amzn1.ask.skill.6661bfdf-5d3f-4ae3-9102-8721685720a3"
      },
      "user": {
        "userId": "test-user"
      },
      "new": true
    },
    "request": {
      "type": "IntentRequest",
      "requestId": "test-request-final",
      "timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'",
      "locale": "en-IN-hinglish",
      "intent": {
        "name": "QueryIntent",
        "slots": {
          "Query": {
            "value": "kya technology news hai aaj"
          }
        }
      }
    }
  }' | jq '.response.outputSpeech.text'

echo ""
echo "2. Testing direct health check:"
curl -s https://helloworld-fqm3wms5ka-uc.a.run.app/health | jq .

