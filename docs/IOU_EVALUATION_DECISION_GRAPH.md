# ChuckleNet: Definitive Decision Graph
**Date:** 2026-08-22 (rechecked after full data audit)
**Status:** 255 videos available — process all with proper labels

---

## Executive Summary

| Item | Count | Status |
|------|-------|--------|
| Audio files on Drive | 1,083 | ✅ |
| EMNLP label files (en_uk) | 261 | ✅ |
| **Videos with BOTH audio + labels** | **255** | ✅ PRIMARY TARGET |
| Audio-only (no labels) | 828 | ⚠️ Not usable |
| Labels-only (no audio) | 6 | ⚠️ Can't process |
| **Proper dataset to process** | **255** | ✅ |

---

## Data Audit Results

### What We Have on Google Drive

```
gdrive:standup4ai/
├── audio/            547 files (YouTube .m4a)
├── audio_1000/        641 files (YouTube .m4a, some overlap)
├── seq-Standup4AI/dataset/en_uk/
│   ├── emnlp+jahak/train/   EMNLP training labels (CSV, word-level BIO)
│   ├── emnlp+jahak/val/     EMNLP validation labels
│   └── Manual/test/          Manual test labels
│   Total: 530 CSV files (261 unique videos)
└── standup4ai_partition.csv  3,751 videos across 11 languages
```

### Proper Dataset: 255 Videos

**These 255 videos have BOTH audio files AND EMNLP word-level BIO labels.**

Each video has:
- Word-level timestamps (start/end per word)
- BIO labels: `O` (non-laugh), `B` (laugh begin), `I` (laugh continue), `L` (single-word laugh)
- Typically 200-1000 words per video
- Ground truth laughter segments can be reconstructed from BIO spans

### Historical Models

| Model | Videos | Labels | Result |
|-------|--------|--------|--------|
| `best_fusion_model.pt` | 87 (Gillick) | Human (22.7% pos) | F1=0.975 (held-out comedians) |
| `scale221_fusion_model.pt` | 221 (EMNLP) | Pseudo-labels (30% fallback) | CV F1=0.8793 (optimistic) |
| `top200_prosody_model.pt` | 200 (YouTube) | Energy threshold (sparse) | SATURATED — all 1.0 |

**Critical lesson:** `top200_prosody_model.pt` used `positive_class_weight=5.0` during training → model saturates to predicting 1.0 for everything. NEVER use pos_weight > 3.0.

---

## Part 2: Processing Plan — Process All 255 Videos

### Step 1: Build Training Dataset

**Goal:** Extract 791-dim features (WavLM 768 + prosody 23) for each word in all 255 videos.

**Input per video:**
- Audio: `gdrive:standup4ai/audio/{vid}.m4a` OR `gdrive:standup4ai/audio_1000/{vid}.m4a`
- Labels: `gdrive:standup4ai/seq-Standup4AI/dataset/en_uk/emnlp+jahak/{train,val}/{vid}.csv`

**Output per video:**
- `{vid}_features.npy` — shape (n_words, 791)
- `{vid}_labels.npy` — shape (n_words,) — 0/1 per word

**Feature extraction:**
```
For each word segment [t0, t1]:
  1. Load 5s audio chunk centered on word (or full word duration)
  2. Extract WavLM 768-dim embedding (GPU, ~0.1s per word)
  3. Extract prosody 23-dim (F0×5 + Energy×5 + Duration×2 + Spectral×5 + VQ×6)
  4. Concatenate → 791-dim feature vector
```

### Step 2: Train Model on 255 Videos

**Architecture:** Same FusionMLP as before
- Input: 791-dim
- MLP: 791→512→256→64→1 + BatchNorm + Dropout(0.3)
- Loss: BCEWithLogitsLoss + pos_weight ≤ 3.0
- Optimizer: AdamW, lr=1e-3

**Split:** Video-level GroupKFold (5-fold)
- Group by video ID
- Never put same video in train and val
- Train: ~204 videos, Val: ~51 videos per fold

**Expected result:** Real CV F1 on properly labeled data (not pseudo-labels)

### Step 3: External Evaluation on EMNLP Test Set

**Test set:** `Manual/test/` folder on Drive (~50 videos with manual labels)

**Metrics:**
- IoU segment-level F1 @ thresholds [0.1, 0.2, 0.3, 0.4, 0.5]
- Compare to StandUp4AI baseline: F1=0.51 @ IoU=0.2

---

## Part 3: Implementation

### Complete Processing Notebook

**File:** `Process_All_255.ipynb` (to be created)
**Runtime:** GPU (Colab T4 or A100)
**Time:** ~4-6 hours for feature extraction + training

**Cells:**
1. Setup (mount Drive, install deps)
2. Download all 255 video IDs list
3. For each video: download audio (yt-dlp fallback) + extract features + save
4. Train with 5-fold GroupKFold
5. Evaluate on test set with IoU metrics
6. Save model to Drive

### Checkpoint Strategy

```
Cell 3: Save every 20 videos
  → features/{vid}_features.npy
  → features/{vid}_labels.npy
  → checkpoint.json (list of done vids)

Cell 5: Save model locally first, then copy to Drive
  → /content/fusion_255_model.pt  (local)
  → gdrive:standup4ai/models/fusion_255_model.pt
```

---

## Part 4: Decision Tree

```
START: Process all 255 videos with proper labels
│
├─ Run GPU Colab notebook
│     Runtime: GPU (T4 or A100)
│     Time: ~4-6 hours
│     Risk: MEDIUM (download/extraction may fail on some videos)
│
├─ Expected output:
│     ├─ 255 × (features.npy, labels.npy) — ~50-100MB
│     ├─ 5-fold CV F1 on proper labels
│     ├─ fusion_255_model.pt
│     └─ IoU evaluation on test set
│
└─ Results determine next step:
      ├─ IoU-F1 ≥ 0.50 → beats StandUp4AI baseline
      │     → Submit paper with EMNLP comparison
      │
      ├─ IoU-F1 0.30–0.49 → partial generalization
      │     → Submit original F1=0.975 paper
      │
      └─ IoU-F1 < 0.30 → model struggles on external data
            → Analyze failure modes
            → May need boundary detection separate from classification
```

---

## Part 5: Critical Rules (From 18 Historical Failures)

| Rule | Value | Enforcement |
|------|-------|-------------|
| pos_weight | ≤ 3.0 | Auto-cap in loss computation |
| Min positive rate | ≥ 15% | Reject pseudo-labels below threshold |
| Held-out evaluation | Video-level split | GroupKFold, never word-level |
| Teacher model quality | F1 > 0.9 required | Only use best_fusion_model.pt |
| Saturation check | prob_std ≥ 0.01 | Warn if model predicts same class |

---

## Part 6: What NOT to Do

- ❌ Don't use `positive_class_weight > 3.0` — causes saturation
- ❌ Don't use pseudo-labels from a weak teacher (max prob < 0.7)
- ❌ Don't evaluate on training data — use held-out videos only
- ❌ Don't claim IoU comparison without proper boundary evaluation
- ❌ Don't use energy threshold alone for pseudo-labels (too sparse)

---

## Immediate Next Step

```bash
# Open this in Colab with GPU:
https://colab.research.google.com/github/Das-rebel/autonomous_laughter_prediction/blob/main/Process_All_255.ipynb

# Or create the notebook with the 255 video IDs listed
```

The 255 videos with proper audio+labels are the definitive dataset.
Process these, train properly, evaluate on held-out test set.
