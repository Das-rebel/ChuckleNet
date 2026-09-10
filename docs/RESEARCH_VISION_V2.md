# ChuckleNet Research Vision v2

**Status:** CANONICAL RESEARCH VISION  
**Date:** 2026-09-10  
**Supersedes:** earlier laughter-only, text-first and multi-product visions as the active direction

## 1. Core thesis

> **ChuckleNet studies non-semantic interaction signals: information carried by how people sound, move and coordinate in time, beyond the literal linguistic content of what they say.**

Laughter is the entry point, not the final product.

The long-term research question is:

> **Can non-semantic multimodal interaction signals provide incremental information about human interaction state and intent beyond speech transcript semantics?**

The project therefore does **not** compete to build a better text humor classifier, sentiment classifier or general-purpose language model.

Text/ASR is used primarily for alignment, context and controlled ablations. The research contribution lives in audio, timing, paralinguistics, visual behavior and cross-modal interaction structure.

## 2. Why laughter is the right starting point

Laughter is an unusually observable social event with a measurable temporal relationship to a preceding human action:

`setup → delivery → pause → punchline → audience reaction`

This makes stand-up comedy a natural laboratory for discovering interaction signals.

The project should therefore use laughter to answer progressively broader questions:

1. Can an acoustic model identify laughter?
2. Can it distinguish laughter from silence, speech, applause and other vocal events?
3. Can it localize reaction onset and offset precisely?
4. Can it model audience reaction as an event linked to preceding discourse?
5. Can it predict reaction before the reaction audio begins?
6. Which signals remain predictive after controlling for text and turn boundaries?
7. Which signals transfer to other human interactions?

## 3. Research object: the interaction signal

An interaction signal is an observable non-semantic or weakly semantic feature of human behavior that changes during an interaction.

### Auditory signals
- pitch/F0 dynamics
- energy and rhythm
- voicing and breathiness
- laughter and speech-laugh
- pause and response latency
- interruptions and overlap
- hesitation/disfluency
- sighs, coughs and other paralinguistic events

### Visual signals
- facial activation and smile dynamics
- gaze/orientation
- head movement
- gesture and posture
- attention/withdrawal

### Temporal/relational signals
- turn completion
- response latency
- interruption probability
- synchronization/alignment
- reaction intensity
- change-point / state-transition signals

### Context signals
- ASR transcript
- speaker identity/diarization
- dialogue structure
- optional CRM or session context in downstream applications

## 4. Model hierarchy

```text
                 HUMAN INTERACTION
                         │
          ┌──────────────┼──────────────┐
          │              │              │
        AUDIO           VIDEO          TEXT
          │              │              │
     paralinguistics   behavior      semantics
     prosody           attention     alignment
     timing            gesture       context
          │              │              │
          └──────────────┼──────────────┘
                         ↓
             INTERACTION SIGNAL ENGINE
                         ↓
              LATENT INTERACTION STATE
                         ↓
          ┌──────────────┼──────────────┐
          │              │              │
        event         state change     timing
          │              │              │
       laughter       engagement      latency
       applause       hesitation      reaction
       interruption   uncertainty     persistence
                         │
                         ↓
                  INTENT CHANGE
                         ↓
                 DOWNSTREAM POLICY
```

The model should expose interpretable event/state streams rather than only one classification score.

## 5. Biosemiotic framing

Biosemiotics is the **theoretical lens**, not a shortcut for inventing labels.

The working idea is that a vocal or visual behavior is a sign whose meaning emerges from its interactional context. The same laughter-like acoustic pattern can have different social functions depending on who produces it, when it occurs and what happened immediately before it.

Therefore:

- do not equate MELD `joy` with Duchenne laughter;
- do not claim that a prosodic feature proves emotional state;
- do not treat a social interpretation as a ground-truth label unless it is independently annotated.

The model should first establish reliable observable event detection, then test whether contextual and multimodal information changes the interpretation of those events.

## 6. Scientific contribution target

The strongest version of the project is a **mechanistic decomposition of interaction**:

- **text** provides semantic/discourse context;
- **prosody/paralinguistics** provide delivery and non-semantic state;
- **temporal structure** provides event relationships and reaction latency;
- **vision** provides embodied behavior;
- **fusion** estimates interaction state.

A major result would be evidence that different modalities carry different information at different stages of an interaction.

## 7. Success criteria

The project should be considered scientifically successful only when it demonstrates most of the following:

1. real-label laughter/event performance on independent datasets;
2. robust negatives such as silence, speech and applause;
3. audience-vs-performer attribution;
4. precise onset/offset or reaction latency estimation;
5. improvement from temporal modeling over static chunk classification;
6. incremental information beyond transcript semantics;
7. cross-comedian and cross-domain transfer;
8. calibrated probabilities and confidence intervals;
9. a public reproducible pipeline;
10. an interpretable interaction-signal representation that can support downstream tasks.

## 8. Commercial extension

The commercial thesis is **not** “emotion AI for lending.”

The candidate product is:

> **Interaction Signal API — real-time non-semantic features for voice and multimodal AI systems.**

Possible outputs:
- engagement change
- hesitation
- uncertainty proxy
- interruption
- turn completion
- reaction/laughter
- response latency
- attention change
- frustration proxy
- intent-shift signal

Financial-services use is a downstream experiment, not the definition of the core model. The safe pattern is:

`interaction signal → intent clarification / existing decision engine → permitted next-best-action`

not:

`voice tone → credit/eligibility decision`.

## 9. Explicit exclusions

The active program does not prioritize:
- text-only humor detection;
- generic LLM-based emotion classification;
- unsupported Duchenne-laughter claims;
- covert psychological profiling;
- direct credit-risk inference from voice;
- mental-health diagnosis;
- a large collection of unrelated cognitive modules before the core interaction signal is validated.

## 10. Relationship to previous work

The project history is retained as evidence and negative knowledge. Earlier high-F1 claims remain historical unless they pass the current label hierarchy and provenance rules.

The September 2026 audit established:
- StandUp4AI 118-video honest result: IoU-F1@0.2 = 0.3302;
- Gillick 162-video real-label revalidation: fusion F1 = 0.559, WavLM-only 0.548, prosody-only 0.537;
- 620-video VTT scale-up has sparse labels and must not be interpreted as equivalent to benchmark-truth laughter data.

These are the current anchors for the new program.
