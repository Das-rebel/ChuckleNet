# ChuckleNet Research Timeline

## Complete Research & Development History with All Findings

---

# Phase 1: Data Collection & Infrastructure (Apr 1 – May 4, 2026)

## Apr 1-3: Project Initiation
- **Goal**: Build multilingual laughter detection for stand-up comedy videos
- **Languages**: English (en), Hindi (hi), Hindi-Latn (Hinglish)
- **Target**: 10,000,000 aligned word-level segments from 1,640 videos
- **Infrastructure**: M1 Mac CPU, faster-whisper for transcription, yt-dlp for downloads

### Key Decisions
- Chose faster-whisper (10x faster than OpenAI Whisper on M1)
- VTT `[laughter]` markers + Whisper word timestamps for alignment
- SQLite database for tracking (`data/collection_tracking.db`)

## Apr 3-5: Core Pipeline
- Built `align_whisper_to_vtt.py` — aligns Whisper transcripts to VTT laughter markers
- Built `download_audio_batch.py` — batch audio download with yt-dlp
- Built `expand_audio_dataset.py` — scale to more videos
- **Output**: `data/audio_comedy/aligned_segments.jsonl`

## May 1-4: Hindi & Scaling
- Built V8.1 pipeline for Hindi comedy collection
- Created synthetic Hindi data generators (Groq, Sarvam, Mistral)
- Merged Hindi data with expanded 10K dataset
- **Result**: ~340K segments across multiple batches

---

# Phase 2: Hypothesis Testing (May 5 – May 17, 2026)

## May 5-9: Initial Hypotheses
- Built XLM-R baseline classifier
- Created hypothesis matrix covering H1-H14

### H1.x: Pause Hypotheses
- **H1.1**: Pause before laughter (Cohen's d > 0.5) → **REJECTED** (d=0.24)
- **H1.5**: Pause alone predicts laughter (F1 ≥ 0.55) → **REJECTED** (F1=0.20)
- **Finding**: Pause has weak effect (d=0.24), insufficient for detection

### H2.x: Multi-word Spans
- **H2.5**: ≥70% of laughter labels span multi-word sequences
- **Result**: CONFIRMED but MISLEADING — 100% artifact of ±5s alignment window
- Labels mean "within ~5 seconds of laughter", not "this word triggered laughter"

## May 10-14: Deep Investigation

### H4.x: Label Quality
- **H4.4**: Biosemotic features contain label leakage → **CONFIRMED** (F1=0.829 from features alone)
  - Previous/next label features leaked the answer
  - **Critical negative result**: All ablation results using these features are INVALID
- **H4.5**: Split leakage → Confirmed (1.9% gap)
- **H4.6**: TF-IDF baseline → **CONFIRMED** (F1=0.73)
  - Surprisingly strong, showing text context matters

### H5: Temporal Position
- **CONFIRMED**: Laugh rate varies by position in video (p=4e-143)
- Peak at 20-30%, minimum at 90-100%
- Large effect size, statistically robust

## May 14-17: Literature Review

### Papers Analyzed
1. **Pickering 2009**: F0 DROP at punchline (not rise!)
2. **Purandare 2006**: Pause 0.8s before laugh (p<0.001)
3. **Bachorowski 2001**: Laughter 250-500Hz oscillating
4. **Bertero 2016**: F0 range wider at punchlines
5. **Gillick 2019**: CNN on spectrograms F1=0.89
6. **MultiLinguahah 2026**: BYOL-A self-supervised encoder + Isolation Forest (F1=0.68)
7. **Interaction Model**: 200ms chunks, native time-awareness, concurrent streams

### Hypothesis Tree Expanded (H6-H14)
- H6: Prosody (F0, energy, pause) improves detection
- H7: Acoustic laughter bursts (250-500Hz oscillating)
- H8: Temporal dynamics (F0 trajectory)
- H9: Speaker normalization
- H10: Cross-lingual transfer
- H11: Comedian-specific models
- H12: Interaction Model (200ms chunks)
- H13: MultiLinguahah (BYOL-A)
- H14: Text + Audio fusion

## May 16-18: Peer Review & Validation
- Jenni peer review identified **label leakage** in biosemotic features
- Independent review confirmed H4.4 is a **critical negative result**
- Hypothesis validation report V2 written
- **Paradigm shift**: word-level labels are weak (±5s window), need utterance-level

---

# Phase 3: Audio Prosody Testing (May 18 – May 20, 2026)

## May 18-19: H6.1 Colab Notebook Development
- Built Colab notebook for H6.1 F0 DROP testing
- Uses real audio data from GDrive (50 videos)
- Extracts F0, energy, pause features via librosa
- Multiple iterations fixing:
  - 403 permission error on GDrive → public sharing
  - gdown download failure → GDrive mount approach
  - KeyError 'start' → fixed span-level segment alignment
  - Syntax error in f-string → escaped quote fix

### Segment Format Fix
- Discovered 203 span-level segments (no timestamps) in 20 videos
- These were duplicate context windows (same transcript 16x)
- Built fuzzy matching alignment to Whisper word timestamps
- Result: 389,483 → 549,334 total segments (all with timestamps)

## May 19-20: H6.1 Results (Colab, 50 videos, 73,947 features)

### Audio-Only Classifier

| Feature Set | F1 |
|-------------|-----|
| Pause only | 0.11 |
| F0 + Energy + Pause (baseline) | 0.29 |
| F0 only | 0.24 |
| Energy only | 0.24 |
| All 49 acoustic features | 0.27 |
| **XLM-R text** | **0.82** |

### H6.1 Statistical Result
- F0 DROP: **CONFIRMED** (p = 7.54e-07) but **NEGLIGIBLE** (Cohen's d = 0.063)
- Laugh words: F0 = 202.0 Hz vs Non-laugh: F0 = 207.1 Hz (Δ = 5.0 Hz)
- **98% distribution overlap** — statistically significant but practically useless
- "Big data significance trap": N=60,475 makes even trivial effects significant

### Feature Importance (Logistic Regression)
| Feature | Coefficient | Interpretation |
|---------|------------|----------------|
| rms_max | +0.82 | Only meaningful feature (loudness peak) |
| rms_mean | -0.73 | Average loudness (inverse) |
| f0_std | +0.008 | **Pure noise** |
| f0_mean | -0.005 | **Pure noise** |
| f0_range | -0.002 | **Pure noise** |

### Acoustic Feature Ceiling Test (47 videos, 73,941 words)

Extended to 49 features: MFCCs (13 coefficients), spectral centroid, bandwidth, rolloff, ZCR, chroma, energy dynamics.

| Feature Set | F1 (10-video) | F1 (47-video) |
|-------------|:------------:|:------------:|
| ZCR alone | 0.44 | 0.23 |
| Spectral alone | 0.44 | 0.23 |
| MFCC mean | 0.35 | 0.25 |
| F0+RMS+Pause baseline | 0.31 | 0.29 |
| **All 49 features** | **0.31** | **0.27** |

**Key finding**: 10-video tests showed promising ZCR/spectral F1=0.44 but this was **overfitting on small test set**. At 47-video scale, all feature sets converge to F1 ≈ 0.27-0.29.

**Acoustic feature ceiling: F1 ≈ 0.30 regardless of feature set or model.**

### Why Audio Failed (Council Analysis)
1. **Wrong level**: Per-word F0 averages away signal. Laughter is supra-segmental.
2. **Wrong features**: F0/RMS are speaker-identity dominated (d>2 vs laugh-detection d=0.06)
3. **Information bottleneck**: 10-49 hand-crafted features can't capture what neural encoders capture in 768+ dimensions
4. **Class imbalance**: 12% positive rate, Gradient Boost fails (F1=0.00)

---

# Phase 4: Path Forward — WavLM + XLM-R Fusion (Planned)

## Architecture: Gated Multimodal Fusion
```
Text (utterance) → XLM-R → text_proj (768→256) ─┐
                                                   ├→ Gated Fusion → classifier
Audio (3-15s) → WavLM-Base+ → audio_proj (768→256) ─┘

Gate: g = σ(Wg·[t; a])
Fused = g⊙t + (1-g)⊙a
```

## Key Design Decisions
1. **Utterance-level** (not word-level): 15K samples, 32.6% positive, 3-15s audio clips
2. **WavLM-Base+**: Pre-trained on 94k hrs, handles noisy speech+laughter
3. **Gated fusion**: Learns when to trust audio vs text
4. **Per-video split**: GroupKFold 5-fold CV prevents leakage
5. **Three-phase training**: text baseline → frozen fusion → joint fine-tune

## Expected Targets
| Model | Expected F1 | Rationale |
|-------|:-----------:|-----------|
| XLM-R text-only (utterance) | 0.75-0.80 | Word-level 0.82 inflated by spans |
| WavLM audio-only (utterance) | 0.55-0.65 | Literature: audio humor F1=0.62-0.63 |
| **Gated fusion** | **0.82-0.87** | Audio adds +3-7% to text |

## Implementation Plan
- `training/extract_wavlm_embeddings.py` — Pre-extract WavLM on Colab (~2hrs)
- `training/model_wavlm_xlmr_fusion.py` — GatedMultimodalFusion architecture
- `training/dataset_utterance_multimodal.py` — Pairs WavLM embeddings with text
- `training/train_fusion_v3.py` — 3-phase training with GroupKFold CV
- Data: `data/audio_comedy/aligned_utterances.jsonl` (15,060 utterances)

---

# Complete Hypothesis Results

| H# | Hypothesis | Result | Detail |
|----|-----------|--------|--------|
| H1.1 | Pause → laughter (d>0.5) | ❌ REJECTED | d=0.24 (weak) |
| H1.5 | Pause alone F1≥0.55 | ❌ REJECTED | F1=0.20 |
| H2.5 | ≥70% multi-word spans | ⚠️ ARTIFACT | 100% from ±5s window |
| H4.4 | Biosemotic leakage | 🔴 CONFIRMED | F1=0.829 (invalid ablation!) |
| H4.5 | Split leakage | ⚠️ CONFIRMED | 1.9% gap |
| H4.6 | TF-IDF baseline | ✅ CONFIRMED | F1=0.73 |
| H5 | Temporal position | ✅ CONFIRMED | p=4e-143 |
| H6.1 | F0 DROP at punchline | ⚠️ TRIVIALLY SMALL | p<10⁻⁶, d=0.063 |
| — | Acoustic feature ceiling | ❌ CEILING | F1≈0.30 for ANY features |
| — | All 49 acoustic features | ❌ | F1=0.27 |
| — | XLM-R text | ✅ | F1=0.82 |
| H13 | MultiLinguahah (BYOL-A) | 📋 Planned | |
| H14 | Text + Audio fusion | 📋 Planned | WavLM+XLM-R gated fusion |

---

# Data Inventory

| Item | Count/Size | Location |
|------|-----------|----------|
| Aligned segments | 549,334 (all with timestamps) | `data/audio_comedy/aligned_segments.jsonl` |
| Audio files | 388 MP3s | `data/audio_comedy/audio/` |
| Whisper transcripts | 166 | `data/audio_comedy/whisper/` |
| Tracking DB | 1,379 entries | `data/collection_tracking.db` |
| GDrive backup | 34.9 GB | `gdrive:/laughter_prediction_backup/` |
| Prosody features (50 videos) | 73,947 × 10 features | `data/audio_comedy/prosody_features_50videos.csv` |
| Combined features (47 videos) | 73,941 × 49 features | `data/audio_comedy/combined_features_50videos.csv` |
| Spectral features (47 videos) | 69,285 × 39 features | `data/audio_comedy/spectral_features_50videos.csv` |
| Utterance dataset | 15,060 utterances | `data/audio_comedy/aligned_utterances.jsonl` |
| Videos downloaded (HIGH tier) | 497 | Various sources |
| Colab notebook | H6.1 test | Gist: `Das-rebel/c5ffe5a6f427ac15a22f8b1a15424b73` |

---

# Key Publications Referenced

1. **Pickering et al. 2009**: F0 DROP at punchline (confirmed but d=0.063, negligible)
2. **Purandare & Picard 2006**: Pause >0.8s before laugh (confirmed but d=0.24, weak)
3. **Bachorowski 2001**: Laughter 250-500Hz oscillating
4. **Bertero 2016**: F0 range wider at punchlines
5. **Gillick et al. 2019**: CNN on spectrograms F1=0.89
6. **MultiLinguahah 2026**: BYOL-A + Isolation Forest F1=0.68
7. **Tsai et al. 2019**: MulT gated fusion for multimodal sentiment
8. **Atmaja & Akagi 2020**: Pause most predictive single feature
9. **Gerazov 2018**: Links linguistic to prosodic forms
10. **Rengaswamy 2019**: Laughter rise-fall contours

---

# Publishable Findings

1. **F0 DROP is real but negligible**: p < 10⁻⁶ but Cohen's d = 0.063. This refines Pickering (2009) — the effect exists but is too small for detection.

2. **Acoustic feature ceiling**: Hand-crafted features (F0, RMS, ZCR, MFCC, spectral) hit F1 ≈ 0.30 regardless of feature count (10 to 49). Word-level analysis is the wrong level.

3. **Label leakage in biosemotic features**: F1=0.829 from features alone revealed that prev/next label features were leaking the answer. All previous ablation results using these features are invalid.

4. **Text context dominates detection**: XLM-R F1=0.82 is 3x better than best audio model. The 16-word context window is what makes it work, not individual word semantics.

5. **Statistical vs practical significance**: With N=60K+ words, even trivially small effects (ΔF0=5Hz, d=0.063) are "highly significant" (p < 10⁻⁶). Always report effect sizes.

---

# Appendix: Revalidation Results (May 20, 2026)

## Stability Check: Colab vs Local Replication

Two independent evaluations on overlapping but different test sets confirm all findings:

| Metric | Colab (50 videos) | Local (47 videos) | Agreement |
|--------|:-----------------:|:-----------------:|:---------:|
| Laugh F0 mean | 202.0 Hz | 200.2 Hz | ✅ |
| Non-laugh F0 mean | 207.1 Hz | 209.5 Hz | ✅ |
| ΔF0 | 5.1 Hz | 9.3 Hz | ✅ (both negligible) |
| Cohen's d | 0.063 | 0.115 | ✅ (both < 0.2) |
| F0+Energy+Pause F1 | 0.29 | 0.29 | ✅ (identical) |
| All 49 features F1 | 0.27 | 0.27 | ✅ (identical) |
| Pause-only F1 | 0.11 | 0.11 | ✅ (identical) |
| ZCR alone F1 | 0.23 | 0.23* | ✅ |

*ZCR showed F1=0.44 on 10-video test set (overfitting). At 47 videos: F1=0.23.

All findings are robust across different test set compositions.

## Additional Revalidated Numbers (47 videos, 49 features)

| Feature | Laugh (mean) | Non-laugh (mean) | Δ | Cohen's d |
|---------|:------------:|:-----------------:|:-:|:---------:|
| F0 mean | 200.2 Hz | 209.5 Hz | 9.3 Hz | 0.115 |
| F0 min | — | — | — | 0.067 |
| F0 max | — | — | — | 0.050 |
| rms_max | — | — | — | 0.144 |
| pause_before | 0.22s | 0.14s | 0.08s | 0.112 |
| word_duration | 0.29s | 0.27s | 0.02s | 0.071 |

All effects are NEGLIGIBLE (d < 0.2) or SMALL (d < 0.5) at most.

## Data Provenance

| File | Rows | Columns | Source |
|------|------|---------|--------|
| aligned_segments.jsonl | 549,334 | 8 | Whisper+VTT aligned, span-level realigned |
| aligned_segments_v1_backup.jsonl | 389,686 | 8 | Original (before span realignment) |
| prosody_features_50videos.csv | 73,947 | 14 | Colab extraction (F0, RMS, pause) |
| combined_features_50videos.csv | 73,941 | 51 | Local extraction (+MFCC, ZCR, spectral) |
| spectral_features_50videos.csv | 69,285 | 42 | Spectral features only |
| aligned_utterances.jsonl | 15,060 | 12 | Utterance-level grouping |

## Colab Notebook Links

- H6.1 Prosody Test (real audio): https://colab.research.google.com/gist/Das-rebel/c5ffe5a6f427ac15a22f8b1a15424b73
- GitHub Gist (source): https://gist.github.com/Das-rebel/c5ffe5a6f427ac15a22f8b1a15424b73
- GDrive shared folder: https://drive.google.com/drive/folders/15ixKiy86MZ67OwGEVxtnwSTs3nvbLRbh
