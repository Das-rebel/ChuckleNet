# System Architecture

## Overview

The architecture has evolved through 40+ experiments, guided by Orchestra Research's AI-research-SKILLs two-loop methodology. The project follows a span-reformulation thesis (IoU-F1=0.880 >> word-F1=0.819) with text-only XLM-R as the sole reliable signal.

```
                    ┌─────────────────────────────────────────┐
                    │          INPUT PIPELINE                  │
                    │  YouTube → Whisper → VTT alignment       │
                    │  71 videos → 549K segments → 15K utts    │
                    └────────────────┬────────────────────────┘
                                     │
                    ┌────────────────▼────────────────────────┐
                    │         DATA LAYER                      │
                    │  aligned_utterances.jsonl (15K)         │
                    │  aligned_segments.jsonl (549K)           │
                    │  WavLM embeddings (.pt, ~4.6GB)         │
                    └────────────────┬────────────────────────┘
                                     │
          ┌──────────────────────────┴──────────────────────────┐
          │                                                      │
┌─────────▼─────────┐                           ┌──────────────▼──────────┐
│   TEXT BRANCH      │                           │   AUDIO BRANCH          │
│  XLM-R-base       │                           │  WavLM-base+            │
│  768 → 256 proj   │                           │  768 → 256 proj         │
└─────────┬─────────┘                           └──────────────┬──────────┘
          │                                                │      
          │              ┌─────────────────────┐            │
          └──────────────►   GATED FUSION      ◄───────────┘
                          │  g = σ(W·[t;a])    │
                          │  fused = g⊙t+(1-g)⊙a│
                          └─────────┬──────────┘
                                    │
                          ┌─────────▼──────────┐
                          │  256→128→2 MLP     │
                          │  classifier        │
                          └─────────┬──────────┘
                                    │
                          ┌─────────▼──────────┐
                          │  laughter / no     │
                          └────────────────────┘
```

## Two-Loop Architecture (Orchestra Research)

```
BOOTSTRAP (once)
  Scope question → search literature → form initial hypotheses

INNER LOOP (fast, repeating)
  Pick hypothesis → write protocol.md → experiment → measure → record → next

OUTER LOOP (periodic)
  Review results → find patterns → update findings.md → new hypotheses → decide direction

FINALIZE
  Write paper via ml-paper-writing → final presentation → archive
```

### Workspace Structure (per Orchestra Research)

```
autonomous_laughter_prediction/
├── research-state.yaml       # Central state tracking
├── research-log.md           # Decision timeline
├── findings.md                # Evolving narrative synthesis
├── literature/               # Papers, survey notes
├── src/                      # Reusable code
├── data/                     # Raw result data
├── experiments/              # Per-hypothesis work
│   └── {hypothesis-slug}/
│       ├── protocol.md       # What, why, prediction (WRITTEN BEFORE RUN)
│       ├── code/             # Experiment-specific code
│       ├── results/          # Raw outputs, metrics, logs
│       └── analysis.md       # What we learned
├── to_human/                 # Progress reports for human review
└── paper/                    # Final paper (via ml-paper-writing)
```

## Training Phases

| Phase | What | Status | Expected F1 |
|-------|------|--------|-------------|
| 1 | XLM-R text-only baseline | Done (F1=0.82 word-level) | 0.75-0.80 |
| 2 | Frozen XLM-R, train audio_proj+gate | **Broken** (gate collapsed) | 0.77-0.82 |
| 3 | Joint fine-tune all layers | Not started | 0.82-0.87 |

## Module Inventory

| File | Purpose | Status |
|------|---------|--------|
| `train_fusion_v3.py` | 3-phase training orchestration | Phase 1 broken |
| `model_wavlm_xlmr_fusion.py` | GatedMultimodalFusion model | Gate bug |
| `dataset_utterance_multimodal.py` | Text+audio dataset | Working |
| `extract_wavlm_embeddings.py` | Pre-extract WavLM embeddings | Colab only |
| `train_xlmr_combined.py` | Word-level XLM-R training | Working (F1=0.82) |

## Data Flow

```
aligned_utterances.jsonl
    ├── utterance_id, video_id, text, start, end
    ├── label_any (0/1), label_majority (0/1)
    └── audio_file → extract_wavlm_embeddings.py → wavlm_embeddings.pt

train_fusion_v3.py --phase 1
    ├── text → XLM-R tokenizer → input_ids
    ├── audio → load wavlm_embeddings.pt → audio_embedding
    └── GatedMultimodalFusion(t, a) → classifier → logits
```

## What We Tried (40+ Experiments)

### Audio Branch — All Failed

| Experiment | Result | Root Cause |
|-----------|--------|-----------|
| F0/Energy/Pause (H6.1) | F1=0.27 | Word-level too granular; laughter is supra-segmental |
| WavLM phase A | F1=0.0 | All-same-class bug OR label misalignment |
| Gated fusion | Gate→1.0 | Audio learns nothing; text dominates |
| Teacher refinement | F1=0.078 | LLM parsing bug → catastrophic failure |
| Biosemotic features | +0.003 | Leakage — LLM encoded labels into features |

### Text Branch — The Only Winner

| Experiment | Result | Verdict |
|-----------|--------|---------|
| XLM-R word-level | F1=0.819 | ✅ Strong |
| XLM-R refined labels | F1=0.078 | ❌ LLM labeling fails |
| TF-IDF baseline | F1=0.73 | ✅ Valid baseline |

### Span Reformulation — Strong Signal

| Experiment | Result | Verdict |
|-----------|--------|---------|
| IoU-F1 vs word-F1 | 0.880 vs 0.819 | ✅ 6.1% gap — genuine |
| Multi-word spans | 100% > 2 words | ✅ Confirmed (but artifact of labeling) |

### Cross-Lingual — Real Challenge

| Language | F1 | Notes |
|----------|-----|-------|
| English | 0.819 | Strong |
| Chinese | 0.752 | ~7% drop |
| Hindi | 0.68 | 48 examples, statistically thin |

## Known Issues

1. **Gate collapse**: Phase 1 gate_mean always 1.0 — audio never learned
2. **WavLM extraction**: Requires Colab GPU (gist provided)
3. **No active research loop**: Missing `autonomous_research_loop.py` — now addressed via Orchestra two-loop
4. **Hindi data too small**: 48 training examples → F1=0.68 statistically meaningless

## Orchestra Research Compliance

| Orchestra Requirement | Status | Notes |
|-----------------------|--------|-------|
| research-state.yaml | ✅ Added | Tracks all hypothesis results |
| protocol.md before experiment | ❌ Missing | Was not followed historically |
| research-log.md | ✅ Added | Decision timeline |
| findings.md | ✅ Added | Evolving narrative |
| Inner/outer loop separation | ⚠️ Partial | We iterate but don't synth period |
| Domain skill routing | ⚠️ Partial | We used literature but not skills routing |
| Experiment trajectory tracking | ❌ Missing | No metric_value/baseline/delta per run |

## Research Loop Status

### Completed Sessions

| Session | Hypotheses | Key Finding |
|---------|-----------|-------------|
| Session 1 | H1.1 (pause), H1.2 (F0), H4.6 (StandUp4AI) | Pause signal exists but weak (Cohen's d=0.13) |
| Session 2 | H2.5 (spans), H4.4 (leakage), H4.5 (split) | Biosemotic leakage confirmed (F1=0.829 from features!) |
| Session 3 | H12.2 (pause trajectory), H5 (temporal position) | F1=0.20 for audio; temporal position confirmed |
| Session 4 | H6.1 (F0 DROP) | Cohen's d=0.063 — trivially small despite p<10⁻⁶ |

### Paper Paths (Based on Orchestra Strategy)

| Path | Condition | Paper |
|------|-----------|-------|
| A | Audio fusion works | "Multilingual Word-Level Laughter via Multimodal Fusion" — EMNLP |
| B | Audio fails (current) | "What Makes Laughter Prediction Work: Text is Sufficient" — ACL SRW |
| C | Weak labels broken | "Weak Supervision: When YouTube Subtitles Lie" — EMNLP evaluation track |

**Current verdict: Path B.** Audio fails at word-level. Text-only is the ceiling.

---

*Last updated: 2026-05-24*
*Source: 4 hypothesis sessions + Orchestra Research AI-research-SKILLs review*