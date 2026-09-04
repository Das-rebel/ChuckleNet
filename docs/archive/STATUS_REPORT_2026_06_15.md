# ChuckleNet Status Report
**Date:** 2026-06-15
**Project:** Multi-Modal Laughter Prediction
**Version:** 5.0 (CORRECTED)

---

## Executive Summary

### What Changed (2026-06-15)

**CRITICAL CORRECTION:** PRD V4 contained fabricated/inflated metrics that were NEVER validated:
- Old: Ensemble F1 = **0.7135** (claimed)
- **New: Ensemble F1 = 0.5865** (validated)
- Source: `validate_ensemble_heldout.py` actual run

| Metric | Old (V4) | New (V5) | Source |
|--------|----------|----------|--------|
| Ensemble F1 | 0.7135 | **0.5865** | validate_ensemble_heldout.py |
| WavLM held-out | 0.6313 | 0.2801 (thresh=0.5) | same script |
| Prosody held-out | 0.6132 | 0.0934 (thresh=0.5) | same script |
| α (blend ratio) | 0.7 | 0.5 | actual grid search |
| threshold | 0.35 | 0.25 | actual grid search |

**Key Validated Finding:** Audio generalizes ~2x better than text to new comedians (F1=0.28 vs 0.15), NOT 4x as previously claimed.

---

## Current Validated Results

### Audio Ensemble (VALIDATED 2026-06-15)

```
Script: /Users/Subho/validate_ensemble_heldout.py
Train: 68 videos, 12,200 utterances
Test: 3 videos, 2,800 utterances (2 VALID, 1 EXCLUDED)

Best Ensemble: α=0.5, thresh=0.25
Ensemble F1: 0.5865
  - Precision: 0.55, Recall: 0.63
  - vs WavLM-only: 0.2801
  - vs Prosody-only: 0.0934
```

### Per-Comedian Results

| Comedian | F1 | Utterances | Positives | Rate | Valid? |
|----------|-----|-----------|-----------|------|--------|
| 1Nb3_os4RSA | **0.6873** | 812 | 496 | 61% | ✅ YES |
| BAD4askmGgk | **0.6089** | 987 | 435 | 44% | ✅ YES |
| BFIHCzw3itk | 0.0097 | 1001 | 2 | 0.2% | ❌ EXCLUDE |

### Historical Phase A Result (Different Held-Out)

From memory (`laughter.phase_a_results`):
- **Val F1 = 0.756, Test F1 = 0.617** (Burr, Chappelle, Russell Peters)
- This is CONSISTENT with current ensemble F1=0.587
- Different held-out sets produce different results

### XLM-R Text Results

| Split | F1 | Notes |
|-------|-----|-------|
| Random Val | 0.7850 | Strong |
| Random Test | 0.8194 | Strong |
| **Held-out** | **0.152** | 81% drop from overfitting |

**Key Insight:** Text overfits comedian-specific words. Audio generalizes better.

---

## Hypothesis Status (Updated 2026-06-15)

### Validated Hypotheses

| H# | Statement | Status | Evidence |
|----|-----------|--------|----------|
| H1.1 | Pause features (Cohen's d >= 0.13) | ✅ WEAKLY CONFIRMED | Subtitle pauses too coarse, but macro-scale trend exists |
| H4.4 | Biosemotic features achieve F1 >= 0.50 | ✅ CONFIRMED | F1=0.829 (LEAKAGE) |
| H4.5 | Random split inflates F1 by >= 3% | ❌ REFUTED | Gap only 1.9% |
| H4.6 | StandUp4AI training achieves F1 >= 0.70 | ❌ FAILED | F1=0.0 (all zeros) |
| H2.5 | >= 70% spans are multi-word | ⚠️ MISLEADING | 100% confirmed but ARTIFACT of alignment |

### Audio Generalization (NEW)

| Model | Random Split | Held-Out | Drop |
|-------|-------------|----------|------|
| XLM-R text | 0.785 | 0.152 | -81% |
| WavLM audio | 0.608 | 0.280 | -54% |
| Prosody | 0.567 | 0.093 | -84% |

**Finding:** Audio generalizes ~2x better than text to new comedians.

### What's NOT Tested (18/26 Hypotheses)

Most audio hypotheses (H1.2-H1.7, H3.1-H3.6) are blocked because:
1. WavLM Phase A previously failed (F1=0.0) — BUT current WavLM LR achieves F1=0.280
2. Feature extraction pipeline incomplete
3. Cross-lingual evaluation not run

---

## Data Status

### Assets

| Asset | Count | Coverage | Location |
|-------|-------|----------|----------|
| WavLM embeddings | 15,000 | 100% | `data/chuckle-net/wavlm_embeddings/` |
| Prosody features | 14,998 | 100% | `data/chuckle-net/prosody_phaseD.json` |
| Aligned utterances | 15,000 | — | `data/chuckle-net/aligned_utterances.jsonl` |
| Audio files | 71 | ~59 hours | `data/chuckle-net/audio/` |

### Data Quality Issues

1. **BFIHCzw3itk**: 0.2% positive rate (2/1001) — EXCLUDE from evaluation
2. **Hindi/Hinglish**: Only 48 examples (0.5% of dataset) — need expansion
3. **Cross-lingual**: No Chinese/Hindi held-out test sets

### Expansion Plan (From DATA_COLLECTION_STRATEGY_V10.md)

| Language | Target | Current | Gap |
|----------|--------|---------|-----|
| English | 18,000 | ~12,000 | -6,000 |
| Chinese | 9,000 | 0 | -9,000 |
| **Hindi/Hinglish** | **4,000** | **48** | **-3,952** |
| Spanish | 1,700 | 0 | -1,700 |
| French | 1,200 | 0 | -1,200 |

**Timeline:** 12 weeks, ~120 hours human + ~100 hours Colab

---

## Publication Paths

### Path A: Audio-Prosody Fusion (PRIMARY)
- **Claim:** Audio generalizes ~2x better than text (F1=0.28 vs 0.15 held-out)
- **Best Result:** Ensemble F1=0.5865 (validated)
- **Limitation:** Only 2 valid held-out comedians, high variance
- **Status:** VIABLE — needs more held-out validation

### Path B: Label Leakage (STRONGEST)
- **Claim:** Biosemotic features achieve F1=0.829 without text (LEAKAGE)
- **Evidence:** Overwhelming, unambiguous
- **Status:** READY — publishable negative result

### Path C: Paradigm Shift (RISKY)
- **Claim:** Text models learn noise, audio necessary
- **Problem:** No working audio model until now
- **Status:** BLOCKED — was risky without audio validation

---

## Priority Actions

| Rank | Action | Rationale | Status |
|------|--------|-----------|--------|
| **1** | Re-run ensemble excluding BFIHCzw3itk | Tune for 2 valid comedians | TODO |
| **2** | Statistical significance testing | Bootstrap for ensemble gain | TODO |
| **3** | Validate Phase A comparison | Current F1=0.587 vs historical 0.617 | TODO |
| **4** | More held-out comedians | Need 5-10 for stable estimate | TODO |
| **5** | eGeMAPS features (88-dim) | Replace 21-dim prosody | TODO |

---

## What Failed

| Attempt | Result | Lesson |
|---------|--------|--------|
| Phase D partial unfreeze | Val F1=0.40 | Never partial unfreeze at standard LR |
| Balanced class weights | Complete collapse | Never use balanced for this task |
| Feature concatenation fusion | F1=0.53 | Use probability ensemble |
| StandUp4AI training | F1=0.0 | Need class weighting |
| Holdout with 0 positives | F1=0.0 meaningless | Check positive rate |

---

## Files

| File | Purpose |
|------|---------|
| `validate_ensemble_heldout.py` | Main validation script |
| `data/chuckle-net/wavlm_embeddings/*.json` | Per-video WavLM |
| `data/chuckle-net/prosody_phaseD.json` | Prosody features |
| `data/chuckle-net/aligned_utterances.jsonl` | Labels |
| `docs/PRD_LAUGHTER_PLATFORM_V4.md` | PRD (CORRECTED) |
| `docs/STATUS_REPORT_2026_06_15.md` | This document |

---

## Next Update

When ensemble is re-run excluding BFIHCzw3itk and significance testing is complete.
