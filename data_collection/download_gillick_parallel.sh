#!/bin/bash
# Download Gillick 988 AudioSet videos in parallel
# Usage: ./download_gillick_parallel.sh [num_parallel] [output_dir]

NUM_PARALLEL=${1:-10}
OUTPUT_DIR=${2:-"/Users/Subho/data/utterances/gillick_audio"}
VIDEO_LIST="/tmp/gillick_988_videos.txt"

mkdir -p "$OUTPUT_DIR"

echo "Downloading Gillick 988 videos to $OUTPUT_DIR"
echo "Parallel downloads: $NUM_PARALLEL"
echo "Video list: $VIDEO_LIST"
echo ""

# Count total
TOTAL=$(wc -l < "$VIDEO_LIST")
echo "Total videos: $TOTAL"
echo ""

# Download with yt-dlp in parallel
# Each parallel instance handles a subset
split -n l/$NUM_PARALLEL "$VIDEO_LIST" /tmp/gillick_batch_

for i in /tmp/gillick_batch_*; do
    (
        echo "Starting batch: $i"
        yt-dlp \
            --write-auto-subs \
            --extract-audio \
            --audio-format mp3 \
            --audio-quality 5 \
            -P "$OUTPUT_DIR" \
            -a "$i" \
            --concurrent-fragments 3 \
            -q
        echo "Batch complete: $i"
    ) &
done

# Wait for all batches
wait
echo ""
echo "All downloads complete!"
echo "Check $OUTPUT_DIR for files"
ls "$OUTPUT_DIR" | wc -l
