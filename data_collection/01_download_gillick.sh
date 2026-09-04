#!/bin/bash
# PART 1: Download Gillick 600 Videos
# This script downloads up to 600 available Gillick AudioSet videos

OUTPUT_DIR="/Users/Subho/data/utterances/gillick_audio"
PARALLEL=10
MAX_VIDEOS=600

mkdir -p "$OUTPUT_DIR"

echo "=== PART 1: DOWNLOAD GILLICK 600 ==="
echo "Output: $OUTPUT_DIR"
echo "Max videos: $MAX_VIDEOS"
echo ""

# Check for available videos (test first 100)
echo "Testing video availability..."
> /tmp/gillick_available.txt

count=0
while IFS= read -r vid && [ $count -lt $MAX_VIDEOS ]; do
    if yt-dlp --dump-json "https://youtu.be/$vid" >/dev/null 2>&1; then
        echo "$vid" >> /tmp/gillick_available.txt
        echo "✓ $vid"
        ((count++))
    else
        echo "✗ $vid (unavailable)"
    fi
done < /tmp/gillick_988_videos.txt

TOTAL=$(wc -l < /tmp/gillick_available.txt)
echo ""
echo "Available: $TOTAL videos"
echo ""

# Download in parallel batches
echo "Downloading in $PARALLEL parallel streams..."
split -n l/$PARALLEL /tmp/gillick_available.txt /tmp/gillick_batch_

for batch in /tmp/gillick_batch_*; do
    (
        while IFS= read -r vid; do
            out="$OUTPUT_DIR/${vid}.mp3"
            if [ ! -f "$out" ]; then
                yt-dlp --extract-audio --audio-format mp3 --audio-quality 5 \
                    -o "$out" "https://youtu.be/$vid" -q 2>/dev/null
                echo "✓ $vid"
            fi
        done < "$batch"
    ) &
done

wait

echo ""
echo "=== PART 1 COMPLETE ==="
FINAL=$(ls "$OUTPUT_DIR"/*.mp3 2>/dev/null | wc -l)
echo "Downloaded: $FINAL / $MAX_VIDEOS videos"
