#!/bin/bash

echo "==================================="
echo "Moving Projects to Google Drive"
echo "==================================="
echo "Account: meghamukherjeedas@gmail.com"
echo ""

# Create backup directories
echo "Creating backup directories..."
rclone mkdir gdrive:/Project_Backups
rclone mkdir gdrive:/Project_Backups/Priority1
rclone mkdir gdrive:/Project_Backups/Priority2
echo "✓ Backup directories created"
echo ""

# Priority 1 Projects (excluding alexa, treequest, task-master)
echo "==================================="
echo "Priority 1 Projects"
echo "==================================="
echo ""

echo "📦 Moving: trading-frontend (621 MB)"
rclone sync "/Users/Subho/trading-frontend" "gdrive:/Project_Backups/Priority1/trading-frontend" --progress
echo "✓ trading-frontend synced"
echo ""

echo "📦 Moving: market-analysis-system (892 KB)"
rclone sync "/Users/Subho/market-analysis-system" "gdrive:/Project_Backups/Priority1/market-analysis-system" --progress
echo "✓ market-analysis-system synced"
echo ""

# Priority 2 Projects (excluding brain-spark-monorepo)
echo "==================================="
echo "Priority 2 Projects"
echo "==================================="
echo ""

echo "📦 Moving: agile-trading-platform (410 MB)"
rclone sync "/Users/Subho/agile-trading-platform" "gdrive:/Project_Backups/Priority2/agile-trading-platform" --progress
echo "✓ agile-trading-platform synced"
echo ""

echo "📦 Moving: smart-ai-enhanced-project (9.2 MB)"
rclone sync "/Users/Subho/smart-ai-enhanced-project" "gdrive:/Project_Backups/Priority2/smart-ai-enhanced-project" --progress
echo "✓ smart-ai-enhanced-project synced"
echo ""

echo "📦 Moving: twitter-bookmark-scraper (18 MB)"
rclone sync "/Users/Subho/twitter-bookmark-scraper" "gdrive:/Project_Backups/Priority2/twitter-bookmark-scraper" --progress
echo "✓ twitter-bookmark-scraper synced"
echo ""

echo "📦 Moving: linkedin-knowledge-assistant (523 MB)"
rclone sync "/Users/Subho/linkedin-knowledge-assistant" "gdrive:/Project_Backups/Priority2/linkedin-knowledge-assistant" --progress
echo "✓ linkedin-knowledge-assistant synced"
echo ""

echo "==================================="
echo "Migration Complete!"
echo "==================================="
echo ""
echo "Projects synced to:"
echo "gdrive:/Project_Backups/Priority1/"
echo "gdrive:/Project_Backups/Priority2/"
echo ""
