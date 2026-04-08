#!/bin/bash
# Monitor Training Progress Script

echo "🎯 GCACU Training Progress Monitor"
echo "================================="
echo ""

TRAINING_PID="40548"
LOG_FILE="autonomous_laughter_prediction/training/turboquant_training.log"

# Check if process is running
if ps -p $TRAINING_PID > /dev/null; then
    echo "✅ Training Process Status: RUNNING (PID: $TRAINING_PID)"
    ps -p $TRAINING_PID -o pid,etime,pcpu,pmem,command
else
    echo "❌ Training Process: NOT RUNNING"
    echo "Please restart training with the deployment script"
    exit 1
fi

echo ""
echo "📊 Latest Training Progress:"
echo "----------------------------"

# Show last 20 lines of training log
if [ -f "$LOG_FILE" ]; then
    tail -20 "$LOG_FILE"
else
    echo "Training log not found: $LOG_FILE"
fi

echo ""
echo "📈 Training Statistics:"
echo "----------------------"

# Extract current batch, loss, and speed
if [ -f "$LOG_FILE" ]; then
    LATEST_BATCH=$(tail -20 "$LOG_FILE" | grep "Batch" | tail -1)
    if [ ! -z "$LATEST_BATCH" ]; then
        echo "$LATEST_BATCH"

        # Extract metrics
        BATCH_NUM=$(echo "$LATEST_BATCH" | grep -oP 'Batch \K[0-9]+')
        TOTAL_BATCHES=$(echo "$LATEST_BATCH" | grep -oP '/\K[0-9]+')
        LOSS=$(echo "$LATEST_BATCH" | grep -oP 'Loss: \K[0-9.]+')
        SPEED=$(echo "$LATEST_BATCH" | grep -oP 'Speed: \K[0-9.]+')

        if [ ! -z "$BATCH_NUM" ] && [ ! -z "$TOTAL_BATCHES" ]; then
            PROGRESS=$(echo "scale=2; $BATCH_NUM / $TOTAL_BATCHES * 100" | bc)
            echo "Progress: ${PROGRESS}%"
        fi
    fi
fi

echo ""
echo "🔧 Quick Commands:"
echo "------------------"
echo "View full log:    tail -f $LOG_FILE"
echo "Stop training:    kill $TRAINING_PID"
echo "Check process:    ps -p $TRAINING_PID"
echo ""
echo "📁 Training output: autonomous_laughter_prediction/models/xlmr_turboquant_training/"