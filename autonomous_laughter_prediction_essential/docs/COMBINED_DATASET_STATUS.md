# Combined Multilingual Dataset - Status Report
**Generated:** 2026-05-04

---

## Dataset Summary

| Metric | Value |
|--------|-------|
| **Total examples** | 10,048 |
| **Languages** | English, Chinese, Hindi |
| **Train/Valid/Test** | 8038 / 1605 / 405 |
| **Laughter rate** | ~37% (balanced) |

---

## Language Distribution

| Language | Code | Train | Valid | Test | Total | % |
|----------|------|-------|-------|------|-------|---|
| English | en | 5,949 | 1,154 | 299 | 7,402 | 73.7% |
| Chinese | zh | 2,051 | 446 | 101 | 2,598 | 25.9% |
| Hindi | hi | 38 | 5 | 5 | 48 | 0.5% |

---

## Laughter Rate by Language

| Language | Rate | Notes |
|----------|------|-------|
| English | 36.6% | Well balanced |
| Chinese | ~38% | Well balanced |
| Hindi | 0% | No laughter labels (real transcripts) |

---

## Hindi Data Status

**Current Hindi examples:** 48 (all from real Vir Das transcripts)
- **Issue:** 0% laughter rate (YouTube transcripts don't include laughter markers)
- **Synthetic Hindi:** Generation interrupted, will resume later
- **For V8.1:** Hindi will be in dataset but not evaluated for laughter prediction

---

## Comparison to Original Claims

| Claim | Original | Actual | Status |
|-------|----------|--------|--------|
| Languages | 100+ | 3 | ❌ |
| Words | 3M | ~165K | ❌ |
| Laughter labels | 130K+ | ~3.7K | ❌ |
| Hindi coverage | 20% target | 0.5% actual | ❌ |

---

## For V8.1 Ablation Study

The dataset is ready for V8.1 with:
- ✅ 10,048 examples (sufficient for ablation)
- ✅ 37% balanced laughter rate (en/zh)
- ✅ Biosemotic features
- ✅ Train/Valid/Test splits
- ⚠️ Hindi included but 0% laughter (document as limitation)

---

## Files

- `data/combined_multilingual/` - Final merged dataset for V8.1
- `docs/V8_1_ABLATION_STUDY.ipynb` - Colab notebook ready
- `docs/RESEARCH_LIMITATIONS.md` - Honest limitations document
- `docs/DATASET_VALIDATION_REPORT.md` - Dataset validation

---

*Status: Ready for V8.1 ablation study*
