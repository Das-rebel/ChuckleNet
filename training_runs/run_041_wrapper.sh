#!/bin/bash
# Training Run #41 - Restart with proven working script (train_xlmr_multitask.py) after Run #40 semaphore leak crash
# Started: 2026-04-18 02:45:23

cd /Users/Subho/autonomous_laughter_prediction

# Training with proven working script from Run #39
# Added PYTHONUNBUFFERED=1 to prevent logging issues
PYTHONUNBUFFERED=1 python3 training/train_xlmr_multitask.py \
  --train-file data/training/final_multilingual_v3_bilingual/train.jsonl \
  --valid-file data/training/final_multilingual_v3_bilingual/valid.jsonl \
  --output-dir models/run_041_training \
  --epochs 10 \
  --batch-size 16 \
  --learning-rate 2e-5 \
  --classifier-lr 1e-4 \
  --max-grad-norm 1.0 \
  --early-stopping-patience 3 \
  --device cpu \
  --eval-every-steps 500 \
  > models/run_041_training/training.log 2>&1
