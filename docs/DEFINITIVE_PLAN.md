# DEFINITIVE_PLAN.md — HISTORICAL / SUPERSEDED

> **This file is retained intentionally for provenance. It is no longer the active project plan.**
>
> The project direction changed on 2026-09-10 from a narrow F0-vs-WavLM laughter-classification thesis to the broader **Interaction Signal Research Program**. Nothing in this historical document should be treated as a current headline claim without re-validation under the new evidence hierarchy.

## What this historical plan captured

The earlier plan centered on the hypothesis that compact F0/prosody features could outperform WavLM on a particular laughter-detection setup. It also correctly identified the need for more videos, independent evaluation and stronger baselines.

Those experiments remain useful. Their interpretation has changed.

## Current interpretation of the F0 work

The F0/prosody experiments are now treated as evidence that **low-dimensional acoustic structure can contain useful information about socially situated vocal events**.

They do **not** establish that F0 universally beats WavLM, nor that a ~0.97 F1 score is the current ChuckleNet benchmark.

The current canonical evidence is maintained in:

- `docs/RESEARCH_VISION_V2.md`
- `docs/RESEARCH_LINEAGE.md`
- `docs/INTERACTION_SIGNAL_RESEARCH_PROGRAM.md`
- `docs/DECISION_GRAPH_V2.md`

## Historical claims that must not be reused as current claims

The old statements about “4.3x better F1,” “F0=0.975,” and universal superiority over deep embeddings were produced under earlier experiment/label configurations. They are retained here because removing them would destroy research provenance, but they are **not canonical conclusions**.

## Historical execution recommendations

The former recommendations to immediately publish the F0 paper, scale only the laughter dataset, and treat commercialization as a small laughter API have been superseded.

The new execution sequence is:

1. evidence/label freeze;
2. adversarial acoustic controls;
3. robust event detection;
4. temporal interaction modeling;
5. attribution and reaction timing;
6. cross-domain validation;
7. audio + vision expansion;
8. incremental-value testing against transcript/context baselines;
9. only then commercial/API validation.

## Preservation note

Do not delete the experiment files, notebooks, result JSONs, model checkpoints, or historical paper drafts referenced by this plan. They are part of the research record and may be required to reproduce, audit or reinterpret earlier findings.
