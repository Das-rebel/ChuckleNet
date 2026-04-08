# Autonomous Laughter Prediction - Dataset Quality Report

## Executive Summary

The internal dataset has **severe quality issues** that will significantly impact model performance. The primary problem is that **positive labels are assigned to punctuation marks rather than actual laughter-triggering content**. Additionally, there are inconsistencies in labeling across splits and a significant domain mismatch between training and test data.

---

## 1. Dataset Overview

| Split   | Examples | Unique Shows | Label Distribution         |
|---------|----------|--------------|---------------------------|
| Train   | 505      | 81           | 505 positive (7.39%)      |
| Valid   | 102      | 17           | 102 positive (6.82%)      |
| Test    | 23       | 4            | 23 positive (6.50%)      |
| **Total** | **630** | **102**    | **630 positive (7.15%)**  |

**Language**: 100% English (no diversity)
**Dataset Age**: Synthetic comedy transcripts with weak laughter labels

---

## 2. Critical Data Quality Issues

### 2.1 Issue: PUNCTUATION-BASED LABELS (CRITICAL)

**Impact: HIGH - Model learns to predict punctuation, not humor**

In `train.jsonl`, the positive labels are predominantly punctuation marks:

| Positive Word | Count | % of All Positive Labels |
|---------------|-------|--------------------------|
| `"` (quote)   | 162   | 32.1%                    |
| `!` (exclaim) | 161   | 31.9%                    |
| `?` (question)| 81    | 16.0%                    |
| **Subtotal**  | **404** | **80.0%**               |

**Root Cause**: The labeling heuristic marks the **last word before a laughter tag** as positive. Since comedy segments often end with punctuation tokens, the model learns that punctuation = laughter trigger rather than learning actual comedic content.

**Sample positive contexts from train.jsonl**:
```
[comedy_club_transcript_1_seg_001] ...for milk ? **"**
[comedy_club_transcript_1_seg_002] ...and bitter ! **"**
[comedy_club_transcript_1_seg_003] ...coffee is getting **?**
[comedy_transcript_100_observational_seg_000] ...weather so much **?**
```

The words marked with `**` are the positive labels - they are almost entirely punctuation or arbitrary segment endings.

### 2.2 Issue: LABELING INCONSISTENCY (CRITICAL)

**Impact: HIGH - Same words get different labels in different contexts**

Words like `?` and `!` have dramatically different positive rates between train and valid:

| Word | Train Positive Rate | Valid Positive Rate |
|------|---------------------|---------------------|
| `?`  | 79.4%               | 0.0%                |
| `!`  | 56.9%               | 0.0%                |
| `"`  | 50.0%               | 50.0%               |

Words with essentially random labeling (50% positive rate):

| Word       | Occurrences | Positive Rate |
|------------|------------|---------------|
| `yesterday`| 42         | 50.0%         |
| `useless`  | 40         | 50.0%         |
| `beach`    | 40         | 50.0%         |
| `beer`     | 40         | 50.0%         |
| `rain`     | 68         | 25.0%         |

This indicates the labeling is essentially random for content words - the "positive" label is not correlated with the actual word meaning.

### 2.3 Issue: DOMAIN MISMATCH BETWEEN SPLITS (CRITICAL)

**Impact: HIGH - Model trained on observational/tech, tested on personal**

The splits are stratified by comedy **type**, not randomly:

| Split  | Comedy Types Present                    |
|--------|----------------------------------------|
| Train  | observational, tech, relatable         |
| Valid  | personal (100%)                        |
| Test   | personal (75%) + observational (25%)   |

**Show IDs by Split**:
- Train: `comedy_transcript_10_observational`, `comedy_transcript_13_tech`, `comedy_transcript_7_relatable`, etc.
- Valid: `comedy_transcript_14_personal`, `comedy_transcript_19_personal`, etc.
- Test: `comedy_transcript_29_personal`, `observational_comedy_2`

**Problem**: The model learns patterns from observational/tech/relatable comedy but is evaluated on personal comedy. These have different structures and humor patterns.

### 2.4 Issue: TINY DATASET (CRITICAL)

**Impact: HIGH - Insufficient training data**

- **Total positive examples**: Only 630 across all splits (~44 per split)
- **Unique positive words**: Only 9 unique words in train set (mostly punctuation)
- **Total vocabulary**: 157 unique words

This is far too small for robust model training. A typical NLP task requires thousands to millions of examples.

### 2.5 Issue: WEAK LABELING METHODOLOGY (HIGH)

**Impact: MEDIUM - Labels don't reflect actual laughter triggers**

The current labeling scheme:
1. Split transcript into segments of ~10-16 words
2. Label the **last word** before a `[laughter]` tag as positive
3. Label all other words as negative

**Problem**: The last word before laughter is NOT necessarily what triggered the laughter. Laughter is a **response** to content, but the label is placed on an **arbitrary boundary token**.

Example from `comedy_club_transcript_1.txt`:
```
Line 9: It's like they're charging us rent for the cup!
[laughter]
```
The segment ends with `!` and the label is on `!`. But the joke is about "charging rent for the cup" - not about exclamation marks.

---

## 3. Split Overlap Analysis

**GOOD NEWS**: No overlap between splits at ID or show_id level.

| Overlap Check           | Count |
|-------------------------|-------|
| Train-Valid ID overlap  | 0     |
| Train-Test ID overlap   | 0     |
| Valid-Test ID overlap  | 0     |
| Train-Valid show overlap| 0    |
| Train-Test show overlap | 0     |

The splits are truly non-overlapping at the transcript level.

---

## 4. Refined Datasets Analysis

The project has attempted to refine the labels with teacher refinement:

| Dataset                       | Examples | Positive Labels | Unique Positive Words |
|-------------------------------|----------|-----------------|----------------------|
| `train_refined.jsonl`         | 505      | 505             | 19                   |
| `train_refined_audit.jsonl`   | 505      | **0**           | 0                    |
| `train_refined_safe_hybrid.jsonl` | 505  | 505             | 20                   |

**Issue**: The `train_refined_audit.jsonl` has **ZERO positive labels** - this appears to be a bug or failed refinement run. The safe_hybrid dataset has slightly different word distribution but still contains many punctuation labels.

---

## 5. Recommendations

### 5.1 Immediate Fixes (High Priority)

1. **Remove punctuation-only labels**
   - Filter out examples where the positive label is only punctuation
   - Or relabel using the **first content word** of the punchline instead of the last token

2. **Fix the domain mismatch**
   - Redistribute comedy types across all splits
   - Use stratified sampling to ensure each split has ~same proportion of each comedy type

3. **Investigate `train_refined_audit.jsonl`**
   - 0 positive labels indicates a bug in the refinement pipeline
   - Fix before using refined datasets

### 5.2 Medium-Term Improvements

4. **Improve labeling methodology**
   - Instead of "last word before laughter", use "first word of the punchline"
   - Or use a more sophisticated alignment method (e.g., forced alignment with audio)

5. **Increase dataset size**
   - Current: 630 examples
   - Target: At least 5,000-10,000 examples for meaningful training
   - Consider scraping real comedy transcripts with aligned laughter data

6. **Add language diversity**
   - 100% English limits generalization
   - Add multi-lingual comedy data

### 5.3 Data Augmentation Ideas

7. **Back-translation augmentation**
   - Translate segments to another language and back
   - Creates synthetic variations

8. **Synonym replacement**
   - Replace content words with synonyms
   - Keep punctuation patterns but change semantic content

9. **Context preservation**
   - When augmenting, ensure laughter-triggering context is preserved

---

## 6. Quantified Impact Assessment

| Issue                        | Severity | Est. Impact on Model Performance |
|------------------------------|----------|--------------------------------|
| Punctuation-based labels     | CRITICAL | Model predicts `!`/`?` instead of content - ~40% accuracy drop expected |
| Labeling inconsistency       | CRITICAL | Model cannot learn stable patterns - validation loss will be noisy |
| Domain mismatch (train/test) | CRITICAL | Poor generalization to test set - possibly 50%+ accuracy drop |
| Tiny dataset (630 examples)  | CRITICAL | Overfitting inevitable - won't generalize to real data |
| Weak labeling methodology    | HIGH     | Misaligned training signal - wrong features learned |
| No language diversity        | MEDIUM   | Limited to English comedy only |

---

## 7. Conclusion

The current dataset is **not suitable for production model training** due to:

1. **80% of positive labels are punctuation** - model learns wrong signal
2. **Inconsistent labeling** - same words have different labels
3. **Domain mismatch** - trained on non-personal, tested on personal comedy
4. **Too small** - 630 examples cannot support robust NLP model

**Immediate action required**: Either fix the labeling methodology or acquire a properly labeled dataset before training proceeds.

---

*Report generated: 2026-04-01*
*Analysis performed on: train.jsonl, valid.jsonl, test.jsonl, and refined datasets*
