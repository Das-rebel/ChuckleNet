# CLEAN_PROJECT_PLAN.md — HISTORICAL / SUPERSEDED

> **Retained intentionally. Do not use this document as the current execution plan.**
>
> This file records the August 2026 cleanup/restructuring state and its then-current interpretation of the experiments. The repository now uses an Interaction Signal Research Program as its canonical direction.

## Why this file is retained

This document contains useful provenance about:
- conflicting label schemes;
- sparse-label failure modes;
- old dataset inventories;
- model/checkpoint names;
- previous cleanup assumptions;
- experiments that should remain reproducible.

Those details should not be erased simply because the research question evolved.

## Superseded conclusions

The following statements from the original version are no longer project conclusions:

- F1≈0.975 as the primary ChuckleNet headline;
- a direct claim that F0/prosody beats WavLM by a fixed multiple;
- immediate paper submission based on the old 87-video setup;
- deletion of sparse-label datasets or old experiment directories;
- treating a single label scheme as the canonical laughter ground truth.

Some of these may become valid again after a provenance-matched re-run, but that requires a new experiment.

## Current canonical path

See:

1. `docs/RESEARCH_VISION_V2.md`
2. `docs/RESEARCH_LINEAGE.md`
3. `docs/INTERACTION_SIGNAL_RESEARCH_PROGRAM.md`
4. `docs/DECISION_GRAPH_V2.md`
5. `docs/PRD_V7_INTERACTION_SIGNAL.md`
6. `docs/COMPETITOR_MAP_2026.md`
7. `docs/COMMERCIALIZATION_INTERACTION_SIGNAL_API.md`

## Preservation rule

Do not delete the datasets, notebooks, model checkpoints, result files or experiment logs described in the historical plan. First determine whether they are reproducibility artifacts, source data, intermediate outputs, or true duplicates. Only an explicit future cleanup decision should remove anything.
