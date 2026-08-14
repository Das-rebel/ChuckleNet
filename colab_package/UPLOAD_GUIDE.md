# Colab Upload Guide for Laughter Prediction Training

## Quick Start

### Step 1: Open Google Colab
Go to: https://colab.research.google.com/

### Step 2: Upload Files
1. Upload `standup4ai_training_colab.ipynb`
2. Upload all 4 CSV files from `colab_package/standup4ai_data/`

### Step 3: Enable GPU
- Runtime → Change runtime type → **GPU** (T4 or better)

### Step 4: Run
- Run all cells (Ctrl+F9 or Runtime → Run all)

---

## Files to Upload

```
1. standup4ai_training_colab.ipynb  (24KB)
2. -1FrUOEswOk.csv  (French - 1,052 words)
3. 0g7nezWZyfY.csv  (English - 1,054 words)
4. 1xvwYZwm8Ig.csv  (English - 811 words)
5. 6JQzl2LlXbQ.csv  (Spanish - 286 words)
```

---

## Expected Training Time
- GPU (T4): ~15-20 minutes for 5 epochs
- Expected Val F1: 0.70-0.80

---

## After Training Completes

1. Download trained model (auto-saves to Google Drive)
2. Download `metrics.json` with F1 scores
3. Proceed to `rl_laughter_prediction_colab.ipynb` for Phase 2

---

## Alternative: Use RL Prediction Notebook Directly

If you want to train on full V8.1 data (12,048 examples):

1. Upload `rl_laughter_prediction_colab.ipynb`
2. Download V8.1 data from project
3. Run with GPU (expect ~1-2 hours for 10 epochs)

---

## Gist Link (for reference)
https://gist.github.com/Das-rebel/cc046ead3740e465481f6f28ad0880d6