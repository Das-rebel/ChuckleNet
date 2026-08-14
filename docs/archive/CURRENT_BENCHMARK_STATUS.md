# Current Benchmark Status

Date: 2026-04-01

## Promoted Model

**Location:** `experiments/xlmr_standup_clause_lexical_tail_pos5_unfreeze4_promoted`

**Recipe:**
- Clause-aware lexical tail context (last 6 tokens from previous clause)
- Positive class weight: 5.0
- Unfreeze last N layers: 4
- Decode: cue-aware topk_span

## Internal Evaluation (Canonical Split)

| Split | F1 | IoU-F1 | Support |
|-------|-----|--------|---------|
| Validation | 0.7500 | 0.8889 | 102 |
| Test | 0.7213 | 0.8261 | 23 |

### Per-Language (Test)
| Language | F1 | IoU-F1 | Support |
|----------|-----|--------|---------|
| English | 0.7609 | 0.8261 | 23 |

### Per-Laughter-Type (Test)
| Type | F1 | IoU-F1 | Support |
|------|-----|--------|---------|
| Continuous | 0.7583 | 0.8333 | 20 |
| Discrete | 0.7778 | 0.7778 | 3 |

## WESR Advanced Companion Benchmark

| Split | Macro F1 | Macro IoU-F1 | Min Type Support |
|-------|----------|--------------|------------------|
| Validation | 0.9959 | 0.9959 | 122 |
| Test | 0.8963 | 0.8963 | 121 |

**Status:** `promotion_ready = true` as companion benchmark (train split has only 18 examples)

## External StandUp4AI Benchmark

**Dataset:** 4 public examples → 28 chunks (128-word window)

| Slice | Precision | Recall | F1 | IoU-F1 | Support |
|-------|-----------|--------|-----|--------|---------|
| Full (cs/en/es/fr) | 0.2789 | 0.1968 | 0.2308 | 0.1980 | 564 |
| English-only | 0.1111 | 0.1075 | 0.1014 | 0.0747 | 118 |

### Per-Language (External)
| Language | F1 | IoU-F1 | Support |
|----------|-----|--------|---------|
| Czech | 0.2463 | 0.2212 | 277 |
| French | 0.2343 | 0.3002 | 97 |
| Spanish | 0.1871 | 0.2074 | 72 |
| English | 0.1014 | 0.0747 | 118 |

## Best Decode Policy

**Cue-aware topk_span:**
- `positive_ratio`: 0.10
- `neighbor_margin`: -2.0
- `max_neighbors`: 2
- `cue_bonus`: 1.0

## Key Findings

1. Cross-lingual transfer works: Czech F1 > French > Spanish > English
2. English is hardest case (F1=0.1014 on external benchmark)
3. Decode-side span expansion lifted English external from 0.0 to 0.1014
4. WESR taxonomy-rich companion shows strong performance (0.8963 test F1)

## Blockers

1. **External data:** Public StandUp4AI repo has no packaged release
2. **22k training:** Timed out on CPU (needs GPU for large-scale training)
3. **Taskmaster CLI:** Blocked by missing API keys

## Next Structural Work

Per LOCAL_TASK_LIST item 55: "Prioritize stronger language/domain conditioning now that decode-side span expansion already pushed the English external slice above zero."
