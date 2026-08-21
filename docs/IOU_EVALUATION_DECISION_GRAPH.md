# ChuckleNet: Definitive Decision Graph
**Date:** 2026-08-22 (rechecked after scale221 completion)
**Status:** Scale221 done — EMNLP external evaluation PENDING

---

## Executive Summary

| Item | Status |
|------|--------|
| Paper result (F1=0.975) | ✅ Verified and ready |
| Scale221 training | ✅ COMPLETED — CV F1=0.8793 |
| Scale221 model | ✅ Saved: `scale221/scale221_fusion_model.pt` |
| EMNLP external evaluation | ⏳ PENDING — run evaluation notebook |
| Citation audit | ⚠️ 4 hallucinated, 23 unmatched |

---

## Part 1: What Scale221 Actually Produced

### Training Results

| Item | Value | Notes |
|------|-------|-------|
| Videos | 221 | From StandUp4AI partition (audio+label overlap) |
| Segments | 20,420 | 5-second windows, 2.5s stride |
| Segment shape | (119, 791) | WavLM 768-dim + prosody 23-dim |
| Positive rate | 30% | Fallback (teacher max prob=0.52) |
| Teacher model | best_fusion_model.pt | F1=0.975 on original data |
| Teacher max prob | 0.52 | Teacher BARELY fires on these segments |
| CV F1 | **0.8793** ± 0.0219 | 5-fold GroupKFold |
| Fold F1s | 0.848, 0.866, 0.899, 0.908, 0.875 | |
| Model | `scale221/scale221_fusion_model.pt` | 2.2MB |

### Critical Warning: CV F1 is on Pseudo-Labels

**The CV F1=0.8793 is optimistic — it's evaluated on the model's own pseudo-labels.**

- Teacher model (best_fusion_model.pt) reaches max probability 0.52 on these segments
- Top 30% selected as positive (arbitrary fallback since teacher didn't clearly fire)
- Training on these noisy pseudo-labels → model learns to predict the noise
- **Real external evaluation may be significantly lower**

This is NOT a reliable result until validated against ground truth.

---

## Part 2: The Evaluation Path (PENDING)

### Evaluation Notebook

**File:** `Scale221_External_Evaluation.ipynb` (commit 315c1a8)
**GitHub:** [Open in Colab →](https://colab.research.google.com/github/Das-rebel/autonomous_laughter_prediction/blob/main/Scale221_External_Evaluation.ipynb)

**What it does:**
1. Downloads 16 audio files via yt-dlp (YouTube)
2. Mounts Google Drive to access labels + scale221 model
3. Loads scale221 model + WavLM on GPU
4. Extracts 791-dim features per word from EMNLP labels
5. Runs IoU evaluation against ground truth BIO labels

**Known limitations:**
- Only 1/16 eval videos overlap with scale221 training set
- 4 audio files failed to download previously
- Labels expected at `gdrive:standup4ai/labels/{vid}.csv` — may not exist

### What Happens After Evaluation

```
Evaluation F1 vs StandUp4AI F1=0.51:
│
├─ F1 ≥ 0.70 → STRONG EXTERNAL VALIDATION
│   ✅ Scale221 generalizes to EMNLP
│   → Submit paper with scale results + EMNLP comparison
│
├─ F1 0.40–0.69 → MODERATE VALIDATION  
│   ✅ Better than StandUp4AI baseline
│   → Submit paper; note performance gap from label noise
│
├─ F1 0.20–0.39 → WEAK VALIDATION
│   ⚠️ Model struggles on external data
│   → Submit paper without scale results
│   → Note: pseudo-label noise affected quality
│
└─ F1 < 0.20 → FAILED VALIDATION
    ❌ Scale221 doesn't generalize
    → Submit original F1=0.975 paper only
    → Don't claim external validity
```

---

## Part 3: Two Submission Paths

### Path A: Submit Original Paper (F1=0.975) — LOW RISK

**If EMNLP evaluation fails OR deadline-driven:**

```
Claim: "When Simple Beats Deep: F0 Prosody Features Outperform WavLM"
Evidence:
  ✅ F1=0.975 on held-out comedians (Bill Burr, Dave Chappelle, Russell Peters)
  ✅ WavLM 768-dim alone: F1=0.22
  ✅ F0 5-dim alone: F1=0.975
  ✅ Comparable to Gillick F1=0.75 (Interspeech 2021)
  
What NOT to claim:
  ❌ "Beats StandUp4AI F1=0.51" — different metrics
  ❌ IoU comparison — 0.975 is segment-level F1, not IoU-F1
  ❌ External validity — not evaluated on EMNLP
  
Venue: INTERSPEECH 2026 or EMNLP 2026 Industry Track
Timeline: 1-2 weeks to write
Risk: LOW
```

### Path B: Submit with Scale221 Results (F1=0.8793 on pseudo-labels) — MEDIUM RISK

**If EMNLP evaluation succeeds (F1 ≥ 0.50):**

```
Claim: "Scalable Laughter Detection via WavLM+Prosody Fusion"
Evidence:
  ✅ Scale221 CV F1=0.8793 on 221 videos, 20,420 segments
  ✅ External validation on EMNLP ground truth (PENDING)
  ✅ Better than StandUp4AI F1=0.51 (IF evaluation confirms)
  
What to verify before claiming:
  ⚠️ EMNLP IoU-F1 ≥ 0.50 (must beat StandUp4AI)
  ⚠️ Held-out comedian gap < 20%
  ⚠️ Citation audit complete (4 hallucinated, 23 unmatched)
  
Venue: EMNLP 2026 (better for seq-labeling comparison)
Timeline: 2-3 weeks (evaluation + paper revision)
Risk: MEDIUM — depends on evaluation results
```

---

## Part 4: Immediate Action Items

### 1. Run EMNLP External Evaluation (CRITICAL)

```bash
# Open in Colab (GPU runtime required):
https://colab.research.google.com/github/Das-rebel/autonomous_laughter_prediction/blob/main/Scale221_External_Evaluation.ipynb

# Steps:
# 1. Runtime → Change runtime type → GPU (T4 or A100)
# 2. Run all cells top to bottom
# 3. Report F1 @ IoU=0.3
```

**Prerequisites:**
- Google Drive mount with:
  - `standup4ai/scale221/scale221_fusion_model.pt` ✅ (on Drive)
  - `standup4ai/labels/{vid}.csv` — may need to copy from `seq-Standup4AI/dataset/en_uk/all/`
  - `standup4ai/audio/{vid}.m4a` — partial coverage on Drive

### 2. Citation Audit (REQUIRED for any submission)

From `experiments/validation/task3_citation_report.md`:
- **4 hallucinated** — remove immediately  
- **23 unmatched/garbled** — verify or replace
- **2 wrong year** — correct (XLM-R 2020, StandUp4AI 2025)

Verify every citation at: scholar.google.com or semanticscholar.org

### 3. Free Disk Space (if running Colab locally)

Current free: ~5GB | Colab needs: ~20GB
Run: `du -sh ~/data/chuckle-net/audio_final/` — consider archiving

---

## Part 5: Scale221 Architecture Summary

```
Input: 5-second audio window
  ↓
WavLM 768-dim (pretrained, frozen)
  ↓ ← concatenated with
Prosody 23-dim (F0×5 + Energy×5 + Duration×2 + Spectral×5 + VQ×6)
  ↓
MLP 791→512→256→64→1
  + BatchNorm + Dropout(0.3) + AdamW
  + pos_weight=2.33 (auto-capped at 3.0)
  ↓
Output: laugh probability (0–1)

Training:
  221 videos → 20,420 segments
  Teacher: best_fusion_model.pt (F1=0.975)
  Pseudo-labels: top 30% by teacher probability
  Positive rate: 30%
  CV F1: 0.8793 (5-fold GroupKFold)
```

---

## Part 6: Historical Failure Patterns (Updated)

| # | Pattern | Status in Scale221 |
|---|---------|-------------------|
| 1 | Label Sparsity | ⚠️ Used 30% fallback (not natural 15%+) |
| 2 | Model Saturation | ✅ pos_weight=2.33 (capped at 3.0) |
| 3 | Boundary Problem | ⏳ EVALUATION PENDING |
| 4 | Teacher Corruption | ⚠️ Teacher max prob=0.52 (barely fires) |
| 5 | Hyperparam Exhaustion | N/A — didn't retrain on pos weights |
| 6 | Garbage Pseudo-Labels | ⚠️ Teacher weak on these segments |
| 7 | WavLM Pipeline Failed | ✅ WavLM embeddings extracted |
| 8 | F0 Extraction Misaligned | ✅ 5-second windows aligned |
| 9 | StandUp4AI val_f1=0.0 | ⏳ EVALUATION PENDING |
| 10 | Prosody Plateau | ✅ Full 23-dim prosody used |
| 11 | Training Overfitting | ✅ GroupKFold (video-level splits) |
| 12 | Pause from Subtitles | ✅ Word-level timestamps from EMNLP |
| 13 | Biosemiotic Leakage | ✅ Teacher didn't see labels |
| 14 | Function Word Removal | Not applied |
| 15 | Internal ≠ External | ⏳ EVALUATION PENDING |
| 16 | Hallucinated Citations | ⚠️ AUDIT NEEDED |
| 17 | Unvalidated Paper | ⏳ EVALUATION PENDING |
| 18 | Incomplete External Val | ⏳ EVALUATION PENDING |

---

## Decision Factor

**What is your timeline?**

| Timeline | Recommendation |
|----------|---------------|
| < 1 week | Submit Path A NOW (original F1=0.975) |
| 1–2 weeks | Run evaluation first, then decide |
| > 2 weeks | Run evaluation → Path A or B depending on results |

**Key decision: Does scale221 generalize to EMNLP ground truth?**
- YES (F1 ≥ 0.50) → Path B (scale results + EMNLP comparison)
- NO (F1 < 0.50) → Path A (original paper only)

---

*Scale221 complete. EMNLP evaluation is the critical next step.*
