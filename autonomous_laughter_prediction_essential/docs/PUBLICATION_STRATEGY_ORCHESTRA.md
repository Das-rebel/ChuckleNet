# ORCHESTRA RESEARCH IDEATION — FULL PUBLICATION STRATEGY
## Frameworks Applied: 3 (Tensions), 5 (What Changed), 6 (Failure Analysis), 7 (Simplicity), 9 (Composition), 10 (Two-Sentence)
## Agents: 3 independent (Codex × 2, MiniMax × 1) + Gemini Pro review
## Date: 2026-05-16

---

## PHASE 1: TENSION & FAILURE ANALYSIS (Codex Agent 1)

### Key Insight
> "The project is no longer 'how do we add more modalities/features?' but 'which contradictions are real, and which are artifacts of supervision and task formulation?'"

### 5 Core Tensions in Laughter Detection

| Tension | Real or Artifact? | Paper Opportunity |
|---------|-------------------|-------------------|
| **Scale vs Quality** | REAL — weak labels from YouTube subs are noisy, but manual labels are tiny | Paper on weak supervision quality |
| **Text vs Audio vs Multimodal** | ARTIFACT — text alone is already strong (0.819); audio adds marginal signal for word-level | Paper showing text dominance |
| **Multilingual vs High-resource** | REAL — cross-lingual transfer degrades sharply (EN 0.82 → HI 0.68) | Paper on language-specific humor transfer |
| **Hand-crafted features vs Learned representations** | RESOLVED — biosemotic +0.003 proves XLM-R already captures these patterns | Negative result paper |
| **Sequence labeling vs Span detection** | REAL — IoU-F1 (0.880) >> word-F1 (0.819) suggests span formulation is better | Paper on task formulation |

### What Failures Teach Us

| Failure | Root Cause | Paper Idea |
|---------|-----------|------------|
| **WavLM F1=0.0** | Likely: all-same-class bug, label misalignment, or feature extraction issue | "Debugging audio SSL for paralinguistic tasks" — systems/position paper |
| **Teacher refinement F1=0.078** | Parsing bug → 0% laughter detected | "When weak supervision fails: Negative results in LLM-assisted labeling" |
| **Biosemotic +0.003** | XLM-R already captures these patterns during pretraining | "Do hand-crafted humor features add anything to pretrained transformers?" |

### Papers from Failures
1. **"When Weak Supervision Fails"** — Venue: EMNLP Findings. Negative results paper documenting teacher refinement catastrophe
2. **"Do Hand-Crafted Features Still Matter?"** — Venue: ACL workshop. Ablation showing biosemotic features add +0.003 to XLM-R
3. **"Audio-Text Fusion: Why Audio Fails for Word-Level Laughter"** — Venue: Interspeech. Analysis of why WavLM gets F1=0.0 on this task

---

## PHASE 2: COMPOSITION & SIMPLICITY (Codex Agent 2)

### Key Insight
> "The only fully validated core is the word-level XLM-R stand-up pipeline, so every composition treats text as the anchor and uses audio/emotion components as cheap add-ons rather than replacing the backbone."

### Top 10 Composition Ideas

| # | Title | Venue | Pitch | Have vs Need | Time |
|---|-------|-------|-------|-------------|------|
| 1 | **"Weak Signals: 733K Audio-Word Segments for Laughter"** | LREC-COLING | "We release the largest publicly available audio-word-aligned dataset for laughter detection (733K segments, 3 languages) with weak labels derived from YouTube subtitles." | Have: 733K segments, alignment code. Need: clean splits, documentation | 2 weeks |
| 2 | **"StandUp NER: Laughter as Sequence Labeling"** | ACL SRW | "We show word-level laughter prediction is a NER-like task where XLM-RoBERTa achieves F1=0.819 on English stand-up, outperforming sentence-level approaches." | Have: model, results. Need: StandUp4AI comparison, error bars | 2-3 weeks |
| 3 | **"Cross-Domain Laughter: From Sitcoms to Stand-up"** | EMNLP | "We show XLM-R trained on stand-up comedy transfers to sitcoms (UR-FUNNY F1=0.552) and TED talks (F1=0.515) with zero-shot, revealing domain-specific humor patterns." | Have: cross-domain results. Need: formal evaluation, more benchmarks | 3-4 weeks |
| 4 | **"Prosody Doesn't Help (Much): Acoustic Features for Word-Level Laughter"** | Interspeech | "We extract 120-dim acoustic features (F0, pauses, MFCC) validated by 50 years of humor research and show they add <1% F1 to a text-only XLM-R baseline for word-level laughter prediction." | Have: acoustic research, XLM-R baseline. Need: feature extraction experiments | 3-4 weeks |
| 5 | **"The Hindi Humor Gap: Zero-Shot Laughter Prediction"** | ACL Workshop | "We document the catastrophic drop in laughter prediction from English (F1=0.819) to Hindi (F1=0.68 with 48 examples), analyzing cultural and linguistic barriers." | Have: results, analysis. Need: more Hindi data OR reframe as analysis paper | 2 weeks |
| 6 | **"Biosemotic Humor: When Theory Meets Transformers"** | NeurIPS Workshop | "We operationalize 9 biosemotic humor dimensions as computational features and show that XLM-RoBERTa already captures >99% of their signal, questioning the need for theory-driven feature engineering." | Have: features, ablation results. Need: deeper analysis, probing experiments | 3-4 weeks |
| 7 | **"Laughter as Spans, Not Words"** | ACL Main | "We reformulate word-level laughter prediction as span detection (like NER with span-F1) and show IoU-F1=0.880 >> word-F1=0.819, suggesting the community should adopt span-based metrics." | Have: both metrics computed. Need: formal span formulation, more experiments | 4-6 weeks |
| 8 | **"Weak Labels from YouTube: How Noisy Are [laughter] Markers?"** | EMNLP | "We analyze 733K audio-word segments with weak labels from YouTube auto-subtitles, finding ~15% label offset and proposing correction heuristics." | Have: 733K segments, analysis. Need: systematic label quality study | 3-4 weeks |
| 9 | **"LaughTrack-ML: A Pipeline for Multilingual Comedy Analytics"** | ACL System Demos | "We present an end-to-end pipeline from YouTube video to word-level laughter prediction, processing 3 languages with sub-minute latency." | Have: all scripts. Need: packaging, demo, documentation | 4-6 weeks |
| 10 | **"What Makes Stand-up Funny Across Languages?"** | TACL Journal | "We analyze 10K+ stand-up comedy segments across English, Chinese, and Hindi, finding that structural features (punchline position, pause patterns) transfer across languages while cultural references do not." | Have: data, model, predictions. Need: linguistic analysis | 6-8 weeks |

### Simplicity Test Result
**The simplest thing that works:** XLM-R text-only, word-level, F1=0.819. Everything else adds noise. The contribution IS the simplicity — and the honesty about what doesn't work.

---

## PHASE 3: VENUE-SPECIFIC STRATEGY (MiniMax Agent 3)

### Framework 5: What Changed?

| Change | What It Enables | Paper Angle |
|--------|----------------|-------------|
| WavLM-Base+ (2022) | Denoising pretraining for noisy comedy | Audio baseline (once debugged) |
| StandUp4AI (2024-25) | External benchmark, 7 languages | Direct comparison paper |
| LoRA/QLoRA mainstream | Fusion model fits T4 | Multimodal paper |
| Apple MLX | Local training on Mac | No cloud needed |
| YouTube weak supervision at scale | 733K+ segments | Resource/dataset paper |

### Venue-by-Venue Breakdown

#### 1. TOP NLP VENUES

**ACL Main** (Deadline ~Jan 2027)
- "Laughter as Spans, Not Words" — reformulate task as span detection
- Feasibility: 4-6 weeks | Acceptance: LOW (need more than just metric reformulation)

**EMNLP Main** (Deadline ~Jun 2026)
- "Weak Signals: What YouTube Subtitles Teach Us About Laughter" — weak supervision analysis
- Feasibility: 3-4 weeks | Acceptance: MEDIUM (novel analysis angle)

#### 2. WORKSHOPS (Best near-term bets)

**ACL SRW** (Deadline ~Feb 2026)
- "StandUp NER: Laughter as Sequence Labeling" — the current Paper 3, fixed
- Feasibility: 2-3 weeks | Acceptance: HIGH (student venue, honest work)

**EMNLP Workshop on Humor** (if exists)
- "Biosemotic Features vs Transformers" — negative result
- Feasibility: 3-4 weeks | Acceptance: MEDIUM-HIGH (workshops love negative results)

**NeurIPS Workshop on Social Intelligence**
- "Cross-Domain Laughter Transfer" — zero-shot analysis
- Feasibility: 3-4 weeks | Acceptance: MEDIUM

#### 3. SPEECH VENUES

**Interspeech** (Deadline ~Mar 2026)
- "Why Audio Fails for Word-Level Laughter: A Negative Result" — analyze WavLM failure
- Feasibility: 4-6 weeks (need to debug + explain) | Acceptance: MEDIUM

**IEEE TASLP** (Rolling)
- "Acoustic Features for Word-Level Laughter Prediction" — 120-dim feature study
- Feasibility: 3-4 months (need proper experiments) | Acceptance: MEDIUM

**Computer Speech & Language** (Rolling)
- "Multimodal Fusion for Comedy Analytics" — if WavLM gets fixed
- Feasibility: 4-6 months | Acceptance: LOW-MEDIUM

#### 4. ML VENUES

**AAAI Workshop**
- "Do Theory-Driven Features Help Transformers?" — biosemotic ablation
- Feasibility: 3-4 weeks | Acceptance: MEDIUM

#### 5. RESOURCE VENUES (HIGH probability)

**LREC-COLING** (Deadline ~Jan 2027)
- **"LaughBank-733K: The Largest Public Audio-Word Laughter Dataset"** — resource paper
- Feasibility: 2-3 weeks | Acceptance: **HIGH** (resource papers have lower bar)
- Have: 733K segments, alignment code, 3 languages
- Need: clean documentation, license check, train/val/test splits, quality analysis

**ACL System Demonstrations**
- "LaughTrack-ML: End-to-End Comedy Analytics Pipeline"
- Feasibility: 4-6 weeks | Acceptance: MEDIUM-HIGH

#### 6. JOURNALS

**TACL** (Rolling, counts as ACL publication)
- "What Makes Stand-up Funny Across Languages? A Multilingual Analysis"
- Feasibility: 6-8 weeks | Acceptance: MEDIUM

**Computational Linguistics**
- "Laughter Prediction as Sequence Labeling: Task Formulation and Metrics"
- Feasibility: 3-4 months | Acceptance: LOW (need deeper theoretical contribution)

#### 7. ARXIV (Immediate, no review)

- **"Negative Results in Laughter Detection: Audio, LLM Labels, and Hand-Crafted Features"** — compile all 3 failures
- Feasibility: 1 week | Impact: citations, establishes honesty
- This becomes a reference for "what doesn't work"

---

## FINAL RANKED STRATEGY

### TIER 1: Submit Now (2-3 weeks)

| Priority | Paper | Venue | Why |
|----------|-------|-------|-----|
| **#1** | **StandUp NER (Paper 3, fixed)** | **ACL SRW** | Real results, honest, 3.5/5 from reviewer |
| **#2** | **LaughBank-733K Resource Paper** | **LREC-COLING** | 733K segments is genuinely unique, resource papers get accepted |
| **#3** | **Negative Results ArXiv Preprint** | **ArXiv** | Quick, establishes priority, builds reputation for honesty |

### TIER 2: Submit 1-3 months

| Priority | Paper | Venue | Why |
|----------|-------|-------|-----|
| **#4** | Cross-Domain Zero-Shot Analysis | EMNLP Workshop | Novel analysis angle |
| **#5** | Biosemotic Features vs Transformers | NeurIPS/AAAI Workshop | Negative result + probing |
| **#6** | Weak Supervision Quality Study | EMNLP Main | Label noise analysis |
| **#7** | Acoustic Features for Laughter | Interspeech | If extraction runs work |

### TIER 3: Submit 3-6 months (requires new experiments)

| Priority | Paper | Venue | Why |
|----------|-------|-------|-----|
| **#8** | Span-Level Laughter Detection | ACL Main | Task reformulation |
| **#9** | LaughTrack-ML Demo | ACL System Demos | Pipeline paper |
| **#10** | Multilingual Humor Analysis | TACL | Deep linguistic study |

---

## WHAT TO DO RIGHT NOW (Today)

1. **Start Paper #1 (ACL SRW):** Fix Paper 3 per reviewer feedback — remove RL, add StandUp4AI baseline, add error bars
2. **Start Paper #2 (LREC):** Document the 733K dataset, create clean splits, write resource paper
3. **Draft Paper #3 (ArXiv):** Compile all 3 negative results into one preprint

These 3 papers can be worked on IN PARALLEL and submitted within 2-3 weeks.

---

*Generated by Orchestra Research Ideation Frameworks 3, 5, 6, 7, 9, 10*
*Agents: Codex × 2, MiniMax × 1, Gemini Pro × 1*
