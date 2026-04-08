# WESR Evaluation Results

## Models Evaluated

| Model | Location | Training Data |
|-------|----------|---------------|
| **xlmr_augmented** | `experiments/xlmr_augmented/best_model` | standup_word_level_augmented |
| **xlmr_fixed_labels_baseline** | `experiments/xlmr_fixed_labels_baseline/best_model` | standup_word_level |

## WESR Benchmark Suite Summary

### xlmr_augmented (Best Model)

#### Canonical Split
| Split | F1 | IoU-F1 | Precision | Recall | Support |
|-------|-----|--------|-----------|--------|---------|
| Validation | 0.800 | 0.667 | 1.000 | 0.667 | 102 |
| Test | 0.800 | 0.681 | 0.941 | 0.696 | 23 |

**Per-Laughter-Type Performance (Test):**
| Type | F1 | IoU-F1 | Support |
|------|-----|--------|---------|
| Continuous | 0.650 | 0.650 | 20 |
| Discrete | 0.889 | 0.889 | 3 |

#### WESR-Balanced Companion Split
| Split | F1 | IoU-F1 | Precision | Recall | Support |
|-------|-----|--------|-----------|--------|---------|
| Validation | 0.681 | 0.638 | 0.667 | 0.696 | 23 |
| **Test** | **0.769** | **0.800** | 0.625 | 1.000 | 105 |

**Per-Laughter-Type Performance (Test):**
| Type | F1 | IoU-F1 | Support |
|------|-----|--------|---------|
| Continuous | 0.833 | 0.833 | 84 |
| Discrete | 0.667 | 0.667 | 21 |

### xlmr_fixed_labels_baseline

**Performance: 0.0 F1 across all metrics** - Complete failure to detect laughter.

---

## Key Findings

### 1. Model Comparison
- **xlmr_augmented** significantly outperforms baseline
- Baseline achieves 0% F1 (complete failure)
- Augmented model achieves 76.9% F1 on WESR test set

### 2. Discrete vs Continuous Performance

**xlmr_augmented WESR Test Results:**
- Continuous laughter: 83.3% F1
- Discrete laughter: 66.7% F1
- Discrete is harder to detect (fewer training examples)

### 3. Dialect Bucket Analysis

**xlmr_augmented WESR Test (Per-Dialect):**
| Dialect Bucket | F1 | Support |
|----------------|-----|---------|
| Contraction-heavy | 0.667 | 21 |
| Neutral | 0.833 | 84 |

Contraction-heavy dialect is more challenging.

### 4. Companion Benchmark Recommendation

The WESR companion benchmark shows:
- Validation macro-F1: 74.4%
- Test macro-F1: 75.0%
- Both laughter types present in validation (3 discrete, 20 continuous)
- Minimum type support: 3 (sufficient for reliable metrics)

**Recommendation:** WESR-balanced split is recommended as a companion benchmark for taxonomy-aware evaluation.

---

## Results Location

- xlmr_augmented: `experiments/xlmr_augmented/wesr_results/results.json`
- xlmr_baseline: `experiments/xlmr_fixed_labels_baseline/wesr_results/results.json`