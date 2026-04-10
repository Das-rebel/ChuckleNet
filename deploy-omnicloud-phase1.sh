#!/bin/bash

###############################################################################
# OmniClaw Personal Assistant - Deployment Script
# Phase 1: Deploy all 4 phases with resilience to Google Cloud Platform
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-omniclaw-personal-assistant}"
REGION="${GOOGLE_CLOUD_REGION:-asia-south1}"
STORAGE_BUCKET="${PROJECT_ID}-cloudbuild"

echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}  OmniClaw Personal Assistant - Deployment${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""

# Check if gcloud is configured
echo -e "${YELLOW}Checking Google Cloud configuration...${NC}"
if ! gcloud projects describe "$PROJECT_ID" &>/dev/null; then
    echo -e "${RED}Error: Project $PROJECT_ID not found or gcloud not configured${NC}"
    echo -e "${YELLOW}Run: gcloud config set project $PROJECT_ID${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Project: $PROJECT_ID${NC}"
echo -e "${GREEN}✓ Region: $REGION${NC}"
echo ""

# Enable required APIs
echo -e "${YELLOW}Enabling required APIs...${NC}"
gcloud services enable \
    cloudfunctions.googleapis.com \
    cloudbuild.googleapis.com \
    firestore.googleapis.com \
    cloudresourcemanager.googleapis.com \
    secretmanager.googleapis.com \
    cloudscheduler.googleapis.com \
    redis.googleapis.com \
    --project="$PROJECT_ID"

echo -e "${GREEN}✓ Required APIs enabled${NC}"
echo ""

# Create deployment directories
echo -e "${YELLOW}Preparing deployment directories...${NC}"
DEPLOY_DIR="/tmp/omniclaw-deploy"
rm -rf "$DEPLOY_DIR"
mkdir -p "$DEPLOY_DIR"

# Function to deploy a Cloud Function
deploy_function() {
    local name=$1
    local source_dir=$2
    local entry_point=$3

    echo -e "${BLUE}Deploying: $name${NC}"

    # Create temporary deployment directory
    local deploy_subdir="$DEPLOY_DIR/$name"
    mkdir -p "$deploy_subdir"

    # Copy source files
    if [ -d "$source_dir" ]; then
        cp -r "$source_dir"/* "$deploy_subdir/"
    else
        echo -e "${RED}Error: Source directory $source_dir not found${NC}"
        return 1
    fi

    # Create package.json if it doesn't exist
    if [ ! -f "$deploy_subdir/package.json" ]; then
        cat > "$deploy_subdir/package.json" << EOF
{
  "name": "$name",
  "version": "1.0.0",
  "main": "$entry_point",
  "dependencies": {
    "express": "^4.18.2",
    "axios": "^1.6.0",
    "winston": "^3.11.0",
    "@google-cloud/firestore": "^7.0.0",
    "@google-cloud/secret-manager": "^5.0.0",
    "dotenv": "^16.3.1"
  }
}
EOF
    fi

    # Deploy to Cloud Functions Gen 2
    gcloud functions deploy "$name" \
        --gen2 \
        --runtime=nodejs22 \
        --region="$REGION" \
        --source="$deploy_subdir" \
        --entry-point="$entry_point" \
        --trigger-http \
        --allow-unauthenticated \
        --memory=2048MB \
        --timeout=120s \
        --max-instances=100 \
        --min-instances=0 \
        --project="$PROJECT_ID"

    echo -e "${GREEN}✓ $name deployed${NC}"
    echo ""
}

# Function to get function URL
get_function_url() {
    local name=$1
    gcloud functions describe "$name" \
        --region="$REGION" \
        --format="value(serviceConfig.uri)" \
        --project="$PROJECT_ID"
}

# ============================================================================
# Deploy OmniClaw Base (OpenClaw with Resilience)
# ============================================================================
echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}  Phase 0: Deploying Base OpenClaw with Resilience${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""

deploy_function "omniclaw-resilient" \
    "/Users/Subho/openclaw-alexa-bridge" \
    "alexaHandler"

OMNICLAW_URL=$(get_function_url "omniclaw-resilient")
echo -e "${GREEN}Base OpenClaw URL: $OMNICLAW_URL${NC}"
echo ""

# ============================================================================
# Deploy Phase 1: Email Intelligence
# ============================================================================
echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}  Phase 1: Deploying Email Intelligence${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""

# Create Email API deployment package
EMAIL_DEPLOY="$DEPLOY_DIR/email-intelligence"
mkdir -p "$EMAIL_DEPLOY"

# Copy email intelligence files
cp -r /Users/Subho/omniclaw-personal-assistant/apps/email-intelligence/* "$EMAIL_DEPLOY/"

# Create index.js entry point
cat > "$EMAIL_DEPLOY/index.js" << 'EOF'
const express = require('express');
const { logger } = require('./services/logger');
const emailApi = require('./api/email-api');

const app = express();
app.use(express.json());
app.use('/api/email', emailApi);

app.get('/', (req, res) => {
  res.json({
    service: 'Email Intelligence',
    status: 'healthy',
    timestamp: new Date().toISOString()
  });
});

const port = process.env.PORT || 8080;
app.listen(port, () => {
  logger.info(`Email Intelligence API listening on port ${port}`);
});

exports.emailIntelligence = app;
EOF

deploy_function "omniclaw-email" \
    "$EMAIL_DEPLOY" \
    "emailIntelligence"

EMAIL_URL=$(get_function_url "omniclaw-email")
echo -e "${GREEN}Email Intelligence URL: $EMAIL_URL${NC}"
echo ""

# ============================================================================
# Deploy Phase 2: Price Tracking
# ============================================================================
echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}  Phase 2: Deploying Price Tracking${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""

# Create Price Tracking deployment package
PRICE_DEPLOY="$DEPLOY_DIR/price-tracking"
mkdir -p "$PRICE_DEPLOY"

# Copy price tracking files
cp -r /Users/Subho/omniclaw-personal-assistant/apps/price-tracking/* "$PRICE_DEPLOY/"

# Create index.js entry point
cat > "$PRICE_DEPLOY/index.js" << 'EOF'
const express = require('express');
const { logger } = require('./services/logger');
const { PriceTracking } = require('./src/index');

const app = express();
app.use(express.json());

const priceTracking = new PriceTracking();

app.get('/', (req, res) => {
  res.json({
    service: 'Price Tracking',
    status: 'healthy',
    timestamp: new Date().toISOString()
  });
});

app.post('/api/price/track', async (req, res) => {
  try {
    const result = await priceTracking.trackProduct(req.body);
    res.json({ success: true, data: result });
  } catch (error) {
    logger.error('Track product failed:', error);
    res.status(500).json({ success: false, error: error.message });
  }
});

app.get('/api/price/current', async (req, res) => {
  try {
    const { url } = req.query;
    const price = await priceTracking.getCurrentPrice(url);
    res.json({ success: true, data: price });
  } catch (error) {
    logger.error('Get current price failed:', error);
    res.status(500).json({ success: false, error: error.message });
  }
});

const port = process.env.PORT || 8080;
app.listen(port, () => {
  logger.info(`Price Tracking API listening on port ${port}`);
});

exports.priceTracking = app;
EOF

deploy_function "omniclaw-price" \
    "$PRICE_DEPLOY" \
    "priceTracking"

PRICE_URL=$(get_function_url "omniclaw-price")
echo -e "${GREEN}Price Tracking URL: $PRICE_URL${NC}"
echo ""

# ============================================================================
# Deploy Phase 3: Media Streaming
# ============================================================================
echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}  Phase 3: Deploying Media Streaming${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""

# Create Media Streaming deployment package
MEDIA_DEPLOY="$DEPLOY_DIR/media-streaming"
mkdir -p "$MEDIA_DEPLOY"

# Copy media streaming files
cp -r /Users/Subho/omniclaw-personal-assistant/apps/media-streaming/* "$MEDIA_DEPLOY/"

# Create index.js entry point
cat > "$MEDIA_DEPLOY/index.js" << 'EOF'
const express = require('express');
const { logger } = require('./services/logger');
const { resolvers, controller } = require('./bridge/media-streaming-resolvers');

const app = express();
app.use(express.json());

app.get('/', (req, res) => {
  res.json({
    service: 'Media Streaming',
    status: 'healthy',
    timestamp: new Date().toISOString()
  });
});

app.get('/health', async (req, res) => {
  try {
    const statuses = await resolvers.Query.getAllPlatformStatuses();
    res.json({
      service: 'Media Streaming',
      status: 'healthy',
      platforms: statuses,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

const port = process.env.PORT || 8080;
app.listen(port, () => {
  logger.info(`Media Streaming API listening on port ${port}`);
});

exports.mediaStreaming = app;
EOF

deploy_function "omniclaw-media" \
    "$MEDIA_DEPLOY" \
    "mediaStreaming"

MEDIA_URL=$(get_function_url "omniclaw-media")
echo -e "${GREEN}Media Streaming URL: $MEDIA_URL${NC}"
echo ""

# ============================================================================
# Deploy Phase 4: Story Narrator
# ============================================================================
echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}  Phase 4: Deploying Story Narrator${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""

# Create Story Narrator deployment package
STORY_DEPLOY="$DEPLOY_DIR/story-narrator"
mkdir -p "$STORY_DEPLOY"

# Copy story narrator files
cp -r /Users/Subho/omniclaw-personal-assistant/apps/story-narrator/* "$STORY_DEPLOY/"

# Create index.js entry point
cat > "$STORY_DEPLOY/index.js" << 'EOF'
const express = require('express');
const { logger } = require('./services/logger');
const { createStoryNarrator } = require('./index');

const app = express();
app.use(express.json());

// Initialize story narrator
let narrator = null;

function getNarrator() {
  if (!narrator) {
    const Anthropic = require('@anthropic-ai/sdk');
    const claudeClient = new Anthropic({
      apiKey: process.env.ANTHROPIC_API_KEY
    });

    narrator = createStoryNarrator(claudeClient, {
      enableStreaming: true,
      targetLatency: 400,
      defaultLanguage: 'en'
    });
  }
  return narrator;
}

app.get('/', (req, res) => {
  res.json({
    service: 'Story Narrator',
    status: 'healthy',
    timestamp: new Date().toISOString()
  });
});

app.post('/api/story/narrate', async (req, res) => {
  try {
    const { storyName } = req.body;
    const narrator = getNarrator();
    const { getStory } = require('./stories/demo-stories');
    const story = getStory(storyName, 'en');
    const result = await narrator.narrateStory(story);

    res.json({ success: true, data: result });
  } catch (error) {
    logger.error('Narrate story failed:', error);
    res.status(500).json({ success: false, error: error.message });
  }
});

const port = process.env.PORT || 8080;
app.listen(port, () => {
  logger.info(`Story Narrator API listening on port ${port}`);
});

exports.storyNarrator = app;
EOF

deploy_function "omniclaw-story" \
    "$STORY_DEPLOY" \
    "storyNarrator"

STORY_URL=$(get_function_url "omniclaw-story")
echo -e "${GREEN}Story Narrator URL: $STORY_URL${NC}"
echo ""

# ============================================================================
# Deployment Summary
# ============================================================================
echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}  Deployment Complete!${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""
echo -e "${GREEN}✓ All OmniClaw phases deployed successfully${NC}"
echo ""
echo -e "${YELLOW}Deployed Services:${NC}"
echo -e "  📧 Email Intelligence:  $EMAIL_URL"
echo -e "  💰 Price Tracking:      $PRICE_URL"
echo -e "  🎵 Media Streaming:     $MEDIA_URL"
echo -e "  📖 Story Narrator:      $STORY_URL"
echo -e "  🤖 Base OpenClaw:       $OMNICLAW_URL"
echo ""
echo -e "${YELLOW}Health Check Endpoints:${NC}"
echo -e "  Email:    $EMAIL_URL/api/email/health"
echo -e "  Price:    $PRICE_URL/"
echo -e "  Media:    $MEDIA_URL/health"
echo -e "  Story:    $STORY_URL/"
echo -e "  Base:     $OMNICLAW_URL/api/health"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo -e "  1. Test health endpoints"
echo -e "  2. Configure API keys in Secret Manager"
echo -e "  3. Update Alexa skill endpoints"
echo -e "  4. Run integration tests"
echo ""
echo -e "${GREEN}Deployment completed at: $(date)${NC}"
echo ""

# Cleanup
rm -rf "$DEPLOY_DIR"

exit 0
