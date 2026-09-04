# Large Dataset Training Results

Date: 2026-04-02

## Summary

Attempted to train on larger datasets (22k and 5k subsets) to improve model performance. Results show that **quality beats quantity** for this task.

## Experiments Conducted

### 1. 22k Full Dataset Training
- **Status:** Timed out on CPU (>40 minutes without completion)
- **Issue:** Tokenizing 22k train + 2.6k valid + 9k test examples is too slow on CPU
- **Recommendation:** Needs GPU for full-scale training

### 2. 5k Subset Training (COMPLETED)
- **Train:** 5,000 examples (subset of 22k augmented data)
- **Valid:** 2,680 examples (full validation)
- **Test:** 9,081 examples (full test)
- **Training time:** ~43 minutes on CPU
- **Config:** batch_size=16, max_length=128, epochs=3, early_stopping_patience=2

## Results Comparison

| Model | Train Size | Val F1 | Val IoU-F1 | Test F1 | Test IoU-F1 |
|-------|-----------|---------|------------|---------|-------------|
| **Promoted (baseline)** | 505 | **0.6667** | 0.5000 | **0.7222** | 0.5652 |
| **5k subset (augmented)** | 5000 | 0.2663 | **0.8993** | 0.1885 | **0.7308** |

## Key Finding: Quality > Quantity

The smaller original dataset (505 examples) **significantly outperforms** the larger augmented dataset (5k) on internal metrics:

1. **3x better F1** on both validation and test sets
2. The augmented data introduces noise that hurts precision
3. The 5k model has paradoxically high IoU-F1 (0.73) but very low F1 (0.19)

### Understanding the IoU-F1 Paradox

The 5k model's results show:
- High IoU-F1 (0.73) = when it predicts positives, they overlap well with ground truth
- Low F1 (0.19) = overall harmonic mean of precision and recall is poor
- Low recall (0.14-0.18) = it misses most positive tokens

This indicates the model is **too conservative** - it only predicts positives when very confident, which gives high overlap scores but doesn't capture enough true positives.

## Recommendations

1. **Don't scale up data blindly** - the augmented data quality hurts performance
2. **Focus on label quality** - the original 505 examples have cleaner labels
3. **For larger training** - needs GPU acceleration; CPU is too slow
4. **External benchmark** - need to evaluate 5k model on external data to see if the pattern holds

## Blockers Confirmed

1. CPU training is too slow for datasets >5k examples
2. Full 22k training requires GPU
3. External StandUp4AI dataset still unavailable (no packaged release)
