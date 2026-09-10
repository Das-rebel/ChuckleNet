# PRD V7 — Interaction Signal Engine

**Status: CANONICAL PRODUCT/RESEARCH SPEC — 2026-09-10**

## 1. Product thesis

ChuckleNet evolves from a laughter detector into an **Interaction Signal Engine** that exposes measurable, non-semantic signals from human communication.

The product should help downstream voice systems answer questions that transcript semantics alone cannot reliably answer:

- Is the person still engaged?
- Did they hesitate?
- Did they interrupt or complete a turn?
- Did their reaction change after an event?
- Was there a delayed response?
- Did interest appear to shift?

## 2. Primary output

A timestamped signal stream rather than a single emotion label.

Example schema:

```json
{
  "timestamp": 12.84,
  "signals": {
    "engagement": 0.71,
    "hesitation": 0.18,
    "uncertainty_proxy": 0.43,
    "interruption": 0.00,
    "turn_completion": 0.82,
    "reaction": 0.64,
    "reaction_latency_ms": 420
  }
}
```

The exact schema is provisional until validated experimentally.

## 3. Modality strategy

### Core now: audio
- pitch/F0
- energy
- spectral characteristics
- rhythm
- voice quality
- pause duration
- turn timing
- laughter and speech-laugh
- reaction timing

### Next: vision
- facial movement
- gaze/attention proxy
- head movement
- gesture
- body motion
- speaker/listener attribution

### Supporting: text
ASR/transcript semantics are used for alignment, context and incremental-value experiments. Text is deliberately not the competitive center.

## 4. Users / buyers

Potential initial buyers:

1. Voice-agent platforms
2. TTS / speech-to-speech platforms
3. Contact-center intelligence platforms
4. Conversational banking platforms
5. Research teams building multimodal interaction models

## 5. Non-goals

- Generic sentiment analysis
- Text humor classification
- Competing with general-purpose LLMs on emotion reasoning
- Direct credit scoring or creditworthiness inference from voice
- Inferring protected attributes from voice
- Presenting uncertain proxies as objective psychological truth

## 6. MVP

The MVP is **not** a production banking system.

It is a reproducible audio-first research API that takes an audio stream and returns timestamped interaction signals with confidence and provenance metadata.

Minimum signal set:

- laughter/reaction event
- pause/hesitation
- interruption
- turn completion
- response latency
- engagement-change proxy

## 7. Model architecture

```text
Audio
  ↓
Frame-level acoustic encoder
  ├── compact prosody
  ├── spectral features
  └── learned audio embedding
  ↓
Temporal interaction encoder
  ↓
Event heads
  ↓
Interaction-state representation
  ↓
Signal API
```

Vision and transcript/context branches are added as controlled extensions, not required for MVP.

## 8. Evaluation

### Scientific
- F1 / precision / recall for event detection
- IoU / temporal overlap
- onset/offset error
- reaction-latency error
- calibration
- speaker-independent performance
- source-independent performance
- cross-dataset performance

### Incremental value

Compare:

`text → text+context → text+context+interaction signals`

Measure change in intent/state prediction and timing decisions.

## 9. Reliability requirements

Every API output should eventually support:

- confidence
- timestamp
- model version
- signal definition
- known limitations

The API should avoid absolute claims such as “customer is lying” or “customer is interested” unless a separately validated task justifies that label.

## 10. Research-to-product progression

```text
Laughter detection
      ↓
Robust acoustic events
      ↓
Temporal interaction events
      ↓
Latent interaction state
      ↓
Cross-domain validation
      ↓
Incremental value over transcript
      ↓
Signal API
      ↓
Downstream voice-agent / contact-center integrations
```

## 11. Banking use case — future only

A banking voice system could eventually combine:

`ASR semantics + permitted customer/context data + interaction signals → existing intent/NBA policy engine`

The interaction layer should not itself decide eligibility or credit risk. Deployment must respect applicable consent, data minimization, confidentiality, auditability and model-risk requirements.

## 12. Success criteria

The project succeeds scientifically if it demonstrates that non-semantic signals provide stable incremental information across speakers, datasets and domains.

It succeeds commercially only if that incremental information improves a real downstream workflow enough to justify integration cost.

If the incremental value disappears outside stand-up or under strong controls, the commercial thesis should be rejected rather than protected by narrative.
