# ChuckleNet Research Lineage

**Status: CANONICAL PROVENANCE MAP — 2026-09-10**

This document preserves the project's prior work while changing its interpretation and forward direction. Historical experiments are not deleted because they contain implementation knowledge, negative results, provenance, and evidence about what does and does not generalize.

## 1. New interpretation of the project

ChuckleNet began as a laughter detector. It now becomes an **interaction-signal research program**, with laughter as the first well-observed social event.

The central question is:

> Can non-semantic multimodal interaction signals provide incremental information about human interaction state and intent beyond transcript semantics?

Audio/paralinguistics and temporal structure are the current core. Vision is the next modality. Text/ASR remains supporting context and alignment, not the competitive center.

## 2. Major workstreams and their new role

| Prior work | What it actually established | New role | Action |
|---|---|---|---|
| F0 / low-dimensional prosody experiments | Laughter-like vocal events contain learnable low-dimensional acoustic structure | Acoustic-event representation hypothesis | Keep; re-run with stronger controls |
| WavLM experiments | Generic learned acoustic representations provide a useful high-capacity baseline | Representation baseline | Keep |
| Prosody + WavLM fusion | Acoustic representations can be complementary | Multimodal-within-audio baseline | Keep; benchmark honestly |
| Pause / timing experiments | Temporal structure is informative and may be more interactional than lexical content | Temporal interaction hypothesis | Expand substantially |
| Word-level XLM-R / text experiments | Event localization is not solved by transcript semantics alone | Negative evidence against text-first framing | Keep as supporting control; deprioritize |
| MELD / biosemiotic work | Vocal behavior can be framed as social signalling, but dataset labels do not prove biological or Duchenne claims | Theoretical foundation | Reframe; remove unsupported equivalences |
| 620/621-video VTT scale-up | Large-scale weak-label pipeline can expose robustness and data-engineering failure modes | Weak-label stress-test infrastructure | Keep; never treat VTT markers as gold laughter labels |
| Gillick-derived 162-video evaluation | Current strongest real-laughter acoustic anchor; WavLM/prosody/fusion all show moderate, non-trivial performance | Gold-label acoustic anchor | Keep as primary anchor |
| StandUp4AI 118-video evaluation | Current stand-up temporal benchmark anchor; IoU-F1@0.2 ≈ 0.3302 | Domain benchmark | Keep; align metrics precisely |
| Historical 87-video ~0.97 results | High score under an older/retired labeling scheme | Provenance-sensitive historical result | Archive as historical; do not headline |

## 3. What we must stop saying

The following claims are **not canonical** and must not appear as current project conclusions without a new, provenance-matched experiment:

- “5 dimensions of F0 beat 768 dimensions of WavLM by 4.3x.”
- “Hand-crafted prosody definitively beats transformers.”
- “ChuckleNet achieves ~0.95–0.98 F1” without naming the exact label scheme, dataset, split, and IoU definition.
- “MELD joy is Duchenne/authentic laughter.”
- Any claim that the project has already demonstrated commercial intent prediction from voice.

Historical documents containing these claims remain valuable evidence of the project's evolution, but the claims are superseded as project headlines.

## 4. Canonical evidence hierarchy

### Tier A — real or manually anchored laughter labels
Use for primary scientific claims.

1. Gillick-derived real-laughter evaluation: 162 videos, GroupKFold by video, out-of-fold evaluation. Current reported F1: WavLM + prosody 0.559; WavLM-only 0.548; prosody-only 0.537.
2. StandUp4AI: 118-video evaluation with IoU-F1@0.2 ≈ 0.3302 in the current ChuckleNet evaluation.
3. StandUp4AI published literature results are comparison points only after exact task/metric alignment.

### Tier B — weak labels / noisy labels
Useful for scale and engineering, not definitive scientific accuracy.

- VTT caption-marker labels across the 620/621-video scale-up.
- Marker-rich subset analyses.

### Tier C — exploratory / pseudo-label evidence
Useful for hypothesis generation only.

- Retired humor-lexicon/pseudo-label experiments.
- Any experiment where “laughter” is inferred from lexical humor markers rather than independently labeled audio events.

## 5. How prior findings become the new research program

### F0 becomes “low-dimensional acoustic structure”
The useful insight is not that F0 wins universally. The useful question is whether a compact prosodic representation captures **interactionally meaningful acoustic events** that generic embeddings partially obscure or entangle.

Next test: matched negative controls, speaker independence, source independence, and temporal ablations.

### Pause becomes “interactional timing”
The useful insight is not that silence itself is meaningful. It is that the relation between speech, pause, vocal event, and listener reaction may encode state transitions.

Next test: predict event onset/offset, reaction latency, and state change while controlling for pause duration.

### Text failure becomes “semantic sufficiency is limited”
The project should not compete with text models. Instead, text becomes a baseline/control used to ask whether non-semantic signals add information beyond lexical semantics.

### Biosemiotics becomes the theory layer
Laughter is treated as a social sign whose meaning depends on producer, recipient, timing, antecedent event, and interaction context. Empirical claims must come from data, not theory labels.

## 6. What is being built next

```text
Audio event
   ↓
Interaction event
   ↓
Interaction state
   ↓
Intent/state transition
   ↓
Decision support / downstream policy
```

The first model family should remain audio-first. Vision enters after the audio representation and temporal evaluation framework are stable.

## 7. Preservation rules

1. Do not delete historical result files, notebooks, scripts, raw result JSON, or paper drafts solely because their conclusions changed.
2. Do not silently overwrite historical metrics. New metrics must carry a new experiment identifier or canonical result date.
3. Every benchmark claim must identify dataset, labels, split, metric, IoU/tolerance, and evaluation protocol.
4. Old documents should be marked **HISTORICAL / SUPERSEDED** when their recommendations conflict with this vision.
5. Reproducibility artifacts remain part of the research record even when their hypothesis is rejected.

## 8. Document migration map

### Canonical going forward
- `docs/RESEARCH_VISION_V2.md`
- `docs/RESEARCH_LINEAGE.md`
- `docs/INTERACTION_SIGNAL_RESEARCH_PROGRAM.md`
- `docs/DECISION_GRAPH_V2.md`
- `docs/PRD_V7_INTERACTION_SIGNAL.md`
- `docs/COMPETITOR_MAP_2026.md`
- `docs/COMMERCIALIZATION_INTERACTION_SIGNAL_API.md`
- `README.md` after this migration is complete

### Historical but retained
Examples include:
- `docs/CLEAN_PROJECT_PLAN.md`
- `docs/DEFINITIVE_PLAN.md`
- `docs/DECISION_GRAPH.md`
- `docs/COMPLETE_REPLAN.md`
- old F0/pitch papers
- old ablation reports
- old taskmaster execution files
- individual result JSON/MD files

These should remain available for provenance and should not be mistaken for current strategy.
