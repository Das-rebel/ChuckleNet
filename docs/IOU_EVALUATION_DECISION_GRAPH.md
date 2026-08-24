# ChuckleNet: Definitive Decision Graph
**Date:** 2026-08-24 (triple-checked against actual work)
**Status:** Batch 1 complete (49/50) — 4 batches remaining, then train

---

## Executive Summary

| Item | Status |
|------|--------|
| Dataset | ✅ 255 videos (audio + EMNLP labels) confirmed |
| Platform | ✅ **Colab T4 GPU** (Kaggle P100 incompatible) |
| Notebook | `Process_All_255_Colab.ipynb` |
| **Batch 1** | ✅ **49/50 processed** (~35K words extracted) |
| Batches remaining | ⏳ 4 more (videos 51–255) |
| Features location | Google Drive: `standup4ai/features_255/` |
| Training notebook | `Train_Fusion_255.ipynb` (fixed to read from Drive) |

---

## Current Stage: Feature Extraction

### What's Done

| Batch | Videos | Status | Output |
|-------|--------|--------|--------|
| 1 | 1–50 | ✅ **49/50 done** | ~35K words, saved to Drive |
| 2 | 51–100 | ⏳ Next (`BATCH_NUM=2`) | — |
| 3 | 101–150 | ⏳ Pending | — |
| 4 | 151–200 | ⏳ Pending | — |
| 5 | 201–255 | ⏳ Pending (55 videos) | — |

### Batch 1 Results

- Avg ~73s per video on T4 GPU
- Word counts: 135–1209 per video
- Laugh rates: 2.9% – 30.7% per video
- No errors, no missing audio or labels

### How to Continue Processing

```
1. Open: Process_All_255_Colab.ipynb in Colab (T4 GPU)
2. Cell 3: Set BATCH_NUM = 2
3. Run Cells: 1 → 2 → 3 → 4 → 5
4. Check Cell 6 for total progress
5. Repeat with BATCH_NUM = 3, 4, 5
```

Each batch takes ~60 minutes.

---

## Pipeline Architecture (Verified)

```
Process_All_255_Colab.ipynb          Train_Fusion_255.ipynb
┌─────────────────────────┐         ┌──────────────────────────┐
│ Mounts Google Drive     │         │ Mounts Google Drive      │
│ Reads labels from Drive │         │ Reads features from Drive│
│ Gets audio (Drive+yt-dlp)│        │ Trains FusionMLP         │
│ Extracts WavLM+prosody  │  ───►   │ 5-fold GroupKFold       │
│ Saves to Drive:         │         │ Evaluates IoU           │
│   features_255/*.npy    │         │ Saves model to Drive    │
└─────────────────────────┘         └──────────────────────────┘
```

### Data Flow

```
Google Drive                          Colab GPU
gdrive:standup4ai/
├── audio/{vid}.m4a  ──────►  WavLM(768) + prosody(23)
├── seq-Standup4AI/...csv ──►  word-level BIO labels
│                                    │
│                                    ▼
├── features_255/  ◄────────── {vid}_features.npy (n_words, 791)
│   (saved to Drive)           {vid}_labels.npy   (n_words,)
│                                    │
│                                    ▼
├── models/fusion255_model.pt ◄── FusionMLP trained
```

---

## Platform Decision Matrix

| Platform | GPU | Compute Cap | PyTorch Default | WavLM Works? |
|----------|-----|-------------|-----------------|--------------|
| **Colab T4** | Tesla T4 | sm_75 | 2.x+cu121 | ✅ Native |
| Kaggle P100 | Tesla P100 | sm_60 | 2.10+cu128 | ❌ CUDA error |
| Kaggle T4 | Tesla T4 | sm_75 | 2.10+cu128 | ❓ Untested |

**Decision:** Use **Colab T4** — it works natively, no dependency hacks needed.

---

## Historical Models Comparison

| Model | Videos | Labels Type | Result | Trustworthy? |
|-------|--------|-------------|--------|-------------|
| `best_fusion_model.pt` | 87 (Gillick) | Human (22.7%) | F1=0.975 | ✅ Yes |
| `scale221_fusion_model.pt` | 221 | Pseudo-labels (30%) | CV F1=0.8793 | ⚠️ Optimistic |
| `top200_prosody_model.pt` | 200 | Energy threshold | SATURATED | ❌ Broken |
| **fusion_255 (pending)** | **255** | **EMNLP ground truth** | **TBD** | **Will be definitive** |

The fusion_255 model will be trained on **proper EMNLP ground truth labels**, not pseudo-labels. This is the first properly-labeled model at this scale.

---

## After Training Completes: Decision Tree

```
Train_Fusion_255.ipynb produces:
  CV F1 + IoU evaluation results
           │
           ├─ IoU-F1 ≥ 0.50 @ IoU=0.2
           │     → BEATS StandUp4AI baseline (F1=0.51)
           │     → Submit paper with EMNLP comparison
           │     → "When Simple Beats Deep" narrative holds
           │
           ├─ IoU-F1 0.30–0.49
           │     → Partial generalization
           │     → Submit original F1=0.975 paper
           │     → Include fusion_255 as supplementary result
           │
           └─ IoU-F1 < 0.30
                 → Model struggles on external data
                 → Analyze: is it boundary detection or classification failing?
                 → May need separate classification head from boundary head
                 → Submit original paper only
```

---

## Critical Rules (Enforced)

| Rule | Value | Where Enforced |
|------|-------|---------------|
| pos_weight ≤ 3.0 | Auto-cap | Train notebook, loss computation |
| Video-level split | GroupKFold | Train notebook |
| Saturation check | prob_std ≥ 0.01 | Train notebook |
| Features on Drive | Persistent | Process notebook saves to Drive |
| Label lookup pre-built | Dict not walk | Process notebook Cell 2 |

---

## Known Issues (Resolved)

| # | Issue | Root Cause | Fix Applied |
|---|-------|-----------|-------------|
| 1 | All videos silently skipped | `find_label()` returned None without reporting | Pre-built LABEL_LOOKUP dict |
| 2 | Audio double extension `.wav.wav` | yt-dlp `-o` template included ext | Removed ext from template |
| 3 | Labels not found on Kaggle | Nested dataset path `/kaggle/input/datasets/...` | Hardcoded correct path |
| 4 | CUDA error on P100 | PyTorch 2.10 doesn't support sm_60 | Switched to Colab T4 |
| 5 | Missing imports across cells | Variables don't persist in Kaggle execution | All imports in Cell 1 |
| 6 | 75% of words dropped | Min duration/chunk too strict | Lowered to 0.005s / 0.01s |
| 7 | Training can't find features | Saved to Drive but training looked locally | Fixed to mount Drive |

---

## Immediate Next Steps

### Step 1: Complete Feature Extraction (4 batches remaining)

```bash
# Open in Colab:
https://colab.research.google.com/github/Das-rebel/autonomous_laughter_prediction/blob/main/Process_All_255_Colab.ipynb

# For each batch (2, 3, 4, 5):
#   1. Set BATCH_NUM = <N> in Cell 3
#   2. Runtime → Change runtime type → T4 GPU
#   3. Run all cells
#   4. Wait ~60 min
#   5. Check Cell 6 output
```

### Step 2: Train Model (after all batches)

```bash
# Open in Colab:
https://colab.research.google.com/github/Das-rebel/autonomous_laughter_prediction/blob/main/Train_Fusion_255.ipynb

# Requires: ≥10 feature files on Drive
# Runtime: T4 GPU
# Time: ~15 min
```

### Step 3: Evaluate Results

Compare CV F1 and IoU-F1 to StandUp4AI baseline (F1=0.51).
Results determine paper submission path.
