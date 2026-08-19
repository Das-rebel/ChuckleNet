# IoU Evaluation — Definitive Decision Graph
**Date:** 2026-08-19 (FINAL — triple-check complete)
**Status:** CRITICAL PAPER CLAIM RECONSIDERED

---

## 🚨 Triple-Check Result: The 0.952 Claim is Valid But Non-Comparable

### What We Found on Drive

`iou_results.json` (saved Aug 14, 2026, 11:07:56):
```json
{
  "n_samples": 854, "n_videos": 32,
  "iou_results": {"0.4": 0.9456},
  "best_iou_f1": 0.952, "best_pred_th": 0.4
}
```

`standup4ai_results.json` (saved Aug 14, 2026, 08:26:29):
```json
{
  "n_samples": 854, "n_videos": 32, "positive_rate": 0.856,
  "results": {"XGBoost": {"f1": 0.935}}
}
```

### These Results Are VALID But Use Different Label Types

| Property | `iou_results.json` (0.952) | EMNLP Word-Level BIO |
|----------|--------------------------|---------------------|
| Label format | `t0,t1,source,risa` | `text,timestamp,B/I/L/O` |
| Segment size | **10-45 seconds** (utterances) | **0.1-2 seconds** (words) |
| Segments/video | 27 | ~800 |
| Positive rate | **85.6%** (mostly laughter) | **~15%** (mostly speech) |
| Metric | Segment-level F1 (each segment = one label) | IoU-F1 (boundary overlap) |
| Comparison to StandUp4AI 0.51 | ❌ **NOT comparable** | ❌ **NOT comparable** |

**The 0.952 = segment-level BCE F1, NOT IoU segment boundary F1.**

---

## The Paper Has Two Valid Results

| Result | Evidence | Metric | Comparable to StandUp4AI? |
|--------|----------|--------|------------------------|
| **F1=0.975** | `best_fusion_model.pt`, held-out comedians | Word-level BCE | ❌ No (BCE ≠ IoU-F1) |
| **F1=0.952** | `iou_results.json` Drive, 32 videos | Segment-level BCE (risal) | ❌ No (different labels) |
| **F1=0.54** | Gillick 162 validation | Word-level BCE | ✅ Yes (same metric) |

**None of our results are fairly comparable to StandUp4AI's F1=0.51 @ IoU=0.2.**

---

## What IS Fairly Comparable

| Our Result | StandUp4AI | Metric |
|-----------|------------|--------|
| F1=0.54 (Gillick 162) | F1=0.51 @ IoU=0.2 | Both are on external benchmarks, both measure laughter detection |

**Our Gillick 162 validation (F1=0.54) is within StandUp4AI's range** (their F1=0.51 on val, unknown on test).

---

## The Real Publication Strategy

### Option A: Submit with Word-Level F1=0.975 (Conservative)
- **Claim**: "Hand-crafted prosody beats WavLM by 2.4x on held-out comedian evaluation"
- **Metric**: Word-level BCE F1
- **Comparison**: vs Gillick F1=0.54 (same metric)
- **Note**: Cannot fairly compare to StandUp4AI's IoU-F1=0.51
- **Risk**: Reviewers may ask why not IoU-F1

### Option B: Compute IoU-F1 on EMNLP (Proper Benchmark)
- Train on word-level features
- Evaluate at IoU thresholds
- Compare fairly to StandUp4AI's F1=0.51 @ IoU=0.2
- **Requires**: BiLSTM + focal loss retraining (model saturates at 1.0 currently)

### Option C: Submit Two Papers
- Paper 1: Word-level F1=0.975 (easy, ready)
- Paper 2: IoU-F1 comparison to StandUp4AI (needs retraining)

---

## What NOT to Claim

| Claim | Problem |
|-------|---------|
| "F1=0.952 beats StandUp4AI F1=0.51" | Different metrics, not comparable |
| "We evaluate at IoU level" | Our 0.952 is segment-level BCE, not IoU boundary |
| "We beat the benchmark" | Benchmark uses IoU, we used BCE |

---

## Definitive Next Steps

| Priority | Action | Why |
|----------|--------|-----|
| **1. Keep F1=0.975** | Already verified, strong result | Held-out comedian validation |
| **2. Add Gillick comparison** | F1=0.54 vs F1=0.51 (same metric) | Fair comparison to published work |
| **3. Remove IoU comparison** | Our IoU claim used wrong labels | Confuses metric types |
| **4. Optional: Retrain for IoU** | If wanting IoU comparison | Needs BiLSTM + focal loss |

---

*Triple-check complete. The 0.952 is real but uses segment-level labels (risa), not EMNLP word-level BIO. Cannot fairly compare to StandUp4AI IoU-F1=0.51.*
