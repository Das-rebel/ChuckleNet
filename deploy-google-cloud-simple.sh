#!/bin/bash

# Simple Docker Build and Push Script for Google Cloud Run
# Doesn't require Docker buildx - uses standard Docker build

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                                                               ║${NC}"
echo -e "${GREEN}║   🚀 Simple Docker Build & Push Script                 ║${NC}"
echo -e "${GREEN}║                                                               ║${NC}"
echo -e "${GREEN}╚═════════════════════════════════════════╝${NC}"
echo ""

# Check if Docker daemon is running
if docker info 2>&1 | grep -q "Server Version"; then
    echo -e "${GREEN}✅ Docker daemon is running${NC}"
    BUILD_CMD="docker build"
else
    echo -e "${YELLOW}⚠️  Docker daemon not running${NC}"
    echo -e "${YELLOW}Please start Docker Desktop first${NC}"
    exit 1
fi

# Build image
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Step 1: Building Docker image${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if ! $BUILD_CMD build -t openclaw-bridge:latest .; then
    echo -e "${RED}❌ Docker build failed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker image built${NC}"
echo ""

# Tag for Google Artifact Registry
echo -e "${BLUE}Step 2: Tagging image${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

IMAGE_TAG="us-central1-docker.pkg.dev/dauntless-glow-487412-s7/openclaw-bridge:latest"
docker tag openclaw-bridge:latest ${IMAGE_TAG}

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Image tagged${NC}"
else
    echo -e "${RED}❌ Tag failed${NC}"
    exit 1
fi

echo ""

# Push to Google Artifact Registry
echo -e "${BLUE}Step 3: Pushing image to Google Cloud${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

if ! docker push ${IMAGE_TAG}; then
    echo -e "${RED}❌ Docker push failed${NC}"
    echo -e "${YELLOW}Please check:${NC}"
    echo -e "${YELLOW}  - Docker Hub authentication (run: docker login)${NC}"
    echo -e "${YELLOW}  - Internet connection${NC}"
    echo -e "${YELLOW}  - Image exists (${IMAGE_TAG})${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Image pushed to Google Artifact Registry${NC}"
echo ""

# Deploy to Cloud Run
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Step 4: Deploying to Cloud Run${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Note: This uses the gcloud CLI, not the Cloud Run UI
# The script is designed to work even if Cloud Run UI is preferred
gcloud run deploy openclaw-bridge \
  --image=${IMAGE_TAG} \
  --platform=managed \
  --region=us-central1 \
  --allow-unauthenticated \
  --port=3000 \
  --memory=512Mi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=1000 \
  --timeout=3600 \
  --set-env-vars="OPENCLAW_GATEWAY_URL=ws://localhost:18789" \
  --set-env-vars="LOG_VERBOSE=true" \
  --set-env-vars="BRIDGE_PORT=3000"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Deployed successfully${NC}"
else
    echo -e "${RED}❌ Deployment failed${NC}"
    echo -e "${YELLOW}Check logs: gcloud run services logs openclaw-bridge --region=us-central1${NC}"
    exit 1
fi

echo ""

# Get deployed URL
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Step 5: Get Deployed URL${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Try up to 10 times to get URL (Cloud Run may take time)
URL=""
for i in {1..15}; do
    URL=$(gcloud run services describe openclaw-bridge --region=us-central1 --format="value(status.url)" 2>/dev/null)
    if [ -n "$URL" ] && [[ "$URL" != http://localhost:* ]]; then
        echo -e "${GREEN}✅ Got URL on attempt $i${NC}"
        echo -e "${BLUE}═══════════════════════════════════════${NC}"
        break
    fi
    sleep 2
done

if [ -z "$URL" ] || [[ "$URL" == http://localhost:* ]]; then
    echo -e "${RED}❌ Failed to retrieve service URL${NC}"
    echo -e "${YELLOW}Note: This is normal for new deployments - service may take up to 10 minutes${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}╔══════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                               ║${NC}"
echo -e "${BLUE}║   🎉 DEPLOYMENT SUCCESSFUL!                           ║${NC}"
echo -e "${BLUE}║                                                               ║${NC}"
echo -e "${BLUE}╚═════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}📡 Public URL:${NC}"
echo -e "${BLUE}${URL}${NC}"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Available endpoints:"
echo ""
echo -e " 🏥  Health Check:"
echo -e "     ${URL}/health"
echo ""
echo -e " 🤖  Alexa Endpoint:"
echo -e "     ${URL}/alexa"
echo ""
echo -e " 📊  Statistics:"
echo -e "     ${URL}/stats"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Ready to deploy!${NC}"
echo ""