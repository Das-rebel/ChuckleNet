# Scale Notebook — Run Instructions
**Date:** 2026-08-19
**Pipeline:** ChuckleNet_Scale500_GPU.ipynb
**Storage:** Google Drive (all outputs persist)

---

## Pre-Flight Checklist

| Item | Status | Action |
|------|--------|--------|
| Fusion model on Drive | ✅ | `gdrive:standup4ai/experiments/best_fusion_model.pt` (2.1MB) |
| Drive space | ✅ 4.4 TiB free | No action needed |
| Partition CSV on Drive | ✅ | `gdrive:standup4ai/standup4ai_partition.csv` (3,751 videos) |
| EMNLP labels on Drive | ✅ | `gdrive:standup4AI/seq-Standup4AI/dataset/` (261 label files) |
| Colab notebook | ✅ | GitHub URL below |
| Local disk space | N/A | Colab VM has 75GB+ |

---

## Step-by-Step: Run on Colab

### Step 1: Open Notebook
```
https://colab.research.google.com/github/Das-rebel/ChuckleNet/blob/15a241b/ChuckleNet_Scale500_GPU.ipynb
```
**[→ Open in Colab](https://colab.research.google.com/github/Das-rebel/ChuckleNet/blob/15a241b/ChuckleNet_Scale500_GPU.ipynb)**

### Step 2: Set GPU Runtime
1. Click **Runtime** → **Change runtime type**
2. Select **T4 GPU** (or A100 if available)
3. Click **Save**

### Step 3: Mount Drive (Cell 1 — runs automatically)
```python
from google.colab import drive
drive.mount('/content/drive', force_remount=True)
```
⚠️ Authenticate with your Google account when prompted.

### Step 4: Run All Cells (in order)

Run each cell by clicking the play button or pressing `Shift+Enter`:

| Cell | What It Does | Time |
|------|--------------|------|
| **Cell 1** | Mount Drive + install deps | ~2 min |
| **Cell 2** | Find 300 new video IDs from partition | instant |
| **Cell 3** | Download 300 audio files (yt-dlp) | ~90 min |
| **Cell 4** | Load WavLM on GPU | ~30 sec |
| **Cell 5** | Define feature extractors (791-dim) | instant |
| **Cell 6** | Extract WavLM+Prosody embeddings | ~30 min |
| **Cell 7** | Load fusion model + pseudo-label | ~5 min |
| **Cell 8** | Retrain fusion model (GroupKFold) | ~15 min |
| **Cell 9** | Save model + results to Drive | ~1 min |

**Total runtime:** ~2.5 hours

---

## Drive Storage Layout (what gets saved)

```
gdrive:standup4ai/
├── scale500/
│   ├── candidates.json              # 300 video IDs to download
│   ├── download_checkpoint.json     # which videos downloaded
│   ├── audio/                      # m4a files (~1.5GB for 300)
│   ├── embeddings/                 # {vid}.npy files (~800MB)
│   │   ├── {vid1}.npy              # (n_segs, 791)
│   │   └── ...
│   ├── extract_checkpoint.json      # which videos processed
│   ├── results.json                # final CV results
│   └── fusion_model_local.pt       # saved locally first
└── experiments/
    └── best_fusion_model.pt        # 2.1MB (already there)
```

---

## If Colab Disconnects

The notebook saves checkpoints to Drive **every 20 videos**. To resume:

1. Reopen the notebook
2. Set GPU runtime again
3. Run all cells from the top
4. Cell 3 will skip already-downloaded files
5. Cell 6 will skip already-processed embeddings
6. Training resumes from last checkpoint

---

## Expected Outputs

### Cell 8 (Training) — What You'll See

```
Training on 50000 segments from 300 videos

Fold 1
  pos_rate=0.223, pos_weight=3.00
  epoch 1: F1=0.812
  epoch 5: F1=0.931 (early stop)
  F1=0.931 P=0.895 R=0.971

Fold 2
  ...

=== CV F1: 0.927 +/- 0.008 ===
```

### Cell 9 (Save) — What Gets Written

```json
{
  "n_videos": 300,
  "n_segments": 50000,
  "positive_rate": 0.22,
  "cross_val_f1": 0.927,
  "cross_val_std": 0.008,
  "fold_f1s": [0.931, 0.922, 0.919, 0.934, 0.928]
}
```

Saved to: `gdrive:standup4ai/scale500/results.json`

Model saved to: `gdrive:standup4ai/experiments/scale500_fusion_model.pt`

---

## Saturation Guard

Cell 8 includes a **saturation check**. If you see:

```
WARNING: Model appears saturated! prob_std=0.000123
Sample probs: min=0.9999, max=1.0000
```

This means the model is predicting the same class for everything — a sign of:
1. Positive rate < 15% in training data, OR
2. pos_weight too high

The notebook will warn you but continue running. Check `results.json` for actual F1.

---

## Local Mac Disk Space

Your Mac only has 5.8GB free. **This doesn't matter for Colab** — the Colab VM has 75GB+ and all outputs go to Drive.

If you want to free local space later:
```bash
# Move old raw audio to external drive or delete:
rm -rf /Users/Subho/data/chuckle-net/audio_final/  # 7.9GB
rm -rf /Users/Subho/data/chuckle-net/audio/         # 3.2GB
```
**Don't delete** `experiments/` or `models/` — those are needed locally too.

---

## After Completion

Once the notebook finishes:

1. **Download results from Drive:**
   - `gdrive:standup4ai/scale500/results.json`
   - `gdrive:standup4ai/experiments/scale500_fusion_model.pt`

2. **Update decision graph** with new F1 scores

3. **Compare to baseline:**
   - Baseline: F1=0.975 (87 videos)
   - Scale: F1=? (300 videos)
   - If scale F1 ≥ 0.95 → stronger paper
   - If scale F1 < 0.90 → investigate why
