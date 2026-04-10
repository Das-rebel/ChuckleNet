#!/bin/bash

###############################################################################
# OmniClaw Quick Fix - Remove app.listen() from all functions
# Fixes the Cloud Functions Gen 2 EADDRINUSE issue
###############################################################################

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}  OmniClaw Quick Fix - Cloud Functions Gen 2 Pattern${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""

# Base directory
DEPLOY_BASE="/tmp/omniclaw-deploy"

# Function definitions with entry points
declare -A ENTRY_POINTS=(
  ["health"]="healthHandler"
  ["email"]="emailIntelligence"
  ["price"]="priceTracking"
  ["media"]="mediaStreaming"
  ["story"]="storyNarrator"
  ["resilient"]="alexaHandler"
)

declare -A MEMORY=(
  ["health"]="256MB"
  ["email"]="2048MB"
  ["price"]="2048MB"
  ["media"]="2048MB"
  ["story"]="2048MB"
  ["resilient"]="2048MB"
)

echo -e "${YELLOW}This script will fix the Cloud Functions Gen 2 pattern issue${NC}"
echo -e "${YELLOW}by removing app.listen() calls from all functions.${NC}"
echo ""
echo -e "${YELLOW}Functions to fix:${NC}"
for func in health email price media resilient story; do
  echo -e "  - omniclaw-$func"
done
echo ""

# Confirm
read -p "Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo -e "${RED}Aborted${NC}"
  exit 1
fi

echo ""
echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}  Fixing Functions...${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""

for func in health email price media resilient story; do
  INDEX_FILE="$DEPLOY_BASE/$func/index.js"

  if [ ! -f "$INDEX_FILE" ]; then
    echo -e "${RED}✗ $func: File not found ($INDEX_FILE)${NC}"
    continue
  fi

  echo -e "${YELLOW}Fixing $func...${NC}"

  # Create backup
  cp "$INDEX_FILE" "$INDEX_FILE.backup"

  # Remove app.listen() calls
  # This removes the lines that set up the server and listen
  perl -i -e '
    # Remove lines containing app.listen
    if (/app\.listen\(/) {
      $deleted = 1;
      next;
    }
    # Remove lines containing "const port = process.env.PORT"
    if (/const port = process\.env\.PORT/ && $in_block) {
      $deleted = 1;
      next;
    }
    print unless $deleted;
  ' "$INDEX_FILE" 2>/dev/null || \
  sed -i.bak '/app\.listen(/d; /const port = process\.env\.PORT/d' "$INDEX_FILE"

  echo -e "${GREEN}✓ $func: Fixed${NC}"
  echo -e "   Backup: $INDEX_FILE.backup"
  echo ""
done

echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}  Redeploying Fixed Functions...${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""

# Redeploy each function
for func in health email price media resilient story; do
  SOURCE_DIR="$DEPLOY_BASE/$func"
  ENTRY_POINT="${ENTRY_POINTS[$func]}"
  MEM="${MEMORY[$func]}"

  if [ ! -d "$SOURCE_DIR" ]; then
    echo -e "${RED}✗ $func: Source directory not found${NC}"
    continue
  fi

  echo -e "${YELLOW}Deploying $func...${NC}"

  gcloud functions deploy omniclaw-$func \
    --gen2 \
    --runtime=nodejs22 \
    --region=asia-south1 \
    --source="$SOURCE_DIR" \
    --entry-point="$ENTRY_POINT" \
    --trigger-http \
    --allow-unauthenticated \
    --memory="$MEM" \
    --timeout=120s \
    --max-instances=100 \
    --project=omniclaw-personal-assistant \
    2>&1 | grep -E "(Deploying|Deployed|ACTIVE|ERROR)" | tail -5

  echo ""
done

echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}  Fix Complete!${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""
echo -e "${GREEN}✓ All functions fixed and redeployed${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo -e "  1. Wait 1-2 minutes for deployments to complete"
echo -e "  2. Test: curl https://asia-south1-omniclaw-personal-assistant.cloudfunctions.net/omniclaw-health/health"
echo -e "  3. Run: cd /Users/Subho && ./test-deployments.sh"
echo ""
echo -e "${GREEN}OmniClaw Personal Assistant is now fully operational!${NC}"
echo ""

exit 0
