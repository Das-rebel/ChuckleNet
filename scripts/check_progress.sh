#!/bin/bash
# Quick progress check

OUTPUT_DIR="/Users/Subho/autonomous_laughter_prediction_essential/data/utterances/vtt_frames"
TOTAL_VIDEOS=626

echo "📊 EXTRACTION PROGRESS CHECK"
echo "=============================="
echo "Timestamp: $(date)"
echo ""

# Check process
PID=$(ps aux | grep extract_vtt_wavlm_frames_prod | grep -v grep | awk '{print $2}')
if [ -n "$PID" ]; then
    echo "✓ Process running (PID: $PID)"
    CPU=$(ps -p $PID -o %cpu | tail -1)
    MEM=$(ps -p $PID -o %mem | tail -1)
    ELAPSED=$(ps -p $PID -o etime | tail -1)
    echo "  CPU: $CPU% | Memory: $MEM% | Time: $ELAPSED"
else
    echo "✗ Process not running"
fi

echo ""

# Check progress
if [ -d "$OUTPUT_DIR" ]; then
    VIDEO_COUNT=$(find "$OUTPUT_DIR" -name "*.npy" | wc -l | tr -d ' ')
    PERCENT=$(echo "scale=1; $VIDEO_COUNT * 100 / $TOTAL_VIDEOS" | bc)
    echo "📁 Progress: $VIDEO_COUNT/$TOTAL_VIDEOS ($PERCENT%)"
    
    if [ "$VIDEO_COUNT" -gt 0 ]; then
        # Calculate ETA
        if [ -n "$ELAPSED" ]; then
            ELAPSED_SECONDS=$(echo "$ELAPSED" | awk -F: '{print $1*60 + $2}')
            if [ "$ELAPSED_SECONDS" -gt 0 ] && [ "$VIDEO_COUNT" -gt 0 ]; then
                AVG_TIME=$((ELAPSED_SECONDS / VIDEO_COUNT))
                REMAINING=$((TOTAL_VIDEOS - VIDEO_COUNT))
                ETA_SECONDS=$((AVG_TIME * REMAINING))
                ETA_HOURS=$((ETA_SECONDS / 3600))
                ETA_MINUTES=$(((ETA_SECONDS % 3600) / 60))
                echo "⏱️  ETA: ~${ETA_HOURS}h ${ETA_MINUTES}m"
            fi
        fi
    fi
fi

echo ""
echo "📂 Data directory: $OUTPUT_DIR"
echo "📋 Monitor log: tail -f /tmp/monitoring.log"
