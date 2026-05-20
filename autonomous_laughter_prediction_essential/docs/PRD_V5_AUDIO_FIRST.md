# PRD v5.0: Audio-First Laughter Detection (Post-Validation)
## Based on: Hypothesis Validation Report V2 (Jenni Peer Review 6/10)
## Date: 2026-05-18
## Status: ACTIVE — Replaces PRD v4.0

---

## 0. Why This PRD Replaces v4.0

PRD v4.0 targeted 10M word-level segments with Wav2Vec2. After comprehensive validation
(Statcheck + Deepchecks + Citation Audit + Jenni Peer Review), we discovered:

1. **Word-level labels are fundamentally broken** — 91.1% of positive labels are in spans >10 words
   (median=16). The label means "within ~5 seconds of laughter," not "this word triggered laughter."
2. **TF-IDF F1=0.08 at word level** — near-random. XLM-R's F1=0.819 exploits 16-word context windows,
   not individual word semantics.
3. **Function words are equally distributed** (χ²=2.2, p=0.14). The problem is NOT function words —
   it's the 5-second alignment window granularity.
4. **Biosemotic features contain label leakage** (F1=0.83 from features alone). All ablation results
   using these features are INVALID.
5. **Audio features are negligible at word level** (Cohen's d=0.15) but literature predicts strong
   signal at utterance/clip level.

**Conclusion:** The entire pipeline must pivot from WORD-LEVEL to UTTERANCE-LEVEL.

---

## 1. Mission

Build the first **audio-native laughter detection system** that proves:
1. Text-based laughter detection on weak labels measures alignment noise, not humor
2. Audio features (eGeMAPS + WavLM) at utterance level can detect REAL audience laughter
3. The first deployable **emotion predictor** from acoustic signals using LLM representations

---

## 2. Validated Evidence (What We KNOW)

### 2.1 Proven Findings (Publication-Ready)

| Finding | Evidence | Strength |
|---------|----------|:--------:|
| 91.1% of labels in spans >10 words | 1.17M segments, 68 videos | ⭐⭐⭐⭐⭐ |
| Median laughter span = 16 words | Span analysis across all data | ⭐⭐⭐⭐⭐ |
| Function words NOT over-represented | χ²=2.2, p=0.14 | ⭐⭐⭐⭐⭐ |
| TF-IDF F1=0.08 at word level | 5-fold CV, 50K subset | ⭐⭐⭐⭐ |
| Biosemotic label leakage (F1=0.83) | LR on features alone | ⭐⭐⭐⭐⭐ |
| Cohen's d=0.13 for pauses (negligible) | 200K words, 26 videos | ⭐⭐⭐ |
| XLM-R F1=0.819 on word-level weak labels | Single run, no error bars | ⭐⭐⭐ |

### 2.2 Corrected Claims (What We Were WRONG About)

| Original Claim | Corrected | Impact |
|---------------|-----------|--------|
| "54% function word noise" | Function words equal across classes (61.2% vs 61.6%) | Paper must claim SPAN LENGTH, not function words |
| "H4.4 CONFIRMED" | H4.4 INVALID (label leakage) | Remove all biosemotic ablation results |
| "XLM-R F1=0.819 = good" | F1=0.819 exploits 16-word context, not word meaning | Reframe as evidence of label noise |
| "Audio d=0.15 at word level = promising" | d=0.15 is negligible; audio needs utterance level | Shift to utterance-level extraction |

### 2.3 Baselines (Per Jenni Review)

| Baseline | Modality | Data | Key Result |
|----------|----------|------|-----------|
| **FunnyNet-W** (Liang 2024) | Audio+Visual+Text | Sitcom laugh tracks | Multimodal beats text-only |
| **LOLgorithm** (Annamoradnejad 2024) | GPT-4 text | Clean curated humor | Works on clean labels |
| **StandUp4AI** (Barrière 2025) | Text (XLM-R) | 3,617 videos, 7 langs | Utterance-level, F1~0.70 |
| **UR-FUNNY** (Hasan 2019) | Multimodal | TED talks | Humor detection benchmark |
| **Our XLM-R** (word-level) | Text | 49 videos, weak labels | F1=0.819 (inflated by context) |

**Key distinction:** FunnyNet-W uses video (sitcom laugh tracks). LOLgorithm uses clean text.
We target **AUDIO-ONLY** on **REAL audience laughter** in **stand-up comedy**.

---

## 3. Architecture (Utterance-Level)

### 3.1 Data Flow

```
YouTube Comedy Videos
        │
        ▼
   ┌─────────┐     ┌──────────────┐
   │ MP3 Audio│     │ VTT Subtitles│
   └────┬─────┘     └──────┬───────┘
        │                  │
        ▼                  ▼
   ┌─────────────────────────────┐
   │ UTTERANCE-LEVEL ALIGNMENT   │  ← NEW: Group words into VTT utterances
   │ (not word-level ±5s window) │
   └────────────┬────────────────┘
                │
        ┌───────┴───────┐
        ▼               ▼
   ┌──────────┐   ┌───────────┐
   │ Audio    │   │ Text      │
   │ Features │   │ Features  │
   └────┬─────┘   └─────┬─────┘
        │               │
        ▼               ▼
   ┌──────────┐   ┌───────────┐
   │ eGeMAPS  │   │ XLM-R     │
   │ 88 feats │   │ embeddings│
   │+ HNR     │   │ (768-dim) │
   │+ spectral│   │           │
   ├──────────┤   ├───────────┤
   │ WavLM    │   │           │
   │ (768-dim)│   │           │
   └────┬─────┘   └─────┬─────┘
        │               │
        └───────┬───────┘
                ▼
        ┌───────────────┐
        │ FUSION MODEL  │
        │ XGBoost / NN  │
        └───────┬───────┘
                ▼
        ┌───────────────┐
        │ EVALUATION    │
        │ Human labels  │
        │ Cross-domain  │
        └───────────────┘
```

### 3.2 Utterance-Level Labels

**Current (BROKEN):** Word-level, 5-second window → 733K segments, 4.2% positive, median span=16 words

**New (CORRECT):** VTT utterance-level → ~50K utterances from existing 49 videos

| Property | Word-Level (Old) | Utterance-Level (New) |
|----------|:---:|:---:|
| Total examples | 733K | ~50K |
| Positive rate | 4.2% | ~30-40% |
| Median positive span | 16 words | 1 utterance |
| Label meaning | "Near a laugh" | "This utterance has laughter" |
| TF-IDF F1 | 0.08 | Expected 0.40-0.60 |
| Audio suitability | d=0.15 (negligible) | d=0.5+ (literature) |

### 3.3 Label Assignment

For each VTT utterance:
1. Check if the utterance overlaps with ANY [laughter] marker in the VTT
2. If overlap → label=1 (contains laughter)
3. If no overlap → label=0
4. **Edge handling:** Utterances spanning a [laughter] boundary get label=1 (conservative)

---

## 4. Acoustic Feature Pipeline

### 4.1 Feature Set (Expanded per Jenni Review)

| Category | Features | Count | Tool | Purpose |
|----------|----------|:-----:|------|---------|
| **eGeMAPS** | Validated paralinguistic set | 88 | openSMILE | Standard affective computing |
| **Prosodic** | F0, pause, speech rate | 5 | librosa | Comedic timing |
| **Voice Quality** | HNR, jitter, shimmer | 3 | librosa+openSMILE | Duchenne vs social laughter |
| **Spectral** | MFCC(13)+delta+dd, centroid, bandwidth, rolloff, ZCR | 42 | librosa | Laugh burst characterization |
| **Energy** | RMS, RMS std, loudness contour | 4 | librosa | Response intensity |
| **WavLM** | SSL embeddings (frozen) | 768 | transformers | Learned representations |
| **TOTAL** | | **910** | | |

### 4.2 Extraction Per Utterance

For each utterance (audio clip of 1-15 seconds):
```python
features = {}
features['egemaps'] = extract_egemaps(audio, sr=16000)      # 88-dim
features['prosodic'] = extract_prosodic(audio, sr=16000)     # 5-dim
features['voice_quality'] = extract_voice_quality(audio)     # 3-dim (HNR, jitter, shimmer)
features['spectral'] = extract_spectral(audio, sr=16000)     # 42-dim
features['energy'] = extract_energy(audio, sr=16000)         # 4-dim
features['wavlm'] = extract_wavlm(audio, sr=16000)           # 768-dim
features['text'] = extract_xlmr(utterance_text)              # 768-dim
# Total: 910 audio + 768 text = 1,678 features per utterance
```

### 4.3 HNR for Duchenne Detection (Novel)

HNR > 15dB → genuine (Duchenne) laughter
HNR < 10dB → social/polite laughter
HNR unavailable → no laughter

This enables **emotion classification** beyond binary laughter detection:
- No laughter (HNR not applicable)
- Social laughter (HNR < 10dB)
- Genuine laughter (HNR > 15dB)

**This is our "first emotion predictor" angle.**

---

## 5. Experimental Plan

### Phase 0: Utterance-Level Realignment (2 days, CPU)

**Goal:** Convert 733K word-level segments → ~50K utterance-level segments

Steps:
1. Load all VTT subtitle files for 49 videos
2. Parse VTT into utterance segments (timestamp + text)
3. Identify [laughter] markers in VTT
4. For each utterance: label=1 if any [laughter] overlaps, else label=0
5. Cross-reference with existing aligned_segments.jsonl for audio timestamps
6. Output: `data/audio_comedy/aligned_utterances.jsonl`

**Deliverable:** Clean utterance-level dataset with:
- utterance_id, video_id, comedian, text, start_time, end_time, label
- Audio file path for each utterance

### Phase 1: Audio Feature Extraction (2 days, CPU)

**Goal:** Extract all 910 acoustic features for each utterance

Steps:
1. For each utterance in aligned_utterances.jsonl:
   a. Load audio clip (from MP3 using ffmpeg + start/end times)
   b. Extract eGeMAPS 88 features (openSMILE)
   c. Extract prosodic + voice quality + spectral + energy (librosa)
   d. Extract WavLM 768-dim embeddings (requires GPU — Colab)
2. Save features to `data/audio_comedy/utterance_features.npz`
3. Statistical analysis: Cohen's d per feature at utterance level

**Deliverable:** Feature matrix (50K × 910) + text embeddings (50K × 768)

### Phase 2: Model Training (3 days, GPU required)

**Goal:** Train and compare text-only, audio-only, and fusion models

#### Experiment 2a: Text-Only Baseline
- XLM-R on utterance text, utterance-level labels
- Expected: F1=0.50-0.65 (better than word-level but still limited by weak labels)

#### Experiment 2b: Audio-Only (THE KEY EXPERIMENT)
- eGeMAPS 88 → XGBoost
- WavLM 768 → MLP classifier
- eGeMAPS + WavLM → XGBoost
- Expected: F1=0.55-0.70 (literature predicts audio works at utterance level)

#### Experiment 2c: Fusion
- Audio features + XLM-R embeddings → XGBoost / Neural fusion
- Expected: F1=0.60-0.75 (best of both)

#### Experiment 2d: Ablation
- Remove HNR → measure F1 drop
- Remove spectral → measure F1 drop
- Remove WavLM → measure F1 drop
- Duchenne classification (3-class): no-laugh / social / genuine

**All experiments:** 5 seeds, error bars, paired bootstrap significance tests

### Phase 3: Validation (2 days)

**Goal:** Prove the paradigm shift with human evaluation

#### 3a: Human Annotation (50 clips)
- Select 50 utterances: 25 labeled positive, 25 labeled negative
- Extract 3-5 second audio clips
- Annotator listens and marks: "Does this contain REAL audience laughter?"
- Measure: weak label vs human label agreement

#### 3b: Cross-Domain Transfer
- Train on stand-up → test on UR-FUNNY (TED talks)
- Train on stand-up → test on sitcom (if data available)
- Measure: does audio model transfer better than text model?

#### 3c: Comparison with Baselines
- Reproduce FunnyNet-W evaluation on our data (if possible)
- Compare with LOLgorithm-style LLM embeddings
- Measure: our audio-only vs their multimodal

---

## 6. Compute Requirements

| Task | Hardware | Time | Cost |
|------|----------|------|------|
| Utterance realignment | CPU (Mac) | 2 hours | $0 |
| Audio feature extraction (eGeMAPS+librosa) | CPU (Mac) | 8 hours | $0 |
| WavLM embedding extraction | GPU (Colab T4) | 2 hours | $0 |
| XLM-R text embeddings | GPU (Colab T4) | 1 hour | $0 |
| Model training (5 seeds × 4 configs) | GPU (Colab T4 / Vast.ai RTX 4090) | 4-8 hours | $0-2 |
| **Total** | | **~17 hours** | **$0-2** |

---

## 7. Paper Structure (Revised)

### Title
**"Laughter Is Not Text: Why Audio-First Models Are Necessary for Paralinguistic Emotion Detection"**

### Abstract (Draft)
We demonstrate that text-based laughter detection using weak labels from YouTube subtitles
is fundamentally flawed: 91.1% of word-level laughter labels are in spans exceeding 10 words
(median=16), meaning the label captures "within earshot of laughter" rather than "this word
triggered laughter." TF-IDF achieves F1=0.08 at word level, confirming word-level classification
is inappropriate. We propose an utterance-level audio-first approach using eGeMAPS acoustic
features and WavLM self-supervised embeddings, achieving F1=X.XX on real audience laughter
detection — the first audio-native system for stand-up comedy laughter prediction.

### Sections
1. **Introduction**: The laughter detection problem, why text fails
2. **Related Work**: FunnyNet-W, LOLgorithm, StandUp4AI, UR-FUNNY, Purandare 2006, Bertero 2016
3. **The Label Granularity Problem**: 91.1% finding, chi-squared proof, span analysis
4. **Audio-First Architecture**: eGeMAPS + WavLM + XLM-R fusion at utterance level
5. **Experiments**: Text-only, audio-only, fusion, ablation, Duchenne classification
6. **Human Evaluation**: 50-clip annotation, weak label vs human agreement
7. **Discussion**: Implications for paralinguistic NLP, emotion prediction, limitations
8. **Conclusion**: Audio is NECESSARY, not additive

### Target Venues (Ordered)
1. **ACL 2025 Main** (paradigm shift argument)
2. **Interspeech 2025** (audio-first, paralinguistic community)
3. **EMNLP 2025 Findings** (empirical evidence)

---

## 8. Success Criteria

| Metric | Target | Minimum | Measurement |
|--------|--------|---------|-------------|
| Audio-only F1 (utterance) | ≥0.60 | ≥0.50 | 5-seed mean |
| Fusion F1 (utterance) | ≥0.70 | ≥0.60 | 5-seed mean |
| Audio > Text on human labels | ≥5pp | ≥3pp | Paired bootstrap |
| Weak vs human label agreement | ≤80% | ≤85% | Cohen's κ |
| Duchenne classification F1 | ≥0.55 | ≥0.45 | 3-class |
| Cross-domain transfer F1 | ≥0.45 | ≥0.35 | Zero-shot |

---

## 9. Risk Register

| Risk | Probability | Impact | Mitigation |
|------|:-----------:|:------:|-----------|
| Utterance-level labels still noisy | Medium | High | Human annotation validation (Phase 3a) |
| WavLM F1=0.0 bug persists | Low | Critical | LR=1e-4 + LayerNorm fix (validated root cause) |
| GPU unavailable for WavLM | Medium | High | Vast.ai RTX 4090 @ $0.15/hr |
| Audio features weak at utterance level | Low | Critical | Literature predicts d≥0.5 (Bachorowski 2001) |
| Fewer utterances than expected | Low | Medium | 49 videos → ~50K utterances sufficient for XGBoost |
| Paper rejected (paradigm shift too bold) | Medium | Medium | Also target Interspeech (audio community more receptive) |

---

## 10. Timeline

| Week | Phase | Deliverable |
|------|-------|-------------|
| **Week 1** | Phase 0 | Utterance-level dataset ready |
| **Week 1** | Phase 1 | Feature extraction pipeline working |
| **Week 2** | Phase 2 | All model results with error bars |
| **Week 2** | Phase 3a | 50 human-annotated clips |
| **Week 3** | Phase 3b-c | Cross-domain + baseline comparison |
| **Week 3** | Paper | First complete draft |
| **Week 4** | Paper | Camera-ready submission |

---

## 11. File Organization

```
autonomous_laughter_prediction_essential/
├── data/audio_comedy/
│   ├── aligned_segments.jsonl          # OLD: word-level (733K)
│   ├── aligned_utterances.jsonl        # NEW: utterance-level (~50K)
│   ├── utterance_features.npz          # NEW: acoustic features
│   └── extracted_clips/                # EXISTING: WAV clips
├── training/
│   ├── align_utterances.py             # NEW: Phase 0
│   ├── extract_utterance_features.py   # NEW: Phase 1
│   ├── train_audio_model.py            # NEW: Phase 2b
│   ├── train_fusion_model.py           # NEW: Phase 2c
│   ├── evaluate_human_labels.py        # NEW: Phase 3a
│   └── cross_domain_eval.py            # NEW: Phase 3b
├── experiments/
│   ├── validation/                     # EXISTING: all validation data
│   ├── utterance_level/                # NEW: utterance experiments
│   └── human_annotation/              # EXISTING: annotation tool
├── docs/
│   ├── PRD_V5_AUDIO_FIRST.md          # THIS DOCUMENT
│   ├── HYPOTHESIS_VALIDATION_REPORT_JENNI_V2.docx  # VALIDATION
│   └── PARADIGM_SHIFT_PAPER.md        # PAPER OUTLINE
└── colab/
    └── wavlm_utterance_training.ipynb  # NEW: GPU training notebook
```

---

## 12. What Changed from PRD v4.0

| Aspect | v4.0 (Old) | v5.0 (New) |
|--------|-----------|-----------|
| **Granularity** | Word-level (733K) | **Utterance-level (~50K)** |
| **Encoder** | Wav2Vec2-Base | **WavLM-Base+** (same params, +4.7% emotion) |
| **Feature Set** | MFCC only | **eGeMAPS 88 + HNR + spectral + WavLM 768** |
| **Labels** | Weak VTT ±5s window | **VTT utterance-level overlap** |
| **Target** | 10M segments (never reached) | **50K utterances from existing data** |
| **Core Claim** | "We built features" | **"Text labels are broken, audio is necessary"** |
| **Baselines** | None cited | **FunnyNet-W, LOLgorithm, StandUp4AI** |
| **Validation** | None | **Statcheck + Deepchecks + Human annotation** |
| **Compute** | Windows GPU (not available) | **Colab T4 / Vast.ai** |
| **Timeline** | Open-ended | **4 weeks to submission** |
