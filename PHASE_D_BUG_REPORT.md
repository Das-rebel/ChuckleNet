# Phase D Notebook — Bug Audit Report

**Date:** 2026-06-01
**File:** `ChuckleNet_PhaseD_AttentionPooling_Engram.ipynb`
**Status:** All 7 bugs fixed, pushed to GDrive

---

## Bugs Found & Fixed

### 🔴 CRITICAL (would crash on Colab)

| # | Bug | Cell | Fix |
|---|-----|------|-----|
| 1 | `F.softmax` used in MLA class but `torch.nn.functional` never imported as `F` | 6 | Added `import torch.nn.functional as F` to Setup cell |
| 2 | `prosody_dim=52` default but `extract_prosody()` returns **55** features | 7, 8 | Changed default to `prosody_dim=55` |
| 3 | Classifier expects 192-dim input but gets 128-dim when `prosody_feats=None` | 7 | Added `_engram_to_classifier` projection layer |
| 4 | Ablation passes `use_engram=False` but PhaseDModel has no such parameter — engram always applied | 7, 14 | Added `use_engram` param, conditional engram creation/forward |

### 🟡 IMPORTANT (would degrade results)

| # | Bug | Cell | Fix |
|---|-----|------|-----|
| 5 | Dead `BCEWithLogitsLoss` code — wrong loss for 2-output model (should be CrossEntropy) | 10 | Removed unused `criterion` definition |
| 6 | Prosody features not standardized — F0 (~100-500), MFCC (~±100), pause (~0-3) on vastly different scales | 10, 11, 14 | Added `StandardScaler` fit on train, transform on train/val/test |
| 7 | `CosineAnnealingWarmRestarts.step()` missing `epoch` argument | 10 | Changed to `scheduler.step(epoch)` |

### 🟢 CLEANUP

| # | Issue | Fix |
|---|-------|-----|
| 8 | Two source lines had `\\",` (double backslash) making JSON unparseable | Fixed raw JSON |

---

## Files Updated

1. `ChuckleNet_PhaseD_AttentionPooling_Engram.ipynb` — All fixes applied
2. Pushed to `gdrive:chuckle_checkpoints/ChuckleNet_PhaseD_AttentionPooling_Engram.ipynb`

---

## How to Run on Colab

1. Open the notebook: https://colab.research.google.com/
   → File → Open notebook → Google Drive → `chuckle_checkpoints/ChuckleNet_PhaseD_AttentionPooling_Engram.ipynb`

2. **Runtime → Change runtime type → GPU (T4)**

3. **Run all cells in order 0→14** (Ctrl+F9 or Runtime → Run all)

   - Cells 0-9: Setup, build model, extract prosody (~15 min)
   - Cell 10: Main training (CSA+Engram, 8 epochs, ~30 min on T4)
   - Cell 11: Threshold sweep evaluation
   - Cell 12: Plot results
   - Cell 14: Ablation study (4 variants × 5 epochs each, ~60 min)

4. **Expected outputs:**
   - `phaseD_best.pt` checkpoint saved to GDrive
   - `phaseD_results.png` plot saved to GDrive
   - Val F1 printed per epoch

---

## Success Criteria

| Metric | Threshold | Meaning |
|--------|-----------|---------|
| Val F1 (best epoch) | > 0.65 | Partial unfreeze is helping |
| Val F1 (best epoch) | > 0.70 | Theory D confirmed — frozen encoder was the root cause |
| Test F1 (best threshold) | > 0.72 | Audio model generalizes |
| Test F1 (best threshold) | > 0.819 | **Audio beats text-only** — new SOTA |

## If Val F1 < 0.65

The partial unfreeze didn't fix it. Possible next steps:
1. Unfreeze MORE layers (try last 8 or all 12)
2. Try Whisper encoder instead of WavLM
3. Check if data loading is wrong (audio files actually exist)
