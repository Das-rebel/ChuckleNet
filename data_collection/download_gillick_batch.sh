#!/bin/bash
# Download Gillick 988 AudioSet videos with laughter labels
# These have PRE-VALIDATED human laughter timestamps
# Just download and use the existing labels!

OUTPUT_DIR="/Users/Subho/data/utterances/gillick_audio"
SKIP_DIR="/Users/Subho/data/utterances/vtt_audio_local"
VIDEO_LIST="/tmp/gillick_988_videos.txt"
PARALLEL=${1:-15}

mkdir -p "$OUTPUT_DIR"

echo "=== GILLICK 988 DOWNLOAD ==="
echo "Output: $OUTPUT_DIR"
echo "Parallel: $PARALLEL"
echo ""

# Count total and already downloaded
TOTAL=$(wc -l < "$VIDEO_LIST")
EXISTING=$(ls "$OUTPUT_DIR" 2>/dev/null | wc -l)
echo "Total in list: $TOTAL"
echo "Already downloaded: $EXISTING"

# Filter out already downloaded
ALREADY=$(ls "$OUTPUT_DIR" 2>/dev/null | sed 's/\.[^.]*$//' | sort -u)
SKIP_THESE=$(echo "$ALREADY" | while read v; do grep -m1 "^$v$" "$VIDEO_LIST" 2>/dev/null; done)
TO_DOWNLOAD=$(grep -vxf <(echo "$SKIP_THESE") "$VIDEO_LIST" 2>/dev/null | wc -l)

echo "To download: $TO_DOWNLOAD"
echo ""

# Download with parallel yt-dlp instances
split -n l/$PARALLEL "$VIDEO_LIST" /tmp/gillick_batch_

for batch in /tmp/gillick_batch_*; do
    (
        echo "Starting: $batch"
        while IFS= read -r vid; do
            outfile="$OUTPUT_DIR/${vid}.mp3"
            if [ ! -f "$outfile" ]; then
                yt-dlp \
                    --extract-audio \
                    --audio-format mp3 \
                    --audio-quality 5 \
                    -o "$outfile" \
                    "https://youtu.be/$vid" \
                    -q 2>/dev/null
            fi
        done < "$batch"
        echo "Complete: $batch"
    ) &
done

wait

echo ""
echo "=== COMPLETE ==="
FINAL=$(ls "$OUTPUT_DIR" 2>/dev/null | wc -l)
echo "Downloaded: $FINAL / $TOTAL"
