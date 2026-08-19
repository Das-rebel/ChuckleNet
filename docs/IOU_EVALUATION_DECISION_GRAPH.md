# IoU Evaluation — Definitive Decision Graph
**Date:** 2026-08-19 (updated after triple-check)
**Status:** AUDIT COMPLETE — critical paper claims UNVERIFIED

---

## 🚨 CRITICAL FINDING: Paper Claims Are Unverified

### What the Paper Claims vs What Exists

| Paper Claim | Source Notebook | Outputs Saved? | Actually Verified? |
|-------------|----------------|----------------|-------------------|
| F1=0.952 @ IoU=0.4 | `IoU_Evaluation.ipynb` (XGBoost, 20-dim) | ❌ **NO** | Unknown |
| F1=0.935 (segment-level) | `StandUp4AI_Fixed.ipynb` | ❌ **NO** | Unknown |
| F1=0.975 (held-out comedians) | `experiments/best_fusion_model.pt` | ✅ YES | ✅ Valid |
| F1=0.54 on Gillick 162 | Literature comparison | ✅ YES | Valid (different metric) |

**The paper's headline IoU result (F1=0.952) was NEVER saved or verified.**

---

## What Actually Exists vs What We Ran

| Evaluation | Model | Dataset | Result | Status |
|-----------|--------|---------|--------|--------|
| This session (Aug 19) | top200_prosody_model.pt (MLP, 15-dim) | 10 EMNLP videos | F1=0.15 @ IoU=0.3 | ✅ Verified |
| `IoU_Evaluation.ipynb` (Aug 14) | XGBoost (20-dim spectral) | ~32 videos | F1=0.952 claimed | ❌ No outputs |
| Word-level BCE | best_fusion_model.pt | 87 videos held-out | F1=0.975 | ✅ Valid |
| Word-level XLM-R | xlmr_standup_word_level.py | EMNLP | IoU-F1=0.50 stuck | ✅ Verified |

---

## Confirmed Findings (This Session)

### 1. Model Saturation
- `top200_prosody_model.pt` outputs **1.0 for ALL words** (min=max=mean=1.0, std=0.0)
- Root cause: `pos_weight=5.0` (47% over natural ratio of 3.4)
- Features ARE discriminative (f0_mean, rms, mfcc1 all p<0.0001) but model ignores them

### 2. Label Granularity Mismatch
- Training: **Utterance-level** labels (22.7% positive)
- Evaluation: **Word-level** BIO labels (EMNLP)
- These measure different things — not comparable without retraining

### 3. Metric Mismatch (Already Known)
- Word-level BCE F1 ≠ IoU segment-level F1
- Cannot fairly compare to StandUp4AI's F1=0.51 @ IoU=0.2

### 4. Past IoU Work (Pre-existing)
- `cascade_architecture.py`: IoU-F1 stuck at 0.50 for XLM-R word-level cascade
- `word-level XLM-R cascade`: stuck at IoU-F1=0.50 (documented in CLEAN_PROJECT_PLAN)
- BiLSTM fix recommended but NEVER trained

---

## Agent Council Final Recommendations

### Agent 1 (ML Architect) — Priority A
> **Run XGBoost IoU notebook first** — verify whether 0.952 actually exists before making any other decision. All downstream decisions depend on this.

### Agent 2 (Paper Reviewer)
> **Submit with word-level F1=0.975 only.** Remove unverified 0.952 IoU claim entirely. The word-level BCE result is valid and strong on its own.

---

## Definitive Next Steps (Priority Order)

### 🔴 Priority 1: Verify 0.952 IoU Claim
```
Run IoU_Evaluation.ipynb (XGBoost) on Colab:
- It uses 20-dim spectral features + GradientBoostingClassifier
- If it produces F1=0.952 → paper claim is VALID
- If it produces F1<0.5 → paper claim is WRONG, must revise
```
**Action:** Open `IoU_Evaluation.ipynb` on Colab, run end-to-end, verify outputs.

### 🟡 Priority 2: Fix MLP Saturation (if Priority 1 confirms)
```
Only if XGBoost IoU confirms 0.952:
- Retrain with BiLSTM + focal loss + pos_weight=2.5
- Match or beat XGBoost IoU result
- Add to paper as improved result
```

### 🟢 Priority 3: Submit Paper (Conservative Path)
```
If Priority 1 cannot reproduce 0.952:
- Remove all IoU comparison claims
- Submit with word-level F1=0.975 only
- Compare fairly to Gillick F1=0.54 (same metric)
- Note: StandUp4AI F1=0.51 uses IoU, not directly comparable
```
**Action:** Revise paper to remove unverified IoU claims.

---

## What NOT to Do

| ❌ Don't | ✅ Do Instead |
|----------|-------------|
| Claim 0.952 without running the notebook | Verify first |
| Compare word-level F1=0.975 to IoU-F1=0.51 | Use same metric or don't compare |
| Try to fix the MLP without verifying XGBoost result | Run XGBoost notebook first |
| Submit paper with unverified results | Submit only verified results |

---

## Files Referenced

| File | Purpose |
|------|---------|
| `IoU_Evaluation.ipynb` | XGBoost IoU evaluation (UNVERIFIED) |
| `StandUp4AI_IoU_Evaluation.ipynb` | MLP evaluation (F1=0.15, verified) |
| `StandUp4AI_IoU_Evaluation_v2.ipynb` | BiLSTM + focal loss fix recipe |
| `best_fusion_model.pt` | Valid F1=0.975 (utterance-level) |
| `cascade_architecture.py` | Past IoU-F1=0.50 diagnosis |
| `paper_f0_breakthrough.md` | Paper with unverified claims |

---

*Triple-check complete. Next action: Run `IoU_Evaluation.ipynb` on Colab to verify 0.952 claim.*
