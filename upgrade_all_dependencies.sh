#!/bin/bash

# Comprehensive Dependency Upgrade Script
# This script upgrades all dependencies across all projects

set -e

echo "🚀 Starting dependency upgrades..."
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Upgrade Python dependencies (monk)
echo -e "${BLUE}📦 Upgrading Python dependencies in monk/...${NC}"
if [ -d "monk" ]; then
    cd monk
    if [ -f "requirements.txt" ]; then
        echo "Installing/upgrading Python packages..."
        pip install --upgrade -r requirements.txt
        echo -e "${GREEN}✅ Python dependencies upgraded${NC}"
    fi
    cd ..
else
    echo -e "${YELLOW}⚠️  monk directory not found, skipping...${NC}"
fi
echo ""

# 2. Upgrade brain-spark-analysis-project
echo -e "${BLUE}📦 Upgrading npm dependencies in brain-spark-analysis-project/...${NC}"
if [ -d "brain-spark-analysis-project" ]; then
    cd brain-spark-analysis-project
    if [ -f "package.json" ]; then
        echo "Checking for outdated packages..."
        npm outdated || true
        echo "Updating packages..."
        npm update
        echo "Running npm-check-updates for major version upgrades..."
        npx -y npm-check-updates -u || echo "npm-check-updates not available, using npm update only"
        if [ -f "package.json.bak" ]; then
            echo "Review package.json.bak for changes, then run: npm install"
        else
            npm install
        fi
        echo -e "${GREEN}✅ brain-spark-analysis-project dependencies upgraded${NC}"
    fi
    cd ..
else
    echo -e "${YELLOW}⚠️  brain-spark-analysis-project directory not found, skipping...${NC}"
fi
echo ""

# 3. Upgrade second-brain
echo -e "${BLUE}📦 Upgrading npm dependencies in second-brain/...${NC}"
if [ -d "second-brain" ]; then
    cd second-brain
    if [ -f "package.json" ]; then
        echo "Checking for outdated packages..."
        npm outdated || true
        echo "Updating packages..."
        npm update
        echo "Running npm-check-updates for major version upgrades..."
        npx -y npm-check-updates -u || echo "npm-check-updates not available, using npm update only"
        if [ -f "package.json.bak" ]; then
            echo "Review package.json.bak for changes, then run: npm install"
        else
            npm install
        fi
        echo -e "${GREEN}✅ second-brain dependencies upgraded${NC}"
    fi
    cd ..
else
    echo -e "${YELLOW}⚠️  second-brain directory not found, skipping...${NC}"
fi
echo ""

echo -e "${GREEN}✨ All dependency upgrades complete!${NC}"
echo ""
echo "📝 Next steps:"
echo "   1. Review any package.json.bak files if created"
echo "   2. Test your applications to ensure everything works"
echo "   3. Commit the updated package files"
echo ""
