# P1 Temporal Decision Memo — 2026-09-18

**Experiment ID:** `P1-TEMPORAL-PAIRED-118V-2026-09-18`  
**Mandate:** V4, P1 — strengthen the temporal finding  
**Dataset:** 118-video human-verified EMNLP-label intersection  
**Artifacts:**

- `results/p1/p1_temporal_118v_results.json`
- `results/p1/p1_temporal_118v_observations.json.gz`
- `training/p1_temporal_validate.py`

---

## Decision

**PARTIAL — STRONGER SUPPORT FOR SEQUENCE CONTEXT, NOT FINE LOCAL ORDER.**

The pre-registered primary gate passed. The secondary local/direction controls did not pass.

This is a useful narrowing, not a failure.

---

## Design

- 118 videos with human-verified EMNLP `B/I/L/O/U` word labels.
- 11,161 fixed 5-second windows; 2,712 positives.
- Positive window rule: a `B/I/L` word midpoint lies inside the window.
- 5-fold `GroupKFold`, video-disjoint.
- 3 fixed seeds: 42, 43, 44.
- Same BiGRU recipe family as E02: 797-d input, hidden 128 bidirectional, `pos_weight=8`, AdamW 5e-4, final bias −2.0, gradient clipping 1.0.
- Conditions:

| Condition | Meaning |
|---|---|
| `true` | original temporal order |
| `random` | full within-video permutation |
| `local_shuffle` | within-video shuffle inside contiguous 25 s blocks |
| `reverse` | within-video reversal |

Model initialization seed was fixed across conditions within each seed/fold. Predictions from permuted inputs were mapped back to original window positions for paired evaluation.

---

## Results

| Condition | Fold mean F1 | Fold SD |
|---|---:|---:|
| true | 0.4935 | 0.0161 |
| random | 0.4196 | 0.0103 |
| local_shuffle | 0.4999 | 0.0164 |
| reverse | 0.4902 | 0.0191 |

Absolute F1 is not directly comparable to older E02 runs because this is a new multi-seed paired protocol. The internal paired comparisons are the evidence.

### Paired clustered bootstrap results

Video-ID clustering; all seed/fold observations for each sampled video. 10,000 bootstrap resamples.

| Comparison | Mean ΔF1 | 95% CI | Improved / worsened / unchanged |
|---|---:|---:|---:|
| true − random | **+0.0769** | **[+0.0617, +0.0917]** | 287 / 66 / 1 |
| true − local_shuffle | −0.0061 | [−0.0170, +0.0044] | 146 / 193 / 15 |
| true − reverse | +0.0071 | [−0.0032, +0.0180] | 165 / 179 / 10 |

---

## Pre-registered gate

Primary gate:

> true > random with bootstrap CI95 lower bound > 0 and mean paired ΔF1 > 0.02

Result: **PASS**

Secondary controls:

> true should also beat local-shuffle and reverse with positive CI lower bounds

Result: **FAIL**

Final verdict: **PARTIAL**

---

## Interpretation

### Supported

Destroying the full within-video sequence substantially hurts laughter-window F1.

This strengthens the earlier E02 finding that sequence structure carries information beyond independent window classification.

### Not supported

Preserving broad temporal location while shuffling within 25-second blocks does not hurt performance. Reversing order also does not hurt performance.

Therefore, the current 118v evidence does **not** support a claim that fine-grained local ordering or forward temporal direction is the source of the effect.

### Correct claim

> Sequence context helps. Full randomization destroys it. But current evidence supports broad sequence/context structure, not fine-grained directional timing.

### Incorrect claim

> “Temporal order matters” stated without qualification.

That is now too broad. The controlled result is narrower.

---

## Implications for the vision

This advances Mandate V4 P1 from a single-seed observation to a paired, multi-seed, controlled result.

It also narrows the interaction-signal hypothesis:

- useful signal appears to live in **sequence/context structure**;
- current fixed 5-second windows do not demonstrate fine onset/direction sensitivity;
- future temporal work should test actual event timing, reaction latency, and preceding-event distance rather than only window-order permutations.

---

## Consequence for model/paper claims

Do **not** headline:

> “Temporal order carries interaction information.”

Use instead:

> “Sequence context carries reproducible laughter-predictive information; full order destruction significantly reduces performance, while local-order and direction controls do not.”

For product language, this still supports a **reaction/context event layer**, not a proven real-time causal timing predictor.

---

## Next step

The next P1-grade experiment should test event-time hypotheses directly:

1. preceding-context length ablation;
2. reaction onset/offset error;
3. reaction-latency prediction;
4. causal/prefix-only evaluation;
5. finer than 5-second resolution where labels permit.

That is more informative than another architecture search or another weak-label Kaggle run.
