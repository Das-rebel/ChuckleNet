#!/bin/bash

# Biosemotic BERT Training Monitor
# Checks training status every 5 minutes and logs progress

TRAINING_PID=67895
LOG_FILE="/Users/Subho/autonomous_laughter_prediction/biosemotic_training.log"
OUTPUT_DIR="/Users/Subho/autonomous_laughter_prediction/experiments/biosemotic_humor_bert_base"
MONITOR_LOG="/Users/Subho/autonomous_laughter_prediction/training_monitor.log"

echo "=== Biosemotic Training Monitor Started ===" | tee -a "$MONITOR_LOG"
echo "Monitoring PID: $TRAINING_PID" | tee -a "$MONITOR_LOG"
echo "Check interval: 5 minutes" | tee -a "$MONITOR_LOG"
echo "Started at: $(date)" | tee -a "$MONITOR_LOG"
echo "" | tee -a "$MONITOR_LOG"

while true; do
    echo "=== Training Status Check: $(date) ===" | tee -a "$MONITOR_LOG"

    # Check if process is still running
    if ps -p $TRAINING_PID > /dev/null 2>&1; then
        echo "✅ Process $TRAINING_PID is running" | tee -a "$MONITOR_LOG"

        # Get process stats
        PROCESS_STATS=$(ps -p $TRAINING_PID -o pid,pcpu,pmem,time,command)
        echo "Process Stats:" | tee -a "$MONITOR_LOG"
        echo "$PROCESS_STATS" | tee -a "$MONITOR_LOG"

        # Check for new training log entries
        echo "" | tee -a "$MONITOR_LOG"
        echo "Recent Training Log (last 10 lines):" | tee -a "$MONITOR_LOG"
        tail -10 "$LOG_FILE" | tee -a "$MONITOR_LOG"

        # Check for output files
        echo "" | tee -a "$MONITOR_LOG"
        echo "Output Files:" | tee -a "$MONITOR_LOG"
        FILE_COUNT=$(find "$OUTPUT_DIR" -type f 2>/dev/null | wc -l)
        echo "Files created: $FILE_COUNT" | tee -a "$MONITOR_LOG"

        if [ $FILE_COUNT -gt 0 ]; then
            echo "Files:" | tee -a "$MONITOR_LOG"
            find "$OUTPUT_DIR" -type f 2>/dev/null | head -20 | tee -a "$MONITOR_LOG"
        fi

        # Check for status updates specifically
        echo "" | tee -a "$MONITOR_LOG"
        echo "Checking for STATUS updates..." | tee -a "$MONITOR_LOG"
        STATUS_COUNT=$(grep -c "STATUS" "$LOG_FILE" 2>/dev/null || echo "0")
        echo "Total STATUS entries: $STATUS_COUNT" | tee -a "$MONITOR_LOG"

        # Look for epoch completion
        if grep -q "Epoch 1/" "$LOG_FILE" 2>/dev/null; then
            echo "🎯 EPOCH 1 COMPLETION DETECTED!" | tee -a "$MONITOR_LOG"
        fi

        # Look for progress updates
        PROGRESS_COUNT=$(grep -c "PROGRESS" "$LOG_FILE" 2>/dev/null || echo "0")
        if [ $PROGRESS_COUNT -gt 0 ]; then
            echo "🔄 Progress updates found: $PROGRESS_COUNT" | tee -a "$MONITOR_LOG"
            echo "Latest progress:" | tee -a "$MONITOR_LOG"
            grep "PROGRESS" "$LOG_FILE" | tail -3 | tee -a "$MONITOR_LOG"
        fi

    else
        echo "❌ Process $TRAINING_PID has stopped" | tee -a "$MONITOR_LOG"
        echo "Training completed or crashed at: $(date)" | tee -a "$MONITOR_LOG"

        # Check for final output files
        echo "" | tee -a "$MONITOR_LOG"
        echo "Final Output Files:" | tee -a "$MONITOR_LOG"
        ls -la "$OUTPUT_DIR" 2>/dev/null | tee -a "$MONITOR_LOG"

        # Check final training log
        echo "" | tee -a "$MONITOR_LOG"
        echo "Final Training Log:" | tee -a "$MONITOR_LOG"
        tail -50 "$LOG_FILE" | tee -a "$MONITOR_LOG"

        break
    fi

    echo "" | tee -a "$MONITOR_LOG"
    echo "Next check in 5 minutes..." | tee -a "$MONITOR_LOG"
    echo "========================================" | tee -a "$MONITOR_LOG"
    echo "" | tee -a "$MONITOR_LOG"

    # Sleep for 5 minutes
    sleep 300
done

echo "=== Monitoring Ended ===" | tee -a "$MONITOR_LOG"