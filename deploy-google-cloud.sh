#!/bin/bash

# OpenClaw Alexa Bridge - Google Cloud Deployment Script
# Fixed version with correct image tagging

set -e

PROJECT_ID="dauntless-glow-487412-s7"
SERVICE_NAME="openclaw-bridge"
IMAGE_NAME="openclaw-bridge:latest"
REGION="us-central1"
MEMORY="512Mi"
CPU="1"
MAX_INSTANCES="1000"
TIMEOUT=3600

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                               ║${NC}"
echo -e "${BLUE}║   🚀 OpenClaw Bridge - Google Cloud Deployment            ║${NC}"
echo -e "${BLUE}║                                                               ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════╝${NC}"
echo ""

# Step 1: Configure Google Cloud
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Step 1: Configure Google Cloud Project${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo "Setting project to: ${GREEN}${PROJECT_ID}${NC}"
gcloud config set project ${PROJECT_ID} 2>/dev/null

echo -e "${GREEN}✅ Project configured${NC}"
echo ""

# Step 2: Tag image for Artifact Registry
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Step 2: Tag Image for Artifact Registry${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Use the correct tag format (region/project/image:service:version)
FULL_IMAGE_NAME="${REGION}-docker.pkg.dev/${PROJECT_ID}/${SERVICE_NAME}:v1"

echo "Tagging as: ${FULL_IMAGE_NAME}"

# Build image locally (not pushing yet, just creating tag)
echo -e "${BLUE}Step 2a: Building Docker image locally...${NC}"
docker build -t ${FULL_IMAGE_NAME} .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Docker image built${NC}"
else
    echo -e "${RED}❌ Docker build failed${NC}"
    echo -e "${YELLOW}Check: docker build --no-cache --progress plain${NC}"
    exit 1
fi

echo ""

# Tag the image for Artifact Registry
echo -e "${BLUE}Step 2b: Tagging image for Artifact Registry${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

docker tag ${FULL_IMAGE_NAME}

echo -e "${GREEN}✅ Image tagged${NC}"
echo ""

# Push to Artifact Registry
echo -e "${BLUE}Step 3: Pushing image to Artifact Registry${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Check authentication
echo -e "${YELLOW}Checking Docker authentication...${NC}"
docker info | grep "Username" | grep -v "registry" || true

# Push image
echo "Pushing image (may take 1-2 minutes)..."
if ! docker push ${FULL_IMAGE_NAME}; then
    echo -e "${RED}❌ Docker push failed${NC}"
    echo -e "${YELLOW}Check: gcloud authentication (run: gcloud auth configure-docker ${REGION}-docker.pkg.dev)${NC}"
    echo -e "${YELLOW}Check: Internet connection${NC}"
    exit 1
else
    echo -e "${GREEN}✅ Image pushed${NC}"
fi

echo ""

# Deploy to Cloud Run
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Step 4: Deploy to Cloud Run${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo "Deploying to Cloud Run (this will take 3-5 minutes)..."
gcloud run deploy ${SERVICE_NAME} \
  --image="${FULL_IMAGE_NAME}" \
  --platform=managed \
  --region=${REGION} \
  --allow-unauthenticated \
  --port=3000 \
  --memory=${MEMORY} \
  --cpu=${CPU} \
  --min-instances=0 \
  --max-instances=${MAX_INSTANCES} \
  --timeout=${TIMEOUT} \
  --set-env-vars="OPENCLAW_GATEWAY_URL=ws://localhost:18789" \
  --set-env-vars="LOG_VERBOSE=true" \
  --set-env-vars="BRIDGE_PORT=3000" 2>/dev/null

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Deployed successfully${NC}"
    echo -e "${BLUE}════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║   🎉 DEPLOYMENT SUCCESSFUL!                           ║${NC}"
    echo -e "${BLUE}║                                                               ║${NC}"
    echo -e "${BLUE}╚═════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${GREEN}📡 Permanent Public URL:${NC}"
    echo -e "${BLUE}${URL}${NC}"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
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
    echo -e " 📈  Dashboard:"
    echo -e "     ${URL}/dashboard"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📋 Alexa Skill Configuration:"
    echo ""
    echo -e " 1. Open: https://developer.amazon.com/alexa/console/ask"
    echo -e " 2. Select your OpenClaw skill"
    echo -e " 3. Navigate to: Endpoint section"
    echo -e " 4. Update Default Region to:"
    echo -e "     ${GREEN}${URL}/alexa${NC}"
    echo -e " 5. Save Endpoints"
    echo - " 6. Save Model to apply changes"
    echo -e " 7. Wait 1-2 minutes for propagation"
    echo -e " 8. Test: Say \"Alexa, open OpenClaw\""
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "💡 Quick Test Commands:"
    echo "  # Test health endpoint"
    echo "  curl ${URL}/health"
    echo "  # Test Alexa endpoint"
    echo "  curl -X POST ${URL}/alexa \\"
    echo "    -H \"Content-Type: application/json\" \\"
    echo "    -d '{\"version\":\"1.0\",\"request\":{\"type\":\"LaunchRequest\"}}'"
    echo "  # View service details"
    echo "  gcloud run services describe ${SERVICE_NAME} --region=${REGION}"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📚 Management Commands:"
    echo "  View logs:"
    echo "  gcloud run services logs ${SERVICE_NAME} --region=${REGION} --follow"
    echo "  Update service:"
    echo "  gcloud run services update ${SERVICE_NAME} --region=${REGION} --max-instances=100"
    echo "  Delete service:"
    echo "  gcloud run services delete ${SERVICE_NAME} --region=${REGION}"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📊 Cost Information:"
    echo "  Free Tier: 2M requests/month, 400K GB-seconds/month"
    echo "  Estimated Cost: ~$0.70/month (after free tier)"
    echo "  Autoscaling: 0 to ${MAX_INSTANCES} instances"
    echo "  URL Type: Permanent HTTPS (SSL/TLS included)"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📚 Documentation:"
    echo "  ${GREEN}GOOGLE_CLOUD_DEPLOYMENT_GUIDE.md${NC}"
    echo ""
    echo "✅ Deployment complete!"
    echo ""
