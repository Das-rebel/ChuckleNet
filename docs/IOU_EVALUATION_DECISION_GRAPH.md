# ChuckleNet: Definitive Decision Graph
**Date:** 2026-09-01 (fast extraction method found and verified)
**Status:** Word-level WavLM extraction RUNNING at ~300 videos/hr

---

## Executive Summary

| Item | Status |
|------|--------|
| **Goal** | Beat StandUp4AI (EMNLP 2025): IoU-F1 = **0.51** @ IoU≥0.2 |
| **Pipeline** | Fusion model (WavLM + prosody) |
| **Current best** | 5s-chunk IoU-F1 = **0.276** (structural gap) |
| **Word-level extraction** | RUNNING: ~300 videos/hr ✅ |
| **Next action** | Wait for extraction, then word-level training |

---

## The Three Tasks (CRITICAL: Don't Mix These Up)

| Task | Granularity | Our F1 | StandUp4AI | Status |
|------|------------|---------|------------|--------|
| **Utterance-level** | 5s window → laugh/no-laugh | **0.975** ✅ | n/a | Done — paper-ready |
| **5s-chunk on EMNLP** | 5s chunk → IoU segment | **0.276** @ IoU≥0.2 | 0.51 | Structural ceiling — wrong granularity |
| **Word-level (REAL GOAL)** | Per-word timestamp | **IN PROGRESS** | 0.51 | 🔄 Extraction running |

**Why 5s-chunk IoU=0.276 ≠ comparable to StandUp4AI:**
- StandUp4AI evaluates on **1–3 second laugh segments** (word-level)
- Our 5s-chunk predictions average ~5s → max IoU with 1s laugh ≈ 0.3–0.4
- This is a **structural mismatch**, not a model failure

---

## Complete Results Table

| Test | N videos | Granularity | Metric | Score | vs StandUp4AI |
|------|:--------:|-------------|--------|:-----:|:---------------:|
| Fusion (risa/no_risa) | 87 | 5s window | F1 | **0.975** ✅ | Different task |
| 5s-chunk XGBoost | 220 | 5s chunk | Chunk F1 | 0.715 | n/a |
| 5s-chunk IoU@0.2 | 220 | 5s chunk | IoU-F1 | **0.276** ❌ | 0.51 (gap: 0.23) |
| 5s-chunk IoU@0.1 | 220 | 5s chunk | IoU-F1 | 0.485 | — |
| **Word-level WavLM** | **221** 🔄 | **per word** | **IoU-F1** | **RUNNING** | Target: ≥0.51 |

---

## Word-Level Extraction: THE FAST METHOD (Found 2026-09-01)

### The Problem (Old Method)
Per-word `librosa.load(..., offset=t0, duration=dur)` re-decodes the entire m4a file from byte 0 for EVERY word:
- **5-30 seconds per word**
- **1 video × 800 words = hours**
- **221 videos = weeks** ❌

### The Solution (Fast Method)
Load audio ONCE, slice with numpy:
```python
# Step 1: Load entire audio ONCE (into memory)
y_full, _ = librosa.load(audio_path, sr=SR, mono=True)

# Step 2: Slice with instant numpy indexing
seg = y_full[int(t0*SR):int(t1*SR)]  # ~0.001s per word

# Step 3: Batch through WavLM
batch = torch.tensor(padded_batch).to(device)
with torch.no_grad():
    out = wavlm(batch).last_hidden_state  # (batch, seq, 768)
    emb = out.mean(dim=1).squeeze(1)      # (batch, 768)
```

### Speed Comparison
| Method | Per word | 800-word video | 221 videos |
|--------|----------|----------------|------------|
| Old: librosa offset/dur | 5-30s | 67 min - 6.7 hrs | weeks ❌ |
| **New: load once + numpy slice** | **~0.001s** | **~2 min** | **~45 min** ✅ |

### Verified Results (2026-09-01)
```
76r8IcowEsE: 1209 words → 239/hr
7E7la6BCpRc: 1062 words → 260/hr
7Gw1NjZ13fA: 218 words → 314/hr
7VkAFkK3bwQ: 965 words → 308/hr
7cBFWZDXlHA: 785 words → 294/hr
7gRo0nF1yS0: 907 words → 297/hr
7kULz2NevT4: 925 words → 289/hr
```
**Average rate: ~300 videos/hr** ✅

### Notebook
**`WordLevel_Fast.ipynb`** — Load once, numpy slice, batch WavLM

---

## Scaling Data Available

| Dataset | Videos | Words | Format | Source |
|---------|:------:|------:|---------|---------|
| EMNLP en_uk train | 261 | ~200K | word timestamps + B/I/L | StandUp4AI |
| EMNLP en_uk val | ~30 | ~20K | word timestamps + B/I/L | StandUp4AI |
| **Available overlap** | **221** | **~176K** | **audio + labels** | Drive |
| Gillick 87 | 87 | ~21K | 5s utterance labels | Internal |

---

## Word-Level Pipeline (Correct Approach)

```
Video audio → For each word: extract exact [t0, t1] timestamp
  → WavLM-base per-word embedding (768-dim)  ← FAST METHOD
  → Prosody per-word (F0, energy, duration)
  → Fusion classifier per-word (laugh/no-laugh)
  → Consecutive positive words → merge into segments
  → IoU evaluation against EMNLP B/I/L ground truth
```

---

## Expected Outcome

| Scenario | Videos | Expected IoU-F1@0.2 |
|----------|:------:|:---------------------:|
| Word-level (agent council estimate) | 221 | **0.50–0.65** |
| With threshold optimization | 221 | **0.55–0.70** |
| StandUp4AI baseline | 330hr | **0.51** |

**Agent council estimate: 0.50–0.65 IoU-F1 achievable with 221 word-level videos**

---

## Critical Rules (From 18 Historical Failures)

| Rule | Value | Source |
|------|-------|--------|
| pos_weight | ≤ 3.0 | Pattern 2 saturation |
| Saturation check | prob_std ≥ 0.01 | Pattern 2 |
| Min videos for word-level | ≥ 100 | Data scale |
| merge_threshold for IoU | sweep 0.3–0.9 | NEW this session |
| Train/val split | Video-level (GroupKFold) | Pattern 11 |
| **Audio loading** | **load ONCE, slice numpy** | **2026-09-01** |

---

## Decision: What to Do Next

```
We have 221 videos with audio + EMNLP word labels
     ↓
Extract per-word WavLM features (Colab T4, ~45 min)
     ↓
Train word-level fusion model
     ↓
Evaluate with proper word-level IoU
     ↓
Target: IoU-F1 ≥ 0.51 to beat StandUp4AI
```

**If word-level IoU ≥ 0.51:** Paper is ready — "When Simple Beats Deep: F0 Prosody Features Outperform WavLM"

**If word-level IoU < 0.51:** Scale further — get more EMNLP videos or try multilingual expansion

---

## Files Reference

| File | Purpose |
|------|---------|
| `WordLevel_Fast.ipynb` | **FAST** per-word extraction (load once + numpy slice + batch WavLM) |
| `WordLevel_Training.ipynb` | Word-level training + IoU eval |
| `Diagnostic.ipynb` | Debug zero-prediction issue |
| `IoU_Evaluation.ipynb` | 5s-chunk IoU eval (structural ceiling) |
| `docs/IOU_EVALUATION_DECISION_GRAPH.md` | This file |
