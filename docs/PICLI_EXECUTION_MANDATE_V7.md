# PICLI EXECUTION STATUS ADDENDUM — V7

**Date:** 2026-09-18  
**Strategic control plane:** `docs/PICLI_EXECUTION_MANDATE_V4.md`  
**Supersedes only execution status in:** V5/V6 kernel-status sections  
**Does not supersede:** V4 priorities, gates, resource allocation, or commercial rules

---

## 0. Governing mandate

The active scientific/business mandate remains **Mandate V4**:

- **P0 — evidence archaeology / reproducibility**
- **P1 — strengthen the temporal finding**
- **P2 — prove beyond-words information on an applicable event/state task**
- **P3 — commercial discovery in parallel**
- **P4/P5 — transfer and visual expansion only after P1/P2**

V4 explicitly says not to spend material effort on P4 while P1/P2 are unresolved. That rule remains binding.

---

## 1. Goal

From Mandate V4:

> Can machines extract, learn, and model useful information from how humans interact that is not contained in the literal words they use?

Formal test:

> Do non-semantic interaction signals provide incremental, reproducible information about interaction events/state beyond transcript semantics and context?

Laughter is only the first observable event laboratory. It is not the final product thesis.

---

## 2. Current execution status

### v32 remains the weak-label flagship

The canonical weak-label 620-video result is still **v32**:

| Metric | v32 value |
|---|---:|
| Validation F1 | **0.2732** @ threshold 0.85 |
| AP | **0.142** |
| Event IoU-F1@0.2 | **0.2290** |

This is a **weak-label/label-ceiling result**, not a product-quality claim. It matches Mandate V4’s interpretation.

The earlier concern that 0.229 might have come from a RICH subset is resolved:

- **0.197** was the earlier 20-video curated gate result.
- **0.229** is the full 620-video v32 result.
- They are different protocol scales, not contradictory measurements.

---

### v30e is complete, but only as P0 reproducibility

Kaggle kernel `subhajitdas/chuckle-e2e-v30e`, run `134760029`, completed.

- 620/620 videos processed.
- 0 extraction skips.
- 121,928 VTT segments indexed.
- 1,965 weak positives indexed.
- Used a **900 s audio decode window**.
- Evaluated only feature-backed IDs.
- Validation: 15,478 samples / 164 positives.
- Segment F1: **0.2444** @ threshold 0.75.
- AP: **0.1642**.
- Event IoU-F1: **0.1743**.

### Correct v30e classification

v30e counts toward **P0 evidence archaeology / reproducibility**, narrowly.

It does **not**:

- replace v32;
- strengthen P1 temporal evidence;
- pass P2 beyond-words testing;
- constitute WavLM fine-tuning;
- support production deployment;
- advance the decision graph beyond the existing weak-label layer.

The WavLM backbone is frozen. Only the small head is trained.

---

## 3. HuggingFace policy

| Repo | Mandate role |
|---|---|
| `Hayasuki/chucklenet-laughter-detector` | **v32 weak-label flagship**; cite this |
| `Hayasuki/chucklenet-v30e` | private P0 restricted-protocol reproducibility artifact; not public |

The v30e card must not describe the model as raw-audio classification. It expects precomputed `[batch, 768]` mean-pooled WavLM embeddings.

---

## 4. Decision-graph status

Against `DECISION_GRAPH_V2.md`:

- **Gate 1 — label validity:** still weak-label. v30e does not change label tier.
- **Gate 2 — shortcut resistance:** no new evidence from v30e.
- **Gate 3 — temporal causality proxy:** existing E02 evidence remains the relevant result; v30e does not update it.
- **Gate 4 — incremental information:** MELD null still blocks generic emotion claims.
- **Attribution / transfer / downstream intent:** still open.

---

## 5. What we actually learned

1. The Kaggle audio path now works end-to-end with local WavLM loading, robust fallback decoding, per-video feature saves, valid-ID-only splitting, and in-memory training.
2. v30e independently reproduced a weak-laughter signal, but under a narrower decode protocol.
3. v30e’s higher segment F1/AP does **not** make it better than v32; its event IoU is lower and its eval set is smaller.
4. The project does not need another frozen-WavLM weak-label repeat.
5. The next useful work remains Mandate V4’s P1: paired, seeded, temporally controlled validation of the sequence effect.

---

## 6. Next highest-information action

Per Mandate V4, the next action is still:

> Execute the P1 temporal-effect validation as a paired/counterfactual experiment with fixed seeds, leakage checks, and temporal permutation controls.

Do not start another 620-video weak-label WavLM repeat.

---

*Mandate V7 — execution status addendum to Mandate V4, generated 2026-09-18.*
