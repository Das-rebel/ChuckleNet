# P2 Level A — Theory Recheck, Literature Sweep, and Pre-Registration — 2026-09-18

**Trigger:** directive to recheck old theoretical concepts (biosemiotic framework), run a literature sweep, and decide what needs to be done next.
**Inputs rechecked:** `docs/BIOSEMIOTIC_FRAMEWORK_V2.md` (2026-09-10), `docs/PAPER_INTERACTION_SIGNAL_V1.md` §2.1–2.2 and §5.2, complete-replan leakage history, P1/P2 results from this date.
**Research channel used:** agent-reach → Exa web search (5 queries) + Jina reader; Algebrica link assessed separately.

---

## 1. Recheck of old concepts

### 1.1 What survives: the biosemiotic THEORY layer

`BIOSEMIOTIC_FRAMEWORK_V2.md` defined five testable hypotheses. Current evidence maps onto them as follows:

| Hypothesis | Content | Status after P1/P2 (2026-09-18) |
|---|---|---|
| H1 relational meaning | predictive value depends on temporal relation to surrounding interaction | **PARTIAL SUPPORT** (P1: order destruction −0.077 F1 [CI −0.092,−0.062]; fine local order null) |
| H2 producer/recipient dependence | same event, different meaning by source | untested (E03 label-blocked) — correctly deferred |
| H3 reaction coupling | event-response coupling beats isolated events | **UNTESTED — now the live experiment (P2 Level A)** |
| H4 non-semantic increment | information survives lexical control | **concurrent variant NULL** (P2: +0.0018 [−0.0046,+0.0080]); **prospective variant untested** |
| H5 multimodal convergence | audio+visual complementary | correctly deferred (P5) |

Conclusion: the theory layer is **not obsolete — it anticipated this exact evidence structure**. Its §7 rule ("theory should generate experiments, not dictate outcomes") is what we now execute: H3 + prospective-H4 = P2 Level A.

### 1.2 What stays dead: synthetic "biosemiotic features"

The old `tom_*`, `duchenne_*`, `incongruity_*`, `speaker_intent` features were LLM-generated **with label knowledge** (features alone reached F1 0.829 → leakage provenance) and were correctly dropped in the COMPLETE_REPLAN. Reviving "biosemiotic" means the **sign-theoretic framing**, never those features. Level A features must be signal-derived only (timestamps, pauses, rates, WavLM frames) with train-fold-only fitting.

### 1.3 The old concept that WAS the plan all along

`PAPER_INTERACTION_SIGNAL_V1.md` §5.2 already specified the temporal encoder targets: "event onset and offset; turn position; response latency; preceding-event relation; persistence." Level A is not a new idea — it is the **unexecuted portion of the existing canonical method**. The P2 concurrent test answered a side question (is the current window's timing informative given its words? no); the core question was always prospective.

### 1.4 Semiotic sharpening (Peirce index vs symbol)

Words are symbols (conventional); laughter is an index (causally connected to the state it signals). The concurrent null now makes sense in these terms: at the moment of laughter, the punchline words already index it (symbolic route dominates). The scientifically open indexical claim is **prospective**: does the signal *before* the onset carry information about the reaction *after*? That cannot be solved by concurrent word content, by construction.

---

## 2. Literature sweep — what exists, what it licenses

| Work | Finding | Implication for us |
|---|---|---|
| ICPhS 2019, "No Laughing Matter" | anticipatory acoustic effects in the vowel/syllable **immediately preceding** laughter: higher F1, spectral COG, spectral SD (pressed-voice/arousal profile) | direct published support that pre-onset acoustics carry onset information → licenses the acoustic-of-before arm |
| Vettin & Todt (2004, via ICPhS intro) | >80% of laughter bouts follow full phrases | laughter onset position is structurally predictable — a position control is mandatory |
| Provine; Jefferson (CA) | laughter "punctuates" speech at precise interactional positions | target = reaction-position prediction, aligns with our discourse-position label finding |
| Ekstedt & Skantze, SIGDIAL 2022 (VAP + prosody) | quantifies how much prosody adds to turn-taking futures over lexical context | **methodological template for our arms** (words-only vs words+prosody increment) |
| Maier/Hough/Schlangen, Interspeech 2017 | predictive end-of-turn: lexical + acoustic both help | Level A precedent in dialogue domain |
| Chang et al., Interspeech 2022 | turn-taking under disfluency; acoustic cues crucial for pause-vs-end discrimination | supports timing-of-before arm |
| "Endpoint Anticipation" (arXiv 2026, Unmute/Kyutai integration) | forecasts end-of-turn up to 2.56 s ahead; beats VAP baselines; −505 ms latency in production framework | **commercial validation** of Design Partner A use case (prospective interaction signal layer for voice AI) — the industry is already paying attention to exactly this shape of signal |
| Li et al., CHI EA 2023 (anticipatory SDS) | predicting next-turn user laughter from system behavior (shared-laughter contagion) | adjacent prior art; ours differs: audience-of-performance setting, incremental-information controls |
| **TIC-TALK (ACL 2026, CHum)** | 90 filmed stand-up specials; 5,400+ aligned topic segments; laughter at 0.8 s (Whisper-AT) + skeletal keypoints; finds **stillness-before-punchline** (kinetic energy r = −0.75 with laughter rate) | (a) external support for pre-onset stillness; (b) **citable related work — we must differentiate** (they study timing correlates; we test incremental *predictive* information under paired controls); (c) candidate P4 transfer/external dataset |

**Algebrica link assessment** (t.co/skqeS84FTR → algebrica.org/founding-supporters): an open, ad-free mathematics/CS/NLP explainer project with a newsletter. Role for us: **writing-rigor resource** for future public explainers of the semiotic framing — not a data source or analysis tool. No action beyond noting it.

**Novelty check result:** nobody appears to have run a *controlled incremental-information* test of prospective audience-laughter prediction (words-before vs +timing-before vs acoustics-before, paired video-clustered bootstrap) on human-labeled stand-up. TIC-TALK is the closest resource; VAP line is the closest method. Our niche is defensible and specific.

---

## 3. Decision

**Run P2 Level A now.** This was pre-designed in `PAPER_INTERACTION_SIGNAL_V1.md` §5.2, is demanded by Mandate V4 §5 Level A, is licensed by the ICPhS-2019/VAP literature, and is the only remaining path to an H3/H4-prospective answer.

## 4. Pre-registration (fixed before running)

**Task.** For each window t (5 s, word-span protocol of P2), predict whether the **next** window t+1 contains a laughter word (B/I/L midpoint). Features may use only information from windows ≤ t. The concurrent-content confound is structurally removed: punchline words inside t+1 are excluded from all features.

**Dataset.** Same 118v / 6,211-window set as P2 (`results/p2` protocol).

**Arms (identical MLP 256-64-1, 5-fold GroupKFold, seeds 42/43/44, train-fold TF-IDF fit, early stopping on val F1@0.5):**

1. `position_only` — relative position of t (shortcut control; mandatory because our labels are discourse positions).
2. `words_before` — TF-IDF of cumulative transcript up to and including window t (B arm).
3. `words_before_plus_timing` — B + 6 timing-of-context features (pause totals/max/counts over trailing 3 windows, mean speaking rate, word density, current-window pause).
4. `acoustic_before` — causal acoustic context: [mean WavLM embedding of windows t−2..t, embedding of window t, position] (1,583-d).
5. `acoustic_plus_words` — 3 + 4 combined (C arm: everything).

**Primary gates (video-clustered bootstrap, 10k resamples):**

- Gate 1 (H4-prospective): `acoustic_plus_words − words_before` CI95 lower > 0 AND mean ΔF1 > 0.02.
- Gate 2 (timing): `words_before_plus_timing − words_before` same rule.
- Gate 3 (acoustic alone): `acoustic_before − words_before` same rule.
- Shortcut quantification: `words_before − position_only` (reported, not gated).

**Outcomes.** Any pass = beyond-words prospective information established at that tier. All-fail = the pre-onset signal is not extractable from these features at 5 s resolution → narrow to finer-resolution audio (Tier: sub-window acoustics) or accept null and strengthen P3-only path. Either way this closes the P2 question opened by Mandate V4.

**Anti-leakage checklist.** labels shifted by −1 (t predicts t+1) · features strictly ≤ t · TF-IDF train-fold-only · video-disjoint folds · no synthetic annotated features · same standardization discipline as P2.

---

*Pre-registered 2026-09-18 before execution. Execution script: `training/p2_level_a_prospective.py`; results: `results/p2_level_a/`.*

---

## 5. Outcome (executed same day)

**VERDICT: BEYOND-WORDS PROSPECTIVE SUPPORTED** (G1 and G3 pass; G2 fails).

Fold mean F1: position 0.418 · words 0.478 · words+timing 0.473 · **acoustic 0.569** · **acoustic+words 0.574**.

| Gate | Treatment − baseline | 95% CI | Improved/worsened | Result |
|---|---:|---|---|---|
| G1 H4-prospective (acoustic+words − words) | **+0.1117** | **[+0.0857, +0.1390]** | 83/28 | **PASS** |
| G2 timing (words+timing − words) | −0.0021 | [−0.0126, +0.0085] | 50/52 | FAIL (null) |
| G3 acoustic alone (acoustic − words) | **+0.1074** | **[+0.0766, +0.1398]** | 81/36 | **PASS** |
| shortcut (words − position) | +0.0497 | [+0.0130, +0.0862] | 66/52 | position is real but far smaller |

### Read-back correction (documented for provenance)
The first gate readout printed NOT SUPPORTED due to a **sign bug in gate evaluation only**: `paired()` already returns treatment-minus-baseline, and the gate code negated it. Raw paired deltas stored in `paired_tests` were always correct; corrected gates were recomputed from saved observations (`p2_level_a_observations.json.gz`) without retraining. Fix is in the script; correction note embedded in the results JSON.

### Interpretation
1. **The pre-onset frozen-WavLM context predicts next-window laughter far better than everything the speaker has said so far** (cumulative transcript). This is the first controlled positive result for H4-prospective / H3 (reaction coupling): pre-onset acoustics carry laughter-predictive information that speech content does not.
2. **Triangulation now closes:** P1 (sequence structure matters) + P2-concurrent (timing aggregates null) + P2 Level A (pre-onset acoustic context ≫ words) ⇒ the beyond-words signal is **acoustic and sequential**, not hand-crafted timing statistics. Consistent with the ICPhS-2019 anticipatory-cues literature.
3. **Honest caveat:** the target is laugh-word midpoint in window t+1; a laugh whose onset falls late in window t but midpoint in t+1 would put audible onset in the context. Part of the effect may therefore be *very-early onset detection* rather than pure pre-speech anticipation. A sub-5 s onset-margin analysis is the natural confirmation step and is registered as the next P2 refinement.
4. Position-only is a real shortcut (0.418) — consistent with the discourse-position label finding — but acoustic context beats it by ~0.15 F1.
5. Timing aggregates null twice (concurrent + prospective): hand-crafted pause summaries do not capture the signal; learned representations do. Do not pitch pause-statistic features.
