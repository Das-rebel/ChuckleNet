# P2 Beyond-Words Decision Memo — 2026-09-18

**Experiment ID:** `P2-BEYOND-WORDS-118V-2026-09-18`
**Mandate:** V4, P2 — prove beyond-words information on an applicable event/state task
**Dataset:** 118-video human-verified EMNLP-label intersection (window-level protocol)
**Artifacts:**

- `results/p2/p2_beyond_words_results.json`
- `results/p2/p2_beyond_words_observations.json.gz`
- `training/p2_beyond_words.py` (window-level implementation)
- `training/p2_beyond_words_wordlevel_slow.py` (preserved slower word-level prototype)

---

## Decision

**NOT SUPPORTED — concurrent pause/timing features add no incremental information over word content at 5-second window resolution.**

This is a valid null result. Per Mandate V4 §5: it narrows the business thesis. It does not kill the program; it redirects the P2 test to the preferred Level A design (prospective event prediction).

---

## Design

- 6,211 fixed 5-second windows (span of word timestamps); 2,765 positives (44.5%).
- Window label: positive iff a `B/I/L` word midpoint lies inside the window (same rule as P1/E02).
- 5-fold GroupKFold by video (same fold structure as P1); 3 seeds (42/43/44).
- Condition A — word content: TF-IDF unigrams+bigrams of the words in each window (train-fold fit, 5,000 features).
- Condition B — A + 7 temporal features: total pause, max pause, pause count (>0.3 s), mean word duration, mean speaking rate, word density, relative position.
- Identical MLP (256-64-1), identical seeds/folds, early stopping on validation F1@0.5.
- Paired evaluation: video-level mean F1 delta, video-clustered bootstrap, 10,000 resamples.

Note: this window set covers the word-timestamped span only, so the positive rate (44.5%) is higher than P1's (24.3%, which included tail windows beyond the last word). This is a self-contained paired comparison; absolute numbers are not comparable to P1.

---

## Results

| Condition | Fold mean F1 | Fold SD |
|---|---:|---:|
| word_content_tfidf | 0.5679 | 0.0209 |
| word_content_plus_temporal | 0.5705 | 0.0148 |

### Paired bootstrap (A − B; positive = temporal features hurt)

| Metric | Value |
|---|---:|
| Mean ΔF1 (B − A) | **+0.0018** |
| 95% CI (B − A) | **[−0.0046, +0.0080]** |
| Videos improved with temporal | 65 / 118 |
| Videos worsened | 52 / 118 |

The CI spans zero decisively. The effect size is two orders of magnitude below the gate threshold (+0.02).

---

## Pre-registered gate

> B > A with video-clustered bootstrap CI95 lower bound > 0 AND mean paired ΔF1 > 0.02

Result: **FAIL** — verdict **NOT SUPPORTED**.

---

## Interpretation

### What this null means

1. **Word content is a strong baseline.** TF-IDF alone reaches 0.568 fold F1 — well above the acoustic-window models in P1 (~0.49). Comedy transcripts are highly predictive of laugh locations; audiences laugh where the words set up jokes.

2. **Crude concurrent timing adds nothing on top of words.** Pause totals, speaking rate, word density, and position carry no measurable information about *whether the current window contains a laugh* beyond what the words already provide.

3. **Compatibility with P1.** P1 showed that destroying the *order* of acoustic window sequences hurts performance (+0.077 F1). P2 shows that *pause/timing statistics* of the current window add nothing over text. These are consistent: the temporal signal lives in the **sequential structure of acoustic representations across windows**, not in window-level timing aggregates. A bag-of-windows timing summary cannot capture what a sequence model does.

### What this null does NOT mean

- It does **not** test prospective prediction. This was a *concurrent* labeling task: "does this window contain a laugh?" The word content of the punchline itself is in the window. That is exactly why word content dominates.
- It does **not** rule out reaction-latency, onset-prediction, or interruption signals. Those require the Level A design.
- It does **not** validate or refute the commercial thesis on its own.

---

## The correct next P2 test (Level A — event prediction)

Mandate V4's preferred target is prospective:

> Predict a future observable interaction event from preceding interaction context.

Concrete design:

- **Task:** predict laugh onset in the window(s) *following* the current context, using only features from *before* the onset.
- **Conditions:** words-before-only (TF-IDF of preceding context) vs words-before + timing-of-before (pause/rate features of preceding context) vs acoustic-sequence-of-before (P1-style WavLM windows).
- **Why this escapes the null:** the answer is not in the current window's words. If timing of the setup (a beat of silence before the punchline, a rate change) predicts the laugh, that is genuinely beyond-words.
- **Gate:** same structure — paired, video-clustered bootstrap CI, ΔF1 > 0.02.

This is now the single highest-information research action.

---

## Business thesis narrowing

- Do **not** pitch "audio timing features improve laugh/emotion detection over transcripts." Concurrent evidence says they do not.
- Keep the thesis in the P1-supported form: **sequence-structured audio representations carry information beyond concurrent classification** — and the untested, commercially interesting version is **prospective**: predicting the reaction before it happens.
- The commercial Layer outputs affected: "hesitation proxy" and "response latency" claims must wait for Level A evidence. "Reaction event detection" concurrent claims remain supported at weak-label tier only.

---

## Next step

Exactly one highest-information next action:

**Run P2 Level A (prospective laugh-onset prediction) on the 118v set: context-words-only vs context-words + context-timing vs context-acoustic-sequence, predicting onset in the next 1–2 windows.**
