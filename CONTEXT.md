# Context: Autonomous Laughter Prediction (ChuckleNet)

## Project Overview
**Task:** Predict whether a word in stand-up comedy is followed by audience laughter.
**Method:** Multimodal (text + audio) sequence labeling at word level.
**Goal:** F1 > 0.85 for laughter detection; prove span-level prediction > word-level.

## Research Question
*"What makes people laugh in stand-up comedy, and can we predict it?"*

Sub-questions:
1. Does text content (word choice, semantic incongruity) predict laughter?
2. Does prosody (F0, pause, energy) predict laughter?
3. Does multimodal fusion outperform text-only?
4. Is span-level prediction (IoU-F1) fundamentally different from word-level (F1)?

## Key Terms
| Term | Definition |
|------|------------|
| **XLM-R** | `FacebookAI/xlm-roberta-base` — 270M params, 768-dim hidden state |
| **WavLM** | `microsoft/wavlm-base-plus` — 810M params, audio encoder |
| **Gated fusion** | `fused = g*t + (1-g)*a` where g = sigmoid(W·[t;a]) |
| **label_any** | Binary 0/1 per word (any laughter marker in ±5s window) |
| **label_majority** | Binary 0/1 (majority of words in window are laughter) |
| **utterance** | Aligned segment with timestamps, 3-15s typical |
| **span** | Multi-word region marked as laughter (our labeling artifact) |
| **IoU-F1** | Span-level F1 using intersection-over-union (vs word-level) |

## Dataset
- **Source:** YouTube stand-up comedy videos (71 videos, en/zh/hi)
- **Alignment:** Whisper word timestamps → VTT [laughter] markers
- **Segments:** 549,334 aligned segments, all with timestamps
- **Utterances:** 15,060 utterances (32.6% positive, label_any)
- **Audio:** 388 MP3s locally, 459 on GDrive

## Current Best Metrics
| Model | Metric | Value | Status |
|-------|--------|-------|--------|
| XLM-R word-level (text only) | F1 | **0.819** | ✅ Strong |
| XLM-R word-level (text only) | IoU-F1 | **0.880** | ✅ Stronger |
| Audio prosody (all 49 features) | F1 | **0.29** | ❌ Ceiling |
| WavLM audio-only phase A | F1 | **0.0** | ❌ Broken |
| Gated fusion phase 1 | Gate→1.0 | — | ❌ Collapsed |
| TF-IDF baseline | F1 | **0.73** | ✅ Valid |

## Two-Loop Architecture (Orchestra Research)

```
BOOTSTRAP (once)
  Scope question → search literature → form initial hypotheses

INNER LOOP (fast, repeating)
  Pick hypothesis → write protocol.md → experiment → measure → record → next

OUTER LOOP (periodic, every 5-10 experiments)
  Review results → find patterns → update findings.md → new hypotheses → decide direction
```

## Workspace Structure (Orchestra-compliant)

```
autonomous_laughter_prediction/
├── research-state.yaml       # Central state tracking (hypotheses, results, direction)
├── research-log.md           # Decision timeline (why we chose X over Y)
├── findings.md               # Evolving narrative synthesis
├── literature/               # Papers, survey notes (one file per paper)
│   ├── pickering_2009.md
│   ├── purandare_2006.md
│   └── ...
├── src/                      # Reusable code (plotting, evaluation, data loading)
├── data/                     # Raw result data (CSVs, JSONs, checkpoints)
├── experiments/              # Per-hypothesis work
│   ├── h1_1_pause_detection/
│   │   ├── protocol.md       # What, why, prediction (WRITTEN BEFORE RUN)
│   │   ├── code/
│   │   ├── results/
│   │   └── analysis.md
│   └── h6_1_f0_drop/
├── to_human/                 # Progress reports for human review
└── paper/                    # Final paper (via ml-paper-writing)
```

## Training Pipeline (Three Phases)

```
Phase 1: XLM-R text-only baseline
  XLM-R [CLS] → classifier → F1≈0.80
  Status: ✅ Complete (F1=0.819 word-level)

Phase 2: Frozen XLM-R, train audio_proj + gate
  text_proj frozen, audio_proj + gate train
  Status: ❌ BROKEN (gate collapses to 1.0, audio learns nothing)

Phase 3: Joint fine-tune
  All layers trainable, target F1 > 0.85
  Status: ⏳ Not started
```

## Hypothesis Results (All Validated)

| H# | Hypothesis | Result | Evidence |
|----|-----------|--------|----------|
| H1.1 | Pause → laughter (Cohen's d > 0.5) | ❌ REJECTED | d=0.24 |
| H1.5 | Pause alone F1 ≥ 0.55 | ❌ REJECTED | F1=0.20 |
| H2.5 | ≥70% multi-word spans | ⚠️ ARTIFACT | ±5s window |
| H4.4 | Biosemiotic leakage | 🔴 CONFIRMED | F1=0.829 from features |
| H4.5 | Split leakage | ⚠️ CONFIRMED | 1.9% gap |
| H4.6 | TF-IDF baseline | ✅ CONFIRMED | F1=0.73 |
| H5 | Temporal position | ✅ CONFIRMED | p=4e-143 |
| H6.1 | F0 DROP at punchline | ⚠️ TRIVIALLY SMALL | d=0.063 (p<10⁻⁶) |
| — | Acoustic ceiling | ❌ FLOOR | F1≈0.30 max |
| — | 49 vs 10 features | ❌ NO IMPROVEMENT | F1=0.27 vs 0.29 |

## Paper Paths

| Path | Condition | Paper |
|------|-----------|-------|
| A | Audio fusion works | "Multilingual Word-Level Laughter via Multimodal Fusion" — EMNLP |
| B | Audio fails (current) | "What Makes Laughter Prediction Work: Text is Sufficient" — ACL SRW |
| C | Weak labels broken | "Weak Supervision: When YouTube Subtitles Lie" — EMNLP evaluation |

**Current verdict: Path B.** Audio fails at word-level. Text-only is the ceiling.

## Critical Issues

1. **Gate collapse**: Phase 1 gate_mean=1.0 — audio never learned
2. **WavLM extraction**: Requires Colab GPU (gist: https://gist.github.com/Das-rebel/10b79eddcf2dce5ec4ff298ec3a46b0d)
3. **Acoustic ceiling**: F1≈0.29 regardless of features/model
4. **Hindi data too small**: 48 training examples → F1=0.68 statistically meaningless

## References

- Pickering 2009: F0 DROP at punchline (not rise)
- Purandare 2006: Pause 0.8s before punchline (p<0.001)
- Bachorowski 2001: Laughter 250-500Hz oscillating
- Gillick 2019: CNN on spectrograms F1=0.89
- MultiLinguahah 2026: BYOL-A + Isolation Forest F1=0.68

---

*Last updated: 2026-05-24*
*Source: Orchestra Research AI-research-SKILLs review + 4 hypothesis sessions*