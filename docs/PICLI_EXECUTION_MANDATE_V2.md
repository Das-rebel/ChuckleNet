# ChuckleNet — Pi CLI Execution Mandate V2

**Status: CANONICAL EXECUTION HANDOFF**  
**Date:** 2026-09-10  
**Supersedes for execution:** `PICLI_EXECUTION_MANDATE_V1.md`  
**Purpose:** Convert the ChuckleNet research vision into the smallest sequence of high-information actions that can be executed with limited time, compute and data.

---

# 0. Executive decision

ChuckleNet should now be run as a **research de-risking + commercial discovery program**, not as an open-ended ML project.

The objective is not to build a large multimodal system first.

The objective is to answer four questions in order:

1. **Is the current acoustic capability real and shortcut-resistant?**
2. **Does temporal interaction structure add information beyond static acoustics?**
3. **Do interaction signals add information beyond transcript semantics/context?**
4. **Does that signal survive outside stand-up comedy and map to a buyer problem?**

Everything else is downstream.

The core thesis remains:

> **Can non-semantic multimodal interaction signals provide incremental information about human interaction state and intent beyond speech transcript semantics?**

Laughter is the entry event, not the product.

---

# 1. Critical correction to the previous execution plan

The previous mandate treated E01 as if success would itself establish an "interaction representation." That is too strong.

**E01 can only establish robust event detection under controls.**

A strong laughter detector does not by itself prove that ChuckleNet has discovered a general interaction signal.

The scientific chain must therefore be:

`robust event detection → temporal value → incremental information → cross-domain utility → commercial value`

Do not skip links in this chain.

Likewise, do not spend scarce resources on full vision/multimodal architecture until the audio + temporal hypothesis survives.

---

# 2. Starting position

Use these as the current evidence anchors; do not revert to older headline scores:

- `GILLICK-162-OOF-2026-09`: real-label acoustic evaluation; fusion F1 0.559, WavLM 0.548, prosody 0.537.
- `STANDUP4AI-118-I20-2026-09`: current stand-up anchor; IoU-F1@0.2 ≈ 0.3302.
- `VTT-620-WEAK-2026-09`: weak-label scale-up; engineering/evidence study, not gold accuracy.
- `HIST-F0-HIGHF1`: historical/provenance-only high scores.

Read `RESEARCH_LINEAGE.md`, `RESEARCH_VISION_V2.md`, `INTERACTION_SIGNAL_RESEARCH_PROGRAM.md`, and `EXPERIMENT_REGISTRY.md` before changing scientific interpretation.

---

# 3. Operating rules for Pi CLI

## Rule 1 — maximize information gained per unit of work

Prefer an experiment that can falsify the thesis over an experiment that merely increases model complexity.

## Rule 2 — no leaderboard chasing

A higher F1 without stronger label/control discipline is not progress.

## Rule 3 — no premature multimodality

Do not build video pipelines unless audio + temporal evidence clears the relevant gate.

## Rule 4 — no commercial overclaiming

Do not call the product "emotion AI," and do not claim voice can establish creditworthiness, eligibility, deception, personality or other sensitive latent attributes.

## Rule 5 — preserve history

Never delete historical notebooks, checkpoints, result files or old plans simply because the interpretation changed.

## Rule 6 — every result must be reproducible

Record dataset, provenance, split, features, model, metric, threshold, uncertainty and artifact path in the experiment registry.

---

# 4. Phase 0 — repository archaeology (mandatory, short)

**Goal:** determine what can be reused before writing new code.

Inventory:

- notebooks
- dataset loaders
- annotation/VTT processors
- feature extraction
- F0/prosody pipelines
- WavLM pipelines
- current evaluation code
- ablation code
- benchmark code
- result JSON/CSV/NPY/PKL
- checkpoints
- taskmaster tasks
- scripts/configs

Produce one machine-readable and one human-readable map:

`artifact → experiment family → provenance → reusable / blocked / historical / unknown`

Then answer exactly:

> **What is the minimum additional implementation/data required to run the first defensible experiment?**

Do not refactor the whole repository.

**Exit condition:** a reproducible E01 run path exists, or a precise blocker is documented.

---

# 5. E01 — shortcut-resistant event validation

## Scientific question

> **Does the current acoustic detector recognize laughter/event structure rather than speaker, source, silence, pause or generic vocal/noise shortcuts?**

This is the first hard scientific gate.

## Minimum experiment

Use the strongest existing real-label dataset(s) first.

Required controls where available:

- ordinary speech
- silence/pause
- applause
- cheering
- audience laughter
- performer laughter
- speech-laugh
- cough/breath/non-speech vocalization
- environmental/noise events

Run the smallest controlled model ladder:

1. F0/prosody
2. compact acoustic features
3. WavLM
4. prosody + WavLM

Do not add a new foundation model unless an existing baseline cannot answer the question.

## Required split discipline

At minimum:

- source/video disjoint
- speaker/person disjoint where labels permit
- no overlapping windows across train/test

## Required metrics

- precision
- recall
- F1
- PR-AUC where sparsity makes it informative
- confusion matrix
- calibration/error analysis
- uncertainty interval or fold variability

## Required diagnosis

For every major failure mode, produce concrete examples/IDs when possible.

Classify the outcome:

**SUPPORTED** — signal remains strong after controls.  
**PARTIALLY SUPPORTED** — useful signal remains but important shortcut dependence exists.  
**NOT SUPPORTED** — most apparent performance disappears under controls.

## E01 gate

Proceed only if there is a meaningful performance floor after speaker/source leakage controls and no single obvious confound explains most performance.

A failed E01 does not kill the project. It forces the claim to narrow.

---

# 6. E02 — temporal information gain

## Scientific question

> **Does the relationship among speech, pause, turn position and reaction contain information that static acoustic windows do not?**

This is where the research begins to become specifically about interaction rather than event classification.

## Counterfactual test

Use matched examples where possible:

- shift laughter relative to preceding speech;
- match non-laughter pauses by approximate duration/energy/F0;
- remove/add turn position;
- compare local acoustic evidence against sequence context.

Compare only the necessary models:

A. acoustic-only  
B. acoustic + pause/timing  
C. acoustic + turn position/preceding event  
D. lightweight sequence model  
E. text + audio only as a supporting control

Preferred sequence model: use **one** lightweight architecture first (TCN or BiGRU). Do not benchmark four architectures unless the first one fails for a technical reason.

## Targets

Choose no more than two primary targets initially:

- reaction onset/offset or latency
- event/state transition

## E02 gate

Require reproducible improvement over the best E01 baseline under the **same split and label protocol**.

This improvement should survive ablations that remove the specific temporal cue being claimed.

---

# 7. E03 — semantic increment (flagship)

## Scientific question

> **Does the interaction-signal stream add information that transcript semantics/context cannot recover?**

This is the most important experiment for the eventual business.

## Baselines

**A:** transcript only  
**B:** transcript + permitted context  
**C:** transcript + permitted context + interaction signals

The interaction-signal input should be an explicit, auditable stream such as:

- pause/response latency
- interruption/overlap
- event/reaction signal
- engagement-change proxy
- hesitation/uncertainty proxy where labels justify it
- temporal relation features

Do not simply add an opaque "emotion score."

## Primary measurement

Use a task where labels genuinely exist.

Preferred order:

1. intent/state classification or transition;
2. reaction/turn prediction;
3. intervention timing;
4. conversion/application-start proxy only if the data and causal interpretation are defensible.

Report:

- absolute performance;
- delta C − B;
- confidence interval / bootstrap distribution;
- effect consistency across speakers/sources;
- calibration;
- compute/latency cost.

## E03 gate

The interaction signal must provide a **stable, statistically credible incremental gain** over transcript + context.

If it does not, the commercial thesis must be narrowed or changed.

---

# 8. E04 — cross-domain transfer

Only after E02/E03 are informative.

Minimum transfer order:

`stand-up → conversational speech → voice-agent/customer-service`

Use the smallest lawful dataset possible.

The key measure is not identical F1 across domains.

Ask:

> **Does the representation retain useful incremental information after domain shift?**

Report domain-specific degradation and what components transfer.

---

# 9. E05 — multimodal expansion

Vision becomes a multiplier only after audio + temporal evidence works.

Candidate additions:

- facial activation/smile dynamics
- head movement
- gaze/orientation proxy
- gesture/body motion
- listener/speaker attribution

Run one clear comparison:

`audio → video → audio+video`

Then test whether video adds incremental information over audio + temporal features.

Do not build a large vision stack before there is a demonstrated information gap that vision can plausibly fill.

---

# 10. Commercial validation runs in parallel from Day 1

Research and commercial discovery are not sequential.

The business hypothesis is:

> **Voice/interaction systems lose useful information contained in timing, reaction, hesitation, interruption and non-semantic delivery. An interaction-signal layer can expose that information to existing intent/policy systems.**

## Design-partner definition

A design partner is **not** someone who says the concept is interesting.

They must provide at least two of:

- access to a realistic evaluation workflow;
- a sample/sandbox dataset that can lawfully be evaluated;
- a named technical owner;
- a named business owner;
- agreement on a measurable evaluation metric;
- willingness to run a retrospective or sandbox pilot.

## Target two partner types

**Partner A — voice AI / TTS / conversational platform**

They can test whether interaction signals improve turn handling, latency, interruption management, reaction detection or conversation quality.

**Partner B — high-volume conversational operator**

Examples include customer service, sales, collections, servicing or financial conversational workflows where the signal can be evaluated against an operational KPI.

Do not start with a bank's credit-risk team. Start with a workflow where interaction quality has a visible KPI and where data rights are tractable.

---

# 11. Commercial discovery scorecard

Pi CLI should maintain a simple pipeline, not a CRM monster.

## Discovery target

**20 qualified conversations** as the first learning milestone.

Track:

- repeated pain/problem;
- current solution;
- signal they cannot currently observe;
- measurable KPI;
- willingness to test;
- data availability;
- integration difficulty;
- economic buyer;
- reason for no.

## Design-partner target

**2 serious design partners**.

Count only when the criteria above are met.

## Pilot target

At least **1 retrospective/sandbox evaluation** with:

`baseline → interaction-signal layer → incremental KPI`

## Commercial proof target

Any one of:

- paid pilot;
- signed LOI/commercial evaluation;
- production-adjacent repeated usage with a named KPI owner;
- statistically credible incremental value accepted by a buyer.

---

# 12. Fundraising operating rule

Do not wait for a finished scientific program to talk to investors.

Begin investor relationship-building **now**.

Do not, however, optimize the research around fundraising theater.

## Phase A — now

Build:

- 8–10 slide pre-seed narrative;
- investor target list;
- 5–10 exploratory conversations;
- clear explanation of what is proven vs hypothesized.

## Phase B — stronger raise trigger

The project becomes materially more fundable when it has:

1. E01 evidence that survives obvious controls;
2. E02 temporal information gain;
3. at least 1 serious design partner, preferably 2;
4. a credible E03 semantic-increment experiment or strong buyer evidence explaining why it can be tested;
5. clear product/API architecture.

Do **not** make "two design partners + E03 + E04 + E05" a prerequisite to begin fundraising. That would delay capital until too many uncertainties are already solved.

The correct posture is:

`investor conversations now → research proof in parallel → formal raise when the hardest technical claim has early evidence and customer pull is visible.`

---

# 13. 30 / 60 / 90-day operating plan

## Days 0–30 — de-risk the core

**Must ship:**

- repository archaeology map;
- reproducible E01;
- E01 decision memo;
- initial 10–20 buyer discovery conversations;
- first investor narrative draft.

**Business gate:** repeated problem pattern emerging.

**Research gate:** robust/partial/not-supported classification for E01.

## Days 31–60 — prove temporal value

**Must ship:**

- E02 temporal ablation;
- lightweight sequence model;
- error analysis;
- 2 design-partner candidates in active evaluation;
- 5–10 additional investor conversations.

**Business gate:** at least 1 serious design partner.

**Research gate:** temporal increment demonstrated or hypothesis narrowed.

## Days 61–90 — prove commercial relevance

**Must ship:**

- E03 semantic increment prototype/evaluation;
- first retrospective/sandbox partner test;
- refined API schema;
- fundraising decision memo: raise now / continue bootstrapping / narrow thesis.

**Business gate:** 2 serious design partners and 1 measurable evaluation.

**Research gate:** interaction signals add value beyond semantics, or explicit evidence that they do not.

---

# 14. Resource allocation rule

For the current stage, allocate effort approximately as:

**50% research experiments**  
**25% data/evaluation infrastructure**  
**20% customer/design-partner discovery**  
**5% fundraising/admin**

Do not let documentation, architecture polish or model benchmarking consume the research budget.

---

# 15. What Pi CLI must NOT do next

Do not:

- build a giant multimodal architecture;
- create ten new model variants without hypothesis value;
- rewrite the repository for cleanliness;
- revive the old 0.95–0.98 headline as current truth;
- turn MELD emotion labels into biological/Duchenne ground truth;
- build a direct credit/eligibility voice model;
- spend weeks on a polished investor deck before there is updated evidence;
- treat a friendly exploratory call as a design partnership.

---

# 16. Weekly output format

Every cycle ends with one page:

### Research
`hypothesis → experiment → metric → uncertainty → conclusion`

### Engineering
`what became reproducible → blocker → next minimal implementation`

### Commercial
`qualified conversations → repeated pain → partner status → KPI → objection`

### Capital
`investor conversations → objection → evidence needed`

### Decision
**CONTINUE / NARROW / PIVOT / STOP**

Then identify the **single highest-information next action**.

---

# 17. Master decision tree

```text
                     CURRENT CHUCKLENET
                            │
                            ▼
                 PHASE 0: ARCHAEOLOGY
                            │
                    reproducible E01?
                       /           \
                     NO             YES
                     │               │
                  unblock       E01 CONTROLS
                                     │
                            shortcut-resistant?
                             /             \
                           NO               YES
                           │                 │
                     narrow claim       E02 TEMPORAL
                                             │
                                     temporal increment?
                                      /            \
                                    NO              YES
                                    │                │
                               narrow claim       E03 SEMANTIC
                                                      │
                                           incremental value?
                                            /             \
                                          NO               YES
                                          │                 │
                                     pivot/narrow       E04 TRANSFER
                                                             │
                                                     cross-domain?
                                                       /       \
                                                     NO         YES
                                                     │            │
                                                  narrow       E05 VIDEO
                                                                 │
                                                    ┌────────────┴───────────┐
                                                    ▼                        ▼
                                              research asset          commercial asset
```

Commercially, run in parallel throughout:

`20 qualified conversations → 1 serious partner → 2 serious partners → 1 measurable pilot → funding decision`

---

# 18. Final instruction to Pi CLI

**Start now.**

First deliverable is **not new code**.

It is:

> **A complete artifact-to-experiment map of the existing repository, followed by the exact minimum execution plan for E01 using already available assets.**

Once that is complete, execute E01.

Do not proceed to E02 on optimism. Proceed only on evidence.

Do not proceed to E03 because the architecture looks promising. Proceed only because E02 establishes temporal value.

Do not proceed to fundraising scale-up because the deck sounds good. Proceed because technical de-risking and customer evidence are beginning to converge.

The project wins by discovering the truth faster than competing teams—not by building the most code.
