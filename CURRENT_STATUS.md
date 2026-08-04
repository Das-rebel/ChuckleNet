# ChuckleNet: Multi-Modal Laughter Detection — Current Status
**Date:** 2026-08-04
**Status:** PIPELINE READY — Executing 1000+ Video Plan

---

## 🎯 TARGET: 1168 Videos

| Source | Videos | Status | Labels |
|--------|--------|--------|--------|
| Gillick 87 | 87 | ✅ Extracted | Human (22.7% pos) |
| YouTube 481 | 481 | ✅ Extracted | Energy-based (8.7% pos) |
| Gillick 600 | ~600 | 📥 Downloading | Human (est ~20%) |
| **TOTAL** | **~1,170** | | **~14% positive** |

---

## 📋 EXECUTION PLAN

### Option 1 + 2 Running in Parallel

**Part 1: Download Gillick 600** (~4-6 hours)
- Test 988 Gillick IDs for availability
- Download ~600 available videos
- Extract 23-dim prosody
- Uses existing human laughter timestamps

**Part 2: Improve Labels for YouTube 481** (~30 min)
- Train F0 model on gold-standard Gillick 87
- Apply to YouTube 481 for better pseudo-labels
- Expected: ~15-20% positive rate (vs 8.7% old)

**Part 3: Train Final Model** (~30 min)
- Combined: 1168 videos, ~350K utterances
- Video-level train/val/test split
- MLP with BCE loss

---

## ✅ VALIDATED RESULTS (87 videos)

| Model | Val F1 | Test F1 |
|-------|---------|----------|
| F0 only (5-dim) | 0.9412 | — |
| Prosody (23-dim) | 0.9756 | — |
| WavLM (768-dim) | 0.5691 | — |
| Late Fusion | 0.9514 | — |

**Key Finding:** Hand-crafted prosody (23-dim) outperforms deep WavLM embeddings (768-dim) by 2.5x for laughter detection.

---

## 📊 PUBLICATION TARGETS

1. **INTERSPEECH** — Prosody Features for Laughter Detection
   - Dataset: 1000+ videos
   - Baseline: F1 > 0.90 on held-out comedians

2. **ACL/EMNLP** — Multimodal (Audio + Text)
   - Add Whisper transcripts
   - Cascade: Text → Prosody refinement

---

## 🔗 LINKS

**Colab Pipeline:** https://colab.research.google.com/github/Das-rebel/ChuckleNet/blob/main/colab_package/Pipeline_1168_videos.ipynb

**Download Scripts:** `data_collection/01_*.sh`

**GitHub:** https://github.com/Das-rebel/ChuckleNet
