# ChuckleNet — RESULTS LOG (single scoreboard)

> Every reported number lands here. Order = chronological. Label tier per docs/LABEL_HIERARCHY.md.
> **Anchor rule:** Tier-1 numbers are "caption-marker detection" — no gold claims without Tier-2/3 anchor evals.

| # | Date | Data | Labels | Model | Metric | Value | Status | Evidence |
|---|------|------|--------|-------|--------|-------|--------|----------|
| 1 | Jul–Aug 2026 | 87v pipeline | T0 humor-lexicon (RETIRED) | F0 / XLM-R cascade / FusionMLP | seg F1 | "0.94–0.98" | ❌ DISQUALIFIED — label circularity (labels ≈ deterministic fn of prosody; 100% provenance proven) | docs/SCALE1000_NOTEBOOK_FORENSICS.json, FUSION096_FULL_VALIDATION.json |
| 2 | Sep 2026 | Gillick-162v | T3 gold | FusionMLP 795d | seg F1 (video-level split) | **0.5590** | ✅ honest gold anchor | docs/GILLICK_REVALIDATION_RESULTS.json |
| 3 | Aug–Sep 2026 | 118v benchmark | T2 StandUp4AI | FusionMLP, IoU-F1@0.2 merge 0.8 | IoU-F1@0.2 | **0.3302** (naive 0.29) | ✅ honest benchmark anchor | docs/BEST_118V_RESULTS.md |
| 4 | — | StandUp4AI paper | T2 | theirs | IoU-F1 | 0.51 | external baseline | paper |
| 5 | **Sep 8** | **GATE: 20 curated v** | **T1 VTT markers** | FusionMLP 795d, GroupKFold5 | PR-AUC | 0.208 ± 0.082 (2.6× random 0.079) | ✅ weak-label gate, FULL | results/RESULTS_V21_GATE_20CURATED.json |
| 6 | **Sep 8** | same FULL | T1 | same | IoU-F1@0.2 | 0.197 ± 0.034 | ✅ below naive | same |
| 7 | **Sep 8** | **GATE: 9 RICH v** | **T1** | same | **IoU-F1@0.2** | **0.407 ± 0.063** | ✅ **first weak-label > naive AND > 0.3302** — ⚠️ NOT comparable (9 marker-selected videos; anchor pending) | same |

## Gate insights (Sep 8)
- Label-noise hypothesis CONFIRMED: RICH-vs-FULL doubles every metric; precision flat (0.447→0.431), recall doubled (0.147→0.296).
- FULL fold-5 anomaly (PR-AUC 0.067 < random 0.079): 4-video folds too small → 620v run fixes fold variance.
- Full-set forensics: pos 1.16% (2,816/243,501), markers in 174/620 videos → FAIL line set to 0.5% (D-GATE-FAIL05).

## Pending
- [ ] **Full 620v run** (GATE_N=0): FULL ≈ 122K deduped samples @ ~1.16% pos; RICH ≈ 10 videos @ ~10.5%. Expect WARN at gate — correct behavior.
- [ ] **Tier-2 anchor eval**: v21 feature pipeline on 118v StandUp4AI-truth set → compare vs 0.3302.
- [ ] **Tier-3 anchor eval**: Gillick-162v → compare vs 0.559.
- [ ] Then: honest paper (weak-label pitfall + label-circularity case study + scaled weak-label numbers).
