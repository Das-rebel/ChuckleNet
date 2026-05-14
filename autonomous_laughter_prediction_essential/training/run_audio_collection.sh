#!/bin/bash
# V9 Audio Data Collection - Quick Start
# Usage: bash training/run_audio_collection.sh "Dave Chappelle" 5

COMEDIAN="${1:-Dave Chappelle}"
MAX_VIDEOS="${2:-5}"
MODEL="${3:-base}"

echo "============================================================"
echo "V9 AUDIO DATA COLLECTION"
echo "============================================================"
echo "Comedian: $COMEDIAN"
echo "Max Videos: $MAX_VIDEOS"
echo "Whisper Model: $MODEL"
echo ""

# Check dependencies
echo "Checking dependencies..."

if ! command -v ffmpeg &> /dev/null; then
    echo "❌ ffmpeg not found. Install with: brew install ffmpeg"
    exit 1
fi

if ! command -v yt-dlp &> /dev/null; then
    echo "❌ yt-dlp not found. Install with: brew install yt-dlp"
    exit 1
fi

if ! python3 -c "import whisper" &> /dev/null; then
    echo "❌ whisper not found. Install with: pip install openai-whisper"
    exit 1
fi

echo "✅ All dependencies found"
echo ""

# Create data directories
DATA_DIR="data/audio_comedy"
mkdir -p "$DATA_DIR/audio" "$DATA_DIR/transcripts"

# Run collection
echo "Starting audio collection..."
python3 training/audio_data_collector.py \
    --comedian "$COMEDIAN" \
    --max_videos $MAX_VIDEOS \
    --model $MODEL \
    --data_dir "$DATA_DIR"

# Check results
MANIFEST="$DATA_DIR/${COMEDIAN,,}.replace(' ', '_')_manifest.json"
if [ -f "$MANIFEST" ]; then
    echo ""
    echo "============================================================"
    echo "✅ Collection complete!"
    echo "============================================================"
    cat "$MANIFEST" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Videos processed: {d[\"videos_processed\"]}'); print(f'Audio files: {len(d[\"audio_files\"])}')"
else
    echo ""
    echo "❌ Collection may have failed. Check manifest."
fi
