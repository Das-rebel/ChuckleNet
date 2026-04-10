#!/bin/bash

# Force deployment of updated service with health check fix

echo "🚀 Forcing deployment of updated service..."

# Build and deploy
gcloud run deploy qce-enhanced \
  --source . \
  --platform=managed \
  --region=us-central1 \
  --allow-unauthenticated \
  --timeout=600s \
  --set-env-vars="ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY,GOOGLE_API_KEY=$GOOGLE_API_KEY,PERPLEXITY_API_KEY=$PERPLEXITY_API_KEY,OPENAI_API_KEY=$OPENAI_API_KEY,CEREBRAS_API_KEY=$CEREBRAS_API_KEY,SARVAM_API_KEY=$SARVAM_API_KEY"

echo "✅ Deployment initiated. Waiting for completion..."

# Wait for deployment
sleep 30

echo "🔍 Checking deployment status..."
gcloud run services describe qce-enhanced --region=us-central1 --format="value(status.latestReadyRevisionName)"

echo "🧪 Testing POST health endpoint..."
curl -s -X POST https://qce-enhanced-493290865097.us-central1.run.app/health \
  -H "Content-Type: application/json" \
  -H "User-Agent: Amazon-Alexa-Health-Check/1.0" \
  -d '{"test":"health"}'

echo "✅ Deployment and health check test complete!"