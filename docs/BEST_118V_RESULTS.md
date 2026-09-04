# Best 118-Video Results (2026-08-26)
**Status:** Best IoU-F1 achieved: **0.3302** at IoU=0.2 (merge threshold = 0.8)

---

## Methodology

- **Data**: 118 videos (intersection of scale221 embeddings + EMNLP labels)
- **Features**: 791-dim (WavLM 768 + prosody 23) per 5-second segment
- **Model**: Standard FusionMLP (791→512→256→64→1) with BatchNorm
- **Training**: 50 epochs, lr=1e-3, batch=256, pos_weight=2.0
- **Split**: 5-fold GroupKFold (video-level)
- **Threshold optimization**: merge_threshold sweep {0.5, 0.6, 0.7, 0.8}

---

## Results

### Word-Level

| Metric | Value |
|--------|-------|
| Total segments | 11,161 |
| Positive rate | 45.9% |
| **OOF F1 @ 0.5** | **0.6783** |
| Improvement vs 30 ep | +0.002 |

### Segment-Level IoU (Threshold Sweep)

| merge_th | IoU>=0.1 | IoU>=0.2 | IoU>=0.3 | IoU>=0.4 | IoU>=0.5 |
|:-:|:-:|:-:|:-:|:-:|:-:|
| 0.5 | 0.4609 | 0.3185 | 0.1872 | 0.1030 | 0.0503 |
| 0.6 | 0.4642 | 0.3207 | 0.1939 | 0.1072 | 0.0527 |
| 0.7 | 0.4657 | 0.3258 | 0.1968 | 0.1109 | 0.0573 |
| **0.8** | **0.4587** | **0.3302** | **0.2105** | **0.1206** | **0.0651** |

### Best Configuration

- **merge_th = 0.8** (higher threshold = only confident predictions form segments)
- **IoU-F1@0.2 = 0.3302** (best result so far)
- StandUp4AI baseline: 0.51 (gap = 0.18)

---

## Key Insight: Higher Merge Threshold Helps

- Using **merge_threshold=0.5** (default): only confident >0.5 segments
- Using **merge_threshold=0.8**: only very confident >0.8 segments
- Higher threshold = fewer false positive segments = better IoU match

The model produces high-confidence predictions around laugh boundaries.
Lower confidence predictions are noise that hurts IoU matching.

---

## Next Step

The 0.33 result confirms:
1. ✅ Architecture works (F1=0.678 word-level)
2. ✅ Threshold tuning improves IoU (0.30 → 0.33)
3. ❌ Still below StandUp4AI 0.51 by 0.18

**To close the gap:**
- More videos (user's Batch 1 + Kaggle data)
- Better features (WavLM-large)
- Explicit boundary detection
