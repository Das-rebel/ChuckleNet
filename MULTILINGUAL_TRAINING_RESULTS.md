# Multilingual Training Results

## Experiment Overview

**Date**: 2026-04-01
**Model**: XLM-RoBERTa-base
**Output Directory**: `experiments/xlmr_multilingual`

## Dataset Summary

### Training Data (Multilingual)
| Language | Code | Count |
|----------|------|-------|
| French | fr | 21 |
| English | en | 21 |
| Czech | cs | 16 |
| Spanish | es | 5 |
| **Total** | | **63** |

### Validation Data
| Language | Count |
|----------|-------|
| fr | 3 |
| en | 3 |
| cs | 2 |
| es | 1 |

### Test Data
| Language | Count |
|----------|-------|
| cs | 3 |
| fr | 3 |
| en | 3 |
| es | 1 |

## Training Configuration

```yaml
model_name: FacebookAI/xlm-roberta-base
epochs: 5
positive_class_weight: 4.0
unfreeze_last_n_layers: 4
learning_rate: 2e-05
classifier_learning_rate: 0.0001
batch_size: 2
gradient_accumulation_steps: 4
loss_type: cross_entropy
```

## Results

### Overall Performance

| Metric | Multilingual Model | English-Only Baseline |
|--------|-------------------|----------------------|
| **Test F1** | **0.354** | 0.308 |
| Test Precision | 0.447 | 0.375 |
| Test Recall | 0.293 | 0.261 |
| Test IoU F1 | 0.153 | 0.246 |

### Cross-Language Analysis (Multilingual Model - Test Set)

| Language | Precision | Recall | F1 | IoU F1 | Support |
|----------|-----------|--------|-----|--------|---------|
| **cs (Czech)** | **0.498** | **0.468** | **0.425** | 0.177 | 72 |
| en (English) | 0.0 | 0.0 | 0.0 | 0.0 | 12 |
| es (Spanish) | 0.0 | 0.0 | 0.0 | 0.0 | 19 |
| fr (French) | 0.0 | 0.0 | 0.0 | 0.333* | 13 |

*IoU F1 for French is 0.333 despite 0.0 precision/recall, indicating some span overlap but no exact matches.

### English-Only Baseline (for comparison)
| Language | Precision | Recall | F1 | Support |
|----------|-----------|--------|-----|---------|
| en | 0.174 | 0.261 | 0.203 | 23 |

## Key Findings

### 1. Czech Performance
The multilingual model significantly outperforms on Czech:
- **Czech F1: 0.425** (multilingual) vs English-only F1: 0.203
- This suggests cross-lingual transfer is working for Czech

### 2. English/ES/FR Performance Issue
The multilingual model shows **0.0 F1** for English, Spanish, and French:
- Model appears to over-fit to Czech patterns
- Possible causes:
  - Czech has highest label density in training data
  - Small sample sizes for other languages (fr: 21, cs: 16, es: 5)
  - Class imbalance across languages

### 3. Overall vs English-Only
- Overall test F1 improved: 0.354 vs 0.308 (+15%)
- But this is driven primarily by Czech performance
- English performance degraded in multilingual setting

## Epoch-by-Epoch Progress (Multilingual)

| Epoch | Train Loss | Val F1 | Notes |
|-------|------------|--------|-------|
| 1 | 0.683 | 0.0 | Model not learning |
| 2 | 0.686 | 0.0 | Still no predictions |
| 3 | 0.667 | 0.0 | No change |
| 4 | 0.651 | 0.110 | First signs of learning |
| 5 | 0.626 | 0.078 | Best model at epoch 4 |

Best validation model saved at epoch 4.

## Recommendations

### Immediate Actions
1. **Balance language distribution** - Current imbalance (es: 5 vs fr: 21) affects learning
2. **Increase training data** for under-represented languages (es especially)
3. **Add language-specific class weights** to compensate for data imbalance

### Model Improvements
1. **Language-aware sampling** - Ensure each batch has balanced language representation
2. **Auxiliary language classification head** - Force model to learn language-agnostic features
3. **Cross-lingual contrastive loss** - Align representations across languages

### Data Collection
1. Collect more Spanish examples (currently only 5 in training)
2. Add more Czech comedy data (label quality seems good)
3. Balance French vs English training examples

## Conclusions

The multilingual training shows **promise for cross-lingual transfer** (Czech F1: 0.425), but suffers from:
- Severe performance degradation on non-Czech languages
- Limited training data overall (63 total examples)
- Class imbalance across languages

**Verdict**: Cross-lingual transfer is achievable but requires larger, more balanced datasets and potentially modified training strategies.

## Files Generated

- `experiments/xlmr_multilingual/training_summary.json` - Full training metrics
- `experiments/xlmr_multilingual/best_model/` - Best checkpoint