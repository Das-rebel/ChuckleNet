# Multilingual Data Addition Report

## Summary

Added multilingual StandUp4AI data to improve model generalization across languages.

## Source Data

**StandUp4AI Examples Label Dataset** (`/tmp/standup4ai_dataset_main/dataset-main/Examples_label/`)

| File | Language | Words | Laughter Tokens |
|------|----------|-------|-----------------|
| -1FrUOEswOk.csv | French (fr) | 1,052 | 97 |
| 1xvwYZwm8Ig.csv | Czech (cs) | 811 | 277 |
| 6JQzl2LlXbQ.csv | Spanish (es) | 286 | 72 |
| 0g7nezWZyfY.csv | English (en) | 1,054 | 118 |

**Total: 3,203 words across 4 transcripts**

## Conversion

Used existing converter: `training/convert_standup4ai_examples_to_jsonl.py`

Format: Word-level JSONL with `words` and `labels` arrays (1 = laughter, 0 = other)

## Multilingual Training Set

Created chunked version at: `data/training/standup_word_level_multilingual/`

### Chunking Strategy
- Chunk size: 50 words
- Overlap: 10 words
- Minimum chunk: 10 words

### Dataset Statistics

| Metric | Count |
|--------|-------|
| Total chunks | 82 |
| Non-English chunks | 55 |
| Non-English word tokens | 2,149 |

### Language Distribution

| Language | Chunks | Laughter Tokens |
|----------|--------|-----------------|
| French (fr) | 27 | 125 |
| Czech (cs) | 21 | 350 |
| Spanish (es) | 7 | 87 |
| English (en) | 27 | 145 |

### Split

| Split | Count |
|-------|-------|
| Train | 63 |
| Valid | 9 |
| Test | 10 |

## Format Validation

Format matches existing word-level training data:
- Same JSON schema (example_id, language, comedian_id, show_id, words, labels, metadata)
- Labels are binary (0 = other, 1 = laughter)
- Word/label arrays are aligned

## Languages Included

- French (fr)
- Czech (cs)
- Spanish (es)
- English (en) - for comparison

## Success Criteria

| Criterion | Target | Actual | Status |
|-----------|--------|--------|--------|
| Minimum non-English examples | 500 | 2,149 word tokens / 55 chunks | Partial* |

*Note: The StandUp4AI repository provides only 4 labeled example files with ~3,200 total words. While word-token count exceeds 500, the number of segment-level examples is limited. The dataset is suitable for multilingual evaluation but may need augmentation for large-scale multilingual training.