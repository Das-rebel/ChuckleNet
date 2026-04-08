# Cognitive Pipeline Integration Test Results

## Test Configuration
- **Training Data**: 50 examples (subset from `standup_word_level/train.jsonl`)
- **Validation Data**: 20 examples (subset from `standup_word_level/valid.jsonl`)
- **Epochs**: 3
- **Embedding Dim**: 64
- **Hidden Dim**: 64
- **Batch Size**: 8
- **Learning Rate**: 1e-4

## Training Metrics

| Epoch | Train Loss | Train F1 | Train Precision | Train Recall | Valid Loss | Valid F1 | Valid Precision | Valid Recall |
|-------|------------|----------|-----------------|--------------|------------|----------|-----------------|--------------|
| 1     | 0.6901     | 0.7013   | 1.0000          | 0.5400       | 0.6748     | 1.0000   | 1.0000          | 1.0000       |
| 2     | 0.6625     | 1.0000   | 1.0000          | 1.0000       | 0.6475     | 1.0000   | 1.0000          | 1.0000       |
| 3     | 0.6323     | 1.0000   | 1.0000          | 1.0000       | 0.6151     | 1.0000   | 1.0000          | 1.0000       |

**Best Validation F1**: 1.0000

## Component Activity Summary

### All 4 Cognitive Components Verified Active

| Component | Output Key | Mean Value | Range | Status |
|-----------|------------|------------|-------|--------|
| **ToM** (Theory of Mind) | `tom.humor_prediction` | 0.4991 | 0.4991-0.4991 | Active |
| **GCACU** (Incongruity) | `gcacu.incongruity_score` | 0.4579 | 0.4501-0.4618 | Active |
| **CLoST** (Thought Leaps) | `clost_probability` | 0.5223 | 0.5217-0.5230 | Active |
| **SEVADE** (Architecture) | `sevade.logits` | -0.0443 | -0.0539 to -0.0323 | Active |

### ToM Mental States Structure
The ToM component produces the following mental state outputs:
- `audience_belief`
- `audience_expectation`
- `comedian_intent`
- `comedian_belief`
- `fused_mental_state` (shape: [1, 64])

## Issues Found

### 1. Uniform Component Outputs
The cognitive components produce very uniform outputs across examples:
- ToM: 0.4991 (nearly identical for all examples)
- GCACU: ~0.46 (low variance)
- CLoST: ~0.52 (low variance)

**Cause**: The `DeterministicTextEmbedder` uses hash-based random embeddings that do not capture semantic meaning. The cognitive components receive essentially similar inputs regardless of actual humor content.

**Impact**: Components are not yet learning to distinguish humorous vs non-humorous content at the embedding level. Real improvements will require:
1. Using a proper pre-trained language model (e.g., XLM-R) for embeddings
2. Training on larger datasets

### 2. Perfect Validation F1
The validation F1 of 1.0 is likely due to:
- Small dataset size (20 examples)
- Random embeddings causing random predictions
- Possible label leakage through hash-based encoding

**Recommendation**: Test on larger held-out dataset with proper semantic embeddings.

## Success Criteria Status

| Criteria | Status | Notes |
|----------|--------|-------|
| Pipeline runs without errors | PASS | Completed 3 epochs successfully |
| Cognitive model produces F1 > baseline | INCONCLUSIVE | F1=1.0 on small dataset; baseline not computed |
| All 4 components active | PASS | ToM, CLoST, SEVADE, GCACU all producing outputs |

## Files Generated
- Model checkpoint: `/tmp/cog_output/best_model/cognitive_model.pt`
- Training summary: `/tmp/cog_output/training_summary.json`

## Next Steps
1. Run with proper XLM-R embeddings instead of hash-based embeddings
2. Test on larger dataset (full training/validation split)
3. Compute baseline XLM-R F1 for comparison
4. Add component-specific loss terms to encourage differentiation
