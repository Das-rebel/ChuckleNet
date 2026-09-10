# ChuckleNet Documentation Status V2

**Date:** 2026-09-10  
**Status:** CANONICAL

This map prevents the repository from having multiple documents that appear to be the current plan.

## Canonical

| File | Role |
|---|---|
| `docs/RESEARCH_VISION_V2.md` | research north star |
| `docs/RESEARCH_LINEAGE.md` | history and reinterpretation |
| `docs/INTERACTION_SIGNAL_RESEARCH_PROGRAM.md` | master research program |
| `docs/DECISION_GRAPH_V2.md` | scientific gates |
| `docs/EXPERIMENT_REGISTRY.md` | experiment provenance control |
| `docs/PRD_V7_INTERACTION_SIGNAL.md` | product/research requirements |
| `docs/BIOSEMIOTIC_FRAMEWORK_V2.md` | theory layer |
| `docs/PAPER_INTERACTION_SIGNAL_V1.md` | current paper direction |
| `docs/COMPETITOR_MAP_2026.md` | competitive landscape |
| `docs/COMMERCIALIZATION_INTERACTION_SIGNAL_API.md` | commercial hypothesis |
| `docs/MODEL_CARD_V3_INTERACTION_SIGNAL.md` | model-card source of truth |
| `docs/PICLI_EXECUTION_MANDATE_V1.md` | Pi CLI execution handoff and operating gates |
| `docs/DOCUMENTATION_MIGRATION_2026-09-10.md` | migration and preservation policy |
| `docs/DOCUMENTATION_STATUS_V2.md` | this status map |
| `README.md` | public repository entry point |

## Historical / superseded

These files remain valuable but are no longer strategy sources:

- `docs/CLEAN_PROJECT_PLAN.md`
- `docs/DEFINITIVE_PLAN.md`
- `docs/DECISION_GRAPH.md`
- `docs/COMPLETE_REPLAN.md`
- `ACL_EMNLP_PUBLICATION_DRAFT.md`
- `AAAI_2027_MELD_BIOSEMIOTIC_PAPER.md`
- `AAAI_MULTI_MODAL_PUBLICATION_PLAN.md`
- `docs/paper_f0_breakthrough.md`
- old ablation status/framework/breakthrough reports
- old taskmaster plans and execution notes

Historical result JSON, notebooks, checkpoints and data artifacts are **not** automatically historical in the sense of being unusable. They remain experimental evidence and must be interpreted through `RESEARCH_LINEAGE.md` and `EXPERIMENT_REGISTRY.md`.

## Rules

1. New strategic documents must point to the canonical spine.
2. Historical documents are not silently rewritten to make the history look cleaner.
3. Current performance claims must use registered evidence.
4. A high score does not override label provenance.
5. Do not delete artifacts during documentation migration unless an independent duplicate/retention audit justifies it.
6. If a historical document is updated for clarity, its historical status must remain explicit.
7. Pi CLI execution plans must use `docs/PICLI_EXECUTION_MANDATE_V1.md` for operational priorities and must not silently redefine the research north star.

## Current one-line direction

> **Build an audio-first, temporally grounded, eventually multimodal representation of non-semantic interaction signals, and prove whether those signals add information beyond transcript semantics.**
