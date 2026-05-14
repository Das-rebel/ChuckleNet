# V8 Training Data Quality Report

**Date:** 2026-05-02
**Project:** autonomous_laughter_prediction_essential

---

## 1. Dataset Line Counts

| Dataset | Path | Lines | Status |
|---------|------|-------|--------|
| enhanced_comedy_small.jsonl | data/ | 0 (corrupted) | **BROKEN** |
| enhanced_comedy_medium.jsonl | data/ | 0 (corrupted) | **BROKEN** |
| enhanced_comedy_large.jsonl | data/ | 0 (corrupted) | **BROKEN** |
| standup_transcript_examples.jsonl | data/ | 16 | OK (but tiny) |
| scraps_from_loft/*.txt | data/ | 24 files, 2 lines each | **FAKE DATA** |
| integrated_comedy_data.jsonl | data/ | 0 (empty file) | BROKEN |

---

## 2. Format Analysis

### enhanced_comedy_*.jsonl (BROKEN)

**Issue:** These files contain multiple JSON objects concatenated WITHOUT newlines.

```
File structure: {json1}{json2}{json3}...  (no separators)
Expected:       {json1}\n{json2}\n{json3}\n
```

Example error:
```
json.decoder.JSONDecodeError: Extra data: line 1 column 379 (char 378)
```

All three files (small, medium, large) have this exact same corruption pattern:
- No newline characters (`\n`) present
- No CRLF (`\r\n`) present
- Files are raw concatenated JSON

**Impact:** Cannot be parsed by `jsonlines`, standard JSON parsers, or training pipelines.

### standup_transcript_examples.jsonl (OK but tiny)

**Format:** Sentence-level text/label pairs (NOT word-level)

Each line is valid JSON with:
```json
{
  "id": "standup-001",
  "setup": "I hit the age where every friend recommends a mattress...",
  "punchline": "Nobody says good morning anymore. They say, 'You need lumbar support.'",
  "text": "I hit the age where every friend recommends a mattress like they discovered fire. Nobody says good morning anymore. They say, 'You need lumbar support.' [laughter]",
  "label": 1,
  "source": "synthetic_standup_style",
  "style": "observational",
  "topic": "aging"
}
```

| Field | Type | Description |
|-------|------|-------------|
| text | string | Full sentence with [laughter] marker |
| label | int | 0/1 binary (1 = has laughter) |
| setup/punchline | string | Segmented joke parts |
| style/topic | string | Metadata |

**Problem:** This is sentence-level classification format, but the pipeline expects **word-level** sequence labeling (words with individual B-I-O tags or similar).

### scraps_from_loft/*.txt (FAKE/PLACEHOLDER DATA)

All 24 files contain identical placeholder content:

```
Demo transcript content for Killin' Them Softly
[laughter]
More stand-up content
```

**These are NOT real comedian transcripts.** They are clearly demo/placeholder files that should not be used for training.

---

## 3. Data Quality Issues

### Critical Issues

1. **Corrupted JSONL files** - enhanced_comedy_*.jsonl cannot be parsed at all
2. **Tiny valid dataset** - Only 16 real records in standup_transcript_examples.jsonl
3. **Fake source data** - scraps_from_loft contains placeholder text, not real transcripts
4. **Format mismatch** - Sentence-level data cannot be used for word-level training

### Format Mismatch Details

The pipeline (per AGENTS.md) expects word-level sequence labeling:
```
words,labels format where each word has a corresponding label
```

But the available valid data (standup_transcript_examples.jsonl) is:
```
text,label format where each record is a full sentence with one label
```

### Missing Files

The file `training/convert_standup_raw_to_word_level.py` referenced in AGENTS.md does NOT exist in this repository. The training/ directory contains different files entirely (audio processing, MHD processing, etc.).

---

## 4. Recommendations for Fixing

### Priority 1: Fix JSONL Format (enhanced_comedy_*.jsonl)

The files appear to be JSON arrays or concatenated JSON objects. Options:

**Option A:** If they're JSON arrays, split into individual lines:
```python
import json
with open('enhanced_comedy_large.jsonl', 'r') as f:
    data = json.load(f)  # Load as single array
with open('enhanced_comedy_large_fixed.jsonl', 'w') as f:
    for item in data:
        f.write(json.dumps(item) + '\n')
```

**Option B:** If they're concatenated objects without arrays, they're likely unrecoverable without manual parsing.

### Priority 2: Convert Sentence-Level to Word-Level

If enhanced_comedy data is recoverable, convert using:
```python
# Pseudo-code for word-level conversion
def to_word_level(sentence_label_record):
    words = sentence_label_record['text'].split()
    label = sentence_label_record['label']
    # Assign same label to all words (or use better alignment)
    return [{'word': w, 'label': label} for w in words]
```

### Priority 3: Replace Fake Scrap Data

scraps_from_loft/*.txt contains demo text. Either:
- Remove these files from training pipeline
- Replace with real transcript segments

### Priority 4: Acquire More Training Data

16 records is insufficient for meaningful word-level sequence labeling. Consider:
- Downloading real StandUp! dataset transcripts
- Using the MHD sitcom data in data/mhd_sitcom/
- Generating synthetic word-level data from existing sentences

---

## 5. Summary

| Issue | Severity | Files Affected |
|-------|----------|----------------|
| JSONL concatenation without newlines | CRITICAL | enhanced_comedy_small/medium/large.jsonl |
| Empty file | CRITICAL | integrated_comedy_data.jsonl |
| Fake/placeholder content | CRITICAL | scraps_from_loft/*.txt (24 files) |
| Format mismatch (sentence vs word-level) | HIGH | standup_transcript_examples.jsonl |
| Dataset too small | HIGH | standup_transcript_examples.jsonl (16 records) |
| Missing conversion script | MEDIUM | convert_standup_raw_to_word_level.py not found |

**Bottom line:** None of the datasets in `data/` are currently usable for the word-level XLM-R training pipeline described in AGENTS.md. The enhanced_comedy files are corrupted, the scraps are fake, and the only valid file has the wrong format and is too small.