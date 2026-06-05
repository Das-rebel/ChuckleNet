# Architecture Decision Records (ADRs)
## Autonomous Laughter Prediction Project

---

## ADR-001: Consolidate to V8/V8.1 Training Pipeline

### Status: ACCEPTED

### Context
The project has multiple training systems:
- `train.py` (552 lines) - Complex, NOT working, uses cognitive modules
- `train_v8_fixed.py` (157 lines) - Simple, WORKS
- `V8_1_FIXED_SCRIPT.py` (518 lines) - Working, in progress

### Decision
**Deprecate `train.py`** in favor of `train_v8_fixed.py` / `V8_1_FIXED_SCRIPT.py`.

### Rationale
- V8/V8.1 scripts produce working models (F1 0.785+)
- `train.py` complexity provides no benefit
- Cognitive modules from `core/` are not connected to actual training

### Consequences
- Must archive or remove `train.py`
- Training docs must reference V8/V8.1 scripts only
- Any future work should extend V8 scripts, not revive `train.py`

---

## ADR-002: Use Pre-Labeled StandUp4AI Data BEFORE Transcribing

### Status: ACCEPTED

### Context
StandUp4AI has:
- 4 pre-labeled videos with word-level L/O labels (3,203 words)
- 195 transcripts already collected locally
- 3,617 videos total but only ~250K words actually transcribed

### Problem
Current approach (transcribe everything first) is backwards. We'd have 3,400+ transcribed videos with NO laugh labels.

### Decision
**Train on existing labels FIRST, then propagate to remaining videos.**

```
PRIORITY 1: TRAIN on 3,203 labeled words (Examples_label/)
PRIORITY 2: APPLY to 195 existing transcripts
PRIORITY 3: GENERATE labels for remaining videos (if needed)
PRIORITY 4: RETRAIN on full labeled dataset
```

### Rationale
- Pre-labeled data exists and should be used immediately
- Validates model quality before scaling
- Avoids spending compute on unlabeled data

### Consequences
- Must create training script using Examples_label/ CSVs
- Must verify model quality on existing transcripts before scaling

---

## ADR-003: Remove or Fix Audio Pipeline

### Status: ACCEPTED (fix required)

### Context
Audio laugh detection is fundamentally broken:
```
energy_threshold.py uses: mean_energy + 1.5 * std_energy
Problem: Studio recordings (The Big Bang Theory) have NO laugh track energy signature
```

The `laugh_track_analyzer.py` has simulated detection (comment: "would use audio in production").

### Decision
**Either fix properly or remove entirely.**

If audio is required:
- Use spectral features (not energy threshold)
- Train on properly labeled audio segments (not simulated)
- Consider pitch-based laughter detection

If audio is not required:
- Remove `audio_wav2vec_train.py` and `laugh_track_analyzer.py`
- Document that system is TEXT-ONLY

### Rationale
- Current approach cannot detect laughter in clean studio audio
- Wav2Vec2 training requires labeled audio (which we don't have)
- Broken code creates false confidence

### Consequences
- If removed: System becomes text-only, simpler to maintain
- If fixed: Requires significant audio ML expertise and properly labeled data

---

## ADR-004: Do Not Use Teacher Refinement Until Bug is Fixed

### Status: ACCEPTED

### Context
Teacher refinement (using Nemotron LLM to relabel weak labels) resulted in:
- F1 dropped from **0.78 → 0.078** (10x worse)
- Root cause: parsing or matching error in `refine_weak_labels_nemotron.py`
- Result: 0% laughter detected in refined labels

### Decision
**Disable teacher refinement until bug is identified and fixed.**

### Rationale
- Current results are catastrophic (10x worse than baseline)
- Cannot trust any model trained on refined labels
- The bug is likely in text parsing or label matching, not the LLM

### Consequences
- Must use original weak labels (which work at F1 0.785)
- Bug must be fixed before re-enabling refinement
- May need to add validation checks before promoting refined model

---

## ADR-005: Cognitive Modules in `core/` Are Unused - Decide Their Fate

### Status: OPEN

### Context
The project contains cognitive architecture modules in `core/`:
- `tom/theory_of_mind.py` (79 lines)
- `clost/clost.py` (79 lines)
- `sevade/sevade.py` (54 lines)
- `gcacu/gcacu.py` (90 lines)
- `core/integrated_model.py` - combines all modules

**These are NOT used in actual V8/V8.1 training.**

### Decision Options

**Option A: Integrate into Training**
- Modify V8/V8.1 scripts to use cognitive modules
- Test if they improve F1 performance
- Requires significant refactoring

**Option B: Remove from Codebase**
- Delete `core/` directory entirely
- Reduces code complexity
- Documents that these were "aspirational" not "production"

**Option C: Keep But Document as Experimental**
- Keep modules but clearly mark as unused
- No active maintenance
- May be used in future research

### Rationale
Unused code creates maintenance burden and confusion. The architecture review found these modules add complexity without functional contribution.

### Consequences
- Option A: Risk of introducing new bugs, potential reward of improved model
- Option B: Cleaner codebase, lost opportunity for improvement
- Option C: Preserves research potential but maintains confusion

---

## ADR-006: Data Format Conversion Must Be Centralized

### Status: ACCEPTED

### Context
The project has systematic data format issues:
- GitHub data: `{words: [...], labels: [...]}` (word-level)
- Training expects: `{text: "...", label: 0|1}` (sentence-level)
- `train_v8_fixed.py` includes conversion function

This mismatch appears repeatedly as a bug pattern.

### Decision
**Create centralized data format utilities with explicit validation.**

```
data_formats/
├── word_level.py      # {words, labels} format
├── sentence_level.py  # {text, label} format
├── convert.py         # Conversion functions with validation
└── validate.py       # Format validation utilities
```

### Rationale
- Conversion logic scattered across multiple scripts
- No validation means silent failures
- Centralized conversion enables consistent handling

### Consequences
- Must refactor existing training scripts
- Must add format validation to data loading
- May break existing data pipelines if format changes

---

## ADR-007: StandUp4AI Claims Do Not Match Reality - Must Reconcile

### Status: ACCEPTED

### Context
| Claim | Reality |
|-------|---------|
| 3,617 videos | Yes, but only ~250K words transcribed |
| 3M words | NO - actual is ~250K (8% of claim) |
| 3 languages | NO - only en, zh confirmed |
| Pre-labeled data | YES - 3,203 words in Examples_label/ |
| Processed data dir | NO - `data/standup4ai_processed/` doesn't exist |

### Decision
**Reconcile docs with reality or fix the discrepancy.**

Options:
1. **If claims are aspirational**: Update docs to say "target: 3M words" not "we have 3M words"
2. **If claims are wrong**: Update to reflect actual state (250K words)
3. **If claims are future**: Document clearly what must be done to achieve them

### Rationale
Documentation that doesn't match reality creates false expectations and misleads contributors.

### Consequences
- Must audit all docs claiming StandUp4AI metrics
- Must decide what "done" looks like for StandUp4AI integration
- Must update paper claims if they exceed actual data

---

## ADR-008: Ablation Study Completes Before Scale

### Status: ACCEPTED

### Context
The V8.1 ablation study (`V8_1_FIXED_SCRIPT.py`) is the current active work:
- Tests biosemotic auxiliary tasks (27 dimensions)
- Tests positive class weight variations (4, 5, 6)
- Tests epoch counts

### Decision
**Complete ablation study before scaling to StandUp4AI data.**

### Rationale
- Resources should focus on validating current approach before expanding
- Ablation results inform which features actually help
- Scale work on proven foundation, not experimental setup

### Consequences
- Ablation must complete (est. 20-30 experiments)
- Results inform StandUp4AI training approach
- May reveal that some "necessary" features are actually harmful

---

## Summary: Open Decisions

| ADR | Status | Action Required |
|-----|--------|-----------------|
| ADR-001 | ACCEPTED | Archive `train.py`, update docs |
| ADR-002 | ACCEPTED | Create training script for Examples_label/ data |
| ADR-003 | ACCEPTED | Decide: fix audio or remove it |
| ADR-004 | ACCEPTED | Disable teacher refinement, fix bug |
| ADR-005 | OPEN | Choose: integrate, remove, or preserve experimental |
| ADR-006 | ACCEPTED | Centralize data format conversion |
| ADR-007 | ACCEPTED | Reconcile StandUp4AI claims vs reality |
| ADR-008 | ACCEPTED | Complete ablation before scale |

---

## Metadata

- **Created**: 2026-05-04
- **Author**: PI Architecture Review
- **Last Updated**: 2026-05-04
- **Status**: IN PROGRESS - decisions being implemented