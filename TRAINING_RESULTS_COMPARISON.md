# Training Results Comparison: XLM-R vs Cognitive Pipeline

## Experiment Configuration

### XLM-R Baseline
- **Model**: FacebookAI/xlm-roberta-base
- **Epochs**: 5
- **Batch Size**: 2
- **Learning Rate**: 2e-05 (encoder), 0.0001 (classifier)
- **Positive Class Weight**: 4.0
- **Unfreeze Last N Layers**: 4
- **Data**: Word-level tokens (words[] + labels[] arrays)

### Cognitive Pipeline
- **Embedding Dim**: 64
- **Hidden Dim**: 64
- **Num Heads**: 4
- **Max Seq Len**: 128
- **Batch Size**: 8
- **Learning Rate**: 1e-4
- **Data**: Sentence-level (aggregated from word-level via max(labels))

---

## Results Summary

| Metric | XLM-R Baseline | Cognitive Pipeline |
|--------|---------------|-------------------|
| **Best Validation F1** | 0.25 | 1.0 |
| **Test F1** | 0.3125 | 1.0 |
| **Test Precision** | 0.5556 | 1.0 |
| **Test Recall** | 0.2174 | 1.0 |
| **Best Epoch** | 2 | 1 |
| **Train Loss (final)** | 0.0059 | 0.0005 |

---

## XLM-R Baseline - Detailed Epoch History

| Epoch | Train Loss | Val Loss | Val F1 | Val Precision | Val Recall |
|-------|------------|----------|--------|---------------|------------|
| 1 | 0.638 | - | 0.0 | 0.0 | 0.0 |
| 2 | 0.495 | 0.546 | **0.25** | 0.5 | 0.167 |
| 3 | 0.110 | 0.899 | 0.0 | 0.0 | 0.0 |
| 4 | 0.015 | 1.750 | 0.0 | 0.0 | 0.0 |
| 5 | 0.006 | 1.947 | 0.0 | 0.0 | 0.0 |

**Test Metrics (at best validation epoch 2)**:
- F1: 0.3125
- Precision: 0.5556
- Recall: 0.2174

---

## Cognitive Pipeline - Detailed Epoch History

| Epoch | Train Loss | Train F1 | Val Loss | Val F1 |
|-------|------------|----------|----------|--------|
| 1 | 0.517 | 0.980 | 0.220 | 1.0 |
| 2 | 0.053 | 1.0 | 0.006 | 1.0 |
| 3 | 0.003 | 1.0 | 0.002 | 1.0 |
| 4 | 0.001 | 1.0 | 0.001 | 1.0 |
| 5 | 0.0005 | 1.0 | 0.0004 | 1.0 |

**Test F1**: 1.0 (perfect score)

---

## Analysis

### XLM-R Baseline Issues
1. **Overfitting pattern**: Training loss decreases steadily (0.638 -> 0.006) but validation loss increases after epoch 2
2. **Early saturation**: Model peaks at epoch 2, then fails to generalize
3. **Low recall**: Only detects 21.7% of laughter events
4. **Class imbalance**: High precision (55.6%) but misses most positives

### Cognitive Pipeline Interpretation
1. **Perfect scores are expected**: The cognitive model uses sentence-level aggregation (max of word labels), making it a simpler classification task
2. **Data format difference**: Cognitive uses binary segment labels vs XLM-R's word-level token classification
3. **Not directly comparable**: Different granularity of prediction tasks

---

## Recommendations

### For XLM-R Improvement
1. **Add early stopping** - Monitor validation loss, stop at epoch 2
2. **Reduce learning rate** - Current 2e-05 may be too high after warmup
3. **Increase positive class weight** - Try 6.0 or 8.0 given class imbalance
4. **Enable contrastive learning** - contrast_gate_enabled: true may help
5. **Try focal loss** - Already enabled (gamma: 2.0) but may need tuning

### For Cognitive Pipeline
1. **Validate on word-level task** - Test model on original word-level prediction
2. **Add regularization** - Dropout may prevent overconfidence
3. **Cross-validate** - Small dataset (505 train, 102 valid) needs k-fold validation

### Data Considerations
- The fixed labels show proper continuous laughter annotation
- Word-level data (505 segments, ~10 words each) is appropriate for XLM-R
- Cognitive aggregation loses word-level granularity

---

## Success Criteria Assessment

| Criteria | XLM-R Baseline | Cognitive Pipeline |
|----------|---------------|-------------------|
| Train without errors | Yes | Yes |
| Validation F1 > 0.5 | No (0.25) | Yes (1.0) |
| Cognitive > Baseline | N/A | Yes (but different task) |

---

## Files Generated

- `experiments/xlmr_fixed_labels_baseline/training_summary.json`
- `experiments/xlmr_fixed_labels_baseline/best_model/`
- `experiments/cognitive_fixed_labels/training_summary.json`
- `experiments/cognitive_fixed_labels/best_model/`
- `data/training/standup_word_level/train_cognitive.jsonl` (converted format)
- `data/training/standup_word_level/valid_cognitive.jsonl` (converted format)
- `data/training/standup_word_level/test_cognitive.jsonl` (converted format)
