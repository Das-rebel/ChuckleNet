# ChuckleNet: Multi-Modal Laughter Prediction — Current Status

**Date:** 2026-08-03
**Status:** KEY FINDING PUBLISHED - Multimodal Fusion Confirmed

---

## 🏆 KEY FINDING: Multimodal Fusion Works

### Final Results (Video-Level Holdout)

| Model | F1 | Notes |
|-------|-----|-------|
| **Prosody + Text (Combined)** | **0.988** | Best - captures both HOW and WHAT |
| Prosody only | 0.977 | Acoustic features dominant |
| Text only | 0.861 | Semantic/conversational context |
| WavLM | 0.569 | Deep embeddings underperform |

### What Each Modality Captures

- **Prosody**: HOW it's said (pitch, energy, duration, rhythm)
- **Text**: WHAT's said (topic, markers, conversational structure)
- **Combined**: Both dimensions of laughter

---

## 📊 Dataset

| Metric | Value |
|--------|-------|
| Total videos | 87 |
| Total utterances | 21,468 |
| Positive (laughter) | 4,883 (22.7%) |
| Labels | Gillick et al. human-verified |

---

## 🔬 Experiments Conducted

### Prosody Feature Analysis
- 23-dim prosody features extracted per utterance
- F0 (pitch) is the most predictive single feature group
- Energy features capture loudness of laughter
- Duration features capture speech rhythm

### Text Feature Analysis
- 8-dim text features from Whisper transcription
- Laughter markers, conversational structure, topic indicators
- Text alone achieves F1=0.86

### WavLM Analysis
- 768-dim embeddings from WavLM-Base
- F1=0.57 - deep embeddings underperform
- Domain mismatch with AudioSet pretraining

### Combined Analysis
- Prosody + Text = F1=0.988 (best)
- Text adds 1.1% over prosody alone
- Multimodal fusion captures complementary information

---

## 📝 Paper

**Location:** `docs/paper_final.md`

**Key claims:**
1. Prosody outperforms WavLM (0.977 vs 0.57)
2. Text adds value (+1.1% over prosody alone)
3. Combined model achieves best results

---

## 🎯 Next Steps

1. Submit paper to arXiv
2. Test on external dataset (StandUp4AI)
3. Scale to more videos with pseudo-labeling

---

## 📁 Key Files

- `data/prosody_aligned/wavlm_training_data_expanded.npz` - Combined prosody + WavLM + labels
- `docs/paper_final.md` - Paper draft
- `training/extract_f0_all_668.py` - F0 extraction script
