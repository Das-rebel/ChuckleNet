# ChuckleNet Priority Execution Plan
**Date:** 2026-06-15
**Goal:** Execute all priorities in order to achieve domain leadership

---

## PRIORITY 1: CRITICAL FIXES (Week 1-2)

### P1.1: Fix MultiLinguahah Citation
```
STATUS: Must fix before any publication
ACTION: Replace fake "MultiLinguahah, 2026" with real papers
REPLACEMENTS:
- "YouTube subtitle laugh marker validation" → StandUp4AI (Barriere et al., 2025)
- "Purandare & Litman (2006)" - pause threshold for laughter
- "Bertero & Fung (2016)" - canned laughter detection
FILES TO UPDATE:
- PAPER_EMNLP_INDUSTRY_2026.md
- ADR.md
- DECISIONS_MAP.md
- findings.md
- OPTIMIZATION_PLAN_V2.md
- LAUGHTER_PREDICTION_RESEARCH_VISION.md
- PRD_*.md files
- RESEARCH_LOOP.md
```

### P1.2: Correct Language Claims
```
STATUS: Claims 5-10 languages, actual is 3
ACTION: Update all docs to reflect actual language count
ACTUAL:
- English: ~12,000 utterances
- Chinese: ~2,500 utterances
- Hindi/Hinglish: 48 utterances (statistically meaningless)
FILES TO UPDATE: All PRD and paper files
```

### P1.3: Rewrite EMNLP Paper Framing
```
STATUS: Paper misframes "gate collapses" as failure
ACTION: Rewrite to emphasize audio generalization
OLD FRAMING: "Fusion adds nothing because gate→1.0"
NEW FRAMING: "Audio generalizes 2x better than text (0.28 vs 0.15 held-out)"
PRIMARY METRIC: 0.587 ensemble held-out (not 0.819 random split)
```

---

## PRIORITY 2: HIGH-ROI TECHNICAL ACTIONS (Week 3-4)

### P2.1: Fine-Tune WavLM with LoRA
```
EXPECTED: +25-30% F1 (0.60 → 0.85)
CURRENT: Frozen WavLM = 60.8% (random), 28% (held-out)
TARGET: Fine-tuned WavLM = 85%+ held-out

TASKS:
1. Load WavLM-Base+ checkpoint
2. Add LoRA adapters (rank=32, alpha=64)
3. Fine-tune on utterance-level laughter detection
4. Evaluate on held-out comedians

OUTPUT: experiments/wavlm_finetuned/results.json
TIMELINE: 4-6 hours
```

### P2.2: Extract eGeMAPS Features
```
EXPECTED: +5-10% prosody F1
CURRENT: 21-dim prosody (6 active)
TARGET: 88-dim eGeMAPS + proper pause extraction

TASKS:
1. Install openSMILE
2. Extract eGeMAPS v01a for all 15,000 utterances
3. Verify pause_before, pause_after features included
4. Retrain prosody classifier

OUTPUT: data/egemaps_features/
TIMELINE: 4-6 hours
```

### P2.3: Statistical Significance Testing
```
EXPECTED: Validate ensemble improvement is real
CURRENT: Ensemble 0.587 vs WavLM 0.28 (delta=0.30)
NEEDS: Bootstrap CI + permutation test

TASKS:
1. Bootstrap resampling for F1 confidence intervals
2. Permutation test for ensemble vs unimodal
3. Report p-values

OUTPUT: experiments/significance_testing/results.json
TIMELINE: 2 hours
```

---

## PRIORITY 3: ARCHITECTURE IMPROVEMENTS (Week 5-6)

### P3.1: Build Cascade Architecture
```
EXPECTED: Better boundary precision, improved held-out
CURRENT: Single-stage classifier
TARGET: Two-stage text→prosody cascade

ARCHITECTURE:
Stage 1: XLM-R text → propose likely laugh REGIONS (coarse)
Stage 2: Prosody/audio → refine BOUNDARIES within regions

TASKS:
1. Implement XLM-R span proposal
2. Extract prosody features for regions
3. Train boundary refinement model
4. Evaluate IoU-F1 improvement

OUTPUT: training/cascade_architecture.py
TIMELINE: 8-12 hours
```

### P3.2: Validate on External Benchmarks
```
EXPECTED: Establish SOTA comparison
CURRENT: Only internal evaluation
TARGET: UR-FUNNY, StandUp4AI benchmarks

TASKS:
1. Obtain UR-FUNNY dataset
2. Run same evaluation pipeline
3. Compare to published SOTA

OUTPUT: experiments/benchmark_results/
TIMELINE: 8-12 hours
```

---

## PRIORITY 4: PUBLICATION (Week 7-8)

### P4.1: Write Negative Result Paper
```
STATUS: Ready to write NOW (no new experiments needed)
TITLE: "When Text Memorizes and Audio Generalizes"
FINDING: Text overfits (0.819→0.152), audio generalizes (0.28)

CONTRIBUTION:
- First demonstration of comedian-specific memorization in text models
- Audio as reliable modality for production deployment
- Probability ensemble as correct fusion strategy

TIMELINE: 1-2 weeks to draft
```

### P4.2: Write Positive Result Paper (after P2.1+P2.2)
```
STATUS: Ready after fine-tuning experiments
TITLE: "Audio-Dominant Laughter Prediction with WavLM+Prosody Fusion"
TARGET: 0.75+ held-out F1

CONTRIBUTION:
- Fine-tuned WavLM for comedy (first application)
- eGeMAPS prosody features for boundary precision
- Cascade architecture for role separation

TIMELINE: 2-3 weeks after experiments complete
```

---

## EXECUTION TRACKING

### Week 1-2: Documentation Fixes
- [ ] P1.1: Fix MultiLinguahah citation → StandUp4AI
- [ ] P1.2: Correct language claims (3, not 5/10)
- [ ] P1.3: Rewrite EMNLP paper framing

### Week 3-4: Technical Improvements
- [ ] P2.1: Fine-tune WavLM with LoRA
- [ ] P2.2: Extract eGeMAPS features
- [ ] P2.3: Statistical significance testing

### Week 5-6: Architecture
- [ ] P3.1: Build cascade architecture
- [ ] P3.2: Validate on external benchmarks

### Week 7-8: Publication
- [ ] P4.1: Submit negative result paper
- [ ] P4.2: Submit positive result paper (if P2.1+P2.2 complete)

---

## IMMEDIATE NEXT ACTIONS (TODAY)

1. **Fix citation in EMNLP paper** (P1.1)
2. **Correct language count** (P1.2)
3. **Rewrite paper abstract** (P1.3)
