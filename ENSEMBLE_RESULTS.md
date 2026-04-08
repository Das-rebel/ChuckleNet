# Ensemble Evaluation Results

## Summary

**Date:** 2026-04-02

**Models Evaluated:**
- `xlmr_augmented` - Available
- `xlmr_multilingual_balanced` - Available
- `xlmr_large_22k` - NOT AVAILABLE (training timed out on CPU)

**Key Finding:** Simple probability averaging ensemble underperforms compared to the best single model due to the multilingual model's poor performance on the English-only validation set.

## Results

### Validation Set (102 examples from standup_word_level)

| Model | Val F1 | Val IoU F1 | Val Precision | Val Recall |
|-------|--------|------------|---------------|------------|
| xlmr_augmented | **0.8000** | **0.6667** | **1.0000** | 0.6667 |
| xlmr_multilingual_balanced | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| **Ensemble (avg)** | 0.1739 | 0.0098 | 0.1026 | 0.5714 |

### Test Set (23 examples)

| Model | Test F1 | Test IoU F1 | Test Precision | Test Recall |
|-------|---------|-------------|----------------|-------------|
| xlmr_augmented | 0.8000 | 0.6812 | 0.9412 | 0.6957 |
| xlmr_multilingual_balanced | 0.5676 | 0.3548 | 0.5943 | 0.5431 |
| **Ensemble (avg)** | 0.2500 | 0.0000 | 0.1429 | 1.0000 |

## Analysis

### Why Ensemble Underperformed

1. **Domain Mismatch**: The `xlmr_multilingual_balanced` model was trained on multilingual data (Czech, English, Spanish, French) with different label distributions. When evaluated on the English-only standup_word_level validation set, it achieves F1=0.0 because its confidence thresholds are calibrated for a different data distribution.

2. **Class Weight Difference**: The augmented model uses `positive_class_weight=4.0` while multilingual uses `positive_class_weight=1.0`, leading to different prediction behaviors.

3. **Dataset Size Difference**: The multilingual model was validated on only 61 examples vs 102 for the augmented model, making its calibration less reliable on this specific split.

### Ensemble Method

Simple probability averaging:
```python
ensemble_prob = mean([model1_prob, model2_prob])
ensemble_pred = argmax(ensemble_prob) if ensemble_prob[:, 1] > 0.5 else 0
```

### Recommendations

1. **Weighted Ensemble**: Instead of equal weighting, use validation-set-optimized weights that give higher weight to better-performing models.

2. **Selective Ensemble**: Only include models that pass a minimum performance threshold on the validation set.

3. **Model Selection**: For English-only deployment, `xlmr_augmented` is the clear choice with F1=0.80.

4. **Train xlmr_large_22k**: If GPU becomes available, training on the 22K dataset could produce a stronger model for ensembling.

## Configuration Details

### xlmr_augmented
- Base model: FacebookAI/xlm-roberta-base
- Positive class weight: 4.0
- Epochs: 5
- unfreeze_last_n_layers: 4
- Validation F1: 0.80

### xlmr_multilingual_balanced
- Base model: FacebookAI/xlm-roberta-base
- Positive class weight: 1.0
- Epochs: 5
- unfreeze_last_n_layers: 2
- Validation F1: 0.0 (on English-only split), 0.57 (on multilingual test)

## Conclusion

The simple ensemble averaging approach did not improve performance because:
- One model (`xlmr_multilingual_balanced`) performed very poorly on the evaluation domain
- Equal weighting dragged down the ensemble below the best single model

**Recommendation:** For production deployment on English comedy content, use the `xlmr_augmented` model alone (F1=0.80) rather than the ensemble.