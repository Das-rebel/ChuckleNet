# TIC-TALK External Validation — Outcome Memo — 2026-09-18

**Experiment:** `TICTALK-EXTERNAL-ANTICIPATION-ONSET-2026-09-18` (+ archived saturated-target v1)
**Source:** public HF dataset `ENC-PSL/TIC-TALK` (CC-BY-NC-4.0) — 90 specials, 5,416 × 60 s blocks; sentence-BERT 384-d text, Whisper-AT laugh events, 1 fps pose. **No raw audio distributed.**
**Artifacts:** `results/p2_tictalk/tictalk_external_onset_results.json` (+ `tictalk_external_results_v1_anylaugh.json` archived); script `training/tictalk_external_validation.py`.

---

## What was testable (and what was not)

- **Not testable:** our *acoustic* anticipation claim — their release has no audio and no WavLM features, and blocks are 60 s (vs our 5 s windows).
- **Testable:** our *protocol* (causal next-block prediction, identical MLP/folds/seeds, paired show-clustered bootstrap) on their feature streams.

## Target design lesson (documented for provenance)

v1 used "any laugh in next block" → **94.1% positive** (stand-up laughter is near-continuous: ~1.2 events/10 s) → saturated, uninformative. Archived. Final target: **laughter ONSET in next block**, where onset = event starting after a ≥5 s laughter-free gap. Sparse and meaningful.

## Results (onset target; fold mean F1; 5 folds × 3 seeds; show-clustered bootstrap)

| Arm | F1 |
|---|---:|
| position_only | 0.689 |
| kin_only (pose proxies) | 0.733 |
| **text_only (sentence-BERT)** | **0.959** |
| text_plus_kin | 0.960 |

| Gate | Δ | 95% CI | Result |
|---|---:|---|---|
| E1: text+kin − text | +0.0012 | [−0.0007, +0.0030] | **null** |
| E2: kin − text | −0.2394 | [−0.2691, −0.2113] | kin ≪ text |
| E3: text − position | **+0.2692** | [+0.2375, +0.3023] | **PASS** |

## Interpretation

1. **The protocol ports cleanly to a second lab's dataset and task** — external check of our experimental machinery, not of our audio claim (impossible without their audio).
2. **Content anticipates strongly on their data too** (E3 PASS, +0.27 over position): consistent with our discourse-position finding and P2's strong word-content baseline. Cross-lab convergence on *that* point.
3. **Their non-lexical stream does not survive incremental controls.** TIC-TALK's headline correlational finding (kinetic energy ↔ laughter rate, r=−0.75 across topics) translates to **zero paired predictive increment** over text in a causal task (E1 null; E2 negative). This is an external demonstration of the exact distinction our methodology contributes: **correlates ≠ incremental predictive information**. Our own claim survived this standard (Level A, Rows 19–22); theirs does not on their released features.
4. **Scope of our claim is unchanged and not refuted:** the audio stream that carries our signal is absent from their release. Our acoustic anticipation result stands on our own human-labeled data with its full control chain.

## Net effect on the evidence base

- External, zero-cost, cross-lab check added to the record.
- Reinforces the paper's methodological thesis: paired incremental-information testing separates real signals from correlates (their kinematics correlate; don't increment; our audio context both correlates AND increments under stronger controls).

## Next options (all free)

1. **True audio replication on TIC-TALK shows** — blocked only by audio access: the shows are anonymized (`SHOW_XXXX`) with no source links, so this requires matching public specials ourselves (out of scope at zero cost; noted for the future).
2. Return to **P3 outreach** (kit ready) — the binding gap remains 0/20 qualified conversations.
