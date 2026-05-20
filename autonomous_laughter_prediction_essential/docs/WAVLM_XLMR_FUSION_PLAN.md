# WavLM + XLM-R Fusion Implementation Plan

## Why Previous Audio Attempts Failed

| Attempt | F1 | Why |
|---------|-----|-----|
| librosa F0/RMS/pause | 0.24-0.29 | Hand-crafted features, word-level (0.3s), F0 d=0.06 |
| MFCC + ZCR + spectral | 0.23-0.29 | More features ≠ more signal, same word-level ceiling |
| WavLM audio-only (Phase A) | 0.0 | Frozen WavLM + MLP on 0.3s word clips, no gradient flow |
| Gradient Boosted trees | 0.0 | Class imbalance (12%), overfits |

**Root cause**: Word-level analysis is the wrong level. Laughter is supra-segmental.

## Architecture: Gated Multimodal Fusion

```
Utterance Text → XLM-R → text_proj (768→256) ─┐
                                                ├→ Gated Fusion → classifier
Audio Clip (3-15s) → WavLM-Base+ → audio_proj (768→256) ─┘

Gate: g = σ(Wg·[t; a])
Fused = g⊙t + (1-g)⊙a  ← learns when to trust audio vs text
```

**Why gated fusion**: 15K utterances, concatenation overfits, cross-attention too complex.
Gate learns "trust audio for physical comedy, trust text for wordplay."

## Three-Phase Training

| Phase | What | Epochs | LR | Goal |
|-------|------|--------|----|------|
| 1: Text baseline | XLM-R only (no audio) | 5 | 5e-5 | F1 ≈ 0.75-0.80 |
| 2: Frozen fusion | Freeze XLM-R, train audio_proj + gate | 10 | 1e-3 | Audio learns complement |
| 3: Joint fine-tune | Unfreeze top 2 XLM-R layers, all | 5 | 2e-5/5e-4 | **Target F1 > 0.85** |

## Expected F1 Targets

| Model | Expected F1 | Rationale |
|-------|:-----------:|-----------|
| XLM-R text-only (utterance) | 0.75-0.80 | Word-level 0.82 inflated by spans |
| WavLM audio-only (utterance) | 0.55-0.65 | Literature: audio humor F1=62-63% |
| **Gated fusion** | **0.82-0.87** | Audio adds +3-7% to text |

## Key Design Decisions

1. **Utterance-level, not word-level**: 15K utterances, 32.6% positive, 3-15s clips
2. **WavLM-Base+** (not Wav2Vec2): Better on noisy speech+laughter
3. **Pre-extract embeddings**: Save WavLM output to disk (~4.6GB), don't compute on-the-fly
4. **Per-video split**: GroupKFold 5-fold CV, no leakage
5. **Differential LR**: 2e-5 for text, 5e-4 for fusion layers

## Files to Create

```
training/extract_wavlm_embeddings.py    ← Colab: ~2hrs for 15K utterances
training/model_wavlm_xlmr_fusion.py    ← GatedMultimodalFusion + WavLMXLMRFusionModel
training/dataset_utterance_multimodal.py ← Pairs WavLM embeddings with tokenized text
training/train_fusion_v3.py            ← 3-phase training with GroupKFold CV
data/audio_comedy/wavlm_embeddings/    ← ~4.6GB pre-extracted embeddings
```

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| WavLM audio F1 < 0.50 | Add prosody features alongside WavLM |
| Fusion hurts text | Phase 2 freezes text → zero risk |
| Gate collapses to text-only (g→0) | Monitor gate stats; add audio auxiliary loss |
| Only 15K samples (overfitting) | 5-fold CV, dropout=0.2, weight decay=0.01 |

## Escalation Path if F1 < 0.85

1. WavLM-Large (768→1024, +1-2% F1)
2. Add hand-crafted prosody alongside WavLM
3. Context window: ±2 neighboring utterances
4. Multi-task: predict label_any + label_majority