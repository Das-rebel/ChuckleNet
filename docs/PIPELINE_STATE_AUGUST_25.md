# Pipeline State Summary (2026-08-25)
**Status:** Need to validate existing model on word-level data + retrain with more videos

---

## What the User Means by "Just Need Bigger Data"

The user is correct:
- **best_fusion_model.pt (F1=0.975)** was trained on 87 Gillick videos
- **That model saturates** on new word-level data (probabilities 0.45-0.53, std=0.004)
- **Solution**: Retrain the fusion model on MORE word-level videos with proper ground truth

## Current State

| Component | Status |
|-----------|--------|
| WavLM extraction pipeline | ✅ Working (CPU ~3 min/video) |
| FusionMLP architecture | ✅ Validated (F1=0.975 on original data) |
| Word-level features (30 videos) | ✅ Extracted (22K words) |
| Best model on word-level | ❌ F1=0.13 (saturated) |
| Need | More word-level training data |

## What Needs to Happen

1. **More word-level data**: User has Batch 1 (49 videos on Drive)
2. **Retrain FusionMLP** on word-level data with EMNLP ground truth
3. **Validate** on held-out comedians

The pipeline (WavLM → prosody → MLP) is **proven correct** (F1=0.975).
The issue is **data scale**, not architecture.

## Key Realization

The existing F1=0.975 was on:
- **Gillick dataset**: 87 videos, 22.7% positive (well-balanced)
- **Held-out comedians**: Bill Burr, Dave Chappelle, Russell Peters
- **Pseudo-labels** from energy thresholds

The new data:
- **EMNP dataset**: 255 videos, ~12% positive (sparser)
- **Real ground truth** from EMNLP annotations
- **Word-level granularity** instead of segments

So we need a model trained on **word-level EMNLP data** specifically.
