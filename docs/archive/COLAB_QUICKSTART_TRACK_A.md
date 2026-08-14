# Track B: Colab Quickstart — Phase A + Prosody Fusion

**Goal:** Validate whether frozen WavLM + attention pooling + prosody fusion improves on MiniLM baseline (Test F1=0.502)

**Runtime:** Python 3, GPU (T4 or higher)

---

## Files on Google Drive

| File | Size | Purpose |
|------|------|---------|
| `wavlm_phaseA_best.pt` | 361 MB | Best Phase A WavLM checkpoint |
| `wavlm_phaseA_final.pt` | 361 MB | Final Phase A checkpoint |
| `prosody_phaseD.json` | 5.2 MB | 21-dim prosody features |
| `phaseA_best.pt` | 1.06 GB | Full Phase A model |
| `ChuckleNet_PhaseA_Prosody_Fusion.ipynb` | 21 KB | Colab notebook |

**Notebook path:** `gdrive:chuckle_checkpoints/ChuckleNet_PhaseA_Prosody_Fusion.ipynb`

---

## Colab Setup

1. Open Google Colab: https://colab.research.google.com/
2. Mount Google Drive:
   ```
   from google.colab import drive
   drive.mount('/content/drive')
   ```
3. Navigate to notebook: `drive/MyDrive/chuckle_checkpoints/ChuckleNet_PhaseA_Prosody_Fusion.ipynb`

---

## Expected Runtime

- Dataset loading: ~5 min
- Prosody loading: ~2 min  
- WavLM inference (1000 videos): ~30 min with T4 GPU
- Training (10 epochs): ~20 min

**Total:** ~1 hour

---

## What This Validates

- [ ] Does WavLM (frozen) + prosody beat MiniLM text-only (F1=0.502)?
- [ ] Does Phase A approach scale to full dataset?
- [ ] What's the real Test F1 for WavLM + prosody fusion?

---

## If It Works

- Establish WavLM as audio backbone
- Move to cascade Stage 2 (prosody boundary refinement)
- Integrate with XLM-R text for combined model

## If It Doesn't

- WavLM may not help beyond text features
- Focus on text-only cascade improvement
- Consider lighter audio features (pause/F0 only)
