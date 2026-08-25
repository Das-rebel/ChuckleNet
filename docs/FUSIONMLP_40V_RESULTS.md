# FusionMLP 40-Video Results (2026-08-25)
**Status:** COMPLETE — Proper architecture tested on 40 videos

---

## Methodology

- **Data**: 40 videos with word-level WavLM+prosody features (extracted on CPU)
- **Model**: FULL FusionMLP (791→512→256→64→1) WITH BatchNorm
- **Loss**: Manual weighted BCE with pos_weight=2.0
- **Split**: 5-fold GroupKFold (8 test videos per fold)
- **Optimizer**: AdamW, lr=1e-3, weight_decay=0.01
- **Epochs**: 30, batch_size=256

---

## Results

### Word-Level Classification

| Metric | Value |
|--------|-------|
| Total words | 27,992 |
| Positive rate | 12.0% |
| **OOF F1 @ 0.5** | **0.2705** |
| OOF Precision | 0.4028 |
| OOF Recall | 0.2036 |

### Per-Fold

| Fold | F1 | P | R |
|------|-----|-----|-----|
| 1 | 0.2195 | 0.4041 | 0.1507 |
| 2 | 0.2730 | 0.3930 | 0.2091 |
| 3 | 0.2585 | 0.3291 | 0.2129 |
| 4 | 0.3435 | 0.5175 | 0.2570 |
| 5 | 0.2493 | 0.3870 | 0.1839 |

### Segment-Level IoU (40 videos)

| IoU | F1 | vs StandUp4AI |
|:-:|:-:|:-:|
| ≥ 0.1 | 0.2918 | — |
| ≥ **0.2** | **0.2230** | Below 0.51 |
| ≥ 0.3 | 0.1766 | — |
| ≥ 0.4 | 0.1431 | — |
| ≥ 0.5 | 0.1212 | — |

### Top Videos at IoU ≥ 0.2

```
0zpUnJSG0EQ    F1@0.2 = 0.44
66CyaeFWucM    F1@0.2 = 0.44
AEnlxaPVtK8    F1@0.2 = 0.43
7VkAFkK3bwQ    F1@0.2 = 0.35
8eYSNXOsyoo    F1@0.2 = 0.33
-UPIA46hBZs    F1@0.2 = 0.32
5cdoHY0ziVA    F1@0.2 = 0.32
7kULz2NevT4    F1@0.2 = 0.31
6Ofc2A75zuw    F1@0.2 = 0.30
18H1aeoGybw    F1@0.2 = 0.30
```

---

## Comparison with Previous Tests

| Test | N | Model | IoU-F1@0.2 |
|------|:-:|---|:-:|
| 5-second windows (Kaggle) | 118 | New MLP, pseudo-labels | 0.30 |
| Word-level (10 videos) | 10 | SimpleMLP no BN | 0.19 |
| Word-level (30 videos) | 30 | SimpleMLP no BN | 0.19 |
| **Word-level (40 videos)** | **40** | **FULL FusionMLP + BN** | **0.22** |

**Improvement**: Better architecture (full FusionMLP with BN) + more data → 0.22 vs 0.19

---

## What's Working

- ✅ Real classification (F1=0.27 word-level)
- ✅ Some videos achieve F1=0.40+ at IoU=0.2
- ✅ Pipeline reproducible

## What's Limiting

- ❌ Below StandUp4AI baseline (0.51)
- � Recall too low (0.20) — model too conservative
- ❌ Some videos at F1=0 (3TgRGK1vrzs, 8nltoWdciws, AES4jzE513Y)

---

## Path Forward

With the **user's Batch 1 (49 videos word-level)** on Drive + more videos:
- Expected to scale to 100+ videos
- Better calibration of pos_weight
- Larger model (WavLM-large) for features
