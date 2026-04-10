#!/bin/bash

# Background deployment monitor that doesn't interfere with typing
# Run with: nohup bash deployment_monitor.sh &

echo "🚀 Starting background deployment monitoring..."
echo "Checking every 30 seconds for qce-enhanced deployment..."
echo ""
echo "This will run continuously until deployment completes."
echo ""
echo "✅ Automatically tests POST /health when service appears"
echo ""
echo "✅ Monitors deployment status"
echo ""
echo "📝 All status updates will be displayed without blocking your input"
echo ""
echo "To stop: Use Ctrl+C or kill the background process"
echo ""
echo "=========================================="
echo ""

# Main monitoring loop
while true; do
    TIMESTAMP=$(date +%H:%M:%S)
    echo "🕐 $TIMESTAMP - Checking deployment status..."
    
    # Check if qce-enhanced service exists
    if gcloud run services describe qce-enhanced --region=us-central1 --format="value(status.url.status)" >/dev/null 2>&1; then
        echo "✅ qce-enhanced service deployed!"
        URL=$(gcloud run services describe qce-enhanced --region=us-central1 --format="value(status.url.status.url)")
        echo "📍 Service URL: $URL"
        echo ""
        echo "🧪 Testing POST /health endpoint..."
        if curl -s -X POST "$URL/health" | head -c; then
            echo "✅ POST /health working! Amazon health checks will pass!"
        else
            echo "❌ POST /health not working yet"
        fi
        echo ""
        echo "🎯 Deployment Complete! Your Alexa skill should now work!"
        echo ""
        echo "📋 Next Steps:"
        echo "1. Update Amazon skill endpoint to: $URL/api/alexa"
        echo "2. Test in Alexa Simulator"
        echo "3. Test on real Alexa devices"
        break
    fi
    
    echo "⏳ Deployment still processing... (will check again in 30 seconds)"
    echo ""
    
    sleep 30
done