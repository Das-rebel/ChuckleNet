#!/bin/bash
# Download more comedy YouTube videos to reach 1500+ total
# Usage: ./download_more_comedy.sh [num_videos]

NUM_VIDEOS=${1:-400}
OUTPUT_DIR="/Users/Subho/data/utterances/comedy_new"
SEARCH_FILE="/tmp/comedy_search_results.txt"

mkdir -p "$OUTPUT_DIR"

echo "Finding $NUM_VIDEOS more comedy videos..."
echo "Output: $OUTPUT_DIR"
echo ""

# Use yt-dlp to search and download comedy specials/playlists
# Top comedy channels on YouTube
COMEDY_CHANNELS=(
    "UCUQ4Fk3jxL9AU4R4STAJPLA"  # Russell Peters
    "UC8QjmCSAZMM7oPyrKCRh8QA"  # KSI
    "UCwWh6q1eITbL9EJKUmE4vPg"  # MrBeast
    "UCMiJRAwDNSNzuYeLNJIiXIQ"  # Stand-up
    "UC8C-zN6L-W2O2D6yLJd5L9A"  # Russell Howard
    "UCXhgK9X6Cv9LT9JBDZ8O1Lw"  # EdGY
    "UCeRqOB9azK9lPxYn5l9LT-Q"  # Jimmy Carr
    "UCc40ZtZ0LPv1q3yJMJgJgIQ"  # Stand-up UK
    "UCL-t5dOAN4rLFJYxJrnqXGw"  # Trevor Noah
    "UCtESyTXHfMRyZ9KJGZVW6Yg"  # Kevin Hart
)

# Alternative: Search by playlist (comedy specials)
PLAYLISTS=(
    "PLrAXtmErZgOeiKm4sgNOkn0T4nEFN9swd"
    "PLR3axsJHNGp7ncf2JLC3JySJ8T5T3M-n"
    "PL9S6xKes3l3vV5cX-v0g6z9dLh2K2qLq"
)

echo "Searching YouTube for comedy videos..."
echo ""

# Get videos from playlists
for playlist in "${PLAYLISTS[@]}"; do
    echo "Getting from playlist: $playlist"
    yt-dlp --flat-playlist -J "https://www.youtube.com/playlist?list=$playlist" 2>/dev/null | \
        python3 -c "import sys,json; data=json.load(sys.stdin); [print(e['id']) for e in data['entries'][:$NUM_VIDEOS]]" >> "$SEARCH_FILE" 2>/dev/null
done

# Get unique IDs
sort -u "$SEARCH_FILE" -o "$SEARCH_FILE"
TOTAL=$(wc -l < "$SEARCH_FILE")
echo ""
echo "Found $TOTAL unique videos"
echo "Starting download..."
echo ""

# Download in parallel
split -n l/10 "$SEARCH_FILE" /tmp/comedy_batch_

for i in /tmp/comedy_batch_*; do
    (
        echo "Starting: $i"
        yt-dlp \
            --write-auto-subs \
            --extract-audio \
            --audio-format mp3 \
            --audio-quality 5 \
            -P "$OUTPUT_DIR" \
            -a "$i" \
            -q
        echo "Complete: $i"
    ) &
done

wait
echo ""
echo "Download complete!"
ls "$OUTPUT_DIR" | wc -l
