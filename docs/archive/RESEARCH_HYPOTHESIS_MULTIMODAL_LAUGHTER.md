# Research Hypothesis: Multimodal Laughter Detection in Multilingual Stand-up Comedy

**Date:** 2026-05-16  
**Status:** WavLM Phase A training in progress (Colab T4 GPU, v6)  
**Project:** Autonomous Laughter Prediction  
**Target:** 10M aligned audio-word segments → SOTA multilingual laughter detection

---

## 1. PROBLEM STATEMENT

We are building a multilingual (en/zh/hi-latn) word-level laughter detection system for stand-up comedy audio. The goal is to identify at the word level whether a comedian's utterance is followed by audience laughter.

---

## 2. CURRENT BASELINES

| Model | Approach | F1 Score | Notes |
|-------|----------|----------|-------|
| **XLM-R Text** | Word text → binary laugh/no-laugh | **0.82** | 19K train, 7 languages, Mac CPU |
| Teacher Refinement | Refined labels via LLM | F1=0.0784 | **BROKEN** |
| WavLM Phase A v5 | Frozen encoder + MLP | F1=0.2271 (declining) | **FAILED** - LR too high |
| WavLM Phase A v6 | LR=1e-4 + CosineAnnealing | **Running** | Expected F1 ≥ 0.35 |

---

## 3. CORE RESEARCH HYPOTHESIS

**Hypothesis:** WavLM audio features + text word embedding fusion outperforms text-only XLM-R for multilingual comedy laughter detection.

**Sub-hypotheses:**
1. Audio prosodic features (laughter rhythm, energy bursts) add signal beyond word content
2. WavLM's denoising pretraining generalizes to noisy comedy audio across languages  
3. Early fusion (concatenate features) is optimal for time-aligned word segments

---

## 4. FAILURE MODE: v5 vs v6

### v5: F1 Declining (0.2271 → 0.1999 → 0.1937)

**Root causes:**
- LR=1e-3 too high for frozen encoder + 200K param MLP
- No LR scheduling = optimizer overshooting
- Loss variance 0.05-1.13 per batch

### v6 Fixes:
- LR: 1e-3 → **1e-4**
- Added: **CosineAnnealingLR** scheduler
- Added: **Gradient clipping** max_norm=1.0

---

## 5. EXPECTED OUTCOMES

| Phase | Target F1 | Rationale |
|-------|-----------|----------|
| Phase A (frozen) | 0.30-0.50 | Limited capacity, frozen features |
| Phase B (unfreeze L2) | 0.50-0.65 | More adaptable features |
| Phase C (full fine-tune) | 0.65-0.80 | Full capacity |
| **Fused model** | **>0.82** | Beat text baseline |

---

## 6. DATA ANALYSIS

### Segments Distribution
- batch1: ~75K segments (en, 38 videos on GDrive)
- batch2: ~53K segments (en, same 38 videos)
- Total: **128,902** usable segments with audio

### Label Distribution
- ~13.5% positive (laugh) - healthy for class weighting

### Audio Path Mapping
```
Local Mac: /Users/Subho/.../data/audio_comedy/audio/en/br44MpGVsK8.mp3
GDrive: /content/gdrive/MyDrive/laughter_prediction/audio/en/br44MpGVsK8.mp3
```

---

## 7. EVALUATION FRAMEWORK

### Primary: F1 Score (binary, positive=laugh)
### Secondary: Precision, Recall, per-language breakdown

### Ablation Studies:
1. Audio-only (WavLM Phase C) vs Text-only (XLM-R F1=0.82)
2. Early fusion vs Late fusion vs Intermediate fusion
3. Different encoder sizes (Base+ vs Large)

---

## 8. OPEN QUESTIONS

1. Is word-level alignment correct? (VTT timestamps may have jitter)
2. Does WavLM English pretraining hurt zh/hi-latn?
3. Should we use Whisper encoder (multilingual) instead of WavLM?
4. Should we incorporate pause patterns (beat before punchline)?
5. Is mean pooling optimal? (Max pooling / attention may be better)

---

## 9. NEXT STEPS

1. Wait for v6 Phase A F1 → decide whether to proceed to Phase B
2. If F1 < 0.30: Debug audio loading / segment alignment  
3. Build fused model once audio baseline established
4. Validate with human listening on 50 random segments

---

*Document generated: 2026-05-16*
