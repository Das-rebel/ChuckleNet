#!/bin/bash
# MASTER: Run all 3 parts in sequence or parallel
# Usage: ./00_MASTER_RUN.sh [part]
# Parts: 1=download, 2=improve_labels, 3=train

PART=${1:-all}

echo "=== CHUCKLENET 1000+ PIPELINE ==="
echo "Part: $PART"
echo ""

case $PART in
    1)
        echo "Running PART 1: Download Gillick 600..."
        bash data_collection/01_download_gillick.sh
        ;;
    2)
        echo "Running PART 2: Improve Labels..."
        bash data_collection/02_improve_labels.sh
        ;;
    3)
        echo "Running PART 3: Train Model..."
        bash data_collection/03_combine_and_train.sh
        ;;
    all)
        echo "Running ALL parts in parallel..."
        echo "NOTE: Part 3 depends on Parts 1 & 2"
        echo ""
        echo "Step 1: Starting Gillick download (background)..."
        nohup bash data_collection/01_download_gillick.sh > /tmp/part1.log 2>&1 &
        P1_PID=$!
        echo "Part 1 PID: $P1_PID"
        echo "Log: /tmp/part1.log"
        echo ""
        echo "Step 2: Starting label improvement (background)..."
        nohup bash data_collection/02_improve_labels.sh > /tmp/part2.log 2>&1 &
        P2_PID=$!
        echo "Part 2 PID: $P2_PID"
        echo "Log: /tmp/part2.log"
        echo ""
        echo "Monitor with: tail -f /tmp/part1.log /tmp/part2.log"
        echo "After complete: bash data_collection/03_combine_and_train.sh"
        ;;
esac
