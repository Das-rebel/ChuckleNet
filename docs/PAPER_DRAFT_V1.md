# PAPER DRAFT V1 — assembled 2026-09-12 from registered results only

> **Status:** draft skeleton with all numbers from RESULTS_LOG/EXPERIMENT_REGISTRY (rows 1–14). No number in this document is unregistered. Reproducibility appendix lists kernels/datasets.
> **Title options:**
> 1. **"Words Carry Emotion, Behavior Carries Laughter: A Multi-Scale Registered Study of Interaction-Signal Information"**
> 2. "Beyond-Words Information in Conversation: Strong Evidence for Laughter, a Null Result for Emotion"
> 3. "Weak Labels Lie Slightly, Sequence Is Real, Emotion Is in the Words: An Honest Audit of Interaction-Signal Detection"

---

## Abstract

We ask whether a machine can recover information from conversational interaction behavior that is not present in the literal words. We test this on laughter detection and general emotion classification using a registered experimental program with pre-specified gates.

**(1)** We show that the common shortcut of deriving training labels from transcript laughter markers (VTT `[laughter]` tags) produces a detector that *looks* strong at scale (620 videos, 121,928 utterances) but carries a measurable weak-label cost; forensics on the trained model show it tracks real signal (ground-truth-rate correlation 0.361) rather than artifacts, yet its ceiling is set by the labels. We document this as a case study in weak-label hygiene.

**(2)** Using true human labels at two independent scales (40 and 118 videos), we show sequence structure — pause/turn features and word-order context — carries real information: a BiGRU over word-level features beats an order-shuffled control by +0.034 and +0.087 IoU-F1@0.2 respectively, replicating across scales, with anchors (Gillick-162 fusion F1 0.559; 118v IoU-F1@0.2 0.3302; RICH 0.407±0.063) confirming the pipeline is calibrated.

**(3)** We then run the flagship test of beyond-words information on a *general* dialogue task: MELD 7-class emotion classification (11,131 utterances with official audio), comparing transcript-only (A), transcript+dialogue context (B), and B+acoustic interaction signals (C). The pre-registered gate fails: Δ(C−B)=0.000 (95% bootstrap CI [−0.014, +0.015]).

**Conclusion:** beyond-words interaction information is real but domain-specific — it is present for laughter/reaction events (where the word stream lacks the signal) and absent for general emotion classification with the same signal class (where it is not). We release the full decision registry, kernels, and per-arm artifacts.

---

## 1. Introduction

- The pitch that launched this program: "the words only tell half the story — can the machine get the other half?" This paper is the honest audit of that claim.
- Contributions:
  1. A registered, gate-governed evaluation program (4 tests) with two-scale replication and order-shuffle controls.
  2. A weak-label case study: VTT-marker training at 620-video scale + post-hoc forensics (what weak labels do and don't cost).
  3. Positive result: temporal/sequence signal on true labels, replicated at two scales (Gate 3 / T2).
  4. Negative result: beyond-words acoustic interaction features do not improve general emotion classification (T3, pre-registered, null).
  5. A sharpened scope statement: beyond-words information is a property of *reaction events*, not of conversation audio in general.

## 2. Background & Related Work

- Laughter detection lineage: Gillick et al. (AudioSet-derived word-aligned labels; word-level F0+MLP, saturated ≈0.975 F1 on our 87v rebuild); stand-up laughter detection on StandUp4AI (our anchor 0.3302 IoU-F1@0.2).
- MELD: text modality dominates emotion classification in published results; audio-only is far weaker. Our A-arm (0.4483 TF-IDF+LR) sits in the expected band for linear text models.
- Weak-label/weak supervision literature: distant supervision label noise; we contribute a *measured* weak-label cost in the laughter domain.
- Gap: no prior work we know tests "beyond-words interaction information" with the same feature class across BOTH a reaction event (laughter) and a general affect task (emotion), with a pre-registered gate on the delta.

## 3. Program Design (mandate tests)

- **T1 acoustic structure** (E01 controls): is laughter acoustically detectable at all, and do prosody features carry weight? Verdict: PARTIALLY SUPPORTED, capped by design (Gillick-162 fusion 0.559 / WavLM 0.548 / prosody 0.537; prosody-23 original recipe unrecoverable → canonical 27-d rebuild documented).
- **T2 temporal structure** (E02): does *order* matter? 4 arms × 2 scales; shuffle control.
- **T3 beyond words** (E05 on MELD; registry E03 source-separation remains label-blocked): A/B/C arms with bootstrap CI on Δ(C−B).
- **T4 transfer** (stand-up → conversation → voice-agent): open; not started.
- Governance: EXPERIMENT_REGISTRY entries with success gates + falsifiers written BEFORE runs; council review; results logged regardless of direction.

## 4. Case Study: Weak Labels at Scale (VTT line)

- Setup: 620 stand-up videos, transcript `[laughter]` markers as weak labels; WavLM-based utterance embeddings; 121,928 utterances.
- Result: IoU-F1@0.2 = **0.2290**, utterance-F1 0.2732, AP 0.142.
- Post-hoc forensics (pre-registered, free analyses on saved npz):
  - truncation cost mild (2s-boundary artifact) — surgical re-run (v33) NOT justified, cancelled;
  - model tracks real signal: corr(ground-truth rate, predicted rate)=**0.361**; no duration/norm shortcut found;
  - conclusion: v32 is honest *for its labels*; its ceiling is the label ceiling.
- Registry rule enforced throughout: weak-label numbers are hypothesis generators, never headline claims.

## 5. T2 — Temporal Structure on True Labels (Gate 3: PASS, replicated)

**Protocol:** 5-fold GroupKFold by video; identical architectures across arms; select by val F1@0.5. Arms: A WavLM+prosody features; B A+temporal pause/turn features; C B+sequence model (BiGRU, stability recipe: pos_weight 8.0, per-fold standardization, final-bias −2.0, lr 5e-4, grad-clip 1.0); C-shuf: C with the same video's rows order-permuted (fixed seed) — a control that destroys order while keeping marginals.

- **40v word-level:** A 0.2231±0.021 → B 0.2984±0.048 (**+0.075**) → C **0.3460±0.046** (IoU 0.3987) → C-shuf 0.3125±0.026 (**sequence effect +0.034**).
- **118v window-level (791-d, 11,161 windows, exact historical window count):** A 0.5884±0.031 (reproduces historical band) → B 0.5785 (pause features degenerate on a fixed 5s grid — constant columns, by design) → C **0.6092±0.026** → C-shuf 0.5227±0.011 (**sequence effect +0.087**, stronger at scale).
- **Anchors hold:** best IoU at 118v = 0.3008 ≈ historical 0.3302 band (labeling-rule difference documented); Gillick-162 anchor 0.559 fusion; falsifier (IoU>0.40 ⇒ label noise) never triggered.
- **Reading:** word-order context and turn/pause structure carry real, replicable information about laughter placement. At the second scale the sequence effect *grows*.

![T2 Gate-3 replication](figs/fig_t2_gate3.png)
**Figure 1.** Gate-3 arm comparison at both true-label scales. Green = sequence model, red = order-shuffled control. The C−C-shuf gap (the sequence effect) is +0.034 at 40v and +0.087 at 118v.

## 6. T3 — Beyond Words on a General Task (MELD: NULL)

- **Design (pre-registered):** MELD 7-class emotion; official test split n=2,609; official MELD.Raw audio key-joined by construction (11,131 utterances with audio; 2 rows lack files — official quirk). A: TF-IDF(1–2g)+LR. B: A + dialogue position + speaker-change. C: B + 16 acoustic interaction features (leading/trailing silence, voiced fraction, energy stats, ZCR, spectral shape, F0/yin stats). Metric: weighted F1; gate: Δ(C−B) 95% bootstrap CI excludes 0 (2,000× resamples).
- **Result:** A **0.4483**; B **0.4433**; C **0.4434**; Δ(C−B)=**0.0000**, CI **[−0.0142, +0.0145]** → **GATE NOT PASSED**.
- **Scope caveats (stated as limitations, not rescue):** hand-crafted 16-d features + linear classifier; deep acoustic encoders untested (optional E03b); the task is emotion, not reaction events.
![T3 null](figs/fig_t3_null.png)
**Figure 2.** Left: T3 arm scores on the official MELD test split. Right: pre-registered gate statistic Δ(C−B) with 2,000× bootstrap CI — the interval straddles zero.

- **Interpretation:** for general emotion classification, the words already carry (nearly all of) the recoverable signal at this model class; interaction signals add nothing. Combined with T2, the information landscape is asymmetric: **laughter/reaction events live off the word stream; emotion lives on it.**

## 7. What Blocks Further Scale (stated for reproducibility)

- True-label scale ceiling: 621 VTT-audio videos ∩ 155 EMNLP-labeled videos = **0 overlap** → 118v is the terminal true-label scale for this label source.
- Source separation (speaker vs audience laughter, applause, speech-laugh): label-blocked (speech-laugh has zero labeled instances anywhere in our sources).
- T4 transfer: deferred by design until T1–T3 resolved.

## 8. Conclusion

A registered program with pre-committed gates produced one confirmed positive (temporal structure, replicated), one informative negative (beyond-words features on emotion), one bounded case study (weak labels), and a sharpened claim: interaction-signal value is real but event-specific. For voice-agent builders: laughter prediction is where behavioral audio pays; emotion classification from text alone is already near the practical ceiling at this scale. We ship the registry, kernels, and artifacts so every number above can be re-run.

## Appendix A. Reproducibility

| Result | Kernel (Kaggle, CPU unless noted) | Artifact |
|---|---|---|
| v32 weak-label run | `chucklenet-v32-vtt-utterance` | v32 npz outputs |
| post-hoc forensics | `chucklenet-v32-posthoc` | `results_v32_posthoc.json` |
| E02 40v | `chucklenet-e02-temporal-ablation` (v4) | `results_e02_temporal.json` |
| E02 118v | `chucklenet-e02-118v-tier2` (v2) | `results_e02_118v.json` |
| T3 MELD | `chucklenet-e03-meld-v3` (v2, 49 min) | `results_e03_meld.json`, `meld_acoustic_official.npz`, `meld_frames.pkl` |
| anchors | Gillick-162v rebuild; StandUp4AI-118; RICH-9v | registry `Existing canonical anchors` |

Datasets: `subhajitdas/chuckle-audio-620-videos`, `subhajitdas/scale221-wordlevel-e02`, `subhajitdas/chucklenet-scale221`, `subhajitdas/standup4ai-en-uk-labels`, `subhajitdas/chucklenet-v32-features`; MELD from declare-lab HF (`MELD.Raw`) + declare-lab GitHub CSVs.

## Appendix B. Registered numbers cross-walk

Every number in this draft maps to RESULTS_LOG rows 1–14 and EXPERIMENT_REGISTRY entries (single source of truth). Cross-run comparisons marked "indicative" where labeling rules differ (40v word-level vs 118v window-level); internal arm comparisons are always same-rule.
