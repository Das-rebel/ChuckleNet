# Hypothesis Test Results (2026-08-25)
**Status:** COMPLETE — Validated on 118 videos with EMNLP ground truth labels

---

## Methodology

- **Data**: 118 videos from StandUp4AI en_uk with both WavLM+prosody embeddings AND EMNLP word-level BIO labels
- **Features**: 791-dim (WavLM 768 + prosody 23)
- **Aggregation**: Word-level BIO labels → 5-second window label (positive if any laugh overlap)
- **Model**: FusionMLP (791→512→256→64→1) with pos_weight=1.18
- **Split**: 5-fold GroupKFold (video-level)
- **Training**: 30 epochs with early stopping

---

## Results

### Segment-Level IoU F1

| IoU Threshold | F1 Score | vs StandUp4AI |
|:-:|:-:|:-:|
| ≥ 0.1 | 0.4557 | — |
| ≥ **0.2** | **0.3040** | Baseline=0.51 (BELOW) |
| ≥ 0.3 | 0.1792 | — |
| ≥ 0.4 | 0.1060 | — |
| ≥ 0.5 | 0.0503 | — |

### Word-Level Classification

| Metric | Value |
|--------|-------|
| Positive rate | 45.9% |
| OOF F1 | 0.6694 |
| OOF Precision | 0.6701 |
| OOF Recall | 0.7314 |

### Top Videos (IoU≥0.2)

| Video | F1@0.2 | GT segments | Pred segments |
|-------|:-:|:-:|:-:|
| BT-WOZQ5JRc | 0.6800 | 25 | 25 |
| jF6Devdvzqo | 0.6400 | 13 | 12 |
| JIWQBC8Q1e8 | 0.6250 | 8 | 8 |
| M1NDZYLSo94 | 0.6154 | 8 | 5 |
| H3Y-9-CarcQ | 0.5600 | 13 | 12 |
| lG-W3DNL4Ps | 0.5238 | 28 | 14 |

---

## Verdict: PROMISING (not yet BEATS)

The model shows real learning (F1=0.67 word-level) but IoU-F1=0.30 at threshold 0.2 is below StandUp4AI's 0.51.

**Why below baseline:**
1. Evaluation granularity: 5-second windows vs StandUp4AI's word-level segments
2. Our windows overlap (stride 2.5s) which inflates prediction count
3. Ground truth segments are ~1-3 seconds, our predictions cover full 5s windows
4. Some "predicted laugh" segments partially overlap ground truth but don't reach IoU=0.2

**What works:**
- Real classification is happening (high recall)
- Some videos achieve F1=0.68
- Pipeline is end-to-end functional

---

## Next Steps

1. ✅ Pipeline validated on 118 videos with ground truth
2. ⚠️ Performance below baseline — investigate why
3. 🔧 Try word-level features directly (not aggregated to 5s windows)
4. 🔧 Add boundary detection separate from classification
5. 📈 Scale to all 255 videos with new word-level features

