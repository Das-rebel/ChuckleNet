# ChuckleNet Decision Graph
**Last updated:** 2026-09-07 full audit session (Drive + validation + timeline audit — see docs/AUDIT_DRIVE_AND_VALIDATION_2026-09-07.md)
**Purpose:** Single source of truth for what was decided, what was learned, and what is dead.

---

## ROOT GOAL (corrected)

> **Build a laughter detection model for stand-up comedy audio that beats the
> StandUp4AI baseline (IoU-F1@0.2 = 0.51) with an honest, publicly reproducible
> Colab pipeline.**

Current honest standing: **IoU-F1@0.2 = 0.31** — BELOW baseline. That gap is the project.

---

## 1. GOAL LAYER

```
ROOT: Beat IoU-F1@0.2 = 0.51 (StandUp4AI baseline) on held-out comedy videos
│
├── G1. Honest metrics only — claims must match result JSONs          [ACTIVE, enforced]
├── G2. ONE canonical Colab pipeline, dimension-consistent            [ACTIVE → v19 CANONICAL]
├── G3. Public reproducibility (Colab gist + GitHub repo)             [ACTIVE]
└── G4. Future pivot: humor STRENGTH prediction (0–100%)              [DEFERRED — after G1–G3]
```

---

## 2. METRICS LAYER — honest vs suspect

### HONEST (verified from JSON result files)
| Source | Metric | Value | vs Baseline |
|---|---|---|---|
| `docs/FULL_FUSIONMLP_118V_RESULTS.json` | IoU-F1@0.2, 118v, 5-fold GroupKFold | **0.310** | 0.51 ✗ below |
| `docs/HYPOTHESIS_TEST_RESULTS.json` | IoU-F1@0.2, same setup | **0.304** | 0.51 ✗ below |
| `docs/FUSIONMLP_40V_RESULTS.json` | IoU-F1@0.2, 40v | **0.223** | 0.51 ✗ below |
| `docs/FULL_FUSIONMLP_118V_RESULTS.json` | word-F1@0.5 | 0.676 | — |
| Gillick AudioSet REAL labels (162v, 1581 segs) | segment-F1@0.5 | **0.559** (revalidated 2026-09-07, OOF GroupKFold — `GILLICK_REVALIDATION_RESULTS.json`) | WavLM-only 0.548, prosody-only 0.537 → fusion wins (original Aug-7 claim 0.541±0.030 reproduced in ordering) |

### SUSPECT / INFLATED — never cite in paper
| Claim | Where | Why suspect |
|---|---|---|
| F1 = 0.975 "breakthrough" | `chuckle.fusion_breakthrough` memory, CLEAN_PROJECT_PLAN | Comedian-split on TRAINING distribution; 22.7% pos rate; model file `fusion_mlp_v2.pt` trained on 791-dim where 13 of 23 prosody dims are LITERAL ZEROS |
| F1 = 0.9909 energy model | `laughter.energy_model_620_results` | **CIRCULAR**: labels are energy-threshold pseudo-labels; model uses energy features. Meaningless. |
| F1 = 0.9759 top200 prosody | `laughter.top200_model_success` | Same pseudo-label circularity risk (energy-threshold labels) |
| F1 = 0.952 original README | HF model card (FIXED) | Fabricated/copied; already replaced with honest 0.31 |
| "Prosody alone F1=0.71" | HF model card (FIXED) | Copied from StandUp4AI paper (related work), never our ablation |
| F1 = 0.960 "Production-ready" | HF model card (CURRENT — REGRESSED Sep 4 19:02–20:37) | NO source JSON anywhere; 2nd regression incident; card re-fix PENDING |
| val 0.9595 / test 0.9729 | gdrive `chuckle_net/gillick_data/fusion_results.json` | **REAL video-level split (train_fusion_local.py, seed 42)** — but on the LOST July-16 labeling scheme (prosody-circularity signature); cite only as historical, not comparable — see `FUSION096_PROVENANCE_VALIDATION.json` |
| F1 = 0.879 | `scale221/results.json` | teacher_max_prob=0.527 pseudo-label circularity |
| "labels" in eval_youtube_labeled.jsonl | `data/chuckle-net-final/` (121,167 utts) | INVALID: 0.1% positive on 100% empty-text utterances — not laughter labels; do not train |

**Rule going forward:** any F1 > 0.7 on this task requires: (a) real human/AudioSet labels,
(b) video-level held-out split, (c) no feature-label circularity. Otherwise assume leakage.

---

## 3. MODEL LAYER — what actually exists on disk

| File | Input dim | Reality |
|---|---|---|
| `models/fusion_mlp_v2.pt` | **791** | ⚠️ FILE LOST (local `models/` empty; nearest artifact `standup4ai/experiments/best_fusion_model.pt` on Drive). Historically: 768 WavLM + 23 "prosody" with dims 10–22 zeros. DEAD — never resume |
| `training/prosody_fusion_embeddings/fusion_mlp_model.pt` | **405** | ✅ exists — different lineage entirely |
| `training/prosody_fusion_results/best_model.pt` | 21-dim prosody proj + WavLM | ✅ exists — `PhaseAWithProsody` lineage (Colab_WavLM_Prosody_Training_v2) |
| `models/energy_model/*` | 38-dim | ⚠️ FILE LOST — was circular pseudo-label model; dead for reporting either way |
| `gdrive:chuckle_net/gillick_data/fusion_best.pt` | 791 | ✅ on Drive — Gillick-162v model, validated by revalidation (F1 0.559); no dead prosody dims in that dataset |

**Feature-count history (source of the 789/791/795 confusion):**
- 789 = 768 + 21 (v2 Colab training notebook: 2 RMS + 2 ZCR + 2 f0 + 13 MFCC... = 19→21 padded)
- 791 = 768 + 23 (fusion_mlp_v2.pt; 10 real + 13 zeros from `prosody_10dim` padding)
- 795 = 768 + 27 (GitHub Colab extraction: 3 RMS + 3 f0 + 2 ZCR + 2 SC + 2 SB + 2 rolloff + 13 MFCC)
- **Resolution:** none of the old numbers matter — fresh training auto-sizes from data
  (`FusionMLP(dim=X_s.shape[1])`). Stop trying to match dead checkpoints.

---

## 4. PIPELINE LAYER — Colab notebook lineage

```
v7 (GitHub original, "last known working")  ← NEVER fully worked (Cell 8 NameError, dedup bug)
├── v8–v11: piecemeal fixes, import errors
├── v9 (ffmpeg loader!)  ← ONLY version with proven successful extraction: 28,204 samples / 180 m4a
├── v12–v14b: rewrites; v14b had whole-cell-on-one-line SyntaxError
├── v15: GitHub base + 7 fixes (blind iteration)
├── v16: + pre-flight, always-define, force-clean (CHECKPOINT_FILE use-before-define bug)
├── v17a: GitHub original had DUPLICATED `if not vtt_path:` block + mangled indent
├── v17b "fix": moved continue to 4sp → made it compile but UNCONDITIONAL → 0 samples
│   (validation was check-theater: grepped 'a 4sp continue exists' — passes either way)
├── v18: ffmpeg loader fixed Cells 2/4; Cell 7 inherited the unconditional continue
└── v19 (CURRENT, CANONICAL): triple-checked via manual review + EXECUTION SIMULATION
    of Cell 7 against mocked I/O + independent LLM corroboration. Fixed:
    1. unconditional continue → 0 samples (proven by simulation: 0/6 files)
    2. missing processed_idx membership guard → resume duplicated features (9→15 proven)
    3. BatchNorm1d crash on batch size 1 (len%32==1) — drop lone sample
    4. checkpoint-load guard `start_idx>0` blocked data on completed runs
    → 12/12 logic tests: fresh / skip-paths / crash-resume / incremental / idempotent
```

**VALIDATION STANDARD (from v19 lesson):** AST compile ≠ correct. Required:
(1) compile every cell, (2) execute critical logic vs mocked I/O with count assertions,
(3) one independent reviewer. No more grep-for-the-fix-pattern checks.

**Root cause of the v8→v17 churn:** editing notebooks without executing them.
**Rule going forward:** no notebook ships without (1) AST compile check of every code cell,
(2) variable-dependency check, (3) logic trace of the critical loop.

---

## 5. DATA LAYER

| Asset | Size | Status |
|---|---|---|
| `data/chuckle-net/aligned_utterances.jsonl` | 15,000 utt / 71 videos / 32% pos | labeled, primary local data |
| `data/chuckle-net/wavlm_embeddings/` | 660 files | extracted |
| `data/chuckle-net/prosody_phaseD.json` | 14,998 × 21-dim | extracted |
| Drive `chuckle_net_1000/` (m4a + VTT) | target 1000, **621 audio + 628 VTT** (verified 2026-09-07; older docs said 180) | 62% downloaded |
| Colab extraction checkpoint (v9, Jul) | 28,204 samples | features 795-dim |
| Colab extraction checkpoint (Sep 5) | 45,192×795, 279 videos | ⚠️ features real but **labels BROKEN (1.6% pos)** — sparse-label join; no per-row timestamps → not re-derivable. Write-off. Lesson: persist (vid, utt_start, utt_end) with every checkpoint |
| `gdrive:chuckle_net/gillick_data/fusion_features.npz` | 1,581 segs × 791, 162 videos, 51.5% pos | ✅ REAL AudioSet labels — revalidation source |
| Gillick fresh (`data/utterances/gillick_fresh/`) | 162 videos, real AudioSet labels | eval-only gold set |

---

## 6. DEAD ENDS (do not revisit)

1. **Word-level cascade** — IoU-F1 stuck ~0.50, abandoned
2. **Sparse-label datasets** (f0_668 1.2% pos, gillick_272 2.2% pos) — don't train on them
3. **Energy-threshold pseudo-labels** — circular; fine for pre-training experiments, never for reported metrics
4. **Probability ensembles** — feature concatenation beat them (+7%)
5. **Matching new extractions to old checkpoints** (789/791/795 hunt) — train fresh, auto-size
6. **Kaggle API** — 403, blocked; **HF Spaces** — 402, blocked. Colab + GitHub gists only.
7. **AST labeling at scale** — Sep-5 run confirms ~1.6% pos at corpus scale; dead end.
8. **YouTube "labeled" packaging** (`chuckle-net-final/eval_youtube_labeled.jsonl`) — 0.1% pos on empty text; labels invalid.
9. **`cascade_data/` (Drive, Aug 6)** — 141MB, no producing script found anywhere; unlogged experiment, provenance UNVERIFIED — do not build on it.

---

## 7. CURRENT PRIORITY STACK (aligned)

```
P0  Run v19 in Colab (gist 188a3bc5...): Cell 2 3/3 LOAD OK → 20-file gate → full 621-video extraction
    + RE-FIX HF model card (regressed to 0.960; honest numbers + provenance links)
P1  Extract remaining ~380 videos → 1000; checkpoints must persist (vid, utt_start, utt_end)
P2  Consolidate gists: mark v19 canonical, archive v8–v18 noise
P3  Error analysis on the 0.31 → 0.51 gap (where do we lose? short laughs? music? crowd noise?)
P4  Paper draft with honest numbers (IoU-F1 0.31 @118v; Gillick-162v ablation 0.559/0.548/0.537 — GILLICK_REVALIDATION_RESULTS.json)
P5  Deferred: humor-strength prediction pivot (research_humor_goals)
```

---
# 📌 ADDENDUM — Sep 7-8, 2026: Label hierarchy proven, PRD v6 recovered, v20 finalized

## New decisions (verified this session, supersedes anything above in conflict)
- **D-LABEL-TIERS**: 4-tier label hierarchy established (docs/LABEL_HIERARCHY.md). July-16 npz labels = humor-lexicon `label_any` (100% uid+label match, 15000/15000, to chuckle_data/aligned_utterances.jsonl). 'Gillick 87' misnomer corrected (0/87 overlap with Gillick-162v). 'EMNLP labels' = StandUp4AI benchmark annotations.
- **D-ANCHOR-RULE**: any Tier-1-trained model MUST carry Tier-2/3 anchor eval before reporting numbers. Prevents 0.96-pattern recurrence.
- **D-033-IS-BEST**: best honest interval number = IoU-F1@0.2 **0.3302** on 118v vs StandUp4AI truth (merge 0.8); '0.310' was pre-sweep. Gold = Gillick-162v fusion 0.559. Real gap: 0.33 → 0.51.
- **D-PRD6-RECOVERED**: PRD_V6 + LAUGHTER_PREDICTION_RESEARCH_VISION recovered from Jun-3 transcript (docs/recovered/, GitHub, Drive). PRD v6 3 products: P1 group laughter (cascade → died at IoU 0.50 ceiling → pivoted to segment-level), P2 individual/sarcasm (deferred, needs diarization), P3 content scorer.
- **D-MONETIZE-C**: DEFINITIVE_PLAN.md (Aug 6 council): paper+open-source, NOT startup. Option C career-first recommended. The planned F0 'When Simple Beats Deep' 0.96 paper = DISQUALIFIED (lexicon labels). Publishable replacement: weak-label pitfall + honest numbers.
- **D-V20-FINAL**: canonical Colab notebook = **ChuckleNet_Final_Colab_v20.ipynb** (v19 + GATE_N=20 gate + pos_rate<10% hard-fail + per-utterance timestamp persistence + IoU-F1@0.2 eval + results_v20.json + fresh *_v20 checkpoint namespace). v19 gist stays as provenance. Gist: <to be created>.

## Track scores (measured Sep 7-8)
Mission 70% · Grand vision ~30% · Research ~40% · Monetization-OptionC ~40%. All converge on: run v20 gate → full 621v → anchor evals → ONE honest paper.
- **D-GATE-V202 (Sep 8)**: v20 gate hard-fail at 0.7% was CORRECT behavior and exposed that the 620v collection is marker-poor: full-set pos_rate 1.16% (2,816/243,501), 174/620 videos with any markers, ~10 videos ≥10% (docs/GATE_FORENSICS_620V_*). Labels proven genuine (Drive VTTs byte-identical to curated set). Fix: 3-tier gate (FAIL<2%/WARN 2-10%/PASS≥10%), curated GATE_IDS, dual FULL+RICH training, PR-AUC metric, YouTube rolling-caption dedup (parsed counts were ~50% inflated). Checkpoint namespace bumped to *_v21 (old _v20 checkpoint = wrong-mix samples, never resume).
