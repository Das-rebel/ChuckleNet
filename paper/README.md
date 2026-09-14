# Paper — Canonical Status (2026-09-14)

## CORE PAPER
**`JENNI_PAPER_CORE.md`** — *"Robust Generalization in Audio-First Laughter Detection Through WavLM and Prosodic Ensembling"*

- **Live editing document:** Jenni.ai (app.jenni.ai), editor id `3TPv3LXEjFIEq4m19LvA` (Subho's Brave session is logged in)
- **This file is the synced mirror** of the live Jenni document, promoted 2026-09-14 as THE core paper
- `PAPER_DRAFT_V1.md` / `PAPER_DRAFT_V2.md` (in SUPPORTING as `PAPER_DRAFT_V2_SUPERSEDED.md`) are **reference-only / superseded**

## Number fidelity rule (MANDATE)
Every quantitative claim traces to `SUPPORTING/RESULTS_LOG.md` (rows 1–15) and `SUPPORTING/EXPERIMENT_REGISTRY.md`. When editing the Jenni doc or this mirror, re-verify numbers against those files. AI writing tools must NEVER add citations — only the 7 verified entries in `SUPPORTING/refs.bib` are allowed.

## Contents
| File | Role |
|---|---|
| `JENNI_PAPER_CORE.md` | **Canonical paper text** (Jenni live mirror) |
| `SUPPORTING/RESULTS_LOG.md` | Registered results, rows 1–15 (incl. HF-v2 GPU v3 null) |
| `SUPPORTING/EXPERIMENT_REGISTRY.md` | Pre-registered gates/falsifiers per experiment |
| `SUPPORTING/refs.bib` | The 7 verified references (ACL Anthology/ISCA/HAL verified 2026-09-13) |
| `SUPPORTING/figs/fig_t2_gate3.png` | T2 sequence-effect figure (both scales) |
| `SUPPORTING/figs/fig_t3_null.png` | T3 MELD null figure (arms + bootstrap CI) |
| `SUPPORTING/PAPER_DRAFT_V2_SUPERSEDED.md` | Previous prose draft (kept for reference) |
| `CHUCKLENET_PAPER_V1.pdf` | Old V1 PDF (superseded) |
| `build_pdf.py` | Legacy PDF builder (update to CORE text when rebuilding) |

## Key registered numbers (for quick integrity checks)
- v32 weak-label: IoU-F1@0.2 **0.2290** (P 0.2814 / R 0.1931), F1 **0.2732**, AP **0.142**, corr **0.361**, 620 videos / 121,928 utts / 1,965 pos
- T2 sequence effect: **+0.034** (40v) / **+0.087** (118v); C 0.3460±0.046 / 0.6092±0.026 vs C-shuf 0.3125±0.026 / 0.5227±0.011
- T3 MELD null: A 0.4483 / B 0.4433 / C 0.4434, Δ(C−B) **0.0000**, CI [−0.0142, +0.0145]
- HF-v2 GPU v3 (2026-09-14): **NULL** F1 0.0192 — Wav2Vec2Model/WavLM class mismatch, random encoder; row 15

## Sync protocol
Jenni edit → export/copy text → replace `JENNI_PAPER_CORE.md` body → git commit → rclone to `gdrive:ChuckleNet/PAPER_CORE/`.
