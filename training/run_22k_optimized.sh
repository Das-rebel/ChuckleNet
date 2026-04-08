#!/bin/bash
# Optimized training script for 22k examples with early stopping and faster settings
#
# Parameters:
#   - early_stopping_patience=2
#   - batch_size=16
#   - gradient_accumulation_steps=4
#   - max_length=128
#   - epochs=3

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

python3 "$SCRIPT_DIR/xlmr_standup_word_level.py" \
    --train-file "$SCRIPT_DIR/../data/training/standup_word_level_large/train.jsonl" \
    --valid-file "$SCRIPT_DIR/../data/training/standup_word_level_large/valid.jsonl" \
    --test-file "$SCRIPT_DIR/../data/training/standup_word_level_large/test.jsonl" \
    --output-dir "$SCRIPT_DIR/../experiments/xlmr_large_22k" \
    --batch-size 16 \
    --gradient-accumulation-steps 4 \
    --max-length 128 \
    --epochs 3 \
    --early-stopping-patience 2 \
    --positive-class-weight 4.0 \
    --unfreeze-last-n-layers 4
