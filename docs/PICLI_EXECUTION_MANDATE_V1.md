# ChuckleNet — Pi CLI Execution Mandate V1

**Status: CANONICAL EXECUTION HANDOFF**  
**Date:** 2026-09-10  
**Purpose:** Hand the day-to-day research, engineering, evidence and commercial-validation loop from ChatGPT to Pi CLI without losing project context.

---

## 0. Operating principle

Pi CLI is now the **execution engine** for ChuckleNet. Do not use effort, code volume, model complexity or number of experiments as the primary measure of progress.

Progress is measured by whether the project clears the next scientific or business gate.

The north star is defined in `docs/RESEARCH_VISION_V2.md`:

> Can non-semantic multimodal interaction signals provide incremental information about human interaction state and intent beyond speech transcript semantics?

Laughter is the entry point. It is not the product definition.

The master research sequence is in `docs/INTERACTION_SIGNAL_RESEARCH_PROGRAM.md`; provenance is controlled by `docs/EXPERIMENT_REGISTRY.md`; scientific decision logic is in `docs/DECISION_GRAPH_V2.md`; commercial hypotheses are in `docs/COMMERCIALIZATION_INTERACTION_SIGNAL_API.md`.

**Do not invent a new strategy unless current canonical documents are demonstrably insufficient.**

---

# 1. Current starting position

## 1.1 Strongest evidence available

### Real-label acoustic anchor

`GILLICK-162-OOF-2026-09`

- 162 videos
- 5-fold GroupKFold by video
- OOF evaluation
- WavLM + prosody fusion F1 = **0.559**
- WavLM-only F1 = **0.548**
- prosody-only F1 = **0.537**

Interpretation: prosody contributes, but the current evidence does **not** support the old headline that F0/prosody dominates WavLM by multiples.

### Stand-up benchmark anchor

`STANDUP4AI-118-I20-2026-09`

- honest current result: **IoU-F1@0.2 ≈ 0.3302**
- use only with exact task/metric alignment when comparing against published results.

### Scale-up weak-label study

`VTT-620-WEAK-2026-09`

- 620/621-video corpus
- sparse VTT marker labels
- approximately 1.16% positive utterances across 243,501 utterances
- 174/620 videos with markers

Interpretation: useful for data engineering and weak-label stress testing; **not equivalent to gold/manual laughter ground truth**.

### Historical high scores

`HIST-F0-HIGHF1`

The historical ~0.96–0.98 results are retained as provenance/hypothesis evidence only. Do not use them as current model performance unless they are independently reconstructed under the current label hierarchy and evaluation rules.

---

# 2. Primary objective for the next execution cycle

The immediate objective is **E01: prove whether ChuckleNet detects an interaction event rather than exploiting an acoustic or dataset shortcut.**

The experiment must be adversarial and diagnostic.

A successful E01 should answer:

> Does the signal remain useful when obvious acoustic confounds, speaker identity, recording source and simple temporal shortcuts are controlled?

A failed E01 is not a project failure. It is a valuable scientific boundary condition. Report it plainly and revise the hypothesis.

---

# 3. E01 — mandatory experiment specification

## 3.1 Required negative/control classes

At minimum evaluate against:

- ordinary speech without laughter
- silence / pause
- applause
- cheering
- audience laughter
- performer/speaker laughter
- speech-laugh / laughter embedded in speech
- cough / breath / non-speech vocalization
- obvious environmental/noise events where available

## 3.2 Required models/features

Establish a controlled ladder:

1. F0 / pitch statistics
2. energy / RMS
3. spectral features
4. MFCC or equivalent compact acoustic features
5. pause/timing features
6. WavLM
7. prosody + WavLM fusion

Do **not** add large models merely to improve a leaderboard score before the controls are understood.

## 3.3 Required split discipline

At minimum, test independence by:

- speaker/person
- comedian/source where relevant
- video/recording

Do not mix windows from the same source across train and test when this can create leakage.

## 3.4 Required metrics

Report, where appropriate:

- precision
- recall
- F1
- PR-AUC for sparse events
- onset/offset or IoU-aware metric for temporal evaluation
- confusion matrix by control class
- calibration/error analysis
- bootstrap or fold-based uncertainty intervals

Every result must include the registry fields in `docs/EXPERIMENT_REGISTRY.md`.

## 3.5 Required diagnostic outputs

Produce:

- result table
- confusion matrix
- per-class failure analysis
- false-positive audio examples or identifiers
- false-negative examples or identifiers
- speaker/source breakdown
- threshold sensitivity
- short written conclusion: **supported / partially supported / not supported**

---

# 4. Counterfactual temporal test — do not skip

Once E01 is stable, run the temporal ablation described in the master research plan.

Construct matched examples where:

1. laughter windows have their temporal relation to the preceding speech turn shifted;
2. non-laughter pauses are matched on approximate duration, F0 and energy;
3. temporal position and preceding-event context can be added or removed independently.

Compare:

- acoustic-only
- acoustic + pause
- acoustic + turn position
- text + audio
- full temporal model

The key scientific question is whether **interactional timing carries information that static acoustics do not**.

---

# 5. E02 — temporal interaction modeling

Only after E01 is defensible, build a lightweight sequence model over frame/event features.

Preferred candidate sequence models:

- TCN
- BiGRU
- lightweight Conformer
- small transformer over frame-level interaction features

Primary targets:

- reaction onset
- reaction offset
- reaction latency
- preceding-event relationship
- turn position
- event persistence
- state-change/change-point score

Success means a measurable and reproducible improvement over the best E01 static/frame baseline **under the same split and label protocol**.

---

# 6. E03 — attribution

Disambiguate:

- performer/speaker laughter
- audience/interlocutor laughter
- applause
- cheering
- speech-laugh
- other vocal/non-vocal reactions

The purpose is to move from “laughter-like sound” toward an interaction event with a producer and recipient.

---

# 7. E04 — interaction-state representation

Build an event/state representation from sequences rather than a single label.

Candidate state outputs:

- engagement increase/decrease
- hesitation
- uncertainty proxy
- interruption
- turn completion
- reaction strength
- response latency
- interest shift
- alignment/synchronization

These are **observable or operational proxies**, not diagnoses of internal psychology.

Do not claim that acoustic features prove an emotion, personality trait, deception, creditworthiness or another latent human attribute without direct validated ground truth.

---

# 8. E05 — semantic increment: flagship scientific gate

Run the core incremental-information test.

### Baselines

**A.** ASR transcript → intent/state model  
**B.** ASR transcript + available permitted context → intent/state model  
**C.** ASR transcript + permitted context + interaction signals → intent/state model

Measure the incremental value of C over B.

Where valid data exists, measure:

- intent classification delta
- intent-transition detection delta
- uncertainty-resolution delta
- reaction/turn prediction delta
- intervention-timing utility
- downstream acceptance/conversion proxy only when legitimately available and causally interpretable

Use cross-validation/bootstrap testing to establish whether the gain is stable rather than noise.

**This is the flagship test for the commercial thesis.**

If interaction signals do not add useful information beyond semantics/context, do not force the commercial thesis. Narrow or pivot the claim.

---

# 9. E06 — multimodal expansion

Add video only after audio + temporal baselines stabilize.

Candidate signals:

- facial movement / smile dynamics
- head movement
- gaze/orientation proxy
- gesture
- posture/body motion
- speaker/listener attribution

Compare:

- audio-only
- video-only
- audio + video
- audio + video + supporting text/context

The objective is not “multimodal because it sounds impressive.” The objective is to measure whether another modality contributes **incremental information**.

---

# 10. E07 — cross-domain transfer

Test representation transfer beyond stand-up comedy where legally and operationally permissible:

1. stand-up comedy
2. general conversational speech
3. voice-agent interactions
4. customer-service/contact-center data
5. multilingual Indian speech

The target is not necessarily equal absolute F1 across all domains.

The high-value question is:

> Does the interaction-signal representation retain incremental predictive value after domain shift?

---

# 11. Commercial execution must run in parallel

Do not wait for a perfect research paper before validating the buyer problem.

## 11.1 Product hypothesis

The candidate product is:

> **Interaction Signal API — real-time non-semantic features for voice and multimodal AI systems.**

The API should expose time-varying signals, not a black-box “emotion score.”

Examples:

- engagement change
- hesitation
- uncertainty proxy
- interruption
- turn completion
- reaction/laughter
- response latency
- attention shift
- frustration proxy
- interest shift
- intent transition

## 11.2 Initial buyer hypotheses

Prioritize two design-partner archetypes:

**Design Partner A — voice/AI platform**  
A TTS, speech-to-speech, conversational-agent or contact-center technology company that already has audio in production and can evaluate an additional real-time interaction signal layer.

**Design Partner B — high-volume conversation operator**  
A bank, fintech, collections, sales, servicing or customer-support operation with enough lawful/consented conversation data and a measurable operational outcome.

These are not customers yet. They are organizations willing to provide workflow access, data access or evaluation feedback under an appropriate agreement.

---

# 12. Design-partner outreach process

For each target company:

1. Identify one technical owner (speech/AI/product) and one business owner (CX, sales, collections, service or automation).
2. Lead with the problem, not the research history.
3. Offer a low-friction retrospective evaluation first.
4. Ask for a small, lawful, appropriately consented sample or sandbox integration.
5. Define one metric before integrating.
6. Convert a positive retrospective result into a limited live pilot.

Suggested first-message framing:

> We are building an interaction-signal layer for voice AI that captures information carried by timing, prosody, reaction and turn behavior that transcripts miss. We are not replacing ASR or the intent model. We are testing whether these signals improve things like turn handling, hesitation detection, intent transitions and intervention timing. We are looking for two design partners for a tightly scoped evaluation rather than a sales rollout.

Do not lead with “emotion AI.”

Do not lead with lending/credit decisions.

---

# 13. Commercial metrics / gates

Track a separate business scorecard.

## Discovery gate

Target: at least **20 qualified conversations** across voice AI, speech/TTS, contact-center and financial-services operators.

Record:

- pain severity
- current solution
- signal gap
- willingness to test
- data accessibility
- budget owner
- technical integration difficulty

## Design-partner gate

Target: **2 serious design partners** with a defined use case, named owner and agreed evaluation protocol.

A company does not count merely because someone said “interesting.”

## Pilot gate

At least one partner should provide a measurable retrospective or sandbox evaluation.

Required evidence:

- baseline system
- interaction-signal augmented system
- incremental metric
- integration effort
- latency/compute requirement
- failure modes

## Commercial proof gate

Before a serious institutional raise, aim for at least one of:

- paid pilot / LOI / commercial evaluation
- repeated usage in a production-adjacent workflow
- statistically credible incremental value with a clearly owned business KPI

---

# 14. Fundraising strategy

The company may be capable of raising a pre-seed now, but **do not optimize the research to impress investors before the core signal has been validated**.

Run two tracks in parallel:

### Track A — research de-risking

Immediate priority:

**E01 → temporal proof → E05 semantic increment**

### Track B — investor relationship building

Start now:

- create a concise 8–10 slide narrative
- build a target list of relevant pre-seed/seed investors
- take exploratory meetings
- collect objections
- avoid presenting unvalidated claims as product facts

A stronger fundraising trigger is reached when the project has:

1. defensible E01 evidence;
2. temporal value;
3. two serious design partners;
4. a credible semantic-increment result;
5. a clear product/API architecture;
6. a believable path to recurring enterprise revenue.

Do not wait for every scientific question to be solved before raising. The goal is to prove enough of the hardest claim that outside capital can accelerate the remaining uncertainty.

---

# 15. Investor story to build toward

The pitch should **not** be:

> “We built a better laughter detector.”

Nor:

> “We can infer emotion/creditworthiness from voice.”

The eventual story is:

> **AI systems understand what people say but lose information in how people react, hesitate, interrupt and coordinate in time. ChuckleNet is building the interaction-signal layer that captures this non-semantic information and exposes it as a machine-readable real-time signal stream.**

Laughter is the first experimentally clean event used to discover and validate the representation.

---

# 16. Scientific kill criteria

Pi CLI must explicitly stop, narrow or redesign a line of work when:

- performance disappears under speaker/source-independent splits;
- performance is driven by obvious acoustic shortcuts;
- temporal features add no value;
- attribution is unreliable and the product concept depends on attribution;
- the representation does not transfer beyond stand-up;
- interaction signals add no stable information beyond transcript/context;
- the commercial use case depends on a prohibited or weakly defensible inference.

A failed hypothesis is a valid research result.

---

# 17. Business kill criteria

Do not continue fundraising/productization merely because the technology is interesting.

Reassess the commercial thesis if:

- <20 qualified discovery conversations produce no repeated problem pattern;
- target buyers cannot identify a measurable KPI affected by the signal;
- data/privacy constraints make evaluation impractical;
- integration cost is too high relative to customer value;
- existing platform vendors can reproduce the signal layer cheaply with no defensible differentiation;
- partners want generic sentiment/emotion rather than the temporal interaction representation we are building.

---

# 18. Weekly operating cadence for Pi CLI

Every execution cycle should finish with a one-page status:

### Research
- experiments completed
- best validated metric
- uncertainty/confidence
- new failure modes
- hypothesis status

### Engineering
- reproducible scripts/configs
- compute/runtime
- data issues
- technical debt blocking next gate

### Commercial
- new qualified conversations
- design-partner status
- buyer pain patterns
- pilot status
- objections

### Decision
- **continue / narrow / pivot / stop**
- why
- next highest-information action

Do not report “N files changed” as a meaningful success metric.

---

# 19. Repository safety rules

**Do not delete important project history.**

Before modifying or replacing any file:

1. check whether it is canonical, historical, experimental or generated;
2. preserve important historical artifacts;
3. create additive replacement documents when the old file contains useful provenance;
4. never overwrite an old result merely to make the new result look better;
5. register new experiments/results in `docs/EXPERIMENT_REGISTRY.md`;
6. update `docs/RESEARCH_LINEAGE.md` when a new result materially changes interpretation.

Historical code, notebooks, checkpoints and result JSON may still contain useful evidence. Investigate before pruning.

---

# 20. First Pi CLI task — exact instruction

Start with **repository archaeology, not implementation**.

### Step 1
Inventory:

- notebooks
- Python scripts
- model definitions
- feature extraction code
- dataset loaders
- training/evaluation scripts
- result JSON/CSV/NPY/PKL files
- checkpoints
- VTT/annotation processing
- old Taskmaster tasks
- ablation implementations
- benchmark evaluation code

### Step 2
Map every relevant artifact to:

- current canonical experiment
- historical result
- reusable component
- obsolete/unsafe component
- unknown provenance

Do not delete anything.

### Step 3
Recover whether E01 can be executed from existing assets with minimal new data collection.

Prefer reuse of existing labeled/weakly labeled data plus a carefully constructed control set.

### Step 4
Implement E01 as a reproducible experiment with:

- fixed config
- fixed splits
- deterministic seeds where practical
- result artifact
- error analysis
- registry entry

### Step 5
Do not move to E02 until E01 has a written conclusion.

### Step 6
In parallel, create a lightweight design-partner prospecting tracker. Do not wait for the research program to finish before starting outreach.

---

# 21. Required final output from every major Pi CLI cycle

Pi CLI should return:

1. **What changed**
2. **What was actually measured**
3. **What hypothesis was supported/refuted**
4. **What remains uncertain**
5. **Which gate is now cleared/not cleared**
6. **What the next highest-information action is**
7. **Any commercial signal discovered**
8. **Any files/results preserved or newly registered**

The answer should be evidence-first and critical.

---

# 22. Priority order

When resources are limited, use this priority order:

**P0 — evidence integrity**  
**P1 — E01 adversarial validation**  
**P2 — temporal value / E02**  
**P3 — semantic increment / E05**  
**P4 — design partners and retrospective pilots**  
**P5 — cross-domain transfer**  
**P6 — multimodal expansion**  
**P7 — fundraising scale-up**

This ordering is intentionally not “research first, business later.” Commercial discovery runs in parallel, while technical claims are gated in sequence.

---

## Canonical references

- `docs/RESEARCH_VISION_V2.md`
- `docs/RESEARCH_LINEAGE.md`
- `docs/INTERACTION_SIGNAL_RESEARCH_PROGRAM.md`
- `docs/DECISION_GRAPH_V2.md`
- `docs/EXPERIMENT_REGISTRY.md`
- `docs/PRD_V7_INTERACTION_SIGNAL.md`
- `docs/BIOSEMIOTIC_FRAMEWORK_V2.md`
- `docs/COMPETITOR_MAP_2026.md`
- `docs/COMMERCIALIZATION_INTERACTION_SIGNAL_API.md`
- `docs/MODEL_CARD_V3_INTERACTION_SIGNAL.md`
- `docs/DOCUMENTATION_STATUS_V2.md`

**Supersession rule:** This document is the execution handoff, not a replacement for the research vision or research program. It translates those documents into operational tasks and gates for Pi CLI.
