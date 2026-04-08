# F1-Based Early Stopping Results

Date: 2026-04-02

## Change Made

Modified early stopping from **IoU-F1 based** to **F1 based** in `training/xlmr_standup_word_level.py`:

- **Before**: Saved model when IoU-F1 improved
- **After**: Saves model when F1 improves

## Results with F1-Based Early Stopping

| Epoch | F1 | IoU-F1 | Train Loss |
|-------|-----|--------|------------|
| 1 | 0.0000 | 0.8959 | 0.4147 |
| 2 | 0.0000 | 0.8959 | 0.1186 |
| 3 | **0.2663** | 0.8993 | 0.0432 |

**Final (best) validation metrics:**
- F1: **0.2663**
- IoU-F1: 0.8993
- Test F1: **0.1885**
- Test IoU-F1: 0.7308

## Analysis

### Why Results Are Same as IoU-F1 Based

The previous run (with IoU-F1 based early stopping) also saved the epoch 3 checkpoint because:
1. Epoch 1 & 2: IoU-F1=0.896, F1=0.0
2. Epoch 3: IoU-F1=0.899, F1=0.266

Epoch 3 had **both** higher IoU-F1 AND higher F1, so both strategies save the same checkpoint.

### Key Insight: Model Struggles to Learn

The model predicted **zero positives** for the first 2 epochs:
- Training loss dropped from 0.41 → 0.12 → 0.04 (learning)
- But F1 stayed at 0.0 for 2 epochs
- Only at epoch 3 did it start predicting positives

This indicates the **augmented data is semantically difficult** - the model couldn't find useful signal until epoch 3.

### Why Augmented Data Underperforms

Comparing original (505) vs augmented (5k):

| Dataset | Val F1 | Val IoU-F1 | Test F1 | Test IoU-F1 |
|---------|--------|------------|---------|-------------|
| Original 505 | **0.6667** | 0.5000 | **0.7222** | 0.5652 |
| Augmented 5k | 0.2663 | **0.8993** | 0.1885 | **0.7308** |

- **Original**: Higher F1, lower IoU-F1 (balanced predictions)
- **Augmented**: Lower F1, higher IoU-F1 (overly conservative, predicts few positives)

The augmented data causes:
1. **Harder learning**: 2 epochs of zero positive predictions
2. **Overfitting**: High IoU-F1 but low F1 (confident but wrong)
3. **No generalization**: Model memorizes training patterns

## Recommendations

1. **Quality > Quantity**: Original 505 examples outperform 5k augmented
2. **Fix data quality first**: Automated augmentation introduces noise
3. **Use Adaptive Focal Loss**: Framework doc recommends this for noisy labels
4. **Implement GCACU**: Explicit incongruity modeling may help
5. **Consider data filtering**: Remove low-quality augmented examples

## Next Steps

Per the framework document, the path forward is:
1. Focus on data quality, not quantity
2. Implement GCACU for contrastive learning
3. Use Adaptive Focal Loss for noisy label handling
4. The 505 original dataset remains the best training base
