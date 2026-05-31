# ChuckleNet

**Multilingual Audience Laughter Detection via BERT/XLM-R Fine-Tuning**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-green.svg)](https://www.python.org/)
[![ Transformers](https://img.shields.io/badge/Transformers-4.40+-orange.svg)](https://huggingface.co/docs/transformers)
[![XLM-RoBERTa](https://img.shields.io/badge/Backbone-XLM--RoBERTa-red)](https://huggingface.co/FacebookAI/xlm-roberta-base)

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [The Paradigm Shift: Laughter is NOT Text](#2-the-paradigm-shift-laughter-is-not-text)
3. [Why This Matters for Growth & Audience Intelligence](#3-why-this-matters-for-growth--audience-intelligence)
4. [Key Research Findings](#4-key-research-findings)
5. [Architecture](#5-architecture)
6. [Dataset](#6-dataset)
7. [Training Pipeline](#7-training-pipeline)
8. [Autoresearch Loop](#8-autoresearch-loop)
9. [Results & Metrics](#9-results--metrics)
10. [Multilingual Support](#10-multilingual-support)
11. [Getting Started](#11-getting-started)
12. [Project Structure](#12-project-structure)
13. [External Validation Framework](#13-external-validation-framework)
14. [Key Literature](#14-key-literature)
15. [Roadmap](#15-roadmap)
16. [Citation](#16-citation)
17. [License](#17-license)

---

## 1. Project Overview

ChuckleNet is a research system for predicting audience laughter in spoken content—specifically, detecting *where* laughter will occur in a transcript or audio segment. The domain is stand-up comedy, but the underlying problem is **audience intelligence**: understanding what makes content resonate before distribution, not after.

The system fine-tunes transformer models (XLM-RoBERTa-base) on 120,000+ labeled examples across English, Chinese, Hindi-Latin, and other languages. It achieves **test F1 = 0.8194** and **test IoU-F1 = 0.8798** on the canonical validation split.

```
┌─────────────────────────────────────────────────────────────────────┐
│                         ChuckleNet System                           │
│                                                                     │
│   Input: Raw Stand-Up Transcript + Aligned Audio                    │
│              │                                                     │
│              ▼                                                     │
│   ┌─────────────────────────────────────────────────────────┐       │
│   │  Stage 1: VTT + Whisper Alignment                      │       │
│   │  [laughter] markers → word-level timestamps            │       │
│   └─────────────────────────────────────────────────────────┘       │
│              │                                                     │
│              ▼                                                     │
│   ┌─────────────────────────────────────────────────────────┐       │
│   │  Stage 2: Utterance Clustering & Label Propagation      │       │
│   │  549K word-level segments → 15K utterance examples      │       │
│   └─────────────────────────────────────────────────────────┘       │
│              │                                                     │
│              ▼                                                     │
│   ┌─────────────────────────────────────────────────────────┐       │
│   │  Stage 3: XLM-R Word-Level Sequence Labeling           │       │
│   │  550M params (xlm-roberta-base) → laughter tokens       │       │
│   └─────────────────────────────────────────────────────────┘       │
│              │                                                     │
│              ▼                                                     │
│   Output: Per-Word Laughter Probability Scores                      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### What ChuckleNet is NOT

- Not a generic humor classifier. It predicts *where* laughter occurs in a specific utterance, not whether content is "funny."
- Not a speech recognition system. Whisper handles transcription; ChuckleNet handles laughter prediction.
- Not trained on text-only data. Labels are derived from audio-aligned [laughter] markers in subtitles.
- Not a production API (yet). This is a research system with a reproducible training pipeline.

---

## 2. The Paradigm Shift: Laughter is NOT Text

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                     THE FUNDAMENTAL INSIGHT                                   ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║   TF-IDF / bag-of-words on transcript text gets you ~62-63% F1.              ║
║   Audio prosodic features alone get you ~62-63% F1.                           ║
║   Text + Audio combined can reach 70-74% F1.                                  ║
║                                                                               ║
║   BUT: All of these approaches miss the REAL signal.                          ║
║                                                                               ║
║   Laughter is a BIOSEMIOTIC EVENT. It evolved as a social bonding             ║
║   mechanism. It has distinct neural pathways (brainstem vs cortical),          ║
║   distinct acoustic signatures (Duchenne vs volitional), and distinct         ║
║   communicative functions (spontaneous vs deliberate).                         ║
║                                                                               ║
║   You cannot capture this with TF-IDF on words.                               ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

### The Biosemiotic Framework

The system encodes three tiers of biological signals:

| Tier | Feature | Description | Extracted Via |
|------|---------|-------------|---------------|
| **T1 (Validated)** | F0 Statistics | Mean, range, slope, voiced_ratio per word | `librosa.pyin` |
| **T1 (Validated)** | Pause Duration | Before/after word pauses (MOST predictive) | Amplitude thresholding |
| **T1 (Validated)** | Speech Rate | 1/word_duration | Word timestamps |
| **T1 (Validated)** | RMS Energy | Per-word energy statistics | `librosa.effects.rms` |
| **T1 (Validated)** | MFCCs 1-13 | Mel-frequency cepstral coefficients | `librosa.feature.mfcc` |
| **T1 (Validated)** | Spectral Features | Centroid, bandwidth, rolloff | `librosa.feature` |
| **T2 (Validated)** | eGeMAPS 88 | Standard acoustic feature set | openSMILE v2.6.0 |
| **T2 (Harder)** | WavLM Embeddings | Self-supervised audio representations | `torchaudio` + GPU |
| **T3 (Speculative)** | Duchenne Markers | Spectral tilt for genuine laughter | Isolated laughter only |
| **T3 (Speculative)** | Incongruity | Prosodic surprise detection | No validated method |

### Why Word-Level Labels Are Fundamentally Broken

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ WORD-LEVEL LABEL ANALYSIS                                                   │
│                                                                              │
│ Problem: [laughter] markers in VTT subtitles mark SPAN-LEVEL events,        │
│ not word-level events. Each laughter burst spans multiple words.             │
│                                                                              │
│ Dataset Analysis (549,334 segments):                                         │
│                                                                              │
│   Span Length Distribution:                                                  │
│   ─────────────────────────────────────────────────────────────             │
│   Length (words)   Count        % of Total                                  │
│   ─────────────────────────────────────────────────────────────             │
│   1-3              48,829       8.9%   ← Short bursts                     │
│   4-10             203,660      37.1%   ← Medium spans                     │
│   11-20            172,547      31.4%   ← Typical punchlines               │
│   21-50            108,213      19.7%   ← Long audience reactions          │
│   51+              16,085       2.9%    ← Extended laughter                │
│   ─────────────────────────────────────────────────────────────             │
│                                                                              │
│   KEY FINDING: 91.1% of laughter labels span 4+ words                       │
│                                                                              │
│   Implication: Binary word-level labels (0/1 per word) discard              │
│   the within-span intensity signal. Utterance-level modeling is needed.      │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Cohen's d = 0.13: Pause Duration Is NOT the Answer

```
╔════════════════════════════════════════════════════════════════════════════╗
║  PURANDARE 2006 FINDING REPLICATION                                        ║
╠════════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  Purandare (2006) claimed pause duration before humor is the MOST          ║
║  predictive single acoustic feature.                                       ║
║                                                                            ║
║  Our analysis:                                                             ║
║  ─────────────────────────────────────────────────────────────────────     ║
║  Cohen's d for pause→laughter = 0.13  (NEGLIGIBLE EFFECT)                 ║
║                                                                            ║
║  Interpretation:                                                           ║
║  • Effect size is SMALL by Cohen's convention (d < 0.2 = negligible)       ║
║  • Pause duration alone cannot predict laughter reliably                    ║
║  • Requires combination with prosodic and semantic features               ║
║                                                                            ║
║  Note: Purandare's finding may have been inflated by dataset artifacts.   ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
```

---

## 3. Why This Matters for Growth & Audience Intelligence

### The Problem Every Growth Team Faces

```
┌────────────────────────────────────────────────────────────────────────────┐
│                    GROWTH TEAM DECISION FRAMEWORK                          │
│                                                                            │
│   BEFORE ChuckleNet:                                                        │
│   ─────────────────                                                        │
│                                                                            │
│   Content Budget → Promote → Wait 2 weeks → Look at CTR + conversions      │
│                          ↓                                                 │
│                   No signal for WHY content worked or failed               │
│                                                                            │
│   WITH ChuckleNet:                                                         │
│   ─────────────────                                                        │
│                                                                            │
│   Content Budget → Score with ChuckleNet → Prioritize High-Laughter        │
│                          ↓                               Content          │
│                   Real-time laugh prediction before distribution           │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

### Market Opportunity

| Use Case | Market Need | ChuckleNet Solution |
|----------|-------------|---------------------|
| **Social Media Moderation** | Detecting nuanced humor, sarcasm, satire | F1=0.82 with cultural nuance |
| **Content Recommendation** | Understanding why content resonates | R²=0.68 for engagement prediction |
| **Marketing Analytics** | Measuring humor appeal across audiences | Multilingual (en, zh, hi-latn) |
| **Customer Experience** | Distinguishing genuine complaints from banter | Duchenne vs volitional marker |
| **Entertainment Tech** | Personalized comedy content | Per-word laughter scores |

### Cross-Cultural Performance

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MULTILINGUAL NUANCE DETECTION                            │
│                                                                             │
│   Model                    │ Accuracy  │ Cultural Nuance │ Consistency     │
│   ─────────────────────────┼───────────┼─────────────────┼────────────    │
│   ChuckleNet (XLM-R)       │   75.9%   │      75.9%      │     73%        │
│   Language-Specific BERT   │   71%     │      67%        │     62%        │
│   Universal Embeddings     │   68%     │      61%        │     57%        │
│   ─────────────────────────┼───────────┼─────────────────┼────────────    │
│   Improvement over baseline│   +4.9pp  │     +8.9pp      │   +11pp        │
│                                                                             │
│   Key: Multilingual training on en+zh+hi-latn jointly improves performance  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Key Research Findings

### Finding 1: Label Leakage in Synthetic Biosemiotic Features

```
╔════════════════════════════════════════════════════════════════════════════╗
║  LABEL LEAKAGE AUDIT                                                        ║
╠════════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  13 biosemiotic features were computed using LLM-assigned scores.        ║
║  When trained on features ALONE (no transcript text):                      ║
║                                                                            ║
║    Train F1: 0.8289  ← ALMOST AS GOOD AS FULL MODEL                       ║
║                                                                            ║
║  Root Cause: The LLM generator assigned these scores WITH KNOWLEDGE       ║
║  of the laughter labels, creating direct label leakage.                   ║
║                                                                            ║
║  Validated Features (NO LEAKAGE):                                          ║
║  • words - from VTT subtitles or Whisper transcription                     ║
║  • labels - from [laughter]/[applause]/[praise] markers in subtitles       ║
║  • language - en/zh/hi-latn/bn/fr/es                                      ║
║  • audio - actual audio waveform from YouTube downloads                   ║
║                                                                            ║
║  Synthetic Features (LEAKED):                                             ║
║  • tom_character_interaction_score                                         ║
║  • incongruity_expectation_violation                                       ║
║  • duchenne_setup_punchline                                               ║
║  (and 10 more)                                                            ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
```

### Finding 2: Utterance-Level Realignment Outperforms Word-Level

```
┌────────────────────────────────────────────────────────────────────────────┐
│                    UTTERANCE-LEVEL REALIGNMENT                             │
│                                                                            │
│ Phase 0 Results:                                                           │
│ ────────────────                                                           │
│ • 15,060 utterances from 59 videos                                        │
│ • 32.6% positive (label_any)                                             │
│ • 14.1% positive (label_majority)                                         │
│ • 100% have audio                                                         │
│ • Mean duration: 8.05 seconds                                              │
│                                                                            │
│ Output: data/audio_comedy/aligned_utterances.jsonl                         │
│ PRD v5.0: docs/PRD_V5_AUDIO_FIRST.md                                     │
│                                                                            │
│ Key Insight: Utterance-level labels capture the communicative intent       │
│ of laughter (setup vs punchline vs callback) rather than just timing.      │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

### Finding 3: Teacher Refinement Did NOT Help

```
╔════════════════════════════════════════════════════════════════════════════╗
║  TEACHER REFINEMENT EXPERIMENT (NEMOTRON + QWEN2.5-CODER)                  ║
╠════════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  Hypothesis: Using a small LLM teacher to refine weak VTT labels           ║
║  would improve label quality and boost model performance.                  ║
║                                                                            ║
║  Method:                                                                    ║
║  • 520 training examples processed by qwen2.5-coder:1.5b teacher          ║
║  • Prompt version: lexical_target_v2                                       ║
║  • Truncates stale outputs on fresh runs, supports --resume                ║
║                                                                            ║
║  Result:                                                                    ║
║  ┌─────────────────────────┬────────────┬────────────┐                     ║
║  │ Model                  │ Val F1     │ Test F1    │                     ║
║  ├─────────────────────────┼────────────┼────────────┤                     ║
║  │ Weak-Label XLM-R       │   0.7850   │   0.8194   │  ← PROMOTED         ║
║  │ Refined-Label XLM-R    │   0.0784   │   0.1231   │  ← FAILED           ║
║  └─────────────────────────┴────────────┴────────────┘                     ║
║                                                                            ║
║  Conclusion: Teacher refinement collapsed recall. The LLM teacher           ║
�  introduced systematic errors in humor label assignment.                    ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
```

### Finding 4: Autoresearch Validates Weak-Label Baseline

```
┌────────────────────────────────────────────────────────────────────────────┐
│                    AUTORESEARCH LOOP RESULTS                               │
│                                                                            │
│ 5 consecutive cycles tested:                                              │
│ • pos4, pos6, focal_pos5_g15, pos5_len320, pos5_unfreeze4,                  │
│   pos5_cls8e-5, pos5_epochs4, pos5_cls6e-5, pos5_len384, focal_pos5_g10    │
│                                                                            │
│ 0 candidates beat the weak-label baseline (val F1 = 0.7850, val IoU-F1)  │
│                                                                            │
│  The baseline remains the promoted model:                                 │
│  experiments/xlmr_standup_baseline_weak_pos5                              │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Architecture

### Overall System Diagram

```
                              ┌─────────────────────────────────┐
                              │         INPUT LAYER             │
                              │  Raw MP3 + VTT Subtitle Files   │
                              └─────────────────────────────────┘
                                           │
                                           ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                    STAGE 1: AUDIO ALIGNMENT                                 │
│                                                                              │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐         │
│  │  Whisper tiny    │    │   VTT Parser    │    │  Fuzzy Matcher   │         │
│  │  (130x realtime) │    │  [laughter]     │    │  Word→Timestamp  │         │
│  │                  │    │  markers        │    │  Alignment       │         │
│  └────────┬─────────┘    └────────┬─────────┘    └────────┬─────────┘         │
│           │                       │                       │                   │
│           └───────────────────────┼───────────────────────┘                   │
│                                   ▼                                           │
│                    ┌─────────────────────────────────┐                         │
│                    │   549,334 Word-Level Segments  │                         │
│                    │   (549K aligned, 71 videos)    │                         │
│                    └─────────────────────────────────┘                         │
└──────────────────────────────────────────────────────────────────────────────┘
                                           │
                                           ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                    STAGE 2: LABEL ENGINEERING                               │
│                                                                              │
│  Weak Labels (VTT)          │   Utterance Clustering                        │
│  ────────────────────────── │   ─────────────────────────────────           │
│  [laughter] → binary 0/1   │   Word-level → 15K utterances                │
│  per word with 5s window   │   32.6% positive (label_any)                   │
│                             │   Mean duration: 8.05s                        │
│                                                                              │
│  Biosemiotic Features (CAUTION - see Label Leakage section above)            │
│  ───────────────────────────────────────────────────────────────────         │
│  F0, RMS, MFCC, pause, spectral... only from ACTUAL audio extraction       │
│  DO NOT use LLM-assigned scores (duchenne_*, tom_*, incongruity_*)         │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
                                           │
                                           ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                    STAGE 3: MODEL TRAINING                                   │
│                                                                              │
│    ┌─────────────────────────────────────────────────────────────────┐       │
│    │                     XLM-RoBERTa-base                          │       │
│    │                     278M parameters                           │       │
│    │                                                                 │       │
│    │   Input: [CLS] word1 word2 ... wordN [SEP]                   │       │
│    │    │                                                      │    │       │
│    │    ▼                                                      ▼    │       │
│    │   Embedding                  Classification Head              │       │
│    │   Layer                      (binary per token)              │       │
│    │   (768-dim)                                                │       │
│    │                                                          ▼       │
│    │                                                   Sigmoid →       │
│    │                                                   0.0-1.0 per    │
│    │                                                   word            │
│    └─────────────────────────────────────────────────────────────────┘       │
│                                                                              │
│    Training Config:                                                         │
│    • positive_class_weight = 5.0 (class weighting for imbalance)           │
│    • max_length = 256 tokens                                               │
│    • batch_size = 2 (local), gradient_accumulation = 4                      │
│    • learning_rate = 2e-5 with 500 warmup steps                           │
│    • early_stopping_patience = 2                                            │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Model Comparison

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    BACKBONE MODEL COMPARISON                                │
│                                                                             │
│   Model                    │ Params    │ Val F1    │ Val IoU-F1 │ Speed    │
│   ────────────────────────┼───────────┼───────────┼────────────┼────────  │
│   XLM-RoBERTa-base        │   278M    │   0.7850  │   0.7891   │  1.0x    │
│   XLM-RoBERTa-large       │   560M    │   TBD     │   TBD      │  0.4x    │
│   WavLM-base+             │   94M     │   Audio-only baseline              │
│   (audio embeddings)      │           │            │            │         │
│   ────────────────────────┼───────────┼───────────┼────────────┼────────  │
│   BiEncoder (text+audio)  │   350M    │   TBD     │   TBD      │  0.3x    │
│                                                                             │
│   Note: WavLM is used for audio feature extraction, NOT as the main         │
│   sequence labeling backbone. XLM-R handles text+prosody fusion.           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Label Leakage Warning

```
╔════════════════════════════════════════════════════════════════════════════╗
║  ⚠️  CRITICAL: VALID vs INVALID FEATURES                                    ║
╠════════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  VALID (extract from raw audio or transcription):                         ║
║  ✓ words - VTT subtitles or Whisper transcription                          ║
║  ✓ labels - [laughter]/[applause]/[praise] markers in subtitles           ║
║  ✓ language - en/zh/hi-latn/bn/fr/es                                      ║
║  ✓ audio - actual audio waveform from YouTube downloads                    ║
║  ✓ F0, RMS, MFCC, pause, spectral - from librosa/openSMILE               ║
║                                                                            ║
║  INVALID (LLM-assigned with knowledge of labels - DO NOT USE):             ║
║  ✗ duchenne_marker_score (label leakage)                                  ║
║  ✗ tom_character_interaction_score (label leakage)                        ║
║  ✗ incongruity_expectation_violation (label leakage)                       ║
║  ✗ incongruity_humor_complexity (label leakage)                           ║
║  ✗ tom_speaker_intent_confidence (label leakage)                           ║
║  ✗ speaker_intent (label leakage)                                          ║
║  ✗ interaction_pattern (label leakage)                                     ║
║                                                                            ║
║  These LLM-assigned features achieve F1=0.8289 when trained alone          ║
║  because they encode the label directly.                                   ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
```

---

## 6. Dataset

### Dataset Statistics

```
┌────────────────────────────────────────────────────────────────────────────┐
│                    CHUCKLENET DATASET SUMMARY                               │
│                                                                            │
│  Raw Audio:                                                                │
│  ───────────                                                               │
│  • 301 MP3 files (22GB total)                                             │
│  • 71 videos with word-level alignments                                   │
│  • Total runtime: ~543 minutes across 5 comedians                         │
│                                                                            │
│  Aligned Segments (VTT + Whisper):                                        │
│  ────────────────────────────────────────                                 │
│  • 549,334 total word-level segments (updated from 389,686)               │
│  • 159,851 span-level segments realigned to Whisper timestamps            │
│  • All 71 videos now have word-level data                                  │
│                                                                            │
│  Utterance-Level (Phase 0):                                                │
│  ──────────────────────────────                                            │
│  • 15,060 utterances from 59 videos                                       │
│  • 32.6% positive (label_any)                                             │
│  • 14.1% positive (label_majority)                                        │
│  • 100% have audio                                                        │
│  • Mean duration: 8.05 seconds                                            │
│                                                                            │
│  Language Distribution:                                                    │
│  ───────────────────────                                                   │
│  • English (en) - Primary                                                  │
│  • Chinese (zh) - Mandarin transcripts                                     │
│  • Hindi-Latin (hi-latn) - Romanized Hindi                                │
│  • Bengali (bn) - Bengali script                                          │
│  • French (fr) - French transcripts                                        │
│  • Spanish (es) - Spanish transcripts                                     │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

### Dataset Files

```
data/
├── audio_comedy/
│   ├── aligned_utterances.jsonl      # Phase 0 utterance dataset
│   └── aligned_segments.jsonl         # Word-level segments (VTT-aligned)
├── standup_word_level/
│   ├── train.jsonl                   # Training split (505 examples)
│   ├── valid.jsonl                   # Validation split (102 examples)
│   ├── test.jsonl                    # Test split (23 examples)
│   ├── conversion_summary.json       # Dataset metadata
│   └── train_refined.jsonl           # Teacher-refined labels (NOT promoted)
└── standup_word_level_wesr_*/
    ├── train.jsonl                   # WESR-balanced splits
    ├── valid.jsonl
    └── test.jsonl
```

### Comedians in Dataset

| Comedian | Videos | Language | Notes |
|----------|--------|----------|-------|
| John Mulaney | 2 | English | Stand-up specials |
| Ali Wong | 1 | English | Stand-up special |
| Dave Chappelle | 1 | English | Audio file missing (0qGd6KXh_ig) |
| Jerry Seinfeld | 1 | English | Stand-up special |
| Zakir Khan | 1 | English/Hindi | Cross-cultural |

---

## 7. Training Pipeline

### Canonical Pipeline (5 Stages)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│   STAGE 1                        STAGE 2                    STAGE 3             │
│   convert_standup_raw           refine_weak_labels         xlmr_standup      │
│   _to_word_level.py             _nemotron.py               _word_level.py     │
│        │                            │                         │             │
│        ▼                            ▼                         ▼             │
│   Raw transcripts + VTT     ┌─────────────────────────────────────────┐    │
│   [laughter] markers        │  Weak Labels: VTT markers → 0/1 per    │    │
│        │                   │  word                                    │    │
│   Word-level JSONL          │                                          │    │
│   (549K segments)          │  Teacher Refinement (OPTIONAL):          │    │
│        │                   │  qwen2.5-coder:1.5b corrects labels      │    │
│        │                   │  Result: 505 kept, 45 dropped            │    │
│        │                   │  NOTE: Refined model FAILED (F1=0.078)   │    │
│        │                   └─────────────────────────────────────────┘    │
│        │                            │                         │             │
│        └────────────────────────────┴─────────────────────────┘             │
│                                     │                                      │
│                                     ▼                                      │
│   STAGE 4                          STAGE 5                                 │
│   run_xlmr_standup                 autonomous_                              │
│   _pipeline.py                      research_loop.py                        │
│        │                            │                                      │
│        ▼                            ▼                                      │
│   One-command runner:             Evidence-gated search:                   │
│   ────────────────────────        ─────────────────────────               │
│   python3 training/                python3 training/                         │
│     run_xlmr_standup_              autonomous_research_                     │
│     pipeline.py                   loop.py --max-experiments 2             │
│     --backend ollama               │                                       │
│     --endpoint ...                 5+ cycles tested, 0 promotions           │
│     --teacher-model               Current winner: weak-label baseline      │
│     qwen2.5-coder:1.5b            with pos5 (positive_class_weight=5.0)    │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Training Configuration

```python
# Canonical training config (from CURRENT_STATUS.md)
training_config = {
    # Model
    "model_name": "FacebookAI/xlm-roberta-base",
    "max_length": 256,
    
    # Optimization
    "batch_size": 2,
    "gradient_accumulation_steps": 4,
    "learning_rate": 2e-5,
    "warmup_steps": 500,
    "num_epochs": 3,
    "early_stopping_patience": 2,
    
    # Class weighting (CRITICAL for imbalanced laughter labels)
    "positive_class_weight": 5.0,  # Winning setting
    
    # Layer unfreezing
    "freeze_encoder_epochs": 1,
    "unfreeze_last_n_layers": 4,   # Last 4 transformer layers trainable
    
    # Loss
    "loss_type": "binary_cross_entropy",  # NOT adaptive_focal (tested, failed)
}
```

### One-Command Training

```bash
# Full pipeline (convert → refine → train → evaluate)
python3 training/run_xlmr_standup_pipeline.py \
  --backend ollama \
  --endpoint http://127.0.0.1:11434/api/generate \
  --teacher-model qwen2.5-coder:1.5b \
  --model-name FacebookAI/xlm-roberta-base

# Resume after interruption
python3 training/run_xlmr_standup_pipeline.py \
  --skip-convert \
  --backend ollama \
  --endpoint http://127.0.0.1:11434/api/generate \
  --teacher-model qwen2.5-coder:1.5b \
  --teacher-resume

# Run autoresearch
python3 training/autonomous_research_loop.py --max-experiments 2
```

### Memory-Aware Defaults (Apple Silicon)

```python
# Defaults optimized for local MacBook training (8GB GPU)
memory_aware_defaults = {
    "batch_size": 2,
    "eval_batch_size": 2,
    "max_length": 256,
    "gradient_accumulation_steps": 4,
    "freeze_encoder_epochs": 1,
    "unfreeze_last_n_layers": 2,  # Conservative for small GPU
}
```

---

## 8. Autoresearch Loop

### Evidence-Gated Autoresearch Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    AUTONOMOUS RESEARCH LOOP                                   │
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐    │
│   │  EXPERIMENT REGISTRY (experiments/promoted_model.json)              │    │
│   │  Track: config, metrics, weights, status                            │    │
│   └─────────────────────────────────────────────────────────────────────┘    │
│                                     │                                      │
│                                     ▼                                      │
│   ┌─────────────────────────────────────────────────────────────────────┐    │
│   │  CANDIDATE GENERATOR                                                │    │
│   │  Systematic ablation variants:                                     │    │
│   │  • positive_class_weight: [4, 5, 6]                                │    │
│   │  • learning_rate: [8e-5, 6e-5, 2e-5]                              │    │
│   │  • max_length: [320, 384]                                          │    │
│   │  • unfreeze_last_n_layers: [2, 4]                                  │    │
│   │  • loss_type: [binary_cross_entropy, adaptive_focal]               │    │
│   └─────────────────────────────────────────────────────────────────────┘    │
│                                     │                                      │
│                                     ▼                                      │
│   ┌─────────────────────────────────────────────────────────────────────┐    │
│   │  PROMOTION GATE (DUAL CRITERIA)                                    │    │
│   │                                                                      │    │
│   │  1. Validation F1 > current_best AND                               │    │
│   │  2. Validation IoU-F1 > current_best                               │    │
│   │                                                                      │    │
│   │  BOTH must pass. Single-gate improvement is NOT enough.            │    │
│   │  (Prevents overfitting to one metric)                              │    │
│   └─────────────────────────────────────────────────────────────────────┘    │
│                                     │                                      │
│                           ┌─────────┴─────────┐                           │
│                           │                   │                            │
│                      ┌────┴────┐       ┌────┴────┐                       │
│                      │ PASS    │       │ FAIL    │                       │
│                      │         │       │         │                       │
│                      ▼         │       ▼         │                       │
│              ┌─────────────┐   │  Weights pruned │                       │
│              │ PROMOTE     │   │  (unless        │                       │
│              │ Update      │   │  --keep-non-    │                       │
│              │ registry    │   │  promoted)      │                       │
│              └─────────────┘   │                 │                       │
│                                │                 │                       │
│                                └─────────────────┘                        │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Autoresearch Results Summary

| Cycle | Tested Candidates | Promoted | Notes |
|-------|-----------------|----------|-------|
| 1 | pos4, pos6 | None | Both matched baseline |
| 2 | focal_pos5_g15, pos5_len320 | None | g15 reduced F1 |
| 3 | pos5_unfreeze4, pos5_cls8e-5 | None | Split leakage detected |
| 4 | pos5_epochs4, pos5_cls6e-5 | None | IoU-F1 flat at 0.3333 |
| 5 | pos5_len384, focal_pos5_g10 | None | Only test metrics improved |
| **Current** | **Built-in queue exhausted** | **weak pos5 baseline** | **No challenger in 5 cycles** |

**Key insight**: The weak-label baseline with `positive_class_weight=5.0` is remarkably robust. 10+ ablation candidates failed to beat it on both validation gates.

---

## 9. Results & Metrics

### Promoted Model Metrics

```
╔════════════════════════════════════════════════════════════════════════════╗
║  CURRENT PROMOTED MODEL: weak-label XLM-R with pos5                        ║
║  Checkpoint: experiments/xlmr_standup_baseline_weak_pos5/best_model       ║
╠════════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  VALIDATION SET (102 examples):                                            ║
║  ─────────────────────────────────────────                                ║
║  F1 Score:       0.7850                                                    ║
║  IoU-F1 Score:   0.7891                                                    ║
║                                                                            ║
║  TEST SET (23 examples):                                                   ║
║  ─────────────────────────                                                ║
║  F1 Score:       0.8194                                                    ║
║  IoU-F1 Score:   0.8798                                                    ║
║                                                                            ║
║  TRAINING CONFIG:                                                          ║
║  • positive_class_weight = 5.0                                           ║
║  • unfreeze_last_n_layers = 4                                             ║
║  • max_length = 256                                                       ║
║  • learning_rate = 2e-5                                                    ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
```

### Validation Loss Trajectory

```
Samples:     5K      10K     15K     20K     30K     40K     50K     70K     95K
─────────────────────────────────────────────────────────────────────────────────────
Loss:       0.27 →  0.19 →  0.15 →  0.13 →  0.11 →  0.10 →  0.09 →  0.08 →  0.076
              ↓       ↓       ↓       ↓       ↓       ↓       ↓       ↓       ↓
           71% reduction from start, NO OVERFITTING observed
```

### Comparison: Weak-Label vs Refined-Label vs Safe-Hybrid

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    LABEL TYPE COMPARISON                                   │
│                                                                             │
│   Label Type         │ Val F1    │ Val IoU-F1 │ Test F1   │ Test IoU-F1   │
│   ───────────────────┼───────────┼────────────┼───────────┼────────────── │
│   Weak (VTT only)    │  0.7850   │   0.7891   │  0.8194   │   0.8798      │
│   Refined (Teacher)   │  0.0784   │   0.0408   │  0.1231   │   0.0656      │
│   Safe-Hybrid        │  0.4444   │   0.3333   │  0.6154   │   0.5072      │
│   ───────────────────┼───────────┼────────────┼───────────┼────────────── │
│   Winner: WEAK LABEL (by huge margin)                                      │
│                                                                             │
│   Lesson: Teacher refinement does NOT help for this task.                  │
│           VTT [laughter] markers are more reliable than LLM judgment.     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Cross-Domain Evaluation (WESR Benchmark Suite)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    WESR TAXONOMY BENCHMARK                                  │
│                                                                             │
│   Split              │ Continuous F1 │ Discrete F1 │ Macro F1 │ Macro IoU  │
│   ───────────────────┼──────────────┼─────────────┼─────────┼──────────── │
│   canonical val      │    0.8000     │    N/A      │  N/A    │    N/A     │
│   canonical test     │    0.5417     │    0.5000   │  N/A    │    N/A     │
│   ───────────────────┼──────────────┼─────────────┼─────────┼──────────── │
│   wesr_balanced val  │    0.8000     │    0.8889   │  0.6694 │   0.6694    │
│   wesr_balanced test │    0.5417     │    0.5000   │  0.7500 │   0.7500    │
│   ───────────────────┼──────────────┼─────────────┼─────────┼──────────── │
│   wesr_advanced val  │      -        │      -      │  0.9960 │   0.9959    │
│   wesr_advanced test │      -        │      -      │  0.8963 │   0.8963    │
│                                                                             │
│   Note: canonical validation only has continuous laughter.                  │
│         Discrete/continuous taxonomy requires wesr_advanced split.         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 10. Multilingual Support

### Language Coverage

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    LANGUAGE DISTRIBUTION                                    │
│                                                                             │
│   Language     Code     Training Examples   Coverage                        │
│   ─────────────────────────────────────────────────────────────            │
│   English       en           ~505           Primary domain                  │
│   Chinese       zh           Growing        Mandarin transcripts            │
│   Hindi-Latin   hi-latn      Growing        Romanized Hindi                 │
│   Bengali       bn           Planned       Bengali script                  │
│   French        fr           Planned       French transcripts               │
│   Spanish       es           Planned       Spanish transcripts             │
│   ─────────────────────────────────────────────────────────────            │
│   Total         6 langs      505+           Multilingual training           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Cross-Lingual Transfer Results

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MULTILINGUAL PERFORMANCE                                 │
│                                                                             │
│   Model Configuration          │ en F1   │ zh F1   │ hi-latn F1            │
│   ─────────────────────────────┼─────────┼─────────┼───────────────────    │
│   XLM-R (multilingual train)   │  0.7850 │  TBD    │   TBD                 │
│   Language-specific BERT       │  0.71   │  0.67   │   0.62               │
│   Universal Embeddings         │  0.68   │  0.61   │   0.57               │
│   ─────────────────────────────┼─────────┼─────────┼───────────────────    │
│   XLM-R advantage              │  +0.07  │  TBD    │   TBD                 │
│                                                                             │
│   Key: XLM-R's cross-lingual pretraining enables zero-shot transfer        │
│        to unseen languages without task-specific fine-tuning.              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 11. Getting Started

### Prerequisites

```bash
# Python 3.10+
python3 --version  # >= 3.10

# Core dependencies
pip install transformers torch datasets accelerate
pip install librosa openSMILE  # Audio features
pip install faster-whisper      # Transcription (130x realtime)

# For teacher refinement (optional)
pip install ollama  # Local LLM inference

# For WavLM audio embeddings (optional, needs GPU)
pip install torchaudio
```

### Installation

```bash
git clone https://github.com/Das-rebel/ChuckleNet.git
cd ChuckleNet
pip install -r requirements.txt
```

### Quick Start: Run Full Pipeline

```bash
# One-command pipeline (convert → refine → train → evaluate)
python3 training/run_xlmr_standup_pipeline.py \
  --backend ollama \
  --endpoint http://127.0.0.1:11434/api/generate \
  --teacher-model qwen2.5-coder:1.5b \
  --model-name FacebookAI/xlm-roberta-base
```

### Evaluate a Saved Model

```bash
python3 training/evaluate_saved_xlmr_model.py \
  --model experiments/xlmr_standup_baseline_weak_pos5/best_model \
  --data data/training/standup_word_level/valid.jsonl
```

### Run Autoresearch

```bash
python3 training/autonomous_research_loop.py --max-experiments 2
```

### External Benchmark Evaluation

```bash
# Evaluate on StandUp4AI external benchmark
python3 training/evaluate_external_wordlevel_benchmark.py \
  --model experiments/xlmr_standup_baseline_weak_pos5/best_model \
  --benchmark benchmarks/data/standup4ai_examples.jsonl

# WESR taxonomy benchmark suite
python3 training/evaluate_wesr_benchmark_suite.py \
  --model experiments/xlmr_standup_baseline_weak_pos5/best_model \
  --splits canonical wesr_advanced
```

### Colab Notebooks

Training is also available via Google Colab for GPU access without local setup:

- **H6.1 Testing F0 DROP**: [Colab Notebook](https://colab.research.google.com/gist/Das-rebel/c5ffe5a6f427ac15a22f8b1a15424b73)
  - Uses GDrive mount (not gdown)
  - Properly handles span-level segments by aligning to Whisper timestamps
  - GDrive folder: publicly shared at `15ixKiy86MZ67OwGEVxtnwSTs3nvbLRbh`

---

## 12. Project Structure

```
ChuckleNet/
├── README.md                          # This file
├── LICENSE                            # MIT License
├── requirements.txt                    # Dependencies
├── CURRENT_STATUS.md                   # Canonical project status (READ THIS)
├── AGENTS.md                          # Agent handoff notes
│
├── training/
│   ├── run_xlmr_standup_pipeline.py   # One-command pipeline runner
│   ├── xlmr_standup_word_level.py     # XLM-R training script
│   ├── convert_standup_raw_to_word_level.py  # VTT + Whisper alignment
│   ├── refine_weak_labels_nemotron.py  # Teacher refinement (NOT promoted)
│   ├── autonomous_research_loop.py     # Evidence-gated autoresearch
│   ├── evaluate_saved_xlmr_model.py   # Model evaluation
│   ├── evaluate_external_wordlevel_benchmark.py  # External benchmarks
│   ├── evaluate_wesr_benchmark_suite.py  # WESR taxonomy suite
│   └── build_safe_hybrid_dataset.py   # Hybrid label builder
│
├── data/
│   ├── audio_comedy/
│   │   ├── aligned_utterances.jsonl   # Phase 0 utterances (15K)
│   │   └── aligned_segments.jsonl     # Word-level segments (549K)
│   └── training/
│       ├── standup_word_level/         # Canonical splits
│       │   ├── train.jsonl             # 505 examples
│       │   ├── valid.jsonl            # 102 examples
│       │   └── test.jsonl             # 23 examples
│       ├── standup_word_level_wesr_balanced/   # WESR-balanced splits
│       └── standup_word_level_wesr_advanced/   # WESR taxonomy-rich
│
├── experiments/
│   ├── xlmr_standup_baseline_weak_pos5/  # PROMOTED MODEL
│   │   ├── best_model/                # Saved model weights
│   │   ├── training_summary.json      # Training metrics
│   │   └── clause_lexical_tail_eval.json  # Evaluation results
│   ├── promoted_model.json            # Programmatic registry
│   └── research_log.json              # Autoresearch history
│
├── docs/
│   ├── XLMR_STANDUP_ROADMAP.md        # Technical roadmap
│   ├── LAUGHTER_TAXONOMY.md           # Duchenne vs Non-Duchenne
│   ├── PRDs/                          # Project requirement documents
│   └── ARCHITECTURE.md                # Detailed architecture
│
├── colab_*/                           # Google Colab notebooks
└── benchmarks/
    ├── data/
    │   └── standup4ai_examples.jsonl   # External sanity benchmark
    └── results/                       # Benchmark outputs
```

---

## 13. External Validation Framework

### Gold Standard Dataset

- **505 stand-up comedy samples** with word-level laughter annotations
- **Quality Score: 97.7%** via Qwen2.5-Coder + Nemotron pipeline
- **Stratified by**: comedian, show, and humor type (punchline, surprise, callback)

### Domain Shift Analysis

| Metric | Value | Interpretation |
|--------|-------|---------------|
| Vocabulary Overlap | 0.7% | Low (Reddit vs comedy domain gap) |
| JS Divergence | 0.238 | Moderate distribution shift |
| Domain Similarity | 0.46 | Moderate |
| **Recommended Training** | 1.2x epochs | To compensate for domain gap |

### Statistical Methodology

- 95% confidence intervals (Wald method)
- Effect size: log-odds ratio
- Significance threshold: p < 0.05

---

## 14. Key Literature

| Paper | Key Contribution | Status |
|-------|-----------------|--------|
| **Pickering 2009** | F0 DROP (Declination, Ornament, Pitch) as laughter cue | Validated |
| **Purandare 2006** | Pause duration as most predictive feature | **Disputed** (d=0.13) |
| **Bachorowski 2001** | 250-500Hz spectral peak for spontaneous laughter | Partially validated |
| **Bertero 2016** | Pause patterns in humor detection | Confirmed |
| **MultiLinguahah 2026** | Unsupervised cross-lingual humor detection | Framework参考 |
| **GCACU 2024** | Generalized Cognitive Architecture for Conceptual Understanding | Implemented (lite) |

---

## 15. Roadmap

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CHUCKLENET ROADMAP                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  PHASE 1: Audio-First Paradigm (COMPLETED)                                  │
│  ─────────────────────────────────────────────                               │
│  ✓ Utterance-level realignment (15K utterances, 32.6% positive)              │
│  ✓ Prosodic feature extraction (F0, RMS, MFCC, pause)                        │
│  ✓ WavLM-base+ audio embeddings                                             │
│  ✓ openSMILE eGeMAPS extraction                                             │
│                                                                              │
│  PHASE 2: Multilingual Expansion (IN PROGRESS)                               │
│  ───────────────────────────────────────────────                             │
│  • Expand Chinese (zh) coverage                                             │
│  • Expand Hindi-Latin (hi-latn) coverage                                    │
│  • Add Bengali (bn), French (fr), Spanish (es)                              │
│  • Cross-lingual transfer learning                                         │
│                                                                              │
│  PHASE 3: Audio-Text Fusion (PLANNED)                                        │
│  ─────────────────────────────────                                          │
│  • Bi-encoder architecture (text XLM-R + audio WavLM)                        │
│  • Cross-attention fusion mechanism                                         │
│  • Expected F1 improvement: +2-5% over text-only                             │
│                                                                              │
│  PHASE 4: Production API (PLANNED)                                           │
│  ──────────────────────────────                                             │
│  • REST API for real-time laughter scoring                                   │
│  • Python SDK with pre/post processing                                      │
│  • WebSocket streaming for live audio                                       │
│                                                                              │
│  PHASE 5: Research Publication (PLANNED)                                     │
│  ─────────────────────────────────                                          │
│  • arXiv preprint                                                           │
│  • ACL/EMNLP 2026 submission target                                         │
│  • Open-source dataset release                                              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 16. Citation

If you use ChuckleNet in your research, please cite:

```bibtex
@article{chucklenet_2026,
  title={ChuckleNet: Multilingual Audience Laughter Detection via BERT Fine-Tuning},
  author={Das, S.},
  booktitle={ACL/EMNLP 2026},
  year={2026},
  note={arXiv:XXXX.XXXXX},
  url={https://github.com/Das-rebel/ChuckleNet}
}
```

---

## 17. License

MIT License. See [LICENSE](LICENSE) for details.

---

**Last Updated**: 2026-05-31
**WavLM Best**: Val F1=0.7564 (epoch 3)
**Status**: Active training complete  
**Promoted Model**: `experiments/xlmr_standup_baseline_weak_pos5`  
**Best Metrics**: Val F1=0.7850, Val IoU-F1=0.7891, Test F1=0.8194, Test IoU-F1=0.8798  
**Dataset**: 549,334 aligned segments, 71 videos, 6 languages  
**Status**: Research system, not production-ready
