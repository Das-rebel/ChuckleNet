# Architecture Decision Records

---

## ADR-001: XLM-R Text-Only as Anchor (F1=0.819)

### Status: ACCEPTED

### Context
After 40+ experiments across audio prosody, biosemiotic features, WavLM fusion, and multimodal approaches, the ONLY consistently strong signal is text-only XLM-R.

### Decision
**Text-only XLM-R baseline (F1=0.819 word-level, IoU-F1=0.880) is the anchor for all composition decisions.**

### Evidence
| Experiment | Result | Verdict |
|-----------|--------|---------|
| Biosemiotic features (32-dim) | +0.003 F1 | **Noise** — leakage confirmed |
| F0/Energy/Pause acoustic | F1=0.20-0.27 | **Weak** |
| WavLM audio-only | F1=0.0 | **Failed** |
| Gated multimodal fusion | Gate→1.0, audio learns nothing | **Broken** |
| Teacher refinement (LLM labels) | F1=0.078 | **Catastrophic** |
| XLM-R text-only | F1=0.819 | **Strong** |

### What This Means
- Text captures ~98% of the laughter signal at word level
- Audio adds noise at word-level (utterance-level TBD)
- Biosemiotic theory is NOT validated by this data
- Weak labels (YouTube [laughter] markers) are sufficient for text-only

---

## ADR-002: Span Reformulation as Primary Contribution

### Status: ACCEPTED

### Context
IoU-F1=0.880 vs word-F1=0.819 — a 6.1% gap that suggests span-level prediction is genuinely different from word-level classification.

### Decision
**The primary contribution is reformulating laughter prediction as a span detection task (like NER) rather than word-level sequence labeling.**

### Evidence
- Span-F1=0.880 >> word-F1=0.819 across all test sets
- Multi-word spans are the norm (100% of laughter labels span 2+ words)
- Literature (Gillick 2019) validates span-based audio detection (F1=0.89)
- Purandare 2006 confirms laughter is supra-segmental (0.8s pauses)

### Consequences
- Paper leads with metric reformulation + span detection
- Results reported in BOTH word-F1 and IoU-F1
- Error analysis distinguishes word-level vs span-level failures

---

## ADR-003: Text-Only XLM-R as Baseline Before Multimodal Fusion

### Status: ACCEPTED

### Context
Audio prosody features (F0, MFCC, pause, RMS) consistently hit F1≈0.29 ceiling. WavLM phase A returned F1=0.0. Gate in fusion collapses to text-only (g=1.0).

### Decision
**Build text-only XLM-R baseline to F1≥0.80 FIRST, then add audio.**
- Text is the strong signal (F1=0.82 word-level)
- Audio adds noise until utterance-level embeddings are fixed
- Phase 1 should be text-only, NOT multimodal

### Rationale
- Audio branch is not ready (WavLM extraction needs Colab GPU)
- Fusion training cannot learn when text is dominant
- Text baseline validates data pipeline before audio complexity

### Consequences
- Phase 1: XLM-R text-only, no audio branch
- Phase 2: Add frozen audio branch, train gate
- Phase 3: Unfreeze and joint fine-tune

---

## ADR-004: Utterance-Level, Not Word-Level, for Fusion

### Status: ACCEPTED

### Context
Word-level analysis gave F1=0.82 but is inflated by multi-word span labeling artifacts. Per-word acoustic features hit F1=0.29 ceiling because laughter is supra-segmental.

### Decision
**Fusion operates at utterance level (3-15s clips), NOT word level.**
- Each utterance = one audio clip + full text
- WavLM mean-pools entire clip to single 768-dim vector
- Binary label per utterance

### Rationale
- Laughter is a speaker behavior spanning 1-10+ seconds
- Word-level audio analysis (0.3s windows) averages out signal
- Literature confirms: audio humor detection F1=62-63% at utterance level

### Consequences
- `dataset_utterance_multimodal.py` is the correct dataset class
- Word-level training (`train_xlmr_combined.py`) is for baseline only
- Audio extraction must preserve full utterance context

---

## ADR-005: Gated Fusion Over Cross-Attention

### Status: ACCEPTED

### Context
Only 15K utterances available. Cross-attention has 768*768 parameters — overfitting risk.

### Decision
**Gated fusion: `fused = g*t + (1-g)*a`**
- Gate learns to trust text vs audio per-utterance
- 2*256*256 = 128K params for fusion layer
- Phase 2 freezes text, trains only audio_proj + gate

### Consequences
- Gate must output non-trivial distribution (not always 0 or 1)
- Monitor gate_stats during training; add auxiliary loss if collapsed
- Cross-attention deferred until 100K+ utterances

---

## ADR-006: Pre-Extract WavLM Embeddings to Disk

### Status: ACCEPTED

### Context
WavLM inference is expensive (forward pass per 10ms window). Running on-the-fly during training wastes GPU cycles.

### Decision
**Pre-extract all WavLM embeddings once, save to .pt file.**
- ~4.6GB for 15K utterances
- One-time Colab compute (~2 hours)
- Training loads pre-computed embeddings from disk

### Consequences
- `extract_wavlm_embeddings.py` must run successfully first
- Gist provided for Colab: https://gist.github.com/Das-rebel/10b79eddcf2dce5ec4ff298ec3a46b0d
- Missing embeddings = fusion training cannot proceed

---

## ADR-007: Fix Gate Collapse Before Phase 2

### Status: ACCEPTED

### Context
Phase 1 fusion gate collapsed to mean=1.0 (always trusts text). Audio branch never learned.

### Decision
**If gate_mean > 0.95 or gate_std < 0.01 after Phase 1, abort and fix.**
- Add audio auxiliary loss: L = 0.7*text_loss + 0.3*audio_loss
- Initialize gate with bias toward audio (contrary to current)
- Use smaller learning rate for gate (1e-4 vs 1e-3)

### Consequences
- Phase 1 must show gate_std > 0.05 to proceed to Phase 2
- Audio branch should achieve F1 > 0.50 standalone

---

## ADR-008: Resume Capability for All Training Scripts

### Status: ACCEPTED

### Context
Training runs take 4+ hours. Interruptions lose all progress.

### Decision
**All training scripts must support `--resume <checkpoint.pt>` flag.**
- Saves: model weights, optimizer state, scheduler state, epoch number
- Loads: best val F1 so far, history
- Incrementally appends to results.json

### Consequences
- Checkpoint every epoch minimum
- results.json must be appendable (not overwrite)

---

## ADR-009: Orchestra Research Two-Loop Methodology

### Status: ACCEPTED

### Context
Orchestra Research's AI-research-SKILLs (98 skills) provides a two-loop architecture (inner optimization + outer synthesis) that we did NOT follow in our early experiments.

### Decision
**Adopt the Orchestra Research methodology for all future experiments.**

### Key Components
1. **research-state.yaml** — Central state tracking
2. **research-log.md** — Decision timeline
3. **findings.md** — Evolving narrative synthesis
4. **experiments/{hypothesis-slug}/** — Per-hypothesis work with protocol.md

### What We Missed (Per Orchestra Framework)
- ❌ No protocol.md written BEFORE experiments (temporal proof)
- ❌ No research-state.yaml tracking across sessions
- ❌ No inner/outer loop separation
- ❌ No systematic literature routing to domain skills
- ❌ No experiment trajectory tracking (metric_value, baseline, delta per run)
- ✅ We DID have hypotheses (H1.1-H14.4), but not structured experiment directories
- ✅ We DID run experiments, but not with protocol-first discipline

### Consequences
- All future experiments follow the two-loop structure
- Each hypothesis gets its own experiments/{slug}/ directory
- Write protocol.md BEFORE running any experiment
- Log every run to research-log.md

---

## ADR-010: Paper Strategy — ACL SRW First, Then Resource Paper

### Status: ACCEPTED

### Context
Orchestra review gave our current paper 2.75/6 (borderline reject). StandUp4AI is the critical missing comparison. Biosemiotic features add only +0.003 (noise).

### Decision
**Submit sequence:**
1. **ACL SRW** (2-3 weeks): StandUp NER — fix error bars, add StandUp4AI comparison, remove speculative RL section
2. **LREC-COLING** (2-3 weeks): LaughBank-733K resource paper — 733K segments is genuinely unique, resource papers have lower bar
3. **EMNLP** (3-4 weeks): Weak supervision quality study — 15% label offset analysis

### Paper Narrative Updates

**OLD (pre-Orchestra):** "XLM-R + biosemiotic features achieves F1=0.819"

**NEW (post-Orchestra):** "XLM-R word-level laughter prediction achieves F1=0.819 (IoU-F1=0.880). We discovered LLM-generated biosemiotc features contain critical label leakage (F1=0.829 from features alone), invalidating ablation studies. Text-only is the ceiling — audio adds noise at word-level. Span reformulation is the primary contribution."

### What StandUp4AI Comparison Must Show
- Our model vs Barrière et al. 2025 on identical test set
- Both word-F1 and IoU-F1 reported
- Error analysis comparing where each model fails

---

## ADR-011: Audio Only Worthwhile at Utterance Level

### Status: ACCEPTED

### Context
Word-level audio features (F0, pause, RMS) achieved F1=0.20-0.27. But utterance-level acoustic features haven't been tested. MultiLinguahah (2026) achieved F1=0.68 on utterance-level audio-only.

### Decision
**Next audio experiment: utterance-level prosody extraction, NOT word-level.**

### Rationale
- Laughter is supra-segmental (1-10+ seconds)
- Word-level analysis (0.3s windows) averages out the signal
- MultiLinguahah proves audio-only F1=0.68 is achievable at utterance level
- Our H6.1 F0 DROP test was at word-level (explains negligible Cohen's d=0.063)

### Consequences
- Extract F0/energy/pause features at utterance level (mean over entire clip)
- Compare: word-level F1=0.27 vs utterance-level F1=TBD
- If utterance-level audio achieves F1 > 0.50, fusion becomes meaningful

---

## ADR-012: Do NOT Trust LLM-Generated Labels for Supervision

### Status: ACCEPTED

### Context
Teacher refinement (Qwen2.5-coder:1.5b) on 520 refined labels → F1=0.078 (catastrophic). Biosemiotic features achieved F1=0.829 from features alone (label leakage).

### Decision
**LLM-generated labels for supervision are untrustworthy without human verification.**
- LLMs hallucinate labels when given task framing
- Always compare LLM labels against human annotation on a sample
- Biosemiotic-style features generated by LLMs WILL encode the labels

### Consequences
- Never use LLM output as direct supervision without validation
- If refining labels via LLM, always spot-check against human judgment
- Teacher refinement approach abandoned — weak labels from VTT are more reliable

---

## ADR-013: Per-Video Split for Evaluation (Not Random)

### Status: ACCEPTED

### Context
Random split inflates F1 by ~1.9% vs per-show split due to comedian-style leakage.

### Decision
**All final evaluations use per-video splits. Random split reported as upper bound.**

### Consequences
- Per-video: model trained on 60 videos, tested on 11
- Random split: same video appears in both train and test
- Report both; explain the gap in paper

---

## ADR-014: Cross-Lingual Transfer Degradation Is the Real Challenge

### Status: ACCEPTED

### Context
English F1=0.819, Chinese F1=0.752, Hindi F1=0.68 (48 examples). The ~7% drop EN→ZH and ~14% EN→HI is the fundamental challenge, not audio.

### Decision
**Prioritize cross-lingual transfer research over audio for the next phase.**

### Rationale
- Audio (F1=0.20) is far below text (F1=0.82) even for English
- Cross-lingual degradation is a genuine unsolved problem
- MultiLinguahah (2026) suggests BYOL-A encoder may help for ZH/HI audio
- But text degradation suggests the problem is semantic, not acoustic

### Consequences
- H13.4 (multilingual transfer en→zh→hi) becomes priority
- H1.4 (audio helps ZH more than EN) may be testable once audio works
- Paper should include cross-lingual analysis as a major finding

---

## ADR-015: Negative Results Are Publishable

### Status: ACCEPTED

### Context
We have three genuine negative results:
1. Teacher refinement fails (F1=0.078)
2. Biosemiotc features add +0.003 (noise, with leakage)
3. Audio prosody adds +0.05 at word-level (negligible)

### Decision
**Compile negative results into a publishable ArXiv preprint + EMNLP workshop paper.**

### Rationale
- Negative results are citeable and establish scientific honesty
- "Audio fails at word-level" is a useful result for the community
- "LLM-generated features cheat" is a methodological warning
- Orchestra framework explicitly values failure analysis

### Consequences
- Paper 3: "Weak Signals: What Doesn't Work for Laughter Detection"
- Cite our own H4.4, H6.1, and teacher refinement failures
- Framework: what we tried, why it failed, what it rules out

---

*Generated: 2026-05-24*
*Source: Orchestra Research AI-research-SKILLs review + 4 hypothesis sessions*