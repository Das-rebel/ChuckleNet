#!/bin/bash
# Parallel Pipeline: Download Gillick 600 + Improve Existing 568
# Run both in parallel for maximum efficiency

set -e

echo "=== PARALLEL PIPELINE: Gillick 600 + Existing 568 Improvement ==="
echo ""

# Create output dirs
mkdir -p /Users/Subho/data/utterances/gillick_audio
mkdir -p /Users/Subho/data/utterances/quality_comedy

# Get available Gillick IDs (already validated downloadable)
echo "Finding available Gillick videos..."
AVAILABLE=0
UNAVAILABLE=0
> /tmp/gillick_available.txt
> /tmp/gillick_unavailable.txt

while IFS= read -r vid; do
    if yt-dlp --dump-json "https://youtu.be/$vid" >/dev/null 2>&1; then
        echo "$vid" >> /tmp/gillick_available.txt
        ((AVAILABLE++))
    else
        echo "$vid" >> /tmp/gillick_unavailable.txt
        ((UNAVAILABLE++))
    fi
    if [ $AVAILABLE -ge 600 ]; then
        break
    fi
done < /tmp/gillick_988_videos.txt

echo "Found $AVAILABLE available Gillick videos"
echo "Unavailable: $UNAVAILABLE"
echo ""

# Save available list
echo "Available Gillick videos saved to /tmp/gillick_available.txt"
