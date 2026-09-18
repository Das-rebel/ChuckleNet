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

## Current position — 2026-09-18

The canonical graph is unchanged. Current evidence maps to it as follows:

| Graph node | Current status |
|---|---|
| Labels independently grounded? | **No for VTT weak labels.** Use as scale/hypothesis evidence only. Human-label anchors remain separate. |
| Acoustic representation detects target event? | **Yes, weakly**, for laughter under weak labels. v32 is the citable full-corpus baseline: F1 0.2732 / AP 0.142 / IoU-F1@0.2 0.2290. |
| Survives adversarial acoustic negatives? | Existing E01 evidence is supportive; v30e adds no new Gate-2 evidence. |
| Temporal context adds information? | **Yes, but narrowly.** P1 paired 3-seed validation (118v, Sep 18) shows true order > random with ΔF1 +0.0769 [CI +0.0617,+0.0917] — primary gate PASS. Local-shuffle and reverse controls do not separate (CI spans zero). Implication: **broad sequence/context structure matters; fine local order and forward direction do not add measurable value at 5 s resolution.** Claim narrowed accordingly. |
| Attribution, transfer, downstream intent | Still open. MELD null blocks generic-emotion overclaim. **P2 concurrent beyond-words test (Sep 18) also NULL**: timing features add +0.0018 F1 [CI −0.0046,+0.0080] over word content for current-window labeling. Gate-4 concurrent claims must not include timing increments. Redirect: P2 Level A prospective onset prediction (context-before → next-window onset) is the open beyond-words test. |

The 2026-09-18 v30e Kaggle run is a **P0 reproducibility artifact**, not a flagship replacement or new decision-graph branch. v32 remains the weak-label flagship.

## Commercial decision boundary

Do not jump from “detected laughter/emotion” to “customer intent.” The scientifically defensible chain is:

`observable signal → interaction event → state change → intent transition → policy decision`

The final policy remains constrained by domain rules and does not turn a voice signal into an eligibility/risk judgment.
