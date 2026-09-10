# ChuckleNet Decision Graph V2

**Status: CANONICAL — 2026-09-10**

## North-star question

> Do non-semantic interaction signals add reliable information about human interaction state beyond transcript semantics?

## Decision graph

```text
START
  │
  ▼
Are labels independently grounded?
  │
  ├─ NO ──► classify as weak/pseudo evidence; do not use as headline
  │
  └─ YES
       │
       ▼
Does acoustic representation detect the target event?
       │
       ├─ NO ──► inspect labels/data/representation; stop premature scaling
       │
       └─ YES
            │
            ▼
Does it survive adversarial acoustic negatives?
            │
            ├─ NO ──► diagnose shortcut learning
            │
            └─ YES
                 │
                 ▼
Does temporal context add information?
                 │
                 ├─ NO ──► retain event detector; do not claim interaction model
                 │
                 └─ YES
                      │
                      ▼
Can events be attributed to speaker/listener/audience?
                      │
                      ├─ NO ──► improve source separation / attribution
                      │
                      └─ YES
                           │
                           ▼
Does the representation predict interaction-state change?
                           │
                           ├─ NO ──► remain at event layer
                           │
                           └─ YES
                                │
                                ▼
Does it transfer beyond stand-up?
                                │
                                ├─ NO ──► diagnose domain-specific structure
                                │
                                └─ YES
                                     │
                                     ▼
Does audio/video add value beyond transcript semantics?
                                     │
                                     ├─ NO ──► do not force multimodal thesis
                                     │
                                     └─ YES
                                          │
                                          ▼
Does the signal improve downstream intent/state decisions?
                                          │
                                          ├─ NO ──► publish scientific result; stop commercialization
                                          │
                                          └─ YES
                                               │
                                               ▼
Is deployment privacy-, consent-, and policy-compatible?
                                               │
                                               ├─ NO ──► redesign use case
                                               │
                                               └─ YES
                                                    │
                                                    ▼
                                             PILOT / API
```

## Scientific gates

### Gate 1 — label validity
Gold/manual labels outrank weak captions. Pseudo-label experiments are hypothesis generators.

### Gate 2 — shortcut resistance
No model is considered robust until it is tested against acoustically similar negatives and source-attribution confounds.

### Gate 3 — temporal causality proxy
The model should be tested on whether the **relation** among events matters, not simply whether a chunk sounds unusual.

### Gate 4 — incremental information
Compare:

- transcript only
- transcript + context
- interaction signals only
- transcript + context + interaction signals

The key quantity is the incremental improvement from the final condition.

## Model decision matrix

| Candidate | Purpose | Current status |
|---|---|---|
| F0/prosody | compact acoustic baseline | active |
| spectral/MFCC | acoustic baseline | active |
| WavLM | learned acoustic baseline | active |
| WavLM + prosody | fusion baseline | active |
| text/XLM-R | semantic control | supporting only |
| temporal TCN/BiGRU/Conformer | interaction sequence | next |
| audio + video temporal fusion | multimodal interaction | later |

## Commercial decision boundary

Do not jump from “detected laughter/emotion” to “customer intent.” The scientifically defensible chain is:

`observable signal → interaction event → state change → intent transition → policy decision`

The final policy remains constrained by domain rules and does not turn a voice signal into an eligibility/risk judgment.
