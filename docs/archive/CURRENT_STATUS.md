# ChuckleNet: Multi-Modal Laughter Prediction — Current Status
**Date:** 2026-07-12
**Status:** Extracting WavLM + Prosody (21-dim) embeddings for 555 videos (~175K utterances)

---

## 📋 EXTRACTION PIPELINE (Active)

### Google Colab Notebook (RUNNING)
```
https://colab.research.google.com/github/Das-rebel/chuck-audio-notebooks/blob/main/Colab_WavLM_Prosody_Training_v2.ipynb?authuser=1
```

**What it extracts (per utterance):**
| Feature | Dimension | Source |
|---------|-----------|--------|
| WavLM | 768-dim | Attention-pooled hidden states |
| Prosody | 21-dim | F0, energy, duration, MFCC, jitter, shimmer |
| Text | 200 chars | Utterance text |
| Label | 0/1 | Laughter marker |

**Output:** `MyDrive/wavlm_prosody_utterance_v2/utterance_features.jsonl`

### Audio Locations (Google Drive)
| Folder | Files | Total |
|--------|-------|-------|
| chuckle_audio | 71 | ✅ Matched |
| chuckle_audio_all/audio | 71 | ✅ Matched |
| chuckle_audio_all/audio_all | 249 | ✅ Matched |
| chuckle_audio_all/audio_final | 429 | ✅ Matched |
| chuckle_audio_all/audio_new | 131 | ✅ Matched |
| **Total unique** | **741** | **555 with labels** |

### Extraction Settings
- **Checkpoint:** Every 25 videos
- **Resume:** Yes (loads from checkpoint.json)
- **Memory:** Streaming (on-demand audio loading)
- **Batch:** 8 utterances per WavLM inference
- **GPU:** T4 (required)
- **Est. time:** ~8 hours on T4 GPU

---

## 📊 VALIDATED RESULTS (From 71 Videos)

### Ensemble Validation ✅ (2026-06-15)
- **Ensemble F1: 0.5865** (α=0.5, thresh=0.25)
- WavLM-only F1: 0.2801 (thresh=0.5)
- Prosody-only F1: 0.0934 (thresh=0.5)
- Statistical significance: p < 0.0001, Cohen's d = 16.30

### Held-Out Per-Comedian Results
| Comedian | F1 | Positives | Rate | Status |
|----------|-----|-----------|------|--------|
| 1Nb3_os4RSA | **0.6873** | 496/812 | 61% | ✅ Valid |
| BAD4askmGgk | **0.6089** | 435/987 | 44% | ✅ Valid |
| BFIHCzw3itk | 0.0097 | 2/1001 | 0.2% | ❌ Excluded |

### Individual Models (Held-Out)
| Model | Held-Out F1 | Notes |
|-------|-------------|-------|
| XLM-R text (random split) | 0.819 | Overfits |
| XLM-R text (held-out) | 0.152 | 81% drop |
| WavLM audio (direct) | 0.280 | Audio generalizes |
| **WavLM + MLP (Kaggle)** | **0.355** | ✅ IMPROVED |
| Prosody MLP | 0.093 | Weak alone |
| **Ensemble** | **0.587** | Best generalization |

---

## 🎯 TRAINING PIPELINE (After Extraction)

### Model Architecture (Matches Working Kaggle Pipeline)
```
Input: WavLM (768) + Prosody (21)
  → Prosody Projection: Linear(21, 64) → GELU → Dropout(0.1) → Linear(64, 32)
  → Fusion: concat(768 + 32 = 800)
  → Classifier: Dropout(0.3) → Linear(800, 128) → GELU
              → Dropout(0.2) → Linear(128, 64) → GELU
              → Linear(64, 2)
Output: Logits (2-class)
```

### Training Config
- **Optimizer:** AdamW (lr=1e-3, weight_decay=0.01)
- **Scheduler:** CosineAnnealingLR
- **Loss:** CrossEntropyLoss(weight=[1.0, 2.5])
- **Epochs:** 20
- **Batch:** 256
- **Gradient clipping:** max_norm=1.0
- **Holdout:** Comedian-level (BFIHCzw3itk, BAD4askmGgk, 1Nb3_os4RSA)

---

## 📁 DATA ASSETS

### Original 71 Videos ✅
- **aligned_utterances.jsonl:** 15,000 utterances
- **WavLM embeddings:** 71 files, 15,000 embeddings (100% coverage)
- **Prosody features:** 21-dim, 14,998 samples
- **Positive rate:** 32.0%
- **Split:** Train 70%, Val 15%, Test 15% by video

### Expanded Collection (555 Videos)
- **Audio on Drive:** 555 matched videos with utterances
- **Expected utterances:** ~175,000
- **Positive rate:** ~6.1% (1,113 / 18,191 in matched subset)
- **WavLM embeddings:** In extraction (checkpoint at 25 videos)

### Local Data
```
/Users/Subho/data/chuckle-net/
├── wavlm_embeddings/          # 660 files (71 utt-level + 589 video-level)
├── wavlm_all_npy/            # 645 NPY files (VIDEO-level, not usable)
├── wavlm_utterance_embeddings/  # In progress extraction
├── fusion_dataset/           # 15K utterances (text + prosody)
└── audio/                   # 71 local audio files
```

---

## 🔑 KEY LEARNINGS (Critical)

### 1. Video-level vs Utterance-level Embeddings
- ❌ **Video-level:** 645 .npy files = one 768-dim vector per VIDEO (useless for utterance prediction)
- ✅ **Utterance-level:** One 768-dim per UTTERANCE SEGMENT (correct approach)

### 2. Audio Folders on Google Drive
- `chuckle_audio/` only has 71 files
- `chuckle_audio_all/` subfolders have the rest (249 + 429 + 131 = 809)
- Must search ALL subfolders, not just `chuckle_audio/`

### 3. Memory of Extraction Attempts
- **2026-07-09:** Extracted 645 video-level .npy files (WRONG approach)
- **2026-07-10:** Tried Colab with wrong audio path (only 71 files found)
- **2026-07-12:** Fixed - now searching all folders, extracting utterance-level

### 4. What Works (From Kaggle Pipeline)
- WavLM FROZEN (feature extractor only)
- Attention pooling over hidden states
- 21-dim prosody (NOT 9-dim)
- Class weights [1.0, 2.5] (NOT high pos_weight)
- Fusion MLP (800→128→64→2) (NOT simple 777→256→64→1)
- Streaming audio (on-demand loading)

---

## 📝 NEXT STEPS

1. **Run Colab extraction** (~8 hours on T4 GPU)
2. **Download embeddings** from Drive to local
3. **Train on 555 videos** (~175K utterances)
4. **Evaluate on held-out comedians**
5. **Submit paper** (EMNLP 2026 Industry Track)

---

## 📚 RELATED DOCS

- `VISION.md` - Project vision and research questions
- `docs/PAPER_EMNLP_AUDIO_FIRST_LAUGHTER_DETECTION.md` - Paper draft
- `docs/XLMR_STANDUP_ROADMAP.md` - XLM-R text pipeline (secondary)
- `EXTRACTION_SUMMARY_2026-07-02.md` - Previous extraction notes
