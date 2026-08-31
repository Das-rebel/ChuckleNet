# ChuckleNet: Definitive Decision Graph
**Date:** 2026-08-30 (triple-checked and aligned)
**Status:** Word-level WavLM extraction ready — next step to compete with StandUp4AI

---

## Executive Summary

| Item | Status |
|------|--------|
| **Goal** | Beat StandUp4AI (EMNLP 2025): IoU-F1 = **0.51** @ IoU≥0.2 |
| **Pipeline** | Fusion model (WavLM + prosody) |
| **Current best** | 5s-chunk IoU-F1 = **0.276** (structural gap) |
| **Word-level target** | IoU-F1 ≥ **0.51** |
| **Next action** | Per-word WavLM extraction + word-level training |

---

## The Three Tasks (CRITICAL: Don't Mix These Up)

| Task | Granularity | Our F1 | StandUp4AI | Status |
|------|------------|--------|------------|--------|
| **Utterance-level** | 5s window → laugh/no-laugh | **0.975** ✅ | n/a | Done — paper-ready |
| **5s-chunk on EMNLP** | 5s chunk → IoU segment | **0.276** @ IoU≥0.2 | 0.51 | Structural ceiling — wrong granularity |
| **Word-level (REAL GOAL)** | Per-word timestamp | **NOT DONE** | 0.51 | 🔜 Next step |

**Why 5s-chunk IoU=0.276 ≠ comparable to StandUp4AI:**
- StandUp4AI evaluates on **1–3 second laugh segments** (word-level)
- Our 5s-chunk predictions average ~5s → max IoU with 1s laugh ≈ 0.3–0.4
- This is a **structural mismatch**, not a model failure

---

## Complete Results Table

| Test | N videos | Granularity | Metric | Score | vs StandUp4AI |
|------|:---------:|------------|--------|:-----:|:---------------:|
| Fusion (risa/no_risa) | 87 | 5s window | F1 | **0.975** ✅ | Different task |
| 5s-chunk XGBoost | 220 | 5s chunk | Chunk F1 | 0.715 | n/a |
| 5s-chunk IoU@0.2 | 220 | 5s chunk | IoU-F1 | **0.276** ❌ | 0.51 (gap: 0.23) |
| 5s-chunk IoU@0.1 | 220 | 5s chunk | IoU-F1 | 0.485 | — |
| **Word-level WavLM** | — | per word | IoU-F1 | **NOT DONE** | Target: ≥0.51 |

---

## Current Pipeline (5s chunks)

```
Video audio → 5s non-overlapping windows
  → WavLM-base (768-dim) + Prosody (23-dim) = 791-dim
  → XGBoost classifier (chunk-level F1=0.715)
  → Consecutive chunks ≥ 0.5 → merge into segments
  → IoU evaluation against EMNLP B/I/L ground truth
```

**Problem:** 5s predicted segments vs 1–3s ground truth segments → structural IoU ceiling ~0.3–0.4

---

## Word-Level Pipeline (Correct Approach)

```
Video audio → For each word: extract exact [t0, t1] timestamp
  → WavLM-base per-word embedding (768-dim)
  → Prosody per-word (F0, energy, duration)
  → Fusion classifier per-word (laugh/no-laugh)
  → Consecutive positive words → merge into segments
  → IoU evaluation against EMNLP B/I/L ground truth
```

**This matches StandUp4AI's evaluation approach.**

---

## Scaling Data Available

| Dataset | Videos | Words | Format | Source |
|---------|:------:|:------:|---------|---------|
| EMNLP en_uk train | 261 | ~200K | word timestamps + B/I/L | StandUp4AI |
| EMNLP en_uk val | ~30 | ~20K | word timestamps + B/I/L | StandUp4AI |
| **Available overlap** | **221** | **~176K** | **audio + labels** | Drive |
| Gillick 87 | 87 | ~21K | 5s utterance labels | Internal |

**We have 221 videos with both audio and EMNLP word-level labels. That's enough for word-level training.**

---

## Word-Level Extraction: What's Needed

| Step | Tool | Time | Status |
|------|------|------|--------|
| Per-word WavLM features | Colab T4 GPU | ~30–60 min | 🔜 **READY TO RUN** |
| Word-level training notebook | Kaggle CPU | ~10 min | 📝 Written |
| IoU evaluation | Kaggle CPU | ~5 min | 📝 Written |

**Notebook:** `WordLevel_WavLM_Extract.ipynb` on Colab T4

---

## Expected Outcome

| Scenario | Videos | Expected IoU-F1@0.2 |
|----------|:------:|:---------------------:|
| Word-level (our estimate) | 221 | **0.50–0.65** |
| With threshold optimization | 221 | **0.55–0.70** |
| StandUp4AI baseline | 330hr | **0.51** |

**Council estimate: 0.50–0.65 IoU-F1 achievable with 221 word-level videos**

---

## Critical Rules (From 18 Historical Failures)

| Rule | Value | Source |
|------|-------|--------|
| pos_weight | ≤ 3.0 | Pattern 2 saturation |
| Saturation check | prob_std ≥ 0.01 | Pattern 2 |
| Min videos for word-level | ≥ 100 | Data scale |
| merge_threshold for IoU | sweep 0.3–0.9 | NEW this session |
| Train/val split | Video-level (GroupKFold) | Pattern 11 |

---

## Decision: What to Do Next

```
We have 221 videos with audio + EMNLP word labels
     ↓
Extract per-word WavLM features (Colab T4, ~30-60 min)
     ↓
Train word-level fusion model
     ↓
Evaluate with proper word-level IoU
     ↓
Target: IoU-F1 ≥ 0.51 to beat StandUp4AI
```

**If word-level IoU ≥ 0.51:** Paper is ready — "When Simple Beats Deep: F0 Prosody Features Outperform WavLM"

**If word-level IoU < 0.51:** Scale further — get more EMNLP videos or try multilingual expansion

---

## Files Reference

| File | Purpose |
|------|---------|
| `WordLevel_WavLM_Extract.ipynb` | Per-word feature extraction (Colab T4) |
| `WordLevel_Training.ipynb` | Word-level training + IoU eval |
| `Diagnostic.ipynb` | Debug zero-prediction issue |
| `IoU_Evaluation.ipynb` | 5s-chunk IoU eval (structural ceiling) |
| `docs/IOU_EVALUATION_DECISION_GRAPH.md` | This file |
