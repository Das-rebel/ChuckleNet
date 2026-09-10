# From Laughter Detection to Interaction Signals

**Working paper — research draft, not submission-ready**  
**Date:** 2026-09-10  
**Author:** Subhajit Das

## Abstract

Human interaction contains information that is not fully represented by the literal words being spoken. Timing, pitch, energy, hesitation, interruption, laughter, reaction latency and embodied behavior can change how an interaction should be interpreted even when the transcript remains similar. This paper proposes an audio-first research framework for learning these **non-semantic interaction signals**, using laughter detection in stand-up comedy as the initial experimental laboratory.

The central hypothesis is not that one handcrafted feature universally beats a large neural representation. Rather, the hypothesis is that compact acoustic structure and temporal relations may encode interactionally meaningful information that generic speech representations do not isolate cleanly. We therefore decompose the problem into acoustic events, interaction events, interaction-state changes, and downstream decisions. Transcript semantics is treated as a supporting baseline and alignment channel rather than the primary research object.

The current evidence motivates the program but does not yet prove the full thesis. A real-labeled 162-video evaluation provides a current acoustic anchor: WavLM + prosody F1 0.559, WavLM-only 0.548, and prosody-only 0.537 under video-grouped out-of-fold evaluation. A separate StandUp4AI evaluation currently reaches approximately IoU-F1@0.2 = 0.3302 on 118 videos. Historical near-0.97 results are retained as provenance-sensitive experiments and are not used as the paper's headline evidence.

The paper's main contribution is therefore a **testable framework**: robust acoustic-event detection, temporal modeling, speaker/listener attribution, counterfactual evaluation, cross-domain transfer, and measurement of incremental value beyond transcript semantics. Vision is introduced only after the audio-temporal foundation is validated.

**Keywords:** interaction signals, paralinguistics, laughter detection, temporal modeling, multimodal interaction, prosody, reaction timing, social signal processing

## 1. Introduction

Conversation systems have become substantially better at understanding the literal content of speech. Yet a transcript removes or compresses many signals that humans use during interaction: hesitation, overlap, timing, prosodic emphasis, laughter, response latency, interruption and visible behavior. A system that receives only the transcript may therefore know what was said while missing how the interaction is changing.

ChuckleNet studies this gap through a narrower and experimentally tractable starting point: laughter in human interaction. Stand-up comedy is useful because it provides a relatively visible temporal structure:

`setup → delivery → pause → punchline → audience reaction`

Laughter is thus treated not merely as an acoustic class but as an observable event embedded in a relation between a producer, an antecedent event, a recipient or audience, and a response. This framing leads to a broader research problem: can machine learning recover interactional information from non-semantic signals and expose it as a reusable representation?

### Research question

> **Can non-semantic multimodal interaction signals provide incremental information about human interaction state and intent beyond speech transcript semantics?**

### Scope

The active contribution is deliberately not text humor classification. Text/ASR is used for alignment, context and controlled ablations. Audio, temporal structure and later vision are the main research objects.

## 2. Conceptual framework

### 2.1 Interaction-signal hierarchy

The project separates four levels:

1. **Acoustic event:** laughter, speech-laugh, applause, silence, breath, cough/noise.
2. **Interaction event:** turn completion, interruption, hesitation, delayed reaction, audience response.
3. **Interaction state:** engagement, uncertainty proxy, reaction strength, interest shift, agreement/objection and related state hypotheses.
4. **Decision:** continue, pause, clarify, route, recommend, follow up or do nothing.

The machine-learning research focuses on Levels 1–3. Level 4 remains a downstream policy problem.

### 2.2 Biosemiotic framing

Biosemiotics supplies the theoretical lens: a vocal or visual behavior can function as a sign whose interpretation depends on who produced it, who received it, when it occurred, what preceded it and what response followed.

This does not justify treating emotion labels as physiological truth. In particular, an emotion label such as MELD's `joy` cannot by itself establish authentic or Duchenne laughter. Social interpretation remains a hypothesis until independently annotated and experimentally tested.

## 3. Prior evidence and its reinterpretation

### 3.1 Low-dimensional prosody

Earlier experiments suggested that pitch and other compact prosodic features can be predictive of laughter-like events. The scientifically useful conclusion is narrower than the historical headline: compact acoustic structure deserves systematic testing against learned representations and strong negative controls.

### 3.2 WavLM

WavLM provides a useful learned acoustic baseline. Current evidence does not support the claim that WavLM is universally inferior or that handcrafted features universally dominate it. The right question is which representation captures which aspect of an interaction event.

### 3.3 Pause and timing

Prior pause experiments motivate a stronger hypothesis: the **relationship** between speech, silence, a vocal event and a response may contain more information than any individual acoustic snapshot.

### 3.4 Text experiments

Earlier text/XLM-R work is retained as negative evidence against a text-first formulation. Transcript features can help align an interaction but do not need to become the project's competitive center.

## 4. Current evidence anchors

| Experiment | Current role | Result |
|---|---|---|
| Gillick-derived 162 videos | primary real-labeled acoustic anchor | fusion F1 0.559; WavLM 0.548; prosody 0.537 |
| StandUp4AI 118 videos | stand-up temporal benchmark anchor | IoU-F1@0.2 ≈ 0.3302 |
| 620/621-video VTT corpus | weak-label scale study | ~1.16% positive across 243,501 utterances; 174/620 videos with markers |
| Historical high-F1 subsets | provenance/hypothesis only | ~0.96–0.98 under incompatible historical label schemes |

These results establish that the repository contains useful acoustic evidence and substantial label/provenance problems. They do not yet establish a universal state-of-the-art laughter detector or a commercial intent model.

## 5. Proposed method

### 5.1 Audio encoder

The first stage compares:

- F0/pitch statistics;
- energy and RMS;
- spectral and MFCC features;
- pause and timing features;
- WavLM embeddings;
- prosody + learned audio fusion.

The representation is kept modular so the project can test whether compact, learned and hybrid signals capture different information.

### 5.2 Temporal interaction encoder

Static windows are extended with a sequence model over frame- or event-level features. Candidate models include a lightweight temporal convolution, BiGRU or Conformer-style encoder.

The temporal model should estimate:

- event onset and offset;
- turn position;
- response latency;
- preceding-event relation;
- persistence;
- change points and state transitions.

### 5.3 Attribution

Where source structure is available, the system should distinguish:

- performer/speaker laughter;
- listener/interlocutor response;
- audience laughter;
- applause or cheering;
- speech-laugh embedded within speech.

This is essential because the same acoustic event can have different interactional roles.

### 5.4 Future visual branch

Only after the audio-temporal foundation is stable, add:

- facial activation and smile dynamics;
- head movement;
- gaze/orientation proxies;
- gesture and body motion;
- speaker/listener attribution.

The scientific test is whether audio + video provides incremental value over the best audio-only system and transcript/control conditions.

## 6. Experimental design

### 6.1 Counterfactual temporal ablation

The primary discriminating experiment is to construct matched examples with similar acoustic properties but different interactional relations.

1. Shift laughter windows relative to the preceding speech turn while preserving the local acoustic event.
2. Match non-laughter pauses for duration, pitch and energy.
3. Compare:
   - acoustic-only;
   - acoustic + pause;
   - acoustic + turn position;
   - text + audio;
   - full temporal interaction model.

If the full model retains an advantage under these controls, the evidence for temporal interaction structure becomes stronger. If the advantage disappears, that failure is itself a useful scientific result because it identifies a shortcut.

### 6.2 Generalization controls

Every primary experiment should report performance under:

- speaker/person-independent splits;
- source/recording-independent splits;
- dataset-independent tests where possible;
- language/channel stress tests;
- audience-versus-speaker attribution.

### 6.3 Evaluation metrics

For acoustic events:

- precision, recall and F1;
- temporal IoU;
- onset/offset error;
- calibration;
- PR-AUC for sparse-event conditions.

For interaction modeling:

- event-to-response latency error;
- state-transition F1 or AUROC/PR-AUC as appropriate;
- early-detection lead time;
- incremental predictive value over semantic baselines.

## 7. Incremental-value experiment

The ultimate falsification test is not “does audio classify laughter?” but “does a validated interaction signal contain information that a semantic system does not already have?”

### Baseline A
`transcript → intent/state model`

### Baseline B
`transcript + permitted context → intent/state model`

### Candidate C
`transcript + context + interaction signals → intent/state model`

The primary quantity is the incremental change from B to C.

Candidate outputs should be narrow and observable: hesitation, turn completion, interruption, reaction, response latency, engagement-change proxy and related signals. Claims such as “customer is interested” or “customer is deceptive” require separate task definitions and independent validation.

## 8. Cross-domain program

The research should progress from:

`stand-up comedy → conversational speech → voice-agent interaction → contact-center/banking workflows`

Stand-up is a laboratory, not the intended boundary of the representation.

A representation that only works for a particular comedy production style should be treated as domain-specific rather than generalized interaction intelligence.

## 9. Expected scientific contributions

The paper aims to establish four contributions:

1. **A decomposition of human interaction signals** into acoustic events, relational events, state changes and decision boundaries.
2. **A temporal evaluation framework** that separates local acoustic shortcuts from interaction structure.
3. **An incremental-information test** that asks whether non-semantic signals add value beyond transcript semantics.
4. **A reusable signal representation** designed for cross-domain deployment rather than a single task-specific classifier.

## 10. Limitations

This draft intentionally does not claim:

- state-of-the-art laughter detection;
- universal superiority of F0 over deep audio models;
- that MELD joy is authentic/Duchenne laughter;
- causal prediction of human internal psychological states;
- direct credit or eligibility inference from voice;
- that commercial demand has already been proven.

The work is successful if the hypotheses survive rigorous controls. Negative results are publishable and should not be hidden to protect the product narrative.

## 11. Reproducibility policy

Every result must be linked to the experiment registry with:

`dataset + label provenance + sample unit + split + model inputs + preprocessing + metric + threshold + aggregation + seed + artifact`

Historical artifacts are preserved. New analyses receive new experiment identifiers and do not overwrite earlier result files.

## 12. Status

**Research draft. Not submission-ready.**

The immediate scientific target is to establish a robust audio-temporal interaction-event benchmark. Only after that benchmark is stable should the paper make stronger claims about latent interaction state, multimodality or downstream intent value.
