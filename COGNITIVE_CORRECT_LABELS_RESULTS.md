# Cognitive Pipeline Results (Correct Labels)

## Training Configuration
- Model: Cognitive Model (ToM + CLoST + SEVADE + GCACU components)
- Embedding: DeterministicTextEmbedder (hash-based random, 128 dim)
- Hidden: 128, Heads: 4
- Epochs: 5, LR: 1e-4

## Data Format Issue
The cognitive_pipeline expects `text` + `label` format but the standard train.jsonl has `words` + `labels` arrays.
Used cognitive-formatted files: `train_cognitive.jsonl`, `valid_cognitive.jsonl`, `test_cognitive.jsonl`

## Results

### Cognitive Model (with correct labels)
| Metric | Train | Valid | Test |
|--------|-------|-------|------|
| Precision | 1.0 | 1.0 | 1.0 |
| Recall | 1.0 | 1.0 | 1.0 |
| F1 | 1.0 | 1.0 | 1.0 |

**Note:** Perfect F1 indicates severe overfitting/memorization.

### XLM-R Baseline (reverted labels, same splits)
| Metric | Train | Valid | Test |
|--------|-------|-------|------|
| Precision | - | 1.0 | 1.0 |
| Recall | - | 0.5 | 0.565 |
| F1 | - | 0.667 | 0.722 |
| IoU-F1 | - | 0.5 | 0.565 |

## Comparison Analysis

### Why Cognitive Model Achieves Perfect F1
1. **Weak Embeddings**: Uses hash-based random embeddings (DeterministicTextEmbedder) vs XLM-R's contextual transformer embeddings
2. **Small Dataset**: 505 train, 102 valid, 23 test (cognitive format) vs much larger word-level data
3. **Memorization**: With random embeddings and high model capacity, the cognitive model can memorize the small training set perfectly

### Fairness of Comparison
**NOT FAIR** - Different datasets used:
- XLM-R: Used `train_refined.jsonl` (word-level format with XLM-R embeddings)
- Cognitive: Used `train_cognitive.jsonl` (reformatted segment-level)

The cognitive model cannot be directly compared to XLM-R because:
1. Different data formats (segment-level vs word-level)
2. Different embedding approaches (random hash vs transformer)
3. Different problem formulations (sentence classification vs token-level prediction)

### IoU-F1 Metric Missing from Cognitive Model
XLM-R reports IoU-F1 (token-level overlap), but cognitive model only computes token-level F1 (exact match). This makes direct comparison impossible.

## Conclusion
The cognitive model showing 1.0 F1 is not meaningful - it's memorizing random embeddings on a tiny dataset. To properly evaluate cognitive components, the model needs:
1. Real semantic embeddings (not hash-based)
2. Evaluation on word-level task (not segment-level)
3. IoU-F1 metric for proper comparison

The cognitive components (ToM, CLoST, SEVADE, GCACU) require integration with proper contextual embeddings to add value over XLM-R baseline.