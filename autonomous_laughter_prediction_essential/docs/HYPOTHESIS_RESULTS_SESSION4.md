# Hypothesis Results — Session 4: H6.1 Prosody Test

## Date: 2025-05-20
## Method: Real audio extraction (librosa) from 50 videos, 73,947 word-level features

---

## H6.1: F0 DROP at Punchline

**Hypothesis**: Laughter words have lower F0 (pitch) than non-laugh words (Pickering, Attardo & Meziani 2009)

### Result: ✅ Statistically CONFIRMED, ❌ Practically NEGIGIBLE

| Metric | Laugh (n=7,074) | Non-Laugh (n=53,401) | Δ | p | Cohen's d |
|--------|-----------------|----------------------|---|---|-----------|
| F0 mean | 202.0 Hz | 207.1 Hz | 5.0 Hz | 7.54e-07 | **0.063** |
| F0 min | 182.7 Hz | 187.7 Hz | 5.0 Hz | 1.24e-07 | **0.067** |
| F0 max | 221.0 Hz | 225.5 Hz | 4.4 Hz | 8.31e-05 | **0.050** |
| F0 range | 38.4 Hz | 37.7 Hz | 0.6 Hz | 0.175 | 0.017 ns |
| F0 std | 13.6 Hz | 13.3 Hz | 0.3 Hz | 0.071 | 0.022 ns |

**Interpretation**: The 5 Hz F0 difference is real (p < 10⁻⁶) but the distributions overlap by ~98%. Cohen's d = 0.063 is negligible. This is a textbook case of the "big data significance trap" — with N = 60,475 words, even trivially small effects are statistically significant.

## Classifier Results (Per-Video Split, No Leakage)

| Model | Train F1 | Test F1 |
|-------|----------|---------|
| Logistic Regression (all features) | 0.21 | **0.25** |
| Random Forest | 0.98 | 0.00 |
| Gradient Boost | 0.01 | 0.00 |

## Feature Subset Analysis (Logistic Regression)

| Feature Set | F1 |
|-------------|-----|
| F0 only | 0.24 |
| Energy only | 0.24 |
| Pause only | 0.11 |
| **F0 + Energy** | **0.27** | ← best
| F0 + Pause | 0.21 |
| Energy + Pause | 0.21 |
| All features | 0.25 |

## Feature Importance (Logistic Regression)

| Feature | Coefficient | Interpretation |
|---------|------------|----------------|
| rms_max | +0.82 | Loudness peaks (ONLY useful feature) |
| rms_mean | -0.73 | Avg loudness (inverse — quieter words = laugh?) |
| rms_std | +0.31 | Loudness variation |
| word_duration | +0.21 | Longer words |
| pause_before | +0.17 | Pause before word |
| f0_std | +0.008 | **F0 features are NOISE** |
| f0_mean | -0.005 | **Zero signal** |
| f0_min | +0.003 | **Zero signal** |
| f0_range | -0.002 | **Zero signal** |
| f0_max | +0.001 | **Zero signal** |

## Comparison Across All Hypotheses

| H# | Hypothesis | Result | Detail |
|----|-----------|--------|--------|
| H1.1 | Pause → laughter (d > 0.5) | ❌ REJECTED | d = 0.24 |
| H1.5 | Pause alone F1 ≥ 0.55 | ❌ REJECTED | F1 = 0.20 |
| H2.5 | ≥70% multi-word spans | ⚠️ ARTIFACT | 100% ±5s window |
| H4.5 | Split leakage | ⚠️ CONFIRMED | 1.9% gap |
| H4.6 | TF-IDF baseline | ✅ CONFIRMED | F1 = 0.73 |
| H4.4 | Biosemiotic leakage | 🔴 CONFIRMED | F1 = 0.829 from features |
| H5 | Temporal position | ✅ CONFIRMED | p = 4e-143 |
| **H6.1** | **F0 DROP at punchline** | **⚠️ TRIVIALLY SMALL** | **p < 0.001, d = 0.063** |
| H12 | Interaction Model | 📋 Planned | |
| H13 | MultiLinguahah (BYOL-A) | 📋 Planned | |
| H14 | Text + Audio fusion | 📋 Planned | |

## Revised H6.1 Conclusion

**Pickering (2009) reported a F0 drop at punchlines. We confirm this effect exists (p < 10⁻⁶) across 60,475 word tokens from 50 stand-up comedy videos in English, but find it is negligible in magnitude (Cohen's d = 0.06). The 5 Hz mean difference between laugh-context words (202.0 Hz) and non-laugh words (207.1 Hz) results in ~98% distribution overlap, making F0 useless as a classification feature (|coef| < 0.01 in logistic regression). Simple acoustic features (F0, energy, pause) achieve F1 = 0.27, only marginally above the pause-only baseline (F1 = 0.11) and far below text-only XLM-R (F1 = 0.82).**

---

## Data Provenance

- 73,947 word-level features from 50 videos
- Per-video train/test split (40 train, 10 test)
- Features extracted via librosa (pyin for F0, RMS for energy)
- Aligned segments: 549,334 total (389,483 word-level + 159,851 realigned from spans)