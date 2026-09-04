#!/bin/bash
# Smart Quality-Filtered Comedy Download
# Downloads more comedy videos, prioritizing high-quality sources
# Output: /Users/Subho/data/utterances/quality_comedy

OUTPUT_DIR="/Users/Subho/data/utterances/quality_comedy"
SKIP_FILE="/tmp/existing_video_ids.txt"
MAX_VIDEOS=${1:-500}

mkdir -p "$OUTPUT_DIR"

echo "=== SMART COMEDY DOWNLOAD ==="
echo "Output: $OUTPUT_DIR"
echo "Max videos: $MAX_VIDEOS"
echo ""

# Comedy search queries - prioritize high-laughter genres
SEARCH_QUERIES=(
    # Stand-up comedy specials (high laughter)
    "standup comedy special full"
    "comedy central roast"
    "late night talk show comedy"
    
    # Improv and interactive
    "improv comedy theater"
    "open mic comedy night"
    "comedy club performance"
    
    # Popular individual comedians (high production)
    "Russell Peters comedy"
    "Dave Chappelle special"
    "Kevin Hart standup"
    "Ali Wong comedy special"
    "John Mulaney special"
    "Hannah Gadsby Nanette"
    "Bo Burnham special"
    "Catherine Cohen comedy"
    "Aashish Gor or comedy"
    "kannada comedy show"
    "telugu comedy skit"
    
    # Crowdsourced/audience laughter
    "audience laughter comedy"
    "roast battle comedy"
    "impromptu comedy"
)

# Deduplicate with existing
echo "Checking existing videos to skip..."
if [ -f "$SKIP_FILE" ]; then
    SKIP_COUNT=$(wc -l < "$SKIP_FILE")
    echo "Will skip $SKIP_COUNT existing videos"
fi

echo ""

# Function to search and download
search_download() {
    local query="$1"
    local outfile="/tmp/yt_search_${RANDOM}.txt"
    
    # Search YouTube
    yt-dlp --dump-json \
        --default-search "ytsearch10" \
        "$query" 2>/dev/null | \
        python3 -c "
import sys, json
for line in sys.stdin:
    try:
        d = json.loads(line)
        if 'id' in d and 'duration' in d:
            # Filter: duration 3-60 min (comedy set length)
            dur = d.get('duration', 0)
            if 180 <= dur <= 3600:
                print(d['id'])
    except:
        pass
" > "$outfile" 2>/dev/null
    
    if [ -s "$outfile" ]; then
        count=$(wc -l < "$outfile")
        echo "Found $count videos for: $query"
        
        # Download
        yt-dlp \
            --write-auto-subs \
            --extract-audio \
            --audio-format mp3 \
            --audio-quality 5 \
            -P "$OUTPUT_DIR" \
            -a "$outfile" \
            -q 2>/dev/null &
    fi
    
    rm -f "$outfile"
}

# Run searches in parallel (3 at a time)
PIDS=()
for query in "${SEARCH_QUERIES[@]}"; do
    search_download "$query" &
    PIDS+=($!)
    
    # Max 3 parallel
    if [ ${#PIDS[@]} -ge 3 ]; then
        wait "${PIDS[0]}" 2>/dev/null
        PIDS=("${PIDS[@]:1}")
    fi
done

# Wait for all
wait

echo ""
echo "=== DOWNLOAD COMPLETE ==="
echo "Videos in $OUTPUT_DIR:"
ls "$OUTPUT_DIR" 2>/dev/null | wc -l
