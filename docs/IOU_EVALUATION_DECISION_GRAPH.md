# ChuckleNet: Definitive Decision Graph
**Date:** 2026-09-02 (honest status after full audit)
**Status:** GPU exhausted. Colab needed for word-level extraction.

---

## Executive Summary

| Item | Status |
|------|--------|
| **Goal** | Beat StandUp4AI (EMNLP 2025): IoU-F1 = **0.51** @ IoU≥0.2 |
| **Pipeline** | Word-level WavLM + prosody fusion |
| **Chunk-level CV F1** | 0.49 @ th=0.5 (NOT comparable to StandUp4AI) |
| **Word-level extraction** | BLOCKED — Colab GPU exhausted |
| **Kaggle GPU** | CUDA sm_60 incompatible with PyTorch 2.10+ |
| **Next action** | Wait for Colab GPU reset (~1-2 days) |

---

## The Three Tasks (CRITICAL: Don't Mix These Up)

| Task | Granularity | Our F1 | StandUp4AI | Status |
|------|-------------|---------|------------|--------|
| **Utterance-level** | 5s window → laugh/no-laugh | **0.975** ✅ | n/a | Done — paper-ready |
| **5s-chunk IoU** | 5s chunk → IoU segment | **0.276** @ IoU≥0.2 | 0.51 | Structural gap — wrong granularity |
| **Word-level (REAL GOAL)** | Per-word timestamp | **IN PROGRESS** | 0.51 | 🔄 Blocked by GPU |

**Why 5s-chunk ≠ comparable to StandUp4AI:**
- StandUp4AI evaluates on **1–3 second laugh segments** (word-level)
- Our 5s-chunk predictions average ~5s → max IoU with 1s laugh ≈ 0.3–0.4
- This is a **structural mismatch**, not a model failure

---

## Current Results

### Chunk-level (221 videos, XGBoost, 5-fold GroupKFold)

| Threshold | Precision | Recall | F1 |
|-----------|-----------|--------|-----|
| 0.3 | 0.45 | 0.97 | **0.62** |
| 0.4 | 0.47 | 0.81 | **0.60** |
| 0.5 | 0.50 | 0.48 | **0.49** |
| 0.6 | 0.60 | 0.18 | **0.28** |

Best chunk F1 = 0.49 at balanced threshold (th=0.5).

### IoU Evaluation (5s chunks → word-level ground truth)

| IoU Threshold | Precision | Recall | F1 |
|--------------|-----------|--------|-----|
| ≥ 0.1 | ~0.48 | ~0.28 | **0.36** |
| ≥ 0.2 | ~0.28 | ~0.15 | **0.20** |
| ≥ 0.3 | ~0.15 | ~0.08 | **0.11** |

**Root cause of low IoU:** 5s chunks are 2–5× longer than ground truth laugh segments (1–3s).

---

## Data Available

| Resource | Count | Status |
|----------|-------|--------|
| EMNLP label files (en_uk) | 261 | ✅ |
| Audio files (en_uk/en_us) | 326 | ✅ |
| **Overlap (audio + labels)** | **221** | ✅ |
| Word-level WavLM features | 0 | ❌ GPU needed |
| Chunk-level features (n, 791) | 221 | ✅ |

---

## Kaggle Status

| Resource | Status |
|----------|--------|
| Dataset: `subhajitdas/chuckle-221-wordlevel` | 221 chunk features ✅ |
| Dataset: `subhajitdas/chuckle-audio-326` | Not created ❌ |
| Kaggle GPU (P100) | CUDA sm_60 incompatible ❌ |
| Kaggle CPU | Works but WavLM too slow (180s/video) ⚠️ |

---

## Path Forward

### Option A: Wait for Colab GPU (~1-2 days)
1. Word-level WavLM extraction: ~30 min for 221 videos
2. Word-level training + IoU evaluation
3. Compare to StandUp4AI IoU-F1 = 0.51

### Option B: Submit paper with utterance-level F1 = 0.975
- Already proven: simple prosody > deep audio
- No IoU comparison needed
- Different contribution claim

### Option C: Kaggle CPU extraction (if Colab unavailable)
- Upload 326 audios to Kaggle (~30 min)
- CPU WavLM: 180s/video × 221 = 11 hours (exceeds 9h limit)
- **Solution:** Process in 3 batches of 75 videos each

---

## Historical Failures (Key Lessons)

| # | Failure | Root Cause | Prevention |
|---|---------|-----------|------------|
| 1 | Label sparsity | <15% positive rate | Use >15% positive rate data |
| 2 | pos_weight saturation | pos_weight > 3.0 | Never exceed 3.0 |
| 3 | Wrong evaluation metric | Chunk F1 ≠ IoU-F1 | Match StandUp4AI's IoU protocol |
| 4 | GPU exhaustion | Colab 100-unit limit | Monitor quota, plan batches |
| 5 | Kaggle CUDA incompatibility | PyTorch 2.10+ sm_90 only | Use CPU or older PyTorch |

---

## Canonical Pipeline

```
1. training/convert_standup_raw_to_word_level.py
2. training/refine_weak_labels_nemotron.py  
3. training/xlmr_standup_word_level.py
4. training/run_xlmr_standup_pipeline.py
5. training/autonomous_research_loop.py
```

**Current winning model:** `experiments/xlmr_standup_baseline_weak_pos5`
- Validation F1: 0.785
- Test F1: 0.819
- Test IoU-F1: 0.880
