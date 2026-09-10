# ChuckleNet — Pi CLI Execution Mandate V3

**Status: CANONICAL EXECUTION CONTROL PLANE**
**Date:** 2026-09-10
**Supersedes for execution:** `PICLI_EXECUTION_MANDATE_V2.md`
**Purpose:** Give Pi CLI the current research question, decision gates, operating rules and resource priorities for ChuckleNet.

---

## 0. Governing research question

> **Can machines extract, learn, and model useful information from how humans interact that is not contained in the literal words they use?**

This is the primary ChuckleNet question.

The more formal scientific version is:

> **Can non-semantic interaction signals provide incremental information about human interaction state and intent beyond speech transcript semantics?**

The first question is the human/intelligence proposition. The second is the falsifiable research formulation.

Laughter is the entry point because it is an observable social event with temporal structure. It is not the product definition.

Pi CLI must optimize for evidence about this question, not for a better laughter leaderboard score.

---

## 1. What ChuckleNet is and is not

### It is

An attempt to discover, extract and model information carried by:

- how people sound;
- how they pause and respond;
- how they interrupt or overlap;
- how reactions occur in time;
- how interaction signals change state;
- eventually, how audio and visual behavior jointly encode interaction.

### It is not

- a text-humor project;
- a generic LLM emotion classifier;
- a black-box "emotion score" API;
- a direct credit/eligibility predictor from voice;
- a psychology/medical diagnostic system.

Text/ASR is primarily a semantic control, alignment source and downstream context.

---

## 2. Critical strategic principle

The project has four layers:

`OBSERVE → LEARN → MODEL → USE`

**Observe:** detect measurable acoustic/visual/temporal events.

**Learn:** establish which patterns and temporal relationships are predictive.

**Model:** produce reusable interaction-signal/state representations.

**Use:** test whether those representations improve a downstream task or decision.

Do not claim the higher layer merely because the lower layer works.

A good laughter detector proves observation. It does not prove a general interaction representation.

---

## 3. Current evidence baseline

Use only the registered canonical anchors unless independently revalidated:

- `GILLICK-162-OOF-2026-09`: real-label acoustic evaluation; WavLM + prosody F1 0.559, WavLM 0.548, prosody 0.537.
- `STANDUP4AI-118-I20-2026-09`: stand-up benchmark anchor; IoU-F1@0.2 ≈ 0.3302.
- `VTT-620-WEAK-2026-09`: sparse weak-label scale study; not gold accuracy.
- `HIST-F0-HIGHF1`: historical/provenance-only results.

Never restore old ~0.95–0.98 results as the current headline without reconstructing their labels, split and evaluation protocol.

Read before changing scientific interpretation:

- `docs/RESEARCH_VISION_V2.md`
- `docs/RESEARCH_LINEAGE.md`
- `docs/SUPPORTING_RESEARCH_AND_HYPOTHESES_V2.md`
- `docs/INTERACTION_SIGNAL_RESEARCH_PROGRAM.md`
- `docs/EXPERIMENT_REGISTRY.md`
- `docs/DECISION_GRAPH_V2.md`
- `docs/COMMERCIALIZATION_INTERACTION_SIGNAL_API.md`

---

## 4. The four tests that matter

Do not treat every planned experiment as equally important. The project can be de-risked by four decisive questions.

### Test 1 — Robust observation

**Can we reliably detect an interaction event after controlling for obvious acoustic/source shortcuts?**

This is E01.

### Test 2 — Temporal learning

**Does the relationship between events in time add information beyond static acoustics?**

This is E02.

### Test 3 — Information not present in words

**Do interaction signals add information beyond transcript semantics/context?**

This is E03 and is the flagship scientific/commercial test.

### Test 4 — Real-world transfer and value

**Does the learned representation survive outside stand-up and improve a real workflow?**

This is E04 plus commercial validation.

Vision/multimodality are optional expansions, not prerequisites for proving the core thesis.

---

## 5. E01 — robust observation

### Hypothesis

The current acoustic capability contains genuine event information that survives source, speaker and confound controls.

### Minimum work

Use the strongest existing real-label assets first. Do not collect a giant new dataset unless required.

Required controls where data permits:

- ordinary speech;
- silence/pause;
- applause;
- cheering;
- audience laughter;
- performer laughter;
- speech-laugh;
- cough/breath/non-speech vocalization;
- environmental noise.

Compare only the minimum useful ladder:

1. F0/prosody;
2. compact acoustic baseline;
3. WavLM;
4. prosody + WavLM.

Required splits:

- video/source disjoint;
- speaker/person disjoint where possible;
- no overlapping windows across train/test.

Required outputs:

- precision, recall, F1;
- PR-AUC when appropriate;
- confusion matrix;
- threshold/calibration analysis;
- fold or bootstrap uncertainty;
- representative false positives/negatives;
- explicit conclusion: **SUPPORTED / PARTIALLY SUPPORTED / NOT SUPPORTED**.

### Gate

Proceed only if useful performance remains after leakage and major shortcut controls.

A failure narrows the claim. It does not justify adding a larger model.

---

## 6. E02 — temporal learning

### Core hypothesis

> **Interaction is not only an event; information is carried by the relationship among events in time.**

Test whether response timing, pause structure, turn position and preceding events add predictive information beyond frame/window acoustics.

### Counterfactual design

Prefer matched examples where:

- laughter/reaction is shifted relative to preceding speech;
- non-laughter pauses are matched on duration/energy/F0;
- turn position is independently added/removed;
- local acoustics are held as constant as practical.

Compare:

A. acoustic-only
B. acoustic + timing/pause
C. acoustic + turn/preceding-event context
D. one lightweight sequence model
E. text + audio as a control

Use one lightweight temporal architecture first, preferably TCN or BiGRU. Do not run architecture tournaments without a hypothesis-level reason.

### Primary targets

Start with no more than two:

- reaction onset/offset or latency;
- event/state transition.

### Gate

Temporal features must provide reproducible improvement over the best E01 baseline under the same labels and split, and the gain must survive targeted temporal ablations.

---

## 7. E03 — the flagship test

### Research question

> **Can the machine recover useful information from interaction behavior that is not contained in the literal words?**

Operationalize this as:

**A:** transcript only

**B:** transcript + permitted context

**C:** transcript + permitted context + interaction signals

Interaction signals should be explicit and auditable, such as:

- pause/response latency;
- interruption/overlap;
- reaction/event signal;
- temporal relation features;
- engagement-change proxy;
- hesitation/uncertainty proxy only where valid labels support the claim.

Do not hide the entire contribution behind one opaque emotion embedding.

### Metrics

Choose a task with actual labels. Prefer:

1. intent/state classification or transition;
2. reaction/turn prediction;
3. intervention timing;
4. downstream conversion/application-start proxy only when data rights and causal interpretation are defensible.

Report:

- absolute performance of B and C;
- delta C − B;
- confidence interval/bootstrap distribution;
- consistency across speakers/sources;
- calibration;
- latency/compute cost.

### Gate

A **stable, statistically credible incremental gain** is required.

If C does not beat B meaningfully, do not force the thesis. Narrow, reframe or stop the commercial claim.

---

## 8. E04 — transfer

The learned signal must leave the comedy laboratory.

Preferred sequence:

`stand-up → conversational speech → voice-agent/customer-service`

Use the smallest lawful evaluation set available.

Measure:

- absolute degradation;
- which signals transfer;
- whether incremental information survives domain shift;
- whether calibration remains usable.

A representation that works only in stand-up is a useful research finding but not yet the proposed general interaction layer.

---

## 9. Multimodality is conditional

Do not build a major vision stack until E01/E02 show a meaningful audio/temporal information gap that vision can plausibly address.

When justified, compare:

`audio → video → audio + video`

Candidate signals:

- facial activation/smile dynamics;
- head movement;
- gaze/orientation proxy;
- gesture/body motion;
- speaker/listener attribution.

The question is always incremental information, not modality count.

---

## 10. Commercial discovery starts immediately

The commercial hypothesis is:

> Voice and multimodal systems lose useful information contained in timing, reaction, hesitation, interruption and non-semantic delivery. An interaction-signal layer can expose that information to existing intent/policy systems.

### Design partner A

Voice AI / TTS / speech-to-speech / conversational platform.

Desired evaluation:

- turn handling;
- interruption detection;
- response timing;
- conversation quality;
- reaction detection.

### Design partner B

High-volume conversation operator such as customer service, sales, servicing or collections.

Desired evaluation:

- intent transition;
- intervention timing;
- objection/hesitation handling;
- resolution/acceptance KPI.

Do not start with a credit-risk team. Use workflows where there is a visible KPI and manageable data/consent constraints.

### Serious design partner definition

A partner counts only when it has a named owner and agrees to a concrete evaluation. Strong evidence includes workflow access, sandbox/retrospective data, an evaluation metric and willingness to run a test.

---

## 11. Commercial scorecard

First milestone: **20 qualified discovery conversations**.

Track only:

- repeated pain;
- signal currently missing;
- measurable KPI;
- current workaround/vendor;
- data access;
- integration difficulty;
- economic buyer;
- reason for no.

Next milestone: **2 serious design partners**.

Then: **1 retrospective/sandbox evaluation**.

Then: commercial proof via one of:

- paid pilot;
- signed LOI/commercial evaluation;
- repeated production-adjacent use with a KPI owner;
- buyer-accepted statistically credible incremental value.

---

## 12. Fundraising rule

Investor relationship-building begins now.

Do not wait for a finished research roadmap.

Do not raise on an unproven "emotion AI" story.

### Current stage

Prepare:

- 8–10 slide narrative;
- investor target list;
- 5–10 exploratory conversations;
- precise separation of proven / hypothesized / unknown.

### Stronger raise trigger

Pursue a serious pre-seed process once the project has a credible combination of:

- E01 evidence;
- early E02 temporal value;
- at least one serious design partner, preferably two;
- a concrete E03 measurement path;
- clear API/product architecture.

Customer pull can compensate for incomplete research depth; strong research evidence can compensate for early customer stage. The best fundraising position is convergence of both.

---

## 13. Resource allocation for a single-founder/limited-resource project

Target effort:

**50% research experiments**
**25% data/evaluation infrastructure**
**20% customer discovery/design partners**
**5% investor/admin**

Do not spend major cycles on:

- architecture polishing;
- documentation multiplication;
- benchmark tourism;
- full multimodal implementation before the audio/temporal thesis earns it.

---

## 14. Hard stop rules

Pi CLI must narrow, redesign or stop a line of work when:

- event performance is mostly speaker/source leakage;
- temporal information adds no stable value;
- transcript/context already explains the downstream signal;
- transfer fails completely;
- buyers cannot identify a KPI;
- data/privacy constraints block evaluation;
- an incumbent can reproduce the capability trivially without differentiation;
- the business requires inappropriate inference such as creditworthiness from voice.

A negative result is progress when it eliminates an incorrect hypothesis.

---

## 15. Repository safety

Never delete project history merely because the research interpretation changed.

Before modifying anything:

1. classify the artifact as canonical / historical / experimental / generated;
2. preserve historical evidence;
3. prefer additive replacement documents;
4. do not overwrite old result artifacts to change their meaning;
5. register new experiments and update lineage;
6. inspect before pruning old code, notebooks or checkpoints.

The V1 and V2 Pi CLI mandates remain retained for provenance. V3 is the current execution authority.

---

## 16. First task for Pi CLI

Do not immediately build new models.

### Step 1 — archaeology
Map the existing repository to:

`artifact → experiment → provenance → reusable / blocked / historical / unknown`

### Step 2 — E01 readiness
Answer:

> **What is the smallest additional implementation and data required to run E01 with defensible controls?**

### Step 3 — execute E01
Run it reproducibly.

### Step 4 — issue a decision memo
Use exactly:

`hypothesis → protocol → result → uncertainty → failure modes → interpretation → gate decision → next highest-information action`

Only after the E01 decision should Pi CLI implement E02.

---

## 17. Weekly operating report

Every cycle ends with:

### Research
`hypothesis | experiment | metric | uncertainty | conclusion`

### Engineering
`reproducibility | blocker | minimum next implementation`

### Commercial
`qualified conversations | repeated pain | partner status | KPI | objection`

### Capital
`investor conversations | objection | evidence requested`

### Decision
**CONTINUE / NARROW / PIVOT / STOP**

Then identify **one** highest-information next action.

---

## 18. Final instruction

Pi CLI is not being asked to make ChuckleNet look advanced.

It is being asked to discover whether the central proposition is true:

> **Humans communicate useful information through interactional behavior beyond literal words, and machines can extract, learn and model that information well enough to improve downstream understanding or action.**

Every experiment, code change and commercial conversation should increase confidence in that proposition, decrease confidence in it, or sharpen its boundary.

Anything that does neither is lower priority.
