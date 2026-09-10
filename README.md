# ChuckleNet — Non-Semantic Interaction Intelligence

**ChuckleNet is evolving from a laughter detector into an independent research program for non-semantic interaction signals in human communication.**

Laughter is the entry point. The longer-term target is to model interaction signals that transcript semantics alone cannot fully capture: **prosody, timing, hesitation, interruption, reaction, turn dynamics, engagement change, and eventually visual behavior.**

> **Research question:** Can non-semantic multimodal interaction signals provide incremental information about human interaction state and intent beyond speech transcript semantics?

## Why laughter first?

Laughter is an unusually useful first event because it is temporally observable and socially structured. A comedy interaction often exposes a sequence such as:

`setup → delivery → pause → punchline → reaction`

That makes laughter a practical laboratory for studying the broader problem of interaction-state change.

## Research architecture

```text
                 HUMAN INTERACTION
                         │
          ┌──────────────┼──────────────┐
          │              │              │
        AUDIO           VIDEO          TEXT
          │              │              │
     prosody/timing    behavior      semantics
     vocal events      attention     alignment
          │              │              │
          └──────────────┼──────────────┘
                         ↓
             INTERACTION SIGNAL ENGINE
                         ↓
                LATENT INTERACTION STATE
                         ↓
             event → state change → intent
                         ↓
                  downstream policy
```

### Modality priorities

- **Audio:** core research modality now.
- **Temporal dynamics:** core research problem, not an optional feature.
- **Vision:** planned expansion for embodied interaction signals.
- **Text/ASR:** supporting context and baseline for measuring incremental value, not the competitive center.

## What the project has established so far

The historical project contains several useful lines of evidence, but they use different datasets and label schemes and must not be conflated.

### Current anchors

| Evidence | Current role |
|---|---|
| **162-video real-laughter evaluation** | Strongest current acoustic anchor; WavLM + prosody F1 0.559, WavLM 0.548, prosody 0.537 under video-grouped OOF evaluation |
| **StandUp4AI 118-video evaluation** | Current stand-up temporal benchmark anchor; IoU-F1@0.2 ≈ 0.3302 |
| **620/621-video VTT scale-up** | Weak-label robustness/data-engineering experiment, not gold-label accuracy |
| **Historical high-F1 experiments** | Preserved as provenance; require exact label/split reconstruction before reuse as headline evidence |

The old repository headline that compact F0 features “beat WavLM by 4.3x” is **not a current scientific conclusion**. The F0 work remains important as a hypothesis about low-dimensional acoustic structure and will be re-tested under stronger controls.

## Research program

The next sequence is:

1. **Evidence hygiene** — freeze label provenance and benchmark definitions.
2. **Acoustic events** — laughter, speech-laugh, applause, silence, breath/noise, speaker/audience attribution.
3. **Temporal interaction** — turn completion, interruption, hesitation, reaction latency and event sequences.
4. **Counterfactual controls** — distinguish genuine interaction structure from acoustic shortcuts.
5. **Interaction state** — engagement, uncertainty proxy, reaction and state transitions.
6. **Cross-domain validation** — move beyond stand-up comedy.
7. **Audio + vision** — add embodied behavior after the audio/temporal framework is stable.
8. **Incremental semantic value** — test whether signals improve intent/state prediction beyond transcript + context.
9. **Product translation** — only if incremental value survives the scientific gates.

## Commercial direction

The potential product is an **Interaction Signal API**, not an emotion-label API.

Possible outputs:

- engagement signal
- hesitation
- uncertainty proxy
- interruption
- turn completion
- reaction/laughter
- response latency
- attention shift
- interest shift
- intent transition

Potential customers include voice-agent platforms, speech/TTS systems, contact-center intelligence vendors and conversational banking platforms.

For financial services, the research direction is explicitly **not** direct creditworthiness or eligibility inference from voice. The intended architecture is:

`ASR semantics + permitted context + interaction signals → intent/state model → existing policy/NBA engine`

## Repository guide

### Canonical strategy

- [`docs/RESEARCH_VISION_V2.md`](./docs/RESEARCH_VISION_V2.md) — north-star research vision
- [`docs/RESEARCH_LINEAGE.md`](./docs/RESEARCH_LINEAGE.md) — mapping of historical work to the new program
- [`docs/INTERACTION_SIGNAL_RESEARCH_PROGRAM.md`](./docs/INTERACTION_SIGNAL_RESEARCH_PROGRAM.md) — master research plan
- [`docs/DECISION_GRAPH_V2.md`](./docs/DECISION_GRAPH_V2.md) — scientific go/no-go logic
- [`docs/PRD_V7_INTERACTION_SIGNAL.md`](./docs/PRD_V7_INTERACTION_SIGNAL.md) — product/research specification
- [`docs/COMPETITOR_MAP_2026.md`](./docs/COMPETITOR_MAP_2026.md) — market and research landscape
- [`docs/COMMERCIALIZATION_INTERACTION_SIGNAL_API.md`](./docs/COMMERCIALIZATION_INTERACTION_SIGNAL_API.md) — commercialization thesis

### Historical research record

Older plans, paper drafts, ablation reports, notebooks, result JSONs and checkpoints are intentionally retained. They document the research path and should not be assumed to represent the current thesis.

Start with `docs/RESEARCH_LINEAGE.md` when interpreting older results.

## Current research principle

**Do not optimize the project around the highest historical F1. Optimize it around the strongest reproducible scientific question.**

The goal is to discover whether human interaction contains a measurable non-semantic layer—and whether that layer can be represented robustly enough to generalize beyond the original laughter task.
