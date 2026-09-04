#!/bin/bash
# Monitor frame extraction progress and notify when complete

OUTPUT_DIR="/Users/Subho/autonomous_laughter_prediction_essential/data/utterances/vtt_frames"
TOTAL_VIDEOS=626
LOG_FILE="/tmp/monitoring.log"

echo "Starting frame extraction monitoring..." | tee -a "$LOG_FILE"
echo "Timestamp: $(date)" | tee -a "$LOG_FILE"

while true; do
    # Check if process is still running
    PID=$(ps aux | grep extract_vtt_wavlm_frames_prod | grep -v grep | awk '{print $2}')
    
    if [ -z "$PID" ]; then
        echo "✗ Extraction process stopped" | tee -a "$LOG_FILE"
        break
    fi
    
    # Check progress
    VIDEO_COUNT=$(find "$OUTPUT_DIR" -name "*.npy" | wc -l | tr -d ' ')
    PERCENT=$(echo "scale=1; $VIDEO_COUNT * 100 / $TOTAL_VIDEOS" | bc)
    
    # Get resource usage
    CPU=$(ps -p $PID -o %cpu | tail -1)
    MEM=$(ps -p $PID -o %mem | tail -1)
    ELAPSED=$(ps -p $PID -o etime | tail -1)
    
    # Log progress
    echo "[$(date +%H:%M:%S)] Progress: $VIDEO_COUNT/$TOTAL_VIDEOS ($PERCENT%) | CPU: $CPU% | MEM: $MEM% | Time: $ELAPSED" | tee -a "$LOG_FILE"
    
    # Check if complete
    if [ "$VIDEO_COUNT" -ge "$TOTAL_VIDEOS" ]; then
        echo "🎉 EXTRACTION COMPLETE!" | tee -a "$LOG_FILE"
        echo "Processed $VIDEO_COUNT videos successfully" | tee -a "$LOG_FILE"
        echo "Timestamp: $(date)" | tee -a "$LOG_FILE"
        
        # Send notification (if possible)
        echo "🚀 Ready to start ultra-optimized training!" | tee -a "$LOG_FILE"
        break
    fi
    
    # Wait 5 minutes before next check
    sleep 300
done

echo "Monitoring stopped at $(date)" | tee -a "$LOG_FILE"
