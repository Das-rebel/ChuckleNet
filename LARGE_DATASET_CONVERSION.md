# Large Dataset Conversion Report

## Overview
Converted 139 scraped comedy transcripts from [Scraps From The Loft](https://scrapsfromtheloft.com) into word-level JSONL training format.

**Date:** 2026-04-01
**Source:** `data/raw/scraped_comedy_transcripts.json`
**Output:** `data/training/standup_word_level_large/`

## Conversion Results

| Split | Examples | Positive | Negative | Positive Rate |
|-------|----------|----------|----------|---------------|
| Train | 22,913 | 5,763 | 17,150 | 25.2% |
| Valid | 2,680 | 443 | 2,237 | 16.5% |
| Test | 9,081 | 2,387 | 6,694 | 26.3% |
| **Total** | **34,674** | **8,593** | **26,081** | **24.8%** |

## Success Criteria Status

| Criteria | Target | Actual | Status |
|----------|--------|--------|--------|
| Minimum training examples | 2,000 | 22,913 | PASS |
| Proper JSONL format | Yes | Yes | PASS |
| No split overlap | 0 overlaps | 0 overlaps | PASS |

## Schema Validation
Schema matches existing `standup_word_level` format exactly:
- `example_id`: Unique identifier per example
- `language`: "en" for all
- `comedian_id`: Derived from transcript URL
- `show_id`: Same as comedian_id for scraped data
- `words`: Tokenized word list
- `labels`: Binary labels (1 = followed by laughter)
- `metadata`: Source info, laughter tag, conversion mode

## Data Quality Checks

### Word/Label Alignment
- All examples have matching `len(words)` == `len(labels)`
- All positive examples (labels[-1]=1) have `next_laughter_tag` set
- All negative examples (labels[-1]=0) have `next_laughter_tag` as null

### Split Integrity
- Train: 110 unique shows
- Valid: 10 unique shows
- Test: 19 unique shows
- **Zero overlap** between any splits (verified by show_id)

### Example Format
```json
{
  "example_id": "scraped_loftcom_comedy_neal_brennan_crazy_good_transcript__seg_0001",
  "language": "en",
  "comedian_id": "scraped_loftcom_comedy_neal_brennan_crazy_good_transcript",
  "show_id": "scraped_loftcom_comedy_neal_brennan_crazy_good_transcript",
  "words": ["I", "feel", "pretty", "great", "."],
  "labels": [0, 0, 0, 0, 1],
  "metadata": {
    "segment_index": 1,
    "next_laughter_tag": "[audience cheering]",
    "laughter_type": "continuous",
    "conversion_mode": "inline_tag_heuristic_scraped",
    "context_token_policy": "clause_lexical_tail",
    "context_tail_tokens": 6,
    "source_url": "https://scrapsfromtheloft.com/comedy/neal-brennan-crazy-good-transcript/",
    "title": "Neal Brennan: Crazy Good (2024) | Transcript",
    "source_laughter_count": 9
  }
}
```

## Processing Details

### Laughter Tags Detected
- `[audience laughing]`
- `[audience cheers]`
- `[audience cheering]`
- `[chuckles]`
- `[laughs]`
- `[laughter]`
- And variations with "whoops", "applause", etc.

### Context Policy
- `clause_lexical_tail`: Keeps last 6 lexical tokens from previous clause
- Applied to both positive and negative examples for consistency

### Tokenization
- Uses regex pattern: `[A-Za-z0-9]+(?:['-][A-Za-z0-9]+)*|['-][A-Za-z0-9]+|[^\w\s]`
- Handles contractions, hyphenated words, punctuation
- Normalizes unicode quotes to ASCII

## Files Generated

```
data/training/standup_word_level_large/
├── train.jsonl  (22,913 examples, 1,161,677 words)
├── valid.jsonl  (2,680 examples, 123,419 words)
└── test.jsonl   (9,081 examples, 251,862 words)
```

## Combined Dataset Potential

When merged with existing `standup_word_level`:
- **Existing train:** 505 examples
- **New train:** 22,913 examples
- **Combined:** 23,418 examples

## Notes

- Conversion script: `convert_scraped_to_word_level.py`
- Original scraped data contained 8,149 annotated laughter segments
- ~50% of segments resulted in positive examples (followed by laughter)
- Average ~50 words per example including context tokens