#!/bin/bash

# Move Projects to Google Drive
# Account: meghamukherjeedas@gmail.com

set -e

echo "==================================="
echo "Google Drive Migration Script"
echo "==================================="
echo ""

# Check if rclone is installed
if ! command -v rclone &> /dev/null; then
    echo "ERROR: rclone not installed"
    exit 1
fi

# Check if gdrive is configured
if ! rclone listremotes | grep -q "^gdrive:"; then
    echo "Google Drive not configured yet. Configuring now..."
    echo ""
    echo "A browser window will open. Please sign in with:"
    echo "📧 meghamukherjeedas@gmail.com"
    echo ""
    read -p "Press Enter to continue..."
    rclone config
    echo ""
    echo "✓ Google Drive configured!"
    echo ""
fi

# Create backup directory in Google Drive
echo "Creating backup directory in Google Drive..."
rclone mkdir gdrive:/Project_Backups
rclone mkdir gdrive:/Project_Backups/Priority1
rclone mkdir gdrive:/Project_Backups/Priority2
echo "✓ Backup directories created"
echo ""

# Priority 1 Projects (excluding alexa, treequest, task-master)
echo "==================================="
echo "Moving Priority 1 Projects"
echo "==================================="
echo ""

P1_PROJECTS=(
    "trading-frontend"
    "market-analysis-system"
)

for project in "${P1_PROJECTS[@]}"; do
    if [ -d "/Users/Subho/$project" ]; then
        size=$(du -sh "/Users/Subho/$project" | cut -f1)
        echo "📦 Moving: $project ($size)"
        rclone sync "/Users/Subho/$project" "gdrive:/Project_Backups/Priority1/$project" --progress
        echo "✓ $project moved to Google Drive"
        echo ""
    else
        echo "⚠️  Warning: $project not found"
    fi
done

# Priority 2 Projects (excluding brain-spark-monorepo)
echo "==================================="
echo "Moving Priority 2 Projects"
echo "==================================="
echo ""

P2_PROJECTS=(
    "agile-trading-platform"
    "smart-ai-enhanced-project"
    "twitter-bookmark-scraper"
    "linkedin-knowledge-assistant"
)

for project in "${P2_PROJECTS[@]}"; do
    if [ -d "/Users/Subho/$project" ]; then
        size=$(du -sh "/Users/Subho/$project" | cut -f1)
        echo "📦 Moving: $project ($size)"
        rclone sync "/Users/Subho/$project" "gdrive:/Project_Backups/Priority2/$project" --progress
        echo "✓ $project moved to Google Drive"
        echo ""
    else
        echo "⚠️  Warning: $project not found"
    fi
done

echo "==================================="
echo "Migration Complete!"
echo "==================================="
echo ""
echo "All projects have been synced to Google Drive:"
echo "📁 gdrive:/Project_Backups/Priority1/"
echo "📁 gdrive:/Project_Backups/Priority2/"
echo ""
echo "You can access them at:"
echo "https://drive.google.com/drive/u/0/folders/..."
