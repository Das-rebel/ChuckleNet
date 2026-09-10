# DECISION_GRAPH.md — HISTORICAL / SUPERSEDED

> **This document is retained as the September 2026 audit record.** It contains important evidence about label tiers, notebook failures, weak-label behavior, and prior decisions. It is no longer the active project decision graph.
>
> **Current canonical decision graph:** `docs/DECISION_GRAPH_V2.md`
> 
> **Current master research program:** `docs/INTERACTION_SIGNAL_RESEARCH_PROGRAM.md`

## Preservation notice

The detailed audit material below is intentionally preserved. In particular, do not delete the result JSONs, checkpoint references, label-forensics notes, or notebook lineage described here. They are research provenance.

## Current interpretation

The old root goal of simply beating the StandUp4AI laughter benchmark has been superseded by a broader scientific question: whether non-semantic interaction signals provide incremental information about interaction state beyond transcript semantics.

The old evidence hierarchy remains useful. Its strongest lessons are now incorporated into `RESEARCH_LINEAGE.md`:

- label provenance must be explicit;
- weak VTT markers are not gold labels;
- historical high-F1 results cannot be used as headlines without reconstructing their label scheme;
- notebook correctness requires execution/logic tests, not just syntax checks;
- the honest StandUp4AI result is a useful benchmark anchor, not the project's entire scientific mission.

## Legacy audit record

The remainder of this file is the original September 2026 audit/decision record. It is preserved verbatim in substance so that earlier reasoning and evidence remain recoverable. New project decisions must be added to `DECISION_GRAPH_V2.md`, not here.

---

# LEGACY CONTENT

The historical decision graph previously defined the root goal as improving laughter detection on StandUp4AI, documented honest-vs-suspect metrics, model/checkpoint lineage, Colab notebook lineage, data-layer findings, dead ends, and the v20/v21 weak-label gate decisions.

Important historical findings include:

- the 118-video StandUp4AI evaluation is below the published benchmark and exposed a real 0.33→0.51 gap;
- the Gillick-162 real-label evaluation is the strongest current acoustic anchor;
- several ~0.96–0.99 historical scores were label-circular or provenance-dependent;
- the 620-video VTT corpus is marker-poor and must not be treated as dense gold laughter data;
- v19/v20 notebook engineering work exposed the need for execution-based validation and timestamp persistence.

For the complete historical text and exact tables, use the Git history for this file and the associated result artifacts. The canonical research interpretation is now maintained in the new documents listed above.
