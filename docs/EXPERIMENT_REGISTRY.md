# ChuckleNet Experiment Registry

**Status: CANONICAL — 2026-09-10**

This registry is the control plane for future experiments. A result is not publication-ready until its provenance is recorded here or in a linked machine-readable result artifact.

## Required fields

Every experiment must record:

- experiment ID
- date
- dataset/version
- label provenance and tier
- sample unit
- train/validation/test split
- speaker/person separation
- model/input features
- preprocessing
- metric and IoU/tolerance
- thresholding
- aggregation method
- random seed(s)
- result artifact path
- interpretation
- known limitations

## Existing canonical anchors

| ID | Dataset | Label tier | Protocol | Result | Role |
|---|---|---|---|---|---|
| `GILLICK-162-OOF-2026-09` | Gillick/AudioSet-derived | Tier 1 real labels | 5-fold GroupKFold by video, OOF | fusion F1 0.559; WavLM 0.548; prosody 0.537 | primary acoustic anchor |
| `STANDUP4AI-118-I20-2026-09` | StandUp4AI | Tier 1 benchmark labels | video-grouped evaluation | IoU-F1@0.2 ≈ 0.3302 | primary stand-up benchmark anchor |
| `VTT-620-WEAK-2026-09` | 620/621-video VTT corpus | Tier 2 weak labels | corpus/marker analysis | ~1.16% positive across 243,501 utterances; 174/620 videos with markers | scale/weak-label study |
| `HIST-F0-HIGHF1` | historical subsets | Tier 3 / provenance-dependent | multiple old protocols | ~0.96–0.98 historical scores | hypothesis/provenance only |

## Required future experiment families

### E01 — acoustic controls
Compare F0/prosody, spectral, WavLM and fusion against acoustically similar non-laughter events.

### E02 — temporal ablation
Compare frame-level models against models with pause, turn-position and preceding-event context.

### E02 Results

#### P1 Validation — 2026-09-18
**ID:** `P1-TEMPORAL-PAIRED-118V-2026-09-18`
**Dataset:** 118-video human-verified EMNLP B/I/L/O/U label intersection (11,161 windows, 2,712 positives)
**Protocol:** 5-fold GroupKFold, 3 seeds (42/43/44), BiGRU 128 hidden, pos_weight=8, AdamW 5e-4, bias −2.0, gradient clip 1.0, 40 epochs, patience 8
**Conditions:** true order · full random within-video · local 25 s block shuffle · reversed
**Result:** Primary gate PASS — true vs random ΔF1 +0.0769, 95% CI [+0.0617, +0.0917]; local-shuffle and reverse controls do not separate (CI spans zero). **Verdict PARTIAL.**
**Interpretation:** Sequence context carries reproducible predictive information. Full randomization destroys it. Fine local order and forward direction do not add measurable value at 5 s resolution. Narrow claim: broad sequence/context structure, not precise temporal ordering.
**Artifacts:** `results/p1/p1_temporal_118v_results.json`, `results/p1/p1_temporal_118v_observations.json.gz`, `training/p1_temporal_validate.py`
**Next:** Event-timing ablation (preceding context length, onset/offset error, reaction latency, causal/prefix eval) — more informative than another architecture search.

### E03 — attribution
Separate speaker laughter, audience laughter, applause and speech-laugh.

### E04 — state transition
Predict engagement/reaction/uncertainty proxies from event sequences.

### E05 — semantic increment
Compare transcript-only vs transcript+context vs transcript+context+interaction signals.

### E06 — multimodal
Add video after audio/temporal baselines stabilize.

### E07 — cross-domain
Test comedy → conversation → voice-agent/contact-center domains where permitted.

## Publication rule

No result becomes a headline because it has a high F1. The evidence must first pass label validity, leakage/shortcut controls, independent splitting and reproducibility review.

## Naming rule

Use stable IDs such as:

`DOMAIN-DATASET-TASK-METHOD-DATE-VERSION`

Never overwrite a prior result artifact to change its meaning. Create a new artifact and link the lineage.
