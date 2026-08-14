#!/bin/bash
echo "📊 Monitoring GPU extraction status..."
while true; do
    echo "⏰ Checking status - $(date)"
    result=$(python3 -m kaggle kernels list --mine | grep -E "(chucklenet.*gpu|extraction.*11.4x)" | head -1)
    if [[ "$result" == *" "* ]]; then
        echo "✅ Kernel found: $result"
    else
        echo "⏳ Still waiting for execution to start..."
    fi
    sleep 60
done
