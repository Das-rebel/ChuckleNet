# ChuckleNet Model Card V3 — Interaction Signal Research

**Status:** CANONICAL MODEL-CARD SPECIFICATION — 2026-09-10  
**Purpose:** source of truth for any future Hugging Face model-card update

## Model identity

ChuckleNet is an independent research project studying **non-semantic interaction signals** in human communication. The current released model artifacts originated from laughter-detection experiments and should not be presented as a validated general interaction-state model.

## Current scientific status

The strongest current real-label acoustic evaluation is a 162-video, video-grouped out-of-fold evaluation:

| Input | F1 |
|---|---:|
| Prosody | 0.537 |
| WavLM | 0.548 |
| WavLM + prosody | 0.559 |

A separate 118-video StandUp4AI evaluation currently reports approximately **IoU-F1@0.2 = 0.3302**.

These numbers are the current evidence anchors. They must not be combined with historical pseudo-label or incompatible label-scheme results.

## Historical results

Older repository experiments reported substantially higher F1 values, including approximately 0.95–0.98. Those experiments are retained for provenance but are **not current model-performance claims** because label provenance, pseudo-label circularity, or evaluation comparability prevents treating them as equivalent to the current gold-label anchors.

## Intended use

The current artifacts are suitable for:

- research into acoustic laughter/event detection;
- benchmarking prosodic and learned audio representations;
- experimentation with temporal interaction signals;
- reproducibility and extension of the research program.

They are **not** validated for:

- psychological diagnosis;
- deception detection;
- creditworthiness or eligibility inference;
- protected-attribute inference;
- direct measurement of internal emotional state;
- autonomous high-stakes decision making.

## Research direction

The next-generation system is intended to expose timestamped interaction signals such as:

- laughter/reaction;
- hesitation;
- turn completion;
- interruption;
- response latency;
- engagement-change proxy;
- uncertainty proxy;
- later, multimodal interaction signals.

These are research hypotheses until each signal has independent labels and validation.

## Architecture direction

```text
Audio ──┐
        ├──> Interaction Signal Engine ──> event/state stream
Video ──┤
        │
Text ───┘  (supporting alignment/context)
```

Audio and temporal structure are the current priorities. Vision is a later expansion. Text is a supporting comparison condition rather than the project's competitive center.

## Evaluation policy

Any future model card must state:

- dataset and version;
- label provenance;
- sample unit;
- split and speaker separation;
- model inputs;
- preprocessing;
- metric and IoU/tolerance;
- thresholding;
- aggregation;
- confidence intervals where available;
- known limitations.

No historical headline should be restored merely because it is numerically attractive.

## Related canonical documents

- `docs/RESEARCH_VISION_V2.md`
- `docs/RESEARCH_LINEAGE.md`
- `docs/INTERACTION_SIGNAL_RESEARCH_PROGRAM.md`
- `docs/EXPERIMENT_REGISTRY.md`
- `docs/PAPER_INTERACTION_SIGNAL_V1.md`
- `docs/BIOSEMIOTIC_FRAMEWORK_V2.md`
