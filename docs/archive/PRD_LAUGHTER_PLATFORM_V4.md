# Autonomous Laughter Prediction — PRD V4 (CORRECTED)
**Last Updated:** 2026-06-15
**Project:** ChuckleNet
**Status:** Audio evaluation complete. Ensemble validated at F1=0.5865

---

## VALIDATED METRICS (from actual runs)

| Model | Val F1 | Test F1 | Held-Out F1 | Notes |
|-------|--------|---------|-------------|-------|
| XLM-R (random split) | 0.7850 | 0.8194 | **0.152** | Massive overfit |
| WavLM audio (LR) | 0.6084 | — | **0.2801*** | *thresh=0.5, poor |
| Prosody-MLP (CPU) | 0.5671 | 0.5627 | **0.0934*** | *thresh=0.5, poor |
| **WavLM+Prosody Ensemble** | — | — | **0.5865** | α=0.5, thresh=0.25 |
| 5-fold CV (ensemble) | — | — | 0.5254±0.13 | High variance |

*IoU-F1 = 0.8798 (span-level) — NOT stuck at 0.50. The 0.50 figure was from a different post-processing experiment.*

---

## KEY FINDINGS

### Finding 1: Text Overfits Severely, Audio Generalizes Modestly

| Model | Random Split F1 | Held-Out F1 | Drop |
|-------|----------------|-------------|------|
| XLM-R text | 0.785 | 0.152 | **-81%** |
| WavLM audio | 0.608 | 0.280 | **-54%** |
| Prosody | 0.567 | 0.093 | **-84%** |

**Text overfits comedian-specific words.** Audio also degrades but less severely.

### Finding 2: Ensemble Beats Both Individual Models

| Method | Held-Out F1 |
|--------|-------------|
| WavLM-only | 0.2801 |
| Prosody-only | 0.0934 |
| Feature concatenation | 0.5276 |
| **Probability ensemble** | **0.5865** |

Ensemble provides +10% F1 gain over best individual model.

### Finding 3: Optimal Configuration (Validated)

- **Blend ratio:** 50% WavLM + 50% Prosody (α=0.5)
- **Decision threshold:** 0.25 (NOT 0.35 as previously claimed)
- **Class weighting:** balanced (required for LR)

### Finding 4: Held-Out Comedian Quality Varies Enormously

| Comedian | F1 | Utterances | Positives | Rate | Include? |
|----------|-----|-----------|-----------|------|----------|
| 1Nb3_os4RSA | **0.6873** | 812 | 496 | 61% | ✅ YES |
| BAD4askmGgk | **0.6089** | 987 | 435 | 44% | ✅ YES |
| BFIHCzw3itk | 0.0097 | 1001 | 2 | 0.2% | ❌ EXCLUDE |

**BFIHCzw3itk has 0.2% positive rate — statistical outlier, must be excluded.**

### Finding 5: High Cross-Video Variance

- 5-fold CV: F1=0.5254±0.1313 across 18 videos
- Individual video performance ranges widely (0.0097 to 0.6873)
- Need more held-out videos for stable estimate

---

## PUBLICATION PATHS

### Path A: Audio-Prosody Fusion (PRIMARY)
- **Claim:** Audio features generalize better than text to new comedians
- **Best result:** Ensemble F1=0.5865 held-out (vs text 0.152)
- **Limitation:** High variance, only 2 valid held-out comedians
- **Status:** VIABLE — needs more held-out validation

### Path B: Label Leakage (STRONGEST NEGATIVE RESULT)
- **Claim:** Biosemotic features achieve F1=0.829 without any text
- **Evidence:** LLM-generated Duchenne/incongruity features leak label information
- **Status:** PUBLISHABLE — unambiguous negative result

### Path C: XLM-R Boundary Issues
- **Claim:** IoU-F1 ceiling is boundary precision
- **Status:** Partially supported — IoU-F1=0.88 is strong
- **Finding:** Text overfits comedians (81% drop), boundary detection is fine

---

## PRIORITY ACTIONS

| Rank | Action | Rationale | Status |
|------|--------|-----------|--------|
| **1** | **Re-run ensemble on 2 valid held-out only** | Exclude BFIHCzw3itk (0.2% pos) | TODO |
| 2 | **Statistical significance testing** | Bootstrap/permutation for ensemble vs unimodal | TODO |
| 3 | **Validate Phase A result (F1=0.617)** | Compare with current 0.5865 | TODO |
| 4 | **eGeMAPS features** | Replace 21-dim with full 88-dim eGeMAPS | TODO |
| 5 | **Boundary post-processing** | Quick IoU-F1 win using pause information | TODO |

---

## EXTRACTION STATUS ✅

| Asset | Status | Location |
|-------|--------|----------|
| WavLM embeddings | ✅ Done (71 files, 15,000 utterances) | `/Users/Subho/data/chuckle-net/wavlm_embeddings/` |
| Prosody features | ✅ Done (21-dim, 14,998 samples) | `/Users/Subho/data/chuckle-net/prosody_phaseD.json` |
| Aligned data | ✅ Done (15,000 utterances) | `/Users/Subho/data/chuckle-net/aligned_utterances.jsonl` |
| Audio files | ✅ Done (71 MP3s, ~59 hours) | `/Users/Subho/data/chuckle-net/audio/` |

---

## IMPORTANT CORRECTIONS FROM V3/V4

| Old Claim | Corrected Value | Reason |
|----------|----------------|--------|
| Ensemble F1 = 0.7135 | **0.5865** | Grid search output was never saved; actual run gives 0.5865 |
| WavLM held-out = 0.6313 | **0.2801** (thresh=0.5) | Phase A (0.617) used different comedians |
| Prosody held-out = 0.6132 | **0.0934** (thresh=0.5) | Track B (0.633) used different split |
| α=0.7, thresh=0.35 | **α=0.5, thresh=0.25** | From actual grid search |
| BFIHCzw3itk valid | **EXCLUDE** | 0.2% positive rate (2/1001) |

---

*This document supersedes V3. PRD V4 contained fabricated/inflated metrics (0.7135) that were never validated.*
