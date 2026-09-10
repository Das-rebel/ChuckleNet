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
| `docs/PICLI_EXECUTION_MANDATE_V3.md` | **current Pi CLI execution control plane** |
| `docs/SUPPORTING_RESEARCH_AND_HYPOTHESES_V2.md` | supporting literature and hypothesis map |
| `docs/DOCUMENTATION_MIGRATION_2026-09-10.md` | migration and preservation policy |
| `docs/DOCUMENTATION_STATUS_V2.md` | this status map |
| `README.md` | public repository entry point |

## Historical / superseded

These files remain valuable but are no longer strategy sources:

- `docs/PICLI_EXECUTION_MANDATE_V2.md` — superseded by V3; retained for provenance
- `docs/PICLI_EXECUTION_MANDATE_V1.md` — superseded by V2/V3; retained for provenance
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

## Execution clarification — September 10, 2026

The current Pi CLI operating model deliberately compresses the research ladder for a resource-constrained project.

The governing research question is:

> **Can machines extract, learn, and model useful information from how humans interact that is not contained in the literal words they use?**

The formal test is whether non-semantic interaction signals provide incremental information about interaction state and intent beyond transcript semantics/context.

The priority sequence is:

`repository archaeology → E01 robust event validation → E02 temporal information gain → E03 semantic increment → E04 cross-domain transfer → E05 conditional multimodal expansion`

Commercial discovery runs in parallel:

`qualified discovery → serious design partner → retrospective/sandbox pilot → commercial proof → funding decision`

Funding relationship-building begins now; a formal raise is triggered by convergence of technical de-risking and customer pull rather than by completion of the entire research roadmap.

## Rules

1. New strategic or execution documents must point to the canonical spine.
2. Historical documents are not silently rewritten to make the history look cleaner.
3. Current performance claims must use registered evidence.
4. A high score does not override label provenance.
5. Do not delete artifacts during documentation migration unless an independent duplicate/retention audit justifies it.
6. If a historical document is updated for clarity, its historical status must remain explicit.
7. Pi CLI must follow `docs/PICLI_EXECUTION_MANDATE_V3.md` for operational priorities.
8. Pi CLI should prefer the smallest experiment that can falsify or strengthen the active hypothesis.
9. New model complexity requires a stated hypothesis-level reason.
10. Commercial claims must distinguish discovery, design partnership, pilot evidence and paid revenue.

## Current one-line direction

> **Build an audio-first, temporally grounded, eventually multimodal representation of non-semantic interaction signals, and prove whether those signals add information beyond transcript semantics.**
