# Cognitive Pipeline Large Data Results

## Experiment Overview

**Date**: 2026-04-01
**Data**: 22,913 train / 2,680 validation examples (large word-level dataset)
**Cognitive Config**: embedding_dim=128, hidden_dim=128, num_heads=4, max_seq_len=128

## Cognitive Model Results

### Training Progress
| Epoch | Train Loss | Train F1 | Valid Loss | Valid F1 |
|-------|------------|----------|------------|----------|
| 1     | 0.5514     | 0.0021   | 0.4343     | 0.0000   |
| 2     | 0.5403     | 0.0606   | 0.4124     | 0.0481   |
| 3     | ~0.53      | ~0.08    | ~0.41      | ~0.05    |

### Final Metrics
- **Validation F1**: ~0.048
- **Validation Loss**: ~0.41
- **Model**: experiments/cognitive_large/best_model/cognitive_model.pt

## XLM-R Baseline Comparison (Same Data Scale)

From `xlmr_standup_lexical_tail_pos4` experiment (comparable config):
- **Validation F1**: 0.40
- **Validation Loss**: 0.694
- **Test F1**: 0.50

## Analysis

### Cognitive Model Issues
1. **Very low F1 scores** (~0.05 vs 0.40 for XLM-R)
2. The sentence-level aggregation (joining words into text) loses word-level precision
3. Using last-token label as segment label is a crude approximation
4. Simple transformer architecture may lack capacity for humor detection

### Why Cognitive Underperforms
1. **Data Format Mismatch**: Word-level laughter prediction != sentence-level classification
2. **Label Strategy**: Majority voting at segment level loses granular signals
3. **Architecture**: 128-dim embeddings may be insufficient for semantic humor detection
4. **Task Difference**: Cognitive pipeline is designed for sentence embedding similarity, not序列 labeling

## Recommendation

The cognitive pipeline does NOT help with laughter prediction on this data. XLM-R baseline significantly outperforms.

### Next Steps
- Return to word-level models (XLM-R with sequence labeling)
- Focus on improving label quality rather than cognitive components
- Consider cognitive features as auxiliary input to XLM-R rather than standalone