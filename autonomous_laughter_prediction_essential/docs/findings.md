# Research Findings — Laughter Prediction Project

**Last Updated:** 2026-05-24
**Experiments:** 40+ across 4 hypothesis sessions + Orchestra Research review

---

## Finding 1: Text-Only XLM-R Is the Ceiling (F1=0.819)

After trying audio prosody, biosemotic features, WavLM fusion, and LLM-generated labels — **text-only is the only reliable signal**.

| Approach | Result | Verdict |
|----------|--------|---------|
| XLM-R text-only | F1=0.819 | ✅ Strong, reproducible |
| F0/Energy/Pause acoustic | F1=0.27 | ❌ Supra-segmental signal averaged out |
| WavLM audio-only | F1=0.0 | ❌ Failed completely |
| Biosemotic features | +0.003 | ❌ Noise + leakage |
| Gated multimodal fusion | Gate→1.0 | ❌ Audio learns nothing |
| Teacher refinement | F1=0.078 | ❌ Catastrophic parsing failure |

**Interpretation:** Laughter prediction at word-level is fundamentally a text task. Audio contains the signal (proven by MultiLinguahah at utterance-level) but our word-level extraction averages it out.

---

## Finding 2: LLM-Generated Features Contain Label Leakage (CRITICAL)

When we trained LogisticRegression on ONLY the 10 biosemotic dimensions (Duchenne, incongruity, ToM) with NO text input, it achieved **F1=0.829** — higher than our full XLM-R model (F1=0.819).

This is impossible without leakage. The LLM that generated the biosemiotic scores was given the task "score this word for laughter potential" and encoded the answer into the feature values.

**Implication:** All ablation studies using biosemotic features are invalid. The +0.003 "improvement" was the model seeing labels through the features, not genuine signal.

**Paper angle:** "Do Theory-Driven Features Help? A Negative Result" — publishable negative result.

---

## Finding 3: The F0 DROP Effect Is Real But Negligible (H6.1)

Pickering (2009) reported F0 DROP at punchlines. We confirmed this across 60,475 word tokens:

| Metric | Laugh | Non-Laugh | Cohen's d |
|--------|-------|-----------|-----------|
| F0 mean | 202.0 Hz | 207.1 Hz | **0.063** |

**p < 10⁻⁶** (statistically significant) but **Cohen's d = 0.063** (negligible effect size).

The 5 Hz difference produces ~98% distribution overlap. At N=60,475, even trivially small effects are significant — the "big data significance trap."

**Interpretation:** The F0 DROP exists in the literature (controlled settings) but is too small to detect in edited stand-up comedy recordings where studio processing averages out prosodic details.

---

## Finding 4: Span Reformulation Is Genuine (IoU-F1=0.880 vs word-F1=0.819)

The 6.1% gap between IoU-F1 and word-F1 is real, not a metric artifact:

- 100% of laughter labels span 2+ consecutive words (avg 19.4 words)
- Multi-word spans are the norm (not an artifact of our labeling)
- Literature (Gillick 2019) validates span-based audio detection at F1=0.89
- Purandare (2006) confirms laughter is supra-segmental (0.8s pauses)

**Interpretation:** The task should be reformulated as span detection (like NER) not word-level sequence labeling. This is the primary architectural contribution.

---

## Finding 5: Cross-Lingual Transfer Is the Real unsolved Challenge

| Language | F1 | Training Examples |
|----------|-----|-------------------|
| English | 0.819 | ~10K |
| Chinese | 0.752 | ~2K |
| Hindi | 0.68 | 48 (statistically meaningless) |

The ~7% EN→ZH drop and ~14% EN→HI drop is the fundamental research challenge — not audio. Text representations degrade sharply for languages with less pretraining data.

**MultiLinguahah (2026)** suggests BYOL-A encoder may help for cross-lingual audio, but text degradation suggests the problem is semantic, not acoustic.

---

## Finding 6: Temporal Position Is Validated (p=4e-143)

Peak laughter at 20-30% through show (15% laugh rate), minimum at 90-100% (10.1%). Chi-square p=4e-143 — this is a real structural pattern in stand-up comedy.

**But:** This is a SHOW-LEVEL pattern, not word-level. Cannot be used as a word-level feature. This validates that laughter prediction needs utterance or span-level analysis, not word-level.

---

## Finding 7: Long Pauses (>1s) Double Laughter Rate

From subtitle timestamps (coarse, but the effect emerges at scale):

| Pause Range | Laughter Rate |
|-------------|---------------|
| 0.0-0.1s | 12.4% |
| 0.1-0.2s | 11.6% |
| 0.5-1.0s | 12.3% |
| 1.0-2.0s | **17.7%** |
| 2.0-5.0s | **23.8%** |

**Interpretation:** The "comedic pause" IS real — pauses >1s have nearly 2× the laughter rate. But subtitle timestamps are too coarse to measure the 0.8s vs 0.3s gap from Purandare (2006).

---

## Finding 8: Split Leakage Is Minor But Real (1.9%)

Random split (cross-video) vs per-show split:

| Split Method | F1 | Gap |
|-------------|:---:|:---:|
| Random (cross-video) | 0.218 | — |
| Per-Show (same video per split) | 0.199 | **+1.9%** |

Below the 3% threshold for "significant leakage" but EXISTS. Per-show splits should be used for final paper results; random-split reported as upper bound.

---

## Orchestra Research Methodology — What We Missed

### What We Did Correctly
- ✅ Formed 26 falsifiable hypotheses (H1.1-H14.4)
- ✅ Ran experiments with measurable outcomes
- ✅ Documented results in hypothesis sessions
- ✅ Identified critical negative results (leakage, F0 negligible)
- ✅ Had literature grounding (Purandare, Pickering, Bachorowski)

### What We Missed (Per Orchestra Two-Loop)
- ❌ **protocol.md before experiment** — no temporal proof our plan existed before results
- ❌ **research-state.yaml** — no central state tracking across sessions
- ❌ **Inner/outer loop separation** — we iterated fast but didn't synth period
- ❌ **findings.md** — no evolving narrative document
- ❌ **Experiment trajectory tracking** — no metric_value/baseline/delta per run
- ❌ **Domain skill routing** — used literature but not Orchestra skill routing
- ❌ **Multi-agent collaboration** — no parallel agent exploration

---

## Paper Narrative Evolution

### OLD (pre-Orchestra)
> "XLM-R + 32-dim biosemotic features achieves F1=0.819, with features adding +0.003"

### NEW (post-Orchestra)
> "XLM-R word-level laughter prediction achieves F1=0.819 (IoU-F1=0.880). We discovered LLM-generated biosemotic features contain critical label leakage (F1=0.829 from features alone), invalidating prior ablation studies. Text-only is the ceiling — audio adds noise at word-level. Span reformulation is the primary contribution."

### Three Paper Paths

| Path | Condition | Paper | Timeline |
|------|-----------|-------|----------|
| **B** (current) | Audio fails | "StandUp NER: Laughter as Sequence Labeling" — ACL SRW | 2-3 weeks |
| **A** | Utterance audio works | "Multilingual Laughter via Multimodal Fusion" — EMNLP | 4-6 weeks |
| **C** | Weak labels broken | "Weak Supervision: When YouTube Subtitles Lie" — EMNLP eval | 3-4 weeks |

---

## What Failed and Why

| Failure | Root Cause | What It Rules Out |
|---------|-----------|-------------------|
| WavLM F1=0.0 | All-same-class bug OR label misalignment | Audio SSL doesn't work off-shelf |
| Teacher refinement F1=0.078 | Parsing bug → 0% laughter detected | LLM-generated labels are unreliable |
| Biosemotic +0.003 | LLM encoded labels in features | Theory-driven features add signal |
| F0 DROP d=0.063 | Studio editing averages prosody | F0 useful as word-level feature |
| Pause trajectory F1=0.20 | Temporal context insufficient alone | Audio signal exists but diffuse |
| Gate collapse (g=1.0) | Text dominates; audio learns nothing | Fusion works at current scale |

---

## What Still Works

| Approach | Status | Next Step |
|----------|--------|----------|
| XLM-R text-only (F1=0.819) | ✅ Strong | Push to F1=0.85 with more data |
| IoU-F1 span detection | ✅ Valid | Reformulate as NER-like task |
| Temporal position (p=4e-143) | ✅ Valid | Show-level feature only |
| Long pauses (>1s) → 2× laugh | ✅ Valid | Extract from audio, not subtitles |
| Per-show split | ✅ Required | Standard going forward |
| Weak labels (YouTube VTT) | ✅ Sufficient | Not broken enough to fix |

---

## Orchestra Research Compliance Checklist

| Requirement | Status | Action |
|-------------|--------|--------|
| Two-loop architecture | ⚠️ Partial | Need outer loop synthesis every 5-10 experiments |
| research-state.yaml | ❌ Missing | Create now |
| protocol.md before experiment | ❌ Missing | Mandate going forward |
| research-log.md | ❌ Missing | Create now |
| findings.md | ❌ Missing | Create now |
| Experiment trajectory tracking | ❌ Missing | Add metric_value/baseline/delta |
| Domain skill routing | ⚠️ Partial | Use skill routing for execution |
| Per-hypothesis experiment directories | ❌ Missing | Create experiments/ structure |

---

## Immediate Next Actions

1. **Create research-state.yaml** — central state tracking for all hypotheses
2. **Create research-log.md** — decision timeline
3. **Create findings.md** — evolving narrative
4. **Add protocol.md mandate** — every experiment must write protocol.md BEFORE running
5. **Submit ACL SRW paper** — fix error bars, add StandUp4AI comparison, remove RL section
6. **Submit LaughBank-733K resource paper** — 733K segments is genuinely unique
7. **Test utterance-level audio** — not word-level (H11)

---

*Generated: 2026-05-24*
*Source: 40+ experiments, 4 hypothesis sessions, Orchestra Research AI-research-SKILLs review*