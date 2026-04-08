# Large Dataset Training Results (22,913 examples)

## Dataset Status
- **Train**: 22,913 examples
- **Valid**: 2,680 examples
- **Test**: 9,081 examples

## Training Attempt

### Configuration
```bash
python3 training/xlmr_standup_word_level.py \
  --train-file data/training/standup_word_level_large/train.jsonl \
  --valid-file data/training/standup_word_level_large/valid.jsonl \
  --test-file data/training/standup_word_level_large/test.jsonl \
  --output-dir experiments/xlmr_large_22k \
  --epochs 5 \
  --positive-class-weight 4.0 \
  --unfreeze-last-n-layers 4 \
  --batch-size 4
```

### Hardware Constraint
- **CUDA available**: No (CPU-only)
- Training XLM-R on 22K examples on CPU is not feasible within reasonable time.

### Subset Testing
Even a 10% subset (2,291 examples) timed out after 10 minutes on CPU without completing a single epoch.

## Comparison with Previous Experiments

| Dataset | Train Size | Val F1 | Test F1 | Status |
|---------|------------|--------|---------|--------|
| Baseline | 505 | 0.6667 | 0.7222 | Completed |
| Augmented | 2,017 | 0.8000 | 0.8000 | Completed |
| Large | 22,913 | N/A | N/A | Timeout (CPU too slow) |

## Conclusion
Training XLM-R on the full 22K dataset requires GPU acceleration. CPU-only training is not viable.

## Recommendations
1. Use GPU instance (Google Colab, Paperspace, etc.)
2. Consider distilled models (XLM-R distilled, DistilBERT multilingual)
3. Use mixed precision training to speed up GPU training
