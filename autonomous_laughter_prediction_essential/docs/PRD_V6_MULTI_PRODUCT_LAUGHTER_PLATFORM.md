# ChuckleNet PRD v6.0: Multi-Product Laughter & Sarcasm Platform

**Date:** 2026-06-04  
**Status:** ACTIVE DEVELOPMENT — REVISED ARCHITECTURE  
**Supersedes:** PRD_UNIFIED_AUDIO_TEXT_MODEL.md, SOTA_PRD_RL_LAUGHTER_PREDICTION.md, PRD_V4_10M_PIPELINE.md  
**Repository:** github.com/Das-rebel/ChuckleNet

---

## Problem Statement

### Current SOTA

| Task | SOTA | Method |
|------|------|--------|
| Humor detection (text) | 74-78% F1 | BERT + contextual |
| Sarcasm detection | 72-80% F1 | Multi-modal (text + prosody) |
| Acoustic laughter detection | 85-90% F1 | Wav2Vec2 fine-tuned |
| Audience laughter prediction | ~65% F1 (ours) | Text + prosody fusion |

**Gap:** No published work on word-level AUDIENCE LAUGHTER DISCOURSE POSITIONING — predicting where in a transcript audiences will laugh. This is a different task from acoustic laughter detection (is there laughter?) or document-level humor classification (is this funny?).

### Our Current Results

| Model | Metric | Value | Notes |
|-------|--------|-------|-------|
| XLM-R text-only | Val F1 | 0.785 | Best overall |
| XLM-R text-only | Test F1 | 0.819 | |
| XLM-R text-only | IoU-F1 | 0.50 | **Bottleneck** |
| Phase A (frozen WavLM) | Val F1 | 0.756 | Best audio-only |
| Phase A (frozen WavLM) | Test F1 | 0.617 | Distribution shift |
| Track B LateFusion | Test F1 | 0.502 | Prosody helps (+5.3%) |
| Phase D (partial unfreeze) | Val F1 | 0.40 | **FAILED** — catastrophic overfitting |

### Critical Discovery

**Labels are NOT acoustic laughter events — they are AUDIENCE REACTION POSITIONS.**

Analysis of word-level labels:
```
Top labeled tokens: 'the', 'a', 'i', 'to', 'and', '.', '!', '"'
Zero laughter-lexical tokens (haha, lol, hehe, lmao)
Labels land on: function words + punctuation AFTER punchlines
```

**This reframes the task:** Text models should handle "is there a laugh cue?" (region detection). Prosody should handle "where exactly does it land?" (boundary refinement).

---

## Products

### Product 1: Group Laughter Predictor ⭐ PRIMARY FOCUS

**What:** Predict which word-positions in a transcript will be followed by audience laughter.

**Core metric:** IoU-F1 (boundary precision, not just detection)

**Commercial uses:**
- Comedian script debugging ("this punchline won't land — pause too short")
- Content resonance scoring (headlines, captions, standup clips)
- Video editing (cut to reaction shot at precise moment)
- Marketing A/B testing of comedic content

**Research contribution:** First word-level audience laughter prediction dataset + cascade architecture.

---

### Product 2: Individual Laughter + Sarcasm Detector

**What:** Detect if a specific person is laughing or being sarcastic.

**Requires:** Speaker diarization + per-person acoustic analysis. **VTT crowd labels CANNOT be used for this product.**

**Commercial uses:**
- Mental health (laugh quality as depression indicator — requires HIPAA)
- Customer service (sarcasm in calls)
- Accessibility (helping autistic individuals read social cues)

---

### Product 3: Sarcasm-Aware Content Scorer

**What:** Score content for sarcasm potential and delivery clarity.

**Signal:** Prosodic features (F0, pause, energy) + semantic incongruity.

---

## Architecture

### Product 1: Cascade Architecture (REVISED)

```
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 1: Text Region Proposal (XLM-R base fine-tuned)         │
│                                                                 │
│  Input: word sequence + punctuation markers (<turn>, <pause>)  │
│  Task: predict which SPANS contain a laugh reaction            │
│  Output: coarse laugh regions (span-level, not token-level)     │
│  Metric: Span-level F1 (not IoU-F1)                             │
│                                                                 │
│  Why separate: Labels mark discourse positions — text captures  │
│  setup/punchline structure, not acoustic events. A single token  │
│  classification head trying to do region+boundary simultaneously│
│  causes the IoU-F1 ceiling at 0.50.                             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                  (crop audio to Stage 1 regions)
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 2: Prosody Boundary Refinement                           │
│                                                                 │
│  Input: Audio frames within Stage 1 proposed regions            │
│  Features:                                                      │
│    - Pause duration (before/after words) ← MOST VALIDATED       │
│    - F0 contour (mean, range, slope, voiced_ratio)             │
│    - RMS energy (mean, max, slope)                              │
│    - MFCCs 1-13                                                  │
│    - Spectral: centroid, bandwidth, rolloff                      │
│                                                                 │
│  Model: WavLM frozen + attention pooling → MLP                  │
│  Task: refine start/end boundaries within Stage 1 regions         │
│  Output: precise word-level boundaries                           │
│  Metric: IoU-F1 (this is where it matters)                       │
└─────────────────────────────────────────────────────────────────┘
```

**Key decisions (validated by ablation):**
- ✅ WavLM FULLY FROZEN — partial unfreeze causes catastrophic overfitting
- ✅ Attention pooling — CSA (Compressed Sparse Attention) HURT in ablation
- ✅ No Engram bottleneck — compression HURT in ablation
- ✅ Simple concatenation + MLP — complex gating HURTS
- ✅ Class weighting MANDATORY — balanced weights cause complete collapse

---

### Product 2: Individual Laughter Architecture

```
INPUT: Audio + Video
    ↓
Speaker Diarization (pyannote or whisper-diarization)
    ↓
Per-speaker track:
├── F0 statistics (mean, range, slope, voiced_ratio)
├── Pause duration (before/after speech)
├── RMS energy (mean, max)
├── MFCCs 1-13
├── Spectral features (centroid, bandwidth, rolloff)
├── Laryngeal features (jitter, shimmer)
    ↓
Classifier: does THIS person find it funny?
├── Per-person binary laugh detection
├── Intensity score (0-1)
└── Laugh type: duchenne/genuine vs fake/social
```

**Data needed:** Individual-level annotations with diarization. VTT crowd labels are NOT suitable.

---

## Research Hypotheses

### Product 1 Hypotheses (Active)

| H# | Hypothesis | Method | Expected | Status |
|----|-----------|--------|----------|--------|
| **H0** | Labels = discourse positions | Analyze label distribution | Task reframed | ✅ VERIFIED |
| **H1** | Cascade > joint prediction | Compare cascade vs simultaneous | +5-10% IoU-F1 | 🆕 NEW |
| **H2** | Pause is #1 acoustic feature | Extract pause (0.8s threshold) | Validate Purandare 2006 | 📋 TODO |
| **H3** | F0 DROP predicts boundary | Extract F0 contours | Boundary refinement signal | 📋 TODO |
| **H4** | Cross-lingual discourse transfer | Train en, test zh/hi | Discourse structure transfers | 📋 TODO |

### Product 2 Hypotheses (Future)

| H# | Hypothesis | Method | Expected |
|----|-----------|--------|----------|
| H6 | Individual laughter ≠ group | Diarization + per-person | Different model |
| H7 | Sarcasm = prosodic + incongruity | Multi-task learning | Shared representations |

---

## Data Inventory

### Product 1: What We Have

| Dataset | Path | Size | Notes |
|---------|------|------|-------|
| aligned_utterances.jsonl | gdrive | 15,000 utterances | **PRIMARY** — has video_id/start for prosody join |
| aligned_segments.jsonl | gdrive | 389K-549K segments | Word-level, 71 videos |
| prosody_phaseD.json | gdrive | 14,998 entries, 21-dim | 6 dims active (F13-F18) |
| combined/ | data/ | 12,200 examples, 33% positive | For ablation |
| merged_final/ | data/ | 19,109 examples | Has synthetic features (LEAKAGE — cannot use) |
| wavlm_embeddings/ | experiments/ | 768-dim per video | Per-video WavLM features |

### Product 1: What We Need

1. **Pause feature extraction** — highest validated acoustic feature, barely used
2. **F0 contour extraction** — for boundary refinement
3. **Word-level prosody alignment** — ensure video_id + start match prosody cache
4. **Cross-lingual validation** — en→zh→hi discourse transfer

### Product 2: What We Need

1. **Individual-level annotations** — VTT labels are crowd, not individual
2. **Speaker diarization** — pyannote or whisper-diarization
3. **Isolated laughter samples** — for acoustic validation
4. **Sarcasm datasets** — Sar sarcasm, MUGEAR for pre-training

---

## Evaluation

### Product 1: Metrics

| Stage | Metric | Current | Target |
|-------|--------|---------|--------|
| Stage 1 (Region Detection) | Span F1 | — | 0.75+ |
| Stage 2 (Boundary Refinement) | IoU-F1 | 0.50 | 0.65+ |
| End-to-end | Token F1 | 0.50 | 0.70+ |
| Held-out generalization | Test F1 | 0.82 (text) / 0.50 (late fusion) | Hold across comedians |

**Evaluation split:** Bill Burr, Dave Chappelle, Russell Peters = held-out test (zero shot).

### Product 2: Metrics

| Metric | Target |
|--------|--------|
| Per-person laughter detection | 0.80+ |
| Sarcasm detection | 0.75+ |

---

## What Failed and Why

| Attempt | Result | Lesson |
|---------|--------|--------|
| Phase D: partial unfreeze + CSA + Engram | Val F1=0.40, catastrophic | Never partial unfreeze at standard LR (5e-5) |
| Phase D: class_weight [1,4] | Val P dropped 0.30→0.19 | Start at [1, 2.5] max |
| Phase D: audio from Drive every batch | Colab hang | Always cache audio to RAM |
| Phase D: padding=True in WavLM | key_padding_mask mismatch | Use padding=False |
| CSA attention | Ablation HURT | Simple pooling > CSA |
| Engram bottleneck | Ablation HURT | No compression needed |
| prosody_dim [1-12] and [19-20] | All zeros | These are padding/unused |
| Balanced class weights | Complete collapse | Never use balanced for this task |

---

## Training Configuration

### Phase A + Prosody (Next Colab Run)

```python
# Architecture
wavlm = WavLMModel.from_pretrained('microsoft/wavlm-base-plus')
wavlm.eval()  # FROZEN
for p in wavlm.parameters():
    p.requires_grad = False

# Audio: attention pooling over WavLM frames
audio_pool = AttentionPooling(768)  # learns per-frame importance

# Prosody: 21-dim → 32-dim projection
prosody_proj = nn.Sequential(
    nn.Linear(21, 64), nn.GELU(), nn.Dropout(0.1), nn.Linear(64, 32)
)

# Fusion: concatenate audio_emb (768) + prosody_emb (32) = 800-dim
classifier = nn.Sequential(
    nn.Dropout(0.3), nn.Linear(800, 128), nn.GELU(),
    nn.Dropout(0.2), nn.Linear(128, 64), nn.GELU(), nn.Linear(64, 2)
)

# Training
optimizer = torch.optim.AdamW(classifier_params, lr=1e-3, weight_decay=0.01)
scheduler = CosineAnnealingLR(optimizer, T_max=10, eta_min=1e-5)
pos_weight = n_neg / n_pos  # ~2.83 for this dataset
criterion = nn.CrossEntropyLoss(weight=[1.0, min(pos_weight, 4.0)])
```

---

## Next Steps (Priority Order)

### Immediate (This Week)

1. **Track B (parallel)**: Run `ChuckleNet_PhaseA_Prosody_Fusion.ipynb` on Colab
   - Validates whether prosody actually helps WavLM
   - Gets real number vs MiniLM baseline (Test F1=0.50)

2. **Track C (FOUNDATION FIRST — user priority)**: Run `training/audit_boundary_errors.py`
   - Audits 100 true positives: label position vs actual audio laugh onset
   - If avg offset <500ms → cascade (Track A) is right path
   - If avg offset >1000ms → label noise is bottleneck, Track C fix is essential
   - Also extracts pause features (most validated acoustic feature)

3. **Track C (continued)**: Run `training/track_c_pause_features.py`
   - Extract pause_before_s, pause_after_s (Purandare 2006: 0.8s threshold)
   - Fix video_id + start alignment for prosody joining
   - Output: 27-dim prosody (21 existing + 6 new features)

### Short-term (2-4 weeks)

4. **Track A ONLY AFTER Track C audit confirms boundaries are clean**
   - Stage 1: XLM-R text → predict coarse LAUGH_REGIONS (span-level)
   - Stage 2: Prosody (pause/F0/energy) → refine boundaries
   - Expected: Break IoU-F1 0.50 ceiling, +5-10% improvement

## Agent Council Decision (2026-06-04)

**Council:** claude-minimax + general-purpose agents

### Decision Summary

| Question | Decision |
|----------|----------|
| Use extracted pause (1.9%)? | ❌ NO — broken, skip |
| Use original prosody (17.1%)? | ⚠️ Defer — text-only cascade first |
| Build Track A cascade? | ✅ YES — text-only XLM-R → regions |
| Run Track B (Colab)? | ⏳ AFTER Track A validates |

### Rationale

1. **Extracted pause (1.9%) = silent failure** — 8.9× lower than original (17.1%). Don't add broken prosody risk to strong text signal.

2. **XLM-R text-only at F1=0.819 is already strong** — text signal is robust (62% labels within 500ms of audio). Don't dilute it.

3. **Cascade Stage 1 text-only gives clean baseline** — compare against this before adding prosody.

4. **Track B runs AFTER cascade validates** — only if IoU-F1 gap remains that prosody can close.

### Execution Plan

```
Stage 1 (NOW): XLM-R → coarse LAUGH_REGIONS (text only)
│   → Validates cascade helps IoU-F1
│   → Establishes text-only baseline
│
↓ If IoU-F1 improves above 0.50
Stage 2: prosody boundary refinement (original pause_before 17.1%)
│   → Only if Stage 1 shows meaningful boundary gap
│
↓ If cascade works
Track B (Colab): WavLM + prosody layered on top
```

---

## Execution Plan (Revised)

### Phase 1.1: Track A Stage 1 — Text Cascade (PRIORITY)
**Architecture:** XLM-R base → word-level classification → span-level regions

**Why:** Establish cascade baseline with text only. Compare against current XLM-R Test F1=0.819, IoU-F1=0.50.

**Tasks:**
- [ ] Build dataset: text tokens + word timestamps + labels → span-level format
- [ ] Train XLM-R for span prediction (not token classification)
- [ ] Evaluate: Span F1 on held-out test (Burr, Chappelle, Peters)
- [ ] Compare: cascade vs current token-classification approach

**Expected outcome:** Break IoU-F1 0.50 ceiling using two-stage text approach.

### Phase 1.2: Track A Stage 2 — Prosody Boundary Refinement
**Add prosody (original pause_before at 17.1%) only if Stage 1 shows boundary gap.**

### Phase 1.3: Track B (Colab) — Post-Cascade Validation
**Only run Track B AFTER cascade validates.** If cascade text-only already breaks 0.50, Track B becomes optional enhancement. If cascade doesn't break 0.50, Track B is the alternative path (WavLM + prosody fusion).

---

### Track C Results (Completed 2026-06-04)

**Output:** `data/prosody_aligned/` with:
- `prosody_features_enhanced_50videos.csv` — 23-dim prosody (21 original + extracted pause)
- `train_with_pause.npz` — 10,207 samples, 384-dim text + 23-dim prosody
- `valid_with_pause.npz` — 1,993 samples
- `test_with_pause.npz` — 2,799 samples

**⚠️ Issue:** Extracted pause features have 1.9% non-zero coverage vs original `pause_before` at 17.1%. **Extracted pause is BROKEN — do not use.** Use original prosody CSV for any prosody features.

### Short-term (2-4 weeks)

4. **Run Stage 2 prosody-only baseline** — establish boundary refinement IoU-F1
5. **Full cascade evaluation** — compare cascade vs joint vs late fusion
6. **Cross-lingual validation** — en→zh→hi transfer

### Medium-term (1-2 months)

7. **Individual laughter data collection** — new dataset for Product 2
8. **Speaker diarization integration** — pyannote or whisper-diarization
9. **Sarcasm detection baseline** — Sar dataset baseline

---

## Open Questions

1. **Is cascade actually better than late fusion?** — needs validation (H1)
2. **Which prosody features matter most for boundary?** — pause vs F0 vs energy (H2, H3)
3. **Can discourse structure transfer across languages?** — en→zh→hi (H4)
4. **What's minimum viable dataset for individual laughter?** — per-person data needs
5. **Is Product 2 commercially viable without clinical partnership?** — mental health angle requires HIPAA
6. **Can we use synthetic laughter labels from LLM?** — teacher refinement failed (0% detected), needs fix

---

## References

| Paper | Contribution | Relevance |
|-------|-------------|----------|
| Pickering 2009 | F0 DROP at punchline | H3 |
| Purandare 2006 | Pause 0.8s threshold before laughter | H2 — most validated acoustic feature |
| Bachorowski 2001 | Laughter 250-500Hz spectral peak | Product 2 |
| Bertero 2016 | Pause as #1 feature for humor detection | H2 validation |
| Wosu 2023 | MultiLinguahah: unsupervised cross-lingual | H4 |
| Castro 2023 | BYOL-A for self-supervised laughter | Product 2 |
| Gillick 2019 | Wav2Vec2 + CNN for laughter detection | Audio baseline |