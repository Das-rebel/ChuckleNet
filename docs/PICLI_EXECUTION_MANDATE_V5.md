# ChuckleNet — Pi CLI Execution Mandate V5

**Status: CANONICAL EXECUTION CONTROL PLANE**  
**Date:** 2026-09-16  
**Supersedes for execution:** `PICLI_EXECUTION_MANDATE_V4.md`  
**Purpose:** Convert the latest empirical evidence into the smallest, highest-information research and commercial actions.

---

# 0. Governing question

> **Can machines extract, learn, and model useful information from how humans interact that is not contained in the literal words they use?**

Formal test:

> **Do non-semantic interaction signals provide incremental, reproducible information about interaction events/state beyond transcript semantics and context?**

The project is **audio-first**, eventually multimodal. It does not compete in text understanding.

Laughter is the first laboratory event because it is observable, temporally localized and socially structured.

---

# 1. Latest evidence changes the priority

The September 14 canonical paper introduced a material result that now deserves attack before more architecture is built:

- weak-label 620-video detector: IoU-F1@0.2 = **0.2290**, AP = **0.142**; treat as weak-label/label-ceiling evidence, not product quality;
- human-labeled temporal study: at 40 videos, sequence model ≈ **0.3460** vs order-shuffled ≈ **0.3125**;
- at 118 videos, sequence model ≈ **0.6092** vs order-shuffled ≈ **0.5227**;
- temporal effect therefore rises from about **+0.034 to +0.087** as data increases;
- MELD beyond-words test was **null**: Δ = **0.0000**, 95% bootstrap CI ≈ **[-0.0142, +0.0145]**.

These are now **hypothesis evidence**, not final proof. The temporal effect is the highest-value scientific lead. The MELD null tells us not to make a generic "audio improves emotion recognition" claim.

Do not revert to historical ~0.95–0.98 headlines.

---

## Kernel execution status (V5 update)

**v25** (just pushed): Full 620-video WavLM fine-tuning pipeline.
- time_limit: 36,000s (~10h) on Tesla T4 GPU
- Feature extraction: 620 videos × ~11s/video ≈ 1.9h via audioread + WavLM batched (MAX_BATCH=32)
- Training: 15 epochs × ~22min × 3 neg ratio ≈ 5.5h
- Total ETA: ~7.4h (within 9h limit, below 36ks cap)
- Dataset: chuckle-vtt-labels (624 VTT files, 620 matched) + chuckle-audio-620-videos (617 m4a files)
- Segments: 121,928 utterances, 1,965 positives (1.6%)
- WavLM: microsoft/wavlm-base, 13s load, 0 missing keys
- Features: mean-pooled last_hidden_state (768-dim) per utterance

**v24** (previous run): Processed 80/620 videos in 904s before external cancellation. WavLM pipeline confirmed functional.

**Critical infrastructure milestone**: End-to-end WavLM fine-tuning on full 620-video dataset is now running as a single kernel. This will produce the first properly trained 620-video WavLM detector, replacing the weak-label v32 evidence anchor.

---

# 2. New priority order

**P0 — evidence archaeology / reproducibility**  
**P1 — strengthen the temporal finding**  
**P2 — prove information beyond words on an event/state task where the claim is actually applicable**  
**P3 — commercial discovery + design partners in parallel**  
**P4 — transfer, then multimodality**

Do not spend material effort on P4 while P1/P2 are unresolved.

---

# 3. P0 — repository + experiment audit

Before implementing a new model, inspect the latest canonical paper and all supporting artifacts.

Find the exact code/config/result artifact behind:

1. 40-video temporal experiment;
2. 118-video temporal experiment;
3. order-shuffled control;
4. weak-label 620-video v32 result (v25 will replace this with trained-WavLM result);
5. Gillick-162 OOF result;
6. MELD null result.

For each, record:

`code path | config | dataset | labels | split | sample unit | feature set | model | seed | threshold | metric | artifact | timestamp`

Check that reported numbers can be regenerated from the saved artifacts.

**Do not rewrite results while auditing them.**

Output:

`docs/CURRENT_EVIDENCE_AUDIT_2026-09-16.md`

**V5 note on P0 progress**: The v25 kernel (kaggle.com/code/subhajitdas/chuckle-e2e-v25) is the current execution of the WavLM fine-tuning on the full 620-video dataset. Its outputs (best_model.pt, history.json, val_predictions.npz, hf_model/) will become the canonical artifact for the trained 620-video detector result. Monitor completion and extract the exact metrics.

Exit condition: all six results have traceable artifacts or explicit missing-artifact blockers.

---

# 4. P1 — temporal effect validation is now the highest-information experiment

## Question

> **Does temporal order carry genuine interaction information, rather than a model/data construction artifact?**

The existing +0.034/+0.087 sequence-vs-shuffled finding is promising. It is not yet strong enough to headline as a scientific discovery.

## Required checks

### A. Paired evaluation

Use the **same held-out examples** for sequence and shuffled conditions. Produce paired per-video scores.

Report:
- mean difference;
- median difference;
- bootstrap CI;
- per-video distribution;
- number of videos improved / worsened / unchanged.

### B. Repeat with multiple fixed seeds

Use at least 3 seeds unless compute makes this unreasonable. If 3 seeds are too expensive, justify 2 and state the limitation.

The question is stability, not leaderboard optimization.

### C. Temporal permutation controls

At minimum compare:

1. true order;
2. full random order;
3. local-window shuffle preserving broad sequence location;
4. reversed order where meaningful.

The goal is to determine whether the gain depends on meaningful order or merely sequence statistics.

### D. Leakage/source controls

Verify:
- no overlapping windows across train/test;
- no same-video leakage;
- speaker/video grouping as applicable;
- preprocessing does not encode target timing.

### E. Feature ablations

Run only the minimum:

- acoustic-only;
- acoustic + pause/timing;
- acoustic + turn/preceding-event features;
- sequence model;
- sequence model with temporal order destroyed.

Do **not** architecture-search multiple sequence models yet.

### F. Null/negative controls

Where existing data allows:
- matched silence/pause;
- applause/cheering;
- speech without laughter;
- performer laughter vs audience laughter;
- speech-laugh.

## P1 decision gate

Classify:

**STRONGER SUPPORTED** — temporal effect remains directionally stable, with a credible paired CI and no obvious leakage/shortcut explanation.

**PARTIAL** — effect exists but is heavily dataset/feature dependent.

**NOT SUPPORTED** — effect collapses under stronger controls.

If partial/not supported, narrow the thesis. Do not add model complexity as a reflex.

---

# 5. P2 — replace the failed generic MELD test with a better test of the thesis

The MELD null should be preserved. Do not keep optimizing it in search of a positive number.

The next "beyond words" experiment must use a target where non-semantic interaction can plausibly contain information that words alone cannot express.

Preferred target hierarchy:

### Level A — event prediction

Predict a future observable interaction event from preceding interaction context:

- audience reaction onset;
- listener back-channel;
- interruption;
- turn completion;
- response latency;
- speech-laugh/reaction onset.

This is preferred because the target itself is temporally observable.

### Level B — interaction-state transition

Predict a labeled transition such as:

`engaged → disengaged`  
`hesitant → committed`  
`question → resolved`

Only use labels that exist and can be independently justified.

### Level C — downstream intent transition

Only where lawful data exists:

`information-seeking → active consideration`  
`objection → willingness to continue`  
`general service → product enquiry`

Do not invent customer-intent labels from acoustic heuristics.

## P2 model comparison

A = transcript only  
B = transcript + permitted context  
C = A/B + explicit interaction signals

Primary measurement:

`Δ = C − B`

Require:
- stable cross-validation;
- speaker/person grouping;
- paired/bootstrap uncertainty;
- calibration;
- latency/compute cost.

The result matters more than absolute benchmark score.

## P2 gate

Proceed to serious commercial productization only if Δ is reproducible and meaningful for at least one real task.

A null result is a valid outcome and should narrow the business thesis.

---

# 6. P3 — commercial discovery runs now, regardless of research gate status

The product hypothesis is:

> **A real-time interaction-signal layer can expose useful non-semantic information to voice AI systems without replacing ASR or the customer's existing intent/policy engine.**

Potential outputs:

- reaction/laughter event;
- response latency;
- interruption/overlap;
- turn completion;
- hesitation proxy;
- engagement-change proxy;
- attention/reaction change;
- interest-shift signal.

Avoid the product label **emotion AI**.

## Design partner A

Voice AI / TTS / speech-to-speech / conversational platform.

Desired test:

`audio stream → interaction signal → better turn timing / interruption / reaction handling`

## Design partner B

High-volume conversation operator: customer support, sales, servicing, collections or similar.

Desired test:

`conversation → interaction signals → better intervention/intent-transition timing`

Do not begin with credit-risk inference.

## Design-partner definition

Counts only if there is:

- named technical owner;
- named business owner;
- concrete use case;
- agreed evaluation metric;
- realistic sandbox/retrospective access;
- willingness to execute a test.

---

# 7. Business scorecard

### First discovery gate

**20 qualified conversations**.

Track only:
- repeated problem;
- current workaround;
- missing signal;
- KPI;
- data accessibility;
- integration effort;
- budget/economic owner;
- objection.

### Design-partner gate

**2 serious design partners**.

### Pilot gate

At least **1 retrospective/sandbox evaluation** with:

`baseline → interaction-signal layer → measurable delta`

### Commercial proof

At least one of:

- paid pilot;
- commercial LOI;
- production-adjacent repeated usage;
- buyer-accepted incremental KPI impact.

---

# 8. P4 — transfer

Only after P1/P2 yield meaningful evidence.

Minimum progression:

`stand-up → conversational speech → voice-agent/customer-service`

Use the smallest lawful datasets available.

Primary question:

> **Does the learned interaction representation retain incremental value after domain shift?**

Do not optimize for identical F1 across domains.

---

# 9. P5 — visual expansion

Only after a measured audio/temporal limitation gives a reason to add vision.

Candidate visual signals:

- facial activation;
- smile dynamics;
- head movement;
- gaze/orientation proxy;
- gesture/body movement;
- speaker/listener attribution.

Test:

`audio → video → audio+video`

The contribution is the **incremental information**, not the number of modalities.

---

# 10. Funding operating rule

Start investor relationship-building immediately.

Do not pitch a finished multimodal platform.

Current narrative:

> **AI systems understand what people say. ChuckleNet investigates the information carried by how people react, hesitate, interrupt and coordinate in time — information that can disappear from the transcript.**

For a formal pre-seed process, target the first convergence point:

- P1 temporal evidence strengthened;
- at least one serious design partner;
- concrete P2 test underway or early evidence;
- credible product/API architecture.

Do not wait for all research questions to be solved.

---

# 11. Resource allocation

For the current resource-constrained stage:

**45% research/validation**  
**25% data/reproducibility**  
**20% design-partner discovery**  
**10% investor preparation/relationships**

No large multimodal engineering allocation yet.

---

# 12. Mandatory weekly report

Pi CLI must finish every cycle with:

### Research
`hypothesis | experiment | result | uncertainty | interpretation`

### Evidence
`new canonical artifact | provenance | reproducibility`

### Commercial
`qualified conversations | partner status | KPI | objection`

### Capital
`investor conversations | objection | evidence requested`

### Decision
`CONTINUE / NARROW / PIVOT / STOP`

### One highest-information next action
Exactly one.

---

# 13. Repository preservation

Never delete historical code, notebooks, checkpoints, result artifacts or previous plans because a thesis changed.

For every proposed deletion, first demonstrate:

`duplicate / invalid artifact / confirmed retention-safe`

Otherwise preserve it.

Canonical strategy documents may supersede old documents, but **historical evidence remains part of the project record**.

---

# 14. Immediate Pi CLI command (V5 update)

Read:

- `docs/RESEARCH_VISION_V2.md`
- `docs/RESEARCH_LINEAGE.md`
- `docs/SUPPORTING_RESEARCH_AND_HYPOTHESES_V2.md`
- `docs/INTERACTION_SIGNAL_RESEARCH_PROGRAM.md`
- `docs/EXPERIMENT_REGISTRY.md`
- `docs/DECISION_GRAPH_V2.md`
- `docs/COMMERCIALIZATION_INTERACTION_SIGNAL_API.md`
- `docs/PICLI_EXECUTION_MANDATE_V4.md`
- the latest canonical paper and supporting results registry
- **kernel: kaggle.com/code/subhajitdas/chuckle-e2e-v25** (running; monitor for completion)

Then do **only**:

1. Monitor v25 completion; on success, extract metrics and update the 620-video detector evidence anchor;
2. repository archaeology for the six current evidence anchors;
3. produce `docs/CURRENT_EVIDENCE_AUDIT_2026-09-16.md`;
4. identify exact reusable code/artifacts for P1;
5. design P1 as a reproducible paired/counterfactual test;
6. execute P1 if all required assets exist;
7. write the P1 decision memo;
8. stop and report before starting P2.

Do not create a new model family until the P1 decision justifies it.

The goal is not to make ChuckleNet look advanced.

The goal is to **find out whether the central proposition is true, where it is true, and whether that truth is useful enough to matter.**

---

# 15. Kernel execution log (v24)

```
Status: CANCEL_ACKNOWLEDGED at 80/620 videos (904s elapsed)
VTT: 620 videos, 243,501 utts, 2,816 laughs (1.2%) ✓
WavLM: loaded in 13s, missing=0, unexpected=0 ✓
Segments: 121,928, pos=1,965 (1.6%) ✓
Feature extraction rate: ~11.3s/video via audioread
Path (GPU container): VTT=/kaggle/input/chuckle-vtt-labels, AUDIO=/kaggle/input/chuckle-audio-620-videos/vtt_audio_local
```
