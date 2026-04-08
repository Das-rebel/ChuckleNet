# Debug Report: StandUp4AI English Slice F1 = 0.0%

Date: 2026-04-01
Phase: 0 - Debug Data Pipeline

## Executive Summary

The 0.0% F1 on StandUp4AI English slice is **NOT a model bug**. The model works correctly on internal data but fails on the benchmark due to a **fundamental data labeling mismatch** between training data and benchmark data.

## Issue 1: Training Data Labeling Bug (CRITICAL)

### Finding
The training data (`data/training/standup_word_level/train.jsonl`) labels are placed on **punctuation marks** instead of actual laughter trigger words.

### Evidence
Analysis of 505 training examples shows:

| Positive Word | Count |
|---------------|-------|
| `"` (double quote) | 162 |
| `!` (exclamation) | 161 |
| `?` (question mark) | 81 |
| yesterday | 21 |
| useless | 20 |
| beach | 20 |
| beer | 20 |
| rain | 17 |

The top 3 positive labels are punctuation marks that account for 80% of all positive labels.

### Root Cause
The training data was created using a flawed heuristic that placed the label on the **last token** of each segment (typically punctuation), which was meant to indicate where the laughter tag appeared in the original transcript. However, this does not represent actual laughter trigger words.

### Impact
The model learns to associate punctuation with "laughter" because that's what the training data says is positive. However, the benchmark expects the model to identify actual speech patterns like "um", "uh", "you know", etc.

## Issue 2: Benchmark Data Labeling (Different Schema)

### Finding
The StandUp4AI benchmark data (`benchmarks/data/standup4ai_examples_en.jsonl`) uses a completely different labeling scheme:

| Positive Words in Benchmark | Example |
|----------------------------|---------|
| um | "i'm trying to watch less porn lately **um** i don't know..." |
| uh | "...all of you **uh** hello..." |
| you | "...perverts **all of you** uh hello..." |
| know | "...don't **know** anyone else..." |
| really | "...**It's really** good..." |

### Key Difference
- **Training data**: Label = position of laughter tag in transcript (usually punctuation)
- **Benchmark data**: Label = actual speech patterns preceding/accompanying laughter

## Issue 3: Model Prediction Analysis

### Finding
When evaluated on the benchmark:
- **Model predicts 0 positive tokens** despite 118 positive labels
- All positive label positions have **deeply negative margins** (e.g., -5.7 to -10.3)
- The model predicts punctuation (`?`, `.`) as positive, but these have `label=-100` (masked)

### Logit Margin Analysis
```
Margin stats: min=-10.328, max=1.448, mean=-5.849

At POSITIVE label positions:
  pos 11: margin=-5.707, word='um', label=1
  pos 12: margin=-8.390, word='i', label=1
  pos 13: margin=-10.101, word='don', label=1
  pos 16: margin=-7.114, word='know', label=1
```

The model is actively predicting AGAINST the truly positive tokens.

## Issue 4: Truncation Issue

### Finding
The English benchmark has 1 example with 1054 words. With `max_length=256`:
- Only 190 tokens are visible after tokenization
- Positive labels in truncated portion are never seen

### Evidence
```
=== LABEL DISTRIBUTION ===
Valid labels count: 190
Positive (1) labels: 23
```

## What Was Working Correctly

1. **JSONL data loading**: All training examples have proper word-label alignment
2. **Tokenization**: XLM-R tokenizer correctly processes words
3. **Label alignment**: `align_word_labels()` correctly maps word labels to token positions
4. **Evaluation pipeline**: Metrics are computed correctly

## Recommendations

### Short-term (Data Alignment)
1. **Re-label training data** to identify actual laughter trigger words instead of using the last-token heuristic
2. **Re-run training** with correctly labeled data
3. **Validate** on benchmark before deployment

### Long-term (Evaluation)
1. **Unified labeling schema** - both training and benchmark should use the same definition of "positive"
2. **Cross-validation** - evaluate on benchmark periodically during training
3. **Debug flag** - use `--debug` flag to monitor prediction distribution during training

## How to Use the Debug Flag

```bash
python3 training/xlmr_standup_word_level.py \
  --train-file data/training/standup_word_level/train.jsonl \
  --valid-file data/training/standup_word_level/valid.jsonl \
  --output-dir experiments/debug_run \
  --debug \
  --epochs 1
```

The debug output will show:
1. Sample word-label pairs from training data
2. Prediction distribution on first batch
3. Per-class prediction counts

## Conclusion

The 0.0% F1 is caused by a **data labeling mismatch**, not a model or evaluation bug. The training data labels punctuation as positive, while the benchmark expects filler words. The fix requires re-labeling the training data with the correct schema.
