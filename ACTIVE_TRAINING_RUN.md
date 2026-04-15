# Active Training Run - TEST_001

**Serial:** TEST_001
**Date:** 2026-04-16
**Status:** IN PROGRESS

## Quick Status

| Metric | Value |
|--------|-------|
| Batch | 2000/37043 (~5%) |
| Epoch | 1/3 |
| Loss | 0.23 |
| Speed | 1.6 batches/s |
| Time Elapsed | ~20 min |
| ETA | ~18 hours total |

## Key Config: classifier_lr=1e-4

This run uses the insight from best experiment (`xlmr_standup_baseline_weak_pos5` with F1=0.8194):
- **classifier_learning_rate: 1e-4** (10x encoder LR)
- This was the critical differentiator in the best result

## Training Command

```bash
cd /Users/Subho/autonomous_laughter_prediction
caffeinate -i -s -u -- python3 -u training/train_with_turboquant.py \
  --train-file data/training/final_multilingual_v3/train.jsonl \
  --valid-file data/training/final_multilingual_v3/valid.jsonl \
  --output-dir experiments/xlmr_biosemiotic_track_v1 \
  --batch-size 4 --epochs 3 --learning-rate 2e-5 \
  --classifier-learning-rate 1e-4 \
  --gradient-accumulation-steps 2 \
  --freeze-encoder-epochs 1 --unfreeze-last-n-layers 2 \
  --positive-class-weight 5.0 --max-length 256 \
  --differentiated-threshold --checkpoint-every 10000
```

## Full Config

| Parameter | Value |
|-----------|-------|
| model | xlm-roberta-base |
| batch_size | 4 |
| gradient_accumulation | 2 (effective 8) |
| epochs | 3 |
| encoder_lr | 2e-5 |
| classifier_lr | 1e-4 |
| freeze_encoder_epochs | 1 |
| unfreeze_last_n_layers | 2 |
| pos_weight | 5.0 |
| turboquant | 3-bit |
| diff_threshold | enabled |

## Checkpoints

- Location: `experiments/xlmr_biosemiotic_track_v1/`
- Every 10,000 batches
- Resume: `--resume-from experiments/xlmr_biosemiotic_track_v1/checkpoint_batch_XXXX`

## Notes

- Disk cleanup performed (freed 3GB)
- LoRA code removed (dead code)
- Previous best F1: 0.8194 from `xlmr_standup_baseline_weak_pos5`
