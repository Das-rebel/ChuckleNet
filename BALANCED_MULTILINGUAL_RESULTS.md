# Multilingual Data Balancing Results

## Original Distribution
| Language | Count |
|----------|-------|
| Spanish (es) | 5 |
| Czech (cs) | 16 |
| French (fr) | 21 |
| English (en) | 21 |
| **Total** | **63** |

## Balancing Strategy
- **Target**: 100 examples per language
- **Method**: Splice augmentation (combining chunks from different examples while preserving laugh label alignment)
- **Augmented total**: 400 examples

## Training Configuration
- Model: xlm-roberta-base
- Epochs: 5
- Training loss (final): 0.306

## Cross-Language Performance (Validation Set)

| Language | Precision | Recall | F1 | Support |
|----------|-----------|--------|-----|---------|
| **cs** | 0.531 | 0.726 | **0.599** | 72 |
| **en** | 0.333 | 0.167 | **0.222** | 12 |
| **es** | 0.0 | 0.0 | **0.0** | 19 |
| **fr** | 0.333 | 0.056 | **0.095** | 13 |
| **Overall** | 0.594 | 0.543 | **0.568** | 116 |

## Key Findings

### 1. Czech (cs) - Best Performance
- F1: 0.599 (highest among all languages)
- High recall (0.726) indicates model detects Czech laughter well
- Original: 16 examples → balanced to 100

### 2. Spanish (es) - Critical Failure
- F1: 0.0 (completely fails to predict)
- Root cause: Only 5 original examples - augmentation cannot create meaningful new patterns
- **Recommendation**: Need genuine Spanish comedy data, not synthetic augmentation

### 3. English (en) - Moderate
- F1: 0.222 with only 12 validation samples (too small to be significant)

### 4. French (fr) - Poor
- F1: 0.095 despite having 21 original examples
- Possible dialect/genre mismatch with augmentation

## Recommendations

1. **Spanish Data Collection**: Authentic Spanish stand-up comedy data is essential
2. **Cross-Lingual Transfer**: Czech benefits from Slavic language similarity in training
3. **Augmentation Limitations**: Splice augmentation preserves labels but creates unnatural word combinations
4. **Minimum Data Threshold**: ~20 examples per language appears insufficient for quality XLM-R training
