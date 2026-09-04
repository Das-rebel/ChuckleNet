# Dataset Validation Report

*Generated: 2026-05-04*  
*Script: training/validate_multilingual_dataset.py*

---

## Executive Summary

| Dataset | Status | Train | Valid | Test | Total | Overall Laughter Rate |
|---|---|---|---|---|---|---|
| final_merged_10k | OK | 8,038 | 1,605 | 405 | 10,048 | 20.5% |
| expanded_10k_with_hindi | OK | 8,038 | 1,605 | 405 | 10,048 | 20.4% |
| synthetic_hindi | EMPTY | 0 | 0 | 0 | 0 | 0.0% |

---

## Detailed Validation Results

### Dataset: `final_merged_10k`
- **Path:** `/Users/Subho/autonomous_laughter_prediction_essential/data/final_merged_10k`
- **Exists:** True

✅ No format errors detected.

#### Split Breakdown

##### TRAIN (n=8,038)

**Language Distribution:**

- en: 5,949 (74.0%
- zh: 2,051 (25.5%
- hi: 38 (0.5%

**Word-Level Laughter Rate:** 20.5% ⚠️
  (Expected range: 30.0% – 45.0%)

**Per-Language Word-Level Laughter Rate:**

| Language | Laughter Rate | Total Words | Laughter Words |
|---|---|---|---|---|
| en | ⚠️ 20.6% | 97,903 | 20,136 |
| hi | ⚠️ 2.1% | 1,833 | 38 |
| zh | ⚠️ 21.2% | 32,569 | 6,902 |

**Sentence-Level Label Distribution:**

- 0: 4,855 (60.4%)
- 1: 2,939 (36.6%)

**Biosemiotic Feature Coverage (examples with ≥1 feature per category):**

- `duchenne_`* : 97.0%
- `incongruity_`* : 97.0%
- `tom_`* : 97.0%

---

##### VALID (n=1,605)

**Language Distribution:**

- en: 1,154 (71.9%
- zh: 446 (27.8%
- hi: 5 (0.3%

**Word-Level Laughter Rate:** 20.2% ⚠️
  (Expected range: 30.0% – 45.0%)

**Per-Language Word-Level Laughter Rate:**

| Language | Laughter Rate | Total Words | Laughter Words |
|---|---|---|---|---|
| en | ⚠️ 20.3% | 18,966 | 3,841 |
| hi | ⚠️ 2.0% | 250 | 5 |
| zh | ⚠️ 20.6% | 7,351 | 1,513 |

**Sentence-Level Label Distribution:**

- 0: 948 (59.1%)
- 1: 608 (37.9%)

**Biosemiotic Feature Coverage (examples with ≥1 feature per category):**

- `duchenne_`* : 96.9%
- `incongruity_`* : 96.9%
- `tom_`* : 96.9%

---

##### TEST (n=405)

**Language Distribution:**

- en: 299 (73.8%
- zh: 101 (24.9%
- hi: 5 (1.2%

**Word-Level Laughter Rate:** 21.3% ⚠️
  (Expected range: 30.0% – 45.0%)

**Per-Language Word-Level Laughter Rate:**

| Language | Laughter Rate | Total Words | Laughter Words |
|---|---|---|---|---|
| en | ⚠️ 22.2% | 4,943 | 1,095 |
| hi | ⚠️ 2.0% | 250 | 5 |
| zh | ⚠️ 21.7% | 1,569 | 340 |

**Sentence-Level Label Distribution:**

- 0: 241 (59.5%)
- 1: 153 (37.8%)

**Biosemiotic Feature Coverage (examples with ≥1 feature per category):**

- `duchenne_`* : 97.3%
- `incongruity_`* : 97.3%
- `tom_`* : 97.3%

---

### Dataset: `expanded_10k_with_hindi`
- **Path:** `/Users/Subho/autonomous_laughter_prediction_essential/data/expanded_10k_with_hindi`
- **Exists:** True

✅ No format errors detected.

#### Split Breakdown

##### TRAIN (n=8,038)

**Language Distribution:**

- en: 5,949 (74.0%
- zh: 2,051 (25.5%
- hi: 38 (0.5%

**Word-Level Laughter Rate:** 20.4% ⚠️
  (Expected range: 30.0% – 45.0%)

**Per-Language Word-Level Laughter Rate:**

| Language | Laughter Rate | Total Words | Laughter Words |
|---|---|---|---|---|
| en | ⚠️ 20.6% | 97,903 | 20,136 |
| hi | ⚠️ 0.0% | 1,833 | 0 |
| zh | ⚠️ 21.2% | 32,569 | 6,902 |

**Sentence-Level Label Distribution:**

- 0: 4,855 (60.4%)
- 1: 2,939 (36.6%)

**Biosemiotic Feature Coverage (examples with ≥1 feature per category):**

- `duchenne_`* : 97.0%
- `incongruity_`* : 97.0%
- `tom_`* : 97.0%

---

##### VALID (n=1,605)

**Language Distribution:**

- en: 1,154 (71.9%
- zh: 446 (27.8%
- hi: 5 (0.3%

**Word-Level Laughter Rate:** 20.2% ⚠️
  (Expected range: 30.0% – 45.0%)

**Per-Language Word-Level Laughter Rate:**

| Language | Laughter Rate | Total Words | Laughter Words |
|---|---|---|---|---|
| en | ⚠️ 20.3% | 18,966 | 3,841 |
| hi | ⚠️ 0.0% | 250 | 0 |
| zh | ⚠️ 20.6% | 7,351 | 1,513 |

**Sentence-Level Label Distribution:**

- 0: 948 (59.1%)
- 1: 608 (37.9%)

**Biosemiotic Feature Coverage (examples with ≥1 feature per category):**

- `duchenne_`* : 96.9%
- `incongruity_`* : 96.9%
- `tom_`* : 96.9%

---

##### TEST (n=405)

**Language Distribution:**

- en: 299 (73.8%
- zh: 101 (24.9%
- hi: 5 (1.2%

**Word-Level Laughter Rate:** 21.2% ⚠️
  (Expected range: 30.0% – 45.0%)

**Per-Language Word-Level Laughter Rate:**

| Language | Laughter Rate | Total Words | Laughter Words |
|---|---|---|---|---|
| en | ⚠️ 22.2% | 4,943 | 1,095 |
| hi | ⚠️ 0.0% | 250 | 0 |
| zh | ⚠️ 21.7% | 1,569 | 340 |

**Sentence-Level Label Distribution:**

- 0: 241 (59.5%)
- 1: 153 (37.8%)

**Biosemiotic Feature Coverage (examples with ≥1 feature per category):**

- `duchenne_`* : 97.3%
- `incongruity_`* : 97.3%
- `tom_`* : 97.3%

---

### Dataset: `synthetic_hindi`
- **Path:** `/Users/Subho/autonomous_laughter_prediction_essential/data/synthetic_hindi`
- **Exists:** True

#### Warnings
- ⚠️ Missing train.jsonl in synthetic_hindi
- ⚠️ Missing valid.jsonl in synthetic_hindi
- ⚠️ Missing test.jsonl in synthetic_hindi

✅ No format errors detected.

#### Split Breakdown

## Recommendations

- **[final_merged_10k/train]** Laughter rate 20.5% outside expected range (30.0%-45.0%) — review label distribution.
- **[final_merged_10k/train/zh]** Language 'zh' laughter rate 21.2% outside expected range.
- **[final_merged_10k/train/en]** Language 'en' laughter rate 20.6% outside expected range.
- **[final_merged_10k/train/hi]** Language 'hi' laughter rate 2.1% outside expected range.
- **[final_merged_10k/valid]** Laughter rate 20.2% outside expected range (30.0%-45.0%) — review label distribution.
- **[final_merged_10k/valid/en]** Language 'en' laughter rate 20.3% outside expected range.
- **[final_merged_10k/valid/zh]** Language 'zh' laughter rate 20.6% outside expected range.
- **[final_merged_10k/valid/hi]** Language 'hi' laughter rate 2.0% outside expected range.
- **[final_merged_10k/test]** Laughter rate 21.3% outside expected range (30.0%-45.0%) — review label distribution.
- **[final_merged_10k/test/en]** Language 'en' laughter rate 22.2% outside expected range.
- **[final_merged_10k/test/zh]** Language 'zh' laughter rate 21.7% outside expected range.
- **[final_merged_10k/test/hi]** Language 'hi' laughter rate 2.0% outside expected range.
- **[expanded_10k_with_hindi/train]** Laughter rate 20.4% outside expected range (30.0%-45.0%) — review label distribution.
- **[expanded_10k_with_hindi/train/zh]** Language 'zh' laughter rate 21.2% outside expected range.
- **[expanded_10k_with_hindi/train/en]** Language 'en' laughter rate 20.6% outside expected range.
- **[expanded_10k_with_hindi/valid]** Laughter rate 20.2% outside expected range (30.0%-45.0%) — review label distribution.
- **[expanded_10k_with_hindi/valid/en]** Language 'en' laughter rate 20.3% outside expected range.
- **[expanded_10k_with_hindi/valid/zh]** Language 'zh' laughter rate 20.6% outside expected range.
- **[expanded_10k_with_hindi/test]** Laughter rate 21.2% outside expected range (30.0%-45.0%) — review label distribution.
- **[expanded_10k_with_hindi/test/en]** Language 'en' laughter rate 22.2% outside expected range.
- **[expanded_10k_with_hindi/test/zh]** Language 'zh' laughter rate 21.7% outside expected range.
- **[synthetic_hindi/train]** No examples found — check data pipeline.
- **[synthetic_hindi/valid]** No examples found — check data pipeline.
- **[synthetic_hindi/test]** No examples found — check data pipeline.

---

## Validation Notes

### Required Fields
These fields are mandatory for every example:
- `example_id`
- `language`
- `words`
- `labels`

### Biosemiotic Feature Categories
- `duchenne_`* — all fields starting with this prefix
- `incongruity_`* — all fields starting with this prefix
- `tom_`* — all fields starting with this prefix

### Expected Laughter Rate
Word-level laughter labels should fall between **30.0%** and 
**45.0%** for each dataset.

---
*Report generated by `training/validate_multilingual_dataset.py`*