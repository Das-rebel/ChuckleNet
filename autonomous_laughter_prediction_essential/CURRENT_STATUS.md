# ChuckleNet Current Status — May 20, 2026

## Key Metrics
- **Aligned segments**: 549,334 (all with timestamps, 71 videos)
- **Audio files**: 388 MP3s locally, 459 on GDrive
- **Whisper transcripts**: 166
- **Utterance dataset**: 15,060 utterances (32.6% positive)
- **GDrive backup**: 34.9 GB

## Hypothesis Results (All Validated)

| H# | Hypothesis | Result | Evidence |
|----|-----------|--------|----------|
| H1.1 | Pause → laughter (d>0.5) | ❌ REJECTED | d=0.24 |
| H1.5 | Pause alone F1≥0.55 | ❌ REJECTED | F1=0.20 |
| H2.5 | ≥70% multi-word spans | ⚠️ ARTIFACT | ±5s window |
| H4.4 | Biosemotic leakage | 🔴 CONFIRMED | F1=0.829 (invalid) |
| H4.6 | TF-IDF baseline | ✅ CONFIRMED | F1=0.73 |
| H5 | Temporal position | ✅ CONFIRMED | p=4e-143 |
| H6.1 | F0 DROP at punchline | ⚠️ TRIVIALLY SMALL | d=0.063 (Colab), d=0.115 (local) |
| — | Acoustic ceiling | ❌ FLOOR | F1≈0.30 for ANY features |
| — | 49 vs 10 features | ❌ NO IMPROVEMENT | F1=0.27 vs 0.29 |

## Best Results
- XLM-R text: **F1 = 0.82** (word-level, 16-word context)
- Audio prosody (all 49 features): **F1 = 0.27**
- F0+Energy+Pause (10 features): **F1 = 0.29**
- Pause only: F1 = 0.11

## Acoustic Feature Ceiling
Hand-crafted features hit a hard ceiling at F1 ≈ 0.29-0.30 regardless of:
- Feature count (10 to 49)
- Feature type (F0, RMS, MFCC, ZCR, spectral, chroma)
- Model type (Logistic Regression, Random Forest, Gradient Boosting)

Root causes:
1. Per-word analysis is wrong level (laughter is supra-segmental)
2. Speaker identity dominates F0/RMS (d>2 vs laugh-detection d<0.15)
3. F0 DROP at punchlines is real (p<10⁻⁶) but negligible (d=0.063)

## Next Steps
1. WavLM-Base+ utterance-level embeddings (expected F1=0.55-0.65)
2. XLM-R + WavLM gated fusion (expected F1=0.82-0.87)
3. Three-phase training: text baseline → frozen fusion → joint fine-tune
4. See: docs/WAVLM_XLMR_FUSION_PLAN.md

## Files
- Research timeline: RESEARCH_TIMELINE.md
- Hypothesis results: docs/HYPOTHESIS_RESULTS_SESSION4.md
- WavLM fusion plan: docs/WAVLM_XLMR_FUSION_PLAN.md
- Prosody data: data/audio_comedy/prosody_features_50videos.csv
- Combined features: data/audio_comedy/combined_features_50videos.csv
- Colab notebook: gist.github.com/Das-rebel/c5ffe5a6f427ac15a22f8b1a15424b73
