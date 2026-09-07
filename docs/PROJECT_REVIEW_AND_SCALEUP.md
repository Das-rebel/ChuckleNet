# ChuckleNet Project Review — Full Audit + Scale-Up Plan
**Date:** 2026-09-07 full audit session (v19 era)
**Companion docs:** `docs/DECISION_GRAPH.md` · `docs/AUDIT_DRIVE_AND_VALIDATION_2026-09-07.md` (Drive findings, Gillick revalidation, timeline)

---

## PART 1 — WHERE THE PROJECT ACTUALLY IS

### 1.1 The one-line truth

We have a fusion architecture (WavLM+prosody → MLP) whose **honest** segmentation
quality is **IoU-F1@0.2 = 0.31 vs a 0.51 baseline**. Every "0.97+" number in the
project history is a split-leakage or pseudo-label-circularity artifact. The
0.31 → 0.51 gap is the project. Everything else is infrastructure for closing it.

### 1.2 Verified assets (ground truth from disk)

| Asset | Verified state |
|---|---|
| `models/fusion_mlp_v2.pt` | ⚠️ FILE LOST (local `models/` empty); nearest artifact on Drive (`standup4ai/experiments/best_model.pt` era, 791-dim, prosody dims 10–22 zeros). Dead checkpoint — never resume. |
| `docs/*.json` results | 118v: IoU-F1@0.2 = **0.310** · 40v: 0.223 · word-F1@0.5 = 0.676 · Gillick real-label ablation **REVALIDATED 2026-09-07: fusion 0.559 / WavLM-only 0.548 / prosody-only 0.537** (`GILLICK_REVALIDATION_RESULTS.json`) |
| `data/chuckle-net/aligned_utterances.jsonl` | 15,000 utt, 71 videos, 32% pos (real VTT labels) |
| `data/chuckle-net/wavlm_embeddings/` | 660 video-level files |
| `data/chuckle-net/prosody_phaseD.json` | 14,998 × 21-dim |
| Drive `chuckle_net_1000/` | **621 audio + 628 VTT verified 2026-09-07** (62% of target; older "180 files" claim was stale) |
| `data/utterances/gillick_fresh/` | 162 videos, REAL AudioSet labels — the gold eval set; artifacts + revalidation JSON on Drive `chuckle_net/gillick_data/` + `docs/GILLICK_REVALIDATION_RESULTS.json` |
| HF `Hayasuki/chuckleNet-v2` | ❌ **REGRESSED Sep 4 19:02–20:37** — card now claims F1=0.960 "production-ready" with no source JSON; re-fix PENDING (honest numbers + provenance links) |

### 1.3 What the review found broken (this session)

1. **CRITICAL — v17 audio loading will fail.** Cell 4 uses `sf.read()` on `.m4a`.
   libsndfile cannot decode AAC/m4a. The librosa fallback removed audioread
   (librosa ≥0.10). On current Colab, **every file fails → 0 samples**.
   The only proven loader is v9's ffmpeg-subprocess (28,204 samples extracted with it).
   → **v19 restores it (canonical, execution-simulation validated).** Cell 2 must test the real loader, not sf.read.
2. **Checkpoint model mismatch** (789/791/795 confusion) — resolved: never load old
   checkpoints into new extractions; train fresh with `dim=X.shape[1]`.
3. **Notebook churn** (v8→v17, 15 gists) — caused by blind editing. New rule: AST-compile
   every cell + dependency check + logic trace before publish (done for v17b).
4. **Goal drift** — effort went to notebook plumbing instead of the metric gap.
   Corrected priority stack is in DECISION_GRAPH.md §7.

---

## PART 2 — SCALE-UP PLAN

### 2.0 Measured facts (basis for all estimates)

| Quantity | Measured | Source |
|---|---|---|
| Utterances per video | **157** | 28,204 utt / 180 files (v9 run) |
| Feature vector | 795-dim float32 = **3.1 KB/utt** | WavLM 768 + prosody 27 |
| Storage @1000 videos | **≈0.5 GB** features.npz | fits free Drive tier easily |
| Pos rate (VTT labels) | ~20–30% | aligned_utterances 32%, extraction runs ~22% |

### 2.1 Stage plan

```
STAGE 0 — Correctness gate (1 Colab session, ~30 min)
  □ v19 (DONE ✓ code-side): ffmpeg loader restored; Cell 2 tests real loader, 3/3 LOAD OK + 20-file gate — awaiting first real Colab run
  □ Dry-run extraction on 20-file slice → verify dims (768+27), pos-rate sanity,
    checkpoint write/read cycle, resume dedup
  GATE: features.npz shape (N, 795), pos rate 15–35%, zero NaNs
        → do NOT scale a broken extractor

STAGE 1 — Extraction at 1000 videos (2–4 Colab T4 sessions)
  Bottlenecks & fixes:
  - WavLM per-utterance forward pass: batch utterances of equal length
    (sort-by-length buckets, batch 8–16) → expect 3–5× throughput
  - librosa.pyin is CPU-heavy (~100ms/utt single-thread): compute prosody in a
    ThreadPoolExecutor(4) overlapped with GPU WavLM calls, OR swap pyin for
    piptrack/YIN mean (5–10× faster) — record the swap in the model card
  - Checkpoint every 20 files (already in v17) + processed_idx dedup → safe resume
    across Colab session timeouts (~4h limit each)
  Output: chuckle_net_1000_features.npz ≈ 157K × 795, ~0.5 GB on Drive

STAGE 2 — Label quality at scale (parallel with Stage 1)
  VTT-regex labels are weak. Plan:
  - Keep VTT labels as train signal ONLY
  - Evaluate ONLY on Gillick gold set (real AudioSet labels, 162 videos)
  - Add agreement audit: sample 200 utterances, hand-check VTT-label precision
  - NO energy pseudo-labels in the training set (circularity — dead end #3)

STAGE 3 — Training at scale (local or single Colab session; minutes, not hours)
  - Fresh FusionMLP(dim=795): 795→512→256→64→1, BN, dropout, AdamW, pos_weight≈2
  - Splits: GroupKFold by video (5-fold) for CV + Gillick gold for external test
  - Report: IoU-F1@0.2/0.3, word-F1@0.5, per-fold std — nothing else
  - Baselines in same run: WavLM-only (768), prosody-only (27) — real ablations,
    so the fusion claim is finally backed by OUR numbers, not StandUp4AI's

STAGE 4 — Error analysis → the actual research (1–2 weeks)
  - Bucket errors: laugh duration, crowd-noise level, music overlap, speaker overlap
  - Hypothesis shortlist (from research tree): H6 prosody F0-drop, H12 chunked
    interaction, H14 hybrid fusion — pick ONE based on error buckets
  - Success criterion: IoU-F1@0.2 ≥ 0.40 first, 0.51 stretch

STAGE 5 — Publication package (only after Stage 4 milestone)
  - Model card: honest numbers + measured ablations + known limitations
  - Repo: ONE canonical notebook (v19, gist 188a3bc5...), utterances_clean.jsonl.gz already public
  - Deferred pivot (humor-strength 0–100%) starts only after 0.40 reached
```

### 2.2 Compute & cost budget

| Stage | Compute | Wall-clock estimate |
|---|---|---|
| 0 | 1× Colab T4, <30 min | 1 session |
| 1 | 2–4× Colab T4 (~4 h each) | 1–2 days of sessions |
| 2 | human audit 200 samples | ~1 h |
| 3 | 1× Colab T4, <15 min | minutes (MLP is tiny) |
| 4 | CPU/local | 1–2 weeks calendar |
| 5 | local | 1 week calendar |

Total: **~5 free Colab sessions + 2–3 weeks calendar** to a publishable, honest
1000-video result. No paid APIs anywhere (Kaggle 403 / HF Spaces 402 stay avoided).

### 2.3 Scale risks & mitigations

| Risk | Mitigation |
|---|---|
| Colab session death mid-extraction | checkpoint@20 + processed_idx dedup (v17, verified) |
| m4a decode failures at scale | ffmpeg loader logs per-file failures; skip-stats summary flags >5% failure |
| Pos-rate drift as video mix changes | print pos-rate every 100 files; alarm if <10% or >45% |
| Drive I/O slowness | write features.npz once at end; checkpoint arrays in RAM, npz every 100 files |
| Label noise dominates at 157K utt | Stage 2 audit BEFORE trusting Stage 3 numbers |
| Dimension creep (another 789/791 incident) | extractor asserts `feats.shape == (795,)` per utterance |

---

## PART 3 — GOALS, RE-ALIGNED

### Was (drifted)
- "Run the notebook" → 15 gist versions of plumbing
- "F1=0.975 ready for paper" → leakage artifact, unreproducible
- "Match old 791-dim checkpoint" → dead end, wasted sessions

### Now (aligned, measurable)
| # | Goal | Metric | Current | Next milestone |
|---|---|---|---|---|
| G1 | Honest eval | IoU-F1@0.2 vs 0.51 baseline | 0.31 | **0.40** |
| G2 | Canonical pipeline | 1 notebook, AST-checked, runs end-to-end | v19 (execution-sim verified, not yet run in Colab) | **v19 green on 20-file gate** |
| G3 | Scale | 1000 videos extracted | 621 audio / 628 VTT on Drive | **1000 (157K utt)** |
| G4 | Real ablations | fusion vs WavLM-only vs prosody-only, our numbers | missing | **in Stage 3 run** |
| G5 | Publish | model card + repo, zero inflated claims | card fixed | **after 0.40** |

**Standing rule:** a number may be reported only if it exists in a result JSON produced
by a video-level held-out split with real labels. Pseudo-label and random-split numbers
are debugging signals, never results.
