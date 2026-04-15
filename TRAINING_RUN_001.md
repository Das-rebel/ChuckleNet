# Training Run #001: xlmr_biosemiotic_track_v1

**Date:** 2026-04-16
**Status:** IN PROGRESS (Epoch 1/3)
**Serial:** TEST_001

## Training Configuration

| Parameter | Value | Notes |
|-----------|-------|-------|
| model_name | FacebookAI/xlm-roberta-base | Base XLM-R |
| batch_size | 4 | |
| max_length | 256 | |
| epochs | 3 | |
| learning_rate | 2e-5 | Base LR for encoder |
| classifier_learning_rate | 1e-4 | 10x base LR (key insight from best exp) |
| gradient_accumulation_steps | 2 | Effective batch = 8 |
| freeze_encoder_epochs | 1 | Frozen first epoch |
| unfreeze_last_n_layers | 2 | Then unfreeze last 2 layers |
| positive_class_weight | 5.0 | Class imbalance handling |
| use_turboquant | True | 3-bit KV cache compression |
| use_differentiated_threshold | True | Per-head thresholds |
| checkpoint_every | 10000 | Saves disk space |

## Dataset

| Split | Count |
|-------|-------|
| train | 148,169 |
| valid | 10,327 |
| test | 10,329 |

**Data path:** `data/training/final_multilingual_v3/`

## Key Insights from Previous Experiments

### Best Previous Result
- **F1: 0.8194** from `xlmr_standup_baseline_weak_pos5`
- Used `classifier_lr=1e-4`, `unfreeze_last=2`, `pos_weight=5.0`

### Critical Findings
1. **classifier_lr=1e-4** (10x base LR) was critical for best F1
2. Separate learning rate for classifier head significantly helps
3. Frozen encoder + gradual unfreezing works well
4. TurboQuant + differentiated thresholds for memory efficiency

## Current Progress

| Metric | Value |
|--------|-------|
| Current Batch | 2000/37043 |
| Epoch | 1/3 |
| Loss | 0.23 |
| Speed | 1.6 batches/s |
| Checkpoints | Every 10,000 batches |

### Loss Progression
```
Batch 100: 0.34
Batch 500: 0.25
Batch 1000: 0.30
Batch 1500: 0.26
Batch 2000: 0.23
```

## Hardware & Environment

- **Device:** CPU (Mac M2)
- **Memory:** ~945MB used
- **Disk:** 4.9GB free (after cleanup)
- **Sleep Prevention:** caffeinate active

## Command Used

```bash
python3 -u training/train_with_turboquant.py \
  --train-file data/training/final_multilingual_v3/train.jsonl \
  --valid-file data/training/final_multilingual_v3/valid.jsonl \
  --output-dir experiments/xlmr_biosemiotic_track_v1 \
  --batch-size 4 \
  --epochs 3 \
  --learning-rate 2e-5 \
  --classifier-learning-rate 1e-4 \
  --gradient-accumulation-steps 2 \
  --freeze-encoder-epochs 1 \
  --unfreeze-last-n-layers 2 \
  --positive-class-weight 5.0 \
  --max-length 256 \
  --differentiated-threshold \
  --checkpoint-every 10000
```

## Files

- Training log: `training.log`
- Experiment dir: `experiments/xlmr_biosemiotic_track_v1/`
- Training script: `training/train_with_turboquant.py`

## Next Steps

1. Continue training to completion (~18 hours total)
2. Monitor for crashes (laptop may crash)
3. Checkpoint at batch 10000 for resume capability
4. Evaluate on test set after training
