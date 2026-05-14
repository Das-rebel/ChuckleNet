# Language Distribution - Quick Summary

## Current State (2026-05-02)

```
Total Examples: 10,375
├── With Language Labels: 1,890 (18.2%) 🔴
├── Without Language Labels: 8,485 (81.8%) 🔴
└── Languages Found: 2 (en, zh) 🔴
```

## Dataset Breakdown

| Dataset | Total | Has Lang | Languages |
|---------|-------|----------|-----------|
| train_merged | 1,515 | ✅ 100% | en (73%), zh (27%) |
| valid_merged | 306 | ✅ 100% | en (70%), zh (30%) |
| test_merged | 69 | ✅ 100% | en (100%) 🔴 |
| synthetic_comedy_data | 8,485 | ❌ 0% | None 🔴 |

## Language Counts

| Language | Count | Overall % | Labeled % |
|----------|-------|-----------|-----------|
| English (en) | 1,383 | 13.33% | 73.17% |
| Chinese (zh) | 507 | 4.89% | 26.83% |
| Unlabeled | 8,485 | 81.78% | N/A |

## Critical Issues

### 🔴 Gap 1: No Language Metadata on 81.8% of Data
- 8,485 synthetic examples have no language field
- Cannot verify actual language diversity

### 🔴 Gap 2: Only 2 Languages vs. Claimed 100+
- STANDUP4AI docs claim "100+ languages"
- Reality: only en and zh
- Missing: hi, es, fr, de (claimed priority languages)

### 🔴 Gap 3: Test Set is Monolingual
- 69 examples, 100% English
- Cannot evaluate Chinese performance
- No multilingual validation

## Immediate Actions Required

1. **Add language detection** to synthetic_comedy_data.jsonl
2. **Create stratified test set** with Chinese examples
3. **Download STANDUP4AI data** for hi, es, fr, de
4. **Update documentation** to reflect reality

## STANDUP4AI Claims vs. Reality

| Feature | Claimed | Actual | Gap |
|---------|---------|--------|-----|
| Languages | 100+ | 2 | -98 |
| Target: hi/es/fr/de | ✅ | ❌ | 0/4 |
| Multilingual eval | ✅ | ❌ | Not possible |

## Full Report

See `docs/LANGUAGE_DISTRIBUTION_REPORT.md` for detailed analysis.
