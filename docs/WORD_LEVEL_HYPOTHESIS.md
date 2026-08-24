# Word-Level Hypothesis Test Results (2026-08-25)

**Status:** COMPLETE — 10 videos extracted locally on CPU

---

## Methodology

- **Data**: 10 videos downloaded from Drive, word-level WavLM+prosody features extracted
- **Model**: Simple MLP (256→64→1, no BatchNorm to avoid NaN issues)
- **Split**: 5-fold GroupKFold (video-level)
- **Hardware**: Mac CPU only (no GPU)

---

## Results

### Segment-Level IoU F1

| IoU | F1 | vs StandUp4AI |
|:-:|:-:|:-:|
| ≥ 0.1 | 0.2039 | — |
| ≥ 0.2 | 0.1915 | Below 0.51 |
| ≥ 0.3 | 0.1757 | — |
| ≥ 0.4 | 0.1098 | — |
| ≥ 0.5 | 0.0857 | — |

### Word-Level F1
- OOF F1 @ 0.5 = 0.0738 (very low)
- Train F1 (final epoch) = 0.2271 (model not learning well)

---

## Why Below StandUp4AI

1. **Tiny dataset**: 10 videos = 8,627 words
2. **NaN input features**: 48 NaN values from librosa.pyin failures
3. **No BatchNorm** (had to disable due to small batch issues)
4. **Class imbalance**: Some videos have <5% positive (3new05S61w4 has 2.9%)

---

## Comparison with 5-second Window Test

| Test | N videos | IoU-F1 @0.2 | Word F1 |
|------|:-:|:-:|:-:|
| 5-second window (118 videos) | 118 | 0.3040 | 0.6740 |
| Word-level (10 videos) | 10 | 0.1915 | 0.0738 |

**Insight**: With MORE data (118 vs 10), word-level F1 is much higher (0.67 vs 0.07). The model learns better with more data, not necessarily better granularity.

---

## Recommended Path

The current results suggest:
1. **More data is critical** — 10 videos is too few
2. **5-second windows work better** at this scale
3. **Need 50+ videos** with proper ground truth to draw conclusions

**Action**: Continue processing more videos (Batch 1 has 49 - all on user's Drive).
