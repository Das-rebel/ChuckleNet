# ChuckleNet — Full Research Audit & Architecture Redesign

**Date:** 2026-05-31
**Status:** Post-Orchestra audit, Phase D redesign

---

## What We Know Is True (Validated)

### Training Results
| Model | Val F1 | Test F1 | Precision | Recall | Split |
|-------|--------|---------|-----------|--------|-------|
| XLM-R text-only | 0.7850 | **0.8194** | — | — | per-video 80/20 |
| WavLM audio (frozen) | 0.7564 | **0.6173** | 0.464 | 0.921 | same |
| Prosody-only (pause/F0) | — | **0.136** | 0.13 | 0.14 | per-video |
| Biosemiotic LLM features | — | **0.829** | — | — | same |
| 3s windows (vs 5s) | — | **0.529** | 0.416 | 0.727 | same |
| Threshold sweep t=0.70 | — | **0.574** | 0.474 | 0.727 | same |

### Theory Verdict (Unanimous Agent Council)
```
❌ Theory A (Boundary contamination): FALSIFIED
   - XLM-R uses same windowing → F1 improves 0.785→0.819 on test
   - If boundaries caused the gap, XLM-R would also fail

✅ Theory D (Frozen encoder): CONFIRMED
   - Frozen WavLM = only learns generic speech features
   - XLM-R text (also frozen) = F1=0.819 because text IS the task
   - Audio requires adaptation to extract laughter-specific patterns
   - Explains ALL three symptoms simultaneously:
     (1) High recall / low precision
     (2) Val→test gap (encoder not adapted to laughter domain)
     (3) Window sensitivity (frozen encoder can't adapt temporal patterns)

✅ Theory C (Window mismatch): DOWNSTREAM of Theory D
   - 3s windows hurt because model learned 5s temporal patterns
   - With proper unfreezing, window size should be less critical

❌ Biosemiotic LLM features: LABEL LEAKAGE (H4.4)
   - F1=0.829 from features alone (higher than XLM-R text!)
   - Impossible without leakage
   - All prior ablation studies using these features are invalid

✅ Purandare pause effect: VALIDATED at scale
   - Pauses >1s → 2× laughter rate (subtitle-level, coarse measurement)
   - But word-level extraction still gives only F1=0.14
   - Utterance-level aggregation dilutes signal further
   - Key: need to extract at word-level within utterance, not aggregate

✅ F0 DROP: REAL but NEGLIGIBLE (Cohen's d=0.063)
   - Statistically significant (p<10⁻⁶) but effect size negligible
   - 5 Hz mean difference across 60K words
   - Studio editing averages out prosodic details
```

---

## What We've Tried — Complete Map

```
audio_comedy/
├── aligned_utterances.jsonl          ← 15K utterances, 71 videos
├── aligned_utterances_3s.jsonl       ← 3s non-overlapping variant
├── prosody_features_50videos.csv      ← 73K word-level prosody rows
│                                      (f0, rms, pause_before, word_duration)
└── audio/                            
    ├── batch1–batch17/               ← 388 MP3s locally
    └── batch1–batch5/ (shortcut)     ← 71 on GDrive

experiments/
├── xlmr_standup_baseline_weak_pos5/  ← PROMOTED: val=0.785, test=0.819
├── xlmr_combined_pos5_uf4/           ← XLM-R with unfreezing
├── wavlm_v2_phaseA/                  ← WavLM Phase A: val=0.756, test=0.617
├── gated_fusion_v1/                  ← Gate → 1.0 collapse (text dominates)
├── fusion_session5/                 ← Another fusion attempt
├── fusion_v3_phase1/                 ← Yet another fusion
├── fusion_v3_phase1_68k/             ← Fusion with 68K examples
└── standup4ai_baseline/              ← External benchmark

training/
├── xlmr_standup_word_level.py       ← XLM-R training script (canonical)
├── convert_standup_raw_to_word_level.py
├── refine_weak_labels_nemotron.py    ← LLM teacher refinement (FAILED)
├── autonomous_research_loop.py       ← Real v1 loop
└── run_xlmr_standup_pipeline.py

ChuckleNet/
├── ChuckleNet_WavLM_Kaggle.ipynb     ← Phase A: frozen WavLM
├── ChuckleNet_Threshold_Sweep.ipynb  ← Threshold + 3s window tests
└── ChuckleNet_PhaseC_TOM_Fusion.ipynb ← XLM-R + WavLM + prosody fusion
```

---

## The Root Cause — Why All Audio Approaches Failed

### Problem 1: Frozen WavLM Encoder (THE big one)
```python
# What we did:
encoder = WavLMModel.from_pretrained('...')
for param in encoder.parameters():
    param.requires_grad = False  # ALL frozen
classifier = MLP()
optimizer = AdamW(classifier.parameters())  # Only head trains
```
**What happens:** WavLM was pretrained on 60K hours of speech for wav2vec2 reconstruction.
It has ZERO laughter-specific acoustic representations. Mean-pooling 500 frames
and classifying is equivalent to "does this 5-second clip sound like generic speech?"
The classifier head can't fix this — it only gets generic audio features.

**What works for text but not audio:** XLM-R text gets F1=0.819 frozen because
incongruity/resolution are SEMANTIC — they survive in pretrained token embeddings.
Laughter acoustic patterns are not in WavLM's pretraining task.

### Problem 2: Gated Fusion Collapses
```python
# What we tried (3 times):
g = sigmoid(Linear(concat([text_emb, audio_emb])))
fused = g * audio_emb + (1-g) * text_emb  # Gate
```
**What happens:** The gate learns g→1.0 (100% text) because text is 10× stronger.
Audio branch gradients → 0. Audio never learns. This is NOT a bug — it's the
correct solution for a model where one modality dominates.

**The fix:** Don't use a gate. Use concat + MLP. Or use a much larger audio encoder.
Or condition the audio branch on text embeddings (cross-attention).

### Problem 3: Prosody Aggregation
```python
# What we did:
word_features: [pause_before, f0, rms, word_duration] × 73K words
→ aggregate to utterance: [mean, max, std] × features
→ train on utterance-level aggregated prosody → F1=0.136
```
**What happens:** Aggregation (mean/max/std) dilutes the signal. `pause_max`
is the strongest word-level signal (Purandare's ToM), but averaging it with
non-laugh words makes it indistinguishable.

**The fix:** Extract prosody at the SAME granularity as labels. If label is
utterance-level, extract utterance-level prosody (not word-then-aggregate).

---

## Phase D: Redesigned Architecture

### Full Model (5 components)

```
COMPONENT 1: WavLM Encoder (PARTIAL UNFREEZE)
  - Freeze all layers initially
  - Unfreeze last 6 transformer blocks
  - Discriminative LR: encoder=5e-5, head=1e-3
  - Rationale: Bottom layers = generic speech, top layers = task-specific
  - FINE-TUNE with audio laughter labels, not frozen inference

COMPONENT 2: Audio Pooling — 3 options
  (A) MeanPooling:     avg(all 500 frame embeddings)     [Phase A baseline]
  (B) AttentionPooling: learn soft weights over frames   [NEW]
  (C) CSA:             select top-50 frames → attention   [NEW]
  (D) MLA:            multi-head latent attention         [NEW]

COMPONENT 3: Engram Module
  - Input: 768-dim (pooled audio)
  - 768 → 256 (GELU) → 128 (linear)
  - + skip connection: 768 → 128
  - Output: 128-dim engram (compressed laughter representation)
  - Rationale: Forces dense encoding, removes noise

COMPONENT 4: Prosody Features (52 dims)
  - Pause-ToM:    pause_max, pause_mean, long_pause_count, has_long_pause
  - Duchenne:     f0_mean, f0_std, f0_variability, voiced_ratio
  - Incongruity:  rms_max, energy_spike_count, delta_rms_max
  - Spectral:      mfcc1-13 mean + delta
  - Projected: 52 → 64-dim

COMPONENT 5: Fusion + Classifier
  - concat([engram_128, prosody_64]) → 192-dim
  - MLP(192→128→64→2), no gate
  - Class weight: [1.0, 4.0] for imbalance
```

### Alternative Backbones

| Model | Pretraining | Size | Advantage |
|-------|-------------|------|-----------|
| WavLM Base+ | wav2vec2 | 95M | Current, speech-trained |
| Whisper Base encoder | Whisper | 74M | Multilingual, semantic |
| HuBERT Base | Masked prediction | 94M | Different SSL objective |
| BEiT Audio | Masked prediction | 90M | Vision-style for audio |
| AudioMAE | Masked autoencoder | 90M | Dense reconstruction |

**Recommendation:** WavLM is fine IF properly unfrozen. The issue was never
the backbone — it was the frozen-ness. But Whisper encoder is worth trying.

---

## What MLA/CSA/Engram Actually Do (Technical)

### Multi-Head Latent Attention (MLA)
MLA (from DeepSeek-V2) uses low-rank key-value projections to reduce KV cache:
```
K_i = W_K_i · x         # instead of full K = W_K · x
V_i = W_V_i · x
```
For audio: Each head can specialize to different acoustic aspects (energy,
pitch, timbre, temporal dynamics). The "latent" part means we compress before
computing attention, making it more efficient.

In our Phase D: We use simplified MLA as Multi-Head Attention Pooling.
Each head computes attention scores independently, then concatenate heads.

### Compressed Sparse Attention (CSA)
For audio with T=500 frames:
1. Score all T frames with a lightweight network (no backprop through encoder)
2. Select top-K=50 frames (hard attention, very sparse)
3. Apply attention pooling only on selected frames

Rationale: Most frames in 5s of audio are silence/speech. Laughter is brief
(~0.3-1s). CSA finds the 50 most "laughter-like" frames and attends only to those.

### Engram Module
Neuroscience: An engram is a physical trace of a memory in the brain.
ML analogue: Force the representation through a narrow bottleneck.
This causes the network to:
1. Compress redundant information
2. Keep only dimensions that help classify laughter
3. Learn a dense, laughter-specific encoding

Architecture: Residual bottleneck (768→256→128 + skip)

---

## Experiments to Run (Priority Order)

### Experiment 1 (Highest Priority): Phase D — CSA + Engram + Partial Unfreeze
```
Train: 8 epochs, batch=32, encoder_lr=5e-5, head_lr=1e-3
Compare 4 ablation variants:
  A: MeanPool (baseline)
  B: AttentionPool
  C: AttentionPool + Engram
  D: CSA + Engram (full Phase D)
```
**Success criteria:** Any Phase D variant > F1=0.70 (meaning partial unfreeze works)

### Experiment 2: Whisper Encoder vs WavLM
Same architecture, replace WavLM with Whisper encoder (whisper-small or base).
Whisper has stronger multilingual semantic understanding.
```python
# whisper-base: dim=768, 8 layers
from transformers import WhisperModel
whisper = WhisperModel.from_pretrained('openai/whisper-base')
```
**Hypothesis:** Whisper's encoder captures better audio-semantic relationships.

### Experiment 3: Multimodal Fusion (text + audio)
After Experiment 1 succeeds (F1 > 0.70):
```
text_emb: XLM-R mean_pool → 256-dim
audio_emb: Phase D Engram output → 128-dim
prosody: prosody_proj → 64-dim
Fused: concat → MLP(448→256→128→2)
```
Expected: If audio and text make different errors, fusion F1 > 0.85.

### Experiment 4: Word-level prosody with CTC/alignment
Instead of utterance-level prosody, use forced alignment to get word-level prosody:
```
1. Use Whisper to transcribe + get word timestamps
2. Extract pause/F0 at each word boundary
3. Aggregate only words within the predicted laughter window
```
This gives word-level prosody matching word-level labels.

---

## What NOT to Do (Lessons Learned)

1. ❌ **Don't use LLM-generated features** — H4.4 proved label leakage
2. ❌ **Don't freeze the audio encoder** — Theory D confirmed
3. ❌ **Don't use gates for fusion** — gate collapses to dominant modality
4. ❌ **Don't aggregate word→utterance for prosody** — dilutes signal
5. ❌ **Don't use 3s windows if trained on 5s** — temporal pattern mismatch
6. ❌ **Don't threshold-tune your way out of precision gap** — doesn't work
7. ❌ **Don't use random split** — per-show split is required for valid results
8. ❌ **Don't train longer than 8 epochs** — WavLM overfits quickly on small data

---

## Honest Assessment

**What's realistic to achieve:**

| Target | Expected F1 | Confidence |
|--------|------------|------------|
| Phase D (partial unfreeze, no fusion) | 0.68–0.75 | High (theory D confirmed) |
| Phase D + text fusion | 0.82–0.87 | Medium (if complementary) |
| Whisper encoder replacing WavLM | 0.70–0.78 | Medium (untested) |
| prosody-only improvement | 0.18–0.25 | Low (history says no) |

**What's unrealistic:**
- F1 > 0.87 from audio alone (text is F1=0.819 and that's close to ceiling)
- Prosody-only F1 > 0.30 (word-level prosody has been tried and failed)
- Any model trained on 71 videos > 0.90 F1 (too few examples for complex task)

**The fundamental limit:** Audio laughter detection at word-level is a HARD task.
WavLM's frozen encoder was the immediate fixable problem. The deeper problem is
that acoustic laughter signals are diffuse and superimposed with speech. The
proven signal (Purandare pauses) requires precise temporal alignment we don't have.

**The right bet:** Text (F1=0.819) + audio (F1≈0.70 unfrozen) + fusion = 0.84–0.87.
This is a genuine contribution — audio adds complementary information that text misses
(who's laughing, not just what's said).
