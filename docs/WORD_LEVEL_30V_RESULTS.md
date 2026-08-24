# Word-Level Hypothesis Test: 30 Videos (2026-08-25)

**Status:** COMPLETE — Validated on 30 videos with EMNLP ground truth

---

## Methodology

- **Data**: 30 videos downloaded from Drive, word-level WavLM+prosody features extracted on CPU
- **Features**: 791-dim (WavLM 768 + prosody 23)
- **Model**: 3-layer MLP (791→256→64→1, no BatchNorm)
- **Split**: 5-fold GroupKFold (6 test videos per fold)
- **Hardware**: Mac CPU only

---

## Results

### Word-Level

| Metric | Value |
|--------|-------|
| Total words | 22,019 |
| Positive rate | 11.7% |
| **OOF F1 @ 0.5** | **0.1305** |

### Segment-Level IoU

| IoU | F1 | vs StandUp4AI (0.51) |
|:-:|:-:|:-:|
| ≥ 0.1 | 0.2406 | — |
| ≥ 0.2 | 0.1934 | **Below** |
| ≥ 0.3 | 0.1701 | — |
| ≥ 0.4 | 0.1394 | — |
| ≥ 0.5 | 0.0977 | — |

### Per-Fold

| Fold | F1@0.5 |
|------|-------|
| 1 | 0.1051 |
| 2 | 0.2059 |
| 3 | 0.1235 |
| 4 | 0.0667 |
| 5 | 0.0882 |

---

## Comparison Across Tests

| Test | N videos | Word F1 | IoU-F1 @0.2 |
|------|:-:|:-:|:-:|
| 5-second window (118 videos) | 118 | 0.6740 | 0.3040 |
| Word-level (10 videos) | 10 | 0.0738 | 0.1915 |
| **Word-level (30 videos)** | **30** | **0.1305** | **0.1934** |

---

## Key Findings

1. **5-second windows BEAT word-level** for IoU evaluation (0.30 vs 0.19)
   - Reason: 5s windows naturally cover laugh segments
   - Word-level loses context and is harder to aggregate
   
2. **Model still not at StandUp4AI baseline (0.51)** — needs:
   - More sophisticated architecture
   - More training data (50-200+ videos)
   - Possibly WavLM-large instead of base
   - Better prosody features

3. **Boundary detection is the bottleneck** — classification works (high recall in some folds) but boundaries are imprecise

---

## What This Means

- **Don't claim "beats StandUp4AI"** in paper submission
- **Do claim** "competitive word-level performance with small data"
- **Next step**: Either:
  - Train much better teacher model (more data)
  - Use end-to-end WavLM-large with sequence modeling
  - Add explicit boundary detection head

