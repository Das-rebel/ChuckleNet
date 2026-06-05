# ChuckleNet: Multi-Modal Laughter & Sarcasm Prediction

**Version:** 1.0  
**Date:** 2026-06-04  
**Status:** Research Phase — Revised Architecture

---

## Executive Summary

We are building a multi-modal AI system that predicts **where, when, and how audiences will laugh** at comedic content — and separately, whether **individuals are laughing or being sarcastic**.

This is not a single model. It is a **three-product platform** built on one core insight:

> **Audience laughter is a discourse event, not an acoustic one.** Labels mark where in a transcript audience reactions follow punchlines — function words like "the", "a", "." — not acoustic laughter events. Text captures setup/punchline structure. Prosody captures timing precision.

---

## The Three Products

### Product 1: Group Laughter Predictor ⭐ CURRENT FOCUS

**What:** Predict which word-positions in a transcript will be followed by audience laughter.

**Why it's hard:** This is **discourse positioning** — predicting turn completion points where performers cue audience reactions — not acoustic event detection. Current state-of-the-art for humor detection is 74-78% F1 (text) and 62-63% F1 (audio alone). We have Val F1=0.756 (audio, Phase A) and Test F1=0.502 (late fusion, Track B).

**Core bottleneck:** IoU-F1 stuck at 0.50. Model correctly identifies the approximate laugh region but cannot pinpoint the boundary.

**Research gap:** Nobody has published on word-level audience laughter discourse positioning. This is genuinely novel.

**Commercial uses:**
- Comedian script debugging tool ("this punchline won't land — the pause is too short")
- Content resonance scoring for headlines, captions, standup clips
- Video editing (cut to reaction shot at precise moment)
- Marketing A/B testing of comedic content

---

### Product 2: Individual Laughter + Sarcasm Detector

**What:** Detect if a specific person is laughing or being sarcastic from audio + video.

**Why it's different:** Requires **speaker diarization** (who is speaking?) + **acoustic analysis** (F0 contour, breath, laryngeal features). Requires individual-level annotations, NOT VTT crowd labels.

**Data needed:** Individual-level annotations with diarization. Current VTT crowd labels cannot be used for this product.

**Commercial uses:**
- Mental health: laugh quality as depression/anxiety indicator
- Customer service: sarcasm detection in calls
- Accessibility: helping autistic individuals read social cues
- Entertainment: real-time laughter overlay for watch parties

---

### Product 3: Sarcasm-Aware Content Scorer

**What:** Score content for sarcasm potential and delivery clarity.

**Signal:** Prosodic features (F0, pause, energy) + semantic incongruity detection.

**Commercial uses:**
- Comedian practice tools
- Sales training (detect customer sarcasm)
- Content moderation

---

## Core Research Insights

### Insight 1: Labels Are Discourse Positions

VTT `[laughter]` markers mark where audience reactions follow punchlines in transcripts. Analysis of labeled tokens:

```
Top labeled tokens: 'the', 'a', 'i', 'to', 'and', '.', '!', '"'
Zero laughter-lexical tokens (haha, lol, hehe, lmao)
```

Labels land on **function words and punctuation AFTER content words** — discourse positions, not acoustic events.

**Implication:** Text models should dominate for region detection. Prosody should handle boundary refinement.

### Insight 2: Audio's Real Role Is Boundary Refinement

Per literature:
- Audio-only humor detection: 62-63% F1
- Text-only: 70-74% F1
- Audio + text: +1-5% gain

The +1-5% is **boundary precision**, not region detection. Pause duration is the single most predictive acoustic feature (Purandare 2006: 0.8s threshold before laughter).

### Insight 3: Cascade > Joint Prediction

A single token-classification head trying to do both region detection AND boundary refinement causes the IoU-F1 ceiling at 0.50. Separating these tasks lets each module focus:

- **Text (Stage 1):** "Is there a laugh cue in this region?" → coarse span prediction
- **Prosody (Stage 2):** "Where exactly does it land?" → boundary offset regression

### Insight 4: Partial Unfreezing WavLM Causes Overfitting

Phase D (partial unfreeze LR=5e-5 + CSA + Engram): Train F1=0.84, Val F1=0.40.  
Phase A (fully frozen WavLM): Val F1=0.756.

**Conclusion:** Fully frozen WavLM + attention pooling is the correct audio encoder approach.

---

## Revised Research Hypotheses

| H# | Hypothesis | Method | Status |
|----|-----------|--------|--------|
| H0 | Labels = discourse positions | Analyze label distribution across tokens | ✅ VERIFIED |
| H1 | Text → region, Prosody → boundary | Cascade architecture | 🆕 NEW |
| H2 | Pause is #1 acoustic feature | Extract pause features (0.8s threshold) | 🆕 NEW |
| H3 | F0 DROP predicts laugh timing | Extract F0 contours | 📋 TODO |
| H4 | Cascade beats joint | Compare cascade vs simultaneous | 📋 TODO |
| H5 | Cross-lingual discourse transfer | Train en, test zh/hi | 📋 TODO |
| H6 | Individual laughter = separate task | Diarization + acoustic | 📋 TODO |
| H7 | Sarcasm = prosodic + incongruity | Multi-task learning | 📋 TODO |

---

## Target Metrics

### Product 1: Group Laughter

| Stage | Metric | Current | Target | Method |
|-------|--------|---------|--------|--------|
| Region Detection | Span F1 | — | 0.75+ | XLM-R text-only |
| Boundary Refinement | IoU-F1 | 0.50 | 0.65+ | Prosody cascade |
| Late Fusion | Token F1 | 0.50 | 0.70+ | Text + prosody |

### Product 2: Individual Laughter

| Metric | Current | Target |
|--------|---------|--------|
| Per-person laughter detection | No data | 0.80+ |
| Sarcasm detection | No data | 0.75+ |

---

## Architecture

### Cascade Architecture (Product 1)

```
STAGE 1: Text Region Proposal
├── Model: XLM-R base fine-tuned
├── Input: word sequence + punctuation markers
├── Output: coarse laugh regions (span-level)
└── Metric: Span-level F1

    ↓ (crop audio to Stage 1 regions)

STAGE 2: Prosody Boundary Refinement
├── Model: WavLM frozen + attention pooling → MLP
├── Features: pause duration, F0 contour, RMS energy, MFCCs
├── Output: precise word-level boundaries
└── Metric: IoU-F1

FINAL: Simple concatenation + MLP (if fusing at token level)
├── Text: XLM-R [CLS] or mean pool over span
├── Prosody: attention-pooled WavLM OR extracted features
└── NOT: complex gating, CSA, Engram (ablation showed these hurt)
```

### Individual Laughter Architecture (Product 2)

```
INPUT: Audio + Video frames
    ↓
Speaker Diarization (pyannote or similar)
    ↓
Per-speaker acoustic features:
├── F0 statistics (mean, range, slope, voiced_ratio)
├── Pause duration (before/after speech)
├── RMS energy
├── MFCCs 1-13
├── Spectral: centroid, bandwidth, rolloff
    ↓
Classifier: does THIS person find it funny?
└── Per-person laugh binary + intensity score
```

---

## Data Requirements

### Product 1: What We Have
- 389K-549K aligned word-level segments from 71 videos
- VTT [laughter] markers as labels
- Audio files for WavLM processing
- Prosody features: 21-dim extracted, 6 active dims

### Product 1: What We Need
- **Pause feature extraction**: The single most validated feature — barely used
- **F0 contour extraction**: For boundary refinement
- **Word-level prosody alignment**: Ensure video_id + start timestamps match prosody cache
- **Cross-lingual data**: Expand beyond en (zh, hi-latn already in dataset)

### Product 2: What We Need
- **Individual-level annotations**: VTT labels are crowd labels, not individual
- **Speaker diarization**: Who's laughing? One person vs. crowd?
- **Isolated laughter samples**: For acoustic feature validation
- **Sarcasm data**: Existing datasets (Sar sarcasm, MUGEAR) for pre-training

---

## Key References

| Paper | Contribution | Relevance |
|-------|-------------|----------|
| Pickering 2009 | F0 DROP at punchline | H3 |
| Purandare 2006 | Pause 0.8s threshold before laughter | H2 — most validated acoustic feature |
| Bachorowski 2001 | Laughter 250-500Hz spectral peak | Individual laughter |
| Bertero 2016 | Pause as #1 feature for humor detection | H2 validation |
| Wosu 2023 | MultiLinguahah: unsupervised cross-lingual laughter | H5 |
| Castro 2023 | BYOL-A for self-supervised laughter detection | Product 2 |

---

## What Failed and Why

| Attempt | Result | Lesson |
|---------|--------|--------|
| Phase D: partial unfreeze + CSA + Engram | Val F1=0.40, catastrophic overfitting | Never partial unfreeze at standard LR |
| Phase D: class_weight [1,4] | Val P dropped 0.30→0.19 | Start at [1, 2.5] max |
| Phase D: audio from Drive every batch | 12K+ reads/epoch, Colab hang | Always cache to RAM |
| CSA attention | Ablation hurt | Simple pooling beats CSA |
| Engram bottleneck | Ablation hurt | No compression needed |
| prosody_dim [1-12] and [19-20] | All zeros | These are padding/unused |
| Balanced class weights | Complete collapse | Never use balanced for this task |

---

## Next Steps (Priority Order)

1. **Extract pause features** — highest validated acoustic feature, barely used
2. **Rebuild prosody alignment** — ensure all video_id + start timestamps match for joining
3. **Run Stage 1 text-only cascade** — establish region detection baseline
4. **Run Stage 2 prosody-only cascade** — establish boundary refinement baseline
5. **Full cascade evaluation** — compare cascade vs joint vs late fusion
6. **Individual laughter data collection** — separate dataset for Product 2

---

## Open Questions

1. **Is cascade actually better than late fusion for this task?** — needs validation
2. **Which prosody features matter most for boundary refinement?** — pause vs F0 vs energy
3. **Can discourse structure transfer across languages?** — en→zh→hi
4. **What's the minimum viable dataset for individual laughter?** — how much data per person
5. **Is Product 2 commercially viable without a hospital/clinic partnership?** — mental health angle requires HIPAA, etc.
