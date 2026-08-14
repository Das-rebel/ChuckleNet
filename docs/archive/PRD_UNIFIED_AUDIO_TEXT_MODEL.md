# PRD: Unified Audio-Text Laughter Prediction
## "What the Words Don't Say, the Audio Does"

**Date:** 2026-05-23
**Status:** Proposed
**Priority:** Q1-Q2 Critical Path

---

## 1. Problem Statement

**Current state:** XLM-R text-only achieves F1=0.819. This captures semantic incongruity (wordplay, setup-punchline structures). But human comedians use TWO channels:

1. **What they say** → captured by text/XLM-R
2. **How they say it** → prosodic emphasis, timing, audience response timing

**The gap:** Text misses non-verbal signals humans use to detect humor. These signals are audible but don't appear in transcripts:

| Audio Signal | Text Misses | Why It Matters |
|-------------|-------------|----------------|
| Prosodic emphasis | "HE said they'd never" vs "he said THEY'D never" | Same words, different meaning |
| Laughter timing | Audience laughs 1.2s after punchline | Response lag encodes what's funny |
| Hesitation markers | False starts, self-correction | Signals incongruity detection |
| Vocal fry/creak | Uncertainty markers | Signals satirical intent |
| Energy spikes | Volume contrast | Marks punchline delivery |
| Pause BEFORE punchline | Silence before delivery | Purandare 2006: 0.8s pause |
| Cultural pragmatics | "That's so..." (ironic) | Tone signals sincerity vs satire |

**Hypothesis:** A unified model that learns to weight text semantics + audio prosody will outperform text-only because audio captures what text transcription misses.

---

## 2. Proposed Solution

### Core Architecture: Late-Gated Fusion

```
TEXT BRANCH                          AUDIO BRANCH
┌─────────────────────┐              ┌──────────────────────┐
│ XLM-R (frozen/joint) │              │ WavLM-Base+ (per-utt) │
│ [CLS] = 768-dim     │              │ Mean-pool = 768-dim  │
└─────────┬───────────┘              └──────────┬───────────┘
          │                                       │
    text_proj (768→256)                    audio_proj (768→256)
          │                                       │
          ▼                                       ▼
    text_emb [256]                            audio_emb [256]
          │                                       │
          └───────────┬───────────────────────────┘
                      │
              ┌───────▼────────┐
              │  GATE MODULE   │
              │  g = σ(W·[t;a])│
              │  [t·(1-g)] +   │
              │  [a·g]         │
              └───────┬────────┘
                      │
              ┌───────▼────────┐
              │  Classifier    │
              │  256→128→2    │
              └───────────────┘
```

**Key insight:** Gate learns WHEN to trust audio vs text. For wordplay → trust text. For physical comedy timing → trust audio.

### Why Late Fusion with Gating

| Fusion Type | Pro | Con |
|-------------|-----|-----|
| **Gated late fusion** (this) | Learns modality selection, prevents audio from drowning | Gate may collapse to one modality |
| Early concatenation | Simple | Overfits with 15K samples |
| Cross-attention | Captures interactions | Too complex, needs more data |
| Ensemble (text + audio separate) | Stable | Doesn't learn cross-modal interactions |

### Audio Branch: Utterance-Level (Not Word-Level)

**Critical fix from prior attempts:** Previous audio failures were word-level (0.3s clips). Laughter is a SUPRA-SEGMENTAL phenomenon — it spans 3-15 seconds.

| Level | Duration | Problem |
|-------|----------|---------|
| **Word-level (old)** | 0.3s | F0/energy averages out over 300ms. No prosody to detect. F1=0.27. |
| **Utterance-level (this)** | 3-15s | Prosodic patterns emerge at utterance level. Gillick 2019: F1=0.89. |

**Utterance definition:** All words from one speaker turn before audience response or long pause (>2s).

---

## 3. Research Hypotheses

### Primary (Must Test)

| H# | Hypothesis | Method | Expected |
|----|-----------|--------|----------|
| **H8.1** | Text + prosody fusion achieves F1 > 0.85 | XLM-R + WavLM gated, utterance-level | +3-6% over text-only |
| **H6.2** | RMS energy spikes precede punchlines (separate from F0) | librosa RMS extraction + LR | Energy may add signal F0 misses |
| **H6.3** | F0 + energy + pause combined improves cross-lingual ZH/HI | Per-language F1 comparison | Bridge 7-14% EN→HI gap |
| **H14.4** | Span detection (IoU-F1) improves with audio | Compare span IoU-F1 with/without audio | Audio timing helps span boundaries |

### Secondary (If Primary Succeeds)

| H# | Hypothesis | Method | Expected |
|----|-----------|--------|----------|
| H13.1 | BYOL-A encoder > WavLM for cross-lingual audio | MultiLinguahah pipeline | BYOL-A may transfer better EN→ZH→HI |
| H13.4 | EN→ZH→HI cross-lingual transfer with audio | Fine-tune ZH, evaluate HI | Audio universals help transfer |
| H8.4 | Cross-lingual fusion bridges EN→HI gap | Compare text-only vs text+audio | Audio adds robustness |

### Diagnostic (For Understanding)

| H# | Hypothesis | Method |
|----|-----------|--------|
| H8.2 | Gate learns interpretable modality selection | Inspect gate values on physical comedy vs wordplay videos |
| H8.3 | Cross-modal attention learns text-prosody alignment | Attention visualization |

---

## 4. What Audio Captures That Text Misses

### 4.1 Prosodic Emphasis (F0 + Energy)

ASR transcripts: "he said they'd never get it done"
Reality: Emphasis on "THEY'D" signals ironic setup for punchline.

**Detection:** F0 contour peak at "THEY'D" word. Energy spike.

### 4.2 Laughter Timing (Audience Response)

Audience laughs 0.8-1.5s AFTER punchline delivery. Words within that window are labeled as "laugh" even if they're just setup for the NEXT punchline.

**Detection:** Audio energy spike (audience laughing), separate from speaker audio. Onset timing.

### 4.3 Hesitation Markers

False starts: "I was gonna, um, I mean I WAS gonna..."
Self-correction: "It's not that I don't like, well, I GUESS I don't like..."

These signal the speaker is navigating incongruity — either setup or punchline delivery.

**Detection:** Word duration anomalies, pause patterns.

### 4.4 Cultural Pragmatics

"Statement ... that's so ..." (sarcastic in US, genuine in India)
Same words, different prosody = different meaning.

**Detection:** F0 contour shape, speech rate, pause after statement.

### 4.5 The Comedic Pause

Purandare 2006: 0.8s pause BEFORE punchline (vs 0.3s average). This is THE single most validated acoustic feature of humor.

**NOT detectable from text.** Whisper transcripts don't encode pause duration between words.

**Detection:** librosa speech/silence segmentation on raw audio, aligned to word timestamps.

---

## 5. Technical Approach

### 5.1 Audio Feature Extraction (WavLM)

```
For each utterance (3-15s audio clip):
  1. Load audio at 16kHz
  2. WavLM-Base+ forward pass → (T, 768) hidden states
  3. Mean pool over time → (768,) embedding
  4. Project 768→256 → audio_emb
```

**Why WavLM-Base+:**
- Denoising pretraining (helps with audience noise)
- +4.7% on emotion benchmarks over Wav2Vec2
- 768-dim (same as XLM-R)
- Per-sample extraction (no position overflow)

**Pre-extraction:** All WavLM embeddings saved to disk (~4.6GB). Training loads from disk, not computed on-the-fly.

### 5.2 Text Feature Extraction (XLM-R)

```
For each utterance (tokenized words):
  1. XLM-R forward pass → (L, 768) hidden states
  2. Mean pool over tokens → (768,) embedding
  3. Project 768→256 → text_emb
```

**Frozen vs Fine-tuned:** Phase 1 frozen (text baseline). Phase 3 joint fine-tune.

### 5.3 Gating Mechanism

```
gate_input = concat([text_emb, audio_emb])  # (512,)
gate_logit = Wg @ gate_input + bg          # (1,)
g = sigmoid(gate_logit)                    # scalar in [0,1]

fused = g * audio_emb + (1-g) * text_emb
```

**Gate initialization fix (from prior collapse):**
```python
with torch.no_grad():
    gate.bias.fill_(-2.2)  # Initial: g≈0.10, 90% text-leaning
```

This prevents gate from collapsing to text-only (g=0) before audio learns.

### 5.4 Training Phases

| Phase | What | Epochs | LR (text/audio/gate) | Checkpoint |
|-------|------|--------|---------------------|------------|
| 1 | Text-only baseline | 5 | 5e-5 / frozen / frozen | Validate text F1 ≈ 0.75 |
| 2 | Frozen text + train audio+gate | 10 | frozen / 1e-3 / 1e-3 | Audio learns complement |
| 3 | Joint fine-tune (top-2 XLM-R layers) | 5 | 2e-5 / 5e-4 / 5e-4 | **Target F1 > 0.85** |

### 5.5 Dataset

**Utterance-level dataset:** 15,060 utterances from 71 videos
- Mean utterance length: ~8s
- Positive rate: 32.6%
- Languages: en (70%), zh (25%), hi-latn (5%)

**Split:** Per-video GroupKFold (5-fold), no comedian leakage.

---

## 6. Failure Modes and Mitigations

| Failure | Detection | Mitigation |
|---------|-----------|------------|
| Gate collapses to text-only (g→0) | Monitor g values; if mean g < 0.05 | Increase gate bias (more negative); add audio auxiliary loss |
| Gate collapses to audio-only (g→1) | If text F1 drops in Phase 3 | Decrease gate bias; freeze audio branch |
| Audio F1 < 0.50 in Phase 2 | Check val metrics per modality | Add prosody hand-features alongside WavLM |
| Overfitting (15K samples) | Track train/val gap | Increase dropout; reduce fusion params |
| Joint fine-tune destabilizes | Loss NaN | Use lower LR; warmup |

---

## 7. Success Metrics

| Stage | Metric | Target | Blocker |
|-------|--------|--------|---------|
| Phase 1 | Val F1 (text-only) | ≥ 0.75 | Stop if < 0.70 |
| Phase 2 | Val F1 (frozen text) | ≥ 0.77 | Audio not helping; stop |
| Phase 2 | Gate mean | 0.05 < g < 0.95 | Gate collapsed |
| **Phase 3** | **Val F1 (joint)** | **≥ 0.85** | **Success criterion** |
| Phase 3 | IoU-F1 | ≥ 0.88 | Span boundaries improve |

---

## 8. Comparison to Prior Art

| Paper | Approach | Audio F1 | Multimodal F1 |
|-------|----------|----------|---------------|
| UR-FUNNY (ACL 2020) | BERT + eGeMAPS | 63.1% | 77.2% |
| Hasnain et al. (LREC 2022) | BERT + IS13 | 62% | 73% |
| Zhao et al. (2024) | Wav2Vec2 + BERT | 66% | 78% |
| **This** | **XLM-R + WavLM** | **?** | **Target 85%** |

**Why we should beat prior art:**
1. XLM-R > BERT for multilingual (covers ZH, HI)
2. WavLM > eGeMAPS (learned representations vs hand-crafted)
3. Utterance-level > word-level (Gillick 2019: 89% vs lower)

---

## 9. Timeline

| Week | Deliverable |
|------|-------------|
| W1 | WavLM embeddings extracted + Phase 1 text baseline retraining |
| W2 | Phase 2 frozen fusion training |
| W3 | Phase 3 joint fine-tune |
| W4 | Evaluation: held-out comedian test, cross-lingual ZH/HI |
| W5 | If F1 < 0.85: Debug gate, try BYOL-A, add prosody features |
| W6 | PRD report: document what worked/what didn't |

---

## 10. Open Questions

1. **Is utterance-level the right granularity?** Maybe ±2 neighboring utterances as context helps.
2. **BYOL-A vs WavLM:** MultiLinguahah uses BYOL-A for cross-lingual. Should we switch?
3. **Gate architecture:** Should gate be more complex (2-layer MLP)? Simple linear might not capture interactions.
4. **Audio features from text:** Can we use forced alignment to get word-level prosody within utterances?
5. **What does gate actually learn?** Physical comedy vs wordplay split would validate the design.

---

## 11. Alternative Approaches (If This Fails)

**If gated fusion fails (gate collapses, no improvement):**

| Approach | Why |
|----------|-----|
| Ensemble: text F1 + audio F1 weighted average | Stable, no gate collapse risk |
| Early fusion: concat [text_emb; audio_emb] → MLP | Simpler, may work with regularization |
| Attention fusion: cross-attention between text and audio tokens | If gate can't learn, let attention discover interactions |
| Audio-only as auxiliary: Multi-task with audio branch predicting pause/F0 | Force audio to learn meaningful features |

---

## 12. This PRD vs Prior Fusion Attempts

| Aspect | Prior (Fusion v3) | This PRD |
|--------|-----------------|----------|
| Audio level | Word-level (0.3s) | Utterance-level (3-15s) |
| Gate bias | Not set | -2.2 (90% text-leaning init) |
| Phase 1 | Text + audio frozen | Text frozen baseline |
| WavLM | Frozen | Trainable (Phase 2-3) |
| prosody features | Not included | Optional add-on |
| Metric | val_f1 | IoU-F1 for spans |

**The single biggest fix:** Utterance-level audio instead of word-level. Prosody doesn't exist at 300ms — it emerges over 3-15 seconds.

---

## 13. Deliverables

1. `training/extract_wavlm_utterance.py` — WavLM per-utterance embedding extraction
2. `training/model_gated_fusion.py` — GatedMultimodalFusion model class
3. `training/dataset_utterance.py` — Utterance-level dataset (text + WavLM pairs)
4. `training/train_gated_fusion.py` — 3-phase training script
5. `experiments/holdout_comedians.txt` — Held-out eval set (Bill Burr, Dave Chappelle, Russell Peters)
6. `experiments/gated_fusion_v1/protocol.md` — Protocol-first research doc
7. `research-state.yaml` — Update with H8.1, H6.2, H6.3, H14.4 results
8. This PRD updated with actual results
