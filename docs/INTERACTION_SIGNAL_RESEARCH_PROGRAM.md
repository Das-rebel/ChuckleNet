# Interaction Signal Research Program

**Status: CANONICAL — v1.0 — 2026-09-10**

## 1. Mission

Build a scientifically defensible representation of **non-semantic interaction signals** in human communication.

Laughter is the entry point because it is temporally observable and socially structured. The long-term target is not “better laughter classification”; it is an interaction-signal layer that detects events and state changes that transcript semantics alone cannot fully represent.

## 2. Core research question

> **Can non-semantic multimodal interaction signals provide incremental information about human interaction state and intent beyond speech transcript semantics?**

## 3. Research questions

- **RQ1 — Acoustic structure:** What compact acoustic/prosodic structures reliably distinguish interaction events?
- **RQ2 — Temporal structure:** Does the temporal relation among speech, pause, vocal event and response carry information beyond frame acoustics?
- **RQ3 — Attribution:** Can we distinguish speaker laughter, interlocutor reaction, audience laughter, applause and other non-speech events?
- **RQ4 — State:** Can event sequences predict engagement, hesitation, uncertainty, alignment, interruption, or reaction shifts?
- **RQ5 — Incremental value:** Do these signals improve intent/state prediction beyond ASR transcript semantics and available context?
- **RQ6 — Generalization:** Do representations transfer across speakers, recording conditions, languages and domains?
- **RQ7 — Multimodality:** Does adding visual behavior materially improve interaction-state inference after audio is controlled?
- **RQ8 — Decision utility:** Can the signals improve downstream timing or policy decisions without becoming a proxy for protected or inappropriate judgments?

## 4. Signal hierarchy

### Level 1 — acoustic events
Laughter, speech-laugh, applause, silence, breath, cough/noise, speaker laughter, audience reaction.

### Level 2 — interaction events
Turn completion, interruption, hesitation, delayed reaction, engagement increase/decrease, conversational alignment, reaction onset/offset.

### Level 3 — interaction state
Uncertainty proxy, frustration proxy, attention/engagement, question resolution, objection, agreement, interest shift, reaction strength.

### Level 4 — downstream decision
Continue, pause, clarify, route, provide information, recommend, follow up, or do nothing.

**ML owns Levels 1–3. A policy/decision engine owns Level 4.**

## 5. Unified architecture

```text
                    HUMAN INTERACTION
                           │
             ┌─────────────┼─────────────┐
             │             │             │
           AUDIO         VIDEO          TEXT
             │             │             │
       paralinguistics   behavior     semantics
       prosody           attention    alignment
       timing            gesture      context
             │             │             │
             └─────────────┼─────────────┘
                           ↓
                INTERACTION SIGNAL ENGINE
                           ↓
                  LATENT INTERACTION STATE
                           ↓
             ┌─────────────┼─────────────┐
             │             │             │
           event       state change    timing
         laughter      engagement      latency
         applause      hesitation      persistence
       interruption    uncertainty     reaction
                           │
                           ↓
                    INTENT CHANGE
                           ↓
                    DOWNSTREAM POLICY
```

## 6. Experimental ladder

### Phase 0 — evidence hygiene
- Freeze canonical datasets and label definitions.
- Create an experiment registry.
- Record dataset version, label provenance, split, metric, IoU/tolerance and model inputs for every result.
- Separate gold/manual labels from weak and pseudo labels.

### Phase 1 — acoustic event foundation
Benchmark:
- F0/pitch statistics
- energy/RMS
- spectral features
- MFCCs
- pause/timing features
- WavLM
- prosody + WavLM fusion

Required controls:
- speech without laughter
- silence/pause
- applause/cheering
- audience laughter
- speaker laughter
- speech-laugh
- cough/breath/noise

### Phase 2 — temporal interaction modeling
Move from independent chunks to sequences.

Candidate models:
- temporal convolution
- BiGRU
- lightweight Conformer
- transformer over frame-level interaction features

Targets:
- onset/offset
- reaction latency
- turn position
- preceding-event relation
- event persistence
- state transition

### Phase 3 — counterfactual evaluation
Construct matched examples where acoustic properties are similar but temporal/interaction context differs.

Primary test:
1. matched laughter windows with shifted relation to preceding speech;
2. matched non-laughter pauses with similar duration, F0 and energy;
3. compare acoustic-only, acoustic+pause, acoustic+turn-position, text+audio, and full temporal models.

A genuine interaction representation should retain explanatory power under these controls rather than merely exploiting obvious acoustic or lexical shortcuts.

### Phase 4 — multimodal expansion
Add visual signals only after audio/temporal baselines are stable:
- facial movement
- head movement
- gaze/attention proxy
- gesture
- body motion
- speaker/listener attribution

Test audio-only vs video-only vs audio+video, with and without text context.

### Phase 5 — cross-domain transfer
Evaluate on:
- stand-up comedy
- conversational speech
- voice-agent interactions
- customer-service/contact-center recordings where lawful and appropriately consented
- multilingual Indian speech where data rights permit.

The key test is not absolute performance on one domain but **incremental information that survives domain shift**.

### Phase 6 — decision utility
Only after Levels 1–3 are validated:

```text
ASR semantics + CRM/context
             │
             ├───────────────┐
             ↓               ↓
      baseline intent   interaction signals
             │               │
             └───────┬───────┘
                     ↓
             intent/state model
                     ↓
               policy / NBA
```

Measure incremental value rather than claiming causal business impact prematurely.

## 7. Current evidence anchors

| Evidence | Current interpretation |
|---|---|
| Gillick-derived 162-video real-laughter evaluation | Strongest current acoustic anchor; WavLM + prosody F1 0.559, WavLM 0.548, prosody 0.537 under video-grouped OOF evaluation |
| StandUp4AI 118-video evaluation | Current stand-up temporal benchmark anchor; IoU-F1@0.2 ≈ 0.3302 |
| 620/621-video VTT scale-up | Weak-label/data-engineering stress test; not gold-label accuracy |
| Historical ~0.97 experiments | Provenance-sensitive and label-scheme dependent; not a current headline |

## 8. Benchmark policy

Every reported score must include:

`dataset + label provenance + sample unit + split + model inputs + metric + IoU/tolerance + thresholding + aggregation`

Never compare scores from different definitions as though they were directly equivalent.

## 9. Generalization requirements

A candidate interaction-signal representation should be tested for:

- speaker independence
- comedian/person independence
- source/recording independence
- dataset independence
- language robustness
- microphone/channel robustness
- audience-vs-speaker attribution
- temporal robustness

## 10. Commercial translation

The research output should eventually be exposable as an **Interaction Signal API**, not an “emotion API.” Candidate outputs are real-time or near-real-time time series:

- engagement
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

Potential customers include voice-agent platforms, speech/TTS systems, contact-center intelligence vendors, and banking conversational platforms.

Financial services should be treated as a downstream application, not as the scientific definition of the model. Do not infer creditworthiness, eligibility, risk, or protected attributes directly from voice.

## 11. Go / no-go gates

### Gate A — acoustic validity
Proceed only if performance survives adversarial negatives and speaker/source-independent evaluation.

### Gate B — temporal value
Proceed only if temporal structure adds measurable information beyond frame-level acoustics.

### Gate C — cross-domain value
Proceed only if the representation transfers beyond stand-up comedy.

### Gate D — semantic increment
Proceed to commercial intent experiments only if interaction signals add statistically meaningful information beyond transcript/context baselines.

### Gate E — decision utility
Commercialize only if the incremental signal is stable, interpretable enough for deployment, privacy-compatible, and useful to a downstream policy engine.

## 12. Publication strategy

Potential papers should follow the scientific sequence:

1. **Acoustic interaction events:** compact prosodic structure and robust laughter/event detection.
2. **Temporal interaction signals:** reaction timing, attribution and state transitions.
3. **Multimodal interaction representation:** audio + vision + supporting text.
4. **Interaction signal utility:** incremental value beyond transcript semantics.

The biosemiotic work should function as theoretical framing across this program, not as a substitute for empirical labels.

## 13. Repository governance

This file is the master research plan. If another planning document conflicts with it, the other document must be marked historical/superseded or explicitly justified as a specialized execution plan.
