# IoU Evaluation Decision Graph
**Date:** 2026-08-19
**Status:** Post-agent-council analysis

---

## Decision 1: Metric Mismatch (CRITICAL — FOUND FIRST)

> **Our reported F1=0.975 and StandUp4AI's F1=0.51 are NOT comparable.**

| Metric | What it measures | Our model | StandUp4AI |
|--------|-----------------|-----------|------------|
| **Word-level F1** | Per-word BCE classification | 0.975 | unknown |
| **IoU-F1 @0.2** | Segment boundary overlap | ~0.15 (this eval) | 0.51 |
| **IoU-F1 @0.3** | Segment boundary overlap | ~0.15 (this eval) | unknown |

**Implication**: We cannot claim to beat StandUp4AI with our current metrics. We need IoU-F1 to make a valid comparison.

---

## Decision 2: Root Cause of Saturation (AGENT COUNCIL CONSENSUS)

### Primary Cause: `positive_class_weight=5.0` over-weighting
- Natural imbalance ratio: 77.3/22.7 = **3.4:1**
- Using **5.0** = **47% over-weighting** beyond natural ratio
- This causes sigmoid outputs → 1.0 for virtually all inputs
- The model finds the "easy solution": predict positive for everything, avoid FN penalty

### Secondary Cause: No temporal context in 15-dim features
- Per-word features lack sequential information
- Laughter is a **temporal event** spanning multiple words
- Individual word prosody cannot distinguish laugh-vs-speech
- Evidence: Even non-laugh words get pred=1.0

### Does dropout(0.3) fix this? NO
- Dropout regularizes hidden layers, doesn't prevent output saturation
- It's a training regularizer, not an output normalizer

### Does focal loss fix this? YES (partially)
- Focal loss (gamma=2) down-weights easy negatives
- Would prevent the model from just predicting 1.0 for everything
- Better than BCE+pos_weight for this imbalance level

---

## Decision 3: Architecture — Sequence vs Per-Word

### StandUp4AI Approach (EMNLP 2025)
- **BiLSTM-CRF** on word-level features
- Temporal context window around each word
- CRF layer enforces valid BIO sequences
- Result: F1=0.51 @ IoU=0.2

### Our Current Approach (FAILS)
- Per-word MLP (no temporal context)
- 15-dim features = single snapshot per word
- Saturation → predicts 1.0 for ALL words
- Consecutive merge → 175 segments vs 20 GT

### Council Recommendation: BiLSTM + Utterance-Level Hybrid

```
Architecture Decision:
├── Option A: BiLSTM-CRF (match StandUp4AI)
│   └── Per-word features → BiLSTM → CRF → BIO tags
├── Option B: Utterance-level (our strength, simpler)
│   └── Per-utterance prosody features → MLP → laugh/no-laugh
│   └── Post-process: segment = whole utterance if laugh
└── Option C: Hybrid (recommended)
    └── Per-word features → BiLSTM → per-word prediction
    └── Post-process: merge consecutive → min duration filter
```

**Verdict**: Option C (Hybrid) — use our F0 features with temporal context, add min-duration filter.

---

## Decision 4: Training Recipe Fix

### Immediate Fix (No Retraining)
1. Raise prediction threshold to **0.8-0.9** (model already saturated to 1.0, so threshold won't help — SKIP THIS)
2. Apply **minimum segment duration filter** (≥3 consecutive words)
3. This reduces over-segmentation from ~175 to ~20-40 segments

### Proper Fix (Retrain Required)
1. **pos_weight**: Lower from 5.0 → **2.5-3.0**
2. **Loss**: Switch to **Focal Loss (gamma=2)** instead of BCE+pos_weight
3. **Architecture**: Add **bidirectional LSTM** (128 hidden) on 15-dim features
4. **Label smoothing**: 0.05 to prevent over-confidence

---

## Decision 5: Evaluation Strategy

### Current Problem
- We evaluate word-level model on word-level labels
- But: model was trained on UTTERANCE-level labels (87-video dataset)
- Utterance-level training ≠ word-level evaluation

### Evaluation Options

| Option | What | Pros | Cons |
|--------|------|------|------|
| **Word-level IoU** | BIO sequence → segments | Standard (StandUp4AI) | Need word-level training |
| **Utterance-level IoU** | Whole utterance = 1 segment | Uses our strengths | Granularity mismatch |
| **Frame-level IoU** | Fine-grained timestamps | Most precise | Need frame-level labels |

**Recommended**: Word-level IoU with BiLSTM-CRF retraining (matches StandUp4AI benchmark).

---

## Decision 6: The 87-Video Constraint

> **Critical vulnerability**: 87 videos is a toy dataset for IoU evaluation.

- StandUp4AI: 330 hours (~2000+ videos)
- Gillick: Switchboard (~70 hours)
- Our 87 videos ≈ 6-8 hours

**For a valid IoU comparison**, we need:
- Either: Evaluate our model on Gillick 162 (already have labels)
- Or: Download and evaluate on StandUp4AI subset

**Current state**: 10 videos evaluated (IoU-F1 ~0.15). Not statistically meaningful.

---

## Recommended Action Plan (Priority Order)

### Phase 1: Immediate (No Retraining)
- [ ] Add minimum laugh segment duration filter (≥3 words)
- [ ] Evaluate on Gillick 162 videos (already have labels) for valid comparison
- [ ] Report Gillick F1 at word-level (not IoU) — this is our true comparison point

### Phase 2: Short-Term (Retrain)
- [ ] Retrain with BiLSTM temporal context layer
- [ ] pos_weight=2.5 (not 5.0) + focal loss
- [ ] Evaluate on 50+ EMNLP videos at IoU level

### Phase 3: Scale
- [ ] Download StandUp4AI full dataset (330hr)
- [ ] Retrain on larger dataset with correct architecture
- [ ] Compare IoU-F1 vs their F1=0.51

---

## Agent Council Verdicts

| Role | Diagnosis | Fix |
|------|-----------|-----|
| **ML Architect** | Gradient masking + temporal blindness | BiLSTM + lower pos_weight |
| **Domain Expert** | Word-level loses temporal context | Utterance-level or BiLSTM |
| **Evaluator** | Over-segmentation from consecutive positives | Min duration filter + Viterbi |
| **Training Engineer** | pos_weight=5.0 (47% over-weight) | pos_weight=2.5-3.0 + focal loss |

---

## Key Decision: What to Report

Since our F1=0.975 is at **word-level BCE** and StandUp4AI F1=0.51 is at **IoU segment-level**, we must choose:

**Option A (Conservative)**: Report our word-level F1=0.975 and note IoU comparison is not valid
**Option B (Aggressive)**: Retrain with BiLSTM, evaluate at IoU, claim IoU-F1 comparison

**Recommendation**: Option A first (publish paper with word-level F1), then Option B for follow-up.

---

*Synthesized from agent council: ML Architect, Domain Expert, Evaluator, Training Engineer*
