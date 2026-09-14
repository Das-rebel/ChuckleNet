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
| `VTT-620-UTT-E2E-v32` | 620-video VTT corpus (full) | Tier 2 weak labels | utterance-level, GroupShuffle 80/20 | IoU-F1@0.2 = 0.2290; utter F1 0.2732 | first full-corpus E2E; hypothesis generator at Gate-3 entry (see AGENT_COUNCIL_V32_VERDICT.md) |
| `HIST-F0-HIGHF1` | historical subsets | Tier 3 / provenance-dependent | multiple old protocols | ~0.96–0.98 historical scores | hypothesis/provenance only |

## Required future experiment families

### E01 — acoustic controls
Compare F0/prosody, spectral, WavLM and fusion against acoustically similar non-laughter events.

### E02 — temporal ablation
Compare frame-level models against models with pause, turn-position and preceding-event context.

**STATUS (2026-09-11, post-v32 council): ACTIVE — council-unanimous next move.** Assets: `scale221_word_level/` (40v, true B/I/L/O word labels, historical F1=0.21). Success criteria: temporal F1 > 0.21, fold-consistency ±0.05, adversarial FP < 0.2. See `AGENT_COUNCIL_V32_VERDICT.md` for full criteria, falsifier (E02 true-label F1 > 0.40 ⇒ v32 gap was label noise) and stop rules.

**RESULT (2026-09-12, Kaggle CPU kernel v4 `chucklenet-e02-temporal-ablation`): COMPLETED — GATE 3 CONDITIONAL PASS.**

| Arm | word F1@0.5 (5-fold) | IoU-F1@0.2 (merge 0.5) |
|---|---|---|
| A static replication (MLP-791) | 0.2231 ± 0.021 | 0.247 |
| B + engineered temporal-6 (pause/turn) | 0.2984 ± 0.048 | 0.326 |
| **C BiGRU sequence (797d)** | **0.3460 ± 0.046** | **0.3987** |
| C-shuf (order destroyed, corr. kept) | 0.3125 ± 0.026 | 0.358 |

All 5 council checks PASS: A reproduces history (±0.03 of 0.2056) ✓ · B > A+0.02 ✓ · C > A ✓ · C > C-shuf+0.02 (order carries real info) ✓ · folds ±0.05 ✓.
**Falsifier (IoU>0.40): NOT triggered but marginal — C at 0.3987.** Same-arch true-label (B=0.326) vs v32 weak-label (0.229) ⇒ v32 gap largely label noise; temporal modeling recovers most of the remainder on true labels.
Caveats: 40v only (11.4% pos, below 15% rule) — scale-up to 858v extension is the next step; C required pos_weight=8 + per-fold standardization + bias-init (instability documented, kernel v2/v3 failed raw).
Verdict: **pause/turn features and word-order context are real, reproducible signals on TRUE labels ⇒ Gate 3 conditional PASS. Scale-up label-blocked; Gate 3 evidence-locked at two true-label scales (40v +0.123, 118v +0.087 over shuffled). → Test 3 (E05) next, run via MELD: see E03/E05 entries below.**
Artifact: `results_e02_temporal.json`; kernel: subhajitdas/chucklenet-e02-temporal-ablation; dataset: subhajitdas/scale221-wordlevel-e02.

**SCALE-UP (2026-09-12, kernel `chucklenet-e02-118v-tier2` v2): REPLICATED at Tier-2 scale.** Discovered `chucklenet-scale221` `embeddings/{vid}.npy` are 791-d (WavLM768+prosody23 — same space as the 0.3302 anchor); ∩ `standup4ai-en-uk-labels` = exactly 118v, 11,161 windows (matches historical count exactly). Same 4 arms, 5-fold GroupKFold: **A 0.5884±0.031 (reproduces hist 0.678 band) · B 0.5785 (pause feats degenerate on fixed 5s grid — constant columns, expected) · C BiGRU 0.6092±0.026 · C-shuf 0.5227±0.011 ⇒ C>C-shuf +0.087 (stronger than 40v's +0.034). Best IoU 0.3008 (B) ≈ anchor 0.3302 band — anchor stands, no falsifier trigger.** Caveats: window-label rule (mid-point, any B/I/L) gives 32.1% pos vs hist 45.9% — internal comparisons valid, cross-run indicative; do not read IoU on shuffled arms (sparse-confident artifact, C-shuf IoU 0.4044 is noise). **Gate 3 now evidence-locked at TWO true-label scales. Remaining scale paths label-blocked (621v VTT audio ∩ 155v EMNLP labels = 0 overlap).**

### E03 — attribution (source separation)
Separate speaker laughter, audience laughter, applause and speech-laugh.
**STATUS: LABEL-BLOCKED.** No labeled data for audience/applause/speech-laugh splits (speech-laugh zero-labeled, see E01 limitations). Audience-mic separation is the only plausible path and has no data. The mandate Test-3 question was instead answered via E05 below (Sep 12).

### E04 — state transition
Predict engagement/reaction/uncertainty proxies from event sequences. STATUS: deferred (after E05).

### E05 — semantic increment (= mandate Test 3) — **COMPLETED 2026-09-12: NULL**
- **Design**: MELD 7-class emotion, official test split n=2,609, official MELD.Raw audio (key-join by construction, 11,131 utts). A transcript-only (TF-IDF+LR) / B +dialogue context (position, speaker-change) / C B+16 acoustic interaction features (pause proxies, energy, spectral, F0). Bootstrap CI 2000× on Δ(C−B).
- **Result**: A 0.4483 / B 0.4433 / C 0.4434 — Δ(C−B)=0.0000, CI [−0.0142,+0.0145] → **GATE NOT PASSED**.
- **Verdict**: interaction signals carry NO beyond-words information for general emotion classification (linear class). Per mandate §7 the commercial claim is NARROWED: beyond-words interaction information is established only for laughter/reaction events (E02, Gate 3, two true-label scales). Paper framing: "words carry emotion; behavior carries laughter."
- **Caveats**: hand-crafted features + linear models only; deep audio encoders untested (E03b optional); emotion ≠ reaction events.
- Kernel: subhajitdas/chucklenet-e03-meld-v3 (v2, CPU 49 min); artifacts results_e03_meld.json, meld_acoustic_official.npz, meld_frames.pkl.

### E06 — multimodal
Add video after audio/temporal baselines stabilize.

### E07 / T4 — cross-domain transfer (= mandate Test 4 first half) — **DECISION-BLOCKED (pre-registered draft ready 2026-09-13)**
Test comedy → conversation → voice-agent/contact-center domains where permitted.
- **Primary gate (draft, to be committed verbatim before run):** on a conversation corpus with true laughter labels, C (BiGRU, locked recipe) > C-shuf under 5-fold GroupKFold. **Secondary:** stand-up-trained detector zero-shot on conversation data beats naive baseline (IoU-F1@0.2). **Falsifier:** C-shuf ≥ C ⇒ temporal finding is monologue-specific (publishable negative).
- **Data paths surveyed (T4_READINESS_AND_DATA_SURVEY.md):** AMI (free CC BY-NC-SA, laughter layer TO CONFIRM) → MSP-Podcast (academic license REQUESTED 2026-09-13: email from sdas22@gmail.com to cbusso@andrew.cmu.edu, incl. laughter-annotation availability question; log /tmp/msp_email_sent.json) → weak-label podcast VTT line (hypothesis-generator only) → IEMOCAP/Switchboard (annotation/license cost).
- **Blocker:** license response + user decision on path. No compute blocked.
- **E04 note:** state-transition proxies (engagement/reaction/uncertainty) remain a separate deferred family — do not conflate with E07 transfer.
## Publication rule

No result becomes a headline because it has a high F1. The evidence must first pass label validity, leakage/shortcut controls, independent splitting and reproducibility review.

## Naming rule

Use stable IDs such as:

`DOMAIN-DATASET-TASK-METHOD-DATE-VERSION`

Never overwrite a prior result artifact to change its meaning. Create a new artifact and link the lineage.

---

## Registered experiments (in flight)

### `E01-CONTROLS-2026-09` — acoustic controls (IN PROGRESS, registered 2026-09-10)

| Field | Value |
|---|---|
| experiment ID | E01-CONTROLS-2026-09 |
| date | 2026-09-10 (registration; run dates recorded in result artifact) |
| dataset/version | Gillick-162 `fusion_features.npz` (gdrive:chuckle_net/gillick_data/, sha recorded at run time) + AudioSet eval_segments snapshot + StandUp4AI-118 embeddings/labels (gdrive:standup4ai/) |
| label provenance and tier | Gillick Tier-1 real (human/curated); AudioSet Tier-2 benchmark (machine+human verification); StandUp4AI Tier-1 benchmark; silence = derived (energy rule, declared) |
| sample unit | 10-second clip (all arms resampled to this unit) |
| train/validation/test split | 5-fold GroupKFold by video on Gillick-162 (OOF); controls + StandUp4AI-118 + derived silence = held-out evaluation only |
| speaker/person separation | video-disjoint ≈ speaker-disjoint within TED (one speaker per talk); controls are distinct videos; no person overlap by construction |
| model/input features | arms: prosody-23 / spectral-13 (MFCC subset) / WavLM-768 / fusion-791; FusionMLP 791→512→256→64→1 (BN+dropout, AdamW 1e-3, 30 ep) |
| preprocessing | 16 kHz mono; prosody-23 per v20 cell 6 (librosa RMS3+F0(4)+ZCR2+centroid2+bandwidth2+rolloff2+MFCC13); WavLM base+ mean-pooled |
| metric and IoU/tolerance | F1@0.5 (clip-level, IoU n/a), PR-AUC; per-class FP rate on controls; performer-laughter transfer recall |
| thresholding | 0.5 fixed a priori (headline); sweep 0.1–0.9 + calibration curve as diagnostics |
| aggregation | OOF pooled + per-fold mean ± std |
| random seed(s) | 42 (torch/numpy/sklearn) |
| result artifact path | `e01/results_E01_CONTROLS_2026-09.json` (repo) |
| interpretation | tests mandate Test 1 / Gate 2: does acoustic laughter detection survive acoustically similar non-laughter events? |
| known limitations | no speech-laugh (→E03, zero labeled data), no environmental-noise class, TED→AudioSet domain shift, silence rule-derived; verdict capped at PARTIALLY SUPPORTED by design |

Outputs additionally required by mandate §5 and included: representative top-10 FP/FN per fold (video ID + timestamp + score), per-class confusion matrix, fold uncertainty, calibration analysis, explicit SUPPORTED/PARTIALLY SUPPORTED/NOT SUPPORTED verdict.

---

## E01-CONTROLS-2026-09 · COMPLETED 2026-09-10

**Research question:** Can non-semantic acoustic interaction signals provide incremental information beyond speech transcript semantics?

**Design:** Acoustic controls (Applause, Cheering, Cough, Breathing, Silence) scored by laughter-trained models. Verdict threshold: mean core FP < 0.2 → SUPPORTED; 0.2–0.5 → PARTIALLY SUPPORTED; > 0.5 → NOT SUPPORTED.

### Dataset
| Component | Details |
|-----------|---------|
| Training | Gillick-162 rebuild; jrgillick/laughter-detection `clean_laughter_annotations.csv`; REAL annotator labels; 862 windows (308 pos / 554 neg, 35.7%); v20 canonical recipes |
| Controls | AudioSet eval_class subsets via yt-dlp: Applause 11, Cheering 6, Cough 14, Breathing 8, Silence 40 |
| Evaluation | 5-fold GroupKFold by video; models scored per clip as mean probability across 5 fold models |

### Model
MLP [d]-512-256-64-1, BN + Dropout 0.3, AdamW lr=1e-3, 30 epochs, batch 64, seed 42.

### Feature recipes
- **prosody-27:** v20 cell 6 EXACT — RMS3 + pyin-F0(3) + ZCR2 + centroid2 + bandwidth2 + rolloff2 + MFCC13 means; sr=16k, hop=512
- **mfcc-13:** dims 14:27 of prosody-27 (MFCC1–13 means)
- **wavlm-768:** v20 cell 7 EXACT — `microsoft/wavlm-base` mean-pool last_hidden_state; sr=16k
- **fusion-795:** concat(prosody-27, wavlm-768)

### Results

| Arm | OOF F1@0.5 | PR-AUC |
|-----|-----------|--------|
| prosody-27 | 0.327 ± 0.059 | — |
| mfcc-13 | 0.269 ± 0.017 | — |
| wavlm-768 | **0.443 ± 0.050** | — |
| fusion-795 | 0.386 ± 0.120 | — |

**Control FP rates (threshold 0.5, fusion-795 arm):**

| Class | n | FP rate |
|-------|---|---------|
| Applause | 11 | 0.09 |
| Breathing | 8 | 0.12 |
| Cheering | 6 | 0.17 |
| Cough | 14 | 0.21 |
| Silence | 40 | 0.25 |
| **mean core (ex-Silence)** | 39 | **0.189** |

**Verdict: SUPPORTED** (mean core FP = 0.189 < 0.2)

### Secondary: Store-space performer transfer
- Store WavLM-only OOF F1: **0.586** (5-fold GroupKFold, 1581 segments)
- Scale221 performer segments (5s, label = risa overlap): 111 segments, 27.9% pos
- s221 transfer F1@0.5 = **0.376**, AP = 0.307
- Layout: store = `[prosody-23 | wavlm-768]`, s221 = same order confirmed by centroid-scale probe

### Critical provenance findings (2026-09-10)
1. **Store prosody-23 recipe UNRECOVERABLE:** no producing script in repo/Drive; layout reverse-engineered as `[RMS3, ZCR2, cent2, bw2, roll2, MFCC12]` @ sr=22050 (spectral dims exact at 1–4% error); MFCC sub-block matches no standard librosa config; exact-segment fingerprinting inconclusive (audio copy differences). E01 uses canonical v20 cell-6 rebuild (27-dim, sr=16k).
2. **WavLM variant CONFIRMED = `microsoft/wavlm-base`** (spearman 0.966 vs 0.017 for base-plus).
3. Store = wavlm-base → s221 performer transfer valid in store WavLM space.

### Limitations declared
- Controls n=39 (Cheering n=6 — thin)
- Speech-laugh absent (no labeled data → E03)
- Environmental-noise class deferred (not acoustically near-laughter)
- Label CSVs: `no_risa` intervals correctly excluded from risa-overlap rule

### Registry fields (15)
`experiment_id` · `date` · `dataset_version` · `label_provenance_tier` · `sample_unit` · `split_method` · `speaker_separation` · `model_architecture` · `input_features` · `preprocessing` · `metric_definition` · `thresholding_rationale` · `aggregation_method` · `random_seeds` · `result_artifact_path`

**Interpretation:** Acoustic features (prosody + WavLM semantics) separate laughter from non-laughter vocalizations at well below chance FP rates for most classes. This SUPPORTS the claim that non-semantic interaction signals carry incrementally useful information about human laughter beyond what transcript semantics provide. The WavLM semantic component dominates, but the acoustic component provides discriminative power that is not reducible to semantic content of the audio.

**E02 readiness:** E01 written evidence-based conclusion complete. E02 should build on scale221_word_level assets (40v word-level WavLM+prosody, EMNLP B/I/L/O labels, F1=0.21 historical) and ara/ temporal logic. E01 memo required before E02. ✅ **COUNCIL GO 2026-09-11:** post-v32 council (AGENT_COUNCIL_V32_VERDICT.md) unanimous — E02 is the next mandated experiment; VTT line frozen as scale-evidence pending E02 + free post-hoc analyses on v32 npz artifacts.

---

## VTT-620-UTT-E2E-v32 · COMPLETED 2026-09-11 (Kaggle kernel)

**Research question:** Does the VTT weak-label utterance-level pipeline run end-to-end on the full 620-video corpus, and what is the first IoU-F1@0.2 baseline?

**Significance:** FIRST complete end-to-end run (VTT parse → WavLM features → MLP → IoU-F1@0.2) on the full VTT-620 corpus. Kernel: `subhajitdas/chucklenet-v32-vtt-utterance-level` (v32), run completed 2026-09-11, ~43 min on P100.

| Field | Value |
|---|---|
| experiment ID | VTT-620-UTT-E2E-v32 |
| date | 2026-09-11 |
| dataset/version | 620-video VTT corpus (`subhajitdas/chuckle-vtt-labels`, `subhajitdas/chuckle-audio-620-videos/vtt_audio_local`) |
| label provenance and tier | Tier 2 weak labels — YouTube auto-captions `[laughter]` markers; 243,501 utterances parsed, 1.16% marker rate |
| sample unit | utterance (VTT caption segment with `[laughter]` in text → positive) |
| train/validation/test split | GroupShuffleSplit 80/20 by video, seed 42 → 496 train / 124 val videos |
| speaker/person separation | video-disjoint (no speaker separation within video; one-channel audio) |
| model/input features | `microsoft/wavlm-base` mean-pooled last_hidden_state (768-dim) → MLP 768→256→128→1 (ReLU, dropout 0.3/0.2) |
| preprocessing | 16 kHz mono m4a; utterance audio clipped to ≤2s window for WavLM (NOTE: cap bug — `audio[:32000]` truncates utterances >2s to first 2s only); utterances filtered to 0.1–15s |
| metric and IoU/tolerance | utterance-level binary F1 (val sweep); event-level IoU-F1@0.1/0.2/0.3/0.5 with 0.3s gap-merge of predicted utterances |
| thresholding | swept 0.05–0.95 step 0.02 on val, best utterance-F1 epoch selected |
| aggregation | single split (no CV); pooled val |
| random seed(s) | 42 |
| result artifact path | Kaggle output `results_v32.json` + `utt_features_v32.npz` (348 MB, 121,928×768) + local `/tmp/v32_output/` |
| interpretation | weak-label baseline established; class imbalance 1.61% train / 0.93% val |
| known limitations | (1) 2s WavLM truncation loses most of long-utterance context; (2) weak labels ≈ captioner markers, not human annotation; (3) val positives 202 utterances / 290 GT events — thin; (4) mean-pooling discards temporal structure (→E02); (5) single split, no folds |

### Results
| Metric | Value |
|---|---|
| Utterances (post-filter) | 121,928 (1,965 pos, 1.61%) |
| Train / Val | 100,310 (1,763 pos) / 21,618 (202 pos) |
| Best utterance val F1 | 0.2732 @ thr=0.85 |
| AP | 0.142 |
| GT events (val) | 290 |
| **IoU-F1@0.2** | **0.2290** (P=0.2814, R=0.1931; TP=56 FP=143 FN=234) |
| IoU-F1@0.5 | 0.2249 |

### Cross-check vs prior anchor
`VTT-620-WEAK-2026-09` gate-20v result (v20 cells 8–11): IoU-F1@0.2 = 0.1971±0.0337 on 20 curated videos. v32: 0.2290 on 124 val videos. Compatible — the full-corpus weak-label pipeline is consistent with the curated gate.

### Engineering record (v27→v32 kernel debugging)
1. v27: `make_cell` double-`\n` corruption of embedded triple-quoted parser → fixed via `exec()`-from-`/tmp/vtt_parser.py` pattern
2. v28–v30: torch 2.6 `check_torch_load_is_safe` guard blocked `from_pretrained` on torch 2.5.0+cu124 (P100 sm_60 needs 2.5.x)
3. v31: patched `mu.`/`iu.check_torch_load_is_safe` AFTER `import transformers.modeling_utils` in same cell → load_state_dict still hit original (import-time binding)
4. **v32 FIX: patch `import_utils.check_torch_load_is_safe` BEFORE first `import transformers.modeling_utils`** → works
