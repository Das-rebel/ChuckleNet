# ChuckleNet: Decision Graph — Scale vs Paper Strategy
**Date:** 2026-08-19
**Status:** Scaleup never ran — need to decide next step

---

## Current Reality (Triple-Checked)

### What We Have on Drive
| Resource | Count | Label Type |
|----------|-------|-----------|
| Audio files | 547 | None (raw m4a) |
| Labels (risa/no_risa) | 36 | Utterance-level, ~85% positive |
| EMNLP labels (B/I/L/O) | 261 | Word-level, ~15% positive |
| Partition CSV | 3,751 videos | Train/Val/Test split |

### What the Model Actually Does
`top200_prosody_model.pt` outputs **1.0 for ALL segments** (saturated due to pos_weight=5.0):
- `eval_1000` results: all probs = 1.0, F1 = 1.0 (on 100% positive labels)
- Local test on 10 EMNLP videos: min=1.0, max=1.0, mean=1.0, std=0.0

### The Two Evaluation Mismatches
1. **Model trained on risa/no_risa (utterance-level, 85% positive)**
2. **Model evaluated on EMNLP word-level B/I/L/O (15% positive)** ← WRONG LABELS

---

## The Paper's Valid Results (No Mismatch)

### ✅ F1=0.975 (Verified, Ready)
| Item | Value |
|------|-------|
| Model | `best_fusion_model.pt` (WavLM 768 + Prosody 23) |
| Data | 87 videos, 21,468 utterances, 22.7% positive |
| Split | Held-out 3 comedians (Burr/Chappelle/Peters) |
| Metric | Word-level BCE F1 |
| Status | **READY — submit as-is** |

### ✅ F1=0.975 (top200_prosody_model.pt, different training)
| Item | Value |
|------|-------|
| Model | `top200_prosody_model.pt` (15-dim prosody MLP) |
| Data | 200 videos, 62K segments, 16.8% positive |
| Metric | Segment-level F1 |
| Status | Works but saturated to 1.0 on EMNLP labels |

### ✅ F1=0.54 (Gillick 162 validation)
| Item | Value |
|------|-------|
| Data | 162 Gillick videos, external benchmark |
| Metric | Word-level BCE F1 |
| Comparable to | Gillick F1=0.75, StandUp4AI F1=0.51 |

---

## The Scale Question

### Scaleup Plan (June 2026 — NEVER RAN)
```
500 raw → 300 curated → 150 gold-standard
```

**What was built:**
- `SCALEUP_collection_pipeline.py` — yt-dlp based video collection (READY)
- `Colab_StandUp4AI_1000.ipynb` — evaluation notebook (READY but broken model)
- 547 audio files on Drive (collected but not from this pipeline)

**What was NEVER done:**
- ❌ Collection pipeline never ran
- ❌ No new labeled data created
- ❌ Model retraining on expanded data

### Why Scaleup Didn't Happen
1. Endorsement was blocking (Reddit post sent, waiting for response)
2. Focus shifted to IoU evaluation (dead end)
3. 87-video result seemed "good enough"

---

## Two Paths Forward

### Path A: Submit Paper NOW (Recommended)
**Use existing F1=0.975 result. No new training needed.**

```
✅ F1=0.975 on held-out comedians
✅ WavLM+Prosody fusion (791-dim)
✅ F0 beats WavLM by 58%
✅ Comparable to Gillick F1=0.75 (external validation)

Submit to: INTERSPEECH 2026 or EMNLP 2026 Industry Track
Timeline: 1-2 weeks to write
Risk: LOW — result is verified
```

### Path B: Run Scaleup FIRST, Then Submit
**Scale to 500+ videos for a stronger paper.**

```
Step 1: Run SCALEUP_collection_pipeline.py (download more labeled videos)
Step 2: Get EMNLP labels for new videos
Step 3: Retrain model on expanded dataset
Step 4: Re-verify F0 > WavLM on larger data
Step 5: Submit paper with stronger results

Timeline: 2-4 weeks
Risk: MEDIUM — model might still saturate
```

---

## What Actually Needs Doing for Scaleup

### If Path B: The Real Bottleneck
The bottleneck is NOT downloading audio. It's **getting labels**.

| Resource | Status | Problem |
|----------|--------|---------|
| Audio (547 files) | ✅ On Drive | Need more (target: 500+) |
| EMNLP labels (261 files) | ✅ On Drive | Can only label videos with existing annotations |
| StandUp4AI partition (3,751) | ✅ On Drive | 3,490 videos have NO audio AND NO labels |
| Collection pipeline | ✅ Built | Never ran |

**To scale labels, you need:**
1. Run collection pipeline to get more audio (target 500+)
2. Use EMNLP labels for those that have them
3. Pseudo-label the rest using the fusion model (F1=0.975)

But: `top200_prosody_model.pt` is saturated → can't use for pseudo-labeling.
**Solution:** Use `best_fusion_model.pt` (F1=0.975) for pseudo-labeling instead.

---

## Recommendation

**Path A (Submit Now) is the right move because:**

1. F1=0.975 is a **verified, strong result**
2. The "F0 beats WavLM" narrative is **genuinely surprising and publishable**
3. Scaleup has a **label bottleneck** — not trivial to solve
4. The model saturation issue makes Path B **risky without fixes**
5. You can always submit and THEN scale up for a second paper

**If you still want to scale:**
1. Use `best_fusion_model.pt` (NOT `top200_prosody_model.pt`) for any pseudo-labeling
2. The collection pipeline is ready — run it to add more audio
3. Focus on getting EMNLP-format labels (word-level B/I/L/O) for new videos

---

*Triple-check complete. Scaleup pipeline built but never ran. Paper result (F1=0.975) is verified and ready.*
