# Parallel Execution Plan: Two-Track Async Strategy
**Date:** 2026-06-20
**Goal:** Execute two-track strategy with maximum parallelism

---

## ARCHITECTURE: Parallel Task Graph

```
                    ┌─────────────────────────────────────────┐
                    │         TRACK A: arXiv (Quality)        │
                    │                                         │
                    │  Task A1: Refine Paper 1 v3           │
                    │    └─→ Paper 1 v4 (ready for submit)   │
                    │                                         │
                    │  Task A2: Hindi Synthetic (V10)         │
                    │    └─→ 4,000 Hindi examples            │
                    │                                         │
                    │  Task A3: Update findings.md           │
                    │    └─→ Reflect v3 scale narrative       │
                    └─────────────────────────────────────────┘

                    ┌─────────────────────────────────────────┐
                    │       TRACK B: INTERSPEECH (Scale)     │
                    │                                         │
                    │  Task B1: Collection Pipeline           │
                    │    └─→ 500 video candidates            │
                    │                                         │
                    │  Task B2: Tiered Quality Filter        │
                    │    └─→ 46 gold + 300 silver            │
                    │                                         │
                    │  Task B3: Kaggle Setup                 │
                    │    └─→ Ready for extraction             │
                    │                                         │
                    │  Task B4: Feature Extraction Script    │
                    │    └─→ WavLM + Prosody extraction      │
                    └─────────────────────────────────────────┘

                    ┌─────────────────────────────────────────┐
                    │         MONITORING (Background)         │
                    │                                         │
                    │  Task M1: Check arXiv endorsement      │
                    │  Task M2: Check Reddit responses        │
                    │  Task M3: Update status docs           │
                    └─────────────────────────────────────────┘
```

---

## TASK DEPENDENCIES

### Track A: arXiv (Can run parallel to Track B)

| Task | Dependencies | Duration | Output |
|:---|:---|:---|:---|
| A1: Paper 1 refinement | None | 2-4 hours | paper_v4.md |
| A2: Hindi synthetic | None | 1 week | 4K Hindi examples |
| A3: findings.md update | None | 1 hour | Updated docs |

### Track B: INTERSPEECH (Parallel to Track A)

| Task | Dependencies | Duration | Output |
|:---|:---|:---|:---|
| B1: Collection | None | 1-2 weeks | 500 video candidates |
| B2: Quality filter | B1 | 1 week | 46 gold + 300 silver |
| B3: Kaggle setup | None | 2 hours | Kaggle notebook ready |
| B4: Extraction script | B3 | 1 week | WavLM + Prosody embeddings |

### Monitoring (Continuous)

| Task | Dependencies | Duration | Output |
|:---|:---|:---|:---|
| M1: Endorsement check | None | Ongoing | Email/Reddit |
| M2: Reddit responses | None | Ongoing | Comments/DMs |
| M3: Status update | A1, A2, B1 | Hourly | docs updated |

---

## EXECUTION ORDER

### NOW (Parallel Launch)
```python
# Launch immediately
Task A1: Paper 1 refinement
Task A3: findings.md update  
Task B3: Kaggle notebook setup
Task M1: Endorsement monitoring
```

### IN 1 HOUR (After A1, A3 complete)
```python
# After paper refinement
Task A2: Hindi synthetic generation
Task B1: YouTube collection pipeline
```

### IN 1 WEEK (After B1 complete)
```python
# After collection
Task B2: Tiered quality filter
Task B4: Feature extraction preparation
```

### CONTINUOUS (Background monitoring)
```python
# Always running
Task M1: Check endorsement every 4 hours
Task M2: Check Reddit every 2 hours
Task M3: Update status daily
```

---

## FILE MANIFEST

| File | Purpose | Status |
|:---|:---|:---|
| `PARALLEL_EXECUTION_PLAN.md` | This file | ✅ Created |
| `SCALEUP_collection_pipeline.py` | Collection (Brave workaround) | ✅ Ready |
| `STABLE_EXTRACTION_PLAN.md` | Kaggle extraction plan | ✅ Ready |
| `SCALEUP_ARCHITECTURE.md` | Full architecture | ✅ Ready |
| `SCALEUP_EXECUTION_SUMMARY.md` | Execution summary | ✅ Ready |
| `scaleup_comparison_for_council.md` | Council review | ✅ Done |
| `agent_council_synthesis.md` | Council synthesis | ✅ Done |

---

## MEMORY TAGS

```
laughter.two_track_20260620:
- Track A (arXiv): Paper refinement + Hindi synthetic
- Track B (INTERSPEECH): Collection + extraction + Kaggle
- Parallel tasks: A1, A2, A3, B1, B2, B3, B4, M1, M2, M3
- Tiered quality: 6.5% gold + 60% silver
- Hindi synthetic: 48 → 4,000 examples
- Brave workaround: For YouTube collection
- Kaggle P100: For stable extraction
```

---

*Last updated: 2026-06-20*
*Status: Ready for parallel execution*
