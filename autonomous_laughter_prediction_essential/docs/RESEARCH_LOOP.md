# Research Loop — Two-Loop Methodology for Laughter Prediction

**Project:** autonomous_laughter_prediction (ChuckleNet)
**Based on:** Orchestra Research AI-research-SKILLs (v1.0.0)
**Last Updated:** 2026-05-24

---

## Overview

The two-loop architecture drives all research in this project. It separates **fast iteration** (inner loop) from **periodic synthesis** (outer loop), preventing the common failure mode of running experiments without ever understanding what they mean.

```
BOOTSTRAP (once, at project start)
  Scope question → search literature → form initial hypotheses

INNER LOOP (fast, autonomous, repeating)
  Pick hypothesis → write protocol.md → experiment → measure → record → next

OUTER LOOP (periodic, every 5-10 experiments or when stuck)
  Review results → find patterns → update findings.md → new hypotheses → decide direction

FINALIZE (when outer loop says "conclude")
  Write paper via ml-paper-writing → final presentation → archive
```

---

## 1. BOOTSTRAP — How We Scoped the Question

Bootstrap is a one-time phase to understand the landscape before committing to experiments. Keep it efficient — the goal is to start iterating, not to write a literature review.

### Our Bootstrap Summary

**Research question:** Can we predict laughter from stand-up comedy audio + text?

**What we searched:**
- Purandare (2006) — pause detection at 0.8s threshold
- Pickering (2009) — F0 DROP at punchlines (Cohen's d=0.24)
- Bachorowski (2001) — laughter F0 in 250-500Hz band
- MultiLinguahah (2026) — BYOL-A cross-lingual audio encoder
- Gillick (2019) — span-based audio detection (F1=0.89)
- Bertero (2016) — pause duration as strongest single acoustic feature

**Initial hypotheses formed (H6-H14):**
- H6: Prosody (F0, energy, pause) — based on Pickering + Purandare
- H7: ToM (political comedy)
- H8: Text+Prosody combination
- H12: Interaction Model (200ms chunks, no VAD)
- H13: MultiLinguahah (BYOL-A + Isolation Forest)
- H14: Hybrid fusion

**Key gap identified:** All prior work operates at utterance or segment level. Word-level analysis is underexplored. Our dataset (549K word-level segments from 71 videos) enables this.

**Baseline established before iterating:**
- XLM-R text-only word-level: F1=0.819 (validation), F1=0.819 (test)
- TF-IDF baseline: F1=0.73
- Audio-only prosody baseline: F1=0.27 (too granular — laughter is supra-segmental)

### When to Bootstrap

| Situation | Action |
|-----------|--------|
| New project | Full bootstrap — scope, literature, hypotheses |
| Continuing existing project | Skip bootstrap, go directly to inner/outer loops |
| Pivot to new research question | Return to bootstrap |

For this project, bootstrap is complete. The question is scoped, baseline is established, and initial hypotheses exist. Proceed to loops.

---

## 2. INNER LOOP — Fast Iteration

The inner loop runs constrained experiments with clear measurable outcomes. Two flavors:

- **Optimization:** make a metric go up/down (val_loss, F1, IoU-F1)
- **Discovery:** test mechanistic hypotheses about why something works

### The Cycle

```
1.  Pick the highest-priority untested hypothesis from research-state.yaml
2.  Write protocol.md — what change, what prediction, why
    COMMIT TO GIT BEFORE RUNNING (research(protocol): {hypothesis})
    This creates temporal proof your plan existed before results
3.  Run the experiment
4.  Sanity check before trusting results:
    - Did training converge? No NaN/Inf?
    - Does baseline reproduce expected performance?
    - Data loading correct? (spot-check a few samples)
5.  Measure the proxy metric (F1, IoU-F1, etc.)
6.  Record in experiments/{hypothesis-slug}/
    Label: CONFIRMATORY (matched protocol) vs EXPLORATORY (discovered during run)
7.  If positive: keep, note WHY it worked
    If negative: this is progress — log what it rules out and what it suggests
8.  Update research-state.yaml with experiment results
9.  If stuck: search literature or brainstorm new ideas — don't random-walk
10. Repeat
```

### Protocol.md Structure

Every experiment must have a protocol.md written **before** running. This is the temporal proof your hypothesis existed before you saw results.

```markdown
# Protocol: {hypothesis-slug}

## Hypothesis
{e.g., "H6.1: F0 DROP at punchlines — mean F0 drops >20Hz at laughter words"}

## Change
{What exactly you are changing in the pipeline}

## Prediction
{What metric change you expect, and why}
{e.g., "F1 will improve from 0.819 to 0.835 because pause is the single
 strongest acoustic feature per Purandare (2006)"}

## Why This Is Worth Testing
{Mechanistic reasoning — why does this hypothesis make sense?}

## Evaluation Criteria
{How you will measure success — specific metric and threshold}

## Literature Reference
{Purandare 2006, Pickering 2009, etc. — relevant prior work}

## Code Location
{experiments/{slug}/code/{script}.py}
```

### Example: Our H6.1 Protocol

```markdown
# Protocol: H6.1-f0-drop

## Hypothesis
H6.1: F0 DROP at punchlines — mean F0 is lower at laughter words vs non-laugh.

## Change
Extracted F0 (fundamental frequency) per word using librosa.pyin.
Trained LogisticRegression on [F0_mean, F0_range, F0_slope, F0_voiced_ratio].
Prediction: F1 > 0.27 (above our prior audio baseline).

## Prediction
F0 DROP of ~20Hz at laughter words, consistent with Pickering (2009).
Cohen's d > 0.20 (medium effect). If effect is real, audio F1 should
improve from 0.27 to ~0.40-0.50.

## Why This Is Worth Testing
Pickering (2009) reported F0 DROP at punchlines (Cohen's d=0.24 in lab).
Purandare (2006) found pause duration >0.8s is the single strongest
acoustic feature. Both suggest prosody carries genuine signal.

## Evaluation Criteria
- Cohen's d for F0_mean: >0.20 (medium effect)
- If d > 0.20: F1 > 0.35 with LogisticRegression on F0 features
- If F1 < 0.35: effect too small for word-level detection

## Literature Reference
- Pickering et al. (2009), "Prosodic continuity...," Psych Science
- Purandare (2006), "Laughter... acoustic cues," ICSA
- Bachorowski et al. (2001), "Acoustic properties of laughter," J Acoust Soc Am

## Code Location
training/extract_prosody_v1.py
experiments/H6.1-f0-drop/code/train_f0_lr.py
```

### Our Inner Loop Results So Far

| Hypothesis | Metric | Result | Verdict |
|-----------|--------|--------|---------|
| H6.1 (F0 DROP) | Cohen's d = 0.063 | F1 = 0.27 | ❌ Negligible effect |
| H4.4 (biosemotic leakage) | F1 = 0.829 from features alone | LEAKAGE | ❌ Invalid |
| H2.5 (span reformulation) | IoU-F1 = 0.880 vs word = 0.819 | +6.1% | ✅ Strong |
| H12.2 (pause trajectory) | F1 = 0.20 | Audio signal diffuse | ❌ Fails alone |
| H5 (temporal position) | p = 4e-143 | Valid at show-level | ⚠️ Wrong granularity |
| H1.1 (pause >1s) | 2× laughter rate | 23.8% vs 12.4% | ✅ Valid signal |
| Teacher refinement | F1 = 0.078 | Parsing bug | ❌ Catastrophic |

**What we learned:** Audio prosody at word-level is too granular. Laughter is supra-segmental — it spans multiple words. Text-only is the ceiling at word-level (F1=0.819).

### Inner Loop Execution

From the project root:

```bash
# Activate the loop (Claude Code)
# NOTE: Run this once per session to enable continuous research
/loop 20m Continue autoresearch. Read research-state.yaml and findings.md. Run the next pending hypothesis from the inner loop. Write protocol.md, commit it, run the experiment, record results, update research-state.yaml and findings.md. If 5+ experiments since last outer loop, trigger an outer loop synthesis. Keep research moving.

# From project root, run next experiment manually
cd ~/autonomous_laughter_prediction
python3 training/run_xlmr_standup_pipeline.py \
  --experiment-name H8-text-prosody-combination \
  --positive-class-weight 6.0 \
  --epochs 3
```

---

## 3. OUTER LOOP — Periodic Synthesis

The outer loop steps back from individual experiments to ask: what do these results *mean*? What patterns emerge? What's the story?

### When to Run

- Every **5-10 inner loop experiments**
- When inner loop is **stalling** (no metric improvement after 3+ attempts)
- When results **contradict** a core assumption
- When a significant **pattern** emerges across experiments

### The Cycle

```
1. Review all results since last outer loop
2. Cluster by type: what changes worked? Which didn't?
3. Ask WHY — identify the mechanism behind successes and failures
4. Update findings.md with current understanding
5. Search literature if results were surprising or assumptions need revisiting
6. Generate new hypotheses if warranted
7. Decide direction (DEEPEN / BROADEN / PIVOT / CONCLUDE)
8. Update research-state.yaml with new direction
9. Log the reflection in research-log.md
10. If meaningful, generate a progress presentation in to_human/
```

### Decision Criteria

| Decision | When | Action |
|----------|------|--------|
| **DEEPEN** | Supported result raises follow-up questions | Sub-hypotheses (H2.5.1, H2.5.2) → inner loop |
| **BROADEN** | Results solid, adjacent questions untested | New root hypotheses → inner loop |
| **PIVOT** | Core assumption invalidated or better idea found | Return to literature → re-bootstrap |
| **CONCLUDE** | Sufficient evidence for a contribution | Invoke ml-paper-writing → write paper |

### Our Outer Loop Decisions So Far

| Session | Decision | Reason |
|--------|----------|--------|
| Session 1 | DEEPEN text-only | F1=0.819 strong, audio F1=0.27 weak |
| Session 2 | PIVOT to leakage detection | F1=0.829 from features alone → critical finding |
| Session 3 | PIVOT to span reformulation | IoU-F1 gap is real, audio fails at word-level |
| Session 4 | DEEPEN text-only | Refined labels failed, text-only confirmed as ceiling |

**Current verdict (2026-05-24):** Path B — audio fails at word-level, text-only is the ceiling. Span reformulation is the primary architectural contribution.

---

## 4. Workspace Structure

```
autonomous_laughter_prediction/
├── research-state.yaml       # Central state: hypotheses, results, direction
├── research-log.md          # Decision timeline (human-readable)
├── findings.md               # Evolving narrative synthesis (READ THIS FIRST)
├── literature/               # Papers, survey notes
│   ├── survey.md            # Running summary of all papers
│   └── *.pdf                # Actual papers
├── src/                      # Reusable code across experiments
│   ├── evaluate.py          # F1/IoU-F1 evaluation
│   ├── plot_results.py       # Trajectory plots
│   └── data_utils.py        # Shared data loading
├── data/                     # Raw result data
│   └── trajectory.csv       # Experiment trajectory (metric per run)
├── experiments/              # Per-hypothesis work
│   └── {hypothesis-slug}/
│       ├── protocol.md      # What, why, prediction (WRITTEN BEFORE RUN)
│       ├── code/            # Experiment-specific code
│       ├── results/         # Raw outputs, metrics, logs
│       │   └── metrics.json # {metric_name: value, baseline: value, delta: value}
│       └── analysis.md       # What we learned
├── to_human/                 # Progress reports for human review
│   └── {date}-report.html   # HTML progress presentation
└── paper/                    # Final paper (via ml-paper-writing)
```

### research-state.yaml Fields

```yaml
project: autonomous_laughter_prediction
last_updated: 2026-05-24
inner_loop_count: 12
outer_loop_count: 4

current_direction: Path B (text-only ceiling, span reformulation)

next_hypothesis: H8.1  # next pending from backlog
hypothesis_backlog:
  - H8.1 (text+prosody combination)
  - H11.1 (utterance-level audio)
  - H13.1 (MultiLinguahah cross-lingual)

results_trajectory:
  - experiment_id: run_001
    hypothesis: H6.1
    metric: F1
    metric_value: 0.27
    baseline: 0.27
    delta: "+0.00"
    wall_time_min: 45
    change_summary: "F0 DROP test — Cohen's d=0.063, negligible"
  - experiment_id: run_002
    hypothesis: H2.5
    metric: IoU-F1
    metric_value: 0.880
    baseline: 0.819
    delta: "+0.061"
    wall_time_min: 120
    change_summary: "Span reformulation — multi-word labels"
```

---

## 5. How to Run the Autonomous Research Loop

### Step 1: Set Up Agent Continuity (MANDATORY)

**Claude Code:**
```
/loop 20m Continue autoresearch. Read research-state.yaml and findings.md. Run the next pending hypothesis from the inner loop. Write protocol.md, commit it, run the experiment, record results, update research-state.yaml and findings.md. If 5+ experiments since last outer loop, trigger an outer loop synthesis. Keep research moving.
```

**OpenClaw (cron):**
```json
{
  "name": "autoresearch-loop",
  "schedule": { "kind": "every", "everyMs": 1200000 },
  "sessionTarget": "current",
  "payload": {
    "kind": "agentTurn",
    "message": "Continue autoresearch. Read research-state.yaml and findings.md..."
  }
}
```

### Step 2: Start First Session

```bash
cd ~/autonomous_laughter_prediction

# Read current state
cat research-state.yaml
cat findings.md

# Pick next hypothesis from backlog
# Write protocol.md for it
cat > experiments/H8.1-text-prosody-combination/protocol.md << 'EOF'
# Protocol: H8.1-text-prosody-combination

## Hypothesis
H8.1: Text + prosody combination outperforms text-only at span-level.

## Change
Combine XLM-R text features with F0/pause/prosody features at utterance-level.
Use late fusion (concatenate [text_embedding, prosody_embedding]).

## Prediction
Span-level F1 improves from 0.880 to 0.895+ because prosody adds
supra-segmental signal that text alone misses.

## Evaluation Criteria
IoU-F1 > 0.895 (+1.5% over text-only baseline)

## Literature Reference
- Purandare (2006) — pause at 0.8s threshold
- MultiLinguahah (2026) — BYOL-A cross-lingual audio

## Code Location
training/train_fusion_v3.py --phase 3
EOF

git add experiments/H8.1-text-prosody-combination/protocol.md
git commit -m "research(protocol): H8.1 — text+prosody combination"
```

### Step 3: Run Experiment

```bash
cd ~/autonomous_laughter_prediction

# Run H8.1 experiment
python3 training/train_fusion_v3.py \
  --phase 3 \
  --experiment-name H8.1-text-prosody-combination \
  --fusion-type late \
  --prosody-features F0,pause,energy \
  --epochs 3 \
  --batch-size 8

# Record results
cat > experiments/H8.1-text-prosody-combination/results/metrics.json << 'EOF'
{
  "metric": "IoU-F1",
  "metric_value": 0.891,
  "baseline": 0.880,
  "delta": "+0.011",
  "wall_time_min": 180,
  "change_summary": "Late fusion text+prosody — +1.1% IoU-F1, within noise",
  "status": "CONFIRMATORY"
}
EOF
```

### Step 4: Update Research State

```bash
# Append to results_trajectory in research-state.yaml
# Update findings.md with new understanding
```

---

## 6. Current State of Our Loops

### Inner Loop Status

| Metric | Value | Baseline | Delta | Status |
|--------|-------|----------|-------|--------|
| Word-level F1 (text-only) | 0.819 | 0.73 (TF-IDF) | +0.089 | ✅ Strong |
| IoU-F1 (span reformulation) | 0.880 | 0.819 | +0.061 | ✅ Strongest |
| Audio F1 (prosody alone) | 0.27 | 0.20 | +0.07 | ❌ Weak |
| Biosemotic F1 (from features) | 0.829 | N/A | LEAKAGE | ❌ Invalid |
| F0 Cohen's d | 0.063 | N/A | negligible | ❌ Negligible |
| Teacher refinement F1 | 0.078 | 0.819 | -0.741 | ❌ Broken |

**Total experiments run:** 40+
**Inner loop experiments since last outer loop:** 3
**Stalled approaches:** audio prosody, biosemotic features, WavLM fusion, teacher refinement

### Outer Loop Status

**Last outer loop:** 2026-05-24 (Session 4)
**Decision:** DEEPEN text-only, pursue span reformulation
**Current direction:** Path B — text-only XLM-R with span reformulation as architectural contribution

### What We Know Is True

1. **Text-only XLM-R is the ceiling at word-level** (F1=0.819)
2. **Span reformulation adds +6.1%** (IoU-F1=0.880) — real, not artifact
3. **LLM-generated features contain label leakage** (F1=0.829 from features alone)
4. **F0 DROP is real but negligible** (Cohen's d=0.063)
5. **Pause >1s doubles laughter rate** (23.8% vs 12.4%) — but at show-level, not word-level
6. **Cross-lingual degradation is the real unsolved challenge** (EN→ZH: -7%, EN→HI: -14%)

### Open Questions (Outer Loop Backlog)

| Question | Priority | Next Action |
|----------|----------|------------|
| Does utterance-level audio work? (H11.1) | High | Extract utterance embeddings, train fusion |
| Can span-level detection reach F1>0.90? | High | Try CRF/seq2seq on span boundaries |
| Can MultiLinguahah recover cross-lingual? | Medium | Test BYOL-A on ZH/HI subsets |
| Is our weak label noise actually hurting? | Medium | Measure inter-annotator agreement |
| What is the theoretical ceiling? | Low | Theoretical analysis, not experiment |

### What to Try Next

**H8.1 (text+prosody late fusion at span-level):** Combine XLM-R text with F0/pause features using late fusion at utterance/span level. Prediction: F1 improves to 0.895+ because prosody adds supra-segmental signal.

**H11.1 (utterance-level audio):** Not word-level — aggregate prosody over full utterance (not per-word). MultiLinguahah showed audio works at utterance-level. This is the right granularity.

---

## Quick Reference

| Task | Command |
|------|---------|
| Start inner loop | `/loop 20m Continue autoresearch...` |
| Run next experiment | `python3 training/run_xlmr_standup_pipeline.py --experiment-name {slug}` |
| Trigger outer loop | Check after every 5-10 experiments or when stalled |
| Update findings | Edit findings.md after every outer loop |
| Update state | Edit research-state.yaml after every experiment |
| Commit protocol | `git add experiments/{slug}/protocol.md && git commit -m "research(protocol): {slug}"` |
| Check trajectory | `cat data/trajectory.csv` |
| Generate report | Create HTML in to_human/ and open it |

---

*Document structure based on Orchestra Research AI-research-SKILLs (v1.0.0)*
*Last updated: 2026-05-24*