# Biosemiotic Framework V2

**Status: CANONICAL THEORETICAL FOUNDATION — 2026-09-10**

## 1. Role in ChuckleNet

Biosemiotics provides the **theoretical lens** for the Interaction Signal Research Program. It is not a shortcut for obtaining labels and it does not replace empirical validation.

The core idea is that vocal and embodied behaviors can function as signs within an interaction. Their meaning is shaped by:

- producer;
- recipient/audience;
- temporal position;
- preceding event;
- response;
- interactional context.

## 2. Laughter as a social sign

Laughter is not treated as a single psychological state. The same acoustic event can serve different interactional functions, including affiliative response, amusement, politeness, tension release, turn management or audience participation.

Therefore the computational target should move from:

`audio → emotion label`

toward:

`audio/video + temporal context → observable interaction event → interactional state hypothesis`

## 3. What this changes empirically

A useful model should ask not only whether a window sounds like laughter, but:

- who produced it?
- when did it occur relative to the preceding turn?
- what event preceded it?
- how quickly did the other participant/audience respond?
- did the interaction state change afterward?

This directly motivates temporal modeling and speaker/listener attribution.

## 4. MELD caution

MELD emotion labels can be useful for exploratory alignment, but an emotion label such as “joy” must **not** be treated as direct ground truth for authentic/Duchenne laughter.

The project should not infer biological or psychological mechanisms that the dataset does not independently measure.

## 5. Testable biosemiotic hypotheses

### H1 — relational meaning
The predictive value of a vocal event depends partly on its temporal relation to surrounding interaction.

### H2 — producer/recipient dependence
The same acoustic event has different interactional interpretations depending on whether it comes from the speaker, listener or audience.

### H3 — reaction coupling
Interaction state is better represented by event-response coupling than by isolated events.

### H4 — non-semantic increment
Some interaction-state information survives when lexical semantics are removed or controlled.

### H5 — multimodal convergence
Audio and visual signals provide complementary evidence about interaction state.

## 6. Computational program

```text
SIGNAL
  ↓
EVENT
  ↓
TEMPORAL RELATION
  ↓
INTERACTION STATE
  ↓
STATE TRANSITION
```

This is the computational bridge between the theoretical framework and ChuckleNet's empirical work.

## 7. Scientific standard

Biosemiotic interpretations are hypotheses until supported by:

- independently grounded labels;
- controlled experiments;
- temporal ablations;
- speaker/source independence;
- cross-domain replication.

The theory should generate experiments, not dictate their outcomes.
