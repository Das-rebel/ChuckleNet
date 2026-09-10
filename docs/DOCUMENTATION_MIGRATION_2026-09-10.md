# Documentation Migration & Preservation Map

**Date:** 2026-09-10  
**Status:** CANONICAL MIGRATION RECORD

## Objective

Realign the repository around the Interaction Signal Research Program without destroying the project's experimental history.

## Canonical spine

| Document | Role |
|---|---|
| `RESEARCH_VISION_V2.md` | North-star thesis |
| `RESEARCH_LINEAGE.md` | Provenance and reinterpretation of prior work |
| `INTERACTION_SIGNAL_RESEARCH_PROGRAM.md` | Master research program |
| `DECISION_GRAPH_V2.md` | Scientific gates and decisions |
| `PRD_V7_INTERACTION_SIGNAL.md` | Product/research requirements |
| `COMPETITOR_MAP_2026.md` | Research + commercial landscape |
| `COMMERCIALIZATION_INTERACTION_SIGNAL_API.md` | Commercial translation |
| `README.md` | Public entry point |

## Documents deliberately retained

All prior paper drafts, ablation reports, result files, notebooks, task plans, model checkpoints and dataset artifacts remain in place unless independently proven to be duplicates or unsafe to retain.

Examples of historical planning documents include:

- `CLEAN_PROJECT_PLAN.md`
- `DEFINITIVE_PLAN.md`
- `DECISION_GRAPH.md`
- `COMPLETE_REPLAN.md`
- `30_DAY_IMMEDIATE_ACTION_PLAN.md`
- publication drafts and F0 breakthrough documents
- ablation status/framework/breakthrough reports
- taskmaster and execution notes
- result JSON/MD files

The two major obsolete planning documents `CLEAN_PROJECT_PLAN.md` and `DEFINITIVE_PLAN.md` have been explicitly marked **HISTORICAL / SUPERSEDED**, rather than deleted.

## Interpretation policy

Historical metrics remain historical facts about their respective experiments. They are not silently rewritten. Current claims must use the new evidence hierarchy and identify exact provenance.

## Next documentation passes

1. Reframe the biosemiotic paper as theoretical foundation.
2. Reframe the main laughter paper around robust acoustic/temporal interaction events rather than an unsupported universal F0-vs-transformer claim.
3. Mark specialized old publication/PRD documents as historical where they conflict with the canonical spine.
4. Audit the Hugging Face model card after the canonical model/result registry is finalized.
5. Add an experiment registry so future results cannot silently become detached from their label provenance.

## Safety rule

No bulk deletion, mass renaming or destructive cleanup is part of this migration. Cleanup decisions require a separate audit showing that an artifact is a true duplicate or has no provenance/reproducibility value.
